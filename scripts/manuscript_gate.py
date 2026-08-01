#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""manuscript_gate.py — Phase 4.5 orchestration and verdict computation.

What this does:

  1. Runs the deterministic checks (MG-5 render lint, claim-index validation,
     MG-6 runner/waiver audit). Always over the whole book — they cost seconds
     and they are what catches collateral damage from a fix.
  2. Prepares the inputs the auditor agents need: concept dossiers, rule
     candidates, and the GROUNDING.md that every auditor reads first.
  3. Computes the propagation set for round 2+, so later rounds audit what
     changed and its siblings rather than the whole book again.
  4. Reads whatever findings JSON files exist and computes the gate verdict.

What this does NOT do: spawn agents. Agent dispatch belongs to the session, not
to a Python script. Run this, dispatch the auditors named in the output, then run
it again with --verdict-only.

See references/manuscript-gate.md for the checks, the taxonomy and the loop.

Usage
  python scripts/manuscript_gate.py --round 1
  python scripts/manuscript_gate.py --deterministic-only
  python scripts/manuscript_gate.py --round 2 --verdict-only
  python scripts/manuscript_gate.py --root /book --units "final/ch-*.md" --round 1
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("Missing PyYAML. Install with: pip install pyyaml")

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from bookkit.project import Project, add_common_args, load_project  # noqa: E402

# D9 (omitted precondition) belongs here. Leaving it out would silently drop the
# one defect class reviewers are already blind to — the failure would compound
# rather than cancel.
DEFECT_RELATIONS = {"D1", "D2", "D3", "D4", "D4a", "D5", "D6", "D7", "D8", "D9"}
POSITIVE_RELATIONS = {"N1", "N2", "D7a"}
BLOCKING = ("critical", "major")

DEFAULTS = {
    "max_rounds": 5,
    "rounds_without_new_to_close": 2,
    "concept_min_units": 2,
    "top_rules": 30,
    "top_concepts": 40,
    "passes_per_subject": 2,
}


@dataclass
class GateState:
    round: int = 1
    verdict: str = "PENDING"
    open_critical: int = 0
    open_major: int = 0
    open_minor: int = 0
    positives: int = 0
    new_blocking: int = 0
    rounds_without_new: int = 0
    deferred: int = 0
    history: list[dict] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Deterministic sweep
# ---------------------------------------------------------------------------


def run_script(name: str, args: list[str]) -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, str(HERE / name), *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def deterministic_sweep(project: Project, round_dir: Path,
                        unit_args: list[str]) -> dict:
    """MG-5 + claim index. Always complete, never sampled."""
    out: dict = {}
    round_dir.mkdir(parents=True, exist_ok=True)

    lint_json = round_dir / "lint-render.json"
    code, log = run_script("lint_render.py", [
        *unit_args, "--json", str(lint_json), "--fail-on", "never", "--quiet"])
    out["lint_render"] = _read_json(lint_json)
    print(log.strip())

    idx_json = round_dir / "claim-index.json"
    code, log = run_script("validate_claim_index.py", [
        *unit_args, "--json", str(idx_json), "--quiet"])
    out["claim_index"] = _read_json(idx_json)
    if log.strip():
        print(log.strip())

    return out


def audit_runners(project: Project) -> dict:
    """MG-6 — every executable surface either ran or carries a waiver.

    A reasoning-only verdict on executable code is not verification. The first
    time eight tests from one such book were run on a real engine, the results
    contradicted what the reviewer had concluded on paper. So this does not
    decide whether reasoning was good enough; it only asks whether the debt is
    declared, and makes an undeclared one blocking.
    """
    surfaces = (project.get("validation_surface.surfaces") or [])
    status = project.load_yaml("project-status.yaml")
    waivers = {w.get("check"): w for w in (status.get("waivers") or [])}

    rows: list[dict] = []
    for s in surfaces:
        sid = s.get("surface", "?")
        runner = str(s.get("runner", "") or "")
        real_runner = bool(runner) and not runner.startswith(("internal:", "reviewer-only"))
        waiver = waivers.get(f"validation_surface.{sid}") or waivers.get(
            "validation_surface.runner")

        # Three states, not two. `executable` declared in meta.yaml is
        # authoritative; the name heuristic is a fallback; and anything the
        # heuristic does not recognize is UNKNOWN, not "fine".
        #
        # Guessing "not executable" is the failure mode that matters here: it
        # turns an undeclared debt into a silent pass, which is exactly how a
        # book shipped with 3,200 lines of code verified only by reasoning.
        if "executable" in s:
            executable = bool(s["executable"])
            determined = True
        else:
            executable = _looks_executable(sid, runner)
            determined = executable or real_runner

        rows.append({
            "surface": sid,
            "runner": runner or "(none)",
            "executable": executable,
            "determined": determined,
            "real_runner": real_runner,
            "waived": bool(waiver),
            "waiver_reason": (waiver or {}).get("reason"),
            "debt": (waiver or {}).get("debt"),
            "blocking": executable and not real_runner and not waiver,
            "undeclared": (not determined) and not waiver,
        })

    if not surfaces:
        rows.append({
            "surface": "(none declared)", "runner": "(none)", "executable": False,
            "real_runner": False, "waived": bool(waivers.get("validation_surface")),
            "blocking": False,
            "waiver_reason": "no validation surface declared for this project",
        })
    return {"surfaces": rows}


