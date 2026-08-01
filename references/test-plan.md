# Test plan — what you owe when the code cannot run here

A validation surface whose content is executable and whose runner is
`reviewer-only` or `internal:*` has not been verified. It has been *reasoned
about*. Those are different things, and the difference is measurable: the first
time eight tests from one such book were executed on a real engine, the results
contradicted what the reviewer had concluded on paper.

The failure mode is worse than it looks, because broken code does not always fail
loudly. An expression that silently returns zero rows looks like a correct query
over an empty result. A reviewer reasoning from documentation cannot see that. An
engine can.

So the skill's position is not "always run the code" — sometimes there is no
sandbox and that is a real constraint. It is: **either run it, or produce the
artifact that lets someone else run it, and record the debt where it is visible.**

That artifact is the test plan. It is a first-class deliverable, not a note.

---

## When you owe one

MG-6 requires, for every declared surface whose content is executable:

- a real runner, and its output on record; **or**
- a `waivers` entry in `project-status.yaml`, **and** a test plan.

A waiver with no test plan is a promise. A test plan with no waiver hides the
debt from the done report. You need both:

```yaml
# project-status.yaml
waivers:
  - check: validation_surface.qlik_load_script
    waived_by: human
    reason: "no sandbox available for this product in this environment"
    date: "2026-08-01"
    debt: "reviews/test-plan/TEST-PLAN.md — 56 tests, 0 run"
```

Update `debt` as results come in. `0 run` on a shipped book is a legitimate
decision; `0 run` that nobody knew about is not.

## Building it

```bash
python scripts/extract_code_corpus.py --out reviews/test-plan
```

That gives you every code block in the book, grouped by kind, with locations and
captions. It is raw material, not a plan — the plan is written from it, plus the
open items in the gate's `deferred` lists (`needs: runner`), which are exactly
the questions an audit could not settle on paper.

Template: `templates/test-plan.md`.

---

## What makes a test plan good

Four things, all learned the expensive way.

### One dataset, engineered so each trap is visible

Not one dataset per test. One dataset, loaded once, whose every property exists
because it makes a specific trap in the book visible. Write that mapping down —
property → which book claim it tests — because otherwise the next person
"simplifies" the data and quietly removes the discrimination.

In the reference plan, one paste-once script covered about 80% of 56 tests:
a region present in the data and absent from the security table, a churned
customer with no current-year sales, a dozen rows with null keys, five duplicate
ids, names with wildcard characters in them. None of that is decoration.

**Deterministic.** Same results on every run. If something must depend on the
current date, say so explicitly in the test rather than letting it drift.

### An empty result slot, and a protocol for it

Every test carries `**Actual result:**` with nothing after it. Fill it in the
file, with literal values, not interpretations.

When a test is skipped, write `NOT RUN` and the reason. An empty slot is
ambiguous — did it pass, or did nobody get to it? `NOT RUN` is not. This one line
of protocol is the difference between a plan that reports honestly at 20%
coverage and one that looks abandoned.

### The defect suspicion, stated before you run it

Each test says what the book expects **and** what would indicate a defect. Both,
before running. A test that only says what is expected invites reading the result
as confirmation — you get the number, it is plausible, you move on.

And when a result surprises you: **do not fix the book yet.** Record it, finish
the block, then decide. A surprising result often means the test is wrong, and a
book edited from one surprising result is worse off than before.

### Paste-ready code

The code in each test is copy-pasteable into the target environment with no
editing. Not a description of what to test — the thing to run. A plan that
requires the reader to write the test is a plan that will not be run.

---

## Ordering

Lead with a short path: the five or six highest-value tests, the ones that settle
open `critical` findings. Someone with forty minutes should be able to resolve the
questions that matter most, and a plan that has to be executed in full or not at
all gets executed not at all.

Group the rest into blocks by subsystem, with a time estimate per block. Put
anything with a destructive or lockout risk in its own block with its own safety
protocol — a security-configuration test that can lock you out of the application
needs a disposable copy per test, and that instruction belongs next to the test,
not in a preamble nobody rereads.

Close with **what was left out and why**. A plan that silently omits an area
reads as coverage.

---

## Feeding results back

Results are evidence, and they belong where evidence lives:

1. Confirmed defect → a finding in the current gate round, `severity` from the
   impact, with the test id as `authority`.
2. Confirmed correct → `verified_against` in `bible/claim-index.yaml`, pointing
   at the test id, and a `do-not-touch` anchor when the claim is one somebody has
   already tried to "fix".
3. Surprising and unresolved → back to `deferred`, with what would settle it.

The point of running the tests is not the report. It is that the book stops
having claims nobody ever checked.

## See also

- `references/validation-surface.md` — declaring surfaces and runners
- `references/manuscript-gate.md` § MG-6
- `references/claim-index.md` — where positive results are persisted
- `templates/test-plan.md`
