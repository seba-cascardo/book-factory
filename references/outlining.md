# Phase 2 — Outlining

After the bible is complete (and the Knowledge Graph is signed off, where the
profile requires one), create the unit-by-unit outline. This is the bridge
between "what the document is about" and "what happens on each page".

The outline lives in `outline/units.yaml` — same path in every profile. It
must be approved by the human before any writing begins. The annotated
per-unit entry schema is `templates/chapter-entry.yaml`; the branches below
say what each profile's entries must contain and how to verify the whole.

Read only the branch matching `project.profile` in `bible/meta.yaml`.

---

## Common first step — unit count

- **Book profiles**: estimate total chapters from target word count and
  target chapter length. 2,000–5,000 words per chapter is typical for prose;
  technical chapters run longer if reference-oriented, shorter if
  tutorial-oriented. Expect ±20% flexibility — chapters will merge and split
  during writing, and that's fine.
- **corporate-guide**: derive sections from the topic inventory in
  `bible/scope.md`; one section per decision or task area an employee
  actually faces.
- **product-docs**: derive articles from the task inventory (see branch —
  tasks first, not features).
- **scientific-paper**: the section count is fixed by the IMRaD skeleton;
  estimate only lengths against the venue's page budget.

Units are numbered `unit-NN` in the order the *reader* meets them. When
talking to the human, use the profile's word (chapter, article, section).

---

## § book-technical

### Pedagogical staircase

Before writing unit-level entries, lay out the overall learning flow:

- **Dependency order**: assign every KG concept to the unit that introduces
  it. No unit may use a concept not yet introduced (unless the structure is
  deliberately reference-style — say so in meta).
- **Knowledge staircase**: each unit adds exactly one (maybe two) new big
  ideas. Piling five new concepts into one unit breaks readers.
- **Practice beats**: every 2–3 units include exercises or a project
  milestone that USES the concepts introduced so far. Pure-theory stretches
  longer than that lose readers.
- **Review points**: at major part boundaries, explicitly confirm what the
  reader can now do. Not filler — a short confirmation of capability.

### Chapter entries

Each entry (full annotated version in `templates/chapter-entry.yaml`)
carries: number, title, section/part, **purpose** (one sentence — what the
reader can DO after this unit), **concepts_introduced** (KG IDs),
**concepts_used** (KG IDs plus the unit that introduced each — this is what
dependency verification runs on), structure (section headings with one-line
coverage), examples (what each demonstrates; runnable or not), exercises
(prompt + solution sketch + concepts used), **forward_references** (concepts
deliberately deferred, with the target unit and a one-line justification —
declared deferrals are fine; undeclared ones are the bug), target_words,
risks (where readers get stuck, misconceptions to preempt), and closing per
the profile's closing policy.

### Dependency verification

After mapping all units, verify:

- **No forward dependencies**: every `concepts_used` points to an earlier
  `concepts_introduced`. If not, either the order is wrong or the concept
  needs a brief in-unit introduction.
- **No orphans**: every `concepts_introduced` is used in at least one later
  unit. If not, mark the concept optional or cut it from the book.
- **Exercise coverage**: every major concept gets at least one exercise
  within 1–2 units of introduction.
- **Pacing**: no more than 2 consecutive theory-only units without hands-on
  content.

Then write `introduced_in: unit-NN` back into `bible/knowledge-graph.yaml`,
flip its `every_concept_assigned_to_chapter` constraint to true, and bump
`knowledge_graph.last_verified`.

### Human review

Present: one-paragraph summary of the learning arc; full unit list with each
unit's purpose; the dependency picture in prose (which units depend on
which); any coverage gaps or pedagogical concerns.

---

## § book-literary

### Beat mapping

Each entry carries: number, title, pov, timeline (story chronology),
location, typed beats (below), emotional_arc (start / shift / end),
plot_threads (advances / introduces / resolves), chekhov (load / fire),
reveals (to_reader / to_characters), characters_present, continuity_notes,
target_words, notes.

