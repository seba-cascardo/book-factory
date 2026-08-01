#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lint_render.py — markdown hazards that are invisible in the source and
obvious in the output.

Why this exists. A book shipped after four technical audits with a paragraph
that printed as an H2 heading in the PDF, because a `---` sat directly under it
with no blank line. Every reviewer had read that paragraph; none of them had
looked at the rendered page. The defect is trivially detectable and completely
undetectable by reading prose.

The whole class is like that: cheap, deterministic, and structurally invisible
to a prose reviewer. So this runs mechanically, at the manuscript gate (MG-5)
and again as a build preflight, rather than being anyone's job to notice.

Usage
  python scripts/lint_render.py                              # auto-detect project
  python scripts/lint_render.py --root PATH --units "final/ch-*.md"
  python scripts/lint_render.py --json findings.json
  python scripts/lint_render.py --fail-on major              # preflight gate

Exit codes: 0 clean at the chosen threshold, 1 otherwise, 2 on a usage error.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from bookkit.project import add_common_args, load_project  # noqa: E402
from bookkit.segment import FENCE_RE, Record, segment  # noqa: E402

SEVERITIES = ["critical", "major", "minor"]

# A setext underline is one or more `=` or `-` alone on a line. CommonMark turns
# the paragraph ABOVE it into a heading. When there is a blank line above, the
# same characters are a harmless thematic break — so the hazard is entirely
# about the missing blank line, which is why this cannot be a regex over text.
SETEXT_RE = re.compile(r"^\s*(=+|-+)\s*$")

TABLE_SEP_RE = re.compile(r"^\s*\|?[\s:|-]+\|?\s*$")

# Comments the pipeline writes for agent-to-agent handoff. They are correct in
# drafts and are defects in `final/` — they flow straight into pandoc and either
# leak into the output or, worse, swallow visible text when malformed.
#
# `SOURCE` is deliberately NOT here: the invisible citation policy puts
# `<!-- SOURCE: ... -->` in shipped prose on purpose. Add project-specific
# exemptions with --allow-comment.
PIPELINE_COMMENT_RE = re.compile(
    r"<!--\s*(EDITOR|FOR\s+HUMANIZER|HUMANIZER|CRITIC|REVIEWER|VOICE-RISK|"
    r"PROOFREADER|TODO|FIXME|DRAFT|WRITER)\b", re.I)

MD_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")

INTERNAL_NAME_RE = re.compile(r"\bunit-\d{2,}\b")


@dataclass
class Finding:
    check: str
    severity: str
    location: str
    message: str
    quote: str = ""

    def line_repr(self) -> str:
        q = f'  |  "{self.quote[:80]}"' if self.quote else ""
        return f"[{self.severity:8}] {self.check:20} {self.location}  {self.message}{q}"


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------


def check_setext_hazard(records: list[Record]) -> list[Finding]:
    """A paragraph immediately followed by `---`/`===` renders as a heading.

    This is the only check here that silently changes the STRUCTURE of the
    printed book, so it is the only one rated critical.
    """
    out: list[Finding] = []
    prev: Record | None = None
    for r in records:
        if r.kind == "code":
            prev = r
            continue
        if prev is not None and prev.kind == "para" and SETEXT_RE.match(r.text):
            level = "H1" if r.text.strip().startswith("=") else "H2"
            out.append(Finding(
                check="setext-hazard",
                severity="critical",
                location=f"{r.path}:{r.line}",
                message=(f"`{r.text.strip()}` directly under a paragraph renders that "
                         f"paragraph as an {level} heading. Insert a blank line above "
                         f"it (or delete the rule)."),
                quote=prev.text.strip(),
            ))
        prev = r
    return out


def check_fences(records: list[Record], path: str) -> list[Finding]:
    """An unclosed fence swallows the rest of the document into a code block."""
    opens = [r for r in records if FENCE_RE.match(r.text)]
    if len(opens) % 2 == 1:
        last = opens[-1]
        return [Finding(
            check="unbalanced-fence",
            severity="critical",
            location=f"{path}:{last.line}",
            message=(f"{len(opens)} fence markers — odd count. Everything after this "
                     f"line renders as code."),
            quote=last.text.strip(),
        )]
    return []


def check_fence_language(records: list[Record], path: str) -> list[Finding]:
    """Fences without a language lose syntax highlighting in every target."""
    out: list[Finding] = []
    opening = True
    for r in records:
        if not FENCE_RE.match(r.text):
            continue
        if opening and not FENCE_RE.sub("", r.text).strip():
            out.append(Finding(
                check="fence-no-language",
                severity="minor",
                location=f"{path}:{r.line}",
                message="Opening fence has no language tag.",
            ))
        opening = not opening
    return out


