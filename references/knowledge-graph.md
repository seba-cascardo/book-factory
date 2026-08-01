# Phase 1.5 — Knowledge Graph

Long-form nonfiction rarely fails at the paragraph level. It fails at the
*sequencing* level — unit 6 assumes a concept the reader does not meet until
unit 8 — or at the *terminology* level: three units call the same feature by
three different names. By the time a beta reader catches either, the fix means
cascading edits across half the manuscript.

The Knowledge Graph is a pre-outlining artifact that makes both failure modes
visible before a word is written. It lists every concept the document teaches,
what each concept depends on, and (in sequential profiles) where each concept
is introduced and reinforced.

**This phase runs AFTER setup and BEFORE outlining.**

## Profile applicability

| Profile | Mode | Why |
|---------|------|-----|
| `book-technical` | **Full** — mandatory | Sequential pedagogy lives or dies on dependency order |
| `scientific-paper` | **Full** — mandatory | Terms must be defined before use in reading order; claims rest on concepts (see § scientific-paper) |
| `corporate-guide` | **Terminology-only** | Light sequence, skim-friendly; the risk is naming drift, not ordering |
| `product-docs` | **Terminology-only** | Modular — no reading order exists, so "introduced before used" is meaningless |
| `book-literary` | Skipped | `plot-structure.md`, `arcs.md`, and `timeline.md` carry the equivalent continuity load |

## What you produce

`bible/knowledge-graph.yaml` — full schema in `templates/knowledge-graph.yaml`.
The graph is the ground truth for what "introduced" and "used" mean in
`outline/units.yaml` and the continuity tracker.

---

## Full mode (book-technical, scientific-paper)

- **Concepts**: every teachable idea the reader walks away knowing. A concept
  is named (stable ID), defined in one sentence, and tagged with its kind
  (term | mechanic | pattern | tool | convention | skill).
- **Dependencies**: directed edges. Concept A `requires` Concept B means the
  reader cannot understand A without having seen B first. Use `builds_on` for
  soft dependencies (A reinforces B; B-first is better pedagogy but not
  strictly necessary). Use `contrasts_with` when two concepts are naturally
  taught together by contrast (SQL JOIN vs. set operations) — order-agnostic
  within the pair.
- **Prerequisites**: concepts assumed before unit 1. These anchor the graph —
  every dependency chain must terminate either in a prerequisite or in another
  concept introduced in the document.
- **Placement**: `introduced_in: unit-NN` is set during outlining (null until
  then); `reinforced_in` optionally lists units that revisit the concept.

### scientific-paper specifics

- **Ordering runs on reading order, not writing order.** The outline fixes a
  writing order (Methods → Results → Introduction → Discussion → Abstract
  last), but the forward-reference check uses the order the *reader* meets the
  sections. A term first used in the Introduction and defined in Methods is a
  forward reference even though Methods was written first.
- **Prerequisites are venue-scoped**: what the target venue's typical reviewer
  already knows. "Familiar with transformer architectures" may be a
  prerequisite at one venue and a concept to introduce at another. Decide with
  the human against the venue named in `bible/meta.yaml`.
- **Claims tie-in**: every claim in `bible/claims-map.yaml` lists the concept
  IDs it rests on (its `concepts:` field). Constraint: every listed ID exists
  in the graph — a claim may not rest on a term the paper never defines. The
  Technical Reviewer (Axis C) and the Critic verify against this mapping.
- Typical size: 10–30 concepts. A paper is not a textbook; if the graph grows
  past ~40, the paper is probably trying to teach too much — raise it.

---

## Terminology mode (corporate-guide, product-docs)

Modular and light-sequence profiles have no guaranteed reading order — a
reader can land on any unit first. Dependency ordering is therefore not just
unnecessary, it is misleading: an outline that "introduces X in unit-03" gives
false comfort when readers routinely start at unit-07. The dominant failure
mode in these profiles is **terminology drift**: the same feature named three
ways across units, eroding trust and breaking search.

Reduced schema — concepts carry only:

```yaml
concepts:
  - id: escalation_path
    name: "Escalation path"          # the ONE canonical name
    kind: term
    one_liner: "The approved routing sequence when an issue exceeds first-line authority."
    contrasts_with: [incident_report]  # near-neighbors readers confuse
```

Omit `requires`, `builds_on`, `introduced_in`, `reinforced_in` entirely. Do
not fill them "just in case" — if you find yourself needing ordering in a
modular profile, question the profile choice with the human instead.

The graph acts as a **controlled vocabulary**:

- Writers use the canonical `name` everywhere; near-synonyms are drift, and
  the `one_liner` is the approved one-line wording when a unit must define
  the term inline.
- `contrasts_with` marks pairs a reader might conflate, so any unit using one
  term disambiguates from — or links to — the other.
- A unit that needs a concept either defines it inline in one line or links
  to the unit that owns it (product-docs: as a linked prerequisite).

Aim for 15–60 terms. Seed the list from `bible/glossary.md` — in this mode
the graph is essentially the glossary with stable IDs and contrast edges.

---

## Roles in the pipeline

