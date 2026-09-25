# Anti-mediocrity — literary

Loaded by the Writer, Humanizer, Critic and CG Mode A on `book-literary`. It
names failure shapes and how to diagnose them; it prescribes no style. What
good sounds like belongs to the project (`bible/voice-profile.md`), so this
file describes BAD shapes and never models a GOOD passage — agents imitate
examples more than they follow rules.
Why: `docs/rationale/literary.md#no-good-examples`

Word lists live in `scripts/lexicons/<lang>.yaml` (`ai_isms`, `cliches`,
`weasels`, `gestures`, `speech_verbs_plain`, `speech_verbs_ornate`,
`not_x_but_y`) plus the project's `bible/lexicon.yaml`; `count_rhet.py` and
`lint_fiction.py` apply them. Never improvise a translation of a list: a
missing pack is reported, not guessed.

## 1. The seven categories — the core taxonomy

Every line-level defect is filed under one category. The Humanizer detects by
category and repairs with the category's move; voice rows cite them.
Detection is noisy — roughly half of automated flags are wrong — so spans are
marked first and edited only when a rule backs them.
Why: `docs/rationale/literary.md#lamp`

| # | Category | Shape | Detection | Repair move |
|---|---|---|---|---|
| 1 | Cliché | stock phrases and images; AI-isms; the book's own tics — a gesture or phrase repeated until it is the book's cliché | lexicon `cliches`, `ai_isms`; `lint_fiction` `gesture_tic`, `repeated_ngram` | the concrete thing this POV would notice, or cut; tics: vary or drop some sites |
| 2 | Unnecessary exposition | explaining what was just shown; the narrator stating the theme or the lesson; recaps | reading (§ 2) | delete; the shown thing stays |
| 3 | Purple prose | ornament beyond the voice profile: stacked modifiers, similes over budget, abstraction wrappers | lexicon `weasels`; simile count | keep the strongest image, cut the rest |
| 4 | Poor sentence structure | runs of one sentence shape; staccato fragment runs; every paragraph closing on a short punch; repeated paragraph openers | `lint_fiction` `sentence_run`, `paragraph_opener`; `checks.json → counts.sentence_length.flat_runs` | vary one or two points; never re-orchestrate |
| 5 | Lack of specificity | a generic noun where the book has a specific one; emotion carried only by generic bodily sensation | reading | the specific the bible or seeds provide — never an invented fact |
| 6 | Awkward phrasing | wrong register for the POV; ornate or adverb-laden dialogue tags; calques; "not X but Y" reframes | lexicon `speech_verbs_ornate`, `not_x_but_y` (rhet-2) | rephrase inside the line; restructure, never swap synonyms |
| 7 | Tense inconsistency | tense or POV slips | reading; CG narrative style | restore the declared tense and POV |

## 2. Diagnostics with budgets

Measurements, not techniques to apply. Defaults; the voice profile's
`rhetoric_budget:` fence may override any of them with the same key.

| Key | Default | Measure |
|---|---|---|
| `similes_per_1000` | ≤ 4 | similes and "as if" comparisons in narration |
| `fragment_ratio` | ≤ 0.15 | verbless narration sentences; never 3+ in a row |
| `one_line_paragraphs_per_1000` | ≤ 2 | one-sentence paragraphs outside dialogue |
| `emotion_channels` | ≥ 2 | channels carrying emotion in the chapter: action or decision, dialogue and subtext, interior thought, bodily sensation. Bodily sensation as the only channel is the tell; a named emotion is not a defect by itself |
| `narrator_theme` | 0 | sentences telling the reader what the story means |
| `explained_shown` | 0 | sentences explaining an action or line that already carried it |

Non-visual senses are used where they do work; there is no per-sentence
quota.

## 3. What the diagnostics protect

- **Subtext**: in loaded exchanges people talk around the issue through an
  adjacent concrete thing; the reader reconstructs the unsaid.
- **Resist the urge to explain**: after showing, stop. The fix is deletion.
- **Character as contradiction**: two traits from the sheet, both true, shown
  in one act.
- **Agency**: characterize by what people do, decide, refuse — not by
  adjective lists or verbs of passive cognition.
- **Dialogue differentiates**: tags covered, each speaker identifiable (sheet
  § Voice); the cast does not share one register.
- **Exposition in action**: information arrives because someone wants,
  withholds or pays for it.
- **Pause, not pausing**: a slow beat carries a turn.
- **Causal chain**: scenes are linked by "therefore" or "but"; episodic
  stringing is a design defect, fixed in the outline (`link`).
- **Thematic focus**: one or two load-bearing themes (`bible/arcs.md`); not
  every scene carries significance, not every chapter ends on a meaningful
  note.
- **Earned stages**: a relationship moves through events, never through a line
  saying it moved.

## 4. Language-aware rules

- **Dashes**: dialogue rayas (—) are dialogue marks, never counted as dashes;
  the em-dash budget (voice-3) counts narration only.
- **Attribution** follows the language's tradition and the style guide. The
  English "said/asked plus action beats" default does not transfer: Spanish
  accepts a wider set of verbs of saying. Only lexicon `speech_verbs_ornate`
  hits and adverb-laden tags are defects.
- **"Not X but Y"** (rhet-2) is the lexicon's `not_x_but_y` for the language
  — in Spanish, "No es X. Es Y." and its variants.

## 5. Removed on purpose

No mandatory techniques — a non-visual sense in every setting sentence, a
short punch after every long sentence, an image in every paragraph, a
signature simile — and no "controlled imperfection". Each produced a new,
detectable tic. Why: `docs/rationale/literary.md#quotas-removed`

## 6. Craft sources (optional)

None is loaded by default. At setup the human may pick sources that fit the
subgenre, recorded in `bible/style-guide.md` § Craft sources: e.g. King or
Cron (craft), Truby or Story Grid (structure), Chandler or Tomlinson (crime
and noir), Save the Cat! or The Bestseller Code (commercial).

## 7. When a scene stays generic (Writer)

Find the scene's value change and redraft from another entry point: later in
the action, from the least obvious character present, or dialogue-only first
with minimal narration added after. The first version is the predictable one.
