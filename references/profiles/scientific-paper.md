# Profile — scientific-paper

Every agent loads this file at the start of its turn. Where it conflicts
with a general reference on register, structure, or citation handling, this
profile wins.

## 1. Unit

The unit is a **section** — one IMRaD component per unit (Abstract, Intro,
Methods, Results, Discussion; plus Related Work, Limitations, Conclusion
where the venue expects them). Files use `unit-NN`; say "section" to the human.

## 2. Sequence: imrad

The outline fixes the WRITING order — not the reading order:
**Methods → Results → Introduction → Discussion → Abstract last.**

Why this order: Methods and Results describe what was actually done and
found — they can be written from the data with no rhetoric. The Intro's
framing (the gap, the contribution claims) depends on the results actually
obtained; written first, it commits the paper to promises the results may
not keep. The Abstract summarizes what exists, so it can only be honest
once everything else is final. Reject other orderings.

- Numbered cross-references between sections are normal, in both directions
  ("see Section 4") — readers of papers do not read linearly.
- Digests: claim-centric, not prose summaries — each approved section's
  digest records which claims-map entries it used and their status.
- Knowledge graph: mandatory (notation, defined terms, method names).

## 3. Register

Sober academic. The paper persuades with evidence and precision, never with
rhetoric — any sentence that works harder than its evidence is a defect.
Prohibited:

- Rhetorical questions — budget is **0** (`rhet-1` tightened, significant).
- Suspense, cliffhangers, narrative hooks, scene-setting anecdotes.
- Self-praising adjectives ("remarkable", "striking", "novel") unless the
  quantity that earns them appears in the same sentence.
- Claims stated stronger than their claims-map entry. If the map says
  "improves X on dataset Z", the prose cannot say "improves X".
- Motivational framing; addressing the reader as "you".

Person and voice ("we" vs. passive) follow the venue convention in `meta.yaml`.
The Humanizer runs every section: it strips AI-isms, enforces this register,
and applies Reviewer advisories — de-embellishing, not enlivening.

## 4. Openings and closings

Each section opens by doing its conventional IMRaD job in the first
paragraph — Methods states what was done, Results what was found — no
warm-up. The opening-rotation rule (`rhet-6`) does NOT apply: IMRaD
convention fixes each opening; rotating for variety would be a defect.

Closing policy: **none**. A section ends when its content ends — no recap,
no bridge, no teaser. The Discussion may end with implications and future
work because that is its content, not a flourish.

## 5. Citation policy: visible-academic

This INVERTS the invisible-citation rule used by the other profiles:

- Citations appear **in the prose**, formatted per
  `meta.yaml → citation_style: apa | ieee | vancouver | author-year`.
- Load-bearing citations ALSO carry the pipeline's HTML comment,
  `<!-- SOURCE: source_id §locator -->`, pointing into `bible/sources/`.

Why both: the visible citation serves the reader; the comment serves the
Technical Reviewer. Formatted citations are ambiguous (author-year collisions,
no file mapping) — the Reviewer never guesses which file backs a claim.

## 6. Claims discipline — `bible/claims-map.yaml`

Every claim the paper makes maps to an entry in `bible/claims-map.yaml`
(template: `templates/claims-map.yaml`). Two types:

- `external` — evidence is a citation grounded in `bible/sources/`
  (source_id + locator).
- `own-result` — evidence is the project's own data: an artifact plus the
  table or figure that presents it.

Setup seeds the core claims. The Writer adds entries and updates
`sections_used` while drafting; the Technical Reviewer verifies evidence
and sets `status` (grounded | pending | unverifiable). A claim in prose
with no entry, or `unverifiable` at gate time, is a rubric hit: hedge, cut,
or gather evidence — never ship as-is.

## 7. Technical Reviewer — Axis C: reference integrity

In addition to Axis A/B, the Reviewer verifies every visible citation:

1. The cited work **exists** (not hallucinated; metadata correct).
2. It **supports** the sentence citing it — topical overlap is not support.
3. It is **not retracted**.

Use Zotero / citecheck / arxiv / openreview MCP tools when connected.
Otherwise degrade gracefully: verify against `bible/sources/` only, flagging
every citation not resolvable there as `unverified` in `tech-review.md` —
never a silent pass. The human decides if unverified refs block submission.

## 8. Mandatory Limitations section (rubric critical)

The outline must include a Limitations section (standalone or inside the
Discussion, per venue). Every referee hunts for limitations; naming them
first is basic honesty and the cheapest defense. A section listing only
flattering limitations fails the same item.

## 9. Methods reproducibility checklist (rubric significant)

Methods must let a competent reader reproduce the work. Verify: data
availability (where, license, access procedure); all parameters and
configuration; software and library versions; random seeds and run counts;
hardware where it affects results. Gaps are declared in the text ("data
available on request"), never silently omitted.

## 10. Running example: off — the paper's own study is the through-line.

## 11. Rubric deltas (see references/rubric.md)

Base `profile-1/2/3` (register, citation policy, opening) apply as the
universal spine. This profile ADDS items in its own `paper-*` id family
(never reusing `profile-N` — see `references/rubric.md` § Profile compliance):

- Add `paper-1`: Limitations present and substantive — critical.
- Add `paper-2`: all prose claims map to grounded claims-map entries — critical.
- Add `paper-3`: reproducibility checklist met or gaps declared — significant.
- Add `paper-4`: citation format matches `citation_style` — minor
  (Proofreader applies fixes mechanically).
- Base `profile-3` (opening in rotation): `not_applicable` — the IMRaD
  section openings are convention-fixed, not rotated (`rhet-6` dropped, §4).
- `rhet-1` tightened to 0; exercise-related pedagogy items dropped;
  `pedagogy-3` evaluates against closing policy `none`.

## 12. Reader-POV personas

1. **Skeptical Reviewer 2** — reads to reject: overclaiming, missing
   baselines or controls, ungrounded generalization, statistics that do not
   support the stated effect, unacknowledged limitations.
2. **Abstract-only reader** — reads only Abstract, figures/tables, and
   conclusions. An abstract that oversells the Results is a hit.

## 13. Validation surfaces

Typical: `citation_check`, `stats_check`, `proof_recheck`, `python_exec`
(when analysis code ships). Declared in `meta.yaml →
validation_surface.surfaces`; see `references/validation-surface.md`.

## 14. Build targets (Phase 5)

LaTeX → PDF, using the venue template when provided in `bible/`. The `.bib`
is generated from claims-map `external` entries joined with bibliographic
metadata in `bible/sources/sources.md`. Every visible citation must resolve
to a `.bib` entry; no `.bib` entry may be orphaned. See
`references/build-export.md`.
