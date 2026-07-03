# Profile — corporate-guide

Internal guides written for one specific organization: best-practices guides,
process manuals, onboarding material, internal handbooks. The reader is a
colleague on the clock, not a customer who bought a book. Every agent loads
this file at the start of its turn; where it disagrees with an agent file on
register or structure, this profile wins.

## Unit

Files use `unit-NN`. The human-facing word is **section** — never "chapter".
A chapter implies a book, and book phraseology is exactly the register this
profile exists to suppress: once agents think "chapter", teasers, arcs, and
transformation promises follow.

## Sequence: linear-light

- Sections have a recommended order, but every section opens self-contained.
  Assume the reader jumped straight here from an intranet link.
- Digests: ON, light use. Digests keep terminology and decisions consistent
  across sections; they do NOT establish what the reader "already read" —
  the reader read nothing. Never write prose that leans on a prior section
  having been read.
- Forward references: by topic only ("escalation is covered in the section
  on incident handling"). Never numbered, never teased.
- Knowledge graph: terminology-only (per SKILL.md Phase 1.5). It exists so
  every section calls the same thing by the same name, not to sequence
  concepts.

## Register: sober corporate — these are defaults, not suggestions

The natural drafting register for long-form nonfiction is a trade book:
hooks, stakes, punchy closers. Internal guides need the opposite, and if the
profile does not bake that in, the human ends up legislating it by hand and
paying rework cycles for it. Writer and Humanizer treat these as hard rules;
the Critic enforces them through the `profile` and `rhet` rubric families.

1. **No mic-drops, no punchy-for-effect prose.** No one-line dramatic
   closers, no snappy inversions built for applause. The voice is a
   competent colleague explaining how things work here — not a keynote.
   - BAD: "Get this wrong, and the whole pipeline burns."
2. **No dramatized stakes.** State consequences factually, at their real
   magnitude, with the actual failure and its actual cost.
   - BAD: "One bad prompt silently poisons everything downstream."
3. **No self-reference to the document.** Never "this guide", "this book",
   "this chapter", "in the pages ahead". The document talks about the work,
   not about itself. Humanizer: watch yourself here — book phraseology is a
   polish-time default that creeps in even when the draft was clean.
4. **No cliffhangers.** Closings are a plain recap or nothing (see below).
   Ending on an open question or a teaser is a `rhet-4` fail.
5. **No numbered cross-references in prose.** Cross-reference by topic, not
   "see Section 4". Internal guides get reordered, split into intranet
   pages, and partially republished — numbers rot, topics don't.
6. **No reader-transformation promises.** Never "after this section you
   will be able to...". Describe what the section covers, not what the
   reader will become.
7. **No pedagogical dichotomy framing unless the dichotomy is real.**
   "Most people think X, but actually Y" only when X is a documented
   misconception in this organization — not as an engagement device.

## Openings and closings

- **Openings**: state what the section covers and when a colleague needs
  it, grounded in the organization's context. The voice-profile opening
  rotation applies (rhet-6 is enforced), but the rotation menu chosen at
  setup must contain only sober structures — direct statement of scope, a
  concrete internal case, a question a colleague actually asks. No tension
  hooks.
- **Closings**: `recap` or `none`, fixed per project in voice-profile.md.
  A recap is a plain summary of the rules and decisions the section
  established. No bridges, no momentum, no "next up".

## Citation policy: invisible

Ground claims in `bible/sources/` and cite in HTML comments per the Writer's
contract. The rendered document shows no citations — an internal guide with
academic apparatus reads as a term paper. Confidence comes from the review
pipeline, not visible sourcing.

## Examples, callouts, practice

- **Examples come from the organization's context**: its systems, roles,
  and workflows as described in `meta.yaml → organization` and the source
  library. Use a generic industry example only when no internal equivalent
  exists. Internal readers dismiss generic examples as "not how it works
  here"; recognition is what drives adoption.
- **Running example**: off by default. If setup enables one, use
  `bible/examples-library.md` as usual, built on an internal case.
- **Callouts**: `Note` / `Template` / `Checklist` only. Never "Recipe"
  (cookbook branding) and no Warning/Trap theatrics — a risk worth flagging
  goes in a Note with the factual consequence.
- **No exercises.** Optionally, short **practice** items ("apply this to
  your own [internal case]") if setup enables them. Practice items use the
  organization's real workflows, never invented scenarios.

## meta.yaml additions

```yaml
organization:
  name:               # who the guide is for
  audience_role:      # who reads it: "data analysts", "all engineering staff"
  internal_context: | # 3-5 lines: systems, workflows, vocabulary that
                      # examples must draw from
  confidentiality:    # public | internal | confidential — what source
                      # material may be quoted or described verbatim
```

Writers pull example material from `internal_context`. The `confidentiality`
field limits what can appear verbatim in prose; when in doubt, paraphrase
and flag for the human.

## Rubric deltas

- `pedagogy-3` (redefined by base rubric to "closing matches profile
  policy"): here the policy is recap-or-none. A bridge or momentum closer
  fails.
- `rhet-4` (artificial cliffhanger): budget is 0 — closing policy is
  recap/none, so the item is always live.
Base `profile-1/2/3` (register, citation policy, opening) apply as the
universal spine. This profile ADDS items in its own `corp-*` id family
(never reusing `profile-N` — see `references/rubric.md` § Profile compliance).
These make specific register prohibitions countable rather than leaving them
to base `profile-1`'s general scan:

- ADD `corp-1` — no self-reference to the document. Countable: grep for
  `this (guide|book|chapter|section|document)` as the sentence's subject.
  **significant**.
- ADD `corp-2` — no reader-transformation promises. Countable: grep for
  "you will be able to", "by the end of this". **significant**.
- ADD `corp-3` — examples use the organization's context wherever an
  internal equivalent exists. **significant**.
- `outline-4` (exercises solvable): applies only when practice items are
  enabled; otherwise `not_applicable`.

## Reader-POV persona (full mode)

An employee of `organization.name` in `audience_role`, with ten minutes
between meetings and one concrete question. They arrived via a link, read
nothing before this section. Report: did they get their answer, and how far
in; what assumed a section they never read; and — decisive for this profile
— did any passage feel like it was *selling* them something. To an internal
reader, register breach reads as marketing, and marketing reads as untrust.

## Build targets (Phase 5)

DOCX and PDF with the organization's front matter: name, confidentiality
notice, version and date. Section numbering is applied at build time, never
in prose — see rule 5. Details in `references/build-export.md`.
