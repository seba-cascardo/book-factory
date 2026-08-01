# Validation Surface — Machine-Verifiable Checks per Domain

The Technical Reviewer audits claims, code, versions, and citations against
whatever surface the unit's content exposes. Not every project has
executable code. But almost every nonfiction project has *some* surface a
machine can check — and leaving it to the Reviewer's free-form prose audit
wastes its leverage.

A **validation surface** is a pairing of (content pattern in the document)
with (a mechanical check that can verify that content). The project's
`bible/meta.yaml` declares which surfaces apply under
`validation_surface.surfaces:`. At unit time, the Technical Reviewer loads
the sub-prompt for each declared surface from this file and runs it over
the draft.

## Surface shape, and the `executable` flag

```yaml
validation_surface:
  surfaces:
    - surface: python_exec
      applies_to: ["drafts/**/*.md", "final/**/*.md"]
      runner: "docker run --rm -v $PWD:/w python:3.12 python /w/snippet.py"
      executable: true              # declare it — see below
      pins: { python: "3.12" }
```

`executable` says whether this surface's content is code that a machine could
actually run. **Declare it explicitly.** MG-6 in the manuscript gate infers it
from the surface id when it is missing, and reports "cannot tell" rather than
guessing "no" — because guessing "no" turns undeclared debt into a silent pass,
and that is how a book shipped with 3,200 lines of code verified only by
reasoning.

## Reasoning is not verification

A surface whose `runner` is `reviewer-only` or `internal:*` has not been
verified. It has been *reasoned about*. Both are legitimate; they are not the
same, and the difference is measurable: the first time eight tests from one such
book were run on a real engine, the results contradicted what the reviewer had
concluded on paper.

The failure mode is worse than it sounds, because broken code does not always
fail loudly. An expression that silently returns zero rows looks exactly like a
correct query over an empty result. A reviewer reasoning from documentation
cannot see that. An engine can.

So `reviewer-only` remains a legal choice — sometimes there is no sandbox and
that is a real constraint — but it is no longer a **silent** one. At the
manuscript gate, an executable surface with no real runner must carry:

- a `waivers` entry in `project-status.yaml` (who waived it, why, and the debt), **and**
- a test plan as a first-class deliverable — see `references/test-plan.md`.

Missing either, MG-6 raises a `major` and the book cannot reach `complete`. The
point is not to force a sandbox into existence. It is that shipping unverified
code should be a decision somebody made, visible in the done report, rather than
a configuration value nobody looked at.

Findings integrate into `tech-review.md` under Axis A (mechanical
correctness), Axis B (grounding / mental models), or Axis C (reference
integrity, scientific-paper profile) — each surface below says where its
findings belong.

## Why this is not "Code Executor only"

"Run the code" only applies if the project has runnable code. Qlik Sense
books, SQL-dialect books, math textbooks, cloud architecture guides,
scientific papers — none of them compile and execute in the Python sense.
But every one of them has *some* surface:

- Qlik Sense: expressions and load scripts have deterministic grammars
  and documented function lists. A syntactic linter and a doc
  cross-reference catches the majority of factual errors a reader
  would hit.
- SQL dialect: every dialect has a parser; use it to validate that the
  SQL in the document actually parses against the target dialect.
- Cloud architecture: CloudFormation / Terraform snippets can be
  `validate`-d against schema without deploying. Diagrams that follow
  a DSL (PlantUML, Mermaid) can be rendered to detect syntax errors.
- Math / proof: proof assistants (Lean, Coq) for formal; re-derivation
  walkthrough for informal.
- Papers: every visible citation either resolves to a known source or
  it does not; reported statistics are either arithmetically coherent
  or they are not.

The surface catalog below is not exhaustive. When you set up a project in
a domain that is not listed, think: *what is the cheapest machine check
that rejects something the reader would hit as an error?* That is the
surface to declare.

## Catalogue of standard surfaces

Each surface has: an ID, what it checks, what it needs, and the
sub-prompt guidance the Technical Reviewer uses when loaded.

### `python_exec`

**Checks**: runnable Python snippets in unit bodies and code blocks.

**Needs**: `runner` pointing at a sandboxed Python of the pinned
version. Docker recommended.

