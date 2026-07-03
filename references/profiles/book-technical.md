# Profile: book-technical

Commercial or self-published technical book: manual, tutorial, reference,
cookbook, textbook, or technically grounded opinion. Correctness is enforced
by machine checks and a grounding library; the voice belongs to the project,
not to this skill. Every agent loads this file at the start of its turn,
then `bible/meta.yaml`, then (prose agents) `bible/voice-profile.md`.

## Unit

The unit is a **chapter**. Files use `unit-NN`; always say "chapter" when
talking to the human.

`project.subtype` in meta.yaml (tutorial / reference / cookbook / textbook /
opinion) refines how chapters teach: reading mode, how self-contained each
chapter must be, how much weight exercises carry. Confirm it during setup —
it shapes the Writer's and Critic's framing, so a wrong subtype costs drafts.

Chapter anatomy is declared per project in `meta.yaml → conventions`, not
here: exercises on/off and their format, callout set (keep it to 4–6 types),
cross-reference style, terminology convention. This profile deliberately
fixes none of them — a single skill-wide exercise format and callout set is
one of the fingerprints that made unrelated books read as one author.

## Sequence

`linear`. Consequences:

- **Digests on.** After approval, write the chapter digest to
  `bible/digests/` (`references/chapter-digest.md`). From unit 6 onward,
  agents read all prior digests plus only the immediately preceding chapter
  in full — continuity without context bloat.
- **Knowledge graph mandatory.** `bible/knowledge-graph.yaml` is built in
  Phase 1.5 and wired to chapters during outlining. The Writer uses it to
  know what the reader already knows; the Critic blocks chapters whose
  `concepts_used` have `introduced_in` later than the current unit.
- **Forward references permitted only when declared.** The outline declares
  them; the continuity tracker carries them until resolved. Undeclared
  pointing-ahead is a rubric hit, not a stylistic choice.
- **Write in outline order.** Each chapter builds on approved predecessors.

## Register

Expert-practitioner teaching voice: someone who has done the work explaining
it to a colleague — direct, concrete, honest about trade-offs and failure
modes. That one sentence is the entire register this profile ships.

Everything more specific — formality, person, humor, sentence rhythm, how
much punch — is a per-project decision recorded in `bible/voice-profile.md`
(generated at setup, mandatory) and `meta.yaml → voice`. When the voice
profile is silent on a register question, ask the human; do NOT fall back to
a punchy, dramatized default. Baked-in register defaults are exactly how
every project ends up sounding like the same book.

Prohibited regardless of voice profile:

- Citational-attribution frames in running prose ("as the official
  documentation states", "according to [source]", parenthetical source
  drops). Citations are invisible in this profile — see Citation policy.
- Importing prose patterns from the skill's reference files into a draft.
  GOOD examples come only from the project's own voice-profile.md.

## Openings and closings

- **Openings**: the allowed opening structures (3–4, chosen by the human at
  setup from the menu in `templates/voice-profile.md`) live in
  `bible/voice-profile.md`. Hard rule: the same structure may not open two
  consecutive chapters (`rhet-6`). The Writer declares which structure it
  used in its self-assessment; the Critic verifies. Rotation is enforced
  because a fixed opening formula is the single strongest homogeneity signal
  across books.
- **Closings**: default policy is **concrete recap or earned bridge**. A
  recap must name the specific things the chapter established — not "we
  covered a lot of ground". A bridge is earned only when the next chapter
  actually depends on this one; artificial cliffhangers are a rubric fail
  (`rhet-4`). The voice profile may override the default (e.g., to `none`).
  The Critic evaluates `pedagogy-3` against whatever policy is in force.

## Citation policy

`invisible`. Claims trace to sources, but citations never surface in prose:

- The Writer runs a mandatory pre-draft grounding pass against
  `bible/sources/` whenever the library holds material relevant to the
  chapter, producing `drafts/unit-NN/grounding-notes.md`. Load-bearing
  claims carry inline `<!-- SOURCE: ... -->` HTML comments — one per claim,
  only for load-bearing specifics. The comments exist for the Technical
  Reviewer, not the reader.
- If `bible/sources/` is empty or has nothing relevant, skip the grounding
  pass with a documented note at the top of the self-assessment. The
  Technical Reviewer's Axis B then degrades to prose-audit with a visible
  "grounding library empty" flag the Critic propagates to the human. The
  degradation is always announced, never silent — the human chose it.
- Machine checks (Axis A) run per `meta.yaml → validation_surface`
  (`references/validation-surface.md`). A book with nothing machine-checkable
  declares `surface: empty` explicitly.

## Running example

Supported (on/off per project; typical for tutorial and project-based
subtypes). When on, its state is tracked in `bible/examples-library.md` and
each digest records where the example stands, so later chapters extend it
instead of contradicting it. When off, do not force one — a running example
grafted onto a reference book reads as filler.

## Rubric deltas

None removed. The full nonfiction rubric in `references/rubric.md` applies:
all families including the complete `rhet` family (budgets overridable in
voice-profile.md) and the `profile` family, which for this profile checks
citation invisibility, closing-policy compliance, and opening rotation.
Exercise-related items apply only when meta.yaml declares exercises.

## Reader-POV persona

Simulate the reader defined in `meta.yaml → audience`: level, context,
reading mode, motivation, and `known_frustrations`. Play that person, not a
generic "beginner" — the persona exists to catch the specific boredom,
condescension, or opacity this audience will punish. Runs per chapter in
`full` mode; in `fast` mode it runs in the batch polish pass (Phase 4).

## Build targets

Phase 5 (`references/build-export.md`): **EPUB / PDF / DOCX**, via pandoc or
the docx/pdf skills when available. Output to `build/`. Confirm targets and
front-matter (title page, TOC depth, code-block styling) with the human
before building.
