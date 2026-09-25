# Rationale — the manuscript gate and its scripts

Why Phase 4.5 and the deterministic scripts are shaped the way they are. Agents
and scripts do not load this file; they keep the rule and, at most, a
`Why: docs/rationale/gate.md#<anchor>` pointer. Most numbers come from one
reference book (18 chapters, ~156k words, technical, English) and from the v3.3
integral review (`REVIEW-v3.3-integral.md` §5.2–5.3). N=1: treat them as the
reason a rule exists, not as a law about every book.

## origin

An audit of the reference book found eight blocking defects after the per-unit
pipeline had passed every chapter. Six of the eight were structurally invisible
to a per-unit gate: they lived between units, or between layers inside one unit
(prose against code, text against exercise, source against rendered output). A
per-unit reviewer sees one side of a cross-unit contradiction and approves it,
correctly. Hence a gate whose unit of analysis is the book.

The book-level passes that did find them were deferred agents that "existed and
were configured" and ran only when someone forced them months later. The v3.3
review corrected half of that story: the Reader-POV batches had in fact run; the
problem was efficacy, not triggering. The automatic trigger stays because it is
cheap; the gate's value comes from its independence and its book-level unit.

## render

A paragraph with a `---` directly under it printed as an H2 in the PDF after four
technical audits: every reviewer read the paragraph, none looked at the rendered
page. The whole MG-5 class is like that — trivially detectable, invisible to a
prose reader. v3.4 added the literary hazards found on a Spanish novel: `1999.`
at the start of a paragraph renders as an ordered list; a raya line with no blank
line above it is swallowed into the narration paragraph. Comments inside fences
used to be parsed, so every Mermaid `-->` produced an unwaivable major (G5).

## coverage

v3.1's verdict was `f(findings)`. Nothing in it knew how many candidates were
never looked at, so a book could reach `complete` having audited 30 of 474
candidate rules, and "two consecutive quiet rounds" held by construction: rounds
2+ re-audited the same 30. The quota was documented as a cost dial and behaved
as a ceiling. v3.2 made coverage a term of the verdict; v3.3 split it into
breadth and depth with two waivers and two signatures.

v3.4 collapses that machinery (review §6, P3): one manifest keyed by content
(`subjects.json`: pending | audited@hash | sampled@hash), one waiver signed over
the exact pending and sampled sets, and `PASS-SAMPLED` merged into
`PASS-PARTIAL` (the report still separates never-opened from partly-read). The
two definitions that do not move: the denominator is post-filter (noise inflates
the percentage in the comfortable direction), and a subject with no findings
file was not audited.

## depth

On the reference book 221 of 454 rules reached more instances than one agent run
can judge. With `tractable` derived purely from `len(instances)`, `sampled == 0`
could never hold and PASS was unreachable by construction — a criterion nobody
can satisfy decays like a percentage floor nobody defends. The ladder
(`bible/rule-probes-tuned.yaml`, `home_cap` on concept probes) exists so a
sampled subject closes by work; the waiver exists for subjects that really are
that wide. Narrowing is a claim about scope, never a way to make a number
smaller. v3.4 also keeps a narrowed rule in the denominator whatever its instance
count: before, narrowing below `--min-instances` made the subject vanish.

## strata

A ranker that added +3.0 for "crosses units" onto a base scale of ~1–4 did not
weight that property, it stratified on it. With 92% of candidates cross-unit, a
40-slot quota emitted 40 cross-unit rules and zero intra-unit ones — and
intra-unit was 7 of 10 real defects. 74% of dossiers were saturated that way
before anyone noticed, because the output still looked full. Hence one quota per
failure mode, in `bookkit/selection.py`.

## calibration

A first gate verified its calibration pairs against the candidate list while
emission capped output independently: the pairs ranked 199/205 and 153/211,
present in the list and absent from the dossier, and the gate said PASS. Hence
one selection function shared by emission and every check on emission. Extended
from two convenient pairs to eight confirmed ones, real recall was 5/8 rules and
3/11 pairs: two data points cannot show a bias. Gaps found by calibration stay in
the selftest, marked and failing.

## similarity

Eight-word shingles with Jaccard ≥ 0.8 found zero clusters on real prose: the
twin passages of a known incomplete fix scored 0.037, 0.000 and 0.000, because a
well-written book rephrases. Jaccard over content terms separates: real twins
0.111–0.359, random pairs median 0.038, p95 0.103, p99 0.154. The weakest twin
sits between p95 and p99, hence the low threshold (0.12) and the pair as a
signal, never a verdict: a false positive costs one pair to read, a false
negative loses the defect.

## omission

Run blind against nine human-confirmed defects, a rule-vs-instance lens caught 6
of 6 contradictions and 0 of 2 omissions. Both misses were a statement and a
silence: a `Peek(…, -1)` watermark that assumes an ascending file, prescribed
five hundred lines later without the assumption; `LOAD Max(OrderDate) … (qvd)`
after a rule that any function on a loaded field breaks the optimized path.
Inverting the default for omissions (in doubt, report D9) moved recall from 6/9
to 8/9 with no new false positive. `violation_kind` is how a run shows it learned
the class rather than the two examples.

## passes

The same lens run twice over the same six rules found sites in the second run
that the first missed, and one finding existed in only one run. The variance is
in the sampling, not the prompt, so no tuning removes it; two passes and a union
do. A finding only one pass produced is the cheapest false-positive signal.
v3.4 makes `passes_per_subject` a coverage term: a subject with one pass of two
is partly read.

## suppressors

