# Rationale — literary profile and shared agents

Why the literary rules are what they are. Agents do not load this file; agent
files keep the rule and, at most, a `Why:` pointer to a section here. Sources
are summarized from `REVIEW-v3.3-integral.md` (§ 5.1, § 7, § 9); preprints
marked *unverified* were reported by a search agent and not checked.

## The evidence that drove v3.4

One real chapter (v2 pipeline, a Spanish rioplatense novel, chapter 1,
~4.8k words) passed the Critic with zero fails in about forty minutes, and the
author rejected it: "para literatura es mala". A usage audit then found what no
gate had seen: "se ríe" ×7, "asiente" ×7, "Voy." ×6, dialogue echoing
dialogue, every character speaking in the same laconic register. A day-of-week
slip ("Italia" said to be Saturday afternoon in a Sunday chapter) and a
probable real-world error (a 2018 cup final with the wrong opponent and score)
passed a Critic that wrote "zero anachronisms".

The diagnosis: the pipeline is quality control against an external truth, and
fiction has none. It ran QA machinery against checklists it wrote itself —
presence of beats, absence of a blacklist, existence of an inventory — and
certified "competent and clean", the exact failure it was built to avoid. The
v3.4 redesign moves the lever upstream (story design, human seeds), makes the
scorecard honest about measuring defects only, counts tics with scripts, and
gets quality signals from an isolated reader and the human.

## The four rules

The user's non-negotiable rules (R1–R4) exist because characters without arcs
and books without endings cannot be repaired at line level: a chapter can only
dramatize a turning point that was designed. Checking them by script
(`check_story.py`, `pipeline_step.py ready`) makes "no drafting without
design" a precondition instead of advice. The Writer may not invent named
characters because every invented name is an unplanned arc (R1) the ending
(R2) never accounted for.

## Calibration contamination

In the rejected chapter, the Critic cleared a "No es una bendición, no es un
permiso. Es un dato." reframe **because a calibration passage used the same
shape**. That passage had been drafted by the model at setup, and it also
modelled the sedated staccato ("Le doy play." / "Apago. El vagón sigue.") that
then dominated the chapter. Inference: the tic entered through calibration and
the gate protected it. Hence: human-written calibration passages
(`calibration-source`, counted by `check_story`), model passages screened for
counted tics, and no exemption from counts for anything a calibration passage
does.

## No GOOD examples

Models imitate examples more faithfully than they follow rules. A GOOD passage
in a shared reference becomes the voice template of every project that loads
it. So references describe BAD shapes and the only imitable prose lives in each
project's `voice-profile.md`. v3.3 still re-introduced neighbours as examples
through "voice calibration samples" in digests, which every Writer turn read;
v3.4 removes them from the literary digest.

## Quotas removed

- **VOICE-RISK "exactly one per chapter"**: a fixed quota breeds a new pattern
  — one odd simile per chapter. A failable quota trains fake risks; so does a
  mandatory one. Now optional, 0–2, with a log so repeated shapes show.
- **Opening rotation**: A-B-C-A-B-C is a periodic formula; no novel opens its
  chapters from a menu. Now an observation (`opening_repeat`).
- **"Mandatory techniques"**: a non-visual sense in every setting sentence, a
  three-word punch after a long sentence, an image in every paragraph, a voice
  simile. They pushed toward purple or staccato prose — the current models'
  signature tic. StoryScope (*unverified*) reports AI fiction conveys emotion
  only through bodily sensation in ~81% of cases vs ~38% for humans: an
  absolute "show, don't tell" pushes toward the AI fingerprint.
