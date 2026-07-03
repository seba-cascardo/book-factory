# Sources — [Project Name]

Grounding library for the Technical Reviewer (Axis B; nonfiction profiles with
a source library). For `scientific-paper` it is also the backing store for
Axis C — reference integrity — and the source of bibliographic metadata for
the Phase 5 `.bib`.

Save to `bible/sources/sources.md`. Put the actual source files — PDFs,
extracted markdown, figures, transcripts, excerpts — in the same folder
alongside this index. Files use `unit-NN`; say chapter / section to the human
per the profile.

---

## How this file works

The Technical Reviewer reads this index when running Axis B (mental models,
framings, terminology) to know:

1. Which sources are available for this project.
2. Which topics each source is authoritative on.
3. Which sources the author knows to be wrong, outdated, or biased (so the
   reviewer does not defer to them blindly).
4. Which sources cover a different version than the one the document teaches
   (version drift).

Without this index, the Technical Reviewer has no grounding library to check
Axis B against and returns a PASS on Axis B with a "skipped — no grounding
library" note. That is not a silent pass; it propagates to the Critic and to
the human. Axis A (claims, code, versions) still runs.

**scientific-paper.** The paper profile uses **visible** citations formatted
per `meta.yaml → citation_style` (apa | ieee | vancouver | author-year), plus
the pipeline's `<!-- SOURCE: source_id §locator -->` comment on load-bearing
citations. Entries here supply the bibliographic metadata the Phase 5 build
joins with `bible/claims-map.yaml` to emit the `.bib`, and they back the
Reviewer's Axis C check that every cited work exists, supports its sentence,
and is not retracted. When Zotero / arxiv / citecheck / openreview MCP tools
are connected, setup and the Reviewer may populate and verify entries through
them; otherwise verify against the files in this folder and flag anything
unresolvable as `unverified`.

---

## Folder layout (expected by the reviewer)

Setup preprocesses raw PDFs so the Technical Reviewer can work efficiently at
unit scale. After setup, the folder looks like:

```
bible/sources/
├── sources.md                    ← this file
├── <source-stem>.pdf             ← original, kept for visual fallback
├── <source-stem>.md              ← extracted text (reviewer's primary read)
├── <source-stem>-figures/        ← extracted images (PNG per figure)
│   ├── fig-001.png
│   └── ...
└── ...
```

The reviewer prefers `.md` for text-based checks (claims, terminology,
framings) and falls back to the PDF or the `-figures/` folder when a figure,
diagram, or UI screenshot is load-bearing for the claim being checked.

If a source only exists as a `.md` (a notes file, a blog post archived to
markdown) that is fine — no PDF required. If a source only exists as a PDF and
extraction failed, note it in the source's entry with the reason.

---

## How to populate this folder

For each source:

1. Put the source file(s) in `bible/sources/`. Setup extracts raw PDFs to
   `.md` + figures automatically; for other formats (md, txt, internal docs)
   just drop the file. For papers, entries can also be added from a reference
   manager via the Zotero MCP when connected.
2. Add an entry to this index (format below).
3. Tag the topics the source is authoritative on, using terminology the
   Writer and Technical Reviewer will recognize from the outline.
4. Flag any version drift between the source and the target version the
   document teaches.

You do not need a massive library. A small, curated set of 3–10 trusted
sources is more useful than a dump of everything on the topic. Quality over
coverage.

---

## Entry format

```markdown
### [Short name — used by the Technical Reviewer in citations]

**Full title**: [title]
**Author(s)**: [names]
**Edition / year / version covered**: [edition, year, software version if any]
**Format**: [Full-text PDF + extracted .md + figures | md notes | external URL | other]
**File in this folder**: [filename.pdf (+ filename.md, filename-figures/), or "external" with URL]
**Bib metadata** (scientific-paper): [venue/journal, volume, pages, DOI — what
the Phase 5 .bib needs; omit for non-paper profiles]

**Authoritative for**:
- [topic area — be specific, e.g., "distributed systems primitives (ch-1–4 of
  the source)", not "distributed systems in general"]
- [topic area]

**Not authoritative for** (the author's judgment):
- [topic area, and why — e.g., "cloud-specific deploys — source is 2015 and
  predates current Kubernetes patterns"]

**Known to be wrong on / outdated on**:
- [specific claims or sections the author would not defer to]
- **Version drift**: [if applicable — see rule below]

**Version drift rule** (if the source covers a different version than the
document teaches):
> Source covers [version A], document teaches [version B]. In units covering
> [specific feature areas that changed between versions], treat source as
> advisory only — flag any divergence as "version drift, not error".

**How to cite when flagging a finding**:
- [e.g., "DDIA, §3.2" — whatever the reviewer should write in tech-review.md;
  for papers this is the SOURCE-comment locator, distinct from the visible
  citation the reader sees]
```

