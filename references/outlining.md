# Phase 2 — Outlining

After the bible is complete (and the knowledge graph signed off where the
profile requires one), write the unit-by-unit outline in `outline/units.yaml`.
The entry schema is `templates/chapter-entry.yaml`; the human approves the
outline before any writing. Read only the branch for `project.profile`.

## Common first step — unit count

- **Book profiles**: total words ÷ unit length (2,000–5,000 words is typical
  for prose; reference-style technical chapters run longer, tutorials
  shorter). Expect ±20%: units merge and split during writing.
- **corporate-guide**: one section per decision or task area in
  `bible/scope.md`.
- **product-docs**: one article per task (branch below).
- **scientific-paper**: fixed by the IMRaD skeleton; estimate lengths against
  the venue's page budget.

Units are `unit-NN` in the order the reader meets them; talk to the human in
the profile's word.

---

## § book-technical

**Staircase first.** Assign every KG concept to the unit that introduces it;
no unit uses a concept not yet introduced (unless meta declares a
reference-style structure). One, at most two, new big ideas per unit. Practice
every 2–3 units using what has been introduced. At part boundaries, a short
confirmation of what the reader can now do.

**Entries** carry: title, part, **purpose** (what the reader can DO after it),
**concepts_introduced** (KG ids), **concepts_used** (KG ids with the unit that
introduced each), structure (headings, one-line coverage), examples (what
each shows; runnable or not), exercises (prompt, solution sketch, concepts),
**forward_references** (deliberate deferrals with target unit and reason —
undeclared ones are the bug), target_words, risks, closing per the profile.

**Verify**: every `concepts_used` points to an earlier `concepts_introduced`
(else reorder or add a brief in-unit introduction); every introduced concept
is used later (else mark it optional or cut it); every major concept gets an
exercise within 1–2 units; never more than 2 theory-only units in a row. Then
write `introduced_in: unit-NN` into `bible/knowledge-graph.yaml`, set its
`every_concept_assigned_to_unit` constraint to true and bump
`knowledge_graph.last_verified`.

**Present**: the learning arc in one paragraph; units with their purposes; the
dependency picture in prose; coverage gaps and concerns.

---

## § book-literary

Precondition: sheets, `plot-structure.md` (with the ending), `arcs.md`,
`timeline.md`, `story-ledger.yaml` and the seeds from setup. The outline is the
story's design contract: the Writer drafts from its scene cards and the
Critic scores against them.

### Entries and scene cards

Schema: `templates/chapter-entry.yaml` § LITERARY — `pov`, `timeline` (story
date with weekday), `location`, `characters_present` (slugs), `arc_moves`,
beats as scene cards, emotional arc, threads, reveals, `secondary_lines`,
`key_scene`. Card rules:

- Every beat is `scene` or `exposition-within-scene`.
- A scene of ≥ 300 planned `words` carries `want`, `opposition`, `pivot`,
  `value` (`name`, `from` → `to`) and `crisis` — a dilemma between two costs.
  Tension and key scenes add `attempts`: what the POV tries, and why each
  fails. Why: `docs/rationale/literary.md#scene-cards`
- `exposition-within-scene` carries `information` and `actioned_by` (who
  wants it, withholds it, pays to say it).
- A deliberate slow beat names its `pause`: the interruption or internal
  change that ends it.
- `link`: how the previous scene causes this one — "therefore …" or "but …",
  never "and then". The first card links to the previous unit's last.
- `ledger`: the ids the scene plants or pays.
- `key_scene: true` sparingly — the climax, the midpoint, a turning point the
  human cares about — with the card marked `key: true`.

### Characters, arcs, ledger

- Every slug in `characters_present` has a complete sheet (R1). A new name
  while outlining — in `characters_present` or in a card's text (`summary`,
  `want`, `opposition`, `pivot`, `crisis`, `attempts`, `information`,
  `actioned_by`; a `world.md` § Names entry counts) → the questionnaire before
  the unit stays in the outline (R4, `references/character-questionnaire.md`;
  `check_story.py` reports `CHAR-UNKNOWN`). Nicknames and diminutives the page
  will use go in the sheet's `aliases`, or the scripts read them as new names.
- Every sheet turning point sits in a unit where that character is present,
  with an `arc_moves` entry — `turning_point` is the 1-based index into the
  sheet's `arc.turning_points`; `resolves_in` ≤ `ending.final_unit`.
- Every ledger entry has a planned `payoff_unit` ≤ `final_unit`, appears in a
  card's `ledger.plants`, and its payoff in a card's `ledger.pays`. Mysteries
  the ending leaves open are `deliberately-ambiguous` from the start, with a
  note.

### Shape

Tension rises in peaks and valleys; value changes alternate; subplots surface
at least every 3–4 units unless declared dormant; a principal absent for many
units is a decision written in `notes`; the midpoint flips a value or
reframes the dramatic question. Tally `characters_present`: every character in
2+ units gets, in one of them, a `secondary_lines` note guaranteeing a line of
their own (craft-3).

