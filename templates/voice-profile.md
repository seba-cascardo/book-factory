# Voice Profile — [Project Name]

<!--
  TEMPLATE — voice-profile.md. Copy to `bible/voice-profile.md` and fill it
  collaboratively during setup (see `references/setup.md` § Sub-Phase 9). The
  human signs off before Phase 2; nothing here is generated unattended.

  WHY THIS FILE EXISTS. Language models imitate examples far more faithfully
  than they follow abstract rules. If the skill shipped "here is how good prose
  sounds" passages, every project built with the skill would converge on that
  one voice — the factory voice. So the skill's reference files carry rules and
  BAD examples only, and the imitable target prose is generated HERE, per
  project, from this project's own approved calibration passages. This is the
  ONLY file in the whole system where imitable GOOD prose is allowed to live.
  Every prose agent (Writer, Humanizer, Critic, Continuity Guardian in Mode A)
  reads this file every turn, alongside `bible/style-guide.md`. Keeping it
  accurate is what stops this project from sounding like every other project.

  RELATIONSHIP TO style-guide.md. The style guide holds calibration passages
  plus mechanical decisions (person, formality, formatting, code/dialogue
  conventions). This file holds the distinctive fingerprint, the opening
  rotation, the rhetoric budget, and the derived GOOD examples. If you are
  deciding "Oxford comma? em-dash spacing?", that goes in the style guide. If
  you are deciding "what does THIS author do that no one else does?", it goes
  here.

  Delete every instructional comment and bracketed placeholder before sign-off.
  A template artifact left half-filled calibrates the pipeline to placeholders.
-->

Profile: [book-technical | book-literary | corporate-guide | product-docs | scientific-paper]

---

## 1. Fingerprint

