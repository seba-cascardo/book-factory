# Validation Surface — Machine-Verifiable Checks per Domain

The Technical Reviewer audits claims, code, and versions (Axis A) against
whatever surface the book's content exposes. Not all technical books have
executable code. But almost every technical book has *some* surface that
a machine can check — and leaving it to the Reviewer's free-form prose
audit wastes its leverage.

A **validation surface** is a pairing of (content pattern in the book)
with (a mechanical check that can verify that content). The book's
`bible/meta.yaml` declares which surfaces apply under `validation_surface.surfaces:`. At chapter time, the Technical Reviewer loads sub-prompts for
each surface and runs them over the chapter.

## Why this is not "Code Executor only"

"Run the code" only applies if the book has runnable code. Qlik Sense
books, SQL-dialect books, math textbooks, cloud architecture books —
none of them compile and execute in the Python sense. But every one of
them has *some* surface:

- Qlik Sense: expressions and load scripts have deterministic grammars
  and documented function lists. A syntactic linter and a doc
  cross-reference catches the majority of factual errors a reader
  would hit.
- SQL dialect: every dialect has a parser; use it to validate that the
  SQL in the book actually parses against the target dialect.
- Cloud architecture: AWS CloudFormation / Terraform snippets can be
  `validate`-d against schema without deploying. Diagrams that follow
  a DSL (PlantUML, Mermaid) can be rendered to detect syntax errors.
- Math / proof: proof assistants (Lean, Coq) for formal; re-derivation
  walkthrough for informal.

The surface catalog below is not exhaustive. When you set up a new
project with a domain that's not listed, think: *what is the cheapest
machine check that rejects something the reader would hit as an
error?* That's the surface to declare.

## Catalogue of standard surfaces

Each surface has: an ID, what it checks, what it needs, and the
sub-prompt guidance the Technical Reviewer uses when loaded.

### `python_exec`

**Checks**: runnable Python snippets in chapter bodies and code blocks.

**Needs**: `runner` pointing at a sandboxed Python of the pinned
version. Docker recommended.

**Sub-prompt**: For each fenced ```python block, extract it (with any
visible setup), run in the sandbox, compare observed output against
what the book claims the output is. If output differs or the snippet
errors, flag Axis A.

### `js_node_exec`

Same shape as `python_exec`, for Node.js. Pin node version.

### `bash_exec`

**Checks**: shell-command snippets (```bash / ```sh / ```shell blocks).

**Needs**: a sandbox that reproduces the book's assumed environment.
Risky — declare only for books where the shell commands are the product
(sysadmin books, CLI tutorials).

**Sub-prompt**: Extract each command, check for destructive operators
(`rm -rf`, `> /dev/sda`, etc.) and flag for human review before running.
For safe commands, run and verify output.

### `sql_dialect_check`

**Checks**: SQL snippets parse against the declared dialect (postgres |
mysql | sqlite | bigquery | snowflake | mssql | oracle).

**Needs**: `runner` that can parse SQL without executing (e.g.,
`sqlfluff` with dialect, or a DB in parse-only mode).

