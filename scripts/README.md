# scripts/

Deterministic checks. No model runs any of these: anything mechanical belongs
here, and the agents keep the judgement.

## Requirements

Python 3.10+ and PyYAML (`pip install pyyaml`). Optional: `jsonschema` (the gate
validates findings files with it, and with a built-in fallback otherwise) and
`git` (the incomplete-fix detector compares blame; everything else works without).

## Common behaviour

Every script takes `--root`. The book-level scripts also take `--units`, so they
run over a book this skill never scaffolded:

```bash
python scripts/lint_render.py --root /path/to/book --units "final/ch-*.md"
```

The per-unit scripts take `--unit unit-NN` (and `--file` for another text than
the default). Every relative path they take — `--file`, `--json`, `--units`,
`--before`/`--after`, `apply-edits` — resolves against the project root, never
the working directory. With no `--root` the root is the nearest ancestor holding
`bible/meta.yaml` (gate scripts: or `final/`), and units resolve to
`final/unit-*.md`, then `final/ch-*.md`, then
`final/*.md`, in reading order (ch-2 before ch-10). Files are read as UTF-8 with
or without BOM and NFC-normalized; a file in another encoding is decoded as cp1252
and reported (`lint_render`: a major `encoding` finding), never a crash. The
language is `project.language_variant` → `conventions.language_variant` →
`project.language` → `en-US`; word lists live in `lexicons/<lang>.yaml`
(`bookkit/lexicon.py`), extended by `bible/lexicon.yaml`.

## What each one is for

| Script | Phase | Blocks? |
|---|---|---|
| `manuscript_gate.py` | 4.5 | computes the verdict; exit 0 converged · 1 not · 2 ERROR |
| `lint_render.py` | 4.5 (MG-5) + build preflight | exit 1 at `--fail-on` (default critical) |
| `check_fixed_defects.py` | 4.5 (MG-7) | a reappearance is `critical` in the gate |
| `sync_manuscript.py` | 4.5 sweep + build preflight | `--check` exits 1 on drift |
| `build_concept_dossier.py` | 4.5 (MG-1), claim index | no — prepares agent input |
| `bootstrap_probes.py` | once, before the above | no |
| `extract_rule_candidates.py` | 4.5 (MG-2) | no — prepares agent input |
| `validate_claim_index.py` | 4.5, post-edit, preflight | **no, by design** |
| `resolve_anchors.py` | 4.5 + after any fix pass | **no, by design** |
| `extract_code_corpus.py` | 4.5 (MG-6) | no |
| `lint_style.py` | Proofreader | no — advisory |
| `pipeline_step.py` | Phase 2–3 brackets | `check`/`ready`/`approve`/`sign`/`apply-edits` exit 1 · `done` 1 re-dispatch, 3 R3/R4 pause, 4 contract violation · `snapshot` 2 refused · `checks` 2 tool failed, 3 story blocker · any command 2 on a `schema_version` other than 3.4 or a missing/unknown `project.profile` |
| `count_rhet.py` · `check_identifiers.py` · `check_role_diff.py` | per unit, via `pipeline_step.py` | no — counts into `checks.json` |
| `lint_fiction.py` · `check_story.py` | literary: per unit, and 4.5 (MG-T, MG-S) | `check_story` exit 1 on a blocking finding (`--manuscript`: also major); 2 on a missing/unknown profile or a `schema_version` other than 3.4 |

`validate_claim_index.py` and `resolve_anchors.py` exit 0 even with findings: a
hard gate on prose gets switched off, and then there is no warning either. The
gate reads their JSON and decides.

### Per-unit scripts (Phase 3)

The orchestrator calls `pipeline_step.py`; it calls the others. Contracts:
`references/pipeline.md`.

