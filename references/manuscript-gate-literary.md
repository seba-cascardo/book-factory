# Manuscript gate — literary branch

For `book-literary`. Trigger, rounds, the findings store, subjects, waivers,
the verdict and convergence are in `references/manuscript-gate.md`; this file
says which checks run for a novel, what each asks, and when the book is done.

## Checks

| id | Question | Engine | Severity |
|---|---|---|---|
| MG-1, MG-2, MG-3, MG-6 | — | `n/a (profile)`: no concepts, rules, exercises or code; no waiver, no probes | — |
| MG-4 | Read cold, end to end: does it hold, and does it keep what it promises? | Reader-POV, whole-book literary | § MG-4 |
| MG-5 | Does it render as meant? | `lint_render.py` | as in `manuscript-gate.md` |
| MG-7 | Did a fixed defect come back? | `check_fixed_defects.py` | as in `manuscript-gate.md` |
| MG-S | Does the story close as designed? | `python scripts/check_story.py --manuscript --json OUT` | blocking → critical; major → major |
| MG-T | Tics, names and form across the book | `python scripts/lint_fiction.py --book --json OUT` | major → major; minor → minor; info ignored |
| MG-C | Continuity and development across the book | Continuity Guardian § MG-C, lenses `continuity` and `developmental` | § MG-C |

**MG-S is the user's rules (R1–R4)**: `checks.MG-S: false` is ignored and
reported as a `major`; a `manuscript_gate.MG-S` waiver is ignored; its findings
are never `refuted`, `fixed` or `accepted-risk` by hand — they close when the
sweep stops reporting them; a missing or failing `check_story.py` makes the
verdict `ERROR`. Convergence also re-runs `check_story.py --manuscript` at
verdict time: it must exit 0. A missing `lint_fiction.py` leaves MG-T a
`blocked` coverage record — never a silent pass. Other deterministic findings
(MG-5, MG-7, MG-T) are never `refuted` or `fixed` by hand either (every
profile); a non-critical MG-5 or MG-T, or a minor MG-7, may be
`accepted-risk` with a note of 20+ characters.

**MG-4 and MG-C are part of R2** (the ending and the arcs read on the page):
`checks.MG-4: false` / `checks.MG-C: false` are ignored and reported as a
`major`, `manuscript_gate.MG-4` / `.MG-C` waivers are ignored, and no
`manuscript_gate.coverage` waiver covers a pending or sampled MG-4/MG-C
subject — the book converges only with both read in full (two passes on the
current manuscript).

**R1/R2 agent findings.** An MG-4 or MG-C finding about an arc that does not
resolve on the page (`rule: "R1"`) or an ending that is not delivered (`rule:
"R2"`) MUST carry that `rule` (plus `category: character` or `plot` for
MG-C). Such a finding is never `accepted-risk`, `refuted` or `fixed` through
`--resolve`, and an adversarial verifier's `REFUTED` does not close it: only a
re-audit of CHANGED text (a new manuscript hash) that no longer reports it
closes it. Other agent findings follow `references/manuscript-gate.md`
(`fixed` needs a note and a changed text; `refuted` / `accepted-risk` a 20+
character note; never accepted-risk for a critical).

**Agent outputs** (`round-N/findings/`, schema
`templates/gate-findings.schema.json`, `subject: "manuscript"`, written even
when clean), **two independent passes each** (fresh subagents, `pass: 1` and
`pass: 2`) per manuscript hash — one pass leaves the subject `pending (passes
1/2)`: MG-4 → `manuscript.whole-book-read.p1.json` and `.p2.json` (`check:
"MG-4"`, `lens: "whole-book-read"`); MG-C → `manuscript.continuity.p1.json`,
`manuscript.developmental.p1.json` and their `.p2.json` (`check: "MG-C"`, `lens`
as in the name).
MG-C findings may carry the optional `category` (`character | factual-detail
| narrative-style | timeline | plot | world`); MG-4 and MG-C findings carry
`rule: "R1"` (an arc unresolved on the page) or `rule: "R2"` (the ending not
delivered) whenever that is what they report.

## MG-S — story closure (script)

