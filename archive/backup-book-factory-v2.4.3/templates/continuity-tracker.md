# Continuity Tracker

Maintained by the Continuity Guardian after each approved chapter.
Save to `bible/continuity-tracker.md`.

Structure: a chapter-by-chapter log at the top, followed by the current
state snapshot. The template differs slightly for literary vs. technical
projects — keep only the block relevant to your project.type.

---

## Chapter-by-chapter log

Most recent at the top.

### ch-NN (added YYYY-MM-DD)

**Changes introduced by this chapter:**

- [character / system]: [what changed]
- [thread]: opened | advanced | closed
- [continuity notes worth carrying]

**Promises to the reader made in this chapter:**

- [promise]: to be paid off in [where, if known]

---

## § Literary projects — current state

### Characters (end of most recent approved chapter)

#### [Character name] — as of end of ch-NN

- **Physical**: [injuries, fatigue, clothing state, possessions]
- **Knows**: [what they've learned; what they still don't know that they
  should/shouldn't]
- **Relationships**: [current state of each named relationship]
- **Location**: [where they are, what time, what day]
- **Emotional state**: [not an essay — a single descriptor tied to behavior]

Repeat for every named character who has been on-page.

### World

- **Timeline**: [current story time — absolute date or "Day N"]
- **Locations**: [any places that have changed state]
- **Plot-relevant objects**: [item — who has it now, condition]
- **Weather / season** (if it matters): [state]

### Open threads

Format: "[thread name] — opened ch-N, last touched ch-M, status".

- [thread]: opened ch-N, last touched ch-M, status: progressing | stale | forgotten
- ...

### Chekhov's guns loaded but not fired

- [thing]: loaded ch-N. Due to fire: [chapter or "not yet scheduled"].

### Reader questions currently holding

- [question the reader is carrying forward]

---

## § Technical projects — current state

### Reader's knowledge (end of most recent approved chapter)

- **Concepts introduced so far**: [full list, linked to first chapter that
  introduces each]
- **Tools / commands the reader has seen**: [list]
- **Example projects built so far**: [name — last state]
- **Exercises attempted**: [count, chapters]
- **Pinned versions in use**: [echo meta.yaml, flag any drift]

### Open forward references

- "[claim made in ch-N that deferred to ch-M]" — status: paid off | still open

### Example / code state

For any running example the book builds across chapters:

- **[project name]**: last state at end of ch-N — [commit hash or brief
  description of the code's state]

### Terminology audit

Glossary terms used in the manuscript so far:

- [term]: used in ch-N, ch-M — spelled consistently: yes | no (flag)

---

## Open flags for the human

Critical and significant findings from the most recent cross-chapter audit
live here until the human resolves them. After resolution, move to the
changelog (or delete).

- [flag]: [ref] — [what / why / suggested fix]
