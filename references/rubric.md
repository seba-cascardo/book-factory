# Rubric — core: scorecard, verdict, Critic protocol

The Critic's verdict is computed, not asserted: every check is a scorecard row,
every row carries evidence, and the verdict is a deterministic function of the
rows. This file is the **only** home of the verdict computation — every other
file points here. Why: `docs/rationale/pipeline.md#computed-verdict`.

The Critic loads this file plus **exactly one** family file:

| Profiles | Family file |
|---|---|
| `book-technical`, `corporate-guide`, `product-docs`, `scientific-paper` | `references/rubric-nonfiction.md` |
| `book-literary` | `references/rubric-literary.md` |

A project runs one family file, so ids never collide inside a scorecard.

## Artifacts

- `drafts/unit-NN/scorecard.yaml` — the machine-readable truth
  (`templates/scorecard.yaml`).
- `drafts/unit-NN/critique.md` — the human render plus Observations
  (`templates/critique-report.md`). No verdict authority of its own.
- `drafts/unit-NN/checks.json` / `checks.md` — script counts, written by
  `python scripts/pipeline_step.py checks unit-NN` before the Critic runs.

## Scorecard entry schema

Every entry has exactly these fields:

- `id` — stable identifier (`scope-1`, `rhet-3`, `craft-5`).
- `rubric` — the family.
- `name` — one line: what was checked.
- `severity` — `critical | significant | minor`.
- `status` — `pass | fail | not_applicable` (N/A carries a one-line reason).
- `evidence` — fails: quoted lines, `file:line`, or a one-sentence diagnosis.
  **Counted items** (any item whose definition names a `checks.json` field)
  always carry the number copied from `checks.json`, pass or fail.
- `loopback_target` — fails only: `Writer | Editor | Humanizer | escalate`.

## Verdict computation — AUTHORITATIVE

```
if any failing item has loopback_target == escalate:
    verdict = ESCALATE
elif count(critical fails) >= 2:
    verdict = REWORK            # back to Writer, fresh draft
elif count(critical fails) == 1:
    verdict = REVISE
elif count(significant fails) >= 1:
    verdict = REVISE
elif count(minor fails) >= 3 and tolerance == full:
    verdict = REVISE
elif any minor fails:
    verdict = PASS, with notes
else:
    verdict = PASS
```

`tolerance` is `full` for nonfiction `full` mode and for `book-literary`;
`fast` otherwise (minor fails never force a loop in fast mode — the polish pass
sweeps them).

**REVISE target**, resolved from the failing items:

1. All failing items share one target → that target.
2. Targets split → the target of the highest-severity failing item.
3. Still tied → Writer (content outranks structure outranks prose).

REWORK always targets the Writer. The Critic chooses neither verdict nor
target; both fall out of the rows. If the verdict feels wrong, the fix is in a
row's status and evidence, never in the header.

`scripts/bookkit/verdict.py` implements exactly this computation: `pipeline_step.py
done unit-NN critic` recomputes the verdict and target from `scorecard.yaml`,
and a `critique.md` header or `computed_verdict` that disagrees — or a scorecard
with no rows — fails the Critic's contract (exit 4). `check unit-NN
proofreader` reads the recomputed verdict, not the header.

## Override layers — apply before scoring

1. `references/profiles/<profile>.md` § Rubric deltas — adds items (own id
   namespace only: `paper-*`, `corp-*`, `docs-*`, `modular-*`), removes items,
   or changes severities. Never redefines a base id.
2. `bible/voice-profile.md` — the ```` ```yaml ```` fence containing
   `rhetoric_budget:` overrides `rhet` quotas only, in either direction.
   `count_rhet.py` reads the same fence, so the quota in `checks.json` is
   already the project's quota.

## `rhet` — rhetoric budget (counted by script)

Every device looks justified alone; the aggregate is the tell. These are quotas
with counts, never per-instance judgement calls. Counts come from
`checks.json → counts.<id>` (`count_rhet.py`: code fences, tables, HTML comments,
headings and — literary — dialogue are already excluded; lists come from
`scripts/lexicons/<lang>.yaml` plus `bible/lexicon.yaml`).

| id | sev | default quota | what the script reports · what the Critic adds | loopback |
|----|-----|---------------|-----------------------------------------------|----------|
| rhet-1 | significant | ≤ 2 | Rhetorical questions in prose (`counts.rhet-1`, with lines). Questions the text answers at once count too. | Humanizer |
| rhet-2 | significant | ≤ 1 | "Not X but Y" reframes (`counts.rhet-2`, lexicon `not_x_but_y`), with the matched lines. | Humanizer |
| rhet-3 | significant | ≤ 2 | Dramatic-danger lexicon (`counts.rhet-3`, lexicon `danger`). All hits count; the quota absorbs legitimate uses. | Humanizer |
| rhet-4 | significant | 0 when the closing policy is recap or none | Tease closing (`counts.rhet-4.hit` + closing text, lexicon `tease_closings`). The Critic confirms against the closing policy. | Humanizer |
| rhet-5 | minor | ≤ 8 per 1000 words | Bold density (`counts.rhet-5.per_1000`). | Humanizer |
| rhet-6 | significant | — | Opening structure differs from the previous unit's. **Judged, not counted**: actual opening vs the Writer's declared structure (draft self-assessment) vs the previous unit's (its scorecard evidence or digest). First unit auto-passes. Evidence records both structures. | Writer |
| rhet-7 | minor | — | Template headings (`counts.rhet-7.headings`, lexicon `template_headings`). The Critic judges each: earned only if its body names this unit's concepts and concrete actions. | Writer |

Literary runs `rhet-2` only (`references/rubric-literary.md`). A `rhet` row
with no count in evidence is invalid.

## Critic protocol

1. **Read `checks.md` first**, then the unit.
2. **Write `## Most important problem:` before scoring** — one sentence, with
   its location: the single change that would most improve this unit. Commit
   to it before the checklist can anchor you. It leads the loopback
   instructions on any non-PASS.
3. **Score every applicable row.** Counted rows copy the number from
   `checks.json`. If you believe a count is wrong, say so under Observations
   with the evidence — never override a script count in a row.
4. **Praise only when tied to a quoted line.** "Strong voice" with no quote is
   not evidence and does not appear.
5. **Compute** the verdict and target per § Verdict computation.
6. **Loopback instructions**: one prioritized instruction first (the most
   important problem), then the remaining failing items with locations and
   what "resolved" looks like — never replacement prose.
