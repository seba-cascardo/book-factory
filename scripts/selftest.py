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


def test_verification_plan(tmp: Path) -> None:
    print("\nmanuscript_gate — unsettled questions become a plan, not a dead end")
    work = tmp / "plan"
    shutil.copytree(FIXTURES, work)
    fdir = work / "reviews" / "manuscript-gate-2026-01-01" / "round-1" / "findings"
    fdir.mkdir(parents=True)
    (fdir / "demo.json").write_text(json.dumps({
        "check": "MG-1", "lens": "source", "subject": "demo", "findings": [],
        "deferred": [
            {"question": "Does the live system behave as unit-01 claims?",
             "why_unresolved": "no access here", "needs": "runner",
             "sites": ["final/unit-01.md:10"],
             "how_to_check": "run the snippet", "expected": "x", "defect_if": "y"},
            {"question": "Does the approval flow really take three days?",
             "why_unresolved": "internal process claim", "needs": "person",
             "sites": ["final/unit-02.md:20"]},
            {"question": "Recommend pattern A or B?",
             "why_unresolved": "editorial choice", "needs": "human-decision",
             "sites": ["final/unit-03.md:30"]},
        ]}), encoding="utf-8")

    code, log = run("manuscript_gate.py", [
        "--root", str(work), "--units", "final/unit-*.md",
        "--date", "2026-01-01", "--round", "1", "--verdict-only"])
    plan = work / "reviews" / "verification-plan" / "PLAN.md"
    check("plan is generated from deferred items", plan.exists(), log.strip()[-300:])
    if not plan.exists():
        return
    text = plan.read_text(encoding="utf-8")
    check("a runner question becomes an entry", "live system behave" in text)
    check("a NON-code question becomes an entry too", "approval flow" in text,
          "code is the obvious case, not the only one — a claim a person could "
          "confirm is just as checkable and just as unverified")
    check("a human decision stays OUT of the plan", "pattern A or B" not in text,
          "no observation settles a choice; it belongs in the human packet")
    check("missing fields are marked TODO, not dropped", "**TODO**" in text,
          "an entry nobody can execute is an entry nobody runs — say so")


def _clean_corpus(tmp: Path, name: str) -> Path:
    """Two lint-clean fixture units. Coverage tests need a corpus whose verdict
    is not already BLOCKED by unit-01's deliberate render defects."""
    work = tmp / name
    (work / "final").mkdir(parents=True)
    for unit in ("unit-02.md", "unit-03.md"):
        shutil.copy(FIXTURES / "final" / unit, work / "final" / unit)
    return work


def _write_findings(round_dir: Path, check: str, subjects: list[str],
                    sampled: bool = False) -> None:
    fdir = round_dir / "findings"
    fdir.mkdir(parents=True, exist_ok=True)
    for s in subjects:
        (fdir / f"{check}-{s}.json").write_text(json.dumps({
            "check": check, "lens": "pairs", "subject": s,
            "sampled": sampled, "findings": []}), encoding="utf-8")


def _verdict(log: str) -> str:
    for line in log.splitlines():
        if "VERDICT:" in line:
            return line.split("VERDICT:")[1].strip()
    return "(none)"


