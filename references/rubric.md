# Rubric & Scorecard System

The Critic's verdict is computed, not asserted. A prose verdict fails
silently when the Critic is wrong: one model, tired at the end of a long
context, misses a check and the unit ships with the error — and the human,
reading a confident summary, has no visible way to know *what was checked*.
The scorecard makes every check explicit, every result auditable, and the
verdict a deterministic function of the results. This kills two failure
modes at once: the Critic skipping a check because it was vibes-satisfied,
and the human rubber-stamping a verdict because reading a summary feels
like review even when it isn't.

The prose summary survives as the **Observations** section of
`critique.md` — for things worth flagging that are not rubric items — but
it carries no verdict authority.

## Artifacts

- `drafts/unit-NN/scorecard.yaml` — the machine-readable truth. Template:
  `templates/scorecard.yaml`.
- `drafts/unit-NN/critique.md` — renders the scorecard for humans, plus
  Observations. Template: `templates/critique-report.md`.

## Scorecard entry schema

Every entry has exactly these fields:

- `id` — stable identifier (e.g., `scope-1`, `rhet-3`, `craft-5`).
- `rubric` — the family the item belongs to (see family lists below).
- `name` — one-line description of what was checked.
- `severity` — `critical | significant | minor`.
- `status` — `pass | fail | not_applicable`.
- `evidence` — for fails: quoted lines, `file:line`, or a one-sentence
  diagnosis. For passes: optional — **except counted items (`rhet`
  family), where evidence must always include the count**, pass or fail.
- `loopback_target` — for fails: `Writer | Editor | Humanizer |
  Reader_POV_plus_Humanizer | escalate`.

Ids are scoped to the rubric in use (nonfiction vs. literary); a project
runs exactly one rubric, so ids never collide inside a scorecard.

## Verdict computation — AUTHORITATIVE

```
if any failing item has loopback_target == escalate:
    verdict = ESCALATE
elif count(critical fails) >= 2:
    verdict = REWORK            # back to Writer, full redraft
elif count(critical fails) == 1:
    verdict = REVISE
elif count(significant fails) >= 1:
    verdict = REVISE
elif count(minor fails) >= 3 and mode == full:
    verdict = REVISE
elif any minor fails:
    verdict = PASS, with notes
else:
    verdict = PASS
```

| Severity    | fast mode                                         | full mode                              |
|-------------|---------------------------------------------------|----------------------------------------|
| critical    | 1 fail → REVISE; ≥2 → REWORK                      | same                                   |
| significant | ≥1 fail → REVISE                                  | same                                   |
| minor       | tolerated in any number; noted for the polish pass | ≥3 fails → REVISE; <3 tolerated w/notes |

Fast mode's soft minor threshold is deliberate: the batch polish pass
catches aggregate drift more cheaply than per-unit loops. The literary
pipeline uses **full-mode tolerances**.

**Loopback target for REVISE** is resolved from the failing items:

1. All failing items share one target → that target.
2. Targets split → the target of the highest-severity failing item.
3. Still tied → Writer (content outranks structure outranks prose).

This rule is deterministic. The Critic does not choose the verdict or the
target; both fall out of the scorecard.

## Which rubric a project runs

- `book-technical`, `corporate-guide`, `product-docs`, `scientific-paper`
  → the **nonfiction rubric**: families `scope, outline, tech_a, tech_b,
  pedagogy, voice, reader_pov, code, consistency, forward_refs, rhet,
  profile`.
- `book-literary` → the **literary rubric**: families `beats, character,
  arc, voice, craft, reader_pov, continuity` plus the `rhet` subset
  (`rhet-2`, `rhet-6` only).

The base items live in this file. Two override layers, read them BEFORE
scoring:

1. `references/profiles/<profile>.md` § Rubric deltas — adds items,
   removes items, or changes severities for that profile (e.g., a modular
   profile redefines `forward_refs` as an outright prohibition; a paper
   profile adds citation-integrity and Limitations items).
2. `bible/voice-profile.md` § Rhetoric budget — overrides `rhet` quotas
   only, in either direction.

## Nonfiction rubric

Run every applicable item. Items marked *(full only)* run only in full
mode; the voice family is strict in full mode and tolerant on microhits
in fast mode, as noted per item.

