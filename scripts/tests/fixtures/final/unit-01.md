# Unit 01 — the defective fixture

Every defect below is deliberate. `scripts/selftest.py` asserts that each one is
found, so this file is a regression gate: if a check stops firing, the test fails
here rather than silently on a real book.

## Setext hazard

The next paragraph must render as an H2 heading, because the rule under it has no
blank line above. This is the single defect in this file that corrupts printed
output, and it is invisible in the source.

This paragraph is about to become a heading.
---

## Ragged table

| Column A | Column B | Column C |
|---|---|---|
| one | two | three |
| only | two |
| far | too | many | cells |

## Leaked pipeline comments

<!-- EDITOR: this handoff comment should never have reached a shipped file -->
The paragraph above carries scaffolding that belongs in drafts, not in `final/`.

<!-- SOURCE: spec.md §4.2 -->
This one is legitimate — the invisible citation policy puts SOURCE comments in
shipped prose on purpose, so the lint must NOT flag it.

## Heading level jump

#### This is an H4 directly under an H2

## A rule and the example that breaks it

Any function call on a loaded field breaks the optimized path. `Upper(Name)`,
`Floor(Timestamp)` — all of them.

```sql
LOAD Upper(Name) AS Name RESIDENT Staging;
```

## An instance that violates a rule stated in another unit

Unit 03 fixes the date-literal form inside a set modifier. This example uses a
bare number instead, which is the violation — and it lives in a different unit
from the rule, so no per-unit reviewer could have caught it.

```sql
SUM({<OrderDate={20240101}>} Amount)
```

## Unbalanced comment

<!-- this comment is never closed, and swallows everything after it
