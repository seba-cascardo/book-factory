# Outlining Process

After the bible is complete, create the chapter-by-chapter outline. This is the
bridge between "what the book is about" and "what happens on each page".

The outline lives in `outline/chapters.yaml`. It must be approved by the human
before any writing begins.

Literary and technical projects outline differently. Read only the section that
matches `project.type`.

---

## Common first step — chapter count

Based on `bible/meta.yaml`:

- Estimate total chapters from the target word count and target chapter length.
  2,000–5,000 words per chapter is typical for prose; technical chapters can be
  longer if they're reference-oriented or shorter if tutorial-oriented.
- Front-load the estimate but expect ±20% flexibility during writing.
- Some chapters will merge or split. That's fine.

---

## § Literary branch

Follow this if `project.type: literary`.

### Beat mapping

For each chapter, define:

```yaml
- number: 1
  title: "[Working title — can change]"
  pov: "[POV character, if alternating]"
  timeline: "[When this happens in story chronology]"
  location: "[Primary setting]"

  beats:
    - "[What happens first — an action, revelation, decision]"
    - "[What happens next]"
    - "[The chapter's turning point]"
    - "[How the chapter ends — hook or unresolved thread]"

  emotional_arc:
    start: "[Character's emotional state at chapter opening]"
    shift: "[What changes and why]"
    end: "[Emotional state at chapter close]"

  plot_threads:
    advances:
      - "[Thread name]: [How it advances]"
    introduces:
      - "[New thread]: [What's planted]"
    resolves:
      - "[Thread name]: [How it closes]"

  reveals:
    to_reader: "[What the reader learns]"
    to_characters: "[What characters learn]"

  characters_present:
    - "[Name]"

  target_words: "[Range, e.g., 3000-4000]"

  notes: "[Tricky aspects, mood reference, writer notes]"
```

### Arc verification

After mapping all chapters:

- Every character arc has identifiable progression points across chapters.
  If a character disappears for 8 chapters, that's either intentional or a
  structural problem.
- Overall tension escalates (non-linearly — peaks and valleys, trending up).
- Subplots appear at least every 3–4 chapters unless explicitly dormant.
- Pacing alternates between high-tension and character-development chapters.
- The **midpoint** chapter shifts something significant. If it's uneventful,
  restructure.

### Human review (literary)

Present the complete outline with:

1. One-paragraph story summary as outlined.
2. Full chapter list with 1-line summaries.
3. Pacing concerns or structural questions.
4. Any chapters where beat placement is uncertain.

---

## § Technical branch

Follow this if `project.type: technical`.

### Pedagogical structure check

Before writing chapter-level outlines, lay out the overall learning flow:

- **Dependency graph**: which concepts depend on which? Make sure no chapter
  uses a concept not yet introduced (unless the structure is deliberately
  reference-style).
- **Knowledge staircase**: each chapter should add exactly one (maybe two)
  new big ideas. Piling five new concepts into one chapter breaks readers.
- **Practice beats**: in a sequential tutorial, every 2–3 chapters should
  include exercises or a project milestone that USES the concepts introduced
  so far. Pure-theory stretches longer than that lose readers.
- **Review points**: at major section boundaries, explicitly summarize what
  the reader can now do. Not filler — a short confirmation.

### Chapter entry (technical)

For each chapter:

```yaml
- number: 1
  title: "[Chapter title]"
  section: "[Part I / Part II / etc., if applicable]"

  purpose: "[One sentence: what the reader can do after this chapter]"

  concepts_introduced:
    - name: "[Term]"
      definition: "[Short definition — will go in glossary]"
      difficulty: "[easy / medium / hard]"

  concepts_used:
    - "[Previously introduced concept — chapter where it was introduced]"

  structure:
    - "[Section heading 1]: [What it covers]"
    - "[Section heading 2]: [What it covers]"
    - "[Section heading 3]: [What it covers]"

  examples:
    - description: "[What the example demonstrates]"
      code_or_scenario: "[Minimal sketch]"

  exercises:
    - prompt: "[What the reader is asked to do]"
      solution_sketch: "[Brief]"

  forward_references:
    - "[Concept deferred to Chapter N with brief justification]"

  target_words: "[Range]"

  risks: "[Places a reader might get stuck, misconceptions to preempt]"
```

### Dependency verification

After mapping all chapters, verify:

- **No forward dependencies**: every `concepts_used` points to an earlier
  `concepts_introduced`. If not, either the order is wrong or the concept needs
  a brief in-chapter introduction.
- **No orphans**: every `concepts_introduced` is used in at least one later
  chapter. If not, either the concept is optional (mark it) or it shouldn't
  be in the book.
- **Exercise coverage**: every major concept has at least one exercise that
  uses it within 1–2 chapters of introduction.
- **Pacing**: no more than 2 consecutive theory-only chapters without hands-on
  content.

### Human review (technical)

Present the complete outline with:

1. One-paragraph summary of the learning arc.
2. Full chapter list with each chapter's purpose.
3. A dependency diagram (prose is fine — just show which chapters depend on
   which).
4. Any coverage gaps or pedagogical concerns.

---

## Lock and proceed

Once approved:

- Save to `outline/chapters.yaml`.
- Update `project-status.yaml`: `phase: writing`, `current_chapter: 1`.
- Announce: ready to start writing chapter 1.

The outline is a living document. It can be revised mid-writing, but only with
human approval. If the Writer flags a beat as problematic, the human decides
whether to change the outline or keep it.