### `scope`

| id | sev | check | loopback |
|----|-----|-------|----------|
| scope-1 | critical | Unit delivers the outline entry's `purpose`. | Writer |
| scope-2 | significant | No topics declared out-of-scope in `bible/scope.md` surface here. | Writer |
| scope-3 | significant | Depth matches the outline entry's declared depth (tutorial / reference / overview). | Writer |

### `outline`

| id | sev | check | loopback |
|----|-----|-------|----------|
| outline-1 | critical | Every `concepts_introduced` from the outline entry is actually introduced. | Writer |
| outline-2 | critical | Every `concepts_used` appears in earlier units, this unit's `concepts_introduced`, or declared prerequisites — knowledge-graph integrity at unit time. | Writer |
| outline-3 | significant | Section structure matches the outline; any added/removed section is flagged, not smuggled. | Editor |
| outline-4 | significant | Exercises (if the outline declares them) are solvable with concepts introduced up to this unit. | Writer |

### `tech_a` — claims, code, versions

| id | sev | check | loopback |
|----|-----|-------|----------|
| tech_a-1 | critical | Every Axis A finding in `tech-review.md` was addressed or carried as an explicit advisory note. | Writer |
| tech_a-2 | critical | Code snippets pass the declared validation surface's checks (see `references/validation-surface.md`). | Writer |
| tech_a-3 | significant | Version references match `bible/meta.yaml` pinned versions. | Writer |
| tech_a-4 | significant | No invented APIs/functions/commands — every identifier cross-references to the grounding library or is flagged as advisory. | Writer |

### `tech_b` — mental models, terminology

| id | sev | check | loopback |
|----|-----|-------|----------|
| tech_b-1 | critical | No Axis B "broken framing" from `tech-review.md` survives unresolved. | Writer |
| tech_b-2 | significant | Glossary terms used consistently — no synonym cycling on load-bearing terms. | Humanizer |
| tech_b-3 | significant | Version-drift items from `tech-review.md` are correctly classified, not reported as errors where the drift rule applies. | Writer |

### `pedagogy`

| id | sev | check | loopback |
|----|-----|-------|----------|
| pedagogy-1 | significant | Each section motivates before mechanizing — why before how. | Writer |
| pedagogy-2 | significant | Examples come after the concept they illustrate. | Editor |
| pedagogy-3 | minor | The closing matches the **profile's closing policy** (recap / related-links / none / bridge-allowed, as adjusted in `voice-profile.md`). A closing that follows a different formula fails — including an uninvited recap where the policy is `none`. | Humanizer |
| pedagogy-4 | significant | No undeclared forward references — every "later" is paid off or recorded in the continuity tracker. | Writer |

`pedagogy-3` deliberately checks against the *policy*, not a universal
formula. A hardcoded recap-or-bridge requirement makes every unit of
every project end the same way; the ending belongs to the profile.

### `voice` (full: strict · fast: tolerant on microhits)

| id | sev | check | loopback |
|----|-----|-------|----------|
| voice-1 | significant | Person (you/we/impersonal) matches `bible/meta.yaml` and stays consistent. | Humanizer |
| voice-2 | significant | Anti-mediocrity Content-layer hits: 0 target; 1–2 tolerated in fast mode only. | Writer |
| voice-3 | significant (full) / minor (fast) | Anti-mediocrity Language-layer (AI-isms) density within mode tolerance. | Humanizer |
| voice-4 | significant | Anti-mediocrity Style-layer signposting absent. | Humanizer |
| voice-5 | critical | Anti-mediocrity Communication-layer artifacts absent — chatbot residue is a hard fail. | Humanizer |
| voice-6 | minor | Anti-mediocrity Filler/Hedging layer within tolerance. | Humanizer |
| voice-7 | significant | Register (tone, formality, person) matches the style decisions and calibration passages in `bible/style-guide.md`. | Humanizer |

### `reader_pov` *(full only)*

| id | sev | check | loopback |
|----|-----|-------|----------|
| reader_pov-1 | critical | No comprehension failure flagged in `reader-report.md` survives unaddressed. | Reader_POV_plus_Humanizer |
| reader_pov-2 | critical | No "reader would close the book here" flag unaddressed. | Reader_POV_plus_Humanizer |
| reader_pov-3 | critical | Outcome match: the reader finishes able to do what the outline promised. An outcome miss is missing content. | Writer |

