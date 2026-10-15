# Technical Project Setup

Technical books (manuals, tutorials, guides, reference material) need structural
clarity more than creative infrastructure. The setup is faster but still rigorous.

---

## Sub-Phase 0 — Project Subtype

Set during `init` but confirmed here. `project.subtype` in `bible/meta.yaml`
shapes how every downstream agent teaches, not just what gets covered.

Options:

- **tutorial** — sequential, hands-on, one running example grows across
  chapters. Reader follows along.
- **reference** — chapters are independent lookups. Reader jumps in.
- **cookbook** — problem → solution recipes. Each chapter is self-contained.
- **textbook** — concept-heavy, exercises, proof-style rigor. Reader works.
- **opinion** — technically grounded but argumentative. Voice is part of the
  product. Reader is persuaded, not just informed.

If `init` set this provisionally, confirm before continuing. The subtype
chosen here is written into the Writer's and Critic's prompts, so a mismatch
costs drafts.

---

## Sub-Phase 1 — Subject & Scope

### What to establish

- **Topic**: what is this book about?
- **Scope boundaries**: what's IN and what's OUT. Be explicit about what the
  book does NOT cover — a fuzzy scope produces a rambling manuscript.
- **Prerequisite knowledge**: what should the reader already know? List it
  concretely (e.g., "comfortable reading basic SQL", not "familiar with
  databases").
- **Learning outcomes**: after reading, the reader should be able to [specific
  skill/understanding]. Aim for verbs: "build", "diagnose", "decide", "operate".
- **Anti-scope**: common misconceptions about what this book is. E.g., "not a
  cookbook", "not an API reference", "not a history of the field". This saves
  arguments with beta readers later.

### Questions to ask

1. ¿De qué trata el libro en una oración?
2. ¿Qué debe saber hacer el lector al terminar?
3. ¿Qué ya sabe el lector al empezar?
4. ¿Qué NO va a cubrir este libro?
5. ¿Qué confundirían con este libro que no es?

### Output

Start writing `bible/meta.yaml` with the `scope` section. Also create
`bible/scope.md` with a longer prose explanation of scope and anti-scope for
the pipeline to reference during chapter drafting.

---

## Sub-Phase 2 — Audience

### What to establish

- **Primary reader**: beginner, intermediate, advanced, or mixed.
- **Context**: student, professional, self-learner, reference user.
- **Reading mode**: cover-to-cover (tutorial) or jump-around (reference)?
- **Motivation**: why is the reader picking this up? A real job task, curiosity,
  preparing for an exam, leveling up? The motivation shapes tone.
- **Frustrations**: what will this reader find boring, patronizing, or opaque?
  Name them so the Writer can avoid each.

### Output

Add to `bible/meta.yaml`:

```yaml
audience:
  level: "[beginner/intermediate/advanced/mixed]"
  context: "[Professional/student/self-learner/reference]"
  reading_mode: "[Sequential / reference / problem-solution]"
  motivation: "[Why they're reading this]"
  known_frustrations:
    - "[Will hate this specific kind of content]"
```

---

## Sub-Phase 3 — Tone & Register

### What to establish

- **Formality**: academic, professional, conversational, casual tutorial.
- **Person**: "you will learn..." (2nd person), "the reader..." (3rd), "we..."
  (1st plural). Pick one and hold it.
- **Humor**: allowed? What kind? How much? (Err on less — dated jokes are
  worse than no jokes.)
- **Anecdotes**: personal voice allowed? From the author? From hypothetical
  users?
- **Opinion register**: neutral reporting, or explicit opinions with rationale?

### Output

Add to `bible/meta.yaml`:

```yaml
voice:
  formality: "[academic/professional/conversational/casual]"
  person: "[1st plural / 2nd / 3rd]"
  humor: "[none/light/dry/absurd] — [amount]"
  anecdotes: "[author/user/none]"
  opinion: "[neutral/explicit-with-rationale]"
```

---

## Sub-Phase 4 — Structure Type

### What to establish

- **Sequential learning**: each chapter builds on the previous (tutorial).
- **Reference manual**: chapters are independent, any order.
- **Problem-solution**: organized around problems the reader faces.
- **Project-based**: building something incrementally across chapters.

Pick one explicitly. Mixed structures (e.g., "mostly sequential but chapters
10–15 are reference") are fine if you commit and the outline reflects it.

### Output

Add `structure_type` to `bible/meta.yaml`.

---

## Sub-Phase 5 — Conventions

### What to establish

- **Code style**: language(s), formatting, comment density, which style guide
  (PEP 8, Google Java, etc.).
- **Example policy**: every concept shown with a runnable example? Or
  conceptual-first, example-later? How minimal should examples be?
- **Callout types**: define the set. Typical: Note, Warning, Tip, Example,
  Trap, Aside. Keep the set small (4–6) so readers don't need a legend.
- **Terminology convention**: define on first use? Glossary at end? Both?
- **Cross-references**: "see Chapter 7" or "(§ 7.2)"? Hyperlink style?
- **Exercises**: end-of-chapter, inline, or none? With solutions or without?
- **Code execution**: is the code in the book runnable? How does the reader
  get the repo? What version of dependencies?

### Output

Add to `bible/meta.yaml`:

```yaml
conventions:
  code_language: "[e.g., Python 3.12]"
  style_guide: "[e.g., PEP 8]"
  callout_types: [note, warning, tip, example, trap]
  has_exercises: "[yes/no]"
  exercises_with_solutions: "[yes/no]"
  code_repo: "[URL if applicable]"
  pinned_versions:
    - "[library==version]"
```

Initialize `bible/glossary.md` now — don't wait for writing to start. As
terms get defined during writing, the Writer adds them; the Continuity
Guardian audits consistency.

---

## Sub-Phase 5.5 — Validation Surface

Not every technical book has executable code. Qlik Sense can't be run like
Python. A math textbook has proofs, not commands. A SQL cookbook has
dialect-specific syntax. The Validation Surface names, per domain, what the
Technical Reviewer can actually verify by machine — and what it can't.

See `references/validation-surface.md` for the catalogue and per-domain
sub-prompts (python_exec, qlik_set_analysis, qlik_load_script,
qlik_expression, sql_dialect_check, yaml/json_schema_validate, linter,
doc_cross_ref, proof_recheck, empty).

### What to establish

- Which surfaces apply to this book? A book can declare several (e.g., a
  full-stack tutorial may declare `python_exec`, `sql_dialect_check`, and
  `doc_cross_ref`).
- What runner verifies each surface? Some run locally (Python subprocess),
  others are reviewer-only (Qlik expressions are reasoned about against the
  source library, not executed).
- What is each surface pinned to? A Python surface pins the interpreter and
  top-level deps. A Qlik surface pins the target Qlik version (and must
  match `target_version` in meta).

### Output

Add to `bible/meta.yaml`:

```yaml
validation_surface:
  surfaces:
    - surface: "[e.g., qlik_expression]"
      applies_to: "[e.g., all fenced ```qlik blocks]"
      runner: "[reviewer-only / python-subprocess / external-cli]"
      pins:
        target_version: "[e.g., Qlik Sense May 2024]"
```

If the book genuinely has no machine-verifiable surface, declare `empty`
explicitly — it's a deliberate choice that the Technical Reviewer surfaces in
every chapter's Axis A note, not a silent skip:

```yaml
validation_surface:
  surfaces:
    - surface: empty
      reason: "Prose-only — no runnable code or checkable expressions."
```

The reviewer will still audit claims against `bible/sources/` (Axis B). The
surface declaration is about Axis A — what mechanical checks run.

---

## Sub-Phase 6 — Style Guide with Calibration

### What to establish

- Sentence length preferences (average, range).
- Active vs. passive policy (default active; passive only when the object is
  the real subject of the sentence).
- Jargon handling: define on first use, link to glossary, both.
- How to introduce new concepts: definition first? example first? motivation
  first?
- Diagram policy: when is a diagram required? What tool?
- Figure/table captioning convention.

### Calibration passages

Write 1–2 short passages (200–400 words) in the target voice. They don't
have to be from the actual book — they demonstrate how a paragraph should
feel. Draft, get feedback, refine until the human says "yes, THIS".

These passages are what every downstream agent uses to calibrate voice. They
are the most important artifact in the bible for a technical project.

### Output

Write `bible/style-guide.md` with all decisions + calibration passages.

---

## Sub-Phase 7 — Sources Library (grounding for Technical Reviewer)

The Technical Reviewer runs a two-axis audit on every chapter. Axis B
(mental models, framings, terminology) is checked against `bible/sources/`
— official docs, reference books, papers, internal reports. Without a
sources library, Axis B auto-PASSes with a visible "skipped — no grounding
library" note. That's not a silent skip, but it means the reviewer can't
catch plausible-sounding-but-wrong framings. For any serious technical
book, invest in sources up front.

This sub-phase sets up `bible/sources/` with three things:
preprocessed files, an index (`sources.md`), and version-drift flags.

### Step 1 — Detect what's already there

Before asking anything, scan `bible/sources/`:

```
bible/sources/
├── *.pdf          → raw PDFs (need extraction)
├── *.md           → preprocessed text (ready to use)
├── *-figures/     → extracted images (ready to use)
└── sources.md     → index (may or may not exist yet)
```

Announce what you found. Examples:

- "Found 3 raw PDFs and no `sources.md`. We'll need to extract text and
  draft the index."
- "Found 2 PDFs already extracted to `.md`, plus 1 new PDF that's raw.
  I'll process just the new one."
- "The `bible/sources/` folder is empty. Either we add sources now, or we
  proceed without a grounding library (Axis B will auto-PASS with a flag
  — that's OK for MVP drafts but worse for published work). ¿Qué preferís?"

If the human says they have sources but didn't put them in the folder,
ask them to drop them in before continuing. Don't proceed with an empty
folder silently.

### Step 2 — Extract raw PDFs to markdown

PDFs are load-bearing in two ways: the text carries the claims, and the
figures carry the visual information (diagrams, UI screenshots, layouts).
We want both, but in forms the Technical Reviewer can actually use at
scale:

- **Markdown (`.md`) is the primary form.** It's cheap to grep, cheap to
  read, and produces tight citations. The Technical Reviewer opens the
  `.md` first for any text-based check.
- **The original PDF stays in the folder.** It's the fallback when the
  reviewer needs to see a figure in context, verify OCR quality, or
  inspect a layout the markdown flattened.
- **Extracted figures live in `<source-stem>-figures/`.** Individual PNGs
  the reviewer can open directly when a diagram is load-bearing.

For each raw PDF found:

1. Invoke the `pdf` skill to extract text and figures. Pass the PDF
   path and ask for:
   - Text output as a single `.md` file next to the PDF (same stem,
     `.md` extension). Preserve chapter/section structure as markdown
     headings.
   - Figure extraction to `<source-stem>-figures/` as PNGs, named
     sequentially (`fig-001.png`, `fig-002.png`, …) with a one-line
     caption file per figure if possible.
2. After extraction, do a sanity pass: open the first 2–3 pages of the
   `.md` side by side with the PDF. OCR errors on headings or garbled
   tables are common and worth fixing before the reviewer has to.
3. If the PDF is huge (400+ pages) and splitting it per chapter would
   help future Greps, propose doing so. E.g.,
   `qlik-admin-guide-ch01.md`, `qlik-admin-guide-ch02.md`, … Split
   only if the human agrees — it's optional.

After extraction, the folder looks like:

```
bible/sources/
├── qlik-admin-guide.pdf
├── qlik-admin-guide.md
├── qlik-admin-guide-figures/
│   ├── fig-001.png
│   └── ...
├── qlik-scripting-ref.pdf
├── qlik-scripting-ref.md
├── qlik-scripting-ref-figures/
└── ...
```

If the `pdf` skill is unavailable or fails on a specific file (encrypted,
scanned-only, DRM), do NOT fall back to silently ignoring it. Report the
failure to the human and decide together: manual extraction, a different
copy of the source, or leave it and flag in `sources.md` that this source
is PDF-only.

### Step 3 — Propose a draft `sources.md`

The index is what makes the library usable — without it, the Technical
Reviewer has to open everything blind on every check. The SME (the human)
owns the final judgments, but you can propose a draft so the human is
correcting a 70% draft rather than filling a blank form.

For each source, read the table of contents (the first few pages of the
`.md`) plus the copyright/publication page, and propose:

```markdown
### [Short name — suggest one based on the title]

**Full title**: [from cover page]
**Author(s)**: [from cover page]
**Edition / year**: [from copyright page]
**Format**: Full-text PDF + extracted .md + figures/
**File in this folder**: [filename.pdf (+ filename.md, filename-figures/)]

**Authoritative for** (DRAFT — human sign-off):
- [topic 1 — based on TOC chapters]
- [topic 2 — based on TOC chapters]

**Not authoritative for** (DRAFT — human sign-off):
- [topics outside the book's stated scope, if obvious]

**Known to be wrong on / outdated on** (DRAFT — human sign-off):
- Version drift: [if the book covers version X and the target book will
  teach version Y, flag here]
- [other items the SME knows about, left blank for now]

**How to cite when flagging a finding**:
- "[Short-name], §[section label from TOC]"
```

Then stop. Present the draft entries to the human and say:

"Here's a proposed `sources.md`. Three things I couldn't decide alone
and need your call on:
1. `authoritative for` — I listed topics from the TOC, but you're the
   SME. Correct the list to reflect what you'd actually stake a chapter
   on.
2. `not authoritative for` — I mostly left this sparse. Add the topics
   this source pretends to cover but you wouldn't trust.
3. `known to be wrong on / outdated on` — especially version drift. If
   this book teaches Qlik Sense May 2024 and the source covers November
   2023, flag every section where the behavior has changed between
   versions. The Technical Reviewer will otherwise tell the Writer to
   'correct' things that are actually version differences."

Take their corrections and write the final `sources.md`. Don't proceed
without explicit sign-off — a wrong `authoritative for` list poisons
every Axis B check downstream.

### Step 4 — Version drift — explicit register

If `bible/meta.yaml` declares a target version (e.g.,
`target_version: "Qlik Sense May 2024"`) and any source covers a
different version, add it to the source entry's "Known to be wrong on /
outdated on" with a clear rule for the reviewer:

> **Version drift rule**: Source covers [version A], book teaches
> [version B]. In chapters covering [specific feature areas that
> changed], treat source as advisory only — flag divergences as
> "version drift, not error".

This keeps the reviewer from sending the Writer on a loop to "fix"
version-specific behavior changes.

### Step 5 — Output

- `bible/sources/sources.md` — the index, human-signed-off.
- `bible/sources/*.pdf` — originals preserved.
- `bible/sources/*.md` — extracted text.
- `bible/sources/*-figures/` — extracted images.

If the human opts out of a sources library entirely, note it on the
setup checklist and proceed. The Technical Reviewer's Axis B will
auto-PASS with the skip flag — the human chose this and the framework
surfaces the choice.

---

## Sub-Phase 8 — Knowledge Graph (pedagogical dependency map)

Before outlining chapters, build the concept dependency graph. This is the
single most important Phase 1.5 artifact for a technical book: every downstream
agent uses it to answer "can the reader understand this yet?"

See `references/knowledge-graph.md` for the full protocol and
`templates/knowledge-graph.yaml` for the schema. In short, the output is
`bible/knowledge-graph.yaml` listing every concept with:

- `id` — stable identifier used across the book.
- `one_liner` — the teaching-ready definition.
- `requires` — concepts that must be introduced first.
- `builds_on` — softer dependencies that improve comprehension but aren't
  strict prerequisites.
- `contrasts_with` — concepts it's commonly confused with (Critic uses this
  to check if the chapter preempts the confusion).
- `introduced_in` — target chapter (filled during outlining).

This map is what prevents the "chapter 4 uses a term introduced in
chapter 7" bug that Critic otherwise catches too late.

### Output

- `bible/knowledge-graph.yaml` — initial graph with `introduced_in` left
  blank on concepts until outlining wires them up.
- `bible/glossary.md` — may be seeded from KG `one_liner` fields (one-way
  sync at setup; the glossary grows during writing).

---

## Setup Completion Checklist

- [ ] `bible/meta.yaml` — complete, reviewed (includes `project.subtype`,
      `validation_surface.surfaces`, `target_version` if applicable)
- [ ] `bible/scope.md` — scope + anti-scope, reviewed
- [ ] `bible/glossary.md` — initialized (will grow during writing)
- [ ] `bible/style-guide.md` — with calibration passages, reviewed
- [ ] `bible/sources/` — PDFs extracted to .md + figures, OR explicit
      opt-out noted
- [ ] `bible/sources/sources.md` — index with authoritative-for and
      version-drift entries signed off by the human (if sources exist)
- [ ] `bible/knowledge-graph.yaml` — initial concept list with `requires`
      / `builds_on` / `contrasts_with` edges; `introduced_in` left blank
      until outlining
- [ ] `bible/continuity-tracker.md` — initialized (tracks terminology + forward
      references, not characters)
- [ ] `bible/digests/` — empty folder created (digests are written
      post-approval per chapter)

Technical projects do NOT need character sheets, world.md, plot-structure.md,
arcs.md, or timeline.md.

Initialize `project-status.yaml`. Set `phase: knowledge-graph` if the graph
still needs work, or `phase: outlining` if the graph is complete.
`current_chapter: 0`.

Announce: "La bible técnica está lista, con knowledge graph y validation
surface declarados. Siguiente paso: outline capítulo a capítulo, mapeando
cada concepto del grafo a su capítulo de introducción. ¿Arrancamos?"
