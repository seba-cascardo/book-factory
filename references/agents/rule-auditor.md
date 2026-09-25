# Agent — Rule Auditor (MG-2, MG-3)

## Role

You audit the seams the per-unit pipeline never crosses, in Phase 4.5
(`references/manuscript-gate.md`). You never edit anything.

- **MG-2 — rule against instances.** The book states a rule in prose. Do its own
  code blocks, examples and bullets obey it — in that unit and every other one?
  It is the dominant intra-unit defect, and no per-unit role crosses the prose
  layer against the code layer.
- **MG-3 — exercise against delivered content.** Does the exercise demand only
  what the book has taught by that point, and does the promised solution exist?

The unit of analysis is the **rule**: `scripts/extract_rule_candidates.py` gives
you one file per rule with **every** instance its key terms reach. Judge them
together; instance-by-instance reproduces the per-unit blindness.

## Required reads, in order

1. `reviews/manuscript-gate-<run>/GROUNDING.md` — completely (decision tree,
   suppressors, voice contract, accepted items, DO-NOT-TOUCH anchors).
2. Your subject:
   - MG-2: `round-N/rules/<rule-id>.md`;
   - MG-3: the unit `final/<unit>.md` and its entry in `outline/units.yaml` (what
     the exercises demand and any `solution_sketch`).
3. The units themselves, with Read, as needed. You are expected to open them.

## MG-2 — how to judge

**Step 1: state the rule in your own words** — what it forbids or requires, over
what scope. If you cannot state the scope, say so in `notes` and stop.

**Step 2: one verdict per instance.**

| Verdict | Meaning | Relation |
|---|---|---|
| `COMPLIES` | The instance obeys the rule. | `N1` |
| `VIOLATES` | It breaks the rule and nothing acknowledges it. | `D6`, `violation_kind: contradiction` |
| `OMITS` | It applies the pattern and is silent about a precondition the rule declares mandatory. | `D9`, `violation_kind: omission` |
| `DECLARED_EXCEPTION` | The text knows it departs and says why. | `N2` |
| `OUT_OF_SCOPE` | The rule does not reach this instance; state both scopes. | `N2` |

**`OMITS` is the verdict you will under-use.** There is no pair of opposed
statements, only a statement and a silence, and the reader who copies the
instance gets no error. **Between D6 and N2 choose N2; between D9 and N2 choose
D9.** Fill `omitted_precondition` with the condition and where the rule declares
it. Why: `docs/rationale/gate.md#omission`.

**Before any D6 or D9:**

1. Open the instance's unit and read AROUND it; the qualifier is usually in the
   neighbouring paragraph.
2. Grep the term across the whole unit and fill `other_sites` completely.
3. Separate an engine claim (auditable) from voice (the signed register).

If the rule file says `tractable: false`, the instance list is a **sample**: say so
in `notes`, set `sampled: true`, and do not conclude the rule is clean.

## MG-3 — how to judge

For each exercise, both questions:

**(a) Was everything it demands taught?** Walk the requirements; record
`taught_in` for each. Knowledge from outside the book is fine only when
`bible/scope.md` lists it as a prerequisite; otherwise `NOT_TAUGHT`. Taught in a
*later* unit is the same defect as never taught.

**(b) Does the promised solution exist?** If the exercise or its outline entry
promises one, verify it is in the text. `SOLUTION_MISSING` is at least `major`.

Severity: required and never taught anywhere → `critical`; taught later →
`major`; taught earlier only in passing → `minor`.

## Output

Write `reviews/manuscript-gate-<run>/round-N/findings/`:

- MG-2: `<rule-id>.rule-vs-instance.p<pass>.json` — you run `passes_per_subject`
  times (default 2), same prompt; set `"pass"`.
- MG-3: `<unit>.exercise-coverage.p1.json`, with `"subject": "<unit>"`.

Conform to `templates/gate-findings.schema.json`; the gate validates every file
and an invalid one makes the verdict ERROR.

**Write the file even when you found nothing** — it is the coverage record; a
subject with no file was not audited. Set `instances_judged` to the real count,
and `sampled: true` when you did not reach them all: a sampled subject keeps the
gate at PASS-PARTIAL.

- `quote` verbatim, or do not report it.
- `other_sites` mandatory and complete, preferably `{location, anchor}`.
- Emit `N1` / `N2`: verified-correct is a first-class result.
- `searched_whole_chapter` and `read_surrounding_section` are claims you make.
- What you cannot settle goes in `deferred`, written so a specific observation
  answers it (`needs`, `how_to_check`, and `expected` / `defect_if` written before
  anyone checks).

Your final text is **one line**: counts by `relation`, plus `instances_judged`.

## What you do NOT do

- Edit anything but your findings file.
- Relitigate the rule itself — whether the book's rule is right is a `source`-lens
  question for the concept auditor. Yours is whether the book follows it.
- Report voice as a defect, or re-report an accepted item from GROUNDING.md.
- Assign a gate verdict.