- `pipeline_step.py` — `check unit-NN <agent> [--cycle N] [--human-override]`
  (inputs exist and are fresh; records the dispatch in
  `drafts/unit-NN/.dispatch.json`; literary Writer: the full `ready` result
  (R3), not only the unit's cast; Critic/Proofreader: `checks.json → source_sha1`
  must match the current `humanized.md` and the story check re-runs live — a
  story block is never overridable; the Proofreader needs the Critic's PASS
  recomputed from `scorecard.yaml`; cycle > 1 reads `loop-state.json`) · `done
  unit-NN <agent> --tier T --cycle N` (output usable and written after the
  dispatch, `runs.tsv` row, role diff `role-diff-<agent>-c<N>.json`, Critic
  verdict recomputed; exit 1 re-dispatch · 3 R3/R4 pause (literary Writer:
  `ready` fails or a story blocker on the page) · 4 contract violation —
  re-dispatch once, the second escalates) · `clean` · `snapshot unit-NN --reason
  critic|tr|adversarial|human [--target writer|editor|humanizer]` (snapshots
  `humanized`/`draft`/`edit`/`scorecard` to `.c<N>` and opens the next cycle
  with its worklist and the Writer's REVISE source) · `checks` (→ `checks.json`
  + `checks.md`) · `ready` · `approve unit-NN` (`proofread.md` → `final/`,
  comments stripped; nonfiction keeps `SOURCE`/`ARTIFACT`; literary refuses a
  failing `ready` and any story block, `--force` included) · `apply-edits
  EDITS.yaml [--dry-run]` (literary: `ready` must pass and every edited unit is
  story-checked — check_story `--unit` blocking, lint_fiction `unknown_name`
  major / `mentioned_on_stage` — before anything is written) · `sign <slug> --by
  NAME` (literary: the human approved the sheet → `status: complete`,
  `signed_on` today, `signed_by`, `signed_hash`; refuses an incomplete sheet).
- `count_rhet.py --unit unit-NN [--file F] [--json OUT]` — the `rhet` counts,
  AI vocabulary, hedges, narration em-dashes, sentence-length runs; quotas from
  the `rhetoric_budget:` fence of `bible/voice-profile.md`.
- `check_identifiers.py --build-index` (at setup, from `bible/sources/`; a hand
  `# allow` section survives) · `--unit unit-NN [--file F] --json OUT` or
  `--units GLOB` — identifiers no source defines (`tech_a-4`).
- `check_role_diff.py --role editor|humanizer|proofreader --before A --after B
  [--budget R]` — sentence diff: Editor added prose, Humanizer touched ratio vs
  budget, Proofreader change list.
- `lint_fiction.py --unit unit-NN [--file F]` or `--book` — tics, names
  (`unknown_name` = NEW-CHARACTER?: mid-sentence, not in the pack's
  `common_words` and never lowercase, or in a speaker/actor position; prose,
  table cells, section headings, italics, ALL CAPS of 5+ letters and internal
  capitals are all scanned — code fences are not; `mentioned_on_stage` = a
  `world.md` word, place or name, or an outline location that speaks or acts),
  dialogue form, render hazards in prose.
- `check_story.py --ready-to-draft | --unit unit-NN | --manuscript` — R1–R4:
  sheets (complete, 3-word narrative fields, `signed_on` + `signed_hash` —
  `CHAR-UNSIGNED-CHANGE` after an edit; every file in `bible/characters/` except
  `_extras.md` is a sheet — `CHAR-INCOMPLETE`/`CHAR-DUPLICATE`), arcs, ending
  (`ENDING-NOT-DELIVERED` also for a final unit under max(300 words, 30% of its
  `target_words`)), ledger (`LEDGER-MISSING`, `LEDGER-INVALID`,
  `LEDGER-UNKNOWN`), new characters on the page and in scene cards, world words
  and extras' label words on stage (`EXTRA-PROMOTE`). Placeholders:
  `bookkit/placeholder.py`.

In the gate, MG-S runs `check_story.py --manuscript --json <round>/story.json`
and MG-T `lint_fiction.py --book --json <round>/fiction.json`; exit 0 or 1 with
valid JSON is a result, anything else an ERROR. A missing `lint_fiction.py`
leaves a `blocked` coverage record; a missing `check_story.py` is an ERROR (R1–R4
are not a coverage question), and literary convergence re-runs `check_story.py
--manuscript` at verdict time.

### The gate's state