**Sub-prompt**: For each fenced ```python block, extract it (with any
visible setup), run in the sandbox, compare observed output against
what the text claims the output is. If output differs or the snippet
errors, flag Axis A.

### `js_node_exec`

Same shape as `python_exec`, for Node.js. Pin the node version.

**Needs**: `runner` pointing at a sandboxed Node of the pinned version, plus a
lockfile if the snippets import anything. `executable: true`.

### `bash_exec`

**Checks**: shell-command snippets (```bash / ```sh / ```shell blocks).

**Needs**: a sandbox that reproduces the document's assumed environment.
Risky — declare only for projects where the shell commands are the
product (sysadmin books, CLI tutorials).

**Sub-prompt**: Extract each command, check for destructive operators
(`rm -rf`, `> /dev/sda`, etc.) and flag those for human review before
running. For safe commands, run and verify output.

### `sql_dialect_check`

**Checks**: SQL snippets parse against the declared dialect (postgres |
mysql | sqlite | bigquery | snowflake | mssql | oracle).

**Needs**: `runner` that can parse SQL without executing (e.g.,
`sqlfluff` with dialect, or a DB in parse-only mode).

**Sub-prompt**: For each ```sql block, run the parser with the target
dialect. Flag parse errors and dialect-specific syntax used outside its
dialect.

### `yaml_schema_validate` / `json_schema_validate`

**Checks**: YAML/JSON in unit bodies validates against a declared schema.

**Needs**: schema file, usually in `bible/schemas/`.

**Sub-prompt**: Extract each YAML/JSON block; validate. Report violations.

### `linter`

**Checks**: static analysis passes for code in the document.

**Needs**: linter name + config file.

**Sub-prompt**: Run the linter on each code block in isolation. Report
findings the reader would encounter.

### `qlik_set_analysis`

**Checks**: Qlik Sense set analysis expressions match the documented
grammar (outer braces, set operators, element functions).

**Needs**: `runner: "internal:qlik_set_analysis_linter"` — a
pattern-based lint pass, or an external linter.

**Sub-prompt**:

> You are checking Qlik Sense set analysis expressions in a unit. A
> set expression lives inside `{...}` braces inside aggregation calls:
> `Sum({<dim={'val'}>} measure)`. Verify:
>
> 1. Every `{<...>}` is enclosed in an aggregation function.
> 2. Inside the braces, selectors use `dim={values}`, `dim={"search"}`,
>    or `dim-=` / `dim+=` for modifiers — not SQL syntax.
> 3. Element functions (`P()`, `E()`, etc.) are used only inside set
>    expressions, not as standalone aggregations.
> 4. Operators between modifiers are `+ - * /` (set ops), not `&` `|`.
> 5. Functions named exist in the pinned Qlik version (cross-reference
>    against the Qlik reference in `bible/sources/`).
>
> Flag each finding as Axis A (incorrect syntax) or Axis B (wrong
> mental model of set analysis, e.g., using `{<dim=val>}` without
> quoting literal values — Qlik tolerates it but it's a trap; the text
> should teach the safer form).

### `qlik_load_script`

**Checks**: Qlik Sense load scripts — directives (`LOAD`, `FROM`,
`STORE`, `LET`, `SET`), field naming, `AutoGenerate` blocks.

**Needs**: a reachable Qlik environment to reload against, or
`runner: "internal:qlik_load_script_lint"` for a pattern-based pass.
`executable: true` either way — a load script is code, and a lint is not a
reload. Without a real environment this surface owes a test plan.

**Sub-prompt**:

> You are checking Qlik Sense load scripts (the data-loading language,
> not the frontend expression language). Verify:
>
> 1. Every `LOAD` ends with a source clause (`FROM`, `RESIDENT`,
>    `INLINE`, `AutoGenerate`, or a preceding `LIB CONNECT TO`).
> 2. `INLINE` blocks have matching `[` `]` or `"` `"` delimiters and a
>    consistent column count per row.
> 3. `STORE INTO` has a valid path format (`lib://...` or relative).
> 4. Variables use `LET` (eval) vs. `SET` (literal) semantically
>    correctly — if the script uses `SET x = Now()`, the variable will
>    hold the literal string `Now()`, not the evaluated date. Flag these.
> 5. `Subroutine` / `Call` pairs match. Unused subroutines or missing
>    `End Sub` are errors.
> 6. Functions named exist in the pinned Qlik version.

