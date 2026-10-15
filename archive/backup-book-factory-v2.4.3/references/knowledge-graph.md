# Phase 1.5 — Knowledge Graph (Technical only)

Technical books rarely fail at the paragraph level. They fail at the
*sequencing* level: Chapter 6 assumes a concept the reader doesn't meet
until Chapter 8. By the time a beta reader catches this, rewriting is
expensive and often means cascading edits across half the book.

The Knowledge Graph is a pre-outlining artifact that makes this failure
mode visible *before* a word is written. It lists every concept the book
teaches, what each concept depends on, and where each concept is
introduced and reinforced.

**This phase runs AFTER setup and BEFORE outlining.** It's technical-only.
For literary projects, the equivalent concern is character/plot
continuity, which lives in the setup phase's `arcs.md` and `timeline.md`.

## When to run it

- New technical project: always, after setup completes.
- Existing project migrating from v2.2 or earlier: optional but strongly
  recommended before writing any new chapter. Build the graph from the
  already-drafted glossary + scope + whatever outline exists. It will
  usually surface two or three forward-reference gaps the project already
  has.

## What you produce

`bible/knowledge-graph.yaml` — see `templates/knowledge-graph.yaml` for the
full schema. In short:

- **Concepts**: every teachable idea the reader walks away knowing. A
  concept is named (stable ID), defined in one sentence, and tagged with
  its kind (term | mechanic | pattern | tool | convention | skill).
- **Dependencies**: directed edges. Concept A `requires` Concept B means
  the reader cannot understand A without having seen B first. Use `builds_on`
  for soft dependencies (A reinforces B, reader could get A cold but better
  with B first). Use `contrasts_with` when two concepts are naturally taught
  together by contrast (SQL JOIN vs. set operations).
- **Prerequisites**: concepts assumed before chapter 1. These anchor the
  graph — every dependency chain must terminate either in a prerequisite
  or in another concept introduced in the book.

The graph is the ground truth for what "introduced" and "used" mean in
`outline/chapters.yaml` and the continuity tracker.

## Roles in the pipeline

| Agent              | Uses the graph for                                             |
|--------------------|----------------------------------------------------------------|
| Writer             | "What may I assume?" — every concept used in this chapter must be in `prerequisites` or introduced ≤ this chapter |
| Technical Reviewer | Axis B — flag terminology drift, flag concepts used before introduction |
| Critic (rubric)    | Pedagogical rubric item: "no undeclared forward references in this chapter"; "all concepts listed in `concepts_introduced` actually get introduced" |
| Continuity Guardian| Full-book audit: every concept introduced exactly once; no orphan concepts in KG; no cycles. **Phase 4 coverage audit**: cross-references manuscript prose against KG + glossary + prerequisites; reports orphan terms (used in prose but not declared) to `bible/orphan-terms-audit.md` for human triage |

The graph is also the outline's spine. The outline phase assigns each
concept to the chapter that introduces it, and optionally lists reinforcement
chapters.

**Two flavors of "orphan", don't confuse them**:

- **Orphan concept in KG** — a concept declared in `knowledge-graph.yaml`
  with no `introduced_in` chapter (or never reached by the dependency
  chain). Caught at sign-off and at every outline revision. Symptom: the
  KG has a node nothing else points to.
- **Orphan term in prose** — a term used in chapter text that is *not*
  declared in KG, glossary, or prerequisites. Caught at Phase 4 by the
  Continuity Guardian's coverage audit. Symptom: the manuscript invokes
  a concept the graph never sanctioned.

The two checks are complementary. The first guards the graph's integrity;
the second guards the prose-graph alignment.

## How to build it (guided session)

This is a collaborative design session with the human, not a form to fill
solo. Aim for 30–90 minutes of real work.

### Step 1 — Inventory the concepts

Read `bible/scope.md`, `bible/glossary.md`, and any prior outline or draft
material. List every teachable unit that will appear in the final book.

Don't include low-level facts ("HTTP uses TCP"); include teachable
*units* ("request/response cycle"). The rule: if a reader could ask
"where in the book do I learn about X?", X is a concept.

Aim for 30–100 concepts for a 200–400-page book. Fewer than 20 means
you're underspecifying. More than 150 means you're bundling what should
be taught together into separate items.

### Step 2 — Define prerequisites

What does the reader know on page 1? Be concrete:

- "Comfortable reading basic SQL (SELECT, JOIN, WHERE, GROUP BY)" — OK
- "Familiar with databases" — too vague, reject and refine

Every prerequisite is a leaf node. Dependencies can point at prerequisites
to signal "builds on the reader's existing knowledge".

### Step 3 — Draw dependencies

For each concept, answer: *to understand this, the reader must have
already seen what?* Use the three edge types:

- `requires` — hard. Reader cannot understand A without B. Cycles in
  `requires` are a design bug.
- `builds_on` — soft. A reinforces B; B-first is better pedagogy but not
  strictly necessary.
- `contrasts_with` — taught together for contrast. Order-agnostic within
  the pair.

You don't need all edges perfect on first pass. The graph improves
through outlining and first-chapter drafting, which will surface missing
dependencies.

### Step 4 — Run the cycle check

Hard cycles (`A requires B`, `B requires A`) are a design flaw, not a
book flaw. The pipeline cannot un-tangle them — the human must choose a
split, introduce one piece as a "preview" before the other, or merge the
two into a single concept.

Report any cycles back to the human. Don't proceed to outlining with
unresolved cycles.

### Step 5 — Sign off

Present the graph to the human. Get explicit sign-off on:

- The concept list is complete (no missing teachable units)
- Prerequisites are correctly scoped (not too ambitious, not too shallow)
- No cycles remain
- Every chain terminates (no orphan concepts)

Record the sign-off in `project-status.yaml` under
`knowledge_graph.last_verified`.

## What to avoid

- **Don't build the graph in the Writer's head, per chapter.** The
  whole point is that sequencing is a whole-book property. Per-chapter
  "I think this concept needs to come first" is exactly the drift the
  graph prevents.
- **Don't treat the graph as frozen after setup.** Expect to revise it
  when drafting reveals missing dependencies or over-granular concepts.
  Bump `knowledge_graph.last_verified` in `project-status.yaml` on
  every revision. Revisions are cheap; undetected forward references
  are expensive.
- **Don't confuse concepts with sections.** One section can introduce
  one or two concepts. One concept might get its own chapter. The
  mapping is in the outline, not the graph.

## What good looks like

A Qlik Sense book's graph might include concepts like:

```yaml
concepts:
  - id: set_analysis
    name: "Set Analysis"
    kind: mechanic
    one_liner: "Scoping aggregations to a subset of rows by a set expression."
    requires: [aggregation_functions, field_selections]
    builds_on: [associative_model]
  - id: associative_model
    name: "Qlik Associative Model"
    kind: mechanic
    one_liner: "In-memory column store with automatic association by shared field names."
    requires: []
    builds_on: []
```

A single chapter that teaches Set Analysis can now be mechanically
verified: it must introduce `set_analysis`, must have already
introduced `aggregation_functions` and `field_selections` by this point,
and should reinforce `associative_model` because the graph says it
builds on it.

That is the leverage this phase buys.
