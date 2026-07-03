# Examples Library — [Project Name]

Running examples used across units. When a document builds one example over
many units — "the todo app we've been working with", "the migration we wrote
in unit-04" — keeping its state consistent is a continuity problem on par with
characters in a novel. This file is the authoritative record of what exists in
the example so far so later units don't contradict earlier ones.

Applies to profiles with a running example on: `book-technical` (default on),
and `corporate-guide` when setup enables one on an internal case. Modular
`product-docs` has no running example — each article stands alone.

Save to `bible/examples-library.md`. Files use `unit-NN`; say chapter /
section to the human per the profile.

---

## How this file works

- Each running example gets an entry with its purpose, current state, and the
  units that touch it.
- The Writer reads the entry before drafting a unit that uses an existing
  example, to know its current state (files, branches, data, versions) — this
  is what stops them re-introducing a function that already exists or skipping
  a migration the reader already ran.
- The Technical Reviewer reads it (Axis A) to verify the example's
  *cumulative* state still works when a unit lands, not the unit's snippet in
  isolation.
- The Continuity Guardian updates the `current_state` field after each unit is
  approved.

This is the nonfiction analogue of `continuity-tracker.md`'s character state —
a central record of "what exists in the world so far".

---

## Entry format

```markdown
### [example-name]

**Purpose**: [one sentence — what the example teaches across the document]
**Language / stack**: [e.g., python 3.12, fastapi 0.110, postgres 16]
**Repo / location**: [path within the project's assets, or external repo]
**First introduced**: unit-[NN]
**Last touched**: unit-[NN]
**Units using it**: [NN, NN, NN]

**Current state** (at end of most recent approved unit):
- Code: [where the code is — tag, commit, or "end of § 3.2 changes"]
- Data: [seed data, migrations applied, etc.]
- Dependencies: [installed packages and versions]
- Open TODOs: [anything the document promised to cover later in this example]

**Evolution log**:
- unit-NN: [what this unit added, removed, or changed in the example]
- unit-NN: ...
```

---

## Rules the pipeline enforces

1. **The Writer must read the entry** for any running example a unit touches —
   otherwise they reintroduce something that already exists or skip a step the
   reader already ran.
2. **Fresh examples need a new entry, not reuse of an old name.** If a unit
   wants a genuinely different todo app, call it something else — reusing the
   name silently forks the reader's mental model.
3. **The Technical Reviewer tests cumulative state, not isolated state.** If
   unit-05 adds a migration, the Reviewer verifies the example still works
   after unit-01 through unit-05's migrations applied in order.
4. **Example state in the document must match the repo.** If the text says "as
   of this unit, the repo is at commit abc123", that commit has to exist and
   match.
5. **The Continuity Guardian updates this file post-approval** — same cadence
   as the continuity tracker, and never mid-pipeline.

---

## Cross-references to other bible files

- `bible/glossary.md` — any load-bearing term in an example's description
  should have a glossary entry.
- `bible/continuity-tracker.md` — the tracker's "Running-example state"
  section pulls from here; keep the two in agreement.
- `bible/knowledge-graph.yaml` — an example that first exercises a concept is
  a `reinforced_in` (or the `introduced_in`) unit for that concept.
