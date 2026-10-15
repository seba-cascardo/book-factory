# Drafts Archive Policy

`drafts/ch-NN/` accumulates artifacts during a chapter's pipeline run:
`grounding-notes.md` (technical, v2.4+), `draft.md`, `tech-review.md`,
`edit.md`, `humanized.md` (both modes since v2.4.1), `coherence.md`
(fast mode, Continuity Guardian Mode A), `reader-report.md` (full mode),
`critique.md`, `scorecard.yaml`.

At chapter 15 of a 20-chapter book, `drafts/` has 14 directories × 5–7
files each. Navigation rots. More importantly, the "what's in flight
right now" question becomes impossible to answer at a glance, which is
exactly when the human most needs a clear signal.

## The rule

When the human approves a chapter (human approval, not Critic PASS),
and after the Proofreader + Continuity Guardian + Chapter Digest steps
complete, the skill **moves** `drafts/ch-NN/` to `drafts/_archive/ch-NN/`.

The move:
- preserves file contents
- stamps `archived_on` in `project-status.yaml` for the chapter
- leaves `final/ch-NN.md` and `bible/digests/ch-NN.digest.md` untouched
  at their canonical locations

This keeps `drafts/` clean — it only contains chapters currently in
flight or not yet started.

## Why archive instead of delete

Cheap insurance. If a chapter is re-opened for a late revision, the
original pipeline artifacts are still there for reference — which
Axis A findings did the Tech Reviewer raise the first time, what was
the voice sample from humanized.md that got approved. Without the
archive, re-opening a chapter means re-running the pipeline from
nothing.

## When to actually delete

Never automatically. The human can manually prune `drafts/_archive/`
after the manuscript is complete and the project is shipped. The skill
will not suggest deletion.

## What happens on chapter re-open

If the human reopens an approved chapter for late revision:

1. `drafts/_archive/ch-NN/` is copied back to `drafts/ch-NN/` (NOT moved
   — archive preserved).
2. The files in `drafts/ch-NN/` are timestamped `-r1`, `-r2` on re-runs
   of each agent, so the archive copy stays intact and new iterations
   don't overwrite the approved-pipeline record.
3. `project-status.yaml`: chapter `status` resets to the pipeline stage
   the re-open starts from; `current_cycle` is bumped; `archived_on` is
   nulled until re-approval.
4. On re-approval, the policy fires again: `drafts/ch-NN/` moves back
   to `drafts/_archive/ch-NN/`, timestamped directory
   (`drafts/_archive/ch-NN-r1/`) to preserve the prior archive.

## Disable the policy

Set `pipeline.archive_drafts.enabled: false` in `bible/meta.yaml`.

Useful for:
- Very short books where the clutter isn't a problem.
- Environments where the user wants to watch all drafts evolve in place.

Default is on.

## Where the skill tells the human

On approval, the skill confirms:

> "Ch-07 aprobado. Archivo movido a `drafts/_archive/ch-07/`. `drafts/`
> ahora muestra solo capítulos en curso."

So the move is never silent.
