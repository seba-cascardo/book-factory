# Changelog

## 3.4 — Verdicts that can say no, and stories that are designed first

Written from an integral review of v3.3 (2026-09-25): a full read of the skill, an
execution audit of every script on technical and literary fixtures (Spanish, raya
dialogue, 30×5k words, encoding edge cases), and the real-use record of the books
written with v2 (Qliking, Prompting, Catalina). No project had run v3.x yet, so the
review's evidence for the gate was the code itself — and the code had the defect class
the gate exists to prevent.

### The gate could declare a book complete with a critical open

`converged()` never looked at the verdict, `rounds_without_new` counted invocations
(three `--verdict-only` runs on round 1 printed "CONVERGED — BLOCKED … can reach
complete"), open findings did not carry over between rounds, and tool failures were
swallowed — a cp1252 file crashed `lint_render` and the gate reported "MG-5: 0
critical" with exit 0. All four are fixed and each has a regression test; the old
selftest (62/62) passed with every one of them present.

The gate is also simpler. Coverage accounting — breadth and depth as separate terms,
two waivers, two signatures — is replaced by a cumulative `findings.jsonl` (open
findings live until resolved with `--resolve`), a content-keyed `subjects.json`, and one
coverage waiver. Verdicts: `ERROR | BLOCKED | NEEDS-REVISION | PASS-PARTIAL | PASS`
(PASS-SAMPLED is gone). Exit codes: 0 converged, 1 not converged, 2 error.
`--audited` is now `--subjects`. Fingerprints keep code spans, operators and case, so
existing claim indexes will report `CHANGED` on passages with inline code — once.

### The gate has a literary branch

It had none: a novel ran concept dossiers built from n-grams (`hasta_que`,
`dijo_elena`) and stalled in PASS-PARTIAL. For `book-literary`, MG-1/2/3/6 are n/a by
profile and three checks replace them: **MG-S** story integrity (`check_story.py
--manuscript`: every arc resolved, the ending delivered in `final_unit`, the ledger
closed), **MG-T** texture (`lint_fiction.py --book`: cross-chapter tics, unknown or
near-duplicate names, attribute contradictions, dialogue format), and **MG-C**
continuity & developmental read. See `references/manuscript-gate-literary.md`.

### Literary: every character has an arc, the story has an ending

Three rules from the author, non-negotiable and enforced by code:

- Every character (protagonist, principal, secondary) has a complete sheet —
  backstory, personality, contradiction, want, need, voice, and an arc with turning
  points on named units and a `resolves_in`. Flat arcs are legal and must say what they
  test. No `TBD`.
- The story has an ending before drafting (`plot-structure.md` → `ending`).
- Drafting starts only when `pipeline_step.py ready` passes. A character added
  mid-book — proposed by anyone, or detected as an unknown proper name in a draft —
  pauses the unit and runs `references/character-questionnaire.md` again. The Writer
  never invents a named character.

Baseline before the change (six fresh agents on v3.3): all six would draft with
characters and ending in `TBD`, citing "Leave TBD where the human isn't ready" and a
`minor` character-3.

The literary flow moved upstream. Scene cards (want, opposition, pivot, value change,
crisis, attempts), a Foreshadow–Trigger–Payoff ledger, an echo check on turning points,
a Reader-POV stress test of the synopsis, and a design rubric are approved with the
outline. Human seeds and at least one human-written calibration passage are required;
key scenes are chosen from divergent versions. The Writer drafts scene by scene; the
Humanizer works by the LAMP categories and its budget is measured, not self-reported;
Continuity Guardian Mode A now runs before the literary gate, with a facts lane for
realistic fiction. Removed: literary opening rotation, "exactly one VOICE-RISK",
"inject controlled imperfection", voice-calibration samples in digests, and the
"mandatory techniques" that pushed prose toward purple and staccato — they are
diagnostics with budgets now.

### Counted means counted by a script

Six new scripts: `count_rhet.py` (rhetoric budget, AI-isms, hedges, narration-only
em-dashes), `check_identifiers.py` (every function or command against an index built
from the sources — the `GroupConcat()` case), `check_role_diff.py` (the Editor added no
prose; the Humanizer stayed in budget; the Proofreader's changes go to the human),
`lint_fiction.py`, `check_story.py`, and `pipeline_step.py` (dispatch brackets
`check`/`done`, `clean`, `snapshot`, `checks`, `ready`, `apply-edits`). Word lists
live in `scripts/lexicons/{en,es}.yaml`; a Spanish book is no longer counted with
English patterns, and a dialogue raya is never an em-dash.

### Pipeline

- Execution model written down: every agent is a subagent; Critic, Reader-POV,
  skeptics, auditors and CG Mode A are isolated with a closed input list; cold readers
  read `humanized.clean.md`.
- Loop semantics: targets are `Writer | Editor | Humanizer | escalate`
  (`Reader_POV_plus_Humanizer` routed reader findings to the one agent forbidden to fix
  them); every target reads its worklist; re-entry from the last gated text; a cycle
  that resolves nothing escalates (plateau rule).
- The Proofreader runs before human review, so the human approves the text that ships.
- Runs log moved to `runs.tsv`; per-unit script results in `checks.json`.
- Adversarial verify: a single-skeptic finding is confirmed by a refutation pass
  (optionally on a second model) — the three lenses are disjoint by design, so "≥2
  skeptics agree" almost never fired.
- Rubric split: `rubric.md` (schema + the verdict computation) plus
  `rubric-nonfiction.md` or `rubric-literary.md` — each Critic loads one family file.

### Closed after an adversarial pass

An independent agent was told to refute "v3.4 is coherent and operable" and
found nine behaviours that let the author's rules or the gate be walked around.
All are closed and each has a regression test:

- A new name that opens a sentence once ("Gustavo no saludó.") went unseen. The
  language packs now carry `common_words`, `initial_verb_forms` and
  `noun_suffixes`; a capitalized token that is none of those and never appears
  in lowercase is a high-confidence name. A flagged token first gets one triage
  question ("is this a person?") — no → `bible/lexicon.yaml → common_words`, yes
  → the questionnaire.
- `world.md` names are mentioned-only: one that speaks, acts in two units or
  enters a scene card is a character (R4). Scene-card text is scanned too.
- Story blocks (R1–R4) are never overridable: not by `--human-override`,
  `approve --force`, a Critic verdict, `--resolve` or a gate waiver. For novels,
  MG-S cannot be disabled or waived, and convergence re-runs `check_story
  --manuscript` live.
- Waivers count only with `waived_by`, `reason`, `debt`; an MG-6 waiver needs a real plan
  entry; code with a language tag and no declared surface is a major.
- Role violations cannot be laundered through a loop: `snapshot --reason`
  records why the loop opened, snapshots `draft`/`edit` too, and a Writer
  REVISE after a Humanizer or Editor violation starts from the text before it.
- Freshness: `check` records the dispatch time; `done` rejects stale outputs;
  the Critic and Proofreader require reports newer than the text they judge.
- `done editor` / `done proofreader` exit 4 on a contract violation.
- `done critic` recomputes the verdict from `scorecard.yaml`
  (`scripts/bookkit/verdict.py`, the one implementation of `rubric.md`) and
  rejects a header that disagrees.
- The Technical Reviewer REVISE path is executable as documented.
- Project schema is now `"3.4"`; anything else is an earlier version (re-scaffold,
  no migration).

A second verifier then attacked the fixed version and found fourteen more ways
around; all are closed (47 reproduced attacks fail closed; selftest 511/0):

- R3 holds at every entry to the page: `check writer`, `done writer`, `approve`
  and `apply-edits` require the full `ready` result, not just the unit's cast.
- The profile and schema are validated by every script; a misspelled profile no
  longer switches the literary rules off.
- Name detection covers italics, ALL CAPS, internal capitals, headings and table
  cells, speech verbs with intervening words, appositives, and inverted subjects;
  a `world.md` or location word that speaks or acts is a character. Known limit:
  a name that is also a common noun and only opens sentences (Luz, Paz) — the
  Critic's character-3 and Continuity Guardian Mode A are the backstop.
- Sheets are bound to content: `pipeline_step.py sign <slug> --by …` writes
  `signed_on` and `signed_hash`; any later edit is `CHAR-UNSIGNED-CHANGE` until
  re-signed. Broken sheets, invalid roles and duplicate slugs block
  (`CHAR-DUPLICATE`); extras labels no longer make names "known".
- Placeholders ("N/A", "x", "completar", "{{…}}", "Lorem ipsum"…) never fill a
  required field; narrative sheet fields need three words or more.
- The story ledger must exist and be well-formed (`LEDGER-MISSING`,
  `LEDGER-INVALID`); a final chapter too thin to carry an ending is
  `ENDING-NOT-DELIVERED`.
- `--resolve` needs evidence: deterministic findings are never closed by hand;
  `fixed` requires the text to have changed; literary findings tagged
  `rule: R1|R2` close only by a re-audit after a text change. Waivers need real
  content; in novels MG-4 and MG-C can be neither disabled nor waived;
  `rounds_without_new_to_close` is at least 2; MG-6 needs runner `evidence`; a
  truncated findings store is an ERROR; `checks.json` carries the hash of the text
  it measured.
- The triage question for a flagged name has three answers: not a person
  (`common_words`), a public figure never on stage (`non_person_names`), or a
  person in the story (the questionnaire).

### Also

- Language: `project.language_variant` is canonical (scripts read it; they used to
  read `conventions.*` and treated a Spanish project as en-US); MG-2 and claim scoring
  use the language packs, with a language-agnostic fallback.
- Text layer: UTF-8-sig, NFC, cp1252 reported instead of crashing, CommonMark fences,
  comments inside code no longer linted (Mermaid `-->` blocked `complete`), scene
  breaks `* * *` accepted, `1999.`-style accidental lists and dialogue glued to
  narration flagged, Windows junctions handled.
- Size: history and measurements moved to `docs/rationale/`; agents load rules only.
  The files agents load shrank by roughly a third while gaining the literary redesign.
- Qlik validation surfaces moved to an optional pack, `references/surfaces/qlik.md`.

## 3.3 — A binary criterion needs a ladder

Written from a review of v3.2. The coverage term landed and was verifiable, but
it carried a flaw of exactly the kind it was built to prevent.

**`PASS` was unreachable by construction.** v3.2 required
`covered == eligible AND sampled == 0`. Breadth had a mechanism — rounds drain
the pool, so it closes by spending rounds. Depth had none: `tractable` was
derived purely from `len(instances) <= 40`, with no override, no narrowing, no
hand-written probe for rules. **On the reference book 221 of 454 rules were over
that line**, so `sampled == 0` could never hold however much work anyone did.
Every large technical book would have ended at `PASS-PARTIAL` plus a standing
waiver, permanently.

That is the decay this design rejects for percentage floors, arriving through the
other door — and `references/manuscript-gate.md` already said so about a
different criterion: *"That is unreachable — and promising it produces a gate
someone turns off."* v3.2 applied the reasoning to findings and not to depth.

Aggravating it, `extract_rule_candidates.py` said twice that *"the fix is a
hand-written probe"* while `bootstrap_probes.py` and `concept-probes-tuned.yaml`
existed only for concepts. The instruction pointed at something that did not
exist.

### Breadth and depth are separate terms

```
if blocking:               BLOCKED
elif major_open:           NEEDS-REVISION
elif not breadth_complete: PASS-PARTIAL     # subjects nobody opened
elif not depth_complete:   PASS-SAMPLED     # subjects read only in part
else:                      PASS
```

They are separate because they close by different work and one of them cannot
always be closed at all. Breadth closes on its own; depth needs human judgement
about a subject's scope. Breadth outranks depth because *"nobody opened it"* is a
worse state than *"we read part of it"*.

Two signatures, two waivers. `manuscript_gate.coverage` (breadth) should feel
expensive — it means nobody looked. `manuscript_gate.depth` is the routine one:
some rules genuinely reach more instances than one agent run can judge, and that
is a fact about the book rather than a shortfall in the audit. Each is stale and
does not count when its signature stops matching.

### The ladder: `bible/rule-probes-tuned.yaml`

The rule-side twin of `concept-probes-tuned.yaml`, and now the file those two
comments were pointing at. Narrow a rule's `key_terms`, add `require_terms`,
scope it with `scope_units` / `scope_heading`, drop instances with
`exclude_pattern`, or `split` one broad rule into scoped sub-rules that are
audited and tracked separately.

**Narrowing is a claim about a rule's SCOPE, and it is auditable.** If a rule
genuinely governs 87 code blocks across nine chapters, do not shrink it to make a
number go down — leave it sampled and waive the depth. A narrowing written to
reach `PASS` is a lie the gate then repeats back as a clean bill of health. The
template says this before it shows the syntax.

For concepts, `home_cap` is now settable **per probe**, so one sprawling concept
can be read in full without raising the global dial.

New: `templates/rule-probes-tuned.yaml`.

### The worklist, generated

An escape hatch nobody can find is not an escape hatch. The gate writes every
still-intractable rule — ranked by instance count, with a commented stub each —
to `round-N/rule-probes-proposed.yaml`. Depth closes one rule at a time, so the
work starts from the real list rather than from a blank file. Same reason the
verification plan is generated from `deferred` rather than described.

### Also

- A check that could not run at all now leaves a `blocked` coverage record and
  says why. MG-1 with no probes used to leave silence, which the verdict read as
  "subjects nobody opened" — sending the reader to dispatch auditors when the
  real problem was a missing input file. Silence reading as something else is the
  defect class this gate exists for; it applies to the gate itself.
- `build_concept_dossier.py` no longer exits when there are no probes. It reports
  and writes an empty coverage record, so "nothing to audit" and "the emitter
  fell over" stay distinguishable.
- `references/manuscript-gate.md` § Calibrating a check gains the transferable
  rule: **before shipping any hard criterion, name the specific work that moves
  it from false to true, and check that a person can actually do that work.** If
  you cannot name it, you have written a percentage floor with extra steps.
- `selftest.py` grows the depth cases, on a corpus generated rather than checked
  in because the shape is arithmetic — a rule needs three key terms whose union
  clears the tractability ceiling while each stays under the `--df-ceiling`, and
  that only holds at a corpus size no hand-written fixture would carry. 62
  assertions, all deterministic.

## 3.2 — The verdict learns what it did not look at

Written from a review of v3.1 against the fix phase of the same 18-chapter
technical book. v3.1 found the defects that had escaped writing; what it could
not do was tell you how much of the book it had looked at.

**The hole was one hole.** The verdict was `f(findings)`. Nothing in it knew that
a book could reach `PASS` → `phase: complete` having audited **30 of 474
candidate rules**, and that the "two consecutive quiet rounds" criterion was
satisfied *by construction*: rounds 2+ audited only edited passages, their
propagation set, and open findings, so the 444 unselected candidates were never
looked at, never produced a finding, and made every later round quiet. The quota
was documented as a cost dial and behaved as a permanent ceiling.

Three files already said a sample is not an all-clear — the rule auditor's *"do
not conclude the rule is clean"*, the findings schema, the report template. The
verdict did not know. That is the same class of defect the skill exists to
prevent, one level up.

### Coverage is a computed term of the verdict

```
if blocking:                 BLOCKED
elif major_open:             NEEDS-REVISION
elif not complete_coverage:  PASS-PARTIAL      # new
else:                        PASS
```

`complete_coverage` is binary — `covered == eligible_candidates` **and** zero
sampled subjects, for every enabled semantic check — and not a percentage floor,
because a floor invites arguing the number and the day it is expensive it gets
waived out of habit. `PASS` means *all of it was looked at*. `PASS-PARTIAL` means
*X of Y, and here is the ranked list of what was not*.

`PASS-PARTIAL` does not block the work. It blocks the claim: `phase: complete`
needs `PASS`, or `PASS-PARTIAL` plus a `manuscript_gate.coverage` waiver carrying
a **signature of the exact numbers**. A waiver whose signature no longer matches
is reported stale and does not count.

Two axes, reported separately: breadth (`covered/eligible`) and depth (subjects
judged from a sample of themselves). A run with 100% breadth and 15% depth is not
a complete run.

### The rounds drain the pool

`reviews/manuscript-gate-<date>/audited.yaml` — cumulative, keyed by subject id
**and fingerprint**. The emitters skip what it records; those subjects leave the
pool but stay in the denominator. Round 2 therefore selects the *next* slice by
ranking, coverage grows monotonically, and `--top` is finally the cost dial its
comment always claimed. The fingerprint spans everything an audit read (a rule
plus its instances, all of a concept's passages), so an edited subject returns to
the queue — the claim index's asymmetry, applied to the ledger.

Without this, `PASS-PARTIAL` would be a state nothing could leave.

### MG-7 — a fixed defect must not come back

`bible/do-not-touch.md` protects text that is correct; `selftest.py` tests the
scripts. Nothing asserted *"this defective formulation must not return"*.
Evidence: closing one defect — a chapter collapsing three set-modifier positions
into two slots, which took **four independent passes** to find — needed a
hand-inverted gate assertion and hand-added linter pins.

`bible/fixed-defects.yaml` + `scripts/check_fixed_defects.py`, in the
deterministic sweep, whole book, every round. A reappearance is `critical` by
default. The load-bearing part is `allow_in`: **the text that corrects a defect
usually quotes the defective form in order to teach against it**, so a literal
pin fires on the fix itself. Pin the claim, not the code.

New: `templates/fixed-defects.yaml`, `scripts/check_fixed_defects.py`.

### Content anchors, and `--heal`

Measured during one day of fixes: line-keyed references broke **three times, and
two of those were caused by adding a section**. A gate that shouts when nothing
happened gets switched off in a week.

Every persisted reference now carries a short verbatim anchor beside its line
number, and resolution distinguishes the case a line number cannot express:

```
anchor at the recorded line     OK
anchor nowhere in the file      EDITED   — the passage was CHANGED
anchor elsewhere, exactly once  DRIFT    — it MOVED; --heal repairs it
anchor matches more than once   AMBIGUOUS
```

`scripts/resolve_anchors.py --heal` rewrites stale numbers after a fix pass, and
deliberately refuses to touch `EDITED` — repairing one would silently attach a
verified-correct anchor to text nobody checked.

New: `scripts/resolve_anchors.py`, `scripts/bookkit/anchors.py`.

### The economy is visible

The token cost sits on the same line as the dial in `meta.yaml` (~170–230k tokens
per lens run, so `top_rules: 30` × `passes_per_subject: 2` ≈ 12M tokens for MG-2
alone). The cut is stated as surface rather than as configuration — *"444
candidates will not be looked at — 94% of the eligible surface"* — and the cut
list reaches the human packet **ranked**, so three specific candidates can be
promoted into the next round without recalibrating anything.

### Also

- `round-N/coverage-summary.md` is generated: the report's header and its
  `What ran` table are computed, not written by an agent from memory.
- `state.json` records coverage per round; the report's round history has a
  coverage column. Two quiet rounds at the same coverage are one round run twice.
- A findings file is now also a coverage record — auditors write one **even when
  they found nothing**, because a subject with no file is a subject nobody read.
- `bookkit/__init__.py` forces UTF-8 on stdout/stderr, so the scripts stop dying
  with a `UnicodeEncodeError` halfway through their own report on a stock Windows
  console.
- `selftest.py` gains the two directions of the coverage case (a one-subject
  quota with zero findings must be `PASS-PARTIAL`; full coverage with zero
  findings must be `PASS`), plus pool-draining, re-queue, MG-7 with its `allow_in`
  exemption, and the full anchor lifecycle. 54 assertions, all deterministic.

Unchanged on purpose, because breaking them would be expensive: `select_rules()`
as the single selection function, the inverted omission default (`D6`/`N2` → `N2`
but `D9`/`N2` → `D9`), the bidirectional selftest, and `violation_kind` as the
anti-memorization check.

## 3.1 — The manuscript gate

Written from a post-mortem of a finished 18-chapter, ~156,000-word technical
book. The pipeline had produced it well: 49 of 69 adjudications against official
documentation came back `SUPPORTED`, the voice held across the whole book, and
the mechanical sweeps were clean. Then seven review passes after approval found
**220 deduplicated defects and 8 blockers**.

What failed was not execution. It was the **unit of analysis**. Every gate in
v3.0 works on one unit, and a per-unit reviewer cannot find a contradiction that
spans two: it sees one side and approves it, correctly. Six of the eight blockers
lived *between* units, or *between layers* inside one — prose against code, text
against exercise, source against rendered output.

### Phase 4.5 — the manuscript gate (new)

A gate, not an audit: it computes a verdict, it blocks, and it **iterates until
it converges**. Six checks with the book as the unit:

| | |
|---|---|
| MG-1 | Concept audit — every claim about one concept, gathered across all units and compared |
| MG-2 | Rule vs instances — does the book's own code obey the rules its prose states? |
| MG-3 | Exercise vs delivered content — was it taught, and does the promised solution exist? |
| MG-4 | Whole-book read — **is it enough?** |
| MG-5 | Render lint |
| MG-6 | Executable code: runner, or declared debt |

It **fires automatically** when the last unit is archived. No path leads from the
last approved unit to `complete` without it. It closes on `PASS` plus two
consecutive rounds with no new blocking findings — one clean round is not
evidence — and at `max_rounds` it escalates rather than relaxing the criterion.

New: `references/manuscript-gate.md`, `references/agents/concept-auditor.md`,
`references/agents/rule-auditor.md`, `templates/gate-findings.schema.json`,
`templates/manuscript-gate-report.md`.

### `bible/claim-index.yaml` — knowing what else says the same thing

The root cause of three separate incomplete fixes in the reference project — the
longest surviving seventeen days and a full audit — was that nothing could answer
"this passage has siblings, where are they?"

The index records, per concept, which passage is canonical and which repeat it,
keyed by **fingerprint of the normalized text, not by line number**. A passage
that moves is repaired silently; a passage that is *edited* flags every sibling
and emits `PROPAGATE`. It is wired into three places that read it automatically —
the gate, the post-edit step, the build preflight — because an index only a human
consults is a checklist, and checklists go stale.

New: `references/claim-index.md`, `templates/claim-index.yaml`.

### `scripts/` — the skill now ships code

Ten scripts (Python 3.10+, PyYAML; `git` optional). A regex does not hallucinate
a violation and is not tired by chapter 14, so everything mechanical moved here
and the agents kept the judgement. All of them accept `--root` and `--units`, so
they also run standalone over a book this skill never scaffolded.

`lint_render.py` is the one that pays for itself immediately: the reference book
shipped a paragraph that **printed as an H2 heading**, because a `---` sat under
it with no blank line. Invisible in the source, obvious in the PDF, past four
technical audits. It also catches pipeline handoff comments (`<!-- EDITOR`,
`<!-- VOICE-RISK`) that flow into `final/` by design and previously had nothing
stopping them at the door.

The calibration comments in the scripts record measurements, not opinions. The
similarity metric is the one to read before touching: n-gram overlap finds *zero*
clusters on real prose, because a well-written book rephrases instead of
repeating.

### Positive verdicts are first-class

A review system that can only record defects loses its positive knowledge the
moment the report is filed. In the reference project that produced a fix pass
that introduced a factual error into text that was already correct — caught and
reverted the same day, but only because somebody remembered.

So: `verified_against` and `do_not_touch` in the claim index, `bible/do-not-touch.md`
for auto-refutation anchors, mandatory `N1`/`N2`/`D7a` emissions in the findings
schema, and a **"What was verified correct"** section in the gate report that must
not be deleted. In the reference audit it held 81 clusters — nearly as many as the
defects.

### Waivers — nothing is turned off silently

New `waivers` block in `project-status.yaml`. Any check disabled records who
waived it, why, and what is owed. A project once carried three configured checks
that had never run for three months while reporting itself publish-ready; when
finally forced, they found six blockers.

`phase: complete` now has checkable preconditions, and two new states exist:
`manuscript-gate` and `blocked-on-manuscript-gate`. Saying a book is blocked is
the useful thing to do.

### Unresolved is not unknowable — the verification plan

When the pipeline cannot establish a claim and reality could, the deliverable is
the plan to go and ask: the check written down in a form somebody can execute,
with an empty slot for the answer. Not a softened claim, and not the claim
asserted anyway because verifying it was inconvenient.

Code is the obvious case and not the only one. Every `deferred` item an auditor
emits now declares what would settle it, and the five values naming something
reality can supply — `runner`, `live-system`, `measurement`, `person`,
`document-of-record` — become numbered plan entries.
`scripts/manuscript_gate.py` writes the skeleton, grouped by need and led by the
checks that close open criticals. `human-decision` is the exception: no
observation settles a choice, so it goes to the human packet instead.

This does not apply to every book — a novel has no reality to check against. The
trigger is narrow: *the pipeline could not settle it, and a defined observation
would.*

The evidence for bothering: the first time eight checks from one such book were
run against a live system, the results **contradicted what the reviewer had
concluded on paper**. The reasoning had been careful; it was still wrong. And the
failure mode is quiet — a malformed query returns zero rows rather than an error,
which reads exactly like a correct query over empty data.

`references/test-plan.md` → `references/verification-plan.md`, broadened past
executable code; template likewise.

### Omission blindness — the finding that transfers furthest

Review agents catch contradictions and are blind to **omitted preconditions**.
Measured, blind, against nine human-confirmed defects: **6 of 6 contradictions,
0 of 2 omissions**. Both misses had the same shape — one passage declares a
condition mandatory, another applies the same pattern and simply does not mention
it. Nothing false is written; there is a statement and a silence, and a reviewer
asking "does this contradict that?" walks past it.

It is also the costliest defect a technical book ships: the reader copies the
instance, loses the condition that made it correct, and **gets no error**.

The fix is a prompt contract, not a phase. New relation `D9` with a required
`violation_kind` (`contradiction` | `omission`), worked examples of each, and —
the load-bearing part — **an inverted default: everywhere else doubt resolves to
"not a defect"; for omission, when in doubt, report it.** That moved recall from
6/9 to 8/9 with no new false positives.

Applied to every agent that compares two passages, not just the gate: Technical
Reviewer, Continuity Guardian, Critic, concept auditor, rule auditor. The
adversarial verifier is explicitly told that "these two do not contradict each
other" is *the definition* of an omission, not a refutation of one.

### Two passes, then union

One pass is not enough, and this is measured rather than assumed: the same lens
run twice over the same six rules found sites in the second round the first
missed, and one finding came back `D6` in one round and did not exist in the
other. The variance is in the sampling, not the instructions, so no prompt tuning
removes it.

MG-1 and MG-2 auditors now run twice per subject and the findings are merged.
The disagreement is itself a free signal: **a finding only one pass produced is
the first candidate for a false positive** (`single_round: true`), and it goes to
the front of the verification queue.

### Selection: one function, and a quota per failure mode

Two bugs that only appear once a gate is actually built, both now structural:

**The gate must measure the artifact that ships.** A first version verified its
calibration pairs against the *candidate* list while emission independently
capped output at 40 — the pairs ranked 199/205 and 153/211, never reached the
dossier an auditor reads, and the gate still said PASS. Fixed by construction:
`scripts/bookkit/selection.py` is the single selection function, used by emission
and by every check on emission.

**A constant bonus in a ranker is a stratifier, not a weight.** Adding a fixed
bonus for "crosses units" onto a base scale of 1–4 sorts *every* cross-unit item
above *every* intra-unit one. With 92% of candidates cross-unit, a 40-slot quota
emitted 40 cross-unit rules and **zero intra-unit** ones — and intra-unit is 7 of
10 defects, the thing the pass exists to catch. Each failure mode now carries its
own quota, and what was cut is always reported.

### Also, from building it

- **A rule can demonstrate its construct instead of naming it.** A rule fixing a
  date format inside a set modifier is written entirely out of field names and
  literals. Requiring a named keyword skipped it. Code spans carrying structural
  punctuation now count as syntactic evidence.
- **Paragraphs, not physical lines.** The claim machinery merges wrapped lines
  back into logical paragraphs first. Calibrated on a corpus where one paragraph
  was one line, this was invisibly a no-op; on a hard-wrapped book no single line
  carried enough signal to score as a claim and the audit silently found nothing.
- **The n-gram fallback for probes was losing nearly every candidate.** Regex
  phrase scanning is greedy and non-overlapping, so "the staging table" was
  matched, rejected for its leading stopword, and "staging table" never tried.
  Now tokenized with overlapping n-grams.
- `scripts/selftest.py`: 28 deterministic assertions, no model, no tokens.

### Changed defaults

- `adversarial_verify`: `off` → **`gate_critical`**. Review agents inflate:
  six findings in the reference case had to be downgraded by hand. Verification
  is cheaper than a fix pass acting on a wrong finding. With nothing marked
  `gate_critical`, this costs nothing.
- `validation_surface`: `reviewer-only` is still legal but no longer silent. An
  executable surface with no real runner needs a waiver **and** a verification
  plan (`references/verification-plan.md`), or MG-6 raises a `major`.
- Build preflight (`lint_render`, `sync_manuscript --check`,
  `validate_claim_index`) now runs for **every** profile, not just `product-docs`.

### Also

- New rubric item `code-4` (critical): no rule a unit states in prose is
  contradicted by that unit's own code or examples. Seven of ten intra-unit
  defects in the reference case were exactly that gesture.
- Reader-POV gains **whole-book mode**. Batches of 3–4 cannot see a concept used
  in unit 1 and taught in unit 10.
- Continuity Guardian's digest cross-check now says plainly that it verifies
  *presence*, not *consistency*, and reads the claim index for the other half.
- The Proofreader delegates its mechanical half to `lint_render` / `lint_style`.
- Fixed: `phase: writing` written by the outliner (not in the vocabulary);
  `gate_critical` read from `outline/units.yaml` but absent from its template;
  `knowledge_graph.last_verified` required but absent from `project-status.yaml`;
  `every_concept_assigned_to_unit` vs `_chapter` name mismatch; `on_hold` missing
  from the unit-status vocabulary; skeptic model tier stated two ways; five
  catalogued validation surfaces with no runner specified.

## 3.0

A ground-up redesign of the writing pipeline. Earlier version history lives
with the prior skill install and is not carried forward here.

### Profiles replace the literary/technical binary
Five document profiles — `book-technical`, `book-literary`, `corporate-guide`,
`product-docs`, `scientific-paper` — each a short file in
`references/profiles/` that every agent loads at the start of its turn. The
profile owns unit naming, sequence, register and prohibitions, opening/closing
policy, citation policy, rubric deltas, Reader-POV personas, and Phase 5 build
targets. When a profile and a general reference disagree, the profile wins.

### Per-project voice, not per-skill voice
New `bible/voice-profile.md` per project: a distinctive fingerprint, banned
traits, an opening rotation, closing policy, and the project's OWN GOOD
examples derived from approved calibration passages. The skill's reference
files now carry rules and BAD examples only — shared GOOD examples produced
identical-sounding output across projects and are gone. Prose agents calibrate
against the voice profile, never against neighboring units.

### Countable rhetoric budget
A `rhet` rubric family (rhetorical questions, "not X but Y", danger lexicon,
artificial cliffhangers, emphasis density, opening rotation, template
headings). The Critic counts and reports the numbers; budgets are overridable
per project in the voice profile.

### Itemized literary rubric + moderate literary package
The literary rubric is itemized for the first time (`beats`, `character`,
`arc`, `voice`, `craft`, `reader_pov`, `continuity`). The package adds a
friction inventory, typed exposition beats, pause-vs-pausing, secondary-line
guarantees, a voice-risk quota, a conservative "preserve-don't-improve"
Humanizer, and a singularity audit every 5 approved units — no new agents.

### Adversarial verify
Optional post-Critic slot (`pipeline.adversarial_verify`): three skeptics run
in parallel, blind to the Critic's verdict, mandated to refute the unit. A
finding confirmed by ≥2 converts a PASS into a REVISE.

### Phase 5 build/export
Per-profile build targets: books → EPUB/PDF/DOCX; corporate guides →
DOCX/PDF; product-docs → a static-site-ready markdown tree; papers →
LaTeX/PDF with a bibliography generated from the claims map.

### Simplified runs log
Cost observability is one line per agent run in `project-status.yaml → runs`
(`[unit-NN, agent, tier, cycle, timestamp]`). Token accounting was specified
but never reliably populated, so it was dropped.

### Model tiers, not model IDs
`meta.yaml → models` maps roles to `creative` / `audit` tiers that default to
`inherit` (the session model). Explicit model IDs appear only in a project's
own `meta.yaml`, and only for cost control — never in skill files.