| Agent | Full mode | Terminology mode |
|-------|-----------|------------------|
| Writer | "What may I assume?" — every concept used must be a prerequisite or introduced ≤ this unit | Canonical names only; inline definitions use the `one_liner` wording |
| Technical Reviewer | Axis B — flag concepts used before introduction, terminology drift | Axis B — flag naming drift against the canonical list |
| Critic (rubric) | No undeclared forward references; every `concepts_introduced` entry actually gets introduced | Terminology consistency items |
| Continuity Guardian | Whole-document audit: each concept introduced exactly once, no orphans, no cycles. **Phase 4 coverage audit**: cross-reference prose against KG + glossary + prerequisites; report orphan terms to `bible/orphan-terms-audit.md` for human triage | Phase 4 cross-unit consistency audit: same coverage audit, plus canonical-name enforcement across units |

**Two flavors of "orphan" — don't confuse them:**

- **Orphan concept in KG** (full mode only) — a concept with no
  `introduced_in` unit, or never reached by any dependency chain. Caught at
  sign-off and at every outline revision. Symptom: a node nothing points to.
- **Orphan term in prose** (both modes) — a term used in unit text that is
  *not* declared in KG, glossary, or prerequisites. Caught at Phase 4 by the
  Continuity Guardian's coverage audit. Symptom: the manuscript invokes a
  concept the graph never sanctioned.

The first guards the graph's integrity; the second guards prose–graph
alignment. They are complementary.

---

## How to build it (guided session)

This is a collaborative design session with the human, not a form to fill
solo. Full mode: 30–90 minutes of real work. Terminology mode: 15–30 minutes,
seeded from the glossary.

### Step 1 — Inventory the concepts (both modes)

Read `bible/scope.md`, `bible/glossary.md`, and any prior outline or draft
material. List every teachable unit of knowledge that will appear in the
final document. Don't include low-level facts ("HTTP uses TCP"); include
teachable *units* ("request/response cycle"). The rule: if a reader could ask
"where do I learn about X?", X is a concept.

Full mode, book-length: aim for 30–100 concepts for a 200–400-page book.
Fewer than 20 means underspecifying; more than 150 means splitting what
should be taught together.

### Step 2 — Define prerequisites (full mode only)

What does the reader know on page 1? Be concrete:

- "Comfortable reading basic SQL (SELECT, JOIN, WHERE, GROUP BY)" — OK
- "Familiar with databases" — too vague, reject and refine

Every prerequisite is a leaf node. Dependencies can point at prerequisites to
signal "builds on the reader's existing knowledge".

### Step 3 — Draw edges

Full mode: for each concept answer *to understand this, the reader must have
already seen what?* — using `requires` (hard; cycles are a design bug),
`builds_on` (soft), `contrasts_with` (taught together). Edges need not be
perfect on the first pass; outlining and early drafting will surface missing
ones.

Terminology mode: only `contrasts_with` — walk the list asking "which other
term could a reader confuse this with?"

### Step 4 — Run the cycle check (full mode only)

Hard cycles (`A requires B`, `B requires A`) are a design flaw the pipeline
cannot untangle. The human must choose: split a concept, introduce one piece
as a preview, or merge the two. Report cycles and do not proceed to outlining
with any unresolved.

### Step 5 — Sign off

Present the graph to the human. Explicit sign-off on:

- Full mode: concept list complete; prerequisites correctly scoped; no
  cycles; every chain terminates. Papers: every claims-map `concepts:` ID
  resolves.
- Terminology mode: one canonical name per concept; `one_liner` wordings
  approved; contrast pairs complete.

Record the sign-off in `project-status.yaml` under
`knowledge_graph.last_verified`.

## Downstream: the graph seeds the concept audit

At the Phase 4.5 manuscript gate, `scripts/bootstrap_probes.py` derives one
concept probe per graph node, and those probes are what gather every passage in
the book that makes a claim about a concept (`references/claim-index.md`). A
project with a good graph gets MG-1 nearly for free.

Two consequences worth knowing while you build it:

- **A node's `name` becomes a search pattern.** A descriptive label ("STORE —
  writing a QVD") makes a bad probe; the surface term readers actually see makes
  a good one. Where the two differ, add the surface forms under `aliases`.
- **The graph is not the ceiling.** The concept that actually contradicts itself
  is often finer-grained than a node — it lives in one sense of a term the node
  covers. Those get hand-written probes in `bible/concept-probes-tuned.yaml`,
  which may introduce ids with no graph node at all. That is expected, not a
  modelling error; do not split the graph to chase it.

---

## What to avoid

- **Don't build the graph in the Writer's head, per unit.** Sequencing and
  naming are whole-document properties. Per-unit "I think this concept needs
  to come first" is exactly the drift the graph prevents.
- **Don't treat the graph as frozen after setup.** Revise it when drafting
  reveals missing dependencies or over-granular concepts; bump
  `knowledge_graph.last_verified` on every revision. Revisions are cheap;
  undetected forward references are expensive.
- **Don't confuse concepts with sections.** One section can introduce two
  concepts; one concept might need a whole unit. The mapping lives in the
  outline, not the graph.

## The leverage

With a signed graph, a unit that teaches `set_analysis` — where the graph
says it `requires: [aggregation_functions, field_selections]` and
`builds_on: [associative_model]` — can be mechanically verified: the unit
must introduce `set_analysis`, both required concepts must carry an
`introduced_in` earlier than this unit, and the unit should reinforce
`associative_model`. No judgment call, no vibes: the check either passes or
it doesn't. That is what this phase buys.
