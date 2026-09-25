# Pipeline specification

The authoritative spec of Phase 3: execution model, agent order, input/output
contracts, gates, loops, retries, digests, logging, and the batch passes. If
another file disagrees with this one on order, inputs or artifact names, this
file wins — report the conflict. History and measurements:
`docs/rationale/pipeline.md`.

## Execution model

The **orchestrator** is the session running the skill. It dispatches every
agent as a **subagent** (Agent/Task tool) and never drafts unit prose itself.
Each dispatch carries:

```
Role:    references/agents/<file>.md            (read first)
Profile: references/profiles/<profile>.md
Inputs:  <the exact list from the contract table below — nothing else>
Write:   <output path(s)>
Model:   models.roles.<role> → models.tiers.<tier> (inherit = no override)
```

**Isolation.** Reviewers are only independent if their context is.

| Must run isolated, closed input list | Should run as subagents |
|---|---|
| Critic · Reader-POV (every mode) · adversarial skeptics and refuters · concept and rule auditors (Phase 4.5) · Continuity Guardian Mode A | Writer · Technical Reviewer · Editor · Humanizer · Proofreader · Continuity Guardian Mode B |

An isolated agent receives only its listed inputs — never the orchestrator's
conversation, other reviewers' reports it is not listed for, or the drafts'
history. **Cold readers** (Reader-POV, adversarial skeptics) read
`drafts/unit-NN/humanized.clean.md`, never `humanized.md`: run
`python scripts/pipeline_step.py clean unit-NN` after every write to
`humanized.md`.

**Dispatch brackets**, around every agent run:

```bash
python scripts/pipeline_step.py check unit-NN <agent>     # non-zero → do not dispatch; fix the input
# … dispatch …
python scripts/pipeline_step.py done unit-NN <agent> --tier <t> --cycle <n>
```

A successful `check` records the dispatch time
(`drafts/unit-NN/.dispatch.json`); `done` accepts only outputs written after
it, so a stale critique, report or tracker cannot pass for new work. On a loop
pass `--cycle N` to both (§ Loops). `check critic` and `check proofreader`
also need `checks.json`, `coherence.md` and (literary, nonfiction `full`)
`reader-report.md` newer than `humanized.md`, and refuse while `checks.json →
blocking` holds a story block (`check critic`: or `errors` a failed tool). `check proofreader` further requires the
Critic's PASS — recomputed from `scorecard.yaml` and matching `critique.md` —
with no newer confirmed adversarial finding; `--human-override` (the human
approved over a red scorecard) turns a non-PASS verdict into a note, never a
story block.

`done` verifies the output exists, is non-empty, not `null` and fresh, appends
`runs.tsv`, and (editor, humanizer, proofreader) writes
`drafts/unit-NN/role-diff-<agent>-c<N>.json`: first pass `draft.md → edit.md`
(Editor) and `edit.md → humanized.md` (Humanizer); on an Editor/Humanizer loop
cycle, the cycle's `humanized.c<N>.md` snapshot → `humanized.md`; the
Proofreader `humanized.md → proofread.md`. `done critic` recomputes the
verdict from the rows (`references/rubric.md`). Exit codes:

| `done` exit | Meaning | Orchestrator |
|---|---|---|
| `0` | ok | next agent |
| `1` | output missing, empty, `null`, stale, or no dispatch record | re-dispatch once (run `check` first); a second failure → stop and tell the human |
| `3` | literary Writer: `ready` fails (R3) or a story blocker on the page (R4) | pause the unit (§ Orders) |
| `4` | contract violation: the Editor added prose, the Proofreader made a non-mechanical change, the Critic's header disagrees with its rows | re-dispatch that agent once with the violation list; a second `4` in the same cycle → escalate |

Never gate on a missing artifact. Agent names: `writer`, `technical_reviewer`,
`editor`, `humanizer`, `reader_pov`, `continuity_a`, `critic`, `adversarial`,
`proofreader`, `continuity_b`, `digest`. `done continuity_b` also needs
`bible/story-ledger.yaml` updated when the unit's cards plant or pay. Why:
`docs/rationale/pipeline.md#freshness`.

