# Loopback Handoff — Structured Escalation

The retry cap in `pipeline.retry_cap` exists because uncapped loopbacks
mean "the pipeline and the human are both confused and neither is
converging." At that point, burning more agent tokens doesn't help. The
human needs the *right information* to decide what to do next.

v2.2 auto-escalated to "ask the human" — too vague. v2.3 requires a
**structured handoff packet** with a diff between attempts, a clear
reason per loopback, and three concrete options for the human to pick
from. This turns escalation from a frustrating "it failed, over to you"
into a useful "here's what we tried, here's why each failed, here's
what I'd try next — pick one."

## When the handoff is triggered

- `retries.by_chapter[ch-NN] >= pipeline.retry_cap` AND
- The next verdict from the Technical Reviewer or Critic is NOT PASS.

On the firing event, the skill pauses the pipeline for this chapter,
produces `drafts/ch-NN/escalation.md` from `templates/loopback-escalation.md`,
and surfaces it to the human. No further agent calls for this chapter
until the human responds.

The human response goes into `drafts/ch-NN/escalation.md` under
`## Human decision` and reset-unblocks the chapter. See "Human
responses" below.

## What the packet contains

`drafts/ch-NN/escalation.md` — follow the template exactly. The fields
are:

### 1. Summary block
- Chapter number, title, cycles used, cap value.
- Timeline of cycles (agent → verdict → loopback target).

### 2. Per-cycle diff
For each cycle the chapter went through:
- Which agent ran.
- What the prior verdict asked them to fix.
- What they produced (link to the artifact, not the prose inline).
- Diff summary vs. the prior cycle (file, lines changed, net +/-).
- Why this cycle did NOT satisfy the next gate.

This is the part that usually reveals the real problem: the diff shows
"Writer added 200 words of motivation" twice in a row and the Critic
still failed on motivation, which means the real problem is *not*
motivation — it's that the concept can't be taught here at all.

### 3. Failure pattern (skill's diagnosis)
The skill classifies the escalation by shape. One and only one of:

- **Thrashing on the same hit** — the same rubric item is failing every
  cycle; each attempted fix regresses a different item. Signal: the
  problem is not what the Critic named.
- **Diverging attempts** — each cycle addresses the hit but introduces
  new issues. Signal: the chapter is not bounded well; the outline beat
  is too big.
- **Insufficient grounding** — the chapter keeps hitting "claim
  unverifiable" or "model unclear" and no amount of rewriting resolves
  it. Signal: the bible/sources library is missing the right source OR
  the writer+reviewer don't have expertise on this topic.
- **Outline-level flaw** — a forward reference that can't be satisfied
  because the concept truly hasn't been taught yet. Signal: Knowledge
  Graph gap, outline needs revision upstream.
- **Prose vs. content mismatch** — Critic keeps routing to Humanizer but
  the issue is actually structural (or vice versa). Signal: the loopback
  rules misclassified the problem.
- **Unclassified** — rare. Describe what was observed; ask the human to
  categorize.

### 4. Three concrete options

The skill proposes three (not more, not fewer) paths forward. Each option
has:
- **What happens next** (1–2 sentences).
- **Cost estimate** (which agents run, rough token cost vs. the chapter's
  average).
- **Risk** (what goes wrong if this is the wrong choice).

The three options are usually shaped by the failure pattern:

| Pattern                    | Typical options                                                  |
|----------------------------|------------------------------------------------------------------|
| Thrashing on same hit      | (a) change the Critic rubric weight on this item; (b) rewrite the chapter with a narrower scope; (c) escalate to the bible — the style guide may be self-contradictory. |
| Diverging attempts         | (a) split chapter into two; (b) Writer re-drafts with explicit scope list; (c) human drafts the contentious section inline. |
| Insufficient grounding     | (a) add a source to bible/sources/; (b) SME session with the human to capture verbal context; (c) downgrade the claim to hedged language and move on. |
| Outline-level flaw         | (a) revise outline (introduce missing concept earlier); (b) add a "primer" section within this chapter; (c) merge two chapters. |
| Prose vs. content mismatch | (a) re-run with corrected routing; (b) bypass the Critic with human judgment on this one; (c) switch modes for this chapter. |
| Unclassified               | (a) continue one more cycle manually; (b) human decides; (c) archive draft and restart fresh. |

If none of the templated options fit, the skill replaces them — but
always exactly three, always concrete.

### 5. What the skill recommends

One paragraph, one recommendation, explicit trade-off. Example:

> "I'd go with option (b) — rewriting chapter 7 with a narrower scope
> excluding the `deferred handlers` mechanic. The failure pattern is
> thrashing on motivation, which usually means the section is trying to
> teach too much at once. Option (a) might mute the symptom without
> fixing it."

The human can override, but the recommendation forces the skill to take
a position rather than hedging.

## Human responses

The human edits `drafts/ch-NN/escalation.md` under `## Human decision`
with one of:

- `chose: a | b | c` — proceed with the picked option.
- `chose: custom` with a prose description of what to do instead.
- `chose: pause` — park the chapter; the skill marks it `on_hold` in
  `project-status.yaml` and unblocks the rest of the book to continue.

After response:
- `retries.by_chapter[ch-NN]` is reset to 0 (the chosen path is a fresh
  attempt, not a continuation of the failed ones).
- The escalation event is logged in `retries.cap_hits` and under
  `notes:` in `project-status.yaml`.
- The pipeline resumes per the chosen option.

## Why three options, not one

One option is a command; the human will either accept or not, with no
grounding. Three options force the skill to show the *space* of responses.
The human often picks option B but with a modification — "B but also do
what A suggested for the grounding library." That's the point. The
three-option form invites a real decision instead of a rubber-stamp.

## Example escalation (abridged)

```
# Escalation — Chapter 7: Set Analysis Deep Dive

Cycles used: 2 / 2. Next verdict would be cycle 3.

## Timeline
- Cycle 1: Writer → Tech Reviewer REVISE (mental-model break) → Writer
- Cycle 2: Writer → Tech Reviewer PASS → Editor → Critic REVISE
  (Humanizer in fast mode = Writer — reader would be confused by section 3)
- Cycle 3 (blocked): cap reached.

## Failure pattern
Thrashing on same hit. Reader-confusion flag survives both rewrites;
Writer each time adds more explanatory prose, which the Critic then
flags as signposting. The chapter is fighting itself.

## Options

### (a) Adjust Critic weight
Lower the signposting rubric weight for this chapter. Fast; risks
publishing signposty prose.

### (b) Split the chapter
Chapter 7a (set analysis basics) + 7b (indirect set analysis). Medium
cost (rewrite both); addresses the real density problem.

### (c) Human drafts section 3 inline
You write the confusing section, the pipeline picks up from your draft
at Tech Review. Cheapest; depends on your bandwidth.

## Recommendation
(b). The thrashing pattern says the section is too dense, not too
signposty. Splitting gives both halves room to motivate before teaching.
```

That's the shape. Concise, diagnostic, actionable — not a dump.
