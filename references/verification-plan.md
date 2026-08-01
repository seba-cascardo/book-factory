# Verification plan — what you owe when you cannot establish the truth here

Some of what a document asserts, the pipeline can settle: it reads the sources,
compares the passages, checks the arithmetic. Some of it, it cannot. And a subset
of *that* is not unknowable — it is merely unknown **here**, because whatever
would answer it lives outside this session: a running system, a measurement
nobody took, a person who owns the process, a document of record the project does
not have.

For those, the deliverable is the plan to go and ask.

**The rule.** When the pipeline cannot establish a claim, and reality could:
write the check down, in a form somebody can execute, with a slot for the answer.
Do not silently soften the claim, and do not assert it anyway.

This is not a formality. The first time eight checks from one such book were run
against a live system, the results **contradicted what the reviewer had concluded
on paper**. The reasoning had been careful. It was still wrong.

And the failure mode is quiet. A malformed query returns zero rows instead of an
error, which reads exactly like a correct query over empty data. A reviewer
reasoning from documentation cannot see that. The system can.

## When you owe a plan

Whenever the manuscript gate's `deferred` lists hold items whose `needs` names
something reality can answer:

| `needs` | Means | Typical of |
|---|---|---|
| `runner` | Execute the code | technical books, papers with analysis scripts |
| `live-system` | Observe the real product or service | product docs, technical books, corporate guides |
| `measurement` | Collect a number nobody has collected | any quantitative claim, performance figures |
| `person` | Someone owns this knowledge and can confirm it | corporate guides, internal process claims |
| `document-of-record` | An authoritative source the project lacks | any grounded nonfiction, papers |

`human-decision` is the exception: no observation settles it, it is a choice, and
it goes to the human packet rather than the plan.

**This does not apply to every book.** A novel has no reality to check against;
a philosophical essay's claims are not that kind of claim. The trigger is narrow
and specific — *the pipeline could not settle it, and a defined observation
would.* When that is true, writing the plan is cheap and skipping it means
shipping a claim nobody ever checked.

Along with the plan, the debt is recorded where it is visible:

```yaml
# project-status.yaml
waivers:
  - check: validation_surface.qlik_load_script
    waived_by: human
    reason: "no sandbox for this product in this environment"
    date: "2026-08-01"
    debt: "reviews/verification-plan/PLAN.md — 56 checks, 0 run"
```

A waiver with no plan is a promise. A plan with no waiver hides the debt from the
done report. Update `debt` as results arrive: `0 run` on a shipped book is a
legitimate decision; `0 run` that nobody knew about is not.

## Building it

`scripts/manuscript_gate.py` collects every `deferred` item in the round and
writes the plan skeleton, grouped by what would settle each one and led by the
checks that close open `critical` findings. For code-bearing projects,
`scripts/extract_code_corpus.py --out reviews/verification-plan` adds every
snippet with its location and caption — raw material, and also the argument:
"3,200 lines verified only by reasoning" is a sentence that changes a decision.

Template: `templates/verification-plan.md`.

---

## What makes a plan good

Five things, all learned the expensive way.

### One setup, engineered so each trap is visible

Not one setup per check. One, built once, whose every property exists because it
makes some specific claim checkable. Write that mapping down — property → the
claim it tests — because otherwise the next person "simplifies" the setup and
quietly removes the discrimination the checks depend on.

In the reference plan, one paste-once script covered about 80% of 56 checks: a
category present in the data and absent from the config table, a churned customer
with no current-year rows, a dozen rows with null keys, five duplicate ids, names
containing wildcard characters. None of it was decoration.

**Deterministic.** Same result every run. If something must depend on the current
date, say so in the check rather than letting it drift.

The same idea holds off the code path: when the answer comes from a person, the
"setup" is knowing who, and what exactly to ask.

### An empty result slot, and a protocol for it

Every check carries `**Actual result:**` with nothing after it. Fill it in the
file, with literal values — the number, the error text, the words the person
actually used. Not "works as expected".

When a check is skipped, write `NOT RUN` and why. An empty slot is ambiguous: did
it pass, or did nobody get to it? `NOT RUN` is not. That single line of protocol
is the difference between a plan that reports honestly at 20% coverage and one
that looks abandoned.

### The defect suspicion, written before you check

Each entry states what the book expects **and** what would indicate a defect —
both, before checking. An entry that only says what is expected invites reading
the result as confirmation: you get a number, it is plausible, you move on.

And when a result surprises you: **do not fix the book yet.** Record it, finish
the block, then decide. A surprising result often means the *check* is wrong, and
a book edited from one surprising result is worse off than before. In the
reference project a hurried fix on an incomplete checklist forced an entire pass
to be reverted.

### Executable, not descriptive

The check is the thing to do, not a description of what to test. Paste-ready
code; the exact screen and the exact click; the exact question, and of whom. A
plan that asks the reader to design the check is a plan that will not be run.

### Ordered, and honest about what it omits

Lead with a short path: the five or six checks that settle open `critical`
findings. Someone with forty minutes should be able to resolve what matters most
— a plan that must be executed in full or not at all gets executed not at all.

Group the rest into blocks with a time estimate each. Anything carrying a
destructive or lockout risk gets its own block and its own safety protocol,
written next to the checks it protects rather than in a preamble nobody rereads.

Close with **what was left out and why**. A plan that silently omits an area
reads as coverage.

---

## Feeding results back

Results are evidence, and evidence belongs where evidence lives:

1. **Confirmed defect** → a finding in the current gate round, severity from the
   impact, with the check id as `authority`.
2. **Confirmed correct** → `verified_against` in `bible/claim-index.yaml`
   pointing at the check id, plus a `bible/do-not-touch.md` anchor when it is a
   claim somebody has already tried to "fix".
3. **Still surprising** → back to `deferred`, with what would settle it now.

The point of running the checks is not the report. It is that the book stops
carrying claims nobody ever verified — and that the ones that *were* verified say
so, durably, so the next pass does not reopen them.

## See also

- `references/manuscript-gate.md` § MG-6 — where the plan is required
- `references/validation-surface.md` — declaring surfaces and runners
- `references/claim-index.md` — where confirmed-correct results are persisted
- `templates/verification-plan.md`
