# Profile — corporate-guide

Internal guides for one organization: best practices, process manuals,
onboarding, handbooks. The reader is a colleague on the clock, not a customer.
Where this file disagrees with an agent file on register or structure, this
file wins.

## Unit

A **section** (files `unit-NN`) — never "chapter". Once agents think
"chapter", teasers, arcs and transformation promises follow.

## Sequence: linear-light

- A recommended order, but every section opens self-contained: the reader
  arrived from an intranet link.
- Digests on, for terminology and decisions only — never prose that assumes a
  prior section was read.
- Forward references by topic only ("escalation is covered in incident
  handling"); never numbered, never teased.
- Knowledge graph: terminology-only.

## Register: sober corporate — defaults, not suggestions

Writer and Humanizer treat these as hard rules; the Critic enforces them
through `profile-1`, `rhet` and the `corp-*` rows.

1. **No mic-drops** or punchy-for-effect closers. BAD: "Get this wrong, and the
   whole pipeline burns."
2. **No dramatized stakes** — the actual failure at its actual cost. BAD: "One
   bad prompt silently poisons everything downstream."
3. **No self-reference** ("this guide", "this chapter", "in the pages ahead").
   A polish-time default that creeps in even when the draft was clean.
4. **No cliffhangers** — recap or nothing (`rhet-4`).
5. **No numbered cross-references** in prose — guides get reordered and
   republished; topics survive, numbers rot.
6. **No reader-transformation promises** ("after this section you will be able
   to…").
7. **No dichotomy framing** ("most people think X, but…") unless X is a
   documented misconception in this organization.

## Openings and closings

- **Openings**: what the section covers and when a colleague needs it, in the
  organization's context. The voice-profile rotation applies (`rhet-6`), but
  every structure on the menu is sober: scope statement, internal case, a
  question a colleague actually asks.
- **Closings**: `recap` or `none`, fixed in the voice profile. No bridges, no
  momentum.

## Citation policy: invisible

Ground in `bible/sources/`, cite in HTML comments; the rendered guide shows no
citations. Process claims that only a person can confirm (owners, thresholds,
SLAs) with no source go to the verification plan with `needs: person`.

## Examples, callouts, practice

- Examples come from `meta.yaml → organization.internal_context` and the
  sources; a generic industry example only when no internal equivalent exists.
- Running example off by default; if setup enables one, build it on an internal
  case.
- Callouts: `Note` / `Template` / `Checklist` only — no "Recipe", no
  Warning theatrics.
- No exercises; optional **practice** items on the organization's real
  workflows if setup enables them.

## meta.yaml additions

```yaml
organization:
  name:               # who the guide is for
  audience_role:      # who reads it
  internal_context: | # systems, workflows, vocabulary examples must draw from
  confidentiality:    # public | internal | confidential — limits verbatim quoting
```

## Reader testing (optional)

`pipeline.reader_testing: true` adds a check after the Humanizer, run by the
orchestrator with two isolated subagents:

1. **Predict**: from the outline entry and the persona below only (not the
   text), list 5–10 questions a colleague would bring to this section.
2. **Answer**: a fresh subagent answers each from `humanized.clean.md` only,
   quoting the passage it used, or says "not answered".

The orchestrator writes `drafts/unit-NN/reader-test.md` (question, answer,
quote, answered / partial / not answered) and the Critic scores `corp-4`.

## Rubric deltas

Base `references/rubric-nonfiction.md`, with:

- `pedagogy-3`: the policy is recap-or-none; a bridge or momentum closer fails.
- `rhet-4`: always live (budget 0).
- `outline-4`: `not_applicable` unless practice items are enabled.
- ADD `corp-1` (significant → Humanizer) — no self-reference to the document;
  quote each hit.
- ADD `corp-2` (significant → Humanizer) — no reader-transformation promises.
- ADD `corp-3` (significant → Writer) — examples use the organization's
  context wherever an internal equivalent exists.
- ADD `corp-4` (significant → Writer; `not_applicable` without reader testing)
  — every predicted question is answered by the text; an unanswered question
  the section's scope covers fails.

## Reader-POV persona (full mode, reader testing)

An employee of `organization.name` in `audience_role`, ten minutes between
meetings, one concrete question, arrived via a link. Report: did they get the
answer and how far in; what assumed a section they never read; and — decisive
here — did any passage feel like it was *selling* them something.

## Build targets

DOCX and PDF with the organization's front matter (name, confidentiality,
version, date); section numbering at build time only
(`references/build-export.md`).
