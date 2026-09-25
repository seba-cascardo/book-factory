#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_role_diff.py — role contracts verified by diff, not self-reported.

Why this exists. Three agents have contracts that are about HOW MUCH they change,
and until v3.4 each one reported its own compliance:

  - The **Editor** is structural: it reorders, cuts and adds transitions. When it
    starts writing prose, two agents own the same sentences and fixes collide.
    Violation: added words beyond transitions (`added_words_ratio > 0.02`).
  - The **Humanizer** has a line-repair budget (literary ~3%). A chapter that
    needs more than that has a draft problem, not a prose problem, and the fix
    belongs to the Writer. `over_budget` when `touched_ratio > budget`.
  - The **Proofreader** runs before human review, so the human approves the text
    that ships; every changed sentence is listed for them (`changes`). Anything
    that is not mechanical (a sentence added, removed, or rewritten past 80%
    similarity) is a violation.

The unit of comparison is the sentence (`¿…?`, `¡…!` and raya lines handled, HTML
comments ignored). A moved sentence is a move, not an add plus a delete, so an
Editor that only reorders scores zero added prose.

Definitions (words_before = words in the BEFORE text):
  added_words_ratio = (words of added sentences + words inserted into modified
                       sentences) / words_before
  touched_ratio     = (words of each modified sentence, the longer of its two
                       versions + words of removed and added sentences) / words_before

Usage
  python scripts/check_role_diff.py --role editor --before drafts/unit-03/draft.md \\
      --after drafts/unit-03/edit.md
  python scripts/check_role_diff.py --role humanizer --before E --after H --budget 0.03 \\
      --json drafts/unit-03/role-diff-humanizer-c1.json

Budget default: `--budget`, else `literary.humanizer_budget` (literary, default
0.03) or `pipeline.humanizer_budget` (nonfiction, default: none — report only).

Exit codes: 0; 1 with --fail-on-violation when a violation is found; 2 input missing.
"""

from __future__ import annotations

import argparse
import difflib
import re
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from bookkit import lexicon as L  # noqa: E402

ROLES = ("editor", "humanizer", "proofreader")
EDITOR_ADDED_LIMIT = 0.02
LITERARY_BUDGET = 0.03
PAIR_MIN = 0.5            # a replaced sentence at least this similar is "modified"
MECHANICAL_MIN = 0.8      # proofreader: below this a change is not mechanical
_FENCE = re.compile(r"^\s*(`{3,}|~{3,})")


@dataclass
class Sent:
    line: int
    text: str
    kind: str   # prose | heading | code

    @property
    def norm(self) -> str:
        return re.sub(r"\s+", " ", self.text).strip()

    @property
    def nwords(self) -> int:
        return len(L.words(self.text))


def sentences(text: str) -> list[Sent]:
    """Sentence units of a markdown text: prose sentences, headings, code lines."""
    out: list[Sent] = []
    para: list[tuple[int, str]] = []
    in_code = False

    def flush():
        if not para:
            return
        first = para[0][0]
        joined = " ".join(t.strip() for _, t in para)
        for s in L.split_sentences(joined):
            out.append(Sent(first, s, "prose"))
        para.clear()

    for n, raw in enumerate(L.strip_comments(text).splitlines(), start=1):
        if _FENCE.match(raw):
            flush()
            in_code = not in_code
            continue
        if in_code:
            if raw.strip():
                out.append(Sent(n, raw.rstrip(), "code"))
            continue
        s = raw.strip()
        if not s:
            flush()
            continue
        if s.startswith("#"):
            flush()
            out.append(Sent(n, s, "heading"))
            continue
        # A raya / list / table / quote line is its own paragraph.
        if s[0] in "—–-*+|>" or re.match(r"\d+[.)]\s", s):
            flush()
            para.append((n, s))
            flush()
            continue
        para.append((n, s))
    flush()
    return out


def _containment(old: str, new: str) -> float:
    """Share of the old sentence's words that survive, in order, in the new one."""
    wa, wb = [w.lower() for w in L.words(old)], [w.lower() for w in L.words(new)]
    if not wa:
        return 0.0
    sm = difflib.SequenceMatcher(None, wa, wb, autojunk=False)
    kept = sum(bl.size for bl in sm.get_matching_blocks())
    score = kept / len(wa)
    return score if score >= 0.8 else 0.0


