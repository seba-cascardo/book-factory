# Phase 4.5 — The manuscript gate

Per-unit gates cannot see a defect that lives between units, or between layers
of one unit (prose against code, text against exercise, source against rendered
output). This phase makes the book the unit of analysis. It computes a verdict,
blocks, and iterates until it converges; Phase 4's continuity audit and polish
pass stay advisory. Why: `docs/rationale/gate.md#origin`.

`scripts/manuscript_gate.py` runs the deterministic checks, prepares the agents'
inputs, keeps the findings and coverage state, and computes the verdict. It never
spawns agents: the orchestrator dispatches what it lists.

---

## Trigger

When the last unit reaches `archived`, the orchestrator writes
`phase: manuscript-gate`, sets `project-status.yaml → manuscript_gate.state` to
the run's `state.json`, and starts round 1. Invariant: **no path leads from the
last approved unit to `complete` without passing through Phase 4.5.**

---

## Checks by profile

| id | Question | Engine | Profiles |
|---|---|---|---|
| **MG-1** Concept audit | Do all claims about one concept agree, across units? | dossiers + `concept-auditor` | nonfiction |
| **MG-2** Rule vs instances | Do the book's code and examples obey the rules its prose states? | rule files + `rule-auditor` | nonfiction |
| **MG-3** Exercise vs content | Was everything an exercise demands taught, and does the promised solution exist? | `rule-auditor` | nonfiction with exercises |
| **MG-4** Whole-book read | Read end to end as the target reader — **is it enough?** | `reader-pov` whole-book mode | all |
| **MG-5** Render lint | Does the source render as meant? | `lint_render.py` | all |
| **MG-6** Checkable against reality | Did the code run, or is the debt declared with a plan? | runner audit + waivers | nonfiction |
| **MG-7** Fixed-defect regression | Did a fixed defect come back? | `check_fixed_defects.py` | all |
| **MG-S** Story closure | Do arcs, ledger and ending close as designed? | `check_story.py --manuscript` | literary |
| **MG-T** Book-level tics and form | Tics, names, dialogue format across units | `lint_fiction.py --book` | literary |
| **MG-C** Continuity & development | Continuity and developmental audit of the whole book | agent, lenses `continuity`, `developmental` | literary |

**Profile branch.** For `book-literary`, MG-1, MG-2, MG-3 and MG-6 are
`n/a (profile)`: no probes are built, no waiver is needed. The literary checks
(MG-4 literary mode, MG-S, MG-T, MG-C) are specified in
`references/manuscript-gate-literary.md`. Every other profile runs MG-1 to MG-7.

**Deterministic checks** (MG-5, MG-6, MG-7, MG-S, MG-T) run over the whole book
in every sweep and cost seconds. **Agent checks** (MG-1, MG-2, MG-3, MG-4, MG-C)
cost agent runs: they carry quotas, their coverage is tracked per subject, and
coverage is a term of the verdict (§ Coverage).

### MG-1 — Concept audit

`scripts/build_concept_dossier.py` gathers, for one concept, every passage in the
book that makes a claim about it; `references/agents/concept-auditor.md` reads
them together. Only concepts spanning at least `concept_min_units` units (default:
two) are eligible: a concept confined to one unit cannot carry a cross-unit
contradiction. Probes and tuning: `references/claim-index.md`.

### MG-2 — Rule vs instances

`scripts/extract_rule_candidates.py` writes one file per rule: the rule and every
code block and example its key terms reach, across the book.
`references/agents/rule-auditor.md` judges each rule against all its instances.
Rule ids are content-derived (`<unit>-<term>-<hash6>`), so inserting lines above
a rule does not orphan its tuning or its audit.

### MG-3 — Exercise vs delivered content

Subjects are the units that declare `exercises` in `outline/units.yaml` (matched
by unit number, so `unit: 01` read by YAML as `1` still matches `unit-01`).
Skipped automatically when no unit declares exercises. Auditor:
`references/agents/rule-auditor.md` § MG-3.

### MG-4 — Whole-book read

Reader-POV reads `manuscript.md` end to end in the profile's persona —
`references/agents/reader-pov.md` § Whole book (MG-4) (literary mode:
`references/manuscript-gate-literary.md`). Its question is not "is this right?"
but **"is it enough?"**. Why: `docs/rationale/gate.md#mg4`.

