# Rubric — literary families

For `book-literary`. Schema, verdict, override layers, `rhet` definitions and
the Critic protocol: `references/rubric.md`. This file defines items and the
Phase 2 design rubric. "`checks.json →`" means: copy that field into evidence
(keys: `references/pipeline.md` § Execution model). Literary sections:
`counts` (count_rhet.py), `fiction.findings` (lint_fiction.py `--unit`; a
finding's `rule` and `severity`), `story` (check_story.py `--unit`: `findings`
by `code`, and `context`), `tics` and `role_diff`. A `fiction.findings` hit
"at minor or above" has severity `minor` or `major`; `info` never reaches
`checks.json`.

The scorecard gates **defects** — outline fidelity, character and arc,
continuity, counted tics, format — not quality, which Reader-POV, the reader
journal and the human judge. A calibration passage never exempts a counted
pattern: only a `rhetoric_budget` override changes a quota.
Why: `docs/rationale/literary.md#calibration-contamination`

## `beats` — the scene cards

| id | sev | check | loopback |
|----|-----|-------|----------|
| beats-1 | critical | Every scene card of the outline entry is on the page under its `<!-- SCENE sN -->` marker (merges and reorders flagged by the Editor are fine). | Writer |
| beats-2 | significant | No major unplanned event: death, reveal, new relationship, ledger plant absent from the cards. Keeping a good one means changing the outline — a human call. | escalate |
| beats-3 | significant | `exposition-within-scene` beats deliver `information` through `actioned_by` — someone wants, withholds or pays for it — not by announcement. | Writer |
| beats-4 | significant | Each card's `pivot` and `value` change (`from` → `to`) are visible: a reader could point to the line where the balance turns. | Writer |

## `character`

| id | sev | check | loopback |
|----|-----|-------|----------|
| character-1 | critical | The POV character's decisions follow their sheet (`want`, `need`, `contradiction`) or visibly strain against it; they never ignore it. | Writer |
| character-2 | significant | Other named characters act and speak as their sheets say, § Never included. | Writer |
| character-3 | significant | Every named person on stage has a complete, signed sheet (R1); no `bible/world.md` word (a § Names entry or a place), outline location or extra's label word speaks or acts. Evidence: `checks.json → story.findings` codes `NEW-CHARACTER`, `EXTRA-PROMOTE`, `CHAR-UNKNOWN`, `CHAR-INCOMPLETE`, `CHAR-UNSIGNED-CHANGE`, `CHAR-DUPLICATE`, and `fiction.findings` rules `unknown_name`, `mentioned_on_stage`. Any hit fails; the orchestrator runs `references/character-questionnaire.md` (R4). **Read, not only count**: the scripts miss a name that is also a common noun used only sentence-initially and never speaking or acting while the noun appears in lowercase elsewhere ("Luz era la hija de Rosa." next to "no había luz") — a person on stage the Critic reads as one fails this row even with no finding. | escalate |

## `arc`

| id | sev | check | loopback |
|----|-----|-------|----------|
| arc-1 | significant | Each `arc_moves` entry is dramatized: that turning point (sheet `arc.turning_points`) happens as an event or decision, not a narrated change of heart. | Writer |
| arc-2 | significant | Transitions are earned: no relational stage of `bible/arcs.md` skipped; no emotional jump the preceding scenes do not cause. | Writer |
| arc-3 | critical | Every arc whose `resolves_in` is this unit (`checks.json → story.context.arcs_resolving_here`, plus `bible/arcs.md`) resolves on the page. | Writer |

## `ending`

| id | sev | check | loopback |
|----|-----|-------|----------|
| ending-1 | critical | Only when `checks.json → story.context.is_final_unit` is true (else `not_applicable`): the unit delivers `ending.resolution` and answers the dramatic question as `ending.answer` states. | Writer |

## `voice`