### `qlik_expression`

**Checks**: Qlik frontend chart expressions — valid function names,
balanced parens, aggregations not nested without inner `Aggr()`, valid
field references.

**Needs**: an app to evaluate the expressions in, or
`runner: "internal:qlik_expression_lint"`. `executable: true`. This is the
surface where reasoning fails most quietly: a malformed set expression returns
zero rows rather than an error, which reads as a correct query over empty data.

**Sub-prompt**:

> You are checking Qlik Sense frontend expressions (for charts and KPIs).
> Verify:
>
> 1. Every function name exists in the pinned Qlik version. Common trap:
>    functions renamed or dropped between releases.
> 2. Aggregations (`Sum`, `Count`, `Avg`, etc.) wrap the non-aggregated
>    dimension. Nested aggregations need `Aggr(..., dim1, dim2)`.
> 3. Parentheses balance. String-delimiter quotes balance.
> 4. `If(` expressions have 2 or 3 arguments — flag the common miss of
>    not providing an `else` value when the chart assumes one.
> 5. Field names referenced exist or are declared. (If the unit doesn't
>    show the data model, this is advisory.)

### `doc_cross_ref`

**Checks**: every function/command/flag mentioned in the unit exists
in the declared grounding sources.

**Needs**: `bible/sources/` populated.

**Sub-prompt**: For every code-formatted identifier in the unit
(function names, CLI flags, config keys), grep the grounding library's
`.md` extracts. If not found, flag as "potentially invented" and
require the Writer to provide a citation or remove it. Axis B.

### `proof_recheck`

**Checks**: mathematical derivations — each step in a derivation
follows from the previous by a named rule.

**Needs**: a proof assistant (`runner: "lean --run"`, Coq, Isabelle) when the
project formalizes its proofs — `executable: true`. Otherwise this is a
**reasoning surface**: no runner, the Reviewer re-derives by hand.
Declare `executable: false` in that case, so it is a stated choice rather than
an unexamined default.

**Sub-prompt**: For each derivation (sequence of `=` or `⟹` steps),
verify the justification given for each step corresponds to a known
identity/rule. Flag unjustified transitions. Axis A.

### `citation_check`

**Checks**: every visible citation in the unit resolves to a known
source, attributes correctly, is formatted per the declared style, and
does not cite retracted work.

**Applies to**: profiles with a `visible-academic` citation policy
(scientific-paper). Invisible-citation profiles get the equivalent
coverage from `doc_cross_ref` plus the Reviewer's normal
source-comment spot checks.

**Needs**: `bible/sources/sources.md` populated; `bible/claims-map.yaml`
current; `citation_style` declared in `bible/meta.yaml`. Retraction
checking additionally needs a connected MCP tool that can query
retraction status (Zotero/scite, citecheck, arxiv, openreview) —
optional, but the skip must be explicit.

**Sub-prompt**:

> For every visible citation in the unit (author-year, numeric, or
> footnote form per the declared `citation_style`):
>
> 1. **Resolution.** The cited work exists in `bible/sources/sources.md`
>    or as an evidence entry in `bible/claims-map.yaml`. A citation that
>    resolves to neither is potentially invented — flag Axis C and
>    require the Writer to add the source to the library (with human
>    sign-off) or remove the citation. Never wave an unresolvable
>    citation through as "probably real": an invented reference is the
>    single most damaging failure a paper can ship.
> 2. **Attribution.** The claim attached to the citation matches what
>    the claims-map records for that source. Citing a real paper for
>    something it does not say is worse than a formatting error and far
>    harder for the human to spot — flag Axis C with the claim, the
>    citation, and what the claims-map/source actually supports.
> 3. **Formatting.** The citation's form matches `citation_style` and is
>    consistent across the unit: bracket vs. parenthetical style, et-al
>    thresholds, punctuation, numeric ordering. Formatting findings are
>    Axis A — report one finding per pattern, not one per instance.
> 4. **Retraction.** When a retraction-capable MCP tool is connected,
>    query each cited DOI/identifier; flag retracted or
>    expression-of-concern works as Axis C, severity critical. When no
>    such tool is available, write "retraction check: unavailable in
>    this environment" in `tech-review.md` — an explicit skip the Critic
>    propagates to the human, never a silent one.

### `stats_check`