---

## Worked example 1 — classic reference book

```markdown
### DDIA

**Full title**: Designing Data-Intensive Applications
**Author(s)**: Martin Kleppmann
**Edition / year / version covered**: 1st ed., 2017
**Format**: Full-text PDF + extracted .md + figures
**File in this folder**: ddia-kleppmann-2017.pdf (+ .md, -figures/)

**Authoritative for**:
- Replication strategies (ch-5)
- Consensus and distributed transactions (ch-9)
- Stream processing mental models (ch-11)

**Not authoritative for**:
- Cloud-native specifics — book predates most managed-service patterns.

**Known to be wrong on / outdated on**:
- Specific performance numbers in ch-3 — hardware has moved on.
- Kafka-specific APIs — current Kafka has diverged.

**How to cite when flagging a finding**:
- "DDIA, ch-5 § 'Replication Logs'"
```

---

## Worked example 2 — vendor docs with version drift

```markdown
### QlikAdmin-Nov2023

**Full title**: Qlik Sense Enterprise on Windows — Administration Guide
**Author(s)**: Qlik (official documentation)
**Edition / year / version covered**: November 2023 release
**Format**: Full-text PDF + extracted .md + figures
**File in this folder**: qlik-admin-nov2023.pdf (+ .md, -figures/)

**Authoritative for**:
- Deployment topologies (single-node, multi-node, geo-distributed)
- Security rules and section access model
- Task scheduling and reload chains

**Not authoritative for**:
- Qlik Cloud / SaaS — this is the on-prem guide only.
- Front-end scripting best practices — the admin guide is infra-focused.

**Known to be wrong on / outdated on**:
- **Version drift**: document teaches Qlik Sense May 2024. Between November
  2023 and May 2024 the following changed:
  - Default authentication flow (IdP config)
  - Some section access resolution rules
  - New scheduling options in the task manager

**Version drift rule**:
> Source covers Qlik Sense November 2023, document teaches May 2024. In units
> on authentication, section access, or scheduling, treat source as advisory
> only — flag divergences as "version drift, not error" and defer to current
> docs or the SME.

**How to cite when flagging a finding**:
- "QlikAdmin-Nov2023, §[section from extracted .md]"
```

---

## Curation rules

1. **Sources are load-bearing.** If a source is not one you would stake a
   unit's correctness on, do not add it. The Technical Reviewer treats every
   source here as trusted unless you have flagged it otherwise.
2. **Coverage is topic-specific, not source-specific.** A great book on X is
   not a great book on Y. Flag which chapters/sections of each source are
   actually in scope.
3. **Version drift is the #1 hidden failure mode.** Vendor docs and official
   references are version-pinned whether or not they say so prominently. If
   the document teaches a newer version, catalogue every feature area that
   changed and flag it under the version drift rule. Otherwise the reviewer
   will cheerfully tell the Writer to "correct" behaviors that are just
   version-accurate.
4. **Update the "Known to be wrong on" list as you learn.** If during drafting
   you discover the source is wrong about something, log it here so future
   units don't defer to it on that topic.
5. **Non-English sources are fine.** The Technical Reviewer works in whatever
   language the sources are in. Flag the language in the entry if it is not
   English so the reviewer can cite appropriately.
6. **Internal / private sources are fine.** If the author has access to an
   unpublished report, internal benchmark, or similar, add it with a note that
   citations will be generic ("internal benchmark, May 2025"). For a paper,
   confirm the venue permits the citation form before relying on it.
7. **Sign-off is the SME's, not the assistant's.** A setup pass can propose
   draft entries from a TOC and cover pages, but `authoritative for`, `not
   authoritative for`, and `known to be wrong on` require human judgment.
   Don't publish a `sources.md` that hasn't been reviewed line by line by the
   SME.