**Script counts before the Critic:** `python scripts/pipeline_step.py checks
unit-NN` writes `drafts/unit-NN/checks.json` + `checks.md`. Top-level keys of
`checks.json`: `unit`, `profile`, `source`, `source_sha1`, `generated_utc`,
`language`, `pack`, `words`, `notes`, `counts` (`count_rhet.py`, one entry per
item: `counts.rhet-2`, `counts.ai_vocab`, `counts.weasels`,
`counts.em_dash_narration`, `counts.sentence_length`, …), `identifiers`
(`check_identifiers.py`, nonfiction: `identifiers.unknown`), `fiction`
(`lint_fiction.py --unit`, literary: `fiction.findings`, info dropped),
`story` (`check_story.py --unit`, literary: `story.findings`,
`story.context.arcs_resolving_here`, `story.context.is_final_unit`, …),
`tics` (literary: `tics.gestures`, `tics.over_quota`, `tics.repeated_ngrams`),
`role_diff` (`role_diff.<agent>` = the latest role diff of the Editor,
Humanizer, Proofreader: `touched_ratio`, `over_budget`, `violations`, …),
`blocking` (story blockers) and `errors` (a tool that failed). A key that does
not apply is `null`. Exit `2` = a tool failed (never gate on it); exit `3` = a
story blocker (R1–R4): the unit pauses before the Critic. Agents copy these
numbers; they never recount. `check … critic` and `check … proofreader` refuse
a `checks.json` whose `source_sha1` is not the current `humanized.md`'s (re-run
`checks`), whatever its mtime, and re-run the story check live on
`humanized.md`.

**Cross-model.** With `pipeline.adversarial_verify.cross_model: true`, the
refutation passes (`references/adversarial-verify.md`) and the manuscript
gate's MG-4 read go to a second model when a tool for one is available (a
Codex MCP tool, the `debate` skill, or equivalent). Otherwise the human packet
says "cross-model unavailable".

## Invariants

- **The Critic gates `humanized.md`**, every mode, every profile.
- **The Humanizer runs every unit.** It alone applies prose fixes and
  Technical Reviewer advisories.
- **The Editor is structural only**: `check_role_diff.py` fails it when it adds
  prose beyond transitions.
- **Verdicts are computed** (`references/rubric.md`); counts come from
  `checks.json`.
- **The human approves the text that ships**: the Proofreader runs before human
  review, and its diff is in the packet.

## Orders

`pipeline.mode` selects `fast` (default) or `full` for nonfiction.
`book-literary` has one flow.

```
Nonfiction fast:
  Writer → Technical Reviewer → Editor → Humanizer → CG Mode A → checks
  → Critic → [Adversarial] → Proofreader → Human review
  → (approve) pipeline_step.py approve → CG Mode B → digest → archive
Nonfiction full: fast + Reader-POV after the Humanizer.
Literary:
  [ready gate passed once] Writer (scene by scene) → Editor (assembly)
  → Humanizer → Reader-POV → CG Mode A (literary) → checks → Critic
  → [Adversarial] → Proofreader → Human review
  → (approve) pipeline_step.py approve → CG Mode B → digest (literary template)
  → reader-journal update → archive
```

`[Adversarial]` runs only after a Critic PASS, per
`pipeline.adversarial_verify.mode`. `corporate-guide` and `product-docs` may add
reader testing after the Humanizer (profile file, `pipeline.reader_testing`).

**Literary readiness gate.** Before the first unit is drafted (`phase:
drafting`), `python scripts/pipeline_step.py ready` must exit 0: every character
in the outline has a complete sheet with an arc, signed by the human through
`python scripts/pipeline_step.py sign <slug> --by <human>` (`signed_hash`
still matching), `bible/plot-structure.md` defines the ending,
`bible/story-ledger.yaml` exists and is well formed, and the seeds and human
calibration passages exist; the outline is approved first (`project-status.yaml
→ outline.approved`). The same full `ready` is re-checked by `check … writer`
and `done … writer` for EVERY unit, by `approve` and by `apply-edits`: a unit
whose own cast is complete still waits while anything in the book's design is
not. Blockers go to the human through `references/character-questionnaire.md`.
**New character mid-book** (exit `3` from `done … writer` or `checks`;
`NEW-CHARACTER` — a name mid-sentence, one that is no common word and never
lowercase, sentence-initial included, or one in a speaker/actor position;
`EXTRA-PROMOTE` — any `world.md` word (a name or a place), outline location or
extra's label word that speaks or acts; `CHAR-UNKNOWN` — a name in
`characters_present` or in a scene card that no sheet knows; a Writer request;
`check … writer` exits 1 on the outline cases): the unit pauses. **Triage first, one question per flagged token:**
ask the human whether it is a person. Not a person (a first-person verb or a
rare word opening a sentence) → add it to `bible/lexicon.yaml →
common_words` and re-run the step; the questionnaire does not run. A real
public figure seen from a distance — on a screen, in the news, in a memory —
who never shares a scene with the characters (the human decides, never the
agent) → `bible/lexicon.yaml → non_person_names`, re-run. A person in the
story →
the questionnaire runs for that character, sheet,
arcs, outline and story ledger are updated and signed, and the unit restarts
at the Writer with its retry counter reset — a design change, not a failed
cycle. The Writer never invents a named character. **Story blocks (R1–R4) are
never overridable**: not by the Critic, a human approval, `--human-override`,
`approve --force`, or a gate waiver.

