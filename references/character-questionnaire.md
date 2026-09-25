# Character questionnaire

Run with the human for **every** character at setup and again for every
character added mid-book (R1, R4 in `references/profiles/book-literary.md`).
Output: `bible/characters/<slug>.md` from `templates/character-sheet.md`. The
sheet becomes `complete` only through `python scripts/pipeline_step.py sign
<slug> --by <human>`, which the orchestrator runs ONLY when the human says the
sheet is approved: it writes `status: complete`, `signed_on` (today),
`signed_by` and `signed_hash` — a hash of name, slug, role, aliases, the six
required fields and the arc. `check_story.py` rejects `complete` without a real
`signed_on` date (2000-01-01 … today) or without a matching `signed_hash`; any
later change to those fields is `CHAR-UNSIGNED-CHANGE` until the block that
changed is run again and the human re-signs. Never write the signature keys by
hand.

## Protocol

1. **One block at a time** (A–H below), in the human's language; the sheet is
   written in the book's language.
2. **Propose, don't interrogate.** For each question offer a draft answer
   derived from `literary.seeds`, `bible/braindump.md`, the bible and —
   mid-book — the approved chapters. The human confirms, edits or replaces it.
   Quote the braindump back when it already answers; never present a draft as
   settled, never overwrite what the seeds or the human fixed.
3. **Short answers are fine; empty ones are not.** Placeholder values count as
   empty (`TBD`, `N/A`, `x`, `-`, `(pendiente)`, `a completar`, `{{…}}`,
   `[template text]`… — full list in the template), and the narrative fields
   (backstory, personality, contradiction, want, need, voice, arc start/end,
   a flat arc's `tests`) need at least three words. If the human cannot answer
   yet, stop the block and say what stays blocked: drafting (R3) or the paused
   unit (R4).
4. **Contradiction check** after each block (below).
5. **Close**: write the sheet, update the linked files (§ Outputs), read back a
   five-line summary, get the human's explicit approval, then run `sign`.

## Blocks

- **A. Identity** — name; what others call them (→ `aliases`); `slug`; role
  (`protagonist | principal | secondary`); age or birth date; occupation;
  where they live; 3–5 physical details. Eyes, hair and age become the
  reference for `lint_fiction` `attribute_mentions`.
- **B. Backstory** — the two or three past events that still act on the
  present; the wound and how it shows now.
- **C. Personality and contradiction** — how they behave under pressure; two
  traits both true that should cancel and don't.
- **D. Want and need** — the conscious want that drives their scenes; the
  need underneath (usually against the want); fear; the lie they tell
  themselves; what they won't do.
- **E. Voice** — vocabulary, sentence length, register shifts, verbal habits,
  what they never say; how they sound different from each character they
  share scenes with (the cast must not share one register); one sample line
  the human accepts or writes.
- **F. Arc** — `type` (positive | negative | flat); start and end state; ≥ 1
  turning point, each tied to a unit and the change it causes; `resolves_in`
  ≤ `ending.final_unit`. Flat: `tests` — what their constancy tests or changes
  in others.
- **G. Relationships** — with each character they share scenes with: the
  dynamic, not a label ("respects him, resents needing him").
- **H. Never** — two to four concrete things they would never do or say.

## Contradiction check

Against the other sheets, `timeline.md`, `world.md`, `plot-structure.md`, the
outline and the ledger:

- ages and dates against the timeline; places against the world;
- relationships mirrored (A's sheet says rival; B's says friend, or nothing);
- each turning point in a unit that exists, where the character is present,
  before or at `final_unit`;
- names: same first name, near-duplicate spelling, alias clash;
- voice too close to an existing character's.

Per hit: state it, propose a fix, the human picks.

## Mid-book additions (R4)

Before block A, settle:

1. **Story function** — what the book needs from them that no existing
   character provides. If one could, propose that instead.
2. **Why now** — why they enter in this unit.
3. **Exit** — where they leave the story, or how they stay to the end.
4. **What they change** — in whom, by which unit.
5. **Ledger** — which entries they plant, trigger or pay; new entries with a
   planned `payoff_unit`.
6. **Retcon check** — were they implied earlier? Search `final/` for the name,
   aliases and role. An earlier mention becomes a constraint on the sheet, or a
   retcon the human approves explicitly.

Then run A–H. Set `added_mid_book: true` and `added_in_unit: unit-NN`; turning
points and `resolves_in` fall inside the remaining outline (from the current
unit to `final_unit`). A promoted extra keeps the facts already on the page.

## Outputs

- The sheet: every front-matter key filled, the block answers as prose
  sections, `Signed off by: <human> on <date>` at the end; then — after the
  human approves — `python scripts/pipeline_step.py sign <slug> --by <human>`
  writes `status: complete`, `signed_on`, `signed_by` and `signed_hash`. A
  later edit to the sheet's content (a new alias included) needs the block
  again and a new `sign`.
- One sheet per character, one slug per sheet: every file in
  `bible/characters/` except `_extras.md` must have valid front matter and a
  role (`protagonist | principal | secondary`) — a stray, broken or role-less
  file blocks every mode (`CHAR-INCOMPLETE`, `CHAR-DUPLICATE`).
- `outline/units.yaml`: the slug in `characters_present` of every unit they
  appear in; an `arc_moves` entry per turning point; `secondary_lines` where
  they recur.
- `bible/arcs.md`: the relational arcs they join.
- `bible/story-ledger.yaml`: the entries from mid-book item 5 or block F.
- `bible/characters/_extras.md` / `bible/world.md` (§ Names or a place):
  remove the entry when an extra or a mentioned-only word comes on stage. An
  extra's label never holds a name, a world.md or outline-location word that
  speaks or acts is a person, and neither makes a name "known".
- Verify: `python scripts/check_story.py --ready-to-draft` (setup, outline) or
  `python scripts/pipeline_step.py check unit-NN writer` (mid-book) no longer
  reports this character.
