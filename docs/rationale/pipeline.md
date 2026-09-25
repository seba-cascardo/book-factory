# Rationale — pipeline, rubric, nonfiction agents

Why the rules in `SKILL.md`, `references/pipeline.md`, `references/rubric*.md`
and the nonfiction agent files are what they are. **Agents do not load this
file**: rules live in the agent files, history lives here. Sources: the
v2.x–v3.3 project postmortems and `REVIEW-v3.3-integral.md` (2026-09-25).
Measurements are from real projects unless marked otherwise; most come from a
single technical book (N=1), which is exactly why they are no longer repeated
inside the rules.

## computed-verdict

A prose verdict fails silently: a tired model at the end of a long context
skips a check, and the human reading a confident summary cannot see what was
checked. The scorecard makes each check a row with evidence and the verdict a
function of the rows. Two copies of a threshold rule drift, so the computation
lives only in `references/rubric.md` — v3.3's `critic.md` restated it and
pointed at a section that did not exist.

## per-unit-gate-saturation

On the reference technical book the per-unit gate passed 31 of 32 chapters;
about 170 confirmed errors surfaced afterwards. The Critic certified an invented
function (`GroupConcat()`) as "real, current release" from memory. The gate was
useful as a checklist and useless as a discriminator. Two responses in v3.4:
counts and identifiers move to scripts (the Critic copies, never judges, what a
machine can count), and review independence becomes an execution requirement
rather than a description.

## isolation

v3.3 never said whether agents ran as subagents or were acted out by the
orchestrator in its own context ("load the agent's file fresh" suggested the
latter). A "cold read" by a context that already loaded the outline, the bible
and the critique is not cold, and a reviewer that wrote the text grades itself.
Observed: a literary Reader-POV declared the prose "not AI prose" and the
Critic used that as independent confirmation; in another project agents
returned `null`, one Critic gated without `coherence.md`, another against a
`humanized.md` that did not exist. Hence the isolation table, `humanized.clean.md`
(the cold reader must not see `<!-- VOICE-RISK -->` or `<!-- EDITOR -->` notes
of intent), and the `pipeline_step.py check|done` brackets that refuse to
dispatch on missing inputs or accept empty outputs.

## counted-by-script

The rubric promised "counted, not felt" and the LLM did the counting, from
English lists "plus target-language equivalents" it re-invented each run — so
the same unit produced different scorecards, and a Spanish chapter could pass
`rhet-2` with three "No es X, es Y". Lists now live in
`scripts/lexicons/<lang>.yaml`; `count_rhet.py` counts, and the Critic records a
disagreement in Observations without overriding the number. Spanish dialogue
rayas are punctuation: `lint_style` once flagged 1,489 of them as em-dashes in
one novel.

## omission

Seven of ten intra-unit defects on the reference book had one shape: a unit
states a rule and violates it in its own example a few lines later — hence
`code-4`. Run blind against nine human-confirmed defects, a rule-vs-instance
lens caught 6 of 6 contradictions and 0 of 2 omissions (an example applying a
pattern while silent about the precondition its rule made mandatory).
Inverting the default for omission ("when in doubt, report") moved recall from
6/9 to 8/9 with no new false positives. Omission is the costlier defect: the
reader copies the example, loses the condition, and gets no error back.

## adversarial

A calibrated gate normalizes the voice it has been reading; by unit 9 a
deviation it would have flagged in unit 2 reads as "how this project sounds".
Fresh agents told a unit was suspect, blind to the verdict, twice caught
register violations the Critic had passed. The default moved from `off` to
`gate_critical` after six polish findings on a finished book had to be
downgraded by hand (one claimed a function was "never taught" when the book
explains it); a fix pass acting on a wrong finding once introduced a factual
error into correct text.

v3.3 confirmed a finding only when ≥2 skeptics flagged it, but the three lenses
are disjoint by design, so almost nothing could be confirmed; in literary the
grounding lens had no inputs at all. v3.4 adds the refutation pass (a fresh
verifier mandated to refute a single-lens finding; a second model when
available — the independence that worked in practice was often another model)
and turns the literary Skeptic B into continuity and facts.

## reasoning-is-not-verification

The first time eight checks from a book verified only "by reviewer reasoning"
ran against the real engine, the results contradicted the reviewer's paper
conclusions. A malformed expression returns zero rows, which reads like a
correct query over empty data. One book shipped 3,200 lines of code verified
only by reasoning. Hence the `executable` flag, the waiver-plus-plan
requirement at MG-6, and number provenance: a number with no source or
producing artifact is a claim nobody checked.

## preflight

