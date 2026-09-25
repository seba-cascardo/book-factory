# scripts/

Deterministic checks. No model runs any of these — that is the point. A regex
does not hallucinate a violation and is not tired by chapter 14, so anything
mechanical belongs here and the agents keep the judgement.

## Requirements

Python 3.10+ and PyYAML. `git` is optional and powers one thing: the
incomplete-fix detector, which spots a claim that was corrected in one place and
left standing in another by comparing blame. Everything else degrades cleanly
without it.

```bash
pip install pyyaml
```

## Common flags

Every script takes `--root` and `--units`, so all of them also run standalone
over a book this skill never scaffolded:

```bash
python scripts/lint_render.py --root /path/to/book --units "final/ch-*.md"
```

With neither flag, the root is the nearest ancestor holding `bible/meta.yaml` or
`final/`, and units resolve to `final/unit-*.md`, then `final/ch-*.md`, then
`final/*.md`.

## What each one is for

| Script | Phase | Blocks? |
|---|---|---|
| `manuscript_gate.py` | 4.5 | computes the verdict |
| `lint_render.py` | 4.5 (MG-5) + build preflight | yes, on `critical` |
| `sync_manuscript.py` | 4 + build preflight | yes, on drift (`--check`) |
| `build_concept_dossier.py` | 4.5 (MG-1) | no — prepares agent input |
| `bootstrap_probes.py` | once, before the above | no |
| `validate_claim_index.py` | 4.5, post-edit, build preflight | **no, by design** |
| `extract_rule_candidates.py` | 4.5 (MG-2) | no — prepares agent input |
| `check_fixed_defects.py` | 4.5 (MG-7) | **yes** — a reappearance is `critical` |
| `resolve_anchors.py` | 4.5 + after any fix pass | **no, by design** |
| `extract_code_corpus.py` | 4.5 (MG-6) | no |
| `lint_style.py` | Proofreader | no |

`validate_claim_index.py` and `resolve_anchors.py` exit 0 even with findings, and
that is deliberate: a hard gate on prose gets switched off within a week, and then
you have neither the gate nor the warning. The manuscript gate reads their JSON
and decides what blocks.

### The two that emit coverage

`build_concept_dossier.py` and `extract_rule_candidates.py` write
`round-N/coverage-<check>.json`: the post-filter candidate count, what was
selected, how many emitted subjects can only be SAMPLED, and the ranked list of
what was cut. The gate's verdict reads it — without that term, `PASS` cannot
distinguish "all of it is clean" from "the 6% we looked at is clean".

They also take `--audited <ledger>` and skip subjects an earlier round already
audited under an unchanged fingerprint. Those stay in the denominator; they only
leave the pool. That is what makes `--top` a per-round cost dial instead of a
permanent ceiling.

Coverage has two axes and they close differently. **Breadth** (how many subjects
were opened) closes by itself as rounds drain the pool. **Depth** (how many were
read only in part) closes only by hand, so `extract_rule_candidates.py` reads
`bible/rule-probes-tuned.yaml` for narrowings and writes the ranked worklist of
still-intractable rules to `round-N/rule-probes-proposed.yaml`. Without that
ladder, `sampled == 0` is unreachable on any large technical book — measured, 221
of 454 rules — and the criterion becomes a permanent waiver.

## A typical run

```bash
# once
python scripts/bootstrap_probes.py
python scripts/build_concept_dossier.py --probe-report   # then tune the noisy ones
python scripts/build_concept_dossier.py --emit-index

# the gate
python scripts/manuscript_gate.py --round 1              # prepare + verdict
#   ... dispatch the auditors it lists ...
python scripts/manuscript_gate.py --round 1 --verdict-only

# round 2 selects the NEXT unaudited slice, not the same one again
python scripts/manuscript_gate.py --round 2

# after a fix pass: repair line numbers from their content anchors
python scripts/resolve_anchors.py --heal

# any time, seconds
python scripts/manuscript_gate.py --deterministic-only
```

## Project configuration

- `bible/audit-config.yaml` — fix-run commits, running-example names, code
  kinds, thresholds. See `templates/audit-config.yaml`. Optional; every field
  has a default and the CLI can override the two that matter for a one-off
  retrofit (`--fix-run-commit`, `--persona`).
- `bible/lint-config.yaml` — terminology pins and the casing watchlist for
  `lint_style.py`. Optional: with no config the watchlist is derived from
  `bible/glossary.md`.
- `bible/concept-probes-tuned.yaml` — hand-written probes. These win over the
  generated ones and are never overwritten. `home_cap` is settable per probe, so
  one sprawling concept can be read in full without raising the global dial.
- `bible/rule-probes-tuned.yaml` — hand-written narrowings for MG-2 rules that
  reach more instances than one agent run can judge. See
  `templates/rule-probes-tuned.yaml`. Narrowing is a claim about a rule's SCOPE:
  if the rule really is that wide, waive the depth instead of shrinking it.
- `bible/fixed-defects.yaml` — defective formulations that must not reappear
  (MG-7). See `templates/fixed-defects.yaml`, and read the "pin the claim, not
  the code" rule there before writing an entry: the corrected text usually quotes
  the wrong form in order to teach against it, so a literal pin fires on the fix.

## `bookkit/`

Shared primitives. Everything imports from here rather than re-deriving
segmentation or similarity, because the checks have to agree on what a passage
*is* — otherwise the claim index points at one thing and the lint reports
another.

- `segment.py` — markdown → line records (fences, heading paths, kinds)
- `textmetrics.py` — normalize, fingerprint, content terms, Jaccard
- `project.py` — root discovery, `meta.yaml`, unit resolution, standalone mode
- `gitblame.py` — line → (sha, date), one subprocess call per file
- `selection.py` — THE stratified quota. One ranking, shared by emission and by
  every check on emission; do not add a second one anywhere
- `coverage.py` — the coverage record and the cumulative audit ledger
- `anchors.py` — resolve a reference by content, distinguishing MOVED from CHANGED

The calibration comments in `textmetrics.py` and `build_concept_dossier.py` record
measurements, not opinions — what was tried, what the numbers were, and why the
obvious approach fails. Read them before changing a threshold.
