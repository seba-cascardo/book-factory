# Claim index — knowing what else says the same thing

The pipeline can tell you whether a unit is good. It cannot tell you, when you
edit line 186, that lines 194, 196 and 454 say the same thing and are now wrong.
That gap is not a small one: it is the mechanism behind every incomplete fix,
and an incomplete fix is worse than the original defect because the document now
contradicts itself and both sides look reviewed.

`bible/claim-index.yaml` closes it. For each concept it records every passage in
the book that makes a claim about it, which one is canonical, and which passages
carry the same sub-claim. When a passage is edited, the index says who else to
look at.

Template: `templates/claim-index.yaml` — read it for the full field reference.
Tooling: `scripts/build_concept_dossier.py` (build) and
`scripts/validate_claim_index.py` (check).

---

## The one design decision that matters

Sites are keyed by **fingerprint** — a hash of the normalized passage text — not
by line number. Everything follows from that:

| What happened | Fingerprint | Verdict | What the system does |
|---|---|---|---|
| Passage moved (lines inserted above) | still present | `MOVED` | repairs the location silently, no human |
| Passage edited | gone | `CHANGED` | flags every sibling, emits `PROPAGATE` |
| Passage deleted | gone, file present | `CHANGED` | same — a deletion is an edit of the claim set |
| Whole unit gone | file absent | `GONE` | dead entry, reported |

Keying by line number would invert the asymmetry: every insertion anywhere would
look like an edit, the warnings would be constant, and within a week nobody
would read them. The value here is entirely in the **signal-to-noise ratio**, so
protect it. Two rules follow:

- `PROPAGATE` fires only to a passage's `related` set — the three or four sites
  that carry the same sub-claim, not the sixty-five sites of the concept. A
  warning that asks you to review sixty-five passages gets ignored.
- The validator is a **warning, never a hard gate**. It exits 0 with findings.
  A hard gate on prose gets switched off within a week, and then you have
  neither the gate nor the warning. The manuscript gate reads its JSON output
  and decides what blocks; the validator itself only reports.

---

## Wiring — the part that is easy to skip and fatal to skip

An index nobody reads automatically is a checklist, and checklists go stale.
This one is read in three places, and all three are mandatory:

1. **Manuscript gate, every round** (`references/manuscript-gate.md`). The
   deterministic sweep runs `validate_claim_index.py --json` before anything
   else. `CHANGED` entries from the previous round's accepted fixes become the
   next round's review set — that is how the gate converges instead of
   re-auditing the whole book each time.

2. **After accepted polish-pass edits** (`references/pipeline.md` § Polish
   pass). The moment an edit lands in `final/unit-NN.md`, run the validator.
   Its `PROPAGATE` lines go into the same human packet as the diff, so the
   person who just accepted an edit sees immediately which siblings it orphaned.

3. **Build preflight** (`references/build-export.md`). `--quiet` mode, before
   any target is produced. Open `PROPAGATE` warnings do not block the build;
   they are printed with the build report, because shipping a document whose
   claim set is known to be internally inconsistent should be a decision
   somebody made, not a thing that happened.

If a project has no claim index yet, all three degrade to a one-line notice.
That is fine. What is not fine is having the index and not reading it.

---

## Roles, and who assigns them

Every site carries a role. The generator seeds them; the audit decides them; the
generator never overwrites a decision that was already made.

| Role | Meaning |
|---|---|
| `CANON` | The definitive statement. **Exactly one per concept** — the validator enforces it. |
| `repeats` | Restates CANON elsewhere. |
| `derives` | Draws a consequence from CANON. |
| `qualifies` | Adds a condition or an exception. |
| `summary` | A recap bullet. It can be the second side of a contradiction, never the first. |
| `example` | Inside an exercise or worked example. |
| `crossref` | A pointer, not a claim. |

The seeding heuristic is deliberately weak — highest-scoring claim in the home
unit becomes provisional CANON, summary bullets become `summary`, exercise
passages become `example`, everything else `repeats`. It is a starting point for
the concept auditor, not a judgement. The auditor's job in MG-1 includes
correcting it, and once corrected the role survives every regeneration because
it is matched by fingerprint.