def test_coverage_verdict(tmp: Path) -> None:
    print("\nmanuscript_gate — the verdict knows how much it did NOT look at")
    work = _clean_corpus(tmp, "cov")
    args = ["--root", str(work), "--units", "final/*.md", "--date", "2026-01-01"]
    rd = work / "reviews" / "manuscript-gate-2026-01-01" / "round-1"

    code, log = run("manuscript_gate.py", args + ["--round", "1", "--top-concepts", "1"])
    cov = json.loads((rd / "coverage-MG-1.json").read_text(encoding="utf-8"))
    check("the emitter writes a coverage record", cov.get("eligible_candidates", 0) > 0,
          "without it the verdict has no coverage term and PASS means nothing")
    check("eligible is bigger than selected under a tight quota",
          cov["eligible_candidates"] > cov["selected"],
          f"got {cov['selected']}/{cov['eligible_candidates']}")
    check("what was cut is recorded, ranked", bool(cov.get("cut")),
          "a silent truncation reads as full coverage")

    # The case §3.1.5 exists for: no findings at all, and still not a PASS.
    _write_findings(rd, "MG-1", [s["id"] for s in cov["subjects"]])
    _write_findings(rd, "MG-4", ["manuscript"])
    code, log = run("manuscript_gate.py", args + ["--round", "1", "--verdict-only"])
    check("a partial sweep with zero findings is PASS-PARTIAL, never PASS",
          _verdict(log) == "PASS-PARTIAL",
          f"got {_verdict(log)} — a book can reach `complete` having audited 30 of "
          f"474 candidates if the verdict is f(findings) alone")
    check("PASS-PARTIAL names the numbers, not just the state",
          "coverage" in log.lower() and "/" in log)

    print("manuscript_gate — full coverage with no findings IS a PASS")
    work2 = _clean_corpus(tmp, "cov-full")
    args2 = ["--root", str(work2), "--units", "final/*.md", "--date", "2026-01-01"]
    rd2 = work2 / "reviews" / "manuscript-gate-2026-01-01" / "round-1"
    run("manuscript_gate.py", args2 + ["--round", "1"])
    cov2 = json.loads((rd2 / "coverage-MG-1.json").read_text(encoding="utf-8"))
    _write_findings(rd2, "MG-1", [s["id"] for s in cov2["subjects"]])
    _write_findings(rd2, "MG-4", ["manuscript"])
    code, log = run("manuscript_gate.py", args2 + ["--round", "1", "--verdict-only"])
    check("no quota, no sampling, every subject audited -> PASS",
          _verdict(log) == "PASS",
          f"got {_verdict(log)} — PASS-PARTIAL has to be a state you can LEAVE, or "
          f"it is just a broken gate. log tail: {log.strip()[-400:]}")

    print("manuscript_gate — a subject nobody audited does not count as covered")
    work3 = _clean_corpus(tmp, "cov-gap")
    args3 = ["--root", str(work3), "--units", "final/*.md", "--date", "2026-01-01"]
    rd3 = work3 / "reviews" / "manuscript-gate-2026-01-01" / "round-1"
    run("manuscript_gate.py", args3 + ["--round", "1"])
    cov3 = json.loads((rd3 / "coverage-MG-1.json").read_text(encoding="utf-8"))
    _write_findings(rd3, "MG-1", [s["id"] for s in cov3["subjects"][:-1]])
    _write_findings(rd3, "MG-4", ["manuscript"])
    code, log = run("manuscript_gate.py", args3 + ["--round", "1", "--verdict-only"])
    check("one missing findings file blocks the PASS",
          _verdict(log) == "PASS-PARTIAL",
          "a dispatched subject with no findings file was not audited; counting it "
          "as covered would make the whole measurement decorative")


def _intractable_corpus(tmp: Path, name: str, tuned: str = "") -> Path:
    """A corpus with one rule too wide to judge in a single agent run.

    Built rather than checked in, because the shape is arithmetic: the rule needs
    three key terms whose union exceeds the tractability ceiling while each term
    stays under the --df-ceiling, and that only holds at a corpus size no
    hand-written fixture would carry.
    """
    work = tmp / name
    (work / "final").mkdir(parents=True)
    (work / "bible").mkdir(parents=True)
    L = ["# Unit 01", "", "## The rule", "",
         "You must never call `AlphaFn`, `BetaFn` or `GammaFn` on a loaded field.", ""]
    marks = ["AlphaFn"] * 18 + ["BetaFn"] * 18 + ["GammaFn"] * 18 + [""] * 86
    for i, mark in enumerate(marks):
        L += [f"## Example {i}", "", "```sql",
              f"LOAD {mark or 'Plain'}(Field) RESIDENT Stage{i};", "```", ""]
    (work / "final" / "unit-01.md").write_text("\n".join(L), encoding="utf-8")
    # Declare the concept probe rather than leaving it to the frequency
    # bootstrap: this corpus is about MG-2's depth, and a heuristic deciding how
    # many concepts exist would make the assertion depend on something the test
    # is not measuring. One unit means nothing spans two, so MG-1's eligible
    # surface is legitimately empty.
    (work / "bible" / "concept-probes.yaml").write_text(
        "probes:\n  - id: loaded_field\n    include: 'loaded field'\n", encoding="utf-8")
    if tuned:
        (work / "bible" / "rule-probes-tuned.yaml").write_text(tuned, encoding="utf-8")
    return work


