#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Content anchors — a reference that survives an edit somewhere else.

Line-keyed references (`bible/do-not-touch.md`, findings' `location` and
`other_sites`) go stale the moment a section is inserted above them. An anchor is
a short verbatim substring stored next to the line number. Four cases:

    1. the line resolves and the anchor is there          OK
    2. the anchor is nowhere in the file                  EDITED — revalidate
    3. the anchor is somewhere else, exactly once         DRIFT — use it, report
    4. the anchor appears more than once                  AMBIGUOUS — noisy fail

Case 2 is the one a line number cannot express: "it moved" vs "they changed it".

Matching: first exact with whitespace collapsed; if that finds nothing, again with
markdown markup (emphasis, backticks, link syntax, quote markers) removed on both
sides — a finding quotes what the auditor READ, which is often the rendered form.
Wording, case and punctuation are always compared exactly. A code block is ONE
block, so an anchor may span its lines.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .segment import paragraphs, segment

_WS = re.compile(r"\s+")
_LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")
_EMPH = re.compile(r"\*+|`+|(?<!\w)_+|_+(?!\w)")


def norm(text: str) -> str:
    """Collapse whitespace. Nothing else."""
    return _WS.sub(" ", text).strip()


def norm_loose(text: str) -> str:
    """Whitespace collapsed and markdown markup removed; wording untouched."""
    t = _LINK.sub(r"\1", text)
    t = re.sub(r"(?m)^\s*>\s?", "", t)
    return norm(_EMPH.sub("", t))


@dataclass
class Block:
    line: int
    end_line: int
    kind: str
    text: str      # whitespace-normalized


def blocks_for(path: Path, root: Path | None = None) -> list[Block]:
    """Logical paragraphs and whole code blocks of one file."""
    out: list[Block] = []
    code: list = []

    def flush_code() -> None:
        if code:
            out.append(Block(line=code[0].line, end_line=code[-1].line, kind="code",
                             text=norm(" ".join(r.text for r in code))))
            code.clear()

    for r in paragraphs(segment(path, rel_to=root)):
        if r.kind == "code":
            code.append(r)
            if r.fence == "close":
                flush_code()
            continue
        flush_code()
        if r.kind == "blank":
            continue
        out.append(Block(line=r.line, end_line=r.end_line or r.line,
                         kind=r.kind, text=norm(r.text)))
    flush_code()
    return out


@dataclass
class AnchorResult:
    status: str            # OK | DRIFT | EDITED | AMBIGUOUS | NO-FILE | NO-ANCHOR
    line: int | None       # where the anchor actually is, when it is anywhere
    detail: str = ""

    @property
    def stale(self) -> bool:
        """True when --heal can repair this by rewriting the line number."""
        return self.status == "DRIFT"


def _hits(blocks: list[Block], anchor: str) -> list[Block]:
    needle = norm(anchor)
    hits = [b for b in blocks if needle in b.text]
    if hits:
        return hits
    loose = norm_loose(anchor)
    return [b for b in blocks if loose and loose in norm_loose(b.text)]


def resolve_anchor(blocks: list[Block], line: int | None,
                   anchor: str | None) -> AnchorResult:
    """Locate a reference by its anchor, using the line only as a hint."""
    if not anchor or not anchor.strip():
        return AnchorResult("NO-ANCHOR", line,
                            "no anchor recorded — keyed on a line number alone, it goes "
                            "stale the next time anything above it is edited")
    hits = _hits(blocks, anchor)
    if len(hits) > 1:
        return AnchorResult(
            "AMBIGUOUS", hits[0].line,
            f"the anchor matches {len(hits)} passages "
            f"({', '.join(str(b.line) for b in hits[:5])}) — lengthen it")
    if not hits:
        return AnchorResult(
            "EDITED", None,
            "the anchor is nowhere in the file: the passage was CHANGED, not moved. "
            "Re-check what this reference asserted before repairing the line")
    hit = hits[0]
    if line is not None and hit.line <= line <= (hit.end_line or hit.line):
        return AnchorResult("OK", hit.line)
    return AnchorResult("DRIFT", hit.line,
                        f"the passage moved: recorded at :{line}, found at :{hit.line}. "
                        f"Repairable with --heal")


def anchor_from_quote(quote: str, words: int = 9) -> str:
    """A usable anchor from the verbatim quote a finding already carries."""
    return " ".join(norm(quote).split()[:words])
