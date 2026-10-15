# Glossary — [Project Name]

The canonical list of terms used in this book. Every glossary term is used
**consistently** by the Writer and Humanizer — no synonyms, no cycling for
"elegance". If you swap "container" for "execution unit" in one chapter, the
Humanizer will put it back.

Save to `bible/glossary.md`.

---

## How this file works

- One entry per load-bearing term.
- Terms are listed alphabetically for lookup, not by chapter order.
- The Writer adds a term when they first coin it; the Technical Reviewer
  (Axis B) flags terms the field uses differently.
- Definitions are one paragraph — enough to disambiguate from neighboring
  terms, not a full treatment. The full treatment is in the chapter.
- `first_use` is the chapter that first introduces the term, for
  cross-reference and for the Continuity Guardian's audit.

---

## Entry format

Use this structure for each term:

```markdown
### Term

**Plural**: [if not obvious]
**Abbreviation**: [if common, e.g., "API (Application Programming Interface)"]
**First use**: ch-[NN]
**Field-standard?**: yes | coined-here | deviates-from-field

[One-paragraph definition. Write it so a reader encountering this term for
the first time gets the right mental model. If the field uses this term
differently than the book does, say so here.]

**Related**: [other glossary terms this concept connects to]
**Do not confuse with**: [terms that often get conflated — flag them]
```

---

## Terms

### [Example term]

**First use**: ch-02
**Field-standard?**: yes

[Definition.]

**Related**: [term], [term]
**Do not confuse with**: [term]

---

## Rules the pipeline enforces

1. **No synonyms in prose.** If the glossary says "container", every chapter
   says "container". The Humanizer restores terminology when the Writer
   drifts.
2. **First-use gets an inline cue.** The chapter that first introduces a term
   gives a brief inline definition alongside the first use. Subsequent uses
   rely on the glossary.
3. **Field-deviating terms get a note.** If the book uses "stream" to mean
   something the field normally calls "channel", the chapter that introduces
   it must say so, and this glossary entry must flag
   `Field-standard?: deviates-from-field`. The Technical Reviewer checks
   this as part of Axis B.
4. **Terms are added, not redefined.** If the meaning of a term shifts mid-
   book, that's a bible change — escalate 