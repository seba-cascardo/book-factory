---
name: book-factory
description: >
  End-to-end book and novel creation with a multi-agent writing pipeline. Use
  whenever the user wants to write a book, novel, short story, technical manual,
  reference, tutorial series, or memoir. Triggers: "write a book", "create a
  novel", "book project", "start a story", "technical manual", "tutorial book",
  "book-factory", "empezar un libro", "escribir una novela", "proyecto de
  escritura", "manual técnico", "libro técnico", or any reference to an existing
  project directory with bible/meta.yaml. Also triggers on chapters, manuscripts,
  story bibles, character sheets, plot outlines, or chapter outlines for original
  content. Use even if the user does not say "book" — if they describe writing
  something multi-chapter and structured, this is the right skill. Do NOT trigger
  for summaries, reviews, or analysis of existing books by other authors.
---

# Book Factory v2.4 — Multi-Agent Writing Framework

A structured framework for creating books through a human-directed, AI-assisted
pipeline. The human is the creative director. Agents are tools that draft, edit,
polish, verify, simulate readers, and critique — but agents never make strategic
decisions about content direction.

## What changed from v1

If you have worked with the v1 framework, the main differences are:

- **Sharper role boundaries**: Editor no longer touches line-level prose. Humanizer
  no longer restructures or applies critique fixes as its primary job. Each agent
  owns a clean, non-overlapping slice.
- **Critic is now a gate**: it runs at the END of the pipeline, audits the text the
  human will actually read, and routes failures back to the correct agent by
  severity — not just produces a diagnostic the Humanizer has to absorb.
- **Full bifurcation by project type**: Technical and literary projects load
  different Writer, Humanizer, Critic, and anti-mediocrity references. Don't mix.
- **Technical pipeline modes (fast vs full)**: technical projects default to
  a correctness-first `fast` mode and can opt into `full` for prose polish.
  v2.4.1 brought Humanizer + a pre-gate Continuity Guardian coherence check
  into fast mode; only Reader-POV is now deferred to full mode per chapter,
  with a batch polish pass at the end of the manuscript covering
  Reader-POV's first read plus a cross-chapter Humanizer pass.
- **Per-role model assignment**: Opus where creativity or gating judgment is
  load-bearing (Writer, Humanizer for literary, Critic); Sonnet for structured
  audit/polish agents. Configured in `bible/meta.yaml` under `models:`.
- **Technical Reviewer replaces Fact-Checker + SME Reviewer**: one agent, two
  labeled axes in a single report (claims/code/versions and mental models /
  framings / terminology / grounded sources).
- **Defined loopback rules**: when the Critic fails a chapter, the skill knows
  exactly which agent to re-enter from, based on the severity and type of the
  problems listed.

## What's new in v2.2

v2.2 tightens the grounding-library story for technical projects. The big
change is that `bible/sources/` is now a first-class setup sub-phase, not a
folder the human is expected to populate on their own before chapter writing
begins.

- **Raw PDFs are auto-detected and preprocessed during setup**. When the
  setup phase finds `.pdf` files in `bible/sources/` without matching `.md`
  siblings, it delegates extraction to the `pdf` skill — producing a
  `.md` (primary read for the Technical Reviewer) and a `-figures/` folder
  of extracted PNGs (fallback when a diagram or screenshot is
  load-bearing). The original PDF stays in place as a visual fallback.
- **`sources.md` gets a guided draft pass**. Setup reads each source's
  table of contents and cover page, proposes an entry with
  `authoritative for` / `not authoritative for` / `known to be wrong on`
  based on the TOC, and then stops for human sign-off. The SME is always
  the final judge on what a source can be trusted on — but the assistant
  now does the legwork of a 70% draft rather than handing back a blank
  form.
