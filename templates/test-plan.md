# Test plan — [project name]

**Target environment:** [product, edition, version — must match `meta.yaml` pins]
**Why this exists:** the validation surface(s) [list] have no runner in this
environment. The code below shipped in the book and has never been executed.
**Waiver:** `project-status.yaml → waivers → [check id]`

**Status:** [N] tests · [N] run · [N] `NOT RUN`

---

## How to use this document

1. Work through **Setup** once. It builds one dataset that covers most tests.
2. Run tests in whatever order suits you. The **short path** below is the six
   highest-value ones if you only have forty minutes.
3. Fill `**Actual result:**` **in this file**, with literal values — the number,
   the error text, the row count. Not "works as expected".
4. Skipping one? Write `NOT RUN` and why. An empty slot is ambiguous; `NOT RUN`
   is not, and at 20% coverage that difference is the whole report.
5. **If a result surprises you, do not fix the book yet.** Record it, finish the
   block, then decide. A surprising result often means the test is wrong.

## Short path — six tests, ~40 minutes

| Test | Settles | Time |
|---|---|---|
| T-01 | [which open critical finding] | ~8 min |

## Time estimate

| Block | Tests | Est. |
|---|---:|---|
| A — [subsystem] | | |
| **Total** | | |

---

## Setup

<!--
ONE dataset, loaded once, deterministic. Every property below exists because it
makes a specific trap visible. Keep the mapping table — without it, the next
person "simplifies" the data and silently removes the discrimination the tests
depend on.
-->

### Data properties, and the trap each one exposes

| Property in the data | Which book claim it makes testable |
|---|---|
| [e.g. a category present in the data and absent from the config table] | [T-04, T-05 — the wildcard claim at `final/unit-08.md:63`] |
| [e.g. ~12 rows with a null key] | [T-11 — the null-handling claim at `unit-06.md:210`] |
| [e.g. 5 duplicate ids] | [T-19] |

### Build script

<!-- Paste-ready. Deterministic: same results on every run. Call out anything
     that depends on the current date. -->

```[language]
[the complete setup script]
```

### Safety protocol — [block with destructive or lockout risk]

<!-- Belongs HERE, next to the tests it protects, not in a preamble nobody
     rereads. E.g.: duplicate a clean baseline per test, because a bad security
     configuration can lock you out of the application entirely. -->

---

# Block A — [subsystem]

### T-01 — [what this settles, in a few words]

- **Claim:** `final/unit-NN.md:LINE` [and the passage it contradicts, if any]
- **Finding:** [gate finding id, severity] · [deferred item id, if it came from one]
- **Setup:** [state required beyond the base dataset; "none" is a valid answer]

```[language]
[paste-ready code — the thing to run, not a description of it]
```

- **What the book expects:** [concretely, with the number or behavior, and the
  passage that says so]
- **Suspect a defect if:** [the specific outcome that would mean the book is
  wrong, and which passage would then be at fault. State this BEFORE running —
  a test that only says what is expected invites reading the result as
  confirmation.]
- **Also record:** [any secondary value worth capturing while you are here]

**Actual result:**


---

### T-02 — [...]

- **Claim:**
- **Finding:**
- **Setup:**

```[language]
```

- **What the book expects:**
- **Suspect a defect if:**

**Actual result:**


---

## What was left out, and why

<!--
Do not delete this section. A plan that silently omits an area reads as coverage.
State what is untested and why: no environment, destructive, needs data you do
not have, out of scope for this book's claims.
-->

| Area | Why untested | What would change that |
|---|---|---|

---

## Results roll-up

<!-- Fill as results come in. This is what feeds back into the gate. -->

| Test | Result | Verdict | Where it goes |
|---|---|---|---|
| T-01 | | confirmed defect / confirmed correct / surprising | gate finding / `claim-index.verified_against` / `deferred` |

**Confirmed defects** → findings in the current gate round, with the test id as
`authority`.
**Confirmed correct** → `verified_against` in `bible/claim-index.yaml`, plus a
`bible/do-not-touch.md` anchor when it is a claim someone has already tried to
"fix".
**Still surprising** → back to `deferred`, with what would settle it.
