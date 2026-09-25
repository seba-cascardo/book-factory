#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Content anchors — a reference that survives an edit somewhere else.

## Why line numbers alone are not enough

MEASURED, during a one-day fix pass on the reference book: the extractor's gate
broke **three times in a day, and two of those were because a section was ADDED,
not because anything was wrong.** Everything below the insertion shifted, every
line-keyed reference went stale at once, and the output was noise.

A gate that shouts when nothing happened gets switched off within a week — the
same failure mode the waivers section exists to prevent, arriving through a
different door.

The claim index already solved this for passages, with fingerprints. What stayed
keyed on line numbers was everything else: `bible/do-not-touch.md`, the
`location` and `other_sites` of findings, and the scope of any check that pins a
passage. This module gives them the same property.

## The four cases

    1. the line resolves and the anchor is there          OK
    2. the anchor is nowhere in the file                  EDITED — revalidate
    3. the anchor is somewhere else, exactly once         DRIFT — use it, report
    4. the anchor appears more than once                  AMBIGUOUS — noisy fail

Case 2 is the valuable one and the one a line number cannot express: it
distinguishes *"it moved"* from *"they changed it"*. A moved passage is
bookkeeping and `--heal` fixes it. A changed passage means the thing the
reference protected may no longer be there, and somebody has to look.

## Matching is whitespace-insensitive, and nothing else

Books are hard-wrapped, so a verbatim anchor spanning a line break would never
match the raw text. Anchors are compared against logical paragraphs with
whitespace collapsed. Case, punctuation and wording are compared exactly: an
anchor that matches a reworded passage is not an anchor, it is a guess.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .segment import paragraphs, segment

_WS = re.compile(r"\s+")


def norm(text: str) -> str:
    """Collapse whitespace. Nothing else — see the module note."""
    return _WS.sub(" ", text).strip()


@dataclass
class Block:
    line: int
    end_line: int
    kind: str
    text: str      # already normalized


def blocks_for(path: Path, root: Path | None = None) -> list[Block]:
    """Logical paragraphs (and code lines) of one file, whitespace-collapsed."""
    out: list[Block] = []
    for r in paragraphs(segment(path, rel_to=root)):
        if r.kind == "blank":
            continue
        out.append(Block(line=r.line, end_line=r.end_line or r.line,
                         kind=r.kind, text=norm(r.text)))
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

    @property
    def needs_a_human(self) -> bool:
        return self.status in ("EDITED", "AMBIGUOUS", "NO-FILE")


def resolve_anchor(blocks: list[Block], line: int | None,
                   anchor: str | None) -> AnchorResult:
    """Locate a reference by its anchor, using the line only as a hint."""
    if not anchor or not anchor.strip():
        return AnchorResult("NO-ANCHOR", line,
                            "no anchor recorded — this reference is keyed on a line "
                            "number alone and will go stale the next time anything "
                            "above it is edited")
    needle = norm(anchor)
    hits = [b for b in blocks if needle in b.text]

    if len(hits) > 1:
        return AnchorResult(
            "AMBIGUOUS", hits[0].line,
            f"the anchor matches {len(hits)} passages "
            f"({', '.join(str(b.line) for b in hits[:5])}) — it is not specific "
            f"enough to identify one, so lengthen it")
    if not hits:
        return AnchorResult(
            "EDITED", None,
            "the anchor is nowhere in the file: the passage was CHANGED, not moved. "
            "Whatever this reference asserted about it has to be re-checked before "
            "the line number is repaired")

    hit = hits[0]
    if line is not None and hit.line <= line <= (hit.end_line or hit.line):
        return AnchorResult("OK", hit.line)
    return AnchorResult(
        "DRIFT", hit.line,
        f"the passage moved: recorded at :{line}, found at :{hit.line}. Repairable "
        f"with --heal")


def anchor_from_quote(quote: str, words: int = 9) -> str:
    """A usable anchor from a verbatim quote a finding already carries.

    Findings already require a verbatim `quote`, so most references can be
    anchored with no new authoring at all. Short enough to survive a
    neighbouring edit, long enough to be unique in practice.
    """
    return " ".join(norm(quote).split()[:words])
