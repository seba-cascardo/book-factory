# bible/do-not-touch.md — auto-refutation anchors

<!--
Passages that were checked, found correct, and must not be "fixed" again. Each
entry names the passage, the source that settles it, and a verbatim quote from
that source. Why: docs/rationale/gate.md#positives.

How it is used:
- The manuscript gate copies the `## Anchors` section into GROUNDING.md, which
  every auditor reads first. A finding against one of these passages is REFUTED
  by default.
- validate_claim_index.py surfaces the claim-index `do_not_touch` flag on any
  PROPAGATE warning touching the concept.
- Any fix pass reads this before editing.

Rules for an entry:
1. The `**Anchor:**` line is the key; the line number is a hint. It is a verbatim
   substring of the PROTECTED passage (not of the source). resolve_anchors.py
   resolves entries by anchor; `--heal` rewrites stale line numbers; an entry with
   no anchor is reported NO-ANCHOR. Why: docs/rationale/gate.md#anchors.
2. Never write an entry without its counter-evidence.
3. Quote the source verbatim: `path:line` plus the sentence.
4. Say what the wrong reading was — it is what stops the next auditor.
5. An anchor verified against version X expires when the pinned version changes.

Delete this comment and the example when the first real entry lands.
-->

## Anchors

### `final/unit-NN.md:LINE` — [one-line description of the claim]

**Anchor:** "[verbatim substring of the protected passage — unique in the file,
short enough to survive a neighbouring edit]"

**Verified against** `bible/sources/<path>.md:LINE`, pinned to `[version]`:

> "[verbatim quote from the authoritative source]"

**What it actually says:** [the correct reading, plainly]

**The wrong reading:** [the plausible misreading, and what it would change]

**History:** [if it was mis-"fixed" before: what, when, when reverted]

A finding against this passage is **REFUTED** unless it cites an authoritative
source that contradicts the page quoted above.

---

<!-- Example of a filled entry:

### `final/ch-03.md:17` — the optimized/standard/source hierarchy

**Anchor:** "about 100 times faster than loading the database"

**Verified against** `bible/sources/manage-data/manage-data.md:12177`, May 2025:

> "Optimized mode is about 10 times faster than standard mode, or about 100
> times faster than loading the database in the ordinary fashion."

**What it actually says:** the 100× is against the database, not standard mode.

**The wrong reading:** treating both figures as one baseline, which makes them
look contradictory and invites "fixing" one.

**History:** "corrected" to "100 times faster than standard mode" on 2026-07-29 —
a factual error, reverted the same day.
-->
