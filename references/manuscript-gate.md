# Phase 4.5 — The manuscript gate

Everything before this phase gates one unit at a time. That is the right unit for
drafting and the wrong unit for finishing, and the gap is not small: in the audit
that produced this design, six of eight blocking defects were structurally
invisible to a per-unit gate. They lived *between* units, or *between layers*
inside one unit — prose against code, text against exercise, source against
rendered output.

A per-unit reviewer cannot find a cross-unit contradiction. It sees one side of
it and approves that side, correctly. So this phase changes the unit of analysis
to the book.

**The gate is not an audit.** It computes a verdict, it blocks, and it iterates
until it converges. Phase 4's continuity audit and polish pass are advisory and
stay advisory; this is the thing that decides whether the book is done.

---

## Automatic trigger

**The gate is not requested. It fires.**

When the last unit reaches `archived`, the orchestrator does **not** report the
book finished. It writes `phase: manuscript-gate` to `project-status.yaml` and
starts Round 1.

This is the direct correction of the failure mode this design comes from: the
deferred agents existed, they were configured, and they never ran until someone
forced them three months later — at which point they found six blockers,
including a paragraph that printed as a heading. A check that depends on someone
remembering to ask for it is a check that does not exist.

Hold this as an invariant alongside the Phase 3 ones:

> **No path leads from the last approved unit to `complete` without passing
> through Phase 4.5.**

---

## The seven checks

| id | Question | Engine | Blocking |
|---|---|---|---|
| **MG-1** Concept audit | For each concept touching ≥2 units, do all its claims agree? | script + auditor agents | yes |
| **MG-2** Rule vs instances | Does the book's own code and examples obey the rules its prose states? | script + auditor agent | yes |
| **MG-3** Exercise vs delivered content | Was everything an exercise demands actually taught, and does the promised solution exist? | auditor agent | yes |
| **MG-4** Whole-book read | Reading it end to end as the target reader — **is it enough?** | Reader-POV agent | yes |
| **MG-5** Render lint | Does the source render as the author meant it to? | `scripts/lint_render.py` | yes (critical) |
| **MG-6** Executable code | Did the code run, or is the debt declared? | `scripts/manuscript_gate.py` + waivers | yes |

| **MG-7** Fixed-defect regression | Did a defect that was already fixed come back? | `scripts/check_fixed_defects.py` | yes (critical) |

MG-5, MG-6 and MG-7 are deterministic, cost seconds, and always run over the
whole book. MG-1 through MG-4 cost agent runs, which is why they carry a quota,
why rounds after the first are incremental (see § The convergence loop), and why
**how much of them ran is a term of the verdict** (see § Coverage).

### MG-1 — Concept audit

`scripts/build_concept_dossier.py` gathers, for one concept, every prose passage
across the whole book that makes a claim about it, into one file. Auditor agents
then read those passages **together**. See `references/agents/concept-auditor.md`
for the three lenses and `references/claim-index.md` for how dossiers are built
and probes tuned.

Run it for every concept whose `text_span` covers two or more units. A concept
confined to one unit cannot carry a cross-unit contradiction, and auditing it
here duplicates work the Critic already did.

### MG-2 — Rule vs instances

The dominant intra-unit defect, measured: **seven of ten** were the same gesture
— the unit states a rule in prose and violates it in its own example, code block
or bullet, a few lines later. Nothing in the per-unit pipeline crosses the prose
layer against the code layer, so nothing catches it.

`scripts/extract_rule_candidates.py` extracts rule-shaped passages and every code
block and example in the book; `references/agents/rule-auditor.md` judges each
rule against **all** its instances, across units.

### MG-3 — Exercise vs delivered content

Per exercise: everything it demands was taught in this unit or earlier, and the
solution it promises actually exists in the text. `outline-4` checks the first
half per unit and is not enough — it runs while the later units that would have
taught the prerequisite do not exist yet, and it never checks the second half at
all. Skip this check for profiles with no exercises (`product-docs`,
`scientific-paper`).

### MG-4 — Whole-book read

Reader-POV reads the entire manuscript continuously, in the profile's persona.
See `references/agents/reader-pov.md` § Whole-book mode.

Its central question is not "is this right?" — five other checks ask that — but
**"is this enough?"** In the audit this comes from, that question revealed that
the security chapter taught the reader to write the security table but never to
deploy or verify it. Six prior technical passes had missed it, because every one
of them verified what was written and none asked whether it sufficed.

