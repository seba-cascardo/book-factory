# Adversarial Verify — blind refutation panel

An optional pass after a Critic PASS and before the Proofreader. Three
skeptics run in parallel as **isolated subagents**, each with one lens, each
blind to the Critic and to every other report, each with one mandate: refute
the unit. Blindness is the active ingredient — a verifier who knows the unit
passed looks for reasons to agree. Why: `docs/rationale/pipeline.md#adversarial`.

## Configuration

```yaml
pipeline:
  adversarial_verify:
    mode: gate_critical   # off | gate_critical | every_unit | every_N
    n: 3                  # every_N only
    cross_model: false    # refutations (and the gate's MG-4 read) on a second model when one is available
```

| Mode | Runs on |
|------|---------|
| `off` | never |
| `gate_critical` (default) | units marked `gate_critical: true` in `outline/units.yaml` |
| `every_N` | the first unit, every Nth after it, and all gate-critical units |
| `every_unit` | every unit |

Mark few units gate-critical: where a shipped defect costs most (the opening
unit, a climax, Methods and Results, the highest-traffic article). With none
marked, the default costs nothing. The human can ask for the pass on any unit.
Skeptics use `models.roles.adversarial` if set, else `roles.default`.

It never runs on a REVISE/REWORK and never replaces the human; it feeds the
packet.

## Common contract

- **Isolated and blind.** Input: `drafts/unit-NN/humanized.clean.md` plus the
  lens inputs below — nothing else. Not `critique.md`, `scorecard.yaml`,
  `tech-review.md`, `coherence.md` (sole exception: literary Skeptic B's facts
  table), `reader-report.md`, the other skeptics' output, or earlier
  adversarial reports. Two skeptics who read the same review are one skeptic.
- **Mandated to refute.** "No findings" is acceptable only with an attack log:
  the angles tried and what was checked for each. An empty report without one
  is a failed run.
- **Evidence or nothing.** Each finding: quoted passage, location, the rule or
  source it violates, severity (`critical | significant | minor`). Manufactured
  severity is as corrosive as blindness.
- **No verdicts.** Consequences are computed below.

## The lenses

**A — Register and profile compliance.** Reads the profile file,
`bible/voice-profile.md`, `bible/meta.yaml`. Hunts the profile's register
prohibitions, the project's banned traits, opening repetition, drift toward a
generic register. Does not reload the anti-mediocrity file — that would
reproduce the Critic's blind spots. Enforces the declared voice; never proposes
another.

**B — nonfiction: Correctness and grounding.** Reads `bible/sources/sources.md`
and the relevant extracts, `bible/glossary.md`, `bible/claims-map.yaml`
(paper) — deliberately not `grounding-notes.md` or `tech-review.md`. Picks the
3–5 load-bearing claims and re-derives each: holds / holds with an omitted
caveat that changes what a reader would do / does not hold / cannot be verified
from the library.

**B — literary: Continuity and facts.** Reads `bible/continuity-tracker.md`,
`timeline.md`, `world.md`, the sheets of the characters present,
`story-ledger.yaml`. Hunts contradictions in character, factual detail,
timeline, plot and world. With `literary.fact_check: realistic` it also reads
the **facts table** of `coherence.md` (the table only — not its findings or
routing) and attacks it: re-checks each `verified` fact's source with a search
tool when one is available, tests `invented` entries against `world.md`, and
hunts checkable facts the table missed. Anything it cannot settle is a question
for the human — never "probably right".

**C — Reader experience.** Reads the clean unit and the persona line from the
profile. Nothing else: the cold read is the method. Hunts confusion (terms
before any definition, leaps, ambiguous referents, unstated setup) and boredom
(deletable paragraphs, restatement chains, stalls), with location and why.

## Confirmation

A finding is **confirmed** when either:

1. two or more skeptics flag the same underlying problem (same passage or same
   failure pattern, judged by substance, not wording); or
2. a **refutation pass** upholds it. Every single-skeptic finding of severity
   `significant` or `critical` gets one: a fresh isolated subagent — on a second
   model when `cross_model: true` and a tool for it exists (a Codex MCP tool, the
   `debate` skill) — given only the finding, the clean unit and that lens's
   inputs, mandated to refute. It returns `CONFIRMED | REFUTED | UNVERIFIED`
   with evidence and, when the severity is wrong, a corrected one in the
   rubric's vocabulary (`critical | significant | minor`); between CONFIRMED
   and UNVERIFIED it chooses UNVERIFIED.

`minor` findings are never confirmed: they are observations. When
`cross_model` is on but no tool exists, the refutation runs on the same model
and the report says "cross-model unavailable".

