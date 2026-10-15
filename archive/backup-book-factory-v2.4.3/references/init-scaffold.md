# Init — Scaffolding a New Project

When the user invokes the skill and no `bible/meta.yaml` exists at the
target path, the skill scaffolds the project directory structure
itself. The human should never have to make folders by hand.

This file specifies what the `init` step creates, in what order, and
what the skill says to the human before and after.

## When init runs

- The user asked to start a new book project AND
- Either (a) named a folder that exists but has no `bible/`, or (b)
  named a folder that doesn't exist, or (c) named no folder (the skill
  then asks).

If a `bible/meta.yaml` exists, DO NOT run init. Go to resume path from
`project-status.yaml`.

## Pre-init conversation (short)

The skill asks two questions before scaffolding — any more and it
becomes a form. These two are gate questions because they change which
folders exist.

1. "¿Qué tipo de proyecto es: literario o técnico?" → sets
   `project.type`.
2. For technical: "¿Qué sub-tipo? Tutorial, referencia, cookbook,
   textbook, u opinión técnica?" → sets `project.subtype`.
   (Defaults to `tutorial` if unclear; can be refined during setup.)
   For literary: skip this; literary has no sub-type at the skill
   level.

The skill does NOT ask the title, audience, tone, or anything else
up front. Those come in setup.

## What init creates

The skeleton below uses the chosen project type. Technical shown;
literary is analogous with different bible/ content.

```
<project-root>/
├── bible/
│   ├── meta.yaml                     ← from templates/meta-technical.yaml
│   │                                   pre-filled with:
│   │                                     project.type: technical
│   │                                     project.subtype: <chosen>
│   │                                   rest has [placeholders] for setup
│   ├── scope.md                      ← empty shell, setup fills
│   ├── style-guide.md                ← empty shell
│   ├── glossary.md                   ← from templates/glossary.md
│   ├── examples-library.md           ← from templates/examples-library.md
│   ├── continuity-tracker.md         ← from templates/continuity-tracker.md
│   ├── sources/                      ← empty folder (Sub-Phase 7 populates)
│   ├── digests/                      ← empty (populated post-chapter-approval)
│   └── knowledge-graph.yaml          ← from templates/knowledge-graph.yaml
│                                       pre-filled empty, Phase 1.5 fills
├── outline/
│   └── chapters.yaml                 ← from templates/chapter-entry.yaml
│                                       (empty but schema present)
├── drafts/
│   └── _archive/                     ← empty, archive policy writes here
├── final/                            ← empty
└── project-status.yaml               ← from templates/project-status.yaml
                                        pre-filled with:
                                          project.type/subtype
                                          phase: setup
                                          created/last_updated dates
```

For literary projects, `bible/` has `characters/`, `world.md`,
`plot-structure.md`, `arcs.md`, `timeline.md` instead of `scope.md`,
`glossary.md`, `sources/`, `examples-library.md`,
`knowledge-graph.yaml`. The template set is the literary one.

## Post-init confirmation

The skill tells the human exactly what was created and what's next:

> "Listo. Creé la estructura del proyecto en `<path>`. Próximo paso:
> Phase 1 — Setup. Voy a hacerte algunas preguntas para escribir
> `bible/meta.yaml` (audiencia, alcance, tono) y después
> `bible/scope.md` y `bible/style-guide.md`. ¿Arrancamos?"

The skill does NOT start setup without the human saying yes. Init is
separate from setup precisely so the human can inspect the scaffold
first if they want.

## Refusal to scaffold

If the target path exists and is not empty (contains files the skill
didn't create), ask before writing anything:

> "La carpeta `<path>` ya tiene archivos. ¿La usamos como está (puedo
> convivir con lo que hay) o querés una carpeta vacía?"

The skill will NOT blow away existing files. If the human says "use
it," the skill creates only the missing pieces from the skeleton, and
logs what it skipped in `project-status.yaml` under `notes:`.

## Migration from v2.2 projects

If `bible/meta.yaml` exists but has no `schema_version: "2.3"` (or
lacks any v2.3-only section like `validation_surface`), the skill
offers a non-destructive migration:

> "Este proyecto fue armado con book-factory v2.2. v2.3 agrega Knowledge
> Graph, Validation Surface, scorecard, digests y escalación
> estructurada. ¿Querés migrar ahora? No toco tu contenido existente —
> solo agrego los archivos que faltan con valores por defecto y flageo
> qué necesita tu atención."

On yes:

1. Backup the current state to `_pre-v2.3-backup/` (copy, not move).
2. Add `bible/knowledge-graph.yaml` from template, pre-filled with
   concepts grepped from `bible/glossary.md` (best-effort; flag
   low-confidence).
3. Add `validation_surface.surfaces: []` to `bible/meta.yaml` with a
   comment pointing to `references/validation-surface.md`.
4. Add `pipeline.chapter_digest` and `pipeline.archive_drafts` sections
   with defaults.
5. Add `bible/digests/` and `drafts/_archive/` folders.
6. Update `project-status.yaml` with the v2.3 schema shape; fill in
   what it can infer from existing state; flag what it couldn't.
7. Leave all existing content, drafts, outlines, and final chapters
   untouched.

On no: the skill still works — v2.3 reads v2.2 projects. It just won't
use the new phases.
