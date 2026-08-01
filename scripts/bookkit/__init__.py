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
"""

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
