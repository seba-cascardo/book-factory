#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Text normalization, fingerprints, and near-duplicate similarity.

The similarity metric is the most consequential calibration in the toolkit; the
measurement behind it is summarized below and told in full in
docs/rationale/gate.md#similarity.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata

# ---------------------------------------------------------------------------
# Normalization and fingerprints
# ---------------------------------------------------------------------------

_CODE_SPAN = re.compile(r"`[^`]*`")


def _prose_form(text: str) -> str:
    t = re.sub(r"[*_#>|]", " ", text)      # markdown marks
    t = re.sub(r"[^\w\s]", " ", t)         # punctuation
    return re.sub(r"\s+", " ", t).strip().lower()


def normalize(text: str) -> str:
    """Canonical form for TERM extraction and similarity (not for fingerprints).

    Code spans go out: `Aggr()` vs `aggr()` should not make two passages look
    unrelated. Markdown marks and punctuation go out; case folds.
    """
    t = unicodedata.normalize("NFC", text)
    return _prose_form(_CODE_SPAN.sub(" ", t))


def fingerprint_form(text: str) -> str:
    """What a fingerprint hashes: prose folded, code spans kept VERBATIM.

    A fix to `Peek(v,-1)` → `Peek(v,1)` is the most common fix in a technical book.
    A fingerprint that dropped code spans, operators and case called that passage
    unchanged, so the claim index never said CHANGED and the audit never
    re-queued it. Prose still folds (a bolded word does not change a claim);
    code does not (a sign does).
    """
    t = unicodedata.normalize("NFC", text)
    parts: list[str] = []
    last = 0
    for m in _CODE_SPAN.finditer(t):
        parts.append(_prose_form(t[last:m.start()]))
        parts.append(re.sub(r"\s+", " ", m.group(0)).strip())
        last = m.end()
    parts.append(_prose_form(t[last:]))
    return " ".join(p for p in parts if p)


def fingerprint(text: str) -> str:
    """Stable 12-hex id of a prose passage.

    The durable key of the claim index — not the line number. A passage that
    MOVES keeps its fingerprint and the validator repairs the line; a passage
    that is EDITED loses it and every sibling gets flagged.
    """
    return hashlib.sha1(fingerprint_form(text).encode("utf-8")).hexdigest()[:12]


def fingerprint_code(body: str) -> str:
    """Stable id of a code block: whitespace collapsed, everything else verbatim."""
    t = re.sub(r"\s+", " ", unicodedata.normalize("NFC", body)).strip()
    return hashlib.sha1(t.encode("utf-8")).hexdigest()[:12]


def text_hash(text: str) -> str:
    """Hash of a whole text (the manuscript), for MG-3/MG-4/MG-C subjects."""
    return hashlib.sha1(unicodedata.normalize("NFC", text).encode("utf-8")).hexdigest()[:12]


# ---------------------------------------------------------------------------
# Similarity
# ---------------------------------------------------------------------------
#
# MEASURED on an 18-chapter technical book: n-gram shingles find ZERO clusters on
# real prose (a good book rephrases). Jaccard over content terms separates:
# real twins 0.111–0.359; random pairs p95 0.103, p99 0.154. Hence a LOW
# threshold, and the pair is a SIGNAL for the auditor, never a verdict.

RELATED_THRESHOLD = 0.12
RELATED_TOP_K = 5

STOPWORDS_EN = set("""
a an the is are was were be been being of in on at to for with by from as it its
this that these those and or but not no if then than so such there here you your
we our they their them can could may might must will would shall should do does
did done have has had having what which who whom when where why how all any both
each few more most other some only own same very just also into out up down over
under again further once about against between through during before after above
below what's don't won't cannot
""".split())

STOPWORDS_ES = set("""
el la los las un una unos unas de del al a en con por para sin sobre entre hasta
desde y o u pero si no ni que qué cual cuál quien quién cuando cuándo donde dónde
como cómo porque es son era eran ser sido siendo está están estar estado hay ha
han había habían se le les lo su sus mi mis tu tus nuestro nuestra este esta esto
ese esa eso aquel aquella más menos muy también sólo solo todo toda todos todas
otro otra cada algún alguna ya aún tras ante bajo durante mediante
""".split())

_STOPWORDS_BY_LANG = {"en": STOPWORDS_EN, "es": STOPWORDS_ES}


def stopwords_for(language_variant: str | None, extra: list[str] | None = None) -> set[str]:
    """Stopwords for a language variant, plus a language pack's `stopwords`.

    Unknown languages get English rather than an empty set: an empty set makes
    every pair look similar and floods the auditor with noise.
    """
    key = str(language_variant or "en").strip().lower().replace("_", "-").split("-")[0]
    base = set(_STOPWORDS_BY_LANG.get(key, STOPWORDS_EN))
    return base | {str(w).lower() for w in (extra or []) if isinstance(w, str)}


def content_terms(text: str, stopwords: set[str] | None = None) -> set[str]:
    """Content words of a passage: normalized, stopword-free, longer than 2."""
    sw = STOPWORDS_EN if stopwords is None else stopwords
    return {w for w in normalize(text).split() if w not in sw and len(w) > 2}


def jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)
