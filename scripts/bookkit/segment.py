#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Markdown segmentation — one pass per line, deterministic, no parser.

Three measured facts about book-length markdown justify this being ~80 lines
instead of a dependency on a markdown AST:

  - A paragraph is one physical line (median 47 words in the corpus this was
    calibrated on). So the natural window is the paragraph, not ±N lines.
  - Code lives strictly inside fences. A fence toggle is enough.
  - Inline code spans (`STORE`) are PROSE — about half the claims in a technical
    book live in a sentence that mentions a keyword in backticks. Only fenced
    blocks are excluded.

An AST would give us less: it normalizes away the exact line numbers and the
raw text that the claim index and the render lint both need.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

# Order matters: `hr` must be tested before `bullet`, or `---` reads as a list
# item. `KIND_BY_PREFIX` is checked top to bottom and the first match wins.
KIND_BY_PREFIX = [
    (re.compile(r"^#{1,6}\s"), "heading"),
    (re.compile(r"^(-{3,}|\*{3,}|_{3,})\s*$"), "hr"),
    (re.compile(r"^>"), "quote"),
    (re.compile(r"^\|"), "table"),
    (re.compile(r"^\s*([-*+]|\d+[.)])\s"), "bullet"),
]

FENCE_RE = re.compile(r"^\s*(```|~~~)")

# Setext underlines: `===` (H1) and `---` (H2) directly under a text line. The
# `---` case also matches the `hr` pattern above, which is exactly the ambiguity
# that renders a paragraph as a heading in the PDF. Kind resolution keeps `hr`;
# lint_render is what decides whether a given `hr` is an accidental Setext.
SETEXT_RE = re.compile(r"^\s*(={2,}|-{2,})\s*$")


@dataclass
class Record:
    """One physical line, classified.

    `unit` is the stem of the source file (`unit-05`, `ch-05`, `article-auth`).
    Keeping the stem rather than a normalized id lets the same code serve both
    a v3 project (`final/unit-NN.md`) and a standalone retrofit run over an
    arbitrary glob.
    """

    unit: str
    line: int          # 1-indexed, matches what an editor shows
    kind: str          # heading | hr | quote | table | bullet | para | code | blank
    heading_path: str  # "Chapter title › Section › Subsection"
    text: str
    path: str = ""     # repo-relative source path, for locations
    end_line: int = 0  # set by paragraphs(); 0 for a single physical line

    @property
    def loc(self) -> str:
        return f"{self.path or self.unit}:{self.line}"


def segment(path: Path, rel_to: Path | None = None) -> list[Record]:
    """Segment a markdown file. Returns every line, including blanks and code.

    Callers filter; nothing is dropped here. A check that needs to reason about
    what is *missing* (a blank line before a `---`) cannot do it on a filtered
    stream.
    """
    text = path.read_text(encoding="utf-8")
    rel = _relpath(path, rel_to)
    return segment_text(text, unit=path.stem, path=rel)


def segment_text(text: str, unit: str = "", path: str = "") -> list[Record]:
    """Same as `segment`, for text already in memory (tests, manuscript.md)."""
    out: list[Record] = []
    in_code = False
    stack: dict[int, str] = {}

    for n, raw in enumerate(text.splitlines(), start=1):
        line = raw.rstrip()

        if FENCE_RE.match(line):
            in_code = not in_code
            out.append(Record(unit, n, "code", _path_of(stack), line, path))
            continue
        if in_code:
            out.append(Record(unit, n, "code", _path_of(stack), line, path))
            continue
        if not line.strip():
            out.append(Record(unit, n, "blank", _path_of(stack), "", path))
            continue

        kind = "para"
        for rx, k in KIND_BY_PREFIX:
            if rx.match(line):
                kind = k
                break

        if kind == "heading":
            depth = len(line) - len(line.lstrip("#"))
            title = line.lstrip("#").strip()
            stack = {d: t for d, t in stack.items() if d < depth}
            stack[depth] = title

        out.append(Record(unit, n, kind, _path_of(stack), line, path))

    return out


def prose_records(records: list[Record]) -> list[Record]:
    """The lines a claim can live in. Code, blanks, rules and headings are out."""
    return [r for r in records if r.kind in ("para", "bullet", "quote", "table")]


