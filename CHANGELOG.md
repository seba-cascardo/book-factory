# Changelog

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
