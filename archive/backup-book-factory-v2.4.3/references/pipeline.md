# Pipeline Specification (v2.4.3)

This file defines how the writing pipeline runs for a single chapter: the order
of agents, their inputs and outputs, how the Critic's gate works, and what happens
when the gate fails.

Read this before running the pipeline for the first time in a session.

The body documents v2.4.3 behavior end-to-end. The "additions" boxes below
record what changed across versions for readers migrating from older
projects.

**v2.4.3** — Phase 4 coverage audit (orphan terms in prose vs. KG/glossary).
**v2.4.2** — Citational-prose watchlist patch (Humanizer + Continuity Guardian Mode A).
**v2.4.1** — Fast mode now runs Humanizer per chapter + a new Continuity
Guardian Mode A (pre-gate coherence). Reader-POV stays the only agent
deferred to full mode per chapter.
**v2.4** — SME Writer (pre-draft grounding pass against `bible/sources/`).

**v2.3 additions** (see companion references for details):

- Chapter digests replace full prior-chapter reads for most agents
  (`references/chapter-digest.md`).
- The Critic emits a rubric scorecard (`references/rubric.md`); the verdict
  is computed from it.
- The Technical Reviewer loads validation-surface sub-prompts for Axis A
  (`references/validation-surface.md`).
- The retry cap triggers a structured escalation packet instead of a vague
  "ask the human" (`references/loopback-handoff.md`).
- Approved chapters' drafts are archived to `drafts/_archive/`
  (`references/archiving.md`).
- Every agent call appends a cost row to `project-status.yaml` under
  `cost_observability.by_call`.

---

## The Pipeline

### Technical mode

Technical projects support two pipeline modes, controlled by `pipeline.mode`
in `bible/meta.yaml`:

#### `fast` (default for technical)

```
Writer → Technical Reviewer → Editor → Humanizer → Continuity Guardian (coherence) → Critic (GATE) → Human
                                                                                                       │
                                                                                       (after approval)
                                                                                                       ↓
                                                                                    Proofreader → Continuity Guardian (tracker update)
```

Six agents per cycle (vs. literary's six; Reader-POV is the only full-mode
add-on). As of v2.4.1, fast mode runs the Humanizer and a pre-gate coherence
pass per chapter: the voice drift and cross-chapter prose/format
inconsistency that used to only surface at the end-of-manuscript polish pass
was leaking into approved chapters too often to defer. Reader-POV stays
opt-in (in `full` mode) — it's the agent whose value per chapter is most
uneven for reference-style technical books.

The Continuity Guardian runs TWICE in fast mode, with two distinct scopes:

- **Pre-gate coherence check** (before Critic): reads the humanized draft
  plus the most recent 1–2 approved chapters and the digests of earlier
  chapters. Flags prose-voice drift, terminology drift, heading-style
  drift, example-notation drift, and any format inconsistency with what
  the reader has already seen. Produces `drafts/ch-NN/coherence.md`.
  Does NOT update the tracker. This pass is advisory → Critic; the
  Critic folds findings into its verdict (REVISE to Humanizer for voice
  drift, to Writer for terminology drift from the glossary).
- **Post-approval tracker update** (unchanged from v2.3): runs after
  Proofreader on the approved `final/ch-NN.md`, updates
  `bible/continuity-tracker.md`, does the 3-chapter cross-audit on schedule.

Use `fast` for: tutorials, references, manuals, internal docs, MVP drafts.

#### `full` (opt-in for technical)

```
Writer → Technical Reviewer → Editor → Humanizer → Reader-POV → Critic (GATE) → Human
                                                                                   │
                                                                   (after approval)
                                                                                   ↓
                                                                Proofreader → Continuity Guardian
```

Six agents per cycle. Use when prose quality matters as much as correctness:
customer-facing books, books with marketing weight, anything where the
reading experience is part of the product.

#### Why one Technical Reviewer instead of two

The Technical Reviewer is a single agent that audits two axes in one pass:

