# Escalation — unit-[NN]: [Title]

<!-- Produced by the orchestrator on a retry-cap hit, the plateau rule (a
     cycle that resolved none of the previous cycle's failing rows), a Critic
     ESCALATE, or a second contract violation (done exit 4 twice). See
     references/loopback-handoff.md. Human-facing unit word per profile. -->

**Unit**: [NN] — [Title]
**Pipeline mode**: [fast | full | literary]
**Cycles used**: [N] / [retry_cap]
**Trigger**: [retry cap | plateau — failing set {…} unchanged or larger vs scorecard.c<N>.yaml | Critic ESCALATE — rows … | contract violation — agent, violations]
**Date**: YYYY-MM-DD

---

## Timeline

<!-- Every run and verdict, newest last; must reconcile with runs.tsv.
     Include adversarial-confirmed REVISEs and human rejections — each spent a
     retry. -->

- Cycle 1: [agent] → [verdict] ([one-line reason]) → loopback to [target]
- Cycle 2: [agent] → [verdict] ([one-line reason]) → loopback to [target]
- Cycle 3 (blocked): retry cap reached.

## Per-cycle diff

<!-- For each cycle, one subsection. Do not paste prose — link the artifact,
     summarize the diff. -->

### Cycle 1
- **Agent**: [Writer | Editor | Humanizer | Reader-POV | ...]
- **Instruction**: [what this agent was asked to fix, one sentence]
- **Artifact**: `drafts/unit-NN/humanized.c1.md` · `role-diff-<agent>-c1.json`
- **Diff vs. previous**: +[N] / −[N] words, sections touched: [...]
- **Failing rows after this cycle**: [ids]
- **Why next gate failed**: [one-sentence diagnosis from the next agent's report]

### Cycle 2
(...)

---

## Failure pattern (skill's diagnosis)

<!-- One and only one. See references/loopback-handoff.md § "Failure pattern"
     for the categories. -->

**Category**: [thrashing_on_same_hit | diverging_attempts | insufficient_grounding | outline_level_flaw | prose_vs_content_mismatch | unclassified]

**Observation**: [2–4 sentences describing the specific pattern seen in this
unit. Include evidence — which rubric item keeps flagging, which diff pattern
repeats, whether an adversarial finding drove a cycle, etc.]

---

## Options

<!-- Exactly three. Each option is self-contained. Do not hedge; do not add a
     fourth; if three templated options do not fit, replace them. -->

### Option (a): [short name]

**What happens next**: [1–2 sentences]
**Cost estimate**: [which agents re-run; rough token cost as a multiplier of a normal cycle]
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

<!-- One paragraph. The skill takes a position. Explicit trade-off. -->

I'd go with option **(?)** because [reason]. The main thing you would trade
away is [what the other options would have bought].

---

## Human decision

<!-- The human fills in this section. The orchestrator watches for a non-empty
     `chose` value and resumes. On any decision, retries.by_unit[unit-NN]
     resets to 0 — the chosen path is a fresh attempt. -->

**chose**: [a | b | c | custom | pause]

**notes** (optional):

<!-- If "custom", describe the path. If "pause", the unit is parked and the
     rest of the project continues. If a/b/c, optionally add modifications
     ("b, but add source X to bible/sources/ first"). -->
