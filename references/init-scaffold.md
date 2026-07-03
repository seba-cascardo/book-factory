# Init — Scaffolding a New Project

When the skill is invoked and no `bible/meta.yaml` exists at the target path,
init scaffolds the project directory. The human never makes folders by hand.

This file specifies the one question init asks, what it creates per profile,
and what it says to the human before and after.

## When init runs

- The user asked to start a new project AND
- either (a) named a folder that exists but has no `bible/`, (b) named a
  folder that does not exist, or (c) named no folder (ask which folder to
  use or create — that is phase detection, not an init question).

If `bible/meta.yaml` exists, do NOT run init. Check its `schema_version`:
`"3.0"` → resume from `project-status.yaml`; anything else → see "Projects
from an earlier skill version" below.

## The one init question: the profile

Init asks exactly one thing, because exactly one thing changes which folders
exist: **"What are you writing?"** Map the answer to one of the five
profiles. Everything else — title, audience, tone, scope — belongs to setup;
asking it here turns a ten-second confirmation into a form.

**Propose, don't interrogate.** The user's first sentence almost always
carries the answer. Map it, state the choice and what it implies in one
line, and move on unless they object:

| The user says something like | Profile |
|---|---|
| novel, story, fiction, memoir with narrative arc | `book-literary` |
| a book about X, tutorial book, textbook, technical book to publish | `book-technical` |
| internal guide, handbook, process manual, "for my company/team" | `corporate-guide` |
| docs, docs site, knowledge base, how-to articles, runbooks | `product-docs` |
| paper, journal/conference submission, preprint | `scientific-paper` |

Only ask a follow-up when the answer is genuinely ambiguous between two
profiles, and make it the discriminating question, not a menu: "Is there a
reading order, or does each page stand alone?" separates `book-technical`
from `product-docs`; "Is the reader a customer or a colleague inside one
organization?" separates `book-technical` from `corporate-guide`.

Confirm using the profile's human-facing unit word (chapter / article /
section) — this is the first moment the human hears the vocabulary the
whole project will use.

## What init creates

Base skeleton, all profiles:

```
<project-root>/
├── bible/
│   ├── meta.yaml                 ← from templates/meta.yaml, pre-filled (below)
│   ├── voice-profile.md          ← from templates/voice-profile.md — empty shell,
│   │                               setup fills it; mandatory for EVERY profile
│   ├── style-guide.md            ← empty shell, setup fills
│   ├── scope.md                  ← empty shell
│   ├── glossary.md               ← from templates/glossary.md
│   ├── continuity-tracker.md     ← from templates/continuity-tracker.md
│   └── sources/                  ← empty folder (setup populates the grounding library)
├── outline/
│   └── units.yaml                ← schema present, no entries (Phase 2 fills)
├── drafts/
│   └── _archive/                 ← empty; archiving policy writes here
├── final/                        ← empty
└── project-status.yaml           ← from templates/project-status.yaml, pre-filled (below)
```

Per-profile additions and omissions:

| Profile | Adds | Omits |
|---|---|---|
| `book-technical` | `bible/knowledge-graph.yaml` (empty, Phase 1.5 fills) · `bible/examples-library.md` · `bible/digests/` | — |
| `book-literary` | `bible/characters/` · `bible/world.md` · `bible/plot-structure.md` · `bible/arcs.md` · `bible/timeline.md` · `bible/digests/` | `knowledge-graph.yaml`, `examples-library.md` — plot-structure and arcs carry the dependency role for fiction |
| `corporate-guide` | `bible/knowledge-graph.yaml` (terminology-only) · `bible/digests/` | `examples-library.md` — running example is off by default; setup creates the file only if it enables one |
| `product-docs` | `bible/knowledge-graph.yaml` (terminology-only) | `bible/digests/` — modular sequence, there is no narrative memory to digest; `examples-library.md` |
| `scientific-paper` | `bible/claims-map.yaml` (from `templates/claims-map.yaml`, empty) · `bible/knowledge-graph.yaml` · `bible/digests/` | `examples-library.md` |

### meta.yaml pre-fill

From `templates/meta.yaml`. Init fills only what it knows; everything else
stays as `[placeholder]` for setup:

```yaml
schema_version: "3.0"
project:
  profile: <chosen profile>
models:
  tiers: { creative: inherit, audit: inherit }
  roles: { writer: creative, critic: creative, humanizer: audit, default: audit }
```

- `book-technical`: keep `project.subtype: "tutorial"` (refined in setup).
  For **every other profile, delete the `subtype` key** — it is
  book-technical-only, and a stray `subtype` on a paper or a docs project
  contradicts the schema. Likewise, un-comment `citation_style` only for
  `scientific-paper`.
- `book-literary`: pre-set `roles.humanizer: creative` — voice is the
  product there, and a default the human must remember to flip is a default
  that ships wrong.
- `corporate-guide`: add the `organization:` block as an empty placeholder
  (`name`, `audience_role`, `internal_context`, `confidentiality`) so setup
  cannot skip it — the profile's example and register rules depend on it.

Never write a model ID into the scaffold. Tiers default to `inherit`; IDs
are a cost-control decision the human makes later, in their own meta.yaml.

### project-status.yaml pre-fill

From `templates/project-status.yaml`:

```yaml
schema_version: "3.0"
project:
  name: "[working title — setup fills]"
  profile: <chosen profile>
  created: <today>
  last_updated: <today>
phase: setup
units: []
retries: { by_unit: {}, cap_hits: [] }
runs: []            # orchestrator appends one line per agent run — see pipeline.md
notes: []
```

`phase: setup`, not `init` — by the time this file exists, init is done, and
a status file that says `init` would make phase detection re-run the
scaffold on the next session.

## Post-init confirmation

Tell the human, in their language and using the profile's unit word:
which profile was chosen and why, the tree that was created, and that the
next step is Phase 1 (setup — a design conversation, not a form). Then
**stop and wait for a go-ahead.** Init is separate from setup precisely so
the human can inspect the scaffold before investing in the design session.

## Non-empty target folder

If the target path exists and contains files the skill did not create, ask
before writing anything: use the folder as-is, or pick an empty one. Never
overwrite or delete existing files. If the human says "use it", create only
the missing pieces of the skeleton and record what was skipped under
`notes:` in `project-status.yaml` — a scaffold that silently coexists with
unknown files is a scaffold nobody can debug later.

## Projects from an earlier skill version

If `bible/meta.yaml` exists but `schema_version` is missing or not `"3.0"`,
the project predates this version of the skill. There is no automatic
migration — a migrator that half-understands an old schema produces a
project that half-works, which is worse than either state.

Tell the human plainly: this project was built with an earlier version;
the current skill cannot run its pipeline against it. Offer a fresh
scaffold (in a new folder, or here after their explicit confirmation —
never touching existing content without it) plus a **manual carry-over**:

- Approved/final units and the outline carry over as content — copy them in
  and treat them as approved input.
- Bible documents (scope, glossary, style guide, sources library, story
  bible) carry over as raw material for setup — review, don't assume.
- `voice-profile.md` and the current meta/status files must be produced
  fresh in setup: they encode decisions the old project never made, and
  defaulting them silently would skip the human sign-off they exist for.

If the human declines, stop — do not run any phase against an old-schema
project.