def _looks_executable(surface_id: str, runner: str) -> bool:
    """Heuristic default. A project can override with `executable:` per surface."""
    tokens = ("exec", "script", "lint", "sql", "schema", "expression", "code",
              "notebook", "shell", "bash", "python", "js", "node")
    return any(t in surface_id.lower() for t in tokens)


# ---------------------------------------------------------------------------
# Preparation
# ---------------------------------------------------------------------------


def prepare_inputs(project: Project, round_dir: Path, unit_args: list[str],
                   cfg: dict, propagation: list[str] | None) -> list[str]:
    """Build dossiers and rule candidates; return the dispatch checklist."""
    todo: list[str] = []

    probes = project.root / "bible" / "concept-probes.yaml"
    if not probes.exists():
        code, log = run_script("bootstrap_probes.py", unit_args)
        print(log.strip())

    dossiers = round_dir / "dossiers"
    if probes.exists():
        code, log = run_script("build_concept_dossier.py", [
            *unit_args, "--all", "--out", str(dossiers),
            "--min-units", str(cfg["concept_min_units"]),
            "--top", str(cfg["top_concepts"])])
        for line in log.strip().splitlines():
            if line.startswith("[dossier]") and ("skipped" in line or "NOT emitted" in line
                                                 or "index" in line):
                print(line)
        n = len(list(dossiers.glob("*.md"))) - 1 if dossiers.exists() else 0
        todo.append(f"MG-1: dispatch concept-auditor over {max(n, 0)} dossier(s) in "
                    f"{dossiers} — lenses `pairs`, `numbers-and-absolutes`, `source`. "
                    f"Read {dossiers / '_index.md'} first and start with the D2 rows.")
    else:
        todo.append("MG-1: SKIPPED — no bible/concept-probes.yaml and bootstrap failed")

    rules = round_dir / "rules"
    code, log = run_script("extract_rule_candidates.py", [
        *unit_args, "--out", str(rules), "--top", str(cfg["top_rules"])])
    for line in log.strip().splitlines():
        if line.startswith("[rules]"):
            print(line)
    todo.append(f"MG-2: dispatch rule-auditor over the rule files in {rules} "
                f"(read {rules / '_index.md'} first)")
    todo.append("MG-1 and MG-2 run TWICE per subject, same prompt, findings merged. "
                "Two runs of one lens disagreed on real sites in the measurement; "
                "the variance is in the sampling, not the prompt. Set `pass: 1|2` in "
                "each findings file so the merge can flag single-round findings.")

    if _has_exercises(project):
        todo.append("MG-3: dispatch rule-auditor in exercise-coverage mode over every "
                    "unit that declares exercises in outline/units.yaml")
    else:
        todo.append("MG-3: skipped — this profile has no exercises")

    todo.append("MG-4: dispatch reader-pov in whole-book mode over manuscript.md "
                "(references/agents/reader-pov.md § Whole-book mode)")

    if propagation:
        todo.insert(0, f"Round scope is INCREMENTAL: {len(propagation)} site(s) in the "
                       f"propagation set. See {round_dir / 'propagation.json'}.")
    return todo


def _has_exercises(project: Project) -> bool:
    if str(project.get("structure.exercises", "none")) not in ("none", "", "None"):
        return True
    outline = project.load_yaml("outline/units.yaml")
    for unit in (outline.get("units") or []):
        if unit.get("exercises"):
            return True
    return False