### MG-5 — Render lint

`scripts/lint_render.py` over the units in `final/`; the gate rebuilds
`manuscript.md` from them (`sync_manuscript.py`) in every sweep, so MG-4 reads
exactly what ships. Hazards: accidental Setext headings, unclosed fences (per
CommonMark: same character, closing fence at least as long), unclosed HTML
comments (comments do not nest; fences and code spans are skipped), tables with
no separator or ragged rows (a lone `| row |` included), lists glued to a
paragraph, a line starting `1999.` (an accidental ordered list), a dialogue raya
glued to the narration line above, heading jumps, multiple H1, pipeline handoff
comments, internal link names, and files that are not UTF-8 (`encoding`, major).
`* * *` and `***` are scene breaks. Severities as reported: `critical` blocks,
`major` needs revision. Why: `docs/rationale/gate.md#render`.

### MG-6 — Checkable against reality

For every validation surface whose content is executable (`executable:` in
`meta.yaml`, else a name heuristic; undeclared surfaces are reported): either
the runner ran and its output is on disk — `evidence: <path>` on the surface,
an existing non-empty runner-output file under the project (a `runner` string
such as "qlik reload (never run)", "reviewer-only" or "x" is a description,
never evidence) — or a complete waiver `validation_surface.<surface>` (§ Verdict → Waivers)
names **a plan entry that exists** — `plan: reviews/verification-plan/PLAN.md#V-03`
(or `plan_entry: V-03`) with a `### V-03` heading in that file. Units with
tagged code fences (```` ```sql ````, ```` ```python ```` …) and an empty
`validation_surface.surfaces` are a `major` "code present, no surface
declared". Anything else is a `major` finding. See
`references/validation-surface.md` and `references/verification-plan.md`.

Beyond code: every `deferred` item whose `needs` is `runner`, `live-system`,
`measurement`, `person` or `document-of-record` is appended to
`reviews/verification-plan/PLAN.md`. `human-decision` goes to the human packet.
Literary (MG-6 `n/a`): the gate still appends the facts lane's questions to the
plan, but no waiver rests on it — the orchestrator puts every open `deferred`
item in the human packet as a question.
**Unresolved here is usually not unknowable, only unknown in this session**:
verify the claim, soften it, or write down the check and record the debt — never
assert it anyway. Why: `docs/rationale/gate.md#mg6`.

### MG-7 — A fixed defect must not come back

`bible/fixed-defects.yaml` lists formulations that were wrong;
`scripts/check_fixed_defects.py` scans the whole book every sweep; a reappearance
defaults to `critical`. **Pin the claim, not the code**: the corrected text
usually quotes the wrong form to teach against it, so pin the conceptual frame
and give the teaching passage an `allow_in` anchor. An entry is born when a
critical or major finding is resolved: the gate's report proposes it, the human
writes it. It never expires; retire it explicitly with a reason. Template:
`templates/fixed-defects.yaml`. Why: `docs/rationale/gate.md#mg7`.

---

## Language

The language is `project.language_variant` → `conventions.language_variant` →
`project.language` → `en-US`. MG-2's rule shapes and MG-1's claim scoring use the
language pack `scripts/lexicons/<lang>.yaml` (`modality`, `universal`, `breaks`),
extended by `bible/lexicon.yaml`. With no pack for the language, MG-2 falls back
to language-agnostic pairing — prose naming a backticked identifier ↔ code blocks
using it — and the coverage record and the gate say "no language pack for
`<lang>`". Zero eligible subjects is reported as such, never read as complete.

---

## The run directory

```
reviews/manuscript-gate-<run>/
├── GROUNDING.md          # regenerated every run; every auditor reads it first
├── state.json            # the gate's source of truth: rounds, verdicts, convergence,
│                         #   per-round manuscript/unit hashes and finding keys
├── findings.jsonl        # the cumulative findings store (§ Findings)
├── subjects.json         # the coverage manifest (§ Coverage)
└── round-N/
    ├── deterministic.json          # normalized MG-5/7/S/T findings + manuscript hash
    ├── lint-render.json · fixed-defects.json · claim-index.json · anchors.json
    ├── story.json · fiction.json   # literary: MG-S, MG-T raw output
    ├── coverage-MG-1.json · coverage-MG-2.json   # every eligible subject + hash
    ├── dossiers/ · rules/          # MG-1 and MG-2 inputs, rebuilt each sweep
    ├── rule-probes-proposed.yaml   # ranked worklist of sampled rules
    ├── findings/<subject>.<lens>.p<N>.json      # written by the auditors
    └── REPORT.md                   # computed block + the template's human sections
reviews/verification-plan/PLAN.md   # append-only
```