It also catches exposition-order defects the batch polish pass cannot see: a
concept used in unit 1 and taught in unit 10 is nine units apart, and no batch of
three or four ever holds both ends.

### MG-5 — Render lint

`scripts/lint_render.py` over `final/` and `manuscript.md`. Deterministic:
accidental Setext headings, unbalanced fences, unbalanced HTML comments, ragged
tables, broken lists, heading-level jumps, and pipeline handoff comments that
reached a shipped file.

Any `critical` here blocks. The class is cheap, mechanical, and completely
invisible to a prose reviewer — a paragraph with a `---` under it reads perfectly
in the source and prints as an H2.

### MG-6 — Checkable against reality

Two things, and the second is the general one.

**Executable code.** For every declared validation surface whose content is
executable: either the runner ran and its output is on record, or there is a
waiver *and* a verification plan. Reasoning about code against documentation is
not verification — the first time eight checks from one such book were run on a
real engine, the results contradicted what the reviewer had concluded on paper.

**Everything else the pipeline could not settle.** Code is the obvious case, not
the only one. Across MG-1 to MG-4 the auditors emit `deferred` items: questions
they could not answer from what they had. Each one declares what *would* answer
it, and the five values that name something reality can supply —
`runner`, `live-system`, `measurement`, `person`, `document-of-record` — become
entries in the verification plan. `human-decision` is the exception: no
observation settles a choice, so it goes to the human packet instead.

`scripts/manuscript_gate.py` writes the skeleton automatically from those items.
See `references/verification-plan.md` and `references/validation-surface.md`.

The principle is worth stating plainly, because it is easy to let slide:
**unresolved here is usually not unknowable, just unknown in this session.** A
claim the pipeline could not establish has three honest endings — verify it,
soften it, or write down the check that would settle it and record the debt. What
it must not do is get asserted anyway because verifying it was inconvenient.

Not every project has a reality to check against. A novel does not; a
philosophical essay's claims are not that kind of claim. The trigger is narrow:
*the pipeline could not settle it, and a defined observation would.*

### MG-7 — A fixed defect must not come back

`bible/do-not-touch.md` protects text that is **correct**. `scripts/selftest.py`
tests the **scripts**. Until v3.2 nothing asserted *"this defective formulation
must not return"*.

Evidence: closing one defect on the reference book — a chapter collapsing the
three positions of a set modifier into two slots, which took **four independent
passes** to detect — required inverting a gate assertion by hand and adding
content pins to a linter, because nothing otherwise stopped the wrong mental
model from reappearing in a later edit.

`bible/fixed-defects.yaml` records, per fixed defect, patterns that may not
reappear. `scripts/check_fixed_defects.py` runs it in the deterministic sweep,
whole book, every round. A reappearance defaults to `critical`: a defect that
cost four passes to find does not get to re-enter quietly.

**Pin the claim, not the code.** The text that corrects a defect usually quotes
the defective form in order to teach against it. The reference fix reads,
verbatim:

> *"…with the set inside the outer aggregation's own parens — only the outer sees
> it… That is the one that looks like the fix and is not."*

A literal pin on that expression fires on the fix itself, every round, forever —
and a check that shouts when nothing happened is a check somebody switches off.
The right pin is the conceptual frame (`two slots`, `the outer aggregation's
reach`), which can only reappear if somebody reintroduced the wrong model. The
`allow_in` anchors are the escape hatch for the cases where claim and
counter-example genuinely share wording, not a substitute for pinning well.

**Lifecycle.** An entry is born when a `critical` or `major` finding is marked
resolved. The gate **proposes** it in the human packet; the human writes and
accepts it, because getting the pattern right needs the judgement above and a
machine that guesses produces a check that cries wolf on the fix. An entry never
expires: if the book changes version and the rule stopped applying, delete it
explicitly with a reason, the way a waiver is retired.

See `templates/fixed-defects.yaml`.

---

## Coverage — how much of the surface was actually looked at

MG-1 and MG-2 carry quotas (`top_concepts`, `top_rules`). Until v3.2 the verdict
was `f(findings)` and knew nothing about them, so a book could reach `PASS` →
`phase: complete` having audited **30 of 474 candidate rules** — and the "two
consecutive quiet rounds" criterion was satisfied *by construction*, because
rounds 2+ re-audited the same 30 and could not produce anything new. The quota
was documented as a cost dial and behaved as a permanent ceiling.

