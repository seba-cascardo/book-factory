# Unit 02 — the clean fixture

This file must produce **zero** critical and **zero** major findings. It exists to
catch the opposite failure from `unit-01.md`: a check that fires on correct prose
is worse than one that misses, because it trains everybody to ignore the output.

Every construct here is legitimate and resembles something the other fixture
gets flagged for.

## A thematic break, correctly spaced

The paragraph below is followed by a horizontal rule with a blank line above it,
which is a thematic break and not a Setext heading.

---

## A well-formed table

| Column A | Column B |
|---|---|
| one | two |
| three | four |

## A closed comment and a legitimate SOURCE marker

<!-- an ordinary comment, properly closed -->

<!-- SOURCE: spec.md §4.2 -->
The invisible citation policy puts SOURCE comments in shipped prose deliberately,
so this must not be reported.

## Code with a language tag

```sql
LOAD Name RESIDENT Staging;
```

## The same rule, obeyed

Any function call on a loaded field breaks the optimized path. The load below
therefore does no transformation at all, and the shaping happens downstream.

```sql
LOAD Name, Timestamp RESIDENT Staging;
```

## Heading levels in order

### A third-level heading under a second-level one

Nothing here should be reported.

## The staging table claim

Once the optimized load finishes, the staging table is dropped and released by
the engine, so a resident load that names the staging table after that point
finds nothing and fails.

## The optimized path claim

Any function applied to a loaded field moves the engine off the optimized path
onto the row-level path, and on a large staging table that costs an order of
magnitude.