def check_html_comments(text: str, path: str) -> list[Finding]:
    """An unclosed `<!--` eats visible text until the next `-->`, or to EOF."""
    out: list[Finding] = []
    depth = 0
    open_line = 0
    for n, line in enumerate(text.splitlines(), start=1):
        pos = 0
        while True:
            o = line.find("<!--", pos)
            c = line.find("-->", pos)
            if o == -1 and c == -1:
                break
            if o != -1 and (c == -1 or o < c):
                if depth == 0:
                    open_line = n
                depth += 1
                pos = o + 4
            else:
                if depth == 0:
                    out.append(Finding(
                        check="unbalanced-comment",
                        severity="major",
                        location=f"{path}:{n}",
                        message="`-->` with no matching `<!--`.",
                        quote=line.strip(),
                    ))
                else:
                    depth -= 1
                pos = c + 3
    if depth > 0:
        out.append(Finding(
            check="unbalanced-comment",
            severity="critical",
            location=f"{path}:{open_line}",
            message=("Unclosed `<!--`. Everything from here to the next `-->` "
                     "(or to end of file) disappears from the rendered output."),
        ))
    return out


def check_pipeline_comments(records: list[Record], path: str,
                            allowed: set[str]) -> list[Finding]:
    """Agent handoff comments that reached a shipped file."""
    out: list[Finding] = []
    for r in records:
        if r.kind == "code":
            continue
        m = PIPELINE_COMMENT_RE.search(r.text)
        if m and m.group(1).upper().replace(" ", "_") not in allowed:
            out.append(Finding(
                check="pipeline-comment",
                severity="major",
                location=f"{path}:{r.line}",
                message=(f"`{m.group(1)}` handoff comment in a shipped file. These are "
                         f"drafting scaffolding and must not reach the build."),
                quote=r.text.strip()[:100],
            ))
    return out


def check_tables(records: list[Record], path: str) -> list[Finding]:
    """A row whose cell count differs from the header renders ragged or drops cells."""
    out: list[Finding] = []
    block: list[Record] = []

    def flush(rows: list[Record]) -> None:
        if len(rows) < 2:
            return
        header, sep = rows[0], rows[1]
        if not TABLE_SEP_RE.match(sep.text) or "-" not in sep.text:
            out.append(Finding(
                check="table-no-separator",
                severity="major",
                location=f"{path}:{header.line}",
                message="Table header is not followed by a `|---|` separator row; "
                        "it will render as plain text.",
                quote=header.text.strip()[:100],
            ))
            return
        want = _cells(header.text)
        if _cells(sep.text) != want:
            out.append(Finding(
                check="table-shape",
                severity="major",
                location=f"{path}:{sep.line}",
                message=f"Separator row has {_cells(sep.text)} cells, header has {want}.",
                quote=sep.text.strip()[:100],
            ))
        for r in rows[2:]:
            got = _cells(r.text)
            if got != want:
                out.append(Finding(
                    check="table-shape",
                    severity="major",
                    location=f"{path}:{r.line}",
                    message=f"Row has {got} cells, header has {want}.",
                    quote=r.text.strip()[:100],
                ))

    for r in records:
        if r.kind == "table":
            block.append(r)
        else:
            flush(block)
            block = []
    flush(block)
    return out


def check_headings(records: list[Record], path: str,
                   expect_single_h1: bool) -> list[Finding]:
    out: list[Finding] = []
    last_depth = 0
    h1_lines: list[int] = []
    prev: Record | None = None

    for r in records:
        if r.kind != "heading":
            prev = r
            continue
        depth = len(r.text) - len(r.text.lstrip("#"))
        if depth == 1:
            h1_lines.append(r.line)
        if last_depth and depth > last_depth + 1:
            out.append(Finding(
                check="heading-jump",
                severity="minor",
                location=f"{path}:{r.line}",
                message=f"H{last_depth} → H{depth} skips a level; the TOC and the "
                        f"EPUB navigation both read this as a gap.",
                quote=r.text.strip()[:80],
            ))
        if prev is not None and prev.kind not in ("blank", "code"):
            out.append(Finding(
                check="heading-no-blank-line",
                severity="minor",
                location=f"{path}:{r.line}",
                message="Heading with no blank line above it. CommonMark accepts it; "
                        "several pandoc writers and most linters do not.",
                quote=r.text.strip()[:80],
            ))
        last_depth = depth
        prev = r

    if expect_single_h1 and len(h1_lines) > 1:
        out.append(Finding(
            check="multiple-h1",
            severity="major",
            location=f"{path}:{h1_lines[1]}",
            message=f"{len(h1_lines)} H1 headings in one unit (lines "
                    f"{', '.join(str(n) for n in h1_lines)}). One unit is one H1; "
                    f"the extras break chapter splitting in EPUB.",
        ))
    return out


