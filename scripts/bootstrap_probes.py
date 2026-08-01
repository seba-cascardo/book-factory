#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bootstrap_probes.py — seed the concept probes the dossier builder needs.

A probe is a tiny record that says "here is how to find every passage about
concept X": an id, a display name, the unit where it belongs, and an include
regex (plus optional exclude and homonym guard).

Three sources, tried in order, so this works on a project the skill scaffolded
AND on a finished book it never touched:

  1. `bible/knowledge-graph.yaml` — the concept list, already curated. Best.
  2. `bible/glossary.md` — multi-word terms the project decided to be consistent
     about. Good enough to find contradictions.
  3. Term frequency over the corpus — capitalized and hyphenated phrases that
     appear in two or more units. Crude, and the only option for a retrofit run
     over a book with neither of the above. Expect to hand-tune.

Hand-tuned probes live in `bible/concept-probes-tuned.yaml` and are NEVER
touched by this script. They win at read time. Tuning is expected: the concept
that actually contradicts itself is usually finer-grained than a graph node.

Usage
  python scripts/bootstrap_probes.py
  python scripts/bootstrap_probes.py --force        # regenerate the base
  python scripts/bootstrap_probes.py --min-units 3  # stricter frequency fallback
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("Missing PyYAML. Install with: pip install pyyaml")

sys.path.insert(0, str(Path(__file__).resolve().parent))

from bookkit.project import Project, add_common_args, load_project  # noqa: E402
from bookkit.segment import segment  # noqa: E402
from bookkit.textmetrics import stopwords_for  # noqa: E402

BASE_PATH = "bible/concept-probes.yaml"
TUNED_PATH = "bible/concept-probes-tuned.yaml"

GLOSSARY_TERM_RES = [
    re.compile(r"^\s*[-*]\s+\*\*(.+?)\*\*"),
    re.compile(r"^\*\*(.+?)\*\*\s*[—:-]"),
    re.compile(r"^#{2,4}\s+(.+?)\s*$"),
    re.compile(r"^\|\s*\*?\*?([^|*]+?)\*?\*?\s*\|"),
]

# Candidate phrases for the frequency fallback are built by TOKENIZING and
# emitting overlapping n-grams — not by scanning with a phrase regex.
#
# The regex version is the obvious implementation and it is wrong. Regex
# scanning is greedy and non-overlapping, so in "the staging table is dropped"
# it matches "the staging table", rejects it for the leading stopword, and has
# already consumed the characters — "staging table" is never tried. On a corpus
# where most noun phrases follow an article, that silently loses nearly every
# good candidate. This path is the whole retrofit story for a book with no
# knowledge graph and no glossary, so losing it quietly is expensive.
WORD_RE = re.compile(r"[A-Za-z][A-Za-z\-]*")
NGRAM_SIZES = (2, 3)


def slugify(name: str) -> str:
    s = re.sub(r"[^\w\s-]", "", name.strip().lower())
    return re.sub(r"[\s-]+", "_", s).strip("_") or "concept"


def probe_from_name(cid: str, name: str, home: str = "",
                    synonyms: list[str] | None = None) -> dict:
    """Build an include regex from a term and its synonyms.

    Spaces become `[\\s-]+` so "drill down", "drill-down" and "drilldown" all
    match: a book that spells a term two ways is exactly the book where the two
    spellings carry two slightly different claims.
    """
    forms = [name] + list(synonyms or [])
    alts = sorted({_term_pattern(f) for f in forms if f and f.strip()}, key=len,
                  reverse=True)
    return {
        "id": cid,
        "name": name,
        "home": home,
        "include": r"\b(" + "|".join(alts) + r")\b" if alts else re.escape(name),
        "exclude": "",
        "homonym_guard": "",
        # Set true for terms that are also ordinary words in the prose language
        # (SET, KEEP, JOIN, LOAD). Case-insensitive matching on those returns
        # triple-digit junk and makes the dossier unreadable.
        "case_sensitive": False,
        "tuned": False,
    }


def _term_pattern(term: str) -> str:
    parts = [re.escape(p) for p in re.split(r"[\s-]+", term.strip()) if p]
    core = r"[\s\-]?".join(parts) if len(parts) > 1 else (parts[0] if parts else "")
    return core + "s?" if core and not core.endswith("s") else core


# ---------------------------------------------------------------------------
# Sources
# ---------------------------------------------------------------------------


def from_knowledge_graph(project: Project) -> list[dict]:
    kg = project.load_yaml("bible/knowledge-graph.yaml")
    out: list[dict] = []
    for node in kg.get("concepts") or []:
        cid = node.get("id")
        name = node.get("name") or cid
        if not cid:
            continue
        out.append(probe_from_name(
            cid, name,
            home=node.get("introduced_in", "") or "",
            synonyms=node.get("aliases") or node.get("synonyms") or [],
        ))
    return out


