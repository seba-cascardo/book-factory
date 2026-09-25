# Critique report template — the Critic's human-facing render

Save to `drafts/unit-NN/critique.md`. The **header block is strict**: the
orchestrator parses `## Verdict:` and `## Loopback target:` to route, so keep
field names and order exactly. The authority is `drafts/unit-NN/scorecard.yaml`;
this file renders it and adds Observations.

The verdict and target are computed per `references/rubric.md` — never chosen.
Valid targets: `Writer | Editor | Humanizer | escalate` (`none` on PASS).
Fill every `[bracket]`, delete the guidance comments; this is structure only —
never paste prose from here into a draft.

---

```markdown
# Critique: [unit label per the profile — Chapter NN / Article: title / Section: title]

## Most important problem: [one sentence, with location — written before scoring]
## Verdict: [PASS | REVISE | REWORK | ESCALATE]
## Loopback target: [Writer | Editor | Humanizer | escalate | none]
## Loopback rationale: [the failing row(s) that set the target; "none" on PASS]
## Cycle count: [N] of [pipeline.retry_cap]

---

## Scorecard

| Severity    | Pass | Fail | N/A |
|-------------|-----:|-----:|----:|
| critical    | [N]  | [N]  | [N] |
| significant | [N]  | [N]  | [N] |
| minor       | [N]  | [N]  | [N] |

**Verdict basis:** [the rule line from rubric.md that fired, e.g. ">=1 significant fail → REVISE"]

### Failing rows

<!-- Most severe first; "(none)" on a clean PASS. Counted rows show the number
     copied from checks.json. -->

| id | name | severity | target | evidence (short) |
|----|------|----------|--------|------------------|
| [id] | [what was checked] | [severity] | [target] | [quote / file:line / checks.json count] |

Full scorecard: `drafts/unit-NN/scorecard.yaml` · script counts: `drafts/unit-NN/checks.md`.

---

## Observations

<!-- Non-rubric signal; never affects the verdict. Praise only with a quoted
     line. Include: script counts you believe are wrong (with evidence — the row
     keeps the script's number), declared-vs-actual opening mismatches, drift to
     watch next unit. -->

- [observation]

**Voice-singularity impression:** [does this read like someone specific, or like
a competent generic writer of this register?]
- Most singular: > "[quote]" ([location])
- Most generic: > "[quote]" ([location])
<!-- Literary: 3 most singular + 3 most generic, quoted — they go to the human packet. -->

---

## Unresolved notes for the human

- [minor items; skips propagated from tech-review.md (Axis B/C, UNVERIFIED
  references, empty validation surface); knowledge-graph deltas]

---

## Specific loopback instructions (REVISE / REWORK)

<!-- "(not applicable)" on PASS / ESCALATE. -->

**To [target agent]:**
1. **First — the most important problem:** [what to change, where, and what
   "resolved" looks like]
2. [row id]: [the change and its location]
- Leave alone: [passing parts the agent must not touch]
```