**Beats are typed.** Every beat is `scene` or `exposition-within-scene`;
beats meant as deliberate decelerations additionally carry a `pause`
annotation:

```yaml
beats:
  - type: scene
    summary: "Diego appears unexpectedly. First friction."
  - type: exposition-within-scene
    summary: "Diego reveals the brother's deception (first half)."
    information: "the deception exists; Marta was excluded from it"
    actioned_by: "Marta resists hearing it; Diego pays a cost for saying it"
  - type: scene
    summary: "Marta alone with the cold coffee."
    pause: "ends when the waiter's question forces her to decide — stay or go"
```

Why typed: unmarked exposition gets drafted as informative dialogue —
characters explaining things to each other for the reader's benefit. Marking
the beat forces the Writer to *action* the information: someone wants it,
someone withholds it, learning it costs something. The Critic checks
`exposition-within-scene` beats against `craft-1`.

Why the `pause` annotation: a deliberate slow beat must contain its own turn
— an interruption or an internal state change — or it reads as scenery with a
character standing in it. Name that turn in the outline so the Editor and the
rubric (`craft-2`) have something concrete to verify.

### Arc verification

After mapping all units:

- Every character arc has identifiable progression points across units. A
  character who disappears for 8 units is either intentional or a structural
  problem — decide which, in the outline.
- Overall tension escalates non-linearly — peaks and valleys, trending up.
- Subplots surface at least every 3–4 units unless explicitly dormant.
- Pacing alternates between high-tension and character-development units.
- The **midpoint** unit shifts something significant. If it's uneventful,
  restructure.

### Secondary-character line check

Tally `characters_present` across all units. Every character who appears in
2+ units gets an outline note — in at least one of those units — guaranteeing
at least one line that is *theirs*: a want, an objection, a joke; not a
functional relay of information or a door that talks. Record it in the entry:

```yaml
secondary_lines:
  - character: "Mariana"
    note: "gets one line of her own — she disagrees with the plan out loud"
```

Why: functional secondaries are a systematic failure, not an occasional one —
drafts default to secondaries who exist only to serve the protagonist's
scene. Guaranteeing the line at outline time is cheaper than retrofitting
personhood in revision. Feeds rubric `craft-3`.

### Human review (literary)

Present: one-paragraph story summary as outlined; full unit list with 1-line
summaries; pacing concerns or structural questions; any units where beat
placement is uncertain; the secondary-character tally.

---

## § corporate-guide

### Section entries

