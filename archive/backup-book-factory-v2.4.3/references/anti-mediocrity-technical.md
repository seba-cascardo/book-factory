# Anti-Mediocrity — Technical Mode

Required reading for any agent working on a technical chapter. The patterns here
are tuned for non-fiction (manuals, tutorials, guides, reference books). They are
drawn from Wikipedia's "Signs of AI writing" guide and field-tested against AI-
generated technical prose.

The underlying principle: AI-generated text tends toward the most statistically
likely phrasing that applies to the widest variety of cases. That is exactly the
opposite of what a good technical writer does. A good technical writer is SPECIFIC
to this reader, this tool, this version, this context. Kill generality on contact.

If an agent catches itself violating any of these, it should stop and rewrite the
offending passage from scratch with a different approach.

---

## Organizing principle

Technical AI prose fails in five layers. An agent doing anti-mediocrity work should
scan each layer in order:

1. **Content**: is the text actually SAYING something useful, or performing the shape
   of saying something?
2. **Language**: specific words and constructions AI prefers that human writers
   rarely use naturally.
3. **Style**: formatting patterns that betray AI authorship.
4. **Communication**: conversational artifacts that belong in chat, not in a book.
5. **Filler**: padding that adds words without adding meaning.

---

## Layer 1 — Content patterns

### 1.1 Significance inflation

AI loves to frame ordinary facts as momentous. Cut the grandeur.

- **BAD**: "This represents a pivotal moment in the evolution of distributed
  systems."
- **GOOD**: "Raft (2014) replaced Paxos as the default consensus protocol in most
  new systems."

Cut any sentence that praises the importance of the topic without adding information.

### 1.2 Notability name-dropping

Don't list generic outlets to imply authority. Cite specifically.

- **BAD**: "Major publications including The New York Times and The Wall Street
  Journal have covered this topic."
- **GOOD**: "A 2023 NYT investigation found [specific finding]."

### 1.3 Superficial -ing analyses

"Showcasing", "symbolizing", "reflecting", "highlighting", "demonstrating",
"showcasing" without content are AI filler.

- **BAD**: "The design showcases modern engineering principles, reflecting a
  commitment to user experience."
- **GOOD**: "The design is one-handed: every primary action sits within a
  4cm radius of a right-handed thumb grip."

### 1.4 Promotional language

Cut breathless adjectives. "Cutting-edge", "revolutionary", "seamless", "robust",
"powerful", "innovative", "state-of-the-art", "world-class", "transformative".

- **BAD**: "This powerful, innovative tool provides a seamless experience."
- **GOOD**: "The tool parses 30k lines/sec on a laptop and takes 12 minutes to set up."

### 1.5 Vague attributions

"Experts believe", "research shows", "studies suggest" — anonymous authorities
are a tell. Cite or drop.

- **BAD**: "Experts believe microservices offer better scalability."
- **GOOD**: "Newman's _Building Microservices_ (2nd ed., 2021) argues that
  scale is a consequence of independence, not the point of it."

### 1.6 Formulaic challenges

"Despite challenges...", "while it comes with difficulties...", "not without
critics..." as a rhetorical pattern rather than a real account of problems.

- **BAD**: "Despite its challenges, Kubernetes continues to thrive in enterprise
  environments."
- **GOOD**: "Kubernetes' cost is operational: a cluster needs a platform team
  the size of roughly one engineer per ten services."

---

## Layer 2 — Language patterns

### 2.1 AI vocabulary audit

Words that signal AI authorship in technical writing. Replace or remove on sight.

