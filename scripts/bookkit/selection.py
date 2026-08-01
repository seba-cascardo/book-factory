#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Stratified selection under a quota — ONE function, shared by every caller.

Two failures this exists to prevent, both measured while building the real thing.

## 1. The gate must measure the artifact that ships

A first version verified that the calibration pairs appeared among the
*candidates*, while emission independently capped the output at 40. The two
calibration pairs ranked 199/205 and 153/211 — present in the candidate list,
absent from the dossier the auditor actually reads. The gate reported PASS on a
pass that was structurally broken.

The fix is trivial and structural: **one selection function, used by emission and
by any check on emission.** As long as there is only one, that failure cannot
come back. So: do not add a second ranking anywhere. Call this.

## 2. A constant bonus in a ranker is not a weight, it is a stratifier

A ranker that added +3.0 for "crosses units" onto a base scale of ~1–4 sorted
*every* cross-unit item above *every* intra-unit one. With 189 cross-unit
candidates out of 205, a quota of 40 emitted 40 cross-unit rules and **zero
intra-unit** ones — and the intra-unit failure mode is 7 of 10 defects, the
single thing the pass exists to catch. 74% of dossiers were saturated that way.

The lesson generalizes past ranking: **if a pass chases two failure modes, each
mode gets its own quota.** Blending them into one score lets the more numerous
mode starve the other, silently, and the output still looks full.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Sequence, TypeVar

T = TypeVar("T")


@dataclass
class Selection:
    """What was emitted, and — just as important — what was not."""
    emitted: list = field(default_factory=list)
    dropped: dict[str, int] = field(default_factory=dict)
    totals: dict[str, int] = field(default_factory=dict)
    quota: int = 0

    @property
    def dropped_total(self) -> int:
        return sum(self.dropped.values())

    def report_lines(self, noun: str = "item") -> list[str]:
        """Human-readable coverage note. Print it — a silent truncation reads as
        full coverage, and that is how a partial audit gets filed as clean."""
        out: list[str] = []
        for stratum, total in self.totals.items():
            kept = total - self.dropped.get(stratum, 0)
            out.append(f"{stratum}: {kept}/{total} {noun}(s) emitted")
        if self.dropped_total:
            out.append(f"NOT emitted: {self.dropped_total} {noun}(s) — coverage is "
                       f"partial and the report must say so")
        return out


def stratified_top(items: Sequence[T],
                   stratum_of: Callable[[T], str],
                   rank_within: Callable[[T], tuple],
                   quota: int,
                   weights: dict[str, float] | None = None) -> Selection:
    """Pick `quota` items, giving each stratum its own share.

    `weights` maps stratum → share of the quota; missing strata split what is
    left equally. Unused share is redistributed, so a stratum with three items
    does not waste a slot when the other stratum has forty waiting.

    `quota <= 0` means no cap: everything is emitted, and `dropped` is empty.
    Ranking still applies, because the ORDER matters to a reader working down a
    list even when nothing is cut.
    """
    buckets: dict[str, list[T]] = {}
    for item in items:
        buckets.setdefault(stratum_of(item), []).append(item)
    for key in buckets:
        buckets[key].sort(key=rank_within)

    totals = {k: len(v) for k, v in buckets.items()}

    if quota <= 0:
        ordered: list[T] = []
        for key in sorted(buckets):
            ordered.extend(buckets[key])
        return Selection(emitted=_interleave(buckets), dropped={}, totals=totals,
                         quota=0)

    weights = dict(weights or {})
    for key in buckets:
        weights.setdefault(key, 1.0)
    live = {k: w for k, w in weights.items() if k in buckets}
    total_w = sum(live.values()) or 1.0

    # First pass: proportional share, capped by what the stratum actually has.
    share: dict[str, int] = {}
    for key, w in live.items():
        share[key] = min(len(buckets[key]), int(quota * w / total_w))

    # Redistribute the remainder to strata that still have items. Round-robin so
    # no single stratum absorbs all of it — that would reintroduce the
    # starvation this function exists to prevent.
    remaining = quota - sum(share.values())
    hungry = [k for k in live if share[k] < len(buckets[k])]
    while remaining > 0 and hungry:
        for key in list(hungry):
            if remaining <= 0:
                break
            share[key] += 1
            remaining -= 1
            if share[key] >= len(buckets[key]):
                hungry.remove(key)

    picked = {k: buckets[k][:share[k]] for k in buckets}
    dropped = {k: len(buckets[k]) - len(picked[k]) for k in buckets
               if len(buckets[k]) > len(picked[k])}
    return Selection(emitted=_interleave(picked), dropped=dropped, totals=totals,
                     quota=quota)


def _interleave(buckets: dict[str, list]) -> list:
    """Round-robin across strata so the head of the output is not one stratum.

    Whoever reads only the first ten entries should see both failure modes.
    """
    out: list = []
    keys = sorted(buckets)
    i = 0
    while True:
        added = False
        for key in keys:
            if i < len(buckets[key]):
                out.append(buckets[key][i])
                added = True
        if not added:
            break
        i += 1
    return out
