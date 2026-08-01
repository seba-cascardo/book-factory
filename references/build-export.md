# Build & Export — Phase 5

Phase 5 turns approved content into shippable artifacts. Input is the
Phase 4 output — `manuscript.md` for sequential profiles, the `final/`
tree for `product-docs`. Output always goes to `build/`.

## Ground rules (every profile)

1. **Confirm targets with the human before building.** The profile
   suggests defaults (below); the human can drop or add targets. Present
   the target list together with the toolchain capability report and get
   a yes before running anything.
2. **`build/` is disposable.** Never hand-edit a built artifact. Content
   fixes go to `final/` or `manuscript.md` (through the human — this is
   post-approval content) and the target is rebuilt. Why: an edited
   artifact silently diverges from the manuscript, and the next build
   erases the fix.
3. **Verify every artifact after producing it.** A zero exit code from
   pandoc is not verification — open it, check its structure, count its
   pages (see Verification below).
4. **Fail honestly.** When a toolchain is missing, report exactly what is
   missing, what it unlocks, and which targets remain possible. Never
   improvise a silent fallback: no HTML renamed to `.epub`, no engine
   swap without telling the human, no skipping the bibliography because
   the compile step failed. Partial delivery is fine when it is explicit
   ("DOCX and EPUB built; PDF needs a LaTeX engine — install one or I can
   use the pdf skill if it is available").
5. **Report what was produced**: one summary with each artifact's
   absolute path, size, the verification performed and its result, and
   any check skipped for a missing tool — named, not glossed.

## Toolchain detection — run first

Check availability before promising targets:

- `pandoc --version` — required for every profile except `product-docs`.
- PDF engine, in preference order: `tectonic`, `xelatex` (via `latexmk`
  when present), `lualatex`, `pdflatex`. Record which exists.
- Optional verifiers: `epubcheck`, `pdfinfo`.
- Document skills: when a `docx` or `pdf` skill is available in the
  session, it is a legitimate alternative for those targets. Prefer
  pandoc when it is installed (single command, reproducible, keeps the
  build scriptable); reach for the skills when pandoc or a PDF engine is
  missing, or when the human wants layout control pandoc does not offer.

Present the resulting capability matrix with the target confirmation.

## Preflight — every profile, before any target

```bash
python scripts/sync_manuscript.py --check          # or drop --check to rebuild
python scripts/lint_render.py --fail-on critical   # BLOCKS the build
python scripts/validate_claim_index.py --quiet     # warns, never blocks
```

**`lint_render` blocks.** Its critical class is small and unarguable: a paragraph
with a `---` directly under it prints as an H2 heading, an unclosed fence turns
the rest of the document into code, an unclosed HTML comment eats visible text.
All three read perfectly in the source, which is why one of them shipped in a
book that had passed four technical audits. Fix the source, never the output.

**`sync_manuscript --check` drifting** means someone hand-edited `manuscript.md`.
It is derived; `final/` is the source of truth. Rebuild it, and find out who
edited the derived file before you rebuild over their work.

**`validate_claim_index` warns and does not block.** A hard gate on prose gets
switched off within a week, and then there is no warning either. But print its
`PROPAGATE` lines with the build report: shipping a document whose claim set is
known to be internally inconsistent should be a decision somebody made, not a
thing that happened.

Until now this preflight existed only for `product-docs`. Every other profile
handed `manuscript.md` straight to pandoc with no lint at all — including the
pipeline's own handoff comments (`<!-- EDITOR`, `<!-- VOICE-RISK`,
`<!-- PROOFREADER log`), which flow into `final/` by design and had nothing
stopping them at the door.

## Shared preparation

- Generate `build/metadata.yaml` from `bible/meta.yaml`: title, subtitle,
  author, `lang`, date, rights. Show it to the human once — this becomes
  the title page and ebook metadata.
- Derive the output filename slug from the project title (lowercase,
  hyphens, no diacritics).

## Books (`book-technical`, `book-literary`) — EPUB / PDF / DOCX

Input: `manuscript.md`.

**EPUB**

```
pandoc manuscript.md \
  --metadata-file=build/metadata.yaml \
  --toc --toc-depth=2 --split-level=1 \
  -o build/<slug>.epub
```

Add `--epub-cover-image=<path>` when the human provides a cover. For
literary books use `--toc-depth=1` — the TOC lists chapters, not scene
headings.

**PDF** (needs a LaTeX engine)

```
pandoc manuscript.md \
  --metadata-file=build/metadata.yaml \
  --pdf-engine=xelatex \
  --toc --number-sections \
  -V documentclass=book -V geometry:margin=25mm \
  -o build/<slug>.pdf
```

Swap `--pdf-engine=tectonic` (or another detected engine) as available —
and say which one ran. Drop `--number-sections` for literary books:
numbered subsections in a novel are a typesetting bug, not a feature. Set
`-V mainfont=` only when the human names a font; never guess one.

**DOCX**

