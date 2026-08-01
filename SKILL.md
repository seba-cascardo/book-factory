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

A framework for producing long-form documents through a human-directed,
AI-assisted pipeline. The human is the creative director. Agents draft, review,
edit, polish, simulate readers, and gate — but never make strategic decisions
about content direction. Nothing advances without explicit human sign-off.

Version history lives in `CHANGELOG.md` — do not load it during normal
operation.

---

## Core principles

1. **The human approves every phase transition.** The Critic can block a unit;
   only the human can approve one.
2. **Grounding before prose.** Nonfiction writers read the source library
   before drafting and cite invisibly (or visibly, per profile). Claims trace
   to sources.
3. **One voice per project, not one voice per skill.** Agents calibrate
   against the project's `bible/voice-profile.md` — its fingerprint, its
   opening rotation, its own GOOD examples generated at setup. The skill's
   reference files carry rules and BAD examples only. This is deliberate:
   shared GOOD examples produce identical-sounding output across projects.
4. **Countable quality gates.** The Critic's verdict is computed from a
   scorecard; rhetoric budgets are counted, not felt.
5. **Roles do not overlap.** Each agent owns a clean slice and flags outside
   its scope via HTML comments instead of fixing silently. If every agent
   fixes everything, the pipeline collapses into four identical rewrites.
6. **The unit of analysis changes at the end.** Per-unit gates cannot see a
   contradiction that spans two units — each reviewer sees one side and
   approves it, correctly. Phase 4.5 re-audits the book as one document and
   iterates until it converges. **No path leads from the last approved unit to
   `complete` without it.**
7. **Nothing is turned off silently.** Any check disabled leaves a `waivers`
   entry in `project-status.yaml` naming who waived it, why, and what is owed.
   A config value nobody looked at is how three agents once sat unrun for three
   months while the project reported itself finished.

---

## Document profiles

`bible/meta.yaml → project.profile` selects one of five profiles. Every agent
loads the profile file at the start of its turn — it is short and changes how
the agent writes, reviews, and gates.

| Profile | Unit | Sequence | Read first |
|---------|------|----------|------------|
| `book-technical` | chapter | linear | `references/profiles/book-technical.md` |
| `book-literary` | chapter | linear | `references/profiles/book-literary.md` |
| `corporate-guide` | section | linear-light | `references/profiles/corporate-guide.md` |
| `product-docs` | article | modular | `references/profiles/product-docs.md` |
| `scientific-paper` | section | imrad | `references/profiles/scientific-paper.md` |

The profile declares: what the unit is called, register defaults and
prohibitions, opening/closing policy, citation policy (invisible HTML comments
vs. visible academic citations), running-example policy, rubric deltas,
Reader-POV personas, and Phase 5 build targets. When this SKILL.md and a
profile disagree on a register or structure question, **the profile wins** —
that is the point of profiles.

Files use `unit-NN` naming internally; when talking to the human, use the
profile's word (chapter, article, section).

---

## Phase detection — start here

1. **User pointed to a folder**:
   - `bible/meta.yaml` with `schema_version: "3.0"` → load
     `project-status.yaml`, announce project, phase, current unit, last
     completed step. Ask what to work on.
   - `bible/meta.yaml` with another schema_version → tell the human this
     project was built with an earlier version of the skill; offer to
     re-scaffold and carry content over manually. There is no automatic
     migration.
   - No `bible/meta.yaml` → new project. Go to Phase 0.
2. **No folder specified** → ask which folder to use or create, then Phase 0.

---

## Phase 0: Init

Read `references/init-scaffold.md`. Ask only what changes the scaffold:

1. **Profile** — ask "what are you writing?" and map the answer to one of the
   five profiles. Propose, don't interrogate: if the user said "an internal
   prompting guide for my company", that is `corporate-guide`, confirm and
   move on.
2. Scaffold the directory per the profile (literary gets characters/world/
   plot; papers get claims-map; product-docs skips digests). Announce what was
   created; proceed to Phase 1 on approval.

---

## Phase 1: Setup

Read `references/setup.md`. Setup is a collaborative design session, not a
form. It produces, with human sign-off per artifact:

- `bible/meta.yaml` — scope, audience, tone, conventions, pipeline config,
  model tiers.
- `bible/scope.md`, `bible/glossary.md`.
- `bible/style-guide.md` — decisions + calibration passages (draft, get
  feedback, refine until the human says "yes, THIS").
