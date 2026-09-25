# Validation surface — machine-checkable content per domain

Almost every nonfiction project has *some* surface a machine can check: code
that runs, SQL that parses, YAML that validates, statistics that recompute,
citations that resolve, identifiers that exist. A **validation surface** pairs
a content pattern with a mechanical check. `bible/meta.yaml →
validation_surface.surfaces` declares which apply; the Technical Reviewer loads
the sub-prompt of each declared surface from this file (or from an optional
pack in `references/surfaces/`) and runs it over the draft.

## Shape

```yaml
validation_surface:
  identifier_allowlist: []           # names check_identifiers.py must accept (tool names, fixtures)
  surfaces:
    - surface: python_exec
      applies_to: ["drafts/**/*.md", "final/**/*.md"]
      runner: "docker run --rm -v $PWD:/w python:3.12 python /w/snippet.py"
      executable: true               # always declare it
      evidence: reviews/runner/python_exec.txt   # the runner's saved output (MG-6)
      pins: { python: "3.12" }
```

`executable` says whether the content is code a machine could run. Declare it:
MG-6 reports "cannot tell" when it is missing, never "no". `evidence` is the
path (under the project) of the runner's saved output from the last run over
the book: MG-6 accepts an executable surface only when that file exists and is
not empty. The `runner` string describes how to run it; it is never evidence
that it ran.

## Reasoning is not verification

A surface whose `runner` is `reviewer-only` or `internal:*` has been reasoned
about, not verified — and a surface with a real runner but no `evidence` file
has not been shown to have run. Both are legal; they are not the same as a run
— broken code does not always fail loudly (an expression that returns zero rows
reads like a correct query over empty data). So at the manuscript gate an
executable surface without an existing `evidence` file needs a complete
`waivers` entry in `project-status.yaml` (who, why, debt — real text, reason
and debt 20+ characters) **and** an entry in the verification plan it names
(`references/verification-plan.md`); missing either, MG-6 raises a `major`.
Units with tagged code fences and no surface declared at all are a `major` too.
Why: `docs/rationale/pipeline.md#reasoning-is-not-verification`.

Findings go into `tech-review.md` under the axis each surface names: A
(mechanical correctness), B (grounding), C (reference integrity, papers).

## Catalogue

### Identifier check (always on for nonfiction — not declared)

`python scripts/check_identifiers.py`
checks every call pattern and backticked identifier against
`bible/identifier-index.txt` (built from `bible/sources/*.md` with
`--build-index`) ∪ glossary ∪ `identifier_allowlist` ∪ the code language's
keywords. Unknowns are "possibly invented" until the Reviewer finds them in a
source. Axis A. Feeds `tech_a-4`.

### `python_exec` · `js_node_exec`

Runnable snippets. **Needs** a sandboxed interpreter of the pinned version
(Docker recommended; a lockfile if snippets import packages).
`executable: true`. **Sub-prompt**: extract each fenced block with its visible
setup, run it, compare the output with what the text claims. Error or mismatch
→ Axis A.

### `bash_exec`

Shell snippets. **Needs** a sandbox reproducing the assumed environment —
declare it only where the commands are the product. **Sub-prompt**: flag
destructive operators (`rm -rf`, raw device writes) for human review before
running; run the rest and verify output.

### `sql_dialect_check`

SQL parses against the declared dialect (postgres | mysql | sqlite | bigquery |
snowflake | mssql | oracle). **Needs** a parser (`sqlfluff` with the dialect,
or a database in parse-only mode). **Sub-prompt**: parse each ```sql block;
flag parse errors and syntax from another dialect.

### `yaml_schema_validate` · `json_schema_validate`

Blocks validate against a schema, usually in `bible/schemas/`. **Sub-prompt**:
extract each block, validate, report violations.

### `linter`

Static analysis for code in the document. **Needs** a linter and its config.
**Sub-prompt**: lint each block in isolation; report what a reader would hit.

### `doc_cross_ref`

Every function, command, flag or config key the unit names exists in the
grounding sources. The identifier check does the mechanical half; this
surface adds the judgement: **Sub-prompt**: for each identifier
`check_identifiers.py` could not place, and each flag or config key in prose,
search the sources' `.md` extracts; not found → "possibly invented", the Writer
cites or removes it. Axis B.

### `proof_recheck`

Each step of a derivation follows from the previous by a named rule. **Needs**
a proof assistant (`lean`, Coq, Isabelle) when proofs are formalized —
`executable: true`; otherwise a reasoning surface, `executable: false`.
**Sub-prompt**: for each derivation, check each step's justification against a
known identity or rule; flag unjustified transitions. Axis A.

### `citation_check` (visible-academic profiles)

Every visible citation resolves, attributes correctly, follows the declared
style, and is not retracted. **Needs** `sources.md`, a current `claims-map.yaml`,
`citation_style`; retraction checks need a connected tool (Zotero/scite,
citecheck, arXiv, OpenReview) — optional, but the skip is explicit.
**Sub-prompt**:

> 1. **Resolution** — the work is in `sources.md` or a claims-map evidence
>    entry; neither → potentially invented (Axis C): add the source with human
>    sign-off, or remove the citation. Never "probably real".
> 2. **Attribution** — the claim matches what the claims map records for that
>    source; otherwise Axis C with claim, citation and what the source
>    supports.
> 3. **Formatting** — form and consistency per `citation_style`; one Axis A
>    finding per pattern.
> 4. **Retraction** — with a tool, query each identifier (retracted or
>    expression of concern → Axis C, critical); without one, write
>    "retraction check: unavailable in this environment".

### `stats_check`

Reported statistics are internally consistent. A **reasoning surface**
(`executable: false`) unless an analysis script ships — then declare
`python_exec` too and let the script be the authority. **Sub-prompt**:

> Collect every number (percentages, Ns, means, p-values, CIs, effect sizes,
> table cells) and check: partitions sum to their totals; the same sample keeps
> the same N, exclusions reconcile; p-values, CIs and significance language
> agree; prose numbers equal their table cells; derived values recompute. Show
> the arithmetic in each finding. Axis A. This catches internal inconsistency
> only — say so when credibility rests on the data or the method.

### `empty`

No machine-checkable content (a philosophical essay). Axis A auto-passes; the
report says "No validation surface". `executable: false`, and mean it: `empty`
on a project that ships code is an undeclared skip.

## Optional packs

Domain-specific surfaces live outside this file so they load only where they
apply. A pack is a markdown file in `references/surfaces/` with the same entry
shape; declare its surfaces in `meta.yaml` as usual and the Reviewer loads the
pack. Shipped: `references/surfaces/qlik.md` (Qlik Sense set analysis, load
scripts, chart expressions).

## Choosing surfaces (Phase 1)

Declared in setup (`references/setup.md`), per project:

1. Executable code? The matching `*_exec`, `executable: true`, versions pinned.
   No runner here? Say so now — the waiver and plan are scope, not an
   afterthought.
2. Declarative configs? A `*_schema_validate` plus `linter`.
3. A tool-specific language? Its surface (SQL, an optional pack) or a custom
   one.
4. Leans on official documentation? `doc_cross_ref`.
5. Visible citations or statistics? `citation_check`, `stats_check`.
6. Anything else: a custom surface — id, `applies_to`, `runner` (even
   `internal:prose_audit`), `pins`. Ask: what is the cheapest machine check
   that rejects something a reader would hit as an error?

No surfaces declared → the Reviewer writes "Validation surface empty — Axis A
is prose audit only", and the Critic carries it to the human.