- **Version drift is a first-class concept**. If a source covers a
  different version than the book teaches (vendor docs are the common
  case — "source is November 2023, book teaches May 2024"), `sources.md`
  now carries a `version drift rule` per source, and the Technical
  Reviewer recognizes divergences in those feature areas as "version
  drift, not error" — preventing the Writer from being sent on a fake
  REVISE loop to "correct" behavior that's actually version-accurate.
- **Technical Reviewer's read order**: `.md` first (cheap, grep-friendly),
  `.pdf` or `-figures/*.png` as fallback when visuals matter. This keeps
  Axis B checks fast at chapter scale.

The setup flow stays the same at the top level — type selection, scope,
audience, tone, structure, conventions, style guide — but Sub-Phase 7
(Sources Library) is now explicit and guided. See
`references/setup-technical.md` for the full procedure.

## What's new in v2.3

v2.3 is about making the pipeline trustworthy at scale — avoiding the
failure modes that only show up once you've written five chapters and can't
tell why chapter 4 feels off. The additions are orthogonal; turn any of them
off in `bible/meta.yaml` if you don't want them.

- **Init command**. When the user invokes the skill with no `bible/meta.yaml`,
  the skill scaffolds the project directory itself. No more asking the human
  to create folders by hand. See `references/init-scaffold.md`. Also covers
  non-destructive migration from v2.2 projects.
- **Phase 1.5 — Knowledge Graph**. Before outlining, build a concept
  dependency map (`bible/knowledge-graph.yaml`). Every concept carries
  `requires` / `builds_on` / `contrasts_with` / `introduced_in`. The Writer
  uses it to know what the reader already knows; the Critic uses it to block
  chapters that reference undefined concepts. See
  `references/knowledge-graph.md`.
- **Validation Surface per domain**. Not every technical book is
  Python-runnable. Qlik expressions can't be executed like scripts; a math
  textbook has proofs, not commands. `bible/meta.yaml` declares which
  surfaces apply (python_exec, qlik_set_analysis, qlik_load_script,
  qlik_expression, sql_dialect_check, doc_cross_ref, proof_recheck, empty,
  and more). The Technical Reviewer reads the declaration and runs only the
  applicable checks. See `references/validation-surface.md`.
- **Rubric-driven Critic with scorecard**. The Critic no longer just picks a
  verdict — it fills a scorecard (`critique-scorecard.yaml`) against a
  published rubric (`references/rubric.md`), and the verdict is *computed*
  from the scorecard (any `critical` failure → REWORK; any `major` →
  REVISE; only `minor`/none → PASS). Deterministic, auditable, harder to
  wave through a weak chapter.
- **Chapter digests**. After approval, each chapter gets a 300–500-word
  digest (`bible/digests/ch-NN.digest.md`): concepts introduced, running
  examples state, open forward references, voice calibration sample. From
  chapter 6+, downstream agents read all prior digests + only the immediately
  preceding chapter in full — preventing context bloat without losing
  cross-chapter continuity. See `references/chapter-digest.md`.
- **Structured loopback handoff on cap hit**. When a chapter hits the retry
  cap, the skill no longer just "escalates to human." It produces a
  structured packet (`references/loopback-handoff.md` + template): the diff
  per cycle, a diagnosed failure pattern (thrashing / diverging /
  insufficient_grounding / outline_level_flaw / prose_vs_content_mismatch),
  three concrete options, and a recommendation. The human decides, but with
  a real brief rather than "it failed, please look".
- **Drafts archive policy**. On approval, `drafts/ch-NN/` moves to
  `drafts/_archive/ch-NN/`. Keeps `drafts/` a working set. Re-opening a
  chapter restores from the archive. See `references/archiving.md`.
- **Cost observability (not cap)**. `project-status.yaml` appends a
  `cost_observability.by_call` row per agent run (model, tokens, duration).
  Aggregates per-chapter and per-agent totals. Visibility is the point — not
  a budget guardrail. The human decides when cost matters; the framework
  just makes the data legible.
