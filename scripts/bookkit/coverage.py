#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Coverage — which subjects of each agent check have been audited, at which text.

Two files, both under `reviews/manuscript-gate-<run>/`:

- `round-N/coverage-<check>.json` — written by an emitter (MG-1 dossiers, MG-2
  rules) each round: EVERY eligible subject with the hash of what an audit of it
  would read, what was emitted this round, what was skipped as already audited,
  and the ranked cut. `eligible` is post-filter: noise in the denominator
  inflates the percentage in the comfortable direction.
- `subjects.json` — the manifest the gate keeps, keyed by content id. States:
  `pending`, `audited@<hash>`, `sampled@<hash>`. An edit changes a subject's hash
  and sends it back to `pending`; emitters skip what is audited at the current
  hash, so each round drains the next slice instead of re-reading the last one.

Why: docs/rationale/gate.md#coverage.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path


def composite_fingerprint(parts: list[str]) -> str:
    """One id over everything an audit of a subject read (order-insensitive)."""
    joined = "\n".join(sorted(p for p in parts if p))
    return hashlib.sha1(joined.encode("utf-8")).hexdigest()[:12]


@dataclass
class Subject:
    """One auditable unit of an agent check: a rule, a concept, a unit, the book."""
    id: str
    hash: str
    stratum: str = ""
    rank: int = 0
    instances: int = 0
    sampled: bool = False      # the emitted file is a SAMPLE of the subject
    site: str = ""

    def as_dict(self) -> dict:
        return {"id": self.id, "hash": self.hash, "stratum": self.stratum,
                "rank": self.rank, "instances": self.instances,
                "sampled": self.sampled, "site": self.site}


# ---------------------------------------------------------------------------
# The manifest
# ---------------------------------------------------------------------------


def load_manifest(path: str | Path | None) -> dict[str, dict[str, dict]]:
    """`{check: {subject_id: entry}}`; {} when absent."""
    if not path or not Path(path).exists():
        return {}
    doc = json.loads(Path(path).read_text(encoding="utf-8") or "{}")
    return {k: dict(v or {}) for k, v in (doc.get("checks") or {}).items()}


def save_manifest(path: str | Path, checks: dict[str, dict[str, dict]]) -> None:
    doc = {"schema_version": "2.0",
           "generated_by": "scripts/manuscript_gate.py — do not hand-edit; delete to "
                           "re-audit everything",
           "checks": {k: dict(sorted(v.items())) for k, v in sorted(checks.items())}}
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(doc, indent=2, ensure_ascii=False, sort_keys=True),
                 encoding="utf-8")


def audited_at(entry: dict | None) -> str:
    """The hash a manifest entry was audited (or sampled) at; '' when pending."""
    state = str((entry or {}).get("state") or "")
    if state.startswith(("audited@", "sampled@")):
        return state.split("@", 1)[1]
    return ""


def partition(subjects: list[Subject], manifest: dict[str, dict]
              ) -> tuple[list[Subject], list[str], list[str]]:
    """Split eligible subjects against the manifest for one check.

    Returns `(pool, already_audited_ids, requeued_ids)`. `already` leave the POOL,
    never the denominator; `requeued` were audited at a hash that no longer matches.
    """
    pool: list[Subject] = []
    already: list[str] = []
    requeued: list[str] = []
    for s in subjects:
        at = audited_at(manifest.get(s.id))
        if at and at == s.hash:
            already.append(s.id)
            continue
        if at:
            requeued.append(s.id)
        pool.append(s)
    return pool, sorted(already), sorted(requeued)


# ---------------------------------------------------------------------------
# The per-round record an emitter writes
# ---------------------------------------------------------------------------


@dataclass
class CoverageRecord:
    check: str
    round: int = 1
    language: str = ""
    pack: str | None = None            # language pack used, None = none for this language
    mode: str = ""                     # e.g. "lexicon" | "language-agnostic"
    eligible: list[Subject] = field(default_factory=list)
    emitted: list[str] = field(default_factory=list)
    already_audited: list[str] = field(default_factory=list)
    requeued: list[str] = field(default_factory=list)
    cut: list[dict] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    blocked: str = ""                  # non-empty = the check could not run

    def as_dict(self) -> dict:
        return {"check": self.check, "round": self.round, "language": self.language,
                "pack": self.pack, "mode": self.mode,
                "eligible": [s.as_dict() for s in self.eligible],
                "emitted": self.emitted, "already_audited": self.already_audited,
                "requeued": self.requeued, "cut": self.cut, "notes": self.notes,
                "blocked": self.blocked}

    def write(self, path: str | Path) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(self.as_dict(), indent=2, ensure_ascii=False,
                                sort_keys=True), encoding="utf-8")

    def report_line(self, noun: str) -> str:
        n = len(self.eligible)
        seen = len(self.already_audited) + len(self.emitted)
        tail = f" · {len(self.requeued)} re-queued (edited since audit)" if self.requeued else ""
        return f"{self.check}: {seen}/{n} {noun}(s) audited or emitted this round{tail}"


def coverage_path(round_dir: str | Path, check: str) -> Path:
    return Path(round_dir) / f"coverage-{check}.json"


def add_coverage_args(parser) -> None:
    """The flags every subject-emitting script accepts."""
    parser.add_argument(
        "--coverage", metavar="PATH", default=None,
        help="Write the round's coverage record here (round-N/coverage-<check>.json).")
    parser.add_argument(
        "--subjects", metavar="PATH", default=None,
        help="The gate's subjects manifest (reviews/manuscript-gate-<run>/subjects.json). "
             "Subjects audited at their current hash are skipped — they leave the pool, "
             "not the denominator.")
