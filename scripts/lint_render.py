#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lint_render.py — markdown hazards invisible in the source, obvious in the output.

A paragraph with a `---` under it reads perfectly in the source and prints as an
H2; an unclosed `<!--` swallows text; a line starting `1999.` becomes an ordered
list. Cheap, deterministic, and structurally invisible to a prose reviewer, so it
runs mechanically at the manuscript gate (MG-5) and as a build preflight.

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

from bookkit import textio  # noqa: E402
from bookkit.project import add_common_args, load_project  # noqa: E402
from bookkit.segment import Record, segment, unclosed_fence  # noqa: E402

SEVERITIES = ["critical", "major", "minor"]

# A setext underline (`===` / `---`, no internal spaces) directly under a text
# line turns that line into a heading. With a blank line above it is a harmless
# thematic break — the hazard is the missing blank line.
SETEXT_RE = re.compile(r"^\s{0,3}(=+|-+)\s*$")
TABLE_SEP_RE = re.compile(r"^\s*\|?[\s:|-]+\|?\s*$")

# Agent handoff comments: correct in drafts, defects in `final/`. `SOURCE` is
# NOT here — the invisible-citation policy ships it on purpose.
PIPELINE_COMMENT_RE = re.compile(
    r"<!--\s*(EDITOR|FOR\s+HUMANIZER|HUMANIZER|CRITIC|REVIEWER|VOICE-RISK|"
    r"PROOFREADER|TODO|FIXME|DRAFT|WRITER)\b", re.I)