def paragraphs(records: list[Record]) -> list[Record]:
    """Physical lines merged into logical paragraphs.

    Everything that reasons about a CLAIM works on this, not on raw lines. A
    claim is a proposition, and a proposition does not stop at column 80.

    The toolkit was first calibrated on a corpus where one paragraph was one
    physical line, so this collapsed to a no-op and the distinction was invisible.
    On a hard-wrapped book it is not: a sentence like "…forces the engine off the
    optimized path and onto the row-level path, which is slower by an order of
    magnitude" splits across three lines, no single line carries enough signal to
    score as a claim, and the concept audit silently finds nothing. Silently is
    the bad part — a check that returns zero findings looks exactly like a clean
    book.

    Merged: consecutive `para` lines; consecutive `quote` lines; a `bullet` plus
    the indented lines that continue it. NOT merged: table rows (each row is its
    own unit) and headings.

    The merged record keeps the FIRST line's number, so locations still point at
    where a reader would look, and `end_line` records the span.
    """
    out: list[Record] = []
    buf: list[Record] = []

    def flush() -> None:
        if not buf:
            return
        head = buf[0]
        merged = Record(
            unit=head.unit, line=head.line, kind=head.kind,
            heading_path=head.heading_path,
            text=" ".join(r.text.strip() for r in buf),
            path=head.path,
        )
        merged.end_line = buf[-1].line
        out.append(merged)
        buf.clear()

    for r in records:
        if buf:
            head = buf[0]
            same_para = head.kind == "para" and r.kind == "para"
            same_quote = head.kind == "quote" and r.kind == "quote"
            # A wrapped bullet continues on indented lines. An unindented line
            # after a bullet starts a new paragraph — merging those would glue
            # a list to the prose that follows it.
            bullet_cont = (head.kind == "bullet" and r.kind == "para"
                           and r.text[:1].isspace())
            if same_para or same_quote or bullet_cont:
                buf.append(r)
                continue
            flush()

        if r.kind in ("para", "quote", "bullet"):
            buf.append(r)
        else:
            out.append(r)
    flush()
    return out


def prev_prose(by_line: dict[int, Record], line: int, window: int = 5) -> Record | None:
    """Nearest prose line above `line`, for resolving a leading anaphora.

    Window of 5 rather than 1 because a bullet list or a table can sit between a
    paragraph and the sentence that refers back to it.
    """
    for n in range(line - 1, max(0, line - window - 1), -1):
        r = by_line.get(n)
        if r and r.kind in ("para", "bullet", "quote"):
            return r
    return None


def fence_after(by_line: dict[int, Record], line: int, path: str,
                lookahead: int = 4) -> str:
    """A reference to the code block that follows a passage, never its content.

    Code goes into a dossier by reference: a technical book carries thousands of
    lines of code and inlining them turns every dossier into a corpus dump.
    """
    for n in range(line + 1, line + lookahead + 1):
        r = by_line.get(n)
        if r and FENCE_RE.match(r.text):
            end = n + 1
            while end in by_line and not FENCE_RE.match(by_line[end].text):
                end += 1
            first = by_line.get(n + 1)
            snippet = (first.text.strip()[:50] + "…") if first else ""
            return f'{path}:{n}-{end} ({end - n - 1} lines, "{snippet}")'
    return ""


def code_blocks(records: list[Record]) -> list[tuple[int, int, str, str]]:
    """Every fenced block as (start_line, end_line, language, body).

    Used by the rule-vs-instance extractor and the code corpus extractor. An
    unterminated final block is still returned — `lint_render` is what reports
    it; silently dropping it here would hide the defect from both.
    """
    out: list[tuple[int, int, str, str]] = []
    start: int | None = None
    lang = ""
    body: list[str] = []

    for r in records:
        if r.kind != "code":
            continue
        if FENCE_RE.match(r.text):
            if start is None:
                start = r.line
                lang = FENCE_RE.sub("", r.text).strip()
                body = []
            else:
                out.append((start, r.line, lang, "\n".join(body)))
                start = None
                lang = ""
                body = []
        elif start is not None:
            body.append(r.text)

    if start is not None:
        out.append((start, records[-1].line if records else start, lang, "\n".join(body)))
    return out


def _path_of(stack: dict[int, str]) -> str:
    return " › ".join(stack[d] for d in sorted(stack))


def _relpath(path: Path, rel_to: Path | None) -> str:
    if rel_to is None:
        return path.name
    try:
        return path.resolve().relative_to(rel_to.resolve()).as_posix()
    except ValueError:
        return path.name