- **Explicit `project-status.yaml` schema**. Versioned (`schema_version: "2.3"`),
  with per-chapter `archived_on` / `scorecard_last_pass_fail` /
  `digest_written`, `retries.cap_hits`, and the cost fields above.

All v2.3 additions are opt-in-by-existence: a v2.2 project still works, and
the init migration path adds the v2.3 artifacts non-destructively.

## What's new in v2.4

v2.4 is a targeted fix to one loopback inefficiency observed at scale in
technical projects: the Writer → Technical Reviewer → (REVISE) → Writer cycle
burning on Axis B hits (framing, terminology, silent divergence from sources)
that a grounding pass at draft time would have caught. The root cause: the
Writer drafted on intuition and scattered `TECH-REVIEW` flags, deferring the
grounding work to the Reviewer; by the time a framing hit came back, the
Writer had already committed to a mental model and had to partially rewrite.

- **SME Writer replaces Writer in technical mode.** The agent is still one
  agent and still runs at the same slot in the pipeline, but its contract
  changes: before drafting, it runs a mandatory pre-draft grounding pass
  against `bible/sources/`, producing `drafts/ch-NN/grounding-notes.md` as
  an explicit artifact. The draft itself carries inline `<!-- SOURCE: ... -->`
  comments on load-bearing claims. See `references/agent-writer-technical.md`.
- **Technical Reviewer audits an already-grounded draft.** Axis B shifts from
  first-line grounding to citation verification plus edge-case audit. A
  hallucinated or misquoted `<!-- SOURCE: ... -->` is its own flavor of hit,
  routed as REVISE → Writer. See `references/agent-technical-reviewer.md`.
- **Graceful degradation when sources are empty.** If `bible/sources/` has no
  relevant content for the chapter, the grounding pass is skipped with a
  documented note at the top of the self-assessment. The Reviewer treats
  Axis B as prose-audit only — same as v2.3 behavior.
- **No change to Literary mode.** Literary projects have no grounding
  library; the Writer stays the Writer.
- **Migration from v2.3 → v2.4 is zero-config.** No new fields in
  `meta.yaml`. The Writer and Reviewer reference files carry the new
  behavior; existing projects get it on the next chapter run.

