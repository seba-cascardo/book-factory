#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""extract_code_corpus.py — pull every code block out of the book, grouped.

Two uses:

  1. **Verification-plan seeding (MG-6).** When a validation surface has no real runner,
     the skill owes a verification plan as a first-class deliverable. This produces its
     raw material: every snippet, with its location, its caption and its
     surrounding heading, grouped so a human can see the shape of what was never
     executed.
  2. **Scale, plainly stated.** "3,200 lines of code verified by reasoning
     against PDFs" is a sentence that changes a decision. The count is the
     argument for buying a sandbox.

Grouping is by artifact type, and the classification patterns come from
`bible/audit-config.yaml → code_kinds` so this is not tied to any one language:

    code_kinds:
      load_script:    ["^\\\\s*(LOAD|SELECT)\\\\b", "\\\\bRESIDENT\\\\b"]
      set_analysis:   ["\\\\{<.*>\\\\}"]
      security:       ["\\\\bSECTION ACCESS\\\\b"]

With no config, blocks group by their fence language tag, which is a reasonable
default and needs nothing.

Usage
  python scripts/extract_code_corpus.py                 # summary table
  python scripts/extract_code_corpus.py --out reviews/verification-plan
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from bookkit.project import Project, add_common_args, load_project  # noqa: E402
from bookkit.segment import code_blocks, prev_prose, segment  # noqa: E402


def classify(body: str, lang: str, patterns: dict[str, list[re.Pattern]]) -> str:
    for kind, pats in patterns.items():
        if any(p.search(body) for p in pats):
            return kind
    return lang.strip() or "untagged"


def load_patterns(project: Project) -> dict[str, list[re.Pattern]]:
    raw = (project.load_yaml("bible/audit-config.yaml").get("code_kinds") or {})
    out: dict[str, list[re.Pattern]] = {}
    for kind, pats in raw.items():
        compiled = []
        for p in (pats if isinstance(pats, list) else [pats]):
            try:
                compiled.append(re.compile(str(p), re.I | re.M))
            except re.error as exc:
                print(f"[corpus] bad pattern for {kind}: {p!r} ({exc}) — skipped")
        if compiled:
            out[kind] = compiled
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Extract the book's code corpus.")
    add_common_args(ap)
    ap.add_argument("--out", default=None, help="Write corpus-<kind>.md files here.")
    ap.add_argument("--min-lines", type=int, default=1,
                    help="Skip blocks shorter than this (default 1).")
    args = ap.parse_args(argv)

    project = load_project(args.root, args.units)
    patterns = load_patterns(project)

    by_kind: dict[str, list[dict]] = defaultdict(list)
    total_lines = 0

    for path in project.unit_paths:
        rel = project.rel(path)
        recs = segment(path, rel_to=project.root)
        by_line = {r.line: r for r in recs}
        for start, end, lang, body in code_blocks(recs):
            n_lines = len(body.splitlines())
            if n_lines < args.min_lines:
                continue
            total_lines += n_lines
            caption = prev_prose(by_line, start)
            head = by_line.get(start)
            by_kind[classify(body, lang, patterns)].append({
                "loc": f"{rel}:{start}-{end}",
                "unit": path.stem,
                "lines": n_lines,
                "lang": lang,
                "heading": head.heading_path if head else "",
                "caption": caption.text if caption else "",
                "body": body,
            })

    n_blocks = sum(len(v) for v in by_kind.values())
    print(f"[corpus] {n_blocks} code block(s), {total_lines:,} line(s) across "
          f"{len(project.unit_paths)} unit(s)\n")
    print(f"{'kind':24} {'blocks':>7} {'lines':>8}  units")
    print("-" * 72)
    for kind, blocks in sorted(by_kind.items(), key=lambda kv: -sum(
            b["lines"] for b in kv[1])):
        units = sorted({b["unit"] for b in blocks})
        print(f"{kind:24} {len(blocks):>7} {sum(b['lines'] for b in blocks):>8}  "
              f"{len(units)} unit(s)")

    if not args.out:
        return 0

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    for kind, blocks in sorted(by_kind.items()):
        L = [f"# Code corpus — {kind}", "",
             f"{len(blocks)} block(s), {sum(b['lines'] for b in blocks):,} line(s).", "",
             "Every block below shipped in the book. If the validation surface for this "
             "kind has no runner, none of it was ever executed — it was verified by "
             "reasoning against documentation, which is not the same thing.", ""]
        for b in sorted(blocks, key=lambda b: (b["unit"], b["loc"])):
            L.append(f"## {b['loc']}  ({b['lines']} lines)")
            L += [f"> {b['heading']}", ""]
            if b["caption"]:
                L += [f"*(caption)* {b['caption']}", ""]
            L += [f"```{b['lang']}", b["body"], "```", ""]
        (out_dir / f"corpus-{kind}.md").write_text("\n".join(L), encoding="utf-8")

    print(f"\n[corpus] {len(by_kind)} file(s) → {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
