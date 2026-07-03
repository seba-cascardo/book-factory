# Changelog

## 3.0

A ground-up redesign of the writing pipeline. Earlier version history lives
with the prior skill install and is not carried forward here.

### Profiles replace the literary/technical binary
Five document profiles — `book-technical`, `book-literary`, `corporate-guide`,
`product-docs`, `scientific-paper` — each a short file in
`references/profiles/` that every agent loads at the start of its turn. The
profile owns unit naming, sequence, register and prohibitions, opening/closing
policy, citation policy, rubric deltas, Reader-POV personas, and Phase 5 build
targets. When a profile and a general reference disagree, the profile wins.

### Per-project voice, not per-skill voice
New `bible/voice-profile.md` per project: a distinctive fingerprint, banned
traits, an opening rotation, closing policy, and the project's OWN GOOD
examples derived from approved calibration passages. The skill's reference
files now carry rules and BAD examples only — shared GOOD examples produced
identical-sounding output across projects and are gone. Prose agents calibrate
against the voice profile, never against neighboring units.

### Countable rhetoric budget
A `rhet` rubric family (rhetorical questions, "not X but Y", danger lexicon,
artificial cliffhangers, emphasis density, opening rotation, template
headings). The Critic counts and reports the numbers; budgets are overridable
per project in the voice profile.

### Itemized literary rubric + moderate literary package
The literary rubric is itemized for the first time (`beats`, `character`,
`arc`, `voice`, `craft`, `reader_pov`, `continuity`). The package adds a
friction inventory, typed exposition beats, pause-vs-pausing, secondary-line
guarantees, a voice-risk quota, a conservative "preserve-don't-improve"
Humanizer, and a singularity audit every 5 approved units — no new agents.

### Adversarial verify
Optional post-Critic slot (`pipeline.adversarial_verify`): three skeptics run
in parallel, blind to the Critic's verdict, mandated to refute the unit. A
finding confirmed by ≥2 converts a PASS into a REVISE.

### Phase 5 build/export
Per-profile build targets: books → EPUB/PDF/DOCX; corporate guides →
DOCX/PDF; product-docs → a static-site-ready markdown tree; papers →
LaTeX/PDF with a bibliography generated from the claims map.

### Simplified runs log
Cost observability is one line per agent run in `project-status.yaml → runs`
(`[unit-NN, agent, tier, cycle, timestamp]`). Token accounting was specified
but never reliably populated, so it was dropped.

### Model tiers, not model IDs
`meta.yaml → models` maps roles to `creative` / `audit` tiers that default to
`inherit` (the session model). Explicit model IDs appear only in a project's
own `meta.yaml`, and only for cost control — never in skill files.
