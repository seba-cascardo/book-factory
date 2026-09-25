# Rubric — nonfiction families

For `book-technical`, `corporate-guide`, `product-docs`, `scientific-paper`.
Schema, verdict computation, override layers, the `rhet` family and the Critic
protocol live in `references/rubric.md`; this file only defines items. Rows
marked *(full only)* are `not_applicable` in `fast` mode. "`checks.json →`"
means: copy the number from that field into evidence.

## `scope`

| id | sev | check | loopback |
|----|-----|-------|----------|
| scope-1 | critical | Unit delivers the outline entry's `purpose`. | Writer |
| scope-2 | significant | No topic declared out of scope in `bible/scope.md` surfaces here. | Writer |
| scope-3 | significant | Depth matches the outline entry's declared depth (tutorial / reference / overview). | Writer |

## `outline`

| id | sev | check | loopback |
|----|-----|-------|----------|
| outline-1 | critical | Every `concepts_introduced` entry is actually introduced. | Writer |
| outline-2 | critical | Every `concepts_used` appears in an earlier unit, in this unit's `concepts_introduced`, or in declared prerequisites. | Writer |
| outline-3 | significant | Section structure matches the outline; added or removed sections are flagged, not smuggled. | Editor |
| outline-4 | significant | Declared exercises are solvable with concepts introduced up to this unit. | Writer |

## `tech_a` — claims, code, versions

| id | sev | check | loopback |
|----|-----|-------|----------|
| tech_a-1 | critical | Every Axis A finding in `tech-review.md` was fixed or carried as an explicit advisory. | Writer |
| tech_a-2 | critical | Code passes the declared validation surfaces (`references/validation-surface.md`). | Writer |
| tech_a-3 | significant | Version references match the pinned versions in `bible/meta.yaml`. | Writer |
| tech_a-4 | significant | No invented identifiers. Evidence: `checks.json → identifiers.unknown` (count + locations). Fails while any unknown identifier remains that `tech-review.md` did not verify against a source (a verified one belongs in the `# allow` section of `bible/identifier-index.txt`). Never pass on memory of the API. | Writer |

## `tech_b` — mental models, terminology

| id | sev | check | loopback |
|----|-----|-------|----------|
| tech_b-1 | critical | No Axis B "broken framing" from `tech-review.md` survives. | Writer |
| tech_b-2 | significant | Glossary terms used consistently — no synonym cycling on load-bearing terms. | Humanizer |
| tech_b-3 | significant | Version-drift items are classified as drift, not reported as errors, where the drift rule in `sources.md` applies. | Writer |

## `pedagogy`

| id | sev | check | loopback |
|----|-----|-------|----------|
| pedagogy-1 | significant | Each section motivates before mechanizing. | Writer |
| pedagogy-2 | significant | Examples come after the concept they illustrate. | Editor |
| pedagogy-3 | minor | The closing follows the closing policy in force (profile default as adjusted in `voice-profile.md`), not a universal formula. | Humanizer |
| pedagogy-4 | significant | No undeclared forward reference — every "later" is paid or recorded in the tracker. | Writer |

## `voice`

One threshold per item; `fast` mode's extra tolerance comes only from the
minor rule in `rubric.md`.

| id | sev | check | loopback |
|----|-----|-------|----------|
| voice-1 | significant | Person (you / we / impersonal) matches `bible/meta.yaml` and holds. | Humanizer |
| voice-2 | significant | Content and dramatic-hazard layers of `anti-mediocrity-nonfiction.md` (layers 1–2): ≤ 1 hit (script-counted `rhet-3` hits excluded). | Writer |
| voice-3 | significant | AI vocabulary ≤ 1 per 1000 words: `checks.json → counts.ai_vocab.count` ÷ `words`. | Humanizer |
| voice-4 | significant | Style layer: no signposting; narration em-dashes ≤ 2 per page (`checks.json → counts.em_dash_narration.per_page`) unless the style guide allows more. Dialogue rayas never count. | Humanizer |
| voice-5 | critical | No chatbot residue (communication layer). | Humanizer |
| voice-6 | minor | Hedges ≤ 3 per 1000 words (`checks.json → counts.weasels.count` ÷ `words`) and no stacked hedges. | Humanizer |
| voice-7 | significant | Register matches the style decisions and calibration passages in `bible/style-guide.md`. | Humanizer |
| voice-8 | significant | Humanizer stayed within its budget: `checks.json → role_diff.humanizer.over_budget` is not true. With no `pipeline.humanizer_budget` set, nonfiction only reports `touched_ratio` (row `not_applicable`, ratio in evidence). Over budget means the draft needed rewriting, not tuning. | Writer |

## `reader_pov` *(full only)*

| id | sev | check | loopback |
|----|-----|-------|----------|
| reader_pov-1 | critical | No comprehension failure in `reader-report.md` survives — a clarity rewrite is Humanizer scope. | Humanizer |
| reader_pov-2 | critical | No "would close the book here" flag survives. | Writer |
| reader_pov-3 | critical | Outcome match: the reader finishes able to do what the outline promised. A miss is missing content. | Writer |

A confusion that is really a missing prerequisite routes as `outline-2`
(taught earlier → Writer adds the pointer; never taught → `escalate`).

## `code`

| id | sev | check | loopback |
|----|-----|-------|----------|
| code-1 | significant | Every snippet has labeled input / expected output. | Writer |
| code-2 | minor | Snippets are minimal — no decorative scaffolding. | Editor |
| code-3 | minor | Code style matches `bible/meta.yaml` conventions. | Humanizer |
| code-4 | critical | No rule this unit states in prose is contradicted **or silently omitted** by this unit's own code, example or bullet. | Writer |

Scoring `code-4`: list the rules the unit states (strong modality, or a
universal plus a breaking verb), then read every code block and example against
them for two shapes — **contradiction** (the example does what the rule
forbids; when in doubt, pass) and **omission** (the example applies the pattern
and says nothing about a precondition the rule made mandatory; **when in
doubt, fail**). Do not extend across units — that is MG-2. An emphatic
imperative is register, not a behavioral rule. Why:
`docs/rationale/pipeline.md#omission`.

## `consistency`

| id | sev | check | loopback |
|----|-----|-------|----------|
| consistency-1 | significant | Voice matches `bible/voice-profile.md`: fingerprint traits observable, banned traits absent. Against the profile, **never** the previous unit. | Humanizer |
| consistency-2 | significant | Terminology matches prior units (digests, tracker, `coherence.md`). | Humanizer |

## `forward_refs`

| id | sev | check | loopback |
|----|-----|-------|----------|
| forward_refs-1 | critical | Pays every forward reference prior units opened and the outline assigned here. | Writer |
| forward_refs-2 | minor | New forward references are flagged for the digest. | Writer |

## `rhet`

All seven items, as defined in `references/rubric.md` § `rhet`.

## `profile` — the universal spine

| id | sev | check | loopback |
|----|-----|-------|----------|
| profile-1 | significant | Register prohibitions in the profile's Register section are respected; quote any hit. | Humanizer |
| profile-2 | significant | Citation policy respected — `invisible`: no visible citations, load-bearing claims carry `<!-- SOURCE -->`; `visible-academic`: every claims-map claim touched here is correctly cited. | Writer |
| profile-3 | significant | The opening is one of the structures listed in `voice-profile.md` § 3 Openings (`rhet-6` checks non-repetition; this checks membership). | Writer |

A profile may mark a spine item `not_applicable` and may add items in its own
namespace; its § Rubric deltas lists them.
