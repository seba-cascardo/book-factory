#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""count_rhet.py — the rhetoric budget, counted by a script instead of felt by a model.

Why this exists. The rubric calls the `rhet` family "counted, not felt", and
until v3.4 the counting was done by the Critic, by hand, from English lists
"plus target-language equivalents". Every run invented its own Spanish
equivalents, so the same unit produced a different scorecard each time, and a
Spanish chapter could pass rhet-2 with three "No es X, es Y" in it because the
model did not recognise the shape. The Critic now copies these numbers from
`checks.json`; it never recounts (design contract §1.5).

What is counted, and over what:
  - Prose only: code fences, tables, HTML comments and headings are out
    (headings come back for rhet-7). Quoted spans are out (rubric rhet-1).
  - Literary: dialogue is out — raya lines and quoted speech — but the narrator's
    incisos stay (`—No —dijo, y no era miedo, era rabia—` counts the inciso).
    A dialogue raya is never an em-dash.
  - Literary gets only rhet-2 from the rhet family (rubric-literary), plus the
    diagnostics; nonfiction gets rhet-1/2/3/4/5/7. rhet-6 is a judgment about a
    declared opening and is not a count.

Lists come from `scripts/lexicons/<lang>.yaml` (+ `bible/lexicon.yaml`); quotas
from the rubric defaults, overridden by the ```yaml fence containing
`rhetoric_budget:` in `bible/voice-profile.md`:

    ```yaml
    rhetoric_budget:
      rhet-1: 1
      rhet-5: 12
    ```

Usage
  python scripts/count_rhet.py --unit unit-07
  python scripts/count_rhet.py --root BOOK --unit unit-07 --file drafts/unit-07/edit.md
  python scripts/count_rhet.py --unit unit-07 --json drafts/unit-07/rhet.json

Exit codes: 0 counted (over-quota items are data, not failure), 2 input missing.
"""

from __future__ import annotations

import argparse
import re
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from bookkit import lexicon as L  # noqa: E402

LITERARY = "book-literary"
DEFAULT_QUOTAS = {"rhet-1": 2, "rhet-2": 1, "rhet-3": 2, "rhet-5": 8}
NONFICTION_ITEMS = ("rhet-1", "rhet-2", "rhet-3", "rhet-4", "rhet-5", "rhet-7")
LITERARY_ITEMS = ("rhet-2",)
# rhet-4 has a quota of 0 only under these closing policies (voice-profile §4).
ZERO_TEASE_POLICIES = {"recap", "none", None}
EXERCISE_RE = re.compile(r"exercis|ejercici|pr[aá]ctica|quiz|self-check|autoevaluaci", re.I)
PAGE_WORDS = 250
FLAT_RUN_MIN = 4          # sentences in a row …
FLAT_RUN_SPREAD = 3       # … whose lengths differ by at most this many words
_BUDGET_FENCE = re.compile(r"```ya?ml[^\n]*\n(.*?)```", re.S)
_POLICY_RE = re.compile(r"^Policy:\s*(.+)$", re.I | re.M)
POLICIES = ("recap", "related-links", "none", "bridge-allowed")


# ---------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------


def load_budget(root: Path) -> tuple[dict[str, int | None], str | None]:
    """Quota overrides from `bible/voice-profile.md`. Returns (overrides, error)."""
    path = root / "bible" / "voice-profile.md"
    if not path.exists():
        return {}, None
    for block in _BUDGET_FENCE.findall(L.read_text(path)):
        if "rhetoric_budget" not in block:
            continue
        try:
            data = L.yaml.safe_load(block) or {}
        except Exception as exc:  # noqa: BLE001 — report, never crash on a doc typo
            return {}, f"voice-profile rhetoric_budget is not valid YAML: {exc}"
        raw = data.get("rhetoric_budget") if isinstance(data, dict) else None
        out: dict[str, int | None] = {}
        bad: list[str] = []
        for key, val in (raw or {}).items():
            if isinstance(val, dict):
                val = val.get("quota")
            if not re.fullmatch(r"rhet-\d+", str(key)):
                continue   # literary diagnostics (similes_per_1000, fragment_ratio, …): read by agents
            try:
                out[str(key)] = None if val is None else int(val)
            except (TypeError, ValueError):
                bad.append(f"{key}: {val!r}")
        return out, (f"voice-profile rhetoric_budget: not a number — {', '.join(bad)}"
                     if bad else None)
    return {}, None


def closing_policy(root: Path) -> str | None:
    """`Policy: **recap**` from voice-profile §4, or None when unset."""
    path = root / "bible" / "voice-profile.md"
    if not path.exists():
        return None
    m = _POLICY_RE.search(L.read_text(path))
    if not m or "[" in m.group(1) or "|" in m.group(1):   # the unfilled template line
        return None
    word = re.sub(r"[*`_]", "", m.group(1)).strip().split()
    val = word[0].lower().rstrip(".,;") if word else ""
    return val if val in POLICIES else None


