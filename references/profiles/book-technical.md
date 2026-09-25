# Profile — book-technical

Commercial or self-published technical book: manual, tutorial, reference,
cookbook, textbook, or technically grounded opinion. Correctness is enforced by
machine checks and a grounding library; the voice belongs to the project. Every
agent loads this file after its own, then `bible/meta.yaml`, then (prose
agents) `bible/voice-profile.md`.

## Unit

A **chapter** (files `unit-NN`). `project.subtype` — tutorial | reference |
cookbook | textbook | opinion — shapes reading mode, how self-contained each
chapter is, and the weight of exercises; confirm it in setup. Chapter anatomy
(exercises and their format, a callout set of 4–6 types, cross-reference style)
is declared per project in `meta.yaml → conventions`; this profile fixes none of
it, because one skill-wide anatomy makes unrelated books read as one author.

## Sequence: linear

- **Digests on** (`references/chapter-digest.md`): from unit 6, agents read all
  prior digests plus only the previous chapter in full.
- **Knowledge graph mandatory** (Phase 1.5). The Critic blocks chapters whose
  `concepts_used` are introduced later.
- **Forward references only when declared** in the outline and carried by the
  tracker until paid.
- **Write in outline order.**

## Register

Expert-practitioner teaching voice: someone who has done the work explaining it
to a colleague — direct, concrete, honest about trade-offs and failure modes.
That sentence is the whole register this profile ships. Formality, person,
humor and rhythm live in `bible/voice-profile.md` and `meta.yaml → tone`; when
the voice profile is silent, ask the human — never fall back to a punchy
default.

Prohibited regardless of voice profile: citational frames in running prose
("as the official documentation states", parenthetical source drops); prose
patterns imported from the skill's files.

## Openings and closings

- **Openings**: 3–4 structures chosen at setup, recorded in the voice profile.
  The same structure may not open consecutive chapters (`rhet-6`); the Writer
  declares its choice, the Critic verifies.
- **Closings**: concrete recap or earned bridge by default — a recap names what
  the chapter established; a bridge is earned only when the next chapter
  depends on this one. Cliffhangers fail `rhet-4`. The voice profile may set
  `none`. `pedagogy-3` checks whatever policy is in force.

## Citation policy: invisible

- Mandatory pre-draft grounding pass whenever `bible/sources/` holds relevant
  material (`grounding-notes.md`); load-bearing claims carry
  `<!-- SOURCE: … -->` comments, for the Reviewer, not the reader.
- **Number provenance**: every number (defaults, limits, benchmarks, sizes)
  carries a SOURCE comment or an `<!-- ARTIFACT: … -->` pointer, or becomes a
  verification-plan item. No orphan figures.
- Every identifier is checked against the sources by `check_identifiers.py`
  (`tech_a-4`). Build the index in setup: `python scripts/check_identifiers.py
  --build-index`.
- Empty or irrelevant library → the grounding pass is skipped with a note and
  Axis B degrades with a visible "grounding library empty" flag. Never silent.
- Machine checks per `meta.yaml → validation_surface`
  (`references/validation-surface.md`); nothing checkable → declare `empty`.

## Running example

On or off per project (typical for tutorial and project-based subtypes). When
on, `bible/examples-library.md` tracks it and each digest records its state. Do
not graft one onto a reference book.

## Rubric deltas

None. The full `references/rubric-nonfiction.md` applies — including all seven
`rhet` items (quotas overridable in the voice profile) and the `profile` spine
(citation invisibility, opening membership). Exercise items apply only when
`meta.yaml` declares exercises.

## Reader-POV persona

The reader in `meta.yaml → audience`: level, context, reading mode,
motivation, `known_frustrations`. Play that person, not a generic beginner.
Per chapter in `full` mode; in the Phase 4 polish pass in `fast` mode.

## Build targets

EPUB / PDF / DOCX (`references/build-export.md`). Confirm targets, title page,
TOC depth and code-block styling first.
