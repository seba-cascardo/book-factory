# Anti-Mediocrity — Nonfiction

Required reading for the Writer, Humanizer, Critic, and Continuity Guardian
(Mode A) on every nonfiction profile (`book-technical`, `corporate-guide`,
`product-docs`, `scientific-paper`). The patterns are drawn from Wikipedia's
"Signs of AI writing" guide and field-tested against AI-generated nonfiction
prose.

## Why this file contains no GOOD prose examples

This file carries rules and BAD examples only — deliberately. Agents imitate
examples more faithfully than they follow rules, so any GOOD passage printed
in a shared reference gets absorbed as a voice template and reproduced in
every project that loads it — that is how unrelated documents end up sounding
identical. What "good" sounds like is defined per project: the calibration
target is `bible/voice-profile.md` — its fingerprint, its approved GOOD
examples, its budgets. Where a pattern below needs a "how to fix it", you get
the properties the fixed version must have, never a passage to copy. Do not
import prose from this file into a draft.

## The underlying principle

AI-generated text tends toward the most statistically likely phrasing that
applies to the widest variety of cases — the opposite of a good nonfiction
writer, who is SPECIFIC to this reader, this tool, this version, this
context. Kill generality on contact. If you catch yourself violating any
pattern below, stop and rewrite the passage from scratch with a different
approach — don't patch words.

## Organizing principle

Nonfiction AI prose fails in six layers. Scan each in order: (1) **Content**
— is the text saying something useful, or performing the shape of saying
something? (2) **Dramatic hazard** — are the stakes real and stated, or
manufactured? (3) **Language** — constructions AI prefers that humans rarely
use. (4) **Style** — formatting that betrays AI authorship. (5)
**Communication** — conversational artifacts that belong in chat. (6)
**Filler** — padding that adds words without adding meaning.

---

## Layer 1 — Content patterns

### 1.1 Significance inflation

AI frames ordinary facts as momentous. Cut the grandeur.

- **BAD**: "This represents a pivotal moment in the evolution of distributed
  systems."

Fixed version: names the specific thing and what factually changed, dates it,
zero evaluative adjectives. If nothing factual changed, delete the sentence.
Cut anything that praises the topic's importance without adding information.

### 1.2 Notability name-dropping

Don't list generic outlets to imply authority.

- **BAD**: "Major publications including The New York Times and The Wall
  Street Journal have covered this topic."

Fixed version: one named source, dated, the actual finding stated, formatted
per the profile's citation policy. Coverage is never the point; the finding is.

### 1.3 Superficial -ing analyses

"Showcasing", "symbolizing", "reflecting", "highlighting", "demonstrating"
without content are AI filler.

- **BAD**: "The design showcases modern engineering principles, reflecting a
  commitment to user experience."

Fixed version: replaces the abstract tribute with the concrete, verifiable
design fact that would have justified it. No such fact → it was decoration.

### 1.4 Promotional language

Cut breathless adjectives: "cutting-edge", "revolutionary", "seamless",
"robust", "powerful", "innovative", "state-of-the-art", "world-class",
"transformative".

- **BAD**: "This powerful, innovative tool provides a seamless experience."

Fixed version: each adjective replaced by the measurement or observable
behavior that would earn it. No measurement → the adjective was empty; cut it.

### 1.5 Vague attributions

"Experts believe", "research shows", "studies suggest" — anonymous
authorities are a tell. Cite or drop.

- **BAD**: "Experts believe microservices offer better scalability."

Fixed version: a named author or work (edition/year when it matters) and the
specific claim as that source actually makes it, cited per the profile's
citation policy (invisible HTML comments or visible academic citations).

### 1.6 Formulaic challenges

"Despite challenges...", "not without critics..." as a rhetorical gesture
rather than a real account of problems.

- **BAD**: "Despite its challenges, Kubernetes continues to thrive in
  enterprise environments."

Fixed version: names the actual problem, quantifies it where possible, and
treats it as information the reader needs — not a concession the writer
performs before returning to praise.

---

## Layer 2 — Dramatic hazard and stakes inflation