- **Axis A (Claims, code, versions)** — what the old Fact-Checker did.
- **Axis B (Mental models, framings, terminology)** — what the old SME
  Reviewer did, including the grounding-library check against
  `bible/sources/`.

Both axes are about content correctness, just measured against different
references. Running them as one agent saves a full bible re-read and
produces a single report (`tech-review.md`) for downstream agents to read.
See `agent-technical-reviewer.md`.

If `bible/sources/` is empty, Axis B runs against the glossary, continuity
tracker, and scope only. The report carries an explicit "Grounding library
empty — Axis B was partial" note. The Critic propagates the note to the
human review packet — never silent.

### Literary mode

```
Writer → Editor → Humanizer → Reader-POV → Critic (GATE) → Human
                                                              │
                                               (after approval)
                                                              ↓
                                            Proofreader → Continuity Guardian
```

Literary mode does not have a fast/full split. For narrative fiction the
Humanizer and Reader-POV are load-bearing per chapter — the voice IS the
product. The Technical Reviewer does not exist in literary mode.

---

## Model assignment

Each agent is spawned with a Claude model configured in `bible/meta.yaml`
under `models:`. The assignment lets you put the heavyweight model only
where it pays off and keep the lighter, cheaper model on structured
audit/polish tasks.

### How the skill resolves the model for an agent

1. Look up `models.<role>` in `bible/meta.yaml` (e.g., `models.writer`).
2. If unset, fall back to `models.default`.
3. If `models:` is missing entirely, fall back to `claude-sonnet-4-6`.

Role keys recognized: `writer`, `technical_reviewer`, `editor`, `humanizer`,
`reader_pov`, `critic`, `continuity_guardian`, `proofreader`.

### Recommended defaults

**Technical:**
- `writer: claude-opus-4-6` — first-draft creativity, hard to recover from a
  bad draft
- `critic: claude-opus-4-6` — single gate, cost of a wrong PASS is high
- `default: claude-sonnet-4-6` — everything else

**Literary:**
- `writer: claude-opus-4-6` — voice is established here
- `humanizer: claude-opus-4-6` — voice is the product
- `critic: claude-opus-4-6`
- `default: claude-sonnet-4-6`

You can override any role in your project's `meta.yaml`. If you have an
unusually voice-heavy technical book, promote `humanizer` to Opus. If you
trust your prompts and want to A/B test, demote `writer` to Sonnet on a
chapter and compare.

---

## Agent contracts

Each agent has a strict input/output contract. An agent may read more than
its input (e.g., the bible) but it produces exactly one artifact.

### Technical mode contracts

| Agent              | Reads                                                                      | Writes                              |
|--------------------|----------------------------------------------------------------------------|-------------------------------------|
| SME Writer         | meta, style-guide, glossary, scope, sources/, outline entry, prev ch., tracker | `drafts/ch-NN/grounding-notes.md` + `drafts/ch-NN/draft.md` |
| Technical Reviewer | draft, grounding-notes, meta, scope, glossary, sources/, outline entry, prev ch., tracker | `drafts/ch-NN/tech-review.md`  |
| Editor             | draft, tech-review, outline entry, meta, prev ch.                          | `drafts/ch-NN/edit.md`              |
| Humanizer (fast + full) | edit, tech-review, style-guide, anti-mediocrity-technical             | `drafts/ch-NN/humanized.md`         |
| Cont. Guardian (fast pre-gate) | humanized, prev 1–2 final/, all digests, style-guide, glossary, tracker | `drafts/ch-NN/coherence.md` |
| Reader-POV (full)  | humanized, meta, outline entry                                             | `drafts/ch-NN/reader-report.md`     |
| Critic (gate)      | humanized, tech-review, coherence (fast) OR reader-report (full), style-guide, tracker, bible | `drafts/ch-NN/critique.md` |
| Proofreader        | `final/ch-NN.md` (after human approves as final)                           | updates `final/ch-NN.md` in place   |
| Cont. Guardian     | `final/ch-NN.md`, all prev final/, continuity-tracker                      | updates tracker, writes audit notes |