`manuscript_gate.py` keeps, under `reviews/manuscript-gate-<run>/`: `state.json`
(rounds, verdicts, convergence, each round's manuscript and unit hashes and
finding keys — the source of truth), `findings.jsonl` (every finding of every
round, content-keyed, `open|fixed|refuted|accepted-risk`; a file missing keys
`state.json` recorded is an ERROR, "findings store truncated"; change a status
with `--resolve KEY --status S --note N` — deterministic and configuration
findings are never `fixed`/`refuted` by hand, `accepted-risk` only for a
non-critical MG-5/MG-T or a minor MG-7; agent findings: `fixed` needs a note
and a changed text, `refuted`/`accepted-risk` a 20+ character note, never
accepted-risk for a critical; literary R1/R2 findings nothing by hand),
`subjects.json` (coverage: `pending | audited@hash | sampled@hash`), and
`GROUNDING.md`. Every sweep deletes the round's tool outputs first; a tool that
exits non-zero or writes no JSON makes the verdict ERROR. Waivers need real
who/why/debt (no placeholders, reason and debt 20+ characters); an executable
validation surface needs `evidence: <path>` to an existing runner output.
Details: `references/manuscript-gate.md`.

### The two emitters

`build_concept_dossier.py` and `extract_rule_candidates.py` write
`round-N/coverage-<check>.json` (every eligible subject with the hash of what an
audit of it reads, what was emitted, what was skipped, the ranked cut) and take
`--subjects <run>/subjects.json` to skip subjects already audited at their
current hash — they leave the pool, never the denominator. Rule ids are
content-derived (`<unit>-<term>-<hash6>`). With no language pack,
`extract_rule_candidates.py` pairs prose naming a backticked identifier with the
code using it, and says so. `--report` prints the table and writes nothing.

## A typical run

```bash
python scripts/bootstrap_probes.py                        # once
python scripts/build_concept_dossier.py --probe-report    # tune the noisy probes
python scripts/build_concept_dossier.py --emit-index

python scripts/manuscript_gate.py --round 1               # sweep + prepare + verdict
#   ... dispatch the auditors it lists ...
python scripts/manuscript_gate.py --round 1 --verdict-only
python scripts/manuscript_gate.py --resolve <key> --status refuted --note "<20+ chars of counter-evidence>"
python scripts/manuscript_gate.py --round 2               # next slice + edited subjects
python scripts/resolve_anchors.py --heal                  # after a fix pass
python scripts/manuscript_gate.py --deterministic-only    # any time, seconds
```

## Project configuration

- `bible/audit-config.yaml` — fix-run commits, running-example names, code kinds,
  thresholds (`templates/audit-config.yaml`). Optional.
- `bible/lint-config.yaml` — pins, forbidden terms, casing watchlist, dash style
  for `lint_style.py` (`templates/lint-config.yaml`). Optional.
- `bible/concept-probes-tuned.yaml` — hand-written probes; they win and are never
  overwritten. `home_cap` per probe.
- `bible/rule-probes-tuned.yaml` — narrowings for MG-2 rules
  (`templates/rule-probes-tuned.yaml`). Narrowing is a claim about scope.
- `bible/fixed-defects.yaml` — formulations that must not return (MG-7;
  `templates/fixed-defects.yaml`). Pin the claim, not the code.

## `bookkit/`

Shared primitives; the checks must agree on what a passage *is*.

- `textio.py` — the one reader (BOM, NFC, cp1252 recorded) and junction-safe paths
- `segment.py` — markdown → line records (CommonMark fences, heading paths, kinds)
- `textmetrics.py` — normalize, fingerprints (code spans verbatim), Jaccard
- `project.py` — root discovery, `meta.yaml`, units, language, `as_list`
- `gitblame.py` — line → (sha, date), one subprocess per file
- `selection.py` — THE stratified quota; do not add a second ranking anywhere
- `coverage.py` — the subjects manifest and the per-round coverage record
- `anchors.py` — resolve a reference by content (MOVED vs CHANGED)
- `schema.py` — findings-file validation
- `lexicon.py` — language packs; `at_root()` resolves CLI paths
- `verdict.py` — the rubric's verdict computation (`references/rubric.md`), in code

Calibration notes and measurements: `docs/rationale/gate.md`.

## Tests

```bash
python scripts/selftest.py        # -v every assertion · -k PATTERN a subset
```

Built-in regression tests, then every `tests/selftest_*.py` module's `TESTS`
(`fn(tmp, check, run)`); a module that fails to import is a FAIL, not a skip.
Never delete a case to go green.