- **`bible/voice-profile.md`** — mandatory for every profile. The project's
  distinctive fingerprint, banned traits, opening rotation, closing policy,
  rhetoric budget overrides, and the project's own GOOD examples derived from
  the approved calibration passages. See `references/setup.md` § Voice
  Profile. This artifact is what keeps this project from sounding like every
  other project.
- `bible/sources/` — grounding library: PDF → markdown extraction, guided
  `sources.md` index with authoritative-for / known-wrong / version-drift,
  human-signed. For `scientific-paper`, references can also be pulled via
  Zotero/arxiv/citecheck MCP tools when connected.
- Literary only: characters/, world.md, plot-structure.md, arcs.md,
  timeline.md.
- Paper only: `bible/claims-map.yaml` seeded with the core claims.

## Phase 1.5: Knowledge graph

Read `references/knowledge-graph.md`. Mandatory for `book-technical` and
`scientific-paper`; terminology-only for `product-docs` and `corporate-guide`;
skipped for literary (plot-structure and arcs serve that role).

## Phase 2: Outlining

Read `references/outlining.md` (profile branches). Output:
`outline/units.yaml`, human-approved before any writing. Literary outlines mark
beats as `scene` or `exposition-within-scene`; profiles with modular sequence
outline standalone units with linked prerequisites; `scientific-paper` fixes
the IMRaD writing order (Methods → Results → Introduction → Discussion →
Abstract last).

## Phase 3: Writing pipeline

Read `references/pipeline.md` for the full specification — inputs/outputs per
agent, verdicts, loopback rules, retry policy. Summary:

**Nonfiction profiles** (`fast` default / `full` opt-in):

```
Writer → Technical Reviewer → Editor → Humanizer → [Reader-POV: full only]
  → Continuity Guardian (Mode A: coherence) → Critic (GATE)
  → [Adversarial Verify: if enabled] → Human review
  → (on approval) Proofreader → Continuity Guardian (Mode B: tracker)
  → digest (sequential profiles) → archive
```

**Literary**:

```
Writer → Editor → Humanizer → Reader-POV → Critic (GATE)
  → [Adversarial Verify: if enabled] → Human review
  → (on approval) Proofreader → Continuity Guardian → digest → archive
```

Invariants (memorize these; several v2 bugs came from drift on exactly these
points):

- The Critic always reads `humanized.md`, in every mode and profile.
- The Humanizer runs every unit, in every mode. The Editor is structural only
  and never applies prose fixes or Reviewer advisories — those belong to the
  Humanizer.
- Verdicts are computed from `drafts/unit-NN/scorecard.yaml` per
  `references/rubric.md`. The Critic does not choose verdicts.
- Retry cap: 2 (fast), 3 (full, literary). On cap hit produce the structured
  escalation packet (`references/loopback-handoff.md`), never a vague "ask the
  human".
- After each agent run, append one line to `project-status.yaml → runs`:
  `- [unit-NN, <agent>, <tier>, <cycle>, <ISO timestamp>]`. Nothing more —
  token accounting proved unenforceable and was dropped.

### Agent reference files

Load the agent's file fresh at the start of its turn, then the profile, then
`bible/meta.yaml`, then (prose agents) `bible/voice-profile.md`.

| Agent | Nonfiction | Literary |
|-------|------------|----------|
| Writer | `references/agents/writer-nonfiction.md` | `references/agents/writer-literary.md` |
| Technical Reviewer | `references/agents/technical-reviewer.md` | — |
| Editor | `references/agents/editor.md` | same file, § Literary |
| Humanizer | `references/agents/humanizer-nonfiction.md` | `references/agents/humanizer-literary.md` |
| Reader-POV | `references/agents/reader-pov.md` | same file, § Literary |
| Critic | `references/agents/critic.md` | same file (loads literary rubric) |
| Proofreader | `references/agents/proofreader.md` | same |
| Continuity Guardian | `references/agents/continuity-guardian.md` | same |
| Adversarial skeptics | `references/adversarial-verify.md` | same |
| Concept Auditor (Phase 4.5) | `references/agents/concept-auditor.md` | same |
| Rule Auditor (Phase 4.5) | `references/agents/rule-auditor.md` | — |

### Anti-mediocrity reads

