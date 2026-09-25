"""bookkit — shared primitives for the book-factory deterministic checks.

Every script under `scripts/` imports from here rather than re-deriving
segmentation or similarity. That matters more than it looks: the checks have to
agree on what a "passage" is, or the claim index points at one thing and the
lint reports another.

Modules:
  segment      — markdown → line records (fences, heading paths, kinds)
  textmetrics  — normalize, fingerprint, content terms, Jaccard
  project      — locate the project, load meta.yaml, resolve units (incl. standalone)
  gitblame     — line → (sha, date), one subprocess call per file
  coverage     — how much of the eligible surface a round actually audited
  selection    — the ONE stratified quota, shared by every caller
"""

import sys as _sys

# Every script here prints em-dashes and arrows, and the default Windows console
# codepage is cp1252, which cannot encode them. Without this, running a check
# directly in a stock terminal dies with a UnicodeEncodeError halfway through its
# own report — the output most likely to be read by someone deciding whether the
# toolkit works at all.
for _stream in (_sys.stdout, _sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):  # pragma: no cover — redirected/exotic stream
        pass

from .segment import Record, segment, segment_text, FENCE_RE, KIND_BY_PREFIX
from .textmetrics import (
    normalize,
    fingerprint,
    content_terms,
    jaccard,
    stopwords_for,
)
from .project import Project, load_project
from .gitblame import blame_map

__all__ = [
    "Record",
    "segment",
    "segment_text",
    "FENCE_RE",
    "KIND_BY_PREFIX",
    "normalize",
    "fingerprint",
    "content_terms",
    "jaccard",
    "stopwords_for",
    "Project",
    "load_project",
    "blame_map",
]
