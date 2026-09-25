# Profile: book-literary

Novels, story cycles, memoir, narrative nonfiction. The story is the engine
and the voice is the product. Every agent loads this file after its agent
file, then `bible/meta.yaml` (its `literary:` block), then — prose agents —
`bible/voice-profile.md`.

## Unit and sequence

Unit = **chapter**; files stay `unit-NN`. Sequence `linear`: write in outline
order. Digests on, from `templates/chapter-digest-literary.md` (story state
only, no voice samples). No knowledge graph: `bible/plot-structure.md`,
`arcs.md`, `timeline.md`, `story-ledger.yaml` and the character sheets carry
that role.

## The four rules — no per-project waiver

- **R1 — every character has an arc.** Every character (role `protagonist`,
  `principal`, `secondary`) has a complete sheet (`templates/character-sheet.md`):
  backstory, personality, contradiction, want, need, voice, and arc (type,
  start, end, ≥ 1 turning point assigned to a unit, `resolves_in`). A `flat` arc
  is legal and names what the character's constancy `tests`. No `TBD`; the
  template lists the placeholder values that count as empty (`N/A`, `x`,
  `(pendiente)`, `{{…}}` included), and the narrative fields need at least three
  words. A sheet is complete only when the human approved it and the
  orchestrator ran `python scripts/pipeline_step.py sign <slug> --by <human>`
  (`signed_on`, `signed_hash`); any later change to its content is
  `CHAR-UNSIGNED-CHANGE` until the block is re-run and the sheet re-signed.
- **R2 — the story has an ending** before drafting: `ending.resolution`,
  `ending.answer` (to the dramatic question) and `ending.final_unit` in the
  front matter of `bible/plot-structure.md`. Every arc resolves at or before
  `final_unit`.
- **R3 — no drafting until R1 and R2 hold for everyone in the outline.**
  `python scripts/pipeline_step.py ready` must exit 0 before `phase: drafting`,
  and it is re-checked at every step that drafts or ships text: `check unit-NN
  writer` and `done unit-NN writer` (the full `ready` result, not only the
  unit's cast), `approve` and `apply-edits`. If the human asks to start anyway,
  explain the rule and run the questionnaire for what is missing: short answers
  are fine, empty ones are not.
- **R4 — characters may join mid-book; the questionnaire runs again.**
  Triggers: the human or the Writer proposes one; the outline gains a name
  (`characters_present` or a scene card: `CHAR-UNKNOWN`); `check_story.py` or
  `lint_fiction.py` reports `NEW-CHARACTER` / `unknown_name` (a name
  mid-sentence, one that is no common word and never lowercase — "Gustavo
  no saludó." counts — or one in a speaker/actor position: "—dijo el viejo
  Gustavo", "Gustavo, con las manos en los bolsillos, dijo…", "Entró Gustavo";
  italics, ALL CAPS, internal capitals, section headings and table cells are
  scanned too) or `EXTRA-PROMOTE` / `mentioned_on_stage`. An ordinary
  word misread as a name (a first-person verb opening a sentence) goes in
  `bible/lexicon.yaml → common_words`; a name never does — mid-sentence it is
  caught whatever the list says. The unit pauses; the orchestrator first asks
  the human, per flagged token, "is this a person?" (no → `common_words`,
  re-run; a public figure seen from a distance, never in a scene with the
  characters → `non_person_names`, re-run; a person in the story →) runs
  `references/character-questionnaire.md` with the human; sheet, arcs, outline
  and ledger are updated; the human signs; the unit restarts at the Writer.
  **The Writer never invents a named character.**

**Extras.** Unnamed incidental figures seen in one unit at most live in
`bible/characters/_extras.md` (`templates/extras.md`). A name or a second unit
makes them characters (R4); a label adds no known name, so a label word used
as a name on the page is `EXTRA-PROMOTE`. People only mentioned, never on
stage, are listed in `bible/world.md` § Names; places, institutions and brands
in its other sections; the outline's `location` words count as places. ANY of
these — a § Names entry, a place, a location word — that speaks or acts on the
page is a person (`EXTRA-PROMOTE`: a "place" that speaks is a person), and a
§ Names entry in a scene card is a character (R4). Every file in
`bible/characters/` except `_extras.md` is a sheet with valid front matter, a
role and its own slug — a broken or role-less file cannot make a name known.
No waiver, human approval or override passes a story block. Why:
`docs/rationale/literary.md#enforcement-holes`.

**Known gap (documented, not fixed).** A name that is also a common noun
(Luz, Paz, Consuelo), used only sentence-initially and never in a
speaker/actor position while the noun is written in lowercase elsewhere ("Luz
era la hija de Rosa." next to "no había luz"), reads as the noun and is not
flagged. The semantic backstop is the Critic's `character-3` (every named
person on stage has a sheet) and CG Mode A (continuity against the sheets).
Code fences are not prose and are not scanned.

## Pipeline (per chapter)

```
Writer (scene by scene) → [human picks key-scene version] → Editor (assembly)
  → Humanizer → Reader-POV → CG Mode A (literary) → checks → Critic
  → [Adversarial] → Proofreader → Human review
  → (approve) `pipeline_step.py approve` → CG Mode B → digest → reader-journal update → archive
```

Dispatch, `pipeline_step.py` brackets, isolation, loops, retry cap (3) and the
plateau rule: `references/pipeline.md`. Literary specifics:

- `pipeline_step.py check unit-NN writer` requires the full `ready` result
  (R3) and runs `check_story.py --unit`; a blocker stops the unit. `done
  unit-NN writer` re-checks both on the draft (exit 3 = pause). The Critic and
  the Proofreader refuse a `checks.json` computed on another text
  (`source_sha1`) and re-run the story check live.
- The literary reader reads `humanized.clean.md` (`pipeline_step.py clean`),
  never the outline, and re-runs after every Editor or Humanizer loopback.
- `key_scene: true` → `literary.key_scene_versions` divergent versions; the
  human picks before the Editor.
- On approval `python scripts/pipeline_step.py approve unit-NN` copies
  `proofread.md` to `final/` with every HTML comment stripped: a novel ships
  no SCENE markers, flags or logs. It refuses while `ready` fails or the text
  carries a story block.
- On approval the orchestrator appends the Writer's declared extras to
  `_extras.md` and the reader's § Journal update to `bible/reader-journal.md`.
- `models.roles.humanizer: creative`.

## Human packet

Short, in this order: the chapter exactly as it will ship, with the
Proofreader's diff; the 3 most singular and 3 most generic passages (Critic
Observations);
tic counts (`checks.md`); the journal excerpt (predictions scored, forward
pull, pairwise note); failing scorecard rows; 1–3 decisions (unverifiable
facts, WRITER NOTEs, VOICE-RISK calls). Everything else is linked, not pasted.
Rejection notes go, dated, to `drafts/unit-NN/human-notes.md`.
Why: `docs/rationale/literary.md#human-taste`

