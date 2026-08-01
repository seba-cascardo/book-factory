# Pipeline Specification

This file is the single authoritative spec of the Phase 3 writing pipeline:
agent order, input/output contracts, the two gates, loopback rules, retry
policy, digests, logging, and the Phase 4 polish pass. Read it before running
the pipeline for the first time in a session. If any other file appears to
disagree with this one on pipeline order or artifact names, this file wins —
report the conflict.

## Invariants

Memorize these; they are the points where documentation drift historically
produced real bugs:

- **The Critic always gates `humanized.md`** — every mode, every profile. The
  Critic must audit the exact text the human will review; gating an earlier
  artifact would let the Humanizer ship unaudited prose.
- **The Humanizer runs every unit, in every mode.** There is no mode without
  a Humanizer in the per-unit cycle.
- **The Editor is structural only.** It never applies prose fixes and never
  applies Technical Reviewer advisories — those belong to the Humanizer. One
  owner per fix; two agents applying the same advisory produce colliding
  edits and untraceable regressions.
- **Verdicts are computed, not chosen.** The Critic fills
  `drafts/unit-NN/scorecard.yaml`; the verdict falls out of it per the rule
  in `references/rubric.md`.

---

## The pipeline

`bible/meta.yaml → pipeline.mode` selects `fast` (default) or `full` for
nonfiction profiles (`book-technical`, `corporate-guide`, `product-docs`,
`scientific-paper`). `book-literary` has a single flow — no fast/full split,
because for fiction the Humanizer and Reader-POV are load-bearing per unit.

### Nonfiction — `fast` (default)

```
Writer → Technical Reviewer → Editor → Humanizer
  → Continuity Guardian (Mode A: coherence) → Critic (GATE)
  → [Adversarial Verify, if enabled] → Human review
  → (on approval) Proofreader → Continuity Guardian (Mode B: tracker)
  → digest (sequential profiles) → archive
```

Use `fast` for tutorials, references, manuals, internal guides, docs sites,
MVP drafts — anywhere correctness dominates and reading experience is
important but not the product.

### Nonfiction — `full` (opt-in)

Identical, plus **Reader-POV between the Humanizer and Continuity Guardian
Mode A**. Use `full` when prose quality matters as much as correctness:
customer-facing books, anything with marketing weight. Reader-POV is the only
agent deferred to `full` — its per-unit value is the most uneven for
reference-style material, and the Phase 4 polish pass gives fast-mode
projects a batch Reader-POV read anyway.

### Literary

```
Writer → Editor → Humanizer → Reader-POV → Critic (GATE)
  → [Adversarial Verify, if enabled] → Human review
  → (on approval) Proofreader → Continuity Guardian → digest → archive
```

The Technical Reviewer does not exist in the literary flow. The Continuity
Guardian additionally runs a singularity audit every 5 approved units — see
`references/agents/continuity-guardian.md`.

### Why one Technical Reviewer, not two

The Technical Reviewer audits multiple axes in one pass: **Axis A** (claims,
code, versions — machine-checkable via `references/validation-surface.md`),
**Axis B** (mental models, framings, terminology — checked against
`bible/sources/`), and for `scientific-paper` **Axis C** (reference
integrity: the citation exists, says what it is claimed to say, is not
retracted). All axes measure content correctness against different
references; one agent means one bible read and one report (`tech-review.md`)
for downstream agents. If `bible/sources/` is empty, Axis B runs against
glossary + tracker + scope only, and the report carries an explicit
"grounding library empty — Axis B partial" note that propagates to the human
review packet. Never silent.

---

## Agent contracts

Every agent loads, in this order: (1) its agent file from
`references/agents/`, (2) the profile file from `references/profiles/`,
(3) `bible/meta.yaml`, (4) `bible/voice-profile.md` if it is a prose agent
(Writer, Humanizer, Critic, Continuity Guardian Mode A), then (5) its
contract inputs below. An agent may read more than its inputs (the bible is
always fair game) but writes exactly the artifacts listed — nothing else.

Anti-mediocrity files (`anti-mediocrity-nonfiction.md` /
`anti-mediocrity-literary.md`, per profile) are loaded by Writer, Humanizer,
Critic, and CG Mode A only. Reader-POV and Proofreader deliberately do not
load them — scope discipline.

### Nonfiction contracts