### `code`

| id | sev | check | loopback |
|----|-----|-------|----------|
| code-1 | significant | Every snippet has labeled input / expected output. | Writer |
| code-2 | minor | Snippets are minimal — no decorative scaffolding. | Editor |
| code-3 | minor | Code style matches `bible/meta.yaml` conventions. | Humanizer |
| code-4 | critical | No rule this unit states in prose is contradicted by this unit's own code, example or bullet. | Writer |

`code-4` is defence in depth against the dominant intra-unit defect. Measured on
a completed book, **seven of ten** intra-unit defects were exactly this gesture:
the unit states a rule and violates it in its own example a few lines later. The
Technical Reviewer checks claims against sources, the Editor checks prose, and
you check the unit as a whole — but until now nothing crossed the prose layer
against the code layer, and this class walked through every gate.

To score it: list the rules the unit states (strong modality, or a universal plus
a breaking verb — "any function call on a loaded field breaks it" is a rule), then
read every code block and example against them. Do not extend this across units;
that is MG-2's job at the manuscript gate, with the whole book in view. And do
not score voice: an emphatic imperative is register, not a rule about behavior.

### `consistency`

| id | sev | check | loopback |
|----|-----|-------|----------|
| consistency-1 | significant | Voice matches `bible/voice-profile.md`: fingerprint traits are observable in this unit; banned traits are absent. | Humanizer |
| consistency-2 | significant | Terminology matches prior units (via digests + continuity tracker). | Humanizer |

`consistency-1` compares against the **voice profile, never the previous
unit**. Comparing against the previous unit rewards homogeneity — each
unit regresses toward the mean of the last one until the whole book (and
every book made with this pipeline) sounds identical. The voice profile
is the stable, human-approved reference. Note the source split: banned
traits here come from the *project's* voice-profile; the *profile's*
register prohibitions are `profile-1`.

### `forward_refs`

| id | sev | check | loopback |
|----|-----|-------|----------|
| forward_refs-1 | critical | This unit pays off every forward ref that prior units opened and the outline assigned here. | Writer |
| forward_refs-2 | minor | New forward refs are flagged for recording in the unit's digest. | Writer |

## Rhetoric budget — `rhet` family (counted, not felt)

Every dramatic device looks justified in isolation; the aggregate is the
tell. That is why these are **quotas with mechanical counts**, not bans
with judgment calls: adjudicating intent per instance reintroduces vibes,
and vibes always approve. Count, record the number in `evidence` (pass or
fail — a `rhet` entry without a count is invalid), compare against the
quota. Quotas below are defaults; `bible/voice-profile.md` § Rhetoric
budget may tighten or loosen them.

All counts run over prose only: strip code fences, tables, and (literary)
quoted dialogue first.