`<run>` is `--run-dir`, else `--date`, else the latest existing run with a
`state.json`, else `current`. Every sweep deletes the round's tool outputs,
dossiers and rule files before regenerating them, so a crashed tool can never be
read through a stale file. `findings/` and `REPORT.md` are never deleted.

**GROUNDING.md** carries: the profile, language and authority rule for
`bible/sources/`, the voice contract, § The finding taxonomy and § False-positive
suppressors of this file verbatim, the accepted items (findings `refuted` or
`accepted-risk` — do not re-report them), and the DO-NOT-TOUCH anchors
(`bible/do-not-touch.md` plus `do_not_touch`/`verified_against` concepts in
`bible/claim-index.yaml`).

**REPORT.md**: the gate replaces only the block between `<!-- BEGIN computed …`
and `<!-- END computed -->` (verdict, coverage, what ran, not-fully-audited
subjects, open findings, dispatch list, round history). Everything else —
verified correct, downgraded as inflated, proposed fixed-defect entries — is
written by the orchestrator from `templates/manuscript-gate-report.md` and
survives every run.

---

## Findings

**Files.** One JSON file per auditor run, named
`round-N/findings/<subject>.<lens>.p<pass>.json`, conforming to
`templates/gate-findings.schema.json`. MG-4: `manuscript.whole-book-read.p1.json`;
MG-C: `manuscript.continuity.p1.json` and `manuscript.developmental.p1.json`
(literary: `.p2.json` too — two passes each).
Every file is schema-validated (`jsonschema` when installed, a built-in fallback
otherwise); **an invalid file makes the verdict `ERROR`**, naming the file. A
subject audited clean still writes a file with an empty `findings` array: the file
is the evidence that anybody looked.

**The store.** `findings.jsonl` holds every finding of every round, one line per
content key: check, subject, relation and the verbatim quotes (never line
numbers), so passes, lenses and rounds that report the same thing merge. It is
recomputed from all findings files and sweep outputs on every run; human
decisions are carried over and **re-validated on every run** (a hand edit to
`findings.jsonl` that breaks a rule below is ignored and named in the report).
The store only grows: `state.json` records every round's finding keys, and a
`findings.jsonl` missing a key an earlier round recorded (truncated, replaced or
deleted) makes the verdict `ERROR` — "findings store truncated" — until the file
is restored or a new run directory is started. Deleting a findings FILE does not
close its findings: they stay open. Statuses:

| Status | Reached by |
|---|---|
| `open` | reported, and not closed by any rule below |
| `fixed` | an agent re-audit of the same subject and lens in a later round no longer reports it · a deterministic finding is absent from the latest sweep · `--resolve --status fixed` (agent findings only, with evidence) |
| `refuted` | the adversarial verifier wrote `verification.verdict: REFUTED` · `--resolve --status refuted --note …` (agent findings only) |
| `accepted-risk` | `--resolve --status accepted-risk --note …` (never for a `critical`) |

`--resolve` discipline, every profile (the gate refuses, and ignores such a
decision found in `findings.jsonl`):

- **Deterministic** findings (MG-5, MG-7, MG-S, MG-T) are never `fixed` or
  `refuted` by hand: they close when the sweep stops reporting them.
  `accepted-risk` only for a non-critical MG-5 or MG-T, or a `minor` MG-7;
  MG-S never.
- **Configuration** findings (a disabled check, an MG-6 runner or surface)
  close by fixing the configuration — never by `--resolve`.
- **Agent** findings (MG-1..4, MG-C): `fixed` needs a note AND evidence — the
  text the finding points at (its unit, or the manuscript for whole-book
  subjects) has a different hash from the one recorded with the finding;
  reverting the text reopens it. `refuted` and `accepted-risk` need a note of
  20+ characters that is not a placeholder; `accepted-risk` never for a
  critical.
- Literary R1/R2 findings (`rule: "R1"|"R2"`): nothing by hand, and not a
  verifier's REFUTED either — only a re-audit of changed text
  (`references/manuscript-gate-literary.md`).

