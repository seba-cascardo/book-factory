# Manuscript gate — [project name]

**Run:** `reviews/manuscript-gate-<YYYY-MM-DD>/` · **Round:** N of `max_rounds`
**Verdict:** `BLOCKED | NEEDS-REVISION | PASS`
**Convergence:** [N] consecutive round(s) with no new critical/major (need
`rounds_without_new_to_close`)

<!--
The cumulative report. Regenerated each round; the per-round detail stays in
round-N/. Two sections here are easy to drop and must not be: "What was verified
correct" and "What was downgraded as inflated". See the notes at each.

Fill only what applies. An empty section with a one-line reason beats a deleted
one — a missing section reads identically to a check that found nothing, and
those are very different states.
-->

## What ran

| Check | Scope this round | Findings | Deferred | Status |
|---|---|---:|---:|---|
| MG-1 concept audit | [N concepts × M lenses / propagation set only] | | | |
| MG-2 rule vs instances | [N rules, K instances judged] | | | |
| MG-3 exercise vs content | [N exercises] | | | |
| MG-4 whole-book read | [full manuscript / units changed] | | | |
| MG-5 render lint | [all units, always complete] | | — | |
| MG-6 executable code | [surfaces, runner or waiver] | | | |

**Sampling:** [any check that could not judge every instance — say which and how
much. A sampled run may never be reported as clean.]

**Waived checks:** [each with its `waivers` entry id, or "none"]

---

## Blocking findings

<!-- critical and major, adversarially verified, unresolved. Most severe first. -->

| ID | Relation | Severity | Sites | What is wrong | Fix scope |
|---|---|---|---|---|---|
| MG1-01 | | | canonical + all other_sites | | |

For each, below: the verbatim quotes, the two propositions, the scopes, the
verifier's verdict and evidence, and **every site that repeats the claim**. A
finding that names one line produces a fix that lands in one of N sites — the
defect this gate exists to eliminate.

### MG1-01 — [one-line title]

- **Relation:** D1 · **Severity:** critical · **Verifier:** CONFIRMED
- **P1** `final/unit-08.md:63` — > "[verbatim]"
- **P2** `final/unit-18.md:576` — > "[verbatim]"
- **Scope 1:** [in words] · **Scope 2:** [in words]
- **Incompatible because:** [why they cannot both hold]
- **Canonical site:** `[the one that should carry the definitive wording]`
- **All other sites:** `[complete list]`
- **Proposed fix:** [what to change, where] — *proposed, not applied*
- **Verifier evidence:** [path:line + quote; `searched_whole_chapter`,
  `other_occurrences`]

---

## What was verified correct

<!--
DO NOT DELETE THIS SECTION.

In the reference audit this held 81 clusters — nearly as many as the defects, and
as useful. It is where `N1`, `N2` and `D7a` results live, and it is the only
durable record that a question was asked and settled.

Its absence is what let a later fix pass reopen three settled items and introduce
a factual error into correct text. Anything worth an anchor also goes into
`bible/do-not-touch.md` and `bible/claim-index.yaml → verified_against`.
-->

| Concept / rule | Sites | Verified against | Anchor? |
|---|---|---|---|
| | | `bible/sources/…:LINE` | yes/no |

**New DO-NOT-TOUCH anchors this round:** [list, or "none"]

---

## What was downgraded as inflated

<!--
DO NOT DELETE THIS SECTION EITHER.

Review agents inflate. Measured on the reference case: six findings had to be
downgraded by hand after verification — one claimed a function was "never taught"
when the book explains it; another flagged a scope contradiction the chapter
announces in as many words.

This section is how you find out your auditors are running hot. A round with zero
downgrades and many findings is a round to be suspicious of, not proud of.
Record upgrades here too, in the other direction.
-->

| ID | Reported as | Actually | Counter-evidence |
|---|---|---|---|
| | major | minor / not a defect | `path:line` + quote |

---

## Minor findings

<!-- Do not block. Consolidated for the human to decide. Group by kind. -->

---

## Deferred — could not be settled here

<!--
Questions the auditors could not resolve from the available sources. These are
NOT findings, and turning one into a finding is how a review invents verdicts.

Each needs: what would settle it (a runner, a source the project lacks, a human
decision). Anything needing a runner belongs in the MG-6 test plan.
-->

| Question | Sites | Needs | Where it goes |
|---|---|---|---|

---

## Round history

| Round | New critical | New major | Resolved | Verdict |
|---:|---:|---:|---:|---|
| 1 | | | | |

**Anti-thrash check:** findings rejected by the human are persisted as
`do_not_touch` in `bible/claim-index.yaml` and are not re-reported. Rejected this
run: [N].

---

## What is still open

- **Unresolved critical:** [N] — blocks `complete`
- **Unresolved major:** [N] — blocks unless waived
- **Open waivers:** [each with reason and debt]
- **Next round scope:** [the propagation set: edited passages + their siblings +
  concepts with open findings]

<!--
If this is the last round and the verdict is PASS, this section becomes the
definition-of-done report: every unit archived, gate PASS with the convergence
criterion met, claim index with no pending CHANGED, build verified per target,
and the list of open waivers and unresolved minors that the human accepted.
-->