## Report — `drafts/unit-NN/adversarial-report.md`

The orchestrator merges the outputs verbatim and adds the consolidation:

```markdown
# Adversarial Report — unit-NN
run: <ISO timestamp> · mode: <mode> · cross-model: <model | unavailable | off>

## Consolidation
| # | Finding | Location | Sev | Flagged by | Refutation | Status |
|---|---------|----------|-----|------------|------------|--------|
| 1 | …       | §…       | significant | A, C | — | CONFIRMED → REVISE (Humanizer) |
| 2 | …       | §…       | critical | B | CONFIRMED | CONFIRMED → REVISE (Writer) |
| 3 | …       | §…       | significant | C | REFUTED | observation |

## Skeptic A · ## Skeptic B · ## Skeptic C · ## Refutation passes
<verbatim outputs>
```

Then `python scripts/pipeline_step.py done unit-NN adversarial --tier <t>
--cycle <n>`.

## Consequences

- **Confirmed finding** → the PASS is suspended and a REVISE is forced,
  counting against the retry cap. Target by problem type: register, voice,
  prose → Humanizer; content, facts, grounding, continuity → Writer;
  structure → Editor; the outline itself → `escalate`. The Writer, Editor or
  Humanizer reads this report as its worklist. After the fix the Critic
  re-gates; the panel does not re-run — the orchestrator checks each confirmed
  finding was addressed and appends an addendum. If the REVISE would exceed the
  cap, produce the escalation packet with this report attached.
- **Everything else** → observations in the human packet, no pipeline effect.
- **Previously overruled patterns**: if the human approved a similar finding
  before (recorded rationale), annotate the row with the precedent; never drop
  it.

Not a second Critic (no scorecard), not a re-litigation of the voice profile,
not a substitute for the human.

## Manuscript-gate mode (Phase 4.5)

The gate reuses the mandate, not the panel: the subject is one finding, and one
verifier suffices because the finding names its evidence. Severities here are
the gate's (`critical | major | minor`, `templates/gate-findings.schema.json`),
not the per-unit rubric's `significant`. Every `critical` and `major` finding
from the gate's agent checks gets one verifier — on the second
model when `cross_model: true` — before it reaches the human. Refuted findings
are recorded, not deleted (`references/manuscript-gate.md`).

> You are an **adversarial verifier**. Your job is to **REFUTE** the finding
> below, not to confirm it.
>
> First read the gate's grounding rules — `reviews/manuscript-gate-<run>/GROUNDING.md`
> when the gate wrote one, else `references/manuscript-gate.md` § False-positive
> suppressors — and `bible/do-not-touch.md`. They override your judgement.
>
> FINDING: `<the finding JSON>`
>
> Before forming an opinion, **read the complete section around each
> passage**, not the cited line: a previous fix often landed in a neighbouring
> paragraph, and then there is no defect.
>
> Valid refutations: different scopes (`N2`); different, named baselines
> (`D7a`); the qualifier is already present; the quote is not verbatim or the
> location is wrong; the passage precedes the concept's introduction by design
> (progressive disclosure); it is the project's signed voice, not a claim about
> behaviour.
>
> **Not valid against a `D9` (omitted precondition):** "the passages do not
> contradict each other" — that is the definition of an omission. To refute a
> `D9`, show the precondition IS stated where the instance is, does not apply
> there, or was never mandatory.
>
> Return JSON: `{"verdict":"CONFIRMED|REFUTED|UNVERIFIED","reason":"...",
> "evidence":"path:line + verbatim quote","searched_whole_chapter":true,
> "other_occurrences":[...],"corrected_severity":"critical|major|minor|null"}`
>
> **Between CONFIRMED and UNVERIFIED, choose UNVERIFIED.** `other_occurrences`
> is mandatory: a confirmed finding that names one line gets fixed in one of N
> places.

The orchestrator writes the result as the finding's `verification` object
**inside its findings file** (`reviews/manuscript-gate-<run>/round-N/findings/…`,
`templates/gate-findings.schema.json`), then re-runs `manuscript_gate.py
--verdict-only`: `REFUTED` sets the finding's status in `findings.jsonl` to
`refuted` (except a literary finding marked `rule: R1|R2`, which only a re-audit
of changed text closes); `corrected_severity` replaces the severity. A finding
the **human** rejects is recorded the same way, with a reason of 20+
characters: `python scripts/manuscript_gate.py --resolve KEY --status refuted
--note "…"` — agent findings only; a deterministic finding (MG-5, MG-7, MG-S,
MG-T) is never refuted by hand.
A `corrected_severity` below the reported one goes to the report's "downgraded
as inflated" section with its counter-evidence — that is how you learn the
auditors run hot.