| id | sev | check | loopback |
|----|-----|-------|----------|
| voice-1 | significant | Lexical fingerprints: AI-isms ≤ 1 (`checks.json → counts.ai_vocab.count`, lexicon `ai_isms`); no `fiction.findings` rule `cliche` or `speech_verb_ornate` at minor or above. | Humanizer |
| voice-2 | significant | No explaining-the-shown, narrator-stated theme or single-channel emotion (`anti-mediocrity-literary.md` § 2); hedges ≤ 2 per 1000 words (`checks.json → counts.weasels.count` ÷ `words`). | Humanizer |
| voice-3 | minor | Rhythm: `checks.json → counts.sentence_length.flat_runs` ≤ 2, at most one `fiction.findings` rule `sentence_run` (always minor); narration em-dashes ≤ 2 per page (`counts.em_dash_narration.per_page`) unless the style guide allows more. Dialogue rayas never count. | Humanizer |
| voice-4 | significant | Narration matches `bible/voice-profile.md`: fingerprint traits observable, banned traits absent. | Humanizer |
| voice-5 | significant | Dialogue is character-specific: tags covered, speakers stay distinguishable; the cast does not share one register. | Writer |
| voice-6 | significant | Humanizer within budget: `checks.json → role_diff.humanizer.over_budget` is not true (`literary.humanizer_budget`, default 0.03). Over budget means the draft needed rewriting, not repair. | Writer |

## `craft`

| id | sev | check | loopback |
|----|-----|-------|----------|
| craft-1 | significant | No exposition-as-dialogue: no line exists only to tell a listener what both know. | Writer |
| craft-2 | significant | A card with `pause` contains the turn it names (interruption or internal change), not stacked sensory anchors. | Writer |
| craft-3 | minor; significant if the same character failed it in an earlier unit | A secondary character in their second or later unit gets a line or act of their own (outline `secondary_lines`). | Writer |
| craft-4 | minor — observation, never fails | VOICE-RISK flags, 0–2, optional: `pass` with the flags quoted, or `not_applicable` when there are none; flags beyond two are not protected. Whether each lands goes in Observations. | — |
| craft-5 | significant | Declared friction is dramatized: each card's `want`, `opposition`, `crisis` and, when present, `attempts` happen in scene — resisted, chosen, failing on the page — not summarized. | Writer |
| craft-6 | significant | Tics: `checks.json → tics.over_quota` empty, and no `fiction.findings` rule `gesture_tic`, `repeated_ngram` or `paragraph_opener` at minor or above (quotas: `meta.yaml → literary.tics`). | Humanizer |

## `format`

| id | sev | check | loopback |
|----|-----|-------|----------|
| format-1 | significant | No `fiction.findings` rule `dialogue_format`, `ordered_list_hazard`, `scene_break_mix` or `near_duplicate_name` at minor or above (a near-duplicate that is really a second person → character-3). | Humanizer |

## `reader_pov`

| id | sev | check | loopback |
|----|-----|-------|----------|
| reader_pov-1 | critical | No unintended comprehension failure in `reader-report.md`. A confusion is intended only when it matches a `mystery` ledger entry or a card's withheld `information`. | Writer |
| reader_pov-2 | critical | No "I would close the book here" flag stands. | Writer |
| reader_pov-3 | significant | No located stretch the reader marks as dragging or rushed. | Editor |
| reader_pov-4 | minor — observation, never fails | Predictability: journal predictions scored `hit`, as hits/total (`reader-report.md` § Predictions scored). Record `pass` with the ratio; comment in Observations when half or more hit. | — |

Comprehension and pacing never route to the Humanizer: its contract forbids
new content. Why: `docs/rationale/literary.md#routing`

## `continuity`

| id | sev | check | loopback |
|----|-----|-------|----------|
| continuity-1 | critical | No contradiction with `bible/continuity-tracker.md`, `timeline.md` (dates, weekdays, durations, ages), `world.md` or the sheets — `coherence.md` categories character, factual detail, timeline, plot, world. | Writer |
| continuity-2 | significant | Within-unit consistency: objects, injuries, knowledge, weather, time of day; no POV or tense slip (`coherence.md` narrative style). | Writer |
| continuity-3 | significant | Facts lane (`literary.fact_check: realistic`; otherwise `not_applicable`): no fact `coherence.md` marks `contradicted` survives. `unverifiable` facts do not fail — they reach the human packet as decisions. | Writer |

