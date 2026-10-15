# Style Guide — [Project Name]

The Editor, Humanizer (full mode only), Technical Reviewer, and Critic read
this. Keep it short and concrete.
Calibration passages matter more than rules.

Save to `bible/style-guide.md`.

---

## Voice in one paragraph

[Write 3–4 sentences that describe the voice of the book. Not "clear and
 accessible" — that's every tech book's marketing copy. Something like:
 "Teacher-at-whiteboard voice. Commits to concrete examples before
 abstractions. Admits trade-offs instead of selling solutions. Uses 'you'
 throughout. Names specific tools, versions, and numbers. Doesn't apologize
 for opinions."]

## Calibration passages

Three short passages (100–200 words) that exemplify the voice. Use real
text from a technical book you're modeling on, or from a section of this
book that you know is right. Every agent calibrates against these.

### Passage 1 — [source]

> [quoted passage]

### Passage 2 — [source]

> [quoted passage]

### Passage 3 — [source]

> [quoted passage]

## Register

- Person: [you | we | impersonal]. Stay consistent throughout.
- Formality: [casual | neutral | formal].
- Humor: [allowed, restrained, not allowed].
- Authorial stance: [opinionated | descriptive | neutral].

## Do

- [e.g., "Name the version when you name a tool."]
- [e.g., "Give concrete numbers when you claim performance."]
- [e.g., "Admit when something is harder than the docs suggest."]
- [e.g., "Pair every new concept with a minimal runnable example."]

## Don't

- [e.g., "No marketing adjectives: powerful, robust, seamless, cutting-edge."]
- [e.g., "No 'let's dive in', 'in this section, we'll explore'."]
- [e.g., "No hedging stacks: 'you might possibly want to'."]
- [e.g., "No em-dashes where a comma works."]
- [e.g., "No Title Case Headings — sentence case only."]

## Formatting

- Heading case: [sentence | title]
- Oxford comma: [yes | no]
- Dash style: [em with no spaces | em with spaces | en]
- Numbers: [e.g., words < 10, digits >= 10, except in code]
- Dates: [YYYY-MM-DD | Month D, YYYY]
- Language variant: [en-US / en-GB / es-AR / ...]

## Code conventions

- Language: [Python 3.12]
- Style: [PEP 8 + black, or whatever applies]
- Shell: [bash / zsh / fish — pick one and stick]
- Comment style: [sparse, only where the code doesn't explain itself]
- Output blocks: [how you present expected output — labeled? as separate
  blocks? inline?]
- Imports: [shown full the first time; elided in later examples?]
- Prompt character: [$ for user, # for root — show it or not?]

## Diagram conventions

- [Tool used: Mermaid, Graphviz, ASCII, hand-drawn SVG...]
- [Style rules for any diagrams: labels, arrows, legends]

## Anti-mediocrity

Apply `references/anti-mediocrity-technical.md`. Additions specific to this
project:

- [project-specific banned words or patterns]

## Terminology

Glossary lives in `bible/glossary.md`. Never swap synonyms for glossary terms.
If the glossary says "container", every chapter says "container" — not
"execution unit" or "sandbox