A named pattern with its own layer because it survives every other filter:
the prose is specific, the vocabulary is clean, and the text still reads as a
thriller about configuration files. AI nonfiction manufactures danger to
create momentum. Manufactured danger is a voice fingerprint — audited corpora
showed the same hazard lexicon dozens of times per book — and it numbs the
reader, so real hazards no longer register. These are counted, not felt: the
Critic greps for them under the rhetoric budget (`rhet-3`, `rhet-4` in
`references/rubric.md`; defaults overridable in `bible/voice-profile.md`).

### 2.1 Hidden-danger lexicon

"Silently", "invisibly", "without complaint", "quietly", "hidden danger",
"lurking", and equivalents — adverbs doing the emotional work that facts
should do. Budget: `rhet-3`, ≤ 2 per unit by default, significant.

- **BAD**: "The cache expires silently, and your dashboard keeps serving
  stale numbers without complaint."
- **BAD**: "This default is the invisible killer of query performance."

### 2.2 "Works until it doesn't" inversions

The setup-then-collapse template: "You X, but Y breaks." Audited books
carried 15–20 of these each — a structural tic, not an insight.

- **BAD**: "That works — until it doesn't."
- **BAD**: "You set it once, you forget about it, and six months later it
  takes production down."

### 2.3 Betrayal-narrative setups

Framing tools and systems as treacherous actors that will deceive the reader.
Software does not betray; it behaves as configured.

- **BAD**: "The optimizer you trusted has been quietly rewriting your joins
  behind your back."
- **BAD**: "Everything looks fine. That's exactly the problem."

### Properties of a fixed hazard passage

- Names the failure mode, the triggering condition, and the observable
  symptom — three facts, no adverbs carrying emotion.
- States the cost in the reader's terms (data lost, hours spent, money) only
  when that cost is real and known.
- Reserves hazard framing for hazards: if every section warns, no section
  warns. Genuinely dangerous facts scare the reader on their own — trust them.
- No artificial cliffhanger when the profile's closing policy is recap or
  none (`rhet-4`, 0 allowed, significant).

---

## Layer 3 — Language patterns

### 3.1 AI vocabulary audit

