#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""resolve_anchors.py — keep every persisted reference pointing at its passage.

## What this is for

`bible/claim-index.yaml` already survives edits: it is keyed by fingerprint, so a
passage that moves is repaired and a passage that changes flags its siblings.
Everything else that names a passage was still keyed on a line number —
`bible/do-not-touch.md`, the `location` and `other_sites` of gate findings, the
scope of a fixed-defect entry.

MEASURED: during one day of fixes on the reference book those references broke
three times, and **two of the three breaks were caused by ADDING a section**, not
by a defect. Everything below an insertion shifts at once. A check that shouts
when nothing happened is a check somebody turns off, and then it is not there for
the time something does happen.

## What it reports

    OK          the anchor is at the recorded line
    DRIFT       the anchor moved — repairable with --heal
    EDITED      the anchor is gone: the passage was CHANGED, not moved
    AMBIGUOUS   the anchor matches several passages — lengthen it
    NO-ANCHOR   the reference has only a line number and will go stale
    NO-FILE     the file the reference names is not in the unit set

`EDITED` is the one that earns the module. A line number cannot tell you whether
a passage moved or was rewritten, and those need opposite responses: one is
bookkeeping, the other means the thing the reference protected may be gone.

## --heal

Rewrites stale line numbers from the anchors, so a fix pass ends with one command
instead of hand-maintenance. `--heal` only ever touches `DRIFT`: an `EDITED`
reference is not repaired, because repairing it would quietly re-point a
DO-NOT-TOUCH anchor at text nobody verified.

Usage
  python scripts/resolve_anchors.py                         # report everything
  python scripts/resolve_anchors.py --heal                  # repair DRIFT in place
  python scripts/resolve_anchors.py --findings reviews/manuscript-gate-*/round-1/findings
  python scripts/resolve_anchors.py --json out.json --quiet
