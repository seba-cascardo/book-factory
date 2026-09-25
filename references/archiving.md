# Drafts archive policy

`drafts/unit-NN/` accumulates a unit's pipeline artifacts: `grounding-notes.md`,
`draft.md`, `tech-review.md`, `edit.md`, `humanized.md`, `humanized.clean.md`,
the loop snapshots `humanized|draft|edit.c<N>.md` and `scorecard.c<N>.yaml`,
the loop and dispatch records `loop-state.json` and `.dispatch.json`,
`reader-report.md`, `reader-test.md`, `coherence.md`, `checks.json`,
`checks.md`, `critique.md`, `scorecard.yaml`, `adversarial-report.md`,
`proofread.md`, `human-notes.md`, `escalation.md`, and the role diffs
`role-diff-<agent>-c<N>.json`. By unit 15, `drafts/` no longer answers "what is
in flight?" at a glance.

## The rule

After human approval and CG Mode B, the digest and (literary) the reader-journal
update, the orchestrator **moves** `drafts/unit-NN/` to
`drafts/_archive/unit-NN/`: contents preserved, `archived_on` stamped in
`project-status.yaml`, `final/unit-NN.md` and the digest left in place. Tell
the human in the profile's unit word: "Chapter 7 approved; its drafts moved to
`drafts/_archive/unit-07/`."

The archive keeps the audit trail: the snapshots and role diffs show what each
cycle changed, the checks show what the scripts counted, the Proofreader's diff
shows what changed after the gate. That is what a later loopback packet, a
re-open or a gate finding needs.

## When the last unit is archived

If every unit in `outline/units.yaml` is now `archived`, do **not** report the
book finished: write `phase: manuscript-gate` and start Phase 4.5
(`references/manuscript-gate.md`). The trigger lives here because this is the
only place that knows a unit was the last one. A unit `on_hold` is not
archived — resolve or drop it first. Why:
`docs/rationale/pipeline.md#three-months`.

## Why archive, never delete

A re-opened unit keeps its record: which findings the Reviewer raised, what
each cycle changed. The skill never deletes or suggests deleting
`drafts/_archive/`; the human may prune it after shipping.

## Re-opening an approved unit

1. **Copy** (not move) `drafts/_archive/unit-NN/` back to `drafts/unit-NN/`.
2. Agents write the usual file names (the scripts expect them); the archive
   copy keeps the approved record. Snapshot and role-diff cycle numbers
   continue from the archived ones.
3. `project-status.yaml`: the unit's status resets to the stage the re-open
   starts from, `current_cycle` is bumped, `archived_on` is nulled.
4. On re-approval the prior archive moves to `drafts/_archive/unit-NN-r1/` and
   the new run takes its place — no approved record is ever lost. The edit to
   `final/` goes through fix-then-verify (`references/pipeline.md`).

## Disable

`pipeline.archive_drafts.enabled: false` in `bible/meta.yaml` — for very short
projects or a human who wants to watch drafts evolve in place. Default on.