Three places already told the truth about this at dossier level — the rule
auditor's *"do not conclude the rule is clean"*, the findings schema's *"a
sampled run may never be reported as clean"*, the report template's copy of the
same line. The verdict did not know. Now it does.

### Two axes, and they are separate terms of the verdict

**Breadth** is `covered / eligible_candidates` — how many subjects anybody
opened. **Depth** is how many of those were judged from a SAMPLE of themselves
rather than all of them: a rule with more instances than an agent can judge in
one run (`tractable: false`), a concept dossier whose home unit was trimmed.

They are separate because they close by different work:

| | closes by | who does it | waiver |
|---|---|---|---|
| **Breadth** | spending rounds — the emitters drain the pool automatically | nobody, it happens | `manuscript_gate.coverage` |
| **Depth** | narrowing a subject so it fits in one run | a human, it is judgement | `manuscript_gate.depth` |

Requiring both for `PASS` was v3.2's mistake, and it was the same mistake this
document warns about two sections down: **221 of 454 rules on the reference book
were over the tractability ceiling**, and `tractable` was derived purely from
`len(instances)` with no override. So `sampled == 0` could never hold however
many rounds anyone ran, `PASS` was unreachable by construction, and every project
would have ended at a standing depth waiver. A criterion nobody can satisfy
decays exactly like a percentage floor nobody defends.

### The ladder out of the depth axis

An escape hatch nobody can find is not an escape hatch. Both scripts said *"the
fix is a hand-written probe"* while `bootstrap_probes.py` and
`concept-probes-tuned.yaml` existed only for concepts — the instruction pointed
at something that did not exist for rules.

- **MG-2** — `bible/rule-probes-tuned.yaml`. Narrow a rule's `key_terms`, add
  `require_terms`, scope it to `scope_units` / `scope_heading`, exclude
  instances by pattern, or `split` one broad rule into scoped sub-rules. See
  `templates/rule-probes-tuned.yaml`.
- **MG-1** — `home_cap` on the probe in `bible/concept-probes-tuned.yaml`, or a
  tighter `include` / `exclude`.

The gate writes the worklist: every intractable rule, ranked by instance count,
with a commented stub each, to `round-N/rule-probes-proposed.yaml`. Starting from
a blank file is how an affordance goes unused.

**Narrowing is a claim about a subject's SCOPE, and it is auditable.** If a rule
genuinely governs 87 code blocks across nine chapters, do not shrink it to make a
number go down — leave it sampled and waive the depth. Waiving is the honest
outcome; a narrowing written to reach `PASS` is a lie the gate then repeats back
as a clean bill of health.

Two definitions are fixed and do not move:

- **`eligible_candidates` is post-filter, not raw.** It counts what survives
  `--min-instances`, `--df-ceiling`, the imperative/voice discard and the
  `--min-units` span floor. Noise in the denominator inflates the percentage, and
  it inflates in the comfortable direction.
- **A subject with no findings file was not audited.** An auditor that ran and
  found nothing still writes a file with an empty `findings` array; that file is
  the only evidence anybody looked. Counting a dispatched-but-unfiled subject as
  covered would make the whole measurement decorative.

### Where it lives

```
reviews/manuscript-gate-<date>/
├── audited.yaml                    # CUMULATIVE ledger: subject id + fingerprint
└── round-N/
    ├── coverage-MG-1.json          # written by build_concept_dossier.py
    ├── coverage-MG-2.json          # written by extract_rule_candidates.py
    ├── rule-probes-proposed.yaml   # ranked worklist of rules that can only be
    │                               # SAMPLED — the ladder out of PASS-SAMPLED
    └── coverage-summary.md         # COMPUTED report header + What-ran table
```

`coverage-summary.md` is pasted into `REPORT.md`. It is generated rather than
written because v3.1's Sampling line was prose an agent filled in, which made the
honest number depend on the agent remembering — the exact mechanism the waivers
section exists to eliminate.

---

## The finding taxonomy

Every finding carries a `relation`. Apply this tree **in order** and **stop at the
first that applies**. Order matters: it is what keeps two auditors from filing the
same passage pair under two different codes.

1. Same surface term, **different referents**? → **D4** (homonym). Different terms,
   same referent? → **D4a** (synonym). STOP.
2. Propositions jointly unsatisfiable **in the same scope**? → if one is the hedged
   version of the other, **D5** (asymmetry); otherwise **D1** (contradiction). STOP.
3. Same scope, same polarity, **different quantities**? → do all sites name their
   baseline? No: **D7**. Yes: **D7a** (NOT a defect). STOP.
