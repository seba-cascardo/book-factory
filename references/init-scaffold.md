# Init — scaffolding a new project

When no `bible/meta.yaml` exists at the target path, init scaffolds the
project. The human never makes folders by hand.

## When init runs

The user asked to start a project and named a folder with no `bible/`, a folder
that does not exist, or none (then ask which folder — that is phase detection,
not an init question). If `bible/meta.yaml` exists, do NOT run init: `"3.4"`
→ resume from `project-status.yaml`; anything else → § Earlier skill versions.

## The one question: the profile

Init asks one thing, because one thing changes which files exist: **"What are
you writing?"** Everything else belongs to setup. Propose, don't interrogate —
map the first sentence, state the choice and what it implies in one line, move
on unless the human objects:

| The user says something like | Profile |
|---|---|
| novel, story, fiction, memoir with a narrative arc | `book-literary` |
| a book about X, tutorial, textbook, technical book | `book-technical` |
| internal guide, handbook, process manual, "for my company/team" | `corporate-guide` |
| docs, docs site, knowledge base, how-to articles, runbooks | `product-docs` |
| paper, journal or conference submission, preprint | `scientific-paper` |

Only when two profiles genuinely fit, ask the discriminating question: "Is there
a reading order, or does each page stand alone?" (`book-technical` vs
`product-docs`); "Is the reader a customer or a colleague in one
organization?" (`book-technical` vs `corporate-guide`). Confirm in the
profile's unit word — the first time the human hears it.

## What init creates

Base skeleton, every profile:

```
<project-root>/
├── bible/
│   ├── meta.yaml              ← templates/meta.yaml, pre-filled (below)
│   ├── voice-profile.md       ← templates/voice-profile.md — setup fills it
│   ├── style-guide.md         ← templates/style-guide.md — setup fills it
│   ├── scope.md               ← empty shell
│   ├── glossary.md            ← templates/glossary.md
│   ├── continuity-tracker.md  ← templates/continuity-tracker.md
│   ├── do-not-touch.md        ← templates/do-not-touch.md (keep the header)
│   ├── fixed-defects.yaml     ← templates/fixed-defects.yaml (delete the example, keep the header)
│   └── sources/               ← empty; setup builds the grounding library
├── outline/units.yaml         ← schema, no entries
├── drafts/_archive/
├── final/
├── reviews/
├── runs.tsv                   ← header row only: unit agent tier cycle timestamp_utc output_bytes
└── project-status.yaml        ← templates/project-status.yaml, pre-filled (below)
```

Create `do-not-touch.md` and `fixed-defects.yaml` now: a project that has to
invent them later invents them after the fix pass that needed them.

Per profile:

| Profile | Adds | Omits |
|---|---|---|
| `book-technical` | `knowledge-graph.yaml` (empty) · `examples-library.md` · `rule-probes-tuned.yaml` (header only) · `digests/` | — |
| `book-literary` | `characters/` with `_extras.md` (← `templates/extras.md`) · `plot-structure.md` (← `templates/plot-structure.md`) · `arcs.md` (← `templates/arcs.md`) · `story-ledger.yaml` (← `templates/story-ledger.yaml`) · `reader-journal.md` (← `templates/reader-journal.md`) · `braindump.md` (empty — setup pastes the human's raw notes verbatim) · `world.md` · `timeline.md` · `digests/` | `knowledge-graph.yaml`, `examples-library.md`, `rule-probes-tuned.yaml` |
| `corporate-guide` | `knowledge-graph.yaml` (terminology-only) · `rule-probes-tuned.yaml` · `digests/` | `examples-library.md` unless setup enables a running example |
| `product-docs` | `knowledge-graph.yaml` (terminology-only) · `rule-probes-tuned.yaml` | `digests/`, `examples-library.md` |
| `scientific-paper` | `claims-map.yaml` (← `templates/claims-map.yaml`) · `knowledge-graph.yaml` · `rule-probes-tuned.yaml` · `digests/` | `examples-library.md` |

Character sheets are created per character during setup from
`templates/character-sheet.md`, through `references/character-questionnaire.md`
— never as empty placeholders, which `pipeline_step.py ready` would reject
anyway.

Generated later, listed so their absence is no puzzle:
`bible/identifier-index.txt` (setup, nonfiction:
`python scripts/check_identifiers.py --build-index`), `bible/claim-index.yaml`,
`concept-probes.yaml`, `audit-config.yaml` (Phase 4.5 scripts),
`bible/lexicon.yaml` (optional: the book's own tics and terms, added when
someone spots them).

### meta.yaml pre-fill

Init fills only what it knows; the rest stays `[placeholder]` for setup:

```yaml
project:
  profile: <chosen profile>
  language_variant: <from the user's language, e.g. es-AR — confirm in setup>
models:
  tiers: { creative: inherit, audit: inherit }
  roles: { writer: creative, critic: creative, humanizer: audit, default: audit }
schema_version: "3.4"
```

- `project.subtype` is `book-technical` only — delete it elsewhere.
  `citation_style` is uncommented for `scientific-paper` only.
- `book-literary`: `roles.humanizer: creative`; `pipeline.retry_cap: 3`;
  keep the `literary:` block; delete the nonfiction regions (`target_version`,
  `pinned_versions`, `validation_surface`).
- Every other profile: delete the `literary:` block.
- `corporate-guide`: add the empty `organization:` block so setup cannot skip
  it.

Never write a model ID into the scaffold.

### project-status.yaml pre-fill

`templates/project-status.yaml` with its comments, and these values:

```yaml
schema_version: "3.4"
project: { name: "[working title]", profile: <profile>, created: <today>, last_updated: <today> }
phase: setup
current_unit: null
outline: { approved: false, approved_on: null }   # pipeline_step.py ready reads it
units: {}
knowledge_graph: { last_verified: null }
waivers: []
manuscript_gate: { state: null }
retries: { by_unit: {}, cap_hits: [] }
notes: []
```

`phase: setup`, not `init` — otherwise phase detection re-runs the scaffold.
The runs log is `runs.tsv`, not a key here.

## After init

Tell the human, in their language and unit word: the profile and why, the tree
created, and that setup comes next (a design conversation, not a form). **Stop
and wait for a go-ahead.**

## Non-empty target folder

Files the skill did not create → ask first: use the folder as-is, or pick an
empty one. Never overwrite or delete. If "use it", create only the missing
pieces and record what was skipped under `notes:` in `project-status.yaml`.

## Earlier skill versions

`schema_version` missing or not `"3.4"` → the project predates this skill
(`pipeline_step.py`, `check_story.py` and `manuscript_gate.py` refuse it, exit
2; so does a missing or unknown `project.profile`).
There is no automatic migration: a migrator that half-understands an old
schema produces a project that half-works. Offer a fresh scaffold (new folder,
or here after explicit confirmation) plus a manual carry-over:

- approved units and the outline carry over as approved content;
- bible documents carry over as raw material for setup — review, don't assume;
- `voice-profile.md`, `meta.yaml`, `project-status.yaml` — and, literary, the
  character sheets through the questionnaire — are produced fresh: they encode
  decisions the old project never made.

If the human declines, stop.