## Periodic passes

- **Tic pass**, every `literary.tic_pass_every` (default 3) approved chapters:
  `lint_fiction.py --book` → Humanizer batch mode
  (`references/agents/humanizer-literary.md` § Tic pass) → the human accepts →
  `pipeline_step.py apply-edits` (refused, nothing written, if `ready` fails or
  an edited unit would carry a story block — a tic pass cannot add a name) →
  fix-then-verify (`references/pipeline.md`).
- **Singularity audit** every 5 approved chapters (Continuity Guardian).
- **Manuscript gate**: `references/manuscript-gate-literary.md`.

## Facts

`literary.fact_check: realistic` → CG Mode A's facts lane checks every
verifiable real-world detail (dates and weekdays, results, geography, prices,
public events). `invented` → `bible/world.md` declares the world fictional and
the lane is off. Research decisions live in `world.md` so agents stop
re-litigating them. No SOURCE comments, no running example.

## Register, openings, closings, risk

Register is per project (`bible/style-guide.md`, `bible/voice-profile.md`);
the floor is `references/anti-mediocrity-literary.md`. No opening rotation:
`rhet-6` does not apply; `lint_fiction` `opening_repeat` is an observation.
Closings follow the outline beat — no "end with momentum" rule. VOICE-RISK is
optional, 0–2 per chapter, logged in the digest so the human sees whether the
risks keep taking one shape. Why: `docs/rationale/literary.md#quotas-removed`

## Rubric deltas

None: the families live in `references/rubric-literary.md` (`beats`,
`character`, `arc`, `ending`, `voice`, `craft`, `format`, `reader_pov`,
`continuity`; `rhet-2` only), scored with full-mode tolerance.

## Reader-POV persona

The reader in `meta.yaml → audience.primary`, who is tired of
`audience.known_frustrations`, reading as `literary.reader_profile` says
(`holistic`: character, subtext, language; `surface`: plot and pace). Widely
read in the genre; has seen no bible, no outline, no checklist.

## Build targets

Phase 5 (`references/build-export.md`): EPUB / PDF / DOCX into `build/`.
Confirm with the human: trim and format, scene-break glyph, dialogue
punctuation, chapter title pages, front and back matter.