A paragraph with `---` under it prints as an H2; it shipped in a book that had
passed four technical audits, because it reads perfectly in the source. Until
v3.1 only `product-docs` had a build preflight; every other profile sent
`manuscript.md` — pipeline handoff comments included — straight to pandoc.
`check_story.py --manuscript` joins the preflight in v3.4 so a novel cannot be
built with arcs unresolved or the ending missing.

## three-months

A project sat at "publish-ready" for three months with three configured checks
that had never run, because running them was nobody's queued action; when
forced, they found six blockers, one of them a paragraph that printed as a
heading. The same project had disabled the batch polish pass, so in `fast` mode
the book was never read as a reader. Hence: Phase 4.5 fires automatically from
archiving, the last unit never reports "done", and disabling a check requires a
waiver.

## fix-regressions

Three incomplete fixes in one project — the longest survived seventeen days
and a full audit — because nobody knew the edited passage had siblings
(`validate_claim_index.py` now prints them). Another audit found a fix pass that
regressed four passages while reporting 98% done. v3.4 adds fix-then-verify:
every accepted fix batch goes through a Technical Reviewer pass limited to the
changed spans, plus the claim index, before it counts as closed.

## anchor-edits

The v3.3 polish pass asked the Humanizer for a unified diff. Models produce
broken hunks, and a diff that half-applies is worse than none. Edits are now
`{unit, find, replace, rule}` records applied by `pipeline_step.py
apply-edits`, which fails the whole batch if any `find` does not match exactly
once.

## loop-semantics

v3.3 named a loopback's target but not the artifact it works on nor what
re-runs after it; the nonfiction Writer, Editor and Humanizer had no
instruction to read `critique.md` on a loop, so each session improvised. Worse,
literary comprehension and pacing failures routed to "Reader-POV + Humanizer",
whose contract forbade rewriting reader-flagged beats and capped it at 3% — a
loop with no exit that burned the retry budget. v3.4 defines re-entry per
target, worklists for every target, snapshots, and routes by what can actually
fix the problem (clarity → Humanizer in nonfiction; comprehension → Writer and
pacing → Editor in fiction; Humanizer over budget → Writer).

## plateau

A cap counts attempts, not progress. Two cycles that fail the same rows are
already evidence the loop is not converging (autonovel's anti-oscillation rule;
CritiCS's one-critique-per-round). The plateau rule stops at the first cycle
that resolves nothing and hands the human the packet while budget remains.

## critic-protocol

"Most important problem" before scoring follows *Help Me Write a Story* and
CritiCS (a leader picks one critique per round instead of applying all
feedback): a checklist scored first anchors the reviewer on what the checklist
asks. Praise only with a quoted line: unanchored praise was how one Critic
licensed a tic ("deliberate rhythm") because it matched a calibration passage.

## runs-log

Per-call token accounting was specified in v2 and never reliably populated — a
log that looked like observability and was fiction. The one-line log survived,
but inside `project-status.yaml` it grew to 1,971 lines in one project and a
stale `deferred_agents` entry misled the session that wrote the postmortem.
`runs.tsv` is written by `pipeline_step.py done` only.

## proofreader-before-human

The Proofreader used to edit `final/` after approval, without showing a diff:
the human approved one text and another shipped. It now runs before the human,
and its changed sentences are in the packet.

## voice-samples

Digests carried a "voice calibration sample" that the Writer read every turn —
reintroducing GOOD examples from neighbouring units, which the skill forbids
because models imitate examples more than rules. Removed in v3.4. For the same
reason GOOD examples in the voice profile should derive from human-written
calibration passages: see `docs/rationale/literary.md#calibration-contamination`.

## qlik-pack

The v3.1–3.3 gate and several agent files were built from one book's
postmortem (Qlik, English). Domain surfaces (`qlik_*`) and Qlik examples inside
general files anchored every book to that book's failure profile. They moved
to `references/surfaces/qlik.md`, an optional pack.

## reader-testing · number-provenance · diataxis

Reader testing with a clean subagent that answers predicted questions from the
text only comes from Anthropic's doc-coauthoring practice; number provenance
from data-to-paper (every number traces to the code that produced it);
Diátaxis quadrant purity from the Diátaxis framework and its agent skill. All
three add a check where the profile had none that bit against something
external.

## freshness

The same review showed the brackets checked existence, not recency: a critique
from cycle 1 satisfied `done critic` in cycle 2, a tracker untouched by CG
Mode B passed, a Writer "REVISE" copied the Humanizer's over-budget rewrite
back into `draft.md` and so erased the violation, and a Critic header could
say PASS over rows that computed REVISE. Dispatch records, snapshot-per-reason
loop records and the recomputed verdict make each of those a refusal instead
of a judgement call.