def propagation_set(project: Project, claim_index_result: dict) -> list[str]:
    """Sites to re-audit next round: what changed, plus its siblings.

    This is the entire reason `related` exists in the claim index. Without it,
    every round re-audits the whole book, the loop becomes unaffordable, someone
    cuts it to one pass, and the gate stops being a gate.
    """
    sites: list[str] = []
    for entry in (claim_index_result.get("propagate") or []):
        sites.append(entry["changed"])
        sites.extend(entry.get("review") or [])
    seen: set[str] = set()
    return [s for s in sites if not (s in seen or seen.add(s))]


# ---------------------------------------------------------------------------
# Verdict
# ---------------------------------------------------------------------------


def read_findings(round_dir: Path) -> list[dict]:
    """Read every findings file and MERGE the two passes.

    MG-1 and MG-2 auditors run twice on the same subject with the same prompt.
    Measured: two runs of one lens over the same six rules disagreed on real
    sites, and one finding existed in only one run. The variance is in the
    sampling, not the instructions, so no prompt tuning removes it — two passes
    and a union do.

    Merging also produces a free signal. A finding only one pass found is the
    first candidate for a false positive: `single_round: true`, and it goes to
    the front of the verification queue.
    """
    raw: list[dict] = []
    fdir = round_dir / "findings"
    if not fdir.exists():
        return raw
    for path in sorted(fdir.glob("*.json")):
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            print(f"[gate] UNREADABLE findings file {path.name}: {exc}")
            continue
        for f in (doc.get("findings") or []):
            f["_file"] = path.name
            f["_check"] = doc.get("check")
            f["_lens"] = doc.get("lens")
            f["_subject"] = doc.get("subject")
            f["_sampled"] = bool(doc.get("sampled"))
            f["_pass"] = doc.get("pass")
            raw.append(f)

    merged: dict[str, dict] = {}
    passes: dict[str, set] = {}
    for f in raw:
        k = _key(f)
        passes.setdefault(k, set()).add(f.get("_pass"))
        if k not in merged:
            merged[k] = f
        else:
            # Keep the richer record: a pass that filled other_sites or the
            # omitted precondition knows more than one that did not.
            if len(f.get("other_sites") or []) > len(merged[k].get("other_sites") or []):
                merged[k] = f

    out = list(merged.values())
    for f in out:
        seen = {p for p in passes[_key(f)] if p is not None}
        # Only meaningful once both passes actually ran and are labelled.
        f["single_round"] = bool(seen) and len(seen) == 1 and len(
            {p for ps in passes.values() for p in ps if p is not None}) > 1
    return out


def compute_verdict(findings: list[dict], lint: dict, runners: dict,
                    prior_rounds: list[dict], cfg: dict) -> GateState:
    st = GateState()

    def unresolved(f: dict) -> bool:
        decision = (f.get("resolution") or {}).get("decision", "open")
        if decision in ("fixed", "rejected", "waived"):
            return False
        # A finding the verifier refuted is not a defect. That is the whole point
        # of the adversarial pass, and treating REFUTED as open would make the
        # loop non-terminating.
        return (f.get("verification") or {}).get("verdict") != "REFUTED"

    for f in findings:
        rel = f.get("relation")
        if rel in POSITIVE_RELATIONS:
            st.positives += 1
            continue
        if rel not in DEFECT_RELATIONS or not unresolved(f):
            continue
        sev = (f.get("verification") or {}).get("corrected_severity") or f.get("severity")
        if sev == "critical":
            st.open_critical += 1
        elif sev == "major":
            st.open_major += 1
        elif sev == "minor":
            st.open_minor += 1

    # MG-5 criticals block on their own. They are deterministic and unarguable:
    # a paragraph that prints as a heading is not a matter of opinion.
    lint_critical = int((lint.get("counts") or {}).get("critical", 0))
    lint_major = int((lint.get("counts") or {}).get("major", 0))
    st.open_critical += lint_critical
    st.open_major += lint_major

    blocking_runners = [r for r in (runners.get("surfaces") or []) if r.get("blocking")]
    st.open_major += len(blocking_runners)
    for r in blocking_runners:
        st.notes.append(
            f"MG-6: surface `{r['surface']}` is executable but its runner is "
            f"`{r['runner']}`, and there is no waiver. Either run it, or record a "
            f"waiver with the test plan as declared debt (references/test-plan.md).")
    for r in (runners.get("surfaces") or []):
        if r.get("undeclared"):
            st.notes.append(
                f"MG-6: cannot tell whether surface `{r['surface']}` is executable. "
                f"Add `executable: true|false` to it in meta.yaml — an undeclared "
                f"surface with no real runner is indistinguishable from a silent skip.")

    if any(f.get("_sampled") for f in findings):
        subs = sorted({f["_subject"] for f in findings if f.get("_sampled")})
        st.notes.append(f"SAMPLED, not exhaustive: {', '.join(subs)}. These may not be "
                        f"reported clean.")

    single = [f for f in findings if f.get("single_round")]
    if single:
        st.notes.append(
            f"{len(single)} finding(s) came from only ONE of the two passes. That is "
            f"the cheapest false-positive signal available — verify these first.")

    omissions = sum(1 for f in findings if f.get("relation") == "D9")
    contradictions = sum(1 for f in findings
                         if f.get("violation_kind") == "contradiction")
    if contradictions and not omissions:
        st.notes.append(
            "Zero omission findings (D9) alongside "
            f"{contradictions} contradiction(s). Reviewers are structurally blind to "
            "omitted preconditions — measured 6/6 contradictions and 0/2 omissions "
            "before the contract existed. A clean sweep here is more likely a lens "
            "that skipped the class than a book without it.")

    st.verdict = ("BLOCKED" if st.open_critical
                  else "NEEDS-REVISION" if st.open_major
                  else "PASS")

    # Convergence: zero blocking AND N consecutive quiet rounds. One clean round
    # is not evidence — finder agents miss things and the defect tail is long.
    prior_keys = {_key(f) for r in prior_rounds for f in (r.get("finding_keys") or [])}
    st.new_blocking = sum(
        1 for f in findings
        if f.get("relation") in DEFECT_RELATIONS
        and ((f.get("verification") or {}).get("corrected_severity")
             or f.get("severity")) in BLOCKING
        and _key(f) not in prior_keys)

    last_quiet = prior_rounds[-1].get("rounds_without_new", 0) if prior_rounds else 0
    st.rounds_without_new = 0 if st.new_blocking else last_quiet + 1
    return st