def from_glossary(project: Project) -> list[dict]:
    path = project.bible / "glossary.md"
    if not path.exists():
        return []
    seen: set[str] = set()
    out: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        for rx in GLOSSARY_TERM_RES:
            m = rx.match(line)
            if not m:
                continue
            term = re.sub(r"[`*_]", "", m.group(1)).strip()
            key = term.lower()
            if key in seen or not (2 <= len(term) <= 48):
                break
            if not re.fullmatch(r"[A-Za-z][\w()\- ]*", term):
                break
            seen.add(key)
            out.append(probe_from_name(slugify(term), term))
            break
    return out


def from_frequency(project: Project, min_units: int, limit: int) -> list[dict]:
    """Last-resort discovery for a book with no graph and no glossary.

    Restricted to phrases that appear in at least `min_units` units, because a
    concept that lives in one unit cannot carry a cross-unit contradiction — and
    finding those is the entire point.
    """
    stop = stopwords_for(project.language_variant)
    units_by_phrase: dict[str, set[str]] = defaultdict(set)
    counts: Counter[str] = Counter()

    for path in project.unit_paths:
        for r in segment(path, rel_to=project.root):
            if r.kind in ("code", "blank", "hr"):
                continue
            text = re.sub(r"`[^`]*`", " ", r.text).lower()
            words = WORD_RE.findall(text)
            for n in NGRAM_SIZES:
                for i in range(len(words) - n + 1):
                    gram = words[i:i + n]
                    if any(w in stop or len(w) <= 2 for w in gram):
                        continue
                    phrase = " ".join(gram)
                    units_by_phrase[phrase].add(path.stem)
                    counts[phrase] += 1

    ranked = sorted(
        (p for p, u in units_by_phrase.items() if len(u) >= min_units),
        key=lambda p: (-len(units_by_phrase[p]), -counts[p]),
    )[:limit]

    out: list[dict] = []
    for phrase in ranked:
        probe = probe_from_name(slugify(phrase), phrase)
        probe["home"] = sorted(units_by_phrase[phrase])[0]
        out.append(probe)
    return out


# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Seed concept probes for the dossier builder.")
    add_common_args(ap)
    ap.add_argument("--force", action="store_true",
                    help="Regenerate the base file even if it exists.")
    ap.add_argument("--min-units", type=int, default=2,
                    help="Frequency fallback: minimum units a phrase must span (default 2).")
    ap.add_argument("--limit", type=int, default=120,
                    help="Frequency fallback: max probes to emit (default 120).")
    ap.add_argument("--source", choices=["auto", "kg", "glossary", "frequency"],
                    default="auto")
    args = ap.parse_args(argv)

    project = load_project(args.root, args.units)
    base = project.root / BASE_PATH

    if base.exists() and not args.force:
        existing = project.load_yaml(BASE_PATH)
        n = len(existing.get("probes") or [])
        print(f"[probes] {BASE_PATH} already has {n} probe(s). "
              f"Use --force to regenerate, or hand-tune in {TUNED_PATH}.")
        return 0

    order = ([args.source] if args.source != "auto"
             else ["kg", "glossary", "frequency"])
    probes: list[dict] = []
    used = ""
    for source in order:
        if source == "kg":
            probes = from_knowledge_graph(project)
        elif source == "glossary":
            probes = from_glossary(project)
        else:
            probes = from_frequency(project, args.min_units, args.limit)
        if probes:
            used = source
            break

    if not probes:
        sys.exit("Could not derive any probe. Provide bible/knowledge-graph.yaml, "
                 "bible/glossary.md, or lower --min-units.")

    doc = {
        "# generated by": "scripts/bootstrap_probes.py — hand-tune in "
                          "bible/concept-probes-tuned.yaml, which wins and is never "
                          "overwritten",
        "# derived from": used,
        "# fields": "id · name · home · include · exclude · homonym_guard · case_sensitive",
        "schema_version": "1.0",
        "probes": probes,
    }
    base.parent.mkdir(parents=True, exist_ok=True)
    base.write_text(yaml.safe_dump(doc, allow_unicode=True, sort_keys=False, width=200),
                    encoding="utf-8")

    print(f"[probes] {len(probes)} probe(s) from {used} → {BASE_PATH}")
    if used == "frequency":
        print("[probes] Frequency-derived probes are crude by construction. Run "
              "`build_concept_dossier.py --probe-report` and tune the noisy ones "
              f"in {TUNED_PATH} before trusting a dossier.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
