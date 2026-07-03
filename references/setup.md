# Setup — Phase 1 (All Profiles)

Setup is a collaborative design session, not a form. Every sub-phase produces
a bible artifact that the human signs off before the next begins. Do not rush
it: a weak bible produces a weak document, and every hour spent here saves
loopback cycles in the pipeline.

Before starting, load `references/profiles/<profile>.md`. The profile
pre-answers many questions below — state the default and ask only when the
human might want to deviate. Propose, don't interrogate. Talk to the human in
their language; write bible artifacts in the document's language. "Unit"
means the profile's unit (chapter / article / section).

Sub-phases 1–7 are common (5 and 7 nonfiction-only), sub-phase 8 is
profile-specific, sub-phase 9 (voice profile) is mandatory for every profile
and runs last because it derives from the approved calibration passages.

---

## Sub-Phase 1 — Scope

Establish:

- **Topic / premise**: what is this document about, in one sentence?
- **Scope boundaries**: what is IN and what is OUT. Be explicit about what it
  does NOT cover — fuzzy scope produces a rambling manuscript.
- **Prerequisite knowledge**: concrete ("comfortable reading basic SQL"), not
  vague ("familiar with databases").
- **Outcomes**: what the reader can DO afterwards. Use verbs: build, diagnose,
  decide, operate. For corporate-guide: what behavior changes on the job.
- **Anti-scope**: what people will mistake this document for ("not an API
  reference", "not a policy manual"). This saves arguments with readers later.

**book-literary branch** — scope means: genre and subgenre, tone descriptors,
2–5 influence works with a *specific take* each (not "McCarthy" but "McCarthy's
sparse dialogue and refusal of quotation marks"), explicit negative constraints
("not YA despite a young protagonist"), and the desired reader experience at
the end. Negative constraints prevent genre drift; record them in meta under
`avoid:`.

**Output**: start `bible/meta.yaml` (from `templates/meta.yaml`, `project` +
`scope` blocks) and write `bible/scope.md` with the prose version of scope and
anti-scope. The pipeline reads scope.md when a Writer is tempted to go wide.

## Sub-Phase 2 — Audience

Establish: primary reader persona (one sentence — who, what they know, what
they are trying to do); experience level; reading context (professional /
student / employee with 10 minutes / user landing from search); reading mode
(the profile's sequence usually decides this); motivation (a real job task?
curiosity? an incident at 3am?); and **known frustrations** — what this
reader finds boring, patronizing, or opaque. Name them so the Writer can
avoid each one and Reader-POV can simulate them.

**Output**: `audience` block in `bible/meta.yaml`. For corporate-guide,
audience is intertwined with the organization block (sub-phase 8).

## Sub-Phase 3 — Tone & Register

The profile arrives with register defaults and hard prohibitions already set
(e.g., corporate-guide prohibits mic-drops, document self-reference,
cliffhangers, and transformation promises out of the box). Do NOT re-litigate
these — present them as the starting point and record only deviations the
human explicitly requests. The point of profiles is that sober-by-default
registers stay sober without the human having to legislate it.

What remains to decide per project:

- **Person**: "you" / "we" / impersonal — pick one and hold it.
- **Formality** within the profile's band.
- **Humor**: allowed? what kind? where (e.g., only in callouts)? Err on less.
- **Anecdotes / opinion**: personal voice allowed? Neutral reporting or
  explicit opinions with rationale?
- **Literary**: POV, tense, prose register (sparse / lush / journalistic),
  profanity and explicit-content boundaries.

**Output**: `tone` block in `bible/meta.yaml`. Fine-grained voice identity
comes later, in the voice profile (sub-phase 9) — here you fix the register
envelope only.

## Sub-Phase 4 — Conventions

Establish (skip items the profile already fixes):

- **Code style** (profiles with code): language(s), style guide, shell,
  pinned versions, code repo if any.
- **Callout set**: small (4–6 types); default to the profile's set (e.g.,
  corporate-guide: Note / Template / Checklist).
- **Example policy**: running example per the profile (if on, initialize
  `bible/examples-library.md`); minimal vs realistic examples.
- **Exercises / practice**: per the profile; corporate-guide's optional
  "practice" uses internal cases, not textbook drills.
- **Terminology**: define on first use, glossary, or both. Initialize
  `bible/glossary.md` now — don't wait for writing to start.
- **Cross-references**: per the profile's sequence (modular profiles link
  prerequisites; some profiles ban numbered cross-refs in prose).
- **Formatting**: heading case, Oxford comma, dash style, number rule, date
  format, language variant.

