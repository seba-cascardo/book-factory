<!-- BEGIN computed by scripts/manuscript_gate.py — placeholder. The gate writes
round-N/REPORT.md from this template and replaces ONLY this block on every run:
verdict, convergence, open findings, coverage (never opened / partly read /
re-queued, and the waiver signature), what ran, subjects not fully audited, the
open-findings table, the dispatch list, round history. Never type these numbers. -->
<!-- END computed -->

<!--
Everything below is written by the orchestrator and survives every run. Fill only
what applies; an empty section with a one-line reason beats a deleted one — a
missing section reads like a check that found nothing.
-->

## Blocking findings — detail

<!-- One block per open critical/major, most severe first, after adversarial
verification. The key is the one in findings.jsonl. -->

### `<key>` — [one-line title]

- **Check · relation · severity:** MG-1 · D1 · critical · **Verifier:** CONFIRMED
- **P1** `final/unit-08.md:63` — > "[verbatim]"
- **P2** `final/unit-18.md:576` — > "[verbatim]"
- **Scopes:** [scope 1] · [scope 2] — **incompatible because:** […]
- **Canonical site** and **all other sites:** […] — a fix to one line of N is the
  defect this gate exists to prevent
- **Proposed fix:** […] — *proposed, not applied*
- **Verifier evidence:** path:line + quote; `searched_whole_chapter`, `other_occurrences`

---

## What was verified correct

<!-- DO NOT DELETE. N1, N2, D7a results: the only durable record that a question
was settled. Anything worth an anchor also goes to bible/do-not-touch.md and
bible/claim-index.yaml → verified_against. Why: docs/rationale/gate.md#positives -->

| Concept / rule | Sites | Verified against | Anchor? |
|---|---|---|---|
| | | `bible/sources/…:LINE` | yes/no |

---

## What was downgraded as inflated

<!-- DO NOT DELETE. Findings refuted or downgraded (`--resolve … --status
refuted`, verifier `corrected_severity`), with the counter-evidence. A round with
many findings and zero downgrades is a round to be suspicious of. -->

| Key | Reported as | Actually | Counter-evidence |
|---|---|---|---|
| | major | minor / not a defect | `path:line` + quote |

---

## Minor findings

<!-- Do not block. Grouped by kind for the human to decide. -->

## Deferred — could not be settled here

<!-- Not findings. Checkable ones were appended to reviews/verification-plan/PLAN.md;
list here the `human-decision` items, which go to the human. -->

| Question | Sites | Needs | Where it goes |
|---|---|---|---|

---

## Proposed fixed-defect entries

<!-- A critical/major marked fixed is a candidate for bible/fixed-defects.yaml. The
gate proposes, the human writes. Pin the CLAIM, not the code, and give the
teaching passage an `allow_in` anchor (templates/fixed-defects.yaml). -->

| Finding key | Proposed `forbid` | Scope | `allow_in` anchor needed? |
|---|---|---|---|

**New DO-NOT-TOUCH anchors this round:** [list, or "none"]

---

## What is still open

- **Waivers in force:** [each with reason and debt; the coverage waiver with its signature]
- **Next round:** [what is pending: edited subjects and their PROPAGATE siblings,
  the next unaudited slice, subjects with passes missing]

<!-- On the last round, this section becomes the done report: every unit archived,
the gate converged, claim index with no pending CHANGED, build verified, and the
open waivers and minors the human accepted. -->
