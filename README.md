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

- **Source-grounded.** Nonfiction writers read a curated source library before drafting and cite their claims. A Technical Reviewer verifies claims, code, versions and framings; every function or command the text names is checked against an identifier index built from the sources, so an invented API cannot pass on a reviewer's memory.
- **One voice per *project*, not one voice per skill.** Every project defines its own voice profile and calibration passages — at least one of them written by you. The skill's reference files carry rules and counter-examples only, never imitable "good" prose.
- **Counted means counted by a script.** Rhetoric budgets, AI-isms, hedges, gesture tics, role boundaries (did the Editor add prose? did the Humanizer rewrite more than its budget?) are measured by code in the project's language — Spanish and English packs ship with the skill. Agents copy the numbers; they never recount.
- **Independent reviewers, for real.** Critic, Reader-POV, skeptics and auditors run as isolated subagents with a closed list of inputs; cold readers read the text with every pipeline comment stripped. A finding one skeptic raises survives only if a refutation pass (optionally on a second model) upholds it.
- **Stories are designed before they are written.** In the literary profile, every character has a complete sheet — backstory, personality, want, need, voice and an arc that resolves on a named chapter — and the story has an ending before a word of chapter one is drafted. A character added mid-book goes through the same questionnaire. Scenes are planned as cards (want, opposition, pivot, value change), setups and payoffs live in a ledger, and turning points are checked against the model's own defaults.
- **A gate for the book, not just for the chapter.** Phase 4.5 re-audits the whole document and loops until it converges. Technical books get concept, rule-vs-code and exercise audits; novels get story integrity (every arc resolved, the ending delivered, the ledger closed), cross-chapter texture (tics, names, attributes) and a continuity/developmental read.
- **It knows what else says the same thing.** A fingerprint-keyed claim index means editing one passage tells you which other passages just went stale.
- **Nothing turns off silently.** Any disabled check records who waived it, why, and what is owed. `complete` has preconditions the skill actually verifies — and the gate's verdict says how much of the book it looked at.

## Pipeline

**Nonfiction** (`fast` default / `full` adds Reader-POV):

```
Writer → Technical Reviewer → Editor → Humanizer → [Reader-POV]
  → Continuity Guardian (coherence) → checks → Critic (GATE)
  → [Adversarial Verify] → Proofreader → Human review
  → (on approval) final/ → Continuity Guardian (tracker) → digest → archive
```

**Literary** (drafting starts only when `pipeline_step.py ready` passes):

```
Writer (scene by scene) → Editor (assembly) → Humanizer → Reader-POV
  → Continuity Guardian (continuity + facts) → checks → Critic (GATE)
  → [Adversarial Verify] → Proofreader → Human review
  → (on approval) final/ → Continuity Guardian (tracker) → digest
  → reader journal → archive
```

Every agent dispatch is bracketed by `scripts/pipeline_step.py check` / `done`, which verify inputs and outputs and write the runs log. Loops re-enter from the last gated text; a cycle that fixes nothing escalates instead of spending the retry budget.

**Then, when the last unit is archived — automatically:**

```
Phase 4.5 · MANUSCRIPT GATE  (the book is the unit, not the chapter)
  technical: concept audit · rule vs its own code · exercise vs content
  literary:  story integrity · texture · continuity & developmental read
  both:      whole-book read · render lint · fixed-defect regression
    → adversarial verification of every critical/major
    → open findings persist across rounds until resolved
  verdict: ERROR | BLOCKED | NEEDS-REVISION | PASS-PARTIAL | PASS
  converges on PASS (or partial coverage under a signed waiver) + two quiet rounds
```

## Install

Clone into your Claude Code skills directory:

```bash
git clone https://github.com/seba-cascardo/book-factory.git ~/.claude/skills/book-factory
```

Then in Claude Code, just describe what you want to write — *"start a technical book about…"*, *"escribir una novela sobre…"*, *"an internal onboarding guide for my company"*, *"a paper on…"* — and the skill takes over from project scaffolding through assembly and export.

## How it's organized

```
SKILL.md                       # the map: phase detection, profiles, execution model
references/
├── profiles/                  # the five document profiles
├── setup.md, outlining.md, character-questionnaire.md, knowledge-graph.md
├── pipeline.md                # authoritative pipeline spec (Phase 3)
├── rubric.md                  # scorecard schema + THE verdict computation
├── rubric-nonfiction.md, rubric-literary.md
├── manuscript-gate.md, manuscript-gate-literary.md   # Phase 4.5
├── claim-index.md, adversarial-verify.md, verification-plan.md, build-export.md, ...
├── surfaces/                  # optional validation-surface packs (e.g. Qlik)
└── agents/                    # one contract per agent
scripts/                       # deterministic checks — no model runs these
├── lexicons/                  # per-language word lists (en, es)
└── tests/                     # selftest modules + fixtures
templates/                     # bible artifacts the scaffold copies into a project
docs/rationale/                # why the rules are what they are (agents do not load this)
```

The scripts need Python 3.10+ and PyYAML; `git` is optional and powers the incomplete-fix detector. They take `--root`, so you can also point the checks at a book this skill never wrote:

```bash
python scripts/lint_render.py --root /path/to/book --units "final/ch-*.md"
python scripts/manuscript_gate.py --root /path/to/book --units "final/ch-*.md" --round 1
python scripts/selftest.py        # the regression suite; no model, no tokens
```

## License

[MIT](LICENSE) © 2026 Sebastian Cascardo

---

*Built with [Claude Code](https://claude.com/claude-code).*
