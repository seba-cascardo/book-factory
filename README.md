# Book Factory

A [Claude Code](https://claude.com/claude-code) skill for producing **long-form documents** through a human-directed, multi-agent writing pipeline grounded in a per-project source library.

You stay the creative director. Specialized agents draft, review, edit, humanize, simulate readers, and gate every unit — but they never make strategic decisions about content, and nothing advances without your sign-off.

## What it writes

One pipeline, five **document profiles** — each with its own register, structure, citation policy, and quality rubric:

| Profile | For |
|---------|-----|
| `book-technical` | Technical books, manuals, tutorial series |
| `book-literary` | Novels, short fiction, narrative nonfiction |
| `corporate-guide` | Internal guides, employee handbooks, onboarding docs |
| `product-docs` | Product documentation, knowledge bases, runbooks |
| `scientific-paper` | Research papers (IMRaD, visible citations, claims-to-evidence mapping) |

## What makes it different

- **Source-grounded.** Nonfiction writers read a curated source library before drafting and cite their claims. A dedicated Technical Reviewer verifies claims, code, versions, framings, and — for papers — reference integrity.
- **One voice per *project*, not one voice per skill.** Every project defines its own voice profile — a distinctive fingerprint, an opening rotation, and its own calibration examples generated at setup. The skill's reference files carry rules and counter-examples only, never imitable "good" prose. This is deliberate: shared examples make every document sound the same.
- **Countable quality gates.** The Critic's verdict is *computed* from a scorecard, not asserted. A rhetoric budget caps rhetorical questions, "not X but Y" reframes, dramatic-danger lexicon, and template headings — counted mechanically, not judged by feel.
- **Roles don't overlap.** Each agent owns a clean slice and flags issues outside its scope instead of fixing them silently. The Editor is structural; the Humanizer owns prose; the Critic only gates.
- **Adversarial verification, on by default.** After a passing gate, independent skeptics — blind to the verdict — try to refute the unit. Findings confirmed by a majority reopen it. Review agents inflate; verification is cheaper than a fix pass acting on a wrong finding.
- **A gate for the book, not just for the chapter.** Per-unit review is structurally blind to a contradiction that spans two units. Phase 4.5 re-audits the whole document — concept by concept, rule against the book's own code, exercise against what was actually taught — and loops until it converges.
- **It knows what else says the same thing.** A fingerprint-keyed claim index means editing one passage tells you which other passages just went stale. Incomplete fixes are the defect class this exists to kill.
- **Deterministic checks are code, not prompts.** Rendering hazards, terminology pins, propagation — a regex doesn't hallucinate a violation and isn't tired by chapter 14. The agents keep the judgement.
- **Nothing turns off silently.** Any disabled check records who waived it, why, and what is owed. `complete` has preconditions the skill actually verifies.

## Pipeline

**Nonfiction** (`fast` default / `full` opt-in):

```
Writer → Technical Reviewer → Editor → Humanizer → [Reader-POV: full only]
  → Continuity Guardian (coherence) → Critic (GATE)
  → [Adversarial Verify: if enabled] → Human review
  → (on approval) Proofreader → Continuity Guardian (tracker) → digest → archive
```

**Literary:**

```
Writer → Editor → Humanizer → Reader-POV → Critic (GATE)
  → [Adversarial Verify: if enabled] → Human review
  → (on approval) Proofreader → Continuity Guardian → digest → archive
```

**Then, when the last unit is archived — automatically:**

```
Phase 4.5 · MANUSCRIPT GATE  (the book is the unit, not the chapter)
  concept audit · rule vs its own code · exercise vs content
  whole-book read · render lint · runner-or-declared-debt
    → adversarial verification of every critical/major
    → human decides → accepted fixes emit PROPAGATE → next round
  closes on PASS + two quiet rounds, or escalates
```

A per-unit reviewer cannot find a contradiction that spans two units — it sees
one side and approves it, correctly. So the last gate changes the unit of
analysis to the whole book, and iterates until it converges. It is not
skippable: no path leads from the last approved unit to `complete` without it.

## Install

Clone into your Claude Code skills directory:

```bash
git clone https://github.com/seba-cascardo/book-factory.git ~/.claude/skills/book-factory
```

Then in Claude Code, just describe what you want to write — *"start a technical book about…"*, *"escribir una novela sobre…"*, *"an internal onboarding guide for my company"*, *"a paper on…"* — and the skill takes over from project scaffolding through assembly and export.

## How it's organized

```
SKILL.md                       # the map: phase detection, profiles, pipeline invariants
references/
├── profiles/                  # the five document profiles
├── setup.md, outlining.md, knowledge-graph.md
├── pipeline.md                # authoritative pipeline spec (Phase 3)
├── manuscript-gate.md         # Phase 4.5 — the book-level gate and its loop
├── claim-index.md             # propagation: what else says the same thing
├── rubric.md                  # scorecard families + computed verdict
├── adversarial-verify.md, verification-plan.md, build-export.md, ...
└── agents/                    # one contract per agent
scripts/                       # deterministic checks — no model runs these
templates/                     # bible artifacts the scaffold copies into a project
```

A project the skill creates keeps its whole state under `bible/` (voice profile, sources, glossary, knowledge graph, claim index), `outline/`, `drafts/`, `final/`, `reviews/`, and a `project-status.yaml`.

The scripts need Python 3.10+ and PyYAML; `git` is optional and powers the incomplete-fix detector. They all take `--root` and `--units`, so you can also point them at a book this skill never wrote:

```bash
python scripts/lint_render.py --root /path/to/book --units "final/ch-*.md"
python scripts/manuscript_gate.py --root /path/to/book --units "final/ch-*.md" --round 1
```

## License

[MIT](LICENSE) © 2026 Sebastian Cascardo

---

*Built with [Claude Code](https://claude.com/claude-code).*
