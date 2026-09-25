#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Markdown segmentation — one pass per line, deterministic, no parser.

Measured facts about book-length markdown that justify this instead of an AST:

  - A paragraph is usually one physical line, so the natural window is the
    paragraph, not ±N lines. Hard-wrapped books are merged by `paragraphs()`.
  - Code lives strictly inside fences. A fence state machine is enough — but it
    has to follow CommonMark (same character, closing fence at least as long as
    the opening one), or a ```` fence that quotes a ``` block reads as prose.
  - Inline code spans (`STORE`) are PROSE. Only fenced blocks are excluded.

An AST would normalize away the exact line numbers and raw text that the claim
index and the render lint both need.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .textio import read_text, safe_rel

# Order matters: `hr` before `bullet`, or `---` / `* * *` read as list items.
KIND_BY_PREFIX = [
    (re.compile(r"^#{1,6}\s"), "heading"),
    (re.compile(r"^\s{0,3}([-*_])(?:[ \t]*\1){2,}[ \t]*$"), "hr"),
    (re.compile(r"^>"), "quote"),
    (re.compile(r"^\|"), "table"),
    (re.compile(r"^\s*([-*+]|\d+[.)])\s"), "bullet"),
]

# "Looks like a fence". Whether it OPENS or CLOSES one is decided by the state
# machine in `segment_text`, which records it on `Record.fence`.
FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})")
_FENCE_OPEN = re.compile(r"^\s*(`{3,}|~{3,})(.*)$")


@dataclass
class Record:
    """One physical line, classified.

    `unit` is the stem of the source file (`unit-05`, `ch-05`, `article-auth`),
    so the same code serves `final/unit-NN.md` and a retrofit over any glob.
    """

    unit: str
    line: int          # 1-indexed, matches what an editor shows
    kind: str          # heading | hr | quote | table | bullet | para | code | blank
    heading_path: str  # "Chapter title › Section › Subsection"
    text: str
    path: str = ""     # repo-relative source path, for locations
    end_line: int = 0  # set by paragraphs(); 0 for a single physical line
    fence: str = ""    # "open" | "close" on a fence delimiter line, else ""

    @property
    def loc(self) -> str:
        return f"{self.path or self.unit}:{self.line}"


def segment(path: Path, rel_to: Path | None = None) -> list[Record]:
    """Segment a markdown file. Returns every line, including blanks and code.

    Callers filter; nothing is dropped here. A check that reasons about what is
    MISSING (a blank line before a `---`) cannot do it on a filtered stream.
    """
    rel = safe_rel(path, rel_to) if rel_to is not None else Path(path).name
    return segment_text(read_text(path), unit=Path(path).stem, path=rel)


def segment_text(text: str, unit: str = "", path: str = "") -> list[Record]:
    """Same as `segment`, for text already in memory (tests, manuscript.md)."""
    out: list[Record] = []
    fence_char, fence_len = "", 0          # "" = not inside a fence
    stack: dict[int, str] = {}

    for n, raw in enumerate(text.splitlines(), start=1):
        line = raw.rstrip()

        if fence_char:
            m = FENCE_RE.match(line)
            closes = (m and m.group(1)[0] == fence_char and len(m.group(1)) >= fence_len
                      and not line.strip()[len(m.group(1)):].strip())
            if closes:
                fence_char, fence_len = "", 0
                out.append(Record(unit, n, "code", _path_of(stack), line, path, fence="close"))
            else:
                out.append(Record(unit, n, "code", _path_of(stack), line, path))
            continue

        m = _FENCE_OPEN.match(line)
        if m and not (m.group(1)[0] == "`" and "`" in m.group(2)):
            fence_char, fence_len = m.group(1)[0], len(m.group(1))
            out.append(Record(unit, n, "code", _path_of(stack), line, path, fence="open"))
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


def unclosed_fence(records: list[Record]) -> Record | None:
    """The opening fence that never closes, if any — it swallows the rest of the file."""
    open_rec: Record | None = None
    for r in records:
        if r.fence == "open":
            open_rec = r
        elif r.fence == "close":
            open_rec = None
    return open_rec


def paragraphs(records: list[Record]) -> list[Record]:
    """Physical lines merged into logical paragraphs.

    Everything that reasons about a CLAIM works on this: a claim is a proposition,
    and a proposition does not stop at column 80. On a hard-wrapped book no single
    line carries enough signal to score as a claim, and the audit silently finds
    nothing — which looks exactly like a clean book.

    Merged: consecutive `para` lines; consecutive `quote` lines; a `bullet` plus
    the indented lines that continue it. NOT merged: table rows, headings, code.
    The merged record keeps the FIRST line's number; `end_line` records the span.
    """
    out: list[Record] = []
    buf: list[Record] = []

    def flush() -> None:
        if not buf:
            return
        head = buf[0]
        merged = Record(unit=head.unit, line=head.line, kind=head.kind,
                        heading_path=head.heading_path,
                        text=" ".join(r.text.strip() for r in buf), path=head.path)
        merged.end_line = buf[-1].line
        out.append(merged)
        buf.clear()

    for r in records:
        if buf:
            head = buf[0]
            same_para = head.kind == "para" and r.kind == "para"
            same_quote = head.kind == "quote" and r.kind == "quote"
            # A wrapped bullet continues on indented lines; an unindented line
            # after a bullet starts a new paragraph.
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

    Window of 5 because a list or a table can sit between a paragraph and the
    sentence that refers back to it.
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
    lines of it and inlining turns every dossier into a corpus dump.
    """
    for n in range(line + 1, line + lookahead + 1):
        r = by_line.get(n)
        if r and r.fence == "open":
            end = n + 1
            while end in by_line and by_line[end].fence != "close":
                end += 1
            first = by_line.get(n + 1)
            snippet = (first.text.strip()[:50] + "…") if first else ""
            return f'{path}:{n}-{end} ({end - n - 1} lines, "{snippet}")'
    return ""


def code_blocks(records: list[Record]) -> list[tuple[int, int, str, str]]:
    """Every fenced block as (start_line, end_line, language, body).

    An unterminated final block is still returned — `lint_render` reports it;
    dropping it here would hide the defect from both.
    """
    out: list[tuple[int, int, str, str]] = []
    start: int | None = None
    lang = ""
    body: list[str] = []

    for r in records:
        if r.kind != "code":
            continue
        if r.fence == "open":
            start, lang, body = r.line, FENCE_RE.sub("", r.text).strip(), []
        elif r.fence == "close" and start is not None:
            out.append((start, r.line, lang, "\n".join(body)))
            start, lang, body = None, "", []
        elif start is not None:
            body.append(r.text)

    if start is not None:
        out.append((start, records[-1].line if records else start, lang, "\n".join(body)))
    return out


def _path_of(stack: dict[int, str]) -> str:
    return " › ".join(stack[d] for d in sorted(stack))
