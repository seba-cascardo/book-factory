# Profile: book-literary

Literary fiction and narrative prose: novels, short-story cycles, memoir,
creative nonfiction with a narrative spine. Voice is the product — the
pipeline optimizes for a text only this narrator could have written, not
merely a correct one. Every agent loads this file at the start of its turn,
then `bible/meta.yaml`, then (prose agents) `bible/voice-profile.md`.

## Unit

The unit is a **chapter**. Files use `unit-NN`; always say "chapter" when
talking to the human.

## Sequence

`linear`. Consequences:

- **Digests on.** After approval, write the chapter digest to
  `bible/digests/`: plot state, character states, open plants/payoffs, a
  voice-calibration note. From unit 6 onward, agents read all digests plus
  only the immediately preceding chapter in full.
- **No knowledge graph.** `bible/plot-structure.md`, `arcs.md`,
  `timeline.md`, and the character sheets carry the dependency role that
  the KG plays in nonfiction.
- **Setups and payoffs are tracked**, not free. A plant (object, secret,
  wound) goes into `bible/continuity-tracker.md` when planted and stays
  open until paid off; the Continuity Guardian audits both directions.
- **Write in outline order.** Tension architecture depends on it.

## Pipeline

The literary pipeline — no Technical Reviewer, no fast/full split:

```
Writer → Editor → Humanizer → Reader-POV → Critic (GATE)
  → [Adversarial Verify: if enabled] → Human review
  → (on approval) Proofreader → Continuity Guardian → digest → archive
```

Humanizer and Reader-POV run every chapter; deferring either leaks generic
prose into approved chapters, and approved chapters are expensive to reopen.
Retry cap: 3. Model roles: `humanizer: creative` is the default here —
line-level voice work is creative work in this profile, not audit work.

## Register

Defined entirely per project: POV, tense, prose register, dialogue
conventions, metaphor policy live in `bible/style-guide.md`; the fingerprint,
banned traits, and budgets live in `bible/voice-profile.md`. This profile
imposes no register of its own — literary registers are too diverse for
defaults, and a default register here would manufacture the same
competent-generic narrator in every project. The universal floor is
`references/anti-mediocrity-literary.md`.

## Openings and closings

- **Openings**: rotation per `bible/voice-profile.md` (3–4 structures chosen
  at setup — e.g., in-media-res action, dialogue, interiority, sensory
  scene-setting). `rhet-6` applies: the same structure may not open two
  consecutive chapters. The Writer declares its choice in the
  self-assessment; the Critic verifies.
- **Closings**: follow the outline's beat, nothing else. There is NO
  "end with forward momentum" rule — mandated momentum produces mechanical
  chapter-end hooks, a formula readers learn to see through. A quiet ending
  that the outline calls for outranks a manufactured one. `rhet-2` guards
  the "not X but Y" reflex at climactic moments, where it clusters.

## Citation policy

`n/a`. No grounding library, no SOURCE comments, no Technical Reviewer.
Factual texture (period detail, craft knowledge, geography) is the human's
call during setup and outlining; record research decisions in
`bible/world.md` so agents stop re-litigating them. If the human wants a
fact verified, that is a request to the human's own research, not a pipeline
stage.

## Running example

`n/a` — a nonfiction device. The equivalent continuity load is carried by
the continuity tracker, character sheets, and timeline.

## Literary package (always on)

Seven hooks against competent-generic prose. Each is enforced where noted;
this profile activates all of them.

1. **Friction inventory** — before drafting, the Writer declares per scene
   of 300+ words: what the POV wants, what opposes it, where it pivots.
   A scene without friction drafts as summary. Missing inventory → `craft-5`
   (significant). See `references/agents/writer-literary.md`.
2. **Exposition beats marked in outline** — beats are `scene` or
   `exposition-within-scene`; the latter carry an instruction to put the
   information into action. Unloading it as informative dialogue → `craft-1`
   (significant). See `references/outlining.md`.
3. **Pause vs pausing** — a structural pause needs an interruption or a
   change of internal state; sensory anchors alone are scenery, not a beat.
   Enforced by the Editor and `craft-2` (significant).
4. **Secondary characters** — anyone appearing twice or more gets at least
   one line that is unmistakably theirs. `craft-3` (minor; significant on
   repeat across units). Wired in during outlining.
5. **Voice-risk quota** — the Writer takes 1 deliberate risk per chapter,
   flagged `<!-- VOICE-RISK: ... -->` in the draft. The rubric cannot fail a
   flagged risk on its own; the Critic comments on it (`craft-4`). Without a
   protected slot for risk, gates sand off everything distinctive.
6. **Conservative Humanizer** — contract: preserve, don't improve. A line
   that violates neither anti-mediocrity nor style-guide nor voice-profile
   stays. Weak beats per the reader-report get 2–3 flagged alternatives, not
   a unilateral rewrite. Hard stop: about to touch >3% of the words → halt
   and flag the Critic. See `references/agents/humanizer-literary.md`.
7. **Singularity audit** — every 5 approved chapters, the Continuity
   Guardian does a cold read with proper nouns masked: did this narrator
   write it, or "a good generic writer of this register"? Output is
   advisory — the 2–3 most singular and most generic passages — so the
   human can recalibrate voice-profile.md.

## Rubric deltas

Use the literary rubric in `references/rubric.md` § Literary — families
`beats`, `character`, `arc`, `voice`, `craft` (craft-1..5 above),
`reader_pov`, `continuity`. Of the `rhet` family only `rhet-2` and `rhet-6`
apply; the rest target nonfiction tics. Verdicts are computed from
`drafts/unit-NN/scorecard.yaml` — same schema as every profile.

## Reader-POV persona

Simulate the reader in `meta.yaml → target_reader`, aiming at
`desired_reader_experience`. Report immersion breaks, confusion, and where
attention drifts — as that reader, who has read widely in the genre but has
never seen the bible and does not load anti-mediocrity. Real readers don't
have a checklist; they have taste.

## Build targets

Phase 5 (`references/build-export.md`): **EPUB / PDF / DOCX**, via pandoc or
the docx/pdf skills when available. Output to `build/`. Confirm with the
human: trim/format conventions, scene-break glyph, chapter title pages,
front and back matter.