def _inserted_words(a: str, b: str) -> int:
    wa, wb = L.words(a), L.words(b)
    sm = difflib.SequenceMatcher(None, wa, wb, autojunk=False)
    return sum(j2 - j1 for op, _i1, _i2, j1, j2 in sm.get_opcodes() if op in ("insert", "replace"))


def diff(before_text: str, after_text: str, role: str, budget: float | None) -> dict:
    a, b = sentences(before_text), sentences(after_text)
    sm = difflib.SequenceMatcher(None, [s.norm for s in a], [s.norm for s in b], autojunk=False)
    added: list[Sent] = []
    removed: list[Sent] = []
    modified: list[tuple[Sent, Sent, float]] = []
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            continue
        if op == "delete":
            removed += a[i1:i2]
            continue
        if op == "insert":
            added += b[j1:j2]
            continue
        # replace: pair each old sentence with its most similar new one, in order
        pool = list(range(j1, j2))
        for i in range(i1, i2):
            best, score, key = None, 0.0, 0.0
            for j in pool:
                r = difflib.SequenceMatcher(None, a[i].norm, b[j].norm, autojunk=False).ratio()
                k = max(r, _containment(a[i].text, b[j].text))
                if k > key:
                    best, score, key = j, r, k
            # Similar enough, or the old sentence survives inside the new one
            # ("La casa estaba vacía." → "La casa estaba vacía y fría …").
            if best is not None and key >= PAIR_MIN:
                modified.append((a[i], b[best], score))
                pool.remove(best)
            else:
                removed.append(a[i])
        added += [b[j] for j in pool]

    # A sentence deleted in one place and inserted verbatim elsewhere was moved.
    moved: list[tuple[Sent, Sent]] = []
    for s in list(added):
        twin = next((r for r in removed if r.norm == s.norm), None)
        if twin is not None:
            moved.append((twin, s))
            removed.remove(twin)
            added.remove(s)

    words_before = sum(s.nwords for s in a) or 0
    words_after = sum(s.nwords for s in b)
    added_words = sum(s.nwords for s in added) + sum(_inserted_words(x.text, y.text)
                                                     for x, y, _ in modified)
    touched = (sum(max(x.nwords, y.nwords) for x, y, _ in modified) + sum(s.nwords for s in removed)
               + sum(s.nwords for s in added))
    added_ratio = round(added_words / words_before, 4) if words_before else 0.0
    touched_ratio = round(touched / words_before, 4) if words_before else 0.0

    changes = (
        [{"kind": "modified", "before": x.text, "after": y.text, "line_before": x.line,
          "line_after": y.line, "similarity": round(r, 3)} for x, y, r in modified]
        + [{"kind": "added", "before": None, "after": s.text, "line_before": None,
            "line_after": s.line, "similarity": 0.0} for s in added]
        + [{"kind": "removed", "before": s.text, "after": None, "line_before": s.line,
            "line_after": None, "similarity": 0.0} for s in removed]
        + [{"kind": "moved", "before": x.text, "after": y.text, "line_before": x.line,
            "line_after": y.line, "similarity": 1.0} for x, y in moved]
    )
    changes.sort(key=lambda c: (c["line_after"] or c["line_before"] or 0, c["kind"]))

    violations: list[str] = []
    over = False
    if role == "editor" and added_ratio > EDITOR_ADDED_LIMIT:
        violations.append(
            f"editor added prose: {added_ratio:.1%} of words added (limit "
            f"{EDITOR_ADDED_LIMIT:.0%} for transitions) — prose belongs to the Writer "
            f"and the Humanizer")
    if role == "humanizer" and budget is not None and touched_ratio > budget:
        over = True
        violations.append(
            f"humanizer over budget: touched {touched_ratio:.1%} of words (budget "
            f"{budget:.0%}) — route the unit to the Writer")
    if role == "proofreader":
        for c in changes:
            if c["kind"] in ("added", "removed"):
                violations.append(f"proofreader {c['kind']} a sentence (line "
                                  f"{c['line_after'] or c['line_before']}): not mechanical")
            elif c["kind"] == "modified" and c["similarity"] < MECHANICAL_MIN:
                violations.append(f"proofreader rewrote line {c['line_after']} "
                                  f"(similarity {c['similarity']}): not mechanical")

    return {
        "role": role,
        "words_before": words_before,
        "words_after": words_after,
        "sentences_before": len(a),
        "sentences_added": len(added),
        "sentences_removed": len(removed),
        "sentences_modified": len(modified),
        "sentences_moved": len(moved),
        "added_words_ratio": added_ratio,
        "touched_ratio": touched_ratio,
        "budget": budget,
        "over_budget": over,
        "violations": violations,
        "changes": changes,
    }


