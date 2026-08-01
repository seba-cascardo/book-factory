#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""selftest.py — regression gate for the deterministic checks.

Runs in seconds, spends no tokens, and asserts two things that matter in
opposite directions:

  1. Every defect class the fixtures carry is **found**. If a check silently
     stops firing, it fails here rather than on a real book six months later.
  2. Correct prose produces **nothing**. A check that fires on the clean fixture
     is worse than one that misses, because it trains everyone to ignore the
     output — and an ignored warning is how the artifact this toolkit replaces
     went stale.

The propagation test is the important one: it reproduces the exact failure the
claim index exists to prevent. Edit a passage, and every sibling that repeats its
claim must be named.

Two rules for anyone extending this file, both learned by getting them wrong:

  - **Assert on the artifact that ships, not on an intermediate list.** A gate
    that checked its calibration pairs against the *candidate* list while
    emission capped output independently reported PASS while the pairs ranked
    199/205 and never reached the file an auditor reads. Assert on emitted
    files, or on the single shared selection that produces them
    (`bookkit/selection.py`) — never on a list that something downstream will
    still filter.
  - **A gap you cannot close stays here, marked, and fails.** Do not delete a
    case to make this green. A recorded gap is debt; a deleted one is forgotten
    and gets rediscovered from scratch.

Usage
  python scripts/selftest.py
  python scripts/selftest.py -v
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIXTURES = HERE / "tests" / "fixtures"

PASSED: list[str] = []
FAILED: list[tuple[str, str]] = []
VERBOSE = "-v" in sys.argv


def check(name: str, condition: bool, detail: str = "") -> None:
    if condition:
        PASSED.append(name)
        if VERBOSE:
            print(f"  ok    {name}")
    else:
        FAILED.append((name, detail))
        print(f"  FAIL  {name}" + (f"\n          {detail}" if detail else ""))