Six findings of the reference audit had to be downgraded by hand after
verification: one claimed a function was "never taught" when the book explains
it, another flagged a scope contradiction the chapter announces in as many words,
and a "10× vs 100×" contradiction was two different baselines (made and reverted
the same day). The five suppressors catch most of that before a human sees it.

## positives

N1, N2 and D7a were 45% of all findings in the reference audit and the "verified
correct" section held 81 clusters. A review that records only defects loses its
positive knowledge when the report is filed: on 2026-07-29 a fix pass "corrected"
three settled items and introduced a factual error into correct text (the 100×
figure is against the database, not against standard mode). Reverted the same
day, only because someone remembered. Hence `do_not_touch`, `verified_against`,
and the accepted-items list in GROUNDING.md.

## mg4

The whole-book read's question is "is it enough?", not "is it right?". On the
reference book it found that the security chapter taught the reader to write the
security table but never to deploy or verify it; six technical passes had
validated every sentence of that chapter. It also sees exposition-order defects
no batch of three units can hold (used in unit 1, taught in unit 10).

## mg6

The first time eight checks from the reference book were run on a real engine,
the results contradicted what the reviewer had concluded on paper. A malformed
query returns zero rows instead of an error, which reads like a correct query over
empty data. The book had shipped 3,200 lines of code verified only by reasoning;
one paste-once setup covered about 80% of 56 checks. v3.4: a waiver with no plan
is a promise, so an MG-6 waiver counts only when it names a plan that exists.
Fix round 2: a `runner` string ("qlik reload (never run)") is a description,
not a run — an executable surface is satisfied only by an `evidence` file of
the runner's output, or by that waiver.

## mg7

Closing one defect — a chapter collapsing the three positions of a set modifier
into two slots, found only after four independent passes — required inverting a
gate assertion by hand and adding content pins to a linter. Nothing else stopped
the wrong model from returning. The corrected text quotes the wrong form to teach
against it ("…That is the one that looks like the fix and is not."), so a pin on
the expression fires on the fix forever; pin the conceptual frame instead.

## anchors

During one day of fixes the extractor's references broke three times; two of the
three were caused by ADDING a section. Everything below an insertion shifts, and
a check that shouts when nothing happened gets switched off. Anchors distinguish
"it moved" (bookkeeping, `--heal`) from "they changed it" (re-read). v3.4 matches
a whole code block as one block and retries without markdown markup, which
removed false EDITED results.

## claim-index

A fix landed in one passage and left its twin, seventeen lines away in the same
chapter, asserting the opposite for seventeen days through a full audit. Nobody
knew the passage had siblings. Keying by fingerprint rather than line keeps the
signal-to-noise ratio: a line key makes every insertion look like an edit. v3.4
fingerprints keep code spans verbatim: `Peek(v,-1)` → `Peek(v,1)` is the most
common fix in a technical book and used to be invisible (G9).

## verification-plan

A plan that must be executed in full is executed not at all; a short path of five
or six checks settling open criticals gets run. An empty result slot is
ambiguous at 20% coverage; `NOT RUN` is not. A hurried fix on an incomplete list
once forced a whole pass to be reverted — hence "record surprises, finish the
block, then decide". v3.4: the gate used to regenerate PLAN.md every run and
delete the results written into it (G8); it now only appends.

## lint-style

Replacing code spans with a space manufactured 2,224 false double-space hits out
of 2,389 on the first calibration run. 111 of 111 first-pass thousands hits were
years. v3.4: 24/24 Spanish dialogue rayas were being reported as em-dashes
(1,489 in a long novel) — the em-dash rule is English-only and follows
`conventions.dash_style`; Spanish 4-digit numbers take no separator (RAE).

## cost

Measured on the reference book, one lens run costs 170–230k tokens and 10–16
minutes; `top_rules: 30` × 2 passes ≈ 12M tokens for MG-2 alone. The cost sits
next to the dial in `meta.yaml` so it is decided, not discovered.

## v34

The v3.3 review found the gate converging with an open critical and even with
verdict BLOCKED (G1), counting invocations instead of rounds so three
`--verdict-only` runs converged (G2), forgetting open findings between rounds
(G3), and swallowing tool failures so a cp1252 file produced "MG-5: 0 critical"
and exit 0 (G4). The redesign answers each with a structure rather than a
patch: a cumulative store recomputed from every round's files (open findings
cannot be forgotten), rounds as distinct swept round numbers (re-running cannot
add rounds), a verdict that must be acceptable before convergence is even asked,
and tool outputs deleted before each sweep so a crash can only read as ERROR.

Decisions taken where the contract was silent:

- A blocking finding fixed within the round it was found still makes that round
  not quiet; a refuted one never counted.
- A critical cannot be `accepted-risk`: it is fixed or refuted.
- Declarations are not evidence (fix round 2): a deterministic finding is never
  `fixed` or `refuted` by hand in any profile; an agent `fixed` needs the text it
  points at to have changed (a hash recorded with the finding); `refuted` and
  `accepted-risk` need a 20-character note that is not a placeholder; the store
  only grows, so a truncated `findings.jsonl` is an ERROR; one quiet round is
  clamped to two.
- MG-3/MG-4/MG-C subjects hash the whole manuscript, so any edit re-queues the
  whole-book read; that is the price of never having a read "valid forever".
- The gate rebuilds `manuscript.md` in every sweep, so MG-4 reads what ships.
- Re-preparing a round that already has findings is refused: it would re-hash
  the subjects under the auditors' feet.
- English claim scoring keeps its calibrated regexes; other languages score with
  their pack, and with no pack the gate says so instead of reporting "0 = clean".
