# Build & export — Phase 5

Input: `manuscript.md` (sequential profiles) or the `final/` tree
(`product-docs`). Output: `build/`.

## Ground rules

1. **Confirm targets first.** Present the profile's default targets with the
   toolchain capability report; get a yes before running anything.
2. **`build/` is disposable.** Never hand-edit an artifact: fix `final/`
   (through the human — it is approved content), re-sync, rebuild. An edited
   artifact diverges silently and the next build erases the fix.
3. **Verify every artifact** (§ Verification). A zero exit code is not
   verification.
4. **Fail honestly.** Missing toolchain → say what is missing, what it
   unlocks, which targets remain. No silent fallback: no HTML renamed to
   `.epub`, no unannounced engine swap, no dropped bibliography. Partial
   delivery is fine when explicit.
5. **Report**: each artifact's absolute path, size, the verification run and
   its result, and every check skipped for a missing tool.

## Toolchain detection

- `pandoc --version` — needed by every profile except `product-docs`.
- PDF engine, in order: `tectonic`, `xelatex` (via `latexmk` if present),
  `lualatex`, `pdflatex`.
- Optional verifiers: `epubcheck`, `pdfinfo`.
- A `docx` or `pdf` skill in the session is a legitimate alternative; prefer
  pandoc when installed (reproducible, scriptable), the skills when pandoc or
  an engine is missing or the human wants layout control.

## Preflight — every profile, before any target

```bash
python scripts/sync_manuscript.py --check          # drop --check to rebuild
python scripts/lint_render.py --fail-on critical   # BLOCKS the build
python scripts/validate_claim_index.py --quiet     # warns, never blocks
python scripts/check_story.py --manuscript         # book-literary: BLOCKS on blocking/major
```

- **`lint_render` blocks.** Its critical class is small and unarguable: a
  paragraph with `---` under it prints as a heading, an unclosed fence turns
  the rest into code, an unclosed comment eats text — all three read fine in
  the source. It also catches handoff comments that leaked into `final/`. Fix
  the source, never the output. Why: `docs/rationale/pipeline.md#preflight`.
- **`sync_manuscript --check` drifting** means someone hand-edited the derived
  `manuscript.md`; find out who before rebuilding over their work.
- **`validate_claim_index` warns.** Print its `PROPAGATE` lines in the build
  report: shipping a known-inconsistent claim set should be a decision.
- **`check_story --manuscript` blocks** a novel with unresolved arcs, an
  ending unit missing from `final/`, or open ledger entries not marked
  `deliberately-ambiguous` — the Definition-of-done test.

## Shared preparation

Generate `build/metadata.yaml` from `bible/meta.yaml` (title, subtitle, author,
`lang` from `project.language_variant`, date, rights) and show it once — it
becomes the title page. Slug the filename from the title (lowercase, hyphens,
no diacritics).

## Books — EPUB / PDF / DOCX

```bash
pandoc manuscript.md --metadata-file=build/metadata.yaml \
  --toc --toc-depth=2 --split-level=1 -o build/<slug>.epub
pandoc manuscript.md --metadata-file=build/metadata.yaml \
  --pdf-engine=xelatex --toc --number-sections \
  -V documentclass=book -V geometry:margin=25mm -o build/<slug>.pdf
pandoc manuscript.md --metadata-file=build/metadata.yaml --toc -o build/<slug>.docx
```

- EPUB: `--epub-cover-image=<path>` when the human provides a cover.
- PDF: use the detected engine and say which ran; `-V mainfont=` only when the
  human names a font.
- DOCX: `--reference-doc=<template.docx>` when the human supplies one.
- **Literary**: `--toc-depth=1` (chapters, not scene headings) and no
  `--number-sections`. Scene-break markers (`* * *`) must survive: check one in
  each output.

## `corporate-guide` — DOCX / PDF with organization front matter

1. Generate `build/front-matter.md`: organization, title, audience
   (`audience_role`), version and date, and the confidentiality label when
   `organization.confidentiality` is set — a build that drops a declared label
   is a defect, not a style choice.
2. Ask for the organization's `reference.docx`; without one, build with pandoc
   defaults and say so.

```bash
pandoc build/front-matter.md manuscript.md --metadata-file=build/metadata.yaml \
  --toc --reference-doc=<org-template.docx> -o build/<slug>.docx
```

PDF: the book invocation with `documentclass=report`. Confidentiality on every
page via the reference template (DOCX) or a small `header-includes` block (PDF)
when the human wants it.

## `product-docs` — validated markdown tree

1. Confirm the layout (flat `build/docs/` or grouped by tag) and the slug
   convention (frontmatter unless the outline sets slugs).
2. Copy each `final/unit-NN.md` to `build/docs/<slug>.md`.
3. **Lint every article — failures block**: frontmatter has non-empty `title`,
   `description`, `tags`, `type` (Diátaxis); every internal link resolves in the
   built tree (a `unit-NN` link is a defect — pipeline names never ship);
   every `related` entry exists; exactly one H1, compatible with the title.
4. Generate `build/docs/index.md` from the outline, grouped, with title and
   description per entry.
5. On a lint failure, fix `final/` (through the human) and rebuild — never the
   copy.
6. Report a per-article table: article, slug, lint result.

## `scientific-paper` — LaTeX + .bib + PDF

1. **`build/references.bib`** from the claims map and `sources.md`: one entry
   per cited source, keys = stable source ids. Every visible citation maps to
   an entry — stop on an orphan and report it; never fabricate an entry.
2. **Citation encoding**: pandoc keys (`[@key]`) → `--citeproc` with a CSL
   matching `citation_style` (none available → `--natbib` for author-year,
   `--biblatex` for numeric, and tell the human which authority ran). Literal
   formatted citations → do not run citeproc over them; render References
   from the claims map and still emit the `.bib`.
3. **LaTeX**:

   ```bash
   pandoc manuscript.md --metadata-file=build/metadata.yaml --standalone \
     --natbib --bibliography=build/references.bib -o build/paper.tex
   ```

4. **PDF**: `latexmk -pdf -interaction=nonstopmode -output-directory=build
   build/paper.tex` or `tectonic build/paper.tex`. Neither available → deliver
   `paper.tex` + `references.bib` and say what compiling needs; never pass an
   uncompiled source off as done.
5. **Compile log**: no `undefined` citations or references, no `??` in the
   output, the bibliography in the declared style.

## Verification

- **EPUB**: `epubcheck` when available; otherwise valid zip, `mimetype` first,
  `META-INF/container.xml` present — and say only the structural check ran.
- **PDF**: non-trivial size; page count via `pdfinfo`; open it (or ask the
  human to) before calling it done.
- **DOCX**: valid zip with `word/document.xml`.
- **Markdown tree**: the lint table fully green.

A target is produced only when its verification passed; otherwise report
"built, not verified — because <missing tool>".