```bash
python scripts/manuscript_gate.py --resolve <key> --status refuted \
    --note "unit-07 §2 states the qualifier; the finding quoted an older draft"
```

`refuted` and `accepted-risk` stick while their note stands. A finding marked
`fixed` by hand reopens if a later round reports it again (a regression) or the
text returns to what the finding described. **The verdict is computed over all
open findings**, whatever round produced them.

---

## Coverage

A **subject** is what one agent run audits: a concept (MG-1), a rule (MG-2), an
exercise unit (MG-3), the manuscript (MG-4), a lens (MG-C). Each has a **hash** of
what an audit of it reads — the concept's passages; the rule plus its instances;
for MG-3, MG-4 and MG-C, the whole manuscript. `subjects.json` records each as:

- `pending` — reason `never-audited`, `edited-since-audit` (its hash moved),
  `passes k/N` (MG-1/MG-2 need `passes_per_subject` distinct passes, default 2),
  or `blocked` (the check could not run: no concept probes, no language pack and
  nothing found, an MG-S/MG-T script not installed, no coverage record);
- `audited@<hash>` — audited in full at that text;
- `sampled@<hash>` — audited from a sample: a rule with more instances than one
  run can judge (`tractable: false`), a dossier whose home unit was trimmed, or a
  findings file with `sampled: true`.

The emitters skip subjects audited at their current hash: they leave the pool,
never the denominator. Eligible means post-filter (`--min-instances`,
`--df-ceiling`, `--min-units`); a rule narrowed by hand stays eligible whatever
its instance count. So each round drains the next slice, and an edit sends its
subjects back to `pending`. The ladder out of `sampled`: narrow the rule in
`bible/rule-probes-tuned.yaml` (worklist: `round-N/rule-probes-proposed.yaml`) or
raise `home_cap` on the concept probe. **Narrowing is a claim about scope**; if a
subject really is that wide, accept it under the coverage waiver instead. Why:
`docs/rationale/gate.md#coverage`, `#depth`.

---

## Verdict

```
ERROR           a tool failed, a findings file is invalid, the round was never swept,
                or findings.jsonl lost keys state.json recorded
BLOCKED         an open critical finding
NEEDS-REVISION  an open major finding
PASS-PARTIAL    nothing open that blocks, but some subject is pending or sampled
PASS            every subject audited in full at the current text, nothing open that blocks
```

`minor` never blocks. A check switched off in `pipeline.manuscript_gate.checks`
without a valid `manuscript_gate.<check>` waiver is itself a `major` finding. The
report separates subjects **never opened** from **partly read** and **re-queued**.

**Waivers.** Every waiver in `project-status.yaml → waivers` counts only when it
says who (`waived_by`), why (`reason`) and what is owed (`debt`) with real
content: none of them a placeholder (`x`, `N/A`, `TBD`, `-`, `(pendiente)` …),
and `reason` and `debt` 20+ characters each. The gate names an incomplete one
and ignores it. `manuscript_gate.MG-6` and `validation_surface.*` waivers also
name a verification-plan entry (§ MG-6). Literary MG-S, MG-4 and MG-C have no
waiver: switching them off is ignored (and reported `major`), and no coverage
waiver covers a pending MG-4/MG-C subject (`references/manuscript-gate-literary.md`).

**The coverage waiver.** `PASS-PARTIAL` does not block the work; it blocks the
claim. To finish there, record one waiver whose signature is the one the gate
prints — a hash of the exact pending and sampled sets:

```yaml
# project-status.yaml
waivers:
  - check: manuscript_gate.coverage
    waived_by: human
    reason: "MG-2 held at 30 rules/round by budget; 14 rules genuinely govern every example"
    debt: "212 rules never opened, 14 sampled, as of round 4"
    signature: "cov:3f2a9b1c0d4e"
```

A signature that no longer matches is stale and does not count: a waiver that
outlives its own facts is what the gate exists to prevent.

---

## Convergence

The gate is **converged** when all hold:

1. the verdict is `PASS`, or `PASS-PARTIAL` with a valid coverage waiver (so no
   open critical or major, no ERROR);
2. the last `rounds_without_new_to_close` (default 2; a lower value is clamped
   to 2, with a note) **distinct swept rounds**
   introduced no new blocking finding — a critical or major, from any check
   (MG-5, MG-7 and MG-S included), first seen in that round and not refuted; one
   fixed within its own round still counts;