def run(script: str, args: list[str]) -> tuple[int, str]:
    proc = subprocess.run([sys.executable, str(HERE / script), *args],
                          capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


# ---------------------------------------------------------------------------


def test_lint_render(tmp: Path) -> None:
    print("\nlint_render — defects found on the defective fixture")
    out = tmp / "lint.json"
    code, log = run("lint_render.py", [
        "--root", str(FIXTURES), "--units", "final/unit-01.md",
        "--json", str(out), "--fail-on", "never", "--quiet"])
    data = json.loads(out.read_text(encoding="utf-8"))
    checks = {f["check"] for f in data["findings"]}

    check("setext hazard found", "setext-hazard" in checks,
          "a paragraph followed by `---` with no blank line prints as a heading")
    check("setext rated critical",
          any(f["severity"] == "critical" for f in data["findings"]
              if f["check"] == "setext-hazard"))
    check("ragged table found", "table-shape" in checks)
    check("leaked pipeline comment found", "pipeline-comment" in checks)
    check("unbalanced comment found", "unbalanced-comment" in checks)
    check("heading jump found", "heading-jump" in checks)
    check("SOURCE comment NOT flagged",
          not any("SOURCE" in (f.get("quote") or "") for f in data["findings"]
                  if f["check"] == "pipeline-comment"),
          "the invisible citation policy puts SOURCE in shipped prose on purpose")

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
    code_c, _ = run("lint_render.py", ["--root", str(FIXTURES),
                                       "--units", "final/unit-01.md",
                                       "--fail-on", "critical", "--quiet"])
    code_ok, _ = run("lint_render.py", ["--root", str(FIXTURES),
                                        "--units", "final/unit-02.md",
                                        "--fail-on", "critical", "--quiet"])
    check("exits 1 on a critical", code_c == 1, f"got {code_c}")
    check("exits 0 when clean", code_ok == 0, f"got {code_ok}")


def test_rule_extraction(tmp: Path) -> None:
    print("\nextract_rule_candidates — rule shapes and quota stratification")
    out = tmp / "rules"
    code, log = run("extract_rule_candidates.py", [
        "--root", str(FIXTURES), "--units", "final/unit-*.md",
        "--out", str(out), "--min-instances", "1"])

    # Assert on the EMITTED FILES, not on the report. A gate that checked an
    # intermediate list while emission capped independently passed while its
    # calibration pairs never reached the dossier.
    emitted = {p.stem for p in out.glob("*.md")} - {"_index"}
    check("rule stated as a consequence is emitted",
          any("upper" in e for e in emitted),
          "universal quantifier + breaking verb, no modal — the shape technical "
          f"prose actually uses. emitted: {sorted(emitted)}")
    check("rule that demonstrates its construct is emitted",
          any("orderdate" in e for e in emitted),
          "a rule written entirely as `{<OrderDate={'…'}>}` names no keyword; "
          f"requiring a named construct skips it. emitted: {sorted(emitted)}")

    print("extract_rule_candidates — each failure mode keeps its own quota")
    sys.path.insert(0, str(HERE))
    from bookkit.selection import stratified_top
    fake = [("cross", i) for i in range(90)] + [("intra", i) for i in range(10)]
    sel = stratified_top(fake, lambda t: t[0], lambda t: t[1], quota=20,
                         weights={"cross": 1.0, "intra": 1.0})
    kinds = {k for k, _ in sel.emitted}
    check("both strata survive a tight quota", kinds == {"cross", "intra"},
          f"got {kinds} — a single ranking emits 20 of the numerous mode and zero "
          f"of the other, which is how 40 cross-unit rules shipped with zero "
          f"intra-unit ones")
    check("the scarce stratum is not truncated",
          sum(1 for k, _ in sel.emitted if k == "intra") == 10,
          "unused share must be redistributed, not wasted")
    check("selection reports what it dropped", sel.dropped_total == 80,
          f"got {sel.dropped_total} — a silent truncation reads as full coverage")


def test_propagation(tmp: Path) -> None:
    print("\nclaim index — MOVED repairs, CHANGED propagates")
    work = tmp / "book"
    shutil.copytree(FIXTURES, work)
    args = ["--root", str(work), "--units", "final/unit-*.md"]

    run("bootstrap_probes.py", args + ["--source", "frequency", "--min-units", "2"])
    code, log = run("build_concept_dossier.py", args + ["--emit-index", "--no-blame"])
    index = work / "bible" / "claim-index.yaml"
    check("claim index generated", index.exists(), log.strip()[-300:])
    if not index.exists():
        return

    code, log = run("validate_claim_index.py", args)
    check("clean corpus validates", "consistent" in log, log.strip()[-200:])

    # Shift every line down: locations go stale, fingerprints survive.
    target = work / "final" / "unit-02.md"
    original = target.read_text(encoding="utf-8")
    target.write_text("# Inserted heading\n\nInserted paragraph.\n\n" + original,
                      encoding="utf-8")
    code, log = run("validate_claim_index.py", args)
    check("a moved passage reports MOVED, not CHANGED",
          "MOVED" in log and "CHANGED" not in log,
          "keying on line numbers would make every insertion look like an edit, "
          "and the warnings would become noise")
    code, log = run("validate_claim_index.py", args + ["--fix"])
    code, log = run("validate_claim_index.py", args)
    check("--fix repairs moved locations", "consistent" in log, log.strip()[-200:])

    # Now edit a passage that has siblings. This is the whole point.
    doc = index.read_text(encoding="utf-8")
    import yaml
    parsed = yaml.safe_load(doc)
    victim = None
    for cid, entry in (parsed.get("concepts") or {}).items():
        for site in entry.get("sites") or []:
            if site.get("related"):
                victim = (cid, site)
                break
        if victim:
            break

    if not victim:
        check("a concept with siblings exists in the fixture", False,
              "the fixture is too small to have related passages")
        return

    cid, site = victim
    path_str, _, line_str = site["location"].rpartition(":")
    edited = work / path_str
    lines = edited.read_text(encoding="utf-8").splitlines()
    idx = int(line_str) - 1
    lines[idx] = lines[idx] + " An edit that changes what this passage claims."
    edited.write_text("\n".join(lines) + "\n", encoding="utf-8")

    code, log = run("validate_claim_index.py", args)
    check("an edited passage reports CHANGED", "CHANGED" in log)
    check("PROPAGATE names the siblings", "PROPAGATE" in log,
          "this is the defect the index exists to prevent: a fix that lands in "
          "one of N sites because nobody knew the passage had siblings")
    check("validator warns without breaking the build", code == 0,
          f"exit {code} — a hard gate on prose gets switched off within a week, "
          f"and then there is no warning either")


def test_manuscript_gate(tmp: Path) -> None:
    print("\nmanuscript_gate — deterministic sweep and verdict")
    work = tmp / "gate"
    shutil.copytree(FIXTURES, work)
    code, log = run("manuscript_gate.py", [
        "--root", str(work), "--units", "final/unit-*.md",
        "--date", "2026-01-01", "--deterministic-only"])
    check("gate runs the deterministic sweep", "MG-5 render lint" in log,
          log.strip()[-300:])
    mg5 = next((l for l in log.splitlines() if "MG-5 render lint" in l), "")
    n_critical = int(mg5.split("MG-5 render lint:")[1].split("critical")[0].strip()
                     ) if mg5 else 0
    check("gate surfaces the fixture's criticals", n_critical >= 1, mg5)


def test_sync_manuscript(tmp: Path) -> None:
    print("\nsync_manuscript — deterministic and idempotent")
    work = tmp / "sync"
    shutil.copytree(FIXTURES, work)
    args = ["--root", str(work), "--units", "final/unit-*.md"]
    code, _ = run("sync_manuscript.py", args + ["--check"])
    check("missing manuscript reports drift", code == 1, f"got {code}")
    run("sync_manuscript.py", args)
    code, _ = run("sync_manuscript.py", args + ["--check"])
    check("rebuilt manuscript verifies", code == 0, f"got {code}")
    first = (work / "manuscript.md").read_text(encoding="utf-8")
    run("sync_manuscript.py", args)
    check("rebuild is byte-identical",
          (work / "manuscript.md").read_text(encoding="utf-8") == first)


def main() -> int:
    if not FIXTURES.exists():
        print(f"Missing fixtures at {FIXTURES}")
        return 2

    print("book-factory selftest — deterministic checks, no model, no tokens")
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        test_lint_render(tmp)
        test_rule_extraction(tmp)
        test_propagation(tmp)
        test_manuscript_gate(tmp)
        test_sync_manuscript(tmp)

    print(f"\n{len(PASSED)} passed, {len(FAILED)} failed")
    if FAILED:
        print("\nFailures:")
        for name, detail in FAILED:
            print(f"  - {name}" + (f"\n      {detail}" if detail else ""))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
