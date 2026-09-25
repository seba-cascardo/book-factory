#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""selftest.py — regression gate for the deterministic checks.

Spends no tokens and asserts two things in opposite directions: every defect
class the fixtures carry is FOUND, and correct prose produces NOTHING (a check
that fires on clean text trains everyone to ignore it).

Rules for anyone extending this file:
  - Assert on the artifact that ships (emitted files, the verdict, the store),
    never on an intermediate list something downstream still filters.
  - A gap you cannot close stays here, marked, and fails. Never delete a case to
    make this green; if the design changes, assert the equivalent on the new one.

After the built-in tests it imports every `tests/selftest_*.py` and runs each
function in its `TESTS` list as `fn(tmp, check, run)`. A module that fails to
import, or a test that raises, is reported as a FAIL — never skipped.

Usage
  python scripts/selftest.py            # everything
  python scripts/selftest.py -v         # every assertion
  python scripts/selftest.py -k gate    # only tests whose name contains "gate"
"""

from __future__ import annotations

import sys

# Before anything prints: a cp1252 console turns the em-dashes below into mojibake.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):  # pragma: no cover
        pass

import argparse  # noqa: E402
import importlib.util  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import shutil  # noqa: E402
import subprocess  # noqa: E402
import tempfile  # noqa: E402
import traceback  # noqa: E402
from pathlib import Path  # noqa: E402

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
FIXTURES = HERE / "tests" / "fixtures"
sys.path.insert(0, str(HERE))

PASSED: list[str] = []
FAILED: list[tuple[str, str]] = []
VERBOSE = False
DATE = "2026-01-01"


def check(name: str, condition: bool, detail: str = "") -> None:
    if condition:
        PASSED.append(name)
        if VERBOSE:
            print(f"  ok    {name}")
    else:
        FAILED.append((name, detail))
        print(f"  FAIL  {name}" + (f"\n          {detail}" if detail else ""))


def run(script: str, args: list[str], env: dict | None = None,
        scripts: Path = HERE) -> tuple[int, str]:
    proc = subprocess.run([sys.executable, str(scripts / script), *args],
                          capture_output=True, text=True, encoding="utf-8", errors="replace",
                          env={**os.environ, **(env or {})})
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


# ---------------------------------------------------------------------------
# Gate helpers
# ---------------------------------------------------------------------------


def gate(root: Path, *a: str, scripts: Path = HERE) -> tuple[int, str]:
    return run("manuscript_gate.py", ["--root", str(root), "--units", "final/*.md",
                                      "--date", DATE, *a], scripts=scripts)


def verdict(log: str) -> str:
    for line in log.splitlines():
        if "VERDICT:" in line:
            return line.split("VERDICT:")[1].strip()
    return "(none)"


def converged(log: str) -> bool:
    return any(line.startswith("[gate] CONVERGED") for line in log.splitlines())


def rdir(root: Path, n: int) -> Path:
    return root / "reviews" / f"manuscript-gate-{DATE}" / f"round-{n}"


def state(root: Path) -> dict:
    return json.loads((rdir(root, 1).parent / "state.json").read_text("utf-8"))


def store(root: Path) -> list[dict]:
    p = rdir(root, 1).parent / "findings.jsonl"
    return [json.loads(line) for line in p.read_text("utf-8").splitlines() if line.strip()]


def write_doc(round_dir: Path, name: str, doc: dict) -> None:
    fdir = round_dir / "findings"
    fdir.mkdir(parents=True, exist_ok=True)
    (fdir / name).write_text(json.dumps(doc), encoding="utf-8")


def clean_files(round_dir: Path, check_id: str, subjects: list[str], lens: str = "pairs",
                passes=(1, 2), sampled: bool = False) -> None:
    for s in subjects:
        for p in passes:
            write_doc(round_dir, f"{s}.{lens}.p{p}.json", {
                "check": check_id, "lens": lens, "subject": s, "pass": p,
                "sampled": sampled, "findings": []})


def emitted(round_dir: Path, check_id: str) -> list[str]:
    p = round_dir / f"coverage-{check_id}.json"
    return json.loads(p.read_text("utf-8")).get("emitted", []) if p.exists() else []


def audit_all(root: Path, n: int, mg4: list | None = None) -> None:
    """Clean findings for every subject emitted in round n, plus the whole-book read."""
    rd = rdir(root, n)
    clean_files(rd, "MG-1", emitted(rd, "MG-1"))
    clean_files(rd, "MG-2", emitted(rd, "MG-2"), lens="rule-vs-instance")
    write_doc(rd, "manuscript.whole-book-read.p1.json", {
        "check": "MG-4", "lens": "whole-book-read", "subject": "manuscript", "pass": 1,
        "findings": mg4 or []})


def finding(severity: str, quote: str = "the security chapter never deploys", **kw) -> dict:
    return {"relation": "D3", "severity": severity, "canonical_site": "final/unit-02.md:3",
            "other_sites": [], "searched_whole_chapter": True, "fix_scope": "add_content",
            "reasoning": "the reader cannot finish the task",
            "p1": {"location": "final/unit-02.md:3", "quote": quote}, **kw}


# The fixture units carry ```sql blocks: a project with code and no declared
# surface is an MG-6 major (item "code present, no surface declared"), so the
# default corpus declares one that ran — its `evidence` file exists (a runner
# string alone is not evidence, item 11).
HEAD = 'schema_version: "3.4"\n'
DEFAULT_META = HEAD + """project:
  profile: book-technical
  language_variant: en-US
validation_surface:
  surfaces:
    - surface: sql_examples
      runner: "sqlite3 in CI"
      executable: true
      evidence: reviews/runner/sql_examples.txt