3. `final/` has not changed since the current round's sweep.

Re-running `--verdict-only` adds no round. One clean round is not evidence:
finder agents miss things and the defect tail is long. "No issues at all" is not
the criterion — minors always remain.

At `max_rounds` (default 5) without convergence the gate does not relax: produce
the escalation packet (`references/loopback-handoff.md` shape) and set
`phase: blocked-on-manuscript-gate`; a sweep past `max_rounds` is refused (exit
2). A loop that does not converge is information. Literary adds a fourth
condition: `check_story.py --manuscript` exits 0 at verdict time.

---

## The loop

```
Round N
  1. manuscript_gate.py --round N        sweep (whole book) + prepare + verdict
  2. dispatch the auditors it lists      each writes a findings file, clean or not
  3. manuscript_gate.py --round N --verdict-only
  4. adversarial verification of every open critical/major
     (references/adversarial-verify.md § Manuscript-gate mode)
  5. human packet → accept / reject / accept risk (--resolve); accepted fixes
     land in final/; validate_claim_index emits PROPAGATE for their siblings
  6. manuscript_gate.py --round N+1      edited subjects are pending again
```

A round that already has findings files is never re-prepared (the gate refuses):
recompute it with `--verdict-only`, or start the next round. **Anti-thrash**: a
rejected finding is `refuted` in the store and listed in GROUNDING.md, and its
concept gets `do_not_touch: true` plus the counter-evidence in
`bible/claim-index.yaml`; otherwise it returns every round and, one day, gets
"fixed" into an error. Why: `docs/rationale/gate.md#positives`.

After a fix pass: `python scripts/resolve_anchors.py --heal` repairs line numbers
that DRIFTED; references to passages that were EDITED are never healed — re-read
them. Why: `docs/rationale/gate.md#anchors`.

---

## The finding taxonomy

Every finding carries a `relation`. Apply this tree **in order** and **stop at the
first that applies**; the order keeps two auditors from filing one pair under two
codes.

1. Same surface term, **different referents**? → **D4** (homonym). Different terms,
   same referent? → **D4a** (synonym). STOP.
2. Propositions jointly unsatisfiable **in the same scope**? → one is the hedged
   version of the other: **D5** (asymmetry); otherwise **D1** (contradiction). STOP.
3. Same scope, same polarity, **different quantities**? → do all sites name their
   baseline? No: **D7**. Yes: **D7a** (not a defect). STOP.
4. **Different scopes**? → transplanting P1 into P2's scope breaks, with nothing
   warning the reader: **D8** (latent tension). Otherwise **N2** (not a defect). STOP.
5. Related passages where **one has blame from a fix run and the other not**? →
   **D2** (incomplete fix). STOP.
6. A **rule in prose** and an **instance in code or an example** that
   **contradicts** it? → **D6**, `violation_kind: contradiction`. STOP.
7. The instance **applies the pattern and is silent about a precondition the rule
   declares mandatory**? → **D9**, `violation_kind: omission`. STOP.
8. Nothing applies → **N1** (consistent restatement, not a defect).

**D3** (gap) stands alone: no passage is false, but together they fail to cover a
behavior the sources document and the reader will walk into. In nonfiction only
the `source` lens emits D3 (literary exceptions: `manuscript-gate-literary.md`).

### Omission — the class reviewers are blind to

An omission has no second statement to compare: one passage declares a
precondition mandatory, another applies the pattern and says nothing. The reader
copies it, loses the condition, and gets no error. **The default inverts here**:
between D6 and N2 choose N2; **between D9 and N2 choose D9**. Every D6/D9 carries
`violation_kind`, which is how a run shows it learned the class rather than the
worked examples. This applies to any agent comparing two passages — Technical
Reviewer, Continuity Guardian, Critic. Why: `docs/rationale/gate.md#omission`.

**N1, N2 and D7a are first-class results and MUST be emitted**: "verified correct,
do not touch" needs somewhere to live.

## False-positive suppressors

Apply BEFORE emitting.

