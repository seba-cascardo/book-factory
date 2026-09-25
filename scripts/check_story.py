#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_story.py — the story's design rules, checked before a word is drafted.

Why this exists. In fiction the value is decided upstream — premise, cast, arcs,
ending — and a pipeline that polishes lines cannot rescue a story nobody
designed. The user set four rules for the literary profile, non-negotiable and
not waivable per project (design contract §6.1):

  R1  Every character (protagonist, principal, secondary) has a complete sheet:
      backstory, personality, contradiction, want, need, voice, and an arc
      (type, start, end, ≥1 turning point assigned to a unit, `resolves_in`;
      a `flat` arc names what its constancy `tests`). No TBD.
  R2  The story has an ending, defined before drafting in
      `bible/plot-structure.md` (`ending.resolution`, `ending.answer`,
      `ending.final_unit`), and every arc resolves at or before `final_unit`.
  R3  Drafting starts only when every character in the outline has backstory,
      personality and an established arc, and the ending exists.
  R4  Characters may be added mid-book, but the questionnaire runs again: a
      named figure on the page that no sheet, alias, extra or world entry knows
      is NEW-CHARACTER, and it blocks the unit.

This script is the mechanical side of those rules. `pipeline_step.py ready` runs
`--ready-to-draft`; `pipeline_step.py check unit-NN writer` and `checks` run
`--unit`; the manuscript gate (MG-S) runs `--manuscript`.

