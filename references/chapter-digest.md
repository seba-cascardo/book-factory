# Digest protocol

Past unit 4–5 of a sequential project, feeding every prior unit in full to
every agent wastes context and crowds out what matters (the outline entry, the
relevant bible sections). A **digest** is a short, structured record of a unit,
written once after approval, that agents read instead of the full unit.

## Which template

| Profile | Template | Carries |
|---|---|---|
| `book-technical`, `corporate-guide` | `templates/chapter-digest.md` | concepts, running-example state, forward references, terminology |
| `scientific-paper` | `templates/chapter-digest.md`, claims subset | claims-map entries used and their status — what later sections may rely on |
| `book-literary` | `templates/chapter-digest-literary.md` | plot state, characters, story-ledger movements, open questions, timeline, VOICE-RISK log |
| `product-docs` | none | articles are standalone; per-article frontmatter and the KG terminology layer carry what a digest would |

Target 300–500 words (papers shorter). Digests record **state**, not prose:
**no voice samples, no quoted passages to imitate**. The Writer reads every
digest; a sample there would make it calibrate against its neighbours, which
the skill forbids — voice comes only from `bible/voice-profile.md`.

## Nonfiction fields

1. **Gist** (≤ 120 words) — what the unit delivered and the mental model the
   reader leaves with; not a section recap.
2. **Concepts introduced** — KG ids with the one-line definition as used here:
   the authoritative record of when each concept entered.
3. **Concepts reinforced** — ids only.
4. **Running examples state** — each tracked example at unit end.
5. **Open forward references** — debts later units must pay (mirrored in the
   tracker).
6. **Terminology decisions** — terms chosen over synonyms, defined inline, or
   narrowed.
7. **Opening structure used** — for the next unit's `rhet-6`.

Not included: section recaps, code listings (read the archive or
`examples-library.md`), anti-mediocrity notes (they live in `critique.md`).

## Who reads what

`references/pipeline.md` § Digests has the table. In short: the Writer and
Technical Reviewer read all digests plus the most recent final (continuity
only); the Humanizer reads the most recent digest; the Critic and CG Mode A
read all; the Editor, Reader-POV and Proofreader read none.

## When and how

After approval, CG Mode B, then the orchestrator writes
`bible/digests/unit-NN.digest.md` from `final/unit-NN.md`, the updated tracker
(literary: and the story ledger), bracketed as agent `digest`
(`pipeline_step.py check` / `done`). Then archiving.

Regenerate only when the unit is edited after approval, when the KG change
touches its `concepts_introduced`, or when the human asks. Batch passes do not
regenerate digests.

## Disabling

`pipeline.chapter_digest.enabled: false` for short projects (≤ 8 units),
reference sets with independent units, or to test whether a quality problem is
context starvation. Default on for linear and linear-light profiles and for
literary projects past 6 units.
