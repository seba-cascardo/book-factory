#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_fixed_defects.py — MG-7: a defect that was fixed does not come back.

## The gap this closes

`bible/do-not-touch.md` protects text that is CORRECT. `scripts/selftest.py`
tests the SCRIPTS. Nothing in the toolkit asserted *"this defective formulation
must not return"*.

Evidence, from the fix pass on the reference book: closing one defect — a chapter
collapsing the three positions of a set modifier into two slots, which took four
independent passes to detect — required inverting a gate assertion by hand and
adding content pins to a linter, because nothing otherwise prevented the wrong
mental model from reappearing in a later edit. A defect that cost four passes to
find should not be able to walk back in silently.

This runs in the deterministic sweep. It costs seconds, it always covers the
whole book, and a reappearance defaults to `critical`.

## Pin the CLAIM, not the code

The trap, and the reason `allow_in` exists at all: **the text that corrects a
defect usually quotes the defective form in order to teach against it.** The
reference fix reads, verbatim:

> *"…with the set inside the outer aggregation's own parens — only the outer sees
> it… That is the one that looks like the fix and is not."*

A literal pin on that expression fires on the fix itself, every round, forever —
and a check that shouts when nothing happened gets switched off.

So the right pin for that defect is not the expression, which appears
legitimately as a counter-example. It is the conceptual frame — `two slots`, `the
outer aggregation's reach` — which can only reappear if somebody reintroduced the
wrong model. Whoever writes the first entry will pin the code; the template says
this, and so does this docstring, because they will read one of the two.

Usage
  python scripts/check_fixed_defects.py
  python scripts/check_fixed_defects.py --json out.json --quiet
  python scripts/check_fixed_defects.py --fail-on critical
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from bookkit.anchors import Block, blocks_for, norm  # noqa: E402
from bookkit.project import Project, add_common_args, as_list, load_project  # noqa: E402

SEVERITIES = ["critical", "major", "minor"]
DEFAULT_SEVERITY = "critical"


@dataclass
class Regression:
    entry: str
    location: str
    severity: str
    pattern: str
    quote: str
    what: str
    fixed_on: str = ""
    detected_by: list[str] = field(default_factory=list)

    def line_repr(self) -> str:
        return (f"{self.severity.upper():<8} {self.location}  [{self.entry}]\n"
                f"         matched `{self.pattern}` — {self.what}\n"
                f"         > {self.quote[:160]}")


def _compile(rule: dict) -> re.Pattern | None:
    pattern = str(rule.get("pattern") or "")
    if not pattern:
        return None
    kind = str(rule.get("kind") or "regex").lower()
    flags = 0 if rule.get("case_sensitive") else re.I
    if kind == "literal":
        return re.compile(re.escape(norm(pattern)), flags)
    try:
        return re.compile(pattern, flags)
    except re.error as exc:
        print(f"[fixed-defects] BAD PATTERN {pattern!r}: {exc}")
        return None


def _exempt(blocks: list[Block], i: int, allow: list[str]) -> str:
    """Is this hit inside a passage the entry explicitly allows?

    The window is the matching block plus its immediate neighbours. A teaching
    passage sets the counter-example up in one paragraph and names it in the
    next, and pinning the anchor to the exact paragraph would make `allow_in`
    fragile in the one situation it exists for.
    """
    window = " ".join(b.text for b in blocks[max(0, i - 1):i + 2])
    for a in allow:
        if a and norm(a) in window:
            return a
    return ""