In both `fast` and `full` modes the Critic reads `humanized.md` (Humanizer's
output). Fast mode also gives it `coherence.md` from the Continuity
Guardian's pre-gate pass; full mode gives it `reader-report.md` from
Reader-POV.

**v2.4 — the SME Writer.** In technical mode, the Writer is now an SME Writer
(see `agent-writer-technical.md`). Before drafting, it runs a pre-draft
grounding pass against `bible/sources/` and emits `grounding-notes.md`
alongside `draft.md`. This front-loads the grounding work that v2.3's
Technical Reviewer did after the fact, reducing Reviewer → Writer loopbacks
on avoidable framing/terminology hits. The Technical Reviewer still audits
both axes, but it verifies the Writer's citations rather than re-deriving
them from scratch. If `bible/sources/` is empty or has no content relevant
to the chapter, the grounding pass is skipped with a documented note —
behavior then matches v2.3.

### Literary mode contracts

| Agent          | Reads                                                              | Writes                              |
|----------------|--------------------------------------------------------------------|-------------------------------------|
| Writer         | meta, style-guide, characters/, world, plot, outline entry, prev ch., tracker | `drafts/ch-NN/draft.md`  |
| Editor         | draft, outline entry, meta, prev ch.                               | `drafts/ch-NN/edit.md`              |
| Humanizer      | edit, style-guide, anti-mediocrity-literary                        | `drafts/ch-NN/humanized.md`         |
| Reader-POV     | humanized, meta, outline entry                                     | `drafts/ch-NN/reader-report.md`     |
| Critic (gate)  | humanized, reader-report, style-guide, tracker, bible              | `drafts/ch-NN/critique.md`          |
| Proofreader    | `final/ch-NN.md` (after human approves as final)                   | updates `final/ch-NN.md` in place   |
| Cont. Guardian | `final/ch-NN.md`, all prev final/, continuity-tracker              | updates tracker, writes audit notes |

---

## The Technical Reviewer mini-gate (technical only)

The Technical Reviewer runs after the Writer and before the Editor. It's a
smaller gate than the Critic: its only hard-stop verdict is REVISE → Writer.
Findings destined for the Editor or Humanizer ride along in `tech-review.md`
as advisory — those agents read the file in their normal turn.

Verdicts:

| Verdict      | Action                                                                                              |
|--------------|-----------------------------------------------------------------------------------------------------|
| **PASS**     | Proceed to Editor. `tech-review.md` carries advisory notes downstream.                              |
| **REVISE**   | Loopback to Writer. Writer re-drafts with the Reviewer's specific instructions.                     |
| **ESCALATE** | Ask the human. Usually a glossary conflict, a wrong pinned version, or a known-wrong-source issue. |

The Technical Reviewer does NOT loopback to Editor or Humanizer — they run
after it, and they consume its report as input. This keeps the pipeline's
one true multi-target gate (the Critic) clean.

Cycles through Reviewer→Writer loopback count against the same retry cap as
Critic cycles (see "Retry policy" below).

---

## The Critic Gate

The Critic is not a pipeline step that produces a deliverable to pass forward.
It is a **gate**: it audits the chapter at its current state (humanized in
full mode, edit in fast mode) and issues a verdict plus a loopback directive.

### Verdicts

| Verdict      | Meaning                                                                          |
|--------------|----------------------------------------------------------------------------------|
| **PASS**     | Ready for the human. Any minor issues are noted but not blocking.                |
| **REVISE**   | Fixable problems. Loopback to one specific agent.                                |
| **REWORK**   | Substantial problems across multiple layers. Loopback to Writer.                 |
| **ESCALATE** | Problem is above the pipeline's pay grade (e.g., outline beat is wrong). Ask the human. |

### Loopback rules

When the Critic says **REVISE**, it must name the target agent and explain why.
The target is determined by the TYPE of problem, not by the severity:

| Type of problem                                                                       | Loopback target                                              |
|---------------------------------------------------------------------------------------|--------------------------------------------------------------|
| Structural, pacing, scene/section order, continuity within chapter                    | **Editor**                                                   |
| Factual error, broken code, wrong version, terminology drift, mental-model failure    | **Writer** (with Technical Reviewer findings as input)       |
| Voice drift, generic prose, AI-isms, rhythm, dialogue voice                           | **Humanizer** (full mode only — in fast mode, REVISE → Writer) |
| Target reader would be confused / bored                                               | **Reader-POV + Humanizer** (full only) or **Writer** (fast)  |
| Outline beat not delivered / altered                                                  | **Writer**                                                   |
| Contradicts bible or prior chapters                                                   | **Writer** (with bible/tracker as input)                     |

In `fast` mode there is no Humanizer in the per-chapter cycle. Prose-quality
issues that the Critic still wants fixed before chapter approval go back to
the Writer. The expectation is that fast-mode chapters are approved on
correctness, and a polish pass at the end addresses voice consistency across
the manuscript.

When the Critic says **REWORK**, always loopback to Writer. This means the
chapter has failed at a level that trimming and polishing can't rescue — it
needs to be written again, usually with amended instructions from the human.

### What the Critic must output

The Critic writes `drafts/ch-NN/critique.md` using the template in
`templates/critique-report.md`. The header is always:

```markdown
# Critique: Chapter NN — [title]

## Verdict: PASS | REVISE | REWORK | ESCALATE

## Loopback target (if REVISE): [agent name]
## Loopback rationale: [one sentence]
```

This header is machine-readable. The skill uses it to decide what happens next.

### Retry policy

A chapter can cycle through the loopback at most `pipeline.retry_cap` times
(from `bible/meta.yaml`) before the skill must escalate to the human,
regardless of verdict. Defaults: **2** for `fast`, **3** for `full`.

The cap counts total loopbacks for the chapter — Reviewer→Writer,
Critic→any agent, or human-triggered revisions all share the same budget.
When the cap is reached, the skill **does not** emit a generic "ask the
human." It produces the structured escalation packet described in
`references/loopback-handoff.md`: per-cycle diff, failure-pattern
diagnosis, three concrete options, and the skill's recommended pick. The
chapter's pipeline is paused until the human chooses.

After the human chooses, `retries.by_chapter[ch-NN]` resets to 0 (the
new path is a fresh attempt) and the pipeline resumes per the chosen
option.

---

## Digests — what replaces reading prior chapters in full

Past chapter 4–5 of a linear book, reading every prior chapter on every
downstream agent's turn is context bloat. v2.3 introduces chapter
digests — 300–500-word structured summaries produced after approval
(see `references/chapter-digest.md`).

Which agents read digests vs. full prior chapters:

| Agent              | Digests                      | Full prior chapter                         |
|--------------------|------------------------------|--------------------------------------------|
| Writer             | All prior chapters           | Most recent chapter only (voice calibration) |
| Technical Reviewer | All prior chapters           | Most recent chapter only (if glossary audit needs it) |
| Editor             | —                            | —                                          |
| Humanizer (fast + full) | Most recent digest      | Most recent chapter (voice)                 |
| Reader-POV (full)  | —                            | — (cold-read simulation)                   |
| Critic             | All prior chapters           | Most recent chapter only                    |
| Continuity Guardian| All digests                  | All chapters (on scheduled audits only)     |

The skill produces each digest after human approval + Proofreader +
Continuity Guardian complete, before archiving. Disable globally with
`pipeline.chapter_digest.enabled: false` for short books.

---

## Archiving approved drafts

After human approval + Proofreader + Continuity Guardian + digest
generation, the skill moves `drafts/ch-NN/` to `drafts/_archive/ch-NN/`.
See `references/archiving.md` for the full policy (re-open handling,
timestamped re-archives, disable flag).

---

## Cost observability

Every agent call appends a row to
`project-status.yaml:cost_observability.by_call`:

```yaml
- chapter: "ch-07"
  agent: "writer"
  model: "claude-opus-4-6"
  input_tokens: 28450
  output_tokens: 4210
  cycle: 2
  timestamp: "2026-04-20T14:02:15Z"
```

The skill aggregates on read into per-chapter and per-agent totals. This
is observability, not a budget cap. The human decides whether a role is
earning its cost after 3–4 chapters of data and may downgrade to a
cheaper model or skip a role via `meta.yaml:models:` overrides.

---

## Human Review (the real gate)

Even a PASS from the Critic doesn't ship the chapter. The human decides. When
presenting a chapter to the human, always include:

- **The chapter text** being approved. Which file depends on mode: in fast
  mode (v2.4.1+) and full mode it's `drafts/ch-NN/humanized.md`. The
  Critic gated against this exact text — the human reviews the same.
- **The Critic's verdict header** from `drafts/ch-NN/critique.md`: `PASS` /
  `REVISE` / `REWORK` / `ESCALATE`, and which scorecard rule produced it
  (e.g., "1 critical fail → REVISE, target=Writer").
- **The scorecard summary** from `drafts/ch-NN/scorecard.yaml`: counts per
  severity, plus the failing items with `evidence`. The human is
  reviewing a checklist, not a narrative — the scorecard is the
  load-bearing artifact.
- **The Critic's `Observations` section** — free-form notes that aren't
  rubric items but are worth flagging.
- **The Technical Reviewer's `tech-review.md`** with any findings. If
  Axis B was skipped because `bible/sources/` is empty, propagate the
  skip note explicitly — never silent.
- **The pre-gate context artifact**: `drafts/ch-NN/coherence.md`
  (fast mode, Continuity Guardian Mode A) or
  `drafts/ch-NN/reader-report.md` (full mode, Reader-POV).
- **Retry summary** if this chapter went through any REVISE/REWORK
  loops: how many cycles, which agent each cycle targeted, what
  changed cycle-to-cycle. Read from `project-status.yaml.retries`.
- **Cost for this chapter** (aggregated from
  `project-status.yaml.cost_observability.by_call`): tokens and
  duration per agent, plus the chapter total. Lets the human spot
  agents that are spending more than they're earning.

The human has three responses:

- **Approve** → triggers Proofreader → Continuity Guardian (Mode B,
  tracker update) → chapter digest generation → archive of `drafts/ch-NN/`
  to `drafts/_archive/ch-NN/`. Chapter is now in `final/`.
- **Reject with revisions** → writes specific notes; the skill routes to
  the agent the human names (or `Writer` by default). Counts against the
  same `pipeline.retry_cap` budget as Critic loopbacks. The retry counter
  does not reset until the human chooses an option from the cap-hit
  escalation packet.
- **Defer** → leaves the chapter in draft state. The pipeline does
  nothing automatically; the human can resume later, or move on to a
  different chapter and come back.

Don't gate human approval on a green scorecard. The scorecard is decision
support, not authority. A human can approve a chapter with `minor` (or
even `significant`) fails if the rationale is recorded in their approval
note. The reverse is also true: the human can reject a `PASS`-ed chapter
if it doesn't feel right, with a free-form revision note that becomes
the next cycle's instruction.

---

## Optional polish pass (technical only, Phase 4)

A batch-level pass over already-approved chapters, run during Phase 4
(Assembly & Review) after the Continuity Guardian's full-manuscript audit
(step 2) and Proofreader (step 3). It exists for two reasons:

- **Reader-POV's missing per-chapter scrutiny**. In `fast` mode,
  Reader-POV is the one agent that does NOT run per chapter (v2.4.1).
  The polish pass is its first read of the manuscript. In `full` mode
  Reader-POV already ran per chapter — this pass replaces a per-chapter
  read with a connected cross-chapter read, which catches different
  failure modes.