"""

from __future__ import annotations

import argparse
import glob as _glob
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from bookkit.anchors import (  # noqa: E402
    AnchorResult, anchor_from_quote, blocks_for, resolve_anchor,
)
from bookkit.project import Project, add_common_args, load_project  # noqa: E402
from bookkit.textio import read_text  # noqa: E402

# `### \`final/unit-07.md:220\` — the optimized/standard hierarchy`
DNT_HEADING = re.compile(r"^(###\s+`)([^`:]+):(\d+)(`.*)$")
# `**Anchor:** "or in the outer aggregation's parens before the"`
DNT_ANCHOR = re.compile(r"^\*\*Anchor:\*\*\s*[\"“]?(.+?)[\"”]?\s*$")


def _blocks_index(project: Project) -> dict[str, list]:
    return {project.rel(p): blocks_for(p, project.root) for p in project.unit_paths}


def _row(source: str, ref: str, res: AnchorResult, recorded: int | None) -> dict:
    return {"source": source, "reference": ref, "status": res.status,
            "recorded_line": recorded, "found_line": res.line, "detail": res.detail}


# ---------------------------------------------------------------------------
# bible/do-not-touch.md
# ---------------------------------------------------------------------------


def check_do_not_touch(project: Project, index: dict[str, list],
                       heal: bool) -> tuple[list[dict], int]:
    """Anchors first, line numbers second.

    The template already asked for a verbatim quote of the SOURCE that settles a
    claim. What it did not carry was a quote of the BOOK passage being protected,
    which is what an anchor has to be: the source quote lives in another file and
    cannot locate anything here.
    """
    path = project.root / "bible" / "do-not-touch.md"
    rows: list[dict] = []
    if not path.exists():
        return rows, 0

    lines = read_text(path).splitlines()
    repaired = 0
    pending: list[tuple[int, str, int]] = []   # (heading index, rel, recorded line)

    for i, line in enumerate(lines):
        m = DNT_HEADING.match(line)
        if m:
            pending.append((i, m.group(2), int(m.group(3))))
            continue
        a = DNT_ANCHOR.match(line.strip())
        if not a or not pending:
            continue
        idx, rel, recorded = pending.pop()
        anchor = a.group(1)
        blocks = index.get(rel)
        if blocks is None:
            rows.append(_row("do-not-touch", f"{rel}:{recorded}",
                             AnchorResult("NO-FILE", None,
                                          f"{rel} is not in the unit set"), recorded))
            continue
        res = resolve_anchor(blocks, recorded, anchor)
        rows.append(_row("do-not-touch", f"{rel}:{recorded}", res, recorded))
        if heal and res.stale and res.line:
            h = DNT_HEADING.match(lines[idx])
            lines[idx] = f"{h.group(1)}{rel}:{res.line}{h.group(4)}"
            repaired += 1

    # A heading with no `**Anchor:**` line under it is the state this whole
    # module exists to retire — report it rather than passing it silently.
    for idx, rel, recorded in pending:
        rows.append(_row("do-not-touch", f"{rel}:{recorded}",
                         AnchorResult("NO-ANCHOR", recorded,
                                      "no `**Anchor:**` line under this entry — add "
                                      "a verbatim substring of the protected passage"),
                         recorded))

    if heal and repaired:
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return rows, repaired


# ---------------------------------------------------------------------------
# gate findings
# ---------------------------------------------------------------------------


def _passage_refs(finding: dict):
    """Yield `(label, container, key)` for every located passage in a finding."""
    for key in ("p1", "p2", "instance"):
        node = finding.get(key)
        if isinstance(node, dict) and node.get("location"):
            yield key, node, "location"


def check_findings(paths: list[Path], index: dict[str, list],
                   heal: bool) -> tuple[list[dict], int]:
    rows: list[dict] = []
    repaired = 0

    for fpath in paths:
        try:
            doc = json.loads(read_text(fpath))
        except (json.JSONDecodeError, OSError) as exc:
            rows.append(_row(fpath.name, "(file)",
                             AnchorResult("NO-FILE", None, str(exc)), None))
            continue
        touched = False

        for finding in (doc.get("findings") or []):
            for label, node, key in _passage_refs(finding):
                loc = str(node.get(key) or "")
                rel, _, ln = loc.rpartition(":")
                if not ln.isdigit():
                    continue
                recorded = int(ln)
                # A finding already carries a VERBATIM quote. Use it when no
                # explicit anchor was written: the cheapest anchor is the one
                # the schema already required.
                anchor = node.get("anchor") or anchor_from_quote(node.get("quote", ""))
                blocks = index.get(rel)
                if blocks is None:
                    rows.append(_row(fpath.name, f"{label} {loc}",
                                     AnchorResult("NO-FILE", None,
                                                  f"{rel} is not in the unit set"),
                                     recorded))
                    continue
                res = resolve_anchor(blocks, recorded, anchor)
                rows.append(_row(fpath.name, f"{label} {loc}", res, recorded))
                if heal and res.stale and res.line:
                    node[key] = f"{rel}:{res.line}"
                    node.setdefault("anchor", anchor)
                    touched = True
                    repaired += 1

            # other_sites: a plain string carries no anchor, so it can only be
            # reported, never healed. The object form is what the schema now
            # asks for, and it is the only form that survives an insertion.
            sites = finding.get("other_sites") or []
            for pos, site in enumerate(sites):
                if isinstance(site, str):
                    rel, _, ln = site.rpartition(":")
                    if ln.isdigit() and rel in index:
                        rows.append(_row(
                            fpath.name, f"other_sites[{pos}] {site}",
                            AnchorResult("NO-ANCHOR", int(ln),
                                         "string form carries no anchor — use "
                                         "{location, anchor} so this survives an edit "
                                         "somewhere above it"), int(ln)))
                    continue
                loc = str(site.get("location") or "")
                rel, _, ln = loc.rpartition(":")
                if not ln.isdigit():
                    continue
                blocks = index.get(rel)
                if blocks is None:
                    rows.append(_row(fpath.name, f"other_sites[{pos}] {loc}",
                                     AnchorResult("NO-FILE", None,
                                                  f"{rel} is not in the unit set"),
                                     int(ln)))
                    continue
                res = resolve_anchor(blocks, int(ln), site.get("anchor"))
                rows.append(_row(fpath.name, f"other_sites[{pos}] {loc}", res, int(ln)))
                if heal and res.stale and res.line:
                    site["location"] = f"{rel}:{res.line}"
                    touched = True
                    repaired += 1

        if heal and touched:
            fpath.write_text(json.dumps(doc, indent=2, ensure_ascii=False),
                             encoding="utf-8")
    return rows, repaired


def _findings_paths(project: Project, patterns: list[str]) -> list[Path]:
    if patterns:
        out: list[Path] = []
        for pat in patterns:
            p = Path(pat)
            base = p if p.is_absolute() else project.root / pat
            if base.is_dir():
                out += sorted(base.glob("*.json"))
            else:
                out += [Path(m) for m in sorted(_glob.glob(str(base)))
                        if Path(m).is_file()]
        return out
    return sorted(project.reviews.glob("manuscript-gate-*/round-*/findings/*.json"))


# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Resolve persisted passage references by their content anchors.")
    add_common_args(ap)
    ap.add_argument("--findings", action="append", default=[], metavar="PATH",
                    help="Findings dir, file or glob, repeatable. Defaults to every "
                         "reviews/manuscript-gate-*/round-*/findings/*.json.")
    ap.add_argument("--no-do-not-touch", action="store_true",
                    help="Skip bible/do-not-touch.md.")
    ap.add_argument("--heal", action="store_true",
                    help="Rewrite DRIFT line numbers from their anchors. Never "
                         "touches EDITED: repairing one would silently re-point a "
                         "verified-correct anchor at text nobody checked.")
    ap.add_argument("--quiet", action="store_true", help="Problems only.")
    ap.add_argument("--json", metavar="PATH", help="Write the result as JSON.")
    ap.add_argument("--fail-on-edited", action="store_true",
                    help="Exit 1 when a reference's passage was changed. OFF by "
                         "default: a hard gate on prose gets switched off, and then "
                         "there is no warning either.")
    args = ap.parse_args(argv)

    project = load_project(args.root, args.units)
    index = _blocks_index(project)

    rows: list[dict] = []
    repaired = 0
    if not args.no_do_not_touch:
        r, n = check_do_not_touch(project, index, args.heal)
        rows += r
        repaired += n
    r, n = check_findings(_findings_paths(project, args.findings), index, args.heal)
    rows += r
    repaired += n

    counts: dict[str, int] = {}
    for row in rows:
        counts[row["status"]] = counts.get(row["status"], 0) + 1

    if not args.quiet:
        print("[anchors] " + ("  ".join(f"{k}={v}" for k, v in sorted(counts.items()))
                              or "no anchored reference found"))
        if repaired:
            print(f"[anchors] {repaired} stale line number(s) rewritten from anchors")

    for row in rows:
        if row["status"] == "OK":
            continue
        if row["status"] == "DRIFT" and args.heal:
            continue
        print(f"{row['status']:<10} {row['source']} · {row['reference']}"
              + (f"  -> :{row['found_line']}" if row["found_line"] else "")
              + (f"\n           {row['detail']}" if row["detail"] else ""))

    edited = counts.get("EDITED", 0)
    if edited and not args.quiet:
        print(f"\n[anchors] {edited} reference(s) point at passages that were CHANGED, "
              f"not moved. --heal deliberately leaves these alone: re-point one and "
              f"you have quietly attached a verified-correct anchor to text nobody "
              f"checked. Re-read them.")

    if args.json:
        out = Path(args.json)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps({"counts": counts, "repaired": repaired,
                                   "rows": rows}, indent=2, ensure_ascii=False,
                                  sort_keys=True), encoding="utf-8")
        if not args.quiet:
            print(f"[anchors] result -> {out}")

    return 1 if (args.fail_on_edited and edited) else 0


if __name__ == "__main__":
    sys.exit(main())
