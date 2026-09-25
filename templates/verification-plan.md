# Verification plan — [project name]

<!--
reviews/verification-plan/PLAN.md. The manuscript gate APPENDS one `### V-NN`
entry per new checkable `deferred` item (inserted before "What was left out") and
never rewrites this file: write the setup, the short path and the results here by
hand, and they survive every run. Rules: references/verification-plan.md.
-->

**Why this exists:** the pipeline could not establish the claims below, and
reality can. [No runner for surface X · no access to the live system · the process
owner has not confirmed it · the source of record is not in `bible/sources/`.]

**Target environment / source of truth:** [product + edition + version, matching
`meta.yaml` pins · or the system, the team, the document]

**Waiver:** `project-status.yaml → waivers → [check id]` (its `plan:` points here)

**Status:** [N] checks · [N] answered · [N] `NOT RUN`

---

## How to use this document

1. Work through **Setup** once.
2. Run checks in any order; the **short path** is the highest-value five or six.
3. Fill `**Actual result:**` in this file with literal values — the number, the
   error text, the words the person used. Not "works as expected".
4. Skipping one? Write `NOT RUN` and why. An empty slot is ambiguous.
5. **A surprising result: do not fix the book yet.** Record it, finish the block,
   then decide — the check may be wrong.

## Short path — [N] checks, ~[N] minutes

| Check | Settles | Time |
|---|---|---|
| V-01 | [which open critical finding, by key] | ~8 min |

## Time estimate

| Block | Checks | What it needs | Est. |
|---|---:|---|---|
| A — [area] | | runner · live-system · person · … | |
| **Total** | | | |

---

## Setup

<!-- ONE setup, prepared once, deterministic. Keep the mapping table: without it
the next person "simplifies" the setup and removes the discrimination the checks
depend on. For a person, the setup is who owns the knowledge and what to ask. -->

### What each property exposes

| Property of the setup | Which claim it makes checkable |
|---|---|
| [a category present in the data and absent from the config table] | [V-04 — the wildcard claim at `final/unit-08.md:63`] |

### Preparation

```[language]
[paste-ready setup — or the access needed and who arranges it]
```

### Safety protocol — [block with destructive or lockout risk]

<!-- Next to the checks it protects, not in a preamble. -->

---

## Block A — [area]

### V-01 — [what this settles]

- **Needs:** runner | live-system | measurement | person | document-of-record
- **Claim:** `final/unit-NN.md:LINE` · **Finding:** [key + severity, if any]
- **Setup:** [beyond the shared setup; "none" is valid]

```[language]
[paste-ready code — or the exact screen and click, the number to count, the
 question to ask and of whom]
```

- **What the book expects:** [concretely, and the passage that says so]
- **Suspect a defect if:** [written BEFORE checking: the observation that means the
  book is wrong, and which passage is at fault]

**Actual result:**


---

## What was left out, and why

<!-- Do not delete: a plan that silently omits an area reads as coverage. -->

| Area | Why unchecked | What would change that |
|---|---|---|

---

## Results roll-up

| Check | Result | Verdict | Where it goes |
|---|---|---|---|
| V-01 | | confirmed defect / confirmed correct / still surprising | findings file / `claim-index.verified_against` / `deferred` |

**Confirmed defect** → a findings file in the current gate round, check id as
`authority`. **Confirmed correct** → `verified_against` in
`bible/claim-index.yaml`, plus a `bible/do-not-touch.md` anchor when somebody
already tried to "fix" it. **Still surprising** → back to `deferred`.
