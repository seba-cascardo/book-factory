# Critique Report Template (v2.3 — rubric-driven)

Used by the Critic agent (both literary and technical). The header block
is strict — the skill parses it to decide loopback routing. Everything
after the header is human-readable.

Save to `drafts/ch-[NN]/critique.md`. The machine-readable truth lives
in `drafts/ch-[NN]/scorecard.yaml` (see `templates/critique-scorecard.yaml`
and `references/rubric.md`). THIS file renders the scorecard for humans;
it does NOT replace it.

The verdict is **computed** from the scorecard — the Critic does not
choose it freely. See `references/rubric.md` § "How the verdict is
computed". This template includes a sanity-check block to surface the
computation.

The canonical mapping from problem TYPE → loopback target lives in
`references/pipeline.md` under "Loopback rules". Rubric items carry
their own `loopback_target` field; the ambiguity rules in `rubric.md`
resolve conflicts.

The set of valid loopback targets depends on `pipeline.mode` (technical
only). In **fast mode** the per-chapter loop is Writer → Technical
Reviewer → Editor → Critic, so the valid targets are **Writer** and
**Editor**. In **full mode** the loop is Writer → Technical Reviewer →
Editor → Humanizer → Reader-POV → Critic, so the valid targets are
**Writer**, **Editor**, **Humanizer**, and **Reader-POV + Humanizer**.
Literary mode always runs the full loop.

---

```markdown
# Critique: Chapter NN — [title]

## Verdict: PASS | REVISE | REWORK | ESCALATE
(computed from scorecard.yaml — see below)

## Loopback target (if REVISE): [Writer | Editor | Humanizer | Reader-POV + Humanizer | null]
## Loopback rationale: [one sentence — the failing item(s) that drove the target]

## Cycle count
This is cycle [N] of at most `pipeline.retry_cap` from `bible/meta.yaml`
(default 2 in fast mode, 3 in full mode). The current count is [N].

## Pipeline mode: [fast | full]   ← technical only; omit for literary

---

## Scorecard summary

| Severity    | Pass | Fail | N/A |
|-------------|-----:|-----:|----:|
| critical    |  [N] |  [N] | [N] |
| significant |  [N] |  [N] | [N] |
| minor       |  [N] |  [N] | [N] |

Full scorecard: `drafts/ch-NN/scorecard.yaml`.

## Failing items

<!-- One row per fail. If PASS, write "(none)". -->

| id             | name                                       | severity     | loopback target | evidence (short) |
|----------------|--------------------------------------------|--------------|-----------------|------------------|
| scope-1        | Chapter delivers the outline purpose       | critical     | Writer          | [quote/line]     |
| voice-3        | Anti-mediocrity Layer 2 density            | significant  | Humanizer       | [top offender]   |

## Verdict computation (sanity check)

<!-- Paste the rule that led to this verdict. One line. Must match the
     rule in rubric.md § "How the verdict is computed". If the rule
     says PASS but a rubric item failed, the scorecard is wrong — fix
     it, don't override. -->

- Computed rule: [e.g., "≥1 critical fail → REWORK"; "only minor fails → PASS with notes"]

---

## Observations

<!-- Free-form. Things that aren't rubric items but worth flagging.
     These do NOT affect the verdict; they're human-facing signal.

     Examples:
     - "Voice in § 3 is slightly more casual than calibration. Worth
        watching in ch-NN+1."
     - "This chapter opens a new forward reference to 'deferred
        actions' — confirm it's slated for ch-12 per the outline."
     - "fast mode: six Layer-2 microhits clustered in § 2. Not enough
        to block; worth sweeping in the polish pass." -->

## Unresolved notes for the human (even if PASS)

- [minor items worth flagging but not blocking]
- [Axis B skip note if `bible/sources/` was empty — the Tech Reviewer's
  report will have flagged this; propagate it here so the human sees it
  at approval time]
- [Fast mode: the microhit count the polish pass should sweep up, if
  any]
- [Knowledge Graph deltas — if this chapter reinforced or introduced a
  concept that doesn't match what the outline entry declared, name the
  delta and propose resolution (tracker update, outline revision,
  graph revision).]

## Specific loopback instructions (if REVISE or REWORK)

<!-- Target agent, specific files/lines to address, what "good" looks
     like. This is what gets passed to the looped agent as their
     instruction. -->

**To [target agent]:**
- Address [item id]: [specific change needed]
- Address [item id]: [specific change needed]
- Leave alone: [any passing-but-interesting-looking item the skill
   shouldn't touch]
```
