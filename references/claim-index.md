# Claim index — knowing what else says the same thing

When you edit one passage, the pipeline cannot tell you that three others say the
same thing and are now wrong. That is the mechanism behind every incomplete fix,
and an incomplete fix is worse than the original defect: the document now
contradicts itself and both sides look reviewed. Why:
`docs/rationale/gate.md#claim-index`.

`bible/claim-index.yaml` records, per concept, every passage that makes a claim
about it, which one is canonical, and which passages carry the same sub-claim.
Template: `templates/claim-index.yaml`. Tooling: `scripts/build_concept_dossier.py`
(build) and `scripts/validate_claim_index.py` (check).

---

## Keyed by fingerprint, not by line

A site's key is the **fingerprint** of its passage: prose normalized (case,
punctuation, markdown folded, NFC), **code spans kept verbatim** — so a fix to
`` `Peek(v,-1)` `` changes the fingerprint even though no word changed.

| What happened | Fingerprint | Verdict | What the system does |
|---|---|---|---|
| Passage moved (lines inserted above) | still present | `MOVED` | `--fix` repairs the location |
| Passage edited or deleted | gone | `CHANGED` | flags its siblings, emits `PROPAGATE` |
| Whole unit gone | file absent | `GONE` | dead entry, reported |

Also reported: `MULTI-CANON`, `NO-CANON`, `BAD-ROLE`, `BAD-LOC`. Two rules protect
the signal-to-noise ratio:

- `PROPAGATE` fires only to a passage's `related` sites (the three or four with
  the same sub-claim), falling back to siblings in the same file — never to every
  site of the concept.
- The validator is a **warning, never a hard gate**: it exits 0 with findings
  (`--fail-on-changed` exists for a CI job that wants to block). A hard gate on
  prose gets switched off, and then there is no warning either. With `--json` it
  always writes its result, `{"absent": true}` when there is no index yet.

---

## Wiring — all three are mandatory

1. **Manuscript gate, every sweep** (`references/manuscript-gate.md`): the
   validator's JSON goes into the round; `CHANGED` sites of accepted fixes and
   their `PROPAGATE` siblings are the next round's review set.
2. **After accepted polish-pass edits** (`references/pipeline.md` § Polish pass):
   run the validator the moment an edit lands in `final/`; its `PROPAGATE` lines go
   into the same human packet as the diff.
3. **Build preflight** (`references/build-export.md`), `--quiet`: open
   `PROPAGATE` warnings are printed with the build report, not blocking.

With no index yet all three degrade to a one-line notice.

---

## Roles

The generator seeds roles; the audit decides them; a decision already made is
never overwritten (it is matched by fingerprint).

| Role | Meaning |
|---|---|
| `CANON` | The definitive statement. **Exactly one per concept.** |
| `repeats` | Restates CANON elsewhere. |
| `derives` | Draws a consequence from CANON. |
| `qualifies` | Adds a condition or an exception. |
| `summary` | A recap bullet: the second side of a contradiction, never the first. |
| `example` | Inside an exercise or worked example. |
| `crossref` | A pointer, not a claim. |

Seeding: the highest-scoring claim in the home unit becomes provisional CANON,
summary bullets `summary`, exercise passages `example`, the rest `repeats`. The
concept auditor corrects it in MG-1. One CANON keeps contradiction reports
actionable ("site X contradicts CANON") instead of an argument among equals.

Claims are scored with the book's language pack (`scripts/lexicons/<lang>.yaml`);
English keeps its calibrated patterns. With no pack for the language only
quantities score, and the builder says so.

---

## Positive verdicts are first-class

```yaml
  reduction_wildcard:
    verified_against: "bible/sources/manage-data/manage-data.md:12177"
    do_not_touch: true
    note: >
      The 100× figure is against the database, NOT against standard mode. A
      finding against this passage is REFUTED unless it cites an official source
      that contradicts that page.
```

Whenever a concept is checked against a source and found correct, write
`verified_against`. Whenever a finding is rejected as not-a-defect, write
`do_not_touch: true` **with the counter-evidence in `note`** — an anchor without a
reason gets overruled. These fields, and `role`, survive every regeneration, even
while a concept has no claim-scored passage. The validator prints them on any
`PROPAGATE` touching the concept, and the gate copies them into GROUNDING.md.
Why: `docs/rationale/gate.md#positives`.

---

## Building it

```bash
python scripts/bootstrap_probes.py                        # once: KG, else glossary, else frequency
python scripts/build_concept_dossier.py --probe-report    # tune the noisy probes first
python scripts/build_concept_dossier.py --emit-index
python scripts/validate_claim_index.py --fix              # --fix repairs MOVED
```

**Tune the probes** in `bible/concept-probes-tuned.yaml`, which wins over the
generated `bible/concept-probes.yaml` and is never overwritten. The concept that
contradicts itself is usually finer-grained than a graph node. Fields: `id`,
`name`, `home`, `include`, `exclude`, `homonym_guard`, `case_sensitive`,
`home_cap`.

- `case_sensitive: true` for keywords that are also ordinary words (`SET`,
  `KEEP`, `JOIN`, `LOAD`), or the probe returns triple-digit junk.
- `homonym_guard` does not filter: it fills a separate dossier section, because a
  merged homonym is the number-one false contradiction.
- `home_cap` raises the home-unit cap for one concept — the way out of a sampled
  (trimmed) dossier.

The frequency bootstrap (no graph, no glossary) tokenizes Unicode words and keeps
phrases spanning two or more units; its output is deterministic.

## The incomplete-fix detector

```yaml
# bible/audit-config.yaml
fix_run_commits: ["3e6829b", "5bdbcc8"]   # short shas of fix passes
persona_names: ["Ana", "Carlos"]          # running-example characters
```

A related pair where **one side has blame in a fix run and the other does not** is
the signature of a fix that landed in 1 of N sites; dossiers list them as
`d2_candidates`, found without a model. For a retrofit, pass `--fix-run-commit`
and `--persona` instead of writing config.

## Retrofit

```bash
python scripts/bootstrap_probes.py --root /path/to/book --units "final/ch-*.md"
python scripts/build_concept_dossier.py --root /path/to/book --units "final/ch-*.md" --emit-index
```

## See also

- `references/manuscript-gate.md` — MG-1, which reads the dossiers
- `references/pipeline.md` § Polish pass · `references/build-export.md`
- `references/knowledge-graph.md` — where probes come from when there is a graph
