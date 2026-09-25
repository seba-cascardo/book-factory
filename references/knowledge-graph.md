# Phase 1.5 — Knowledge graph

Long nonfiction fails less at the paragraph than at the **sequence** (unit 6
assumes a concept the reader meets in unit 8) and the **terminology** (three
units, three names for one feature). The knowledge graph makes both visible
before a word is written: every concept the document teaches, what it depends
on, and — in sequential profiles — where it is introduced. It runs after setup
and before outlining.

| Profile | Mode | Why |
|---------|------|-----|
| `book-technical` | Full — mandatory | Sequential pedagogy lives or dies on dependency order |
| `scientific-paper` | Full — mandatory | Terms defined before use in reading order; claims rest on concepts |
| `corporate-guide` | Terminology-only | Light sequence; the risk is naming drift |
| `product-docs` | Terminology-only | No reading order exists |
| `book-literary` | Skipped | Plot structure, arcs, timeline and story ledger carry the load |

Output: `bible/knowledge-graph.yaml` (schema: `templates/knowledge-graph.yaml`)
— the ground truth for "introduced" and "used" in `outline/units.yaml` and the
tracker.

## Full mode

- **Concepts**: every teachable idea, with a stable id, a one-sentence
  definition and a kind (term | mechanic | pattern | tool | convention |
  skill).
- **Edges**: `requires` (hard — the reader cannot understand A without B;
  cycles are design bugs), `builds_on` (soft), `contrasts_with` (taught
  together, order-agnostic).
- **Prerequisites**: what the reader knows on page 1 — concrete ("reads basic
  SQL: SELECT, JOIN, WHERE, GROUP BY"), never vague ("familiar with
  databases"). Every chain ends in a prerequisite or an introduced concept.
- **Placement**: `introduced_in: unit-NN` set during outlining;
  `reinforced_in` optional.

**scientific-paper**: forward references run on **reading** order, not the
IMRaD writing order (a term used in the Introduction and defined in Methods is
a forward reference). Prerequisites are venue-scoped — decide them with the
human against the venue in `meta.yaml`. Every claims-map entry lists the
concept ids it rests on (`concepts:`), and each must exist in the graph. Typical
size 10–30 concepts; past ~40, the paper is teaching too much — raise it.

## Terminology mode

A reader can land on any unit first, so ordering is meaningless and misleading
here; the failure is terminology drift. Concepts carry only:

```yaml
concepts:
  - id: escalation_path
    name: "Escalation path"            # the ONE canonical name
    kind: term
    one_liner: "The approved routing sequence when an issue exceeds first-line authority."
    contrasts_with: [incident_report]  # near-neighbours readers confuse
```

No `requires`, `builds_on`, `introduced_in`, `reinforced_in` — needing ordering
in a modular profile means questioning the profile with the human. The graph is
a controlled vocabulary: canonical names everywhere, the `one_liner` as the
approved inline definition, `contrasts_with` pairs disambiguated or linked.
Aim for 15–60 terms, seeded from the glossary.

## Roles in the pipeline

| Agent | Full mode | Terminology mode |
|-------|-----------|------------------|
| Writer | Every concept used is a prerequisite or introduced ≤ this unit | Canonical names; inline definitions use the `one_liner` |
| Technical Reviewer | Axis B: concepts used before introduction, terminology drift | Axis B: naming drift |
| Critic | `outline-1/2`, `forward_refs` rows | Terminology rows |
| Continuity Guardian | Each concept introduced once, no orphans, no cycles; Phase 4 orphan-terms audit to `bible/orphan-terms-audit.md` | Phase 4 cross-unit audit and canonical-name enforcement |

Two different orphans: an **orphan concept** (a graph node with no
`introduced_in`, or unreachable — caught at sign-off and outline revisions) and
an **orphan term** (a term in prose that the graph, glossary and prerequisites
never sanctioned — caught by the Phase 4 coverage audit).

## Building it with the human

1. **Inventory** from scope, glossary and any prior material. A concept is
   anything a reader could ask "where do I learn about X?" for — teachable
   units, not low-level facts. Book-length: 30–100; under 20 underspecifies,
   over 150 splits what should be taught together.
2. **Prerequisites** (full mode) — concrete leaves.
3. **Edges** — full: "to understand this, what must the reader have seen?";
   terminology: only "which term could a reader confuse this with?".
4. **Cycle check** (full) — hard cycles block outlining until the human splits
   a concept, previews one piece, or merges the two.
5. **Sign-off** — full: list complete, prerequisites scoped, no cycles, chains
   terminate, papers' claim concepts resolve; terminology: one canonical name
   each, `one_liner`s approved, contrast pairs complete. Record
   `knowledge_graph.last_verified` in `project-status.yaml`.

Revise the graph when drafting reveals missing dependencies; bump
`last_verified` each time. Don't build it per unit in the Writer's head, and
don't confuse concepts with sections — the mapping lives in the outline.

## Downstream: the gate's concept audit

At Phase 4.5, `scripts/bootstrap_probes.py` derives a concept probe per node
(`references/claim-index.md`). A node's `name` becomes a search pattern: use
the surface term readers see and put other forms under `aliases`. Contradictions
often live in a finer sense than a node; those get hand-written probes in
`bible/concept-probes-tuned.yaml` — do not split the graph to chase them.

With a signed graph, "unit 7 teaches X, which requires A and B" is checkable:
both must carry an earlier `introduced_in`. No judgement call.
