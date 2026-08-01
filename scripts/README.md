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
| `extract_code_corpus.py` | 4.5 (MG-6) | no |
| `lint_style.py` | Proofreader | no |

`validate_claim_index.py` exits 0 even with findings, and that is deliberate: a
hard gate on prose gets switched off within a week, and then you have neither the
gate nor the warning. The manuscript gate reads its JSON and decides what blocks.

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
  generated ones and are never overwritten.

## `bookkit/`

Shared primitives. Everything imports from here rather than re-deriving
segmentation or similarity, because the checks have to agree on what a passage
*is* — otherwise the claim index points at one thing and the lint reports
another.

- `segment.py` — markdown → line records (fences, heading paths, kinds)
- `textmetrics.py` — normalize, fingerprint, content terms, Jaccard
- `project.py` — root discovery, `meta.yaml`, unit resolution, standalone mode
- `gitblame.py` — line → (sha, date), one subprocess call per file

The calibration comments in `textmetrics.py` and `build_concept_dossier.py` record
measurements, not opinions — what was tried, what the numbers were, and why the
obvious approach fails. Read them before changing a threshold.
