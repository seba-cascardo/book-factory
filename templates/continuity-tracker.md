# Continuity Tracker

Maintained by the Continuity Guardian (Mode B) after each approved unit, and
consulted by the Writer and Critic before each new one. Save to
`bible/continuity-tracker.md`.

Structure: a unit-by-unit changelog at the top (newest first, dated), then the
current-state snapshot below. Keep only the block that matches your profile:

- **Literary** (`book-literary`) — character and world state, open threads,
  loaded-but-unfired plants, reader questions in flight.
- **Nonfiction** — reader-knowledge state, open forward references, running-
  example state, terminology audit. Used by every nonfiction profile; in
  modular `product-docs` most of it collapses (no reading order to carry
  state across), so keep only the terminology audit there.

Files use `unit-NN`; say chapter / article / section to the human per the
profile.

---

## Unit-by-unit log

Most recent at the top. One block per approved unit.

### unit-NN (added YYYY-MM-DD)

**Changes introduced by this unit:**

- [character / system / example]: [what changed]
- [thread / forward reference]: opened | advanced | closed | paid off
- [continuity notes worth carrying]

**Promises to the reader made in this unit:**

- [promise]: to be paid off in [where, if known]

---

## § Literary projects — current state

### Characters (end of most recent approved unit)

#### [Character name] — as of end of unit-NN

- **Physical**: [injuries, fatigue, clothing state, possessions]
- **Knows**: [what they've learned; what they still don't know that they
  should or shouldn't]
- **Relationships**: [current state of each named relationship]
- **Location**: [where they are, what time, what day]
- **Emotional state**: [not an essay — a single descriptor tied to behavior]

Repeat for every named character who has been on-page. Cross-check against
each `bible/characters/<name>.md` — a state here that contradicts the sheet is
a flag, not an edit.

### World

- **Timeline**: [current story time — absolute date or "Day N"]
- **Locations**: [any places that have changed state]
- **Plot-relevant objects**: [item — who has it now, condition]
- **Weather / season** (if it matters): [state]

### Open threads

Format: "[thread name] — opened unit-N, last touched unit-M, status".

- [thread]: opened unit-N, last touched unit-M, status: progressing | stale | forgotten

### Plants loaded but not paid off

Setups and payoffs are tracked, not free. A plant (object, secret, wound) goes
here when planted and stays open until paid off; the Guardian audits both
directions.

- [thing]: planted unit-N. Due to pay off: [unit or "not yet scheduled"].

### Reader questions currently holding

- [question the reader is carrying forward]

---

## § Nonfiction projects — current state

### Reader's knowledge (end of most recent approved unit)

- **Concepts introduced so far**: [full list, each linked to the unit that
  first introduces it — this mirrors `introduced_in` in
  `bible/knowledge-graph.yaml`]
- **Tools / commands the reader has seen**: [list]
- **Running examples built so far**: [name — last state; full record lives in
  `bible/examples-library.md`]
- **Exercises / practice attempted**: [count, units]
- **Pinned versions in use**: [echo meta.yaml; flag any drift]

### Open forward references

A claim that defers to a later unit is a promise. It stays open here until the
later unit delivers.

- "[claim made in unit-N that deferred to unit-M]" — status: paid off | still open

### Running-example state

For any example the document builds across units (see
`bible/examples-library.md` for the authoritative record):

- **[example name]**: last state at end of unit-N — [tag / commit / brief
  description of the code's state]

### Terminology audit

Glossary / knowledge-graph terms used in the manuscript so far, checked for
consistent naming against the canonical `name`:

- [term]: used in unit-N, unit-M — spelled consistently: yes | no (flag)

> Note: the whole-manuscript orphan-terms audit (terms used in prose but not
> declared in the graph, glossary, or prerequisites) runs in Phase 4 and is
> reported separately to `bible/orphan-terms-audit.md`, not here. This section
> tracks only naming consistency of already-declared terms.

---

## Open flags for the human

Critical and significant findings from the most recent cross-unit audit live
here until the human resolves them. After resolution, move the note into the
unit-by-unit log (or delete it).

- [flag]: [ref] — [what / why / suggested fix]