| Agent | Reads (beyond agent file, profile, meta, voice-profile) | Writes |
|---|---|---|
| Writer | style-guide, glossary, scope, sources/, claims-map (paper), outline entry, all digests + most recent final unit, tracker, anti-mediocrity | `drafts/unit-NN/grounding-notes.md` + `drafts/unit-NN/draft.md` |
| Technical Reviewer | draft, grounding-notes, scope, glossary, sources/, claims-map (paper), outline entry, digests, validation-surface | `drafts/unit-NN/tech-review.md` |
| Editor | draft, tech-review (awareness only — see below), outline entry | `drafts/unit-NN/edit.md` |
| Humanizer | edit, tech-review (applies its advisories), style-guide, anti-mediocrity, most recent digest | `drafts/unit-NN/humanized.md` |
| Reader-POV (full) | humanized, outline entry; persona from the profile | `drafts/unit-NN/reader-report.md` |
| CG Mode A | humanized, most recent 1–2 final units, all digests, style-guide, glossary, tracker, anti-mediocrity | `drafts/unit-NN/coherence.md` |
| Critic (gate) | humanized, tech-review, coherence, reader-report (full), style-guide, tracker, rubric, digests, anti-mediocrity | `drafts/unit-NN/critique.md` + `drafts/unit-NN/scorecard.yaml` |
| Adversarial skeptics | humanized + lens-specific inputs — blind to critique and scorecard | `drafts/unit-NN/adversarial-report.md` |
| Proofreader | `final/unit-NN.md` (after human approval) | updates `final/unit-NN.md` in place |
| CG Mode B | `final/unit-NN.md`, tracker, digests | tracker update + audit notes |

### Literary contracts

| Agent | Reads (beyond agent file, profile, meta, voice-profile) | Writes |
|---|---|---|
| Writer | style-guide, characters/, world, plot-structure, arcs, timeline, outline entry, all digests + most recent final unit, tracker, anti-mediocrity-literary | `drafts/unit-NN/draft.md` |
| Editor | draft, outline entry | `drafts/unit-NN/edit.md` |
| Humanizer | edit, style-guide, anti-mediocrity-literary | `drafts/unit-NN/humanized.md` |
| Reader-POV | humanized, outline entry | `drafts/unit-NN/reader-report.md` |
| Critic (gate) | humanized, reader-report, style-guide, tracker, rubric, digests, anti-mediocrity-literary | `drafts/unit-NN/critique.md` + `drafts/unit-NN/scorecard.yaml` |
| Proofreader | `final/unit-NN.md` | updates in place |
| Continuity Guardian | `final/unit-NN.md`, tracker, digests | tracker update + audit notes |

Notes:

- The Writer's **pre-draft grounding pass** (nonfiction) reads
  `bible/sources/` before drafting and emits `grounding-notes.md`. This
  front-loads grounding so the Reviewer verifies citations instead of
  re-deriving them, cutting avoidable Reviewer→Writer loopbacks. If sources/
  is empty or has nothing relevant to the unit, skip the pass with a
  documented note in `grounding-notes.md`.
- The Writer's **self-assessment** travels at the top of `draft.md` as an
  HTML comment: which opening structure from the voice-profile rotation it
  used (the Critic verifies `rhet-6` against it), and — literary — the
  friction inventory per scene. Details in the writer agent files.
- The Editor reads `tech-review.md` only so it does not restructure around
  content the Reviewer flagged for change. It applies none of it. Prose-level
  findings the Editor notices go into `edit.md` as HTML-comment flags for the
  Humanizer, never as silent fixes.
- Voice calibration is **always against `bible/voice-profile.md`**, never
  against neighboring units. Reading the most recent unit is for continuity
  of argument or story — where the reader left off — not for imitating its
  prose. Calibrating against neighbors rewards homogeneity drift.

---

## The Technical Reviewer mini-gate (nonfiction only)

Runs after the Writer, before the Editor. A smaller gate than the Critic:
its only hard-stop loopback target is the Writer.

| Verdict | Action |
|---|---|
| **PASS** | Proceed to Editor. `tech-review.md` carries advisories downstream. |
| **REVISE** | Loopback to Writer with specific instructions. |
| **ESCALATE** | Ask the human — typically a glossary conflict, wrong pinned version, known-wrong source, or (papers) an unverifiable load-bearing citation. |