| id | sev | quota | check & counting procedure | loopback |
|----|-----|-------|----------------------------|----------|
| rhet-1 | significant | ≤ 2 | **Rhetorical questions.** Count every `?` in narrative prose. Exclude: questions inside exercises, quoted speech, and FAQ-style headings where the heading *is* the user's question. Everything else counts — including questions the text immediately answers (those are the worst offenders). Evidence: `count=N (lines …)`. | Humanizer |
| rhet-2 | significant | ≤ 1 | **"Not X but Y" reframes.** Count matches of these shapes (case-insensitive): sentence beginning `It's not / It isn't / This isn't` with a later `it's`; sentence-initial `Not X. Y` or `Not X but Y`; `isn't just X; it's Y`; `less about X than (about) Y`; plus target-language equivalents. Plain mid-sentence factual contrasts (`returns not a list but a tuple`) are not matched by these shapes and do not count. Evidence: count + quoted matches. | Humanizer |
| rhet-3 | significant | ≤ 2 | **Dramatic-danger lexicon.** `grep -icE 'silently\|invisibl\|quietly\|without (complaint\|warning)\|hidden (danger\|cost\|failure)\|lurk\|time bomb\|ticking'` plus target-language equivalents. Count ALL prose hits — do not adjudicate whether a use is "technical enough"; the quota absorbs legitimate uses, and per-instance adjudication is how dozens of them get approved one justified case at a time. Evidence: count + terms found. | Humanizer |
| rhet-4 | significant | 0 when closing policy is recap or none | **Artificial cliffhanger.** Inspect the final two paragraphs for tease constructs: an unresolved sentence-final question, forward teases (`we'll see`, `that's when things get interesting`, `but there's a catch`). Any hit fails. Evidence: quote the closing lines. | Humanizer |
| rhet-5 | minor | ≤ 8 per 1000 words | **Bold density.** Bolds = count of `**` markers ÷ 2, excluding table rows and headings; words via `wc -w` on prose. Evidence: `N bolds / M words = D per 1000`. | Humanizer |
| rhet-6 | significant | — | **Opening rotation.** Read the Writer's declared opening structure in its self-assessment; verify the actual opening matches the declaration; compare against the previous unit's declared structure (in its scorecard evidence or digest). Same structure two units in a row fails. First unit: auto-pass. Evidence: this unit's structure + previous unit's — always record both so the next unit has its reference. | Writer |
| rhet-7 | minor | — | **Template headings only when earned.** Grep headings for `What's next`, `Key takeaways`, `Payoff`, `Wrapping up`, `Final thoughts` and equivalents. For each hit, check the section body names concepts from THIS unit and concrete actions. Generic, swap-into-any-chapter content fails. Evidence: heading + one-line assessment. | Writer |

## Profile compliance — `profile` family

The profile file is a contract; these three items are the **universal spine**
every nonfiction profile runs. `profile-1/2/3` mean the same thing in every
project — the Critic agent file describes them by these base meanings.

| id | sev | check | loopback |
|----|-----|-------|----------|
| profile-1 | significant | **Register prohibitions respected.** For each prohibition in the profile's Register section (e.g., mic-drops, self-reference like "this guide", transformation promises), scan the unit; quote any hit. | Humanizer |
| profile-2 | significant | **Citation policy respected.** `invisible`: no visible citations in prose, load-bearing claims carry HTML-comment citations. `visible-academic`: every claim in `bible/claims-map.yaml` touched by this unit has a correctly formatted citation. | Writer |
| profile-3 | significant | **Opening structure is in the rotation.** The opening matches one of the structures declared in `voice-profile.md` § Opening rotation. (`rhet-6` checks non-repetition; this checks membership.) | Writer |

A profile MAY mark a spine item `not_applicable` (e.g., product-docs and
scientific-paper fix the opening, so `profile-3` is N/A) and MAY add its own
items — but **only in its own id namespace** (`paper-*`, `corp-*`, `docs-*`),
never by redefining `profile-1/2/3`. Reusing a base id would put two
conflicting definitions of one id in a scorecard, breaking the "ids never
collide" contract. Each profile's § Rubric deltas lists the items it adds.

## Literary rubric

Same scorecard schema, same verdict computation, full-mode tolerances.
Families and items:

### `beats` — outline fidelity

| id | sev | check | verify | loopback |
|----|-----|-------|--------|----------|
| beats-1 | critical | Unit delivers every beat the outline assigned to it. | List the outline entry's beats; locate each in the draft. | Writer — escalate if the beat itself proves unwritable |
| beats-2 | significant | No major unassigned plot events smuggled in. | Diff the unit's events against the outline + plot-structure.md. | Writer |
| beats-3 | significant | Beats marked `exposition-within-scene` action their information — the reveal happens through consequence, not announcement. | For each such beat, identify HOW the information reaches the reader. | Writer |

### `character`

| id | sev | check | verify | loopback |
|----|-----|-------|--------|----------|
| character-1 | critical | POV character's actions and decisions are consistent with their sheet. | Read `bible/characters/<name>.md`; list this unit's decisions; flag contradictions. | Writer |
| character-2 | significant | Non-POV named characters act consistently with their sheets. | Same procedure per appearing character. | Writer |
| character-3 | minor | Every new named character has (or is flagged for) a sheet entry. | Cross-check names against `bible/characters/`. | Writer |

### `arc`

| id | sev | check | verify | loopback |
|----|-----|-------|--------|----------|
| arc-1 | significant | The unit advances at least one arc assigned to it in `bible/arcs.md`. | Name the arc and the specific movement; "nothing changed" fails. | Writer |
| arc-2 | significant | Emotional and relationship transitions are earned — no stage-skipping relative to arc position. | Compare end-state vs. arc timeline; flag unearned jumps. | Writer |