def default_file(root: Path, unit: str) -> Path:
    return root / "drafts" / unit / "humanized.md"


# ---------------------------------------------------------------------------
# Shared sentence metrics (lint_fiction imports these: one definition of "flat")
# ---------------------------------------------------------------------------


def sentence_lengths(texts: list[str]) -> list[int]:
    """Word counts of every sentence in `texts`, in order."""
    out: list[int] = []
    for t in texts:
        for s in L.split_sentences(t):
            n = len(L.words(s))
            if n:
                out.append(n)
    return out


def runs(lengths: list[int], *, min_len: int, pred) -> list[tuple[int, int]]:
    """Maximal runs `(start, length)` of ≥ `min_len` consecutive sentences where
    `pred(window)` holds for the whole run."""
    found: list[tuple[int, int]] = []
    i = 0
    while i < len(lengths):
        j = i + 1
        while j < len(lengths) and pred(lengths[i:j + 1]):
            j += 1
        if j - i >= min_len and pred(lengths[i:j]):
            found.append((i, j - i))
            i = j
        else:
            i += 1
    return found


def flat(window: list[int]) -> bool:
    return max(window) - min(window) <= FLAT_RUN_SPREAD


def length_stats(lengths: list[int]) -> dict:
    if not lengths:
        return {"mean": 0.0, "sd": 0.0, "sentences": 0, "flat_runs": 0}
    return {
        "mean": round(statistics.fmean(lengths), 1),
        "sd": round(statistics.pstdev(lengths), 1),
        "sentences": len(lengths),
        "flat_runs": len(runs(lengths, min_len=FLAT_RUN_MIN, pred=flat)),
    }


# ---------------------------------------------------------------------------
# Counting
# ---------------------------------------------------------------------------


def _paragraphs(lines: list[L.ProseLine]) -> list[tuple[str, list[tuple[int, int]]]]:
    """Consecutive narration lines of one paragraph, joined, with offset→line map."""
    paras: list[tuple[str, list[tuple[int, int]]]] = []
    buf: list[L.ProseLine] = []

    def flush():
        if not buf:
            return
        text, offsets = "", []
        for pl in buf:
            offsets.append((len(text), pl.line))
            text += pl.narration.strip() + " "
        paras.append((text.strip(), offsets))
        buf.clear()

    prev = None
    for pl in lines:
        joinable = (prev is not None and pl.kind == "para" and prev.kind == "para"
                    and pl.line == prev.line + 1 and not pl.dialogue and not prev.dialogue)
        if not joinable:
            flush()
        buf.append(pl)
        prev = pl
    flush()
    return paras


def _line_at(offsets: list[tuple[int, int]], pos: int) -> int:
    line = offsets[0][1]
    for start, ln in offsets:
        if start <= pos:
            line = ln
    return line


def _snip(text: str, limit: int = 160) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return text if len(text) <= limit else text[:limit - 1] + "…"


