# Profile — product-docs

Product documentation / knowledge base: how-to articles, reference pages,
troubleshooting guides that ship as a docs site. Every agent loads this file
at the start of its turn; where it disagrees with an agent file on register
or structure, this profile wins.

## Unit

Files use `unit-NN`. The human-facing word is **article**.

## Sequence: modular — STRICT

The defining constraint: **no reading order exists.** Every article is the
reader's first page. Everything below follows from that.

- **Every article is standalone.** It never assumes any other article was
  read. "As we saw", "in the previous article", "you already configured X"
  are all critical fails (`modular-1`).
- **Prerequisites are LINKED, never assumed and never re-taught.** If a
  task needs prior setup, say so at the top with a link to the article that
  covers it. Re-teaching inline bloats every article and forks the content;
  assuming strands the reader.
- **Forward references are FORBIDDEN.** Not "declared and paid off later" —
  there is no "later" in a modular tree. Link to a related article instead.
- **No digests.** There is no previous unit to digest; `bible/digests/` is
  not created. Cross-article consistency comes from the knowledge graph and
  the Phase 4 audit, not from narrative memory.
- **No running example thread.** Each article's examples are self-contained.
  A thread across articles would silently impose the reading order this
  profile forbids.
- **Knowledge graph: terminology consistency only.** It exists so the whole
  KB calls the same thing by the same name — not to sequence concepts or
  track pedagogical dependencies.
- **Writing order: any.** Articles depend only on the KG, glossary, and
  outline — never on each other's text — so units can be drafted in any
  order and in parallel.

## Register

Task-first, terse, neutral. The reader is mid-task, possibly mid-failure,
and every sentence they must read before the answer costs them.

- Second-person imperative for steps ("Click", "Run", "Set").
- Motivation is one sentence maximum, and only when the task's purpose is
  genuinely non-obvious. No scene-setting, no stakes, no hooks.
- No self-reference beyond the task-first formula, no reader-transformation
  promises, no dramatized consequences. A warning states the actual
  consequence and the recovery path.
- Version-specific behavior is stated inline ("In version X and later...")
  and grounded against `bible/sources/` — docs outlive releases, and an
  unversioned claim is a future bug report.

## Openings and closings

- **Openings: task-first.** The first sentence states what the article
  shows or does: "This article shows how to configure X." Predictability
  is a feature here — a searcher confirms relevance in one line or bounces.
  The voice-profile opening rotation does NOT apply; uniform openings are
  correct in docs, so `rhet-6` is `not_applicable` (there is also no
  "previous unit" for it to compare against).
- **Closings: related-links only.** A short "Related" list of linked
  articles. No recap (the article IS the summary), no bridges, no
  encouragement.
- **Callouts**: standard docs set — `Note` / `Warning` / `Tip`, defined at
  setup. Warnings are factual, per the register rule.
- **No exercises**, no practice items. The reader's task is the exercise.

## Citation policy: invisible

Ground claims in `bible/sources/` (product specs, release notes, API
references) and cite in HTML comments per the Writer's contract. Rendered
articles show no citation apparatus.

## Per-article frontmatter

Every `final/unit-NN.md` opens with YAML frontmatter. The Writer drafts it,
the Editor verifies it structurally, Phase 4 audits it tree-wide.

```yaml
---
title:          # task-phrased: "Configure SSO with Okta"
description:    # one sentence for search results, ≤ 160 characters
tags: []        # from the controlled vocabulary in meta.yaml
related: []     # articles this links to (slugs or unit ids)
---
```

## Rubric deltas

- REPLACE the `forward_refs` family with:
  - `modular-1` — zero forward references and zero assumptions of prior
    reading. Countable: grep for "as we saw", "previous article", "earlier
    we", "later we'll", "we'll cover". **critical**.
  - `modular-2` — prerequisites linked at the top; none re-taught inline,
    none silently assumed. **significant**.
  - `modular-3` — frontmatter present and complete; description ≤ 160
    chars; tags from the controlled vocabulary; related links resolve.
    **significant**.
- `pedagogy-3` (closing matches profile policy): related-links only; a
  recap or bridge closing fails.
- Base `profile-1/2` (register, citation policy) apply. Base `profile-3`
  (opening in rotation): `not_applicable` — the opening is fixed task-first,
  not rotated. This profile ADDS its own `docs-*` id family (never reusing
  `profile-N` — see `references/rubric.md` § Profile compliance):
- ADD `docs-1` — opening is task-first: the first sentence states the
  task or outcome. **significant**.
- `rhet-6` — `not_applicable` (see Openings).
- `outline-4` (exercises) — `not_applicable`.
- `consistency-2` (terminology) is enforced against the KG across the whole
  tree, not against adjacent units — adjacency means nothing here.

## Reader-POV personas

**Primary (always)**: a user who landed from a search engine with an urgent
task — mid-configuration, error on screen, zero patience. They have read
nothing else in the KB. Report: time-to-answer (how far they scrolled
before the fix), any assumed context that broke them, and whether the steps
work as written from a cold start.

**Optional second** (enable in `meta.yaml`): a skimming evaluator —
someone assessing the product itself, skimming articles to judge capability
and quality. Report: what impression of the product the article leaves and
what they looked for but could not find.

## Phase 4: cross-article audit + index — NO manuscript

product-docs never concatenates into `manuscript.md`. Concatenation is a
book operation; a KB's integrity is graph-shaped, not linear. Phase 4 is:

1. **Cross-article consistency audit**: terminology against the KG, callout
   and step formatting, frontmatter integrity, and duplicated content —
   two articles half-answering the same question is worse than either
   alone, because the searcher finds the wrong half.
2. **Index build**: generate the KB index (by tag and by task) and verify
   the related-links graph — no dead links, no orphan articles unreachable
   from the index or any `related` list.

## Build targets (Phase 5)

A markdown tree with frontmatter, ready for a static site generator:
`final/` mirrored to `build/docs/` with slugged filenames, the generated
index, and the tag/related graph intact. No page numbering, no ordering —
navigation belongs to the SSG. Details in `references/build-export.md`.