**Checks**: reported statistics are internally consistent. This is a
**reasoning surface**: no runner, no external tool — the Reviewer
recomputes and cross-checks by explicit arithmetic (or with
`python_exec` when that surface is also declared).

**Needs**: nothing, and that is the point — declare `executable: false`. It is a
genuine reasoning surface, not a skipped one, and the flag is what tells the gate
the difference. When the numbers come from an analysis script that ships with the
project, declare `python_exec` alongside and let the script be the authority.

**Applies to**: any unit reporting quantitative results — Results
sections of papers, benchmark chapters, survey summaries.

**Sub-prompt**:

> Collect every numeric claim in the unit (percentages, Ns, means,
> p-values, confidence intervals, effect sizes, table cells). Then
> attack their consistency:
>
> 1. Percentages that partition a whole sum to 100 (± rounding).
>    Subgroup counts sum to their stated totals.
> 2. Ns match across text and tables: the same sample keeps the same N
>    everywhere it appears; exclusions and dropouts are accounted for
>    arithmetically (N analyzed = N enrolled − N excluded).
> 3. p-values, confidence intervals, and significance language cohere:
>    a CI that crosses the null cannot accompany "significant
>    (p < .05)"; a CI that excludes the null cannot accompany p > .05.
>    When a test statistic, df, and p are all reported, verify they are
>    mutually plausible.
> 4. Numbers repeated in prose match their table cells exactly.
> 5. Derived values recompute: rates from counts, pooled means from
>    subgroup means, differences and ratios as stated. Show the
>    arithmetic inside the finding — a stats finding without the
>    recomputation attached is just an opinion.
>
> File findings under Axis A. Scope honestly: this surface catches
> internal inconsistency only. It cannot validate the underlying data
> or the choice of statistical method — say so in the report when the
> unit's credibility rests on either.

### `empty`

The project has no machine-verifiable surface. Rare but valid — e.g., a
philosophical essay on software engineering. Axis A auto-PASSes; Axis B
runs against the grounding library only. The report carries an explicit
"No validation surface" note.

Declare it as `executable: false`, and mean it. `empty` on a project that ships
code is not "no surface", it is an undeclared skip, and MG-6 treats it as one.

## How to choose surfaces for a project

Surfaces are declared during Phase 1 setup, when conventions are decided
(`references/setup.md`). The profile suggests defaults — `scientific-paper`
typically declares `citation_check` + `stats_check` + `proof_recheck` +
`python_exec`; code-heavy profiles start from the matching `*_exec` — but
the declaration is per project, not per profile. Walk through:

1. **Does the document contain executable code?** Declare the relevant
   `*_exec` surface, with `executable: true`. Pin versions. If no runner is
   available in this environment, say so now rather than at the gate: the
   waiver and the test plan are part of the project's scope, not an
   afterthought.
2. **Does it contain declarative configs?** (YAML, JSON, Terraform,
   Kubernetes manifests.) Declare a `*_schema_validate` surface + linter.
3. **Does it contain a tool-specific DSL?** (SQL, Qlik expressions,
   regex.) Declare the matching surface or, if the tool is obscure,
   write a minimal sub-prompt and register it as custom.
4. **Does it rely heavily on official documentation?** Declare
   `doc_cross_ref` to catch invented APIs and commands.
5. **Does it carry visible citations or reported statistics?** Declare
   `citation_check` and/or `stats_check`.
6. **Anything else?** Custom surface. Follow the shape: id, `applies_to`
   globs, `runner` (even if it's "internal:prose_audit"), `pins`.

The same project can declare multiple surfaces. A Python book with YAML
fixtures declares `python_exec` + `yaml_schema_validate` + `linter`. Each
runs independently.

## How the Technical Reviewer uses them

At unit time, the Reviewer:

1. Reads `bible/meta.yaml`, extracts `validation_surface.surfaces`.
2. For each surface, loads its sub-prompt from this file.
3. Runs the surface's check over the draft content matching
   `applies_to`. Produces a list of findings.
4. Integrates findings into `tech-review.md` under the axis each surface
   names (A: mechanical; B: grounding; C: reference integrity).
5. If `surfaces` is empty, emits the explicit
   "Validation surface empty — Axis A is prose audit only" note that the
   Critic propagates to the human.

This means "technically correct output" has a checkable floor per
project, whatever the domain.