The single-CANON invariant is what makes contradiction reporting tractable: with
one canonical statement, a disagreement is "site X contradicts CANON", which is
actionable. With three co-equal statements it is "these three differ", which
starts an argument about which one is right and usually ends in a compromise
edit that makes all three vaguer.

---

## Positive verdicts are first-class

Two fields exist to record that something is **correct**:

```yaml
  reduction_wildcard:
    verified_against: "bible/sources/manage-data/manage-data.md:12177"
    do_not_touch: true
    note: >
      The 100× figure is against the database, NOT against standard mode.
      Someone "corrected" this to "100 times faster than standard mode" on
      2026-07-29 — a factual error, reverted the same day. A finding against
      this passage is REFUTED unless it brings an official citation that
      contradicts that page.
```

This is not bookkeeping. A review system that can only record defects loses its
positive knowledge the moment the report is filed, and the next pass re-opens
settled questions. In the audit this design comes from, that produced a fix pass
that introduced a factual error into text that was already right — caught and
reverted the same day, but only because someone remembered.

So: whenever a concept is checked against a source and found correct, write
`verified_against`. Whenever a finding is rejected as not-a-defect, write
`do_not_touch: true` **with the counter-evidence in `note`**. An anchor without
a reason is just an assertion, and the next auditor will overrule it.

`validate_claim_index.py` surfaces both flags on any `PROPAGATE` touching that
concept, so the guard travels with the warning.

---

## Building it

```bash
# 1. Seed the probes (once). Uses the knowledge graph when there is one,
#    the glossary when there is not, term frequency as a last resort.
python scripts/bootstrap_probes.py

# 2. Check coverage and tune the noisy probes before trusting anything.
python scripts/build_concept_dossier.py --probe-report

# 3. Generate the index.
python scripts/build_concept_dossier.py --emit-index

# 4. Validate. --fix repairs moved locations.
python scripts/validate_claim_index.py --fix
```

**Tune the probes.** This is not optional polish. A probe derived from a
knowledge-graph node name finds the passages that use the node's label, and the
concept that actually contradicts itself is usually finer-grained than a graph
node — it lives in one sense of a term the node covers. Write those by hand in
`bible/concept-probes-tuned.yaml`, which wins over the generated base and is
never overwritten.

Two calibration facts, so nobody has to rediscover them:

- **Case sensitivity matters** for any keyword that is also an ordinary word in
  the prose language (`SET`, `KEEP`, `JOIN`, `LOAD`). Without
  `case_sensitive: true` those probes return triple-digit junk.
- **`homonym_guard` does not filter.** It populates a separate section of the
  dossier. Merging homonyms into the main passage list is the number-one false
  positive: the auditor reads two different referents as one claim and reports a
  contradiction that is not there.

## Enabling the incomplete-fix detector

List the commits of past fix passes in `bible/audit-config.yaml`:

```yaml
fix_run_commits: ["3e6829b", "5bdbcc8"]   # short shas of fix passes
persona_names: ["Ana", "Carlos"]          # running-example characters
```

A related pair where **one side has blame in a fix run and the other does not**
is the mechanical signature of a fix that landed in 1 of N sites. Dossiers report
these as `d2_candidates`, found without spending a token on a model. For a
retrofit run over a project you would rather not add config files to, pass
`--fix-run-commit` and `--persona` on the command line instead.

---

## Retrofit

The whole toolkit runs over a book the skill never scaffolded:

```bash
python scripts/bootstrap_probes.py --root /path/to/book --units "final/ch-*.md"
python scripts/build_concept_dossier.py --root /path/to/book --units "final/ch-*.md" --emit-index
```

With no knowledge graph the probes come from the glossary, and with no glossary
from term frequency across units — restricted to phrases spanning two or more
units, since a concept confined to one unit cannot carry a cross-unit
contradiction. Frequency-derived probes are crude by construction; run
`--probe-report` and tune before trusting a dossier.

## See also

- `references/manuscript-gate.md` — MG-1, which reads the dossiers
- `references/pipeline.md` § Polish pass — the post-edit wiring
- `references/build-export.md` — the preflight
- `references/knowledge-graph.md` — where probes come from when there is a graph