The cost: the Writer now spends time reading source `.md` extractions before
drafting. The win: fewer REVISE loops, and the ones that do happen are
higher-value (novel edge cases, not "you didn't read the source we already
had in the library").

## What's new in v2.4.1

v2.4.1 is a targeted fix to two regressions observed at scale on v2.4
technical projects.

- **SME Writer voice recalibration.** v2.4's emphatic grounding instructions
  pushed the Writer into citational prose — paragraphs opening with "as the
  official documentation states", inline SOURCE references threaded through
  the running text, definitions quoted and then "unpacked". That's not the
  SME workshop voice the role was meant to embody; it's a technical-translator
  voice. The Writer reference now leads with an explicit voice-and-personality
  section, forbids citational prose patterns by name, and clarifies that
  grounding is invisible in running text — citations live only in HTML
  `<!-- SOURCE: ... -->` comments for the Technical Reviewer, and then only
  for load-bearing specifics (one per claim, not one per paragraph). See
  `references/agent-writer-technical.md` § "Voice and personality".
- **Fast mode now includes Humanizer + pre-gate coherence.** Deferring all
  prose-level work to the end-of-manuscript polish was leaking voice drift
  and format inconsistency into approved chapters. Fast mode now runs the
  Humanizer every chapter (same contract as in full mode) and runs the
  Continuity Guardian in a new Mode A — a pre-gate coherence pass against
  the last 1–2 approved chapters plus all digests — before the Critic. The
  Continuity Guardian's original post-approval tracker update (Mode B) is
  unchanged. Reader-POV remains the only agent deferred to full mode per
  chapter. See `references/pipeline.md` § "fast" and
  `references/agent-continuity-guardian.md` § "Two modes of invocation".

Migration from v2.4 → v2.4.1 is zero-config. No new fields in `meta.yaml`.
Existing projects pick up the new behavior on the next chapter run.

## What's new in v2.4.2

- **Citational-prose watchlist patch**: added parenthetical and mid-sentence citational-attribution check to Humanizer Layer 2 and Continuity Guardian Mode A — fourth consecutive Critic-gate citational-frame leak across ch-11..14 warranted a formal watchlist entry rather than continued case-by-case catches.

## What's new in v2.4.3

- **Coverage audit at Phase 4 (technical only)**: the Continuity Guardian's
  full-manuscript audit now includes a check for **orphan terms** — load-
  bearing terms invoked in prose but absent from
  `bible/knowledge-graph.yaml`, `bible/glossary.md`, and the outline's
  declared `concepts_introduced` / `concepts_used`. This closes the gap
  where the Critic's `outline-2` rubric item ("All `concepts_used` appear
  in earlier chapters, current chapter's `concepts_introduced`, or
  prerequisites") could only anchor against the *declared* vocabulary, not
  against the prose actually written — so a term the Writer dropped in
  without ever adding to KG/glossary slipped through every per-chapter
  gate. The audit reads the manuscript, builds candidate terms from
  backticks / bold / italic / acronyms / recurring noun phrases, filters
  through an allow-list, cross-references the project's known vocabulary,
  and writes `bible/orphan-terms-audit.md` for human triage. Advisory, not
  blocking. Toggle: `pipeline.coverage_audit.enabled` in `meta.yaml`. See
  `references/agent-continuity-guardian.md` § "Orphan terms (KG/glossary
  coverage)" and `templates/orphan-terms-audit.md`.

  Why a Phase 4 pass instead of a per-chapter check: orphan detection
  benefits from cross-chapter signal. A term recurring across ch-7, ch-9,
  and ch-12 is almost certainly load-bearing; the same term once in ch-7
  is more likely a one-off. Per-chapter coverage would also burn cycles
  flagging terms that legitimately get introduced later in the book.

Migration from v2.4.2 → v2.4.3 is zero-config — existing projects pick up
the new audit on the next Phase 4 run. To opt out, set
`pipeline.coverage_audit.enabled: false` in `bible/meta.yaml`.

---

## Core Principle

The human approves every phase transition. Nothing advances without explicit sign-off.
Agents are tools, not authors. The Critic can block a chapter, but only the human
can approve one.

---

## Phase Detection — Start Here

When the skill is invoked, detect the project state before doing anything else:

1. **If the user pointed to a folder**:
   - `bible/meta.yaml` exists with `schema_version: "2.3"` → load
     `project-status.yaml`, resume where it left off.
   - `bible/meta.yaml` exists without `schema_version: "2.3"` → offer a
     non-destructive v2.2 → v2.3 migration (see
     `references/init-scaffold.md` § "Migration from v2.2 projects").
   - `bible/meta.yaml` missing → this is a new project. Go to Phase 0 (Init).
2. **If no folder specified**: ask the user which folder to use (or create
   one). Then go to Phase 0 (Init) if it has no `bible/meta.yaml`.
3. **Resume path**: read `project-status.yaml`, announce the project name, current
   phase, current chapter, last completed pipeline step. Ask what to work on next.

---

## Phase 0: Init (Scaffolding)

For new projects. The skill creates the directory structure itself — the
human never has to `mkdir bible/digests` or stare at an empty folder
wondering what template goes where.

Ask only the two questions that change WHICH folders get created:

1. **Type**: literary or technical?
2. **Subtype** (technical only): tutorial / reference / cookbook / textbook /
   opinion. Default `tutorial` if unclear; refine during setup.

Then scaffold per `references/init-scaffold.md`. The scaffold writes:
- `bible/meta.yaml` pre-filled with `project.type` and `project.subtype`
- All empty shell files (scope, style-guide, glossary, knowledge-graph,
  continuity-tracker, sources/, digests/, drafts/_archive/, final/,
  examples-library)
