"""lexicon — the language layer: per-language lists, and the prose conventions
every language-aware check must agree on.

Every language-dependent list the checks use lives in one YAML file per language
(`lexicons/en.yaml`, `lexicons/es.yaml`, ...), not inside the scripts. Two
reasons. A Critic that invents "target-language equivalents" on every run
produces a different count every run, and a script that hardcodes English lists
silently reports "zero hits" on a Spanish book — which reads as clean.

A project may extend or override a language pack with `bible/lexicon.yaml`
(same keys; lists are appended, scalars replaced, mappings merged). That file is
where a book's own tics go once somebody has spotted them.

Pack convention: every list entry is a Python regular-expression fragment,
matched case-insensitively and word-bounded (`compile_any(..., regex=True)`).
Plain words are valid fragments. Plain-word lists (no regex): `stopwords`,
`name_exclusions`, `non_person_names`, `institution_heads`, `name_connectors`,
`locative_prepositions`, `indefinite_articles`, `object_markers`,
`common_words` (the language's most frequent word forms, folded — the R4 name
detector's "is this an ordinary word?"). `initial_verb_forms` entries match a
whole token. `gestures` is a mapping
`label: pattern` so a count can say "asentir ×7" instead of quoting a regex.
`attribute_terms.<attr>` entries carry a named group `value`.

The second half of this module is the prose layer shared by `count_rhet`,
`lint_fiction`, `check_story` and `check_role_diff`: what counts as dialogue
(the raya line, quoted speech), where a sentence ends (¿…? and ¡…! included),
what a word is. Those are language conventions, and the checks have to agree on
them — a rhetoric count that treats a dialogue raya as an em-dash, next to a
fiction lint that does not, produces two numbers for one text.

Usage
    from bookkit.lexicon import load, compile_any
    lex = load("es-AR", project_root)          # variant → base language
    rx = compile_any(lex.get("danger", []), regex=True)
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

try:
    import yaml
except ImportError:  # pragma: no cover — every script checks this first
    yaml = None

LEXICON_DIR = Path(__file__).resolve().parent.parent / "lexicons"
DEFAULT_LANG = "en"


# ---------------------------------------------------------------------------
# Packs
# ---------------------------------------------------------------------------


def base_language(variant: str | None) -> str:
    """`es-AR` → `es`; empty or unknown → `en`."""
    if not variant:
        return DEFAULT_LANG
    return str(variant).strip().lower().replace("_", "-").split("-")[0] or DEFAULT_LANG


def available() -> list[str]:
    return sorted(p.stem for p in LEXICON_DIR.glob("*.yaml"))


def _read(path: Path) -> dict[str, Any]:
    if yaml is None or not path.exists():
        return {}
    data = yaml.safe_load(read_text(path)) or {}
    return data if isinstance(data, dict) else {}


def _merge(base: dict[str, Any], extra: dict[str, Any]) -> dict[str, Any]:
    out = dict(base)
    for key, value in extra.items():
        if isinstance(value, list) and isinstance(out.get(key), list):
            out[key] = list(out[key]) + [v for v in value if v not in out[key]]
        elif isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _merge(out[key], value)
        else:
            out[key] = value
    return out


def load(variant: str | None, project_root: Path | None = None) -> dict[str, Any]:
    """Language pack for `variant`, falling back to English for unknown languages.

    The fallback is announced by `lex["_language"]` differing from the requested
    base language, so a caller can report "no pack for xx — counts are English
    only" instead of printing a clean-looking zero.
    """
    lang = base_language(variant)
    path = LEXICON_DIR / f"{lang}.yaml"
    if not path.exists():
        lang = DEFAULT_LANG
        path = LEXICON_DIR / f"{DEFAULT_LANG}.yaml"
    lex = _read(path)
    if project_root is not None:
        lex = _merge(lex, _read(Path(project_root) / "bible" / "lexicon.yaml"))
    lex["_language"] = lang
    lex["_requested"] = base_language(variant)
    return lex


def compile_any(items: list[str], *, regex: bool = False, flags: int = re.I) -> re.Pattern | None:
    """One word-bounded alternation over `items`.

    Plain entries are escaped; set `regex=True` for lists whose entries are
    already patterns (e.g. `not_x_but_y`). Returns None for an empty list, so
    callers can tell "no pack entries" from "no hits".
    """
    items = [i for i in items or [] if isinstance(i, str) and i.strip()]
    if not items:
        return None
    parts = items if regex else [re.escape(i) for i in items]
    return re.compile(r"(?<!\w)(?:" + "|".join(parts) + r")(?!\w)", flags)


def compile_labeled(entries: Any, flags: int = re.I) -> list[tuple[str, re.Pattern]]:
    """`[(label, pattern)]` from a `label: regex` mapping or a plain list.

    Kept separate from `compile_any` because a count per family ("asentir ×7")
    needs one pattern per label, and patterns with named groups cannot be joined
    into one alternation.
    """
    pairs: list[tuple[str, str]] = []
    if isinstance(entries, dict):
        for label, pat in entries.items():
            for p in (pat if isinstance(pat, list) else [pat]):
                if isinstance(p, str) and p.strip():
                    pairs.append((str(label), p))
    elif isinstance(entries, list):
        pairs = [(p, p) for p in entries if isinstance(p, str) and p.strip()]
    return [(label, re.compile(r"(?<!\w)(?:" + p + r")(?!\w)", flags)) for label, p in pairs]


def plain_set(entries: Any) -> set[str]:
    """A plain-word list as a folded set (`stopwords`, `name_exclusions`)."""
    return {fold(str(e)) for e in entries or [] if str(e).strip()}


# ---------------------------------------------------------------------------
# Text and project access (tolerant — a check must not die on a BOM)
# ---------------------------------------------------------------------------

try:  # the toolkit's one reader, when present: records cp1252 files centrally
    from .textio import read_text as _toolkit_read_text  # type: ignore
except Exception:  # pragma: no cover — older bookkit
    _toolkit_read_text = None


def read_text(path: str | Path) -> str:
    """UTF-8 with or without BOM, NFC; a cp1252 file is decoded, not fatal."""
    if _toolkit_read_text is not None:
        return _toolkit_read_text(path)
    raw = Path(path).read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        raw = raw[3:]
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("cp1252", errors="replace")
    return unicodedata.normalize("NFC", text)


def find_root(root: str | Path | None) -> Path:
    """`--root`, else the nearest ancestor of cwd holding `bible/meta.yaml`."""
    if root:
        p = Path(root).expanduser().resolve()
        if not p.exists():
            raise SystemExit(f"Root does not exist: {p}")
        return p
    here = Path.cwd().resolve()
    for cand in [here, *here.parents]:
        if (cand / "bible" / "meta.yaml").exists():
            return cand
    return here


def at_root(root: Path, path: str | Path | None) -> Path | None:
    """A CLI path: absolute as given, relative → under the project root. Every
    new script resolves `--file`, `--json`, `--units` and friends this way, so a
    run from another directory with `--root` reads and writes the same files."""
    if path is None or str(path) == "":
        return None
    p = Path(path)
    return p if p.is_absolute() else Path(root) / p


def read_yaml(path: str | Path) -> Any:
    """Parsed YAML, None when the file is absent. Raises ValueError on bad YAML."""
    p = Path(path)
    if not p.exists():
        return None
    if yaml is None:  # pragma: no cover
        raise SystemExit("Missing PyYAML. Install with: pip install pyyaml")
    try:
        return yaml.safe_load(read_text(p))
    except yaml.YAMLError as exc:
        raise ValueError(f"{p.name}: invalid YAML — {exc}") from exc


def load_meta(root: Path) -> dict:
    try:
        data = read_yaml(Path(root) / "bible" / "meta.yaml")
    except ValueError as exc:
        raise SystemExit(f"bible/meta.yaml is not valid YAML: {exc}")
    return data if isinstance(data, dict) else {}


def meta_get(meta: dict, dotted: str, default=None):
    node: Any = meta
    for part in dotted.split("."):
        if not isinstance(node, dict) or part not in node:
            return default
        node = node[part]
    return node


PROFILES = ("book-technical", "book-literary", "corporate-guide", "product-docs",
            "scientific-paper")
SCHEMA_VERSION = "3.4"


def profile_of(meta: dict) -> str:
    """`project.profile`, normalized (stripped, lowercase): `Book-Literary ` is
    the literary profile, not an unknown one that silently skips R1–R4."""
    return str(meta_get(meta, "project.profile", "") or "").strip().lower()


def profile_problem(meta: dict) -> str:
    """'' when `project.profile` names a known profile, else what is wrong. A
    missing or misspelled profile must stop the scripts (exit 2): read as
    "nonfiction", it switched the literary rules off."""
    raw = meta_get(meta, "project.profile")
    p = profile_of(meta)
    if not p:
        return ("bible/meta.yaml has no project.profile — set one of: " + ", ".join(PROFILES))
    if p not in PROFILES:
        return (f"bible/meta.yaml project.profile {raw!r} is not a known profile — use one of: "
                + ", ".join(PROFILES))
    return ""


def schema_problem(meta: dict) -> str:
    """'' when `schema_version` is the current one ("3.4")."""
    schema = str(meta.get("schema_version") or "").strip()
    if schema != SCHEMA_VERSION:
        return (f"bible/meta.yaml schema_version is {schema or '(none)'!r}, not "
                f"{SCHEMA_VERSION!r}: an earlier version of the skill built this project. Offer "
                "a fresh scaffold and manual carry-over (references/init-scaffold.md); there is "
                "no migration.")
    return ""


def resolve_variant(meta: dict) -> str:
    """`project.language_variant` → `conventions.language_variant` →
    `project.language` → `en` (design contract §3)."""
    for key in ("project.language_variant", "conventions.language_variant",
                "project.language"):
        val = meta_get(meta, key)
        if val and str(val).strip() and not str(val).strip().startswith("["):
            return str(val).strip()
    return DEFAULT_LANG


_FM_RE = re.compile(r"\A---[ \t]*\n(.*?)\n(?:---|\.\.\.)[ \t]*(?:\n|\Z)", re.S)


def front_matter(text: str) -> tuple[dict | None, str, str | None]:
    """(data, body, error). `data` is None when the file has no front matter."""
    m = _FM_RE.match(text)
    if not m:
        return None, text, None
    try:
        data = yaml.safe_load(m.group(1)) if yaml else None
    except yaml.YAMLError as exc:  # type: ignore[union-attr]
        return None, text[m.end():], f"invalid YAML front matter — {exc}"
    return (data if isinstance(data, dict) else {}), text[m.end():], None


def unit_num(value: Any) -> int | None:
    """`unit-05`, `ch-5`, `05`, 5 → 5. PyYAML reads `unit: 05` as 5, `08` as '08'."""
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return value
    m = re.search(r"(\d+)", str(value))
    return int(m.group(1)) if m else None


def unit_id(value: Any) -> str | None:
    n = unit_num(value)
    return None if n is None else f"unit-{n:02d}"


def write_json(path: str | Path, data: Any) -> Path:
    """UTF-8, `ensure_ascii=False`, sorted keys, LF — the contract for every output."""
    import json
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(data, fh, ensure_ascii=False, sort_keys=True, indent=2)
        fh.write("\n")
    return p


# ---------------------------------------------------------------------------
# Prose primitives
# ---------------------------------------------------------------------------

WORD_RE = re.compile(r"[^\W\d_]+(?:['’][^\W\d_]+)*|\d+(?:[.,]\d+)*")
RAYA = "—"
# A dialogue line opens with a raya. Hyphen / en-dash openers are malformed
# dialogue in a raya language; they count as dialogue for exclusion purposes so
# a botched line is not scored as narration, and lint_fiction reports them.
_DIALOGUE_OPEN = re.compile(r"^\s*(?:>\s*)?(?:—|–\s?(?=\S)|-\s?(?=[¿¡«\"“]?[^\W\d_]))")
_QUOTE_OPEN = re.compile(r"^\s*(?:>\s*)?[\"“«]")
_QUOTED = re.compile(r"“[^”\n]*”|«[^»\n]*»|\"[^\"\n]{1,600}\"")
_COMMENT = re.compile(r"<!--.*?-->", re.S)
_ABBREV = {
    "sr", "sra", "srta", "dr", "dra", "lic", "ing", "prof", "etc", "ej", "vs",
    "mr", "mrs", "ms", "st", "jr", "no", "nº", "núm", "pág", "cap", "fig", "art",
    "av", "bv", "gral", "cnel", "ud", "uds", "e.g", "i.e", "p. ej", "aprox",
}
_SENT_BREAK = re.compile(r"([.!?…]+[\"'”’»)\]]*)(\s+)(?=[¿¡—–«\"“(\[]*\s?[^\W\d_\s]|\d)")


def fold(text: str) -> str:
    """Lowercase, accents stripped (ñ kept): `Tomás` and `Tomas` fold together."""
    out = []
    for ch in unicodedata.normalize("NFD", str(text).lower()):
        if unicodedata.category(ch) == "Mn" and ch != "̃":
            continue
        out.append(ch)
    return unicodedata.normalize("NFC", "".join(out))


def words(text: str) -> list[str]:
    return WORD_RE.findall(text)


def strip_comments(text: str) -> str:
    """HTML comments out, line count preserved (multi-line comments keep their newlines)."""
    return _COMMENT.sub(lambda m: "\n" * m.group(0).count("\n"), text)


def is_dialogue_line(text: str, *, literary: bool = True) -> bool:
    """Raya-initial always; hyphen/en-dash-initial only in fiction (else it is a list)."""
    if text.lstrip().startswith(RAYA):
        return True
    if literary and _DIALOGUE_OPEN.match(text):
        return True
    return bool(literary and _QUOTE_OPEN.match(text))


def split_raya(text: str) -> tuple[list[str], list[str]]:
    """(speech parts, narrator incisos) of a raya line.

    `—Hola —dijo Mariana—. ¿Venís?` → (["Hola ", ". ¿Venís?"], ["dijo Mariana"]).
    After the opening raya the text alternates speech / inciso at every raya.
    """
    body = re.sub(r"^\s*(?:>\s*)?[—–-]\s?", "", text, count=1)
    parts = body.split(RAYA)
    speech = [p for i, p in enumerate(parts) if i % 2 == 0]
    narr = [p for i, p in enumerate(parts) if i % 2 == 1]
    return speech, narr


def strip_quoted(text: str) -> str:
    return _QUOTED.sub(" ", text)


def quoted_spans(text: str) -> list[str]:
    return [m.group(0) for m in _QUOTED.finditer(text)]


def split_sentences(text: str) -> list[str]:
    """Sentences of one paragraph. `¿…?` and `¡…!` close sentences; a raya after
    the break opens the next one; common abbreviations do not break."""
    out: list[str] = []
    start = 0
    for m in _SENT_BREAK.finditer(text):
        end = m.end(1)
        before = text[start:m.start(1)]
        last = before.split()[-1].lower().strip("(¿¡\"“«") if before.split() else ""
        if m.group(1).startswith(".") and len(m.group(1)) == 1 and (
                last in _ABBREV or (len(last) == 1 and last.isalpha())):
            continue
        piece = text[start:end].strip()
        if piece:
            out.append(piece)
        start = m.end()
    tail = text[start:].strip()
    if tail:
        out.append(tail)
    return out


@dataclass
class ProseLine:
    """One prose line with dialogue separated from narration.

    `narration` is what a rhetoric count reads (dialogue speech removed, incisos
    kept — an inciso is the narrator's voice); `speech` is what a dialogue ratio
    reads; `text` keeps everything, for name and tic detection.
    """
    line: int
    kind: str
    text: str
    dialogue: bool = False
    narration: str = ""
    speech: list[str] = field(default_factory=list)
    heading_path: str = ""


def prose_lines(path: str | Path, *, literary: bool, rel_to: Path | None = None
                ) -> tuple[list[ProseLine], list[tuple[int, str]], list[tuple[int, str]]]:
    """(prose lines, headings, scene-break lines) of a markdown file.

    Code fences, tables and HTML comments are excluded. Uses bookkit's segmenter,
    so a fence here is a fence everywhere else in the toolkit.
    """
    from .segment import segment_text  # local: keeps `lexicon` importable alone
    text = strip_comments(read_text(path))
    records = segment_text(text, unit=Path(path).stem, path=Path(path).name)
    out: list[ProseLine] = []
    heads: list[tuple[int, str]] = []
    breaks: list[tuple[int, str]] = []
    for r in records:
        t = r.text
        if r.kind == "code" or r.kind == "blank" or r.kind == "table":
            continue
        if r.kind == "heading":
            heads.append((r.line, t.lstrip("#").strip()))
            continue
        if r.kind == "hr" or _is_scene_break(t):
            breaks.append((r.line, t.strip()))
            continue
        if not t.strip():
            continue
        body = re.sub(r"^\s*>\s?", "", t) if r.kind == "quote" else t
        out.append(make_prose_line(r.line, r.kind, body, literary, r.heading_path))
    return out, heads, breaks


def make_prose_line(line: int, kind: str, body: str, literary: bool,
                    heading_path: str = "") -> ProseLine:
    """One ProseLine from a text: dialogue split from narration (raya or quotes)."""
    pl = ProseLine(line=line, kind=kind, text=body, heading_path=heading_path)
    if literary and is_dialogue_line(body, literary=True) and not _QUOTE_OPEN.match(body):
        speech, narr = split_raya(body)
        pl.dialogue = True
        pl.speech = speech + quoted_spans(" ".join(narr))
        pl.narration = strip_quoted(" ".join(n.strip() for n in narr))
    else:
        pl.speech = quoted_spans(body)
        pl.dialogue = bool(literary and _QUOTE_OPEN.match(body))
        pl.narration = strip_quoted(body)
    return pl


def table_lines(path: str | Path, *, literary: bool = True) -> list[ProseLine]:
    """Every cell of every table row as its own ProseLine (separator rows
    skipped). Names hide in tables too; tics and rhetoric counts do not read
    these."""
    from .segment import segment_text
    text = strip_comments(read_text(path))
    out: list[ProseLine] = []
    for r in segment_text(text, unit=Path(path).stem, path=Path(path).name):
        if r.kind != "table":
            continue
        cells = [c.strip() for c in r.text.strip().strip("|").split("|")]
        if all(re.fullmatch(r":?-{2,}:?", c) or not c for c in cells):
            continue
        out += [make_prose_line(r.line, "table", c, literary, r.heading_path)
                for c in cells if c]
    return out


_SCENE_BREAK = re.compile(r"^\s*(?:[*•·~#⁂]\s*){1,5}$")


def _is_scene_break(text: str) -> bool:
    return bool(_SCENE_BREAK.match(text))


def iter_matches(rx: re.Pattern | None, text: str) -> Iterable[re.Match]:
    return rx.finditer(text) if rx is not None else ()