### Echo check

For each turning point — the major beats of `plot-structure.md` and every
turning point of a protagonist or principal — dispatch K = 3 fresh subagents
(5 for the climax and the ending) given only the premise and a plain summary
of the story up to that point, each asked what happens there, in one
paragraph. If most converge on one move and the planned turning point is that
move, flag it **model default** and discuss it with the human: keep it
knowingly, or change it. Record each turning point, the alternatives in a
line each, and the decision in `outline/echo-check.md`.
Why: `docs/rationale/literary.md#echo-check`

### Stress test

Write plain synopses — story events only, no cards, ledger or arcs — cut at
about ⅓, ½ and ¾ of the units: `outline/synopsis-to-unit-NN.md`. Reader-POV
reads each cut as a fresh subagent (`references/agents/reader-pov.md` §
Outline stress test). List every prediction that matches a planned turning
point for the human.

### Design rubric, review, readiness

Fill the design rubric (`references/rubric-literary.md` § Design rubric) →
`outline/design-scorecard.yaml`. Present: the story in one paragraph; the
units, one line each; the design scorecard, fails first; model defaults and
predicted turning points; the secondary-character tally; open questions. After
approval (§ Lock and proceed), `python scripts/pipeline_step.py ready` must
exit 0 (R3); fix any blocker with the human (questionnaire, plot-structure,
seeds, human calibration passages) and re-run.

---

## § corporate-guide

**Entries** carry: title, **purpose** (what the employee can do or decide),
**audience_moment** (when someone reaches for it: a meeting, an incident, an
approval), key_points, practice (optional, internal cases per
`meta.yaml → organization`), templates_and_checklists, cross_refs,
target_words.

**Rules**: every section opens self-contained and task-first — a reader who
skipped everything before can use it; front-to-back order works but nothing
depends on it (sections are skimmed and forwarded one at a time);
cross-references name the topic ("see the section on escalation paths"),
never a number.

**Verify**: openings self-contained; every cross_ref resolves to a real
section topic; KG terms under canonical names; no section depends on another's
example or exercise. **Present**: sections with purpose and audience_moment,
the suggested reading order and why, topics of `scope.md` left uncovered.

---

## § product-docs

**Inventory by task**, not by feature: what users try to DO ("rotate an API
key"), grouped by domain, from `scope.md`, support tickets and search queries
when available. One article ≈ one task.

**Entries** carry: task-phrased title, **`type`** (Diátaxis: `tutorial` |
`how-to` | `reference` | `explanation` — `references/profiles/product-docs.md`),
**description** (one sentence; becomes frontmatter), user_goal,
**prerequisites** (links, never assumed reading), structure, **tags**,
**related**, target_words.

**Rules**: no forward references, ever — any article can be read first; a
concept needed here is explained in one line (the KG's `one_liner`) or linked
as a prerequisite. Every entry makes sense alone, landing from search.

**Verify**: every article has one `type`; prerequisite links resolve and form
no cycle; every task has exactly one owning article; tags come from one finite
list defined in the
outline; KG terms under canonical names. **Present**: the task inventory by
domain; articles with description and prerequisites; the tag list; tasks out
of scope.

---

## § scientific-paper

**Skeleton** in reading order (abstract, introduction, methods, results,
discussion, plus the venue's extras). Each entry carries a
**`writing_order_rank`**; the pipeline walks units by ascending rank: Methods
→ Results → Introduction → Discussion → Abstract last (highest rank). Methods
and Results are bound by what was done, so writing them first keeps the paper
from claiming more than its evidence; the Abstract summarizes claims that
already survived review.

**Entries** carry: name, `writing_order_rank`, **claims** (ids from
`bible/claims-map.yaml`), key_moves, figures_tables (each with the claim it
supports), evidence_needed, target_words, and a checklist — Methods: the
reproducibility checklist (data availability, parameters, environment,
seeds); Discussion: **limitations**, a mandatory move (rubric critical).

**Claims assignment**: every map claim is argued with evidence in at least one
section (else give it one or remove it from the map); no section lists a claim
absent from the map (new claims enter the map first, with evidence); a
Limitations move exists; every claim's `concepts:` resolve in the KG.
**Present**: reading and writing order; claims per section; claims unassigned
or weakly evidenced; the reproducibility checklist.

---

## Lock and proceed

Once the human approves, in this order:

1. Save `outline/units.yaml` and set `project-status.yaml → outline.approved:
   true` with `outline.approved_on` (`ready` reads it).
2. Run `python scripts/pipeline_step.py ready`; it must exit 0 (book-literary:
   R3). Blockers go back to the human.
3. Update `project-status.yaml`: `phase: drafting`, `current_unit:` the first
   unit — for `scientific-paper`, the first in writing order (methods).
4. Announce readiness to start.

The outline can change mid-writing, but only with the human's approval. A
Writer that flags a beat or entry never deviates silently; the human decides.