4. **Different scopes**? → does transplanting P1 into P2's scope break, with nothing
   warning the reader? **D8** (latent tension). Otherwise **N2** (NOT a defect). STOP.
5. Related passages where **one has blame from a fix run and the other does not**?
   → **D2** (incomplete fix). STOP.
6. One is a **rule in prose** and the other an **instance in code or an example**,
   and the instance **contradicts** the rule? → **D6** (example divergence),
   `violation_kind: contradiction`. STOP.
7. Does the instance **apply the pattern while staying silent about a
   precondition the rule declares mandatory**? → **D9** (omitted precondition),
   `violation_kind: omission`. STOP. Read § Omission below before deciding this
   one — it is the class every reviewer misses.
8. Nothing applies → **N1** (consistent restatement, NOT a defect).

**D3** (gap) is emitted alone, with no pair: no passage is false, but the *union*
of all of them fails to cover a behavior the sources document and the reader will
walk straight into. Only the `source` lens may emit D3.

### Omission — the class reviewers are blind to

This step is late in the tree and first in importance. Measured: run blind
against nine human-confirmed defects, a rule-vs-instance lens caught **6 of 6
contradictions and 0 of 2 omissions**. Not noise — a shape.

Both misses looked the same:

> A rule states that a watermark read via `Peek(…, -1)` assumes the file is
> sorted ascending. Five hundred lines later, another passage prescribes the same
> `Peek` and **never mentions the assumption**.

> A rule states that any function applied to a loaded field breaks the optimized
> path. A later passage writes `LOAD Max(OrderDate) … (qvd)` and **never says
> this one already fell back to a standard load**.

Neither *contradicts* anything. Both **apply the pattern with the precondition
left out**. There are not two opposed statements to compare — there is a
statement and a silence, and a reviewer trained on "does this contradict that?"
looks straight past it.

It is also the most expensive defect a technical book can ship. A reader who
copies the instance gets the recipe without the condition that makes it correct,
and **receives no error**.

**So the default inverts here.** Everywhere else in this tree, doubt resolves
toward "not a defect" — between `D6` and `N2`, choose `N2`. For omission it is
the opposite: **when in doubt, report the omission.** Two different questions,
two different defaults, and conflating them is what produced the blindness.

The same fix moved recall from 6/9 to 8/9 with no new false positives — the one
instance that declared its exception legitimately stayed correctly filed as a
non-defect.

Every finding on a rule↔instance pair carries `violation_kind`
(`contradiction` | `omission`). It is not bookkeeping: it is how you check that a
lens actually generalized rather than memorizing the two examples above. A run
that only ever reports omissions matching these worked cases has learned the
examples, not the class.

**This is not only MG-2's contract.** Any agent comparing two passages needs it —
Technical Reviewer, Continuity Guardian, Critic. The question that matters is not
"does this passage say something false?" but **"does this passage stay silent
about something another passage declared mandatory?"**

**`N1`, `N2` and `D7a` are first-class results and MUST be emitted.** Without
them, "verified correct, do not touch" has nowhere to live — and that exact gap
is what let a later fix pass introduce a factual error into text that was already
right. In the reference audit these accounted for 45% of all findings and were
worth as much as the defects.

---

## False-positive suppressors — apply BEFORE emitting

Review agents inflate. Measured on the reference case: six findings had to be
downgraded by hand after verification, one of which claimed a function was "never
taught" when the book explains it, and another flagged a scope contradiction the
chapter announces in as many words. These five rules catch most of it before it
reaches a human.

| Trap | Rule |
|---|---|
| **Scope collapse** | Every passage carries its `heading_path`. You may not emit **D1** without stating `scope_1` and `scope_2` in words. And if you cannot name two different scopes, you may not file **N2** either — pick one and justify it. |
| **Baseline blindness** | Before emitting **D7**, fill `baseline_1` and `baseline_2`. "10× against X" and "100× against Y" have different baselines: that is **D7a**, not a contradiction. This exact error was made and reverted the same day. |
| **Progressive disclosure** | Unit 1 deliberately simplifies what unit 6 refines — that is the book's design. If P1's unit is *earlier* than the concept's `home`, the most you may emit is **D5**, never D1, and you must argue the simplification is *actionably* false, not merely incomplete. |
| **Summary bullets** | A passage flagged `[summary]` can only ever be **P2** in a pair, never P1, and only yields D5/D7 — never D1. A recap restates; it does not establish. |
| **Deliberately divergent example** | A **D6** must state which of the two forms the book itself prefers. If neither passage says, `fix_scope` is `add_crossref`, not an edit. |