The Reviewer never loops back to the Editor or Humanizer — they run after it
and consume its report. This keeps the pipeline's one multi-target gate (the
Critic) clean. Reviewer→Writer cycles count against the same retry cap as
Critic cycles.

---

## The Critic gate

The Critic is not a step that passes a deliverable forward; it is a **gate**.
It audits `humanized.md` and emits `critique.md` (template
`templates/critique-report.md`) plus `scorecard.yaml` (template
`templates/scorecard.yaml`).

**The verdict is computed from the scorecard.** The computation rule —
severity counts to PASS / REVISE / REWORK / ESCALATE — lives in
`references/rubric.md` and only there. Do not restate or approximate it in
any other file; two copies of a threshold rule will drift.

| Verdict | Meaning |
|---|---|
| **PASS** | Ready for the human (or Adversarial Verify, if enabled). Minor issues noted, not blocking. |
| **REVISE** | Fixable. Loopback to exactly one named agent, with rationale. |
| **REWORK** | Failed at a level polish cannot rescue. Always → Writer. |
| **ESCALATE** | Above the pipeline's pay grade. Ask the human. |

The `critique.md` header (verdict, loopback target, one-line rationale) is
machine-readable — the orchestrator uses it to decide what runs next.

### Loopback by problem type

The REVISE target is determined by the TYPE of problem, never its severity:

| Type of problem | Loopback target |
|---|---|
| Structure, pacing, section/scene order, within-unit continuity | **Editor** |
| Factual error, broken code, wrong version, terminology drift, mental-model failure, framing | **Writer** (with tech-review findings as input) |
| Voice drift, generic prose, AI-isms, rhythm, rhetoric-budget overruns, dialogue voice | **Humanizer** — in every mode; the Humanizer always exists |
| Target reader confused or bored | **Reader-POV + Humanizer** (full, literary) or **Writer** (fast) |
| Contradicts bible or prior units | **Writer** (with bible/tracker as input) |
| Outline beat not delivered or wrong | **ESCALATE** — the outline is a human-approved artifact; agents do not relitigate it |

### Retry policy

A unit may loop at most `pipeline.retry_cap` times (from `bible/meta.yaml`):
**2** for `fast`, **3** for `full` and literary. The cap counts ALL loopbacks
for the unit — Reviewer→Writer, Critic→any agent, adversarial-confirmed
REVISEs, and human-triggered revisions share one budget.

On cap hit, do NOT emit a vague "ask the human". Produce the structured
escalation packet in `references/loopback-handoff.md`: per-cycle diff,
failure-pattern diagnosis, three concrete options, recommended pick. The
unit pauses until the human chooses; then `retries.by_unit[unit-NN]` resets
to 0 (the chosen path is a fresh attempt).

---

## Adversarial Verify (optional slot)

Config: `pipeline.adversarial_verify: off | gate_critical | every_unit |
every_N` (default `off`; `every_N: 3` recommended for long projects). When
active, it runs **after a Critic PASS and before human review** — never on a
failing unit.

Three skeptics run in parallel, **blind to the Critic's verdict and
scorecard**, each with one lens: (a) profile/register compliance,
(b) correctness/grounding, (c) reader experience. Their mandate is to refute
the unit. A finding confirmed by ≥2 skeptics converts the PASS into a REVISE
toward the appropriate loopback target (counts against the retry cap);
single-skeptic findings ride into the human packet as observations. Output:
`drafts/unit-NN/adversarial-report.md`. Full protocol:
`references/adversarial-verify.md`.

The slot exists because a gate that always approves in one voice develops
blind spots; independent skeptics with a refutation mandate have repeatedly
caught problems a PASS had waved through.

---

## Continuity Guardian — two modes

- **Mode A — pre-gate coherence (nonfiction).** Before the Critic, reads
  `humanized.md` against `bible/voice-profile.md`, the most recent 1–2
  approved units, and all digests. Flags voice drift from the profile,
  terminology drift, heading/notation/format inconsistency with what the
  reader has already seen. Writes `coherence.md`. Advisory only — it does not
  update the tracker; the Critic folds its findings into the scorecard
  (voice drift → Humanizer target; glossary/terminology drift → Writer).
- **Mode B — post-approval tracker.** After the Proofreader, on the approved
  `final/unit-NN.md`: updates `bible/continuity-tracker.md` and runs the
  scheduled cross-unit audit. Literary adds the every-5-units singularity
  audit here. Mode B never touches drafts.

