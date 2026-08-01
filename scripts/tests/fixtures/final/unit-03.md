# Unit 03 — the sibling fixture

This file exists so the corpus contains what a real book contains and a toy
fixture usually does not: **the same claim, restated in different words, in a
different unit**.

That is the shape the claim index is built for. A well-written book rephrases
instead of repeating, which is why n-gram overlap finds nothing and why the
similarity metric works on content terms instead. These passages are worded
deliberately differently while asserting the same thing.

## The staging table claim, restated

The staging table is dropped once the optimized load completes, so any resident
load that references the staging table afterwards fails. The engine has already
released it and there is nothing left to read.

## The optimized path claim, restated

Applying any function to a loaded field forces the engine off the optimized path
and onto the row-level path, which is slower by an order of magnitude on a large
staging table.

## The write atomicity claim

A store writes the entire file every time, unconditionally. There is no modifier
that asks the engine to append rows to an existing file, and readers never
observe a partially written file.

## A rule that demonstrates its construct instead of naming it

The date literal inside a set modifier must always be written as
`{<OrderDate={'2024-01-01'}>}` and never as a bare number. This rule names no
keyword and no function — it shows the shape. An extractor that requires a named
construct skips it, and the defect it guards becomes invisible.

## The same atomicity claim, worded differently

Every store operation replaces the whole target file rather than appending to
it, and a reader either sees the previous complete file or the new complete
file, never a partial one.
