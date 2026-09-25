#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_identifiers.py — every function the book calls must exist in its sources.

Why this exists. A technical book shipped a chapter built around `GroupConcat()`,
a function that does not exist. The Critic certified it as real; the Reader-POV
praised the line. Both judged from memory, and a model's memory is exactly where
an invented API lives. `tech_a-4` ("no invented APIs") was a judgment call; it is
now a lookup against an index built from `bible/sources/`.

Two modes.

  --build-index   Writes `bible/identifier-index.txt` from `bible/sources/**/*.md`:
                  call patterns `Name(`, backticked identifiers, and every
                  identifier inside the sources' code blocks. Everything after a
                  line `# allow` is written by hand and survives rebuilds.

  check           `--unit unit-NN [--file F]` or `--units GLOB`. Candidates are
                  calls (`Name(` in code and in backticks) and API-looking
                  backticked tokens (dotted, snake_case, camelCase, `Name()`,
                  ALLCAPS). Known = index ∪ glossary terms ∪
                  `meta.validation_surface.identifier_allowlist` ∪ keywords of
                  `conventions.code_language` and of each fence's language ∪
                  what the checked text defines itself (`AS Alias`, table labels,
                  `def`/`function`/`let`/`SET` names, assignments). Field and
                  variable names used bare in the text's own code are known for
                  backtick mentions — the book's data model is the author's — but
                  never make a CALL known: an invented function is the defect.

Comparison is case-insensitive by default (`--case-sensitive` to change it).

Usage
  python scripts/check_identifiers.py --build-index
  python scripts/check_identifiers.py --unit unit-11
  python scripts/check_identifiers.py --units "final/unit-*.md" --json ids.json
  python scripts/check_identifiers.py --unit unit-11 --fail-on-unknown

