#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""selftest_new.py — regression tests for the v3.4 scripts (S2).

`scripts/selftest.py` imports every `tests/selftest_*.py` and runs each callable
in `TESTS` as `fn(tmp, check, run)`, with the same semantics as its own tests:

  check(name, condition, detail="")   records one assertion
  run(script, args) -> (code, output) runs `scripts/<script>` in a subprocess

Every script gets both directions, as the main selftest demands: the defect is
**found**, and clean input produces **nothing**. The user's literary rules are
tested by name, and every hole the v3.4 adversarial review found has a
regression here (`item N` in the assertion name):

  R3  `pipeline_step.py ready` fails while any character in the outline has a TBD
      backstory/personality/arc, an unsigned sheet, or the ending is missing.
  R4  a name no sheet knows — mid-sentence, or sentence-initial and never
      lowercase ("Gustavo no saludó.") — blocks the unit; so does a world.md
      name that speaks or acts, and a new name in an outline card. No human
      override, waiver or --force gets past a story block.

Fixtures: `tests/fixtures_new/novela` (Spanish, raya dialogue, one incomplete
sheet), `novela-fixes/` (the completed sheet, a new character's sheet, a clean
final chapter 3), and `tests/fixtures_new/tecnico` (a Qlik chapter calling the
invented `GroupConcat()`).
"""

from __future__ import annotations

import json
import os
import re
import shutil
import sys
import time
from pathlib import Path
from typing import Callable

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent
FIX = HERE / "fixtures_new"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

_counter = [0]


def _copy(tmp: Path, name: str, *, fixed: bool = False) -> Path:
    """A private copy of a fixture. `fixed=True` completes Rosa's sheet (R1 met)."""
    _counter[0] += 1
    dst = tmp / f"s2-{name}-{_counter[0]}"
    shutil.copytree(FIX / name, dst)
    if fixed:
        shutil.copyfile(FIX / "novela-fixes" / "rosa.md", dst / "bible/characters/rosa.md")
    return dst


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def _edit(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    assert old in text, f"fixture drift: {old!r} not in {path.name}"
    _write(path, text.replace(old, new, 1))


def _touch_later(path: Path, than: Path) -> None:
    st = than.stat()
    os.utime(path, ns=(st.st_atime_ns, st.st_mtime_ns + 2_000_000_000))


def _backdate(path: Path, seconds: int = 30) -> None:
    st = path.stat()
    os.utime(path, ns=(st.st_atime_ns, st.st_mtime_ns - seconds * 1_000_000_000))


def _ps(run, work: Path):
    return lambda *a: run("pipeline_step.py", ["--root", str(work), *a])


def _step(ps, unit: str, agent: str, write, cycle: int = 1, tier: str = "audit",
          extra: tuple = ()) -> tuple[int, str]:
    """check → write the output → done. Raises when `check` refuses (setup only)."""
    code, log = ps("check", unit, agent, *(("--cycle", str(cycle)) if cycle > 1 else ()), *extra)
    if code != 0:
        raise AssertionError(f"setup: check {unit} {agent} c{cycle} refused:\n{log[-600:]}")
    write()
    return ps("done", unit, agent, "--tier", tier, "--cycle", str(cycle))


CLEAN_U3 = (FIX / "novela-fixes/unit-03-final.md").read_text(encoding="utf-8")


def _scorecard(rows: list[tuple], verdict: str, target: str | None, tolerance: str = "full") -> str:
    """rows: (id, severity, status, target)."""
    out = [f'schema_version: "3.4"', 'unit: "unit-03"', f"tolerance: {tolerance}", "items:"]
    for rid, sev, status, tgt in rows:
        out += [f"  - id: {rid}", "    rubric: x", f"    name: {rid}", f"    severity: {sev}",
                f"    status: {status}", "    evidence: \"x\"",
                f"    loopback_target: {tgt if tgt else 'null'}"]
    out += [f"computed_verdict: {verdict}", f"loopback_target: {target or 'null'}"]
    return "\n".join(out) + "\n"


def _critique(verdict: str, target: str) -> str:
    return (f"# Critique: unit-03\n\n## Most important problem: x\n## Verdict: {verdict}\n"
            f"## Loopback target: {target}\n## Loopback rationale: x\n## Cycle count: 1 of 3\n")


PASS_ROWS = [("beats-1", "critical", "pass", None), ("voice-6", "significant", "pass", None)]


def _literary_to_critic(ps, d: Path, text: str, unit: str = "unit-03") -> None:
    """A literary unit bracketed Writer → … → checks, ready for the Critic."""
    body = "<!-- SCENE s1 -->\n" + text
    _step(ps, unit, "writer", lambda: _write(d / "draft.md", body), tier="creative")
    _step(ps, unit, "editor", lambda: _write(d / "edit.md", body))
    _step(ps, unit, "humanizer", lambda: _write(d / "humanized.md", body), tier="creative")
    _step(ps, unit, "reader_pov", lambda: _write(d / "reader-report.md", "# Reader\n\nfine\n"))
    _step(ps, unit, "continuity_a", lambda: _write(d / "coherence.md", "# Coherence\n\nok\n"))
    ps("checks", unit)


def _critic(ps, d: Path, rows, verdict, target, unit: str = "unit-03") -> tuple[int, str]:
    return _step(ps, unit, "critic", lambda: (_write(d / "scorecard.yaml",
                                                     _scorecard(rows, verdict, target)),
                                              _write(d / "critique.md",
                                                     _critique(verdict, target or "none"))),
                 tier="creative")


# ---------------------------------------------------------------------------
# Lexicon packs
# ---------------------------------------------------------------------------


def test_lexicon_packs(tmp: Path, check, run) -> None:
    print("\nlexicons — both packs complete, every pattern compiles")
    from bookkit import lexicon as L
    keys = ["modality", "universal", "breaks", "stopwords", "ai_vocab", "ai_isms", "weasels",
            "danger", "not_x_but_y", "template_headings", "tease_closings",
            "speech_verbs_plain", "speech_verbs_ornate", "gestures", "cliches",
            "attribute_terms", "common_words", "initial_verb_forms", "person_actions",
            "object_markers"]
    for lang in ("es", "en"):
        lex = L.load(lang)
        missing = [k for k in keys if not lex.get(k)]
        check(f"{lang} pack has every contract key", not missing, f"missing: {missing}")
        bad = []
        for k in keys:
            if k in ("stopwords", "common_words", "object_markers"):
                continue
            if k == "gestures":
                L.compile_labeled(lex[k])
            elif k == "attribute_terms":
                for attr in ("eyes", "hair", "age"):
                    check(f"{lang} attribute_terms.{attr} present", bool(lex[k].get(attr)))
                    for _l, rx in L.compile_labeled({attr: lex[k].get(attr) or []}):
                        if "value" not in rx.groupindex:
                            bad.append(f"{attr}: no (?P<value>)")
            elif L.compile_any(lex[k], regex=True) is None:
                bad.append(k)
        check(f"{lang} patterns compile", not bad, f"{bad}")
        nonstr = [w for w in lex["stopwords"] + lex.get("name_exclusions", [])
                  + lex["common_words"] + lex["object_markers"] if not isinstance(w, str)]
        check(f"{lang} plain-word lists hold only strings", not nonstr,
              f"YAML read {nonstr} as booleans — quote 'no', 'on', 'off'")
        check(f"item 1: {lang} common_words is a real frequency list (≥1500 words)",
              len(set(lex["common_words"])) >= 1500, str(len(lex["common_words"])))
    es = L.load("es-AR")
    rx = L.compile_any(es["not_x_but_y"], regex=True)
    for s in ("No es una bendición, no es un permiso. Es un dato.",
              "No era miedo, era cansancio.", "no solo llegó tarde, sino que se fue temprano",
              "No se trata de ganar. Se trata de no perder."):
        check(f"es not_x_but_y matches {s[:30]!r}", bool(rx.search(s)))
    check("es not_x_but_y ignores a plain contrast",
          not rx.search("No quiero agua, sino vino.") and not rx.search("Tenía menos plata que antes."))
    common = L.plain_set(es["common_words"])
    check("item 1: sentence starters are common (nadie, afuera, todavia, entonces, despues)",
          {"nadie", "afuera", "todavia", "entonces", "despues"} <= common)
    check("item 1: first-name words stay out of common_words (rosa, clara, paz, luz)",
          not {"rosa", "clara", "paz", "luz", "victoria"} & common)


# ---------------------------------------------------------------------------
# count_rhet
# ---------------------------------------------------------------------------


def test_count_rhet(tmp: Path, check, run) -> None:
    print("\ncount_rhet — the rhetoric budget, counted")
    tech = FIX / "tecnico"
    out = tmp / "rhet-tech.json"
    code, log = run("count_rhet.py", ["--root", str(tech), "--unit", "unit-01", "--json", str(out)])
    check("count_rhet runs on the technical fixture", code == 0 and out.exists(), log[-300:])
    if not out.exists():
        return
    c = _json(out)["counts"]
    check("rhet-1 counts the rhetorical questions (3, over quota 2)",
          c["rhet-1"]["count"] == 3 and c["rhet-1"]["over"], f"{c['rhet-1']}")
    check("rhet-2 finds both reframes", c["rhet-2"]["count"] == 2, f"{c['rhet-2']}")
    check("rhet-3 counts the danger lexicon (silently ×2, lurking)",
          c["rhet-3"]["count"] == 3, f"{c['rhet-3']}")
    check("rhet-4 flags the tease closing under a recap policy",
          c["rhet-4"]["hit"] and c["rhet-4"]["over"], f"{c['rhet-4']}")
    check("rhet-5 bold density over quota", c["rhet-5"]["over"], f"{c['rhet-5']}")
    check("rhet-7 finds the template heading", len(c["rhet-7"]["headings"]) == 1)
    check("ai_vocab finds delve/leverage", c["ai_vocab"]["count"] >= 2)

    out2 = tmp / "rhet-tech-clean.json"
    run("count_rhet.py", ["--root", str(tech), "--unit", "unit-01", "--file",
                          "final/unit-01.md", "--json", str(out2)])
    c2 = _json(out2)["counts"]
    check("clean technical text: rhet-1..3 are zero",
          c2["rhet-1"]["count"] == c2["rhet-2"]["count"] == c2["rhet-3"]["count"] == 0,
          f"{ {k: c2[k].get('count') for k in ('rhet-1', 'rhet-2', 'rhet-3')} }")
    check("clean technical text: no tease, no template heading",
          not c2["rhet-4"]["hit"] and not c2["rhet-7"]["headings"])

    nov = FIX / "novela"
    out3 = tmp / "rhet-lit.json"
    run("count_rhet.py", ["--root", str(nov), "--unit", "unit-03", "--json", str(out3)])
    r3 = _json(out3)
    lines = [m["line"] for m in r3["counts"]["rhet-2"]["matches"]]
    check("literary rhet-2 counts narration reframes (2)", r3["counts"]["rhet-2"]["count"] == 2,
          f"{r3['counts']['rhet-2']}")
    check("literary rhet-2 ignores the reframe inside raya dialogue (line 14)", 14 not in lines)
    check("literary report carries only rhet-2 of the rhet family",
          not any(k in r3["counts"] for k in ("rhet-1", "rhet-3", "rhet-5", "rhet-7")))
    check("literary speech_verbs_ornate finds 'espetó'",
          any(h["term"].lower() == "espetó" for h in r3["counts"]["speech_verbs_ornate"]["hits"]))
    out4 = tmp / "rhet-lit-clean.json"
    run("count_rhet.py", ["--root", str(nov), "--unit", "unit-01", "--file", "final/unit-01.md",
                          "--json", str(out4)])
    c4 = _json(out4)["counts"]
    check("dialogue rayas are never counted as em-dashes", c4["em_dash_narration"]["count"] == 0,
          f"{c4['em_dash_narration']}")
    check("clean literary text: rhet-2 zero, no AI-isms",
          c4["rhet-2"]["count"] == 0 and c4["ai_vocab"]["count"] == 0)

    # Spanish nonfiction + a voice-profile override that tightens rhet-2 to 0.
    work = _copy(tmp, "tecnico")
    _edit(work / "bible/meta.yaml", 'language_variant: "en-US"', 'language_variant: "es-AR"')
    _write(work / "bible/voice-profile.md",
           "## 5. Rhetoric budget\n\n```yaml\nrhetoric_budget:\n  rhet-2: 0\n```\n")
    _write(work / "drafts/unit-02/humanized.md",
           "# Agregar textos\n\n¿Por qué una lista en una celda? Porque la piden.\n\n"
           "No es un truco de formato, es una agregación. La función falla en silencio "
           "cuando el campo es nulo.\n")
    out5 = tmp / "rhet-es.json"
    run("count_rhet.py", ["--root", str(work), "--unit", "unit-02", "--json", str(out5)])
    c5 = _json(out5)["counts"]
    check("Spanish nonfiction: rhet-1 counts ¿…?", c5["rhet-1"]["count"] == 1, f"{c5['rhet-1']}")
    check("Spanish nonfiction: 'No es X, es Y' counted", c5["rhet-2"]["count"] == 1)
    check("voice-profile rhetoric_budget override applies (rhet-2 quota 0 → over)",
          c5["rhet-2"]["quota"] == 0 and c5["rhet-2"]["over"], f"{c5['rhet-2']}")
    check("Spanish danger lexicon: 'en silencio'", c5["rhet-3"]["count"] == 1, f"{c5['rhet-3']}")


# ---------------------------------------------------------------------------
# check_identifiers
# ---------------------------------------------------------------------------


def test_check_identifiers(tmp: Path, check, run) -> None:
    print("\ncheck_identifiers — the GroupConcat case")
    work = _copy(tmp, "tecnico")
    out = tmp / "ids.json"
    code, log = run("check_identifiers.py", ["--root", str(work), "--unit", "unit-01",
                                             "--json", str(out)])
    data = _json(out)
    names = {e["identifier"] for e in data["unknown"]}
    check("invented GroupConcat() is reported", "GroupConcat" in names, f"{names}")
    check("GroupConcat reported in code too",
          any(e["identifier"] == "GroupConcat" and e["in_code"] for e in data["unknown"]))
    check("documented Concat/Peek, the book's own OrderDate and the allowlisted vCurrentYear "
          "are not reported", not names & {"Concat", "Peek", "OrderDate", "vCurrentYear"},
          f"{names}")
    code, _ = run("check_identifiers.py", ["--root", str(work), "--unit", "unit-01",
                                           "--fail-on-unknown"])
    check("--fail-on-unknown exits 1 on an invented identifier", code == 1, f"got {code}")

    out2 = tmp / "ids-clean.json"
    code, _ = run("check_identifiers.py", ["--root", str(work), "--units", "final/unit-*.md",
                                           "--json", str(out2), "--fail-on-unknown"])
    check("clean chapter: no unknown identifier", code == 0 and not _json(out2)["unknown"],
          f"{_json(out2)['unknown']}")

    code, log = run("check_identifiers.py", ["--root", str(work), "--build-index"])
    idx = work / "bible/identifier-index.txt"
    check("--build-index writes the index", code == 0 and idx.exists(), log[-200:])
    _write(idx, idx.read_text(encoding="utf-8") + "GroupConcat  approved by hand for a test\n")
    run("check_identifiers.py", ["--root", str(work), "--build-index"])
    text = idx.read_text(encoding="utf-8")
    check("hand-written '# allow' section survives a rebuild",
          "GroupConcat  approved by hand" in text.split("# allow", 1)[-1])
    out3 = tmp / "ids-allowed.json"
    run("check_identifiers.py", ["--root", str(work), "--unit", "unit-01", "--json", str(out3)])
    check("an allowed identifier is known", not _json(out3)["unknown"],
          f"{_json(out3)['unknown']}")


# ---------------------------------------------------------------------------
# check_role_diff
# ---------------------------------------------------------------------------


def test_check_role_diff(tmp: Path, check, run) -> None:
    print("\ncheck_role_diff — role contracts verified by diff")
    base = (FIX / "novela/final/unit-01.md").read_text(encoding="utf-8")
    d = tmp / "roles"
    _write(d / "before.md", base)
    paras = base.split("\n\n")
    moved = "\n\n".join([paras[0], paras[2], paras[1], *paras[3:]])
    _write(d / "moved.md", moved)
    out = tmp / "rd-move.json"
    run("check_role_diff.py", ["--root", str(d), "--role", "editor", "--before", "before.md",
                               "--after", "moved.md", "--json", str(out)])
    r = _json(out)
    check("editor that only reorders: no violation, moves detected",
          not r["violations"] and r["sentences_moved"] >= 1 and r["added_words_ratio"] == 0,
          f"{ {k: r[k] for k in ('violations', 'sentences_moved', 'added_words_ratio')} }")

    _write(d / "added.md", base + "\nMariana pensó en todo lo que había pasado en esa casa, "
           "en los veranos largos, en las siestas, en la voz de su madre llamándola desde "
           "la cocina para tomar la leche.\n")
    out2 = tmp / "rd-add.json"
    code, _ = run("check_role_diff.py", ["--root", str(d), "--role", "editor", "--before",
                                         "before.md", "--after", "added.md", "--json", str(out2),
                                         "--fail-on-violation"])
    check("editor that writes a new paragraph is a violation",
          code == 1 and _json(out2)["violations"], f"code {code}")

    small = base.replace("Tenía la perilla pegada con cinta aisladora.",
                         "Tenía la perilla pegada con cinta.")
    _write(d / "small.md", small)
    out3 = tmp / "rd-small.json"
    run("check_role_diff.py", ["--root", str(d), "--role", "humanizer", "--before", "before.md",
                               "--after", "small.md", "--budget", "0.03", "--json", str(out3)])
    r3 = _json(out3)
    check("humanizer within 3%: not over budget",
          not r3["over_budget"] and r3["sentences_modified"] == 1, f"{r3['touched_ratio']}")
    big = re.sub(r"—dijo (\w+)", r"—le dijo \1 en voz baja", base)
    _write(d / "big.md", big)
    out4 = tmp / "rd-big.json"
    run("check_role_diff.py", ["--root", str(d), "--role", "humanizer", "--before", "before.md",
                               "--after", "big.md", "--budget", "0.03", "--json", str(out4)])
    check("humanizer touching many sentences: over budget", _json(out4)["over_budget"],
          f"{_json(out4)['touched_ratio']}")

    proof = base.replace("—¿Y eso? —preguntó Mariana.", "—¿Y eso? —preguntó Mariana—.")
    _write(d / "proof.md", proof)
    out5 = tmp / "rd-proof.json"
    run("check_role_diff.py", ["--root", str(d), "--role", "proofreader", "--before",
                               "before.md", "--after", "proof.md", "--json", str(out5)])
    r5 = _json(out5)
    check("proofreader: the one changed raya/¿? sentence is listed for the human",
          len(r5["changes"]) == 1 and r5["changes"][0]["kind"] == "modified"
          and not r5["violations"], f"{r5['changes']}")
    out6 = tmp / "rd-same.json"
    run("check_role_diff.py", ["--root", str(d), "--role", "proofreader", "--before",
                               "before.md", "--after", "before.md", "--json", str(out6)])
    check("identical texts: no changes", not _json(out6)["changes"])



# ---------------------------------------------------------------------------
# lint_fiction
# ---------------------------------------------------------------------------


def test_lint_fiction(tmp: Path, check, run) -> None:
    print("\nlint_fiction — tics, names, dialogue form")
    nov = FIX / "novela"
    out = tmp / "lf-unit.json"
    code, log = run("lint_fiction.py", ["--root", str(nov), "--unit", "unit-03", "--json", str(out),
                                        "--fail-on", "major"])
    data = _json(out)
    rules = {(f["rule"], f["severity"]) for f in data["findings"]}
    subj = {(f["rule"], f.get("subject")) for f in data["findings"]}
    check("defective unit exits 1 with --fail-on major", code == 1, f"got {code}")
    check("unknown name Gustavo → major NEW-CHARACTER?",
          ("unknown_name", "Gustavo") in subj and ("unknown_name", "major") in rules)
    check("'Tomas' reported as near-duplicate of 'Tomás', not as a new character",
          ("near_duplicate_name", "Tomas") in subj and ("unknown_name", "Tomas") not in subj)
    check("hyphen dialogue and glued dialogue → dialogue_format major",
          sum(1 for f in data["findings"] if f["rule"] == "dialogue_format") >= 2)
    check("'1999.' paragraph → ordered_list_hazard major", ("ordered_list_hazard", "major") in rules)
    check("AI-ism → cliche major, stock phrase → cliche minor",
          ("cliche", "major") in rules and ("cliche", "minor") in rules)
    check("ornate speech verb 'espetó'", ("speech_verb_ornate", "minor") in rules)
    check("gesture tics over quota (reír, asentir)",
          {("gesture_tic", "reír"), ("gesture_tic", "asentir")} <= subj, f"{subj}")
    check("eye colour conflict with an approved unit → attribute_mentions",
          ("attribute_mentions", "mariana") in subj)
    check("mixed scene breaks", ("scene_break_mix", "minor") in rules)

    for unit in ("unit-01", "unit-02"):
        out2 = tmp / f"lf-clean-{unit}.json"
        code, _ = run("lint_fiction.py", ["--root", str(nov), "--unit", unit, "--file",
                                          f"final/{unit}.md", "--json", str(out2),
                                          "--fail-on", "major"])
        clean = _json(out2)["findings"]
        names = [f for f in clean if f["rule"] in ("unknown_name", "near_duplicate_name",
                                                   "mentioned_on_stage")]
        check(f"clean {unit}: no major finding", code == 0,
              f"{[f for f in clean if f['severity'] == 'major']}")
        # Italics and ALL CAPS are scanned now (fix round 2, item 3): the title
        # *Rayuela* and the box label FRÁGIL are low-confidence notes, never blocks.
        check(f"item 1: clean {unit} — zero blocking name false positives (raya openers, "
              "Domingo, Dios, Mari, Central, Buenos Aires, Spica, sentence starters); only the "
              "marked *Rayuela* / FRÁGIL as low-confidence notes",
              not [f for f in names if f["severity"] == "major"]
              and {f["subject"] for f in names} <= {"Rayuela", "Frágil"}, f"{names}")
        check(f"clean {unit}: no dialogue_format finding",
              not any(f["rule"] == "dialogue_format" for f in clean))

    # Spanish name heuristics: places, institutions, brands and openers are not
    # people; a real new name is, wherever it stands.
    trap = _copy(tmp, "novela", fixed=True)
    _write(trap / "drafts/unit-03/humanized.md",
           "# 3. Trampas\n\n—Dale, vamos —dijo Mariana.\n\n"
           "Llegó el Lunes. Le dije: Vamos. Fuimos a Córdoba en marzo, al Banco Nación y a la "
           "Plaza San Martín, y después al Bar Roma.\n\n"
           "Tomás miraba un partido en YouTube y tomaba una Coca. Rezó un Padre Nuestro.\n\n"
           "Su tío vive en Treviso desde hace años.\n\n"
           "—Hola, Julián —dijo Rosa—. ¿Venís a comer?\n\n"
           "—No, Julián no viene —Mariana se rió.\n")
    out5 = tmp / "lf-trap.json"
    run("lint_fiction.py", ["--root", str(trap), "--unit", "unit-03", "--json", str(out5)])
    tf = _json(out5)["findings"]
    high = {f["subject"] for f in tf if f["rule"] == "unknown_name" and f["severity"] == "major"}
    check("heuristics: 'Julián' (mid-sentence) and the undeclared 'Treviso' (never lowercase, "
          "not a common word) are the high-confidence names", high == {"Julián", "Treviso"},
          f"high={high}")
    check("heuristics: Banco Nación / Plaza San Martín / Bar Roma / YouTube / una Coca / "
          "Córdoba / Padre / Lunes / Vamos / Rezó are not names",
          not high & {"Nación", "Martín", "Roma", "YouTube", "Coca", "Córdoba", "Padre",
                      "Lunes", "Vamos", "Dale", "Banco", "Plaza", "Bar", "Rezó", "Fuimos"},
          f"{high}")
    with open(trap / "bible/world.md", "a", encoding="utf-8", newline="\n") as fh:
        fh.write("- **Treviso**: donde vive el tío de Mariana.\n")
    run("lint_fiction.py", ["--root", str(trap), "--unit", "unit-03", "--json", str(out5)])
    high = {f["subject"] for f in _json(out5)["findings"]
            if f["rule"] == "unknown_name" and f["severity"] == "major"}
    check("a place declared in world.md is known: only 'Julián' remains", high == {"Julián"},
          f"high={high}")

    # item 1 — one sentence-initial mention is enough; common openers are not names.
    _write(trap / "drafts/unit-03/humanized.md",
           "# 3. La boleta\n\nRosa tocó el timbre. Mariana abrió.\n\n"
           "Gustavo no saludó. Tomás salió de la cocina.\n")
    run("lint_fiction.py", ["--root", str(trap), "--unit", "unit-03", "--json", str(out5)])
    g = [f for f in _json(out5)["findings"] if f.get("subject") == "Gustavo"]
    check("item 1: 'Gustavo no saludó.' (one sentence-initial mention) → major unknown_name",
          any(f["rule"] == "unknown_name" and f["severity"] == "major" for f in g), f"{g}")
    _write(trap / "drafts/unit-03/humanized.md",
           "# 3. Inicios\n\nNadie contestó. Afuera llovía. Todavía era temprano. Entonces sonó "
           "el timbre. Después, nada.\n\nSilencio. Caminando por el pasillo, Mariana contó las "
           "puertas. Quedarse era lo único. Pensó en la madre. Tenía frío. Rosa llegó tarde.\n\n"
           "Lentamente abrió el sobre. Volvieron a mirarse. Estaban cansados. Habían dormido "
           "poco.\n\n—Preguntale a ella —dijo Tomás—. Decime la verdad.\n\n—Pasen —dijo "
           "Mariana.\n")
    run("lint_fiction.py", ["--root", str(trap), "--unit", "unit-03", "--json", str(out5)])
    names = [f["subject"] for f in _json(out5)["findings"] if f["rule"] == "unknown_name"]
    check("item 1: sentence-initial common words and verb forms are not names", not names,
          f"{names}")
    _write(trap / "drafts/unit-03/humanized.md",
           "# 3. Trámites\n\nFirmo un papel. Cobro como monotributista. Tomás tardó.\n\n"
           "Mariana habló con Gustavo en la puerta.\n")
    run("lint_fiction.py", ["--root", str(trap), "--unit", "unit-03", "--json", str(out5)])
    high = {f["subject"] for f in _json(out5)["findings"]
            if f["rule"] == "unknown_name" and f["severity"] == "major"}
    check("item 1: 'Firmo un papel.' (verb before a determiner) is not a name; 'Cobro' is",
          "Firmo" not in high and "Cobro" in high, f"{high}")
    _write(trap / "bible/lexicon.yaml", "common_words: [cobro, gustavo]\n")
    run("lint_fiction.py", ["--root", str(trap), "--unit", "unit-03", "--json", str(out5)])
    high = {f["subject"] for f in _json(out5)["findings"]
            if f["rule"] == "unknown_name" and f["severity"] == "major"}
    check("an ordinary word declared in bible/lexicon.yaml → common_words stops blocking; a "
          "name put there is still caught mid-sentence", "Cobro" not in high and "Gustavo" in high,
          f"{high}")
    (trap / "bible/lexicon.yaml").unlink()

    work = _copy(tmp, "novela", fixed=True)
    shutil.copyfile(FIX / "novela-fixes/unit-03-final.md", work / "final/unit-03.md")
    out3 = tmp / "lf-book.json"
    run("lint_fiction.py", ["--root", str(work), "--book", "--json", str(out3)])
    book = _json(out3)
    ngrams = [f.get("subject") for f in book["findings"] if f["rule"] == "repeated_ngram"]
    check("book mode: a phrase in 3 units → repeated_ngram",
          any("ventilador hizo clic" in (g or "") for g in ngrams), f"{ngrams}")
    check("book mode on clean chapters: no major", not any(
        f["severity"] == "major" for f in book["findings"]),
        f"{[f for f in book['findings'] if f['severity'] == 'major']}")

    # English pack: a quote-dialogue project with a new name and an ornate tag.
    en = tmp / "s2-en"
    _write(en / "bible/meta.yaml", 'project: {profile: "book-literary", language: "en"}\n')
    _write(en / "bible/characters/anna.md", '---\nname: "Anna Weiss"\nslug: anna\n'
           'aliases: []\nrole: protagonist\n---\n')
    _write(en / "drafts/unit-01/humanized.md",
           '# One\n\n"Stay," Anna said. She looked at Bruno across the table.\n\n'
           '"No," Bruno hissed. On Monday she left for Paris.\n\n'
           'Slowly, she turned. Nobody answered. Outside, it rained. Finally the door opened. '
           'Walking home, Anna counted the lamps. Emily did not answer.\n')
    out4 = tmp / "lf-en.json"
    run("lint_fiction.py", ["--root", str(en), "--unit", "unit-01", "--json", str(out4)])
    en_f = _json(out4)["findings"]
    en_names = {f.get("subject") for f in en_f if f["rule"] == "unknown_name"}
    check("English: unknown 'Bruno' and sentence-initial 'Emily' reported, 'Monday' excluded, "
          "openers (Slowly, Nobody, Outside, Finally, Walking) are not names",
          {"Bruno", "Emily"} <= en_names and not en_names & {
              "Monday", "Slowly", "Nobody", "Outside", "Finally", "Walking"}, f"{en_names}")
    check("English: ornate 'hissed'", any(f["rule"] == "speech_verb_ornate" for f in en_f))


# ---------------------------------------------------------------------------
# check_story — R1–R4
# ---------------------------------------------------------------------------


def test_user_rule_ready(tmp: Path, check, run) -> None:
    print("\nR3 — `pipeline_step.py ready` gates drafting on characters and ending")
    work = _copy(tmp, "novela")
    code, log = run("pipeline_step.py", ["--root", str(work), "ready"])
    check("R3: ready FAILS while Rosa's sheet has TBD backstory/personality and no arc",
          code == 1 and "CHAR-INCOMPLETE rosa" in log, f"code {code}\n{log[-400:]}")

    shutil.copyfile(FIX / "novela-fixes/rosa.md", work / "bible/characters/rosa.md")
    code, log = run("pipeline_step.py", ["--root", str(work), "ready"])
    check("R3: ready PASSES when every character in the outline is complete and the ending "
          "exists", code == 0, log[-400:])

    plot = work / "bible/plot-structure.md"
    good = plot.read_text(encoding="utf-8")
    _write(plot, "# Plot structure\n\nThe ending: we'll see.\n")
    code, log = run("pipeline_step.py", ["--root", str(work), "ready"])
    check("R2/R3: ready FAILS without an ending", code == 1 and "ENDING-MISSING" in log,
          log[-300:])
    _write(plot, good.replace('final_unit: unit-03', 'final_unit: ""'))
    code, log = run("pipeline_step.py", ["--root", str(work), "ready"])
    check("R2: an empty ending.final_unit is a missing ending", code == 1 and "ENDING-MISSING" in log)
    _write(plot, good)

    sheet = work / "bible/characters/mariana.md"
    good_sheet = sheet.read_text(encoding="utf-8")
    _write(sheet, re.sub(r'personality: ".*"', 'personality: "TBD"', good_sheet))
    code, log = run("pipeline_step.py", ["--root", str(work), "ready"])
    check("R3: TBD personality on the protagonist blocks drafting",
          code == 1 and "CHAR-INCOMPLETE mariana" in log, log[-300:])
    _write(sheet, good_sheet.replace('signed_on: "2026-09-20"\n', ""))
    code, log = run("pipeline_step.py", ["--root", str(work), "ready"])
    check("item 16: `status: complete` without `signed_on` is not signed → CHAR-INCOMPLETE",
          code == 1 and "CHAR-INCOMPLETE mariana" in log and "signed_on" in log, log[-300:])
    _write(sheet, good_sheet)

    tomas = work / "bible/characters/tomas.md"
    text = tomas.read_text(encoding="utf-8")
    _write(tomas, re.sub(r"arc:\n(?:  .*\n)+", "", text))
    code, log = run("pipeline_step.py", ["--root", str(work), "ready"])
    check("R1: a character without an arc → CHAR-NO-ARC", code == 1 and "CHAR-NO-ARC tomas" in log,
          log[-300:])
    _write(tomas, text)
    code, _ = run("pipeline_step.py", ["--root", str(work), "ready"])
    check("…and passes again once restored", code == 0)

    status = work / "project-status.yaml"
    _edit(status, "approved: true", "approved: false")
    code, log = run("pipeline_step.py", ["--root", str(work), "ready"])
    check("an unapproved outline blocks drafting", code == 1 and "OUTLINE-NOT-APPROVED" in log)

    tech = _copy(tmp, "tecnico")
    code, log = run("pipeline_step.py", ["--root", str(tech), "ready"])
    check("nonfiction: approved outline + signed KG → ready", code == 0, log[-300:])
    _edit(tech / "bible/knowledge-graph.yaml", "every_concept_assigned_to_unit: true",
          "every_concept_assigned_to_unit: false")
    code, log = run("pipeline_step.py", ["--root", str(tech), "ready"])
    check("nonfiction: KG not assigned to units → not ready", code == 1 and "KG-UNASSIGNED" in log)


GUS_ONCE = ("# 3. La boleta\n\n<!-- SCENE s1 -->\nRosa tocó el timbre a las tres de la tarde. "
            "Mariana abrió la puerta con la libreta todavía en la mano.\n\n—Traje algo que era "
            "de tu mamá —dijo Rosa.\n\nTraía un sobre de papel madera. Atrás, en la vereda, "
            "esperaba el hijo del agenciero con las manos en los bolsillos.\n\nGustavo no "
            "saludó. Tomás salió de la cocina secándose las manos en el pantalón.\n\n"
            "Mariana guardó la boleta en la libreta de tapas verdes.\n")


def test_user_rule_new_character(tmp: Path, check, run) -> None:
    print("\nR4 — a new name on the page blocks the unit")
    work = _copy(tmp, "novela", fixed=True)
    ps = _ps(run, work)
    out = tmp / "story-unit.json"
    code, log = run("check_story.py", ["--root", str(work), "--unit", "unit-03", "--json", str(out)])
    f = _json(out)["findings"]
    check("R4: draft naming 'Gustavo' → NEW-CHARACTER blocking, exit 1",
          code == 1 and any(x["code"] == "NEW-CHARACTER" and x["subject"] == "Gustavo"
                            and x["severity"] == "blocking" for x in f), f"code {code}; {f}")
    check("R4: the typo 'Tomas' is not a new character",
          not any(x["code"] == "NEW-CHARACTER" and x["subject"] == "Tomas" for x in f))

    code, log = run("check_story.py", ["--root", str(work), "--unit", "unit-01", "--file",
                                       "final/unit-01.md"])
    check("clean chapter: no blocking NEW-CHARACTER, exit 0",
          code == 0 and "[blocking] NEW-CHARACTER" not in log, log[-300:])

    code, log = ps("checks", "unit-03")
    check("R4: `pipeline_step.py checks` pauses the unit (exit 3) before the Critic",
          code == 3 and "NEW-CHARACTER" in log, f"code {code}")
    code, log = _step(ps, "unit-03", "writer", lambda: shutil.copyfile(
        work / "drafts/unit-03/humanized.md", work / "drafts/unit-03/draft.md"), tier="creative")
    check("R4: `done writer` pauses right after the Writer (exit 3)",
          code == 3 and "questionnaire" in log, f"code {code}")

    # item 1 — ONE sentence-initial mention, the adversarial review's repro.
    one = _copy(tmp, "novela", fixed=True)
    ps1 = _ps(run, one)
    code, log = _step(ps1, "unit-03", "writer",
                      lambda: _write(one / "drafts/unit-03/draft.md", GUS_ONCE), tier="creative")
    check("item 1: 'Gustavo no saludó.' (one sentence-initial mention) → `done writer` exit 3",
          code == 3 and "NEW-CHARACTER Gustavo" in log, f"code {code}\n{log[-400:]}")
    out1 = tmp / "story-gus-once.json"
    code, _ = run("check_story.py", ["--root", str(one), "--unit", "unit-03", "--file",
                                     "drafts/unit-03/draft.md", "--json", str(out1)])
    check("item 1: …and check_story --unit reports it blocking, exit 1",
          code == 1 and any(x["code"] == "NEW-CHARACTER" and x["severity"] == "blocking"
                            and x["subject"] == "Gustavo" for x in _json(out1)["findings"]))
    _write(one / "drafts/unit-03/draft.md",
           "# 3. Inicios\n\nNadie contestó. Afuera llovía. Todavía era temprano. Entonces sonó "
           "el timbre. Después, nada. Silencio. Rosa llegó tarde.\n\n—Pasen —dijo Mariana.\n")
    code, log = run("check_story.py", ["--root", str(one), "--unit", "unit-03", "--file",
                                       "drafts/unit-03/draft.md"])
    check("item 1: sentence-initial common words (Nadie, Afuera, Todavía, Entonces, Después, "
          "Silencio, Pasen) do not block", code == 0 and "NEW-CHARACTER" not in log, log[-300:])

    shutil.copyfile(FIX / "novela-fixes/gustavo.md", work / "bible/characters/gustavo.md")
    code, log = run("check_story.py", ["--root", str(work), "--unit", "unit-03"])
    check("R4: once the questionnaire produced Gustavo's sheet, the unit is unblocked",
          code == 0 and "NEW-CHARACTER" not in log, log[-400:])

    work2 = _copy(tmp, "novela", fixed=True)
    code, log = run("pipeline_step.py", ["--root", str(work2), "check", "unit-03", "writer"])
    check("the Writer check reads outline and sheets, not the old draft", code == 0, log[-300:])
    _edit(work2 / "outline/units.yaml", "characters_present: [mariana, tomas, rosa]",
          "characters_present: [mariana, tomas, rosa, julian]")
    code, log = run("pipeline_step.py", ["--root", str(work2), "check", "unit-03", "writer"])
    check("R4: the outline gains a name without a sheet → the Writer may not start",
          code == 1 and "CHAR-UNKNOWN julian" in log, log[-300:])
    work3 = _copy(tmp, "novela", fixed=True)
    _edit(work3 / "outline/units.yaml", 'summary: "Rosa trae la última boleta; Mariana decide '
          'quedarse."', 'summary: "Rosa trae la última boleta. Gustavo espera en la vereda."')
    code, log = run("pipeline_step.py", ["--root", str(work3), "check", "unit-03", "writer"])
    check("item 2: a scene card gains a name (summary) → CHAR-UNKNOWN, the Writer may not start",
          code == 1 and "CHAR-UNKNOWN Gustavo" in log, log[-300:])
    code, log = run("pipeline_step.py", ["--root", str(work3), "ready"])
    check("item 2: …and `ready` fails on it", code == 1 and "CHAR-UNKNOWN Gustavo" in log,
          log[-300:])
    # Planning shorthand is not a cast list: a card that opens with a noun-shaped
    # word, or names a place after a locative preposition, must not block.
    work4 = _copy(tmp, "novela", fixed=True)
    _edit(work4 / "outline/units.yaml", 'summary: "Rosa trae la última boleta; Mariana decide '
          'quedarse."', 'summary: "Llamada con Mariana. Rosa espera en Diagonal."')
    code, log = run("pipeline_step.py", ["ready", "--root", str(work4)])
    check("card shorthand: a noun-shaped opener and a place after 'en' do not block `ready` "
          "(and --root works after the subcommand)",
          code == 0 and "CHAR-UNKNOWN Llamada" not in log
          and "✗ CHAR-UNKNOWN Diagonal" not in log, log[-400:])


def test_mentioned_only_names(tmp: Path, check, run) -> None:
    print("\nR4 — world.md holds mentioned-only names; a name that speaks or acts is a character")
    work = _copy(tmp, "novela", fixed=True)
    with open(work / "bible/world.md", "a", encoding="utf-8", newline="\n") as fh:
        fh.write("\n## Names\n\n- Gustavo — el hijo del agenciero, sólo mencionado.\n")
    out = tmp / "promote.json"
    code, log = run("check_story.py", ["--root", str(work), "--unit", "unit-03", "--json", str(out)])
    f = _json(out)["findings"]
    check("item 2: a world.md § Names name that SPEAKS (—dijo Gustavo—) → EXTRA-PROMOTE "
          "blocking, exit 1",
          code == 1 and any(x["code"] == "EXTRA-PROMOTE" and x["subject"] == "Gustavo"
                            and x["severity"] == "blocking" for x in f), f"{f}")
    out2 = tmp / "promote-lf.json"
    run("lint_fiction.py", ["--root", str(work), "--unit", "unit-03", "--json", str(out2)])
    lf = _json(out2)["findings"]
    check("item 2: lint_fiction reports mentioned_on_stage (major), not a silent 'known'",
          any(x["rule"] == "mentioned_on_stage" and x.get("subject") == "Gustavo"
              and x["severity"] == "major" for x in lf), f"{lf}")
    code, log = run("pipeline_step.py", ["--root", str(work), "checks", "unit-03"])
    check("item 2: `checks` pauses the unit (exit 3)", code == 3 and "EXTRA-PROMOTE" in log,
          log[-300:])

    h = work / "drafts/unit-03/humanized.md"
    _write(h, "# 3. La boleta\n\n" + CLEAN_U3.split("\n", 2)[2]
           + "\nRosa habló de Gustavo, el hijo del agenciero, que nunca venía a la casa.\n")
    code, log = run("check_story.py", ["--root", str(work), "--unit", "unit-03"])
    check("item 2: a mentioned-only name that is only mentioned does not block",
          code == 0 and "EXTRA-PROMOTE" not in log and "NEW-CHARACTER" not in log, log[-300:])
    _write(h, "# 3. La boleta\n\n" + CLEAN_U3.split("\n", 2)[2] + "\nGustavo no saludó.\n")
    out3 = tmp / "promote-one.json"
    code, log = run("check_story.py", ["--root", str(work), "--unit", "unit-03", "--json", str(out3)])
    check("fix2 item 3: a world.md name ACTING on stage, even in one unit, is EXTRA-PROMOTE "
          "blocking (a figure on stage is a character)",
          code == 1 and any(x["code"] == "EXTRA-PROMOTE" and x["severity"] == "blocking"
                            for x in _json(out3)["findings"]), log[-300:])
    with open(work / "final/unit-02.md", "a", encoding="utf-8", newline="\n") as fh:
        fh.write("\nGustavo cerró la puerta del auto sin mirar a nadie.\n")
    code, log = run("check_story.py", ["--root", str(work), "--unit", "unit-03"])
    check("item 2: acting as the subject of a scene in 2 units → EXTRA-PROMOTE blocking",
          code == 1 and "EXTRA-PROMOTE" in log and "2 units" in log, log[-300:])
    code, log = run("check_story.py", ["--root", str(work), "--manuscript"])
    check("item 2: the manuscript check (MG-S) sees it too", code == 1 and "EXTRA-PROMOTE" in log,
          log[-300:])

    card = _copy(tmp, "novela", fixed=True)
    with open(card / "bible/world.md", "a", encoding="utf-8", newline="\n") as fh:
        fh.write("\n## Names\n\n- Gustavo — el hijo del agenciero, sólo mencionado.\n")
    _edit(card / "outline/units.yaml", 'pivot: "Rosa entrega la boleta."',
          'pivot: "Rosa entrega la boleta que le dio Gustavo."')
    code, log = run("pipeline_step.py", ["--root", str(card), "ready"])
    check("item 2: a mentioned-only name in an outline card (pivot) → CHAR-UNKNOWN in ready",
          code == 1 and "CHAR-UNKNOWN Gustavo" in log and "mentioned-only" in log, log[-300:])


def test_check_story_codes(tmp: Path, check, run) -> None:
    print("\ncheck_story — design codes")
    work = _copy(tmp, "novela", fixed=True)

    def codes(args):
        out = tmp / f"story-{_counter[0]}-{len(args)}.json"
        _counter[0] += 1
        code, _ = run("check_story.py", ["--root", str(work), *args, "--json", str(out)])
        data = _json(out)
        return code, {(x["code"], x["severity"], x["subject"]) for x in data["findings"]}

    code, found = codes(["--ready-to-draft"])
    check("complete fixture: no finding at ready-to-draft", code == 0 and not found, f"{found}")

    extras = work / "bible/characters/_extras.md"
    _edit(extras, "units: [unit-02]", "units: [unit-01, unit-02]")
    _, found = codes(["--ready-to-draft"])
    check("a recurring extra → EXTRA-PROMOTE", ("EXTRA-PROMOTE", "blocking", "mozo del bar") in found)
    _edit(extras, "units: [unit-01, unit-02]", "units: [unit-02]")
    _edit(extras, 'label: "chofer del 115"', 'label: "Don Pedro"')
    _, found = codes(["--ready-to-draft"])
    check("a named extra → EXTRA-PROMOTE", ("EXTRA-PROMOTE", "blocking", "Don Pedro") in found)
    _edit(extras, 'label: "Don Pedro"', 'label: "chofer del 115"')

    plot = work / "bible/plot-structure.md"
    _edit(plot, "final_unit: unit-03", "final_unit: unit-02")
    _, found = codes(["--ready-to-draft"])
    check("an arc resolving after the ending → ARC-AFTER-ENDING",
          ("ARC-AFTER-ENDING", "blocking", "mariana") in found, f"{found}")
    check("item 10: a ledger payoff after the ending → LEDGER-NO-PAYOFF, blocking at ready",
          ("LEDGER-NO-PAYOFF", "blocking", "F01") in found, f"{found}")
    _edit(plot, "final_unit: unit-02", "final_unit: unit-03")

    ledger = work / "bible/story-ledger.yaml"
    _edit(ledger, "payoff_unit: unit-03", "payoff_unit: null")
    code, found = codes(["--ready-to-draft"])
    check("item 10: an open plant without a planned payoff → LEDGER-NO-PAYOFF blocking, exit 1",
          code == 1 and ("LEDGER-NO-PAYOFF", "blocking", "F01") in found, f"{found}")
    code, log = run("pipeline_step.py", ["--root", str(work), "ready"])
    check("item 10: …and `pipeline_step.py ready` refuses", code == 1 and "LEDGER-NO-PAYOFF" in log)
    _edit(ledger, "payoff_unit: null", "payoff_unit: unit-03")

    outline = work / "outline/units.yaml"
    _edit(outline, "ledger: {plants: [], pays: [F02]}", "ledger: {plants: [], pays: [F99]}")
    code, found = codes(["--ready-to-draft"])
    check("item 10: a card citing ledger id F99, which the ledger lacks → LEDGER-UNKNOWN blocking",
          code == 1 and ("LEDGER-UNKNOWN", "blocking", "F99") in found, f"{found}")
    _edit(outline, "pays: [F99]", "pays: [F02]")
    _edit(outline, "- {character: mariana, turning_point: 1}",
          "- {character: mariana, turning_point: 2}")
    code, found = codes(["--ready-to-draft"])
    check("item 10: arc_moves pointing at a turning point the sheet does not place → "
          "CHAR-ARC-OUT-OF-OUTLINE blocking at ready",
          code == 1 and ("CHAR-ARC-OUT-OF-OUTLINE", "blocking", "mariana") in found, f"{found}")
    code, log = run("pipeline_step.py", ["--root", str(work), "ready"])
    check("item 10: …and `ready` refuses", code == 1 and "CHAR-ARC-OUT-OF-OUTLINE" in log)
    _edit(outline, "- {character: mariana, turning_point: 2}",
          "- {character: mariana, turning_point: 1}")

    _edit(work / "bible/style-guide.md", "calibration-source: human", "calibration-source: model")
    meta = work / "bible/meta.yaml"
    _edit(meta, '      - "el olor a naftalina del placard del pasillo"\n', "")
    _, found = codes(["--ready-to-draft"])
    check("no human calibration passage → CALIBRATION-NO-HUMAN",
          ("CALIBRATION-NO-HUMAN", "blocking", "style-guide") in found)
    check("fewer seeds than min_seeds → SEEDS-MISSING",
          ("SEEDS-MISSING", "blocking", "literary.seeds") in found)

    work2 = _copy(tmp, "novela", fixed=True)
    out = tmp / "story-ms.json"
    code, _ = run("check_story.py", ["--root", str(work2), "--manuscript", "--json", str(out)])
    ms = {(x["code"], x["subject"]) for x in _json(out)["findings"]}
    check("manuscript without the final unit → ENDING-NOT-DELIVERED, exit 1",
          code == 1 and ("ENDING-NOT-DELIVERED", "ending") in ms, f"{ms}")
    check("manuscript: arcs resolving in the missing unit → ARC-NOT-RESOLVED",
          ("ARC-NOT-RESOLVED", "mariana") in ms)
    check("manuscript: an open plant → LEDGER-OPEN", ("LEDGER-OPEN", "F01") in ms)
    shutil.copyfile(FIX / "novela-fixes/unit-03-final.md", work2 / "final/unit-03.md")
    _edit(work2 / "bible/story-ledger.yaml", "status: open\n    paid_in: null",
          "status: paid\n    paid_in: unit-03")
    out2 = tmp / "story-ms-clean.json"
    code, log = run("check_story.py", ["--root", str(work2), "--manuscript", "--json", str(out2)])
    ms_clean = _json(out2)["findings"]
    check("complete manuscript: exit 0, nothing blocking or major (only the low-confidence "
          "notes on the italic title *Rayuela* and the box label FRÁGIL)",
          code == 0 and all(x["severity"] == "warning" for x in ms_clean)
          and {x["subject"] for x in ms_clean} <= {"Rayuela", "Frágil"}, f"{ms_clean}")

    code, log = run("check_story.py", ["--root", str(FIX / "tecnico"), "--ready-to-draft"])
    check("nonfiction project: check_story is n/a, exit 0", code == 0 and "n/a" in log)


# ---------------------------------------------------------------------------
# pipeline_step
# ---------------------------------------------------------------------------


def test_pipeline_step(tmp: Path, check, run) -> None:
    print("\npipeline_step — brackets, dispatch records, clean text, snapshots, checks, edits")
    work = _copy(tmp, "novela", fixed=True)
    d = work / "drafts/unit-03"
    ps = _ps(run, work)

    code, log = ps("check", "unit-03", "editor")
    check("check: missing input → exit 1 and names it", code == 1 and "draft.md: missing" in log,
          log[-300:])
    shutil.copyfile(d / "humanized.md", d / "draft.md")
    code, _ = ps("check", "unit-03", "editor")
    check("check: inputs present → exit 0, dispatch recorded",
          code == 0 and "editor" in _json(d / ".dispatch.json")["agents"])

    _write(d / "edit.md", "null\n")
    code, log = ps("done", "unit-03", "editor", "--tier", "audit", "--cycle", "1")
    check("done: a `null` output → exit 1 (re-dispatch)", code == 1 and "null" in log)
    check("done: a failed run is not logged", not (work / "runs.tsv").exists())
    shutil.copyfile(d / "draft.md", d / "edit.md")
    code, log = ps("done", "unit-03", "editor", "--tier", "audit", "--cycle", "1")
    runs = (work / "runs.tsv").read_text(encoding="utf-8").splitlines()
    check("done: ok → runs.tsv header + one 6-column line",
          code == 0 and runs[0].startswith("unit\tagent") and len(runs) == 2
          and len(runs[1].split("\t")) == 6, f"{runs}")
    rd = d / "role-diff-editor-c1.json"
    check("done editor: role diff recorded", rd.exists() and not _json(rd)["violations"])

    code, log = ps("done", "unit-03", "humanizer", "--tier", "creative", "--cycle", "1")
    check("item 7: done without a prior `check` (no dispatch record) → exit 1",
          code == 1 and "no dispatch record" in log, log[-300:])
    ps("check", "unit-03", "humanizer")
    _backdate(d / "humanized.md")
    code, log = ps("done", "unit-03", "humanizer", "--tier", "creative", "--cycle", "1")
    check("item 7: an output not written after the dispatch (stale) → exit 1",
          code == 1 and "stale" in log, log[-300:])
    _write(d / "humanized.md", (d / "draft.md").read_text(encoding="utf-8")
           + "\n```html\n<!-- inside code: keep -->\n```\n<!-- EDITOR: leak\nsecond line -->\n")
    code, log = ps("done", "unit-03", "humanizer", "--tier", "creative", "--cycle", "1")
    check("done humanizer: fresh output → exit 0, clean copy refreshed",
          code == 0 and "clean copy refreshed" in log, log[-300:])
    clean = (d / "humanized.clean.md").read_text(encoding="utf-8")
    check("clean: HTML comments gone (multi-line too), code-fence comment kept",
          "EDITOR" not in clean and "SCENE" not in clean and "inside code: keep" in clean)
    (d / "humanized.clean.md").unlink()
    code, _ = ps("check", "unit-03", "reader_pov")
    check("check reader_pov: no clean copy → exit 1", code == 1)
    ps("clean", "unit-03")
    code, _ = ps("check", "unit-03", "reader_pov")
    check("check reader_pov: fresh clean copy → exit 0", code == 0)
    _touch_later(d / "humanized.md", d / "humanized.clean.md")
    code, log = ps("check", "unit-03", "reader_pov")
    check("check reader_pov: stale clean copy → exit 1", code == 1 and "stale" in log)

    code, log = ps("checks", "unit-03")
    cj = d / "checks.json"
    data = _json(cj) if cj.exists() else {}
    check("checks (literary): checks.json + checks.md written",
          cj.exists() and (d / "checks.md").exists())
    check("checks: counts copied from count_rhet (rhet-2 = 2)",
          (data.get("counts") or {}).get("rhet-2", {}).get("count") == 2)
    check("checks: latest role diffs collected",
          set(data.get("role_diff", {})) >= {"editor", "humanizer"})
    check("checks: story blocker → exit 3", code == 3 and data.get("blocking"), f"code {code}")
    check("checks: fiction lint included",
          any(f["rule"] == "gesture_tic" for f in (data.get("fiction") or {}).get("findings", [])))
    code, log = ps("check", "unit-03", "critic")
    check("check critic: missing reader-report/coherence → exit 1", code == 1)
    code, log = ps("check", "unit-03", "technical_reviewer")
    check("check: an agent with no slot in the profile → exit 1",
          code == 1 and "no slot" in log, log[-200:])

    code, log = ps("snapshot", "unit-03")
    check("snapshot needs --reason (critic|tr|adversarial|human)", code == 2, log[-200:])

    tech = _copy(tmp, "tecnico")
    code, log = run("pipeline_step.py", ["--root", str(tech), "checks", "unit-01"])
    tj = _json(tech / "drafts/unit-01/checks.json")
    check("checks (nonfiction): exit 0 and identifiers.unknown carries GroupConcat",
          code == 0 and any(e["identifier"] == "GroupConcat" for e in tj["identifiers"]["unknown"]),
          log[-300:])
    check("checks (nonfiction): rhet counts present", tj["counts"]["rhet-1"]["count"] == 3)

    edits = work / "edits.yaml"
    _write(edits, '- {unit: unit-01, find: "Nadie se rió.", replace: "Nadie dijo nada.", '
                  'rule: gesture_tic}\n'
                  '- {unit: 2, find: "Tomás se rió, y esta vez sí tenía ganas.", '
                  'replace: "Tomás largó una carcajada corta.", rule: gesture_tic}\n')
    before = (work / "final/unit-01.md").read_text(encoding="utf-8")
    code, _ = ps("apply-edits", "edits.yaml", "--dry-run")
    check("apply-edits --dry-run: ok and nothing written (path relative to the root)",
          code == 0 and (work / "final/unit-01.md").read_text(encoding="utf-8") == before)
    code, _ = ps("apply-edits", str(edits))
    check("apply-edits: both anchors applied",
          code == 0 and "Nadie dijo nada." in (work / "final/unit-01.md").read_text(encoding="utf-8")
          and "carcajada corta" in (work / "final/unit-02.md").read_text(encoding="utf-8"))
    bad = tmp / "bad-edits.yaml"
    _write(bad, 'edits:\n  - {unit: unit-01, find: "Nadie dijo nada.", replace: "X", rule: a}\n'
                '  - {unit: unit-01, find: "Mariana", replace: "M.", rule: b}\n')
    snap = (work / "final/unit-01.md").read_text(encoding="utf-8")
    code, log = ps("apply-edits", str(bad))
    check("apply-edits: an ambiguous find fails the whole batch, nothing written",
          code == 1 and (work / "final/unit-01.md").read_text(encoding="utf-8") == snap
          and "matches" in log, log[-300:])


def test_story_blocks_never_overridable(tmp: Path, check, run) -> None:
    print("\nitem 3 — R1–R4 blocks survive every override: Critic, human override, approve --force")
    work = _copy(tmp, "novela", fixed=True)
    d = work / "drafts/unit-03"
    ps = _ps(run, work)
    gus = (FIX / "novela/drafts/unit-03/humanized.md").read_text(encoding="utf-8")
    # An orchestrator that ignores the R4 pause and pushes on:
    _literary_to_critic(ps, d, gus.split("\n", 2)[2])
    code, log = ps("check", "unit-03", "critic")
    check("item 3: `check critic` is NOT READY while checks.json → blocking holds a story block",
          code == 1 and "story block" in log and "NEW-CHARACTER" in log, log[-400:])
    _write(d / "scorecard.yaml", _scorecard(PASS_ROWS, "PASS", None))
    _write(d / "critique.md", _critique("PASS", "none"))
    _write(d / "human-notes.md", "2026-09-25 human approves over the red scorecard\n")
    code, log = ps("check", "unit-03", "proofreader", "--human-override")
    check("item 3: `check proofreader --human-override` refuses a story block",
          code == 1 and "never overridable" in log, log[-400:])
    _write(d / "proofread.md", (d / "humanized.md").read_text(encoding="utf-8"))
    _touch_later(d / "proofread.md", d / "humanized.md")
    code, log = ps("approve", "unit-03", "--force")
    check("item 3: `approve --force` refuses a story block on the text that would ship",
          code == 1 and "never overridable" in log and not (work / "final/unit-03.md").exists(),
          log[-400:])

    # The same unit with a red scorecard but no story block: the human may override.
    ok = _copy(tmp, "novela", fixed=True)
    d2 = ok / "drafts/unit-03"
    ps2 = _ps(run, ok)
    _literary_to_critic(ps2, d2, CLEAN_U3.split("\n", 2)[2])
    rows = [("beats-1", "critical", "pass", None), ("voice-2", "significant", "fail", "Humanizer")]
    code, log = _critic(ps2, d2, rows, "REVISE", "Humanizer")
    check("a consistent REVISE critique is accepted (done critic exit 0)", code == 0, log[-300:])
    code, log = ps2("check", "unit-03", "proofreader")
    check("check proofreader on a REVISE scorecard → exit 1", code == 1 and "not PASS" in log,
          log[-300:])
    code, log = ps2("check", "unit-03", "proofreader", "--human-override")
    check("…--human-override over a red scorecard (no story block) → exit 0, noted",
          code == 0 and "human override" in log, log[-300:])


def test_role_laundering(tmp: Path, check, run) -> None:
    print("\nitem 6/8 — a Writer REVISE never starts from a role-contract violator's text")
    work = _copy(tmp, "novela", fixed=True)
    d = work / "drafts/unit-03"
    ps = _ps(run, work)
    body = "<!-- SCENE s1 -->\n" + CLEAN_U3.split("\n", 2)[2]
    heavy = body.replace(".", " sin apuro.")
    _step(ps, "unit-03", "writer", lambda: _write(d / "draft.md", body), tier="creative")
    _step(ps, "unit-03", "editor", lambda: _write(d / "edit.md", body))
    code, log = _step(ps, "unit-03", "humanizer", lambda: _write(d / "humanized.md", heavy))
    check("the Humanizer over its 3% budget is recorded (done exit 0, over_budget)",
          code == 0 and _json(d / "role-diff-humanizer-c1.json")["over_budget"], log[-300:])
    _step(ps, "unit-03", "reader_pov", lambda: _write(d / "reader-report.md", "# R\n\nok\n"))
    _step(ps, "unit-03", "continuity_a", lambda: _write(d / "coherence.md", "# C\n\nok\n"))
    ps("checks", "unit-03")
    rows = [("beats-1", "critical", "pass", None), ("voice-6", "significant", "fail", "Writer")]
    _critic(ps, d, rows, "REVISE", "Writer")
    code, log = ps("snapshot", "unit-03", "--reason", "critic")
    loop = _json(d / "loop-state.json")["cycles"]["2"]
    check("item 6: snapshot also keeps draft.c1.md and edit.c1.md",
          code == 0 and (d / "draft.c1.md").exists() and (d / "edit.c1.md").exists()
          and (d / "humanized.c1.md").exists(), log[-300:])
    check("item 6: voice-6 (Humanizer over budget) → the Writer's REVISE source is edit.c1.md, "
          "not the Humanizer's rewrite", loop["writer_source"] == "drafts/unit-03/edit.c1.md",
          f"{loop}")
    code, log = ps("check", "unit-03", "writer", "--cycle", "2")
    check("item 6: `check writer --cycle 2` verifies and names that source",
          code == 0 and "Writer REVISE input: drafts/unit-03/edit.c1.md" in log, log[-300:])
    check("item 6: …and records the check in the loop state",
          bool(_json(d / "loop-state.json")["cycles"]["2"].get("writer_source_checked_utc")))
    (d / "edit.c1.md").unlink()
    code, log = ps("check", "unit-03", "writer", "--cycle", "2")
    check("item 6: a missing REVISE source → the Writer may not start", code == 1, log[-300:])

    ed = _copy(tmp, "novela", fixed=True)
    d2 = ed / "drafts/unit-03"
    ps2 = _ps(run, ed)
    _step(ps2, "unit-03", "writer", lambda: _write(d2 / "draft.md", body), tier="creative")
    padded = body + ("\nMariana pensó en todo lo que había pasado en esa casa, en los veranos "
                     "largos, en las siestas, en la voz de su madre llamándola desde la cocina "
                     "para tomar la leche con pan y manteca.\n")
    code, log = _step(ps2, "unit-03", "editor", lambda: _write(d2 / "edit.md", padded))
    check("item 8: an Editor that adds prose → `done editor` exit 4, re-dispatch once",
          code == 4 and "re-dispatch" in log, log[-300:])
    code, log = _step(ps2, "unit-03", "editor", lambda: _write(d2 / "edit.md", padded + "\n"))
    check("item 8: a second violation in the same cycle → exit 4 and ESCALATE",
          code == 4 and "ESCALATE" in log, log[-300:])
    _step(ps2, "unit-03", "humanizer", lambda: _write(d2 / "humanized.md", padded))
    _step(ps2, "unit-03", "reader_pov", lambda: _write(d2 / "reader-report.md", "# R\n\nok\n"))
    _step(ps2, "unit-03", "continuity_a", lambda: _write(d2 / "coherence.md", "# C\n\nok\n"))
    ps2("checks", "unit-03")
    rows = [("beats-1", "critical", "fail", "Writer")]
    _critic(ps2, d2, rows, "REVISE", "Writer")
    ps2("snapshot", "unit-03", "--reason", "critic")
    loop = _json(d2 / "loop-state.json")["cycles"]["2"]
    check("item 6: after an Editor violation the Writer revises draft.c1.md (the text before "
          "the Editor)", loop["writer_source"] == "drafts/unit-03/draft.c1.md", f"{loop}")


def test_tr_revise_walk(tmp: Path, check, run) -> None:
    print("\nitem 9 — the Technical Reviewer REVISE sequence, walked literally (nonfiction)")
    tech = _copy(tmp, "tecnico")
    d = tech / "drafts/unit-01"
    shutil.rmtree(d)
    ps = _ps(run, tech)
    good = (FIX / "tecnico/final/unit-01.md").read_text(encoding="utf-8")
    code, _ = _step(ps, "unit-01", "writer", lambda: (
        _write(d / "draft.md", good), _write(d / "grounding-notes.md", "- Concat: §2\n")),
        tier="creative")
    check("writer c1 done", code == 0)
    code, _ = _step(ps, "unit-01", "technical_reviewer",
                    lambda: _write(d / "tech-review.md", "## Verdict: REVISE\n\n- §2 is wrong\n"))
    check("technical reviewer c1 done (REVISE)", code == 0)
    code, log = ps("snapshot", "unit-01", "--reason", "tr")
    check("item 9: snapshot works before humanized.md exists (exit 0, with a note)",
          code == 0 and "no humanized.md yet" in log and (d / "draft.c1.md").exists(), log[-300:])
    code, log = ps("check", "unit-01", "writer", "--cycle", "2")
    check("item 9: check writer --cycle 2 → exit 0, input draft.c1.md, worklist tech-review.md",
          code == 0 and "drafts/unit-01/draft.c1.md" in log, log[-300:])
    _write(d / "draft.md", good.replace("Concat", "Concat ", 1))
    _write(d / "grounding-notes.md", "- Concat: §2 (fixed)\n")
    code, log = ps("done", "unit-01", "writer", "--tier", "creative", "--cycle", "2")
    check("item 9: done writer --cycle 2", code == 0, log[-300:])
    code, log = _step(ps, "unit-01", "technical_reviewer",
                      lambda: _write(d / "tech-review.md", "## Verdict: PASS\n"), cycle=2)
    check("item 9: technical reviewer c2", code == 0, log[-300:])
    code, log = ps("check", "unit-01", "editor", "--cycle", "2")
    check("item 9: check editor --cycle 2 does not demand humanized.md (first pass after a "
          "Writer loop)", code == 0 and "humanized.md" not in log, log[-300:])
    _write(d / "edit.md", (d / "draft.md").read_text(encoding="utf-8"))
    code, log = ps("done", "unit-01", "editor", "--tier", "audit", "--cycle", "2")
    rd = _json(d / "role-diff-editor-c2.json")
    check("item 9: done editor --cycle 2 diffs draft.md → edit.md",
          code == 0 and rd["before"].endswith("draft.md") and rd["after"].endswith("edit.md"),
          log[-300:])
    code, log = _step(ps, "unit-01", "humanizer",
                      lambda: _write(d / "humanized.md", (d / "edit.md").read_text("utf-8")),
                      cycle=2, tier="creative")
    rh = _json(d / "role-diff-humanizer-c2.json")
    check("item 9: humanizer c2 is a first pass (edit.md → humanized.md)",
          code == 0 and rh["before"].endswith("edit.md"), log[-300:])


def test_worklist_and_freshness(tmp: Path, check, run) -> None:
    print("\nitems 7/11 — fresh reports, fresh worklists")
    work = _copy(tmp, "novela", fixed=True)
    d = work / "drafts/unit-03"
    ps = _ps(run, work)
    _literary_to_critic(ps, d, CLEAN_U3.split("\n", 2)[2])
    _backdate(d / "coherence.md")          # humanized.md changed after CG A and Reader-POV
    _backdate(d / "reader-report.md")
    code, log = ps("check", "unit-03", "critic")
    check("item 7: check critic refuses a coherence.md older than humanized.md",
          code == 1 and "coherence.md: stale" in log and "reader-report.md: stale" in log,
          log[-400:])
    _step(ps, "unit-03", "reader_pov", lambda: _write(d / "reader-report.md", "# R\n\nok\n"))
    _step(ps, "unit-03", "continuity_a", lambda: _write(d / "coherence.md", "# C\n\nok\n"))
    rows = [("beats-1", "critical", "pass", None), ("voice-2", "significant", "fail", "Humanizer")]
    ps("check", "unit-03", "critic")
    _write(d / "scorecard.yaml", _scorecard(rows, "REVISE", "Humanizer"))
    _write(d / "critique.md", _critique("REVISE", "Humanizer"))
    _backdate(d / "critique.md")
    code, log = ps("done", "unit-03", "critic", "--tier", "creative", "--cycle", "1")
    check("item 7: a critique not written after the dispatch (stale) → done exit 1",
          code == 1 and "critique.md: stale" in log, log[-300:])
    _write(d / "critique.md", _critique("REVISE", "Humanizer"))
    code, log = ps("done", "unit-03", "critic", "--tier", "creative", "--cycle", "1")
    check("done critic with a fresh, consistent critique → exit 0", code == 0, log[-300:])

    code, log = ps("snapshot", "unit-03", "--reason", "critic")
    check("item 11: snapshot --reason critic opens cycle 2 targeted at the Humanizer",
          code == 0 and _json(d / "loop-state.json")["cycles"]["2"]["target"] == "humanizer",
          log[-300:])
    code, log = ps("snapshot", "unit-03", "--reason", "critic")
    check("a second snapshot of the same cycle is refused", code == 2, log[-200:])
    crit = d / "critique.md"
    saved = crit.stat()
    _backdate(crit, 3600)
    code, log = ps("check", "unit-03", "humanizer", "--cycle", "2")
    check("item 11: a worklist older than the Humanizer's previous dispatch → NOT READY",
          code == 1 and "older than the humanizer's previous dispatch" in log, log[-300:])
    os.utime(crit, ns=(saved.st_atime_ns, saved.st_mtime_ns))
    code, log = ps("check", "unit-03", "humanizer", "--cycle", "2")
    check("item 11: the fresh critique is the worklist → READY", code == 0, log[-300:])
    code, log = ps("check", "unit-03", "humanizer", "--cycle", "3")
    check("item 11: a cycle with no loop record → NOT READY", code == 1
          and "no loop record" in log, log[-300:])
    _write(d / "humanized.md", (d / "humanized.c1.md").read_text(encoding="utf-8")
           .replace("Esa noche no llamó", "Esa noche tampoco llamó"))
    code, log = ps("done", "unit-03", "humanizer", "--tier", "creative", "--cycle", "2")
    rd = _json(d / "role-diff-humanizer-c2.json")
    check("done humanizer on a patch cycle: diff against the cycle's snapshot",
          code == 0 and rd["before"].endswith("humanized.c1.md"), log[-300:])

    _step(ps, "unit-03", "reader_pov", lambda: _write(d / "reader-report.md", "# R\n\nok\n"),
          cycle=2)
    _step(ps, "unit-03", "continuity_a", lambda: _write(d / "coherence.md", "# C\n\nok\n"),
          cycle=2)
    ps("checks", "unit-03")
    _step(ps, "unit-03", "critic", lambda: (
        _write(d / "scorecard.yaml", _scorecard(rows, "REVISE", "Humanizer")),
        _write(d / "critique.md", _critique("REVISE", "Humanizer"))), cycle=2)
    code, log = ps("snapshot", "unit-03", "--reason", "human", "--target", "writer")
    code, log = ps("check", "unit-03", "writer", "--cycle", "3")
    check("item 11: a human-rejection loop needs human-notes.md", code == 1
          and "human-notes.md" in log, log[-300:])
    _write(d / "human-notes.md", "2026-09-25 — the ending of the scene is rushed\n")
    code, log = ps("check", "unit-03", "writer", "--cycle", "3")
    check("item 11: …present and fresh → READY", code == 0, log[-300:])


def test_verdict(tmp: Path, check, run) -> None:
    print("\nitem 12 — the verdict is recomputed from the rows (bookkit/verdict.py)")
    from bookkit import verdict as V

    def rows(*r):
        return [{"id": i, "severity": s, "status": st, "loopback_target": t} for i, s, st, t in r]
    cases = [
        (rows(("a", "critical", "fail", "Editor"), ("b", "minor", "fail", "escalate")), "fast",
         ("ESCALATE", "escalate")),
        (rows(("a", "critical", "fail", "Editor"), ("b", "critical", "fail", "Humanizer")), "fast",
         ("REWORK", "Writer")),
        (rows(("a", "critical", "fail", "Editor"), ("b", "significant", "fail", "Humanizer")),
         "fast", ("REVISE", "Editor")),
        (rows(("a", "significant", "fail", "Editor"), ("b", "significant", "fail", "Humanizer")),
         "fast", ("REVISE", "Writer")),
        (rows(("a", "minor", "fail", "Humanizer"), ("b", "minor", "fail", "Humanizer"),
              ("c", "minor", "fail", "Humanizer")), "full", ("REVISE", "Humanizer")),
        (rows(("a", "minor", "fail", "Humanizer"), ("b", "minor", "fail", "Humanizer"),
              ("c", "minor", "fail", "Humanizer")), "fast", ("PASS", "none")),
        (rows(("a", "critical", "pass", None)), "full", ("PASS", "none")),
    ]
    for items, tol, want in cases:
        got = V.compute(items, tol)
        check(f"verdict {want[0]}→{want[1]} ({tol}): {got['basis']}",
              (got["verdict"], got["target"]) == want, f"{got}")
    check("an empty scorecard is invalid", bool(V.validate([])))

    work = _copy(tmp, "novela", fixed=True)
    d = work / "drafts/unit-03"
    ps = _ps(run, work)
    _literary_to_critic(ps, d, CLEAN_U3.split("\n", 2)[2])
    bad_rows = [("beats-1", "critical", "fail", "Writer"), ("voice-2", "minor", "pass", None)]
    code, log = _step(ps, "unit-03", "critic", lambda: (
        _write(d / "scorecard.yaml", _scorecard(bad_rows, "REVISE", "Writer")),
        _write(d / "critique.md", _critique("PASS", "none"))), tier="creative")
    check("item 12: a critique header that disagrees with its rows → done critic exit 4",
          code == 4 and "rows compute REVISE" in log, log[-400:])
    code, log = _step(ps, "unit-03", "critic", lambda: (
        _write(d / "scorecard.yaml", 'unit: "unit-03"\nitems: []\ncomputed_verdict: PASS\n'),
        _write(d / "critique.md", _critique("PASS", "none"))), tier="creative")
    check("item 12: a scorecard with no rows → exit 4", code == 4 and "no `items`" in log,
          log[-300:])
    code, log = _critic(ps, d, bad_rows, "REVISE", "Writer")
    check("item 12: a consistent critique → exit 0 with the recomputed verdict",
          code == 0 and "verdict recomputed from scorecard.yaml: REVISE" in log, log[-300:])


def test_integration(tmp: Path, check, run) -> None:
    print("\nintegration — runs.tsv, proofreader, approve, CG Mode B, parsing, schema, paths")
    work = _copy(tmp, "novela", fixed=True)
    d = work / "drafts/unit-03"
    ps = _ps(run, work)

    # A scaffolded runs.tsv: header only, CRLF, no final newline.
    (work / "runs.tsv").write_bytes(b"unit\tagent\ttier\tcycle\ttimestamp_utc\toutput_bytes")
    body = "<!-- SCENE s1 -->\n" + CLEAN_U3.split("\n", 2)[2]
    _step(ps, "unit-03", "writer", lambda: _write(d / "draft.md", body), tier="creative")
    rows = (work / "runs.tsv").read_text(encoding="utf-8").splitlines()
    check("done: header-only runs.tsv (no final newline) → one header, one new row",
          sum(r.startswith("unit\tagent") for r in rows) == 1 and len(rows) == 2
          and rows[1].startswith("unit-03\twriter"), f"{rows}")
    _step(ps, "unit-03", "editor", lambda: _write(d / "edit.md", body))
    ed = _json(d / "role-diff-editor-c1.json")
    check("done editor, first pass: role diff draft.md → edit.md",
          ed["before"].endswith("draft.md") and ed["after"].endswith("edit.md"))
    _step(ps, "unit-03", "humanizer", lambda: _write(d / "humanized.md", body), tier="creative")
    hu = _json(d / "role-diff-humanizer-c1.json")
    check("done humanizer, first pass: role diff edit.md → humanized.md",
          hu["before"].endswith("edit.md") and hu["after"].endswith("humanized.md"))
    _step(ps, "unit-03", "reader_pov", lambda: _write(d / "reader-report.md", "# R\n\nok\n"))
    _step(ps, "unit-03", "continuity_a", lambda: _write(d / "coherence.md", "# C\n\nok\n"))
    code, _ = ps("checks", "unit-03")
    check("clean chapter: checks exit 0", code == 0)
    code, log = _critic(ps, d, PASS_ROWS, "PASS", None)
    check("done critic: PASS recomputed", code == 0 and "PASS" in log, log[-300:])
    code, log = ps("check", "unit-03", "proofreader")
    check("check proofreader: a PASS scorecard → exit 0", code == 0, log[-300:])
    _write(d / "adversarial-report.md",
           "| 1 | x | §1 | critical | B | CONFIRMED | CONFIRMED → REVISE (Writer) |\n")
    _touch_later(d / "adversarial-report.md", d / "critique.md")
    code, log = ps("check", "unit-03", "proofreader")
    check("check proofreader: a newer confirmed adversarial finding suspends the PASS",
          code == 1 and "suspended" in log, log[-300:])
    (d / "adversarial-report.md").unlink()

    code, log = _step(ps, "unit-03", "proofreader", lambda: _write(
        d / "proofread.md", body + "\nY entonces, sin que nadie se lo pidiera, Mariana decidió "
        "contar la historia entera desde el principio.\n"))
    check("item 8: a Proofreader that adds a sentence → done exit 4 (not mechanical)",
          code == 4 and "not mechanical" in log, log[-300:])
    code, log = _step(ps, "unit-03", "proofreader", lambda: _write(
        d / "proofread.md", body.replace("—dijo Rosa.", "—dijo Rosa—.", 1)))
    pr = _json(d / "role-diff-proofreader-c1.json")
    check("done proofreader: role diff humanized.md → proofread.md, changes listed",
          code == 0 and pr["before"].endswith("humanized.md")
          and pr["after"].endswith("proofread.md") and pr["changes"], log[-300:])

    fin = work / "final/unit-03.md"
    code, log = ps("approve", "unit-03")
    ftext = fin.read_text(encoding="utf-8") if fin.exists() else ""
    check("approve (literary): final/ gets proofread.md with every HTML comment stripped",
          code == 0 and "<!--" not in ftext and "—dijo Rosa—." in ftext and "\n\n\n" not in ftext,
          log[-300:])
    code, log = ps("approve", "unit-03")
    check("approve: an existing final/ file is not replaced without --force",
          code == 1 and "--force" in log)
    code, log = ps("check", "unit-03", "continuity_b")
    code, log = ps("done", "unit-03", "continuity_b", "--tier", "audit", "--cycle", "1")
    check("item 7: done continuity_b with the tracker untouched since dispatch → exit 1",
          code == 1 and "continuity-tracker.md: stale" in log, log[-300:])
    with open(work / "bible/continuity-tracker.md", "a", encoding="utf-8") as fh:
        fh.write("\n- unit-03: Rosa trae la boleta.\n")
    code, log = ps("done", "unit-03", "continuity_b", "--tier", "audit", "--cycle", "1")
    check("item 7: unit-03 pays F01 per its card → the story ledger must be updated too",
          code == 1 and "story-ledger.yaml: stale" in log, log[-300:])
    _edit(work / "bible/story-ledger.yaml", "status: open\n    paid_in: null",
          "status: paid\n    paid_in: unit-03")
    code, log = ps("done", "unit-03", "continuity_b", "--tier", "audit", "--cycle", "1")
    check("item 7: tracker and ledger updated after the dispatch → exit 0", code == 0, log[-300:])
    _touch_later(d / "humanized.md", d / "proofread.md")
    code, log = ps("approve", "unit-03", "--force")
    check("approve: a proofread.md older than humanized.md is refused",
          code == 1 and "older" in log, log[-300:])

    tech = _copy(tmp, "tecnico")
    td = tech / "drafts/unit-01"
    _write(td / "proofread.md", "# Peek\n\nPeek reads a loaded row. <!-- SOURCE: qlik-functions "
                                "§Peek -->\n\n<!-- HUMANIZER: touched 1 -->\n\nMore text.\n\n"
                                "```\n// <!-- EDITOR: inside code -->\n\n\nx = 1\n```\n")
    _touch_later(td / "proofread.md", td / "humanized.md")
    code, log = run("pipeline_step.py", ["--root", str(tech), "approve", "unit-01", "--force"])
    t = (tech / "final/unit-01.md").read_text(encoding="utf-8")
    check("approve (nonfiction): SOURCE markers ship, handoff comments do not, code untouched",
          code == 0 and "<!-- SOURCE: qlik-functions §Peek -->" in t and "HUMANIZER" not in t
          and "inside code -->\n\n\nx = 1" in t and "touched 1" not in t, t)

    # Parsing tolerance: CRLF sheets, the calibration placeholder, literary
    # diagnostics in the rhetoric_budget fence.
    tol = _copy(tmp, "novela", fixed=True)
    for p in [*(tol / "bible/characters").glob("*.md"), tol / "bible/plot-structure.md"]:
        p.write_bytes(p.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
    code, log = run("pipeline_step.py", ["--root", str(tol), "ready"])
    check("CRLF sheets and plot-structure parse: ready still passes", code == 0, log[-300:])

    vp = tol / "bible/voice-profile.md"
    _edit(vp, "  rhet-2: 1\n", "  rhet-2: 3\n  similes_per_1000: 5\n  fragment_ratio: 0.2\n"
                              "  emotion_channels: 2\n")
    out = tmp / "rhet-diag.json"
    code, log = run("count_rhet.py", ["--root", str(tol), "--unit", "unit-03", "--json", str(out)])
    rep = _json(out) if out.exists() else {}
    check("count_rhet: literary diagnostic keys in the budget fence are tolerated",
          code == 0 and rep.get("counts", {}).get("rhet-2", {}).get("quota") == 3
          and not any("rhetoric_budget" in n for n in rep.get("notes", [])), log[-300:])

    _edit(tol / "bible/style-guide.md", "<!-- calibration-source: human -->",
          "<!-- calibration-source: human | model | reference -->")
    code, log = run("pipeline_step.py", ["--root", str(tol), "ready"])
    check("the template placeholder `human | model | reference` is not a human passage",
          code == 1 and "CALIBRATION-NO-HUMAN" in log, log[-300:])

    # R4: a character added mid-book has its arc in the REMAINING outline.
    mid = _copy(tmp, "novela", fixed=True)
    sheet = mid / "bible/characters/gustavo.md"
    shutil.copyfile(FIX / "novela-fixes/gustavo.md", sheet)
    code, log = run("check_story.py", ["--root", str(mid), "--unit", "unit-03", "--no-draft"])
    check("R4: a mid-book sheet with its arc from added_in_unit on → no placement blocker",
          code == 0 and "added_in_unit" not in log, log[-300:])
    _edit(sheet, "    - unit: unit-03\n      change:", "    - unit: unit-02\n      change:")
    out = tmp / "story-mid.json"
    code, log = run("check_story.py", ["--root", str(mid), "--ready-to-draft", "--json", str(out)])
    check("R4: a mid-book turning point before added_in_unit → CHAR-ARC-OUT-OF-OUTLINE blocking",
          code == 1 and any(f["code"] == "CHAR-ARC-OUT-OF-OUTLINE" and f["severity"] == "blocking"
                            and "added_in_unit" in f["detail"] for f in _json(out)["findings"]),
          log[-400:])

    # item 14 — the project schema is 3.4; anything else predates the skill.
    old = _copy(tmp, "novela", fixed=True)
    _edit(old / "bible/meta.yaml", 'schema_version: "3.4"', 'schema_version: "3.0"')
    code, log = run("pipeline_step.py", ["--root", str(old), "ready"])
    check("item 14: schema_version 3.0 → pipeline_step exits 2 and offers a re-scaffold",
          code == 2 and "fresh" in log and "3.4" in log, log[-300:])

    # item 15 — relative --json/--file resolve against --root, whatever the cwd.
    rel = _copy(tmp, "tecnico")
    runs = [("check_identifiers.py", ["--unit", "unit-01", "--file", "final/unit-01.md",
                                      "--json", "out/ids.json"], "out/ids.json"),
            ("count_rhet.py", ["--unit", "unit-01", "--json", "out/rhet.json"], "out/rhet.json"),
            ("check_role_diff.py", ["--role", "proofreader", "--before", "final/unit-01.md",
                                    "--after", "final/unit-01.md", "--json", "out/rd.json"],
             "out/rd.json")]
    for script, args, target in runs:
        code, log = run(script, ["--root", str(rel), *args])
        check(f"item 15: {script} writes a relative --json under --root",
              (rel / target).exists() and not (Path.cwd() / target).exists(), log[-300:])
    lit = _copy(tmp, "novela", fixed=True)
    for script, args, target in (
            ("check_story.py", ["--unit", "unit-01", "--file", "final/unit-01.md",
                                "--json", "out/story.json"], "out/story.json"),
            ("lint_fiction.py", ["--unit", "unit-01", "--file", "final/unit-01.md",
                                 "--json", "out/lf.json"], "out/lf.json")):
        code, log = run(script, ["--root", str(lit), *args])
        check(f"item 15: {script} writes a relative --json under --root",
              (lit / target).exists() and not (Path.cwd() / target).exists(), log[-300:])


def test_help(tmp: Path, check, run) -> None:
    print("\n--help — every new script documents itself")
    for script in ("count_rhet.py", "check_identifiers.py", "check_role_diff.py",
                   "pipeline_step.py", "lint_fiction.py", "check_story.py"):
        code, log = run(script, ["--help"])
        check(f"{script} --help", code == 0 and "usage" in log.lower(), log[-200:])


# ---------------------------------------------------------------------------
# Fix round 2 — one regression per item (advverify2 attacks)
# ---------------------------------------------------------------------------


def _story(run, work: Path, *args) -> tuple[int, set, str]:
    out = work / f".story-{_counter[0]}.json"
    _counter[0] += 1
    code, log = run("check_story.py", ["--root", str(work), *args, "--json", str(out)])
    data = _json(out) if out.exists() else {"findings": []}
    return code, {(x["code"], x["severity"], x["subject"]) for x in data["findings"]}, log


def _ship(ps, work: Path, extra: str) -> tuple[int, str]:
    """Clean chapter 3 + `extra` → proofread.md → approve (advverify2's tryship)."""
    d = work / "drafts/unit-03"
    for f in ("humanized.md", "checks.json"):
        (d / f).unlink(missing_ok=True)
    (work / "final/unit-03.md").unlink(missing_ok=True)
    _write(d / "proofread.md", CLEAN_U3 + "\n" + extra + "\n")
    return ps("approve", "unit-03")


def test_fix2_r3_at_the_writer(tmp: Path, check, run) -> None:
    print("\nfix2 item 1 — R3 at the Writer: the full `ready`, not only the unit's cast")
    work = _copy(tmp, "novela")                      # Rosa (unit-03) incomplete
    ps = _ps(run, work)
    code, log = ps("check", "unit-01", "writer")
    check("item 1: `check unit-01 writer` is NOT READY while `ready` fails (Rosa is in unit-03, "
          "not unit-01)", code == 1 and "R3" in log and "CHAR-INCOMPLETE rosa" in log,
          log[-400:])
    fixed = _copy(tmp, "novela", fixed=True)
    psf = _ps(run, fixed)
    code, log = psf("check", "unit-01", "writer")
    check("item 1: …and READY once `ready` passes", code == 0, log[-300:])
    _edit(fixed / "bible/style-guide.md", "calibration-source: human", "calibration-source: model")
    _write(fixed / "drafts/unit-01/draft.md", (fixed / "final/unit-01.md").read_text("utf-8"))
    code, log = psf("done", "unit-01", "writer", "--tier", "creative", "--cycle", "1")
    check("item 1: `done writer` pauses (exit 3) when `ready` fails after the dispatch",
          code == 3 and "R3" in log and "CALIBRATION-NO-HUMAN" in log, log[-400:])
    code, log = _ship(psf, fixed, "")
    check("item 1: `approve` refuses while `ready` fails (a clean chapter)",
          code == 1 and "R3" in log and not (fixed / "final/unit-03.md").exists(), log[-300:])
    _write(fixed / "edits.yaml", '- {unit: unit-01, find: "Nadie se rió.", replace: "Nadie dijo '
           'nada.", rule: gesture_tic}\n')
    before = (fixed / "final/unit-01.md").read_text("utf-8")
    code, log = psf("apply-edits", "edits.yaml")
    check("item 1: `apply-edits` refuses while `ready` fails; nothing written",
          code == 1 and "R3" in log
          and (fixed / "final/unit-01.md").read_text("utf-8") == before, log[-300:])


def test_fix2_profile(tmp: Path, check, run) -> None:
    print("\nfix2 item 2 — project.profile normalized; unknown/missing profile or schema → exit 2")
    meta_rx = re.compile(r'profile: "book-literary"')
    for label, repl, want in (("'Book-Literary ' (case, space)", 'profile: "Book-Literary "', 1),
                              ("'book-fiction' (unknown)", 'profile: "book-fiction"', 2),
                              ("no profile", "", 2)):
        work = _copy(tmp, "novela")
        meta = work / "bible/meta.yaml"
        _write(meta, meta_rx.sub(repl, meta.read_text("utf-8")))
        c1, l1 = run("pipeline_step.py", ["--root", str(work), "ready"])
        c2, l2 = run("check_story.py", ["--root", str(work), "--ready-to-draft"])
        if want == 1:
            check(f"item 2: {label} is the literary profile — R1 still blocks (exit 1)",
                  c1 == 1 and c2 == 1 and "CHAR-INCOMPLETE rosa" in l1, l1[-300:])
        else:
            check(f"item 2: {label} → pipeline_step and check_story exit 2 with the reason",
                  c1 == 2 and c2 == 2 and "profile" in l1 and "profile" in l2,
                  f"{c1}/{c2} {l1[-200:]}")
    old = _copy(tmp, "novela", fixed=True)
    _edit(old / "bible/meta.yaml", 'schema_version: "3.4"', 'schema_version: "3.0"')
    code, log = run("check_story.py", ["--root", str(old), "--ready-to-draft"])
    check("item 2: check_story on schema_version 3.0 → exit 2", code == 2 and "3.4" in log,
          log[-300:])


def test_fix2_name_detection(tmp: Path, check, run) -> None:
    print("\nfix2 item 3 — names in italics, capitals, headings, tables; speaker positions")
    work = _copy(tmp, "novela", fixed=True)
    h = work / "drafts/unit-03/humanized.md"
    body = "# 3. La boleta\n\n" + CLEAN_U3.split("\n", 2)[2]
    cases = [("'—dijo *Gustavo*' (italic, speaker)", "—Son doscientos mil —dijo *Gustavo*.",
              "Gustavo"),
             ("'—dijo _Gustavo_'", "—Son doscientos mil —dijo _Gustavo_.", "Gustavo"),
             ("an italic paragraph", "*Esa tarde Gustavo le había dicho que la quiniela era un "
              "impuesto a la esperanza.*", "Gustavo"),
             ("'DiStefano' (internal capital)", "—Son doscientos mil —dijo DiStefano.",
              "DiStefano"),
             ("'McAllister'", "McAllister cerró la puerta del auto.", "McAllister"),
             ("'GUSTAVO' (all caps, speaker)", "—Son doscientos mil —dijo GUSTAVO.", "Gustavo"),
             ("a '## Gustavo' section heading", "## Gustavo\n\nEsperaba en la vereda.",
              "Gustavo"),
             ("dialogue in a table cell", "| —Son doscientos mil —dijo Gustavo. |\n|---|",
              "Gustavo"),
             ("'Luz' acting and speaking (a name that is a noun)",
              "Luz llegó cuando ya no había luz. —No sé nada —Luz miró a Mariana.", "Luz")]
    for label, extra, subj in cases:
        _write(h, body + "\n" + extra + "\n")
        code, found, log = _story(run, work, "--unit", "unit-03")
        check(f"item 3: {label} → NEW-CHARACTER blocking",
              code == 1 and ("NEW-CHARACTER", "blocking", subj) in found, f"{found}")
    _write(h, body + "\nEncima había una caja que decía FRÁGIL, un libro de *Rayuela* y un "
           "cartel de la ONU. Tomás volvió en el Falcon con una bolsa del Carrefour.\n")
    code, found, log = _story(run, work, "--unit", "unit-03")
    check("item 3: FRÁGIL (a sign), *Rayuela* (a title), ONU (acronym), Falcon/Carrefour "
          "(brands) never block", code == 0 and not {s for c, sev, s in found
                                                     if sev == "blocking"}, f"{found}")
    # Speaker/actor positions for world.md words (places too).
    with open(work / "bible/world.md", "a", encoding="utf-8", newline="\n") as fh:
        fh.write("- La agencia de **Gustavo** en Oroño.\n")
    for label, extra in (("'—dijo el viejo Gustavo' (two words in between)",
                          "—Son doscientos mil —dijo el viejo Gustavo."),
                         ("'—le explicó entonces Gustavo'",
                          "—Son doscientos mil —le explicó entonces Gustavo."),
                         ("'Gustavo, con las manos en los bolsillos, dijo' (appositive)",
                          "Gustavo, con las manos en los bolsillos, dijo que eran doscientos "
                          "mil."),
                         ("'Entró Gustavo.' (subject after the verb)",
                          "Entró Gustavo. Nadie lo saludó.")):
        _write(h, body + "\n" + extra + "\n")
        code, found, log = _story(run, work, "--unit", "unit-03")
        check(f"item 3: a world.md place in a speaker/actor position — {label} → EXTRA-PROMOTE",
              code == 1 and ("EXTRA-PROMOTE", "blocking", "Gustavo") in found, f"{found}")
    _write(h, body + "\nRosa dijo que Gustavo vendría a la tarde, y habló de Gustavo un rato.\n")
    code, found, log = _story(run, work, "--unit", "unit-03")
    check("item 3: 'dijo que Gustavo…' / 'habló de Gustavo' only MENTION him (no promotion)",
          code == 0 and not any(c == "EXTRA-PROMOTE" for c, _s, _x in found), f"{found}")


def test_fix2_bible_laundering(tmp: Path, check, run) -> None:
    print("\nfix2 item 4 — sheets, extras and locations cannot launder a name")
    line = "—Son doscientos mil —dijo Gustavo."
    work = _copy(tmp, "novela", fixed=True)
    _edit(work / "bible/characters/_extras.md", 'label: "mozo del bar"',
          'label: "gustavo, el mozo del bar"')
    _write(work / "drafts/unit-03/humanized.md", CLEAN_U3 + "\n" + line + "\n")
    code, found, log = _story(run, work, "--unit", "unit-03")
    check("item 4: an _extras.md label word used as a name → EXTRA-PROMOTE (extras add no "
          "known names)", code == 1 and ("EXTRA-PROMOTE", "blocking", "Gustavo") in found,
          f"{found}")
    loc = _copy(tmp, "novela", fixed=True)
    _edit(loc / "outline/units.yaml", 'location: "Pichincha, Rosario"',
          'location: "Pichincha, Rosario (agencia de Gustavo)"')
    _write(loc / "drafts/unit-03/humanized.md", CLEAN_U3 + "\n" + line + "\n")
    code, found, log = _story(run, loc, "--unit", "unit-03")
    check("item 4: an outline location word that speaks → EXTRA-PROMOTE (a place, not a person)",
          code == 1 and ("EXTRA-PROMOTE", "blocking", "Gustavo") in found, f"{found}")
    for label, sheet, code_ in (
            ("role: minor", '---\nname: "Gustavo Ledesma"\nrole: minor\n---\n', "CHAR-INCOMPLETE"),
            ("no front matter", "# Personaje — Gustavo\n\nEl agenciero.\n", "CHAR-INCOMPLETE"),
            ("broken YAML", '---\nname: "Gustavo\nrole: secondary: x\n---\n', "CHAR-INCOMPLETE"),
            ("a duplicate slug", '---\nname: "Gustavo Ledesma"\nslug: tomas\nrole: secondary\n'
             'status: draft\n---\n', "CHAR-DUPLICATE")):
        w = _copy(tmp, "novela", fixed=True)
        _write(w / "bible/characters/gustavo.md", sheet)
        _write(w / "drafts/unit-03/humanized.md", CLEAN_U3 + "\n" + line + "\n")
        code, found, log = _story(run, w, "--unit", "unit-03")
        check(f"item 4: a sheet with {label} → {code_} blocking in --unit mode",
              code == 1 and any(c == code_ and sev == "blocking" for c, sev, _s in found),
              f"{found}")


def test_fix2_signatures(tmp: Path, check, run) -> None:
    print("\nfix2 item 5 — a signature is bound to the content it approved")
    import datetime as _dt
    work = _copy(tmp, "novela")
    ps = _ps(run, work)
    code, log = ps("sign", "rosa", "--by", "Seba")
    check("item 5: `sign` refuses an incomplete sheet (TBD backstory)",
          code == 1 and "not complete" in log, log[-300:])
    shutil.copyfile(FIX / "novela-fixes/rosa.md", work / "bible/characters/rosa.md")
    sheet = work / "bible/characters/rosa.md"
    _write(sheet, re.sub(r"signed_(?:by|hash): .*\n", "", sheet.read_text("utf-8")))
    code, log = ps("ready")
    check("item 5: `status: complete` without signed_hash is not signed → CHAR-INCOMPLETE",
          code == 1 and "signed_hash" in log, log[-300:])
    code, log = ps("sign", "rosa", "--by", "Seba")
    text = sheet.read_text("utf-8")
    check("item 5: `sign rosa --by Seba` writes status, signed_on (today), signed_by, signed_hash",
          code == 0 and f'signed_on: "{_dt.date.today().isoformat()}"' in text
          and 'signed_by: "Seba"' in text and 'signed_hash: "sha256:' in text, text[:400])
    code, log = ps("ready")
    check("item 5: …and `ready` passes", code == 0, log[-300:])
    _write(sheet, text.replace('aliases: ["la vecina", "doña Rosa"]',
                               'aliases: ["la vecina", "doña Rosa", "Gustavo"]'))
    code, log = ps("ready")
    check("item 5: an alias added after signing → CHAR-UNSIGNED-CHANGE (re-run the "
          "questionnaire block and re-sign)", code == 1 and "CHAR-UNSIGNED-CHANGE rosa" in log
          and "re-sign" in log, log[-300:])
    _write(sheet, text.replace("personality: \"Chismosa", "personality: \"Muy chismosa"))
    code, log = ps("ready")
    check("item 5: a required field edited after signing → CHAR-UNSIGNED-CHANGE",
          code == 1 and "CHAR-UNSIGNED-CHANGE rosa" in log, log[-300:])
    code, _ = ps("sign", "rosa", "--by", "Seba")
    code2, _ = ps("ready")
    check("item 5: re-signing after the human approves the change → ready again",
          code == 0 and code2 == 0)
    good = sheet.read_text("utf-8")
    future = (_dt.date.today() + _dt.timedelta(days=3)).isoformat()
    for label, date in (("an impossible date 2026-02-30", "2026-02-30"),
                        (f"a future date {future}", future), ("1999-12-31", "1999-12-31")):
        _write(sheet, re.sub(r'signed_on: ".*"', f'signed_on: "{date}"', good))
        code, log = ps("ready")
        check(f"item 5: signed_on {label} → CHAR-INCOMPLETE",
              code == 1 and "CHAR-INCOMPLETE rosa" in log and "signed_on" in log, log[-300:])
    _write(sheet, good)
    code, log = ps("sign", "nadie", "--by", "Seba")
    check("item 5: `sign` on an unknown slug → exit 1", code == 1, log[-200:])
    code, log = ps("sign", "rosa", "--by", "TBD")
    check("item 5: `sign --by TBD` (a placeholder signer) → exit 1", code == 1, log[-200:])


def test_fix2_placeholders(tmp: Path, check, run) -> None:
    print("\nfix2 item 6 — placeholders and the 3-word minimum")
    from bookkit.placeholder import is_placeholder, too_short
    empties = ["N/A", "n/a", "x", "-", "none", "null", "nil", "(pendiente)", "pendiente",
               "sin definir", "a completar", "completar", "<completar>", "{{nombre}}", "XXX",
               "TODO: ver", "TBD", "Lorem ipsum", "falta", "?", "…", "[describir personalidad]"]
    check("item 6: every listed placeholder counts as empty",
          all(is_placeholder(v) for v in empties), f"{[v for v in empties if not is_placeholder(v)]}")
    answers = ["Todo lo que toca lo rompe.", "(no tiene hermanos)",
               "Falta de padre desde los ocho años.", "Pendiente de la aprobación del padre."]
    check("item 6: real answers are not placeholders (Spanish 'Todo…', 'Falta de…', '(no tiene…)')",
          not any(is_placeholder(v) for v in answers), f"{[v for v in answers if is_placeholder(v)]}")
    check("item 6: 'Tímido.' is too short for a narrative field; 'Tímido con los extraños.' is not",
          too_short("Tímido.") and not too_short("Tímido con los extraños."))
    work = _copy(tmp, "novela", fixed=True)
    sheet = work / "bible/characters/mariana.md"
    good = sheet.read_text("utf-8")
    for field, val in (("backstory", "N/A"), ("need", "(pendiente)"), ("voice", "{{voz}}"),
                       ("personality", "Irónica.")):
        _write(sheet, re.sub(rf'^{field}: ".*"$', f'{field}: "{val}"', good, flags=re.M))
        code, log = run("pipeline_step.py", ["--root", str(work), "ready"])
        check(f"item 6: {field}: {val!r} → CHAR-INCOMPLETE mariana",
              code == 1 and "CHAR-INCOMPLETE mariana" in log and field in log, log[-300:])
    _write(sheet, good)
    plot = work / "bible/plot-structure.md"
    pgood = plot.read_text("utf-8")
    _write(plot, re.sub(r'resolution: ".*"', 'resolution: "N/A"',
                        re.sub(r'answer: ".*"', 'answer: "(pendiente)"', pgood)))
    code, log = run("pipeline_step.py", ["--root", str(work), "ready"])
    check("item 6: ending resolution 'N/A' and answer '(pendiente)' → ENDING-MISSING",
          code == 1 and "ENDING-MISSING" in log and "ending.resolution" in log, log[-300:])
    _write(plot, pgood)
    _edit(work / "bible/story-ledger.yaml", 'what: "El clic', 'what: "TBD" #')
    code, log = run("pipeline_step.py", ["--root", str(work), "ready"])
    check("item 6: a ledger entry whose `what` is TBD → LEDGER-INVALID",
          code == 1 and "LEDGER-INVALID" in log, log[-300:])


def test_fix2_ledger(tmp: Path, check, run) -> None:
    print("\nfix2 item 7 — the story ledger exists and is well formed")
    work = _copy(tmp, "novela", fixed=True)
    shutil.copyfile(FIX / "novela-fixes/unit-03-final.md", work / "final/unit-03.md")
    led = work / "bible/story-ledger.yaml"
    good = led.read_text("utf-8").replace("status: open\n    paid_in: null",
                                          "status: paid\n    paid_in: unit-03")
    _write(led, good)
    code, found, _ = _story(run, work, "--manuscript")
    check("item 7: a well-formed ledger, all paid → no LEDGER finding",
          not any(c.startswith("LEDGER") for c, _s, _x in found), f"{found}")
    led.unlink()
    code, found, _ = _story(run, work, "--ready-to-draft")
    check("item 7: no story-ledger.yaml → LEDGER-MISSING blocking at ready",
          code == 1 and ("LEDGER-MISSING", "blocking", "story-ledger") in found, f"{found}")
    code, found, _ = _story(run, work, "--manuscript")
    check("item 7: …and major in --manuscript", code == 1
          and ("LEDGER-MISSING", "major", "story-ledger") in found, f"{found}")
    _write(led, "entries: []\n")
    _edit(work / "outline/units.yaml", "ledger: {plants: [F01, F02], pays: []}",
          "ledger: {plants: [], pays: []}")
    _edit(work / "outline/units.yaml", "ledger: {plants: [], pays: [F02]}",
          "ledger: {plants: [], pays: []}")
    _edit(work / "outline/units.yaml", "ledger: {plants: [], pays: [F01]}",
          "ledger: {plants: [], pays: []}")
    code, found, _ = _story(run, work, "--ready-to-draft")
    check("item 7: `entries: []` is a valid empty ledger", code == 0
          and not any(c.startswith("LEDGER") for c, _s, _x in found), f"{found}")
    for label, old, new in (("status 'postponed'", "status: paid\n    paid_in: unit-03",
                             "status: postponed\n    paid_in: null"),
                            ("paid without paid_in", "status: paid\n    paid_in: unit-03",
                             "status: paid\n    paid_in: null"),
                            ("paid in a unit that does not exist",
                             "status: paid\n    paid_in: unit-03",
                             "status: paid\n    paid_in: unit-99")):
        _write(led, good.replace(old, new, 1))
        code, found, _ = _story(run, work, "--ready-to-draft")
        code2, found2, _ = _story(run, work, "--manuscript")
        check(f"item 7: {label} → LEDGER-INVALID (blocking at ready, major in --manuscript)",
              code == 1 and any(c == "LEDGER-INVALID" and s == "blocking" for c, s, _x in found)
              and code2 == 1 and any(c == "LEDGER-INVALID" and s == "major"
                                     for c, s, _x in found2), f"{found} {found2}")


def test_fix2_thin_ending(tmp: Path, check, run) -> None:
    print("\nfix2 item 8 — the final unit carries its ending on the page")
    work = _copy(tmp, "novela", fixed=True)
    _edit(work / "bible/story-ledger.yaml", "status: open\n    paid_in: null",
          "status: paid\n    paid_in: unit-03")
    _write(work / "final/unit-03.md", "# 3. La boleta\n\nMariana, Tomás y Rosa.\n")
    code, found, log = _story(run, work, "--manuscript")
    check("item 8: a 4-word final unit → ENDING-NOT-DELIVERED blocking",
          code == 1 and ("ENDING-NOT-DELIVERED", "blocking", "ending") in found, log[-300:])
    shutil.copyfile(FIX / "novela-fixes/unit-03-final.md", work / "final/unit-03.md")
    code, found, log = _story(run, work, "--manuscript")
    check("item 8: the 350-word final chapter delivers (≥ max(300, 30% of 450))",
          code == 0 and not any(c == "ENDING-NOT-DELIVERED" for c, _s, _x in found), log[-300:])
    _edit(work / "outline/units.yaml", "    target_words: 450\n    beats:\n      - id: s1\n"
          "        type: scene\n        summary: \"Rosa trae",
          "    target_words: 2000\n    beats:\n      - id: s1\n        type: scene\n"
          "        summary: \"Rosa trae")
    code, found, log = _story(run, work, "--manuscript")
    check("item 8: with target_words 2000 the same chapter is below 30% (600) → "
          "ENDING-NOT-DELIVERED", code == 1
          and ("ENDING-NOT-DELIVERED", "blocking", "ending") in found, log[-300:])


def test_fix2_checks_provenance(tmp: Path, check, run) -> None:
    print("\nfix2 item 13 — checks.json must describe the current humanized.md")
    work = _copy(tmp, "novela", fixed=True)
    d = work / "drafts/unit-03"
    ps = _ps(run, work)
    _literary_to_critic(ps, d, CLEAN_U3.split("\n", 2)[2])
    code, log = ps("check", "unit-03", "critic")
    check("item 13: fresh checks.json on the current text → critic READY", code == 0, log[-300:])
    _write(d / "humanized.md", (d / "humanized.md").read_text("utf-8")
           + "\n—Son doscientos mil —dijo Gustavo.\n")
    for f in ("checks.json", "checks.md", "reader-report.md", "coherence.md"):
        _touch_later(d / f, d / "humanized.md")
    code, log = ps("check", "unit-03", "critic")
    check("item 13: a checks.json from another text, with a NEWER mtime → NOT READY "
          "(source_sha1), and the live story check sees Gustavo",
          code == 1 and "source_sha1" in log and "NEW-CHARACTER Gustavo" in log, log[-400:])
    code, log = ps("check", "unit-03", "proofreader", "--human-override")
    check("item 13: …the Proofreader too, whatever the override",
          code == 1 and "source_sha1" in log, log[-300:])


def test_fix2_apply_edits(tmp: Path, check, run) -> None:
    print("\nfix2 item 14 — apply-edits story-checks every edited unit before writing")
    work = _copy(tmp, "novela", fixed=True)
    shutil.copyfile(FIX / "novela-fixes/unit-03-final.md", work / "final/unit-03.md")
    ps = _ps(run, work)
    before = (work / "final/unit-03.md").read_text("utf-8")
    _write(work / "edits.yaml", 'edits:\n  - unit: unit-03\n    find: "—Sentate, Rosa."\n'
           '    replace: "—Sentate, Rosa —dijo Gustavo, el agenciero, desde la puerta."\n'
           '    rule: tic-pass\n')
    code, log = ps("apply-edits", "edits.yaml", "--dry-run")
    check("item 14: a tic-pass edit that adds a name is refused, even as a dry run",
          code == 1 and "Gustavo" in log, log[-300:])
    code, log = ps("apply-edits", "edits.yaml")
    check("item 14: …and nothing is written",
          code == 1 and (work / "final/unit-03.md").read_text("utf-8") == before, log[-300:])
    _write(work / "edits.yaml", 'edits:\n  - unit: unit-03\n    find: "Nadie habló durante un '
           'rato."\n    replace: "Nadie dijo nada durante un rato."\n    rule: tic-pass\n')
    code, log = ps("apply-edits", "edits.yaml")
    check("item 14: a clean edit still applies",
          code == 0 and "Nadie dijo nada durante" in (work / "final/unit-03.md").read_text("utf-8"),
          log[-300:])


TESTS: list[Callable[[Path, Callable, Callable], None]] = [
    test_lexicon_packs,
    test_count_rhet,
    test_check_identifiers,
    test_check_role_diff,
    test_lint_fiction,
    test_user_rule_ready,
    test_user_rule_new_character,
    test_mentioned_only_names,
    test_check_story_codes,
    test_pipeline_step,
    test_story_blocks_never_overridable,
    test_role_laundering,
    test_tr_revise_walk,
    test_worklist_and_freshness,
    test_verdict,
    test_integration,
    test_help,
    test_fix2_r3_at_the_writer,
    test_fix2_profile,
    test_fix2_name_detection,
    test_fix2_bible_laundering,
    test_fix2_signatures,
    test_fix2_placeholders,
    test_fix2_ledger,
    test_fix2_thin_ending,
    test_fix2_checks_provenance,
    test_fix2_apply_edits,
]