## `rhet`

| id | sev | check | loopback |
|----|-----|-------|----------|
| rhet-2 | significant | As defined in `references/rubric.md` — the only `rhet` row a literary scorecard carries (the count excludes dialogue). | Humanizer |

**Not scored** (Observations only): `fiction.stats` (dialogue ratio, sentence
statistics) and the `fiction.findings` rules `opening_repeat` and
`unit_length`.

---

## Design rubric (Phase 2)

Filled once per outline version, before `pipeline_step.py ready`, by an
isolated subagent on the Critic's tier whose whole brief is this section.
Inputs: `python scripts/check_story.py --ready-to-draft --json OUT`, the
outline, `plot-structure.md`, `arcs.md`, `story-ledger.yaml`, the sheets,
`outline/echo-check.md`, `outline/stress-test.md`. Output:
`outline/design-scorecard.yaml`, one row per item: `{id, name, status:
pass|fail|not_applicable, evidence}`.

No verdict, no loopback. **Enforced** rows mirror `check_story.py` codes: `ready`
refuses while a blocking code stands. **Reviewed** rows go to the human with
the outline: fix it, or accept the row with a one-line `accepted:` note.

| id | kind | check |
|----|------|-------|
| design-1 | enforced | R1: every slug in any `characters_present` has a sheet signed with `pipeline_step.py sign` (`status: complete`, `signed_on`, a `signed_hash` that still matches), every file in `bible/characters/` is a valid sheet with one slug, and no scene card names a person without one (no `CHAR-INCOMPLETE`, `CHAR-NO-ARC`, `CHAR-UNKNOWN`, `CHAR-UNSIGNED-CHANGE`, `CHAR-DUPLICATE`). |
| design-2 | enforced | Arcs placed: each turning point sits in a unit where the character is present with an `arc_moves` entry; `resolves_in` ≤ `ending.final_unit` (no `CHAR-ARC-OUT-OF-OUTLINE`, `ARC-AFTER-ENDING`). |
| design-3 | enforced | R2: ending front matter complete, `final_unit` in the outline (no `ENDING-MISSING`). |
| design-4 | enforced | Human material: seeds ≥ `literary.min_seeds`, human calibration passages ≥ `literary.human_calibration_passages`, extras unnamed and single-unit (no `SEEDS-MISSING`, `CALIBRATION-NO-HUMAN`, `EXTRA-PROMOTE`). |
| design-5 | enforced | Ledger: `bible/story-ledger.yaml` exists (`entries: []` is fine; no `LEDGER-MISSING`); every entry has a status in open\|paid\|deliberately-ambiguous, a real `what` and `trigger`, `paid_in` on a unit that exists when paid (no `LEDGER-INVALID`), a planned `payoff_unit` ≤ `final_unit` (no `LEDGER-NO-PAYOFF`), and every id in a card's `ledger` exists (no `LEDGER-UNKNOWN`). |
| design-6 | reviewed | Scene cards complete: each `scene` of ≥ 300 planned `words` has `want`, `opposition`, `pivot`, `value`, `crisis`; exposition beats have `information` and `actioned_by`; slow beats name their `pause`. |
| design-7 | reviewed | Causal chain: every card's `link` is a "therefore" or a "but" in the book's language; an "and then" link, or an empty one, fails. |
| design-8 | reviewed | Tension: key-scene cards and every crisis or climax card carry `attempts` with `fails_because`; value changes alternate across units instead of repeating one direction. |
| design-9 | reviewed | Midpoint: the middle unit flips a value or reframes the dramatic question. |
| design-10 | reviewed | Echo check done on every turning point (`outline/echo-check.md`); each "model default" carries the human's keep-or-change decision. |
| design-11 | reviewed | Stress test done (`outline/stress-test.md`); every prediction that matched a planned turning point is listed for the human. |
| design-12 | reviewed | Coverage: subplots surface at least every 4 units unless declared dormant; no principal character is absent for more than 4 units without a reason in `notes`. |
