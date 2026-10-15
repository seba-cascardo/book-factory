# Literary Project Setup

This reference guides the setup of a literary project (fiction, creative nonfiction,
memoir, narrative). The process has 6 sub-phases. Each produces files that become
part of the project bible. The human approves each sub-phase before the next begins.

**Rule**: do not rush this. A weak bible produces a weak book. Ask real questions,
propose options, let the human react. This is collaborative design, not a form.

---

## Sub-Phase 1 — Genre & Influences

### What to establish

- **Genre**: thriller, sci-fi, literary fiction, romance, horror, etc.
- **Subgenre**: hard sci-fi vs. space opera, cozy mystery vs. noir.
- **Tone**: dark, light, satirical, melancholic, whimsical, raw, clinical.
- **Inspirational works**: 2–5 books, authors, or films that define the target feel.
  For each, state specifically what to borrow: not "Cormac McCarthy" but "McCarthy's
  sparse dialogue, refusal to use quotation marks, desert-as-character".
- **What this book is NOT**: explicit negative constraints. "Not YA despite a young
  protagonist." "Not grimdark despite dark themes." Negative constraints are as
  important as positive ones — they prevent drift.
- **Target reader**: who is this for? What experience should they have at the end?

### Questions to ask

1. ¿Qué género y subgénero imaginás?
2. Nombrá 2–3 libros, películas o series que tengan el "feel" que buscás. ¿Qué
   específicamente querés tomar de cada uno?
3. ¿Qué tono? Oscuro, ligero, irónico, crudo, poético.
4. ¿Qué NO querés que sea este libro? ¿Qué trampas del género querés evitar?
5. ¿Quién lo leería? ¿Qué querés que sientan al terminarlo?

### Output

Write `bible/meta.yaml`:

```yaml
project:
  title: "[Working title]"
  type: literary
  language: "[Language of the book]"
  genre: "[Primary genre]"
  subgenre: "[If applicable]"
  tone: "[2-3 tone descriptors]"
  pov: "[TBD in Sub-Phase 6]"
  tense: "[TBD in Sub-Phase 6]"
  target_word_count: "[Estimated range]"
  target_chapters: "[Estimated range]"

influences:
  - work: "[Title]"
    author: "[Author]"
    take: "[What specifically to adopt]"

avoid:
  - "[Thing to explicitly not do]"
  - "[Genre trap to sidestep]"

target_reader: "[Description]"
desired_reader_experience: "[What the reader should feel/think after finishing]"
```

---

## Sub-Phase 2 — Characters

### What to establish

For each significant character (protagonist, antagonist, major supporting):

- **Core identity**: name, age, distinctive physical features (not police-report
  descriptions), occupation, social position.
- **Psychology**: conscious desire, unconscious need (often in tension with the
  desire), greatest fear, core wound and how it manifests now.
- **Contradiction**: every interesting character contains at least one. A generous
  person who can't forgive. A brave person who fears intimacy.
- **Voice**: how they speak (see anti-mediocrity-literary.md §6 for specifics).
- **Arc**: starting emotional state, ending emotional state, what forces the
  change.
- **Relationships**: specific dynamics, not labels. "She respects him but resents
  needing him" rather than "friends".

### Questions to ask (per character)

1. ¿Quién es? Contame lo básico.
2. ¿Qué quiere conscientemente? ¿Qué necesita en realidad?
3. ¿Qué pasado lo/la marcó?
4. ¿Cuál es su contradicción interna?
5. ¿Cómo habla? ¿Algo que lo/la distinga?
6. ¿Cómo cambia a lo largo de la historia?

It's fine to leave fields as `TBD` if a character isn't fully formed yet — they
often reveal themselves during outlining. Don't force premature commitment.

### Output

Create `bible/characters/[name].md` using the template in `templates/character-sheet.md`.

---

## Sub-Phase 3 — World

### What to establish

Depth depends on genre. Contemporary drama needs less worldbuilding than a
fantasy epic. Calibrate.

- **Setting**: where and when. Physical environment, climate, sensory character.
- **Social rules**: class structure, power dynamics, cultural norms that affect the story.
- **If speculative**: magic systems, technology rules, what differs from our
  world and what doesn't. Be specific about **constraints** — a magic system
  without limits is dramatically useless.
