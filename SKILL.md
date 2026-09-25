---
name: book-factory
description: >
  End-to-end long-form document creation with a multi-agent, source-grounded
  writing pipeline. Five profiles: technical books, literary fiction, internal
  corporate guides, product documentation / knowledge bases, and scientific
  papers. Use whenever the user wants to write, continue, or manage any
  structured multi-part document — book, novel, manual, tutorial, memoir,
  internal guide, handbook, docs site, runbook collection, or paper. Triggers:
  "write a book", "book project", "start a story", "technical manual",
  "corporate guide", "documentation project", "knowledge base", "scientific
  paper", "write a paper", "book-factory", "empezar un libro", "escribir una
  novela", "guía corporativa", "paper científico", or any project directory
  with bible/meta.yaml. Use it even when the user never says "book" — anything
  multi-unit and structured (chapters, articles, sections) written across
  sessions belongs here. Do NOT trigger for summaries or reviews of others'
  works, or for single short documents.
---

# Book Factory v3 — Multi-Agent Writing Framework

The human is the creative director: agents draft, review and gate, never
decide content direction. Do not load `CHANGELOG.md` or `docs/` in normal
operation — they are history, not instructions.

## Core principles

1. **The human approves every phase transition.** The Critic can block a unit;
   only the human approves one.
2. **Grounding before prose.** Nonfiction claims trace to the source library.
3. **One voice per project**: `bible/voice-profile.md`. Skill files carry rules
   and BAD examples only.
4. **Counted means counted by a script.** Rhetoric, identifiers, tics and role
   diffs come from `scripts/` into `checks.json`; agents copy numbers, never
   recount. Verdicts are computed from the scorecard (`references/rubric.md`).
5. **Isolation makes review independent.** Critic, Reader-POV, skeptics and
   auditors run as isolated subagents with a closed input list; cold readers
   see clean text.
6. **Roles do not overlap.** Each agent owns one slice and flags the rest via
   HTML comments; role diffs are verified by script.
7. **The unit of analysis changes at the end.** Phase 4.5 audits the whole
   book; no path to `complete` skips it.
8. **Nothing is turned off silently.** A disabled check leaves a `waivers`
   entry in `project-status.yaml`: who (`waived_by`), why (`reason`), what is
   owed (`debt`) — real text, not a placeholder, reason and debt 20+
   characters; a waiver missing any of them does not count. The literary
   rules R1–R4 have no waiver at all.

## Profiles

`bible/meta.yaml → project.profile`. Every agent loads its profile; on register
or structure, **the profile wins**. The scripts read it stripped and
lowercased; a missing or unknown profile stops them (exit 2).

| Profile (`references/profiles/<profile>.md`) | Unit | Sequence |
|---|---|---|
| `book-technical` | chapter | linear |
| `book-literary` | chapter | linear |
| `corporate-guide` | section | linear-light |
| `product-docs` | article | modular |
| `scientific-paper` | section | imrad |

Files say `unit-NN`; talk to the human in the profile's word.

## Phase detection — start here

- Folder with `bible/meta.yaml`, `schema_version: "3.4"` → load
  `project-status.yaml`; announce project, phase, current unit, last step
  (`runs.tsv`); ask what to work on.
- Other `schema_version` → an earlier skill built it (`pipeline_step.py`
  refuses it, exit 2); offer a fresh scaffold and manual carry-over
  (`references/init-scaffold.md`), never migration.
- Otherwise → Phase 0.

## Phases

**0 — Init** (`references/init-scaffold.md`). One question: what are you
writing? Map it to a profile, scaffold, stop for a go-ahead.

**1 — Setup** (`references/setup.md`). A design conversation, sign-off per
artifact: `meta.yaml`, scope, glossary, style guide with calibration passages,
the mandatory voice profile, `sources/` (nonfiction), `claims-map.yaml`
(paper). Literary adds human seeds (`literary.seeds`), the preserved
`braindump.md`, ≥ `literary.human_calibration_passages` passages written by the
human, characters, world, plot structure with the ending, arcs, timeline, story
ledger, reader journal.

**1.5 — Knowledge graph** (`references/knowledge-graph.md`). Full for
`book-technical` and `scientific-paper`; terminology-only for `corporate-guide`
and `product-docs`; skipped for literary.

**2 — Outlining** (`references/outlining.md`). `outline/units.yaml`,
human-approved before any writing. Literary: scene cards, causal chain, story
ledger with planned payoffs, echo check on turning points, Reader-POV outline
stress test and the design rubric (`references/rubric-literary.md`), then the
readiness gate below.

**Literary readiness — the user's rules, no waiver:**

- **R1** Every character (protagonist, principal, secondary) has a complete,
  signed sheet: backstory, personality, contradiction, want, need, voice, and
  an arc with turning points and `resolves_in` (flat arcs name what they test).
  Signed = the human approved it and you ran `python scripts/pipeline_step.py
  sign <slug> --by <human>`; a later edit needs the questionnaire block and a
  new signature.
