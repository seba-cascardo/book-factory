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
  adversarial_verify: gate_critical   # off | gate_critical | every_unit | every_N
  adversarial_verify_n: 3             # read only when the mode is every_N
```

| Mode | Runs on |
|------|---------|
| `off` | never |
| `gate_critical` (default) | units marked `gate_critical: true` in `outline/units.yaml` |
| `every_N` | the first unit, every Nth unit after it, **and** all gate-critical units |
| `every_unit` | every unit |

Recommend `every_N: 3` for long projects (10+ units) — that is where
Critic normalization has time to develop. Mark as gate-critical the units where a
shipped defect is most expensive: the opening unit, a climax, Methods and
Results in a paper, the highest-traffic article in a docs set. The human
can also request the pass ad hoc for any unit.

**The default is `gate_critical`, not `off`.** It used to be `off`, on the
reasoning that three extra agent runs per unit is real cost. The measurement
says otherwise: review agents inflate, and on a completed book six polish
findings had to be downgraded by hand after verification — one asserting a
function was "never taught" when the book explains it, another flagging a scope
contradiction the chapter announces in as many words. A fix pass acting on a
wrong finding costs more than the verification, and the revert costs more again.
Once one of those edits introduced a factual error into correct text.

With nothing marked `gate_critical`, this default costs nothing — which makes
honest marking the thing that matters, not the flag itself. Mark few.

Skeptics run on the audit tier (`models.roles.default`); override only if the
human asks. `models.roles.adversarial` is accepted as an explicit override and
takes precedence when set.

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

## Manuscript-gate mode (Phase 4.5)

The gate reuses the mandate, not the panel. Per-unit the three skeptics attack a
whole unit blind; at the gate the subject is **one finding**, and one verifier is
enough because the finding already names its own evidence.

Every `critical` and `major` finding from MG-1 through MG-4 gets one verifier
before it reaches the human packet. Findings that survive go into the report;
findings that do not are recorded as refuted, and their concept gets
`do_not_touch: true` plus the counter-evidence in `bible/claim-index.yaml`. That
last step is what stops the next round from rediscovering them, and without it
the convergence loop does not terminate.

> You are an **adversarial verifier**. Your job is to **REFUTE** the finding
> below, not to confirm it.
>
> Read `reviews/manuscript-gate-<date>/GROUNDING.md` first — the authority rules,
> the false-positive suppressors, the voice contract and the DO-NOT-TOUCH
> anchors all override your judgement.
>
> FINDING: `<the finding JSON>`
>
> Mandatory before you form an opinion: **read the complete section around each
> passage**, not the cited line. The lesson this whole gate is built on is that
> previous fixes usually landed in a neighbouring paragraph — and if one did,
> there is no defect.
>
> Valid grounds for refutation:
> - the two passages are in **different scopes** → REFUTED as `N2`
> - the figures differ because the **baselines** differ and both are named →
>   REFUTED as `D7a`
> - the newer passage **already carries the qualifier**; the finding points at a
>   line that was already fixed
> - the quote is **not verbatim**, or the location is wrong
> - the passage precedes the unit where the concept is introduced — that is
>   **progressive disclosure**, the book's design, not an error
> - it is **voice** (the project's signed register), not a claim about behavior
>
> **NOT valid grounds, on a `D9` (omitted precondition):** "the two passages do
> not contradict each other". That is the definition of an omission, not a
> refutation of one. A `D9` says one passage applies a pattern while staying
> silent about a condition another passage declared mandatory — there is no
> contradiction to find, and looking for one is exactly the blindness that made
> a lens miss 2 of 2 omissions while catching 6 of 6 contradictions. To refute a
> `D9` you must show the precondition IS stated where the instance is, or that it
> does not apply there, or that the rule never made it mandatory.
>
> Return JSON: `{"verdict":"CONFIRMED|REFUTED|UNVERIFIED","reason":"...",
> "evidence":"path:line + verbatim quote","searched_whole_chapter":true,
> "other_occurrences":[...],"corrected_severity":"critical|major|minor|null"}`
>
> **Between CONFIRMED and UNVERIFIED, choose UNVERIFIED.** Only decisive evidence
> confirms. `other_occurrences` is not optional — a confirmed finding that names
> one line produces a fix that lands in one of N sites, which is the defect this
> gate exists to eliminate.

Fill the finding's `verification` block from the result (see
`templates/gate-findings.schema.json`). A `corrected_severity` lower than the
reported one belongs in the report's **"What was downgraded as inflated"**
section with its counter-evidence — that section is how you find out your
auditors are running hot.
