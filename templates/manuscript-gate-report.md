# Manuscript gate — [project name]

**Run:** `reviews/manuscript-gate-<YYYY-MM-DD>/` · **Round:** N of `max_rounds`

<!--
PASTE THE NEXT BLOCK FROM `round-N/coverage-summary.md`. Do not type it.

Everything between here and the end of "What ran" is COMPUTED by
scripts/manuscript_gate.py: the verdict, the coverage line, the per-check scope,
the sampling note. v3.1 left the sampling line as prose for an agent to fill,
which made the honest number depend on an agent remembering — the same mechanism
the waivers section exists to eliminate.

Shape of what you paste:

**Verdict:** BLOCKED | NEEDS-REVISION | PASS-PARTIAL | PASS-SAMPLED | PASS
**Coverage:** MG-1 40/169 concepts · MG-2 60/474 rules (14 sampled) · MG-3 12/12 · MG-4 full
**Breadth signature:** `MG-1:40/169|MG-2:60/474|MG-3:12/12|MG-4:1/1`
**Depth signature:** `MG-1:0s/40|MG-2:14s/60|MG-3:0s/12|MG-4:0s/1`
**Convergence:** [N] consecutive round(s) with no new critical/major

Coverage has two axes and they mean different things:

- `PASS-PARTIAL` — there are subjects **nobody opened**. Closes by spending
  rounds: the emitters skip what `audited.yaml` records, so breadth grows
  monotonically. Waivable with `manuscript_gate.coverage`, and it should feel
  expensive.
- `PASS-SAMPLED` — every subject was opened, but some were judged from a
  **sample of themselves**. Closes by narrowing them in
  `bible/rule-probes-tuned.yaml` (worklist: `round-N/rule-probes-proposed.yaml`)
  or by raising a concept's `home_cap`. Waivable with `manuscript_gate.depth`,
  and on a large technical book waiving it is often the honest answer — some
  rules genuinely reach more instances than one agent run can judge.

Neither blocks the work. Both block the claim.
-->

<!--
The cumulative report. Regenerated each round; the per-round detail stays in
round-N/. Two sections here are easy to drop and must not be: "What was verified
correct" and "What was downgraded as inflated". See the notes at each.

Fill only what applies. An empty section with a one-line reason beats a deleted
one — a missing section reads identically to a check that found nothing, and
those are very different states.
-->

## What ran

<!-- Paste the table from round-N/coverage-summary.md. -->

| Check | Scope this round | Findings | Deferred | Status |
|---|---|---:|---:|---|
| MG-1 concept audit | | | | |
| MG-2 rule vs instances | | | | |
| MG-3 exercise vs content | | | | |
| MG-4 whole-book read | | | | |
| MG-5 render lint | all units, always complete | | — | |
| MG-6 executable code | surfaces, runner or waiver | | | |

## Depth — subjects read only in part

<!--
Computed; paste from coverage-summary.md. These count toward breadth — they were
opened — but each was judged from a SAMPLE of itself and may not be reported
clean. The table names the way out per check.

Narrowing a subject is a claim about its SCOPE, and it is auditable. If a rule
really does govern 87 code blocks across nine chapters, do not shrink it to make
the number go down: waive the depth and say so here. A narrowing written to reach
PASS is a lie the gate then repeats back as a clean bill of health.
-->

| Check | Sampled | Of covered | How to close it |
|---|---:|---:|---|
| | | | |

## What will NOT be looked at

<!--
Also computed, also pasted: the ranked cut list per check, from
coverage-summary.md.

Say it as a decision, not as a setting. "30 of 474" reads like configuration;
"444 candidate rules will not be looked at — 94% of the surface" reads like
something a person chose, which is what it is. The list is ranked so the human
can promote three specific candidates into the next round without recalibrating
anything.
-->

**Waived checks:** [each with its `waivers` entry id, or "none"]

**Coverage waivers:** [`manuscript_gate.coverage` (breadth) and/or
`manuscript_gate.depth`, each with its signature — or "none, both axes are
complete" / "none — another round is planned"]

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
decision). Anything reality could answer becomes a verification-plan entry
(references/verification-plan.md); only `human-decision` items stop here.
-->

| Question | Sites | Needs | Where it goes |
|---|---|---|---|

---

## Round history

| Round | New critical | New major | Resolved | Coverage | Verdict |
|---:|---:|---:|---:|---|---|
| 1 | | | | MG-1 x/y · MG-2 x/y | |

<!--
The coverage column is the one that tells you whether the loop is doing anything.
Two quiet rounds at the same coverage are not two quiet rounds — they are the
same round run twice, because rounds 2+ re-read the slice round 1 already read.
Coverage must GROW between rows, or the convergence criterion is being satisfied
by construction. It is read from `state.json`, which records it per round.
-->

## New DO-NOT-TOUCH and fixed-defect entries

<!--
A `critical` or `major` finding marked resolved is a candidate for
`bible/fixed-defects.yaml`: a defect that cost four passes to find should not be
able to walk back in silently. The gate PROPOSES the entry here; the human writes
and accepts it, because getting the `forbid` pattern right needs judgement.

Pin the CLAIM, not the code. The corrected text usually quotes the wrong form in
order to teach against it, so a literal pin on the expression fires on the fix
itself. Pin the conceptual frame that can only reappear if someone reintroduced
the wrong model, and give the teaching passage an `allow_in` anchor.
-->

| Finding | Proposed `forbid` | Scope | `allow_in` anchor needed? |
|---|---|---|---|
| | | | |

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