## Contracts

Every agent loads its agent file, the profile, `bible/meta.yaml`, and — prose
agents (Writer, Humanizer, Critic, CG Mode A) — `bible/voice-profile.md`, then
the inputs below. It writes exactly the listed artifacts.

### Nonfiction

| Agent | Reads | Writes |
|---|---|---|
| Writer | style-guide, glossary, scope, knowledge-graph, sources/, claims-map (paper), outline entry, all digests + most recent final unit (continuity only), tracker, examples-library, anti-mediocrity-nonfiction; on a loop: the worklist (§ Loops) | `grounding-notes.md`, `draft.md` |
| Technical Reviewer | draft, grounding-notes, scope, glossary, knowledge-graph, sources/, claims-map (paper), outline entry, digests, validation-surface, `identifiers.json` (it runs `check_identifiers.py --unit unit-NN --file drafts/unit-NN/draft.md --json drafts/unit-NN/identifiers.json`; the index is built at setup with `--build-index`) | `tech-review.md` |
| Editor | draft (or `humanized.md` on a loop), tech-review § Notes → Editor, outline entry | `edit.md` (loop: patches `humanized.md`) |
| Humanizer | edit (or `humanized.md` on a loop), tech-review, style-guide, glossary, anti-mediocrity-nonfiction, most recent digest | `humanized.md` |
| Reader-POV (full) | `humanized.clean.md`, outline entry `purpose`, persona from the profile, previous final (sequential) | `reader-report.md` |
| CG Mode A | humanized, most recent 1–2 finals, digests, style-guide, glossary, tracker, anti-mediocrity-nonfiction | `coherence.md` |
| Critic | humanized, draft (self-assessment comment only), checks.json + checks.md, tech-review, coherence, reader-report (full), reader-test (if run), outline entry, style-guide, glossary, tracker, claims-map (paper), digests, `rubric.md` + `rubric-nonfiction.md`, anti-mediocrity-nonfiction | `critique.md`, `scorecard.yaml` |
| Adversarial skeptics | `humanized.clean.md` + lens inputs — blind to every report | `adversarial-report.md` (merged) |
| Proofreader | humanized, style-guide, glossary, one or two finals | `proofread.md` |
| CG Mode B | `final/unit-NN.md`, tracker, digests | tracker update + audit notes |

### Literary

| Agent | Reads | Writes |
|---|---|---|
| Writer | style-guide, characters/ (sheets for `characters_present`) + `_extras.md`, world, plot-structure, arcs, timeline, story-ledger, outline entry (scene cards), literary digests + most recent final unit (continuity only), tracker, anti-mediocrity-literary; on a loop: the worklist | `draft.md` (scenes marked `<!-- SCENE s1 -->`); key scenes also `key-sN-vK.md` — the human picks, the orchestrator swaps the pick into `draft.md` before the Editor |
| Editor | draft (or `humanized.md` on a loop), outline entry | `edit.md` — assembly, order, transitions; no new prose (loop: patches `humanized.md`) |
| Humanizer | edit (or `humanized.md` on a loop), style-guide, anti-mediocrity-literary | `humanized.md` |
| Reader-POV | `humanized.clean.md`, `bible/reader-journal.md`, the previous `final/` unit, the pairwise benchmark named in the journal's `Benchmark:` line (attached by the orchestrator), persona — **no outline** | `reader-report.md` incl. its journal entry |
| CG Mode A (literary) | humanized, outline entry, sheets of `characters_present` + `_extras.md`, world, timeline, tracker, story-ledger, literary digests, most recent 1–2 finals | `coherence.md` (continuity + facts lane) |
| Critic | humanized, draft (self-assessment only), checks.json + checks.md, reader-report, coherence, outline entry, characters/, arcs, plot-structure, story-ledger, style-guide, tracker, digests, `rubric.md` + `rubric-literary.md`, anti-mediocrity-literary | `critique.md`, `scorecard.yaml` |
| Adversarial skeptics | `humanized.clean.md` + lens inputs | `adversarial-report.md` |
| Proofreader | humanized, style-guide, characters/ (names) | `proofread.md` |
| CG Mode B | `final/unit-NN.md`, tracker, story-ledger, digests | tracker + ledger update |

