# Setup — Phase 1 (all profiles)

Setup is a collaborative design session, not a form. Each sub-phase produces a
bible artifact the human signs before the next begins. Load
`references/profiles/<profile>.md` first: it pre-answers many questions —
state the default and ask only where the human might deviate. Propose, don't
interrogate. Talk in the human's language; write the bible in the document's
language.

Sub-phases 1–4, 6 and 9 are common; 5 and 7 are nonfiction-only; 8 is
per-profile; 9 (voice profile) runs last because it derives from the approved
calibration passages.

---

## Sub-phase 1 — Scope

Establish the premise in one sentence; what is IN and OUT; concrete
prerequisites ("reads basic SQL", not "knows databases"); outcomes as verbs
(corporate-guide: the behavior that changes on the job); anti-scope — what
people will mistake the document for.
**Output**: `bible/meta.yaml` (from `templates/meta.yaml`: `project`, `scope`)
and `bible/scope.md` with scope and anti-scope in prose.

**book-literary** — scope is: genre and subgenre; tone; 2–5 influences, each
with a specific take ("McCarthy's refusal of quotation marks", not
"McCarthy"); negative constraints ("not YA despite a young protagonist") in
`scope.md`'s anti-scope. Then the human material, which the pipeline never
invents:

- **Seeds** in `meta.yaml → literary.seeds`: the title, the premise, and at
  least `literary.min_seeds` concrete details only this book has
  (`only_in_this_book`: places, objects, phrases, facts). Ask for them; offer
  no candidates.
- **Braindump**: everything the human already imagines, kept verbatim in
  `bible/braindump.md` — the reference to check later whether the design
  betrayed the intention.
- `literary.fact_check`: `realistic` (real places, dates, events — the facts
  lane checks them) or `invented`.

Missing seeds (`SEEDS-MISSING`) and too few human calibration passages
(sub-phase 6, `CALIBRATION-NO-HUMAN`) block `pipeline_step.py ready` exactly
as an incomplete sheet does. Why: `docs/rationale/literary.md#human-taste`

## Sub-phase 2 — Audience

The primary reader in one sentence (who, what they know, what they want),
level, reading context and mode, motivation, and **known frustrations** —
what bores, patronizes or loses them, so the Writer avoids it and Reader-POV
simulates it. **Output**: `audience` block (corporate-guide: together with the
organization block of sub-phase 8). **book-literary**: `audience.primary` also
states the experience the reader should have at the end; set
`literary.reader_profile` (`holistic` | `surface`).

## Sub-phase 3 — Tone and register

The profile's register defaults and prohibitions are the starting point;
record only deviations the human explicitly asks for. Decide person (you /
we / impersonal), formality within the profile's band, humor (err toward
less), personal voice and opinion. Literary: POV, tense, prose register,
profanity and explicit-content limits. **Output**: `tone` block — the envelope
only; identity comes in sub-phase 9.

## Sub-phase 4 — Conventions

Skip what the profile fixes: code style, shell and pinned versions; the
callout set (4–6 types; profile default); example policy (running example →
`bible/examples-library.md`); exercises or practice; terminology (initialize
`bible/glossary.md` now); cross-reference style; formatting (heading case,
Oxford comma, narration dash style, numbers, dates, language variant in
`project.language_variant`). **Output**: `conventions` block; glossary.

## Sub-phase 5 — Validation surface (nonfiction)

Name, per domain, what the Technical Reviewer can verify by machine and what it
cannot (`references/validation-surface.md`: `python_exec`,
`sql_dialect_check`, `linter`, `doc_cross_ref`, `proof_recheck`,
`citation_check`, `stats_check`, `empty`, …): which surfaces apply, which runner
checks each, and what each is pinned to. No machine-checkable surface →
`empty` with a reason, never a silent skip. Papers almost always declare
`citation_check`, plus `stats_check` with quantitative results. Names the book
defines itself (its own helpers, fixture names) go in
`validation_surface.identifier_allowlist`, so `check_identifiers.py` accepts
them; real APIs belong in the sources.
**Output**: `validation_surface` block, with `target_version` when pinned.

## Sub-phase 6 — Style guide and calibration passages