- `project-status.yaml` at `phase: setup` with `schema_version: "2.3"`

Init is separate from setup on purpose — the human can inspect the scaffold
before the skill starts asking questions. After scaffolding, announce what
was created and ask to proceed to Phase 1.

---

## Phase 1: Project Setup

Start with one question:

**"¿Qué tipo de proyecto es: literario o técnico?"**

(If the user already made this clear in the conversation, skip the question and
proceed. Don't ask things whose answer is obvious in context.)

- **Technical** (manuals, tutorials, guides, reference books): read
  `references/setup-technical.md`.
- **Literary** (fiction, creative nonfiction, memoir, narrative): read
  `references/setup-literary.md`.

The setup produces files in the project's `bible/` directory. The human reviews
and approves each file before the next one is produced. Setup is NOT a form-filling
exercise — it's a collaborative design session. Ask good questions, propose options,
let the human react.

The setup writes `bible/meta.yaml` with `project.type: technical` or
`project.type: literary`. **All downstream agents read this field to select their
own mode.** If you pick the wrong mode, the chapter will be written as the wrong
kind of prose.

For technical projects, the setup also asks for `pipeline.mode` (`fast` or
`full`) and writes the `models:` section with sensible defaults (Opus for
Writer and Critic, Sonnet for everything else). The human can change these at
any point.

Technical setup ends with **Sub-Phase 8 — Knowledge Graph** (see
`references/knowledge-graph.md`): the concept dependency map that anchors
outlining and enforces "no chapter uses a term introduced later". Do not
skip this sub-phase for serious technical books — it's what makes the
Critic's forward-reference checks useful.

---

## Phase 1.5: Knowledge Graph (technical only)

A distinct phase between setup and outlining, because it's load-bearing for
both. By the end, `bible/knowledge-graph.yaml` lists every concept the book
will teach with `requires` / `builds_on` / `contrasts_with`. Outlining then
assigns each concept an `introduced_in: ch-NN` value; the Critic checks that
chapters only reference concepts whose `introduced_in` is ≤ current chapter.

See `references/knowledge-graph.md` for the guided session.

Literary projects skip this phase — plot structure and character arcs serve
the equivalent role via `plot-structure.md` and `arcs.md`.

---

## Phase 2: Outlining

Read `references/outlining.md`. It has branches for technical vs. literary.

The outline is saved to `outline/chapters.yaml`. The human approves the full outline
before any writing begins.

---

## Phase 3: Writing Pipeline

This is the heart of the framework. For each chapter, run the pipeline sequentially.

### Technical pipeline

Two modes, controlled by `pipeline.mode` in `bible/meta.yaml`:

#### fast mode (default)

```
Writer → Technical Reviewer → Editor → Humanizer → Continuity Guardian (coherence) → Critic (GATE) → Human Review
                                                                                          ↓
                                                                            [loopback if FAIL]
                                                                                          ↓
                                                                               (after approval)
                                                                                          ↓
                                                              Proofreader → Continuity Guardian (tracker update)
```

Six agents per cycle as of v2.4.1. Humanizer runs per chapter to keep voice
drift out of approved chapters. Continuity Guardian runs a pre-gate coherence
pass that verifies prose and format match earlier chapters (terminology,
heading style, example notation, voice) before the Critic gates the chapter;
a separate post-approval run updates the tracker. Only Reader-POV is deferred
to `full` mode. This remains the right default for most technical books:
tutorials, references, manuals, MVP drafts.

#### full mode (opt-in)

```
Writer → Technical Reviewer → Editor → Humanizer → Reader-POV → Critic (GATE) → Human Review
```

Six agents per cycle. Use when prose quality matters as much as correctness —
customer-facing books, books where the reading experience is part of the
product.

#### The Technical Reviewer

A single agent that replaces what used to be the Fact-Checker and SME Reviewer.
It audits the chapter on two axes and produces one report (`tech-review.md`):

- **Axis A — Claims, code, versions**: verifies factual claims, runs code
  (if `pipeline.reviewer_can_run_code: true`), checks pinned versions,
  flags unverifiable assertions.
- **Axis B — Mental models, framings, terminology**: checks the chapter's
  framings and mental models against the grounding library in
  `bible/sources/`, verifies terminology consistency with the glossary,
  flags silent divergences from authoritative sources.

If `bible/sources/` is empty, Axis B runs against the glossary, continuity
tracker, and scope only. The report carries an explicit "Grounding library
empty" note that the Critic propagates to the human — never silent.

### Literary pipeline

```
Writer → Editor → Humanizer → Reader-POV → Critic (GATE) → Human Review
                                                ↓
                                     [loopback if FAIL]
                                                ↓
                                        (after approval)
                                                ↓
                                 Proofreader → Continuity Guardian
```

Literary mode does not have fast/full. For narrative fiction the Humanizer
and Reader-POV are load-bearing per chapter — voice IS the product.

**Read `references/pipeline.md` for the full specification**: exact
inputs/outputs per agent, loopback rules, verdict severities, retry policy,
model assignment details. Do not skip it — the pipeline is what makes this
skill work.

### Agent reference files

Each agent has its own reference file. Load it fresh at the start of that
agent's turn — do not rely on memory of a previous chapter's instructions.

| Agent                | Technical reference                              | Literary reference                              |
|----------------------|--------------------------------------------------|-------------------------------------------------|
| Writer (SME in tech) | `references/agent-writer-technical.md`           | `references/agent-writer-literary.md`           |
| Technical Reviewer   | `references/agent-technical-reviewer.md`         | — (not in literary pipeline)                    |
| Editor               | `references/agent-editor.md` (§ Technical)       | `references/agent-editor.md` (§ Literary)       |
| Humanizer (full only)| `references/agent-humanizer-technical.md`        | `references/agent-humanizer-literary.md`        |
| Reader-POV (full only)| `references/agent-reader-pov.md` (§ Technical)  | `references/agent-reader-pov.md` (§ Literary)   |
| Critic (gate)        | `references/agent-critic-technical.md`           | `references/agent-critic-literary.md`           |
| Proofreader          | `references/agent-proofreader.md` (both)         | `references/agent-proofreader.md` (both)        |
| Continuity Guard.    | `references/agent-continuity-guardian.md` (both) | `references/agent-continuity-guardian.md` (both)|

In technical `fast` mode, only Reader-POV is skipped per chapter. Humanizer
runs every chapter (as of v2.4.1), and Continuity Guardian runs twice per
chapter — a pre-gate coherence check before the Critic, and the tracker
update after approval. Reader-POV runs only in `full` mode per chapter, or
in the optional polish pass over batches of approved chapters.

### Model assignment per role

Each agent is spawned with a Claude model configured in `bible/meta.yaml`
under `models:`. The default layout puts Opus where creativity or gating
judgment is load-bearing, and Sonnet elsewhere.

| Role                | Technical default | Literary default |
|---------------------|-------------------|------------------|
| Writer              | Opus              | Opus             |
| Technical Reviewer  | Sonnet            | —                |
| Editor              | Sonnet            | Sonnet           |
| Humanizer           | Sonnet            | Opus             |
| Reader-POV          | Sonnet            | Sonnet           |
| Critic              | Opus              | Opus             |
| Proofreader         | Sonnet            | Sonnet           |
| Continuity Guardian | Sonnet            | Sonnet           |

Override any role in your project's `meta.yaml`. The skill falls back to
`models.default` (Sonnet) if a role isn't explicitly set, and to
`claude-sonnet-4-6` if `models:` is missing entirely.

### Anti-mediocrity reads

Agents that produce, tune, or audit prose must load the matching
anti-mediocrity file. Agents whose scope is structural, factual, mechanical,
or simulation-only do NOT load it (loading it pulls them toward scope creep).

| Agent                | Reads anti-mediocrity? |
|----------------------|------------------------|
| Writer               | yes — avoid patterns while drafting |
| Technical Reviewer   | no — correctness scope only |
| Editor               | no — structural scope only, flags prose for Humanizer |
| Humanizer            | yes — its primary checklist |
| Reader-POV           | **no** — deliberate constraint; real readers don't have it |
| Critic (gate)        | yes — audits hits, assigns loopback |
| Proofreader          | no — mechanical pass only |
| Continuity Guardian  | yes (Mode A coherence pass — voice drift detection); no (Mode B tracker update) |

Mode selection:

- Technical → `references/anti-mediocrity-technical.md`
- Literary → `references/anti-mediocrity-literary.md`

### What "sharpened boundaries" means in practice

If you are playing the role of an agent, do ONLY what your reference file
says. Resist scope creep.

- **Writer**: produces a draft. Does not self-edit. Does not polish.
  **In technical mode, this is the SME Writer**: before drafting, it runs
  a pre-draft grounding pass against `bible/sources/` and emits
  `grounding-notes.md`. Load-bearing claims in the draft carry inline
  `<!-- SOURCE: ... -->` comments. Literary Writer is unchanged.
- **Technical Reviewer** (tech only): audits correctness in two axes
  (claims/code/versions, and mental models/framings/terminology/grounded
  sources). Produces a report with an optional loopback-to-Writer verdict.
  Does not rewrite. Runs before the Editor so it evaluates the draft in
  its uncompressed form.
- **Editor**: fixes STRUCTURE only — scene order, chapter opening/ending
  shape, pacing, transitions, internal continuity inside the chapter.
  Reads the Technical Reviewer's report (when technical) to incorporate
  sequencing suggestions. Does NOT fix weak verbs, hedging, rhythm, or
  dialogue voice. That is the Humanizer's job.
- **Humanizer** (full mode only for technical): line-level prose — voice,
  rhythm, subtext (literary) or clarity, concreteness, de-signposting
  (technical). Does NOT restructure or add content.
- **Reader-POV** (full mode only for technical): simulates the reading
  experience, flags confusion or disengagement, produces a report. Does
  not fix anything.
- **Critic**: gate. Audits the final-candidate text. Issues a verdict and
  a loopback directive.
- **Proofreader**: post-approval. Typos, commas, capitalization, heading
  styles.
- **Continuity Guardian**: post-approval. Updates the tracker file. Runs
  cross-chapter audits on schedule.

When an agent is tempted to fix something outside its scope, it should
FLAG it for the next-appropriate agent via an HTML comment, not fix it
silently. This is non-negotiable — if every agent fixes everything, the
pipeline collapses into four identical rewrites and the role separation
is meaningless.

---

## Phase 4: Assembly & Review

After all chapters are approved:

1. Concatenate `final/ch-NN.md` files in order into `manuscript.md`.
2. Run the Continuity Guardian's full-manuscript audit (see its reference
   file). For technical projects, this includes the orphan-terms coverage
   audit (output: `bible/orphan-terms-audit.md`) — terms used in prose but
   absent from KG/glossary surface here for human triage before shipping.
   Advisory, not blocking. Disable with
   `pipeline.coverage_audit.enabled: false`.
