#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lint_fiction.py — the mechanical half of fiction review: tics, names, dialogue form.

Why this exists. A chapter passed every gate while carrying "se ríe" ×7,
"asiente" ×7, "Voy." ×6 and a cast that all spoke the same clipped way — none of
it visible to a reviewer reading one unit, all of it obvious to a counter reading
five. A tic that appears once per unit passes as `minor` every time and is a
pattern across the book. Fiction also has defects no prose reviewer is looking
for: a new named character the Writer invented (the user's rule R4 says the
Writer never does that), a dialogue opened with a hyphen instead of the raya, a
paragraph starting "1999." that prints as an ordered list.

Rules (severity):
  dialogue_ratio (info) · sentence_stats (info) · sentence_run (minor: staccato or
  flat runs) · repeated_ngram (minor: 3–6-grams recurring in ≥3 units) ·
  gesture_tic (minor: lexicon `gestures`, per 1000 words and across units) ·
  paragraph_opener (minor) · cliche (AI-isms major, stock phrases minor) ·
  speech_verb_ornate (minor) · unknown_name (major "NEW-CHARACTER?" at high
  confidence, minor at low — § Confidence) · near_duplicate_name (minor) ·
  attribute_mentions (minor: conflicting eyes/hair/age for one character) ·
  mentioned_on_stage (major) ·
  dialogue_format (major: hyphen/en-dash dialogue in a raya language, mixed
  conventions, dialogue glued to narration) · ordered_list_hazard (major) ·
  scene_break_mix (minor) · unit_length (minor, vs target_words ±30%) ·
  opening_repeat (minor: same opening type 3 units running, or first lines ≥0.5
  similar).

Name detection. Scanned: every prose line, every table cell and every
heading of the chapter except its title (the first heading); code fences and
HTML comments are not. A capitalized
token is a name candidate unless it is a stopword or a `name_exclusions` /
`non_person_names` word (days, months, honorifics, countries, big cities,
platforms, brands, stores). Internal capitals are candidates (`DiStefano`,
`McAllister`; brands like `YouTube` sit in `non_person_names`). ALL-CAPS tokens
of 5+ letters that are not a common or lowercase-elsewhere word are candidates
(`GUSTAVO`); 4 letters or fewer are acronyms and skipped. Italics are scanned:
an italic sentence is prose like any other; a short italic span with no
sentence punctuation (`*Rayuela*`, a title) is a "marked" candidate, and so is
an ALL-CAPS one — marked candidates are low confidence unless they stand in a
speaker/actor position (below). Words of a section heading ("## Gustavo") are
read as sentence-initial. A
token right after an `institution_heads` noun is a place ("Banco Nación",
"Plaza San Martín", "calle Mitre"). Known names come from the character sheets
(name and aliases) and every capitalized word in `bible/world.md` (places,
clubs, venues, public figures). The outline's `location`/`setting` words count
as places (like world.md), never as people. `_extras.md` labels contribute NO
known names: extras are unnamed, and a label word used as a name on the page is
reported as an extra that got a name (`extra_label`; check_story →
EXTRA-PROMOTE).

