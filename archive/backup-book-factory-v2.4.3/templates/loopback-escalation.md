# Escalation — Chapter [NN]: [Title]

<!-- Produced by the skill when retries.by_chapter[ch-NN] >= retry_cap
     AND the next verdict would not be PASS. See
     references/loopback-handoff.md. -->

**Chapter**: [NN] — [Title]
**Pipeline mode**: [fast | full]
**Cycles used**: [N] / [retry_cap]
**Date**: YYYY-MM-DD

---

## Timeline

<!-- Every agent run and verdict, newest last. Keep it terse. -->

- Cycle 1: [agent] → [verdict] ([one-line reason]) → loopback to [target]
- Cycle 2: [agent] → [verdict] ([one-line reason]) → loopback to [target]
- Cycle 3 (blocked): retry cap reached.

## Per-cycle diff

<!-- For each cycle, one subsection. Don't paste prose — link artifacts,
     summarize diff. -->

### Cycle 1
- **Agent**: [Writer | Editor | Humanizer | ...]
- **Instruction**: [what this agent was asked to fix, one sentence]
- **Artifact**: `drafts/ch-NN/<file>.md` (at cycle 1)
- **Diff vs. previous**: +[N] / -[N] words, sections touched: [...]
- **Why next gate failed**: [one-sentence diagnosis from the next agent's report]

### Cycle 2
(...)

---

## Failure pattern (skill's diagnosis)

<!-- One and only one. See references/loopback-handoff.md §
     "Failure pattern" for the categories. -->

**Category**: [thrashing_on_same_hit | diverging_attempts | insufficient_grounding | outline_level_flaw | prose_vs_content_mismatch | unclassified]

**Observation**: [2–4 sentences describing the specific pattern seen in
this chapter. Include evidence — which rubric item keeps flagging, which
diff pattern repeats, etc.]

---

## Options

<!-- Exactly three. Each option is self-contained. Don't hedge; don't
     add a fourth; if three don't fit the situation, replace them. -->

### Option (a): [short name]

**What happens next**: [1–2 sentences]
**Cost estimate**: [which agents re-run; rough token cost as multiplier of a normal cycle]
**Risk**: [what goes wrong if this is the wrong pick]

### Option (b): [short name]

**What happens next**: [1–2 sentences]
**Cost estimate**: [...]
**Risk**: [...]

### Option (c): [short name]

**What happens next**: [1–2 sentences]
**Cost estimate**: [...]
**Risk**: [...]

---

## Recommendation

<!-- One paragraph. Skill takes a position. Explicit trade-off. -->

I'd go with option **(?)** because [reason]. The main thing you'd trade
away is [what the other options would have bought].

---

## Human decision

<!-- Human fills in this section. The skill watches for a non-empty
     value here and resumes. -->

**chose**: [a | b | c | custom | pause]

**notes** (optional):

<!-- If "custom", describe the path. If "pause", the chapter is parked.
     If a/b/c, optionally add modifications ("b, but add source X to
     bible/sources/ first"). -->