def scan(project: Project, entries: list[dict]) -> tuple[list[Regression], list[dict]]:
    findings: list[Regression] = []
    exemptions: list[dict] = []

    index = {project.rel(p): (p.stem, blocks_for(p, project.root))
             for p in project.unit_paths}

    for entry in entries:
        eid = str(entry.get("id") or "(unnamed)")
        severity = str(entry.get("severity_if_back") or DEFAULT_SEVERITY)
        if severity not in SEVERITIES:
            severity = DEFAULT_SEVERITY
        # as_list: `scope: ch-11` is one unit, not five letters.
        scope = {str(s) for s in as_list(entry.get("scope"))}
        allow = [str(a.get("anchor") or "") if isinstance(a, dict) else str(a)
                 for a in as_list(entry.get("allow_in"))]
        rules = [(r, _compile(r)) for r in as_list(entry.get("forbid")) if isinstance(r, dict)]

        for rel, (stem, blocks) in sorted(index.items()):
            # Empty scope = the whole book. A defect fixed in two chapters can
            # reappear in a third, and scoping it to where it was found would
            # miss exactly that.
            if scope and stem not in scope and rel not in scope:
                continue
            for i, block in enumerate(blocks):
                for raw, rx in rules:
                    if rx is None:
                        continue
                    m = rx.search(block.text)
                    if not m:
                        continue
                    reason = _exempt(blocks, i, allow)
                    if reason:
                        exemptions.append({
                            "entry": eid, "location": f"{rel}:{block.line}",
                            "pattern": raw.get("pattern"), "allowed_by": reason})
                        continue
                    findings.append(Regression(
                        entry=eid, location=f"{rel}:{block.line}", severity=severity,
                        pattern=str(raw.get("pattern")),
                        quote=block.text, what=str(entry.get("what") or ""),
                        fixed_on=str(entry.get("fixed_on") or ""),
                        detected_by=[str(d) for d in as_list(entry.get("detected_by"))],
                    ))
    return findings, exemptions


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="MG-7 — a fixed defect must not reappear.")
    add_common_args(ap)
    ap.add_argument("--registry", default="bible/fixed-defects.yaml")
    ap.add_argument("--json", metavar="PATH", help="Write the result as JSON.")
    ap.add_argument("--quiet", action="store_true", help="Problems only.")
    ap.add_argument("--fail-on", choices=[*SEVERITIES, "never"], default="never",
                    help="Exit 1 at or above this severity (default never — the "
                         "gate reads the JSON and decides).")
    args = ap.parse_args(argv)

    project = load_project(args.root, args.units)
    reg_path = project.root / args.registry
    doc = project.load_yaml(args.registry)
    entries = [e for e in as_list(doc.get("defects")) if isinstance(e, dict)]

    if not reg_path.exists():
        if not args.quiet:
            print(f"[fixed-defects] no {args.registry} — nothing pinned yet. Entries "
                  f"are born when the gate marks a critical/major finding resolved; "
                  f"see templates/fixed-defects.yaml.")
        _write(args.json, [], [], 0)
        return 0

    findings, exemptions = scan(project, entries)
    counts = {s: sum(1 for f in findings if f.severity == s) for s in SEVERITIES}

    if not args.quiet:
        for f in findings:
            print(f.line_repr())
        if findings:
            print()
    print(f"[fixed-defects] {len(entries)} entry(ies) · {counts['critical']} critical · "
          f"{counts['major']} major · {counts['minor']} minor · "
          f"{len(exemptions)} allowed by an `allow_in` anchor")
    if findings and not args.quiet:
        print("[fixed-defects] a reappearance is a REGRESSION of a confirmed defect, "
              "not a new finding. Check the entry's `allow_in` before fixing the "
              "prose: text that teaches against the wrong form is supposed to quote "
              "it, and pinning the code instead of the claim is the usual cause.")

    _write(args.json, findings, exemptions, len(entries))
    if args.json and not args.quiet:
        print(f"[fixed-defects] result -> {args.json}")

    if args.fail_on == "never":
        return 0
    threshold = SEVERITIES.index(args.fail_on)
    return 1 if any(SEVERITIES.index(f.severity) <= threshold for f in findings) else 0


def _write(path: str | None, findings: list[Regression], exemptions: list[dict],
           n_entries: int) -> None:
    if not path:
        return
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({
        "check": "MG-7",
        "tool": "check_fixed_defects",
        "entries": n_entries,
        "counts": {s: sum(1 for f in findings if f.severity == s) for s in SEVERITIES},
        "findings": [asdict(f) for f in findings],
        "exemptions": exemptions,
    }, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
