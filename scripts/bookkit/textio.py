#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Text input — one reader for every file the checks open.

Three things every script needs and none may do differently:

  - **UTF-8 with or without a BOM.** A BOM left in place becomes part of the first
    heading and is copied into `manuscript.md`.
  - **NFC.** "canción" typed on a Mac (NFD) and on Windows (NFC) are different
    byte strings; without normalization they fingerprint differently and a moved
    passage reads as an edited one.
  - **A legacy encoding is a finding, not a crash.** A cp1252 file used to kill
    `lint_render` and the gate then reported "MG-5: 0 critical". It is decoded
    as cp1252, the text is still checked, and the problem is recorded here so
    `lint_render` reports it as a `major` `encoding` finding.
"""

from __future__ import annotations

import os
import unicodedata
from pathlib import Path

# path (as given) → message. Read by lint_render after it has read the units.
_PROBLEMS: dict[str, str] = {}


def read_text(path: str | Path) -> str:
    """Decode a text file: UTF-8 (BOM stripped), else cp1252 + a recorded problem."""
    p = Path(path)
    raw = p.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        raw = raw[3:]
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        text = raw.decode("cp1252", errors="replace")
        _PROBLEMS[str(p)] = (f"not valid UTF-8 (byte 0x{raw[exc.start]:02x} at offset "
                             f"{exc.start}); decoded as cp1252 — re-save the file as UTF-8")
    return unicodedata.normalize("NFC", text.replace("\r\n", "\n").replace("\r", "\n"))


def problems() -> dict[str, str]:
    """Encoding problems seen so far in this process, keyed by path."""
    return dict(_PROBLEMS)


def safe_rel(path: str | Path, root: str | Path) -> str:
    """`path` relative to `root`, POSIX-style, without resolving links first.

    `Path.resolve()` follows a Windows junction (or a symlink) out of the project,
    so `final/` as a junction made every location collapse to a bare file name and
    every anchor read NO-FILE. Lexical first; resolved only as a fallback.
    """
    p, r = Path(path), Path(root)
    for a, b in ((os.path.abspath(p), os.path.abspath(r)), (p.resolve(), r.resolve())):
        try:
            return Path(a).relative_to(Path(b)).as_posix()
        except ValueError:
            continue
    return p.name