Speaker/actor position (one definition, used for world.md names, outline
locations, extras' label words and every unknown name): the first word of a
raya inciso (`—Hola —Gustavo sonrió`); up to three words after a speech verb
with no punctuation, `que` or conjunction in between (`—dijo el viejo Gustavo`,
`—le explicó entonces Gustavo`); the name followed — through clitics, negation
or an appositive of up to eight words between commas (`Gustavo, con las manos
en los bolsillos, dijo…`) — by a speech verb, a `person_actions` verb or a
gesture; or right after an `inverted_subject_verbs` verb (`Entró Gustavo.`).
A name right after an `object_markers` word (`a Gustavo`, `de Gustavo`) is not
in that position.

Confidence — high (major; `check_story` makes it a blocking NEW-CHARACTER):
  - seen mid-sentence, not after a locative preposition or an indefinite
    article; or
  - in ANY position, not in the pack's `common_words`, never written in
    lowercase anywhere in the draft or the book, and — when it only ever opens a
    sentence — not an `initial_verb_forms` match ("Gustavo no saludó." is high;
    "Rezó un Padre Nuestro." is not); or
  - in a speaker/actor position, when it is not a common word or a verb form
    ("—Luz miró a Mariana" is high even with "luz" in lowercase elsewhere).
A sentence-initial word right before a `determiners` word ("Firmo un papel.")
reads as a verb. "Never lowercase" looks at the draft, the approved units and
the bible's own prose. An ordinary word still misread as a name goes in
`bible/lexicon.yaml → common_words` — never a name: a mid-sentence occurrence
is high whatever the lists say.
Low (minor): only after a locative/indefinite, a common word that opens ≥2
sentences and is never lowercase, or a marked candidate (short italic span,
ALL CAPS) outside a speaker/actor position. A raya that closes speech and opens
an inciso (`—Hola —Mariana sonrió`) does NOT start a sentence.
Known gap — the semantic backstop is the Critic's character-3 and CG Mode A: a
name that is also a common noun, used only sentence-initially and never in a
speaker/actor position while the noun appears in lowercase elsewhere ("Luz era
la hija de Rosa." next to "no había luz"), reads as the noun.

Mentioned-only names. `bible/world.md` lists figures that are talked about but
never on stage (a `## Names` section, plus places and public figures). ANY
world.md word — a name, a place, a club — and any outline `location` word that
stands in a speaker/actor position is on stage: rule `mentioned_on_stage`
(major). `check_story` turns it into a blocking EXTRA-PROMOTE (a "place" that
speaks or acts is a person).

Usage
  python scripts/lint_fiction.py --unit unit-07
  python scripts/lint_fiction.py --unit unit-07 --file drafts/unit-07/draft.md
  python scripts/lint_fiction.py --book --json drafts/_polish/tics-06/lint.json

Exit codes: 0 (advisory) unless --fail-on major|minor matches; 2 on missing input.
"""

from __future__ import annotations

import argparse
import difflib
import glob as _glob
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from bookkit import lexicon as L  # noqa: E402
from count_rhet import length_stats, runs, flat  # noqa: E402  — one definition of "flat"

SEVERITY_RANK = {"info": 0, "minor": 1, "major": 2}
RAYA_LANGS = {"es", "ca", "gl", "pt"}
TOKEN_RE = re.compile(r"[^\W\d_]+(?:['’][^\W\d_]+)*")
OPENERS = "¿¡«“\"'‘([*_ \t"
STACCATO_MAX_WORDS = 5
RUN_MIN = 5
GESTURE_MIN = 3
GESTURE_PER_1000 = 0.6
NGRAM_MIN_UNITS = 3
NGRAM_TOP_BOOK = 20
NGRAM_TOP_UNIT = 10
LENGTH_TOLERANCE = 0.30
OPENING_SIMILARITY = 0.5
_TIME_OPENING = re.compile(
    r"^(?:(?:el|la|aquel|aquella|ese|esa|esta|este|the|that|on|at|in|one)\s+)?"
    r"(?:lunes|martes|mi[eé]rcoles|jueves|viernes|s[aá]bado|domingo|ma[ñn]ana|tarde|"
    r"noche|madrugada|verano|invierno|oto[ñn]o|primavera|monday|tuesday|wednesday|"
    r"thursday|friday|saturday|sunday|morning|afternoon|evening|night|dawn|summer|"
    r"winter|autumn|spring)\b|^(?:a las|al amanecer|hace \w+|en \d{4}|\d{4}\b|at dawn|"
    r"years later|a[ñn]os despu[ée]s|days later|d[ií]as despu[ée]s)", re.I)
_NUMBERED = re.compile(r"^\s*(\d{1,4})[.)]\s+\S")
_HYPHEN_DIALOGUE = re.compile(r"^\s*(?:--?|–)\s?[¿¡«\"“]?[^\W\d_]")
_HYPHEN_INCISO = re.compile(r"\s[-–](?=[a-záéíóúüñ])")
_GLUED = re.compile(r"[.!?…][\"»”’]?\s+[—–]\s?[¿¡]?[^\W\d_]")
_MASKS = [                      # never prose: code spans, link targets, HTML tags
    re.compile(r"`[^`]*`"),
    re.compile(r"\]\([^)]*\)"),
    re.compile(r"<[^>]+>"),
]
_ITALIC = [re.compile(r"(?<![*\w])\*(?!\*)[^*\n]+?\*(?![*\w])"),
           re.compile(r"(?<![_\w])_[^_\n]+?_(?![_\w])")]
_SENTENCE_PUNCT = re.compile(r"[.!?…;:]")
TITLE_MAX_WORDS = 6            # a short italic span with no sentence punctuation = a title
APPOSITIVE_MAX_WORDS = 8
SPEECH_GAP_WORDS = 3
# Words that end a speech-verb → name attribution: "dijo que Gustavo…" reports
# Gustavo, it does not make him speak.
_ATTRIBUTION_BREAK = {"que", "y", "e", "o", "u", "ni", "pero", "sino", "cuando", "si",
                      "porque", "como", "donde", "mientras", "aunque", "and", "or", "but",
                      "that", "when", "if", "because", "while", "as"}
_APPOSITIVE = re.compile(r"[*_]*\s*,\s*([^,.;:!?¡¿—–()\n]{1,120}?)\s*,\s*")

_ES_NUM = {
    "un": 1, "uno": 1, "una": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5, "seis": 6,
    "siete": 7, "ocho": 8, "nueve": 9, "diez": 10, "once": 11, "doce": 12, "trece": 13,
    "catorce": 14, "quince": 15, "dieciseis": 16, "diecisiete": 17, "dieciocho": 18,
    "diecinueve": 19, "veinte": 20, "veintiun": 21, "veintiuno": 21, "veintidos": 22,
    "veintitres": 23, "veinticuatro": 24, "veinticinco": 25, "veintiseis": 26,
    "veintisiete": 27, "veintiocho": 28, "veintinueve": 29, "treinta": 30,
    "cuarenta": 40, "cincuenta": 50, "sesenta": 60, "setenta": 70, "ochenta": 80,
    "noventa": 90, "cien": 100,
}
_EN_NUM = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
    "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13,
    "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18,
    "nineteen": 19, "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60,
    "seventy": 70, "eighty": 80, "ninety": 90, "hundred": 100,
}


# ---------------------------------------------------------------------------
# Cast and context (check_story imports these — one implementation)
# ---------------------------------------------------------------------------


@dataclass
class Character:
    slug: str
    path: Path
    data: dict = field(default_factory=dict)
    error: str | None = None
    has_front_matter: bool = True
    legacy_name: str = ""      # pre-v3.4 sheet without front matter

    @property
    def name(self) -> str:
        return str(self.data.get("name") or self.legacy_name or "").strip()

    @property
    def aliases(self) -> list[str]:
        raw = self.data.get("aliases") or []
        return [str(a) for a in (raw if isinstance(raw, list) else [raw]) if str(a).strip()]

    @property
    def role(self) -> str:
        return str(self.data.get("role") or "").strip().lower()

    def tokens(self) -> set[str]:
        """Name and alias tokens. Not the slug: slugs are ASCII by convention, and
        `tomas` as a known token would hide a missing accent on `Tomás`."""
        out = set(TOKEN_RE.findall(self.name))
        for a in self.aliases:
            out |= set(TOKEN_RE.findall(a))
        return {t for t in out if t}


def load_cast(root: Path) -> list[Character]:
    """Every `bible/characters/*.md` except `_extras.md`: each one is a
    character sheet (check_story reports a broken, role-less or duplicate one)."""
    base = root / "bible" / "characters"
    cast: list[Character] = []
    if not base.is_dir():
        return cast
    for p in sorted(base.glob("*.md")):
        if p.name == "_extras.md":
            continue
        text = L.read_text(p)
        data, _body, err = L.front_matter(text)
        ch = Character(slug=p.stem, path=p, data=data or {}, error=err,
                       has_front_matter=data is not None)
        if data is None:
            # A pre-v3.4 sheet still names its character: check_story reports the
            # missing front matter; the name detector should not also call the
            # whole cast NEW-CHARACTER.
            m = (re.search(r"\*\*Full name\*\*:\s*([^\n\[]+)", text)
                 or re.search(r"^#\s+.*?[—–-]\s*([^\n\[]+)$", text, re.M))
            ch.legacy_name = m.group(1).strip() if m else p.stem.capitalize()
        if data and data.get("slug"):
            ch.slug = str(data["slug"]).strip()
        cast.append(ch)
    return cast


def load_extras(root: Path) -> tuple[list[dict], str | None]:
    path = root / "bible" / "characters" / "_extras.md"
    if not path.exists():
        return [], None
    data, _body, err = L.front_matter(L.read_text(path))
    if err:
        return [], err
    extras = (data or {}).get("extras") or []
    return [e for e in extras if isinstance(e, dict)], None


def load_outline(root: Path) -> list[dict]:
    """`outline/units.yaml` entries, each with a normalized `_id` (unit-NN)."""
    try:
        data = L.read_yaml(root / "outline" / "units.yaml")
    except ValueError:
        return []
    entries = data.get("units") if isinstance(data, dict) else data
    out = []
    for e in entries or []:
        if isinstance(e, dict):
            uid = L.unit_id(e.get("unit", e.get("id")))
            if uid:
                e = dict(e)
                e["_id"] = uid
                out.append(e)
    return out


@dataclass
class Context:
    root: Path
    meta: dict
    lex: dict
    variant: str
    literary: bool
    raya: bool
    cast: list[Character]
    extras: list[dict]
    outline: list[dict]
    stop: set[str]
    excl: set[str]                   # name_exclusions ∪ non_person_names ∪ institution_heads
    heads: set[str]                  # institution_heads
    connectors: set[str]
    locative: set[str]
    indefinite: set[str]
    known_exact: dict[str, str]      # lower() → display
    known_fold: dict[str, str]       # fold() → display
    name_slug: dict[str, str]        # lower() token → character slug
    common: set[str] = field(default_factory=set)         # common_words (folded)
    verb_forms: list = field(default_factory=list)        # initial_verb_forms, compiled
    object_markers: set[str] = field(default_factory=set)
    world: dict[str, str] = field(default_factory=dict)   # lower() → display, world.md
    mentioned: dict[str, str] = field(default_factory=dict)  # lower() → display, § Names
    speech_rx: re.Pattern | None = None
    action_rx: re.Pattern | None = None
    determiners: set[str] = field(default_factory=set)
    bible_lower: set[str] = field(default_factory=set)   # lowercase words of bible/**/*.md
    extra_tokens: set[str] = field(default_factory=set)  # folded name-like words of extras' labels
    inverted_rx: re.Pattern | None = None                # verbs whose subject may FOLLOW them

    def verb_form(self, tok: str) -> bool:
        return any(rx.fullmatch(tok) for rx in self.verb_forms)


_NAMES_HEADING = re.compile(r"^(#{1,6})\s*(?:names?|nombres?|mentioned|mencionad\w*)\b", re.I)
_HEADING = re.compile(r"^(#{1,6})\s")


def load_world(root: Path, stop: set[str]) -> tuple[set[str], set[str]]:
    """(every capitalized token of bible/world.md, the tokens of its § Names).

    § Names (`## Names`, `## Nombres`, `## Mentioned …`) holds figures that are
    talked about and never on stage; the rest are places, clubs, brands."""
    path = root / "bible" / "world.md"
    if not path.exists():
        return set(), set()
    text = L.strip_comments(L.read_text(path))
    caps = lambda s: {t for t in TOKEN_RE.findall(s)  # noqa: E731
                      if t[:1].isupper() and L.fold(t) not in stop}
    everything, names = caps(text), set()
    level = None
    for line in text.splitlines():
        m, h = _NAMES_HEADING.match(line), _HEADING.match(line)
        if m:
            level = len(m.group(1))
            continue
        if h and level is not None and len(h.group(1)) <= level:
            level = None
        if level is not None:
            names |= caps(line)
    return everything, names


def build_context(root: Path, meta: dict | None = None) -> Context:
    meta = meta if meta is not None else L.load_meta(root)
    variant = L.resolve_variant(meta)
    lex = L.load(variant, root)
    cast = load_cast(root)
    extras, _ = load_extras(root)
    outline = load_outline(root)
    known: set[str] = set()
    name_slug: dict[str, str] = {}
    for ch in cast:
        for t in ch.tokens():
            known.add(t)
            name_slug[t.lower()] = ch.slug
    stop = L.plain_set(lex.get("stopwords"))
    common = L.plain_set(lex.get("common_words"))
    # Extras are unnamed by definition: their labels add NO known names. A label
    # word that is not an ordinary word ("gustavo, el mozo del bar") is watched
    # for instead — on the page as a name, it is an extra that got a name.
    extra_tokens = {L.fold(t) for e in extras for t in TOKEN_RE.findall(str(e.get("label") or ""))
                    if len(t) >= 3 and L.fold(t) not in stop and L.fold(t) not in common}
    world, mentioned = load_world(root, stop)
    # The outline's location/setting words are places — known like world.md's,
    # never persons: in a speaker/actor position they are on stage (EXTRA-PROMOTE).
    for e in outline:
        for key in ("location", "setting"):
            world |= {t for t in TOKEN_RE.findall(str(e.get(key) or ""))
                      if t[:1].isupper() and L.fold(t) not in stop}
    known |= world
    speech = [p for k in ("speech_verbs_plain", "speech_verbs_ornate") for p in lex.get(k) or []]
    actions = list(lex.get("person_actions") or []) + speech + [
        p for _l, rx in L.compile_labeled(lex.get("gestures")) for p in [rx.pattern]]
    return Context(
        root=root, meta=meta, lex=lex, variant=variant,
        literary=L.profile_of(meta) == "book-literary",
        raya=L.base_language(variant) in RAYA_LANGS,
        cast=cast, extras=extras, outline=outline,
        stop=stop,
        excl=(L.plain_set(lex.get("name_exclusions")) | L.plain_set(lex.get("non_person_names"))
              | L.plain_set(lex.get("institution_heads"))),
        heads=L.plain_set(lex.get("institution_heads")),
        connectors=L.plain_set(lex.get("name_connectors")),
        locative=L.plain_set(lex.get("locative_prepositions")),
        indefinite=L.plain_set(lex.get("indefinite_articles")),
        known_exact={t.lower(): t for t in known},
        known_fold={L.fold(t): t for t in known},
        name_slug=name_slug,
        common=common,
        verb_forms=[re.compile(p, re.I) for p in lex.get("initial_verb_forms") or []
                    if isinstance(p, str) and p.strip()],
        object_markers=L.plain_set(lex.get("object_markers")),
        world={t.lower(): t for t in world if t.lower() not in name_slug},
        mentioned={t.lower(): t for t in mentioned if t.lower() not in name_slug},
        speech_rx=L.compile_any(speech, regex=True),
        action_rx=L.compile_any(actions, regex=True),
        determiners=L.plain_set(lex.get("determiners")),
        bible_lower=_bible_lower(root),
        extra_tokens={t for t in extra_tokens if t not in {L.fold(x) for x in known}},
        inverted_rx=L.compile_any(list(lex.get("inverted_subject_verbs") or []), regex=True),
    )


def _bible_lower(root: Path) -> set[str]:
    """Every word the bible writes in lowercase (style-guide calibration passages,
    sheets' prose, digests…): the book's own vocabulary, beyond the frequency list."""
    out: set[str] = set()
    base = root / "bible"
    if not base.is_dir():
        return out
    for p in base.rglob("*.md"):
        try:
            text = L.strip_comments(L.read_text(p))
        except OSError:
            continue
        out |= {L.fold(w) for w in TOKEN_RE.findall(text) if w[:1].islower()}
    return out


# ---------------------------------------------------------------------------
# Units
# ---------------------------------------------------------------------------


@dataclass
class UnitText:
    unit: str
    path: Path
    lines: list[L.ProseLine]
    heads: list[tuple[int, str]]
    breaks: list[tuple[int, str]]
    tables: list[L.ProseLine] = field(default_factory=list)

    @property
    def words(self) -> int:
        return sum(len(L.words(pl.text)) for pl in self.lines)

    @property
    def name_lines(self) -> list[L.ProseLine]:
        """What the name detector reads: prose, table cells and headings. The
        unit's first heading is its title (kind `title`: not scanned for names —
        "# 3. Trampas"); later headings (kind `heading`: a section named
        "## Gustavo") read as sentence-initial prose. Tics, lengths and rhetoric
        read `lines` only."""
        heads = [L.make_prose_line(n, "title" if k == 0 else "heading", h, True)
                 for k, (n, h) in enumerate(self.heads) if h.strip()]
        return sorted(self.lines + self.tables + heads, key=lambda pl: pl.line)


def read_unit(unit: str, path: Path, literary: bool = True) -> UnitText:
    lines, heads, breaks = L.prose_lines(path, literary=literary)
    return UnitText(unit, path, lines, heads, breaks, L.table_lines(path, literary=literary))


def unit_file(root: Path, unit: str) -> Path | None:
    for rel in (f"drafts/{unit}/humanized.md", f"drafts/{unit}/edit.md",
                f"drafts/{unit}/draft.md", f"final/{unit}.md"):
        if (root / rel).exists():
            return root / rel
    return None


def final_units(root: Path, patterns: list[str] | None = None) -> list[tuple[str, Path]]:
    for pat in patterns or ["final/unit-*.md", "final/ch-*.md"]:
        full = pat if Path(pat).is_absolute() else str(root / pat)
        paths = [Path(m) for m in _glob.glob(full) if Path(m).is_file()]
        if paths:
            paths.sort(key=lambda p: (L.unit_num(p.stem) or 10**9, p.stem))
            return [(L.unit_id(p.stem) or p.stem, p) for p in paths]
    return []


# ---------------------------------------------------------------------------
# Names
# ---------------------------------------------------------------------------


def _mask(text: str) -> str:
    for rx in _MASKS:
        text = rx.sub(lambda m: " " * len(m.group(0)), text)
    return text


def _is_initial(prefix: str) -> bool:
    p = prefix.rstrip(OPENERS)
    if not p:
        return True
    c = p[-1]
    if c in ".!?…:":
        return True
    if c in "—–-":
        before = p[:-1].rstrip(OPENERS)
        return not before or before[-1] in ".!?…:"
    return False


def _gap_ok(gap: str) -> bool:
    """Only spaces (and italic markers) between two words: no punctuation."""
    return not gap.replace("*", "").replace("_", "").strip()


def _title_spans(masked: str) -> list[tuple[int, int]]:
    """Italic spans that read as a title, not as italic prose: at most
    TITLE_MAX_WORDS words and no sentence punctuation (`*Rayuela*`,
    `_Cien años de soledad_`). A whole italic sentence is prose."""
    out = []
    for rx in _ITALIC:
        for m in rx.finditer(masked):
            inner = m.group(0)[1:-1]
            if not _SENTENCE_PUNCT.search(inner) and len(L.words(inner)) <= TITLE_MAX_WORDS:
                out.append((m.start(), m.end()))
    return out


def name_key(raw: str) -> str | None:
    """The candidate form of a word, or None when it cannot be a name.
    `GUSTAVO` → `Gustavo` (ALL CAPS, 5+ letters); `ONU`, `YPF` → None (acronyms);
    `DiStefano` stays as written; lowercase words → None."""
    tok = re.sub(r"['’]s$", "", raw)
    if len(tok) < 2 or not tok[0].isupper():
        return None
    if tok.isupper():
        if sum(ch.isalpha() for ch in tok) < 5:
            return None
        return tok[0] + tok[1:].lower()
    return tok


@dataclass
class Candidate:
    token: str
    initial: bool
    prev1: str        # the word right before, as written ("" at line start)
    prev2: str
    next1: str = ""   # the word right after, when only spaces separate them
    marked: str = ""  # "" | "italic" (a short italic span, e.g. a title) | "caps"


def name_candidates(text: str, all_initial: bool = False) -> list[Candidate]:
    """Every capitalized token of a line, with its sentence position and the two
    words before it (the context the place/product heuristics read).

    Skipped outright: one-letter tokens and acronyms (ALL CAPS, ≤4 letters).
    ALL CAPS of 5+ letters are candidates under their title-case form, marked
    `caps`; a token inside a short italic span is marked `italic`. Internal
    capitals (`DiStefano`) are ordinary candidates. `all_initial`: every word
    reads as sentence-initial (headings)."""
    masked = _mask(text)
    titles = _title_spans(masked)
    out = []
    words = list(TOKEN_RE.finditer(masked))
    for i, m in enumerate(words):
        tok = name_key(m.group(0))
        if tok is None:
            continue
        marked = "caps" if re.sub(r"['’]s$", "", m.group(0)).isupper() else ""
        if not marked and any(s <= m.start() < e for s, e in titles):
            marked = "italic"
        # Previous words only count when nothing but spaces/connectors separate
        # them: "Bar Roma", "Cooperativa de Aguas" — not "bar. Roma".
        prev = []
        for j in (i - 1, i - 2):
            if j < 0:
                break
            if not _gap_ok(masked[words[j].end():words[j + 1].start()]):
                break
            prev.append(words[j].group(0))
        prev += ["", ""]
        nxt = ""
        if i + 1 < len(words) and _gap_ok(masked[m.end():words[i + 1].start()]):
            nxt = words[i + 1].group(0)
        initial = all_initial or _is_initial(masked[:m.start()])
        out.append(Candidate(tok, initial, prev[0], prev[1], nxt, marked))
    return out


def lower_forms(units: list[UnitText]) -> set[str]:
    out: set[str] = set()
    for u in units:
        for pl in u.name_lines:
            out |= {L.fold(t) for t in TOKEN_RE.findall(pl.text) if t[:1].islower()}
    return out


def _levenshtein(a: str, b: str) -> int:
    if abs(len(a) - len(b)) > 1:
        return 2
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def _hint(ctx: Context, tok: str) -> str:
    f = L.fold(tok)
    for kf, disp in ctx.known_fold.items():
        if len(f) >= 5 and len(kf) >= 5 and _levenshtein(f, kf) == 1:
            return f" — near-duplicate of '{disp}' (typo?)"
    for kf, disp in ctx.known_fold.items():
        if len(kf) >= 4 and len(f) >= 4 and kf[:4] == f[:4] and (
                kf.startswith(f) or f.startswith(kf) or re.search(r"(it[ao]|cit[ao]|in)$", f)):
            return f" — possible alias or diminutive of '{disp}': add it to that sheet's aliases"
    return ""


def unknown_names(ctx: Context, unit: UnitText, corpus_lower: set[str]) -> list[dict]:
    """Findings `unknown_name` / `near_duplicate_name` for one unit."""
    seen: dict[str, dict] = {}
    staged_at = positions(ctx, unit)
    for pl in unit.name_lines:
        if pl.kind == "title":
            continue                # "# 3. Trampas": the chapter title is not the stage
        for c in name_candidates(pl.text, all_initial=pl.kind == "heading"):
            tok = c.token
            low, f = tok.lower(), L.fold(tok)
            if f in ctx.stop or f in ctx.excl or low in ctx.known_exact:
                continue
            if c.marked == "caps" and (f in ctx.common or f in corpus_lower
                                       or f in ctx.bible_lower):
                continue            # "FRÁGIL" on a box: an ordinary word in capitals
            p1, p2 = L.fold(c.prev1), L.fold(c.prev2)
            if p1 in ctx.heads or (p2 in ctx.heads and (p1 in ctx.connectors
                                                      or c.prev1[:1].isupper())):
                continue            # "Banco Nación", "Plaza San Martín", "calle Mitre"
            e = seen.setdefault(tok, {"lines": [], "mid": 0, "initial": 0, "strong": 0,
                                      "verbish": 0, "marked": 0})
            e["lines"].append(pl.line)
            if c.marked:
                e["marked"] += 1     # a title in italics, a sign in capitals: position decides
                continue
            e["mid" if not c.initial else "initial"] += 1
            # "Firmo un papel", "Cobro el sueldo": a sentence-initial word followed by
            # a determiner is a verb far more often than a name ("Gustavo el…").
            if c.initial and L.fold(c.next1) in ctx.determiners:
                e["verbish"] += 1
            # "en Treviso", "una Coca": mid-sentence, but a place or a product is
            # the likelier reading. Strong = mid-sentence without that context.
            if not c.initial and p1 not in ctx.locative and p1 not in ctx.indefinite:
                e["strong"] += 1
    out: list[dict] = []
    for tok, e in seen.items():
        f = L.fold(tok)
        lines = sorted(set(e["lines"]))
        where = ", ".join(str(n) for n in lines[:6])
        if f in ctx.known_fold:
            out.append(_f("near_duplicate_name", "minor", unit.unit, lines[0],
                          f"'{tok}' differs from '{ctx.known_fold[f]}' only by accents or case "
                          f"(lines {where})", subject=tok))
            continue
        initial_only = not e["mid"]
        verbish = initial_only and (ctx.verb_form(tok) or e["verbish"] == e["initial"])
        rare = (f not in ctx.common and f not in corpus_lower and f not in ctx.bible_lower
                and not verbish)
        stage = staged_at.get(tok) or {}
        staged = sorted(set(stage.get("speaks", []) + stage.get("acts", [])))
        if staged and f not in ctx.common and not ctx.verb_form(tok):
            how = "speaks" if stage.get("speaks") else "acts"
            conf, why = "high", (f" [{how} on the page (line {min(stage[how])}) — a figure "
                                 "with lines or actions is a person]")
        elif not (e["mid"] or e["initial"]):
            conf, why = "low", (" [low confidence: only in italics or capitals, never speaking "
                                "or acting — a title, a sign, an emphasis? If it is a person, "
                                "it needs a sheet]")
        elif e["strong"]:
            conf, why = "high", ""
        elif rare:
            conf, why = "high", (" [not a common word, never written in lowercase"
                                 + (", sentence-initial only — an ordinary word goes in "
                                    "bible/lexicon.yaml → common_words, a name never"
                                    if initial_only else
                                    ", only after a locative preposition or an indefinite "
                                    "article — a place goes in world.md") + "]")
        elif e["mid"] or (e["initial"] >= 2 and f not in corpus_lower):
            conf, why = "low", (" [low confidence: " + (
                "only after a locative preposition or an indefinite article" if e["mid"]
                else "a common word, sentence-initial only, never lowercase") + "]")
        else:
            continue
        n = len(e["lines"])
        extra = f in ctx.extra_tokens
        out.append(_f("unknown_name", "major" if conf == "high" else "minor", unit.unit,
                      lines[0],
                      f"NEW-CHARACTER? '{tok}' ×{n} (lines {where}) — not in any character "
                      f"sheet, alias or world.md" + why
                      + (" — it is a word of an _extras.md label: extras are unnamed, and an "
                         "extra with a name is a character" if extra else "")
                      + _hint(ctx, tok),
                      subject=tok, confidence=conf, extra_label=extra))
    return out


def _segments(pl: L.ProseLine) -> list[tuple[str, bool]]:
    """(text, is_inciso) pieces of a prose line where the NARRATOR speaks: the
    incisos of a raya line, or the sentences of any other line with quoted
    speech removed. What a character says is not what the page shows it doing."""
    if pl.kind in ("heading", "title"):
        return []
    if pl.text.lstrip().startswith(L.RAYA) or (pl.dialogue and not re.match(r"^\s*[\"“«]",
                                                                           pl.text)):
        return [(s.strip(), True) for s in L.split_raya(pl.text)[1] if s.strip()]
    return [(s, False) for s in L.split_sentences(L.strip_quoted(pl.text))]


def _skippable(ctx: Context, word: str) -> bool:
    return L.fold(word) in ctx.stop


def _clause_verb(ctx: Context, masked: str, words: list, j: int, pos: int) -> str | None:
    """From word j on (`pos` = where the name ended), through at most three
    clitics / negations: 'speech', 'action' or None. "Gustavo no saludó",
    "Gustavo le dijo", "Gustavo el que hablaba"."""
    start = j
    while j < len(words) and j <= start + 2:
        if not _gap_ok(masked[pos:words[j].start()]):
            return None                          # punctuation ends the clause
        rest = masked[words[j].start():]
        if ctx.speech_rx is not None and ctx.speech_rx.match(rest):
            return "speech"
        if ctx.action_rx is not None and ctx.action_rx.match(rest):
            return "action"
        if not _skippable(ctx, words[j].group(0)):
            return None
        pos, j = words[j].end(), j + 1
    return None


def _word_at(words: list, pos: int) -> int:
    return next((k for k, w in enumerate(words) if w.start() >= pos), len(words))


def positions(ctx: Context, unit: UnitText) -> dict[str, dict[str, list[int]]]:
    """Every capitalized token (candidate form: `GUSTAVO` → `Gustavo`) in a
    SPEAKER or ACTOR position, with its lines. The one definition shared by
    world.md names, outline locations, extras' label words and unknown names:

      speaks — the first word of a raya inciso ("—Hola —Gustavo sonrió");
               a speech verb up to SPEECH_GAP_WORDS words before it, no
               punctuation / `que` / conjunction / other name in between
               ("—dijo el viejo Gustavo", "—le explicó entonces Gustavo");
               or followed by a speech verb (below).
      acts   — followed, through clitics/negation or one appositive of up to
               APPOSITIVE_MAX_WORDS words between commas, by a speech verb, a
               person action or a gesture ("Gustavo no saludó", "Gustavo, con
               las manos en los bolsillos, dijo…"); or right after an
               `inverted_subject_verbs` verb ("Entró Gustavo.").
    Not a position: right after an object marker ("a Gustavo", "de Rosario"),
    an institution head ("calle Salta") or another capitalized word ("Rosario
    Central")."""
    cache = unit.__dict__.setdefault("_positions", {})
    if id(ctx) in cache:
        return cache[id(ctx)]
    out: dict[str, dict[str, list[int]]] = {}
    for pl in unit.name_lines:
        _line_positions(ctx, pl, out)
    out = {k: v for k, v in out.items() if v["speaks"] or v["acts"]}
    cache[id(ctx)] = out
    return out


def text_positions(ctx: Context, text: str) -> dict[str, dict[str, list[int]]]:
    """`positions` for one free text (an outline card field)."""
    out: dict[str, dict[str, list[int]]] = {}
    _line_positions(ctx, L.make_prose_line(0, "para", text, True), out)
    return {k: v for k, v in out.items() if v["speaks"] or v["acts"]}


def _line_positions(ctx: Context, pl: L.ProseLine, out: dict) -> None:
    for seg, inciso in _segments(pl):
        masked = _mask(seg)
        words = list(TOKEN_RE.finditer(masked))
        titles = _title_spans(masked)
        for i, m in enumerate(words):
            tok = name_key(m.group(0))
            if tok is None or L.fold(tok) in ctx.stop:
                continue
            # A sign or a title after a speech verb in narration is what the
            # object says ("la caja decía FRÁGIL"): for capitals and short
            # italic spans the speech verb counts only in a dialogue inciso.
            marked = (re.sub(r"['’]s$", "", m.group(0)).isupper()
                      or any(s <= m.start() < e for s, e in titles))
            prev = words[i - 1] if i else None
            pw = prev.group(0) if prev is not None else ""
            glued = prev is not None and _gap_ok(masked[prev.end():m.start()])
            inverted = bool(glued and ctx.inverted_rx is not None
                            and ctx.inverted_rx.fullmatch(pw))
            if glued and not inverted and (
                    L.fold(pw) in ctx.object_markers or L.fold(pw) in ctx.heads
                    or (pw[:1].isupper() and L.fold(pw) not in ctx.excl
                        and L.fold(pw) not in ctx.stop
                        and not (ctx.speech_rx and ctx.speech_rx.fullmatch(pw)))):
                continue     # "a Gustavo" (object), "calle Salta", "Rosario Central"
            speaks = inciso and i == 0
            # a speech verb up to three words back: "dijo el viejo Gustavo"
            for k in range(i - 1, max(-1, i - 2 - SPEECH_GAP_WORDS), -1):
                if speaks or ctx.speech_rx is None or (marked and not inciso):
                    break
                if not _gap_ok(masked[words[k].end():words[k + 1].start()]):
                    break                        # punctuation in between
                w = words[k].group(0)
                if ctx.speech_rx.fullmatch(w):
                    speaks = True
                elif L.fold(w) in _ATTRIBUTION_BREAK or (
                        w[:1].isupper() and L.fold(w) not in ctx.stop
                        and L.fold(w) not in ctx.excl):
                    break                        # "dijo que Gustavo", "dijo Mariana a…"
            # the name, then (clitics, negation, an appositive) a verb
            verb = _clause_verb(ctx, masked, words, i + 1, m.end())
            if verb is None:
                ap = _APPOSITIVE.match(masked, m.end())
                if ap and 0 < len(L.words(ap.group(1))) <= APPOSITIVE_MAX_WORDS:
                    verb = _clause_verb(ctx, masked, words, _word_at(words, ap.end()),
                                        ap.end())
            rec = out.setdefault(tok, {"speaks": [], "acts": []})
            if speaks or verb == "speech":
                rec["speaks"].append(pl.line)
            if verb or inverted:
                rec["acts"].append(pl.line)


def stage_presence(ctx: Context, unit: UnitText) -> dict[str, dict[str, list[int]]]:
    """For every world.md word (a name, a place, a club) and outline location
    that is not a character: the lines where it SPEAKS or ACTS (`positions`).
    Mentioned-only means neither."""
    out: dict[str, dict[str, list[int]]] = {}
    if not ctx.world:
        return out
    for tok, rec in positions(ctx, unit).items():
        disp = ctx.world.get(tok.lower())
        if disp is None:
            continue
        r = out.setdefault(disp, {"speaks": [], "acts": []})
        r["speaks"] += rec["speaks"]
        r["acts"] += rec["acts"]
    return out


def on_stage_findings(ctx: Context, unit: UnitText) -> list[dict]:
    """`mentioned_on_stage`: a world.md / outline-location word that speaks or
    acts on this page."""
    out = []
    for tok, rec in sorted(stage_presence(ctx, unit).items()):
        lines = sorted(set(rec["speaks"] + rec["acts"]))
        what = "speaks" if rec["speaks"] else "acts as the subject of a scene"
        out.append(_f("mentioned_on_stage", "major", unit.unit, lines[0],
                      f"'{tok}' is in bible/world.md or an outline location (mentioned-only: a "
                      f"name, a place) but {what} here (lines "
                      f"{', '.join(map(str, lines[:6]))}) — a figure on stage is a character",
                      subject=tok, speaks=bool(rec["speaks"]), acts=bool(rec["acts"])))
    return out


# ---------------------------------------------------------------------------
# Per-unit rules
# ---------------------------------------------------------------------------


def _f(rule: str, severity: str, unit: str, line: int | None, detail: str, **extra) -> dict:
    d = {"rule": rule, "severity": severity, "unit": unit, "line": line, "detail": detail}
    d.update(extra)
    return d


def _num(value: str, lang: str) -> int | None:
    v = L.fold(value.strip())
    if v.isdigit():
        return int(v)
    table = _ES_NUM if lang == "es" else _EN_NUM
    total = 0
    for part in re.split(r"\s+y\s+|-|\s+", v):
        if not part:
            continue
        if part not in table:
            return None
        total += table[part]
    return total or None


def _norm_value(attr: str, value: str, lang: str) -> str | None:
    if attr == "age":
        n = _num(value, lang)
        return str(n) if n else None
    v = L.fold(value)
    if lang == "es":
        v = v[:-1] if v.endswith("s") else v
        if v.endswith("e") and len(v) > 3 and v[-2] in "lnrzs":
            v = v[:-1]
        if v.endswith("a"):
            v = v[:-1] + "o"
    return v.replace("grey", "gray").replace("blonde", "blond")


def attributes(ctx: Context, unit: UnitText) -> list[tuple[str, str, str, str, int]]:
    """(slug, attr, value, unit, line) for attribute mentions tied to ONE character."""
    lang = L.base_language(ctx.variant)
    pats = {attr: L.compile_labeled({attr: p})
            for attr, p in (ctx.lex.get("attribute_terms") or {}).items()}
    out = []
    for pl in unit.lines:
        for sent in L.split_sentences(pl.text):
            slugs = {ctx.name_slug[t.lower()] for t in TOKEN_RE.findall(sent)
                     if t[:1].isupper() and t.lower() in ctx.name_slug}
            if len(slugs) != 1:
                continue
            slug = next(iter(slugs))
            for attr, compiled in pats.items():
                for _label, rx in compiled:
                    for m in rx.finditer(sent):
                        val = _norm_value(attr, m.group("value"), lang)
                        if val:
                            out.append((slug, attr, val, unit.unit, pl.line))
    return out


def attribute_conflicts(mentions, focus: str | None = None) -> list[dict]:
    by: dict[tuple[str, str], list] = defaultdict(list)
    for slug, attr, val, unit, line in mentions:
        by[(slug, attr)].append((val, unit, line))
    out = []
    for (slug, attr), rows in sorted(by.items()):
        values = {v for v, _, _ in rows}
        if len(values) < 2:
            continue
        if focus and not any(u == focus for _, u, _ in rows):
            continue
        desc = "; ".join(f"{v} ({u}:{ln})" for v, u, ln in rows[:8])
        first = next(((u, ln) for v, u, ln in rows if u == focus), (rows[0][1], rows[0][2]))
        out.append(_f("attribute_mentions", "minor", first[0], first[1],
                      f"{slug} {attr}: conflicting values — {desc}", subject=slug))
    return out


def gesture_counts(ctx: Context, unit: UnitText) -> dict[str, dict]:
    words = unit.words or 1
    per_1000 = float(L.meta_get(ctx.meta, "literary.tics.gesture_per_1000", GESTURE_PER_1000))
    minimum = int(L.meta_get(ctx.meta, "literary.tics.gesture_min", GESTURE_MIN))
    quota = max(minimum, round(per_1000 * words / 1000))
    out: dict[str, dict] = {}
    for label, rx in L.compile_labeled(ctx.lex.get("gestures")):
        lines = [pl.line for pl in unit.lines for _ in rx.finditer(pl.text)]
        if lines:
            out[label] = {"count": len(lines), "lines": lines, "quota": quota,
                          "per_1000": round(len(lines) / words * 1000, 2),
                          "over": len(lines) > quota}
    return out


def per_unit(ctx: Context, u: UnitText, target: int | None) -> tuple[list[dict], dict]:
    out: list[dict] = []
    lex = ctx.lex
    words = u.words
    speech_words = sum(len(L.words(" ".join(pl.speech))) for pl in u.lines)
    ratio = round(speech_words / words, 3) if words else 0.0
    out.append(_f("dialogue_ratio", "info", u.unit, None,
                  f"dialogue {ratio:.0%} of {words} words"))

    # Sentences of narration, with their lines
    narr: list[tuple[int, int]] = []
    for pl in u.lines:
        if ctx.literary and pl.dialogue:
            continue
        for s in L.split_sentences(pl.narration):
            n = len(L.words(s))
            if n:
                narr.append((pl.line, n))
    lengths = [n for _, n in narr]
    st = length_stats(lengths)
    out.append(_f("sentence_stats", "info", u.unit, None,
                  f"narration sentences {st['sentences']}: mean {st['mean']}, sd {st['sd']}"))
    for start, length in runs(lengths, min_len=RUN_MIN,
                              pred=lambda w: max(w) <= STACCATO_MAX_WORDS):
        out.append(_f("sentence_run", "minor", u.unit, narr[start][0],
                      f"staccato run: {length} sentences in a row of ≤{STACCATO_MAX_WORDS} "
                      f"words"))
    for start, length in runs(lengths, min_len=RUN_MIN, pred=flat):
        if min(lengths[start:start + length]) > STACCATO_MAX_WORDS:
            out.append(_f("sentence_run", "minor", u.unit, narr[start][0],
                          f"flat run: {length} sentences in a row of near-identical length"))

    # Gesture tics
    tics = gesture_counts(ctx, u)
    for label, t in sorted(tics.items()):
        if t["over"]:
            out.append(_f("gesture_tic", "minor", u.unit, t["lines"][0],
                          f"'{label}' ×{t['count']} in {words} words (quota {t['quota']}; "
                          f"lines {', '.join(map(str, sorted(set(t['lines']))[:8]))})", subject=label))

    # Paragraph openers
    openers: Counter = Counter()
    first_line: dict[str, int] = {}
    paras = [pl for pl in u.lines if pl.kind == "para" and not pl.dialogue]
    for pl in paras:
        w = [x.lower() for x in L.words(pl.text)[:2]]
        if len(w) == 2:
            key = " ".join(w)
            openers[key] += 1
            first_line.setdefault(key, pl.line)
    for key, n in openers.items():
        if n >= 3 and n >= 0.1 * len(paras):
            out.append(_f("paragraph_opener", "minor", u.unit, first_line[key],
                          f"{n} paragraphs open with '{key}'"))

    # Clichés and AI-isms
    for key, sev, label in (("ai_isms", "major", "AI-ism"), ("cliches", "minor", "cliché")):
        rx = L.compile_any(lex.get(key, []), regex=True)
        for pl in u.lines:
            for m in L.iter_matches(rx, pl.text):
                out.append(_f("cliche", sev, u.unit, pl.line, f"{label}: '{m.group(0)}'",
                              subject=m.group(0)))

    rx = L.compile_any(lex.get("speech_verbs_ornate", []), regex=True)
    for pl in u.lines:
        for m in L.iter_matches(rx, pl.text):
            out.append(_f("speech_verb_ornate", "minor", u.unit, pl.line,
                          f"ornate speech verb '{m.group(0)}' — let the line carry the manner",
                          subject=m.group(0)))

    out += dialogue_format(ctx, u)

    numbered = {pl.line for pl in u.lines if _NUMBERED.match(pl.text)}
    for pl in u.lines:
        m = _NUMBERED.match(pl.text)
        if not m:
            continue
        neighbours = any(abs(pl.line - o) <= 2 for o in numbered if o != pl.line)
        if int(m.group(1)) >= 10 or not neighbours:
            out.append(_f("ordered_list_hazard", "major", u.unit, pl.line,
                          f"paragraph starts '{m.group(0).strip()[:12]}…' — renders as an "
                          f"ordered list; escape it ('{m.group(1)}\\.') or rephrase"))

    styles = {}
    for ln, s in u.breaks:
        styles.setdefault(re.sub(r"\s+", " ", s.strip()), ln)
    if len(styles) > 1:
        out.append(_f("scene_break_mix", "minor", u.unit, min(styles.values()),
                      f"scene breaks mix styles: {', '.join(repr(s) for s in styles)}"))

    if target:
        dev = (words - target) / target
        if abs(dev) > LENGTH_TOLERANCE:
            out.append(_f("unit_length", "minor", u.unit, None,
                          f"{words} words vs target {target} ({dev:+.0%}; tolerance ±30%)"))

    stats = {"words": words, "dialogue_ratio": ratio, "sentence_mean": st["mean"],
             "sentence_sd": st["sd"], "flat_runs": st["flat_runs"],
             "tics": {k: {kk: v[kk] for kk in ("count", "per_1000", "quota", "over")}
                      for k, v in tics.items()}}
    return out, stats


def dialogue_format(ctx: Context, u: UnitText) -> list[dict]:
    out = []
    raya_lines = [pl for pl in u.lines if pl.text.lstrip().startswith(L.RAYA)]
    quote_lines = [pl for pl in u.lines if re.match(r"^\s*[\"“«]", pl.text)]
    for pl in u.lines:
        t = pl.text
        if ctx.raya and _HYPHEN_DIALOGUE.match(t):
            out.append(_f("dialogue_format", "major", u.unit, pl.line,
                          "dialogue opened with a hyphen/en-dash — use the raya (—)"))
        elif ctx.raya and t.lstrip().startswith(L.RAYA) and _HYPHEN_INCISO.search(t):
            out.append(_f("dialogue_format", "major", u.unit, pl.line,
                          "inciso marked with a hyphen — use the raya (—)"))
        if not t.lstrip().startswith((L.RAYA, "–", "-")) and _GLUED.search(t):
            out.append(_f("dialogue_format", "major", u.unit, pl.line,
                          "dialogue glued to narration — a speech line starts mid-paragraph; "
                          "give it its own paragraph"))
    if raya_lines and quote_lines:
        out.append(_f("dialogue_format", "major", u.unit, quote_lines[0].line,
                      f"mixed dialogue conventions: {len(raya_lines)} raya line(s) and "
                      f"{len(quote_lines)} quote-opened line(s)"))
    glyphs = {pl.text.lstrip()[0] for pl in quote_lines}
    if len({"«" if g == "«" else "“" if g == "“" else '"' for g in glyphs}) > 1:
        out.append(_f("dialogue_format", "major", u.unit, quote_lines[0].line,
                      f"mixed quotation marks for dialogue: {' '.join(sorted(glyphs))}"))
    return out


# ---------------------------------------------------------------------------
# Cross-unit rules
# ---------------------------------------------------------------------------


def _ngrams(ctx: Context, u: UnitText) -> Counter:
    names = {t for t in ctx.name_slug} | {L.fold(t) for t in ctx.known_exact}
    grams: Counter = Counter()
    for pl in u.lines:
        w = [L.fold(x) for x in L.words(pl.text)]
        for n in range(3, 7):
            for i in range(len(w) - n + 1):
                g = w[i:i + n]
                content = [x for x in g if x not in ctx.stop and x not in names
                           and not x.isdigit()]
                if len(content) >= 2 or (content and n >= 4):
                    grams[" ".join(g)] += 1
    return grams


def repeated_ngrams(ctx: Context, units: list[UnitText], focus: str | None = None) -> list[dict]:
    per_unit = {u.unit: _ngrams(ctx, u) for u in units}
    where: dict[str, set[str]] = defaultdict(set)
    total: Counter = Counter()
    for unit, grams in per_unit.items():
        for g, c in grams.items():
            where[g].add(unit)
            total[g] += c
    cands = [g for g, us in where.items() if len(us) >= NGRAM_MIN_UNITS
             and (focus is None or focus in us)]
    cands.sort(key=lambda g: (-len(where[g]), -len(g.split()), -total[g], g))
    chosen: list[str] = []
    for g in cands:
        if any(f" {g} " in f" {c} " and where[c] == where[g] for c in chosen):
            continue
        chosen.append(g)
        if len(chosen) >= (NGRAM_TOP_UNIT if focus else NGRAM_TOP_BOOK):
            break
    return [_f("repeated_ngram", "minor", focus or "book", None,
               f"'{g}' ×{total[g]} across {len(where[g])} units "
               f"({', '.join(sorted(where[g]))})", subject=g) for g in chosen]


def cross_tics(ctx: Context, units: list[UnitText], focus: str | None = None) -> list[dict]:
    per: dict[str, dict[str, int]] = defaultdict(dict)
    for u in units:
        for label, t in gesture_counts(ctx, u).items():
            per[label][u.unit] = t["count"]
    out = []
    need = max(NGRAM_MIN_UNITS, (len(units) + 1) // 2)
    for label, counts in sorted(per.items()):
        heavy = [u for u, c in counts.items() if c >= 2]
        if len(heavy) >= need and (focus is None or focus in heavy):
            out.append(_f("gesture_tic", "minor", focus or "book", None,
                          f"'{label}' recurs across units: "
                          + ", ".join(f"{u}×{counts[u]}" for u in sorted(counts)),
                          subject=label))
    return out


def _opening(u: UnitText) -> tuple[str, str]:
    first = next((pl for pl in u.lines if pl.text.strip()), None)
    if first is None:
        return "empty", ""
    sent = (L.split_sentences(first.text) or [first.text])[0]
    if first.dialogue or first.text.lstrip().startswith(L.RAYA):
        kind = "dialogue"
    elif sent.rstrip(" »”\"").endswith("?"):
        kind = "question"
    elif _TIME_OPENING.match(re.sub(r"^[\W_]+", "", sent)):
        kind = "time"
    else:
        kind = "narration"
    return kind, sent


def opening_repeat(units: list[UnitText], focus: str | None = None) -> list[dict]:
    kinds = [(u.unit, *_opening(u)) for u in units]
    out = []
    for i in range(len(kinds)):
        unit, kind, sent = kinds[i]
        if focus and unit != focus:
            continue
        if i >= 2 and kinds[i - 1][1] == kind == kinds[i - 2][1] and kind != "empty":
            out.append(_f("opening_repeat", "minor", unit, None,
                          f"third unit in a row opening with {kind} "
                          f"({kinds[i - 2][0]}, {kinds[i - 1][0]}, {unit})"))
        for j in range(max(0, i - 3), i):
            a = [L.fold(w) for w in L.words(sent)]
            b = [L.fold(w) for w in L.words(kinds[j][2])]
            if a and b:
                r = difflib.SequenceMatcher(None, a, b, autojunk=False).ratio()
                if r >= OPENING_SIMILARITY:
                    out.append(_f("opening_repeat", "minor", unit, None,
                                  f"first line {r:.0%} similar to {kinds[j][0]}'s"))
    return out


def confusable_names(ctx: Context) -> list[dict]:
    firsts = []
    for ch in ctx.cast:
        toks = TOKEN_RE.findall(ch.name)
        if toks:
            firsts.append((ch.slug, toks[0]))
    out = []
    for i in range(len(firsts)):
        for j in range(i + 1, len(firsts)):
            (sa, a), (sb, b) = firsts[i], firsts[j]
            fa, fb = L.fold(a), L.fold(b)
            if fa == fb or (min(len(fa), len(fb)) >= 4 and _levenshtein(fa, fb) <= 1):
                out.append(_f("near_duplicate_name", "minor", "bible", None,
                              f"confusable character names: '{a}' ({sa}) and '{b}' ({sb})"))
    return out


# ---------------------------------------------------------------------------


def _target(ctx: Context, unit: str) -> int | None:
    for e in ctx.outline:
        if e["_id"] == unit and e.get("target_words"):
            try:
                return int(e["target_words"]) or None
            except (TypeError, ValueError):
                return None
    val = L.meta_get(ctx.meta, "structure.unit_length_target_words")
    try:
        return int(val) if val else None
    except (TypeError, ValueError):
        return None


def lint_unit(root: Path, unit: str, file: Path | None = None,
              ctx: Context | None = None) -> dict:
    ctx = ctx or build_context(root)
    path = file or unit_file(root, unit)
    if path is None or not path.exists():
        raise FileNotFoundError(path or f"no text for {unit}")
    u = read_unit(unit, path, literary=True)
    others = [read_unit(uid, p) for uid, p in final_units(root)
              if not (uid == unit and p.resolve() == path.resolve())]
    others = [o for o in others if o.unit != unit]
    corpus = [u] + others
    findings, stats = per_unit(ctx, u, _target(ctx, unit))
    findings += unknown_names(ctx, u, lower_forms(corpus))
    findings += on_stage_findings(ctx, u)
    mentions = [m for x in corpus for m in attributes(ctx, x)]
    findings += attribute_conflicts(mentions, focus=unit)
    ordered = sorted(others + [u], key=lambda x: (L.unit_num(x.unit) or 0, x.unit))
    findings += opening_repeat([x for x in ordered if (L.unit_num(x.unit) or 0)
                                <= (L.unit_num(unit) or 0)], focus=unit)
    findings += repeated_ngrams(ctx, corpus, focus=unit)
    findings += cross_tics(ctx, corpus, focus=unit)
    return _report("unit", ctx, findings, {unit: stats}, [_rel(path, root)])


def lint_book(root: Path, patterns: list[str] | None = None,
              ctx: Context | None = None) -> dict:
    ctx = ctx or build_context(root)
    units = [read_unit(uid, p) for uid, p in final_units(root, patterns)]
    if not units:
        raise FileNotFoundError("no unit files (final/unit-*.md)")
    corpus_lower = lower_forms(units)
    findings: list[dict] = []
    stats: dict = {}
    for u in units:
        f, s = per_unit(ctx, u, _target(ctx, u.unit))
        findings += f + unknown_names(ctx, u, corpus_lower) + on_stage_findings(ctx, u)
        stats[u.unit] = s
    findings += attribute_conflicts([m for u in units for m in attributes(ctx, u)])
    findings += opening_repeat(units)
    findings += repeated_ngrams(ctx, units)
    findings += cross_tics(ctx, units)
    findings += confusable_names(ctx)
    styles = {re.sub(r"\s+", " ", s.strip()) for u in units for _, s in u.breaks}
    if len(styles) > 1:
        findings.append(_f("scene_break_mix", "minor", "book", None,
                           f"scene-break styles across the book: "
                           f"{', '.join(repr(s) for s in sorted(styles))}"))
    return _report("book", ctx, findings, stats, [_rel(u.path, root) for u in units])


def _report(mode: str, ctx: Context, findings: list[dict], stats: dict, files: list[str]) -> dict:
    findings.sort(key=lambda f: (str(f["unit"]), f["line"] or 0, f["rule"], f["detail"]))
    counts = Counter(f["severity"] for f in findings)
    notes = []
    if ctx.lex.get("_language") != ctx.lex.get("_requested"):
        notes.append(f"no lexicon pack for '{ctx.lex.get('_requested')}' — English lists used")
    if not ctx.cast:
        notes.append("no character sheets in bible/characters/ — every name reads as unknown")
    return {
        "mode": mode,
        "language": ctx.variant,
        "pack": ctx.lex.get("_language"),
        "files": files,
        "findings": findings,
        "stats": {"units": stats, "severity": dict(counts)},
        "notes": notes,
    }


def _rel(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Mechanical fiction lint: tics, names, dialogue form.")
    ap.add_argument("--root", default=None,
                    help="Project root (default: nearest ancestor with bible/meta.yaml).")
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--unit", help="Lint one unit (default text: newest draft artifact).")
    mode.add_argument("--book", action="store_true", help="Lint every approved unit.")
    ap.add_argument("--file", help="With --unit: the file to lint.")
    ap.add_argument("--units", action="append", help="With --book: unit glob, repeatable.")
    ap.add_argument("--json", metavar="OUT", help="Write findings as JSON.")
    ap.add_argument("--fail-on", choices=("major", "minor", "never"), default="never",
                    help="Exit 1 when a finding at or above this severity exists.")
    ap.add_argument("--quiet", action="store_true", help="Only the summary line.")
    args = ap.parse_args(argv)

    root = L.find_root(args.root)
    try:
        if args.unit:
            unit = L.unit_id(args.unit) or args.unit
            f = L.at_root(root, args.file)
            report = lint_unit(root, unit, f)
        else:
            report = lint_book(root, args.units)
    except FileNotFoundError as exc:
        print(f"[lint_fiction] input missing: {exc}", file=sys.stderr)
        return 2

    fs = report["findings"]
    sev = report["stats"]["severity"]
    print(f"[lint_fiction] {report['mode']} · {len(report['files'])} file(s) · "
          f"{sev.get('major', 0)} major, {sev.get('minor', 0)} minor, {sev.get('info', 0)} info")
    if not args.quiet:
        for f in fs:
            if f["severity"] == "info":
                continue
            loc = f"{f['unit']}:{f['line']}" if f["line"] else f["unit"]
            print(f"  [{f['severity']:5}] {f['rule']:20} {loc:12} {f['detail']}")
        for n in report["notes"]:
            print(f"  note: {n}")
    if args.json:
        out = L.write_json(L.at_root(root, args.json), report)
        print(f"[lint_fiction] findings → {out}")
    if args.fail_on != "never":
        floor = SEVERITY_RANK[args.fail_on]
        if any(SEVERITY_RANK[f["severity"]] >= floor for f in fs):
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