def compute(root: Path, unit: str, file: Path | None = None,
            meta: dict | None = None) -> dict:
    """The count report for one unit, as a dict (the JSON contract)."""
    meta = meta if meta is not None else L.load_meta(root)
    profile = L.profile_of(meta)
    literary = profile == LITERARY
    variant = L.resolve_variant(meta)
    lex = L.load(variant, root)
    path = Path(file) if file else default_file(root, unit)
    if not path.is_absolute():
        path = root / path
    if not path.exists():
        raise FileNotFoundError(path)

    lines, heads, _breaks = L.prose_lines(path, literary=literary)
    overrides, budget_error = load_budget(root)
    quotas = dict(DEFAULT_QUOTAS)
    quotas.update({k: v for k, v in overrides.items() if k in quotas})

    total_words = sum(len(L.words(pl.text)) for pl in lines)
    narr_lines = [pl for pl in lines if pl.narration.strip()]
    notes: list[str] = []
    if lex.get("_language") != lex.get("_requested"):
        notes.append(f"no lexicon pack for '{lex.get('_requested')}' — "
                     f"English lists used; language-specific counts are unreliable")
    if budget_error:
        notes.append(budget_error)

    counts: dict[str, dict] = {}
    items = LITERARY_ITEMS if literary else NONFICTION_ITEMS

    # rhet-1 — rhetorical questions in narration (exercises excluded)
    if "rhet-1" in items:
        qlines: list[int] = []
        for pl in narr_lines:
            if EXERCISE_RE.search(pl.heading_path or ""):
                continue
            n = len(re.findall(r"\?+", pl.narration))
            qlines += [pl.line] * n
        counts["rhet-1"] = _quota({"count": len(qlines), "lines": qlines}, quotas["rhet-1"])

    # rhet-2 — "not X but Y" reframes, per paragraph of narration
    if "rhet-2" in items:
        rx = L.compile_any(lex.get("not_x_but_y", []), regex=True)
        matches = []
        for text, offsets in _paragraphs(narr_lines):
            for m in L.iter_matches(rx, text):
                matches.append({"line": _line_at(offsets, m.start()), "text": _snip(m.group(0))})
        counts["rhet-2"] = _quota({"count": len(matches), "matches": matches}, quotas["rhet-2"])

    # rhet-3 — dramatic-danger lexicon
    if "rhet-3" in items:
        terms = _hits(lex.get("danger"), narr_lines, lambda pl: pl.narration)
        counts["rhet-3"] = _quota({"count": len(terms), "terms": terms}, quotas["rhet-3"])

    # rhet-4 — artificial cliffhanger in the final two paragraphs
    if "rhet-4" in items:
        paras = [p for p in _paragraphs(narr_lines) if p[0]]
        closing = " ".join(p[0] for p in paras[-2:])
        rx = L.compile_any(lex.get("tease_closings", []), regex=True)
        tease = [m.group(0) for m in L.iter_matches(rx, closing)]
        last = L.split_sentences(paras[-1][0])[-1] if paras else ""
        question = last.rstrip(" »”\"')").endswith("?")
        policy = closing_policy(root)
        counts["rhet-4"] = {
            "hit": bool(tease or question),
            "closing": _snip(closing, 400),
            "teases": tease,
            "final_question": question,
            "policy": policy,
            "quota": 0 if policy in ZERO_TEASE_POLICIES else None,
        }
        counts["rhet-4"]["over"] = bool(counts["rhet-4"]["hit"] and counts["rhet-4"]["quota"] == 0)

    # rhet-5 — bold density
    if "rhet-5" in items:
        bolds = sum(pl.text.count("**") for pl in lines) // 2
        per = round(bolds / total_words * 1000, 2) if total_words else 0.0
        counts["rhet-5"] = {"bolds": bolds, "per_1000": per, "quota": quotas["rhet-5"],
                            "over": quotas["rhet-5"] is not None and per > quotas["rhet-5"]}

    # rhet-7 — template headings
    if "rhet-7" in items:
        rx = L.compile_any(lex.get("template_headings", []), regex=True)
        hits = [{"line": ln, "heading": h} for ln, h in heads if rx and rx.search(h)]
        counts["rhet-7"] = {"headings": hits}

    # Diagnostics (no quota): the Critic reads them, the rubric decides.
    vocab_key = "ai_isms" if literary else "ai_vocab"
    hits = _hits(lex.get(vocab_key), lines if literary else narr_lines,
                 (lambda pl: pl.text) if literary else (lambda pl: pl.narration))
    counts["ai_vocab"] = {"count": len(hits), "hits": hits, "list": vocab_key}
    wh = _hits(lex.get("weasels"), narr_lines, lambda pl: pl.narration)
    counts["weasels"] = {"count": len(wh), "hits": wh}
    # Raya lines were split at their rayas, so only narration dashes remain.
    dashes = sum(pl.narration.count("—") for pl in narr_lines)
    pages = total_words / PAGE_WORDS if total_words else 0
    counts["em_dash_narration"] = {"count": dashes,
                                   "per_page": round(dashes / pages, 2) if pages else 0.0}
    if literary:
        sh = _hits(lex.get("speech_verbs_ornate"), lines, lambda pl: pl.text)
        counts["speech_verbs_ornate"] = {"count": len(sh), "hits": sh}
    narrative = [pl.narration for pl in narr_lines if not (literary and pl.dialogue)]
    counts["sentence_length"] = length_stats(sentence_lengths(narrative))

    return {
        "unit": unit,
        "file": _rel(path, root),
        "language": variant,
        "pack": lex.get("_language"),
        "profile": profile,
        "words": total_words,
        "counts": counts,
        "notes": notes,
    }