| Trap | Rule |
|---|---|
| **Scope collapse** | No **D1** without `scope_1` and `scope_2` stated in words. If you cannot name two different scopes you cannot file **N2** either: pick one and justify it. |
| **Baseline blindness** | Before **D7**, fill `baseline_1` and `baseline_2`. Different baselines are **D7a**. |
| **Progressive disclosure** | If P1's unit is earlier than the concept's `home`, the most you may emit is **D5**, and only if the simplification is *actionably* false. |
| **Summary bullets** | A `[summary]` passage is only ever P2, and yields only D5/D7. |
| **Deliberately divergent example** | A **D6** states which form the book itself prefers; if neither passage says, `fix_scope` is `add_crossref`. |

- **Voice is not a defect.** The project's signed register
  (`bible/voice-profile.md`) — rhetorical absolutes, second person, humor, short
  sentences. An absolute inside advice is voice; an absolute about how the system
  behaves is a claim.
- **Search the whole unit.** Grep the unit for the topic before reporting; a
  previous fix usually landed in a neighbouring paragraph. `searched_whole_chapter:
  true` is a claim you are making.

Why: `docs/rationale/gate.md#suppressors`.

---

## Two passes, then union

MG-1 and MG-2 auditors run `passes_per_subject` times (default 2) on the same
subject with the same prompt; the store merges them by content key. A subject with
fewer passes is `pending (passes k/N)`. A finding only one pass produced is the
first false-positive candidate: verify it first. Why: `docs/rationale/gate.md#passes`.

## Adversarial verification

Every open critical and major finding passes through a verifier whose mandate is
to refute it (`references/adversarial-verify.md` § Manuscript-gate mode), who
reads the whole section around each passage and writes the `verification` object
into the finding. Between CONFIRMED and UNVERIFIED it chooses UNVERIFIED.
`REFUTED` makes the finding `refuted`; `corrected_severity` replaces the severity.

**Cross-model.** With `pipeline.adversarial_verify.cross_model: true` and a tool
for a second model, the verifiers **and MG-4** (the whole-book read, every
profile) run on that model — a second reader is where model diversity pays most.
No tool → both run on the session model and the report says "cross-model
unavailable".

---

## Running it

```bash
python scripts/manuscript_gate.py --round 1                  # sweep + prepare + verdict
python scripts/manuscript_gate.py --round 1 --verdict-only   # after the auditors
python scripts/manuscript_gate.py --round 2                  # next slice + re-queued
python scripts/manuscript_gate.py --deterministic-only       # seconds; no round, no store
python scripts/manuscript_gate.py --resolve KEY --status fixed|refuted|accepted-risk|open --note "…"
python scripts/manuscript_gate.py --root /book --units "final/ch-*.md" --round 1   # retrofit
```

Exit codes: `0` converged · `1` not converged · `2` ERROR or usage error — also
when `bible/meta.yaml` has no known `project.profile` (read stripped and
lowercased) or a `schema_version` other than "3.4" (a retrofit writes a minimal
`bible/meta.yaml` with both first). `--deterministic-only` exits 1 on an open
critical/major. `--round` defaults to the latest recorded round;
`--top-concepts` / `--top-rules` override the quotas for one run.

## Configuration

```yaml
# bible/meta.yaml
pipeline:
  manuscript_gate:
    max_rounds: 5
    rounds_without_new_to_close: 2   # minimum 2 (lower values are clamped)
    concept_min_units: 2
    top_concepts: 40          # per-round quota; ~170-230k tokens x passes EACH
    top_rules: 30             # per-round quota; ~170-230k tokens x passes EACH
    passes_per_subject: 2     # MG-1/MG-2
    checks:                   # false only with a complete manuscript_gate.<check> waiver
      MG-1: true              # … MG-7, and MG-S (never false), MG-T, MG-C for book-literary
```

Why the cost sits next to the dial: `docs/rationale/gate.md#cost`.

## See also

- `references/manuscript-gate-literary.md` — MG-4 literary, MG-S, MG-T, MG-C
- `references/claim-index.md` — probes, the claim index, PROPAGATE
- `references/agents/concept-auditor.md` (MG-1) · `rule-auditor.md` (MG-2, MG-3) ·
  `reader-pov.md` § Whole book (MG-4)
- `references/validation-surface.md` · `references/verification-plan.md` (MG-6)
- `templates/fixed-defects.yaml` (MG-7) · `templates/rule-probes-tuned.yaml`
- `references/adversarial-verify.md` § Manuscript-gate mode
