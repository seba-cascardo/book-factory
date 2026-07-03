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
- **Optional adversarial verification.** After a passing gate, independent skeptics — blind to the verdict — try to refute the unit. Findings confirmed by a majority reopen it.

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
├── pipeline.md                # authoritative pipeline spec
├── rubric.md                  # scorecard families + computed verdict
├── adversarial-verify.md, build-export.md, ...
└── agents/                    # one contract per agent
templates/                     # bible artifacts the scaffold copies into a project
```

A project the skill creates keeps its whole state under `bible/` (voice profile, sources, glossary, knowledge graph), `outline/`, `drafts/`, `final/`, and a `project-status.yaml`.

## License

[MIT](LICENSE) © 2026 Sebastian Cascardo

---

*Built with [Claude Code](https://claude.com/claude-code).*