- **R2** The ending exists before drafting (`bible/plot-structure.md` front
  matter); every arc resolves at or before `ending.final_unit`.
- **R3** Drafting starts only when `python scripts/pipeline_step.py ready`
  exits 0 — re-checked by every Writer `check`/`done`, `approve` and
  `apply-edits`. If the human wants to start anyway, explain the rule and run
  the questionnaire for what is missing (`references/character-questionnaire.md`).
- **R4** Characters may join mid-book, but the questionnaire runs again and the
  unit restarts at the Writer; the Writer never invents a named character.
  Unnamed one-unit figures live in `bible/characters/_extras.md` (a label is
  never a name); names only talked about, and places, live in `bible/world.md`
  — any of them that speaks or acts on the page, or a § Names entry in a scene
  card, is a character.

These blocks are never overridable — not by a human approval over a red
scorecard, `--human-override`, `approve --force`, or a gate waiver.

Details: `references/profiles/book-literary.md`.

**3 — Writing pipeline** (`references/pipeline.md`, authoritative).

```
Nonfiction (fast; full adds Reader-POV after the Humanizer):
  Writer → Technical Reviewer → Editor → Humanizer → CG Mode A → checks
  → Critic → [Adversarial] → Proofreader → Human review
  → final/ → CG Mode B → digest → archive
Literary:
  Writer (by scene) → Editor (assembly) → Humanizer → Reader-POV
  → CG Mode A → checks → Critic → [Adversarial] → Proofreader
  → Human review → final/ → CG Mode B → digest → reader journal → archive
```

You are the **orchestrator** and never draft unit prose.
Dispatch each agent as a subagent with its agent file, the profile and its
contract's exact inputs; bracket each run with `pipeline_step.py check` /
`done`; run `clean` after every write to `humanized.md`, `checks` before the
Critic. `done` exits `1` (re-dispatch), `3` (R3/R4 pause) or `4` (contract
violation: re-dispatch once, the second escalates). Loop targets: `Writer |
Editor | Humanizer | escalate`; `snapshot --reason …` before each loop, then
every agent of the cycle runs with `--cycle N`; each reads its worklist; a
cycle that fixes nothing stops at once (plateau rule); retry cap 2 (`fast`) or
3 (`full`, literary), then the escalation packet
(`references/loopback-handoff.md`). A Critic ESCALATE is no loop: escalation
packet, unit `on_hold` until the human decides.

Agent files (`references/agents/`): `writer-` and `humanizer-` come in
`-nonfiction` / `-literary`; `editor`, `reader-pov`, `continuity-guardian`,
`critic` and `proofreader` serve both; `technical-reviewer` is nonfiction only;
skeptics follow `references/adversarial-verify.md`. `meta.yaml → models` maps
roles to tiers (`inherit` = session model); model IDs live only on a project's
tiers.

**Human packet** (short; `references/pipeline.md` § Human review): the
proofread text that ships and the Proofreader's changes; nonfiction adds
verdict, most important problem, failing rows, skips and retry summary;
literary adds the 3 most singular and 3 most generic passages, tic counts, the
reader-journal entry and 1–3 decisions. Approve (with a reason if the scorecard
is red; never over a story block) → `python scripts/pipeline_step.py approve unit-NN` copies
`proofread.md` to `final/` without HTML comments; reject with notes
(`human-notes.md`); or defer.

**4 — Assembly** (advisory). `sync_manuscript.py` builds `manuscript.md`
(product-docs: index + cross-article audit); CG full-manuscript audit; polish
pass (nonfiction `fast`) or tail tic pass (literary), with fix-then-verify.

**4.5 — Manuscript gate** (`references/manuscript-gate.md`; literary:
`references/manuscript-gate-literary.md`). Fires automatically when the last
unit is archived. Nonfiction runs MG-1…MG-7. Literary: MG-1/2/3/6 are
`n/a (profile)`; it runs MG-4 (literary read), MG-5, MG-7, MG-S
(`check_story.py --manuscript`), MG-T (`lint_fiction.py --book`) and MG-C
(continuity and developmental audit, two passes each, like MG-4). Findings
persist in `reviews/manuscript-gate-<run>/findings.jsonl` until resolved (a
later re-audit or sweep, or `manuscript_gate.py --resolve KEY --status
fixed|refuted|accepted-risk --note …` within the limits of
`references/manuscript-gate.md` § Findings — deterministic findings never
fixed or refuted by hand, agent `fixed` only after the text changed, literary
MG-S and R1/R2 findings never); coverage lives in `subjects.json`;
critical/major findings face a refutation pass. Verdict:
`ERROR | BLOCKED | NEEDS-REVISION | PASS-PARTIAL | PASS`; one waiver type
(`manuscript_gate.coverage`; never over literary MG-4/MG-C). Converged =
`PASS` (or `PASS-PARTIAL` with a valid coverage waiver), no open
critical/major, two distinct rounds with no new blocking finding, and
(literary) `check_story.py --manuscript` exiting 0. A
round past `max_rounds` is refused. Start: `python scripts/manuscript_gate.py
--round 1`; exit `0` converged · `1` not converged · `2` ERROR.