"""
WAIVER = ("    waived_by: human\n    reason: \"selftest: the reason is spelled out here\"\n"
          "    debt: \"selftest: what is owed, spelled out here\"\n")


def write_meta(work: Path, meta: str = "") -> None:
    """bible/meta.yaml plus the runner evidence DEFAULT_META points at."""
    (work / "bible").mkdir(parents=True, exist_ok=True)
    (work / "bible" / "meta.yaml").write_text(meta or DEFAULT_META, encoding="utf-8")
    ev = work / "reviews" / "runner" / "sql_examples.txt"
    ev.parent.mkdir(parents=True, exist_ok=True)
    ev.write_text("sqlite3: 12 statements, 0 errors\n", encoding="utf-8")


def corpus(tmp: Path, name: str, units=("unit-02.md", "unit-03.md"), meta: str = "") -> Path:
    """Lint-clean fixture units (unit-01 carries deliberate render defects)."""
    work = tmp / name
    (work / "final").mkdir(parents=True)
    for unit in units:
        shutil.copy(FIXTURES / "final" / unit, work / "final" / unit)
    write_meta(work, meta)
    return work


# ---------------------------------------------------------------------------
# lint_render
# ---------------------------------------------------------------------------


def test_lint_render(tmp: Path) -> None:
    print("\nlint_render — defects found on the defective fixture")
    out = tmp / "lint.json"
    run("lint_render.py", ["--root", str(FIXTURES), "--units", "final/unit-01.md",
                           "--json", str(out), "--fail-on", "never", "--quiet"])
    data = json.loads(out.read_text(encoding="utf-8"))
    checks = {f["check"] for f in data["findings"]}
    check("setext hazard found", "setext-hazard" in checks)
    check("setext rated critical", any(f["severity"] == "critical" for f in data["findings"]
                                       if f["check"] == "setext-hazard"))
    check("ragged table found", "table-shape" in checks)
    check("leaked pipeline comment found", "pipeline-comment" in checks)
    check("unbalanced comment found", "unbalanced-comment" in checks)
    check("heading jump found", "heading-jump" in checks)
    check("SOURCE comment NOT flagged",
          not any("SOURCE" in (f.get("quote") or "") for f in data["findings"]
                  if f["check"] == "pipeline-comment"))

    print("lint_render — silence on the clean fixture")
    out2 = tmp / "lint-clean.json"
    run("lint_render.py", ["--root", str(FIXTURES), "--units", "final/unit-02.md",
                           "--json", str(out2), "--fail-on", "never", "--quiet"])
    clean = json.loads(out2.read_text(encoding="utf-8"))
    blocking = [f for f in clean["findings"] if f["severity"] in ("critical", "major")]
    check("clean fixture has no critical/major", not blocking,
          f"false positives: {[(f['check'], f['location']) for f in blocking]}")
    check("correctly spaced thematic break not flagged",
          not any(f["check"] == "setext-hazard" for f in clean["findings"]))

    print("lint_render — exit codes gate correctly")
    code_c, _ = run("lint_render.py", ["--root", str(FIXTURES), "--units", "final/unit-01.md",
                                       "--fail-on", "critical", "--quiet"])
    code_ok, _ = run("lint_render.py", ["--root", str(FIXTURES), "--units", "final/unit-02.md",
                                        "--fail-on", "critical", "--quiet"])
    check("exits 1 on a critical", code_c == 1, f"got {code_c}")
    check("exits 0 when clean", code_ok == 0, f"got {code_ok}")

    print("lint_render — fences, comments, tables, lists, scene breaks, dialogue")
    from bookkit.segment import segment_text
    import lint_render as lr

    def lint(text: str) -> list:
        recs = segment_text(text, "u", "u.md")
        return (lr.check_setext_hazard(recs) + lr.check_fences(recs, "u.md")
                + lr.check_html_comments(recs, "u.md") + lr.check_tables(recs, "u.md")
                + lr.check_lists(recs, "u.md") + lr.check_dialogue(recs, "u.md"))

    nested = "Intro.\n\n````markdown\n```python\nx = 1\n```\n````\n\nAfter the block.\n"
    recs = segment_text(nested, "u", "u.md")
    inner = next(r for r in recs if r.text == "```")
    check("a ```` fence quoting a ``` block stays code until ````",
          inner.kind == "code" and not inner.fence
          and next(r for r in recs if r.text == "````").fence == "close"
          and next(r for r in recs if r.text == "After the block.").kind == "para"
          and not lint(nested), f"{[(r.line, r.kind, r.fence) for r in recs]}")
    mermaid = "```mermaid\nA --> B\n```\n\n```html\n<!-- example only\n```\n\nText.\n"
    check("comment markers inside fences are ignored (G5)",
          not [f for f in lint(mermaid) if f.check == "unbalanced-comment"],
          str([(f.check, f.location) for f in lint(mermaid)]))
    check("`<!-- a <!-- b -->` is one closed comment, not a critical",
          not [f for f in lint("Text <!-- a <!-- b --> more.\n") if f.severity == "critical"])
    check("an unclosed `<!--` is still critical",
          any(f.severity == "critical" for f in lint("Text <!-- never closed.\n\nMore.\n")))
    check("a lone `| row |` is flagged, not passed silently",
          any(f.check == "table-no-separator" for f in lint("Intro.\n\n| MG-7 | x | y |\n")))
    wrapped = ("Steps:\n\n- first item that wraps\n  onto a second line\n- second item\n"
               "lazily continued\n- third\n")
    check("a wrapped list item is not 'list-no-blank-line'",
          not [f for f in lint(wrapped) if f.check == "list-no-blank-line"],
          str([(f.check, f.location) for f in lint(wrapped)]))
    check("a list glued to a paragraph is still flagged",
          any(f.check == "list-no-blank-line" for f in lint("A paragraph.\n- a bullet\n")))
    scene = "Ella cerró la puerta.\n\n* * *\n\nA la mañana siguiente.\n\n***\n\nOtra escena.\n"
    check("`* * *` / `***` are scene breaks, not lists or findings",
          not lint(scene) and [r.kind for r in segment_text(scene) if "*" in r.text] == ["hr", "hr"])
    check("`1999. Ese año…` is flagged as an accidental ordered list",
          any(f.check == "ordered-list-hazard" and f.severity == "major"
              for f in lint("Intro.\n\n1999. Ese fue el año.\n")))
    glued = "Juan entró en la cocina.\n—Hola —dijo.\n\nElla miró\n—y se fue sin más.\n"
    hits = [f for f in lint(glued) if f.check == "dialogue-glued"]
    check("dialogue glued to narration is flagged; a wrapped inciso is not",
          len(hits) == 1 and hits[0].location == "u.md:2", str([(f.location) for f in hits]))

    print("lint_render — encodings: BOM and cp1252 are handled, never a crash (G15)")
    enc = tmp / "enc"
    (enc / "final").mkdir(parents=True)
    (enc / "final" / "unit-01.md").write_bytes("﻿# Capítulo uno\n\nTexto.\n".encode("utf-8"))
    (enc / "final" / "unit-02.md").write_bytes("# Capítulo 2\n\nAcción y canción.\n".encode("cp1252"))
    out3 = tmp / "enc.json"
    code, log = run("lint_render.py", ["--root", str(enc), "--units", "final/*.md",
                                       "--json", str(out3), "--fail-on", "never", "--quiet"])
    data = json.loads(out3.read_text("utf-8")) if out3.exists() else {"findings": []}
    check("a cp1252 unit is a major `encoding` finding, not a crash",
          code == 0 and [f["location"] for f in data["findings"] if f["check"] == "encoding"]
          == ["final/unit-02.md:1"], log[-300:])
    check("a BOM does not break the first heading",
          not [f for f in data["findings"] if f["location"].startswith("final/unit-01")],
          str(data["findings"]))


# ---------------------------------------------------------------------------
# The text layer and bookkit
# ---------------------------------------------------------------------------


def test_text_layer(tmp: Path) -> None:
    print("\nbookkit — fingerprints, encodings, language, paths, schema")
    import unicodedata
    from bookkit import schema, textio
    from bookkit.anchors import blocks_for, resolve_anchor
    from bookkit.project import as_list, load_project, natural_key, unit_number
    from bookkit.textmetrics import fingerprint, fingerprint_code

    check("a code-span fix changes the fingerprint (G9)",
          fingerprint("The watermark uses `Peek(v,-1)` here.")
          != fingerprint("The watermark uses `Peek(v,1)` here."))
    check("case inside code spans is kept (G9)",
          fingerprint("Use `SELECT` here.") != fingerprint("Use `select` here."))
    check("prose case and markup still fold",
          fingerprint("The **Engine** returns rows.") == fingerprint("the engine returns rows"))
    check("an operator edit in a code block changes its fingerprint",
          fingerprint_code("if a >= b:") != fingerprint_code("if a < b:"))
    nfc = "La canción está lista."
    check("NFC and NFD spellings fingerprint alike",
          fingerprint(nfc) == fingerprint(unicodedata.normalize("NFD", nfc)))

    f = tmp / "bom.md"
    f.write_bytes("﻿# Título\r\n".encode("utf-8"))
    check("textio strips the BOM and CRLF", textio.read_text(f) == "# Título\n")

    root = tmp / "lang"
    (root / "final").mkdir(parents=True)
    (root / "bible").mkdir()
    (root / "final" / "unit-01.md").write_text("# x\n", encoding="utf-8")
    meta = root / "bible" / "meta.yaml"
    cases = [("project:\n  language: es\n  language_variant: es-AR\n", "es-AR"),
             ("conventions:\n  language_variant: en-GB\n", "en-GB"),
             ("project:\n  language: pt\n", "pt"), ("{}\n", "en-US")]
    got = []
    for text, _want in cases:
        meta.write_text(text, encoding="utf-8")
        got.append(load_project(root).language_variant)
    check("language_variant: project → conventions → project.language → en-US (G6)",
          got == [w for _t, w in cases], str(got))

    check("as_list never iterates a string (G16)", as_list("ch-03") == ["ch-03"])
    check("unit ids match on the number: `01`, 1, `unit-01` (G13)",
          unit_number("01") == unit_number(1) == unit_number("unit-01") == 1)
    check("natural sort puts ch-2 before ch-10",
          sorted(["ch-10", "ch-2", "ch-1"], key=natural_key) == ["ch-1", "ch-2", "ch-10"])

    # G14 — final/ as a junction (Windows) or symlink.
    jroot, jtarget = tmp / "jroot", tmp / "jtarget"
    jroot.mkdir()
    jtarget.mkdir()
    (jtarget / "unit-01.md").write_text("# u\n", encoding="utf-8")
    linked = False
    try:
        import _winapi  # type: ignore
        _winapi.CreateJunction(str(jtarget), str(jroot / "final"))
        linked = True
    except (ImportError, OSError, AttributeError):
        try:
            os.symlink(jtarget, jroot / "final", target_is_directory=True)
            linked = True
        except OSError:
            pass
    if linked:
        p = load_project(jroot)
        check("final/ as a junction keeps repo-relative paths (G14)",
              p.rel(p.unit_paths[0]) == "final/unit-01.md", p.rel(p.unit_paths[0]))
    else:
        print("  SKIP  junction test — this platform cannot create a junction or symlink")

    bad = {"check": "MG-2", "lens": "pairs", "subject": "x", "findings": [
        {**finding("Critical")}]}
    good = {"check": "MG-2", "lens": "pairs", "subject": "x", "findings": [finding("major")]}
    check("fallback validator rejects `severity: Critical` (G11)",
          bool(schema.validate(bad, force_fallback=True)))
    check("fallback validator accepts a valid file",
          not schema.validate(good, force_fallback=True),
          str(schema.validate(good, force_fallback=True)))
    check("fallback validator rejects an unknown top-level key",
          bool(schema.validate({**good, "verdict": "x"}, force_fallback=True)))

    a = tmp / "anch.md"
    a.write_text("# U\n\nThe **outer** aggregation sees it.\n\n```sql\nLOAD a\nRESIDENT b;\n```\n",
                 encoding="utf-8")
    blocks = blocks_for(a)
    check("an anchor spanning two code lines resolves (not EDITED)",
          resolve_anchor(blocks, 6, "LOAD a RESIDENT b;").status == "OK")
    check("an anchor quoted without markdown still resolves",
          resolve_anchor(blocks, 3, "The outer aggregation sees it").status == "OK")

    # gitblame: a repeated commit keeps ITS date, not the last one printed.
    if shutil.which("git"):
        from bookkit.gitblame import blame_map
        g = tmp / "blame"
        g.mkdir()

        def git(*args, date="2020-01-01T12:00:00+0000"):
            subprocess.run(["git", *args], cwd=g, capture_output=True,
                           env={**os.environ, "GIT_AUTHOR_DATE": date, "GIT_COMMITTER_DATE": date,
                                "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
                                "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"})
        git("init", "-q")
        (g / "f.md").write_text("a1\na2\na3\n", encoding="utf-8")
        git("add", ".")
        git("commit", "-qm", "A")
        (g / "f.md").write_text("a1\nb2\na3\n", encoding="utf-8")
        git("commit", "-qam", "B", date="2021-06-01T12:00:00+0000")
        bm = blame_map(g, "f.md")
        check("git blame: line 3 of commit A keeps A's date, not B's",
              bm.get(3, ("", ""))[1] == "2020-01-01" and bm.get(2, ("", ""))[1] == "2021-06-01",
              str(bm))

    print("bootstrap_probes — Unicode words and a deterministic probe file")
    import bootstrap_probes as bp
    check("WORD_RE keeps accented words whole",
          bp.WORD_RE.findall("maría canción") == ["maría", "canción"])
    bdir = tmp / "boot"
    shutil.copytree(FIXTURES, bdir)
    outs = []
    for seed in ("1", "2"):
        run("bootstrap_probes.py", ["--root", str(bdir), "--units", "final/unit-*.md",
                                    "--source", "frequency", "--force"], env={"PYTHONHASHSEED": seed})
        outs.append((bdir / "bible" / "concept-probes.yaml").read_text("utf-8"))
    check("the probe file does not depend on PYTHONHASHSEED", outs[0] == outs[1])


# ---------------------------------------------------------------------------
# Rule extraction
# ---------------------------------------------------------------------------


def test_rule_extraction(tmp: Path) -> None:
    print("\nextract_rule_candidates — rule shapes and quota stratification")
    out = tmp / "rules"
    run("extract_rule_candidates.py", ["--root", str(FIXTURES), "--units", "final/unit-*.md",
                                       "--out", str(out), "--min-instances", "1"])
    names = {p.stem for p in out.glob("*.md")} - {"_index"}
    check("rule stated as a consequence is emitted", any("upper" in e for e in names),
          f"emitted: {sorted(names)}")
    check("rule that demonstrates its construct is emitted",
          any("orderdate" in e for e in names), f"emitted: {sorted(names)}")

    from bookkit.selection import stratified_top
    fake = [("cross", i) for i in range(90)] + [("intra", i) for i in range(10)]
    sel = stratified_top(fake, lambda t: t[0], lambda t: t[1], quota=20,
                         weights={"cross": 1.0, "intra": 1.0})
    check("both strata survive a tight quota", {k for k, _ in sel.emitted} == {"cross", "intra"})
    check("the scarce stratum is not truncated",
          sum(1 for k, _ in sel.emitted if k == "intra") == 10)
    check("selection reports what it dropped", sel.dropped_total == 80, str(sel.dropped_total))

    print("extract_rule_candidates — content ids, --report, order, language")
    work = tmp / "rules-ids"
    shutil.copytree(FIXTURES, work)
    args = ["--root", str(work), "--units", "final/unit-*.md", "--min-instances", "1"]
    c1 = tmp / "c1.json"
    run("extract_rule_candidates.py", args + ["--coverage", str(c1)])
    u1 = work / "final" / "unit-01.md"
    u1.write_text("# Inserted\n\nThree new lines.\n\n" + u1.read_text("utf-8"), encoding="utf-8")
    c2 = tmp / "c2.json"
    run("extract_rule_candidates.py", args + ["--coverage", str(c2)])
    ids = [sorted(s["id"] for s in json.loads(p.read_text("utf-8"))["eligible"]) for p in (c1, c2)]
    check("rule ids survive lines inserted above the rule (G10)", ids[0] == ids[1] and ids[0],
          str(ids))
    rep = tmp / "rep"
    run("extract_rule_candidates.py", args + ["--report", "--out", str(rep),
                                              "--coverage", str(tmp / "rep.json")])
    check("--report writes no files, even with --out/--coverage",
          not rep.exists() and not (tmp / "rep.json").exists())

    import extract_rule_candidates as erc
    from bookkit.project import load_project
    nat = tmp / "nat"
    (nat / "final").mkdir(parents=True)
    for n in (1, 2, 10):
        (nat / "final" / f"ch-{n}.md").write_text(f"# Ch {n}\n", encoding="utf-8")
    check("extractors walk units in reading order (ch-2 before ch-10)",
          list(erc.load_records(load_project(nat))) == ["ch-1", "ch-2", "ch-10"])

    es = tmp / "es"
    (es / "final").mkdir(parents=True)
    (es / "bible").mkdir()
    (es / "bible" / "meta.yaml").write_text("project:\n  language_variant: es-AR\n", "utf-8")
    body = ("# Capítulo 1\n\nNunca uses `Now()` dentro de una expresión cacheada.\n\n"
            + "".join(f"## Ejemplo {i}\n\n```sql\nSELECT Now() FROM t{i};\n```\n\n"
                      for i in range(3)))
    (es / "final" / "unit-01.md").write_text(body, encoding="utf-8")
    ces = tmp / "es.json"
    code, log = run("extract_rule_candidates.py", ["--root", str(es), "--coverage", str(ces)])
    rec = json.loads(ces.read_text("utf-8")) if ces.exists() else {}
    check("a Spanish rule is extracted with the es pack (G7)",
          rec.get("pack") == "es" and any("now" in s["id"] for s in rec.get("eligible", [])),
          log[-300:])
    (es / "bible" / "meta.yaml").write_text("project:\n  language_variant: pt-BR\n", "utf-8")
    code, log = run("extract_rule_candidates.py", ["--root", str(es), "--coverage", str(ces)])
    rec = json.loads(ces.read_text("utf-8")) if ces.exists() else {}
    check("no pack → language-agnostic pairing, and it says so (not '0 = complete')",
          rec.get("mode") == "language-agnostic" and rec.get("eligible")
          and "no language pack" in log, log[-300:])

    tuned = tmp / "tuned"
    shutil.copytree(FIXTURES, tuned)
    targs = ["--root", str(tuned), "--units", "final/unit-*.md"]
    ct = tmp / "ct.json"
    run("extract_rule_candidates.py", targs + ["--min-instances", "1", "--coverage", str(ct)])
    rid = next(s["id"] for s in json.loads(ct.read_text("utf-8"))["eligible"] if "upper" in s["id"])
    (tuned / "bible").mkdir(exist_ok=True)
    (tuned / "bible" / "rule-probes-tuned.yaml").write_text(
        f"rules:\n  - id: {rid}\n    scope_units: unit-02\n    require_terms: NoSuchTerm\n", "utf-8")
    run("extract_rule_candidates.py", targs + ["--coverage", str(ct)])
    elig = {s["id"]: s for s in json.loads(ct.read_text("utf-8"))["eligible"]}
    check("a rule narrowed below --min-instances stays in the denominator; string "
          "`scope_units` is one unit (G16)", rid in elig and elig[rid]["instances"] == 0,
          str(elig.get(rid)))


# ---------------------------------------------------------------------------
# Claim index
# ---------------------------------------------------------------------------


def test_propagation(tmp: Path) -> None:
    print("\nclaim index — MOVED repairs, CHANGED propagates")
    import yaml
    work = tmp / "book"
    shutil.copytree(FIXTURES, work)
    args = ["--root", str(work), "--units", "final/unit-*.md"]
    absent = tmp / "ci-absent.json"
    run("validate_claim_index.py", args + ["--json", str(absent), "--quiet"])
    check("the validator writes JSON even with no index yet",
          absent.exists() and json.loads(absent.read_text("utf-8")).get("absent") is True)

    run("bootstrap_probes.py", args + ["--source", "frequency", "--min-units", "2"])
    code, log = run("build_concept_dossier.py", args + ["--emit-index", "--no-blame"])
    index = work / "bible" / "claim-index.yaml"
    check("claim index generated", index.exists(), log.strip()[-300:])
    if not index.exists():
        return
    code, log = run("validate_claim_index.py", args)
    check("clean corpus validates", "consistent" in log, log.strip()[-200:])

    target = work / "final" / "unit-02.md"
    target.write_text("# Inserted heading\n\nInserted paragraph.\n\n"
                      + target.read_text("utf-8"), encoding="utf-8")
    code, log = run("validate_claim_index.py", args)
    check("a moved passage reports MOVED, not CHANGED", "MOVED" in log and "CHANGED" not in log)
    run("validate_claim_index.py", args + ["--fix"])
    code, log = run("validate_claim_index.py", args)
    check("--fix repairs moved locations", "consistent" in log, log.strip()[-200:])

    parsed = yaml.safe_load(index.read_text("utf-8"))
    victim = next(((cid, s) for cid, e in (parsed.get("concepts") or {}).items()
                   for s in e.get("sites") or [] if s.get("related")), None)
    if not victim:
        check("a concept with siblings exists in the fixture", False, "fixture too small")
        return
    cid, site = victim
    path_str, _, line_str = site["location"].rpartition(":")
    lines = (work / path_str).read_text("utf-8").splitlines()
    lines[int(line_str) - 1] += " An edit that changes what this passage claims."
    (work / path_str).write_text("\n".join(lines) + "\n", encoding="utf-8")
    code, log = run("validate_claim_index.py", args)
    check("an edited passage reports CHANGED", "CHANGED" in log)
    check("PROPAGATE names the siblings", "PROPAGATE" in log)
    check("validator warns without breaking the build", code == 0, f"exit {code}")

    print("claim index — human metadata survives a concept with no claims this run")
    parsed["concepts"]["ghost_concept"] = {"name": "ghost", "do_not_touch": True,
                                           "note": "refuted on 2026-01-01", "sites": []}
    index.write_text(yaml.safe_dump(parsed, allow_unicode=True, sort_keys=False), "utf-8")
    probes = work / "bible" / "concept-probes-tuned.yaml"
    probes.write_text("probes:\n  - id: ghost_concept\n    include: 'zzqqxx'\n", "utf-8")
    run("build_concept_dossier.py", args + ["--emit-index", "--no-blame"])
    ghost = (yaml.safe_load(index.read_text("utf-8")).get("concepts") or {}).get("ghost_concept")
    check("do_not_touch/note kept when the concept has no claims", bool(ghost)
          and ghost.get("do_not_touch") is True and ghost.get("note"), str(ghost))


# ---------------------------------------------------------------------------
# The manuscript gate
# ---------------------------------------------------------------------------


def test_manuscript_gate(tmp: Path) -> None:
    print("\nmanuscript_gate — deterministic sweep")
    work = tmp / "gate"
    shutil.copytree(FIXTURES, work)
    write_meta(work)
    code, log = run("manuscript_gate.py", ["--root", str(work), "--units", "final/unit-*.md",
                                           "--date", DATE, "--deterministic-only"])
    mg5 = next((line for line in log.splitlines() if line.startswith("[gate] MG-5:")), "")
    check("gate runs the deterministic sweep", bool(mg5), log.strip()[-300:])
    n_crit = int(mg5.split("MG-5:")[1].split("critical")[0].strip()) if mg5 else 0
    check("gate surfaces the fixture's criticals", n_crit >= 1, mg5)
    check("--deterministic-only exits 1 on an open critical (G16: never always 0)",
          code == 1, f"exit {code}")
    check("--deterministic-only touches no round",
          not rdir(work, 1).exists() and not (rdir(work, 1).parent / "state.json").exists())

    print("manuscript_gate — default run directory")
    work2 = corpus(tmp, "defaultdir")
    run("manuscript_gate.py", ["--root", str(work2), "--units", "final/*.md", "--round", "1"])
    check("with no --date the run dir is reviews/manuscript-gate-current",
          (work2 / "reviews" / "manuscript-gate-current" / "state.json").exists(),
          str(list((work2 / "reviews").glob("*"))))


def test_verification_plan(tmp: Path) -> None:
    print("\nmanuscript_gate — unsettled questions become a plan, append-only (G8)")
    work = corpus(tmp, "plan")
    gate(work, "--round", "1")
    deferred = [
        {"question": "Does the live system behave as unit-02 claims?",
         "why_unresolved": "no access here", "needs": "runner",
         "sites": ["final/unit-02.md:10"], "how_to_check": "run the snippet",
         "expected": "x", "defect_if": "y"},
        {"question": "Does the approval flow really take three days?",
         "why_unresolved": "internal process claim", "needs": "person",
         "sites": ["final/unit-02.md:20"]},
        {"question": "Recommend pattern A or B?", "why_unresolved": "editorial choice",
         "needs": "human-decision", "sites": ["final/unit-03.md:30"]}]
    write_doc(rdir(work, 1), "demo.source.p1.json", {"check": "MG-1", "lens": "source",
                                                     "subject": "demo", "findings": [],
                                                     "deferred": deferred})
    code, log = gate(work, "--round", "1", "--verdict-only")
    plan = work / "reviews" / "verification-plan" / "PLAN.md"
    check("plan is generated from deferred items", plan.exists(), log.strip()[-300:])
    if not plan.exists():
        return
    text = plan.read_text("utf-8")
    check("a runner question becomes an entry", "live system behave" in text)
    check("a NON-code question becomes an entry too", "approval flow" in text)
    check("a human decision stays OUT of the plan", "pattern A or B" not in text)
    check("missing fields are marked TODO, not dropped", "**TODO**" in text)

    plan.write_text(text.replace("**Actual result:**\n", "**Actual result:** 42 rows\n", 1), "utf-8")
    write_doc(rdir(work, 1), "demo2.source.p1.json", {
        "check": "MG-1", "lens": "source", "subject": "demo2", "findings": [],
        "deferred": [{"question": "How long does the nightly reload take?",
                      "why_unresolved": "never measured", "needs": "measurement"}]})
    gate(work, "--round", "1", "--verdict-only")
    text2 = plan.read_text("utf-8")
    check("a filled result survives the next run (PLAN.md is never overwritten)",
          "**Actual result:** 42 rows" in text2)
    check("new questions are appended once, old ones not duplicated",
          "nightly reload" in text2 and text2.count("live system behave") == 1)


def test_coverage_verdict(tmp: Path) -> None:
    print("\nmanuscript_gate — the verdict knows how much it did NOT look at")
    work = corpus(tmp, "cov")
    rd = rdir(work, 1)
    gate(work, "--round", "1", "--top-concepts", "1")
    cov = json.loads((rd / "coverage-MG-1.json").read_text("utf-8"))
    check("the emitter writes a coverage record", len(cov.get("eligible", [])) > 0)
    check("eligible is bigger than emitted under a tight quota",
          len(cov["eligible"]) > len(cov["emitted"]),
          f"{len(cov['emitted'])}/{len(cov['eligible'])}")
    check("what was cut is recorded, ranked", bool(cov.get("cut")))
    audit_all(work, 1)
    code, log = gate(work, "--round", "1", "--verdict-only")
    check("a partial sweep with zero findings is PASS-PARTIAL, never PASS",
          verdict(log) == "PASS-PARTIAL", f"got {verdict(log)}")
    check("PASS-PARTIAL names the numbers, not just the state",
          "coverage" in log.lower() and "/" in log)
    check("PASS-PARTIAL without a waiver is not converged (exit 1)", code == 1 and not converged(log))

    print("manuscript_gate — full coverage with no findings IS a PASS")
    work2 = corpus(tmp, "cov-full")
    gate(work2, "--round", "1")
    audit_all(work2, 1)
    code, log = gate(work2, "--round", "1", "--verdict-only")
    check("no quota, no sampling, every subject audited -> PASS", verdict(log) == "PASS",
          f"got {verdict(log)}: {log.strip()[-400:]}")

    print("manuscript_gate — a subject nobody audited does not count as covered")
    work3 = corpus(tmp, "cov-gap")
    rd3 = rdir(work3, 1)
    gate(work3, "--round", "1")
    audit_all(work3, 1)
    victim = emitted(rd3, "MG-1")[-1]
    for p in rd3.glob(f"findings/{victim}.*.json"):
        p.unlink()
    code, log = gate(work3, "--round", "1", "--verdict-only")
    check("one missing findings file blocks the PASS", verdict(log) == "PASS-PARTIAL")
    (rd3 / "findings" / f"{emitted(rd3, 'MG-1')[0]}.pairs.p2.json").unlink()
    gate(work3, "--round", "1", "--verdict-only")
    subj = json.loads((rd3.parent / "subjects.json").read_text("utf-8"))["checks"]["MG-1"]
    check("one pass of two is 'partly read', not audited (passes_per_subject)",
          subj[emitted(rd3, "MG-1")[0]].get("reason") == "passes 1/2",
          str(subj.get(emitted(rd3, "MG-1")[0])))


def _intractable_corpus(tmp: Path, name: str, tuned: str = "") -> Path:
    """One rule too wide for one agent run: three key terms whose union exceeds the
    tractability ceiling while each stays under the --df-ceiling."""
    work = tmp / name
    (work / "final").mkdir(parents=True)
    (work / "bible").mkdir(parents=True)
    L = ["# Unit 01", "", "## The rule", "",
         "You must never call `AlphaFn`, `BetaFn` or `GammaFn` on a loaded field.", ""]
    for i, mark in enumerate(["AlphaFn"] * 18 + ["BetaFn"] * 18 + ["GammaFn"] * 18 + [""] * 86):
        L += [f"## Example {i}", "", "```sql", f"LOAD {mark or 'Plain'}(Field) RESIDENT Stage{i};",
              "```", ""]
    (work / "final" / "unit-01.md").write_text("\n".join(L), encoding="utf-8")
    (work / "bible" / "concept-probes.yaml").write_text(
        "probes:\n  - id: loaded_field\n    include: 'loaded field'\n", encoding="utf-8")
    write_meta(work)
    if tuned:
        (work / "bible" / "rule-probes-tuned.yaml").write_text(tuned, encoding="utf-8")
    return work


def test_depth_axis(tmp: Path) -> None:
    print("\nmanuscript_gate — subjects read only in part")
    work = _intractable_corpus(tmp, "depth")
    rd = rdir(work, 1)
    gate(work, "--round", "1")
    cov = json.loads((rd / "coverage-MG-2.json").read_text("utf-8"))
    check("the wide rule is eligible and emitted", len(cov["emitted"]) == 1, str(cov["emitted"]))
    check("it is flagged as judgeable only from a sample",
          sum(1 for s in cov["eligible"] if s["sampled"]) == 1)
    proposed = rd / "rule-probes-proposed.yaml"
    check("the intractable rule gets a worklist entry",
          proposed.exists() and "AlphaFn" in proposed.read_text("utf-8"))
    write_doc(rd, "manuscript.whole-book-read.p1.json", {
        "check": "MG-4", "lens": "whole-book-read", "subject": "manuscript", "findings": []})
    code, log = gate(work, "--round", "1", "--verdict-only")
    check("an unopened subject keeps the gate at PASS-PARTIAL", verdict(log) == "PASS-PARTIAL")
    clean_files(rd, "MG-2", cov["emitted"], lens="rule-vs-instance", sampled=True)
    code, log = gate(work, "--round", "1", "--verdict-only")
    subj = json.loads((rd.parent / "subjects.json").read_text("utf-8"))["checks"]["MG-2"]
    # v3.4: PASS-SAMPLED merged into PASS-PARTIAL; the equivalent assertion is that
    # the subject is recorded as partly read (sampled), not as never opened.
    check("every subject opened but one only sampled -> PASS-PARTIAL, recorded as sampled",
          verdict(log) == "PASS-PARTIAL" and subj[cov["emitted"][0]]["state"].startswith("sampled@"),
          f"got {verdict(log)} / {subj}")
    check("the verdict names the way out of a sampled rule", "rule-probes-tuned" in log)

    print("manuscript_gate — narrowing the rule closes it by work")
    rid = cov["emitted"][0]
    work2 = _intractable_corpus(tmp, "depth-tuned", tuned=(
        f"rules:\n  - id: {rid}\n    key_terms: [AlphaFn]\n"
        "    note: the rule is about AlphaFn; the other two are taught elsewhere\n"))
    rd2 = rdir(work2, 1)
    code, log = gate(work2, "--round", "1")
    cov2 = json.loads((rd2 / "coverage-MG-2.json").read_text("utf-8"))
    check("a tuned probe brings the rule under the ceiling",
          not any(s["sampled"] for s in cov2["eligible"]), log.strip()[-300:])
    audit_all(work2, 1)
    code, log = gate(work2, "--round", "1", "--verdict-only")
    check("depth closed by WORK reaches a real PASS", verdict(log) == "PASS",
          f"got {verdict(log)}: {log.strip()[-400:]}")


def test_pool_drains(tmp: Path) -> None:
    print("\nmanuscript_gate — round 2 audits what round 1 did not")
    work = corpus(tmp, "drain")
    gate(work, "--round", "1", "--top-concepts", "1")
    first = emitted(rdir(work, 1), "MG-1")
    clean_files(rdir(work, 1), "MG-1", first)
    gate(work, "--round", "1", "--verdict-only")
    check("the subjects manifest is persisted", (rdir(work, 1).parent / "subjects.json").exists())
    gate(work, "--round", "2", "--top-concepts", "1")
    r1 = json.loads((rdir(work, 1) / "coverage-MG-1.json").read_text("utf-8"))
    r2 = json.loads((rdir(work, 2) / "coverage-MG-1.json").read_text("utf-8"))
    check("round 2 selects different subjects",
          bool(r2["emitted"]) and not set(r2["emitted"]) & set(first),
          f"round 1 {first}, round 2 {r2['emitted']}")
    check("already-audited subjects stay in the denominator",
          len(r2["eligible"]) == len(r1["eligible"]))
    check("coverage grows between rounds", r2["already_audited"] == sorted(first),
          str(r2["already_audited"]))
    dossier = (rdir(work, 1) / "dossiers" / f"{first[0]}.md").read_text("utf-8")
    loc = next(line for line in dossier.splitlines() if line.startswith("### final/")).split()[1]
    rel, _, ln = loc.rpartition(":")
    lines = (work / rel).read_text("utf-8").splitlines()
    lines[int(ln) - 1] += " An edit that changes what this passage claims."
    (work / rel).write_text("\n".join(lines) + "\n", encoding="utf-8")
    gate(work, "--round", "3", "--top-concepts", "1")
    r3 = json.loads((rdir(work, 3) / "coverage-MG-1.json").read_text("utf-8"))
    check("an edited subject is re-queued", first[0] in r3["requeued"], str(r3["requeued"]))


def test_convergence(tmp: Path) -> None:
    print("\nmanuscript_gate — G1: BLOCKED never converges; G3: open findings persist")
    work = corpus(tmp, "g1")
    gate(work, "--round", "1")
    audit_all(work, 1, mg4=[finding("critical")])
    logs = [gate(work, "--round", "1", "--verdict-only") for _ in range(3)]
    check("3x --verdict-only on a BLOCKED round never converges (G1/G2)",
          all(verdict(l) == "BLOCKED" and not converged(l) and c == 1 for c, l in logs),
          str([(c, verdict(l)) for c, l in logs]))
    for n in (2, 3):
        code, log = gate(work, "--round", str(n))
    check("a round-1 critical is still open in round 3 (G3)", verdict(log) == "BLOCKED",
          f"got {verdict(log)}")
    check("two quiet rounds do not converge a BLOCKED book (G1)",
          not converged(log) and code == 1, log.strip()[-300:])
    key = next(r["key"] for r in store(work) if r["check"] == "MG-4")
    code, log = run("manuscript_gate.py", ["--root", str(work), "--units", "final/*.md",
                                           "--date", DATE, "--resolve", key, "--status",
                                           "accepted-risk", "--note", "shipping anyway"])
    check("a critical cannot be accepted as a risk", code == 2, log[-200:])
    run("manuscript_gate.py", ["--root", str(work), "--units", "final/*.md", "--date", DATE,
                               "--resolve", key, "--status", "refuted", "--note",
                               "unit-02 §3 deploys it; the reader skipped a page"])
    code, log = gate(work, "--round", "3", "--verdict-only")
    check("--resolve refuted clears the block; the refuted finding was never new blocking",
          verdict(log) == "PASS" and converged(log) and code == 0,
          f"{code} {verdict(log)}: {log.strip()[-300:]}")
    check("the refuted finding reaches GROUNDING.md as an accepted item",
          key in (rdir(work, 1).parent / "GROUNDING.md").read_text("utf-8"))

    print("manuscript_gate — G2: rounds, not invocations; MG-5 counts as new blocking")
    work = corpus(tmp, "g2")
    u3 = work / "final" / "unit-03.md"
    good = u3.read_text("utf-8")
    u3.write_text(good + "\nThis paragraph prints as a heading.\n---\n", encoding="utf-8")
    gate(work, "--round", "1")
    audit_all(work, 1, mg4=[finding("major", quote="step three is missing")])
    for _ in range(3):
        code, log = gate(work, "--round", "1", "--verdict-only")
    st = state(work)
    check("an MG-5 critical counts as new blocking in its round",
          st["rounds"]["1"]["new_blocking"] >= 2, str(st["rounds"]["1"]))
    u3.write_text(good, encoding="utf-8")
    gate(work, "--round", "2")
    rd2 = rdir(work, 2)
    clean_files(rd2, "MG-1", emitted(rd2, "MG-1"))
    clean_files(rd2, "MG-2", emitted(rd2, "MG-2"), lens="rule-vs-instance")
    write_doc(rd2, "manuscript.whole-book-read.p1.json", {
        "check": "MG-4", "lens": "whole-book-read", "subject": "manuscript", "findings": []})
    logs = [gate(work, "--round", "2", "--verdict-only") for _ in range(3)]
    check("the re-read that no longer reports a finding closes it (G3)",
          all(r["status"] == "fixed" for r in store(work) if r["check"] == "MG-4"),
          str([(r["key"], r["status"]) for r in store(work)]))
    check("PASS after one quiet round is not converged, however often re-run (G2)",
          all(verdict(l) == "PASS" and not converged(l) for _c, l in logs),
          str([verdict(l) for _c, l in logs]))
    code, log = gate(work, "--round", "3")
    check("two consecutive quiet ROUNDS converge (exit 0)", converged(log) and code == 0,
          log.strip()[-300:])


def test_loud_failures(tmp: Path) -> None:
    print("\nmanuscript_gate — G4: tool failures are loud, stale outputs never reused")
    root = tmp / "g4"
    (root / "final").mkdir(parents=True)
    write_meta(root, HEAD + "project:\n  profile: book-technical\n  language_variant: es-AR\n")
    (root / "final" / "unit-01.md").write_text(
        "# Capítulo\n\nEste párrafo se imprime como título.\n---\n\nTexto.\n", encoding="utf-8")
    (root / "final" / "unit-02.md").write_bytes("# Capítulo 2\n\nAcción y canción.\n".encode("cp1252"))
    code, log = gate(root, "--round", "1")
    check("a cp1252 unit does not crash MG-5: its critical and the encoding major surface",
          verdict(log) == "BLOCKED" and code == 1
          and any(r["relation"] == "encoding" for r in store(root)), log.strip()[-300:])

    work = corpus(tmp, "g4b")
    gate(work, "--round", "1")
    fd = rdir(work, 1) / "fixed-defects.json"
    ok_before = fd.exists()
    (work / "bible").mkdir(exist_ok=True)
    (work / "bible" / "fixed-defects.yaml").write_text("defects: [unclosed\n", encoding="utf-8")
    code, log = gate(work, "--round", "1")
    check("a crashed tool makes the verdict ERROR and exits 2",
          verdict(log) == "ERROR" and code == 2 and "MG-7" in log, log.strip()[-300:])
    check("the stale output of the earlier run is deleted, not reused",
          ok_before and not fd.exists())

    code, log = gate(corpus(tmp, "g4c"), "--round", "1", "--verdict-only")
    check("--verdict-only on a round never swept is ERROR, never '{}'",
          verdict(log) == "ERROR" and code == 2, log.strip()[-200:])

    work = corpus(tmp, "g4d")
    gate(work, "--round", "1")
    write_doc(rdir(work, 1), "manuscript.whole-book-read.p1.json", {
        "check": "MG-4", "lens": "whole-book-read", "subject": "manuscript",
        "findings": [finding("Critical")]})
    code, log = gate(work, "--round", "1", "--verdict-only")
    check("`severity: Critical` is an ERROR naming the file, not zero criticals (G11)",
          verdict(log) == "ERROR" and "manuscript.whole-book-read.p1.json" in log, log[-300:])
    code, log = gate(work, "--round", "1")
    check("re-preparing a round that has findings is refused", code == 2 and "--verdict-only" in log)


TECH_META = HEAD + """project:
  profile: book-technical
  language_variant: en-US