| Agent | Loads |
|-------|-------|
| Writer, Humanizer, Critic, CG (Mode A) | `anti-mediocrity-nonfiction.md` or `anti-mediocrity-literary.md` per profile |
| Technical Reviewer, Editor, Proofreader, Reader-POV, CG (Mode B) | none — scope discipline |

These files contain rules and BAD examples only. GOOD examples live in the
project's `bible/voice-profile.md`. Never import prose examples from the
skill's references into a draft.

### Model assignment

`bible/meta.yaml → models` maps roles to **tiers**, not model IDs:

```yaml
models:
  tiers: { creative: inherit, audit: inherit }   # inherit = session model
  roles: { writer: creative, critic: creative, humanizer: audit, default: audit }
```

Literary projects set `humanizer: creative` (voice is the product). Set an
explicit model ID on a tier only when the human wants cost control; never
hardcode IDs anywhere else.

## Phase 4: Assembly & review

1. Sequential profiles: concatenate `final/unit-NN.md` → `manuscript.md`.
   `product-docs`: no concatenation — build the index and cross-article
   consistency audit instead.
2. Continuity Guardian full-manuscript audit (includes orphan-terms coverage
   for KG profiles).
3. Proofreader over late-edited units.
4. Optional polish pass (nonfiction fast mode): batch Reader-POV + Humanizer
   over 3-4 approved units; proposed edits as a diff the human accepts or
   rejects. See `references/pipeline.md` § Polish pass.
5. Literary: singularity audit if 5+ units approved since the last one
   (`references/agents/continuity-guardian.md` § Singularity audit).
6. Style consistency report; the human decides final revisions.

Everything in Phase 4 is advisory. The gate is next, and it is not.

## Phase 4.5: Manuscript gate

Read `references/manuscript-gate.md`. **Fires automatically** when the last unit
reaches `archived` — write `phase: manuscript-gate` and start Round 1. Do not
report the book finished from Phase 4.

Six checks over the whole book, not the unit:

| | Question | Engine |
|---|---|---|
| MG-1 | Do all claims about one concept agree, across units? | dossiers + `concept-auditor` |
| MG-2 | Does the book's code obey the rules its prose states? | rule candidates + `rule-auditor` |
| MG-3 | Was everything an exercise demands actually taught? | `rule-auditor` |
| MG-4 | Reading it end to end — **is it enough?** | `reader-pov` whole-book mode |
| MG-5 | Does the source render as intended? | `scripts/lint_render.py` |
| MG-6 | Did the code run, or is the debt declared? | runner audit + waivers |

Every `critical`/`major` from MG-1–4 goes through adversarial verification with a
mandate to refute before it reaches the human.

**The verdict is computed** — any unresolved critical → `BLOCKED`; any unresolved
major → `NEEDS-REVISION`; else `PASS`. **The gate iterates**: fixes are proposed,
the human decides, accepted edits make the claim index emit `PROPAGATE`, and those
siblings become the next round's scope. It closes on `PASS` **plus two
consecutive rounds with no new blocking findings** — one clean round is not
evidence. At `max_rounds` it escalates rather than relaxing the criterion.

```bash
python scripts/manuscript_gate.py --round 1        # prepare + verdict
python scripts/manuscript_gate.py --verdict-only   # after dispatching auditors
```

## Phase 5: Build & export

Read `references/build-export.md`. Per profile: books → EPUB/PDF/DOCX (pandoc,
or the docx/pdf skills when available); corporate guides → DOCX/PDF with the
organization's front matter; product-docs → markdown tree with frontmatter
ready for a static site; papers → LaTeX/PDF with formatted bibliography from
the claims map. Output to `build/`. Always confirm targets with the human
before building.

Preflight, every profile: `lint_render.py --fail-on critical`,
`sync_manuscript.py --check`, `validate_claim_index.py --quiet`.

## Definition of done

`phase: complete` is not a label anyone may assert. It requires all of:

1. every unit `archived`;
2. the manuscript gate at `PASS` **and converged**;
3. no unresolved `CHANGED` in `bible/claim-index.yaml`;
4. every build target verified;
5. a done report the human accepted, listing open `waivers` and unresolved
   minors.

Anything short of that is `blocked-on-manuscript-gate`, and saying so is the
useful thing to do.

## Scripts

