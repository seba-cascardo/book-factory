# Chapter Digest Protocol

When the book is long, feeding every prior chapter in full to every
downstream agent wastes context and — more importantly — degrades
quality. Around chapter 8 of a 20-chapter book, the Writer is juggling
~30k tokens of prior-chapter prose that don't help it write chapter 9;
they just crowd out what matters (the current outline entry, the
relevant bible sections, the immediate prior chapter's voice).

A **digest** is a short, structured summary of a chapter — produced
once, right after the chapter is approved — that downstream agents read
in place of the full chapter.

## What every digest contains

Produced by the skill (not by a dedicated agent) immediately after a
chapter is archived. Target: 300–500 words. Fields listed here are
mandatory — what's not on this list can be skipped.

1. **One-paragraph gist** (≤120 words). What this chapter taught, why it
   mattered in the book's arc, the mental model the reader walked away
   with.
2. **Concepts introduced**. Bullet list with `id` from the Knowledge
   Graph + one-line definition as used in this chapter. This is the
   authoritative record of when each concept entered the book.
3. **Concepts reinforced**. IDs of concepts from prior chapters that
   this chapter leaned on. Lets the Writer of a later chapter know what's
   been recently refreshed vs. what needs a quick reminder.
4. **Running examples state**. For each long-form example the book tracks
   (a tutorial codebase, a case study), the state at chapter end.
   Example: "Todo app: auth flow complete, DB migrations set up, no
   front-end yet."
5. **Open forward references**. Claims the chapter made with "we'll see
   in chapter N" or equivalent. Each forward reference is a debt the
   later chapter must pay. Tracks in the `continuity-tracker.md`; the
   digest surfaces what's outstanding.
6. **Terminology decisions**. Any case where this chapter picked a term
   over its synonyms, defined a term inline, or narrowed an existing
   term's meaning. Later chapters must stay consistent.
7. **Voice calibration sample** (1–2 short passages, ≤60 words each).
   A paragraph that exemplifies the chapter's rhythm and register. Later
   chapters' Humanizer (full mode) or Writer calibrates against these +
   the style-guide passages.

## What NOT to include

- Plot summary / section-by-section recap. The gist covers it.
- Code listings. Later chapters that need the code read the archived
  chapter or the examples library.
- Anti-mediocrity notes. They live in the original critique file.

## When a digest is read vs. when the full chapter is read

| Agent              | Reads digests                 | Reads full prior chapters      |
|--------------------|-------------------------------|--------------------------------|
| Writer             | All prior chapters' digests   | ONLY the most recent chapter (N-1) — for voice continuity |
| Technical Reviewer | All prior digests             | The most recent chapter only, when glossary audit needs proof |
| Editor             | None                          | None — scope is this chapter only |
| Humanizer          | The most recent digest only   | The most recent chapter (voice calibration) |
| Reader-POV         | None                          | None — simulates cold-read |
| Critic             | All prior digests             | The most recent chapter only (cross-chapter voice check) |
| Continuity Guardian| All digests                   | All chapters (on scheduled audits) |

The Writer's "prior chapter" read is the one high-leverage exception:
voice bleeds from chapter to chapter and a digest can't carry rhythm.
Everything else reads digests unless there's a specific reason.

## When the skill creates the digest

After the human approves a chapter and the Proofreader has run. The
pipeline order is:

```
... → Critic PASS → Human approves → Proofreader → Continuity Guardian
                                          ↓
                                   Digest produced
                                          ↓
                                     Archive drafts
```

The skill reads the approved `final/ch-NN.md`, the chapter's
`critique.md` (for the voice calibration sample selection), and the
updated `continuity-tracker.md`, then writes
`bible/digests/ch-NN.digest.md`.

## When a digest is re-generated

- The chapter is edited after approval (late revision).
- The Knowledge Graph's concept list changes in a way that affects this
  chapter's `concepts_introduced`.
- The human explicitly requests a re-draft of the digest.

Otherwise digests are write-once artifacts.

## When to disable digests

Set `pipeline.chapter_digest.enabled: false` in `bible/meta.yaml` when:

- The book is short (≤8 chapters). The overhead outweighs the benefit.
- The book is a reference where chapters are independent. There's no
  "what the reader already knows" to track.
- You're debugging a quality problem that might be rooted in context
  starvation. Turn digests off for one chapter, see if quality improves,
  turn them back on.

The default is on for any linear/tutorial technical book and for any
literary project past 6 chapters.

## Format

Digests live in `bible/digests/ch-NN.digest.md`. They use the template
in `templates/chapter-digest.md` — follow it exactly. The fields are
machine-addressable so later agents can grep for a specific concept's
definition or forward-reference status without reading everything.
