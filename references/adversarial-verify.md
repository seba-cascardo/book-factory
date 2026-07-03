# Adversarial Verify — Blind Refutation Panel

An optional pass that runs after a Critic PASS and before the human review
packet. Three skeptic agents, in parallel, each with a distinct lens, each
**blind to the Critic's verdict and scorecard**, each with one mandate:
refute the unit.

## Why this pass exists

The Critic is a calibrated gate, and calibration is exactly its weakness.
After gating nine units in the same voice, it has normalized that voice:
deviations it would have flagged in unit 2 read as "how this project
sounds" by unit 9. The same drift affects register — a profile-prohibited
move that slips through once becomes invisible the second time, because
the Critic has now read it in an approved unit.

This is not hypothetical. In a real project run with this pipeline, an
equivalent pass performed manually — fresh agents told the unit was
suspect, given no access to the Critic's verdict — twice caught register
violations on units the Critic had passed. The pattern generalizes:
blindness plus a refutation mandate produces findings that a
confirmation-anchored reviewer structurally cannot.

Blindness is the active ingredient. A verifier who knows the unit already
passed inherits the PASS as an anchor and looks for reasons to agree. A
verifier told "this unit is suspected of defects your lens can detect"
looks for reasons to disagree. Same text, different findings.

## Configuration

`bible/meta.yaml`:

```yaml
pipeline:
  adversarial_verify: off      # off | gate_critical | every_unit | every_N
  adversarial_verify_n: 3      # read only when the mode is every_N
```

| Mode | Runs on |
|------|---------|
| `off` (default) | never |
| `gate_critical` | units marked `gate_critical: true` in `outline/units.yaml` |
| `every_N` | the first unit, every Nth unit after it, **and** all gate-critical units |
| `every_unit` | every unit |

Recommend `every_N: 3` for long projects (10+ units) — that is where
Critic normalization has time to develop. `gate_critical` is the floor for
high-stakes projects on a budget. Mark as gate-critical the units where a
shipped defect is most expensive: the opening unit, a climax, Methods and
Results in a paper, the highest-traffic article in a docs set. The human
can also request the pass ad hoc for any unit.

Default is `off` because the pass costs three extra agent runs per
verified unit. Skeptics run on the audit tier (`models.roles.default`);
override only if the human asks.

## Placement

Strictly after a Critic PASS, strictly before the human packet. It never
runs on a REVISE/REWORK verdict (there is nothing to refute — the unit is
already going back), and it never replaces the human: it feeds the packet.

## The panel

Common contract for all three skeptics:

- **Blind.** Do not read `critique.md`, `scorecard.yaml`,
  `tech-review.md`, `coherence.md`, `reader-report.md`, other skeptics'
  output, or any prior adversarial report. The orchestrator spawns the
  three in parallel with only the inputs listed below. Why: the
  confirmation rule (≥2 skeptics) only measures independent agreement if
  the findings are independent — two skeptics who read the same review
  are one skeptic.
- **Mandated to refute.** The prompt frames the unit as suspect. "No
  findings" is an acceptable answer only after genuine attempts: a
  no-findings report must list the specific attack angles tried and what
  was checked for each. An empty report with no attack log is a failed
  run, not a clean unit.
- **Evidence or nothing.** Every finding carries a quoted passage, a
  location, and the rule or source it violates. The mandate cuts both
  ways: manufactured severity is as corrosive as normalized blindness —
  do not invent findings to justify the run.
- **No verdicts.** Skeptics report findings; they do not PASS or REVISE
  anything. Consequences are computed from the merged report (below).

### Skeptic A — Register and profile compliance

**Reads**: `humanized.md`, `references/profiles/<profile>.md`,
`bible/voice-profile.md`, `bible/meta.yaml`. Nothing else.

**Hunts**: violations of the profile's register prohibitions and the
project's declared voice — exactly the class the Critic normalizes.
Prohibited moves from the profile (self-reference, cliffhangers,
transformation promises, whatever the profile bans), banned traits from
the voice profile, opening-structure repetition, register drift toward a
generic default. Skeptic A does not reload the anti-mediocrity file: the
Critic already applied that rulebook, and re-running it reproduces the
Critic's blind spots. This lens tests the *project's own law* with eyes
that have never read a previous unit.

### Skeptic B — Correctness and grounding