The split matters: Mode A protects the reader's experience of consistency
*before* the gate; Mode B keeps the project's memory accurate *after* the
decision. Merging them tempts the Guardian to edit — which is not its job.

---

## Digests

Past unit 4–5 of a sequential project, re-reading every prior unit on every
turn is context bloat. After approval (post-Proofreader, post-Mode B, before
archiving), produce a 300–500-word structured digest per
`references/chapter-digest.md` into `bible/digests/`.

Policy by sequence type (declared in the profile):

| Sequence | Profiles | Digest policy |
|---|---|---|
| linear | book-technical, book-literary | Full digest per unit |
| linear-light | corporate-guide | Full digest per unit — units open self-contained, but terminology and decisions still accumulate |
| modular | product-docs | **No digests.** Articles are standalone; cross-article consistency is the KG terminology layer + the Phase 4 audit |
| imrad | scientific-paper | Short claims-state digest per section: claims introduced, evidence status, what downstream sections may rely on |

Who reads digests vs. full prior units:

| Agent | Digests | Full prior units |
|---|---|---|
| Writer | All | Most recent only (continuity, not voice) |
| Technical Reviewer | All | Most recent only, if a terminology audit needs it |
| Editor | — | — |
| Humanizer | Most recent | — (voice comes from voice-profile.md) |
| Reader-POV | — | — (cold-read simulation) |
| CG Mode A | All | Most recent 1–2 |
| Critic | All | — (`coherence.md` carries cross-unit findings) |
| CG Mode B | All | All finals, on scheduled audits only |

Digests freeze at approval. Disable globally with
`pipeline.chapter_digest.enabled: false` for short projects.

## Archiving

After approval + Proofreader + Mode B + digest, move `drafts/unit-NN/` to
`drafts/_archive/unit-NN/`. Re-open handling, timestamped re-archives, and
the disable flag are in `references/archiving.md`.

---

## Runs log

After each agent run, the **orchestrator** (the session driving the
pipeline — never the agents themselves) appends one line to
`project-status.yaml → runs`:

```yaml
- [unit-07, writer, creative, 2, 2026-07-03T14:02Z]
#  unit     agent   tier      cycle timestamp
```

That is the entire contract. Token accounting is deliberately absent: richer
per-call token rows proved unenforceable — they were specified and never
reliably populated, producing a log that looked like observability but
wasn't. A minimal log that actually gets written beats a detailed one that
is fiction. The log feeds the retry summary in the human packet and lets the
human spot roles that loop repeatedly or are not earning their tier.

---

## Model tiers

`bible/meta.yaml → models` maps roles to **tiers**, never to model IDs:

```yaml
models:
  tiers:
    creative: inherit    # inherit = whatever model this session runs
    audit: inherit
  roles:
    writer: creative
    critic: creative
    humanizer: audit     # literary projects: creative — voice is the product
    default: audit
```

Resolution: look up the agent in `models.roles` (recognized keys: `writer`,
`technical_reviewer`, `editor`, `humanizer`, `reader_pov`, `critic`,
`continuity_guardian`, `proofreader`, `adversarial`; fall back to
`roles.default`) → that names a tier → `models.tiers.<tier>` resolves to
`inherit` (session model) or an explicit model ID.

Set an explicit ID on a tier only when the human wants cost control — e.g.,
a cheaper model on `audit` after a few units show the audit roles don't need
the heavyweight one. Never write model IDs into skill references, templates,
or agent instructions: model names churn, and a skill with IDs scattered
through it rots in months. The tier indirection is the single place IDs may
appear, and only in the project's own `meta.yaml`.

---

## Human review (the real gate)

A Critic PASS does not ship a unit. Present to the human, together:

- **The unit text** — `drafts/unit-NN/humanized.md`, always. The Critic
  gated this exact text; the human reviews the same.
- **The computed verdict** from `critique.md`, plus the failing scorecard
  items from `scorecard.yaml` with their `evidence` fields. The scorecard is
  the load-bearing artifact — the human reviews a checklist, not a narrative.
- **The Critic's Observations** — non-rubric notes worth flagging.
- **`tech-review.md`** (nonfiction), with any skipped-check or
  partial-grounding notes made explicit — never silent.
- **`coherence.md`** and, when it ran, **`reader-report.md`**.
- **`adversarial-report.md`** if the slot ran.
- **Retry summary**: cycles used, target per cycle, what changed — from
  `project-status.yaml → retries` and the unit's `runs` lines.

