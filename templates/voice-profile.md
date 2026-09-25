# Voice Profile — [Project Name]

<!--
  TEMPLATE — copy to `bible/voice-profile.md` and fill it WITH the human during
  setup (`references/setup.md`, voice profile step). The human signs it before
  Phase 2.

  WHY IT EXISTS. Models imitate examples far more than they follow rules. The
  skill's files therefore carry rules and BAD examples only; this file is the
  ONE place where imitable GOOD prose lives, derived from THIS project's
  approved passages. Every prose agent (Writer, Humanizer, Critic, CG Mode A)
  reads it every turn.

  style-guide.md holds calibration passages and mechanical decisions (person,
  punctuation, dash style, dialogue format). This file holds what THIS author
  does that others don't: fingerprint, banned traits, openings, closing,
  rhetoric budget, GOOD examples.

  Delete every comment and placeholder before sign-off: a half-filled profile
  calibrates the pipeline to placeholders.
-->

Profile: [book-technical | book-literary | corporate-guide | product-docs | scientific-paper]

## 1. Fingerprint

<!--
  3-5 traits this document has that most competent documents of its register
  do NOT. Each must be (a) observable in one paragraph — a reader or a grep
  could point at it — and (b) false for most peers. "Clear and engaging" fails
  (b). Phrase each so the Critic can check presence and the Humanizer knows
  never to sand it off: a recurring structural habit, a bounded source of
  analogy, a sentence shape, where humor is or isn't allowed.
-->

- **[Trait 1]** — [the move + a marker an agent can check]
- **[Trait 2]** — […]
- **[Trait 3]** — […]

## 2. Banned traits

<!--
  3-5 prohibitions specific to THIS project, on top of the anti-mediocrity
  files and the profile's register rules (don't restate those). Ask the human
  what they cannot stand in books like this one. Each needs a detectable
  marker: "no weather as scene-opener", "never 'leverage' as a verb". A
  recurring word or phrase can also go into `bible/lexicon.yaml` so the
  scripts count it.
-->

- **[Banned 1]** — [marker]
- **[Banned 2]** — […]
- **[Banned 3]** — […]

## 3. Openings

<!--
  NONFICTION (book-technical, corporate-guide): pick 3-4 opening STRUCTURES —
  scene-problem · direct question (sparingly; rhet-1) · counterintuitive data ·
  field case · task-first. The same structure may not open two consecutive
  units (rhet-6); the Writer declares its choice, the Critic checks membership
  (profile-3) and non-repetition (rhet-6). corporate-guide: sober structures
  only (scope statement, internal case, a real colleague's question).

  product-docs: write "Fixed: task-first. rhet-6 = not_applicable."
  scientific-paper: write "Fixed by IMRaD. rhet-6 = not_applicable."

  book-literary: NO rotation. Chapters open where the story needs them to;
  write "No rotation (literary)." A menu of openings becomes a periodic
  formula. lint_fiction.py reports the same opening type three chapters
  running as an observation, nothing more.
-->

Allowed opening structures (the Writer declares which it used):

- [Structure 1]
- [Structure 2]
- [Structure 3]

rhet-6: **[enforced | not_applicable — reason]**

## 4. Closing policy

<!--
  Inherited from the profile, adjustable here with the human's sign-off.
  Defaults: book-technical recap or earned bridge · book-literary follow the
  outline beat · corporate-guide recap or none · product-docs related-links ·
  scientific-paper none. pedagogy-3 checks the policy recorded here, and
  count_rhet.py reads the line below for rhet-4 — keep its format:
  `Policy: **recap**`.
-->

Policy: **[recap | related-links | none | bridge-allowed]**
[One line: any project-specific adjustment and why.]

## 5. Rhetoric budget

<!--
  Quotas for the rhet family (references/rubric.md § rhet), counted by
  scripts/count_rhet.py. Defaults: rhet-1 rhetorical questions ≤ 2 ·
  rhet-2 "not X but Y" ≤ 1 · rhet-3 danger lexicon ≤ 2 · rhet-5 bold ≤ 8 per
  1000 words. rhet-4 is 0 when the closing policy is recap or none.

  book-literary runs rhet-2 only, plus the diagnostics of
  references/anti-mediocrity-literary.md § 2 (same fence, same keys):
  similes_per_1000 ≤ 4 · fragment_ratio ≤ 0.15 · one_line_paragraphs_per_1000
  ≤ 2 · emotion_channels ≥ 2 · narrator_theme 0 · explained_shown 0. The
  script counts rhet-N keys; the diagnostics are read by the Humanizer and the
  Critic. Tic quotas and the Humanizer budget live in meta.yaml → literary.

  Write ONLY the overrides the human chooses, inside the yaml fence below —
  count_rhet.py parses that fence, so the key must stay `rhetoric_budget:` and
  the values plain numbers. Left empty, every default holds.
  Profile-fixed values (paper: rhet-1 = 0) need not be repeated.
-->

```yaml
rhetoric_budget:
  # rhet-1: 1     # e.g. this project answers questions in prose, not by asking them
  # rhet-5: 12    # e.g. reference material is legitimately bold-heavy
  # similes_per_1000: 6   # literary, e.g. an image-dense narrator the human signed
```

## 6. Voice risks (book-literary only)

<!--
  VOICE-RISK is optional: 0-2 risks per chapter, each flagged by the Writer
  in a `VOICE-RISK:` HTML comment — never a quota. A flagged risk is
  exempt from the voice rows, not from continuity, character or facts. The
  literary digest logs each risk, so a run of risks that are all the same kind
  (the same odd simile every chapter) shows up. Record here what kind of risk
  this voice welcomes and which kind it refuses.
-->

- Welcome: [e.g. long unpunctuated interior runs at moments of panic]
- Refuse: [e.g. synesthetic similes]

## 7. Project GOOD examples

<!--
  The ONLY imitable prose in the system. Derive them preferably from passages
  the HUMAN wrote (the style guide marks each calibration passage with a
  `calibration-source: human | model | reference` HTML comment); model-drafted
  passages may complement them but never be the only source — a model's
  passage carries the model's tics into every chapter. A `reference` passage
  (a published author the human chose) is contrast, not a template to copy.

  3-5 passages, 80-150 words each, each TAGGED with what it demonstrates (a
  fingerprint trait, an opening structure, a move). Iterate with the human
  until they say "yes, THIS"; if they cannot tell a draft from a generic
  competent text of the register, discard it — a generic example teaches
  genericness. Keep them current after recalibrations.
-->

### Example 1 — source: [human | model | reference] — demonstrates: [technique]

> [80-150 words of approved, in-voice prose]

### Example 2 — source: […] — demonstrates: […]

> [passage]

### Example 3 — source: […] — demonstrates: […]

> [passage]

---

Signed off by: [human] on [date]. The Critic scores `consistency-1`
(nonfiction) / `voice-4` (literary) against §1–2 and `rhet-6` / `profile-3`
against §3; an unsigned or placeholder-filled profile poisons every prose gate.

- [date] — [what changed and why]
