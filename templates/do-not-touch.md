# bible/do-not-touch.md — auto-refutation anchors

<!--
WHAT THIS IS

A short list of passages that have been checked, found correct, and must not be
"fixed" again. Every entry names the passage, the source that settles it, and a
verbatim quote from that source.

WHY IT EXISTS

A review system that can only record defects loses its positive knowledge the
moment a report is filed. The next pass reopens the settled question, reaches a
different conclusion, and edits correct text into incorrect text. That is not a
hypothetical: on 2026-07-29 in the project this design comes from, a fix pass
"corrected" three items that were already resolved, and in one case introduced a
factual error into a passage that was right. All reverted the same day — but only
because someone happened to remember.

The structural fix is to make "verified correct" a first-class, persisted result.
This file and the `verified_against` / `do_not_touch` fields in
`bible/claim-index.yaml` are the two places it lives.

HOW IT IS USED

- The manuscript gate copies these entries verbatim into the GROUNDING.md it
  hands every auditor. A finding against one of these passages is REFUTED by
  default.
- `scripts/validate_claim_index.py` surfaces the flag on any PROPAGATE warning
  touching the concept, so the guard travels with the warning.
- Any fix pass, at any time, reads this before editing.

RULES FOR WRITING AN ENTRY

1. **Never write an entry without its counter-evidence.** An anchor with no
   reason is just an assertion, and the next auditor will overrule it — correctly.
2. **Quote the source verbatim.** "Verified against the docs" is not an anchor.
   `path:line` plus the sentence is.
3. **Say what the wrong reading was**, if there was one. The near-miss is the
   most useful part: it tells the next reader what trap to avoid, not just what
   the answer is.
4. **Anchors expire when the pinned version changes.** A behavior verified
   against version X is not verified against version Y. Note the pin.

Delete this comment block and the example when the first real entry lands.
-->

## Anchors

### `final/unit-NN.md:LINE` — [one-line description of the claim]

**Verified against** `bible/sources/<path>.md:LINE`, pinned to `[version]`:

> "[verbatim quote from the authoritative source]"

**What it actually says:** [the correct reading, stated plainly]

**The wrong reading:** [the plausible misreading, and what it would change —
this is the part that stops the next auditor from repeating it]

**History:** [if this was mis-"fixed" before: what happened, when, what the
damage was, when it was reverted]

A finding against this line is **REFUTED** unless it brings a citation from an
authoritative source that contradicts the page quoted above.

---

<!-- Example of a filled entry, from the reference case:

### `final/ch-03.md:17` — the optimized/standard/source hierarchy

**Verified against** `bible/sources/manage-data/manage-data.md:12177`, pinned to
May 2025:

> "Optimized mode is about 10 times faster than standard mode, or about 100
> times faster than loading the database in the ordinary fashion."

**What it actually says:** the 100× is against **the database**, not against
standard mode. Two different baselines, two different figures, both correct.

**The wrong reading:** treating both figures as measuring the same thing, which
makes them look contradictory and invites "fixing" one of them.

**History:** on 2026-07-29 someone "corrected" this to "up to 100 times faster
than standard mode" — a factual error. Reverted the same day. This is the entry
that motivated the whole file.

-->