Fill `templates/style-guide.md`: sentence length, active/passive, jargon,
how concepts are introduced, diagrams and captions; literary: dialogue
conventions (the language's dialogue mark, attribution tradition) and
optional craft sources by subgenre.

Then 1–3 **calibration passages** (100–300 words) that show how a paragraph
should feel. Each carries `<!-- calibration-source: human | model |
reference -->` on the line under its heading. Iterate until the human says
"yes, THIS" — a tolerated passage calibrates every agent to a voice nobody
wanted.

- **book-literary**: at least `literary.human_calibration_passages` are
  written by the human (`human`); a `reference` passage (a published author
  the human picks) is for contrast, not imitation; a `model` passage is never
  the only source. Screen every `model` passage for what the rubric counts —
  "not X but Y" shapes, staccato runs, repeated gestures: a tic in a
  calibration passage gets imitated, then defended.
  Why: `docs/rationale/literary.md#calibration-contamination`
- Other profiles: real text the human models on, the human's own writing, or
  drafts refined together.

**Output**: `bible/style-guide.md`, approved.

## Sub-phase 7 — Sources library (nonfiction)

The Technical Reviewer audits every unit against `bible/sources/`; without a
library Axis B passes with a visible "no grounding library" note and misses
plausible-but-wrong framings. Literary projects may keep an un-audited
research folder in the same layout.

1. **Detect** what `bible/sources/` holds (`*.pdf`, `*.md`, `*-figures/`,
   `sources.md`). Empty → the human chooses: add sources, or proceed
   ungrounded (flagged). Never silently.
2. **Extract** each PDF with the `pdf` skill to a same-stem `.md` (headings
   kept; figures to `<stem>-figures/fig-NNN.png`); check the first pages
   against the PDF and fix OCR now; offer to split 400+-page files. A file
   that fails (encrypted, scanned, DRM) is decided with the human.
3. **Index**: draft `sources.md` (`templates/sources.md`) from each TOC and
   copyright page, then ask for what only the expert knows: authoritative
   for, not authoritative for, known wrong or outdated on. No sign-off, no
   progress — a wrong authoritative-for list poisons every Axis B check.
4. **Version drift**: when `target_version` differs from a source's, add a
   drift rule for the changed areas (divergence there is drift, not error).
5. **Identifier index**: `python scripts/check_identifiers.py --build-index`
   writes `bible/identifier-index.txt` from the sources; re-run it whenever
   a source is added. Identifiers verified by hand go under its `# allow`
   section, which survives rebuilds.

**Output**: signed `sources.md`, originals kept, extracted `.md` and figures,
the identifier index; an opt-out is recorded. scientific-paper: Zotero / arxiv / citecheck /
openreview tools, when connected, pull references, metadata and retraction
status — every reference still gets a `sources.md` entry and sign-off.

## Sub-phase 8 — Profile artifacts

### book-literary

The human approves each artifact before the next; nothing stays `TBD` for
characters or the ending (R1, R2 in `references/profiles/book-literary.md`).

- **Characters**: run `references/character-questionnaire.md` for **every**
  character — protagonist, principal, secondary — one sheet per character in
  `bible/characters/<slug>.md`. When the human approves a sheet, and only then,
  run `python scripts/pipeline_step.py sign <slug> --by <human>` (it writes
  `status: complete`, `signed_on`, `signed_by`, `signed_hash`). Unnamed
  one-unit figures are extras (`bible/characters/_extras.md`, from
  `templates/extras.md`); their labels never hold a name.
- **World** (`bible/world.md`): depth fitted to the genre; constraints for
  anything speculative; research decisions; with `fact_check: invented`, the
  declaration that the world is fictional. Every proper noun the book uses
  that is not a character is listed (`lint_fiction` treats anything else as
  unknown): places, institutions and brands under their own headings; people
  only mentioned, never on stage, under `## Names`. Any world.md word — a name
  or a place — that speaks or acts on the page, or a `## Names` entry in a
  scene card, is a person: it becomes a character (R4). The outline's
  `location` words count as places, never as people.
- **Plot structure** (`bible/plot-structure.md`, from
  `templates/plot-structure.md`): one committed framework, the dramatic
  question, major beats by unit, subplots, tension architecture. **The ending
  is mandatory**: `ending.resolution`, `ending.answer`, `ending.final_unit`.
- **Arcs** (`bible/arcs.md`, from `templates/arcs.md`): thematic and relational
  arcs only; character arcs live in the sheets.
- **Timeline** (`bible/timeline.md`): every event, backstory included; with
  `fact_check: realistic`, absolute dates with weekdays.
- **Story ledger** (`bible/story-ledger.yaml`, from
  `templates/story-ledger.yaml`): the plants, promises and mysteries already
  known, each with a planned payoff when possible (completed in Phase 2).
- **Reader journal** (`bible/reader-journal.md`, from
  `templates/reader-journal.md`): header only; the human may name a benchmark.
- **Tracker**: initialize `bible/continuity-tracker.md`.

### scientific-paper

Set `citation_style` (apa | ieee | vancouver | author-year). Seed
`bible/claims-map.yaml` with the 5–15 claims the paper stands on, each mapped
to its evidence — a citation in `bible/sources/` or an own result with its
data pointer; `pending` where evidence is still missing. Confirm the
Limitations section and the Methods reproducibility checklist now.

### corporate-guide

Add `organization` to `meta.yaml`: `name`, `audience_role`,
`internal_context` (systems, policies, house terms for examples),
`confidentiality` (public | internal | confidential — bounds what detail may
appear).

### product-docs

Agree the skeleton of each Diátaxis type (`tutorial`, `how-to`, `reference`,
`explanation`); a closed tag vocabulary (free tags rot into synonyms), fixed
in the outline; the frontmatter contract (`references/profiles/product-docs.md`
§ Per-article frontmatter).

## Sub-phase 9 — Voice profile (mandatory, all profiles)

The skill ships no GOOD prose; each project's imitable examples are made
here, from its own approved passages, in `bible/voice-profile.md`
(`templates/voice-profile.md`), read by every prose agent every turn.

1. **Fingerprint** — 3–5 traits observable in a paragraph and false for most
   competent documents of the register ("clear and engaging" fails).
2. **Banned traits** — 3–5 detectable prohibitions beyond the global floor.
3. **Opening structure** — product-docs and scientific-paper fix it (record
   the one line; `rhet-6` not applicable); **book-literary has no rotation**
   (skip); other profiles pick 3–4 structures from the menu, and the same one
   may not open two consecutive units.
4. **Closing policy** — the profile default, adjusted if the human wants.
5. **Budget overrides** — the `rhetoric_budget:` fence: `rhet` quotas from
   `references/rubric.md`; book-literary adds only `rhet-2` and the
   diagnostics of `anti-mediocrity-literary.md` § 2. Record overrides only.

Then generate 3–5 **GOOD examples** (80–150 words), each tagged with the trait
or move it demonstrates, derived from the approved passages — book-literary:
from the `human` passages first. Iterate to the same "yes, THIS". If the human
cannot tell a draft from a generic competent book, discard it. Never import
prose from the skill's references or from another project.
**Output**: `bible/voice-profile.md`, approved.

## Wrap-up — pipeline and models

Confirm the `pipeline` block — `mode`, `retry_cap`, digests;
`adversarial_verify` (`mode`, `n`, `cross_model`: refutations and the MG-4
read on a second model when a tool for one exists); `humanizer_budget`
(nonfiction; `null` = report only); `reader_testing` (corporate-guide,
product-docs) — and `models` (tiers `creative` / `audit`, default `inherit`; a
model id only on a tier, only for cost control). book-literary: confirm the
`literary` block (`key_scene_versions`, `tic_pass_every`; optional
`humanizer_budget`, `tics`).

## Completion checklist

All profiles: `meta.yaml` complete; `scope.md`; `glossary.md`;
`style-guide.md` approved; `voice-profile.md` approved;
`continuity-tracker.md` initialized; `project-status.yaml` initialized
(`schema_version: "3.4"`).

- Nonfiction: `validation_surface` (or `empty` with reason); `bible/sources/`
  signed or opt-out recorded; `examples-library.md` if the running example is
  on; `bible/digests/` for sequential profiles.
- book-literary: seeds and braindump; every sheet signed with `pipeline_step.py
  sign` (`status: complete`, `signed_on`, `signed_hash`); `_extras.md`;
  `world.md` with § Names; `plot-structure.md` with the ending; `arcs.md`;
  `timeline.md`; `story-ledger.yaml` (`entries: []` when empty — the file must
  exist); `reader-journal.md`.
- scientific-paper: `claims-map.yaml` seeded; `citation_style` set.
- corporate-guide: `organization` block. product-docs: taxonomy, tag
  vocabulary, frontmatter contract.

Handoff: `book-technical`, `scientific-paper` → Phase 1.5 (knowledge graph);
`product-docs`, `corporate-guide` → Phase 1.5 (terminology-only);
`book-literary` → Phase 2. Announce it in the human's language and ask before
proceeding.