validation_surface:
  surfaces:
    - surface: python_exec
      runner: reviewer-only
      executable: true
pipeline:
  manuscript_gate:
    checks:
      MG-4: false
"""


def test_gate_config(tmp: Path) -> None:
    print("\nmanuscript_gate — config: disabled checks, MG-6 plans, waivers, MG-3 ids (G13/G16)")
    work = corpus(tmp, "cfg", meta=TECH_META)
    (work / "outline").mkdir()
    (work / "outline" / "units.yaml").write_text(
        "units:\n  - unit: 02\n    exercises:\n      - prompt: build it\n", encoding="utf-8")
    gate(work, "--round", "1")
    audit_all(work, 1)
    write_doc(rdir(work, 1), "unit-02.exercise-coverage.p1.json", {
        "check": "MG-3", "lens": "exercise-coverage", "subject": "unit-02", "findings": []})
    code, log = gate(work, "--round", "1", "--verdict-only")
    keys = {r["key"]: r for r in store(work)}
    check("a check switched off without a waiver is a major finding",
          keys.get("MG-4-disabled", {}).get("status") == "open", str(list(keys)))
    check("MG-6: an executable surface with no runner and no waiver is major",
          any(r["check"] == "MG-6" and r["status"] == "open" for r in keys.values()))
    check("MG-3 matches `unit: 02` (YAML int) to findings for unit-02 (G13)",
          "MG-3 1/1 audited" in log, log.strip()[-500:])

    status = work / "project-status.yaml"
    status.write_text("waivers:\n"
                      "  - check: manuscript_gate.MG-4\n    reason: read by the author\n",
                      encoding="utf-8")
    code, log = gate(work, "--round", "1", "--verdict-only")
    keys = {r["key"]: r for r in store(work)}
    check("item 5: a waiver without who / what is owed does not count (MG-4 still disabled)",
          keys["MG-4-disabled"]["status"] == "open" and "does not count" in log,
          log.strip()[-300:])
    status.write_text("waivers:\n"
                      "  - check: manuscript_gate.MG-4\n    waived_by: \"N/A\"\n"
                      "    reason: \"x\"\n    debt: \"TBD\"\n", encoding="utf-8")
    code, log = gate(work, "--round", "1", "--verdict-only")
    keys = {r["key"]: r for r in store(work)}
    check("item 10: a waiver whose who/why/debt are placeholders (N/A, x, TBD) does not count",
          keys["MG-4-disabled"]["status"] == "open" and "placeholder" in log,
          log.strip()[-300:])
    status.write_text("waivers:\n"
                      "  - check: manuscript_gate.MG-4\n    waived_by: human\n"
                      "    reason: read by the author\n    debt: \"no MG-4 report\"\n",
                      encoding="utf-8")
    code, log = gate(work, "--round", "1", "--verdict-only")
    keys = {r["key"]: r for r in store(work)}
    check("item 10: reason / debt under 20 characters do not count",
          keys["MG-4-disabled"]["status"] == "open", log.strip()[-300:])
    status.write_text("waivers:\n"
                      "  - check: manuscript_gate.MG-4\n    waived_by: human\n"
                      "    reason: the author read the whole book twice\n"
                      "    debt: \"no MG-4 report in this run; a cold reader in v2\"\n"
                      "  - check: validation_surface.python_exec\n" + WAIVER,
                      encoding="utf-8")
    code, log = gate(work, "--round", "1", "--verdict-only")
    keys = {r["key"]: r for r in store(work)}
    check("a complete waiver silences the disabled-check finding",
          keys["MG-4-disabled"]["status"] == "fixed")
    check("an MG-6 waiver WITHOUT a plan does not count",
          any(r["check"] == "MG-6" and r["status"] == "open" for r in keys.values()))
    plan = work / "reviews" / "verification-plan" / "PLAN.md"
    plan.parent.mkdir(parents=True, exist_ok=True)
    plan.write_text("# plan\n", encoding="utf-8")
    status.write_text(status.read_text("utf-8") + "    plan: reviews/verification-plan/PLAN.md\n",
                      encoding="utf-8")
    code, log = gate(work, "--round", "1", "--verdict-only")
    check("item 5: an MG-6 waiver naming a plan FILE but no entry does not count",
          any(r["check"] == "MG-6" and r["status"] == "open" for r in store(work)),
          log.strip()[-300:])
    plan.write_text("# plan\n\n### V-01 — does the python sample run?\n", encoding="utf-8")
    status.write_text(status.read_text("utf-8").replace(
        "PLAN.md\n", "PLAN.md#V-01\n"), encoding="utf-8")
    code, log = gate(work, "--round", "1", "--verdict-only")
    check("an MG-6 waiver pointing at a plan entry that exists counts",
          not any(r["check"] == "MG-6" and r["status"] == "open" for r in store(work)),
          log.strip()[-300:])
    status.write_text(status.read_text("utf-8").replace("#V-01", "#V-07"), encoding="utf-8")
    gate(work, "--round", "1", "--verdict-only")
    key = next(r["key"] for r in store(work) if r["check"] == "MG-6" and r["status"] == "open")
    code, log = run("manuscript_gate.py", ["--root", str(work), "--units", "final/*.md",
                                           "--date", DATE, "--resolve", key, "--status",
                                           "accepted-risk", "--note", "later"])
    check("item 5: a configuration finding cannot be closed with --resolve", code == 2,
          log[-200:])

    print("manuscript_gate — item 5: code present, no validation surface declared")
    work = corpus(tmp, "nosurface", meta=HEAD + "project:\n  profile: book-technical\n"
                  "  language_variant: en-US\n")
    gate(work, "--round", "1")
    audit_all(work, 1)
    code, log = gate(work, "--round", "1", "--verdict-only")
    check("fenced ```sql with no surface declared → MG-6 major, not converged",
          any(r["key"] == "MG-6-no-surface" and r["status"] == "open" for r in store(work))
          and verdict(log) == "NEEDS-REVISION", log.strip()[-300:])
    (work / "bible" / "meta.yaml").write_text(
        HEAD + "project:\n  profile: book-technical\n  language_variant: en-US\npipeline:\n"
        "  manuscript_gate:\n    checks:\n      MG-6: false\n", encoding="utf-8")
    (work / "project-status.yaml").write_text(
        "waivers:\n  - check: manuscript_gate.MG-6\n" + WAIVER, encoding="utf-8")
    code, log = gate(work, "--round", "1", "--verdict-only")
    check("item 5: `checks.MG-6: false` with a waiver that has no plan entry is still major",
          any(r["key"] == "MG-6-disabled" and r["status"] == "open" for r in store(work)),
          log.strip()[-300:])

    print("manuscript_gate — ONE coverage waiver, any of several may match")
    work = corpus(tmp, "waiver")
    gate(work, "--round", "1", "--top-concepts", "1")
    audit_all(work, 1)
    code, log = gate(work, "--round", "1", "--verdict-only")
    sig = next(line.split("signature:")[1].split()[0] for line in log.splitlines()
               if "coverage signature:" in line)
    (work / "project-status.yaml").write_text(
        "waivers:\n  - check: manuscript_gate.coverage\n    signature: cov:000000000000\n"
        + WAIVER + f"  - check: manuscript_gate.coverage\n    signature: {sig}\n",
        encoding="utf-8")
    code, log = gate(work, "--round", "1", "--verdict-only")
    check("item 5: a matching coverage waiver without who / what is owed is not valid",
          "waiver valid" not in log, log.strip()[-300:])
    (work / "project-status.yaml").write_text(
        "waivers:\n  - check: manuscript_gate.coverage\n    signature: cov:000000000000\n"
        + WAIVER + f"  - check: manuscript_gate.coverage\n    signature: {sig}\n" + WAIVER,
        encoding="utf-8")
    code, log = gate(work, "--round", "1", "--verdict-only")
    check("the second, matching waiver is found (not only the first)", "waiver valid" in log,
          log.strip()[-300:])

    print("manuscript_gate — MG-4's subject is the manuscript hash")
    (work / "final" / "unit-02.md").write_text(
        (work / "final" / "unit-02.md").read_text("utf-8") + "\nOne more sentence.\n", "utf-8")
    gate(work, "--round", "2", "--top-concepts", "1")
    subj = json.loads((rdir(work, 1).parent / "subjects.json").read_text("utf-8"))["checks"]
    check("an edit anywhere sends the whole-book read back to pending (no '' fingerprint)",
          subj["MG-4"]["manuscript"].get("reason") == "edited-since-audit", str(subj["MG-4"]))
    check("re-preparing cleans stale dossiers",
          not (rdir(work, 2) / "dossiers").exists()
          or {p.stem for p in (rdir(work, 2) / "dossiers").glob("*.md")} - {"_index"}
          == set(emitted(rdir(work, 2), "MG-1")))


LIT_META = HEAD + "project:\n  profile: book-literary\n  language_variant: es-AR\n"
STORY_STUB = '''import argparse, json, sys
ap = argparse.ArgumentParser(); ap.add_argument("--root"); ap.add_argument("--json")
ap.add_argument("--manuscript", action="store_true"); a = ap.parse_args()
json.dump({"findings": [
  {"code": "ARC-NOT-RESOLVED", "severity": "blocking", "subject": "mariana",
   "detail": "the arc never resolves", "location": "bible/characters/mariana.md"},
  {"code": "SEEDS-MISSING", "severity": "warning", "subject": "meta", "detail": "4 of 5",
   "location": "bible/meta.yaml"}]}, open(a.json, "w", encoding="utf-8"))
sys.exit(1)
'''
FICTION_STUB = '''import argparse, json, sys
ap = argparse.ArgumentParser(); ap.add_argument("--root"); ap.add_argument("--json")
ap.add_argument("--book", action="store_true"); ap.add_argument("--units"); a = ap.parse_args()
json.dump({"findings": [
  {"rule": "gesture_tic", "severity": "major", "unit": "unit-01", "line": 3, "detail": "asiente x7"},
  {"rule": "dialogue_ratio", "severity": "info", "unit": "unit-01", "line": 0, "detail": "0.4"}],
  "stats": {}}, open(a.json, "w", encoding="utf-8"))
'''


def test_literary_branch(tmp: Path) -> None:
    print("\nmanuscript_gate — literary branch (MG-S, MG-T, MG-C; MG-1/2/3/6 n/a)")
    skill = tmp / "skill"
    shutil.copytree(HERE, skill / "scripts", ignore=shutil.ignore_patterns("__pycache__", "tests"))
    shutil.copytree(SKILL / "templates", skill / "templates")
    scripts = skill / "scripts"
    for s in ("check_story.py", "lint_fiction.py"):
        (scripts / s).unlink(missing_ok=True)
    work = tmp / "novela"
    (work / "final").mkdir(parents=True)
    (work / "bible").mkdir()
    (work / "bible" / "meta.yaml").write_text(LIT_META, encoding="utf-8")
    for n in (1, 2):
        (work / "final" / f"unit-{n:02d}.md").write_text(
            f"# Capítulo {n}\n\nMateo cerró la puerta.\n\n—Hola —dijo Mariana.\n", "utf-8")
    code, log = gate(work, "--round", "1", scripts=scripts)
    rd = rdir(work, 1)
    check("literary: no dossiers or rule files are built", not (rd / "dossiers").exists()
          and not (rd / "rules").exists() and "n/a" in log, log.strip()[-300:])
    check("item 4: a missing check_story.py (MG-S) is an ERROR, not a waivable gap; "
          "a missing lint_fiction.py leaves MG-T BLOCKED",
          verdict(log) == "ERROR" and code == 2 and "MG-S" in log and "MG-T BLOCKED" in log,
          log.strip()[-400:])
    check("MG-4 and MG-C are dispatched, two passes each", "MG-4: reader-pov literary" in log
          and "manuscript.continuity" in log and "manuscript.developmental" in log
          and ".p2.json" in log)

    (scripts / "check_story.py").write_text(STORY_STUB, encoding="utf-8")
    (scripts / "lint_fiction.py").write_text(FICTION_STUB, encoding="utf-8")
    code, log = gate(work, "--round", "2", scripts=scripts)
    recs = {(r["check"], r["relation"]): r for r in store(work)}
    check("with the scripts back, round 2 runs (no ERROR)", verdict(log) != "ERROR",
          log.strip()[-300:])
    check("MG-S: blocking → critical, warning → minor",
          recs.get(("MG-S", "ARC-NOT-RESOLVED"), {}).get("severity") == "critical"
          and recs.get(("MG-S", "SEEDS-MISSING"), {}).get("severity") == "minor", str(list(recs)))
    check("MG-T: major kept, info ignored",
          recs.get(("MG-T", "gesture_tic"), {}).get("severity") == "major"
          and ("MG-T", "dialogue_ratio") not in recs)
    check("an MG-S blocking finding blocks the book", verdict(log) == "BLOCKED")
    for lens in ("continuity", "developmental"):
        write_doc(rdir(work, 2), f"manuscript.{lens}.p1.json", {
            "check": "MG-C", "lens": lens, "subject": "manuscript", "findings": []})
    code, log = gate(work, "--round", "2", "--verdict-only", scripts=scripts)
    check("item 16: one MG-C pass per lens is not audited (passes 1/2)",
          "MG-C 0/2 audited" in log and "passes 1/2" in log, log.strip()[-400:])
    for lens in ("continuity", "developmental"):
        write_doc(rdir(work, 2), f"manuscript.{lens}.p2.json", {
            "check": "MG-C", "lens": lens, "subject": "manuscript", "pass": 2, "findings": []})
    code, log = gate(work, "--round", "2", "--verdict-only", scripts=scripts)
    check("MG-C files cover both lenses, two passes each", "MG-C 2/2 audited" in log,
          log.strip()[-400:])
    (scripts / "lint_fiction.py").write_text("raise SystemExit('boom')\n", encoding="utf-8")
    code, log = gate(work, "--round", "3", scripts=scripts)
    check("a crashed MG-T script is an ERROR, not a pass", verdict(log) == "ERROR" and code == 2)


STORY_OK = '''import argparse, json, os, sys
ap = argparse.ArgumentParser(); ap.add_argument("--root"); ap.add_argument("--json")
ap.add_argument("--manuscript", action="store_true"); a = ap.parse_args()
bad = os.path.exists(os.path.join(a.root, "STORY_BROKEN"))
fs = [{"code": "LEDGER-OPEN", "severity": "major", "subject": "F01", "detail": "open",
       "location": "bible/story-ledger.yaml"}] if bad else []
json.dump({"findings": fs}, open(a.json, "w", encoding="utf-8"))
sys.exit(1 if bad else 0)
'''
FICTION_OK = '''import argparse, json, sys
ap = argparse.ArgumentParser(); ap.add_argument("--root"); ap.add_argument("--json")
ap.add_argument("--book", action="store_true"); ap.add_argument("--units"); a = ap.parse_args()
json.dump({"findings": [{"rule": "unit_length", "severity": "minor", "unit": "unit-01",
  "line": 0, "detail": "short"}], "stats": {}}, open(a.json, "w", encoding="utf-8"))
'''


def _literary_gate_project(tmp: Path, name: str, meta: str = LIT_META) -> tuple[Path, Path]:
    skill = tmp / f"skill-{name}"
    shutil.copytree(HERE, skill / "scripts", ignore=shutil.ignore_patterns("__pycache__", "tests"))
    shutil.copytree(SKILL / "templates", skill / "templates")
    scripts = skill / "scripts"
    (scripts / "check_story.py").write_text(STORY_OK, encoding="utf-8")
    (scripts / "lint_fiction.py").write_text(FICTION_OK, encoding="utf-8")
    work = tmp / name
    (work / "final").mkdir(parents=True)
    (work / "bible").mkdir()
    (work / "bible" / "meta.yaml").write_text(meta, encoding="utf-8")
    for n in (1, 2):
        (work / "final" / f"unit-{n:02d}.md").write_text(
            f"# Capítulo {n}\n\nMateo cerró la puerta.\n\n—Hola —dijo Mariana.\n", "utf-8")
    return work, scripts


def _audit_literary(work: Path, n: int, passes=(1, 2)) -> None:
    rd = rdir(work, n)
    for p in passes:
        write_doc(rd, f"manuscript.whole-book-read.p{p}.json", {
            "check": "MG-4", "lens": "whole-book-read", "subject": "manuscript", "pass": p,
            "findings": []})
        for lens in ("continuity", "developmental"):
            write_doc(rd, f"manuscript.{lens}.p{p}.json", {
                "check": "MG-C", "lens": lens, "subject": "manuscript", "pass": p,
                "findings": []})


def test_literary_gate_rules(tmp: Path) -> None:
    print("\nmanuscript_gate — literary: R1–R4 cannot be switched off, waived or resolved away")
    work, scripts = _literary_gate_project(tmp, "litrules")
    (work / "STORY_BROKEN").write_text("x", encoding="utf-8")
    gate(work, "--round", "1", scripts=scripts)
    _audit_literary(work, 1)
    code, log = gate(work, "--round", "1", "--verdict-only", scripts=scripts)
    key = next(r["key"] for r in store(work) if r["check"] == "MG-S")
    check("an MG-S major (LEDGER-OPEN) makes the literary book NEEDS-REVISION",
          verdict(log) == "NEEDS-REVISION", log.strip()[-300:])
    for status in ("accepted-risk", "refuted", "fixed"):
        code, log = run("manuscript_gate.py", ["--root", str(work), "--units", "final/*.md",
                                               "--date", DATE, "--resolve", key, "--status",
                                               status, "--note", "the human accepts"],
                        scripts=scripts)
        check(f"item 4: --resolve {status} on an MG-S finding is refused (exit 2)",
              code == 2 and "MG-S" in log, log[-200:])
    lines = [json.loads(x) for x in (rdir(work, 1).parent / "findings.jsonl")
             .read_text("utf-8").splitlines() if x.strip()]
    for rec in lines:
        if rec["key"] == key:
            rec["human"] = {"status": "accepted-risk", "round": 1, "note": "hand-edited"}
    (rdir(work, 1).parent / "findings.jsonl").write_text(
        "\n".join(json.dumps(r) for r in lines) + "\n", encoding="utf-8")
    code, log = gate(work, "--round", "1", "--verdict-only", scripts=scripts)
    check("item 4: an accepted-risk written into findings.jsonl by hand is ignored",
          verdict(log) == "NEEDS-REVISION" and "ignored" in log, log.strip()[-300:])
    tkey = next(r["key"] for r in store(work) if r["check"] == "MG-T")
    code, log = run("manuscript_gate.py", ["--root", str(work), "--units", "final/*.md",
                                           "--date", DATE, "--resolve", tkey, "--status",
                                           "accepted-risk", "--note",
                                           "short by design: a vignette chapter of 150 words"],
                    scripts=scripts)
    check("a non-critical MG-T finding may still be accepted as a risk", code == 0, log[-200:])

    print("manuscript_gate — literary: MG-S cannot be disabled or waived")
    meta = LIT_META + "pipeline:\n  manuscript_gate:\n    checks:\n      MG-S: false\n"
    work, scripts = _literary_gate_project(tmp, "litnos", meta=meta)
    (work / "STORY_BROKEN").write_text("x", encoding="utf-8")
    (work / "project-status.yaml").write_text(
        "waivers:\n  - check: manuscript_gate.MG-S\n" + WAIVER, encoding="utf-8")
    code, log = gate(work, "--round", "1", scripts=scripts)
    keys = {r["key"]: r for r in store(work)}
    check("item 4: `checks.MG-S: false` is ignored (MG-S still sweeps) and is itself a major",
          "MG-S-cannot-disable" in keys and any(r["check"] == "MG-S" and r["kind"] == "tool"
                                               for r in keys.values()),
          str(list(keys)))
    check("item 4: a manuscript_gate.MG-S waiver is ignored", "not waivable" in log,
          log.strip()[-300:])

    print("manuscript_gate — literary convergence: two passes, live check_story, max rounds")
    work, scripts = _literary_gate_project(tmp, "litconv")
    gate(work, "--round", "1", scripts=scripts)
    _audit_literary(work, 1, passes=(1,))
    code, log = gate(work, "--round", "1", "--verdict-only", scripts=scripts)
    check("item 16: one MG-4 read is not an audit (PASS-PARTIAL)",
          verdict(log) == "PASS-PARTIAL" and "passes 1/2" in log, log.strip()[-300:])
    _audit_literary(work, 1)
    code, log = gate(work, "--round", "1", "--verdict-only", scripts=scripts)
    check("two passes of MG-4 and MG-C per lens → PASS", verdict(log) == "PASS",
          log.strip()[-300:])
    gate(work, "--round", "2", scripts=scripts)
    _audit_literary(work, 2)
    (work / "STORY_BROKEN").write_text("x", encoding="utf-8")
    code, log = gate(work, "--round", "2", "--verdict-only", scripts=scripts)
    check("item 4: converged requires check_story --manuscript to exit 0 NOW "
          "(the bible changed after the sweep)",
          not converged(log) and "check_story.py --manuscript" in log, log.strip()[-300:])
    (work / "STORY_BROKEN").unlink()
    code, log = gate(work, "--round", "2", "--verdict-only", scripts=scripts)
    check("…and converges once it passes", converged(log) and code == 0, log.strip()[-300:])
    meta = LIT_META + "pipeline:\n  manuscript_gate:\n    max_rounds: 2\n"
    (work / "bible" / "meta.yaml").write_text(meta, encoding="utf-8")
    code, log = gate(work, "--round", "3", scripts=scripts)
    check("item 16: a sweep beyond max_rounds is refused with the escalation message",
          code == 2 and "escalation packet" in log and "blocked-on-manuscript-gate" in log,
          log.strip()[-300:])


# ---------------------------------------------------------------------------
# Fix round 2 — gate regressions (advverify2 attacks g1–g4, t1–t4)
# ---------------------------------------------------------------------------


def resolve(root: Path, key: str, status: str, note: str, scripts: Path = HERE) -> tuple[int, str]:
    return run("manuscript_gate.py", ["--root", str(root), "--units", "final/*.md", "--date",
                                      DATE, "--resolve", key, "--status", status, "--note", note],
               scripts=scripts)


LONG = "unit-03 §2 covers step three; the reader skipped a page"


def test_fix2_gate_profile(tmp: Path) -> None:
    print("\nfix2 item 2 — the gate refuses an unknown profile or schema")
    for n, (label, meta, want) in enumerate((
            ("no project.profile", HEAD + "project:\n  language_variant: en-US\n", 2),
            ("profile 'book-fiction'", HEAD + "project:\n  profile: book-fiction\n", 2),
            ("schema_version 3.0", 'schema_version: "3.0"\nproject:\n  profile: book-technical\n',
             2),
            ("profile 'Book-Technical ' (normalized)", DEFAULT_META.replace(
                "profile: book-technical", "profile: \"Book-Technical \""), 0))):
        work = corpus(tmp, f"prof-{n}", meta=meta)
        code, log = gate(work, "--deterministic-only")
        check(f"item 2: gate with {label} → exit {want}", code == want, log.strip()[-300:])


def test_fix2_gate_resolve(tmp: Path) -> None:
    print("\nfix2 item 9 — --resolve discipline: evidence for fixed, reasons for the rest")
    work = corpus(tmp, "fix2-resolve")
    gate(work, "--round", "1")
    audit_all(work, 1, mg4=[finding("critical"), finding("major", quote="step three is missing")])
    gate(work, "--round", "1", "--verdict-only")
    keys = {r["severity"]: r["key"] for r in store(work) if r["check"] == "MG-4"}
    crit, maj = keys["critical"], keys["major"]
    for label, key, status, note, why in (
            ("fixed with no note", crit, "fixed", "", "needs --note"),
            ("fixed with the text unchanged", crit, "fixed", "rewrote the deploy step",
             "has not changed"),
            ("refuted with note 'x'", crit, "refuted", "x", "20+"),
            ("accepted-risk with a 2-word note", maj, "accepted-risk", "ok then", "20+"),
            ("accepted-risk on a critical", crit, "accepted-risk", LONG, "critical")):
        code, log = resolve(work, key, status, note)
        check(f"item 9: agent finding — {label} is refused (exit 2)",
              code == 2 and why in log, log.strip()[-250:])
    u2 = work / "final" / "unit-02.md"
    good = u2.read_text("utf-8")
    u2.write_text(good + "\nThe deploy step now names the service account.\n", encoding="utf-8")
    code, log = resolve(work, crit, "fixed", "unit-02 §3 now deploys the service")
    check("item 9: fixed after the text changed, with a note → accepted", code == 0, log[-250:])
    gate(work, "--round", "1", "--verdict-only")
    check("item 9: …the store shows it fixed",
          next(r for r in store(work) if r["key"] == crit)["status"] == "fixed")
    u2.write_text(good, encoding="utf-8")
    code, log = gate(work, "--round", "1", "--verdict-only")
    check("item 9: reverting the text re-opens a hand-`fixed` finding (re-validated every run)",
          next(r for r in store(work) if r["key"] == crit)["status"] == "open"
          and "ignored" in log, log.strip()[-300:])
    code, log = resolve(work, maj, "refuted", LONG)
    check("item 9: refuted with a real 20+ character note → accepted", code == 0, log[-250:])
    lines = [json.loads(x) for x in (rdir(work, 1).parent / "findings.jsonl")
             .read_text("utf-8").splitlines() if x.strip()]
    for rec in lines:
        if rec["key"] == crit:
            rec["human"] = {"status": "refuted", "round": 1, "note": "x"}
    (rdir(work, 1).parent / "findings.jsonl").write_text(
        "\n".join(json.dumps(r) for r in lines) + "\n", encoding="utf-8")
    code, log = gate(work, "--round", "1", "--verdict-only")
    check("item 9: a `refuted` with note 'x' written into findings.jsonl by hand is ignored",
          verdict(log) == "BLOCKED" and "ignored" in log, log.strip()[-300:])

    print("fix2 item 9 — deterministic findings close only when the sweep stops reporting them")
    work = corpus(tmp, "fix2-tool")
    u3 = work / "final" / "unit-03.md"
    u3.write_text(u3.read_text("utf-8") + "\nThis paragraph prints as a heading.\n---\n",
                  encoding="utf-8")
    (work / "bible" / "fixed-defects.yaml").write_text(
        "defects:\n  - id: FIX-02\n    what: the old name of the fixture\n"
        "    severity_if_back: minor\n    forbid:\n      - kind: literal\n"
        "        pattern: \"the clean fixture\"\n", encoding="utf-8")
    gate(work, "--round", "1")
    recs = store(work)
    mg5 = next(r["key"] for r in recs if r["check"] == "MG-5" and r["severity"] == "critical")
    mg7 = next(r["key"] for r in recs if r["check"] == "MG-7")
    for status in ("refuted", "fixed", "accepted-risk"):
        code, log = resolve(work, mg5, status, LONG)
        check(f"item 9: a technical MG-5 critical cannot be {status} by hand (exit 2)",
              code == 2, log[-250:])
    code, log = resolve(work, mg7, "accepted-risk", "x")
    check("item 9: MG-7 minor accepted-risk needs a real note", code == 2, log[-250:])
    code, log = resolve(work, mg7, "accepted-risk", LONG)
    check("item 9: a minor MG-7 may be accepted as a risk with a real note", code == 0, log[-250:])

    print("fix2 item 9 — literary R1/R2 findings: only a re-audit of changed text closes them")
    work, scripts = _literary_gate_project(tmp, "fix2-r2")
    gate(work, "--round", "1", scripts=scripts)
    r2 = {"relation": "D3", "severity": "major", "category": "plot", "rule": "R2",
          "canonical_site": "final/unit-02.md:3", "other_sites": [],
          "searched_whole_chapter": True, "fix_scope": "add_content",
          "reasoning": "ending.resolution does not happen on the page",
          "p1": {"location": "final/unit-02.md:3", "quote": "Mateo cerró la puerta."},
          "verification": {"verdict": "REFUTED", "reason": "the verifier disagrees"}}
    _audit_literary(work, 1)
    write_doc(rdir(work, 1), "manuscript.developmental.p1.json", {
        "check": "MG-C", "lens": "developmental", "subject": "manuscript", "pass": 1,
        "findings": [r2]})
    code, log = gate(work, "--round", "1", "--verdict-only", scripts=scripts)
    key = next(r["key"] for r in store(work) if r["check"] == "MG-C")
    check("item 9: a verifier's REFUTED does not close an R2 finding (NEEDS-REVISION)",
          verdict(log) == "NEEDS-REVISION"
          and next(r for r in store(work) if r["key"] == key)["status"] == "open",
          log.strip()[-300:])
    for status in ("accepted-risk", "refuted", "fixed"):
        code, log = resolve(work, key, status, LONG, scripts=scripts)
        check(f"item 9: --resolve {status} on a literary R2 finding is refused",
              code == 2 and "R2" in log, log[-250:])
    gate(work, "--round", "2", scripts=scripts)
    _audit_literary(work, 2)
    code, log = gate(work, "--round", "2", "--verdict-only", scripts=scripts)
    check("item 9: a re-audit of the SAME manuscript that no longer reports it does not close it",
          next(r for r in store(work) if r["key"] == key)["status"] == "open", log.strip()[-300:])
    u2 = work / "final" / "unit-02.md"
    u2.write_text(u2.read_text("utf-8") + "\nMariana se quedó en la casa.\n", encoding="utf-8")
    gate(work, "--round", "3", scripts=scripts)
    _audit_literary(work, 3)
    code, log = gate(work, "--round", "3", "--verdict-only", scripts=scripts)
    check("item 9: …a re-audit of CHANGED text that no longer reports it closes it",
          next(r for r in store(work) if r["key"] == key)["status"] == "fixed", log.strip()[-300:])


def test_fix2_gate_waivers(tmp: Path) -> None:
    print("\nfix2 item 10 — literary MG-4/MG-C: never off, never coverage-waived; quiet rounds ≥ 2")
    meta = LIT_META + ("pipeline:\n  manuscript_gate:\n    checks: {MG-4: false, MG-C: false}\n"
                       "    rounds_without_new_to_close: 1\n")
    work, scripts = _literary_gate_project(tmp, "fix2-lit-off", meta=meta)
    (work / "project-status.yaml").write_text(
        "waivers:\n  - check: manuscript_gate.MG-4\n" + WAIVER
        + "  - check: manuscript_gate.MG-C\n" + WAIVER, encoding="utf-8")
    code, log = gate(work, "--round", "1", scripts=scripts)
    keys = {r["key"] for r in store(work)}
    check("item 10: `checks.MG-4/MG-C: false` in literary → majors, the waivers are ignored, and "
          "both are still dispatched", {"MG-4-cannot-disable", "MG-C-cannot-disable"} <= keys
          and "is ignored" in log and "MG-4: reader-pov literary" in log, log.strip()[-400:])
    check("item 10: rounds_without_new_to_close: 1 is clamped to 2, with a note",
          "clamped to 2" in log, log.strip()[-300:])

    work, scripts = _literary_gate_project(tmp, "fix2-lit-cov")
    code, log = gate(work, "--round", "1", scripts=scripts)
    sig = next(line.split("signature:")[1].split()[0] for line in log.splitlines()
               if "coverage signature:" in line)
    (work / "project-status.yaml").write_text(
        f"waivers:\n  - check: manuscript_gate.coverage\n    signature: {sig}\n" + WAIVER,
        encoding="utf-8")
    gate(work, "--round", "1", "--verdict-only", scripts=scripts)
    gate(work, "--round", "2", scripts=scripts)
    code, log = gate(work, "--round", "3", scripts=scripts)
    check("item 10: a complete coverage waiver never covers unread MG-4/MG-C in literary",
          not converged(log) and "no waiver covers them" in log, log.strip()[-300:])

    work = corpus(tmp, "fix2-quiet", meta=DEFAULT_META + "pipeline:\n  manuscript_gate:\n"
                                                        "    rounds_without_new_to_close: 0\n")
    gate(work, "--round", "1")
    audit_all(work, 1)
    code, log = gate(work, "--round", "1", "--verdict-only")
    check("item 10: rounds_without_new_to_close: 0 is clamped — one quiet PASS round does not "
          "converge", verdict(log) == "PASS" and not converged(log) and "clamped" in log,
          log.strip()[-300:])


def test_fix2_gate_mg6_evidence(tmp: Path) -> None:
    print("\nfix2 item 11 — an executable surface needs runner EVIDENCE, not a runner string")
    for n, (label, surface, ok) in enumerate((
            ("runner 'qlik reload (never run)', no evidence",
             "runner: \"qlik reload (never run)\"", False),
            ("runner 'sqlite3 in CI', no evidence", "runner: \"sqlite3 in CI\"", False),
            ("evidence pointing at a missing file",
             "runner: x\n      evidence: reviews/runner/missing.txt", False),
            ("evidence pointing at an existing runner output",
             "runner: x\n      evidence: reviews/runner/sql_examples.txt", True))):
        meta = HEAD + ("project:\n  profile: book-technical\n  language_variant: en-US\n"
                       "validation_surface:\n  surfaces:\n    - surface: sql_examples\n"
                       "      executable: true\n      " + surface + "\n")
        work = corpus(tmp, f"fix2-mg6-{n}", meta=meta)
        gate(work, "--round", "1")
        open_mg6 = any(r["check"] == "MG-6" and r["status"] == "open" for r in store(work))
        check(f"item 11: {label} → MG-6 {'satisfied' if ok else 'open (major)'}",
              open_mg6 != ok, str([r["detail"] for r in store(work) if r["check"] == "MG-6"]))


def test_fix2_gate_store(tmp: Path) -> None:
    print("\nfix2 item 12 — the findings store only grows; truncation is an ERROR")
    work = corpus(tmp, "fix2-store")
    gate(work, "--round", "1")
    audit_all(work, 1, mg4=[finding("critical")])
    gate(work, "--round", "1", "--verdict-only")
    st = state(work)
    check("item 12: state.json records the round's finding keys and count",
          st["rounds"]["1"].get("store_keys") and st["rounds"]["1"].get("store_count", 0) >= 1)
    (rdir(work, 1) / "findings" / "manuscript.whole-book-read.p1.json").unlink()
    code, log = gate(work, "--round", "1", "--verdict-only")
    check("item 12: deleting the findings FILE leaves its finding open (BLOCKED)",
          verdict(log) == "BLOCKED" and code == 1, log.strip()[-300:])
    p = rdir(work, 1).parent / "findings.jsonl"
    kept = [x for x in p.read_text("utf-8").splitlines() if x.strip() and '"MG-4"' not in x]
    p.write_text("\n".join(kept) + "\n", encoding="utf-8")
    code, log = gate(work, "--round", "1", "--verdict-only")
    check("item 12: a findings.jsonl missing a recorded key → ERROR 'findings store truncated'",
          verdict(log) == "ERROR" and code == 2 and "truncated" in log, log.strip()[-300:])
    code, log = gate(work, "--round", "1", "--verdict-only")
    check("item 12: …and it stays an ERROR on the next run (the truncated file is not rebuilt)",
          verdict(log) == "ERROR" and "truncated" in log, log.strip()[-300:])
    p.unlink()
    code, log = resolve(work, "MG-4", "refuted", LONG)
    check("item 12: --resolve on a deleted store is refused too", code == 2, log[-250:])


def test_lint_style(tmp: Path) -> None:
    print("\nlint_style — dash_style, language, numbers, tables")
    work = tmp / "style"
    (work / "final").mkdir(parents=True)
    (work / "bible").mkdir()
    meta = work / "bible" / "meta.yaml"
    (work / "final" / "unit-01.md").write_text(
        "# Uno\n\n—Hola —dijo ella—. Llegamos en 2019 con 1500 cajas y 25000 pesos.\n\n"
        "El color gris.\n\n| a  | b |\n|---|---|\n| x  | y |\n", encoding="utf-8")
    out = tmp / "style.json"

    def lint() -> dict:
        run("lint_style.py", ["--root", str(work), "--json", str(out)])
        rules: dict = {}
        for f in json.loads(out.read_text("utf-8"))["findings"]:
            rules.setdefault(f["rule"], []).append(f["found"])
        return rules

    meta.write_text("project:\n  language_variant: es-AR\nconventions:\n  dash_style: "
                    "\"em-dash, no spaces\"\n", encoding="utf-8")
    es = lint()
    check("Spanish: dialogue rayas are never em-dash findings", "em_dash" not in es, str(es))
    check("Spanish: no 4-digit thousands rule (RAE), 5+ digits still flagged",
          es.get("thousands") == ["25000"], str(es.get("thousands")))
    check("aligned table cells are not double spaces", "double_space" not in es, str(es))
    (work / "final" / "unit-01.md").write_text(
        "# One\n\nIt was grey — and then it was not.\n", encoding="utf-8")
    meta.write_text("project:\n  language_variant: en-US\nconventions:\n  dash_style: "
                    "\"em-dash, no spaces\"\n", encoding="utf-8")
    en = lint()
    check("English + 'no spaces': a spaced em-dash is flagged",
          bool(en.get("em_dash")) and bool(en.get("spelling_variant")), str(en))


def test_fixed_defects(tmp: Path) -> None:
    print("\ncheck_fixed_defects — a fixed defect cannot walk back in")
    work = tmp / "fixed"
    (work / "final").mkdir(parents=True)
    (work / "bible").mkdir(parents=True)
    (work / "final" / "unit-01.md").write_text(
        "# Unit 01\n\n## The regression\n\nThe set modifier has two slots, and the outer one "
        "wins.\n\n## The teaching passage\n\nWriters reach for the two slots model here.\n"
        "That is the one that looks like the fix and is not.\n", encoding="utf-8")
    (work / "bible" / "fixed-defects.yaml").write_text(
        "defects:\n  - id: FIX-01\n    what: three positions collapsed into two slots\n"
        "    severity_if_back: critical\n    scope: unit-01\n    forbid:\n"
        "      - kind: regex\n        pattern: '\\btwo[- ]slots?\\b'\n    allow_in:\n"
        "      - anchor: \"That is the one that looks like the fix and is not\"\n"
        "        why: the corrected text quotes the wrong form to teach against it\n",
        encoding="utf-8")
    out = work / "fd.json"
    run("check_fixed_defects.py", ["--root", str(work), "--units", "final/*.md",
                                   "--json", str(out), "--quiet"])
    data = json.loads(out.read_text("utf-8"))
    check("the reappearance is found (string `scope` is one unit)",
          len(data["findings"]) == 1, str([f["location"] for f in data["findings"]]))
    check("a reappearance is critical by default", data["counts"]["critical"] == 1)
    check("the teaching passage is NOT flagged", bool(data["exemptions"]))
    (work / "final" / "unit-01.md").write_text(
        "# Unit 01\n\nThe set modifier has three positions, and each is different.\n", "utf-8")
    run("check_fixed_defects.py", ["--root", str(work), "--units", "final/*.md",
                                   "--json", str(out), "--quiet"])
    check("clean text produces no finding", not json.loads(out.read_text("utf-8"))["findings"])


def test_anchors(tmp: Path) -> None:
    print("\nresolve_anchors — a moved passage is repaired, a changed one is not")
    work = tmp / "anchors"
    (work / "final").mkdir(parents=True)
    (work / "bible").mkdir(parents=True)
    unit = work / "final" / "unit-01.md"
    unit.write_text("# Unit 01\n\n## Baselines\n\nOptimized mode is about 100 times faster "
                    "than loading the database.\n", encoding="utf-8")
    dnt = work / "bible" / "do-not-touch.md"
    dnt.write_text("# Anchors\n\n### `final/unit-01.md:5` — the baseline hierarchy\n\n"
                   "**Anchor:** \"about 100 times faster than loading the database\"\n",
                   encoding="utf-8")
    args = ["--root", str(work), "--units", "final/*.md"]
    out = work / "a.json"

    def counts() -> dict:
        run("resolve_anchors.py", args + ["--json", str(out), "--quiet"])
        return json.loads(out.read_text("utf-8"))["counts"]

    check("an intact reference resolves OK", counts().get("OK") == 1)
    unit.write_text("# Unit 01\n\n## A new section\n\nInserted.\n\n"
                    + unit.read_text("utf-8").split("\n", 1)[1], encoding="utf-8")
    check("an insertion above reports DRIFT, not a defect", counts().get("DRIFT") == 1)
    run("resolve_anchors.py", args + ["--heal", "--quiet"])
    check("--heal repairs the line from the anchor", counts().get("OK") == 1)
    unit.write_text(unit.read_text("utf-8").replace(
        "about 100 times faster than loading the database",
        "roughly ten times faster than a standard load"), encoding="utf-8")
    check("an edited passage reports EDITED, not DRIFT", counts().get("EDITED") == 1)
    before = dnt.read_text("utf-8")
    run("resolve_anchors.py", args + ["--heal", "--quiet"])
    check("--heal leaves an EDITED reference alone", dnt.read_text("utf-8") == before)


def test_sync_manuscript(tmp: Path) -> None:
    print("\nsync_manuscript — deterministic, idempotent, BOM-free")
    work = tmp / "sync"
    shutil.copytree(FIXTURES, work)
    args = ["--root", str(work), "--units", "final/unit-*.md"]
    code, _ = run("sync_manuscript.py", args + ["--check"])
    check("missing manuscript reports drift", code == 1, f"got {code}")
    run("sync_manuscript.py", args)
    code, _ = run("sync_manuscript.py", args + ["--check"])
    check("rebuilt manuscript verifies", code == 0, f"got {code}")
    first = (work / "manuscript.md").read_text("utf-8")
    run("sync_manuscript.py", args)
    check("rebuild is byte-identical", (work / "manuscript.md").read_text("utf-8") == first)
    u2 = work / "final" / "unit-02.md"
    u2.write_bytes(b"\xef\xbb\xbf" + u2.read_bytes())
    run("sync_manuscript.py", args)
    check("a unit's BOM does not end up inside manuscript.md",
          "﻿" not in (work / "manuscript.md").read_text("utf-8"))


BUILTIN = [test_lint_render, test_text_layer, test_rule_extraction, test_propagation,
           test_manuscript_gate, test_verification_plan, test_coverage_verdict, test_depth_axis,
           test_pool_drains, test_convergence, test_loud_failures, test_gate_config,
           test_literary_branch, test_literary_gate_rules, test_fix2_gate_profile,
           test_fix2_gate_resolve, test_fix2_gate_waivers, test_fix2_gate_mg6_evidence,
           test_fix2_gate_store, test_lint_style, test_fixed_defects, test_anchors,
           test_sync_manuscript]


def discovered() -> list[tuple[str, object]]:
    """(label, fn) for every TESTS entry of tests/selftest_*.py; a module that does
    not import becomes a single failing entry."""
    out: list[tuple[str, object]] = []
    for path in sorted((HERE / "tests").glob("selftest_*.py")):
        try:
            spec = importlib.util.spec_from_file_location(path.stem, path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            tests = list(getattr(mod, "TESTS"))
        except Exception:  # noqa: BLE001 — any import failure is a FAIL, never a crash
            err = traceback.format_exc(limit=3).strip().splitlines()[-1]
            out.append((f"{path.name} (import)", lambda *_a, _e=err: (_ for _ in ()).throw(
                RuntimeError(_e))))
            continue
        out += [(f"{path.stem}.{getattr(fn, '__name__', 'test')}", fn) for fn in tests]
    return out


def main() -> int:
    global VERBOSE
    ap = argparse.ArgumentParser(description="book-factory selftest — deterministic checks, "
                                             "no model, no tokens.")
    ap.add_argument("-v", "--verbose", action="store_true", help="Print every assertion.")
    ap.add_argument("-k", metavar="PATTERN", default="",
                    help="Run only tests whose name contains PATTERN.")
    args = ap.parse_args()
    VERBOSE = args.verbose
    if not FIXTURES.exists():
        print(f"Missing fixtures at {FIXTURES}")
        return 2

    print("book-factory selftest — deterministic checks, no model, no tokens")
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        for fn in BUILTIN:
            if args.k and args.k not in fn.__name__:
                continue
            sub = tmp / fn.__name__
            sub.mkdir()
            try:
                fn(sub)
            except Exception:  # noqa: BLE001
                check(f"{fn.__name__} ran to completion", False,
                      traceback.format_exc(limit=4).strip().replace("\n", "\n          "))
        mods = [(label, fn) for label, fn in discovered() if not args.k or args.k in label]
        if mods:
            print("\ntests/selftest_*.py")
        for i, (label, fn) in enumerate(mods):
            sub = tmp / f"mod-{i}"
            sub.mkdir()
            try:
                fn(sub, check, run)
            except Exception:  # noqa: BLE001
                check(f"{label} ran to completion", False,
                      traceback.format_exc(limit=4).strip().replace("\n", "\n          "))

    print(f"\n{len(PASSED)} passed, {len(FAILED)} failed")
    if FAILED:
        print("\nFailures:")
        for name, detail in FAILED:
            print(f"  - {name}" + (f"\n      {detail}" if detail else ""))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
