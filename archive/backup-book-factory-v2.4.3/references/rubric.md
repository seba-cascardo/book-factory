# Rubric-Driven Critic

v2.2 Critic produced a prose verdict — PASS / REVISE / REWORK / ESCALATE
— with a rationale paragraph. That works when the Critic is right. It
fails silently when the Critic is wrong: a single Opus model, tired at
the end of a long context, misses a rubric item and the chapter ships
with the error. The human, reading the Critic's summary, has no visible
way to check *what was checked* — only that the verdict says PASS.

v2.3 replaces the prose verdict with a **rubric scorecard**: an explicit
list of checks, each with its own pass/fail and evidence. The overall
PASS is derived from the scorecard, not asserted as a standalone
judgment.

This kills two failure modes:

1. The Critic skipping a check because it was vibes-satisfied and
   forgetting to mention it.
2. The human rubber-stamping a verdict because reading a prose summary
   feels like review even when it isn't.

The prose summary doesn't go away — it's still in `critique.md` as an
"Observations" section — but the verdict is computed from the scorecard.

## The scorecard shape

The Critic writes `drafts/ch-NN/critique.md` using the template at
`templates/critique-report.md` (v2.3 updated shape), plus
`drafts/ch-NN/scorecard.yaml` using `templates/critique-scorecard.yaml`.

The scorecard is the machine-readable truth. `critique.md` renders it
for humans.

Every scorecard entry has:

- `id` — stable identifier
- `rubric` — which family (scope | outline | tech_a | tech_b | pedagogy |
  voice | reader_pov | code | consistency | forward_refs)
- `name` — one-line description of what was checked
- `severity` — critical | significant | minor
- `status` — pass | fail | not_applicable
- `evidence` — for fails: quoted lines, file:line, or one-sentence
  diagnosis. For passes: optional.
- `loopback_target` — for fails: Writer | Editor | Humanizer |
  Reader_POV_plus_Humanizer | escalate.

## How the verdict is computed

```
if any rubric item with severity=critical is fail:
    verdict = REWORK (if ≥2 critical fails) OR REVISE (if exactly 1)
elif any rubric item with severity=significant is fail:
    verdict = REVISE
elif any rubric item with severity=minor is fail:
    verdict = PASS, with notes
else:
    verdict = PASS
```

For REVISE, the loopback target is determined by the failing items:

- If all failing items share the same loopback target → that target.
- If failing items split across targets → the one with the highest
  severity item; if tied, Writer (content > structure > prose).
- If any item has `loopback_target: escalate` → ESCALATE.

This rule is deterministic. The Critic doesn't choose the verdict; the
verdict falls out of the scorecard.

## The rubric families (technical chapter)

The Critic runs every applicable item. Items marked (mode-sensitive) run
only in the mode noted.

### `scope`
- `scope-1` — Chapter delivers the outline `purpose`. **critical**.
- `scope-2` — No topics declared out-of-scope surface in this chapter. **significant**.
- `scope-3` — Depth matches `scope.depth` (tutorial | reference | …). **significant**.

### `outline`
- `outline-1` — All `concepts_introduced` from the outline entry are
  actually introduced in the chapter. **critical**.
- `outline-2` — All `concepts_used` appear in earlier chapters, current
  chapter's `concepts_introduced`, or prerequisites. **critical**.
  (Enforces Knowledge Graph integrity at chapter time.)
- `outline-3` — Section structure matches the outline's sections; any
  added/removed section is flagged. **significant**.
- `outline-4` — Exercises (if `outline.has_exercises`) are solvable with
  concepts introduced ≤ this chapter. **significant**.

### `tech_a` — Claims, code, versions
- `tech_a-1` — Every Axis A finding in `tech-review.md` was either
  addressed in the chapter or carried as an explicit advisory note.
  **critical**.
- `tech_a-2` — Code snippets in the chapter pass the declared
  validation surface's sub-prompt(s). **critical**.
- `tech_a-3` — Pinned versions referenced in the chapter match
  `meta.yaml:pinned_versions`. **significant**.
- `tech_a-4` — No "invented" APIs/functions/commands (every identifier
  cross-references to grounding library OR is flagged as advisory).
  **significant**.

### `tech_b` — Mental models, terminology
- `tech_b-1` — No Axis B "broken framing" from `tech-review.md` survives
  unresolved. **critical**.
- `tech_b-2` — Glossary terms are used consistently (no synonym cycling
  on load-bearing terms). **significant**.
- `tech_b-3` — Version-drift items from `tech-review.md` are correctly
  classified (not sent as errors where the `version drift rule` applies).
  **significant**.

### `pedagogy`
- `pedagogy-1` — Each section motivates before mechanizing (why before
  how). **significant**.
- `pedagogy-2` — Examples come after the concept they illustrate (not
  before). **significant**.