- "actually" (as a conversational pivot)
- "additionally"
- "moreover"
- "furthermore"
- "testament to"
- "landscape" ("the AI landscape", "the modern development landscape")
- "boasts" (as in "the library boasts a rich API")
- "realm"
- "paradigm" (unless you mean it in Kuhn's sense)
- "leverage" (as a verb when you mean "use")
- "utilize" (use "use")
- "facilitate" (replace with what it's actually doing)
- "encompass"
- "holistic"
- "synergy" / "synergies"
- "ecosystem" (overused; OK for actual software ecosystems)
- "journey" (for any non-travel process)

### 2.2 Copula avoidance

AI prefers verbose linking verbs. Collapse to simple ones.

- "serves as" → "is"
- "functions as" → "is" or "works as"
- "represents" → "is" (when it literally is)
- "features" (as a verb) → "has"
- "constitutes" → "is"

- **BAD**: "The README serves as the entry point and features a quick-start guide."
- **GOOD**: "The README is the entry point and has a quick-start guide."

### 2.3 Negative parallelisms

The "It's not just X, it's Y" pattern is an AI fingerprint.

- **BAD**: "This isn't just a library; it's a framework. It's not simply a tool;
  it's a platform."
- **GOOD**: "It's a framework — library + conventions + project layout."

Allowed at most once per chapter, and only when the contrast is load-bearing.

### 2.4 Forced rule of three

AI reflexively produces triplets. Use natural counts.

- **BAD**: "The system is fast, scalable, and reliable."
- **GOOD**: "The system handles 50k req/s per node and recovers from a leader
  failure in under 2 seconds."

If you find yourself writing three adjectives, ask: are these the three things
that matter, or am I filling a pattern?

### 2.5 Synonym cycling

When a term is load-bearing, repeat it. Don't swap synonyms for variety.

- **BAD**: "Containers run processes. These lightweight execution environments
  isolate workloads. Such virtualized units..."
- **GOOD**: "Containers run processes. Containers isolate those processes from
  each other and from the host."

Synonym cycling confuses readers who are learning a term. In technical writing,
consistency is clarity.

### 2.6 False ranges

"Spanning everything from X to Y" when X and Y aren't a spectrum.

- **BAD**: "Uses range from embedded systems to machine learning."
- **GOOD**: "It's used in embedded systems and in ML pipelines; those are its
  two main communities."

---

## Layer 3 — Style patterns

### 3.1 Em-dash overuse

AI loves em-dashes as a rhythm tool. Prefer commas, colons, or separate sentences.
Max 2 em-dashes per page unless the style guide explicitly allows more.

### 3.2 Formatting artificiality

- Bold everywhere reads as a pitch deck. Use bold for terms being defined or for
  genuine warnings, not to decorate.
- Emoji in technical prose is rarely earned. Code comments ≠ chapter prose.
- Title Case headings read as marketing copy. Prefer sentence case:
  "Strategic negotiations" not "Strategic Negotiations".

### 3.3 Inline-header lists

Don't use bold terms followed by colons as a substitute for real paragraphs:

- **BAD**: "**Performance:** The system is fast. **Scalability:** It scales.
  **Reliability:** It's reliable."
- **GOOD**: Either a real table with numbers, or prose that explains WHY each
  property holds.

### 3.4 Unnecessary hyphenated compounds

AI hyphenates common phrases that aren't compound modifiers:

- "data-driven" as a standalone noun → "data driven"
- "real-time" when you mean "realtime" or just "fast"

Only hyphenate when the compound actually modifies a following noun:
"data-driven decisions" (yes), "we are data driven" (no hyphen).

### 3.5 Signposting

Remove meta-announcements about what the text is going to do.

- **BAD**: "Let's dive into the details. Here's what you need to know. In this
  section, we'll explore..."
- **GOOD**: Just write the thing.

A heading is already signposting. Another sentence that repeats the heading is
a waste.

### 3.6 Fragmented headers repeating content

- **BAD**:
  ```
  ## Setting up the environment
  In this section, we set up the environment by...
  ```
- **GOOD**:
  ```
  ## Setting up the environment
  Install Node 20 or newer. On macOS: `brew install node@20`.
  ```

---

## Layer 4 — Communication patterns

### 4.1 Chatbot artifacts

The book is not a conversation. Remove:

- "I hope this helps!"
- "Let me know if you have any questions."
- "Feel free to..."
- "If you'd like, I can..."
- "Here's a summary of what we covered."
- "Great question!"

### 4.2 Knowledge-cutoff disclaimers

- **BAD**: "While specific details may vary depending on recent updates..."
- **GOOD**: Either state a version ("as of v2.18") or drop the hedge entirely.

### 4.3 Sycophancy

- **BAD**: "That's an excellent question to consider at this stage."
- **GOOD**: Direct answer.

### 4.4 Helpful-assistant residue

Watch for "we'll", "let's", "you might want to" — these are fine in tutorials
when consistent with the style guide, but they become AI residue when scattered
inconsistently. Pick a register (we / you / impersonal) in the style guide and
hold it.

---

## Layer 5 — Filler and hedging

### 5.1 Compress filler constructions

- "in order to" → "to"
- "due to the fact that" → "because"
- "at this point in time" → "now"
- "in the event that" → "if"
- "for the purpose of" → "for" or drop
- "with regard to" → "about"
- "it should be noted that" → cut, then write the note
- "it is important to remember that" → cut

### 5.2 Stacked hedges

- **BAD**: "This could potentially possibly lead to issues in some cases."
- **GOOD**: "This may cause [specific failure mode] when [specific condition]."

One hedge at most. If you need two, you're unsure — then say what you're unsure
about, don't pile hedges.

### 5.3 Generic conclusions

Chapter endings that restate the chapter are filler.

- **BAD**: "In conclusion, we've seen that Kubernetes is a powerful tool for
  orchestrating containers at scale."
- **GOOD**: Either a concrete summary ("You've built a cluster, deployed two
  services, and exposed one via ingress.") or a bridge to the next chapter
  ("The cluster is running but nothing is persisted. Chapter 8 adds state.").

---

## The technical paragraph test

After writing any paragraph, run through:

1. **Can I delete the first sentence?** If the paragraph still conveys the
   information, the first sentence was signposting. Cut it.
2. **Does every sentence advance the reader's understanding?** If a sentence
   could be removed without reducing information, remove it.
3. **Is there a specific, non-generic claim in this paragraph?** A number, a
   version, a concrete example, a named thing? If not, add one.
4. **Does this paragraph match the audience level?** Not too junior, not too
   expert for the stated audience in `meta.yaml`.
5. **Read aloud**: does it sound like a human teaching, or like a product
   marketing site?

---

## Two-pass rewrite rule

When the Humanizer works on technical prose, it runs two passes:

1. **Pass 1**: address every pattern above, paragraph by paragraph.
2. **Pass 2**: re-read the whole chapter asking "does this read like it was
   written by a human who knows this subject, or like an AI summarizing blog
   posts about this subject?" Any paragraph that fails that sniff test gets
   rewritten from a different angle.

Two passes catch what one pass misses, because Pass 1 is line-by-line and Pass 2
is holistic.