def test_depth_axis(tmp: Path) -> None:
    print("\nmanuscript_gate — breadth and depth are separate terms")
    work = _intractable_corpus(tmp, "depth")
    args = ["--root", str(work), "--units", "final/*.md", "--date", "2026-01-01"]
    rd = work / "reviews" / "manuscript-gate-2026-01-01" / "round-1"

    run("manuscript_gate.py", args + ["--round", "1"])
    cov = json.loads((rd / "coverage-MG-2.json").read_text(encoding="utf-8"))
    check("the wide rule is eligible and emitted", cov["selected"] == 1,
          f"got {cov['selected']}/{cov['eligible_candidates']}")
    check("it is flagged as judgeable only from a sample",
          cov["sampled_within"] == 1,
          f"got sampled_within={cov['sampled_within']} — the rule reaches "
          f"{cov['subjects'][0]['instances'] if cov['subjects'] else '?'} instances")

    proposed = rd / "rule-probes-proposed.yaml"
    check("the intractable rule gets a worklist entry", proposed.exists()
          and "AlphaFn" in proposed.read_text(encoding="utf-8"),
          "an escape hatch nobody can find is not an escape hatch: depth closes by "
          "narrowing these one at a time, so the toolkit owes a ranked list rather "
          "than a blank file")

    # Breadth short AND depth short: breadth wins, because 'nobody opened it' is
    # a worse state than 'we read part of it'.
    _write_findings(rd, "MG-4", ["manuscript"])
    code, log = run("manuscript_gate.py", args + ["--round", "1", "--verdict-only"])
    check("an unopened subject outranks a sampled one",
          _verdict(log) == "PASS-PARTIAL", f"got {_verdict(log)}")

    _write_findings(rd, "MG-2", [s["id"] for s in cov["subjects"]], sampled=True)
    code, log = run("manuscript_gate.py", args + ["--round", "1", "--verdict-only"])
    check("every subject opened but one only sampled -> PASS-SAMPLED",
          _verdict(log) == "PASS-SAMPLED",
          f"got {_verdict(log)} — collapsing the two axes made PASS unreachable by "
          f"construction: 221 of 454 rules on the reference book were over the "
          f"ceiling, so `sampled == 0` could never hold however many rounds ran")
    check("the verdict names the way out of the depth axis",
          "rule-probes-tuned" in log,
          "a criterion nobody can satisfy decays exactly like a floor nobody "
          "defends; the difference is whether there is a ladder")

    print("manuscript_gate — narrowing the rule closes the depth axis")
    work2 = _intractable_corpus(tmp, "depth-tuned", tuned=(
        "rules:\n"
        "  - id: unit-01-5-alphafn\n"
        "    key_terms: [AlphaFn]\n"
        "    note: the rule is about AlphaFn; the other two are taught elsewhere\n"))
    args2 = ["--root", str(work2), "--units", "final/*.md", "--date", "2026-01-01"]
    rd2 = work2 / "reviews" / "manuscript-gate-2026-01-01" / "round-1"
    code, log = run("manuscript_gate.py", args2 + ["--round", "1"])
    cov2 = json.loads((rd2 / "coverage-MG-2.json").read_text(encoding="utf-8"))
    check("a tuned probe brings the rule under the ceiling",
          cov2["sampled_within"] == 0,
          f"got sampled_within={cov2['sampled_within']}; log tail: {log.strip()[-300:]}")

    _write_findings(rd2, "MG-2", [s["id"] for s in cov2["subjects"]])
    _write_findings(rd2, "MG-4", ["manuscript"])
    code, log = run("manuscript_gate.py", args2 + ["--round", "1", "--verdict-only"])
    check("depth closed by WORK reaches a real PASS", _verdict(log) == "PASS",
          f"got {_verdict(log)} — this is the whole point of the ladder: PASS has "
          f"to be reachable without a waiver. log tail: {log.strip()[-400:]}")