- **Humanizer's cross-chapter awareness**. The per-chapter Humanizer
  (v2.4.1) sees one chapter at a time. A specific AI-ism appearing once
  per chapter would be a `minor` hit each time and pass; the same AI-ism
  showing up four times across four chapters is a `significant` voice
  problem only visible at batch level. Same for em-dash density,
  signposting cadence, and synonym cycling on load-bearing terms.

### When to run

Phase 4 step 4. After full-manuscript audit (step 2) and Proofreader
(step 3), before the style consistency report (step 5). Skip if there
are fewer than 3 approved chapters since the last polish run — below
that, the cross-chapter signal is too thin to justify the cost.

### What it does

For each batch of 3–4 consecutive approved chapters (`final/ch-NN.md`):

1. **Reader-POV (batch mode)**. Reads the batch as one continuous read.
   Looks for: chapters that drag, chapters that lean on a concept that
   was supposed to land in the previous chapter but didn't quite, batch-
   level pacing issues, and sustained engagement. Loads `meta.yaml` and
   the outline entries for the batch. Does NOT load chapter digests —
   the simulation is "fresh reader". Output:
   `drafts/_polish/batch-[NN]-[MM]/reader-report.md`.
2. **Humanizer (batch mode)**. Reads the batch + Reader-POV's batch
   report + `bible/style-guide.md` + `references/anti-mediocrity-technical.md`.
   Re-runs the Layer 1–5 checklist with cross-chapter awareness. Output:
   proposed line-level edits against the relevant `final/ch-NN.md`
   files, written as a unified diff in
   `drafts/_polish/batch-[NN]-[MM]/proposed-edits.diff`.

The Humanizer's edits are PROPOSED, not applied — same gate as a
per-chapter Critic REVISE: the human reviews the diff and decides
accept-all, partial-accept, or reject. Accepted edits update
`final/ch-NN.md` in place; rejected edits become inline review comments
on the chapter for the next iteration. Continuity Guardian re-runs Mode
B (tracker update) on any chapter whose `final/ch-NN.md` changed.

### What it does NOT do

- It does NOT re-run the Critic. The chapters are already approved; the
  polish pass is voice-and-pacing, not gate.
- It does NOT touch `bible/knowledge-graph.yaml`, `bible/glossary.md`,
  or `bible/scope.md`. Vocabulary changes are the human's call. The
  coverage audit in step 2 is what surfaces vocabulary gaps.
- It does NOT run for literary mode. Literary chapters get the
  Humanizer + Reader-POV per chapter — there's no fast/full split to
  compensate for at the batch level.
- It does NOT regenerate chapter digests. Digests freeze at chapter
  approval; if a chapter changes during the polish pass, only the
  tracker is updated, not the digest. This is intentional: digests are
  voice-calibration samples for downstream chapters during *writing*,
  and the writing is done by the time polish runs.

### Disabling

`pipeline.polish_pass.enabled: false` in `meta.yaml` skips this step
entirely. Default is `true` for `fast` mode and ignored for `full` mode
(no behavior to enable — Reader-POV already ran per chapter, and a batch
re-run is rarely worth it for full-mode books that paid for thorough
prose work upfront).

### Cost-vs-value reading

After 3–4 polish passes on a project, read
`project-status.yaml.cost_observability` for the polish-pass agents and
check the human's edit-acceptance rate. If acceptance is below ~30%, the
pass is generating noise — consider tightening the batch trigger to 5+
chapters or disabling it for this project. This is observability, not a
hard rule.

---

## See also

- `references/agent-continuity-guardian.md` for the Mode A/B split and
  the Phase 4 full-manuscript audit (including the orphan-terms
  coverage check, v2.4.3+).
- `references/rubric.md` for the scorecard schema and verdict
  computation.
- `references/loopback-handoff.md` for the cap-hit escalation packet.
- `references/archiving.md` for how approved drafts are moved to
  `drafts/_archive/`.
- `references/chapter-digest.md` for the post-approval digest.
- `templates/critique-scorecard.yaml` and `templates/critique-report.md`
  for the Critic's output shape.
