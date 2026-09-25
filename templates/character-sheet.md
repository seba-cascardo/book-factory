---
name: ""
slug: ""
aliases: []
role: secondary            # protagonist | principal | secondary
status: draft              # draft | complete — written by `pipeline_step.py sign`, never by hand
signed_on: null            # written by `sign`: the date the human approved (YYYY-MM-DD)
signed_by: null            # written by `sign --by <human>`
signed_hash: null          # written by `sign`: hash of name, slug, role, aliases, the
                           # required fields and the arc — any later edit → CHAR-UNSIGNED-CHANGE
added_mid_book: false
added_in_unit: null
backstory: ""              # REQUIRED
personality: ""            # REQUIRED
contradiction: ""          # REQUIRED
want: ""                   # REQUIRED
need: ""                   # REQUIRED
voice: ""                  # REQUIRED
arc:
  type: positive           # positive | negative | flat
  start: ""                # REQUIRED
  end: ""                  # REQUIRED
  tests: ""                # REQUIRED when type = flat
  turning_points:          # REQUIRED, >= 1
    - unit: unit-NN
      change: ""
  resolves_in: unit-NN     # REQUIRED, <= ending.final_unit
relationships:
  - with: ""               # slug
    dynamic: ""
---
<!-- templates/character-sheet.md → bible/characters/<slug>.md (book-literary).
     Filled through references/character-questionnaire.md, blocks A–H below.
     Front matter = the short answers; scripts parse it, keep the keys. Prose =
     the full answers. Empty means (scripts/bookkit/placeholder.py): "", null,
     TBD, TODO, N/A, x, -, none, nil, ?, ..., …, pendiente, (pendiente), a
     definir, por definir, sin definir, a completar, completar, <completar>,
     {{…}}, XXX, falta, Lorem ipsum, lo vemos, or any [bracketed template text].
     backstory, personality, contradiction, want, need, voice, arc.start,
     arc.end and a flat arc's tests need at least 3 words. When the human
     approves the sheet the orchestrator runs
     `python scripts/pipeline_step.py sign <slug> --by <human>` (status,
     signed_on, signed_by, signed_hash); an edit afterwards means re-running
     that questionnaire block and signing again. Current state (where they are,
     what they know now) lives in bible/continuity-tracker.md, never here.
     Delete this comment. -->

# [Name]

## A. Identity
[Age or birth date · occupation · where they live · 3–5 physical details:
eyes, hair, one distinguishing feature.]

## B. Backstory
[The past events that still act on the present; the wound and how it shows.]

## C. Personality and contradiction
[Under pressure they… · two traits, both true.]

## D. Want and need
[Want · need · fear · the lie they tell themselves · what they won't do.]

## E. Voice
[Vocabulary, sentence length, register shifts, verbal habits, what they never
say; how they differ from the characters they share scenes with.]
Sample line: "[one line only they would say]"

## F. Arc
[Start → end; each turning point and what forces it; flat: what their
constancy tests.]

## G. Relationships
- [slug]: [the dynamic, not a label]

## H. Never
- [a concrete act or line they would never produce]

Signed off by: [human] on [date].