MD_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
INTERNAL_NAME_RE = re.compile(r"\bunit-\d{2,}\b")
INLINE_CODE_RE = re.compile(r"`+[^`]*`+")
# A prose line that starts with a number of 3+ digits and a period — "1999. Ese
# año…" — renders as an ordered list numbered 1999.
ORDERED_HAZARD_RE = re.compile(r"^\s{0,3}(\d{3,})[.)]\s")
# A dialogue line (raya) that opens a new speaker must start a paragraph.
DIALOGUE_OPEN_RE = re.compile(r"^\s*[—―]\s?[¿¡«\"“A-ZÁÉÍÓÚÑÜ]")
SENTENCE_END_RE = re.compile(r"[.!?…:»\"”)]\s*$")


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

    The only check that silently changes the STRUCTURE of the printed book, so
    the only one rated critical besides unclosed fences and comments.
    """
    out: list[Finding] = []
    prev: Record | None = None
    for r in records:
        if (r.kind != "code" and prev is not None and prev.kind == "para"
                and SETEXT_RE.match(r.text)):
            level = "H1" if r.text.strip().startswith("=") else "H2"
            out.append(Finding(
                "setext-hazard", "critical", f"{r.path}:{r.line}",
                f"`{r.text.strip()}` directly under a paragraph renders that paragraph "
                f"as an {level} heading. Insert a blank line above it (or delete it).",
                prev.text.strip()))
        prev = r
    return out


def check_fences(records: list[Record], path: str) -> list[Finding]:
    """An unclosed fence swallows the rest of the document into a code block."""
    rec = unclosed_fence(records)
    if rec is None:
        return []
    return [Finding("unbalanced-fence", "critical", f"{path}:{rec.line}",
                    "This fence never closes (a closing fence needs the same character, "
                    "at least as many of them, and nothing after). Everything after "
                    "this line renders as code.", rec.text.strip())]


def check_fence_language(records: list[Record], path: str) -> list[Finding]:
    """Fences without a language lose syntax highlighting in every target."""
    return [Finding("fence-no-language", "minor", f"{path}:{r.line}",
                    "Opening fence has no language tag.")
            for r in records
            if r.fence == "open" and not re.sub(r"^\s*(`{3,}|~{3,})", "", r.text).strip()]


def check_html_comments(records: list[Record], path: str) -> list[Finding]:
    """An unclosed `<!--` eats visible text until the next `-->`, or to EOF.

    HTML comments do not nest: inside one, only `-->` matters. Fenced code and
    inline code spans are skipped — a Mermaid arrow `-->` or a quoted `<!--` in a
    code sample is content, not markup.
    """
    out: list[Finding] = []
    in_comment = False
    open_line = 0
    for r in records:
        if r.kind == "code":
            continue
        line = INLINE_CODE_RE.sub("", r.text) if not in_comment else r.text
        pos = 0
        while True:
            if in_comment:
                c = line.find("-->", pos)
                if c == -1:
                    break
                in_comment, pos = False, c + 3
                continue
            o, c = line.find("<!--", pos), line.find("-->", pos)
            if o != -1 and (c == -1 or o < c):
                in_comment, open_line, pos = True, r.line, o + 4
            elif c != -1:
                out.append(Finding("unbalanced-comment", "minor", f"{path}:{r.line}",
                                   "`-->` with no matching `<!--` — prints literally.",
                                   r.text.strip()))
                pos = c + 3
            else:
                break
    if in_comment:
        out.append(Finding("unbalanced-comment", "critical", f"{path}:{open_line}",
                           "Unclosed `<!--`. Everything from here to the next `-->` (or "
                           "to end of file) disappears from the rendered output."))
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
            out.append(Finding("pipeline-comment", "major", f"{path}:{r.line}",
                               f"`{m.group(1)}` handoff comment in a shipped file.",
                               r.text.strip()[:100]))
    return out


def check_tables(records: list[Record], path: str) -> list[Finding]:
    """Ragged rows, a missing separator, and a lone `| row |` that prints as text."""
    out: list[Finding] = []

    def flush(rows: list[Record]) -> None:
        if not rows:
            return
        header = rows[0]
        if len(rows) < 2 or not TABLE_SEP_RE.match(rows[1].text) or "-" not in rows[1].text:
            out.append(Finding(
                "table-no-separator", "major", f"{path}:{header.line}",
                "Table row(s) with no `|---|` separator under the header; this renders "
                "as plain text" + (" (a lone row, often detached from the table above "
                                   "by a blank line)." if len(rows) < 2 else "."),
                header.text.strip()[:100]))
            return
        want = _cells(header.text)
        if _cells(rows[1].text) != want:
            out.append(Finding("table-shape", "major", f"{path}:{rows[1].line}",
                               f"Separator row has {_cells(rows[1].text)} cells, header has {want}.",
                               rows[1].text.strip()[:100]))
        for r in rows[2:]:
            if _cells(r.text) != want:
                out.append(Finding("table-shape", "major", f"{path}:{r.line}",
                                   f"Row has {_cells(r.text)} cells, header has {want}.",
                                   r.text.strip()[:100]))

    block: list[Record] = []
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
            out.append(Finding("heading-jump", "minor", f"{path}:{r.line}",
                               f"H{last_depth} → H{depth} skips a level.", r.text.strip()[:80]))
        if prev is not None and prev.kind not in ("blank", "code"):
            out.append(Finding("heading-no-blank-line", "minor", f"{path}:{r.line}",
                               "Heading with no blank line above it; several pandoc "
                               "writers do not accept it.", r.text.strip()[:80]))
        last_depth = depth
        prev = r
    if expect_single_h1 and len(h1_lines) > 1:
        out.append(Finding("multiple-h1", "major", f"{path}:{h1_lines[1]}",
                           f"{len(h1_lines)} H1 headings in one unit (lines "
                           f"{', '.join(str(n) for n in h1_lines)}); EPUB chapter "
                           f"splitting breaks."))
    return out


def check_lists(records: list[Record], path: str) -> list[Finding]:
    """A list starting on the line after a PARAGRAPH, with no blank line between.

    Renderers disagree on whether that is a list. A wrapped list item (indented or
    lazy continuation) followed by the next item is not a paragraph and is not
    flagged. A 3+-digit number at line start is the ordered-list hazard instead.
    """
    out: list[Finding] = []
    prev: Record | None = None
    in_list = False
    for r in records:
        if r.kind == "bullet":
            hazard = ORDERED_HAZARD_RE.match(r.text)
            if hazard and not in_list:
                out.append(Finding(
                    "ordered-list-hazard", "major", f"{path}:{r.line}",
                    f"The line starts with `{hazard.group(1)}.` and renders as an ordered "
                    f"list numbered {hazard.group(1)}. Escape it (`{hazard.group(1)}\\.`) "
                    f"or reword.", r.text.strip()[:80]))
            elif prev is not None and prev.kind == "para" and not in_list:
                out.append(Finding(
                    "list-no-blank-line", "minor", f"{path}:{r.line}",
                    "List starts directly after a paragraph with no blank line; "
                    "renderers disagree on whether this is a list.", r.text.strip()[:80]))
            in_list = not hazard or in_list
        elif r.kind == "para":
            in_list = in_list and prev is not None and (
                prev.kind in ("bullet", "para")
                or (prev.kind == "blank" and r.text[:1].isspace()))
        elif r.kind not in ("blank", "code"):
            in_list = False
        prev = r
    return out


def check_dialogue(records: list[Record], path: str) -> list[Finding]:
    """A dialogue line (raya) glued to the narration line above it.

    Without a blank line the two render as ONE paragraph: the new speaker's line
    is swallowed into the narration. Only fires when the line above ends a
    sentence and the raya opens speech (capital, ¿, ¡, «), so a hard-wrapped
    inciso ("…dijo\\n—y se fue") is left alone.
    """
    out: list[Finding] = []
    prev: Record | None = None
    for r in records:
        if (r.kind == "para" and prev is not None and prev.kind == "para"
                and DIALOGUE_OPEN_RE.match(r.text) and SENTENCE_END_RE.search(prev.text)
                and not DIALOGUE_OPEN_RE.match(prev.text)):
            out.append(Finding(
                "dialogue-glued", "major", f"{path}:{r.line}",
                "Dialogue line directly under a narration line, with no blank line: "
                "both render as one paragraph. Insert a blank line above it.",
                r.text.strip()[:80]))
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
                out.append(Finding("internal-name-leak", "major", f"{path}:{r.line}",
                                   f"Link points at `{target}` — internal pipeline naming "
                                   f"must not appear in a shipped tree."))
                continue
            if not check_files or target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            rel = target.split("#", 1)[0]
            if rel and not (source.parent / rel).exists() and not (root / rel).exists():
                out.append(Finding("broken-link", "major", f"{path}:{r.line}",
                                   f"Relative link `{rel}` does not resolve to a file."))
    return out


def _cells(row: str) -> int:
    """Cell count of a markdown table row, ignoring escaped pipes."""
    body = re.sub(r"\\\|", "\x00", row.strip()).strip("|")
    return len(body.split("|"))


# ---------------------------------------------------------------------------


def lint_file(path: Path, root: Path, relpath: str, *,
              expect_single_h1: bool = True,
              allowed_comments: set[str] | None = None,
              check_links_exist: bool = False) -> list[Finding]:
    records = segment(path, rel_to=root)
    for r in records:
        r.path = relpath

    findings: list[Finding] = []
    problem = textio.problems().get(str(path))
    if problem:
        findings.append(Finding("encoding", "major", f"{relpath}:1", problem))
    findings += check_setext_hazard(records)
    findings += check_fences(records, relpath)
    findings += check_fence_language(records, relpath)
    findings += check_html_comments(records, relpath)
    findings += check_pipeline_comments(records, relpath, allowed_comments or set())
    findings += check_tables(records, relpath)
    findings += check_headings(records, relpath, expect_single_h1)
    findings += check_lists(records, relpath)
    findings += check_dialogue(records, relpath)
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
                    help="Comment tag legitimate in shipped prose, repeatable. SOURCE is "
                         "always allowed.")
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
        findings += lint_file(path, project.root, project.rel(path),
                              expect_single_h1=not args.allow_multiple_h1,
                              allowed_comments=allowed,
                              check_links_exist=args.check_links)

    order = {s: i for i, s in enumerate(SEVERITIES)}
    findings.sort(key=lambda f: (order.get(f.severity, 9), f.location))
    counts = {s: sum(1 for f in findings if f.severity == s) for s in SEVERITIES}

    if not args.quiet:
        for f in findings:
            print(f.line_repr())
        if findings:
            print()
    print(f"[lint_render] {len(project.unit_paths)} file(s) · {counts['critical']} critical · "
          f"{counts['major']} major · {counts['minor']} minor")

    if args.json:
        out = Path(args.json)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps({
            "check": "MG-5", "tool": "lint_render",
            "files": [project.rel(p) for p in project.unit_paths],
            "counts": counts, "findings": [asdict(f) for f in findings],
        }, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
        print(f"[lint_render] findings → {out}")

    if args.fail_on == "never":
        return 0
    threshold = order[args.fail_on]
    return 1 if any(order.get(f.severity, 9) <= threshold for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
