# Loopback handoff — structured escalation

When a unit stops converging, more agent runs do not help: the human needs the
right information to decide. The orchestrator then produces a **structured
packet** — the diff between attempts, one classified failure pattern, and three
concrete options — never a bare "ask the human".

## When it fires

Any of:

- **Retry cap**: `retries.by_unit[unit-NN] >= pipeline.retry_cap` (2 `fast`,
  3 `full` and literary) and the next Reviewer or Critic verdict would not be
  PASS.
- **Plateau rule**: a cycle resolved none of the previous cycle's failing rows
  — the failing set in `scorecard.yaml` is the same as, or larger than, the one
  in the previous `scorecard.c<N>.yaml`. Fire at once, whatever budget
  remains: the loop is not converging, and spending the rest of the budget
  only proves it again.
- **Critic ESCALATE**: a failing row targets `escalate` (`snapshot` refuses to
  open a loop for it).
- **Second contract violation**: `pipeline_step.py done` exits `4` twice for the
  same agent in one cycle (an Editor that keeps adding prose, a Proofreader
  that keeps rewriting, a Critic whose header keeps contradicting its rows).

The cap counts every loopback from every source, and the packet's timeline
must reconcile with `runs.tsv`: Reviewer → Writer cycles, Critic → any-agent
REVISE/REWORK, adversarial-confirmed REVISEs (one retry each, shown as their
own entry), and human rejections routed to an agent. Omitting one
misdiagnoses the pattern.

On firing, pause the unit (`on_hold` in `project-status.yaml`), write `drafts/unit-NN/escalation.md` from
`templates/loopback-escalation.md`, and show it to the human. No further agent
calls for this unit until the human answers.

## What the packet contains

1. **Summary** — unit, title, mode, cycles used / cap, trigger (cap, plateau,
   Critic ESCALATE, contract violation).
2. **Timeline** — every run and verdict, newest last:
   `agent → verdict (one-line reason) → target`.
3. **Per-cycle diff** — per cycle: the agent, what it was asked to fix, the
   artifact (`humanized.c<N>.md`, `role-diff-*-c<N>.json` — link, never paste),
   net ± words and sections touched, and why the next gate still failed. This
   is usually where the real problem shows: the Writer added motivation twice
   and the Critic still failed on motivation — so motivation is not the
   problem.
4. **Failure pattern** — exactly one:
   - `thrashing_on_same_hit` — the same row fails every cycle; each fix
     regresses another. The problem is not what the Critic named.
   - `diverging_attempts` — each cycle fixes the hit and opens new ones. The
     unit is not well bounded.
   - `insufficient_grounding` — "unverifiable" or "model unclear" survives
     every rewrite. A source is missing, or the expertise is. (Papers: often an
     `unverifiable` claims-map entry.)
   - `outline_level_flaw` — a dependency that cannot be satisfied here; the
     outline needs revising upstream.
   - `prose_vs_content_mismatch` — routed to the Humanizer while the issue is
     structural or content (or the reverse); the routing misclassified it.
   - `unclassified` — describe it; ask the human to classify.
5. **Three options** — exactly three, each with what happens next, cost (which
   agents re-run, as a multiple of a normal cycle) and risk.

   | Pattern | Typical options |
   |---|---|
   | thrashing_on_same_hit | (a) revisit the budget or rule the row counts against — it may contradict another; (b) redraft with a narrower scope; (c) fix the bible: style guide or rubric weighting fight each other |
   | diverging_attempts | (a) split the unit; (b) redraft with an explicit scope list; (c) the human drafts the contentious passage |
   | insufficient_grounding | (a) add a source; (b) an SME session with the human; (c) hedge the claim and move on |
   | outline_level_flaw | (a) revise the outline; (b) a primer section in this unit; (c) merge two units |
   | prose_vs_content_mismatch | (a) re-run with corrected routing; (b) the human overrides the gate; (c) switch pipeline mode for this unit |
   | unclassified | (a) one more cycle, supervised; (b) the human decides; (c) archive the draft, restart fresh |

   Replace them when none fits — always three, always concrete.
6. **Recommendation** — one pick, one paragraph, an explicit trade-off.

## Human response

Under `## Human decision` in the packet: `chose: a | b | c`, `chose: custom`
(with a description), or `chose: pause` (the unit goes `on_hold`; the rest of
the project continues). Then `retries.by_unit[unit-NN]` resets to 0 — the
chosen path is a fresh attempt — and the escalation is logged in
`retries.cap_hits` and `notes:` in `project-status.yaml`.

Three options, not one: a single option is a command to rubber-stamp; three
show the space, and the human often picks one with a piece of another.

## Example (abridged)

```
# Escalation — unit-05: Retry policies for the payment client
Mode: full. Cycles 2/3. Trigger: plateau (failing set {reader_pov-1, voice-4} unchanged).

## Timeline
- Cycle 1: Writer → Reviewer PASS → … → Reader-POV → Critic REVISE (reader_pov-1: §3 loses the reader) → Humanizer
- Cycle 2: Humanizer → Reader-POV → Critic REVISE (reader_pov-1 again; voice-4: new signposting) → plateau, packet

## Failure pattern
prose_vs_content_mismatch. Each clarity rewrite adds explanatory signposts and
the confusion survives: §3 uses idempotency keys two sections before defining
them. That is order or content, not prose.

## Options
(a) Editor moves the idempotency subsection before §3 — one partial cycle; risk: §2 loses its example.
(b) Writer adds a two-sentence definition in §3 — one full cycle; risk: duplication with §5.
(c) Split into unit-05a (keys) and unit-05b (retries) — two cycles; risk: outline change.

## Recommendation
(a): the text exists, only its order is wrong; it costs least and removes the cause.
```
