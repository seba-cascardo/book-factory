#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""validate_claim_index.py — keeps the concept × location matrix honest.

## The problem this solves

A fix landed in one passage and left its twin, seventeen lines apart in the same
chapter, asserting the opposite. The chapter contradicted itself for seventeen
days and survived a full audit. Nobody knew the first passage had siblings.

`bible/claim-index.yaml` records, per concept, which passage is CANONICAL and
which ones repeat it. This validator keeps that record true, and — the part that
actually prevents the defect — tells you who else to look at when you edit one.

## Why this does not go stale the way a checklist does

Three structural differences, not differences of discipline:

1. **It is an index of pointers, not a store of claims.** It cannot "disagree"
   with the book: either the fingerprint is in the text, or the validator says so.
2. **It has no state field a human has to remember to tick.** No `[ ]` / `[x]`.
   All state is derived from the text and from git blame.
3. **Something reads it automatically** — the build preflight, the manuscript
   gate, and the post-edit hook. A checklist that only a human reads every couple
   of weeks is a checklist that is wrong for a couple of weeks.

## Verdicts

  OK           the fingerprint is still on the recorded line
  MOVED        the fingerprint is on ANOTHER line → auto-repaired with --fix
  CHANGED      the passage was EDITED → every sibling is suspect; emits PROPAGATE.
               This is the incomplete-fix detector, permanently on.
  GONE         the passage no longer exists → dead entry
  MULTI-CANON  more than one CANON for a concept → invariant violated
  NO-CANON     no CANON at all → invariant violated
  BAD-ROLE     unknown role
  BAD-LOC      unparseable location

Usage
  python scripts/validate_claim_index.py            # report
  python scripts/validate_claim_index.py --fix      # also auto-repair MOVED
  python scripts/validate_claim_index.py --quiet    # problems only (build preflight)
  python scripts/validate_claim_index.py --json out.json
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("Missing PyYAML. Install with: pip install pyyaml")

sys.path.insert(0, str(Path(__file__).resolve().parent))

from bookkit.project import add_common_args, load_project  # noqa: E402
from bookkit.segment import paragraphs, segment  # noqa: E402
from bookkit.textmetrics import fingerprint  # noqa: E402

ROLES = {"CANON", "repeats", "derives", "qualifies", "summary", "example", "crossref"}


def load_fingerprints(project) -> dict[str, dict[str, int]]:
    """relative path → {fingerprint: first line}. One pass over the units."""
    idx: dict[str, dict[str, int]] = {}
    for path in project.unit_paths:
        rel = project.rel(path)
        fps: dict[str, int] = {}
        # Same unit of analysis as build_concept_dossier, or the fingerprints
        # would never match and every site would read as CHANGED.
        for r in paragraphs(segment(path, rel_to=project.root)):
            if r.kind in ("code", "blank", "hr"):
                continue
            fps.setdefault(fingerprint(r.text), r.line)
        idx[rel] = fps
    return idx


def parse_loc(loc: str) -> tuple[str, int]:
    path, _, line = str(loc).rpartition(":")
    return path, int(line)


