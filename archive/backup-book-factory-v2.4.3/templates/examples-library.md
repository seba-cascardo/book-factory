# Examples Library — [Project Name]

Running examples used across chapters. For a linear technical book, the
examples build on each other — "the todo app we've been working with", "the
migration we wrote in ch-4" — and keeping their state consistent is a
continuity problem on par with characters in a novel.

Save to `bible/examples-library.md`.

---

## How this file works

- Each running example gets an entry with its purpose, current state, and the
  chapters that touch it.
- The Writer reads this before drafting a chapter that uses an existing
  example to know its current state (files, branches, data, commits).
- The Technical Reviewer reads it (Axis A) to verify the example's
  cumulative state still works when a chapter lands.
- The Continuity Guardian updates the `current_state` field after each
  chapter is approved.

This is analogous to `continuity-tracker.md` for literary projects — a
central record of "what exists in the world so far" so chapters don't
contradict prior ones.

---

## Entry format

```markdown
### [example-name]

**Purpose**: [one sentence — what the example teaches across the book]
**Language / stack**: [python 3.12, fastapi 0.110, postgres 16]
**Repo / location**: [path within the book's assets, or external repo]
**First introduced**: ch-[NN]
**Last touched**: ch-[NN]
**Chapters using it**: [NN, NN, NN]

**Current state** (at end of most recent approved chapter):
- Code: [brief description of where the code is — tag or commit or "end of
  § 3.2 changes"]
- Data: [any seed data, migrations applied, etc.]
- Dependencies: [installed packages and versions]
- Open TODOs: [anything the book promised to cover later in this example]

**Evolution log**:
- ch-NN: [what this chapter added, removed, or changed in the example]
- ch-NN: ...
```

---

## Rules the pipeline enforces

1. **The Writer must read the entry** for any running example a chapter
   touches — otherwise they'll re-introduce a function that already exists
   or skip a migration the reader already ran.
2. **Fresh examples need a new entry, not reuse of an old name.** If a
   chapter wants a totally different todo app, call it something else.
3. **The Technical Reviewer tests cumulative state, not isolated state.** If
   ch-5 adds a migration, the Reviewer verifies the example still works
   after ch-1 through ch-5's migrations applied in order.
4. **Example state in the book must match the repo**. If the book says "as
   of this chapter, the repo is at commit abc123", that commit has to exist
   and match.
5. **The Continuity Guardian updates this file post-approval.** Same cadence
   as the continuity tracker.

---

## Cross-references to other bible files

- `bible/glossary.md` — any term used in this example's description should
  appear in the glossary if it's load-bearing.
- `bible/continuity-tracker.md` — the tracker's "Example / code state"
  section in technical projects pulls from here. Ke