Two more that are not about pairs:

- **Voice is not a defect.** Rhetorical absolutes, second person, dry humor and
  short sentences are the project's signed voice (`bible/voice-profile.md`). An
  absolute inside an imperative or a piece of advice is voice; an absolute about
  how the system behaves is a claim and is auditable. Auditors that were not told
  this spend their budget rewriting the book's register.
- **Search the whole unit, always.** Before reporting, grep the unit for the
  topic — not just the cited line. Previous fixes usually landed in a neighbouring
  paragraph, and if one did, there is no defect. `searched_whole_chapter: true`
  is a claim you are making; do not make it falsely.

---

## Two passes, then union

**Run every MG-1 and MG-2 auditor twice on the same subject, with the same
prompt, and merge the findings.** One pass is not enough, and this is measured
rather than assumed: the same lens run twice over the same six rules found sites
in round two that round one missed, and one finding came back `D6` in one round
and did not exist in the other. Agreement is high; it is not total.

Two passes cost one extra agent run per subject and recover findings that no
amount of prompt tuning gets from a single pass, because the variance is in the
sampling, not in the instructions.

Merge by (relation, p1 location, p2 location). And keep the round in the record,
because the disagreement is itself a signal:

> **A finding that appeared in only one of the two rounds is the first candidate
> for a false positive.** Free triage — no extra agent, no extra pass — and it
> tells the adversarial verifier where to look hardest.

Mark those `single_round: true` and sort them to the front of the verification
queue. Findings that both rounds produced independently are the ones to trust
before verification even runs.

## Adversarial verification

Every `critical` and `major` finding from MG-1 through MG-4 passes through a
verifier **whose mandate is to refute it**, before it reaches the human packet.
`references/adversarial-verify.md` § Manuscript-gate mode. Start with the
`single_round: true` findings.

The verifier must read the complete section around each passage — not the cited
line — and fill `searched_whole_chapter` and `other_occurrences`. Between
`CONFIRMED` and `UNVERIFIED`, it chooses `UNVERIFIED`: only decisive evidence
confirms.

Findings verified `REFUTED` do not disappear. They are recorded, and the concept
gets `do_not_touch: true` plus the counter-evidence in `bible/claim-index.yaml`.
That is what stops the next round from rediscovering them.

---

## Verdict

Computed, not chosen — same principle as the Critic's scorecard:

```
blocking = a critical finding is unresolved and not waived
major_open = a major finding is unresolved and not waived
breadth_complete = for EVERY enabled semantic check: covered == eligible_candidates
depth_complete   = for EVERY enabled semantic check: sampled == 0

if blocking:               BLOCKED
elif major_open:           NEEDS-REVISION
elif not breadth_complete: PASS-PARTIAL     # subjects nobody opened
elif not depth_complete:   PASS-SAMPLED     # subjects read only in part
else:                      PASS
```

Breadth outranks depth because *"nobody opened it"* is a worse state than *"we
read part of it"*, and because the two need different work from different people.

A finding is **resolved** when it was fixed and re-verified in a later round, or
rejected as not-a-defect by the human, or waived with a recorded reason.
`minor` findings never block; they consolidate into the report and the human
decides.

`BLOCKED` makes `phase: complete` unreachable. `NEEDS-REVISION` is waivable by the
human with a rationale in `project-status.yaml → waivers` — never silently.

### Why each criterion is binary and not a percentage floor

A floor like `0.80` invites arguing the number, and the day the number is
expensive it gets waived out of habit — the same decay as a hard gate on prose. A
binary criterion is not arguable. `PASS` means *"all of it was looked at, all the
way"*; the two partial states each name exactly what is short and list it.
Nobody has to defend a percentage.

The corollary, learned the expensive way in v3.2: **a binary criterion needs a
ladder.** Binary plus unreachable is not rigour, it is a gate that everyone
routes around. That is why depth is its own term with its own way out.

### What the partial states do and do not block

**They do not block the work. They block the claim.** A partially audited book is
a legitimate state; a clean bill of health over the part nobody read is not.

`phase: complete` requires `PASS`, or a waiver in `project-status.yaml → waivers`
for **each axis that is short**, carrying the exact numbers:

```yaml
waivers:
  - check: manuscript_gate.coverage          # BREADTH — should feel expensive
    reason: "18-chapter book, MG-2 quota held at 30/round by budget; three more
             rounds planned post-launch"
    debt: "444 rule candidates unaudited as of round 3"
    signature: "MG-1:40/169|MG-2:60/474|MG-3:12/12|MG-4:1/1"

  - check: manuscript_gate.depth             # DEPTH — often the honest answer
    reason: "14 rules genuinely govern the whole load-script surface"
    debt: "14 of 60 audited rules judged from a sample; listed in REPORT.md"
    signature: "MG-1:0s/40|MG-2:14s/60|MG-3:0s/12|MG-4:0s/1"
```

The gate prints both signatures; paste them. A waiver whose signature no longer
matches is reported as **stale and does not count** — a waiver that outlives its
own facts is the failure this gate spends its design budget preventing.

They are separate waivers because they are different debts. Breadth means nobody
looked, and it closes by itself if you spend rounds. Depth means the subject is
wider than one agent run, which is sometimes just true.

---

## The convergence loop

The gate iterates. One pass is not a gate, it is a report.

```
Round N
  1. Deterministic sweep, ALWAYS COMPLETE      MG-5, claim index, anchors,
                                               MG-6, MG-7
  2. Semantic sweep                            MG-1..MG-4
       Round 1: the whole book, up to the quota
       Round 2+: the propagation set, PLUS the next unaudited slice (below)
  3. Adversarial verification of every critical/major finding
  4. Report + human packet — fixes are PROPOSED, never applied
  5. Human accepts / rejects / waives each finding
  6. Accepted fixes land in final/ → validate_claim_index emits PROPAGATE
       → those siblings join round N+1's set
  7. Recompute the verdict. Not converged? Round N+1.
```

### Convergence criterion

The gate closes when **all** hold:

1. Zero unresolved `critical` and zero unresolved `major`.
2. **Two consecutive rounds with no new `critical` or `major` findings.**
3. `PASS`, or a signature-matching waiver for each coverage axis that is short.

One clean round is not evidence. Finder agents miss things, and the defect tail
is long — this is the loop-until-dry pattern, and the second round is where it
earns its cost. Configure with `manuscript_gate.rounds_without_new_to_close`
(default 2).

Criterion 3 is what keeps criterion 2 honest. **Two quiet rounds at the same
coverage are not two quiet rounds — they are one round run twice.** The round
history table in the report carries a coverage column for exactly this: it has to
grow between rows, or the loop is converging on its own blind spot.

Note what is *not* the criterion: "no issues at all". That is unreachable —
minors and cosmetics always remain — and promising it produces a gate someone
turns off. Say what is true instead: no blocking defects, and two quiet rounds.

### Incremental rounds

Round 1 audits the whole book, up to the quota. From round 2 the semantic sweep
runs over:

- passages edited since the last round,
- **their propagation set** from `bible/claim-index.yaml` — this is what
  `PROPAGATE` is for,
- concepts and rules with findings still open,
- **the next `top_rules` / `top_concepts` UNAUDITED candidates, by ranking.**

That last line is what makes the quota a cost dial instead of a ceiling. Without
it the unselected candidates fall into none of the first three categories, are
never audited, therefore never produce a finding, and "two consecutive quiet
rounds" is satisfied by construction.

The mechanism is `reviews/manuscript-gate-<date>/audited.yaml`: a cumulative
ledger keyed by subject id **and fingerprint**. The emitters skip what it already
records — those stay in the denominator, they only leave the pool — so coverage
grows monotonically and a project that wants a true `PASS` reaches it by spending
rounds, which is an explicit budget decision rather than an invisible ceiling.

The fingerprint spans everything an audit of that subject read: the rule sentence
plus its instances, all of a concept's passages. So a subject whose text was
edited since it was audited comes **back into the pool** — the same asymmetry the
claim index uses, applied to the ledger.

The deterministic sweep always runs complete. It costs seconds and it is the one
that catches collateral damage from a fix — an edit that fixed a contradiction
and broke a table.

Without incremental rounds the loop is unaffordable and gets cut to one pass,
which puts you back where you started.

### Anchors — references that survive an edit somewhere else

MEASURED, during one day of fixes on the reference book: the extractor's gate
broke **three times, and two of those were caused by ADDING a section**, not by a
defect. Everything below an insertion shifts, every line-keyed reference goes
stale at once, and the output is noise. A gate that shouts when nothing happened
gets switched off within a week.

The claim index already solved this for passages, with fingerprints. Everything
else that names a passage now carries an **anchor** — a short verbatim substring
— next to the line number:

```json
{"location": "final/ch-11.md:220",
 "anchor": "or in the outer aggregation's parens before the"}
```

Resolution, and why the second case is the one that matters:

```
1. the line resolves and the anchor is there       OK
2. the anchor is nowhere in the file               EDITED — the passage was CHANGED
3. the anchor is elsewhere, exactly once           DRIFT — it MOVED; repairable
4. the anchor matches more than once               AMBIGUOUS — lengthen it
```

A line number cannot distinguish *"it moved"* from *"they changed it"*, and those
need opposite responses: one is bookkeeping, the other means the thing the
reference protected may be gone.

`scripts/resolve_anchors.py` reports all four, runs in the deterministic sweep,
and `--heal` rewrites stale line numbers from the anchors after a fix pass —
without which keeping references true is recurring manual work and therefore does
not happen. `--heal` deliberately never touches an `EDITED` reference: repairing
one would quietly attach a verified-correct anchor to text nobody checked.

Findings already require a verbatim `quote`, so most references anchor
themselves; `bible/do-not-touch.md` entries carry an explicit `**Anchor:**` line.

### Anti-thrash: the loop's memory

Each round deduplicates against **everything seen**, not against what was
confirmed. A finding the human rejected is persisted as `N2` + `do_not_touch` in
the claim index, with the counter-evidence in `note`.

Skip this and two things happen. The rejected finding returns every round and the
gate never converges. Worse, some round eventually "fixes" it — which is exactly
the 2026-07-29 failure in the reference case, where a fix pass introduced a
factual error into correct text and had to be reverted the same day. The
auto-refutation anchor is what stops the loop from eating its own work.

### Cap and escalation

`manuscript_gate.max_rounds` (default 5). If the gate has not converged, it does
**not** keep spinning and does **not** relax the criterion. It produces a
structured escalation packet in the same shape as
`references/loopback-handoff.md`: which finding will not close, what was tried
each round, and what evidence exists on each side. The project state becomes
`blocked-on-manuscript-gate`.

A loop that does not converge is information. It usually means the disagreement
is real and the human has to make a call that no amount of auditing will make
for them.

---

## Calibrating a check, honestly

Every check here has a threshold or a quota, and every one of them was wrong on
the first try. Four rules, each of which cost a rewrite to learn:

**Measure the artifact that ships, not an intermediate list.** A first gate
verified that its calibration pairs appeared among the *candidates* while
emission independently capped the output at 40. The pairs ranked 199/205 and
153/211 — present in the list, absent from the dossier the auditor reads. The
gate said PASS on a pass that was structurally broken. The fix is structural, not
careful: **one selection function, shared by emission and by every check on
emission** (`scripts/bookkit/selection.py`). As long as there is exactly one, the
failure cannot return.

**If the pass chases two failure modes, each mode gets its own quota.** A ranker
adding a constant bonus for "crosses units" onto a base scale of 1–4 does not
weight that property, it *stratifies* on it: every cross-unit item sorts above
every intra-unit one. With 92% of candidates cross-unit, a 40-slot quota emitted
40 cross-unit rules and zero intra-unit ones — and intra-unit is 7 of 10 defects.
74% of dossiers were saturated that way before anyone noticed, because the output
still looked full.

**Calibrate against every confirmed positive you have, not the convenient ones.**
A gate that started with two known pairs — both from the same unit — looked
excellent. Extended to the eight pairs a prior pass had already confirmed by
hand, real recall was 5/8 rules and 3/11 pairs. Two data points cannot show you a
bias; they can only fail to.

**Gaps stay inside the list, marked.** When calibration finds a case the check
misses, leave it in the gate's list flagged as a known gap. Do not delete it to
make the gate green. **A recorded gap is debt; a deleted gap is forgotten**, and
the next person to touch the check will rediscover it from scratch.

**A binary criterion needs a ladder.** Binary beats a percentage floor because
nobody can argue it down — but binary plus *unreachable* is worse than a floor,
because a criterion nobody can satisfy is one everybody routes around. v3.2
required `sampled == 0` for `PASS` while `tractable` was derived purely from
`len(instances)` with no override; on the reference book 221 of 454 rules were
over the line, so `PASS` could never be reached and the waiver would have become
permanent. The test to apply before shipping any hard criterion: **name the
specific work that moves it from false to true, and check that a person can
actually do that work.** If you cannot name it, you have written a percentage
floor with extra steps.

## Artifacts

