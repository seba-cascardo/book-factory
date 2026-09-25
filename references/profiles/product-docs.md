# Profile — product-docs

Product documentation and knowledge bases: tutorials, how-to articles,
reference pages, explanations, troubleshooting — shipped as a docs site. Where
this file disagrees with an agent file on register or structure, this file
wins.

## Unit

An **article** (files `unit-NN`).

## Sequence: modular — strict

**No reading order exists: every article is the reader's first page.**

- Standalone: "as we saw", "in the previous article", "you already configured
  X" are critical fails (`modular-1`).
- Prerequisites are **linked** at the top, never assumed, never re-taught.
- Forward references are forbidden — link a related article instead.
- No digests (`bible/digests/` is not created); no running example across
  articles.
- Knowledge graph: terminology consistency only.
- Writing order: any; articles depend on the KG, glossary and outline, never on
  each other's text.

## Diátaxis type — one per article

Each article declares one type in its frontmatter (`type:`) and, when the
outline carries it, in its outline entry:

| `type` | Serves | Must not contain |
|---|---|---|
| `tutorial` | learning by doing, one guaranteed path | options, alternatives, theory beyond a line |
| `how-to` | a competent user's task | teaching basics, background essays |
| `reference` | lookup: complete, consistent, austere | instructions, opinions, narrative |
| `explanation` | understanding, context, why | step-by-step procedures |

Material of another type moves to its own article and is linked (`docs-3`).

## Register

Task-first, terse, neutral; the reader is mid-task, possibly mid-failure.
Second-person imperative for steps. Motivation: one sentence at most, only when
the purpose is not obvious. No hooks, no stakes, no self-reference beyond the
task-first formula, no transformation promises. A warning states the actual
consequence and the recovery path. Version-specific behaviour is stated inline
("In version X and later…") and grounded — docs outlive releases.

## Openings and closings

- **Openings: task-first.** The first sentence states what the article shows
  or does (`docs-1`). Uniform openings are correct here: no rotation, `rhet-6`
  and `profile-3` are `not_applicable`.
- **Closings: related links only** — no recap, bridge or encouragement.
- **Callouts**: `Note` / `Warning` / `Tip`, factual.
- No exercises; the reader's task is the exercise.

## Citation policy: invisible

Ground in `bible/sources/` (specs, release notes, API references) with HTML
comments; every identifier is checked by `check_identifiers.py`. Behaviour only
the live product can confirm goes to the verification plan with
`needs: live-system`.

## Per-article frontmatter

```yaml
---
title:          # task-phrased: "Configure SSO with Okta"
description:    # one sentence, ≤ 160 characters
type:           # tutorial | how-to | reference | explanation
tags: []        # from the closed tag list defined in the outline
related: []     # slugs or unit ids
---
```

## Reader testing (optional)

`pipeline.reader_testing: true`: after the Humanizer, one isolated subagent
predicts 5–10 questions the primary persona would search for (from the outline
entry and persona only); a fresh isolated subagent answers them from
`humanized.clean.md` alone, quoting its evidence. The orchestrator writes
`drafts/unit-NN/reader-test.md`; the Critic scores `docs-2`.

## Rubric deltas

Base `references/rubric-nonfiction.md`, with:

- REPLACE `forward_refs` with `modular-1` (critical → Writer: zero forward
  references and zero assumed prior reading), `modular-2` (significant →
  Writer: prerequisites linked at the top, none re-taught or assumed),
  `modular-3` (significant → Writer: frontmatter complete, description ≤ 160
  characters, tags from the vocabulary, `related` resolves).
- `pedagogy-3`: related links only.
- `profile-3`, `rhet-6`, `outline-4`: `not_applicable`.
- `consistency-2`: enforced against the KG across the whole tree.
- ADD `docs-1` (significant → Editor) — the first sentence states the task or
  outcome.
- ADD `docs-2` (significant → Writer; `not_applicable` without reader testing)
  — every predicted question in scope is answered by the article.
- ADD `docs-3` (significant → Writer) — quadrant purity: the article stays
  within its declared Diátaxis `type`.

## Reader-POV personas

**Primary**: a user from a search engine with an urgent task, error on screen,
zero patience, nothing else read. Report time-to-answer, assumed context that
broke them, and whether the steps work from a cold start. **Optional second**
(enable in `meta.yaml`): a skimming evaluator judging the product — what
impression the article leaves, what they looked for and missed.

## Phase 4: cross-article audit and index — no manuscript

1. **Consistency audit**: terminology against the KG, callouts and step
   formatting, frontmatter integrity, `type` distribution, and duplicated
   content — two articles half-answering one question is worse than either.
2. **Index**: by tag, by task and by type; no dead links, no article
   unreachable from the index or any `related` list.

## Build targets

A markdown tree with frontmatter for a static site generator
(`references/build-export.md`); navigation belongs to the generator.
