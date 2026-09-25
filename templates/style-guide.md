# Style Guide — [Project Name]

<!-- templates/style-guide.md → bible/style-guide.md, filled at setup
     (references/setup.md § Sub-phase 6) and signed by the human. Read every
     turn by the prose agents with bible/voice-profile.md.
     Division of labor: HERE the calibration passages and the mechanical,
     reversible decisions ("which convention?"); in voice-profile.md the
     identity — fingerprint, bans, budgets, GOOD examples (derived from the
     passages below, so they are load-bearing twice). Keep only the sections
     your profile uses; delete comments and placeholders before sign-off. -->

Profile: [book-technical | book-literary | corporate-guide | product-docs | scientific-paper]

## Voice in one paragraph
<!-- 3–4 sentences of concrete commitments and refusals — what the prose does
     before abstracting, whether it admits trade-offs, its stance on opinion,
     the moves it never makes. "Clear and engaging" calibrates nothing. -->

[3–4 sentences.]

## Calibration passages
<!-- 1–3 passages, 100–300 words, in the target voice; one strong beats three
     weak. The line under each heading declares the source — human (written by
     the human) | model (drafted at setup) | reference (a published author,
     for contrast, not imitation) — and check_story.py counts `human`.
     book-literary: at least literary.human_calibration_passages are `human`,
     and every `model` passage is screened for counted tics. Iterate to
     "yes, THIS", not polite approval. -->

### Passage 1 — [source]
<!-- calibration-source: [human | model | reference] -->

> [100–300 words.]

### Passage 2 — [source, optional]
<!-- calibration-source: [human | model | reference] -->

> [passage]

## Register
<!-- Per-project choices only; never restate the profile's prohibitions. -->

- Person: [you | we | impersonal]
- Formality: [casual | neutral | formal]
- Humor: [none | restrained, where … | allowed]
- Authorial stance: [neutral | opinionated with rationale]
- Literary: POV [first | close third | omniscient | …], tense [past |
  present], prose register [sparse | lush | …], profanity and explicit-content
  limits.

## Do / Don't
<!-- Mechanical, detectable, project-specific ("name the version whenever you
     name a tool"). Identity traits go in voice-profile.md; universal rules are
     already in the anti-mediocrity file. -->

- Do: […]
- Don't: […]

## Formatting

- Heading case: [sentence | title] · Oxford comma: [yes | no]
- Narration dash: [none | em-dash, no spaces | em-dash, spaced | en-dash,
  spaced] — dialogue marks are set below and never count as dashes.
- Numbers: [e.g. words < 10] · Dates: [format]
- Language variant: [en-US | es-AR | …]
- Literary: scene-break glyph [`* * *` | blank line]; quotation marks
  [« » | “ ” | …] for quotes inside narration.

## Dialogue conventions  <!-- book-literary -->

- Dialogue mark: [raya — (U+2014) | “ ” | « »]. Spanish raya: a raya opens
  each line; an interjected tag is closed with another raya only when the line
  continues (—No —dijo—. Mañana.); never a hyphen or an en-dash; dialogue is
  never glued to a narration paragraph (`lint_fiction` `dialogue_format`).
- Attribution: [plain verbs of saying (lexicon `speech_verbs_plain`) | action
  beats | …]. "Said/asked only" is an English default; Spanish may use a wider
  set of verbs of saying — only lexicon `speech_verbs_ornate` hits are defects.
- Dialect and accent: [rendered through vocabulary | phonetic, where …].

## Craft sources  <!-- book-literary, optional -->

- [None | sources chosen for this subgenre — see
  `references/anti-mediocrity-literary.md` § 6]

## Tonal range  <!-- book-literary -->

- Light where: […] · never light: […] · emotional ceiling: […] · humor: […]

## Code conventions  <!-- profiles with code -->

- Language + version: [pinned; checked against `validation_surface`]
- Style: […] · Shell: […] · Comments: […]
- Output blocks: [how expected output is shown] · Imports: [full first time?]
- Prompt char: [$ user / # root — shown?]

## Diagram conventions  <!-- if the project uses diagrams -->

- Tool: [Mermaid | Graphviz | SVG | …] · labels, arrows, captions: […]

## Terminology

- Define terms on: [first use | glossary | both]. Never swap synonyms for a
  glossary term (`bible/glossary.md`).

## Anti-mediocrity additions

- [plain lexical or mechanical bans specific to this project; identity-level
  bans go in voice-profile.md]

---

Signed off by: [human] on [date].