def _key(f: dict) -> str:
    if isinstance(f, str):
        return f
    p1 = (f.get("p1") or {}).get("location") or (f.get("instance") or {}).get("location", "")
    p2 = (f.get("p2") or {}).get("location", "") if f.get("p2") else ""
    return f"{f.get('relation')}|{p1}|{p2}|{f.get('_subject', '')}"


def converged(st: GateState, cfg: dict) -> bool:
    return (st.verdict == "PASS"
            and st.rounds_without_new >= cfg["rounds_without_new_to_close"])


# ---------------------------------------------------------------------------


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def gate_config(project: Project) -> dict:
    cfg = dict(DEFAULTS)
    raw = project.get("pipeline.manuscript_gate") or {}
    for k in cfg:
        if k in raw:
            cfg[k] = raw[k]
    cfg["checks"] = raw.get("checks") or {}
    return cfg


def load_state(run_dir: Path) -> list[dict]:
    p = run_dir / "state.json"
    return _read_json(p).get("rounds", []) if p.exists() else []


def save_state(run_dir: Path, rounds: list[dict]) -> None:
    (run_dir / "state.json").write_text(
        json.dumps({"rounds": rounds}, indent=2, ensure_ascii=False), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Phase 4.5 manuscript gate.")
    add_common_args(ap)
    ap.add_argument("--round", type=int, default=1)
    ap.add_argument("--run-dir", default=None,
                    help="Defaults to reviews/manuscript-gate-<date>/. Pass --date or "
                         "this explicitly; the script never reads the clock, so that a "
                         "re-run lands in the same place.")
    ap.add_argument("--date", default=None, help="YYYY-MM-DD for the run directory.")
    ap.add_argument("--deterministic-only", action="store_true",
                    help="MG-5 + claim index + MG-6 only. Fast; run any time.")
    ap.add_argument("--verdict-only", action="store_true",
                    help="Recompute the verdict from existing findings; prepare nothing.")
    args = ap.parse_args(argv)

    project = load_project(args.root, args.units)
    cfg = gate_config(project)
    unit_args = ["--root", str(project.root)]
    for u in (args.units or []):
        unit_args += ["--units", u]

    if args.run_dir:
        run_dir = Path(args.run_dir)
    else:
        stamp = args.date or _existing_run_stamp(project) or "current"
        run_dir = project.reviews / f"manuscript-gate-{stamp}"
    round_dir = run_dir / f"round-{args.round}"
    round_dir.mkdir(parents=True, exist_ok=True)

    print(f"[gate] {project.root.name} · round {args.round}/{cfg['max_rounds']} · {run_dir}")

    det = {} if args.verdict_only else deterministic_sweep(project, round_dir, unit_args)
    if args.verdict_only:
        det = {"lint_render": _read_json(round_dir / "lint-render.json"),
               "claim_index": _read_json(round_dir / "claim-index.json")}
    runners = audit_runners(project)
    (round_dir / "runners.json").write_text(
        json.dumps(runners, indent=2, ensure_ascii=False), encoding="utf-8")

    if args.deterministic_only:
        _print_deterministic(det, runners)
        return 0

    prior = load_state(run_dir)
    todo: list[str] = []
    if not args.verdict_only:
        prop = propagation_set(project, det.get("claim_index") or {}) if args.round > 1 else []
        if prop:
            (round_dir / "propagation.json").write_text(
                json.dumps({"sites": prop}, indent=2), encoding="utf-8")
        todo = prepare_inputs(project, round_dir, unit_args, cfg, prop)

    findings = read_findings(round_dir)
    st = compute_verdict(findings, det.get("lint_render") or {}, runners, prior, cfg)
    st.round = args.round
    st.deferred = _count_deferred(round_dir)

    print()
    _print_deterministic(det, runners)
    print(f"[gate] findings read: {len(findings)} "
          f"({st.positives} verified-correct, {st.deferred} deferred)")
    print(f"[gate] open: {st.open_critical} critical · {st.open_major} major · "
          f"{st.open_minor} minor · new blocking this round: {st.new_blocking}")
    for note in st.notes:
        print(f"[gate] NOTE {note}")

    print(f"\n[gate] VERDICT: {st.verdict}")
    if converged(st, cfg):
        print(f"[gate] CONVERGED — PASS with {st.rounds_without_new} consecutive "
              f"round(s) with no new blocking findings. The book can reach `complete`.")
    elif st.verdict == "PASS":
        need = cfg["rounds_without_new_to_close"] - st.rounds_without_new
        print(f"[gate] NOT converged — PASS, but {need} more quiet round(s) needed. "
              f"One clean round is not evidence; finder agents miss things.")
    elif args.round >= cfg["max_rounds"]:
        print(f"[gate] MAX ROUNDS REACHED without converging. Do NOT relax the "
              f"criterion. Produce the escalation packet "
              f"(references/loopback-handoff.md shape) and set "
              f"`phase: blocked-on-manuscript-gate`.")

    if todo:
        print("\n[gate] dispatch these, then re-run with --verdict-only:")
        for t in todo:
            print(f"  - {t}")

    prior.append({
        "round": args.round, "verdict": st.verdict,
        "open_critical": st.open_critical, "open_major": st.open_major,
        "open_minor": st.open_minor, "positives": st.positives,
        "new_blocking": st.new_blocking,
        "rounds_without_new": st.rounds_without_new,
        "converged": converged(st, cfg),
        "finding_keys": [_key(f) for f in findings],
    })
    save_state(run_dir, prior)
    return 0


def _existing_run_stamp(project: Project) -> str | None:
    if not project.reviews.exists():
        return None
    runs = sorted(p.name for p in project.reviews.glob("manuscript-gate-*") if p.is_dir())
    return runs[-1].replace("manuscript-gate-", "") if runs else None


def _count_deferred(round_dir: Path) -> int:
    n = 0
    for path in (round_dir / "findings").glob("*.json") if (round_dir / "findings").exists() else []:
        try:
            n += len(json.loads(path.read_text(encoding="utf-8")).get("deferred") or [])
        except json.JSONDecodeError:
            pass
    return n


def _print_deterministic(det: dict, runners: dict) -> None:
    lint = (det.get("lint_render") or {}).get("counts") or {}
    print(f"[gate] MG-5 render lint: {lint.get('critical', 0)} critical · "
          f"{lint.get('major', 0)} major · {lint.get('minor', 0)} minor")
    ci = (det.get("claim_index") or {})
    counts = ci.get("counts") or {}
    print(f"[gate] claim index: " + ("  ".join(f"{k}={v}" for k, v in sorted(counts.items()))
                                     or "not built yet")
          + f" · PROPAGATE={len(ci.get('propagate') or [])}")
    rows = runners.get("surfaces") or []
    blocking = sum(1 for r in rows if r.get("blocking"))
    print(f"[gate] MG-6 runners: {len(rows)} surface(s), {blocking} blocking")


if __name__ == "__main__":
    sys.exit(main())