def _quota(entry: dict, quota: int | None) -> dict:
    entry["quota"] = quota
    entry["over"] = quota is not None and entry["count"] > quota
    return entry


def _hits(patterns, lines: list[L.ProseLine], get) -> list[dict]:
    rx = L.compile_any(patterns or [], regex=True)
    out = []
    for pl in lines:
        for m in L.iter_matches(rx, get(pl)):
            out.append({"line": pl.line, "term": m.group(0)})
    return out


def _rel(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


# ---------------------------------------------------------------------------


def render(report: dict) -> str:
    out = [f"[count_rhet] {report['unit']} · {report['file']} · {report['language']} "
           f"(pack {report['pack']}) · {report['profile'] or 'no profile'} · "
           f"{report['words']} words"]
    for key in sorted(report["counts"]):
        c = report["counts"][key]
        flag = "  OVER" if c.get("over") else ""
        if "count" in c:
            q = f" / {c['quota']}" if c.get("quota") is not None else ""
            out.append(f"  {key:22} {c['count']}{q}{flag}")
            for h in (c.get("matches") or c.get("terms") or c.get("hits") or [])[:5]:
                out.append(f"      l.{h['line']}  {h.get('text') or h.get('term')}")
        elif key == "rhet-4":
            out.append(f"  {key:22} hit={c['hit']} policy={c['policy']}{flag}")
        elif key == "rhet-5":
            out.append(f"  {key:22} {c['bolds']} bolds, {c['per_1000']}/1000 (quota "
                       f"{c['quota']}){flag}")
        elif key == "rhet-7":
            out.append(f"  {key:22} {len(c['headings'])} template heading(s)")
        elif key == "sentence_length":
            out.append(f"  {key:22} mean {c['mean']} sd {c['sd']} flat_runs {c['flat_runs']}")
    for n in report.get("notes") or []:
        out.append(f"  note: {n}")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Count the rhetoric budget of one unit.")
    ap.add_argument("--root", default=None,
                    help="Project root (default: nearest ancestor with bible/meta.yaml).")
    ap.add_argument("--unit", required=True, help="Unit id, e.g. unit-07.")
    ap.add_argument("--file", default=None,
                    help="File to count (default drafts/<unit>/humanized.md).")
    ap.add_argument("--json", metavar="OUT", help="Write the report as JSON.")
    args = ap.parse_args(argv)

    root = L.find_root(args.root)
    unit = L.unit_id(args.unit) or args.unit
    try:
        report = compute(root, unit, L.at_root(root, args.file))
    except FileNotFoundError as exc:
        print(f"[count_rhet] input missing: {exc}", file=sys.stderr)
        return 2
    print(render(report))
    if args.json:
        out = L.write_json(L.at_root(root, args.json), report)
        print(f"[count_rhet] report → {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
