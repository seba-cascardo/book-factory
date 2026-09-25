#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""What counts as "not filled in" — one definition for sheets, endings, the
story ledger, gate waivers and `--resolve` notes.

A field that reads `TBD`, `N/A`, `x`, `(pendiente)`, `{{name}}` or
`[describe the backstory]` was never answered. The user's literary rules
(R1–R4) and the gate's waivers both depend on telling an answer from a
placeholder, so both import this module instead of keeping their own lists.

  is_placeholder(value)          -> bool
  too_short(value, words=3)      -> bool   (fewer than `words` words)
  filled(value, min_chars=0)     -> bool   (not a placeholder, long enough)
"""

from __future__ import annotations

import re

# Exact values (compared lowercased, surrounding whitespace removed).
EXACT = {
    "", "?", "??", "???", "...", "…", "-", "--", "—", "–", "_",
    "tbd", "tba", "todo", "to do", "wip", "n/a", "n.a.", "na", "none", "null", "nil",
    "x", "xx", "xxx", "xxxx", "lorem ipsum",
    "pendiente", "a definir", "por definir", "sin definir", "a completar", "completar",
    "por completar", "falta", "falta completar", "falta definir", "lo vemos", "ya veremos",
    "idem", "ídem", "etc", "etc.",
}
# A value that STARTS with one of these is a placeholder with a comment after it
# ("TBD — ask the author", "pendiente: ver con Seba"). `TODO` only in capitals:
# "Todo lo que toca lo rompe" is a Spanish sentence, not a note to self.
_PREFIX = re.compile(
    r"^(?:tbd|tba|n/a|x{3,}|lorem ipsum|a definir|por definir|sin definir|a completar|"
    r"por completar|falta (?:completar|definir)|lo vemos|pendiente\s*(?:[:\-—–(]|$))", re.I)
_TODO = re.compile(r"^TODO\b")
_WRAPPED = re.compile(r"^(?:\[(?P<b>[^\]]*)\]|\((?P<p>[^)]*)\)|<(?P<a>[^>]*)>|\{\{(?P<c>.*)\}\})$",
                      re.S)
_ONLY_PUNCT = re.compile(r"^[\s.?¿!¡…\-—–_*/\\|#~]*$")
_ONLY_X = re.compile(r"^x+$", re.I)
_WORD = re.compile(r"[^\W\d_]+(?:['’][^\W\d_]+)*|\d+(?:[.,]\d+)*")


def is_placeholder(value) -> bool:
    """True for anything that was never really answered.

    None, empty lists/dicts, the EXACT values, a known placeholder prefix,
    `TODO…`, text made only of punctuation or x's, and any value that is
    wholly [bracketed], <angled>, {{templated}} — or (parenthesized) around a
    placeholder, like "(pendiente)"."""
    if value is None:
        return True
    if isinstance(value, bool):
        return False
    if isinstance(value, (list, tuple, set, dict)):
        return len(value) == 0
    s = str(value).strip()
    low = s.lower()
    if low in EXACT or _PREFIX.match(low) or _TODO.match(s):
        return True
    if _ONLY_PUNCT.match(s) or _ONLY_X.match(s):
        return True
    m = _WRAPPED.match(s)
    if m:
        if m.group("p") is not None:              # "(pendiente)", but not "(no tiene)"
            return is_placeholder(m.group("p"))
        return True                               # [template], <completar>, {{name}}
    return False


def word_count(value) -> int:
    return len(_WORD.findall(str(value or "")))


def too_short(value, words: int = 3) -> bool:
    """Fewer than `words` words: "Tímido." is not a personality."""
    return word_count(value) < words


def filled(value, min_chars: int = 0) -> bool:
    """Not a placeholder, and at least `min_chars` characters once stripped."""
    return not is_placeholder(value) and len(str(value).strip()) >= min_chars