def validate(project, doc: dict, fix: bool) -> dict:
    concepts = doc.get("concepts") or {}
    idx = load_fingerprints(project)

    counts: dict[str, int] = defaultdict(int)
    problems: list[str] = []
    propagate: list[dict] = []
    moved: list[str] = []
    repaired = 0

    for cid, entry in sorted(concepts.items()):
        sites = entry.get("sites") or []
        roles = [s.get("role") for s in sites]

        n_canon = roles.count("CANON")
        if n_canon > 1:
            problems.append(f"MULTI-CANON  {cid}: {n_canon} passages marked CANON")
            counts["MULTI-CANON"] += 1
        elif n_canon == 0 and sites:
            problems.append(f"NO-CANON     {cid}: no passage marked CANON")
            counts["NO-CANON"] += 1
        for r in roles:
            if r not in ROLES:
                problems.append(f"BAD-ROLE     {cid}: unknown role {r!r}")
                counts["BAD-ROLE"] += 1

        changed_here: list[str] = []

        for site in sites:
            loc = site.get("location", "")
            fp = site.get("fingerprint", "")
            try:
                rel, line = parse_loc(loc)
            except ValueError:
                problems.append(f"BAD-LOC      {cid}: unreadable location {loc!r}")
                counts["BAD-LOC"] += 1
                continue

            fps = idx.get(rel)
            if fps is None:
                problems.append(f"GONE         {cid} {loc}: {rel} is not in the unit set")
                counts["GONE"] += 1
                continue

            actual = fps.get(fp)
            if actual == line:
                counts["OK"] += 1
            elif actual is not None:
                counts["MOVED"] += 1
                moved.append(f"MOVED        {cid} {loc} -> :{actual}")
                if fix:
                    site["location"] = f"{rel}:{actual}"
                    repaired += 1
            else:
                counts["CHANGED"] += 1
                problems.append(
                    f"CHANGED      {cid} {loc} [{site.get('role')}]: the text was edited")
                changed_here.append(loc)

        # The incomplete-fix detector. When a passage changes, the siblings that
        # carry the same claim are suspect until someone looks at them.
        #
        # It propagates ONLY to `related` (same sub-claim), never to every site
        # of the concept. A PROPAGATE that tells you to review 65 passages gets
        # ignored, and an ignored warning is precisely how the checklist this
        # replaces went stale. When a site declares no `related`, it falls back
        # to siblings in the same file — still bounded.
        for site in sites:
            if site.get("location") not in changed_here:
                continue
            rel_list = list(site.get("related") or [])
            if not rel_list:
                same_file = str(site["location"]).rpartition(":")[0]
                rel_list = [s["location"] for s in sites
                            if str(s.get("location", "")).startswith(same_file + ":")
                            and s["location"] not in changed_here]
            rel_list = [r for r in rel_list if r not in changed_here]
            if rel_list:
                propagate.append({
                    "concept": cid,
                    "changed": site["location"],
                    "role": site.get("role"),
                    "review": rel_list,
                    "do_not_touch": bool(entry.get("do_not_touch")),
                    "verified_against": entry.get("verified_against"),
                })

    return {
        "counts": dict(counts),
        "problems": problems,
        "moved": moved,
        "propagate": propagate,
        "repaired": repaired,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Validate the claim index against the text.")
    add_common_args(ap)
    ap.add_argument("--index-path", default="bible/claim-index.yaml")
    ap.add_argument("--fix", action="store_true", help="Auto-repair MOVED locations.")
    ap.add_argument("--quiet", action="store_true", help="Problems only.")
    ap.add_argument("--json", metavar="PATH", help="Write the result as JSON.")
    ap.add_argument("--fail-on-changed", action="store_true",
                    help="Exit 1 when a passage was edited. OFF by default, on purpose "
                         "— see the note at the bottom of this file.")
    args = ap.parse_args(argv)

    project = load_project(args.root, args.units)
    index_path = project.root / args.index_path

    if not index_path.exists():
        if not args.quiet:
            print(f"[claim-index] {args.index_path} does not exist yet — nothing to "
                  f"validate. Generate it with "
                  f"`build_concept_dossier.py --emit-index`.")
        return 0

    doc = yaml.safe_load(index_path.read_text(encoding="utf-8")) or {}
    result = validate(project, doc, args.fix)

    if args.fix and result["repaired"]:
        index_path.write_text(
            yaml.safe_dump(doc, allow_unicode=True, sort_keys=False, width=200),
            encoding="utf-8")

    if not args.quiet:
        counts = result["counts"]
        print("[claim-index] " + ("  ".join(f"{k}={v}" for k, v in sorted(counts.items()))
                                  or "empty"))
        if result["repaired"]:
            print(f"[claim-index] {result['repaired']} location(s) auto-repaired")
        for m in result["moved"]:
            print(m + ("" if args.fix else "  (use --fix)"))

    for p in result["problems"]:
        print(p)

    for entry in result["propagate"]:
        guard = ""
        if entry["do_not_touch"]:
            guard = "  [DO-NOT-TOUCH concept — check the anchor before editing]"
        elif entry["verified_against"]:
            guard = f"  [verified against {entry['verified_against']}]"
        print(f"PROPAGATE    {entry['concept']}: {entry['changed']} changed "
              f"[{entry['role']}] -> review {', '.join(entry['review'])}{guard}")

    n = len(result["problems"]) + len(result["propagate"])
    if n:
        print(f"\n[claim-index] {n} thing(s) to look at. This is a WARNING; it does "
              f"not break the build.")
    elif not args.quiet:
        print("[claim-index] consistent.")

    if args.json:
        out = Path(args.json)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        if not args.quiet:
            print(f"[claim-index] result → {out}")

    # Exit 0 by default even with findings. A hard gate on prose gets switched
    # off within a week, and then there is no warning either. `--fail-on-changed`
    # exists for a CI job that WANTS to block, but the pipeline does not use it:
    # the manuscript gate reads the JSON and decides.
    if args.fail_on_changed and result["counts"].get("CHANGED"):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
