# Profile — scientific-paper

Every agent loads this file after its own. Where it conflicts with a general
reference on register, structure or citation handling, this file wins.

## 1. Unit

A **section** — one IMRaD component per unit (Abstract, Introduction, Methods,
Results, Discussion; Related Work, Limitations, Conclusion where the venue
expects them).

## 2. Sequence: imrad

The outline fixes the **writing** order: **Methods → Results → Introduction →
Discussion → Abstract last.** Methods and Results are written from the data,
with no rhetoric; the Introduction's framing depends on the results actually
obtained; the Abstract can only be honest once everything else is final.
Reject other orders.

- Numbered cross-references between sections are normal, in both directions.
- Digests are claims-state snapshots (`references/chapter-digest.md`).
- Knowledge graph mandatory (notation, defined terms, method names); forward
  references run on reading order.

## 3. Register

Sober academic: evidence and precision, never rhetoric. Prohibited:

- rhetorical questions (`rhet-1` quota 0);
- suspense, hooks, scene-setting anecdotes;
- self-praising adjectives ("remarkable", "novel") unless the earning quantity
  is in the same sentence;
- claims stronger than their claims-map entry ("improves X on dataset Z" never
  becomes "improves X");
- motivational framing; addressing the reader as "you".

Person and voice follow the venue (`meta.yaml`). The Humanizer de-embellishes;
it never enlivens.

## 4. Openings and closings

Each section opens by doing its IMRaD job in the first paragraph — no warm-up,
no rotation (`rhet-6` and `profile-3` are `not_applicable`). Closing policy
**none**; the Discussion may end with implications and future work because
that is its content.

## 5. Citation policy: visible-academic

Citations appear in prose per `meta.yaml → citation_style` (apa | ieee |
vancouver | author-year). Load-bearing citations also carry
`<!-- SOURCE: source_id §locator -->` into `bible/sources/`: the visible
citation serves the reader, the comment tells the Reviewer which file backs the
claim.

## 6. Claims and numbers — `bible/claims-map.yaml`

Every claim maps to an entry (`templates/claims-map.yaml`): `external` (a
citation grounded in `bible/sources/`) or `own-result` (an artifact plus the
table or figure presenting it). Setup seeds the core claims; the Writer adds
entries and `sections_used`; the Reviewer verifies and sets `status`
(grounded | pending | unverifiable).

**Number provenance.** Every number in the prose — Ns, means, effect sizes,
p-values, percentages, hyperparameters — traces to a claims-map entry, a SOURCE
comment, or an `<!-- ARTIFACT: path[#table|:line] -->` pointer to the file or
script that produces it. An orphan number is hedged, cut, or recorded as a
verification-plan item (`needs: runner | measurement`); it never ships as-is.

## 7. Technical Reviewer — Axis C

Every visible citation: the work **exists**, it **supports** the sentence
(topical overlap is not support), it is **not retracted**. Use Zotero,
citecheck, arXiv or OpenReview tools when connected; otherwise verify against
`bible/sources/` and flag each unresolvable citation `UNVERIFIED` in
`tech-review.md` — the normal path when no tool connects, never a silent pass.
The human decides whether unverified references block submission.

## 8. Limitations (critical)

The outline includes a Limitations section (standalone or in the Discussion).
Naming limitations first is honesty and the cheapest defence; a list of only
flattering limitations fails the same row.

## 9. Methods reproducibility (significant)

Data availability (where, license, access); every parameter and
configuration; software and library versions; seeds and run counts; hardware
where it matters. Gaps are declared in the text, never omitted.

## 10. Running example: off — the study is the through-line.

## 11. Rubric deltas

Base `references/rubric-nonfiction.md`, with:

- ADD `paper-1` (critical → Writer) — Limitations present and substantive.
- ADD `paper-2` (critical → Writer) — every prose claim maps to a grounded
  claims-map entry.
- ADD `paper-3` (significant → Writer) — reproducibility checklist met or gaps
  declared.
- ADD `paper-4` (minor → Humanizer) — citation format matches `citation_style`
  (the Proofreader fixes mechanical cases).
- ADD `paper-5` (significant → Writer) — number provenance: no orphan number
  (evidence: the count of numbers without an entry, SOURCE or ARTIFACT pointer,
  from `tech-review.md`).
- `rhet-1` quota 0; `rhet-6` and `profile-3` `not_applicable`; exercise items
  dropped; `pedagogy-3` against closing policy `none`.

## 12. Reader-POV personas

1. **Skeptical Reviewer 2** — reads to reject: overclaiming, missing baselines
   or controls, ungrounded generalization, statistics that do not support the
   effect, unacknowledged limitations.
2. **Abstract-only reader** — Abstract, figures, tables and conclusions only;
   an Abstract that oversells the Results is a hit.

## 13. Validation surfaces

Typical: `citation_check`, `stats_check`, `proof_recheck`, `python_exec` when
analysis code ships (`references/validation-surface.md`).

## 14. Build targets

LaTeX → PDF with the venue template when provided; the `.bib` from claims-map
`external` entries joined with `sources.md` metadata; no orphan citation, no
orphan entry (`references/build-export.md`).
