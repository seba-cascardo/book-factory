#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""git blame, one subprocess call per file.

Blame is what makes the incomplete-fix detector cheap. When two passages make
the same claim and one of them was touched in a fix run while the other was not,
that is the mechanical signature of "the fix landed in 1 of N sites" — found
without spending a single token on an LLM.

Everything here degrades to empty rather than failing: a project that is not a
git repo still gets every other check.
"""

from __future__ import annotations

import datetime as _dt
import re
import subprocess
from pathlib import Path

_cache: dict[tuple[str, str], dict[int, tuple[str, str]]] = {}

_PORCELAIN_HEAD = re.compile(r"^([0-9a-f]{40}) \d+ (\d+)")


def blame_map(root: Path, relpath: str, enabled: bool = True) -> dict[int, tuple[str, str]]:
    """line number → (short sha, YYYY-MM-DD). Empty dict when unavailable.

    One call per file, not per line: on an 18-chapter book that is 18 subprocess
    invocations instead of ~5000.
    """
    if not enabled:
        return {}

    key = (str(root), relpath)
    if key in _cache:
        return _cache[key]

    out: dict[int, tuple[str, str]] = {}
    try:
        proc = subprocess.run(
            ["git", "blame", "--porcelain", "--", relpath],
            cwd=root, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=120,
        )
        raw = proc.stdout if proc.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        _cache[key] = out
        return out

    sha: str | None = None
    lineno: int | None = None
    ts = ""
    for ln in raw.splitlines():
        m = _PORCELAIN_HEAD.match(ln)
        if m:
            sha, lineno = m.group(1)[:7], int(m.group(2))
        elif ln.startswith("author-time ") and sha:
            try:
                ts = _dt.datetime.fromtimestamp(
                    int(ln.split()[1]), _dt.timezone.utc).strftime("%Y-%m-%d")
            except (ValueError, OverflowError):
                ts = ""
        elif ln.startswith("\t") and sha and lineno:
            out[lineno] = (sha, ts)
            sha = None
            lineno = None

    _cache[key] = out
    return out


def is_repo(root: Path) -> bool:
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=root, capture_output=True, text=True, timeout=20,
        )
        return proc.returncode == 0 and proc.stdout.strip() == "true"
    except (OSError, subprocess.SubprocessError):
        return False


def in_fix_run(sha: str, fix_run_commits: set[str]) -> bool:
    """True when a line's blame belongs to one of the declared fix-run commits.

    Compared on the 7-char prefix so the project can list short shas in its
    audit config, which is what a human actually copies out of `git log`.
    """
    if not sha or not fix_run_commits:
        return False
    return sha[:7] in {c[:7] for c in fix_run_commits}
