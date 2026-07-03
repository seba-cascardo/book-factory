# Glossary — [Project Name]

The canonical list of load-bearing terms for this document. Every glossary
term is used **consistently** by the Writer and Humanizer — no synonyms, no
cycling for "elegance". If you swap "container" for "execution unit" in one
unit, the Humanizer puts it back. Naming drift across units erodes trust and
breaks search; a controlled vocabulary is cheaper to enforce here than to
untangle in a finished manuscript.

Save to `bible/glossary.md`.

Say "chapter", "article", or "section" to the human per the profile; the
files below use `unit-NN`.

---

## How this file works

- One entry per load-bearing term. If a reader could reasonably ask "what
  exactly do you mean by X here?", X earns an entry.
- Terms are listed alphabetically for lookup, not by unit order.
- The Writer adds a term when they first coin it; the Technical Reviewer
  (Axis B) flags terms the field uses differently.
- Definitions are one paragraph — enough to disambiguate from neighboring
  terms, not a full treatment. The full treatment lives in the unit that
  teaches the term.
- `first_use` is the unit that first introduces the term, for cross-reference
  and for the Continuity Guardian's Phase 4 coverage audit.
- In terminology-only knowledge-graph mode (`corporate-guide`, `product-docs`)
  the glossary and `bible/knowledge-graph.yaml` describe the same vocabulary:
  the graph is the glossary with stable IDs and `contrasts_with` edges. Keep
  the canonical `name` identical in both files.

---

## Entry format

Use this structure for each term. Fields in brackets are optional — include
them only when they earn their place.

```markdown
### Term

**Plural**: [if not obvious]
**Abbreviation**: [if common, e.g., "API (Application Programming Interface)"]
**First use**: unit-[NN]
**Field-standard?**: yes | coined-here | deviates-from-field

[One-paragraph definition. Write it so a reader meeting this term for the
first time gets the right mental model. If the field uses this term
differently than the document does, say so here — that difference is the
whole reason the entry exists.]

**Related**: [other glossary terms this concept connects to]
**Do not confuse with**: [terms that often get conflated — name them so the
unit that introduces this term can disambiguate]
```

---

## Terms

### [Example term]

**First use**: unit-02
**Field-standard?**: yes

[Definition.]

**Related**: [term], [term]
**Do not confuse with**: [term]

---

## Rules the pipeline enforces

1. **No synonyms in prose.** If the glossary says "container", every unit
   says "container". The Humanizer restores terminology when the Writer
   drifts; the Technical Reviewer (Axis B) flags drift it missed.
2. **First use gets an inline cue.** The unit that first introduces a term
   gives a brief inline definition alongside the first use — in terminology
   mode, reuse the `one_liner` wording from `knowledge-graph.yaml` so the
   phrasing is identical everywhere. Later uses rely on the glossary.
3. **Field-deviating terms get a note.** If the document uses "stream" to
   mean what the field normally calls "channel", the introducing unit must
   say so, and this entry must carry `Field-standard?: deviates-from-field`.
   The Technical Reviewer checks this under Axis B.
4. **Terms are added, not redefined.** If a term's meaning shifts mid-
   document, that is a bible change — stop and escalate to the human rather
   than letting two definitions coexist.
5. **Modular profiles link, they do not assume.** In `product-docs`, a unit
   that needs a term either defines it inline in one line or links to the
   unit that owns it; it never assumes the reader met it earlier, because in
   a modular document there is no "earlier".