The human has three responses:

- **Approve** → Proofreader → Continuity Guardian Mode B → digest
  (sequential profiles) → archive. The unit lands in `final/unit-NN.md`.
- **Reject with notes** → routed to the agent the human names (Writer by
  default). Counts against the retry cap; the counter resets only via the
  cap-hit escalation packet.
- **Defer** → unit stays in draft; nothing runs automatically.

Do not gate approval on a green scorecard. It is decision support, not
authority: the human may approve over `significant` fails (record the
rationale in the approval note) and may reject a PASS with a free-form note
that becomes the next cycle's instruction.

---

## Polish pass (Phase 4, nonfiction)

A batch pass over already-approved units, run in Phase 4 after the
full-manuscript audit and Proofreader steps. Default: enabled for `fast`
mode, ignored for `full` (Reader-POV already ran per unit), never for
literary (its per-unit pipeline already carries both agents). Skip when fewer
than 3 units were approved since the last run — the cross-unit signal is too
thin.

Disabling it with `pipeline.polish_pass.enabled: false` requires a `waivers`
entry in `project-status.yaml`. In `fast` mode this pass is Reader-POV's only
per-batch appearance, so switching it off silently means a book gets written
without ever being read as a reader — which is exactly what happened once, for
three months, while the project reported itself finished. The whole-book read at
the Phase 4.5 gate still runs regardless; it is not skippable, and it is not a
substitute for this one (batch reading catches tics and pacing; the whole-book
read catches exposition order and sufficiency).

Why it exists: in `fast` mode this is Reader-POV's first read; and the
per-unit Humanizer sees one unit at a time, so a tic appearing once per unit
passes as `minor` each time while being a `significant` pattern across four
units — visible only at batch level (same for emphasis density, signposting
cadence, synonym cycling on load-bearing terms).

For each batch of 3–4 approved units (consecutive for sequential profiles;
for `product-docs`, a cluster of related articles by tag or topic):

1. **Reader-POV, batch mode** — reads the batch as one continuous read using
   the profile's persona; loads meta and the batch's outline entries, no
   digests (fresh-reader simulation). Flags units that drag, concepts that
   were supposed to land earlier and didn't, batch-level pacing. Output:
   `drafts/_polish/batch-NN-MM/reader-report.md`.
2. **Humanizer, batch mode** — reads the batch + the batch reader report +
   style-guide + voice-profile + anti-mediocrity-nonfiction. Re-runs its
   checklist with cross-unit awareness. Output: proposed line-level edits as
   a unified diff, `drafts/_polish/batch-NN-MM/proposed-edits.diff`.

**Edits are proposed, never applied.** The human reviews the diff:
accept-all, partial, or reject. Accepted edits update `final/unit-NN.md` in
place; CG Mode B re-runs on any changed unit. Digests are NOT regenerated —
they are writing-time calibration artifacts and the writing is done.

**After any accepted edit, run `python scripts/validate_claim_index.py`.** Its
`PROPAGATE` lines go into the same packet as the diff, so the person who just
accepted an edit sees immediately which sibling passages it orphaned. This is the
step whose absence produced three separate incomplete fixes in one project, the
longest surviving seventeen days and a full audit — nobody knew the edited
passage had siblings. See `references/claim-index.md`.

The pass does not re-run the Critic (the units are approved; this is voice
and pacing, not a gate) and does not touch the KG, glossary, or scope —
vocabulary changes are the human's call. If the human's acceptance rate
drops below ~30% across a few batches, the pass is generating noise: tighten
the trigger to 5+ units or disable it for this project.

---

## See also

- `references/rubric.md` — scorecard schema and the authoritative verdict
  computation.
- `references/validation-surface.md` — Axis A/C machine checks.
- `references/adversarial-verify.md` — skeptic protocol.
- `references/loopback-handoff.md` — cap-hit escalation packet.
- `references/chapter-digest.md`, `references/archiving.md` — post-approval.
- `references/agents/continuity-guardian.md` — Mode A/B detail, singularity
  audit, Phase 4 full-manuscript audit.
- `references/manuscript-gate.md` — **Phase 4.5**, which fires automatically
  when the last unit is archived. Nothing in this file gates the book; it gates
  units. The gate is there.
- `references/claim-index.md` — the propagation warning that runs after any
  edit to an approved unit.
