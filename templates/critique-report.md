# Critique Report Template — the Critic's human-facing render

Used by the Critic in every profile. The **header block is strict**: the
orchestrator parses it to route loopbacks, so keep the field names and order
exactly as below. Everything after the header is human-readable.

Save to `drafts/unit-NN/critique.md`. The machine-readable truth lives in
`drafts/unit-NN/scorecard.yaml` (template `templates/scorecard.yaml`). THIS
file renders that scorecard for humans and adds Observations — it does NOT
replace it and carries no independent verdict authority.

The verdict is **computed** from the scorecard per
`references/rubric.md` § "Verdict computation — AUTHORITATIVE" — the Critic
does not choose it. The REVISE loopback target is likewise resolved from the
failing items (shared target → that target; split → highest-severity item's
target; tied → Writer), never picked by feel.

Valid loopback targets: `Writer | Editor | Humanizer |
Reader_POV_plus_Humanizer | escalate`. In nonfiction fast mode Reader-POV
does not run, so `Reader_POV_plus_Humanizer` cannot appear — a reader-confusion
fail routes to Writer there instead.

Fill every `[bracket]`; delete the guidance comments before saving. The blocks
below are STRUCTURE only — never paste model prose into a draft from here.

---

```markdown
# Critique: [unit label per the profile — Chapter NN / Article: title / Section: title]

## Verdict: [PASS | REVISE | REWORK | ESCALATE]
<!-- Copied from scorecard.yaml computed_verdict. If it disagrees with the
     item statuses, the items win — fix the items, do not override here. -->

## Loopback target: [Writer | Editor | Humanizer | Reader_POV_plus_Humanizer | escalate | none]
## Loopback rationale: [one sentence — the failing item(s) that drove the target; "none" on PASS]
## Cycle count: [N] of [retry_cap from bible/meta.yaml]

---

## Scorecard

<!-- Render scorecard.yaml. The failing-items table is the load-bearing part;
     the summary counts orient the human. -->

| Severity    | Pass | Fail | N/A |
|-------------|-----:|-----:|----:|
| critical    | [N]  | [N]  | [N] |
| significant | [N]  | [N]  | [N] |
| minor       | [N]  | [N]  | [N] |

**Computed-verdict basis:** [the single rule line from rubric.md that produced
the verdict — e.g. ">=1 significant fail → REVISE"; on a clean pass: "no fails
→ PASS"]

### Failing items

<!-- One row per fail, most severe first. If PASS with no fails, write "(none)".
     For rhet rows, the evidence MUST show the count. -->

| id        | name                              | severity    | loopback           | evidence (short)        |
|-----------|-----------------------------------|-------------|--------------------|-------------------------|
| [rhet-3]  | [Dramatic-danger lexicon quota]   | [significant] | [Humanizer]      | [count=4 (terms, lines)]|
| [item id] | [what was checked]                | [severity]  | [target]           | [quote / file:line]     |

Full scorecard: `drafts/unit-NN/scorecard.yaml`.

---

## Observations

<!-- Free-form, NON-rubric signal for the human. Does not affect the verdict.
     Cross-unit patterns, voice-risk commentary (literary craft-4), a microhit
     cluster the polish pass should sweep, a forward reference to confirm
     against the outline, an Axis B / grounding-empty note propagated from
     tech-review.md so the human sees it at approval time. -->

- [observation]
- [observation]

**Voice-singularity impression:** [one line — reading this unit cold, does it
read as THIS project's voice (fingerprint traits from voice-profile.md
present) or as "a competent generic writer in this register"? Name the single
most singular passage and the single most generic one. This is an impression,
not a rubric hit; consistency-1 / voice-4 already scored the mechanical part.
It exists to give the human an early signal before the every-5-unit
singularity audit runs.]

---

## Specific loopback instructions (if REVISE or REWORK)

<!-- The exact instruction handed to the looped agent. Address only the failing
     items; name files/lines; state what "resolved" looks like without writing
     the replacement prose. On PASS/ESCALATE write "(not applicable)". -->

**To [target agent]:**
- Address [item id]: [the specific change needed and where]
- Address [item id]: [the specific change needed and where]
- Leave alone: [any passing item the looped agent should not touch, to prevent
  collateral regressions]
```