def test_pool_drains(tmp: Path) -> None:
    print("\nmanuscript_gate — round 2 audits what round 1 did not")
    work = _clean_corpus(tmp, "drain")
    args = ["--root", str(work), "--units", "final/*.md", "--date", "2026-01-01"]
    run_dir = work / "reviews" / "manuscript-gate-2026-01-01"

    run("manuscript_gate.py", args + ["--round", "1", "--top-concepts", "1"])
    r1 = json.loads((run_dir / "round-1" / "coverage-MG-1.json").read_text("utf-8"))
    first = [s["id"] for s in r1["subjects"]]
    _write_findings(run_dir / "round-1", "MG-1", first)
    run("manuscript_gate.py", args + ["--round", "1", "--verdict-only"])
    check("the audit ledger is persisted", (run_dir / "audited.yaml").exists(),
          "without it round 2 re-selects round 1's slice and the quota is a "
          "permanent ceiling rather than a cost dial")

    code, log = run("manuscript_gate.py", args + ["--round", "2", "--top-concepts", "1"])
    r2 = json.loads((run_dir / "round-2" / "coverage-MG-1.json").read_text("utf-8"))
    second = [s["id"] for s in r2["subjects"]]
    check("round 2 selects different subjects", bool(second) and not set(second) & set(first),
          f"round 1 audited {first}, round 2 emitted {second} — rounds 2+ that "
          f"re-read the same slice satisfy 'two quiet rounds' by construction")
    check("already-audited subjects stay in the denominator",
          r2["eligible_candidates"] == r1["eligible_candidates"],
          "shrinking the denominator would manufacture the completeness this "
          "whole measurement exists to report")
    check("coverage grows between rounds",
          len(r2["already_audited"]) == len(first), f"got {r2['already_audited']}")

    # An edited subject comes back. This is propagation, applied to the ledger:
    # edit a passage OF THE CONCEPT round 1 audited, not just any passage.
    dossier = (run_dir / "round-1" / "dossiers" / f"{first[0]}.md").read_text("utf-8")
    site = next(l for l in dossier.splitlines() if l.startswith("### final/"))
    loc = site.split()[1]
    rel, _, ln = loc.rpartition(":")
    edited = work / rel
    lines = edited.read_text(encoding="utf-8").splitlines()
    lines[int(ln) - 1] += " An edit that changes what this passage claims."
    edited.write_text("\n".join(lines) + "\n", encoding="utf-8")

    run("manuscript_gate.py", args + ["--round", "3", "--top-concepts", "1"])
    r3 = json.loads((run_dir / "round-3" / "coverage-MG-1.json").read_text("utf-8"))
    check("an edited subject is re-queued", bool(r3["requeued"]),
          "a subject whose text changed since it was audited must go back into "
          "the pool, or the ledger becomes a claim about a book that no longer exists")


def test_fixed_defects(tmp: Path) -> None:
    print("\ncheck_fixed_defects — a fixed defect cannot walk back in")
    work = tmp / "fixed"
    (work / "final").mkdir(parents=True)
    (work / "bible").mkdir(parents=True)
    (work / "final" / "unit-01.md").write_text(
        "# Unit 01\n\n"
        "## The regression\n\n"
        "The set modifier has two slots, and the outer one wins.\n\n"
        "## The teaching passage\n\n"
        "Writers reach for the two slots model here.\n"
        "That is the one that looks like the fix and is not.\n",
        encoding="utf-8")
    (work / "bible" / "fixed-defects.yaml").write_text(
        "defects:\n"
        "  - id: FIX-01\n"
        "    what: the chapter collapsed three positions into two slots\n"
        "    severity_if_back: critical\n"
        "    forbid:\n"
        "      - kind: regex\n"
        "        pattern: '\\btwo[- ]slots?\\b'\n"
        "    allow_in:\n"
        "      - anchor: \"That is the one that looks like the fix and is not\"\n"
        "        why: the corrected text quotes the wrong form to teach against it\n",
        encoding="utf-8")

    out = work / "fd.json"
    code, log = run("check_fixed_defects.py", [
        "--root", str(work), "--units", "final/*.md", "--json", str(out), "--quiet"])
    data = json.loads(out.read_text(encoding="utf-8"))
    hits = [f["location"] for f in data["findings"]]
    check("the reappearance is found", len(hits) == 1,
          f"got {hits} — nothing else in the toolkit asserts 'this defective "
          f"formulation must not return'")
    check("a reappearance is critical by default",
          data["counts"]["critical"] == 1, str(data["counts"]))
    check("the teaching passage is NOT flagged", bool(data["exemptions"]),
          "the text that corrects a defect quotes the defective form on purpose; "
          "a pin that fires on the fix gets switched off within a week")

    print("check_fixed_defects — silence when nothing regressed")
    (work / "final" / "unit-01.md").write_text(
        "# Unit 01\n\nThe set modifier has three positions, and each is different.\n",
        encoding="utf-8")
    code, log = run("check_fixed_defects.py", [
        "--root", str(work), "--units", "final/*.md", "--json", str(out), "--quiet"])
    data = json.loads(out.read_text(encoding="utf-8"))
    check("clean text produces no finding", not data["findings"],
          f"false positives: {data['findings']}")