- **"Inject controlled imperfection"** contradicted the Humanizer ("added
  imperfections are the factory's idea of imperfection") and was removed.
- **Em-dash cap and "said/asked only"** were anglocentric: in Spanish the raya
  is the dialogue mark (a style linter flagged 24/24 dialogue rayas as
  em-dashes; 1,489 in a long novel).
- Commercial and noir craft sources were "mandatory" for a profile that also
  covers memoir and literary fiction; now optional by subgenre.

## Conserve, not improve

Observed failure: "conserve" quietly became "improve", one flagged beat at a
time. A Humanizer rewriting 5–10% of a draft is a second Writer with no
outline duties. The 3% budget is now measured by `check_role_diff.py`, and
exceeding it routes to the Writer (`voice-6`) — in v3.3 the advice to route
there existed in the Humanizer file but no rubric item encoded it, so the
computed verdict sent voice failures back to the Humanizer.

## Routing

v3.3 routed literary comprehension and pacing (`reader_pov-1/2/3`) to
"Reader-POV + Humanizer", whose contract forbade rewriting reader-flagged beats
and capped it at 3%: a loop with no exit that burned retries until escalation.
A slow beat is a content or structure problem wearing a prose costume, so
comprehension and "would close the book" go to the Writer and pacing to the
Editor.

## LAMP

LAMP ("Can AI writing be salvaged?", Chakrabarty et al., CHI 2025, arXiv
2409.14509) gives a seven-category taxonomy of AI prose idiosyncrasies
(cliché, unnecessary exposition, purple prose, poor sentence structure, lack
of specificity, awkward phrasing, tense inconsistency) and reports low
precision for automatic detection (≈0.46). Hence: mark spans first, edit only
spans a rule backs, few-shot from the project. Related: negative prompting and
temperature do not fix homogeneity (arXiv 2606.17350, *unverified*) — word
lists are hygiene; originality comes from structure and human seeds.

## Reader isolation

A cold read is impossible when the same context has loaded the bible, the
outline and the critique. In the rejected chapter the Reader-POV said the
prose "is not AI prose" and the Critic used that as independent confirmation.
`humanized.md` also carried VOICE-RISK, HUMANIZER and EDITOR comments — the
"cold" reader read the author's intent — and the literary reader read the
outline entry, which spoiled the beats and told it what to feel. Hence the
isolated subagent, the comment-stripped `humanized.clean.md`, no outline for
the literary reader, and the reader journal as its only memory (tension probe
by prediction: "Spoiler Alert", arXiv 2604.09854, *unverified*). LLM judges do
not correlate with experts on literary quality (TTCW, arXiv 2309.14556): the
reader reports experience; the human judges quality. Reviewers blind to each
other avoid homogenized reviews (arXiv 2601.08003, *unverified*).

## Scene cards

A 5k-word chapter drafted in one pass tends to summarize; DOC/Re3 (arXiv
2212.10077), Agents' Room (arXiv 2410.02603) and Story Grid practice write per
scene. Cards move the friction inventory from the Writer's after-the-fact
self-assessment into the human-approved outline: want, opposition, pivot,
value change, and the crisis as a dilemma (Story Grid). `attempts` — what the
character tries and why each fails — comes from adversarial suspense planning
(Xie & Riedl, EACL 2024, arXiv 2402.17119). The causal "therefore/but" link is
the old anti-mediocrity causal-chain rule moved to where it can be checked.
The Foreshadow–Trigger–Payoff ledger replaces loose `chekhov` lists (CFPG,
arXiv 2601.07033, *unverified*, reports much higher payoff rates).

## Echo check

"Echoes in AI" / Sui Generis (arXiv 2501.00273): a plot element that appears in
most alternative generations is a model default. Generating K alternatives per
turning point and flagging a planned turn that matches the majority puts that
choice in front of the human instead of letting it pass as design.

## Facts lane

Realistic fiction has verifiable facts, and v3.3 left them to nobody ("n/a,
the human's call"). ConStory-Bench (arXiv 2603.05890, *unverified*) gives the
continuity categories used by CG Mode A and reports contradictions cluster at
40–60% of the text — hence the extra comparison in the middle half.

## Human taste

GPT-4 writes better from a human author's titles and worse in Spanish (Pron vs
Prompt, arXiv 2407.01119). Taste is the central input of fiction and v3.3 only
let it in as approval of model output — five thousand words plus six reports,
which invites signing without reading. Hence: seeds the pipeline never
invents, a preserved braindump (Sudowrite's story bible practice), human
calibration passages, key scenes chosen among divergent versions (choosing is
cheaper than evaluating), and a short packet.

## Omission

Nonfiction history of a shared agent (CG Mode A). Run blind against nine
human-confirmed defects, a rule-vs-instance lens caught 6 of 6 contradictions
and 0 of 2 omissions; inverting the default for omissions moved recall from
6/9 to 8/9 with no new false positives. A digest cross-check proves presence,
not consistency — that gap shipped a book.

## Whole-book read

Nonfiction history of a shared agent (Reader-POV, MG-4). On the reference
technical book a concept appeared in unit 1 and was taught in unit 10, another
in unit 7 and taught in unit 9, and the security chapter taught writing the
security table but never deploying or verifying it; six technical passes had
validated every sentence. Batches of 3–4 cannot hold both ends; "is it
enough?" is a question no other check asks.

## Enforcement holes

An adversarial review of v3.4 (2026-09-25) found every R1–R4 guarantee
bypassable by a determined or careless orchestrator. The fixes, and why:

- **Sentence-initial names.** "Gustavo no saludó." produced no finding: the
  detector trusted only mid-sentence capitals, and Spanish drops subjects, so a
  name often opens its sentence. A frequency list (`common_words`) plus "never
  written in lowercase in the book" separates *Gustavo* from *Nadie*; verb
  endings that no frequent name shares (`initial_verb_forms`) keep *Rezó* out.
  Endings shared with names (María, Fernando, Javier) stay out on purpose.
- **Known-name loophole.** Any capital in `world.md` counted as known, so
  listing a character there skipped R4. `world.md` names are now
  mentioned-only: speaking, acting, or entering a scene card makes them
  characters.
- **Overrides.** A human approval over a red scorecard, `--human-override` and
  `approve --force` each let a unit with an unknown speaker reach `final/`;
  the gate let `accepted-risk`, `refuted` and a disabled MG-S converge a novel
  whose ending was never delivered. The rules the user set are not waivable,
  so no path around them exists in code.

A second adversarial pass (fix round 2) replayed the same threat — an
orchestrator that rationalizes its way to "done", or a careless operator — and
found laundering routes rather than missing checks:

- **Every door to the page checks R3.** A unit whose own cast was complete
  could be drafted while the rest of the design was not; now the Writer's
  `check`/`done`, `approve` and `apply-edits` all require the full `ready`.
- **A misspelled profile switched the rules off.** `Book-Literary`,
  `book-fiction` or no profile read as "nonfiction". The profile is
  normalized, and an unknown one stops the scripts.
- **Names hid in form.** Italics, ALL CAPS, internal capitals, headings, table
  cells, and attributions with words in between ("—dijo el viejo Gustavo",
  "Gustavo, con las manos en los bolsillos, dijo") are scanned; any world.md
  word — a place too — that speaks or acts is a person.
- **The bible laundered names.** A lowercase name in an extras label, a
  location in the outline, a role-less or broken sheet, a duplicate slug, an
  alias added to a signed sheet: each made a name "known". Extras and
  locations no longer know people, every sheet is validated, and a signature
  is a hash of what the human approved.
- **Placeholders and thin endings passed.** `N/A`, `x`, `(pendiente)` filled
  a field; a one-line final chapter "delivered" the ending; a missing ledger
  was a warning. Each is now blocking where it matters.
- **The gate trusted declarations.** `fixed` with no change, `refuted` with
  "x", waivers of `N/A`, a runner string as proof of a run, one quiet round,
  and a truncated findings store all converged a book. Deterministic findings
  close only by the sweep, agent findings need evidence or a real reason,
  R1/R2 findings only by a re-audit of changed text.

Cheap and explainable beats clever: every mechanism is a string rule or a
hash, and each has a regression in the selftest. Known gap, documented rather
than patched with a model: a name that is also a common noun ("Luz"), used
only to open sentences and never speaking or acting, while "luz" appears in
lowercase — the Critic's character-3 and CG Mode A read for it.