Notes:

- **Grounding pass** (nonfiction): the Writer reads `bible/sources/` before
  drafting and writes `grounding-notes.md`; skipped with a note when nothing
  relevant exists.
- **Self-assessment** travels as an HTML comment **at the end of `draft.md`**:
  declared opening structure (nonfiction), grounding summary, open questions;
  literary per `references/agents/writer-literary.md`.
- **Editor and advisories**: the Editor reads the Reviewer's structural notes
  only and applies none of its advisories; prose issues it notices become
  `<!-- FOR HUMANIZER -->` flags.
- **Voice calibration is always against `bible/voice-profile.md`**, never
  against neighbouring units. Prior units are read for continuity only.

## Technical Reviewer mini-gate (nonfiction)

After the Writer, before the Editor. `PASS` → Editor (advisories ride
downstream). `REVISE` → Writer. `ESCALATE` → human (glossary conflict, wrong
pinned version, known-wrong source, unverifiable load-bearing citation). It
never loops to the Editor or Humanizer. Its cycles share the retry cap.

## The Critic gate

The Critic audits `humanized.md` and writes `scorecard.yaml` and `critique.md`.
Verdicts `PASS | REVISE | REWORK | ESCALATE` are computed per
`references/rubric.md` — nowhere else; `done critic` recomputes them from the
rows and exits `4` when the header disagrees. The orchestrator routes on
`## Verdict:` and `## Loopback target:`. **ESCALATE** is not a loop: produce the
escalation packet (`references/loopback-handoff.md`), set the unit `on_hold`
in `project-status.yaml`, and wait for the human's decision.

Routing is by **problem type**, carried by each rubric row's target:

| Problem | Target |
|---|---|
| Structure, order, pacing (nonfiction), within-unit continuity of placement | Editor |
| Facts, code, versions, framing, missing content, contradiction with bible or prior units | Writer |
| Voice, generic prose, AI-isms, rhythm, rhetoric overruns, unapplied advisories, nonfiction clarity | Humanizer |
| Humanizer over budget (`voice-8` / literary `voice-6`) | Writer |
| Literary comprehension, "would close the book" | Writer; literary pacing → Editor |
| The outline itself is wrong; a named character without a complete sheet | `escalate` |

## Loops

Loopback targets are exactly `Writer | Editor | Humanizer | escalate`.