3. Run the Proofreader on any chapters that had late edits.
4. **(Technical, fast mode) Optional polish pass**: run the Humanizer and
   Reader-POV over batches of 3–4 approved chapters to smooth voice
   consistency across the manuscript. This is cheaper than paying those
   agents per chapter and produces better cross-chapter consistency. See
   `references/pipeline.md` § "Optional polish pass".
5. Generate a style consistency report: voice drift across chapters, repeated
   phrases, pacing of the whole arc.
6. Present findings. Human decides on final revisions.

---

## Project File Structure

```
book-project/
├── bible/
│   ├── meta.yaml                # Project metadata. Contains project.type,
│   │                            # pipeline.mode, models:.
│   ├── style-guide.md           # Voice, tone, conventions, calibration passages
│   ├── characters/              # (literary only) one file per significant character
│   │   └── ...
│   ├── world.md                 # (literary only) setting, rules, lore
│   ├── plot-structure.md        # (literary only) acts, major beats
│   ├── arcs.md                  # (literary only) character + thematic arcs
│   ├── timeline.md              # (literary only) chronological events
│   ├── glossary.md              # (technical only) terminology with definitions
│   ├── scope.md                 # (technical only) in/out-of-scope, prerequisites
│   ├── sources/                 # (technical only) grounding library for Technical Reviewer
│   │   ├── sources.md           # index of books/papers/specs + authoritative-for + version drift
│   │   ├── *.pdf                # originals (kept for visual/layout fallback)
│   │   ├── *.md                 # extracted text (reviewer reads this first)
│   │   └── *-figures/           # extracted images (PNG per figure)
│   ├── examples-library.md      # (technical only) running code examples across chapters
│   └── continuity-tracker.md    # Character/state tracker (both, different content)
├── outline/
│   └── chapters.yaml            # Chapter-by-chapter breakdown
├── drafts/
│   └── ch-01/
│       ├── grounding-notes.md   # (v2.4, technical) SME Writer pre-draft grounding artifact
│       ├── draft.md             # Writer output
│       ├── tech-review.md       # Technical Reviewer output (technical only)
│       ├── edit.md              # Editor output
│       ├── humanized.md         # Humanizer output (full mode only for technical)
│       ├── reader-report.md     # Reader-POV output (full mode only for technical)
│       ├── critique.md          # Critic prose report (renders scorecard)
│       └── critique-scorecard.yaml  # (v2.3) machine-readable scorecard; verdict computed from it
├── drafts/
│   └── _archive/                # (v2.3) approved chapters' draft bundles move here
│       └── ch-NN/
├── bible/
│   ├── knowledge-graph.yaml     # (v2.3, technical) concept dependency map
│   └── digests/                 # (v2.3) per-chapter 300–500-word digests
│       └── ch-NN.digest.md
├── final/
│   └── ch-NN.md                 # Approved chapters (Proofreader-polished)
├── project-status.yaml          # (v2.3 schema) phase, current_chapter, retries,
│                                # archived chapters, cost_observability
├── loopback-escalation-ch-NN.md # (v2.3) emitted on cap hit — see loopback-handoff.md
└── manuscript.md                # (Phase 4) concatenated approved chapters
```