```
pandoc manuscript.md \
  --metadata-file=build/metadata.yaml \
  --toc \
  -o build/<slug>.docx
```

Add `--reference-doc=<template.docx>` when the human supplies a styling
template (publisher or personal).

## `corporate-guide` — DOCX / PDF with organization front matter

Input: `manuscript.md` plus the `organization` block in `bible/meta.yaml`
(`name`, `audience_role`, `internal_context`, `confidentiality`).

1. Generate `build/front-matter.md`: organization name, document title,
   intended audience (`audience_role`), version and date, and the
   confidentiality notice. If `organization.confidentiality` is set, the
   label must appear on the title page — internal documents get
   forwarded, the label travels with the file, and a build that drops a
   declared confidentiality marking is a defect, not a styling choice.
2. Ask for the organization's `reference.docx` branding template. Build
   with pandoc defaults if there is none — and say so in the report.

```
pandoc build/front-matter.md manuscript.md \
  --metadata-file=build/metadata.yaml \
  --toc \
  --reference-doc=<org-template.docx> \
  -o build/<slug>.docx
```

PDF: same inputs with the book PDF invocation (documentclass `report`
reads better than `book` for guides). Put the confidentiality notice in
running footers via the reference template (DOCX) or a small
`-V header-includes=` fancyhdr block (PDF) when the human wants it on
every page.

## `product-docs` — validated markdown tree

No concatenation, no pandoc by default. The deliverable is a tree a
static site generator can ingest.

1. Confirm the layout with the human: flat `build/docs/` or grouped by
   tag/section, and the slug convention (from article frontmatter unless
   the outline provides explicit slugs).
2. Copy each `final/unit-NN.md` to `build/docs/<slug>.md`.
3. **Lint every article — failures block the build:**
   - Frontmatter exists and has non-empty `title`, `description`, and
     `tags`.
   - Every internal link resolves to a file in the built tree. A link to
     a `unit-NN` name is a defect — internal pipeline naming must never
     leak into the shipped tree.
   - Every `related:` entry resolves to an existing article.
   - Exactly one H1 per article, matching or compatible with the
     frontmatter title.
4. Generate `build/docs/index.md` from the outline: grouped article list
   with title and description per entry.
5. On lint failure: fix at the source in `final/` (through the human) and
   rebuild. Never patch the copy in `build/`.
6. Report a per-article table: article, slug, lint result.

## `scientific-paper` — LaTeX + .bib + PDF

Input: `manuscript.md`, `bible/claims-map.yaml`,
`bible/sources/sources.md`, `citation_style` from `bible/meta.yaml`.

1. **Generate `build/references.bib`** from the claims map and the
   sources index: one BibTeX entry per source the manuscript cites, with
   citation keys equal to the stable source IDs from `sources.md`. Every
   visible citation in the manuscript must map to a bib entry —
   `citation_check` enforced this during writing; re-verify at build time
   and stop on any orphan (report it, never fabricate an entry).
2. **Detect the citation encoding** in the manuscript:
   - Pandoc citation keys (`[@key]`) present → build with `--citeproc`
     and a CSL file matching `citation_style`. If no matching CSL file is
     available locally, fall back to `--natbib` (author-year styles) or
     `--biblatex` (numeric styles) and tell the human which formatting
     authority actually ran — the rendered punctuation may differ from
     the declared style.
   - Literal formatted citations in prose → do not run citeproc over
     them. Generate the References section from the claims map + sources
     in the declared style, and still emit `references.bib` — journals
     and submission tooling want it even when the PDF does not use it.
3. **LaTeX**:

```
pandoc manuscript.md \
  --metadata-file=build/metadata.yaml \
  --standalone --natbib \
  --bibliography=build/references.bib \
  -o build/paper.tex
```

(Swap `--natbib` for `--biblatex` or `--citeproc` per step 2.)

4. **PDF**: `latexmk -pdf -interaction=nonstopmode -output-directory=build
   build/paper.tex`, or `tectonic build/paper.tex`. If neither is
   available, deliver `paper.tex` + `references.bib` and say what is
   needed to compile — a valid LaTeX source is a legitimate deliverable
   (many venues want exactly that), an uncompiled one passed off as
   "done" is not.
5. **Verify the compile log**: no unresolved citations or references
   (grep the log for `undefined` warnings; grep the output text for
   `??`), and the bibliography actually rendered in the declared style.

## Verification (every target, before reporting done)

- **EPUB**: run `epubcheck` when available. Otherwise verify structure —
  valid zip, `mimetype` as first entry, `META-INF/container.xml`
  present — and report that only the structural check ran.
- **PDF**: file exists and is non-trivial in size; page count via
  `pdfinfo` when available; open it (or ask the human to) before calling
  the target done.
- **DOCX**: valid zip containing `word/document.xml`.
- **Markdown tree**: the lint table is fully green.

A target is "produced" only after its verification passes. Anything less
goes in the report as "built, not verified — because <missing tool>".