### `voice`

| id | sev | check | verify | loopback |
|----|-----|-------|--------|----------|
| voice-1 | significant | Zero anti-mediocrity-literary blacklist hits (AI-isms). | Grep the blacklist terms; count. | Humanizer |
| voice-2 | significant | No explaining-the-shown (RUE) or weasel-adverb violations beyond tolerance. | Scan emotion-labeling after action/dialogue that already carries it. | Humanizer |
| voice-3 | minor | Sentence rhythm varies — no runs of 3+ same-shape sentences. | Sample 3 paragraphs; map sentence lengths/structures. | Humanizer |
| voice-4 | significant | Narration matches `voice-profile.md`: fingerprint traits observable, banned traits absent. | Check each fingerprint trait for presence; grep banned traits. | Humanizer |
| voice-5 | significant | Dialogue is character-specific — lines attributable without tags. | Strip attributions from one exchange; test whether speakers remain distinguishable by diction. | Writer |

### `craft`

| id | sev | check | verify | loopback |
|----|-----|-------|--------|----------|
| craft-1 | significant | No exposition-as-dialogue: no line exists only to inform the reader of what both speakers already know. | For each expository dialogue line, ask: would this character say this to this listener? | Writer |
| craft-2 | significant | Pause beats have texture: an interruption or an internal state change, not just sensory anchors laid side by side. | For each low-action passage, identify what shifts during it. Scenery-only pauses fail. | Writer |
| craft-3 | minor → significant on recurrence | Recurring secondary characters (2+ appearances) have ≥1 line or gesture of their own. | Count appearances via continuity tracker; check for an owned line. Escalate to significant if the same character already failed this in a prior unit. | Writer |
| craft-4 | observation only — NEVER a fail | The Writer's declared voice risk (`<!-- VOICE-RISK: ... -->`) is present and flagged. | Locate the flag; record `pass` with the quoted flag, or `not_applicable` with a note. Comment on whether the risk lands in Observations. A failable risk quota would train the Writer to take fake risks. | — |
| craft-5 | significant | Every scene ≥ 300 words has a friction inventory in the Writer's self-assessment: what the POV wants / what opposes / where it pivots. | Measure scene lengths; match each qualifying scene to an inventory block. | Writer |

### `reader_pov`

| id | sev | check | verify | loopback |
|----|-----|-------|--------|----------|
| reader_pov-1 | critical | No comprehension failure in `reader-report.md` survives unaddressed. | Cross-check each flag against the humanized draft. | Reader_POV_plus_Humanizer |
| reader_pov-2 | critical | No "would close the book here" flag unaddressed. | Same. | Reader_POV_plus_Humanizer |
| reader_pov-3 | significant | Pacing and emotional beats land per the reader report. | Same. | Reader_POV_plus_Humanizer |

### `continuity`

| id | sev | check | verify | loopback |
|----|-----|-------|--------|----------|
| continuity-1 | critical | No contradiction with the continuity tracker, timeline, or world bible. | Check facts stated here against `bible/continuity-tracker.md`, `timeline.md`, `world.md`. | Writer |
| continuity-2 | significant | Within-unit state consistency: objects, injuries, knowledge, weather, time of day. | Track stateful details across the unit. | Writer |

### `rhet` subset

Only `rhet-2` (≤ 1, significant) and `rhet-6` (opening rotation,
significant) apply, with the same counting procedures as the nonfiction
table. The rest do not: rhetorical questions are legitimate interiority
in free indirect style, bold barely exists in fiction, and danger lexicon
is genre-dependent — but the "not X but Y" reflex and the repeated
opening template kill voice in any register.

## Why this beats a prose verdict

- **Auditable** — the human sees exactly what was checked and each result.
- **Non-overlapping** — each item checks one thing; no "the unit feels off".
- **Stable** — the same unit produces near-identical scorecards across runs.
- **Computed loopback** — the target is read off the failing items, not picked.

The Critic's remaining prose responsibility is Observations: cross-unit
patterns, voice-risk commentary, anything worth a human's eye that no
item captures.