Replace or remove on sight: "actually" (as a conversational pivot),
"additionally", "moreover", "furthermore", "testament to", "landscape" ("the
modern development landscape"), "boasts", "realm", "paradigm" (unless in
Kuhn's sense), "leverage" (verb for "use"), "utilize" (use "use"),
"facilitate" (say what it actually does), "encompass", "holistic",
"synergy"/"synergies", "ecosystem" (OK for actual software ecosystems),
"journey" (for any non-travel process).

### 3.2 Copula avoidance

AI prefers verbose linking verbs. Collapse to simple ones: "serves as" →
"is" · "functions as" → "is" / "works as" · "represents" → "is" (when it
literally is) · "features" (verb) → "has" · "constitutes" → "is".

### 3.3 Negative parallelisms

The "It's not just X, it's Y" pattern is an AI fingerprint.

- **BAD**: "This isn't just a library; it's a framework. It's not simply a
  tool; it's a platform."

Budget: `rhet-2`, ≤ 1 per unit, significant — and only when the contrast is
load-bearing. Fixed version: states what the thing is directly, in one
clause, without staging a reveal.

### 3.4 Forced rule of three

AI reflexively produces triplets.

- **BAD**: "The system is fast, scalable, and reliable."

Fixed version: as many claims as there are facts, each backed by a number or
a mechanism. Writing three adjectives? Ask: are these the three things that
matter, or am I filling a pattern?

### 3.5 Synonym cycling

When a term is load-bearing, repeat it. Don't swap synonyms for variety.

- **BAD**: "Containers run processes. These lightweight execution
  environments isolate workloads. Such virtualized units..."

Fixed version: uses the glossary term every time. Synonym cycling confuses
readers who are learning the term; in nonfiction, consistency is clarity.

### 3.6 False ranges

"Spanning everything from X to Y" when X and Y aren't a spectrum.

- **BAD**: "Uses range from embedded systems to machine learning."

Fixed version: lists the actual cases as cases, without pretending they are
endpoints of a continuum.

---

## Layer 4 — Style patterns

### 4.1 Em-dash overuse

Prefer commas, colons, or separate sentences. Max 2 em-dashes per page unless
the style guide explicitly allows more.

### 4.2 Formatting artificiality

- Bold everywhere reads as a pitch deck. Bold is for terms being defined or
  genuine warnings. Budget: `rhet-5`, ≤ 8 bolds per 1000 words, minor.
- Emoji in nonfiction prose is rarely earned.
- Title Case headings read as marketing copy. Prefer sentence case:
  "Strategic negotiations" not "Strategic Negotiations".
- Template scaffold headings only when earned: a heading whose section is
  empty or formulaic fails `rhet-7` (minor).

### 4.3 Inline-header lists

Don't use bold terms followed by colons as a substitute for real paragraphs:

- **BAD**: "**Performance:** The system is fast. **Scalability:** It scales.
  **Reliability:** It's reliable."

Use either a real table with numbers, or prose that explains WHY each
property holds.

### 4.4 Unnecessary hyphenated compounds

Only hyphenate when the compound actually modifies a following noun:
"data-driven decisions" (yes), "we are data driven" (no hyphen).

### 4.5 Signposting

Remove meta-announcements about what the text is going to do.

- **BAD**: "Let's dive into the details. Here's what you need to know. In
  this section, we'll explore..."

Just write the thing. A heading is already signposting; a sentence repeating
the heading is a waste.

### 4.6 Fragmented headers repeating content

- **BAD**:
  ```
  ## Setting up the environment
  In this section, we set up the environment by...
  ```

Fixed version: the first line under a heading delivers content — a fact, a
command, a requirement — never a restatement of the heading.

---

## Layer 5 — Communication patterns

### 5.1 Chatbot artifacts

The document is not a conversation. Remove: "I hope this helps!", "Let me
know if you have any questions.", "Feel free to...", "If you'd like, I
can...", "Here's a summary of what we covered.", "Great question!"

### 5.2 Knowledge-cutoff disclaimers

- **BAD**: "While specific details may vary depending on recent updates..."

Either state a version ("as of v2.18") or drop the hedge entirely.

### 5.3 Sycophancy

- **BAD**: "That's an excellent question to consider at this stage."

Answer directly.

### 5.4 Helpful-assistant residue

"We'll", "let's", "you might want to" — fine when the register the style
guide chose uses them consistently; AI residue when scattered inconsistently.
The register (we / you / impersonal) is fixed in `bible/style-guide.md` and
the profile. Hold it.

---

## Layer 6 — Filler and hedging

### 6.1 Compress filler constructions

"in order to" → "to" · "due to the fact that" → "because" · "at this point
in time" → "now" · "in the event that" → "if" · "for the purpose of" → "for"
or drop · "with regard to" → "about" · "it should be noted that" → cut, then
write the note · "it is important to remember that" → cut.

### 6.2 Stacked hedges

- **BAD**: "This could potentially possibly lead to issues in some cases."

One hedge at most. Fixed version: names what is uncertain — which failure
mode, under which condition. Needing two hedges means you're unsure; say what
you're unsure about instead of piling qualifiers.

### 6.3 Generic conclusions

Endings that restate the unit are filler.

- **BAD**: "In conclusion, we've seen that Kubernetes is a powerful tool for
  orchestrating containers at scale."

Fixed version: follows the profile's closing policy (recap, related-links,
none, or bridge) as tuned in `bible/voice-profile.md`; whatever the policy,
the closing carries concrete information — what the reader now has, or what
specifically remains open — and never an artificial cliffhanger.

---

## The nonfiction paragraph test

After writing any paragraph:

1. **Can I delete the first sentence?** If the paragraph still conveys the
   information, it was signposting. Cut it.
2. **Does every sentence advance the reader's understanding?** If not,
   remove it.
3. **Is there a specific, non-generic claim?** A number, a version, a
   concrete example, a named thing? If not, add one.
4. **Does it match the audience** stated in `bible/meta.yaml`?
5. **Read aloud**: a person who knows this subject, or a marketing site?

---

## Two-pass rewrite rule

When the Humanizer works on nonfiction prose, it runs two passes:

1. **Pass 1**: address every pattern above, paragraph by paragraph.
2. **Pass 2**: re-read the whole unit asking two questions. Does this read
   like a human who knows this subject, or like an AI summarizing blog posts
   about it? And does it sound like THIS project's `bible/voice-profile.md`,
   or like a generically competent document? Any passage that fails either
   test gets rewritten from a different angle.

Two passes catch what one pass misses: Pass 1 is line-by-line, Pass 2 is
holistic.