Deterministic checks live in `scripts/` and run without a model. Python 3.10+
and PyYAML; `git` optional (it powers the incomplete-fix detector). They all
accept `--root` and `--units`, so every one of them also runs standalone over a
book this skill never scaffolded. See `scripts/README.md`.

| Script | What it is for |
|---|---|
| `manuscript_gate.py` | Phase 4.5: deterministic sweep, agent inputs, verdict |
| `lint_render.py` | MG-5 rendering hazards; build preflight gate |
| `build_concept_dossier.py` | MG-1 dossiers and `bible/claim-index.yaml` |
| `validate_claim_index.py` | `PROPAGATE` — what else says the same thing |
| `bootstrap_probes.py` | Seeds concept probes from the KG, glossary, or frequency |
| `extract_rule_candidates.py` | MG-2 rule ↔ instance pairing |
| `extract_code_corpus.py` | MG-6 verification-plan raw material |
| `lint_style.py` | The Proofreader's mechanical half |
| `sync_manuscript.py` | `final/` → `manuscript.md`, with `--check` |

---

## Human review packet (every unit, every profile)

Present together: the unit text (`humanized.md`); the Critic's computed
verdict + failing scorecard items with evidence; the Critic's observations;
`tech-review.md` (nonfiction) with any skipped-check notes made explicit;
`coherence.md` or `reader-report.md`; the adversarial report if it ran; retry
summary; the one-line run log for the unit.

The human can approve (even against a red scorecard — record the rationale),
reject with notes (routed to the agent they name, counts against the retry
cap), or defer. The scorecard is decision support, not authority.

---

## Project file structure

```
project/
├── bible/
│   ├── meta.yaml              # profile, audience, pipeline, models (tiers)
│   ├── voice-profile.md       # fingerprint, opening rotation, budgets, GOOD examples
│   ├── style-guide.md         # decisions + calibration passages
│   ├── scope.md · glossary.md · knowledge-graph.yaml · continuity-tracker.md
│   ├── sources/               # PDFs + .md extractions + figures/ + sources.md index
│   ├── claim-index.yaml       # concept × location + propagation (generated)
│   ├── concept-probes.yaml    # generated · concept-probes-tuned.yaml (hand-written)
│   ├── audit-config.yaml      # fix-run commits, persona names, code kinds
│   ├── do-not-touch.md        # auto-refutation anchors — verified-correct passages
│   ├── claims-map.yaml        # scientific-paper only
│   ├── characters/ world.md plot-structure.md arcs.md timeline.md   # literary only
│   ├── examples-library.md    # profiles with a running example
│   └── digests/               # sequential profiles only
├── outline/units.yaml
├── drafts/unit-NN/            # grounding-notes.md draft.md tech-review.md edit.md
│                              # humanized.md reader-report.md coherence.md
│                              # critique.md scorecard.yaml adversarial-report.md
├── drafts/_archive/ · drafts/_polish/
├── final/unit-NN.md
├── project-status.yaml        # phase, retries, runs, waivers, manuscript_gate
├── manuscript.md              # Phase 4, generated by scripts/sync_manuscript.py
├── reviews/manuscript-gate-<date>/   # Phase 4.5: GROUNDING.md, round-N/, REPORT.md
└── build/                     # Phase 5 outputs
```

---

## Reference map (load on demand)

| Trigger | Read |
|---------|------|
| New project | `references/init-scaffold.md` |
| Setup | `references/setup.md` |
| Any agent turn | `references/profiles/<profile>.md` + the agent file |
| Knowledge graph | `references/knowledge-graph.md` |
| Outlining | `references/outlining.md` |
| Pipeline (full spec) | `references/pipeline.md` |
| Critic scorecard + verdicts | `references/rubric.md` |
| Machine checks (Axis A/C) | `references/validation-surface.md` |
| Adversarial pass | `references/adversarial-verify.md` |
| Retry cap hit | `references/loopback-handoff.md` |
| After approval | `references/chapter-digest.md` + `references/archiving.md` |
| Last unit archived | `references/manuscript-gate.md` — **not optional** |
| Claim propagation, "what else says this?" | `references/claim-index.md` |
| Executable code with no runner | `references/verification-plan.md` |
| Phase 5 | `references/build-export.md` |

Templates live in `templates/` — the scaffold copies from these. The
scorecard template is `templates/scorecard.yaml` and the per-unit artifact is
always `drafts/unit-NN/scorecard.yaml`.