Exit codes: 0 (unknowns are data) unless --fail-on-unknown and any unknown → 1;
2 on a usage error or missing input.
"""

from __future__ import annotations

import argparse
import builtins
import glob as _glob
import keyword
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from bookkit import lexicon as L  # noqa: E402

INDEX_REL = "bible/identifier-index.txt"
ALLOW_MARK = "# allow"

IDENT = r"[A-Za-z_$@#][A-Za-z0-9_$@#]*"
CALL_RE = re.compile(r"(?<![\w.$@#])(" + IDENT + r"(?:\." + IDENT + r")*)\s*\(")
CALL_TIGHT_RE = re.compile(r"(?<![\w.$@#])(" + IDENT + r"(?:\." + IDENT + r")*)\(")
IDENT_RE = re.compile(IDENT)
BACKTICK_RE = re.compile(r"`([^`\n]+)`")
FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})\s*([\w+#-]*)")
FILE_LIKE = re.compile(r"^[\w./-]+\.(?:md|txt|csv|qvd|qvf|json|ya?ml|py|js|ts|html?|xml|"
                       r"pdf|png|jpe?g|svg|log|sql|sh|toml|ini|cfg|xlsx?)$", re.I)
PLURAL_PAREN = re.compile(r"^\((?:s|es|as|os|a|o|n|en)\)")
DEFINE_RES = [
    re.compile(r"\bAS\s+\[?(" + IDENT + r")", re.I),
    re.compile(r"^\s*\[?(" + IDENT + r")\]?\s*:\s*$"),
    re.compile(r"\b(?:def|function|class|let|const|var|sub|SET|LET|macro|func|fn|"
               r"procedure|interface|type|struct|enum)\s+(" + IDENT + r")", re.I),
    re.compile(r"^\s*(" + IDENT + r")\s*(?::[^=]+)?=(?!=)"),
    re.compile(r"\bfor\s+(" + IDENT + r")\s+in\b"),
]

_JS = set("""
break case catch class const continue debugger default delete do else export
extends finally for function if import in instanceof new return super switch this
throw try typeof var void while with yield let static await async of null true false
undefined NaN Infinity console JSON Math Object Array String Number Boolean Promise
Date RegExp Error Map Set Symbol parseInt parseFloat isNaN require module exports
window document fetch setTimeout setInterval clearTimeout
""".split())
_SQL = set("""
select from where group by order having join inner left right outer full cross on
as and or not in is null like between exists union all distinct insert into values
update set delete create table view index drop alter add primary key foreign
references case when then else end with limit offset count sum avg min max coalesce
cast convert substring trim upper lower length round abs now current_date
current_timestamp over partition row_number rank dense_rank lag lead nullif ifnull
""".split())
_BASH = set("""
if then else elif fi for while do done case esac function in echo printf cd ls pwd
export source read local return exit set unset shift test true false cat grep sed
awk cut sort uniq head tail mkdir rm cp mv chmod chown find xargs curl wget tar git
""".split())
KEYWORDS = {
    "python": set(keyword.kwlist) | set(dir(builtins)) | {"self", "cls"},
    "javascript": _JS,
    "typescript": _JS | {"interface", "type", "enum", "implements", "readonly",
                         "string", "number", "boolean", "any", "unknown", "never"},
    "sql": _SQL,
    "bash": _BASH,
}
LANG_ALIASES = {"py": "python", "python3": "python", "js": "javascript", "node": "javascript",
                "jsx": "javascript", "ts": "typescript", "tsx": "typescript", "sh": "bash",
                "shell": "bash", "zsh": "bash", "console": "bash", "postgresql": "sql",
                "postgres": "sql", "mysql": "sql", "sqlite": "sql", "tsql": "sql",
                "plsql": "sql"}
GENERIC = {"if", "else", "for", "while", "return", "and", "or", "not", "in", "is"}


# ---------------------------------------------------------------------------
# Scanning
# ---------------------------------------------------------------------------


def _norm(name: str, case_sensitive: bool) -> str:
    return name if case_sensitive else name.casefold()


def _lang(tag: str) -> str:
    t = (tag or "").strip().lower()
    return LANG_ALIASES.get(t, t)


def _scan(text: str):
    """Yield (line_no, in_code, fence_lang, line_text) for a markdown text."""
    in_code, fence, lang = False, "", ""
    for n, raw in enumerate(L.strip_comments(text).splitlines(), start=1):
        m = FENCE_RE.match(raw)
        if m and (not in_code or (m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence))):
            if not in_code:
                in_code, fence, lang = True, m.group(1), _lang(m.group(2))
            else:
                in_code, fence, lang = False, "", ""
            continue
        yield n, in_code, lang, raw


def _api_like(tok: str) -> bool:
    if FILE_LIKE.match(tok):
        return False
    core = tok[:-2] if tok.endswith("()") else tok
    if not re.fullmatch(IDENT + r"(?:\." + IDENT + r")*", core):
        return False
    return (tok.endswith("()") or "." in core or "_" in core.strip("_")
            or bool(re.search(r"[a-z][A-Z]", core))
            or sum(1 for c in core if c.isupper()) >= 2 and not core.isupper()
            or (core.isupper() and len(core) >= 3))


def index_terms(text: str) -> set[str]:
    """Identifiers a source file vouches for."""
    out: set[str] = set()
    for _n, in_code, _lang_, line in _scan(text):
        if in_code:
            out.update(IDENT_RE.findall(line))
            continue
        for m in CALL_RE.finditer(line):
            out.add(m.group(1))
            out.update(m.group(1).split("."))
        for span in BACKTICK_RE.findall(line):
            out.update(IDENT_RE.findall(span))
            for m in CALL_RE.finditer(span):
                out.add(m.group(1))
    return {t for t in out if t}


def candidates(text: str):
    """Yield (identifier, line, in_code, is_call, fence_lang) from a checked text."""
    for n, in_code, lang, line in _scan(text):
        if in_code:
            for m in CALL_TIGHT_RE.finditer(line):
                yield m.group(1), n, True, True, lang
            continue
        spans = BACKTICK_RE.findall(line)
        for span in spans:
            calls = list(CALL_TIGHT_RE.finditer(span))
            for m in calls:
                yield m.group(1), n, False, True, ""
            tok = span.strip()
            if not calls and _api_like(tok):
                yield tok[:-2] if tok.endswith("()") else tok, n, False, tok.endswith("()"), ""
        bare = BACKTICK_RE.sub(" ", line)
        for m in CALL_TIGHT_RE.finditer(bare):
            name = m.group(1)
            rest = bare[m.end() - 1:]
            if PLURAL_PAREN.match(rest) or not re.fullmatch(r"[A-Za-z0-9_.]+", name):
                continue
            if "." in name or "_" in name or re.search(r"[a-z][A-Z]|^[A-Z]", name):
                yield name, n, False, True, ""


def definitions(text: str) -> tuple[set[str], set[str], set[str]]:
    """(defined names, bare code identifiers, fence languages) of a checked text."""
    defined, bare, langs = set(), set(), set()
    for _n, in_code, lang, line in _scan(text):
        if not in_code:
            continue
        if lang:
            langs.add(lang)
        for rx in DEFINE_RES:
            defined.update(m.group(1) for m in rx.finditer(line))
        called = {m.group(1) for m in CALL_TIGHT_RE.finditer(line)}
        stripped = re.sub(r"'[^']*'|\"[^\"]*\"", " ", line)
        bare.update(t for t in IDENT_RE.findall(stripped) if t not in called)
    return defined, bare, langs


# ---------------------------------------------------------------------------
# Index
# ---------------------------------------------------------------------------


def source_files(root: Path) -> list[Path]:
    base = root / "bible" / "sources"
    return sorted(p for p in base.rglob("*.md") if p.is_file()) if base.is_dir() else []


def build_index_terms(root: Path) -> tuple[set[str], int]:
    terms: set[str] = set()
    files = source_files(root)
    for p in files:
        terms |= index_terms(L.read_text(p))
    return terms, len(files)


def read_index(path: Path) -> tuple[set[str], list[str]]:
    """(generated + allowed identifiers, hand-written allow lines)."""
    if not path.exists():
        return set(), []
    terms, allow, in_allow = set(), [], False
    for line in L.read_text(path).splitlines():
        s = line.strip()
        if s.lower() == ALLOW_MARK:
            in_allow = True
            continue
        if in_allow:
            allow.append(line)
        if not s or s.startswith("#"):
            continue
        terms.add(s.split()[0])
    return terms, allow


def write_index(root: Path) -> tuple[Path, int, int]:
    path = root / INDEX_REL
    _old, allow = read_index(path)
    terms, nfiles = build_index_terms(root)
    lines = [
        "# identifier-index.txt — generated by scripts/check_identifiers.py --build-index",
        f"# from bible/sources/ ({nfiles} file(s), {len(terms)} identifiers).",
        "# Everything above the '# allow' line is regenerated. Add hand-approved",
        "# identifiers (one per line, optional comment after a space) below it.",
        "",
        *sorted(terms, key=lambda t: (t.casefold(), t)),
        "",
        ALLOW_MARK,
        *allow,
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines).rstrip("\n") + "\n")
    return path, len(terms), nfiles


def glossary_terms(root: Path) -> set[str]:
    path = root / "bible" / "glossary.md"
    if not path.exists():
        return set()
    out: set[str] = set()
    for line in L.read_text(path).splitlines():
        if re.match(r"^#{2,4}\s", line) or re.match(r"^\s*[-*]\s+\*\*", line):
            out.update(IDENT_RE.findall(re.sub(r"[*`#]", " ", line)))
        for span in BACKTICK_RE.findall(line):
            out.update(IDENT_RE.findall(span))
    return out


# ---------------------------------------------------------------------------


def unit_file(root: Path, unit: str) -> Path | None:
    for rel in (f"drafts/{unit}/humanized.md", f"drafts/{unit}/edit.md",
                f"drafts/{unit}/draft.md", f"final/{unit}.md"):
        if (root / rel).exists():
            return root / rel
    return None


def check(root: Path, files: list[Path], *, case_sensitive: bool = False,
          meta: dict | None = None) -> dict:
    meta = meta if meta is not None else L.load_meta(root)
    notes: list[str] = []
    index_path = root / INDEX_REL
    index, _allow = read_index(index_path)
    state = "file"
    if not index_path.exists():
        index, nfiles = build_index_terms(root)
        state = "built-on-the-fly" if nfiles else "none"
        notes.append("no bible/identifier-index.txt — " + (
            f"built in memory from {nfiles} source file(s); run --build-index to persist"
            if nfiles else "no bible/sources/ either: every identifier below is unverifiable"))

    allow = L.meta_get(meta, "validation_surface.identifier_allowlist") or []
    code_lang = _lang(str(L.meta_get(meta, "conventions.code_language") or ""))
    n = lambda s: _norm(s, case_sensitive)  # noqa: E731

    texts = {p: L.read_text(p) for p in files}
    defined, bare, langs = set(), set(), set()
    for text in texts.values():
        d, b, lg = definitions(text)
        defined |= d
        bare |= b
        langs |= lg
    kw: set[str] = set(GENERIC)
    for lang in {code_lang, *langs}:
        kw |= KEYWORDS.get(lang, set())
    known = {n(t) for t in index | glossary_terms(root) | {str(a) for a in allow} | kw | defined}
    known_bare = {n(t) for t in bare}

    found: dict[str, dict] = {}
    checked: set[str] = set()
    for path, text in texts.items():
        rel = _rel(path, root)
        for name, line, in_code, is_call, _lang_ in candidates(text):
            checked.add(n(name))
            last = name.split(".")[-1]
            if n(name) in known or n(last) in known:
                continue
            if not is_call and (n(name) in known_bare or n(last) in known_bare):
                continue
            entry = found.setdefault(n(name), {"identifier": name, "locations": [],
                                               "in_code": False, "call": False})
            loc = f"{rel}:{line}"
            if loc not in entry["locations"]:
                entry["locations"].append(loc)
            entry["in_code"] = entry["in_code"] or in_code
            entry["call"] = entry["call"] or is_call

    return {
        "unknown": sorted(found.values(), key=lambda e: e["identifier"].casefold()),
        "index_size": len(index),
        "index": INDEX_REL,
        "index_state": state,
        "checked": len(checked),
        "files": [_rel(p, root) for p in files],
        "notes": notes,
    }


def _rel(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Check that every identifier the text calls exists in bible/sources/.")
    ap.add_argument("--root", default=None,
                    help="Project root (default: nearest ancestor with bible/meta.yaml).")
    ap.add_argument("--build-index", action="store_true",
                    help="(Re)write bible/identifier-index.txt from bible/sources/.")
    ap.add_argument("--unit", help="Unit id, e.g. unit-11.")
    ap.add_argument("--file", help="File to check for --unit (default: newest draft "
                                   "artifact, then final/<unit>.md).")
    ap.add_argument("--units", action="append",
                    help="Glob of files to check, repeatable (e.g. 'final/unit-*.md').")
    ap.add_argument("--json", metavar="OUT", help="Write the result as JSON.")
    ap.add_argument("--fail-on-unknown", action="store_true",
                    help="Exit 1 when any identifier is unknown.")
    ap.add_argument("--case-sensitive", action="store_true",
                    help="Compare identifiers case-sensitively.")
    args = ap.parse_args(argv)

    root = L.find_root(args.root)
    if args.build_index:
        path, count, nfiles = write_index(root)
        print(f"[check_identifiers] index → {_rel(path, root)}: {count} identifiers "
              f"from {nfiles} source file(s)")
        if not (args.unit or args.units):
            return 0

    files: list[Path] = []
    if args.unit:
        unit = L.unit_id(args.unit) or args.unit
        f = L.at_root(root, args.file) if args.file else unit_file(root, unit)
        if f is None or not f.exists():
            print(f"[check_identifiers] no file for {unit}", file=sys.stderr)
            return 2
        files.append(f)
    for pattern in args.units or []:
        pat = str(L.at_root(root, pattern))
        files += sorted(Path(m) for m in _glob.glob(pat) if Path(m).is_file())
    if not files:
        ap.error("give --build-index, --unit or --units")

    result = check(root, files, case_sensitive=args.case_sensitive)
    unknown = result["unknown"]
    print(f"[check_identifiers] {result['checked']} identifier(s) checked against "
          f"{result['index_size']} indexed ({result['index_state']}); "
          f"{len(unknown)} unknown")
    for e in unknown:
        kind = "call" if e["call"] else "mention"
        where = "code" if e["in_code"] else "prose"
        print(f"  UNKNOWN {e['identifier']!r} ({kind}, {where}) at {', '.join(e['locations'])}")
    for note in result["notes"]:
        print(f"  note: {note}")
    if args.json:
        out = L.write_json(L.at_root(root, args.json), result)
        print(f"[check_identifiers] result → {out}")
    return 1 if (args.fail_on_unknown and unknown) else 0


if __name__ == "__main__":
    sys.exit(main())