**5 — Build** (`references/build-export.md`). Confirm targets first. Preflight:
`lint_render.py --fail-on critical`, `sync_manuscript.py --check`,
`validate_claim_index.py --quiet`; literary adds `check_story.py --manuscript`.

## Definition of done

`phase: complete` requires all of:

1. every unit `archived`;
2. the manuscript gate converged: `python scripts/manuscript_gate.py
   --verdict-only` exits 0 (`references/manuscript-gate.md`);
3. no unresolved `CHANGED` in `bible/claim-index.yaml` (where one exists);
4. literary: every arc resolved, the ending delivered (`final_unit` in
   `final/` with at least max(300, 30% of its target) words), the story ledger
   closed (no `open` entry unless
   `deliberately-ambiguous`) — `check_story.py --manuscript` exits 0;
5. every build target verified;
6. a done report the human accepted: open waivers, unresolved minors, and what
   the gate never opened. Otherwise: `blocked-on-manuscript-gate`.

## Scripts

Python 3.10+, PyYAML, all accept `--root`; word lists live in
`scripts/lexicons/<lang>.yaml` + `bible/lexicon.yaml`. See `scripts/README.md`.

| Script | Purpose |
|---|---|
| `pipeline_step.py` | `check`/`done` brackets, `clean`, `snapshot`, `checks`, `ready`, `approve`, `apply-edits`, `sign` |
| `count_rhet.py` · `check_identifiers.py` | Rhetoric and prose counts · invented identifiers (`--build-index`) |
| `check_role_diff.py` | Editor adds no prose; Humanizer budget; Proofreader changes |
| `lint_fiction.py` · `check_story.py` | Literary tics, dialogue, names · readiness, arcs, ending, ledger |
| `manuscript_gate.py` | Phase 4.5 sweep, agent inputs, verdict |
| `lint_render.py` · `lint_style.py` | Render hazards (MG-5, preflight) · the Proofreader's mechanical half |
| `build_concept_dossier.py` · `validate_claim_index.py` · `bootstrap_probes.py` | MG-1 dossiers and claim index · `PROPAGATE` · concept probes |
| `extract_rule_candidates.py` · `check_fixed_defects.py` · `extract_code_corpus.py` | MG-2 · MG-7 · MG-6 inputs |
| `resolve_anchors.py` · `sync_manuscript.py` | Content anchors (`--heal`) · `final/` → `manuscript.md` |

## Project file structure

```
project/
├── bible/
│   ├── meta.yaml · voice-profile.md · style-guide.md · scope.md · glossary.md
│   ├── continuity-tracker.md · do-not-touch.md · fixed-defects.yaml
│   ├── lexicon.yaml               # optional: the book's own tics and terms
│   ├── sources/ (+ sources.md) · identifier-index.txt   # nonfiction
│   ├── knowledge-graph.yaml · examples-library.md · claims-map.yaml (paper)
│   ├── claim-index.yaml · concept-probes*.yaml · rule-probes-tuned.yaml
│   ├── characters/<slug>.md · characters/_extras.md       # literary
│   ├── plot-structure.md · arcs.md · world.md · timeline.md
│   ├── story-ledger.yaml · reader-journal.md · braindump.md
│   └── digests/
├── outline/units.yaml
├── drafts/unit-NN/     # draft edit humanized(.clean|.cN) proofread checks.json/.md
│                       # critique scorecard(.cN) role-diff-<agent>-cN.json
│                       # tech-review coherence reader-report human-notes …
├── drafts/_archive/ · drafts/_polish/
├── final/unit-NN.md · manuscript.md
├── runs.tsv            # one line per agent run (pipeline_step.py done)
├── project-status.yaml # phase, units, retries, waivers, gate pointer
├── reviews/manuscript-gate-<run>/
└── build/
```

## Reference map (load on demand)

| When | Read |
|---|---|
| Init · setup · KG · outline | `references/init-scaffold.md` · `setup.md` · `knowledge-graph.md` · `outlining.md` |
| Pipeline, loops, packet, batch passes | `references/pipeline.md` |
| Scorecard, verdict, Critic protocol | `references/rubric.md` + `references/rubric-nonfiction.md` or `references/rubric-literary.md` |
| Literary characters (R1–R4) | `references/character-questionnaire.md` |
| Machine checks | `references/validation-surface.md`; optional packs, e.g. `references/surfaces/qlik.md` |
| Adversarial · cap or plateau | `references/adversarial-verify.md` · `references/loopback-handoff.md` |
| After approval | `references/chapter-digest.md` + `references/archiving.md` |
| Last unit archived | `references/manuscript-gate.md` (+ `references/manuscript-gate-literary.md`) |
| Propagation · unverifiable claims · Phase 5 | `references/claim-index.md` · `verification-plan.md` · `build-export.md` |
| Why a rule exists (humans) | `docs/rationale/*.md` |