- **Economy**: how people survive, what's scarce, what's valued.
- **History that matters**: only backstory that directly affects the plot.

### Output

Write `bible/world.md` with sections appropriate to the project's scope.

---

## Sub-Phase 4 — Plot Structure

### What to establish

- **Structural framework**: three-act, five-act, Kishotenketsu, episodic, custom.
  Commit to one.
- **The dramatic question**: what question does the story pose that the ending
  answers?
- **Major beats**: non-negotiable plot events. At minimum: inciting incident,
  first turning point, midpoint shift, crisis/dark moment, climax, resolution.
- **Subplots**: secondary threads and how they weave into the main plot.
- **Tension architecture**: how tension escalates across the book. Not linear —
  map the peaks and valleys.

### Questions to ask

1. ¿Tenés una estructura en mente o la diseñamos juntos?
2. ¿Cuál es la pregunta dramática central?
3. ¿Qué momentos clave ya tenés claros?
4. ¿Hay subtramas? ¿Cómo se conectan con la trama principal?
5. ¿Cómo termina? (Está bien si no lo sabe aún, pero empujá suavemente.)

### Output

Write `bible/plot-structure.md` with the framework and all defined beats.

---

## Sub-Phase 5 — Narrative Arcs

### What to establish

Arcs ≠ plot. Plot is WHAT HAPPENS. Arcs are HOW THINGS CHANGE.

- **Character arcs**: connect the sketches from character sheets to specific
  plot beats. "Marco's arc breaks at the midpoint when [event] forces him to
  confront [wound]."
- **Thematic arcs**: what themes the book explores and how they evolve. Theme
  is not a message — it's a question explored from multiple angles.
- **Relational arcs**: how key relationships change across the book.
- **Arc intersections**: where character, thematic, and plot arcs converge.
  These intersections are usually the most powerful scenes.

### Output

Write `bible/arcs.md` mapping each arc with its key beats.

Write `bible/timeline.md` — a chronological sequence of all events (including
backstory) with dates or relative timing.

Initialize `bible/continuity-tracker.md` from `templates/continuity-tracker.md`.

---

## Sub-Phase 6 — Style Guide

### What to establish

This is the voice of the book. The most granular setup step, and the most
important.

- **POV**: first person, third limited, third omniscient, second person,
  alternating.
- **Tense**: past, present, alternating (with rules).
- **Prose register**: literary, accessible, sparse, lush, journalistic.
- **Sentence style**: preferences for length and complexity.
- **Paragraph density**: short punchy? Long flowing? Mixed?
- **Dialogue style**: quotation marks or dashes? Tags or action beats? Ratio
  of dialogue to narration.
- **Metaphor/simile policy**: frequent and ornate, rare and surgical, or
  domain-specific (a mechanic character whose narration uses machine metaphors).
- **Profanity / explicit content**: level and boundaries.
- **Chapter structure**: average length, titles, epigraphs.

### Calibration passages

The style guide MUST include 2–3 short passages (200–300 words each) written
in the target style. These serve as calibration anchors for every agent in the
pipeline. They don't need to be from the actual story — they just demonstrate
the voice.

Write these collaboratively with the human. Draft them, get feedback, refine
until the human says "yes, THIS is how I want it to sound."

### Output

Write `bible/style-guide.md` with all decisions plus calibration passages.

---

## Setup Completion Checklist

Before declaring setup complete:

- [ ] `bible/meta.yaml` — complete, reviewed
- [ ] `bible/characters/[name].md` — one per significant character, reviewed
- [ ] `bible/world.md` — appropriate depth for genre, reviewed
- [ ] `bible/plot-structure.md` — all major beats defined, reviewed
- [ ] `bible/arcs.md` — character + thematic arcs mapped, reviewed
- [ ] `bible/timeline.md` — chronological sequence, reviewed
- [ ] `bible/continuity-tracker.md` — initialized, reviewed
- [ ] `bible/style-guide.md` — with calibration passages, reviewed

Initialize `project-status.yaml` from `templates/project-status.yaml`. Set
`phase: outlining`, `current_chapter: 0`.

Announce: "La bible está completa. Siguiente paso: outline capítulo a capítulo.
¿Arrancamos?"