def check_lists(records: list[Record], path: str) -> list[Finding]:
    """A list that starts on the line after a paragraph, with no blank between.

    CommonMark lets a bullet list interrupt a paragraph but an ordered list only
    when it starts at 1 — and pandoc's readers do not all agree. The result is a
    list that renders as a run-on sentence in one target and correctly in another.
    """
    out: list[Finding] = []
    prev: Record | None = None
    for r in records:
        if r.kind == "bullet" and prev is not None and prev.kind == "para":
            out.append(Finding(
                check="list-no-blank-line",
                severity="minor",
                location=f"{path}:{r.line}",
                message="List starts directly after a paragraph with no blank line; "
                        "renderers disagree on whether this is a list.",
                quote=r.text.strip()[:80],
            ))
        prev = r
    return out


def check_links(records: list[Record], path: str, root: Path,
                source: Path, check_files: bool) -> list[Finding]:
    out: list[Finding] = []
    for r in records:
        if r.kind == "code":
            continue
        for target in MD_LINK_RE.findall(r.text):
            if INTERNAL_NAME_RE.search(target):
                out.append(Finding(
                    check="internal-name-leak",
                    severity="major",
                    location=f"{path}:{r.line}",
                    message=f"Link points at `{target}` — internal pipeline naming "
                            f"must not appear in a shipped tree.",
                ))
                continue
            if not check_files:
                continue
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            rel = target.split("#", 1)[0]
            if not rel:
                continue
            if not (source.parent / rel).exists() and not (root / rel).exists():
                out.append(Finding(
                    check="broken-link",
                    severity="major",
                    location=f"{path}:{r.line}",
                    message=f"Relative link `{rel}` does not resolve to a file.",
                ))
    return out


def _cells(row: str) -> int:
    """Cell count of a markdown table row, ignoring escaped pipes."""
    stripped = row.strip()
    body = re.sub(r"\\\|", "\x00", stripped)
    body = body.strip("|")
    return len([c for c in body.split("|")])


# ---------------------------------------------------------------------------


def lint_file(path: Path, root: Path, relpath: str, *,
              expect_single_h1: bool = True,
              allowed_comments: set[str] | None = None,
              check_links_exist: bool = False) -> list[Finding]:
    text = path.read_text(encoding="utf-8")
    records = segment(path, rel_to=root)
    for r in records:
        r.path = relpath

    findings: list[Finding] = []
    findings += check_setext_hazard(records)
    findings += check_fences(records, relpath)
    findings += check_fence_language(records, relpath)
    findings += check_html_comments(text, relpath)
    findings += check_pipeline_comments(records, relpath, allowed_comments or set())
    findings += check_tables(records, relpath)
    findings += check_headings(records, relpath, expect_single_h1)
    findings += check_lists(records, relpath)
    findings += check_links(records, relpath, root, path, check_links_exist)
    return findings


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Lint markdown for rendering hazards invisible in the source.")
    add_common_args(ap)
    ap.add_argument("--fail-on", choices=SEVERITIES + ["never"], default="critical",
                    help="Exit non-zero at this severity or above (default: critical).")
    ap.add_argument("--json", metavar="PATH", default=None,
                    help="Also write findings as JSON for the manuscript gate.")
    ap.add_argument("--allow-comment", action="append", default=[],
                    help="Comment tag that is legitimate in shipped prose, repeatable. "
                         "SOURCE is always allowed.")
    ap.add_argument("--allow-multiple-h1", action="store_true",
                    help="Skip the one-H1-per-unit check (manuscript.md, or a profile "
                         "that concatenates).")
    ap.add_argument("--check-links", action="store_true",
                    help="Resolve relative markdown links against the filesystem.")
    ap.add_argument("--quiet", action="store_true", help="Only print the summary.")
    args = ap.parse_args(argv)

    project = load_project(args.root, args.units)
    allowed = {c.upper().replace(" ", "_") for c in args.allow_comment} | {"SOURCE"}

    findings: list[Finding] = []
    for path in project.unit_paths:
        findings += lint_file(
            path, project.root, project.rel(path),
            expect_single_h1=not args.allow_multiple_h1,
            allowed_comments=allowed,
            check_links_exist=args.check_links,
        )

    order = {s: i for i, s in enumerate(SEVERITIES)}
    findings.sort(key=lambda f: (order.get(f.severity, 9), f.location))

    counts = {s: sum(1 for f in findings if f.severity == s) for s in SEVERITIES}

    if not args.quiet:
        for f in findings:
            print(f.line_repr())
        if findings:
            print()

    print(f"[lint_render] {len(project.unit_paths)} file(s) · "
          f"{counts['critical']} critical · {counts['major']} major · "
          f"{counts['minor']} minor")

    if args.json:
        out = Path(args.json)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps({
            "check": "MG-5",
            "tool": "lint_render",
            "files": [project.rel(p) for p in project.unit_paths],
            "counts": counts,
            "findings": [asdict(f) for f in findings],
        }, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"[lint_render] findings → {out}")

    if args.fail_on == "never":
        return 0
    threshold = order[args.fail_on]
    return 1 if any(order.get(f.severity, 9) <= threshold for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
