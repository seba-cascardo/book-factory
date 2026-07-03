# Drafts Archive Policy

`drafts/unit-NN/` accumulates artifacts during a unit's pipeline run:
`grounding-notes.md` (nonfiction with sources), `draft.md`, `tech-review.md`
(nonfiction), `edit.md`, `humanized.md`, `reader-report.md` (full/literary),
`coherence.md` (Mode A), `critique.md`, `scorecard.yaml`, and
`adversarial-report.md` when the adversarial slot ran.

At unit 15 of a 20-unit project, `drafts/` holds 14 directories of 5–9 files
each. Navigation rots. More importantly, the "what is in flight right now"
question becomes impossible to answer at a glance — exactly when the human
most needs a clear signal.

## The rule

When the human approves a unit (human approval, not Critic PASS), and after
the Proofreader, Continuity Guardian Mode B, and digest steps complete, the
orchestrator **moves** `drafts/unit-NN/` to `drafts/_archive/unit-NN/`.

The move:

- preserves file contents,
- stamps `archived_on` for the unit in `project-status.yaml`,
- leaves `final/unit-NN.md` and (sequential profiles)
  `bible/digests/unit-NN.digest.md` untouched at their canonical locations.

This keeps `drafts/` clean — it holds only units currently in flight or not
yet started.

## Why archive instead of delete

Cheap insurance. If a unit is re-opened for a late revision, the original
pipeline artifacts are still there for reference — which Axis A findings the
Technical Reviewer raised the first time, what the approved voice sample from
`humanized.md` was. Without the archive, re-opening a unit means re-running
the pipeline from nothing.

## When to actually delete

Never automatically. The human may manually prune `drafts/_archive/` after the
document is complete and shipped. The skill will not suggest deletion.

## What happens on unit re-open

If the human re-opens an approved unit for late revision:

1. `drafts/_archive/unit-NN/` is **copied** back to `drafts/unit-NN/` (not
   moved — the archive is preserved).
2. Files in `drafts/unit-NN/` are timestamped `-r1`, `-r2` on each agent
   re-run, so the archive copy stays intact and new iterations do not
   overwrite the approved-pipeline record.
3. `project-status.yaml`: the unit's `status` resets to the pipeline stage the
   re-open starts from; `current_cycle` is bumped; `archived_on` is nulled
   until re-approval.
4. On re-approval, the policy fires again: `drafts/unit-NN/` moves back to
   `drafts/_archive/`, but the prior archive is preserved under a timestamped
   directory (`drafts/_archive/unit-NN-r1/`) so no approved-pipeline record is
   ever lost.

## Disable the policy

Set `pipeline.archive_drafts.enabled: false` in `bible/meta.yaml`.

Useful for:

- Very short projects where the clutter is not a problem.
- Environments where the user wants to watch all drafts evolve in place.

Default is on.

## Where the skill tells the human

The move is never silent. On approval, the skill confirms it in the profile's
unit word — for a technical book:

> "Chapter 7 approved. Its drafts moved to `drafts/_archive/unit-07/`;
> `drafts/` now shows only units in progress."

For product-docs, say "article"; for corporate-guide and scientific-paper,
"section". The message is about `drafts/`; the archive itself is the same
`drafts/_archive/unit-NN/` path in every profile.