**Sub-prompt**: For each ```sql block, run the parser with the target
dialect. Flag parse errors and dialect-specific syntax used outside its
dialect.

### `yaml_schema_validate` / `json_schema_validate`

**Checks**: YAML/JSON in chapter bodies validates against a declared
schema.

**Needs**: schema file, usually in `bible/schemas/`.

**Sub-prompt**: Extract each YAML/JSON block; validate. Report violations.

### `linter`

**Checks**: static analysis passes for code in the book.

**Needs**: linter name + config file.

**Sub-prompt**: Run linter on each code block in isolation. Report
findings the reader would encounter.

### `qlik_set_analysis`

**Checks**: Qlik Sense set analysis expressions match the documented
grammar (outer braces, set operators, element functions).

**Needs**: `runner: "internal:qlik_set_analysis_linter"` — the skill's
pattern-based linter, or an external one.

**Sub-prompt**:

> You are checking Qlik Sense set analysis expressions in a chapter. A
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
>    against bible/sources/ Qlik reference).
>
> Flag each finding as Axis A (incorrect syntax) or Axis B (wrong
> mental model of set analysis, e.g., using `{<dim=val>}` without
> quoting literal values — Qlik tolerates it but it's a trap; book
> should teach the safer form).

### `qlik_load_script`

**Checks**: Qlik Sense load scripts — directives (`LOAD`, `FROM`,
`STORE`, `LET`, `SET`), field naming, `AutoGenerate` blocks.

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
>    hold the literal string `Now()`, not the evaluated date. Flag
>    these.
> 5. `Subroutine` / `Call` pairs match. Unused subroutines or missing
>    End Sub are errors.
> 6. Functions named exist in the pinned Qlik version.

### `qlik_expression`

**Checks**: Qlik frontend chart expressions — valid function names,
balanced parens, aggregations not nested without inner `Aggr()`, valid
field references.

**Sub-prompt**:

> You are checking Qlik Sense frontend expressions (for charts and KPIs).
> Verify:
>
> 1. Every function name exists in the pinned Qlik version. Common traps:
>    mixing pre-May-2024 and post-May-2024 spellings, using Qlik View
>    functions that were dropped (e.g., older `Alt()` behaviors).
> 2. Aggregations (`Sum`, `Count`, `Avg`, etc.) wrap the non-aggregated
>    dimension. Nested aggregations need `Aggr(..., dim1, dim2)`.
> 3. Parentheses balance. String-delimiter quotes balance.
> 4. `If(` expressions have 2 or 3 arguments — flag the common miss of
>    not providing an `else` value when the chart assumes one.
> 5. Field names referenced exist or are declared. (If the chapter
>    doesn't show data model, this is advisory.)

### `doc_cross_ref`

**Checks**: every function/command/flag mentioned in the chapter exists
in the declared grounding sources.

**Needs**: `bible/sources/` populated.

**Sub-prompt**: For every code-formatted identifier in the chapter
(function names, CLI flags, config keys), grep the grounding library's
`.md` extracts. If not found, flag as "potentially invented" and
require the Writer to provide a citation or remove.

### `proof_recheck`

**Checks**: mathematical derivations — each step in a derivation
follows from the previous by a named rule.

**Sub-prompt**: For each derivation (sequence of `=` or `⟹` steps),
verify the justification given for each step corresponds to a known
identity/rule. Flag unjustified transitions.

### `empty`

The book has no machine-verifiable surface. Rare but valid — e.g., a
philosophical essay on software engineering. Axis A auto-PASSes; Axis B
runs against the grounding library only. The report carries an explicit
"No validation surface" note.

## How to choose surfaces for a project

During setup Sub-Phase 5 (Conventions) or the new Sub-Phase 8, walk
through this list and ask:

1. **Does the book contain executable code?** If yes, declare the
   relevant `*_exec` surface. Pin versions.
2. **Does it contain declarative configs?** (YAML, JSON, Terraform,
   CloudFormation, Kubernetes manifests.) Declare a `*_schema_validate`
   surface + linter.
3. **Does it contain a DSL specific to a tool?** (SQL, Qlik
   expressions, regex.) Declare the matching surface or, if the tool
   is obscure, write a minimal sub-prompt and register it as custom.
4. **Does it rely heavily on official documentation?** Declare
   `doc_cross_ref` to catch invented APIs and commands.
5. **Anything else?** Custom surface. Follow the shape: id, `applies_to`
   globs, `runner` (even if it's "internal:prose_audit"), `pins`.

The same book can declare multiple surfaces. A Python book with declared
YAML fixtures would declare `python_exec` + `yaml_schema_validate` +
`linter`. Each runs independently.

## How the Technical Reviewer uses them

At chapter time, the Reviewer:

1. Reads `bible/meta.yaml`, extracts `validation_surface.surfaces`.
2. For each surface, loads its sub-prompt (from this file).
3. Runs the surface's check over the draft chapter content matching
   `applies_to`. Produces a list of findings.
4. Integrates findings into `tech-review.md` under Axis A (surface-based)
   or Axis B (grounding-based), as appropriate.
5. If `surfaces` is empty, emits the explicit
   "Validation surface empty — Axis A is prose audit only" note that the
   Critic propagates to the human.

This means "perfect technical output" has a checkable floor per book,
whatever the domain.
