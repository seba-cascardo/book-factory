#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lint_style.py — the deterministic half of the Proofreader.

A model is worse than a regex at this and better at everything else. It
hallucinates the occasional violation, and by chapter 14 it is tired. Spelling
variants, pinned terminology and declared conventions are mechanical, so they
run mechanically; concordance, broken sentences and real typos stay with the
Proofreader agent.

Prose only. Fenced blocks are excluded, because `colour` inside a field name and
`1000` inside code are not errors.

Config: `bible/lint-config.yaml` when present (see templates/lint-config.yaml).
With no config the script still runs — spelling variants and whitespace rules
need nothing, and the casing watchlist is derived from `bible/glossary.md`.

Usage
  python scripts/lint_style.py
  python scripts/lint_style.py --by-unit --rule en_gb
  python scripts/lint_style.py --json findings.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from bookkit.project import add_common_args, load_project, Project  # noqa: E402
from bookkit.segment import segment  # noqa: E402

# --- Spelling variants. Keyed by the variant the project pinned AGAINST. -----
# These are inert unless `language_variant` says which side is wrong, so a
# project pinned to en-GB gets the mirror list instead of 26 false positives.
GB_TO_US = {
    r"\bcolours?\b": "color(s)", r"\bcoloured\b": "colored",
    r"\bbehaviours?\b": "behavior(s)", r"\borganis(e|ed|ing|ation)\b": "organiz-",
    r"\bcentres?\b": "center(s)", r"\banalys(e|ed|ing)\b": "analyz-",
    r"\bcatalogues?\b": "catalog(s)", r"\bwhilst\b": "while",
    r"\bamongst\b": "among", r"\bgrey\b": "gray", r"\bdefence\b": "defense",
    r"\blabell(ed|ing)\b": "label-", r"\bmodell(ed|ing)\b": "model-",
    r"\btravell(ed|ing)\b": "travel-", r"\bcancell(ed|ing)\b": "cancel-",
    r"\bfulfil\b": "fulfill", r"\bprogramme\b": "program",
    r"\brecognis(e|ed|ing)\b": "recogniz-", r"\bnormalis(e|ed|ing)\b": "normaliz-",
    r"\boptimis(e|ed|ing|ation)\b": "optimiz-", r"\bsummaris(e|ed|ing)\b": "summariz-",
    r"\bprioritis(e|ed|ing)\b": "prioritiz-", r"\bspecialis(e|ed|ing)\b": "specializ-",
    r"\blicence\b": "license", r"\bpractis(e|ed|ing)\b": "practic-",
    r"\bmanoeuvre\b": "maneuver", r"\bdialogue box\b": "dialog box",
}

US_TO_GB = {
    r"\bcolors?\b": "colour(s)", r"\bcolored\b": "coloured",
    r"\bbehaviors?\b": "behaviour(s)", r"\borganiz(e|ed|ing|ation)\b": "organis-",
    r"\bcenters?\b": "centre(s)", r"\banalyz(e|ed|ing)\b": "analys-",
    r"\bcatalogs?\b": "catalogue(s)", r"\bgray\b": "grey", r"\bdefense\b": "defence",
    r"\brecogniz(e|ed|ing)\b": "recognis-", r"\bnormaliz(e|ed|ing)\b": "normalis-",
    r"\boptimiz(e|ed|ing|ation)\b": "optimis-", r"\bsummariz(e|ed|ing)\b": "summaris-",
    r"\bdialog box\b": "dialogue box", r"\blicense\b": "licence (noun)",
}

RX_EMDASH_TIGHT = re.compile(r"\S—|—\S")
RX_THOUSANDS = re.compile(r"(?<![\d.,])\d{4,}(?![\d.,%])")
RX_DOUBLE_SPACE = re.compile(r"(?<=\S)  +(?=\S)")
RX_SPACE_BEFORE_PUNCT = re.compile(r"\s+[,.;:!?](?=\s|$)")
RX_REPEATED_WORD = re.compile(r"\b(\w+)\s+\1\b", re.I)

# Title Case heading where the project asked for sentence case. Conservative on
# purpose: 3+ capitalized words in a row, no intervening lowercase to explain it.
RX_TITLE_CASE = re.compile(r"^#{2,6}\s+(?:[A-Z][a-z]+\s+){2,}[A-Z][a-z]+\s*$")

# Glossary term shapes, for deriving the casing watchlist with no config.
GLOSSARY_TERM_RES = [
    re.compile(r"^\s*[-*]\s+\*\*(.+?)\*\*"),
    re.compile(r"^\*\*(.+?)\*\*\s*[—:-]"),
    re.compile(r"^#{2,4}\s+(.+?)\s*$"),
    re.compile(r"^\|\s*\*?\*?([^|*]+?)\*?\*?\s*\|"),
]