1. **Snapshot first**, before every loopback, whatever the target:
   `python scripts/pipeline_step.py snapshot unit-NN --reason
   critic|tr|adversarial|human [--target writer|editor|humanizer]` closes cycle
   N: it copies whatever exists of `humanized.md`, `draft.md`, `edit.md` and
   `scorecard.yaml` to `<name>.c<N>` (the plateau rule compares the
   scorecards) and opens cycle N+1 in `drafts/unit-NN/loop-state.json` —
   reason, target (default: the critique's `## Loopback target:`, the
   adversarial report's, else Writer), worklist, and the Writer's REVISE
   source. A Critic ESCALATE is refused (§ The Critic gate). Every agent of
   the new cycle runs `check` and `done` with `--cycle N+1`.
2. **Worklist.** Every target reads `critique.md` § Specific loopback
   instructions plus the failing rows, and the report of the loop's reason:
   `critique.md` (critic), `tech-review.md` (tr), `adversarial-report.md`
   (adversarial), `drafts/unit-NN/human-notes.md` (human — the orchestrator
   appends the dated notes there). `check <target> --cycle N+1` refuses a
   missing worklist or one older than that agent's previous dispatch.
3. **Re-entry.**

   | Target | Input → output | What re-runs after |
   |---|---|---|
   | Writer, REVISE | the source `check writer --cycle N+1` names → new `draft.md` = that text with targeted fixes only | the whole chain, first-pass contracts (Editor `draft → edit`, Humanizer `edit → humanized`) |
   | Writer, REWORK | outline + critique → fresh `draft.md` | the whole chain |
   | Editor / Humanizer | patches `humanized.md` in place | Reader-POV (literary always; nonfiction if a `reader_pov` row failed) → CG Mode A → checks → Critic |

   **Writer REVISE source**: the snapshot of the latest text
   (`humanized.c<N>.md`, or `draft.c<N>.md` when the loop re-entered before
   the Humanizer existed). When the cycle broke a role contract — Humanizer
   over budget (`voice-6` / `voice-8`, `role_diff.humanizer.over_budget`) or
   an Editor violation — it is the last text **before** the violating agent:
   `edit.c<N>.md` (Humanizer) or `draft.c<N>.md` (Editor), so the violation
   is not carried into the next draft.

   `check_role_diff.py` (via `done`) verifies the Editor added no prose and
   measures the Humanizer's touched ratio on every pass, first or loop.

   **Technical Reviewer REVISE** (nonfiction, before any Humanizer run):

   ```bash
   python scripts/pipeline_step.py snapshot unit-NN --reason tr     # draft.c1.md; cycle 2 opens
   python scripts/pipeline_step.py check unit-NN writer --cycle 2   # names draft.c1.md + tech-review.md
   # Writer → new draft.md + grounding-notes.md, then: done unit-NN writer --tier T --cycle 2
   # technical_reviewer, editor, humanizer: check/done --cycle 2 (first-pass inputs)
   ```
4. **Plateau rule.** If a cycle resolves none of the previous cycle's failing
   rows (same or larger failing set, compared against `scorecard.c<N>.yaml`),
   stop and produce the escalation packet now, whatever budget remains.
5. **Retry cap**: `pipeline.retry_cap` — 2 `fast`, 3 `full` and literary. One
   budget for Reviewer→Writer, Critic→any, confirmed adversarial findings and
   human rejections. On cap or plateau: `references/loopback-handoff.md`.

## Adversarial verify

Optional, after a Critic PASS, before the Proofreader. Three blind skeptics
with one lens each; a finding is confirmed by two skeptics or by a refutation
pass that upholds it; confirmed non-minor findings force a REVISE (counts
against the cap). Protocol: `references/adversarial-verify.md`.

## Continuity Guardian — two modes

- **Mode A (pre-gate, isolated).** Nonfiction: voice drift from the profile,
  terminology, notation and format drift against recent finals and digests.
  Literary: continuity against tracker, timeline, world and sheets, plus the
  facts lane when `literary.fact_check: realistic`. Writes `coherence.md`;
  never edits; the Critic folds it into rows.
- **Mode B (post-approval).** On `final/unit-NN.md`: updates the tracker (and,
  literary, the story ledger) and runs scheduled audits. Never touches drafts.

Details: `references/agents/continuity-guardian.md`.

## Human review

The packet is short; full reports are linked, not pasted.

**Nonfiction**: the text that ships (`drafts/unit-NN/proofread.md`); the
Proofreader's changed sentences (`role-diff-proofreader-c<N>.json →
changes`); the verdict, most important problem and failing rows with evidence;
the Critic's Observations; every non-silent skip (Axis B/C partial, UNVERIFIED
references, cross-model unavailable, validation surface empty); the adversarial
consolidation table; reader-test gaps (if run); the retry summary (from
`runs.tsv` and the critique headers).

**Literary**: the text that ships and the Proofreader's changes; the 3 most
singular and 3 most generic passages (Critic Observations); tic counts and
story-ledger/arc status from `checks.md`; the reader-journal entry for this
chapter (and whether last chapter's predictions came true); 1–3 decisions for
the human (key-scene pick, facts-lane questions, new characters). Verdict rows
only when not PASS.

Responses: **approve** (even over a red scorecard — record why in
`human-notes.md` — but **never over a story block**: R1–R4 are not
overridable) → `python scripts/pipeline_step.py approve unit-NN` copies
`proofread.md` to `final/unit-NN.md` with HTML comments stripped (nonfiction
keeps `SOURCE`/`ARTIFACT` markers; it refuses a `proofread.md` older than
`humanized.md` and, literary, a failing `ready` or any blocking
`check_story.py --unit` finding on `proofread.md`, `--force` included) → CG
Mode B → digest → (literary) append
the Reader-POV journal entry to `bible/reader-journal.md` → archive. Never copy
by hand.
**Reject with notes** → dated entry in `human-notes.md`, routed to the agent
the human names (Writer by default), counts against the cap. **Defer** →
nothing runs.

## Digests

After approval, CG Mode B, then the digest (orchestrator, bracketed as agent
`digest`) into `bible/digests/`: `references/chapter-digest.md`, template
`templates/chapter-digest.md` (nonfiction) or
`templates/chapter-digest-literary.md`. No voice samples — the Writer must not
calibrate against neighbours.

| Sequence | Profiles | Policy |
|---|---|---|
| linear | book-technical, book-literary | Full digest per unit |
| linear-light | corporate-guide | Full digest; units still open self-contained |
| modular | product-docs | No digests (frontmatter + KG terminology) |
| imrad | scientific-paper | Claims-state snapshot per section |

| Agent | Digests | Full prior units |
|---|---|---|
| Writer | All | Most recent only — continuity, not voice |
| Technical Reviewer | All | Most recent, when a terminology audit needs it |
| Editor, Reader-POV, Proofreader | — | — |
| Humanizer | Most recent | — |
| CG Mode A | All | Most recent 1–2 |
| Critic | All | — |
| CG Mode B | All | All, on scheduled audits only |

Disable with `pipeline.chapter_digest.enabled: false` for short projects.

## Archiving

After the digest (and reader-journal update), move `drafts/unit-NN/` to
`drafts/_archive/unit-NN/`: `references/archiving.md`.

## Runs log

`runs.tsv` at the project root, one line per agent run, written **only** by
`pipeline_step.py done`: `unit agent tier cycle timestamp_utc output_bytes`.
It feeds the retry summary. `project-status.yaml` keeps phase, retries and
waivers, not the log.

## Model tiers

`models.roles.<role>` names a tier; `models.tiers.<tier>` is `inherit` (session
model, no override) or a model ID. Role keys: `writer`, `technical_reviewer`,
`editor`, `humanizer`, `reader_pov`, `critic`, `continuity_guardian`,
`proofreader`, `adversarial`; anything else → `roles.default`. Model IDs live
only on a project's tiers, never in skill files.

## Batch passes over approved units

Edits proposed by a batch pass are **anchor edits**, never unified diffs:
`proposed-edits.yaml` = `[{unit, find, replace, rule}]`, each `find` matching
exactly once in `final/unit-NN.md`. The human accepts all, some or none; then
`python scripts/pipeline_step.py apply-edits <file> --dry-run`, then without
`--dry-run`. A batch with any non-matching `find` fails whole. Literary: the
batch also fails whole — nothing written — when `ready` fails or any edited
unit, as it would be written, carries a story block (`check_story.py --unit`
blocking, `lint_fiction.py` `unknown_name` major or `mentioned_on_stage`).

### Polish pass

Nonfiction, Phase 4. On by default in `fast`, ignored in `full`. Per batch of
3–4 approved units (consecutive; product-docs: a tag cluster): Reader-POV batch mode reads the finals as a reader (HTML comments
ignored, no digests) → `drafts/_polish/batch-NN-MM/reader-report.md`; the
Humanizer, batch mode (`references/agents/humanizer-nonfiction.md` § Batch
mode), proposes cross-unit fixes (a tic once per unit is a pattern across
four) → `proposed-edits.yaml`. Skip when fewer than 3 units were
approved since the last batch. Disabling it needs a `waivers` entry. Acceptance
below ~30% across batches means noise: widen the trigger or turn it off.

### Tic pass

Literary, every `literary.tic_pass_every` approved chapters and once over the
tail in Phase 4:

```bash
python scripts/lint_fiction.py --book --json drafts/_polish/tics-NN/lint.json
```

Then the Humanizer (literary,
batch mode — `references/agents/humanizer-literary.md` § Tic pass) proposes
`proposed-edits.yaml` for gesture tics, repeated n-grams, paragraph openers and
opening repeats across chapters.

### Fix-then-verify

Every accepted fix batch (polish, tic, gate fix pass, late edit):

1. apply the edits;
2. nonfiction: the Technical Reviewer in fix-verify mode over the changed spans
   only (`references/agents/technical-reviewer.md` § Fix-verify mode) →
   `fix-verify.md` beside the edits file; literary: `lint_fiction.py --unit`
   and `check_story.py --unit` on each changed unit;
3. `python scripts/validate_claim_index.py` (claim-index projects) — its
   `PROPAGATE` lines go to the human with the result;
4. CG Mode B on each changed unit. Digests are not regenerated.

A fix is closed only after step 2 passes. Why:
`docs/rationale/pipeline.md#fix-regressions`.

## See also

`references/rubric.md` · `references/adversarial-verify.md` ·
`references/loopback-handoff.md` · `references/chapter-digest.md` ·
`references/archiving.md` · `references/manuscript-gate.md` (Phase 4.5 — the
book-level gate; this file gates units) · `references/claim-index.md`.