- `pedagogy-3` — Chapter ends with concrete recap ("you can now do X")
  or a bridge to next chapter. Generic summary = fail. **minor**.
- `pedagogy-4` — No undeclared forward references (every "we'll cover
  this later" paid off later or declared in continuity tracker).
  **significant**.

### `voice` (full mode: strict; fast mode: tolerant on microhits)
- `voice-1` — Person (you/we/impersonal) matches `meta.yaml` and stays
  consistent. **significant**.
- `voice-2` — Anti-mediocrity Layer 1 (Content) hits: 0 is target, 1–2
  tolerated in fast mode only. **significant**.
- `voice-3` — Anti-mediocrity Layer 2 (Language / AI-isms) density
  within mode tolerance. **significant** (full) / **minor** (fast).
- `voice-4` — Anti-mediocrity Layer 3 (Style) signposting absent.
  **significant**.
- `voice-5` — Anti-mediocrity Layer 4 (Communication artifacts)
  absent. **critical** — chatbot artifacts are a hard fail.
- `voice-6` — Anti-mediocrity Layer 5 (Filler/Hedging) within tolerance.
  **minor**.
- `voice-7` — Voice matches calibration passages in
  `bible/style-guide.md`. **significant**.

### `reader_pov` (full mode only)
- `reader_pov-1` — No comprehension failure flagged in
  `reader-report.md` survives unaddressed. **critical**.
- `reader_pov-2` — No "reader would close the book here" flag
  unaddressed. **critical**.
- `reader_pov-3` — Outcome match: reader finishes able to do what the
  outline promised. **critical**.

### `code`
- `code-1` — Every snippet has labeled input / expected output. **significant**.
- `code-2` — Snippets are minimal (no decorative scaffolding). **minor**.
- `code-3` — Code style matches `meta.yaml:conventions`. **minor**.

### `consistency`
- `consistency-1` — Voice matches prior chapter (based on the prior
  chapter's digest calibration sample). **significant**.
- `consistency-2` — Terminology matches prior chapters (via digests +
  continuity-tracker). **significant**.

### `forward_refs`
- `forward_refs-1` — This chapter pays off every forward ref from prior
  chapters that the outline assigned here. **critical**.
- `forward_refs-2` — New forward refs are recorded in the chapter's
  digest (will be, post-approval) and flagged. **minor**.

## The rubric for literary chapters

Literary mode uses a different rubric. Families:

- `scope` (plot beats) — chapter delivers the beat(s) the outline
  assigned to it.
- `character` — every POV character acts consistently with their sheet.
- `arc` — scene-level arcs advance the larger character/thematic arcs.
- `voice` — full anti-mediocrity-literary coverage (no AI-isms,
  voice matches calibration, dialogue character-specific).
- `reader_pov` — comprehension, pacing, emotional beats land.
- `continuity` — no contradictions with tracker, timeline, world.

The literary rubric is in this file under the section above
(`## The rubric for literary chapters`). Same scorecard schema and
verdict-computation rule as the technical rubric — only the rubric
items differ. Technical projects evaluate only `## The rubric families
(technical chapter)`; literary projects evaluate only the literary
section. The Critic loads its mode from `bible/meta.yaml:project.type`.

## Tolerance levels per mode

| Severity    | Fast mode — action                                | Full mode — action                                |
|-------------|----------------------------------------------------|----------------------------------------------------|
| critical    | 1 fail → REVISE; ≥2 → REWORK                       | 1 fail → REVISE; ≥2 → REWORK                       |
| significant | ≥1 fail → REVISE                                   | ≥1 fail → REVISE                                   |
| minor       | Any number tolerated; noted for batch polish pass  | ≥3 fails → REVISE; <3 tolerated with notes         |

In fast mode, `minor` items are a deliberately soft threshold because
the polish pass over batches of chapters is what catches the aggregate
drift. In full mode, `minor` items are real but still cheaper than
critical — ≥3 is the trigger.

## Why this is better than a prose verdict

- **Auditable.** Human sees exactly what was checked and what each
  result was. No hiding.
- **Non-overlapping.** Each rubric item checks one thing. No vibes-based
  "the chapter feels off."
- **Stable across runs.** Given the same chapter, two Critic runs
  produce very similar scorecards. Prose verdicts drifted.
- **Loopback is computed, not chosen.** The Critic doesn't "pick"
  Writer-vs-Humanizer; the rule reads the failing items' targets.

The Critic's remaining prose responsibility is the **Observations**
section of `critique.md`: things that aren't rubric items but are worth
flagging. Things like "the voice shifted halfway through — may want to
check chapter 5's calibration" or "this chapter opens three forward
references; are any of them planned elsewhere?" The human reads this
alongside the scorecard.