@dataclass
class Finding:
    rule: str
    unit: str
    location: str
    found: str
    suggestion: str


@dataclass
class Config:
    language_variant: str = "en-US"
    pins: list[dict] = None
    casing_watch: list[str] = None
    allow: list[str] = None
    sentence_case_headings: bool = True
    thousands_separator: bool = True

    def __post_init__(self):
        self.pins = self.pins or []
        self.casing_watch = self.casing_watch or []
        self.allow = self.allow or []


def load_config(project: Project) -> Config:
    raw = project.load_yaml("bible/lint-config.yaml")
    cfg = Config(
        language_variant=str(raw.get("language_variant")
                             or project.language_variant or "en-US"),
        pins=list(raw.get("pins") or []),
        casing_watch=list(raw.get("casing_watch") or []),
        allow=list(raw.get("allow") or []),
        sentence_case_headings=bool(raw.get("sentence_case_headings", True)),
        thousands_separator=bool(raw.get("thousands_separator", True)),
    )
    for entry in raw.get("forbidden") or []:
        cfg.pins.append({
            "pattern": rf"\b{re.escape(str(entry.get('term', '')))}\b",
            "prefer": entry.get("prefer", ""),
            "why": "forbidden term",
        })
    if not cfg.casing_watch:
        cfg.casing_watch = derive_casing_watch(project)
    return cfg


def derive_casing_watch(project: Project) -> list[str]:
    """Multi-word glossary terms make a good default watchlist.

    The glossary already names the terms the project decided to be consistent
    about, so a project with a glossary gets this check for free. Single words
    are skipped: they collide with ordinary prose too often to be worth it.
    """
    path = project.bible / "glossary.md"
    if not path.exists():
        return []
    terms: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        for rx in GLOSSARY_TERM_RES:
            m = rx.match(line)
            if not m:
                continue
            term = re.sub(r"[`*_]", "", m.group(1)).strip().lower()
            if 2 <= len(term.split()) <= 4 and re.fullmatch(r"[a-z][a-z \-]+", term):
                terms.add(term)
            break
    return sorted(terms)


def strip_code_spans(text: str) -> str:
    """Remove code spans WITHOUT leaving a space.

    Replacing them with " " manufactures exactly the double spaces and
    space-before-punctuation this script then reports: on the first calibration
    run that produced 2,224 false hits out of 2,389. The whitespace rules run on
    the ORIGINAL text; this is only for vocabulary rules.
    """
    return re.sub(r"`[^`]*`", "", text)


def lint(project: Project, cfg: Config) -> list[Finding]:
    out: list[Finding] = []
    allow = [re.compile(p, re.I) for p in cfg.allow]
    variant = cfg.language_variant.strip().lower()
    spelling = US_TO_GB if variant.startswith("en-gb") else (
        GB_TO_US if variant.startswith("en") else {})
    pins = [(re.compile(p["pattern"]), p.get("prefer", ""), p.get("why", "style pin"))
            for p in cfg.pins if p.get("pattern")]

    casing_seen: dict[str, dict[str, list]] = {
        t: defaultdict(list) for t in cfg.casing_watch}
    casing_rx = (re.compile("|".join(re.escape(t) for t in cfg.casing_watch))
                 if cfg.casing_watch else None)

    for path in project.unit_paths:
        rel = project.rel(path)
        for r in segment(path, rel_to=project.root):
            if r.kind in ("code", "blank", "hr"):
                continue
            if any(rx.search(r.text) for rx in allow):
                continue

            loc = f"{rel}:{r.line}"

            if r.kind == "heading":
                if cfg.sentence_case_headings and RX_TITLE_CASE.match(r.text):
                    out.append(Finding("heading_case", r.unit, loc, r.text.strip(),
                                       "project convention is sentence case"))
                continue

            bare = strip_code_spans(r.text)

            for rx, sug in spelling.items():
                for m in re.finditer(rx, bare, re.I):
                    out.append(Finding("spelling_variant", r.unit, loc, m.group(0), sug))

            for rx, prefer, why in pins:
                for m in rx.finditer(bare):
                    out.append(Finding("pin", r.unit, loc, m.group(0),
                                       f"{prefer} ({why})" if prefer else why))

            if RX_EMDASH_TIGHT.search(bare):
                out.append(Finding("em_dash", r.unit, loc,
                                   _ctx(bare, RX_EMDASH_TIGHT), "spaces on both sides"))

            if cfg.thousands_separator:
                for m in RX_THOUSANDS.finditer(bare):
                    # Years carry no thousands separator: on the calibration run
                    # 111 of 111 first-pass hits were "2024" / "2025".
                    if 1900 <= int(m.group(0)) <= 2100:
                        continue
                    # Nor do line references into a source library, which a
                    # grounded book cites constantly ("§'Preceding load' line 7264").
                    pre = bare[max(0, m.start() - 24):m.start()].lower()
                    if re.search(r"\b(line|lines|p\.|pp\.|page|§)\s*$", pre):
                        continue
                    out.append(Finding("thousands", r.unit, loc, m.group(0),
                                       "thousands separator"))

            # Whitespace rules run on ORIGINAL text. Indented blockquotes are
            # quoted code, not prose.
            if not (r.kind == "quote" and re.match(r"^>\s{2,}\S", r.text)):
                for rx, name, sug in (
                    (RX_DOUBLE_SPACE, "double_space", "single space"),
                    (RX_SPACE_BEFORE_PUNCT, "space_punct", "no space before punctuation"),
                    (RX_REPEATED_WORD, "repeated_word", "duplicated word"),
                ):
                    if rx.search(r.text):
                        out.append(Finding(name, r.unit, loc, _ctx(r.text, rx), sug))

            if casing_rx:
                low = bare.lower()
                for m in casing_rx.finditer(low):
                    before = bare[:m.start()].rstrip()
                    # Sentence-initial capitals are legitimate, not drift.
                    if not before or before.endswith((".", "!", "?", ":", "—", ")")):
                        continue
                    casing_seen[m.group(0)][bare[m.start():m.end()]].append(loc)

    out += _casing_findings(casing_seen)
    return out


