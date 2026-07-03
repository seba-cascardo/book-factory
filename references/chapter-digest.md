# Digest Protocol

When a project runs long, feeding every prior unit in full to every
downstream agent wastes context and — more importantly — degrades quality.
Around unit 8 of a 20-unit book, the Writer is juggling ~30k tokens of
prior-unit prose that do not help it write unit 9; they just crowd out what
matters (the current outline entry, the relevant bible sections, the
immediate prior unit's voice).

A **digest** is a short, structured summary of a unit — produced once, right
after the unit is approved — that downstream agents read in place of the
full unit. The template is `templates/chapter-digest.md`; follow it exactly.

## Which profiles produce digests

Digests exist only for **sequential** profiles. The profile's `sequence`
field decides:

| Sequence | Profiles | Digest policy |
|---|---|---|
| linear | book-technical, book-literary | Full digest per unit |
| linear-light | corporate-guide | Full digest per unit — units open self-contained, but terminology and decisions still accumulate |
| modular | product-docs | **No digests** — see below |
| imrad | scientific-paper | Short claims-state snapshot per section — see below |

- **product-docs makes no digests.** Modular means no previous unit exists to
  digest; `bible/digests/` is not created. Cross-article memory is carried by
  the KG terminology layer and the Phase 4 audit, not by narrative summary.
  What a digest would carry (a description, tags, related links) lives in each
  article's **YAML frontmatter** instead — per-article, not accumulated.
- **scientific-paper digests are claims-state snapshots**, not prose
  summaries. Each approved section's digest records which `claims-map.yaml`
  entries the section used and each entry's status, so a later section knows
  what has been established with evidence and may be relied on. It carries the
  claims fields below and skips the pedagogical ones (running examples,
  forward references framed as teaching debts).

## What every digest contains

Produced by the orchestrator (not by a dedicated agent) immediately after a
unit is archived. Target: 300–500 words. The fields below are mandatory for
sequential book/guide profiles; scientific-paper carries only the
claims-relevant subset.

1. **One-paragraph gist** (≤120 words). What this unit delivered, why it
   mattered in the arc, the mental model or story state the reader walked away
   with. Not a section-by-section recap.
2. **Concepts introduced**. Bullet list with `id` from the Knowledge Graph +
   one-line definition as used in this unit. This is the authoritative record
   of when each concept entered the document.
3. **Concepts reinforced**. IDs of prior-unit concepts this unit leaned on.
   Lets a later Writer know what has been recently refreshed vs. what needs a
   quick reminder.
4. **Running examples state**. For each long-form example the project tracks
   (a tutorial codebase, a case study), its state at unit end. Example: "Todo
   app: auth flow complete, DB migrations set up, no front-end yet."
5. **Open forward references**. Claims the unit made with "we'll see in
   unit N" or equivalent. Each forward reference is a debt the later unit must
   pay. Tracked in `bible/continuity-tracker.md`; the digest surfaces what is
   outstanding.
6. **Terminology decisions**. Any case where this unit picked a term over its
   synonyms, defined a term inline, or narrowed an existing term's meaning.
   Later units must stay consistent.
7. **Voice calibration sample** (1–2 short passages, ≤60 words each). A
   passage that exemplifies the unit's rhythm and register. **This is a
   reference point, NOT a copy source.** The calibration authority is
   `bible/voice-profile.md` — its fingerprint, its GOOD examples, its budgets.
   The sample shows where this unit's voice landed so a later agent can notice
   drift; no agent lifts phrasing from it. If the sample and voice-profile.md
   ever disagree, voice-profile.md wins and the drift is the finding.

## What NOT to include

- Plot / section-by-section recap. The gist covers it.
- Code listings. Later units that need the code read the archived unit or
  `bible/examples-library.md`.
- Anti-mediocrity notes. They live in the unit's `critique.md`.

## When a digest is read vs. when the full unit is read

| Agent | Reads digests | Reads full prior units |
|---|---|---|
| Writer | All prior units' digests | Most recent unit only — for continuity of argument/story, not voice |
| Technical Reviewer | All prior digests | Most recent unit only, when a terminology audit needs proof |
| Editor | None | None — scope is this unit only |
| Humanizer | Most recent digest only | None — voice comes from `bible/voice-profile.md` |
| Reader-POV | None | None — simulates a cold read |
| Critic | All prior digests | None — `coherence.md` carries cross-unit findings |
| Continuity Guardian | All digests | All units, on scheduled audits only |

Note the deliberate change from a naive design: **no agent calibrates voice
against the most recent unit.** Reading the prior unit is for knowing where
the reader left off, never for imitating its prose — calibrating against
neighbors rewards homogeneity drift. Voice calibration is always against
`bible/voice-profile.md`.

## When the orchestrator creates the digest

After the human approves a unit, the Proofreader has run, and Continuity
Guardian Mode B has updated the tracker. Pipeline order:

```
... → Critic PASS → Human approves → Proofreader → CG Mode B
                                          ↓
                                    Digest produced
                                          ↓
                                     Archive drafts
```

The orchestrator reads the approved `final/unit-NN.md`, the unit's
`critique.md` (to pick a voice sample the scorecard marked clean on voice),
and the updated `bible/continuity-tracker.md`, then writes
`bible/digests/unit-NN.digest.md`.

## When a digest is re-generated

- The unit is edited after approval (late revision).
- The Knowledge Graph's concept list changes in a way that affects this
  unit's `concepts_introduced`.
- The human explicitly requests a re-draft of the digest.

Otherwise digests are write-once artifacts and freeze at approval. The Phase 4
polish pass does **not** regenerate them — they are writing-time calibration
artifacts and by Phase 4 the writing is done.

## When to disable digests

Set `pipeline.chapter_digest.enabled: false` in `bible/meta.yaml` when:

- The project is short (≤8 units). The overhead outweighs the benefit.
- The document is reference-style with independent units. There is no "what
  the reader already knows" to track.
- You are debugging a quality problem that might be rooted in context
  starvation. Turn digests off for one unit, see if quality improves, turn
  them back on.

Default on for any linear/linear-light project and for any literary project
past 6 units. Always off for `product-docs` (structurally, not by flag).

## Format

Digests live in `bible/digests/unit-NN.digest.md` and use
`templates/chapter-digest.md`. The fields are machine-addressable so a later
agent can grep for a concept's definition or a forward reference's status
without reading everything.