**Output**: `conventions` block in `bible/meta.yaml`; glossary initialized.

## Sub-Phase 5 — Validation Surface (nonfiction profiles)

Not every project has executable code. A BI tool can't be run like Python; a
math text has proofs, not commands. The validation surface names, per domain,
what the Technical Reviewer can verify by machine — and what it can't. See
`references/validation-surface.md` for the catalogue (python_exec,
sql_dialect_check, linter, doc_cross_ref, proof_recheck, citation_check,
stats_check, empty, ...).

Establish: which surfaces apply (several are fine); what runner verifies each
(local subprocess, external CLI, reviewer-only reasoning against sources);
and what each is pinned to (interpreter + deps, target product version,
citation style). If the project genuinely has no machine-verifiable surface,
declare `empty` with a reason — a deliberate choice the Reviewer surfaces in
every unit's Axis A note, never a silent skip. scientific-paper projects
should almost always declare `citation_check`, plus `stats_check` when there
are quantitative results.

**Output**: `validation_surface` block in `bible/meta.yaml`, including
`target_version` if the subject is version-pinned.

## Sub-Phase 6 — Style Guide with Calibration Passages

Establish the mechanics: sentence-length preferences, active/passive policy,
jargon handling, how new concepts get introduced (definition / example /
motivation first), diagram and caption policy, dialogue conventions
(literary). Fill `templates/style-guide.md`.

Then the **calibration passages** — 2–3 short passages (100–300 words) in the
target voice. They don't need to be from the actual document; they demonstrate
how a paragraph should *feel*. Use real text from a work the human is modeling
on, from the human's own best writing, or draft them yourself. Draft, get
feedback, refine until the human says "yes, THIS". Do not settle for polite
approval — a passage the human merely tolerates calibrates every downstream
agent to a voice nobody wanted.

These passages are the seed for the voice profile's GOOD examples (sub-phase
9), so their quality is load-bearing twice.

**Output**: `bible/style-guide.md`, human-approved.

## Sub-Phase 7 — Sources Library (nonfiction profiles)

The Technical Reviewer audits every unit against `bible/sources/`. Without a
library, Axis B auto-PASSes with a visible "skipped — no grounding library"
note: not silent, but the Reviewer can't catch plausible-sounding-but-wrong
framings. For any serious nonfiction project, invest here. Literary projects
may keep a research folder in the same layout; it is optional and un-audited.

### Step 1 — Detect what's already there

Scan `bible/sources/` before asking anything: raw `*.pdf` (need extraction),
`*.md` (ready), `*-figures/` (ready), `sources.md` (may not exist yet).
Announce what you found and what work remains. If the folder is empty, offer
the choice explicitly: add sources now, or proceed without grounding (Axis B
flagged — acceptable for early drafts, worse for published work). If the
human has sources elsewhere, ask them to drop the files in first — never
proceed silently with an empty folder.

### Step 2 — Extract raw PDFs to markdown

Markdown is the primary form (cheap to grep, tight citations); the original
PDF stays as visual fallback; extracted figures live in `<stem>-figures/` as
PNGs. For each raw PDF: (1) invoke the `pdf` skill — text to a single `.md`
next to the PDF (same stem), preserving section structure as headings;
figures to `<stem>-figures/fig-NNN.png` with captions if possible. (2) Sanity
pass: compare the first 2–3 pages of the `.md` against the PDF — OCR errors
on headings and garbled tables are common; fix them now, not when the
Reviewer trips over them. (3) For huge PDFs (400+ pages), propose splitting
the `.md` per chapter for cheaper greps — optional, human's call.

If the `pdf` skill is unavailable or fails on a file (encrypted, scanned-only,
DRM), do NOT silently ignore it. Report and decide together: manual
extraction, a different copy, or keep it flagged PDF-only in `sources.md`.

### Step 3 — Propose a draft `sources.md`