def _casing_findings(casing_seen: dict[str, dict[str, list]]) -> list[Finding]:
    """Report the MINORITY variant, not every occurrence.

    An even split usually means both spellings are legitimate in different
    contexts, so anything above 40% of the majority is left alone. Reporting all
    variants of a term used 60 times produces a wall of noise nobody reads.
    """
    out: list[Finding] = []
    for _term, variants in casing_seen.items():
        if len(variants) < 2:
            continue
        ranked = sorted(variants.items(), key=lambda kv: -len(kv[1]))
        majority, majority_hits = ranked[0]
        for variant, hits in ranked[1:]:
            if len(hits) > len(majority_hits) * 0.4:
                continue
            for loc in hits:
                out.append(Finding("casing", loc.split(":")[0], loc, variant,
                                   f"majority: '{majority}' ({len(majority_hits)} uses)"))
    return out


def _ctx(text: str, rx: re.Pattern) -> str:
    m = rx.search(text)
    if not m:
        return ""
    a, b = max(0, m.start() - 30), min(len(text), m.end() + 30)
    return "…" + text[a:b].strip() + "…"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Deterministic style and convention lint.")
    add_common_args(ap)
    ap.add_argument("--by-unit", action="store_true", help="Group by unit instead of rule.")
    ap.add_argument("--rule", help="Show one rule only.")
    ap.add_argument("--limit", type=int, default=0, help="Max rows per group.")
    ap.add_argument("--json", metavar="PATH", help="Write findings as JSON.")
    args = ap.parse_args(argv)

    project = load_project(args.root, args.units)
    cfg = load_config(project)
    hits = lint(project, cfg)
    if args.rule:
        hits = [h for h in hits if h.rule == args.rule]

    if not hits:
        print("[lint_style] no findings.")
    else:
        groups: dict[str, list[Finding]] = defaultdict(list)
        for h in hits:
            groups[h.unit if args.by_unit else h.rule].append(h)

        print(f"[lint_style] {len(hits)} finding(s) in "
              f"{len({h.unit for h in hits})} unit(s)\n")
        for key in sorted(groups):
            rows = groups[key]
            print(f"### {key}  ({len(rows)})")
            for h in (rows[:args.limit] if args.limit else rows):
                tag = f"[{h.rule}] " if args.by_unit else ""
                print(f"  {h.location}  {tag}{h.found!r}  ->  {h.suggestion}")
            if args.limit and len(rows) > args.limit:
                print(f"  … and {len(rows) - args.limit} more")
            print()

        per: dict[str, int] = defaultdict(int)
        for h in hits:
            per[h.rule] += 1
        print("by rule:")
        for k, v in sorted(per.items(), key=lambda kv: -kv[1]):
            print(f"  {k:20} {v}")

    if args.json:
        out = Path(args.json)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps({
            "tool": "lint_style",
            "language_variant": cfg.language_variant,
            "casing_watch": cfg.casing_watch,
            "findings": [asdict(h) for h in hits],
        }, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\n[lint_style] findings → {out}")

    # Advisory by design: these are Proofreader inputs, not a gate. A hard gate
    # on prose conventions gets switched off within a week, and then there is no
    # warning either.
    return 0


if __name__ == "__main__":
    sys.exit(main())
