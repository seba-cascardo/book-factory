"""bookkit — shared primitives for the book-factory deterministic checks.

Every script imports from here rather than re-deriving segmentation or
similarity: the checks have to agree on what a "passage" is, or the claim index
points at one thing and the lint reports another.

Modules:
  textio       — the one file reader: UTF-8 ± BOM, NFC, cp1252 recorded not fatal
  segment      — markdown → line records (CommonMark fences, heading paths, kinds)
  textmetrics  — normalize, fingerprints (code spans kept verbatim), Jaccard
  project      — locate the project, load meta.yaml, resolve units, language
  gitblame     — line → (sha, date), one subprocess call per file
  coverage     — the subjects manifest and the per-round coverage record
  selection    — the ONE stratified quota, shared by every caller
  anchors      — resolve a reference by content (MOVED vs CHANGED)
  schema       — validate findings files (jsonschema, or a minimal fallback)
  lexicon      — per-language word lists from scripts/lexicons/
  placeholder  — what counts as "not filled in" (sheets, endings, ledger, waivers)
  verdict      — the rubric's verdict computation (references/rubric.md), in code
"""

import sys as _sys

# The default Windows console codepage (cp1252) cannot encode the em-dashes and
# arrows these scripts print; without this a stock terminal dies mid-report.
for _stream in (_sys.stdout, _sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):  # pragma: no cover — redirected/exotic stream
        pass

from .segment import Record, segment, segment_text, FENCE_RE, KIND_BY_PREFIX  # noqa: E402
from .textmetrics import (  # noqa: E402
    normalize, fingerprint, fingerprint_code, content_terms, jaccard, stopwords_for,
)
from .project import Project, load_project  # noqa: E402
from .gitblame import blame_map  # noqa: E402

__all__ = [
    "Record", "segment", "segment_text", "FENCE_RE", "KIND_BY_PREFIX",
    "normalize", "fingerprint", "fingerprint_code", "content_terms", "jaccard",
    "stopwords_for", "Project", "load_project", "blame_map",
]