Codes (severity by mode — ready / unit / manuscript):
  CHAR-INCOMPLETE, CHAR-NO-ARC, CHAR-UNKNOWN, CHAR-DUPLICATE ... blocking everywhere
      (CHAR-INCOMPLETE: a required field missing, a placeholder, or — for the
      narrative fields backstory, personality, contradiction, want, need,
      voice, arc.start, arc.end, arc.tests of a flat arc — fewer than 3
      words; `status` other than complete; `signed_on` not a real ISO date
      between 2000-01-01 and today; no `signed_hash`. It also covers EVERY
      file in bible/characters/ except _extras.md: no or broken front matter,
      or a role outside protagonist|principal|secondary, blocks in every mode
      — a sheet cannot launder a name. CHAR-DUPLICATE: two sheets with one
      slug. CHAR-UNKNOWN includes a name in an outline card — summary, want,
      opposition, pivot, crisis, attempts, information, actioned_by — that no
      sheet knows, that world.md lists as mentioned-only, or that the card
      makes speak or act while only world.md or a location knows it)
  CHAR-UNSIGNED-CHANGE ..................................... blocking everywhere
      (the sheet's content no longer matches its `signed_hash`: name, slug,
      role, aliases, the required fields or the arc changed after the human
      signed — re-run the questionnaire block and `pipeline_step.py sign`)
  CHAR-ARC-OUT-OF-OUTLINE .. blocking (ready, unit) / major (manuscript)
  ARC-AFTER-ENDING, ENDING-MISSING, EXTRA-PROMOTE ......... blocking
      (EXTRA-PROMOTE: a recurring or named extra; a word of an _extras.md
      label used as a name on the page — a warning at low confidence, like
      NEW-CHARACTER; ANY world.md word — a name or a place — or outline
      location word in a speaker/actor position on the page)
  NEW-CHARACTER ... blocking (high confidence: mid-sentence, not a common
                    word and never lowercase, or in a speaker/actor position)
                    / warning (low confidence)
  LEDGER-NO-PAYOFF, LEDGER-UNKNOWN .......... blocking (ready, unit) / major
  LEDGER-MISSING, LEDGER-INVALID ............ blocking (ready) / major (manuscript)
      (no bible/story-ledger.yaml — `entries: []` is fine; a status outside
      open|paid|deliberately-ambiguous; `paid` without a `paid_in` unit that
      exists; a placeholder `what` or `trigger`)
  SEEDS-MISSING, CALIBRATION-NO-HUMAN ..... blocking (ready) / warning (manuscript)
  ARC-NOT-RESOLVED, LEDGER-OPEN (manuscript) .............. major
  ENDING-NOT-DELIVERED (manuscript) ....................... blocking
      (final/<final_unit>.md is missing, or holds fewer than max(300, 30% of
      that unit's target_words) words of prose)

Placeholders that count as empty (bookkit/placeholder.py): "", null, TBD, TODO,
N/A, x, -, none, nil, ?, ..., …, pendiente, (pendiente), a definir, por
definir, sin definir, a completar, completar, <completar>, {{…}}, XXX, falta,
Lorem ipsum, lo vemos, and any [bracketed template text].

Known gap (documented, not fixed): a name that is also a common noun, used only
sentence-initially and never in a speaker/actor position while the noun is
written in lowercase elsewhere ("Luz era la hija de Rosa." / "no había luz"),
reads as the noun. The semantic backstop is the Critic's character-3 and CG
Mode A.

Usage
  python scripts/check_story.py --ready-to-draft
  python scripts/check_story.py --unit unit-07 [--file drafts/unit-07/draft.md]
  python scripts/check_story.py --unit unit-07 --no-draft     # outline and sheets only
  python scripts/check_story.py --manuscript --json reviews/story.json

Exit codes: 1 if any blocking finding (or any major in --manuscript), else 0;
2 on a usage error, missing input, an unknown or missing `project.profile`, or
a `schema_version` other than "3.4".
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from bookkit import lexicon as L  # noqa: E402
from bookkit.placeholder import is_placeholder, too_short  # noqa: E402,F401 — re-exported
import lint_fiction as LF  # noqa: E402  — one implementation of the cast and of names

LITERARY = "book-literary"
ROLES = ("protagonist", "principal", "secondary")
ARC_TYPES = ("positive", "negative", "flat")
REQUIRED_TEXT = ("backstory", "personality", "contradiction", "want", "need", "voice")
MIN_WORDS = 3                      # narrative fields: "Tímido." is not a personality
LEDGER_STATUSES = ("open", "paid", "deliberately-ambiguous")
ENDING_MIN_WORDS = 300             # the final unit carries at least this much prose …
ENDING_MIN_SHARE = 0.30            # … or this share of its target_words, whichever is larger
SIGNED_FIELDS = ("name", "role", "aliases", *REQUIRED_TEXT, "arc", "added_mid_book",
                 "added_in_unit")
_CALIBRATION = re.compile(r"<!--\s*calibration-source:\s*([a-z]+)\s*-->", re.I)
SEVERITIES = ("blocking", "major", "warning")
QUESTIONNAIRE = "references/character-questionnaire.md"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _as_date(value) -> _dt.date | None:
    """A real calendar date, from a YAML date or a `YYYY-MM-DD` string."""
    if isinstance(value, _dt.datetime):
        return value.date()
    if isinstance(value, _dt.date):
        return value
    s = str(value or "").strip()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
        return None
    try:
        return _dt.date.fromisoformat(s)
    except ValueError:
        return None


def signed_on_problem(value, today: _dt.date | None = None) -> str:
    """'' when `signed_on` is a real ISO date in [2000-01-01, today]."""
    d = _as_date(value)
    today = today or _dt.date.today()
    if d is None:
        return f"signed_on is {value!r}, not a real YYYY-MM-DD date"
    if d < _dt.date(2000, 1, 1) or d > today:
        return f"signed_on {d.isoformat()} is outside 2000-01-01 … {today.isoformat()}"
    return ""


def _norm(value):
    """Canonical form for hashing: NFC strings with collapsed whitespace, unit
    ids normalized, dict keys sorted (by json.dumps), aliases sorted."""
    if isinstance(value, dict):
        return {str(k): _norm(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_norm(v) for v in value]
    if isinstance(value, (bool, int, float)) or value is None:
        return value
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", str(value))).strip()


def sheet_hash(data: dict, slug: str) -> str:
    """What the human signed: name, slug, role, aliases, the six required
    fields, the arc (type, start, end, tests, turning points, resolves_in) and
    the mid-book markers. `pipeline_step.py sign` writes it as `signed_hash`;
    any later change to those fields no longer matches."""
    body = {k: _norm(data.get(k)) for k in SIGNED_FIELDS}
    body["slug"] = _norm(slug)
    body["role"] = str(body.get("role") or "").lower()
    if isinstance(body.get("aliases"), list):
        body["aliases"] = sorted(str(a) for a in body["aliases"])
    arc = body.get("arc")
    if isinstance(arc, dict):
        arc["resolves_in"] = L.unit_id(arc.get("resolves_in")) or arc.get("resolves_in")
        for tp in arc.get("turning_points") or []:
            if isinstance(tp, dict):
                tp["unit"] = L.unit_id(tp.get("unit")) or tp.get("unit")
    body["added_in_unit"] = L.unit_id(body.get("added_in_unit")) or body.get("added_in_unit")
    raw = json.dumps(body, ensure_ascii=False, sort_keys=True, default=str)
    return "sha256:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _find(code: str, severity: str, subject: str, detail: str, location: str = "") -> dict:
    return {"code": code, "severity": severity, "subject": subject, "detail": detail,
            "location": location}


def _rel(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


class Story:
    """Everything the rules read, loaded once and tolerant of missing files."""

    def __init__(self, root: Path, ctx: LF.Context | None = None):
        self.root = root
        self.ctx = ctx or LF.build_context(root)
        self.meta = self.ctx.meta
        self.cast = {ch.slug: ch for ch in self.ctx.cast}
        self.outline = self.ctx.outline
        self.outline_ids = [e["_id"] for e in self.outline]
        self.errors: list[dict] = []
        self.plot, self.plot_error = self._plot()
        self.ending = (self.plot or {}).get("ending") if isinstance(self.plot, dict) else None
        self.final_unit = L.unit_id((self.ending or {}).get("final_unit")) \
            if isinstance(self.ending, dict) else None
        self.ledger, self.ledger_error = self._ledger()
        self.extras, self.extras_error = LF.load_extras(root)

    def _plot(self):
        path = self.root / "bible" / "plot-structure.md"
        if not path.exists():
            return None, "bible/plot-structure.md does not exist"
        data, _body, err = L.front_matter(L.read_text(path))
        if err:
            return None, f"bible/plot-structure.md: {err}"
        if data is None:
            return None, "bible/plot-structure.md has no YAML front matter"
        return data, None

    def _ledger(self):
        path = self.root / "bible" / "story-ledger.yaml"
        if not path.exists():
            return None, None
        try:
            data = L.read_yaml(path)
        except ValueError as exc:
            return [], str(exc)
        if data is None:
            return [], "bible/story-ledger.yaml is empty — write `entries: []` at least"
        entries = data.get("entries") if isinstance(data, dict) else data
        if not isinstance(entries, list) and entries is not None:
            return [], "bible/story-ledger.yaml: `entries` is not a list"
        return [e for e in entries or [] if isinstance(e, dict)], None

    # -- lookups ----------------------------------------------------------

    def resolve(self, ref) -> LF.Character | None:
        """Slug first; then a character's full name, first name or alias."""
        key = str(ref or "").strip()
        if key in self.cast:
            return self.cast[key]
        f = L.fold(key)
        for ch in self.cast.values():
            names = [ch.name, *(ch.name.split()[:1]), *ch.aliases, ch.slug]
            if any(L.fold(n) == f for n in names if n):
                return ch
        return None

    def entry(self, unit: str) -> dict | None:
        return next((e for e in self.outline if e["_id"] == unit), None)

    def present(self, unit: str) -> list:
        e = self.entry(unit)
        return list((e or {}).get("characters_present") or [])

    def outline_slugs(self) -> dict[str, list[str]]:
        """ref as written in the outline → units where it appears."""
        out: dict[str, list[str]] = {}
        for e in self.outline:
            for ref in e.get("characters_present") or []:
                out.setdefault(str(ref), []).append(e["_id"])
        return out

    def after_ending(self, unit) -> bool:
        n, end = L.unit_num(unit), L.unit_num(self.final_unit)
        return n is not None and end is not None and n > end


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------


def ending_findings(st: Story) -> list[dict]:
    loc = "bible/plot-structure.md"
    if st.plot_error:
        return [_find("ENDING-MISSING", "blocking", "ending", st.plot_error + " — R2: the "
                      "ending is defined before drafting", loc)]
    missing = []
    if is_placeholder(st.plot.get("dramatic_question")):
        missing.append("dramatic_question")
    ending = st.ending if isinstance(st.ending, dict) else {}
    for key in ("resolution", "answer", "final_unit"):
        if is_placeholder(ending.get(key)):
            missing.append(f"ending.{key}")
    out = []
    if missing:
        out.append(_find("ENDING-MISSING", "blocking", "ending",
                         f"missing or placeholder: {', '.join(missing)}", loc))
    elif st.final_unit is None:
        out.append(_find("ENDING-MISSING", "blocking", "ending",
                         f"ending.final_unit is not a unit id: {ending.get('final_unit')!r}", loc))
    elif st.outline_ids and st.final_unit not in st.outline_ids:
        out.append(_find("ENDING-MISSING", "blocking", "ending",
                         f"ending.final_unit {st.final_unit} is not in outline/units.yaml", loc))
    return out


def sheet_findings(st: Story, ch: LF.Character, outline_units: list[str],
                   placement: str = "blocking") -> list[dict]:
    """R1 for one character. `placement`: severity of CHAR-ARC-OUT-OF-OUTLINE."""
    loc = _rel(ch.path, st.root)
    subj = ch.slug
    if ch.error:
        return [_find("CHAR-INCOMPLETE", "blocking", subj, ch.error, loc)]
    if not ch.has_front_matter:
        return [_find("CHAR-INCOMPLETE", "blocking", subj,
                      "no YAML front matter — the sheet predates the v3.4 format; run "
                      f"{QUESTIONNAIRE}", loc)]
    d = ch.data
    out: list[dict] = []
    missing = []

    def narrative(key: str, value) -> None:
        if is_placeholder(value):
            missing.append(key)
        elif too_short(value, MIN_WORDS):
            missing.append(f"{key} (fewer than {MIN_WORDS} words: {str(value).strip()!r})")

    if is_placeholder(d.get("name")):
        missing.append("name")
    if ch.role not in ROLES:
        missing.append(f"role ({d.get('role')!r} is not protagonist|principal|secondary)")
    for k in REQUIRED_TEXT:
        narrative(k, d.get(k))

    arc = d.get("arc")
    if not isinstance(arc, dict) or str(arc.get("type") or "").strip().lower() not in ARC_TYPES:
        why = ("no arc" if not isinstance(arc, dict) or is_placeholder(arc.get("type"))
               else f"arc.type {arc.get('type')!r} is not positive|negative|flat")
        out.append(_find("CHAR-NO-ARC", "blocking", subj, f"{why} — R1: every character "
                         "has an arc (a flat arc names what it tests)", loc))
        arc = arc if isinstance(arc, dict) else {}
    else:
        for key in ("start", "end"):
            narrative(f"arc.{key}", arc.get(key))
        if str(arc.get("type")).strip().lower() == "flat":
            if is_placeholder(arc.get("tests")):
                missing.append("arc.tests (required for a flat arc)")
            elif too_short(arc.get("tests"), MIN_WORDS):
                missing.append(f"arc.tests (fewer than {MIN_WORDS} words)")
        tps = arc.get("turning_points")
        if not isinstance(tps, list) or not tps:
            missing.append("arc.turning_points (≥1)")
        else:
            for i, tp in enumerate(tps, 1):
                if not isinstance(tp, dict) or L.unit_id(tp.get("unit")) is None:
                    missing.append(f"arc.turning_points[{i}].unit")
                elif is_placeholder(tp.get("change")):
                    missing.append(f"arc.turning_points[{i}].change")
        if L.unit_id(arc.get("resolves_in")) is None:
            missing.append("arc.resolves_in")
    if d.get("added_mid_book") and L.unit_id(d.get("added_in_unit")) is None:
        missing.append("added_in_unit (added_mid_book is true)")
    if missing:
        out.append(_find("CHAR-INCOMPLETE", "blocking", subj,
                         "missing or placeholder: " + "; ".join(missing), loc))
    sign = f"`python scripts/pipeline_step.py sign {ch.slug} --by <human>`"
    if str(d.get("status") or "").strip().lower() != "complete":
        out.append(_find("CHAR-INCOMPLETE", "blocking", subj,
                         f"status: {d.get('status')!r} — complete means every field filled "
                         f"AND signed by the human ({sign} when the human approves the sheet)",
                         loc))
    elif signed_on_problem(d.get("signed_on")):
        out.append(_find("CHAR-INCOMPLETE", "blocking", subj,
                         f"status: complete but {signed_on_problem(d.get('signed_on'))} — the "
                         f"human signs the sheet: {sign}", loc))
    elif is_placeholder(d.get("signed_hash")):
        out.append(_find("CHAR-INCOMPLETE", "blocking", subj,
                         f"status: complete but no signed_hash — a signature is bound to the "
                         f"content it approved: {sign}", loc))
    elif str(d.get("signed_hash")).strip() != sheet_hash(d, ch.slug):
        out.append(_find("CHAR-UNSIGNED-CHANGE", "blocking", subj,
                         "the sheet changed after the human signed it (name, role, aliases, a "
                         "required field or the arc no longer match signed_hash) — re-run the "
                         f"questionnaire block for what changed and re-sign: {sign}", loc))

    # Arc placement against the outline and the ending
    units = [(f"turning point {i}", L.unit_id(tp.get("unit")))
             for i, tp in enumerate(arc.get("turning_points") or [], 1) if isinstance(tp, dict)]
    units.append(("resolves_in", L.unit_id(arc.get("resolves_in"))))
    added_in = L.unit_num(d.get("added_in_unit")) if d.get("added_mid_book") else None
    for what, uid in units:
        if uid is None:
            continue
        if added_in is not None and (L.unit_num(uid) or 0) < added_in:
            out.append(_find("CHAR-ARC-OUT-OF-OUTLINE", "blocking", subj,
                             f"{what} → {uid}, before added_in_unit "
                             f"{L.unit_id(d.get('added_in_unit'))} — R4: a character added "
                             "mid-book has its arc in the remaining outline", loc))
        if outline_units and uid not in outline_units:
            out.append(_find("CHAR-ARC-OUT-OF-OUTLINE", "blocking", subj,
                             f"{what} → {uid}, which is not in outline/units.yaml", loc))
        elif what.startswith("turning") and outline_units:
            present = [st.resolve(r) for r in st.present(uid)]
            if not any(p is not None and p.slug == ch.slug for p in present):
                out.append(_find("CHAR-ARC-OUT-OF-OUTLINE", placement, subj,
                                 f"{what} is in {uid}, but {ch.slug} is not in that unit's "
                                 "characters_present", "outline/units.yaml"))
            n = int(what.split()[-1])
            moves = [mv for mv in (st.entry(uid) or {}).get("arc_moves") or []
                     if isinstance(mv, dict) and mv.get("turning_point") == n
                     and getattr(st.resolve(mv.get("character")), "slug", None) == ch.slug]
            if not moves:
                out.append(_find("CHAR-ARC-OUT-OF-OUTLINE", placement, subj,
                                 f"{what} is in {uid}, but that unit's arc_moves has no "
                                 f"{{character: {ch.slug}, turning_point: {n}}}",
                                 "outline/units.yaml"))
        if st.after_ending(uid):
            out.append(_find("ARC-AFTER-ENDING", "blocking", subj,
                             f"{what} → {uid}, after ending.final_unit {st.final_unit} — R2: "
                             "every arc resolves at or before the ending", loc))
    return out


def arc_move_findings(st: Story, units: list[str], placement: str = "blocking") -> list[dict]:
    out = []
    for e in st.outline:
        if e["_id"] not in units:
            continue
        for mv in e.get("arc_moves") or []:
            if not isinstance(mv, dict):
                continue
            ch = st.resolve(mv.get("character"))
            if ch is None:
                out.append(_find("CHAR-UNKNOWN", "blocking", str(mv.get("character")),
                                 f"arc_moves in {e['_id']} names a character with no sheet",
                                 "outline/units.yaml"))
                continue
            tps = ((ch.data.get("arc") or {}).get("turning_points") or []) \
                if isinstance(ch.data.get("arc"), dict) else []
            idx = mv.get("turning_point")
            tp = tps[idx - 1] if isinstance(idx, int) and 0 < idx <= len(tps) else None
            if tp is None or L.unit_id((tp or {}).get("unit")) != e["_id"]:
                out.append(_find("CHAR-ARC-OUT-OF-OUTLINE", placement, ch.slug,
                                 f"arc_moves in {e['_id']} points at turning point {idx!r}, "
                                 "which the sheet does not place in this unit",
                                 "outline/units.yaml"))
    return out


def extras_findings(st: Story, unit: str | None = None) -> list[dict]:
    loc = "bible/characters/_extras.md"
    if st.extras_error:
        return [_find("EXTRA-PROMOTE", "blocking", "_extras.md", st.extras_error, loc)]
    out = []
    for e in st.extras:
        label = str(e.get("label") or "")
        units = [L.unit_id(u) for u in (e.get("units") or []) if L.unit_id(u)]
        if unit and unit not in units:
            continue
        if len(units) > 1:
            out.append(_find("EXTRA-PROMOTE", "blocking", label,
                             f"extra appears in {len(units)} units ({', '.join(units)}) — a "
                             f"recurring figure is a character: run {QUESTIONNAIRE}", loc))
        if any(t[:1].isupper() for t in LF.TOKEN_RE.findall(label)):
            out.append(_find("EXTRA-PROMOTE", "blocking", label,
                             "extra label looks like a proper name — a named figure is a "
                             f"character: run {QUESTIONNAIRE}", loc))
    return out


def bible_findings(st: Story) -> list[dict]:
    """Every file in bible/characters/ except _extras.md is a character sheet:
    valid front matter, a role in protagonist|principal|secondary, one slug per
    sheet. A broken, role-less or duplicate sheet still names someone — without
    this check it made that name "known" and let it onto the page (every mode)."""
    out: list[dict] = []
    by_slug: dict[str, list[str]] = {}
    for ch in st.ctx.cast:
        loc = _rel(ch.path, st.root)
        by_slug.setdefault(ch.slug, []).append(loc)
        if ch.error:
            out.append(_find("CHAR-INCOMPLETE", "blocking", ch.slug, f"broken sheet: {ch.error} — "
                             f"fix the YAML front matter, or run {QUESTIONNAIRE}", loc))
        elif not ch.has_front_matter:
            out.append(_find("CHAR-INCOMPLETE", "blocking", ch.slug,
                             "no YAML front matter — every file in bible/characters/ except "
                             f"_extras.md is a character sheet (templates/character-sheet.md); "
                             f"run {QUESTIONNAIRE}", loc))
        elif ch.role not in ROLES:
            out.append(_find("CHAR-INCOMPLETE", "blocking", ch.slug,
                             f"role {ch.data.get('role')!r} is not protagonist|principal|secondary "
                             "— a figure without a role has no arc; an unnamed one-unit figure "
                             "goes in _extras.md", loc))
    for slug, locs in sorted(by_slug.items()):
        if len(locs) > 1:
            out.append(_find("CHAR-DUPLICATE", "blocking", slug,
                             f"{len(locs)} sheets share slug '{slug}' ({', '.join(locs)}) — one "
                             "sheet per character, one slug per sheet", locs[-1]))
    return out


def ledger_findings(st: Story, *, manuscript: bool, units: list[str] | None = None) -> list[dict]:
    """The story ledger (design-5). Before and during drafting a plant with no
    planned payoff, or a card citing an id the ledger does not have, blocks.
    The ledger itself must exist (`entries: []` is a valid empty ledger) and
    every entry must be well formed."""
    loc = "bible/story-ledger.yaml"
    sev = "major" if manuscript else "blocking"
    if st.ledger_error:
        return [_find("LEDGER-INVALID", sev, "story-ledger", st.ledger_error, loc)]
    if st.ledger is None:
        return [_find("LEDGER-MISSING", sev, "story-ledger",
                      "no bible/story-ledger.yaml — create it from templates/story-ledger.yaml "
                      "(`entries: []` when nothing is planted yet)", loc)]
    finals = {uid for uid, _p in LF.final_units(st.root)} if manuscript else set()
    out = []
    for e in st.ledger:
        eid = str(e.get("id") or "?")
        raw_status = e.get("status")
        status = str(raw_status or "").strip().lower()
        if status not in LEDGER_STATUSES:
            out.append(_find("LEDGER-INVALID", sev, eid,
                             f"status {raw_status!r} is not one of {'|'.join(LEDGER_STATUSES)}",
                             loc))
        for key in ("what", "trigger"):
            if is_placeholder(e.get(key)):
                out.append(_find("LEDGER-INVALID", sev, eid,
                                 f"`{key}` is missing or a placeholder ({e.get(key)!r})", loc))
        if status == "paid":
            paid = L.unit_id(e.get("paid_in"))
            known = set(st.outline_ids) | finals
            if paid is None or (known and paid not in known):
                out.append(_find("LEDGER-INVALID", sev, eid,
                                 f"status paid but paid_in is {e.get('paid_in')!r} — `paid` "
                                 "names the unit that pays it off, and that unit exists", loc))
        payoff = L.unit_id(e.get("payoff_unit"))
        if payoff is None and status not in ("deliberately-ambiguous", "paid"):
            out.append(_find("LEDGER-NO-PAYOFF", sev, eid,
                             f"{e.get('kind', 'entry')} planted in {e.get('planted_in')} has no "
                             "payoff_unit (or mark it deliberately-ambiguous)", loc))
        elif payoff and st.after_ending(payoff):
            out.append(_find("LEDGER-NO-PAYOFF", sev, eid,
                             f"payoff_unit {payoff} is after ending.final_unit {st.final_unit}",
                             loc))
        elif payoff and st.outline_ids and payoff not in st.outline_ids:
            out.append(_find("LEDGER-NO-PAYOFF", sev, eid,
                             f"payoff_unit {payoff} is not in outline/units.yaml", loc))
        if manuscript and status == "open":
            out.append(_find("LEDGER-OPEN", "major", eid,
                             f"still open at the end of the book: {e.get('what') or ''}".strip(),
                             loc))
    known = {str(e.get("id")) for e in st.ledger if e.get("id") is not None}
    for e in st.outline:
        if units is not None and e["_id"] not in units:
            continue
        for b in e.get("beats") or []:
            led = b.get("ledger") if isinstance(b, dict) else None
            if not isinstance(led, dict):
                continue
            for key in ("plants", "pays"):
                for ref in led.get(key) or []:
                    if str(ref) not in known:
                        out.append(_find("LEDGER-UNKNOWN", sev, str(ref),
                                         f"the card {e['_id']}/{b.get('id', '?')} {key} "
                                         f"{ref}, which bible/story-ledger.yaml does not have",
                                         "outline/units.yaml"))
    return out


def seeds_findings(st: Story, severity: str) -> list[dict]:
    seeds = L.meta_get(st.meta, "literary.seeds") or {}
    try:
        need = int(L.meta_get(st.meta, "literary.min_seeds", 5))
    except (TypeError, ValueError):
        need = 5
    missing = [k for k in ("title", "premise") if is_placeholder(seeds.get(k))]
    details = [s for s in (seeds.get("only_in_this_book") or []) if not is_placeholder(s)]
    out = []
    if missing or len(details) < need:
        parts = ([f"{', '.join(missing)} empty"] if missing else []) + (
            [f"{len(details)} of {need} only_in_this_book details"] if len(details) < need else [])
        out.append(_find("SEEDS-MISSING", severity, "literary.seeds",
                         "; ".join(parts) + " — seeds come from the human; the pipeline never "
                         "invents them", "bible/meta.yaml"))
    try:
        want = int(L.meta_get(st.meta, "literary.human_calibration_passages", 1))
    except (TypeError, ValueError):
        want = 1
    guide = st.root / "bible" / "style-guide.md"
    sources = Counter(m.group(1).lower() for m in
                      _CALIBRATION.finditer(L.read_text(guide))) if guide.exists() else Counter()
    if sources["human"] < want:
        out.append(_find("CALIBRATION-NO-HUMAN", severity, "style-guide",
                         f"{sources['human']} calibration passage(s) marked "
                         f"`calibration-source: human`, {want} required "
                         f"(found: {dict(sources) or 'no markers'})", "bible/style-guide.md"))
    return out


def cast_findings(st: Story, only: list[str] | None = None,
                  placement: str = "blocking") -> list[dict]:
    """R1/R3: the characters in the outline (or `only`) and every cast sheet."""
    out: list[dict] = []
    refs = st.outline_slugs()
    wanted = set()
    for ref, units in refs.items():
        if only is not None and ref not in only:
            continue
        ch = st.resolve(ref)
        if ch is None:
            out.append(_find("CHAR-UNKNOWN", "blocking", ref,
                             f"characters_present in {', '.join(units)} names '{ref}', which has "
                             f"no sheet in bible/characters/ — run {QUESTIONNAIRE}",
                             "outline/units.yaml"))
        else:
            wanted.add(ch.slug)
    if only is not None:
        for ref in only:
            if ref not in refs:
                ch = st.resolve(ref)
                if ch is None:
                    out.append(_find("CHAR-UNKNOWN", "blocking", ref, "no sheet",
                                     "outline/units.yaml"))
                else:
                    wanted.add(ch.slug)
    else:
        wanted |= {s for s, ch in st.cast.items() if ch.role in ROLES}
    for slug in sorted(wanted):
        out += sheet_findings(st, st.cast[slug], st.outline_ids, placement)
    return out


CARD_FIELDS = ("summary", "want", "opposition", "pivot", "crisis", "information",
               "actioned_by")


def _card_texts(entry: dict):
    """(where, text) for every text field of the unit's scene cards."""
    for b in entry.get("beats") or []:
        if not isinstance(b, dict):
            continue
        bid = b.get("id") or "?"
        for k in CARD_FIELDS:
            if isinstance(b.get(k), str) and b[k].strip():
                yield f"{bid}.{k}", b[k]
        for i, a in enumerate(b.get("attempts") or [], 1):
            parts = a.values() if isinstance(a, dict) else [a]
            for v in parts:
                if isinstance(v, str) and v.strip():
                    yield f"{bid}.attempts[{i}]", v


def _noun_shaped(folded: str, ctx) -> bool:
    """A capitalized card-opening word with a noun suffix (`llamada`, `decisión`,
    `mudanza`) is shorthand for an event, not a person. Suffixes live in the
    language pack (`noun_suffixes`); a pack without them never matches."""
    sufs = [L.fold(str(s)) for s in (ctx.lex.get("noun_suffixes") or []) if str(s).strip()]
    return any(folded.endswith(s) and len(folded) > len(s) + 2 for s in sufs)


def card_findings(st: Story, units: list[str]) -> list[dict]:
    """R4 — "the outline gains a name". A name in a scene card that no sheet
    knows, or that world.md lists as mentioned-only, puts a figure on stage."""
    ctx = st.ctx
    lower = LF.lower_forms([LF.read_unit(uid, p) for uid, p in LF.final_units(st.root)])
    for e in st.outline:
        for _w, text in _card_texts(e):
            lower |= {L.fold(t) for t in LF.TOKEN_RE.findall(text) if t[:1].islower()}
    out, seen = [], set()
    for e in st.outline:
        if e["_id"] not in units:
            continue
        for where, text in _card_texts(e):
            staged = LF.text_positions(ctx, text)
            for c in LF.name_candidates(text):
                tok, low, f = c.token, c.token.lower(), L.fold(c.token)
                if f in ctx.stop or f in ctx.excl or low in ctx.name_slug:
                    continue
                p1, p2 = L.fold(c.prev1), L.fold(c.prev2)
                if p1 in ctx.heads or (p2 in ctx.heads and (p1 in ctx.connectors
                                                          or c.prev1[:1].isupper())):
                    continue
                if (e["_id"], tok) in seen:
                    continue
                if low in ctx.mentioned:
                    why = ("world.md lists it as mentioned-only; a name in a scene card is on "
                           "stage")
                    sev = "blocking"
                elif low in ctx.world and tok in staged:
                    why = ("only world.md or an outline location knows it (a place, a public "
                           "figure), but the card makes it speak or act — a figure on stage is "
                           "a character")
                    sev = "blocking"
                elif low in ctx.known_exact or f in ctx.known_fold:
                    continue
                elif c.initial and (f in ctx.common or f in lower or ctx.verb_form(tok)
                                    or _noun_shaped(f, ctx)):
                    # Card fields are planning shorthand ("Llamada con Mariana."): a
                    # capitalized first word that is a common word, a verb, or has a
                    # noun suffix is not a person. "Gustavo espera en la vereda." still
                    # blocks — and a name is caught mid-sentence and on the page anyway.
                    continue
                elif p1 in ctx.locative or p1 in ctx.indefinite:
                    # "lo escucha en Diagonal": a place until proven otherwise.
                    why = ("reads as a place (after a locative preposition) — list it in "
                           "world.md, or run the questionnaire if it is a person")
                    sev = "warning"
                else:
                    why = "no sheet, alias, extra or world entry knows it"
                    sev = "blocking"
                seen.add((e["_id"], tok))
                out.append(_find("CHAR-UNKNOWN", sev, tok,
                                 f"outline card {e['_id']}/{where} names '{tok}' — {why}. R4: "
                                 f"the outline gained a name; run {QUESTIONNAIRE}",
                                 "outline/units.yaml"))
    return out


def promotion_findings(st: Story, texts: list, focus: str | None = None) -> list[dict]:
    """R4 — ANY world.md word (a mentioned-only name, a place, a club) or outline
    location that SPEAKS or ACTS on the page is a figure on stage: a character.
    A "place" that speaks is a person. `texts`: UnitText list; `focus`: the unit
    being checked (unit mode) — only names on its page are reported."""
    presence = {u.unit: (u, LF.stage_presence(st.ctx, u)) for u in texts}
    names = sorted({tok for _u, p in presence.values() for tok in p})
    out = []
    for tok in names:
        if focus and tok not in (presence.get(focus) or (None, {}))[1]:
            continue
        acting = sorted(uid for uid, (_u, p) in presence.items() if p.get(tok, {}).get("acts"))
        speaking = [(u, p[tok]["speaks"]) for u, p in presence.values()
                    if p.get(tok, {}).get("speaks") and (focus is None or u.unit == focus)]
        if speaking:
            u, lines = speaking[0]
            out.append(_find("EXTRA-PROMOTE", "blocking", tok,
                             f"'{tok}' is known only to bible/world.md or an outline location (a "
                             f"mentioned-only name, a place) but speaks on the page — a figure "
                             f"with lines is a character: run {QUESTIONNAIRE}",
                             f"{_rel(u.path, st.root)}:{lines[0]}"))
        elif acting and (focus is None or focus in acting):
            u, p = presence[focus or acting[0]]
            out.append(_find("EXTRA-PROMOTE", "blocking", tok,
                             f"'{tok}' is known only to bible/world.md or an outline location (a "
                             f"mentioned-only name, a place) but acts as the subject of a scene "
                             f"in {len(acting)} unit{'s' if len(acting) > 1 else ''} "
                             f"({', '.join(acting)}) — a figure on stage is a character: run "
                             f"{QUESTIONNAIRE}", f"{_rel(u.path, st.root)}:{p[tok]['acts'][0]}"))
    return out


def _name_finding(st: Story, x: dict, where: str, unit_mode: bool) -> dict:
    """lint_fiction's unknown_name → NEW-CHARACTER, or EXTRA-PROMOTE when the
    word comes from an _extras.md label (an extra that got a name)."""
    high = x.get("confidence") == "high"
    detail = x["detail"].replace("NEW-CHARACTER? ", "")
    if unit_mode:
        detail += (f" — R4: the unit pauses; run {QUESTIONNAIRE} for this character, or make "
                   "the figure an unnamed extra" if high else
                   " — low confidence: check whether it is a name")
    code = "EXTRA-PROMOTE" if x.get("extra_label") else "NEW-CHARACTER"
    return _find(code, "blocking" if high else "warning", x["subject"], detail, where)


# ---------------------------------------------------------------------------
# Modes
# ---------------------------------------------------------------------------


def ready_to_draft(st: Story) -> dict:
    f = ending_findings(st) + cast_findings(st) + arc_move_findings(st, st.outline_ids)
    f += bible_findings(st)
    f += extras_findings(st) + ledger_findings(st, manuscript=False)
    f += card_findings(st, st.outline_ids)
    f += seeds_findings(st, "blocking")
    notes = [] if st.outline else ["outline/units.yaml has no entries — only the sheets "
                                   "were checked"]
    return _result("ready-to-draft", None, f, {}, notes)


def unit_mode(st: Story, unit: str, file: Path | None = None, scan_draft: bool = True) -> dict:
    notes: list[str] = []
    entry = st.entry(unit)
    if entry is None:
        notes.append(f"{unit} has no entry in outline/units.yaml — characters not verified")
    present = [str(r) for r in st.present(unit)]
    f = ending_findings(st) + cast_findings(st, only=present) + bible_findings(st)
    f += arc_move_findings(st, [unit]) + extras_findings(st, unit)
    f += card_findings(st, [unit])
    f += [x for x in ledger_findings(st, manuscript=False, units=[unit])
          if x["code"] == "LEDGER-UNKNOWN"]

    context: dict = {"final_unit": st.final_unit, "is_final_unit": unit == st.final_unit,
                     "characters_present": present}
    context["arcs_resolving_here"] = sorted(
        ch.slug for ch in st.cast.values() if isinstance(ch.data.get("arc"), dict)
        and L.unit_id(ch.data["arc"].get("resolves_in")) == unit)
    context["turning_points_here"] = sorted(
        f"{ch.slug}#{i}" for ch in st.cast.values() if isinstance(ch.data.get("arc"), dict)
        for i, tp in enumerate(ch.data["arc"].get("turning_points") or [], 1)
        if isinstance(tp, dict) and L.unit_id(tp.get("unit")) == unit)
    context["ledger_due_here"] = sorted(
        str(e.get("id")) for e in st.ledger or []
        if L.unit_id(e.get("payoff_unit")) == unit
        and str(e.get("status") or "open").lower() == "open")
    context["ledger_planted_here"] = sorted(
        str(e.get("id")) for e in st.ledger or [] if L.unit_id(e.get("planted_in")) == unit)
    context["extras_here"] = sorted(
        str(e.get("label")) for e in st.extras
        if unit in [L.unit_id(u) for u in e.get("units") or []])

    if scan_draft:
        path = file or LF.unit_file(st.root, unit)
        if path is None or not Path(path).exists():
            notes.append(f"no draft text for {unit} — page not scanned for new names")
        else:
            context["scanned"] = _rel(Path(path), st.root)
            f += new_character_findings(st, unit, Path(path))
            u = LF.read_unit(unit, Path(path))
            on_page = sorted({st.ctx.name_slug[c.token.lower()] for pl in u.lines
                              for c in LF.name_candidates(pl.text)
                              if c.token.lower() in st.ctx.name_slug})
            context["characters_on_page"] = on_page
    return _result("unit", unit, f, context, notes)


def new_character_findings(st: Story, unit: str, path: Path) -> list[dict]:
    """R4: named figures on the page that nothing in the bible knows."""
    u = LF.read_unit(unit, path)
    corpus = [u] + [LF.read_unit(uid, p) for uid, p in LF.final_units(st.root) if uid != unit]
    out = promotion_findings(st, corpus, focus=unit)
    for f in LF.unknown_names(st.ctx, u, LF.lower_forms(corpus)):
        if f["rule"] == "unknown_name":
            out.append(_name_finding(st, f, f"{_rel(path, st.root)}:{f['line']}", True))
    return out


def ending_delivery(st: Story, finals: dict) -> list[dict]:
    """R2 on the page: the final unit exists and carries enough prose to hold an
    ending — at least max(ENDING_MIN_WORDS, ENDING_MIN_SHARE × target_words)."""
    if not st.final_unit:
        return []
    if st.final_unit not in finals:
        return [_find("ENDING-NOT-DELIVERED", "blocking", "ending",
                      f"ending.final_unit {st.final_unit} is not in final/ — the book stops "
                      "before its ending", "bible/plot-structure.md")]
    words = LF.read_unit(st.final_unit, finals[st.final_unit]).words
    try:
        target = int((st.entry(st.final_unit) or {}).get("target_words") or 0) or None
    except (TypeError, ValueError):
        target = None
    floor = max(ENDING_MIN_WORDS, int(ENDING_MIN_SHARE * target) if target else 0)
    if words < floor:
        return [_find("ENDING-NOT-DELIVERED", "blocking", "ending",
                      f"final/{st.final_unit}.md holds {words} words of prose, fewer than "
                      f"{floor} (max of {ENDING_MIN_WORDS} and {int(ENDING_MIN_SHARE * 100)}% of "
                      f"target_words {target or '—'}) — a one-line chapter does not deliver "
                      "ending.resolution", f"final/{st.final_unit}.md")]
    return []


def manuscript_mode(st: Story) -> dict:
    f = ending_findings(st) + cast_findings(st, placement="major") + bible_findings(st)
    f += arc_move_findings(st, st.outline_ids, placement="major")
    f += extras_findings(st) + ledger_findings(st, manuscript=True)
    f += seeds_findings(st, "warning")
    finals = dict(LF.final_units(st.root))
    f += ending_delivery(st, finals)
    for ch in st.cast.values():
        arc = ch.data.get("arc") if isinstance(ch.data.get("arc"), dict) else None
        if ch.role not in ROLES or arc is None:
            continue
        uid = L.unit_id(arc.get("resolves_in"))
        if uid is None:
            continue
        if uid not in finals:
            f.append(_find("ARC-NOT-RESOLVED", "major", ch.slug,
                           f"arc resolves_in {uid}, which is not in final/",
                           _rel(ch.path, st.root)))
            continue
        text = L.read_text(finals[uid])
        if not any(re.search(r"(?<!\w)" + re.escape(t) + r"(?!\w)", text)
                   for t in ch.tokens() if len(t) > 2):
            f.append(_find("ARC-NOT-RESOLVED", "major", ch.slug,
                           f"{ch.slug} never appears in {uid}, where the arc resolves",
                           f"final/{uid}.md"))
    units = [LF.read_unit(uid, p) for uid, p in finals.items()]
    f += promotion_findings(st, units)
    lower = LF.lower_forms(units)
    for u in units:
        for x in LF.unknown_names(st.ctx, u, lower):
            if x["rule"] == "unknown_name":
                f.append(_name_finding(st, x, f"{_rel(u.path, st.root)}:{x['line']}", False))
    return _result("manuscript", None, f, {"final_unit": st.final_unit,
                                            "units_in_final": sorted(finals)}, [])


def _result(mode: str, unit: str | None, findings: list[dict], context: dict,
            notes: list[str]) -> dict:
    seen, uniq = set(), []
    for x in findings:
        key = (x["code"], x["severity"], x["subject"], x["detail"])
        if key not in seen:
            seen.add(key)
            uniq.append(x)
    uniq.sort(key=lambda x: (SEVERITIES.index(x["severity"]), x["code"], x["subject"]))
    counts = Counter(x["severity"] for x in uniq)
    return {"mode": mode, "unit": unit, "applicable": True, "findings": uniq,
            "summary": {s: counts.get(s, 0) for s in SEVERITIES},
            "context": context, "notes": notes}


def run(root: Path, mode: str, unit: str | None = None, file: Path | None = None,
        scan_draft: bool = True, ctx: LF.Context | None = None) -> dict:
    """Entry point for pipeline_step and the gate. `mode`: ready | unit | manuscript."""
    ctx = ctx or LF.build_context(root)
    if not ctx.literary:
        profile = L.profile_of(ctx.meta) or "unknown"
        return {"mode": mode, "unit": unit, "applicable": False, "findings": [],
                "summary": {s: 0 for s in SEVERITIES}, "context": {},
                "notes": [f"n/a — profile {profile} is not book-literary"]}
    st = Story(root, ctx)
    if mode == "ready":
        return ready_to_draft(st)
    if mode == "unit":
        return unit_mode(st, unit or "", file, scan_draft)
    return manuscript_mode(st)


def failed(result: dict) -> bool:
    s = result["summary"]
    return bool(s["blocking"] or (result["mode"] == "manuscript" and s["major"]))


def render(result: dict) -> str:
    s = result["summary"]
    head = (f"[check_story] {result['mode']}" + (f" {result['unit']}" if result["unit"] else "")
            + f" · {s['blocking']} blocking, {s['major']} major, {s['warning']} warning")
    lines = [head]
    for x in result["findings"]:
        loc = f"  ({x['location']})" if x["location"] else ""
        lines.append(f"  [{x['severity']:8}] {x['code']:24} {x['subject']}: {x['detail']}{loc}")
    need_q = sorted({x["subject"] for x in result["findings"] if x["severity"] == "blocking"
                     and x["code"] in ("CHAR-INCOMPLETE", "CHAR-NO-ARC", "CHAR-UNKNOWN",
                                       "NEW-CHARACTER", "EXTRA-PROMOTE")})
    if need_q:
        lines.append(f"  → run {QUESTIONNAIRE} with the human for: {', '.join(need_q)}")
    for n in result["notes"]:
        lines.append(f"  note: {n}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Check the literary design rules R1–R4.")
    ap.add_argument("--root", default=None,
                    help="Project root (default: nearest ancestor with bible/meta.yaml).")
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--ready-to-draft", action="store_true",
                      help="R1–R3 before drafting (pipeline_step.py ready).")
    mode.add_argument("--unit", help="One unit: its cast, arcs, and new names on its page.")
    mode.add_argument("--manuscript", action="store_true",
                      help="The whole book (manuscript gate MG-S).")
    ap.add_argument("--file", help="With --unit: the text to scan (default: newest draft "
                                   "artifact, then final/<unit>.md).")
    ap.add_argument("--no-draft", action="store_true",
                    help="With --unit: check the outline and sheets only, not the page.")
    ap.add_argument("--json", metavar="OUT", help="Write findings as JSON.")
    args = ap.parse_args(argv)

    root = L.find_root(args.root)
    if not (root / "bible" / "meta.yaml").exists():
        print(f"[check_story] no bible/meta.yaml under {root}", file=sys.stderr)
        return 2
    meta = L.load_meta(root)
    for problem in (L.schema_problem(meta), L.profile_problem(meta)):
        if problem:
            print(f"[check_story] {problem}", file=sys.stderr)
            return 2
    if args.ready_to_draft:
        result = run(root, "ready")
    elif args.manuscript:
        result = run(root, "manuscript")
    else:
        unit = L.unit_id(args.unit) or args.unit
        f = L.at_root(root, args.file)
        if f is not None and not f.exists():
            print(f"[check_story] missing: {f}", file=sys.stderr)
            return 2
        result = run(root, "unit", unit, f, scan_draft=not args.no_draft)
    print(render(result))
    if args.json:
        out = L.write_json(L.at_root(root, args.json), result)
        print(f"[check_story] findings → {out}")
    return 1 if failed(result) else 0


if __name__ == "__main__":
    sys.exit(main())