**Reads**: `humanized.md`, `bible/sources/sources.md` plus the relevant
source extracts, `bible/claims-map.yaml` (papers), `bible/glossary.md`.
Deliberately does **not** read `grounding-notes.md` or `tech-review.md` —
the point is independent re-derivation, not re-auditing the Writer's own
citation trail.

**Does**: select the 3–5 load-bearing claims — the ones the unit's
argument collapses without — and re-derive each from the sources. Per
claim, one verdict: holds / holds with a caveat the text omits / does not
hold / cannot be verified from the library. The last two are findings;
"holds with omitted caveat" is a finding when the caveat changes what a
reader would do.

### Skeptic C — Reader experience

**Reads**: `humanized.md` and the Reader-POV persona line from the
profile. Nothing else — the cold read *is* the method. Context that the
skeptic reads but the real reader will not have would cure exactly the
confusion this lens exists to catch.

**Hunts**: confusion (terms used before any visible definition or
prerequisite link, logical leaps, ambiguous referents, examples that
assume unstated setup) and boredom (paragraphs deletable with no loss,
restatement chains, sections that stall the persona's actual task).
Reports where attention broke, at what location, and why.

## Consolidation — `drafts/unit-NN/adversarial-report.md`

The orchestrator merges the three outputs verbatim, then adds a
consolidation table. Two findings **match** when they point at the same
underlying problem — the same passage, or the same failure pattern across
passages — judged by substance, not wording. A register hit and a
confusion hit on the same sentence are still two different findings.

```markdown
# Adversarial Report — unit-NN
run: <ISO timestamp> · mode: <config value> · critic verdict at run time: PASS

## Consolidation
| # | Finding | Location | Flagged by | Status |
|---|---------|----------|------------|--------|
| 1 | ...     | §...     | A, C       | CONFIRMED → REVISE (humanizer) |
| 2 | ...     | §...     | B          | observation |

## Skeptic A — register/profile
<verbatim output, findings or attack log>
## Skeptic B — correctness/grounding
<verbatim>
## Skeptic C — reader experience
<verbatim>
```

## Consequences

- **Confirmed finding (flagged by ≥2 skeptics)** → the unit's PASS is
  suspended and a REVISE is forced. It counts against the retry cap —
  adversarial findings are not free passes around the loop budget. Route
  by problem type, same table as any loopback:

  | Problem | Target |
  |---------|--------|
  | register, voice, prose | Humanizer |
  | content, facts, grounding | Writer |
  | structure, ordering | Editor |
  | reader confusion | Reader-POV + Humanizer (full) / Writer (fast) |
  | the outline beat itself is wrong | ESCALATE |

  After the fix, the Critic re-gates `humanized.md` as always. The panel
  does **not** automatically re-run — one panel per unit per approval
  attempt keeps the cost model honest. Instead the orchestrator verifies
  the confirmed findings were addressed and appends an addendum to the
  report. If the forced REVISE would exceed the retry cap, produce the
  escalation packet (`references/loopback-handoff.md`) with the
  adversarial report attached instead of looping.

- **Single-skeptic finding** → an observation in the human review packet.
  No pipeline effect. Why: a lone agent under a refutation mandate
  produces some false positives *by design*; the ≥2 confirmation rule is
  what converts adversarial pressure into signal instead of churn. The
  human sees every observation and can act on any of them.

- **Previously overruled patterns**: if the human already approved a
  similar finding on an earlier unit (recorded approval rationale), the
  orchestrator annotates the consolidation row with that precedent. It
  does not drop the finding — the skeptics are blind, the human is not.

## Logging

One run-log line per skeptic in `project-status.yaml → runs`:

```yaml
- [unit-NN, skeptic-register, audit, 1, 2026-07-03T14:02Z]
- [unit-NN, skeptic-grounding, audit, 1, 2026-07-03T14:02Z]
- [unit-NN, skeptic-reader, audit, 1, 2026-07-03T14:02Z]
```

## What this pass is not

- **Not a second Critic.** No scorecard, no computed verdict. Only the
  confirmation rule can force a REVISE.
- **Not a re-litigation of human decisions.** The voice profile and the
  approved calibration passages are law. A finding that amounts to "I
  would have chosen a different voice" is out of scope — Skeptic A
  enforces the declared voice, never proposes another one.
- **Not a substitute for human review.** It sharpens the packet; the
  human still decides.