<!--
  3-5 traits THIS author/document has that most competent documents of the same
  register do NOT. WHY: sameness is the enemy; a fingerprint is what a reader
  recognizes the document by, and what every prose agent must actively
  reproduce rather than sand off toward the register mean.

  THE TEST for a good trait — it must be BOTH:
    (a) observable in a single paragraph (a reader or a grep could point at it), and
    (b) FALSE for most competent documents of the same register.
  "Clear and engaging", "authoritative", "accessible" fail (b) — they describe
  every competent document. Rewrite until each trait is specific and falsifiable.

  BAD (too generic — could describe any book): "Warm, approachable tone."
  BAD (unfalsifiable): "Deep respect for the reader's intelligence."
  Shape that passes (fill with THIS project's real traits): a concrete,
  checkable move — a recurring structural habit, a bounded source of analogy, a
  characteristic sentence shape, a specific place humor is or isn't allowed.
  Each trait should be phrased so the Critic can check for its presence and the
  Humanizer knows never to remove it.
-->

- **[Trait 1]** — [one line: what the move is + a marker an agent can check for.]
- **[Trait 2]** — […]
- **[Trait 3]** — […]
- [Trait 4-5, optional]

## 2. Banned traits

<!--
  3-5 prohibitions SPECIFIC to this project, ON TOP of the global anti-mediocrity
  floor (`anti-mediocrity-nonfiction.md` / `anti-mediocrity-literary.md`) and on
  top of the profile's Register prohibitions. Do NOT restate the global or
  profile rules here — this section is for the extra things THIS human hates in
  THIS genre. WHY separate: the global floor is universal; these are the tics
  that would make this specific book feel wrong even though no universal rule
  names them.

  Elicit by asking the human what they cannot stand in books/docs like this one.
  Make each one checkable. The Humanizer and Critic enforce these like any style
  rule (nonfiction `consistency-1`; literary `voice-4`); a banned trait an agent
  cannot detect is not enforceable, so phrase it with a marker.

  BAD (vague): "Nothing pretentious."
  Shape that passes: a named, detectable pattern, e.g. a specific overused
  word, a construction, a metaphor family, a punctuation habit — "no weather as
  scene-opener", "never the word 'leverage' as a verb", "no rule-of-three lists".
-->

- **[Banned 1]** — [detectable marker.]
- **[Banned 2]** — […]
- **[Banned 3]** — […]
- [Banned 4-5, optional]

## 3. Opening rotation

<!--
  WHY ROTATION EXISTS: a single opening formula, repeated across every unit, is
  the loudest sameness signal a reader gets. Rotation forces variety at the one
  position readers notice most.

  Pick 3-4 opening STRUCTURES from this menu, compatible with the profile:
    - scene-problem        (open inside a concrete situation that needs solving)
    - direct question       (open with the question the unit answers — spend sparingly; see rhet-1)
    - counterintuitive data  (open with a number or fact that unsettles an assumption)
    - field case            (open with a real case from the domain/organization)
    - task-first            (open by stating what the unit does: "This X shows how to Y")
    - in-media-res          (open mid-action; literary)
  Literary projects may substitute genre-appropriate structures (dialogue,
  interiority, sensory scene-setting) — record whatever set was agreed.

  HARD RULE (rhet-6, significant): the same structure may not open two
  CONSECUTIVE units. The Writer declares which structure it used in its
  self-assessment; the Critic verifies the declaration against the actual
  opening (profile-3: membership in this list) and against the previous unit's
  declared structure (rhet-6: non-repetition).

  PROFILE OVERRIDES — read carefully, some profiles turn this section OFF:
    - product-docs: opening is FIXED task-first, NO rotation. Uniform openings
      are correct in docs (a searcher confirms relevance in one line). rhet-6 is
      not_applicable — there is also no "previous unit" in a modular tree to
      compare against. If this project is product-docs, replace the list below
      with the single line "Fixed: task-first. rhet-6 = not_applicable." and
      leave it at that.
    - scientific-paper: each section's opening is FIXED by IMRaD convention
      (Methods states what was done, Results what was found). No rotation;
      rhet-6 dropped. If this project is a paper, record "Fixed by IMRaD;
      rhet-6 = not_applicable."
    - corporate-guide: rotation applies, but the chosen structures must all be
      sober (scope statement, internal case, a real colleague question) — no
      tension hooks.
  Any modular profile has no "previous unit", so rhet-6 cannot fire even where a
  rotation is listed; treat the list there as a membership menu (profile-3) only.
-->

Allowed opening structures for this project (one per bullet; Writer declares
which it used each unit):

- [Structure 1 from the menu]
- [Structure 2]
- [Structure 3]
- [Structure 4, optional]

rhet-6 (no consecutive repeat): **[enforced | not_applicable — reason]**

## 4. Closing policy

<!--
  Inherited from the profile; adjustable here with the human's sign-off. WHY it
  lives with the voice: the ending is the last thing the reader carries, and a
  single mandated closing shape ("end with a recap", "end with momentum") makes
  every unit of every project end identically. The Critic checks pedagogy-3
  (nonfiction) against WHATEVER policy is recorded here, not a universal formula.

  Values: recap | related-links | none | bridge-allowed.
  Profile defaults you are inheriting (state the one that applies, then any
  adjustment):
    - book-technical: concrete recap or earned bridge (adjustable to none).
    - book-literary: follow the outline beat, nothing else — no momentum rule.
    - corporate-guide: recap or none, fixed at setup.
    - product-docs: related-links only.
    - scientific-paper: none.

  rhet-4 (artificial cliffhanger, significant) is enforced against this policy:
  when the policy is recap or none, any forward tease in the final paragraphs
  fails. Record the policy so rhet-4 has something to check against.
-->

Policy: **[recap | related-links | none | bridge-allowed]**
[One line: any project-specific adjustment to the profile default, and why.]

## 5. Rhetoric budget

<!--
  The `rhet` family from `references/rubric.md`, restated with its DEFAULTS so
  the human can see what they are tuning. The Critic COUNTS these mechanically
  and records the number in scorecard evidence (a rhet entry with no count is
  invalid) — they are quotas, not vibes. WHY quotas and not bans: every dramatic
  device looks justified in isolation; the aggregate is the tell, and
  per-instance intent adjudication always approves.

  Record ONLY the overrides the human chooses; any item left at its default
  keeps the default automatically — do not copy defaults you are not changing.
  Overrides may tighten OR loosen. Some profiles fix some of these (paper sets
  rhet-1 = 0 and drops rhet-6; product-docs drops rhet-6). Note those as fixed,
  not adjustable.

  Defaults (per unit unless noted; all counts run over prose only — strip code
  fences, tables, and quoted dialogue first):
    rhet-1  rhetorical questions        ≤ 2     significant
    rhet-2  "not X but Y" reframes       ≤ 1     significant
    rhet-3  dramatic-danger lexicon      ≤ 2     significant
            (silently / invisible / quietly / without warning / hidden danger /
             lurk / ticking … + target-language equivalents)
    rhet-4  artificial cliffhanger       0 when closing policy is recap/none   significant
    rhet-5  bold density                 ≤ 8 per 1000 words   minor
    rhet-6  opening ≠ previous unit's    —       significant   (see §3 overrides)
    rhet-7  template headings only when earned   —   minor
-->

Overrides (leave blank to inherit all defaults):

- [e.g., rhet-1 tightened to ≤ 1 — this project answers questions in prose, not by asking them.]
- [e.g., rhet-5 loosened to ≤ 12 per 1000 — reference material is legitimately bold-heavy.]

Fixed by profile (not adjustable): [e.g., "rhet-6 = not_applicable" for product-docs / paper; "rhet-1 = 0" for paper. Delete if none.]

## 6. Project GOOD examples

<!--
  THE HEART OF THIS FILE, and the ONLY place in the whole system where imitable
  target prose is permitted. WHY HERE AND NOWHERE ELSE: shared GOOD examples in
  the skill's references would teach every project the same voice; these
  examples are derived from THIS project's approved calibration passages, so
  they teach THIS project's voice. Every prose agent calibrates against these,
  NOT against any passage in the skill's reference files. Importing prose from a
  reference file, or reusing a passage from another project, recreates exactly
  the shared-voice problem this artifact exists to prevent — never do either.

  HOW THEY ARE PRODUCED (setup, sub-phase 9): start from the approved
  calibration passages in `bible/style-guide.md`, then draft 1-2 additional
  short passages per KEY TECHNIQUE — a "technique" is a fingerprint trait (§1)
  or a recurring move agents must reproduce: an opening in one of the rotation
  structures (§3), a callout in the project's humor, a definition paragraph, a
  scene beat in the book's POV. Draft, present, iterate until the human says
  "yes, THIS" — the same bar as the calibration passages, not polite tolerance.
  If the human cannot tell a draft from a generic competent document of the
  register, DISCARD IT and retry: a generic example teaches agents to be
  generic, which is worse than no example.

  3-5 passages total, roughly 80-150 words each. TAG each with what it
  demonstrates (which fingerprint trait / which opening structure / which move),
  so an agent reaching for a specific technique knows which example to study.
  Keep them current: if the human recalibrates the voice (e.g., after a
  singularity audit), update these passages — stale examples silently steer the
  whole pipeline.
-->

<!-- Example format — repeat 3-5 times. The blockquote is the ONLY imitable
     prose in the system; everything else in the skill describes, never models. -->

### Example 1 — demonstrates: [fingerprint trait / opening structure / move]

> [80-150 words of approved, in-voice prose for THIS project.]

### Example 2 — demonstrates: [technique]

> [passage]

### Example 3 — demonstrates: [technique]

> [passage]

<!-- Examples 4-5 optional; add one per additional key technique that agents
     must reproduce and that examples 1-3 do not already cover. -->

---

<!--
  SIGN-OFF. This artifact is generated collaboratively at setup and is not valid
  until the human signs it off. Downstream agents treat it as authoritative:
  the Critic scores `consistency-1` (nonfiction) / `voice-4` (literary) against
  the fingerprint and banned traits here, and rhet-6 / profile-3 against the
  opening rotation here. An unsigned or placeholder-filled voice profile poisons
  every prose gate for the life of the project.
-->

Signed off by: [human] on [date]. Revisions logged below.

- [date] — [what changed and why, e.g., "tightened rhet-1 after unit 4 read
  question-heavy"; "added fingerprint trait 4 after singularity audit at unit 5".]
