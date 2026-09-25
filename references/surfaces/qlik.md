# Optional surface pack — Qlik Sense

Load only when `bible/meta.yaml → validation_surface.surfaces` declares one of
these ids. Same entry shape as `references/validation-surface.md`. Pin the Qlik
release under `pinned_versions` and keep the Qlik function reference in
`bible/sources/` so `check_identifiers.py --build-index` knows every real
function name.

### `qlik_set_analysis`

Set analysis expressions match the documented grammar. **Needs**
`runner: "internal:qlik_set_analysis_linter"` (pattern-based) or an external
linter. **Sub-prompt**:

> A set expression lives in `{…}` inside an aggregation: `Sum({<dim={'val'}>} measure)`.
> 1. Every `{<…>}` sits inside an aggregation function.
> 2. Selectors use `dim={values}`, `dim={"search"}`, or `dim-=` / `dim+=` —
>    not SQL syntax.
> 3. Element functions (`P()`, `E()`) appear only inside set expressions.
> 4. Operators between sets are `+ - * /`, not `&` or `|`.
> 5. Every function exists in the pinned release (the identifier check covers
>    the name; you check the usage).
>
> Axis A for syntax; Axis B for a wrong mental model — e.g. unquoted literal
> values that Qlik tolerates but the text should not teach.

### `qlik_load_script`

Load scripts (`LOAD`, `FROM`, `STORE`, `LET`, `SET`, `AutoGenerate`).
**Needs** a Qlik environment to reload against, or
`runner: "internal:qlik_load_script_lint"`. `executable: true` either way — a
lint is not a reload, so without an environment this surface owes a
verification plan. **Sub-prompt**:

> 1. Every `LOAD` ends with a source clause (`FROM`, `RESIDENT`, `INLINE`,
>    `AutoGenerate`, or a preceding `LIB CONNECT TO`).
> 2. `INLINE` blocks have matching delimiters and a constant column count.
> 3. `STORE INTO` uses a valid path (`lib://…` or relative).
> 4. `LET` evaluates, `SET` is literal: `SET x = Now()` stores the string
>    `Now()` — flag it.
> 5. `Sub` / `Call` pairs match; no missing `End Sub`.
> 6. Every function exists in the pinned release.

### `qlik_expression`

Chart and KPI expressions. **Needs** an app to evaluate in, or
`runner: "internal:qlik_expression_lint"`. `executable: true`. Reasoning fails
quietly here: a malformed set expression returns zero rows, not an error.
**Sub-prompt**:

> 1. Every function exists in the pinned release (renamed or dropped functions
>    are the common trap).
> 2. Aggregations wrap the non-aggregated dimension; nested aggregations need
>    `Aggr(…, dim1, dim2)`.
> 3. Parentheses and string quotes balance.
> 4. `If(` has 2 or 3 arguments — flag a missing else the chart assumes.
> 5. Referenced fields exist or are declared (advisory when the unit does not
>    show the data model).