Reports `ARC-NOT-RESOLVED`, `LEDGER-OPEN`, `ENDING-NOT-DELIVERED` (`final_unit`
not in `final/`, or holding fewer than max(300, 30% of its `target_words`)
words of prose — a one-line chapter does not deliver an ending),
`LEDGER-MISSING` / `LEDGER-INVALID` (major here) and any design code a
mid-book change broke. Fix the page (Writer on the unit) or, with the human,
the design: move a `resolves_in`, or mark a ledger entry
`deliberately-ambiguous` with a note.

## MG-T — book-level tics and form (script)

Tics invisible one chapter at a time (`repeated_ngram` across ≥ 3 units,
`gesture_tic`, `paragraph_opener`, `opening_repeat`), names, attribute
conflicts and dialogue format. Fix with a tic pass
(`references/agents/humanizer-literary.md` § Tic pass); names through the
questionnaire or a spelling fix.

## MG-4 — whole-book read (Reader-POV)

The reader picks up the finished novel cold: `manuscript.md` only — no
outline, no journal, no bible. Report as findings, each with `reader_impact`:

| Finding | Relation | Severity |
|---|---|---|
| Where I would stop reading | D3 | major |
| A sag: two or more consecutive chapters with low pull | D3 | major |
| A question the book made me hold and never answered (not left open on purpose) | D3 | major |
| A payoff that arrives without build-up, or too early | D3 | minor |
| A character I cared about who vanishes or changes without cause — their arc never resolves on the page (`rule: "R1"`) | D3 | major |
| The ending does not land, or does not answer the question I was holding (`rule: "R2"`) | D3 | major |
| Sameness: a move repeated across the book; chapters doing the same work | D3 | minor |
| What worked — do not touch | N1 | null |

The ending's existence is MG-S's; MG-4 judges whether it works.

## MG-C — continuity and development (Continuity Guardian)

Relations (`templates/gate-findings.schema.json` → `relation`):

- two sites that cannot both be true — including a rule of the world broken
  later with nothing acknowledging it → **D1** (one hedged, one flat → **D5**);
- one person, place or object under two names or spellings → **D4a**; one
  name for two → **D4**;
- a designed element missing from the page — an arc not resolved on the page
  (`category: character`, `rule: "R1"`), the ending not delivered (`category:
  plot`, `rule: "R2"`), a plant never paid, a turning point that never happens
  → **D3**, with `gap_description` and `reader_impact`;
- checked and consistent → **N1** (first-class; emit it).

In this branch **D3** may come from `developmental` and from MG-4; the
source-lens restriction in `manuscript-gate.md` is nonfiction's.

Severities:

- **critical** — a contradiction that breaks the story's logic (a dead
  character acting, a date that makes an event impossible); the ending not on
  the page.
- **major** — any other contradiction between chapters; a `contradicted`
  real-world fact in realistic fiction; an arc unresolved on the page; a ledger
  entry open; an impossible weekday or duration.
- **minor** — attribute drift a careful reader might catch; a thread dropped
  without consequence.

A fact the lane could not verify goes to `deferred` with `needs: person` or
`document-of-record` — a question for the human packet, never a finding
(MG-6 is `n/a`: no waiver or plan rests on it).

## Suppressors

Apply before emitting, together with those of `manuscript-gate.md`:

- **Voice is not a defect**: fragments, dialect, register and style choices
  signed in the voice profile.
- **Deliberate openness**: a ledger entry `deliberately-ambiguous`, or a
  mystery the ending leaves open by design (`plot-structure.md`), is not a gap.
- **Subjective narration**: when the style guide or a sheet declares an
  unreliable narrator or faulty memory, two accounts inside one character's
  telling are **N2** unless the narration itself asserts both as fact.
- **Search the whole book** for the other site before reporting.

## Definition of Done (literary)

`phase: complete` requires, besides the verdict and convergence rules of
`references/manuscript-gate.md`:

1. **Every arc resolved** on the page, at or before `ending.final_unit`: no
   `ARC-NOT-RESOLVED`, no open developmental arc finding.
2. **The ending delivered** in `final_unit`: no `ENDING-NOT-DELIVERED`; that
   unit passed `ending-1`.
3. **The ledger closed**: every entry `paid`, or `deliberately-ambiguous`
   with the human's note; no `LEDGER-OPEN`.
4. No open critical or major finding from MG-4, MG-5, MG-7, MG-S, MG-T, MG-C.
5. The human has read the MG-4 report and signed.