```
reviews/manuscript-gate-<YYYY-MM-DD>/
├── GROUNDING.md              # passed verbatim to every auditor — see below
├── audited.yaml              # CUMULATIVE ledger: what each check has audited,
│                             # keyed by subject id + fingerprint
├── state.json                # per-round verdict, convergence and COVERAGE
├── round-1/
│   ├── findings/             # one JSON per auditor run (gate-findings.schema.json)
│   │                         # including clean runs — the file IS the coverage
│   ├── dossiers/             # MG-1 concept dossiers
│   ├── rules/                # MG-2 rule candidates
│   ├── coverage-MG-1.json    # eligible / selected / sampled / ranked cut list
│   ├── coverage-MG-2.json
│   ├── rule-probes-proposed.yaml   # the depth worklist, ranked
│   ├── coverage-summary.md   # COMPUTED report header + What-ran table — paste it
│   ├── lint-render.json      # MG-5
│   ├── fixed-defects.json    # MG-7
│   ├── anchors.json          # anchor resolution across findings + do-not-touch
│   ├── claim-index.json      # validator output
│   └── REPORT.md             # templates/manuscript-gate-report.md
├── round-2/ …
└── REPORT.md                 # cumulative, the one the human reads at the end
```

**`GROUNDING.md` is generated once per gate run and passed verbatim to every
auditor.** It carries: the authority rules for this project's sources, the
finding taxonomy above, the false-positive suppressors, the voice contract, the
accepted-items list, and the DO-NOT-TOUCH anchors from
`bible/claim-index.yaml` + `bible/do-not-touch.md`. Auditors that do not receive
it re-litigate the voice and rediscover refuted findings.

The report template has two sections that are easy to drop and should not be:
**"What was verified correct"** (in the reference audit, 81 clusters — nearly as
many as the defects, and as useful) and **"What was downgraded as inflated"**,
with the counter-evidence for each. The second is how you find out your auditors
are running hot.

---

## Running it

```bash
# Round 1, everything
python scripts/manuscript_gate.py --round 1

# Deterministic checks only — fast, run this any time
python scripts/manuscript_gate.py --deterministic-only

# Later rounds: propagation set + the next unaudited slice of the pool
python scripts/manuscript_gate.py --round 2

# After a fix pass: repair the line numbers of everything anchored
python scripts/resolve_anchors.py --heal

# Retrofit over a book this skill never scaffolded
python scripts/manuscript_gate.py --root /path/to/book --units "final/ch-*.md" --round 1
```

The script runs the deterministic checks, prepares the dossiers and rule
candidates the agents need, writes the report skeleton, and computes the verdict
from whatever findings files exist. It does **not** spawn agents — the
orchestrator does that, using the agent files, because agent dispatch belongs to
the session and not to a Python script.

## Configuration

```yaml
# bible/meta.yaml
pipeline:
  manuscript_gate:
    max_rounds: 5
    rounds_without_new_to_close: 2
    checks:                        # disable only via a recorded waiver
      MG-1: true
      MG-2: true
      MG-3: true                   # auto-skipped when the profile has no exercises
      MG-4: true
      MG-5: true
      MG-6: true
      MG-7: true                   # fixed-defect regression
    concept_min_units: 2           # audit concepts spanning at least this many units
    top_concepts: 40               # ~170-230k tokens x passes_per_subject EACH
    top_rules: 30                  # ~170-230k tokens x passes_per_subject EACH
```

The cost sits on the same line as the dial on purpose. Measured on the reference
book, one lens run costs 170–230k tokens and 10–16 minutes, so `top_rules: 30`
with `passes_per_subject: 2` is roughly **12M tokens for MG-2 alone**. That is a
decision, and it should not be discovered afterwards.

Turning a check off requires a `waivers` entry in `project-status.yaml` naming
who waived it and why. A check silently disabled in config is how the deferred
agents disappeared for three months.

## See also

- `references/claim-index.md` — the propagation machinery the loop runs on
- `references/agents/concept-auditor.md` — MG-1
- `references/agents/rule-auditor.md` — MG-2, MG-3
- `references/agents/reader-pov.md` § Whole-book mode — MG-4
- `references/validation-surface.md` and `references/verification-plan.md` — MG-6
- `templates/fixed-defects.yaml` — MG-7, and the "pin the claim, not the code" rule
- `templates/rule-probes-tuned.yaml` — the ladder out of the depth axis for MG-2
- `references/adversarial-verify.md` § Manuscript-gate mode
- `references/pipeline.md` — Phase 3, and the polish pass this does not replace
