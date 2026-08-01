# Verification plan — [project name]

**Why this exists:** the pipeline could not establish the claims below, and
reality can. [Name what is missing: no runner for surface X · no access to the
live system · the process owner has not confirmed it · the source of record is
not in `bible/sources/`.]

**Target environment / source of truth:** [product + edition + version, matching
`meta.yaml` pins · or the system, the team, the document]

**Waiver:** `project-status.yaml → waivers → [check id]`

**Status:** [N] checks · [N] answered · [N] `NOT RUN`

---

## How to use this document

1. Work through **Setup** once. It prepares what most checks share.
2. Run checks in any order. The **short path** below is the five or six highest
   value ones if you only have forty minutes.
3. Fill `**Actual result:**` **in this file**, with literal values — the number,
   the error text, the words the person actually used. Not "works as expected".
4. Skipping one? Write `NOT RUN` and why. An empty slot is ambiguous; `NOT RUN`
   is not, and at 20% coverage that difference is the whole report.
5. **If a result surprises you, do not fix the book yet.** Record it, finish the
   block, then decide. A surprising result often means the *check* is wrong, and
   a hurried fix on an incomplete list has already forced one whole pass to be
   reverted.

## Short path — [N] checks, ~[N] minutes

| Check | Settles | Time |
|---|---|---|
| V-01 | [which open critical finding, by id] | ~8 min |

## Time estimate

| Block | Checks | What it needs | Est. |
|---|---:|---|---|
| A — [subsystem / question area] | | runner · live-system · person · … | |
| **Total** | | | |

---

## Setup

<!--
ONE setup, prepared once, deterministic. Every property below exists because it
makes some specific claim checkable. Keep the mapping table — without it, the
next person "simplifies" the setup and silently removes the discrimination the
checks depend on.

When the answer comes from a person rather than a system, the "setup" is knowing
who owns the knowledge and what exactly to ask them. Write that here.
-->

### What each property exposes

| Property of the setup | Which claim it makes checkable |
|---|---|
| [e.g. a category present in the data and absent from the config table] | [V-04, V-05 — the wildcard claim at `final/unit-08.md:63`] |
| [e.g. ~12 rows with a null key] | [V-11 — the null-handling claim at `unit-06.md:210`] |
| [e.g. the process owner for approvals is <role>] | [V-20 — the three-day claim at `unit-04.md:88`] |

### Preparation

<!-- Paste-ready. Deterministic: same result on every run. Call out anything that
     depends on the current date. -->

```[language]
[the complete setup script — or, for non-code checks, the access needed and who
 to arrange it with]
```

### Safety protocol — [block with destructive or lockout risk]

<!-- Belongs HERE, next to the checks it protects, not in a preamble nobody
     rereads. E.g.: duplicate a clean baseline per check, because a bad security
     configuration can lock you out of the application entirely. -->

---

# Block A — [subsystem / question area]

### V-01 — [what this settles, in a few words]

- **Claim:** `final/unit-NN.md:LINE` [and the passage it contradicts, if any]
- **Finding:** [gate finding id + severity] · [deferred item id, if it came from one]
- **Needs:** runner | live-system | measurement | person | document-of-record
- **Setup:** [what is required beyond the shared setup; "none" is a valid answer]

```[language]
[paste-ready code — the thing to run, not a description of it]
```

<!-- For a non-code check, replace the block above with the exact observation:
     the screen and the click, the number to count and how, or the question to
     ask and of whom. The test is that someone else could do it without
     designing anything. -->

- **What the book expects:** [concretely, with the number or behavior, and the
  passage that says so]
- **Suspect a defect if:** [the specific observation that would mean the book is
  wrong, and which passage would then be at fault. Write this BEFORE checking —
  an entry that only says what is expected invites reading the result as
  confirmation.]
- **Also record:** [any secondary value worth capturing while you are here]

**Actual result:**


---

### V-02 — [...]

- **Claim:**
- **Finding:**
- **Needs:**
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
State what is unchecked and why: no environment, destructive, needs data or
access you do not have, out of scope for this book's claims.
-->

| Area | Why unchecked | What would change that |
|---|---|---|

---

## Results roll-up

<!-- Fill as answers arrive. This is what feeds back into the gate. -->

| Check | Result | Verdict | Where it goes |
|---|---|---|---|
| V-01 | | confirmed defect / confirmed correct / still surprising | gate finding / `claim-index.verified_against` / `deferred` |

**Confirmed defects** → findings in the current gate round, with the check id as
`authority`.
**Confirmed correct** → `verified_against` in `bible/claim-index.yaml`, plus a
`bible/do-not-touch.md` anchor when it is a claim someone has already tried to
"fix". This half matters as much as the other: a verified-correct result that is
not persisted gets re-litigated by the next pass.
**Still surprising** → back to `deferred`, with what would settle it now.
