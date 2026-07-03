# Style Guide — [Project Name]

<!--
  TEMPLATE — style-guide.md. Copy to `bible/style-guide.md` and fill it during
  setup (see `references/setup.md` § Sub-Phase 6). The human signs off before
  writing begins. Read by every prose agent — Writer, Editor, Humanizer, Critic,
  Continuity Guardian (Mode A) — every turn, alongside `bible/voice-profile.md`.

  DIVISION OF LABOR — read this before filling either file. This style guide
  holds the CALIBRATION PASSAGES and the MECHANICAL DECISIONS: person,
  formality, formatting, code/dialogue conventions, terminology handling. The
  companion `bible/voice-profile.md` holds the DISTINCTIVE FINGERPRINT, the
  opening rotation, the rhetoric budget, and the derived GOOD examples. Rule of
  thumb: reversible, mechanical, "which convention?" → here. Identity, "what
  makes this document itself?" → voice profile.

  NO GOOD PROSE EXAMPLES LIVE HERE except the calibration passages below.
  Imitable in-voice GOOD examples belong in voice-profile.md § Project GOOD
  examples, which is derived FROM the calibration passages you approve here.
  That is why the passages are load-bearing twice: they set the voice now, and
  they seed the only imitable prose in the system later.

  Keep only the sections your profile uses (each is tagged with the profiles it
  applies to). Delete instructional comments and bracketed placeholders before
  sign-off. Keep it short and concrete — a long style guide goes unread.
-->

Profile: [book-technical | book-literary | corporate-guide | product-docs | scientific-paper]

---

## Voice in one paragraph

<!--
  3-4 sentences describing how a paragraph should FEEL. Not marketing copy —
  "clear and accessible" (nonfiction) and "literary and evocative" (literary)
  describe every document and calibrate nothing. Name concrete, checkable
  habits: what the prose commits to, what it refuses. WHY here and not the
  voice profile: this is the register envelope, the broad-strokes feel; the
  sharp distinctive traits go in voice-profile.md § Fingerprint. Together they
  brief a new agent in under a minute.

  BAD: "An authoritative yet approachable voice that engages the reader."
  Shape that passes: concrete commitments and refusals — e.g. what it does
  before abstracting, whether it admits trade-offs, its stance on opinion, the
  one or two moves it never makes.
-->

[3-4 sentences.]

## Calibration passages

<!--
  THE MOST IMPORTANT PART OF THIS FILE. 1-3 short passages (100-300 words each)
  in the target voice. They need not be from the actual document — they show how
  a paragraph should feel. Sources: real text from a work the human is modeling
  on, the human's own best writing, or drafts you write and refine together.

  Draft, get feedback, refine until the human says "yes, THIS" — NOT polite
  approval. A passage the human merely tolerates calibrates every downstream
  agent to a voice nobody wanted. WHY it matters twice: these passages seed the
  voice profile's GOOD examples (setup sub-phase 9), the only imitable prose in
  the system. A weak calibration passage produces a weak fingerprint produces a
  generic book.

  Attribute each passage to its source (published author + work, "author's own",
  or "drafted at setup"). 1 strong passage beats 3 weak ones — do not pad to 3.
-->

### Passage 1 — [source]

> [100-300 words in the target voice.]

### Passage 2 — [source, optional]

> [passage]

### Passage 3 — [source, optional]

> [passage]

## Register  <!-- all profiles -->

<!--
  The mechanical register decisions. Fine-grained voice identity is NOT here —
  it is in voice-profile.md. Here you fix the envelope. The profile arrives with
  register defaults and hard prohibitions already set (e.g. corporate-guide bans
  mic-drops, self-reference, cliffhangers, transformation promises); do NOT
  restate the profile's prohibitions here — record only per-project choices and
  any explicit deviation from a profile default. The Critic checks `voice-1`
  (person) and `voice-7` (register match) against these.
-->

- **Person**: [you | we | impersonal] — pick one and hold it every unit.
- **Formality**: [casual | neutral | formal] — within the profile's band.
- **Humor**: [not allowed | restrained, where: … | allowed] — err toward less.
- **Authorial stance**: [neutral reporting | opinionated with rationale].
- **Literary only**: POV [first | close third | omniscient | …], tense
  [past | present], prose register [sparse | lush | journalistic], profanity
  and explicit-content boundaries. Delete this line for nonfiction.