def test_anchors(tmp: Path) -> None:
    print("\nresolve_anchors — a moved passage is repaired, a changed one is not")
    work = tmp / "anchors"
    (work / "final").mkdir(parents=True)
    (work / "bible").mkdir(parents=True)
    unit = work / "final" / "unit-01.md"
    unit.write_text(
        "# Unit 01\n\n"
        "## Baselines\n\n"
        "Optimized mode is about 100 times faster than loading the database.\n",
        encoding="utf-8")
    dnt = work / "bible" / "do-not-touch.md"
    dnt.write_text(
        "# Anchors\n\n"
        "### `final/unit-01.md:5` — the baseline hierarchy\n\n"
        "**Anchor:** \"about 100 times faster than loading the database\"\n\n"
        "**What it actually says:** the 100x is against the database.\n",
        encoding="utf-8")
    args = ["--root", str(work), "--units", "final/*.md"]

    out = work / "a.json"
    run("resolve_anchors.py", args + ["--json", str(out), "--quiet"])
    check("an intact reference resolves OK",
          json.loads(out.read_text("utf-8"))["counts"].get("OK") == 1,
          json.dumps(json.loads(out.read_text("utf-8"))["rows"]))

    # ADDING a section is what broke the references three times in one day.
    unit.write_text("# Unit 01\n\n## A new section\n\nInserted.\n\n"
                    + unit.read_text(encoding="utf-8").split("\n", 1)[1],
                    encoding="utf-8")
    run("resolve_anchors.py", args + ["--json", str(out), "--quiet"])
    data = json.loads(out.read_text("utf-8"))
    check("an insertion above reports DRIFT, not a defect",
          data["counts"].get("DRIFT") == 1,
          f"got {data['counts']} — two of three observed breakages were caused by "
          f"adding a section, and a check that shouts when nothing happened gets "
          f"switched off")

    run("resolve_anchors.py", args + ["--heal", "--quiet"])
    run("resolve_anchors.py", args + ["--json", str(out), "--quiet"])
    check("--heal repairs the line from the anchor",
          json.loads(out.read_text("utf-8"))["counts"].get("OK") == 1,
          "without this, keeping references true is recurring manual work, which "
          "means it does not happen")

    # Now CHANGE the passage. This is the case a line number cannot express.
    text = unit.read_text(encoding="utf-8").replace(
        "about 100 times faster than loading the database",
        "roughly ten times faster than a standard load")
    unit.write_text(text, encoding="utf-8")
    run("resolve_anchors.py", args + ["--json", str(out), "--quiet"])
    data = json.loads(out.read_text("utf-8"))
    check("an edited passage reports EDITED, not DRIFT",
          data["counts"].get("EDITED") == 1,
          f"got {data['counts']} — 'it moved' and 'they changed it' need opposite "
          f"responses, and that distinction is the whole point of the anchor")

    before = dnt.read_text(encoding="utf-8")
    run("resolve_anchors.py", args + ["--heal", "--quiet"])
    check("--heal leaves an EDITED reference alone",
          dnt.read_text(encoding="utf-8") == before,
          "re-pointing it would silently attach a verified-correct anchor to text "
          "nobody checked")


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
        test_verification_plan(tmp)
        test_coverage_verdict(tmp)
        test_depth_axis(tmp)
        test_pool_drains(tmp)
        test_fixed_defects(tmp)
        test_anchors(tmp)
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