---

## v2.3 reference files (read on demand)

The SKILL.md body is a map, not the full spec. Load these when the
corresponding phase or event is active:

| Trigger                                | Read                                          |
|----------------------------------------|-----------------------------------------------|
| New project, no `bible/`               | `references/init-scaffold.md`                 |
| Technical setup                        | `references/setup-technical.md`               |
| Literary setup                         | `references/setup-literary.md`                |
| Phase 1.5 (technical only)             | `references/knowledge-graph.md`               |
| Outlining                              | `references/outlining.md`                     |
| Writing pipeline (full spec)           | `references/pipeline.md`                      |
| Per-agent behavior                     | `references/agent-*.md` (one per agent)       |
| Technical Reviewer validation config   | `references/validation-surface.md`            |
| Critic rubric + verdict computation    | `references/rubric.md`                        |
| Retry cap hit                          | `references/loopback-handoff.md`              |
| After chapter approval                 | `references/chapter-digest.md` + `references/archiving.md` |
| Anti-mediocrity guard (during prose)   | `references/anti-mediocrity-{technical,literary}.md` |

Templates live under `templates/` (meta, project-status, knowledge-graph,
chapter-digest, critique-scorecard, loopback-escalation, chapter-entry,
orphan-terms-audit). Scaffold and migration copy from these.