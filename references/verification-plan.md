# Verification plan — what you owe when you cannot establish the truth here

Some claims the pipeline can settle: it reads the sources, compares passages,
checks arithmetic. Some it cannot, and a subset of those is not unknowable, only
unknown **here**: the answer lives in a running system, a measurement nobody
took, a person who owns the process, a document of record the project lacks.

**The rule.** When the pipeline cannot establish a claim and reality could, write
the check down in a form somebody can execute, with a slot for the answer. Do not
silently soften the claim, and do not assert it anyway. Reasoning about code
against documentation is not verification: the failure mode is quiet (a malformed
query returns zero rows, which reads like a correct query over empty data). Why:
`docs/rationale/gate.md#mg6`.

## When you owe a plan

When the gate's `deferred` items name something reality can answer:

| `needs` | Means | Typical of |
|---|---|---|
| `runner` | Execute the code | technical books, papers with analysis scripts |
| `live-system` | Observe the real product or service | product docs, technical books, corporate guides |
| `measurement` | Collect a number nobody collected | performance figures, any quantitative claim |
| `person` | Someone owns this knowledge and can confirm it | corporate guides, process claims |
| `document-of-record` | An authoritative source the project lacks | grounded nonfiction, papers |

`human-decision` is not in the plan: no observation settles a choice; it goes to
the human packet. A novel or a philosophical essay usually owes no plan — the
trigger is *the pipeline could not settle it, and a defined observation would*.

The debt is recorded where the done report sees it, **and an MG-6 waiver counts
only when it is complete (who, why, debt) and names a plan entry that exists**
(`references/manuscript-gate.md` § MG-6):

```yaml
# project-status.yaml
waivers:
  - check: validation_surface.sql_dialect_check
    waived_by: human
    reason: "no sandbox for this product in this environment"
    date: "2026-08-01"
    plan: reviews/verification-plan/PLAN.md#V-03    # the ### V-03 entry must exist
    debt: "56 checks, 0 run"
```

Update `debt` as results arrive: `0 run` on a shipped book can be a legitimate
decision; `0 run` that nobody knew about is not.

## Building it

`scripts/manuscript_gate.py` **appends** every new checkable `deferred` item to
`reviews/verification-plan/PLAN.md` — one `### V-NN — question` entry with an
empty `**Actual result:**` slot, inserted before "What was left out". It never
rewrites the file: entries, filled results, the setup and the ordering you add by
hand all survive every run, and a question already in the plan is not added
twice. For code-bearing projects, `scripts/extract_code_corpus.py --out
reviews/verification-plan` adds every snippet with its location and caption.
Template for the parts a human writes: `templates/verification-plan.md`.

---

## What makes a plan good

**One setup, engineered so each trap is visible.** Not one setup per check: one,
built once, deterministic, whose every property exists because it makes a specific
claim checkable — a category present in the data and absent from the config, a
row with a null key, a name containing a wildcard. Write the mapping property →
claim down, or the next person "simplifies" the setup and removes the
discrimination. For a person, the setup is knowing who, and what exactly to ask.

**An empty result slot, and a protocol for it.** Fill `**Actual result:**` in the
file with literal values — the number, the error text, the words the person used.
A skipped check says `NOT RUN` and why: an empty slot is ambiguous.

**The defect suspicion, written before you check.** Each entry states what the
book expects **and** what would indicate a defect, before checking — otherwise
the result gets read as confirmation. When a result surprises you, **do not fix
the book yet**: record it, finish the block, then decide; a surprising result
often means the check is wrong.

**Executable, not descriptive.** Paste-ready code; the exact screen and click; the
exact question and of whom.

**Ordered, and honest about what it omits.** Lead with a short path: the five or
six checks that settle open critical findings. Group the rest in blocks with a
time estimate; destructive or lockout-risk checks get their own block and their
own safety protocol next to them. Close with what was left out and why.

Why: `docs/rationale/gate.md#verification-plan`.

---

## Feeding results back

1. **Confirmed defect** → a finding in the current gate round (a findings file
   with the check id as `authority`), severity from the impact.
2. **Confirmed correct** → `verified_against` in `bible/claim-index.yaml` pointing
   at the check id, plus a `bible/do-not-touch.md` anchor when somebody has
   already tried to "fix" that claim.
3. **Still surprising** → back to `deferred`, with what would settle it now.

## See also

- `references/manuscript-gate.md` § MG-6 — Checkable against reality ·
  `references/validation-surface.md`
- `references/claim-index.md` — where confirmed-correct results are persisted
- `templates/verification-plan.md`
