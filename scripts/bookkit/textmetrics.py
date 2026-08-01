#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Text normalization, fingerprints, and near-duplicate similarity.

The similarity metric here is the single most consequential calibration in the
whole toolkit, so the measurement that produced it is recorded inline rather
than in a design doc that will drift away from the code.
"""

from __future__ import annotations

import hashlib
import re

# ---------------------------------------------------------------------------
# Normalization and fingerprints
# ---------------------------------------------------------------------------


def normalize(text: str) -> str:
    """Canonical form for fingerprinting and term extraction.

    Code spans go out because `Aggr()` vs `aggr()` is a style question, not a
    different claim. Markdown marks go out because bolding a word does not
    change what the sentence asserts.
    """
    t = re.sub(r"`[^`]*`", " ", text)      # code spans
    t = re.sub(r"[*_#>|]", " ", t)         # markdown marks
    t = re.sub(r"[^\w\s]", " ", t)         # punctuation
    return re.sub(r"\s+", " ", t).strip().lower()


def fingerprint(text: str) -> str:
    """Stable 12-hex id of a passage's normalized text.

    This is the durable key of the claim index — not the line number. When a
    passage MOVES the fingerprint survives and the validator repairs the line;
    when a passage is EDITED the fingerprint disappears and every sibling gets
    flagged. That asymmetry is the incomplete-fix detector, and the reason the
    index cannot go stale the way a hand-ticked checklist does.
    """
    return hashlib.sha1(normalize(text).encode("utf-8")).hexdigest()[:12]


# ---------------------------------------------------------------------------
# Similarity
# ---------------------------------------------------------------------------
#
# MEASURED (2026-07-30, 18-chapter technical book, ~156k words). The obvious
# design — 8-word shingles with Jaccard >= 0.8 — finds ZERO clusters on real
# prose. The three twin passages of a known incomplete fix scored 0.037, 0.000
# and 0.000 against each other. A well-written book REPHRASES instead of
# repeating, so n-gram overlap is nil even when the claim is identical.
#
# What does separate is Jaccard over content terms with stopwords removed:
#     real twins        0.111 – 0.359
#     random pairs      median 0.038, p95 0.103, p99 0.154, max 0.291
#
# The separation is imperfect on purpose, and worth stating: the weakest true
# twin (0.111) falls between the p95 and the p99 of the noise. Hence a LOW
# threshold, and hence the cluster is a SIGNAL FOR THE AUDITOR, never a verdict.
# A false positive costs one extra pair to read; a false negative loses the
# defect entirely. Those are not symmetric, so the threshold leans toward noise.

RELATED_THRESHOLD = 0.12
RELATED_TOP_K = 5

# English stopwords. `stopwords_for()` resolves the right set from the project's
# `language_variant`; anything not listed falls back to English, which is a safe
# degradation — an unfiltered stopword just adds a constant to both sides of the
# Jaccard and slightly compresses the range.
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

_STOPWORDS_BY_LANG = {
    "en": STOPWORDS_EN,
    "en-us": STOPWORDS_EN,
    "en-gb": STOPWORDS_EN,
    "es": STOPWORDS_ES,
    "es-ar": STOPWORDS_ES,
    "es-es": STOPWORDS_ES,
}


def stopwords_for(language_variant: str | None) -> set[str]:
    """Stopword set for a project's `meta.yaml → conventions.language_variant`.

    Unknown variants get English rather than an empty set: an empty set makes
    every pair look similar (articles and prepositions dominate the term
    overlap), which floods the auditor with noise pairs.
    """
    if not language_variant:
        return STOPWORDS_EN
    key = str(language_variant).strip().lower()
    if key in _STOPWORDS_BY_LANG:
        return _STOPWORDS_BY_LANG[key]
    return _STOPWORDS_BY_LANG.get(key.split("-")[0], STOPWORDS_EN)


def content_terms(text: str, stopwords: set[str] | None = None) -> set[str]:
    """Content words of a passage: normalized, stopword-free, longer than 2."""
    sw = STOPWORDS_EN if stopwords is None else stopwords
    return {w for w in normalize(text).split() if w not in sw and len(w) > 2}


def jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def shingles(text: str, k: int = 8) -> set[str]:
    """K-word shingles. Kept for diagnostics only — see the calibration note
    above for why this is NOT the similarity metric. Useful when you want to
    demonstrate to someone that verbatim repetition is not what you are looking
    for."""
    w = normalize(text).split()
    if len(w) < k:
        return {" ".join(w)} if w else set()
    return {" ".join(w[i:i + k]) for i in range(len(w) - k + 1)}


def related_pairs(texts: list[str],
                  stopwords: set[str] | None = None,
                  threshold: float = RELATED_THRESHOLD,
                  top_k: int = RELATED_TOP_K
                  ) -> tuple[list[tuple[float, int, int]], dict[int, list[tuple[float, int]]]]:
    """Similarity graph over passages.

    Returns (pairs sorted by score desc, top-K neighbours per index).

    PAIRS, not connected components. With a threshold this low the transitive
    closure collapses a whole chapter into one 30-passage "cluster", which tells
    an auditor nothing. A pair does: "these two make the same claim, and one was
    touched in a fix run and the other wasn't" is directly actionable.
    """
    terms = [content_terms(t, stopwords) for t in texts]
    n = len(texts)
    neighbours: dict[int, list[tuple[float, int]]] = {i: [] for i in range(n)}

    for i in range(n):
        for j in range(i + 1, n):
            s = jaccard(terms[i], terms[j])
            if s >= threshold:
                neighbours[i].append((s, j))
                neighbours[j].append((s, i))

    for i in range(n):
        neighbours[i] = sorted(neighbours[i], reverse=True)[:top_k]

    pairs: list[tuple[float, int, int]] = []
    seen: set[tuple[int, int]] = set()
    for i in range(n):
        for s, j in neighbours[i]:
            key = (min(i, j), max(i, j))
            if key not in seen:
                seen.add(key)
                pairs.append((s, key[0], key[1]))
    pairs.sort(reverse=True)
    return pairs, neighbours