The index is what makes the library usable — without it the Reviewer opens
everything blind on every check. Propose a 70%-draft the human corrects
rather than a blank form: for each source, read the TOC and copyright page
and draft an entry per `templates/sources.md`. Then stop and ask for the
three judgments only the SME can make: **authoritative for** (correct the
TOC-derived list to what they would stake a unit's correctness on), **not
authoritative for** (topics the source pretends to cover but the human
wouldn't trust), and **known to be wrong on / outdated on** (especially
version drift). Do not proceed without explicit sign-off: a wrong
authoritative-for list poisons every Axis B check downstream.

### Step 4 — Version drift, explicit register

If `meta.yaml` declares a `target_version` and a source covers a different
one, add a version-drift rule to that source's entry naming the feature areas
that changed: "treat source as advisory only there; flag divergences as
version drift, not error". Otherwise the Reviewer will send the Writer to
"fix" behavior that is simply version-accurate.

### Step 5 — Outputs

`bible/sources/sources.md` (human-signed), originals preserved, extracted
`.md` + `-figures/`. Opt-out is allowed but recorded on the checklist.
**scientific-paper**: when Zotero / arxiv / citecheck / openreview MCP tools
are connected, use them to pull references, metadata, and retraction status
into the library — but every reference still gets a `sources.md` entry and
human sign-off. The claims map (sub-phase 8) points at these entries.

## Sub-Phase 8 — Profile-Specific Artifacts

### book-literary — characters, world, plot, arcs, timeline

Human approves each artifact before the next. Leave `TBD` where the human
isn't ready — characters often reveal themselves during outlining; don't force
premature commitment.

- **Characters** (`bible/characters/<name>.md`, from
  `templates/character-sheet.md`): core identity; conscious desire vs
  unconscious need (usually in tension); core wound and how it shows now;
  **contradiction** — every interesting character contains at least one;
  voice; arc endpoints and what forces the change; relationships as dynamics,
  not labels ("respects him but resents needing him", never "friends").
- **World** (`bible/world.md`): depth calibrated to genre — contemporary
  drama needs less than fantasy epic. Setting, social rules, economy, history
  that touches the plot. If speculative, be specific about **constraints** —
  a magic system without limits is dramatically useless.
- **Plot structure** (`bible/plot-structure.md`): one framework, committed;
  the dramatic question the ending answers; major beats (inciting incident,
  turning points, midpoint, crisis, climax, resolution); subplots; tension
  architecture — map peaks and valleys, not a straight ramp.
- **Arcs** (`bible/arcs.md`): arcs ≠ plot — plot is what happens, arcs are
  how things change. Character arcs tied to specific beats; thematic arcs
  (theme is a question explored, not a message); relational arcs; arc
  intersections — usually the strongest scenes.
- **Timeline** (`bible/timeline.md`): chronological sequence of all events
  including backstory. Initialize `bible/continuity-tracker.md`.

### scientific-paper — claims map + citation style

- Set `citation_style` in `meta.yaml` (apa | ieee | vancouver | author-year).
  This drives the visible-academic citation policy for the Writer and the
  Reviewer's Axis C (reference integrity).
- Seed `bible/claims-map.yaml` (from `templates/claims-map.yaml`) with the
  paper's core claims — the 5–15 assertions the paper stands on. Each claim
  maps to its evidence: an external citation (whose source lives in
  `bible/sources/`) or an own result (with a pointer to data/analysis). Claims
  without evidence yet are marked `pending` — the map is a working artifact
  the pipeline updates per section, not a one-shot form.
- Confirm the mandatory Limitations section and the Methods reproducibility
  checklist with the human now, so the outline reserves room for both.

### corporate-guide — organization block

Add to `bible/meta.yaml`:

```yaml
organization:
  name: "..."
  audience_role: "..."     # who inside the org reads this, in what role
  internal_context: "..."  # systems, policies, house terminology for examples
  confidentiality: "..."   # public | internal | confidential — bounds examples
```

This block is why the guide sounds written *inside* the organization:
examples come from `internal_context`; `confidentiality` tells the Writer
what real detail may appear.

### product-docs — article taxonomy + tags

- **Taxonomy**: agree the article types this KB uses (typical: task / concept
  / reference / troubleshooting) and each type's skeleton. The outline will
  type every article.
- **Tag vocabulary**: a closed, human-approved tag list. Free-form tags rot
  into synonyms ("auth", "authentication", "login") that break the
  related-articles surface.
- **Frontmatter contract**: every article carries `title`, `description`
  (search-result quality, one sentence), `tags` (from the vocabulary),
  `related`. Record in `meta.yaml → conventions`.

## Sub-Phase 9 — Voice Profile (mandatory, all profiles)

Why this artifact exists, and why it is per-project: language models imitate
examples far more faithfully than they follow abstract rules. If the skill
shipped "here's how good prose sounds" passages, every project would converge
on that one voice — the references therefore carry rules and BAD examples
only, and the GOOD examples are generated HERE, from this project's approved
calibration passages, and live in `bible/voice-profile.md`. This file is what
keeps this project from sounding like every other project. Fill
`templates/voice-profile.md`; every prose agent reads it every turn.

Guide the human through five decisions, then generate the examples:

1. **Fingerprint — 3–5 distinctive traits.** Traits this document does that
   others in the register don't. The test for a good trait: observable in a
   paragraph, and FALSE for most competent documents of the same register
   ("clear and engaging" fails the test; "analogies only from aviation" or
   "opens sections with an uncomfortable number" pass). Elicit by asking what
   the human's favorite writers do that nobody else does, and what a reader
   should recognize this document by.
2. **Banned traits — 3–5 prohibitions** beyond the global anti-mediocrity
   rules. Ask what the human hates in this genre/register. Enforced by the
   Humanizer and Critic like any style rule.
3. **Opening rotation.** First check the profile. **product-docs and
   scientific-paper fix the opening** (task-first / IMRaD convention) and mark
   `rhet-6` = `not_applicable` — for these, SKIP the menu and the
   consecutive-repeat rule; record the single fixed-opening line in
   `voice-profile.md` per `templates/voice-profile.md` and move on. For every
   other profile, offer the menu: scene-problem / direct question /
   counterintuitive fact / field case / in-media-res / data point (plus
   task-first where it fits). The human picks 3–4. HARD RULE for rotating
   profiles: the same structure may not open two consecutive units. The Writer
   declares the structure used in its self-assessment; the Critic verifies it
   against the previous unit (rhet-6). Rotation exists because a single opening
   formula, repeated 18 times, is the loudest sameness signal a reader gets.
4. **Closing policy.** Inherited from the profile (recap | related-links |
   none | bridge-allowed); the human may adjust. rhet-4 (no artificial
   cliffhangers) is enforced against the recorded policy.
5. **Rhetoric budget overrides.** Show the defaults from
   `references/rubric.md` (family `rhet`) and ask whether to tighten or
   loosen any. Record ONLY the overrides; unlisted items keep defaults.

Then **generate the project GOOD examples** — the heart of the artifact:
3–5 short passages (roughly 80–150 words each) in the project's voice,
derived from the approved calibration passages, plus 1–2 per key technique —
a "technique" is a fingerprint trait or recurring move agents must reproduce
(an opening in one of the rotation structures, a callout in the project's
humor, a definition paragraph, a scene beat in the book's POV). Draft them
yourself, present, and iterate until the human says yes — the same "yes,
THIS" bar as the calibration passages. If the human can't tell your draft
from a generic competent book, discard and retry: a generic example teaches
agents to be generic. Tag each approved example with what it demonstrates.
Never import prose from the skill's reference files, and never reuse a
passage from another project — either move recreates the shared-voice problem
this artifact exists to prevent.

**Output**: `bible/voice-profile.md`, human-approved.

## Wrap-Up — Pipeline & Models

Confirm the `pipeline` block (mode fast/full, `adversarial_verify`,
`retry_cap`, digests per profile) and the `models` block — tiers
(`creative` / `audit`), default `inherit` (the session's model). Set an
explicit model ID on a tier only if the human wants cost control; never
suggest specific IDs otherwise.

## Completion Checklist

All profiles:

- [ ] `bible/meta.yaml` — complete: profile, scope, audience, tone,
      conventions, pipeline, models (tiers)
- [ ] `bible/scope.md` — scope + anti-scope, reviewed
- [ ] `bible/glossary.md` — initialized
- [ ] `bible/style-guide.md` — decisions + calibration passages, approved
- [ ] `bible/voice-profile.md` — fingerprint, banned traits, opening
      rotation, closing policy, budget overrides, GOOD examples — approved
- [ ] `bible/continuity-tracker.md` — initialized
- [ ] `project-status.yaml` — initialized (`schema_version: "3.0"`)

Nonfiction profiles add:

- [ ] `validation_surface` declared (or `empty` with reason)
- [ ] `bible/sources/` — extracted + `sources.md` signed off, OR explicit
      opt-out recorded
- [ ] `bible/examples-library.md` — if the profile's running example is on
- [ ] `bible/digests/` — created (sequential profiles only)

Per profile add:

- [ ] book-literary: `characters/`, `world.md`, `plot-structure.md`,
      `arcs.md`, `timeline.md` — each reviewed
- [ ] scientific-paper: `claims-map.yaml` seeded; `citation_style` set
- [ ] corporate-guide: `organization` block in meta
- [ ] product-docs: taxonomy + tag vocabulary + frontmatter contract in meta

Handoff: `book-technical` and `scientific-paper` → Phase 1.5 (knowledge
graph, mandatory); `product-docs` and `corporate-guide` → Phase 1.5
(terminology-only); `book-literary` → Phase 2 (outlining — plot-structure and
arcs play the KG's role). Announce the transition to the human in their
language and ask before proceeding.
