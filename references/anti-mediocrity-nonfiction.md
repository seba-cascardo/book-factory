# Anti-mediocrity — nonfiction

Required reading for the Writer, Humanizer, Critic and Continuity Guardian
(Mode A) on `book-technical`, `corporate-guide`, `product-docs` and
`scientific-paper`.

**Rules and BAD examples only.** Models imitate examples more faithfully than
they follow rules, so a GOOD passage printed here would become every project's
voice. What "good" sounds like lives in each project's
`bible/voice-profile.md`. Where a pattern needs a fix, you get the properties
the fixed version must have, never a passage to copy.

**Word lists are not in this file.** They live per language in
`scripts/lexicons/<lang>.yaml` (keys named below), extended by the project's
`bible/lexicon.yaml`; `count_rhet.py` counts them into `checks.json`. The
English BAD examples illustrate a pattern — find the pattern in the project's
language, not the English words.

**The principle.** AI text drifts to the most probable phrasing that fits the
widest set of cases; a good nonfiction writer is specific to this reader, this
tool, this version. When you catch a pattern below, rewrite the passage from a
different angle — don't patch words.

The layers, scanned in order: content, dramatic hazard, language, style,
communication, filler.

---

## Layer 1 — Content

- **Significance inflation** — ordinary facts framed as momentous.
  BAD: "This represents a pivotal moment in the evolution of distributed
  systems." Fix: the specific thing, what factually changed, when; no
  evaluative adjective. Nothing changed → delete the sentence.
- **Name-dropping for authority.** BAD: "Major publications including The New
  York Times have covered this topic." Fix: one named, dated source and its
  actual finding, cited per the profile's policy.
- **Superficial -ing analyses** (showcasing, reflecting, highlighting).
  BAD: "The design showcases modern engineering principles, reflecting a
  commitment to user experience." Fix: the verifiable design fact that would
  justify the tribute; none → it was decoration.
- **Promotional adjectives** (lexicon `ai_vocab` carries the language's set).
  BAD: "This powerful, innovative tool provides a seamless experience." Fix:
  each adjective replaced by the measurement or behaviour that would earn it.
- **Vague attribution.** BAD: "Experts believe microservices scale better."
  Fix: a named work and the claim as that work makes it.
- **Formulaic challenges.** BAD: "Despite its challenges, Kubernetes continues
  to thrive." Fix: the actual problem, quantified, as information the reader
  needs — not a concession before more praise.

## Layer 2 — Dramatic hazard

Manufactured danger survives every other filter: the prose is specific, the
vocabulary clean, and it still reads as a thriller about configuration files.
It numbs the reader, so real hazards stop registering. Counted, not felt.

- **Hazard lexicon** (lexicon `danger`; `rhet-3`, ≤ 2 per unit). BAD: "The
  cache expires silently, and your dashboard keeps serving stale numbers
  without complaint."
- **"Works until it doesn't" inversions.** BAD: "That works — until it
  doesn't." A structural tic, not an insight.
- **Betrayal narratives** — software as a treacherous actor. BAD: "The
  optimizer you trusted has been quietly rewriting your joins behind your
  back." Software behaves as configured.
- **Tease closings** (lexicon `tease_closings`; `rhet-4`, 0 when the closing
  policy is recap or none).

A fixed hazard passage names the failure mode, the triggering condition and the
observable symptom — three facts, no adverb carrying emotion; states a cost only
when it is real and known; and reserves hazard framing for hazards.

## Layer 3 — Language

- **AI vocabulary** (lexicon `ai_vocab`; `voice-3`). Replace or remove on
  sight; the pack is the list, `bible/lexicon.yaml` adds the book's own.
- **Copula avoidance** — a verbose linking verb where a plain "is" or "has"
  works ("serves as", "features" as a verb, and their equivalents). Collapse.
- **Negative parallelisms** (lexicon `not_x_but_y`; `rhet-2`, ≤ 1). BAD:
  "This isn't just a library; it's a framework." Fix: say what it is, in one
  clause, without staging a reveal. Plain factual contrasts ("returns a tuple,
  not a list") are not this pattern.
- **Forced triplets.** BAD: "fast, scalable, and reliable." Fix: as many claims
  as there are facts, each with a number or a mechanism.
- **Synonym cycling.** BAD: "Containers run processes. These lightweight
  execution environments… Such virtualized units…" Fix: the glossary term,
  every time.
- **False ranges.** BAD: "Uses range from embedded systems to machine
  learning." Fix: list the cases as cases.

## Layer 4 — Style

- **Em-dashes in narration**: ≤ 2 per page unless the style guide allows more
  (`voice-4`, counted as `em_dash_narration`). A dialogue raya is punctuation,
  never counted. Prefer commas, colons, or two sentences.
- **Formatting artificiality**: bold for defined terms and real warnings only
  (`rhet-5`, ≤ 8 per 1000 words); emoji rarely earned; sentence-case headings
  unless the style guide says otherwise; template scaffold headings only when
  earned (lexicon `template_headings`; `rhet-7`).
- **Inline-header lists** — bold term plus colon instead of paragraphs. BAD:
  "**Performance:** It's fast. **Scalability:** It scales." Fix: a real table
  with numbers, or prose that says why each property holds.
- **Hyphenation** only where the compound modifies a following noun.
- **Signposting.** BAD: "Let's dive into the details. In this section, we'll
  explore…" A heading already signposts; the first line under it delivers
  content, never a restatement of the heading.

## Layer 5 — Communication

- **Chatbot residue** ("I hope this helps", "Feel free to", "Great question")
  — the document is not a conversation (`voice-5`, critical).
- **Knowledge-cutoff disclaimers.** BAD: "While details may vary depending on
  recent updates…" Fix: a version ("as of v2.18") or nothing.
- **Sycophancy** — answer directly.
- **Register drift** — "we", "let's", "you might want to" scattered
  inconsistently. The register is fixed in `bible/style-guide.md` and the
  profile; hold it.

## Layer 6 — Filler and hedging

- **Compressible phrases** — multi-word stand-ins for one word ("in order to",
  "due to the fact that" and the language's equivalents); cut "it should be
  noted that" and write the note.
- **Stacked hedges** (lexicon `weasels`; `voice-6`). BAD: "This could
  potentially possibly lead to issues in some cases." Fix: one hedge at most,
  naming what is uncertain and under which condition.
- **Generic conclusions.** BAD: "In conclusion, we've seen that Kubernetes is
  a powerful tool." Fix: follow the closing policy in force; whatever it is,
  the closing carries concrete information and never a tease.

---

## The paragraph test

1. Delete the first sentence — does the paragraph still work? Then it was
   signposting.
2. Does every sentence advance understanding?
3. Is there a specific claim — a number, a version, a named thing?
4. Does it fit the audience in `bible/meta.yaml`?
5. Read aloud: a practitioner, or a marketing site?

## Two passes

The Humanizer runs Pass 1 (every layer, paragraph by paragraph) and Pass 2 (the
whole unit: does it read like someone who knows this subject, and like THIS
project's voice profile?). A passage that fails Pass 2 is rewritten from a
different angle.
