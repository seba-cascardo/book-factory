# Loopback Handoff — Structured Escalation

The retry cap in `pipeline.retry_cap` exists because uncapped loopbacks mean
"the pipeline and the human are both confused and neither is converging." At
that point, burning more agent tokens does not help — the human needs the
*right information* to decide what to do next.

A bare "ask the human" is too vague. On a cap hit the orchestrator produces a
**structured handoff packet**: a diff between attempts, one classified reason
for the failure, and three concrete options to pick from. This turns
escalation from a frustrating "it failed, over to you" into a useful "here is
what we tried, here is why each failed, here is what I would try next — pick
one."

## When the handoff is triggered

- `retries.by_unit[unit-NN] >= pipeline.retry_cap` (2 for `fast`, 3 for
  `full` and literary), AND
- the next verdict from the Technical Reviewer or Critic would NOT be PASS.

**The cap counts every loopback for the unit, from all sources**, so the
retry accounting on the packet must reconcile against `project-status.yaml →
runs`:

- Technical Reviewer → Writer cycles,
- Critic → any-agent REVISE/REWORK cycles,
- **Adversarial-Verify-confirmed REVISEs** — a finding confirmed by ≥2
  skeptics converts a Critic PASS into a REVISE, and that cycle spends one
  retry exactly like a Critic REVISE. It appears in the timeline as its own
  entry (adversarial → REVISE → target),
- human-triggered rejections routed back to a named agent.

All four share one budget. A packet whose timeline omits an adversarial cycle
under-reports how much was tried and mis-diagnoses the failure pattern — count
them.

On the firing event the orchestrator pauses the pipeline for this unit,
produces `drafts/unit-NN/escalation.md` from
`templates/loopback-escalation.md`, and surfaces it to the human. No further
agent calls for this unit until the human responds.

## What the packet contains

`drafts/unit-NN/escalation.md` — follow the template exactly. The fields:

### 1. Summary block

Unit number, title, pipeline mode, cycles used, cap value.

### 2. Timeline

Every agent run and verdict, newest last, one line each — including any
adversarial cycle: `agent → verdict (one-line reason) → loopback target`.

### 3. Per-cycle diff

For each cycle:

- which agent ran,
- what the prior verdict asked it to fix,
- what it produced (link to the artifact — do not paste prose inline),
- diff summary vs. the prior cycle (file, sections touched, net +/− words),
- why this cycle did NOT satisfy the next gate.

This is the part that usually reveals the real problem: the diff shows "Writer
added 200 words of motivation" twice in a row and the Critic still failed on
motivation — which means the real problem is *not* motivation. The concept
may not be teachable here at all.

### 4. Failure pattern (skill's diagnosis)

Classify the escalation by shape. One and only one of:

- **thrashing_on_same_hit** — the same rubric item fails every cycle; each
  attempted fix regresses a different item. Signal: the problem is not what
  the Critic named.
- **diverging_attempts** — each cycle addresses the hit but introduces new
  issues. Signal: the unit is not well bounded; the outline beat is too big.
- **insufficient_grounding** — the unit keeps hitting "claim unverifiable" or
  "model unclear" and no amount of rewriting resolves it. Signal:
  `bible/sources/` is missing the right source, OR Writer + Reviewer lack
  expertise on this topic. (For scientific-paper this is often an
  `unverifiable` claims-map entry the pipeline cannot ground.)
- **outline_level_flaw** — a forward reference that cannot be satisfied
  because the concept truly has not been taught yet. Signal: Knowledge Graph
  gap; the outline needs revision upstream.
- **prose_vs_content_mismatch** — the Critic keeps routing to the Humanizer
  but the issue is structural (or the reverse). Signal: the loopback rules
  misclassified the problem.
- **unclassified** — rare. Describe what was observed; ask the human to
  categorize.

### 5. Three concrete options

Propose three — not more, not fewer. Each option carries:

- **What happens next** (1–2 sentences),
- **Cost estimate** (which agents re-run; rough token cost as a multiplier of
  a normal cycle),
- **Risk** (what goes wrong if this is the wrong pick).

The three are usually shaped by the failure pattern:

| Pattern | Typical options |
|---|---|
| thrashing_on_same_hit | (a) revisit the voice-profile/style budget the item counts against — it may be self-contradictory; (b) rewrite the unit with a narrower scope; (c) escalate to the bible — the style guide or rubric weighting may be fighting itself. |
| diverging_attempts | (a) split the unit into two; (b) Writer re-drafts with an explicit scope list; (c) the human drafts the contentious section inline. |
| insufficient_grounding | (a) add a source to `bible/sources/`; (b) SME session with the human to capture verbal context; (c) downgrade the claim to hedged language and move on. |
| outline_level_flaw | (a) revise the outline (introduce the missing concept earlier); (b) add a primer section within this unit; (c) merge two units. |
| prose_vs_content_mismatch | (a) re-run with corrected loopback routing; (b) the human overrides the gate on this unit; (c) switch pipeline mode for this unit. |
| unclassified | (a) run one more cycle manually; (b) the human decides; (c) archive the draft and restart fresh. |

If none of the templated options fit, replace them — but always exactly
three, always concrete.

### 6. What the skill recommends

One paragraph, one recommendation, an explicit trade-off. It forces the skill
to take a position rather than hedge. The human can override.

## Human responses

The human edits `drafts/unit-NN/escalation.md` under `## Human decision`:

- `chose: a | b | c` — proceed with the picked option.
- `chose: custom` — a prose description of what to do instead.
- `chose: pause` — park the unit; the orchestrator marks it `on_hold` in
  `project-status.yaml` and unblocks the rest of the project to continue.

After the response:

- `retries.by_unit[unit-NN]` resets to 0 — the chosen path is a fresh attempt,
  not a continuation of the failed ones.
- The escalation is logged in `retries.cap_hits` and under `notes:` in
  `project-status.yaml`.
- The pipeline resumes per the chosen option.

## Why three options, not one

One option is a command; the human accepts or not, with no grounding. Three
options force the skill to show the *space* of responses. The human often
picks option (b) with a modification — "(b), but also do what (a) suggested
for the grounding library." That is the point: the three-option form invites a
real decision instead of a rubber-stamp.

## Example escalation (abridged)

```
# Escalation — unit-07: Set Analysis Deep Dive

Mode: fast. Cycles used: 2 / 2. Next verdict would be cycle 3.

## Timeline
- Cycle 1: Writer → Tech Reviewer REVISE (mental-model break) → Writer
- Cycle 2: Writer → Tech Reviewer PASS → Editor → Humanizer → Critic PASS
           → Adversarial REVISE (2 skeptics: section 3 confuses the target
           reader) → Humanizer
- Cycle 3 (blocked): retry cap reached.

## Failure pattern
thrashing_on_same_hit. The reader-confusion flag survives both rewrites; the
Humanizer each time adds explanatory prose, which the Critic then flags as
signposting. The unit is fighting itself.

## Options
### (a) Rebalance the style budget
Loosen the signposting budget for this unit in voice-profile.md. Fast; risks
shipping signposty prose.
### (b) Split the unit
unit-07a (basics) + unit-07b (indirect analysis). Medium cost (rewrite both);
addresses the real density problem.
### (c) Human drafts section 3 inline
You write the confusing section; the pipeline resumes at Tech Review.
Cheapest; depends on your bandwidth.

## Recommendation
(b). The thrashing says the section is too dense, not too signposty. Splitting
gives both halves room to motivate before teaching.
```

Concise, diagnostic, actionable — not a dump.