## Do / Don't  <!-- all profiles -->

<!--
  Concrete, checkable moves this project commits to and rules out. These are
  MECHANICAL style rules, not identity traits (traits → voice-profile.md § 1/2)
  and not universal anti-mediocrity rules (those are in the anti-mediocrity
  reference the prose agents already load — do not duplicate them). Keep each
  item detectable so an agent can self-check and the Critic can verify.

  BAD (identity, belongs in voice profile): "Sound like a trusted mentor."
  BAD (already global): "No 'let's dive in'." (anti-mediocrity covers it)
  Good shape (mechanical, project-specific): a concrete convention only this
  project needs — e.g. "name the version whenever you name a tool", "no
  em-dash where a comma works", "sentence-case headings only".
-->

**Do**

- [project-specific mechanical commitment]
- […]

**Don't**

- [project-specific mechanical prohibition]
- […]

## Formatting  <!-- all profiles -->

- Heading case: [sentence | title]
- Oxford comma: [yes | no]
- Dash style: [em, no spaces | em, spaced | en]
- Numbers: [e.g., words < 10, digits ≥ 10, except in code]
- Dates: [YYYY-MM-DD | Month D, YYYY]
- Language variant: [en-US | en-GB | es-AR | es-ES | …]
- **Literary**: scene break glyph [*** | line gap]; quote style
  [curly | straight, single | double]. **Nonfiction**: delete this line.

## Code conventions  <!-- profiles with code: book-technical, product-docs, some scientific-paper -->

<!-- Delete this whole section if the project has no code. -->

- Language + version: [e.g., Python 3.12 — pin it; the Reviewer checks against
  `meta.yaml → validation_surface`.]
- Style: [PEP 8 + black, or whatever applies]
- Shell: [bash | zsh | fish — pick one]
- Comments: [sparse, only where the code doesn't explain itself]
- Output blocks: [how expected output is shown — labeled? separate block?]
- Imports: [shown full first time; elided later?]
- Prompt char: [$ user / # root — shown or not?]

## Diagram conventions  <!-- profiles that use diagrams -->

<!-- Delete if no diagrams. -->

- Tool: [Mermaid | Graphviz | ASCII | SVG | …]
- Style rules: [labels, arrows, legends, caption format]

## Dialogue conventions  <!-- book-literary only -->

<!-- Delete this whole section for nonfiction profiles. -->

- Attribution: ["said" default | voicey tags allowed where …]
- Tag spacing / punctuation placement: […]
- Profanity policy: […]
- Dialect / accent: [phonetic | indicated through vocabulary only]

## Terminology  <!-- all profiles; load-bearing for KG profiles -->

<!--
  The glossary lives in `bible/glossary.md`. State the handling rule here. WHY:
  synonym cycling on load-bearing terms is a real Critic hit (`tech_b-2`,
  `consistency-2`) — it reads as sloppiness and, in KG profiles, breaks the
  concept graph. For book-technical / scientific-paper the KG enforces this
  tree-wide; for product-docs the KG enforces terminology across the whole tree,
  not adjacent units.
-->

- Define terms on: [first use | glossary | both].
- Never swap synonyms for a glossary term. If the glossary says "container",
  every unit says "container" — not "execution unit", not "sandbox".

## Anti-mediocrity additions  <!-- all profiles -->

<!--
  The global floor is `references/anti-mediocrity-nonfiction.md` or
  `-literary.md`, which the prose agents already load — do NOT copy it here.
  This section is for extra MECHANICAL banned words/patterns specific to this
  project that fit nowhere above. Distinctive identity-level banned traits go in
  voice-profile.md § Banned traits instead; put a pattern here only if it is a
  plain lexical/mechanical ban (a word, a punctuation habit, a construction).
-->

- [project-specific banned word or pattern, detectable]
- […]

## Tonal range  <!-- book-literary only -->

<!-- Delete this whole section for nonfiction profiles. -->

- Where the book can be light: [scenes / characters].
- Where it must not be: [scenes / characters].
- Emotional ceiling: [how much melodrama is acceptable].
- Humor style: [dry | absurd | character-driven | none].

---

<!--
  SIGN-OFF. The style guide is not valid until the human approves it — chiefly
  the calibration passages, which seed the voice profile. Record it so the
  handoff to sub-phase 9 (voice profile) is traceable.
-->

Signed off by: [human] on [date].