Each entry carries: number, title, **purpose** (what the employee can do or
decide after reading), **audience_moment** ("when does someone reach for
this?" — a meeting, an incident, an approval request), key_points, practice
(optional — exercises grounded in the organization's internal cases, per
`meta.yaml → organization`), templates_and_checklists (artifacts the section
ships), cross_refs (topic-based, see below), target_words.

### Structural rules

- **Self-contained openings**: each section must open so a reader who skipped
  everything before it can still use it. The first paragraph states what the
  section covers and when to use it — task-first. Never open with "as we saw
  earlier" or assume the previous section landed.
- **Light sequence**: order sections so front-to-back reading works, but
  never *depend* on it. This document will be skimmed in 10-minute windows
  and forwarded one section at a time.
- **Topic-based cross-refs**: refer to other sections by topic ("see the
  section on escalation paths"), never by number ("see Section 3"). Numbered
  refs break when the guide is excerpted or reorganized, and the profile bans
  them in prose anyway — don't seed the outline with refs the Writer can't
  legally render.

### Verification

Every opening plan is self-contained; every cross_ref resolves to a real
section topic; every KG term appears under its canonical name; no section
depends on an exercise or example defined in another section.

### Human review

Present: full section list with purpose + audience_moment per section; the
suggested reading order and why; any topics from scope.md left uncovered.

---

## § product-docs

### Article inventory by task

Start from tasks, not features: list what users actually try to DO ("rotate
an API key", "invite a teammate"), not what the product has ("the Settings
page"). Sources: scope.md, support tickets, search queries if the human has
them. Group by task domain. One article ≈ one task; an article covering three
tasks is three articles.

### Article entries

Each entry carries: number, title (task-phrased — "Rotate an API key", not
"API keys"), **description** (one sentence, becomes frontmatter),
user_goal, **prerequisites** (links to other articles — never assumed
reading), structure (steps or sections), **tags**, **related** (articles to
surface at the end), target_words.

### Structural rules

- **NO forward references, ever.** Modular means any article can be the
  first one read; there is no "later in this guide". A concept needed here is
  either explained inline in one line (using the KG's canonical `one_liner`
  wording) or linked as a prerequisite article. An outline entry containing
  "covered further down" is a bug, not a style choice.
- **Standalone entries**: every article's outline must make sense read
  alone, in any order, landing from search with a task half-done.

### Verification

Every prerequisite link resolves to a real article in the inventory; no
cycles in prerequisite links; every task in the inventory has exactly one
owning article and no two articles own the same task; tags come from a
shared, finite tag list (define it here, in the outline); every KG term is
used under its canonical name.

### Human review

Present: the task inventory grouped by domain; the article list with
description + prerequisites per article; the tag list; tasks deliberately
out of scope.

---

## § scientific-paper

### IMRaD skeleton

`outline/units.yaml` lists sections in **reading order** — abstract,
introduction, methods, results, discussion, plus venue-specific extras
(related work, limitations if the venue wants it standalone, conclusion).
Unit numbers follow reading order; they are stable IDs for `drafts/unit-NN/`.

Each entry carries a **`writing_order_rank`** field — an integer that ranks
the unit in write order — and the pipeline walks the units by ascending rank,
not in reading order. Lower rank is written first; the Abstract gets the
highest rank:

Methods → Results → Introduction → Discussion → Abstract last.

Why: Methods and Results are constrained by what was actually done — write
them first and the paper cannot drift into claiming more than the evidence
supports. The Introduction frames what Results already proved. The Abstract
is written last because it summarizes claims that must already have survived
review — an abstract written first is a promise the paper then bends to keep.

### Section entries

Each entry carries: number (reading order), name, `writing_order_rank`
(integer write-order rank), **claims** (IDs from `bible/claims-map.yaml`
this section argues), key_moves (the
section's argumentative steps, one line each), figures_tables (planned, with
the claim each supports), target_words, and a checklist where applicable —
Methods carries the reproducibility checklist (data availability, parameters,
environment, seed/rng policy); Discussion carries **limitations** as a
mandatory move (rubric critical).

### Claims assignment

Walk `bible/claims-map.yaml` and assign every claim to the sections that
handle it: typically Results states it with evidence, Discussion interprets
it, the Introduction promises it, the Abstract compresses it. Then verify:

- Every claim in the map is assigned to at least one section that argues it
  with evidence — an unassigned claim either gets a section or leaves the map.
- No section's `claims` list contains an ID absent from the map — new claims
  discovered during outlining go into the map first, with their evidence.
- A Limitations move (or section) exists.
- Every claim's `concepts:` IDs resolve in the Knowledge Graph.

### Human review

Present: the skeleton with reading and writing order; per-section claims
assignment; the claims left unassigned or weakly evidenced; the
reproducibility checklist as planned.

---

## Lock and proceed

Once the human approves:

- Save to `outline/units.yaml`.
- Update `project-status.yaml`: `phase: writing`, `current_unit:` the first
  unit — for `scientific-paper`, the first unit in *writing* order (methods),
  not unit-01.
- Announce readiness to start the first unit.

The outline is a living document. It can be revised mid-writing, but only
with human approval. If the Writer flags a beat or entry as problematic, the
human decides whether to change the outline or keep it — a Writer never
silently deviates from an approved outline.