def default_budget(root: Path | None) -> float | None:
    """Literary: `literary.humanizer_budget` (0.03). Nonfiction: `pipeline.humanizer_budget`
    or None — the nonfiction Humanizer's scope is wider, so it reports unless the
    project sets a number."""
    if root is None or not (root / "bible" / "meta.yaml").exists():
        return None
    meta = L.load_meta(root)
    if L.profile_of(meta) == "book-literary":
        val = L.meta_get(meta, "literary.humanizer_budget", LITERARY_BUDGET)
    else:
        val = L.meta_get(meta, "pipeline.humanizer_budget")
    return None if val is None else float(val)


def diff_files(before: Path, after: Path, role: str, budget: float | None) -> dict:
    result = diff(L.read_text(before), L.read_text(after), role, budget)
    result["before"] = before.as_posix()
    result["after"] = after.as_posix()
    return result


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Verify a role's contract by sentence diff.")
    ap.add_argument("--root", default=None,
                    help="Project root, for the budget default (default: nearest "
                         "ancestor with bible/meta.yaml).")
    ap.add_argument("--role", required=True, choices=ROLES)
    ap.add_argument("--before", required=True, help="Text the agent received.")
    ap.add_argument("--after", required=True, help="Text the agent produced.")
    ap.add_argument("--budget", type=float, default=None,
                    help="Humanizer touched-ratio budget, e.g. 0.03.")
    ap.add_argument("--json", metavar="OUT", help="Write the result as JSON.")
    ap.add_argument("--fail-on-violation", action="store_true",
                    help="Exit 1 when the role broke its contract.")
    args = ap.parse_args(argv)

    root = L.find_root(args.root)
    before, after = L.at_root(root, args.before), L.at_root(root, args.after)
    for p in (before, after):
        if not p.exists():
            print(f"[check_role_diff] missing: {p}", file=sys.stderr)
            return 2
    budget = args.budget if args.budget is not None else (
        default_budget(root) if args.role == "humanizer" else None)
    r = diff_files(before, after, args.role, budget)
    print(f"[check_role_diff] {r['role']}: {r['words_before']} words before · "
          f"+{r['sentences_added']} −{r['sentences_removed']} ~{r['sentences_modified']} "
          f"↕{r['sentences_moved']} sentences · added {r['added_words_ratio']:.1%} · "
          f"touched {r['touched_ratio']:.1%}"
          + (f" (budget {r['budget']:.0%})" if r["budget"] is not None else ""))
    for v in r["violations"]:
        print(f"  VIOLATION {v}")
    if args.role == "proofreader":
        for c in r["changes"]:
            print(f"  [{c['kind']}] {c['before']!r} → {c['after']!r}")
    if args.json:
        out = L.write_json(L.at_root(root, args.json), r)
        print(f"[check_role_diff] result → {out}")
    return 1 if (args.fail_on_violation and r["violations"]) else 0


if __name__ == "__main__":
    sys.exit(main())
