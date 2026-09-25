#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""manuscript_gate.py — Phase 4.5: sweep, agent inputs, cumulative findings, verdict.

What it does, per run:

  1. Deterministic sweep (always the whole book): rebuild manuscript.md, MG-5
     render lint, claim index, anchors, MG-7 fixed defects; literary: MG-S
     (`check_story.py --manuscript`) and MG-T (`lint_fiction.py --book`).
  2. Prepare agent inputs (technical): MG-1 dossiers, MG-2 rule files, the
     GROUNDING.md every auditor reads first.
  3. Ingest every findings file of every round into `findings.jsonl` (content-keyed,
     statuses open|fixed|refuted|accepted-risk) and every audit into
     `subjects.json` (pending | audited@hash | sampled@hash).
  4. Compute the verdict over ALL open findings, coverage, and convergence.

It never spawns agents; the orchestrator dispatches what it lists, then re-runs
with --verdict-only. See references/manuscript-gate.md.

Literary (book-literary): MG-S cannot be switched off or waived, its findings
cannot be resolved by hand (they close when the sweep stops reporting them), a
missing or failing check_story.py is an ERROR, MG-4 and MG-C can be neither
switched off nor coverage-waived and need two passes per manuscript hash, and
convergence re-runs `check_story.py --manuscript` live — it must exit 0. Agent
findings marked `rule: R1|R2` (an unresolved arc, an undelivered ending) close
only through a re-audit of CHANGED text that no longer reports them — never
through --resolve or a verifier's REFUTED. A round beyond `max_rounds` is refused.

--resolve discipline (every profile). Deterministic findings (MG-5, MG-7,
MG-S, MG-T) and configuration findings are never `fixed` or `refuted` by hand:
they close when the sweep stops reporting them. `accepted-risk` only for a
non-critical MG-5/MG-T or a minor MG-7. Agent findings (MG-1..4, MG-C): `fixed`
needs a note AND evidence — the text the finding points at (its unit, or the
manuscript for whole-book subjects) changed since the finding was recorded;
`refuted` and `accepted-risk` need a note of 20+ characters that is not a
placeholder; `accepted-risk` is never for a critical. Hand edits to
findings.jsonl are re-validated on every run. state.json records every round's
finding keys: a findings.jsonl missing keys an earlier round recorded is an
ERROR ("findings store truncated").

Waivers must say who, why and what is owed with real content: `waived_by`,
`reason`, `debt` not placeholders, `reason` and `debt` 20+ characters.
`rounds_without_new_to_close` below 2 is clamped to 2 (with a note). An
executable validation surface is satisfied only by `evidence: <path>` naming an
existing runner-output file — a runner string ("never run", "reviewer-only")
is not evidence — or by a complete waiver with a plan entry.

`project.profile` (stripped, lowercased) must name a known profile and
`schema_version` must be "3.4": otherwise exit 2.

Usage
  python scripts/manuscript_gate.py --round 1                 # sweep + prepare + verdict
  python scripts/manuscript_gate.py --round 1 --verdict-only  # after the auditors wrote files
  python scripts/manuscript_gate.py --deterministic-only      # seconds; touches no round
  python scripts/manuscript_gate.py --resolve KEY --status fixed --note "fixed in unit-07"

Exit codes: 0 converged · 1 not converged · 2 ERROR (a tool failed, a findings file
is invalid, the round was never swept, or a usage error).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from bookkit import lexicon as LX  # noqa: E402
from bookkit.anchors import norm  # noqa: E402
from bookkit.coverage import coverage_path, load_manifest, save_manifest  # noqa: E402
from bookkit.placeholder import is_placeholder  # noqa: E402
from bookkit.project import (  # noqa: E402
    Project, add_common_args, as_list, load_project, natural_key, unit_number,
)
from bookkit.schema import load_schema, validate  # noqa: E402
from bookkit.textio import read_text  # noqa: E402
from bookkit.textmetrics import text_hash  # noqa: E402

DEFECT_RELATIONS = {"D1", "D2", "D3", "D4", "D4a", "D5", "D6", "D7", "D8", "D9"}
POSITIVE_RELATIONS = {"N1", "N2", "D7a"}
BLOCKING = ("critical", "major")
SEV_RANK = {"critical": 0, "major": 1, "minor": 2}
STATUSES = ("open", "fixed", "refuted", "accepted-risk")
COVERAGE_WAIVER = "manuscript_gate.coverage"

TECHNICAL_CHECKS = ["MG-1", "MG-2", "MG-3", "MG-4", "MG-5", "MG-6", "MG-7"]
LITERARY_CHECKS = ["MG-4", "MG-5", "MG-7", "MG-S", "MG-T", "MG-C"]
AGENT_CHECKS = ("MG-1", "MG-2", "MG-3", "MG-4", "MG-C")
NA_LITERARY = ("MG-1", "MG-2", "MG-3", "MG-6")
TOOL_CHECKS = ("MG-5", "MG-7", "MG-S", "MG-T")
RISK_OK = ("MG-5", "MG-T")                 # tool checks a human may accept as a (non-critical) risk
LITERARY_ALWAYS_ON = ("MG-S", "MG-4", "MG-C")   # R1–R4 and the page-level ending/arc read
STORY_RULES = ("R1", "R2")                 # agent findings about arcs / the ending (literary)
MIN_NOTE = 20                              # characters of a refuted / accepted-risk note, a waiver's why
MIN_ROUNDS_QUIET = 2
PLAN_DEFAULT = "reviews/verification-plan/PLAN.md"
NON_CODE_TAGS = {"text", "txt", "plain", "plaintext", "markdown", "md", "output", "log",
                 "none", "nohighlight", "console-output"}

DEFAULTS = {"max_rounds": 5, "rounds_without_new_to_close": 2, "concept_min_units": 2,
            "top_rules": 30, "top_concepts": 40, "passes_per_subject": 2}

# Sweep outputs, deleted before every sweep so a crashed tool can never be read
# through a stale file from an earlier run.
ROUND_OUTPUTS = ["lint-render.json", "claim-index.json", "anchors.json",
                 "fixed-defects.json", "story.json", "fiction.json", "deterministic.json",
                 "coverage-MG-1.json", "coverage-MG-2.json", "rule-probes-proposed.yaml"]
ROUND_DIRS = ["dossiers", "rules"]
CHECKABLE_NEEDS = {"runner", "live-system", "measurement", "person", "document-of-record"}


class GateError(Exception):
    """A usage error: exit 2 with the message."""


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------


def run_tool(script: str, args: list[str]) -> tuple[int, str]:
    proc = subprocess.run([sys.executable, str(HERE / script), *args],
                          capture_output=True, text=True, encoding="utf-8", errors="replace")
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def _tail(log: str, n: int = 240) -> str:
    return " ".join(log.strip().split())[-n:]


def read_json(path: Path) -> dict | None:
    """Parsed JSON object, or None when missing/unreadable. Never `{}` for a missing file."""
    if not path.exists():
        return None
    try:
        data = json.loads(read_text(path))
    except (json.JSONDecodeError, OSError):
        return None
    return data if isinstance(data, dict) else None


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True),
                    encoding="utf-8")


def make_key(*parts) -> str:
    raw = "|".join(norm(str(p or "")) for p in parts)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]


def gate_config(project: Project) -> dict:
    raw = project.get("pipeline.manuscript_gate") or {}
    cfg = {k: raw.get(k, v) for k, v in DEFAULTS.items()}
    cfg["checks"] = raw.get("checks") or {}
    cfg["_notes"] = []
    try:
        quiet = int(cfg["rounds_without_new_to_close"])
    except (TypeError, ValueError):
        quiet = MIN_ROUNDS_QUIET
    if quiet < MIN_ROUNDS_QUIET:
        cfg["_notes"].append(f"rounds_without_new_to_close {cfg['rounds_without_new_to_close']!r} "
                             f"is below {MIN_ROUNDS_QUIET}: clamped to {MIN_ROUNDS_QUIET} (one "
                             "quiet round proves nothing)")
        quiet = MIN_ROUNDS_QUIET
    cfg["rounds_without_new_to_close"] = quiet
    return cfg


def manuscript_hash(project: Project) -> str:
    return text_hash("\n\n".join(read_text(p) for p in project.unit_paths))


def waivers(project: Project) -> list[dict]:
    """Every waiver entry, complete or not (see `waiver_problem`)."""
    return [w for w in as_list(project.load_yaml("project-status.yaml").get("waivers"))
            if isinstance(w, dict)]


def _filled(value, min_chars: int = 0) -> bool:
    return not is_placeholder(value) and len(str(value).strip()) >= min_chars


def waiver_problem(w: dict) -> str:
    """Why a waiver does not count: it must say who, why and what is owed
    (`waived_by`/`by`, `reason`, `debt`/`owed`) with real content — not a
    placeholder (`x`, `N/A`, `TBD`, …), and `reason`/`debt` of at least
    MIN_NOTE characters. '' when complete."""
    missing = [name for name, keys, n in (("waived_by", ("waived_by", "by"), 0),
                                          ("reason", ("reason",), MIN_NOTE),
                                          ("debt", ("debt", "owed"), MIN_NOTE))
               if not any(_filled(w.get(k), n) for k in keys)]
    return (f"missing or placeholder {', '.join(missing)} (reason and debt: {MIN_NOTE}+ "
            "characters of real content)") if missing else ""


def plan_entry(project: Project, w: dict) -> str:
    """'' when the waiver names a verification-plan entry that exists
    (`plan: reviews/verification-plan/PLAN.md#V-03`, or `plan_entry: V-03`),
    else why not. A plan file with no entry for this debt is not a plan."""
    ref = str(w.get("plan") or "")
    path, _, anchor = ref.partition("#")
    anchor = anchor or str(w.get("plan_entry") or "")
    path = path or PLAN_DEFAULT
    m = re.fullmatch(r"\s*V-?0*(\d+)\s*", anchor, re.I)
    if not m:
        return (f"names no plan entry — add `plan: {PLAN_DEFAULT}#V-NN` pointing at the "
                f"entry that records this debt (references/verification-plan.md)")
    file = project.root / path
    if not file.exists():
        return f"its plan {path} does not exist"
    if not re.search(rf"^#{{2,4}}\s+V-0*{m.group(1)}\b", read_text(file), re.M):
        return f"{path} has no entry V-{int(m.group(1)):02d}"
    return ""


def _code_blocks(project: Project) -> list[str]:
    """Language tags of the fenced code blocks in the units (executable-looking)."""
    tags = []
    for p in project.unit_paths:
        for line in read_text(p).splitlines():
            m = re.match(r"^\s*(?:`{3,}|~{3,})\s*([A-Za-z][\w+#.-]*)", line)
            if m and m.group(1).lower() not in NON_CODE_TAGS:
                tags.append(m.group(1).lower())
    return tags


def applicable_checks(project: Project) -> list[str]:
    return LITERARY_CHECKS if project.literary else TECHNICAL_CHECKS


# ---------------------------------------------------------------------------
# Run directory, state
# ---------------------------------------------------------------------------


def resolve_run_dir(project: Project, args) -> Path:
    """--run-dir > --date > the latest existing run with a state.json > `-current`."""
    if args.run_dir:
        return Path(args.run_dir)
    if args.date:
        return project.reviews / f"manuscript-gate-{args.date}"
    runs = sorted((p for p in project.reviews.glob("manuscript-gate-*")
                   if (p / "state.json").exists()), key=lambda p: p.name)
    return runs[-1] if runs else project.reviews / "manuscript-gate-current"


def load_state(run_dir: Path) -> dict:
    st = read_json(run_dir / "state.json") or {}
    st.setdefault("rounds", {})
    return st


def swept_rounds(state: dict, upto: int) -> list[int]:
    return sorted(int(r) for r, v in state["rounds"].items() if v.get("swept") and int(r) <= upto)


# ---------------------------------------------------------------------------
# Deterministic sweep
# ---------------------------------------------------------------------------


def sweep(project: Project, round_dir: Path, unit_args: list[str], checks: list[str],
          errors: list[str]) -> dict:
    """Run every deterministic tool. A non-zero exit or a missing output is an ERROR."""
    for name in ROUND_OUTPUTS:
        (round_dir / name).unlink(missing_ok=True)
    for name in ROUND_DIRS:
        shutil.rmtree(round_dir / name, ignore_errors=True)
    round_dir.mkdir(parents=True, exist_ok=True)
    out: dict = {"tools": {}, "blocked": {}}

    code, log = run_tool("sync_manuscript.py", unit_args)
    if code != 0:
        errors.append(f"sync_manuscript.py exited {code}: {_tail(log)}")

    def json_tool(label: str, script: str, args: list[str], name: str,
                  ok: tuple[int, ...] = (0,), need: str = "") -> dict | None:
        path = round_dir / name
        code, log = run_tool(script, [*args, "--json", str(path)])
        data = read_json(path)
        if code not in ok or data is None or (need and not isinstance(data.get(need), list)):
            errors.append(f"{label}: {script} exited {code}"
                          + (" and wrote no valid JSON" if data is None else "")
                          + f" — {_tail(log)}")
            return None
        return data

    if "MG-5" in checks:
        out["tools"]["MG-5"] = json_tool("MG-5", "lint_render.py", [
            *unit_args, "--fail-on", "never", "--quiet"], "lint-render.json", need="findings")
    if not project.literary:
        out["claim_index"] = json_tool("claim index", "validate_claim_index.py",
                                       [*unit_args, "--quiet"], "claim-index.json")
    out["anchors"] = json_tool("anchors", "resolve_anchors.py", [*unit_args, "--quiet"],
                               "anchors.json")
    if "MG-7" in checks:
        out["tools"]["MG-7"] = json_tool("MG-7", "check_fixed_defects.py", [
            *unit_args, "--quiet", "--fail-on", "never"], "fixed-defects.json", need="findings")
    root_arg = ["--root", str(project.root)]
    for check, script, args, name in (
            ("MG-S", "check_story.py", [*root_arg, "--manuscript"], "story.json"),
            ("MG-T", "lint_fiction.py", [*root_arg, "--book"] + (
                ["--units", unit_args[unit_args.index("--units") + 1]]
                if "--units" in unit_args else []), "fiction.json")):
        if check not in checks:
            continue
        if not (HERE / script).exists():
            if check == "MG-S":
                # R1–R4 are not a coverage question: no waiver may close them.
                errors.append(f"MG-S: scripts/{script} is not installed — the story rules "
                              "cannot be checked; the gate cannot pass without them")
                continue
            # The check could not run, so it is not complete.
            out["blocked"][check] = f"scripts/{script} is not installed"
            continue
        out["tools"][check] = json_tool(check, script, args, name, ok=(0, 1), need="findings")
    return out


def det_records(sweep_out: dict) -> list[dict]:
    """Tool output → normalized finding records, keyed by content (never by line)."""
    recs: list[dict] = []
    seen: dict[str, int] = {}

    def add(check: str, rule: str, severity: str, location: str, text: str, detail: str) -> None:
        file = location.rpartition(":")[0] or location
        base = make_key(check, rule, file, text or detail)
        seen[base] = seen.get(base, 0) + 1
        key = f"{check}-{base}" + (f"-{seen[base]}" if seen[base] > 1 else "")
        recs.append({"key": key, "check": check, "kind": "tool", "relation": rule,
                     "subject": file, "severity": severity, "location": location,
                     "quote": (text or "")[:200], "detail": detail[:300]})

    tools = sweep_out.get("tools") or {}
    for f in (tools.get("MG-5") or {}).get("findings") or []:
        add("MG-5", f.get("check", ""), f.get("severity", "minor"), f.get("location", ""),
            f.get("quote", ""), f.get("message", ""))
    for f in (tools.get("MG-7") or {}).get("findings") or []:
        add("MG-7", f.get("entry", ""), f.get("severity", "critical"), f.get("location", ""),
            f.get("quote", ""), f"matched `{f.get('pattern')}` — {f.get('what', '')}")
    for f in (tools.get("MG-S") or {}).get("findings") or []:
        sev = {"blocking": "critical", "major": "major", "warning": "minor"}.get(
            str(f.get("severity")), "minor")
        add("MG-S", f.get("code", ""), sev, str(f.get("location") or f.get("subject") or ""),
            f"{f.get('subject') or ''} {f.get('detail') or ''}", str(f.get("detail") or ""))
    for f in (tools.get("MG-T") or {}).get("findings") or []:
        sev = str(f.get("severity"))
        if sev not in ("major", "minor"):
            continue                                   # info is observation only
        unit, line = str(f.get("unit") or ""), f.get("line")
        add("MG-T", f.get("rule", ""), sev, f"{unit}:{line}" if line else unit, "",
            f"{unit} {f.get('detail', '')}")
    return recs


def config_records(project: Project, cfg: dict, checks: list[str]) -> tuple[list[dict], set[str], list[str]]:
    """Findings that come from configuration, recomputed on every run.

    Returns (records, checks switched off WITH a valid waiver, notes). A check
    switched off without a complete `manuscript_gate.<check>` waiver (who, why,
    what is owed; MG-6 also a plan entry) is a `major` finding: silence in config
    is how deferred checks disappeared for months. Literary MG-S is never off.
    """
    recs: list[dict] = []
    notes: list[str] = []
    waived: set[str] = set()
    ws = waivers(project)

    def rec(key, check, relation, subject, detail):
        recs.append({"key": key, "check": check, "kind": "config", "relation": relation,
                     "subject": subject, "severity": "major", "location": "bible/meta.yaml",
                     "quote": "", "detail": detail})

    for w in ws:
        why = waiver_problem(w)
        if why:
            notes.append(f"waiver `{w.get('check')}` does not count: {why} (who, why, what is "
                         "owed — SKILL.md principle 8)")
    for check in checks:
        if project.literary and check in LITERARY_ALWAYS_ON:
            why = ("R1–R4 are not waivable" if check == "MG-S" else
                   "the whole-book read of arcs and ending on the page is part of R2")
            if cfg["checks"].get(check) is False:
                rec(f"{check}-cannot-disable", check, "check-disabled", check,
                    f"{check} cannot be disabled in book-literary: {why}. The setting "
                    f"`checks.{check}: false` is ignored — remove it")
            if any(w.get("check") == f"manuscript_gate.{check}" for w in ws):
                notes.append(f"a `manuscript_gate.{check}` waiver is ignored: {why}")
            continue
        if cfg["checks"].get(check) is not False:
            continue
        cands = [w for w in ws if w.get("check") == f"manuscript_gate.{check}"]
        good = [w for w in cands if not waiver_problem(w)
                and (check != "MG-6" or not plan_entry(project, w))]
        if good:
            waived.add(check)
            continue
        extra = ""
        if cands and check == "MG-6":
            extra = " (the waiver " + (waiver_problem(cands[0]) or plan_entry(project, cands[0])) + ")"
        elif cands:
            extra = f" (the waiver is incomplete: {waiver_problem(cands[0])})"
        rec(f"{check}-disabled", check, "check-disabled", check,
            f"{check} is switched off in pipeline.manuscript_gate.checks with no complete "
            f"`manuscript_gate.{check}` waiver in project-status.yaml" + extra)
    if "MG-6" in checks and "MG-6" not in waived and cfg["checks"].get("MG-6") is not False:
        surfaces = [s for s in as_list(project.get("validation_surface.surfaces"))
                    if isinstance(s, dict)]
        tags = _code_blocks(project)
        if tags and not surfaces:
            rec("MG-6-no-surface", "MG-6", "runner", "validation_surface",
                f"code present, no surface declared: {len(tags)} fenced block(s) tagged "
                f"{', '.join(sorted(set(tags))[:6])} and `validation_surface.surfaces` is empty — "
                "declare the surface (references/validation-surface.md) and run it, or waive "
                "it with a plan entry")
        for row in audit_runners(project, ws)["surfaces"]:
            if row.get("blocking"):
                rec(f"MG-6-{make_key('surface', row['surface'])}", "MG-6", "runner",
                    row["surface"], row["why"])
            elif row.get("undeclared"):
                notes.append(f"MG-6: cannot tell whether surface `{row['surface']}` is "
                             f"executable — add `executable: true|false` to it in meta.yaml.")
    return recs, waived, notes


def surface_evidence(project: Project, s: dict) -> str:
    """'' when the surface names `evidence: <path>` — an existing, non-empty
    runner-output file under the project — else why not. A runner string
    ("qlik reload (never run)", "reviewer-only", "x") is a description, never
    evidence that anything ran."""
    ev = s.get("evidence")
    if is_placeholder(ev):
        return "no `evidence: <path>` to the runner's output"
    path = project.root / str(ev).strip()
    try:
        ok = path.is_file() and path.stat().st_size > 0
    except OSError:
        ok = False
    return "" if ok else f"its evidence `{ev}` is not an existing, non-empty file"


def audit_runners(project: Project, ws: list[dict]) -> dict:
    """MG-6 — every executable surface ran (its `evidence` file exists), or
    carries a waiver WITH a plan.

    Three states: `executable` declared wins; the name heuristic is a fallback;
    anything unrecognized is UNKNOWN, not fine. A waiver counts only when it is
    complete and points at a verification-plan entry that exists: a waiver with
    no plan is a promise, not declared debt.
    """
    by_check: dict[str, list[dict]] = {}
    for w in ws:
        by_check.setdefault(str(w.get("check")), []).append(w)
    rows: list[dict] = []
    for s in as_list(project.get("validation_surface.surfaces")):
        if not isinstance(s, dict):
            continue
        sid = str(s.get("surface", "?"))
        runner = str(s.get("runner", "") or "")
        missing = surface_evidence(project, s)
        ran = not missing
        if "executable" in s:
            executable, determined = bool(s["executable"]), True
        else:
            executable = any(t in sid.lower() for t in (
                "exec", "script", "lint", "sql", "schema", "expression", "code", "notebook",
                "shell", "bash", "python", "js", "node"))
            determined = executable or ran
        cands = by_check.get(f"validation_surface.{sid}", []) + by_check.get(
            "validation_surface.runner", [])
        planned = [w for w in cands if not waiver_problem(w) and not plan_entry(project, w)]
        why = ""
        if executable and not ran:
            why = (f"surface `{sid}` is executable (runner `{runner or '(none)'}`) and has "
                   f"{missing}, and "
                   + (f"its waiver does not count — it "
                      + (waiver_problem(cands[0]) or plan_entry(project, cands[0]))
                      if cands else "there is no waiver. Run it and record the output as "
                                    "`evidence`, or waive it WITH a plan entry"))
        rows.append({"surface": sid, "runner": runner or "(none)", "executable": executable,
                     "evidence": s.get("evidence"),
                     "blocking": executable and not ran and not planned,
                     "undeclared": (not determined) and not cands, "why": why})
    return {"surfaces": rows}


# ---------------------------------------------------------------------------
# Findings files
# ---------------------------------------------------------------------------


def read_finding_docs(run_dir: Path, upto: int) -> tuple[list[dict], list[str]]:
    """Every findings file of every round ≤ `upto`, schema-validated.

    An invalid file is an ERROR by name, never a silent drop: `"severity":
    "Critical"` used to count as zero criticals.
    """
    schema = load_schema()
    docs: list[dict] = []
    errors: list[str] = []
    for rd in sorted(run_dir.glob("round-*"), key=lambda p: natural_key(p.name)):
        n = unit_number(rd.name)
        if n is None or n > upto:
            continue
        for path in sorted((rd / "findings").glob("*.json")):
            where = f"{rd.name}/findings/{path.name}"
            try:
                doc = json.loads(read_text(path))
            except json.JSONDecodeError as exc:
                errors.append(f"{where}: not valid JSON ({exc})")
                continue
            problems = validate(doc, schema)
            if problems:
                errors.append(f"{where}: does not match templates/gate-findings.schema.json — "
                              + "; ".join(problems[:3]))
                continue
            m = re.search(r"\.p(\d+)\.json$", path.name)
            doc["_round"] = n
            doc["_pass"] = int(doc.get("pass") or (m.group(1) if m else 1))
            doc["_file"] = where
            docs.append(doc)
    return docs, errors


def subject_of(doc: dict, exercise_ids: dict[int, str]) -> str:
    """The coverage subject a findings file audited."""
    if doc.get("check") == "MG-C":
        return str(doc.get("lens"))
    if doc.get("check") == "MG-3":
        n = unit_number(doc.get("subject"))
        return exercise_ids.get(n, str(doc.get("subject"))) if n is not None else str(doc.get("subject"))
    return str(doc.get("subject"))


def agent_records(docs: list[dict], exercise_ids: dict[int, str]
                  ) -> tuple[dict[str, dict], dict[str, int]]:
    """Merge agent findings across passes, lenses and rounds by content key."""
    out: dict[str, dict] = {}
    positives: dict[str, int] = {}
    for doc in docs:
        check = str(doc.get("check"))
        subject = (subject_of(doc, exercise_ids) if check == "MG-3"
                   else str(doc.get("subject")))
        for f in doc.get("findings") or []:
            rel = f.get("relation")
            if rel in POSITIVE_RELATIONS:
                positives[check] = positives.get(check, 0) + 1
                continue
            if rel not in DEFECT_RELATIONS:
                continue
            side1 = f.get("p1") or f.get("instance") or {}
            side2 = f.get("p2") or {}
            q1, q2 = side1.get("quote") or "", side2.get("quote") or ""
            key = f"{check}-" + make_key(check, subject, rel,
                                         q1 or f.get("canonical_site"), q2)
            ver = f.get("verification") or {}
            sev = ver.get("corrected_severity") or f.get("severity")
            rec = out.setdefault(key, {
                "key": key, "check": check, "kind": "agent", "relation": rel,
                "subject": subject, "severity": sev,
                "location": side1.get("location") or f.get("canonical_site", ""),
                "quote": q1[:200], "detail": str(f.get("reasoning", ""))[:300],
                "lenses": [], "rounds": [], "passes": [], "files": [],
                "verification": None, "_ver_round": 0})
            if SEV_RANK.get(sev, 9) < SEV_RANK.get(rec["severity"], 9):
                rec["severity"] = sev
            if f.get("rule") in STORY_RULES:
                rec["rule"] = f["rule"]
            if f.get("category"):
                rec["category"] = f["category"]
            for field, val in (("lenses", doc.get("lens")), ("rounds", doc["_round"]),
                               ("passes", doc["_pass"]), ("files", doc["_file"])):
                if val not in rec[field]:
                    rec[field].append(val)
            if ver.get("verdict") and doc["_round"] >= rec["_ver_round"]:
                rec["verification"] = ver.get("verdict")
                rec["_ver_round"] = doc["_round"]
                if ver.get("corrected_severity"):
                    rec["severity"] = ver["corrected_severity"]
    return out, positives


# ---------------------------------------------------------------------------
# The cumulative store
# ---------------------------------------------------------------------------


def load_store(run_dir: Path) -> dict[str, dict]:
    path = run_dir / "findings.jsonl"
    if not path.exists():
        return {}
    out: dict[str, dict] = {}
    for line in read_text(path).splitlines():
        if line.strip():
            rec = json.loads(line)
            out[rec["key"]] = rec
    return out


def save_store(run_dir: Path, store: dict[str, dict]) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps({k: v for k, v in rec.items() if not k.startswith("_")},
                        ensure_ascii=False, sort_keys=True)
             for _k, rec in sorted(store.items())]
    (run_dir / "findings.jsonl").write_text("\n".join(lines) + ("\n" if lines else ""),
                                            encoding="utf-8")


class TextHashes:
    """Hashes of the text a finding points at — its unit (from `location`), or
    the whole manuscript for whole-book subjects (MG-4, MG-C, `manuscript`) —
    per swept round (state.json) and live. `--resolve fixed` needs the live
    hash to differ from the one recorded with the finding: evidence that the
    text was edited, not a declaration."""

    def __init__(self, project: Project | None, state: dict | None):
        self.project = project
        self.state = state or {"rounds": {}}
        self._manuscript: str | None = None

    @staticmethod
    def unit_of(rec: dict) -> str | None:
        loc = str(rec.get("location") or "").strip()
        path = loc.rpartition(":")[0] if re.search(r":\d+$", loc) else loc
        return path.replace("\\", "/") or None

    def whole_book(self, rec: dict) -> bool:
        return (rec.get("check") in ("MG-4", "MG-C") or rec.get("subject") == "manuscript"
                or self.unit_of(rec) is None)

    def live(self, rec: dict) -> str | None:
        if self.project is None:
            return None
        if not self.whole_book(rec):
            p = self.project.root / str(self.unit_of(rec))
            if p.is_file():
                return text_hash(read_text(p))
        if self._manuscript is None:
            self._manuscript = manuscript_hash(self.project)
        return self._manuscript

    def at_round(self, rec: dict, r: int) -> str | None:
        rnd = self.state["rounds"].get(str(r)) or {}
        if self.whole_book(rec):
            return rnd.get("manuscript_hash")
        return (rnd.get("unit_hashes") or {}).get(str(self.unit_of(rec)))

    def round_manuscript(self, r: int) -> str | None:
        return (self.state["rounds"].get(str(r)) or {}).get("manuscript_hash")


def build_store(prev: dict[str, dict], agent: dict[str, dict], docs: list[dict],
                det_by_round: dict[int, list[dict]], live: list[dict], round_no: int,
                exercise_ids: dict[int, str], literary: bool = False,
                hashes: TextHashes | None = None) -> dict[str, dict]:
    """Recompute every record from its sources, then lay the human decisions on top.

    Auto status: agent findings stay `open` until the same subject is re-audited
    (same check and lens) in a LATER round that no longer reports the key, or the
    verifier REFUTED it. Literary R1/R2 findings (`rule`): the re-audit counts
    only on a manuscript that changed since the round that reported them, and a
    verifier's REFUTED does not close them. Tool findings are `open` while the
    latest sweep still reports them. Human `--resolve` decisions are
    re-validated (`resolve_refusal`) on every run: `refuted`/`accepted-risk`
    stick; `fixed` sticks until the key is reported again in a later round (a
    regression) or the text returns to what the finding described.
    """
    hashes = hashes or TextHashes(None, None)
    store: dict[str, dict] = {}
    audits: dict[tuple, list[int]] = {}
    for d in docs:
        audits.setdefault((d.get("check"), subject_of(d, exercise_ids), d.get("lens")), []).append(d["_round"])

    for key, rec in agent.items():
        last = max(rec["rounds"])
        later = [r for lens in rec["lenses"]
                 for r in audits.get((rec["check"], subject_of({"check": rec["check"], "subject": rec["subject"], "lens": lens}, exercise_ids), lens), [])
                 if r > last]
        story_rule = literary and rec.get("rule") in STORY_RULES
        if story_rule:
            h_last = hashes.round_manuscript(last)
            later = [r for r in later if hashes.round_manuscript(r)
                     and hashes.round_manuscript(r) != h_last]
        status, note = "open", ""
        if rec["verification"] == "REFUTED" and not story_rule:
            status, note = "refuted", "refuted by the adversarial verifier"
        elif later:
            status, note = "fixed", f"not reported by the re-audit in round {min(later)}"
        elif rec["verification"] == "REFUTED":
            note = (f"a verifier's REFUTED does not close an {rec['rule']} finding — only a "
                    "re-audit of changed text that no longer reports it")
        recorded = (prev.get(key) or {}).get("recorded_hash") \
            or hashes.at_round(rec, min(rec["rounds"])) or hashes.live(rec)
        store[key] = {**rec, "status": status, "auto_note": note, "recorded_hash": recorded}

    swept = sorted(det_by_round)
    latest = swept[-1] if swept else round_no
    for r in swept:
        for rec in det_by_round[r]:
            cur = store.setdefault(rec["key"], {**rec, "rounds": []})
            cur.update({k: rec[k] for k in ("location", "quote", "detail", "severity")})
            if r not in cur["rounds"]:
                cur["rounds"].append(r)
    for rec in live:
        prior_rounds = (prev.get(rec["key"]) or {}).get("rounds") or []
        store[rec["key"]] = {**rec, "rounds": sorted(set(prior_rounds) | {round_no})}
    live_keys = {r["key"] for r in live}
    for key, rec in store.items():
        if rec["kind"] == "tool":
            present = latest in rec["rounds"]
            rec["status"] = "open" if present else "fixed"
            rec["auto_note"] = "" if present else f"absent from the round-{latest} sweep"
        elif rec["kind"] == "config":
            rec["status"] = "open"
            rec["auto_note"] = ""

    # Config findings that stopped firing, and records whose source files are gone.
    for key, old in prev.items():
        if key in store:
            continue
        if old.get("kind") == "config" and key not in live_keys:
            store[key] = {**old, "status": "fixed", "auto_note": "no longer reported"}
        elif old.get("kind") == "agent":
            store[key] = {**old, "source_missing": True}   # persists until resolved
        elif old.get("kind") == "tool":
            store[key] = {**old, "status": "fixed", "auto_note": "absent from later sweeps"}

    for key, rec in store.items():
        rec["first_round"] = min(rec["rounds"]) if rec.get("rounds") else round_no
        human = (prev.get(key) or {}).get("human")
        rec["history"] = (prev.get(key) or {}).get("history") or []
        why = resolve_refusal(rec, (human or {}).get("status"), str((human or {}).get("note") or ""),
                              literary, hashes.live(rec)) if human else ""
        if why:
            rec["human_ignored"] = f"{human.get('status')} ignored: {why}"
            rec["auto_note"] = rec["human_ignored"]
            human = None
        else:
            rec.pop("human_ignored", None)
        if human:
            rec["human"] = human
            hs = human.get("status")
            if hs in ("refuted", "accepted-risk", "open"):
                rec["status"] = hs
            elif hs == "fixed":
                if max(rec.get("rounds") or [0]) > int(human.get("round") or 0) and rec["status"] == "open":
                    rec["auto_note"] = (f"REGRESSED: marked fixed in round {human.get('round')}, "
                                        f"reported again in round {max(rec['rounds'])}")
                else:
                    rec["status"] = "fixed"
    return store


def new_blocking(store: dict[str, dict], r: int) -> int:
    """Blocking findings a round INTRODUCED. A refuted one was never a defect; one
    fixed within the same round still means that round was not quiet."""
    return sum(1 for rec in store.values()
               if rec.get("first_round") == r and rec.get("severity") in BLOCKING
               and rec.get("status") != "refuted")


def resolve_refusal(rec: dict, status: str | None, note: str, literary: bool,
                    current_hash: str | None) -> str:
    """Why a human may NOT set `status` on this finding ('' when allowed). The
    same rules apply to `--resolve` and to a decision found in findings.jsonl
    (hand edits are re-validated on every run).

    Deterministic (MG-5, MG-7, MG-S, MG-T): never `fixed` or `refuted` by hand —
    they close when the sweep stops reporting them; `accepted-risk` only for a
    non-critical MG-5/MG-T or a minor MG-7; MG-S never. Configuration findings
    close by fixing the configuration. Agent findings: `fixed` needs a note and
    a changed text (live hash ≠ `recorded_hash`); `refuted` / `accepted-risk`
    need a MIN_NOTE-character note that is not a placeholder; no accepted-risk
    for a critical. Literary R1/R2 findings: nothing by hand.
    """
    if status in (None, "open"):
        return ""
    kind, check, sev = rec.get("kind"), rec.get("check"), rec.get("severity")
    real_note = not is_placeholder(note) and len(note.strip()) >= MIN_NOTE
    if kind == "config":
        return ("a configuration finding closes when the configuration is fixed "
                "(a complete waiver, a declared surface), not by --resolve")
    if status == "accepted-risk" and sev == "critical":
        return "a critical finding cannot be accepted as a risk — fix it"
    if kind == "tool":
        if status in ("fixed", "refuted"):
            return (f"{check} is deterministic: it closes when the next sweep stops reporting "
                    "it — fix the text and run the next round (never --status "
                    f"{status} by hand)")
        if check == "MG-S":
            return "MG-S (R1–R4) cannot be accepted as a risk — the rules are not waivable"
        if not (check in RISK_OK or (check == "MG-7" and sev == "minor")):
            return (f"{check} ({sev}) cannot be accepted as a risk — only a non-critical "
                    "MG-5/MG-T or a minor MG-7 can")
        if not real_note:
            return f"accepted-risk needs --note: {MIN_NOTE}+ characters of real reasoning"
        return ""
    # agent findings
    if literary and rec.get("rule") in STORY_RULES:
        return (f"a literary {rec['rule']} finding (an unresolved arc, an undelivered ending) "
                "closes only when a re-audit of CHANGED text no longer reports it — not by "
                "--resolve")
    if status == "fixed":
        if is_placeholder(note):
            return "--status fixed needs --note saying what changed and where"
        if not rec.get("recorded_hash") or current_hash is None:
            return ("no text hash was recorded with this finding — re-run the round "
                    "(--verdict-only) before resolving it")
        if current_hash == rec.get("recorded_hash"):
            return ("the text this finding points at has not changed since it was recorded — "
                    "edit it first (fixed is evidence, not a declaration)")
        return ""
    if not real_note:
        return (f"--status {status} needs --note with {MIN_NOTE}+ characters of real "
                "counter-evidence or reasoning (not a placeholder)")
    return ""


def do_resolve(run_dir: Path, args, literary: bool = False,
               hashes: TextHashes | None = None) -> int:
    store = load_store(run_dir)
    if not store:
        raise GateError(f"no findings.jsonl in {run_dir} — nothing to resolve")
    hits = [k for k in store if k == args.resolve] or [k for k in store if k.startswith(args.resolve)]
    if len(hits) != 1:
        raise GateError(f"--resolve {args.resolve!r} matches {len(hits)} finding(s) — "
                        f"give the full key from findings.jsonl")
    if args.status not in STATUSES:
        raise GateError(f"--status must be one of {', '.join(STATUSES)}")
    rec = store[hits[0]]
    hashes = hashes or TextHashes(None, None)
    why = resolve_refusal(rec, args.status, args.note or "", literary, hashes.live(rec))
    if why:
        raise GateError(f"{rec['key']} ({rec.get('check')} · {rec.get('severity')}): {why}")
    state = load_state(run_dir)
    rnd = args.round or max([int(r) for r in state["rounds"]] or [1])
    rec["human"] = {"status": args.status, "round": rnd, "note": args.note or ""}
    rec.setdefault("history", []).append({"round": rnd, "status": args.status,
                                          "note": args.note or "", "by": "human"})
    rec["status"] = args.status
    save_store(run_dir, store)
    print(f"[gate] {rec['key']} ({rec['check']} · {rec.get('severity')}) → {args.status}. "
          f"Re-run with --verdict-only to recompute the verdict.")
    return 0


# ---------------------------------------------------------------------------
# Coverage — the subjects manifest
# ---------------------------------------------------------------------------


def exercise_units(project: Project) -> dict[int, str]:
    """MG-3's subjects: {unit number: unit id}. `unit: 01` is read by YAML as 1,
    so everything matches on the NUMBER, never the string."""
    stems = {unit_number(p.stem): p.stem for p in project.unit_paths}
    outline = project.load_yaml("outline/units.yaml")
    nums = [unit_number(u.get("id") or u.get("unit") or u.get("slug"))
            for u in as_list(outline.get("units")) if isinstance(u, dict) and u.get("exercises")]
    nums = [n for n in nums if n is not None]
    if not nums and str(project.get("structure.exercises", "none")) not in ("none", "", "None"):
        nums = [n for n in stems if n is not None]
    return {n: stems.get(n, f"unit-{n:02d}") for n in sorted(set(nums))}


def round_subjects(project: Project, run_dir: Path, state: dict, check: str, r: int,
                   exercise_ids: dict[int, str]) -> dict | None:
    """{subject_id: {hash, sampled, ...}} for a check as of round r, None if unknown."""
    if check in ("MG-1", "MG-2"):
        rec = read_json(coverage_path(run_dir / f"round-{r}", check))
        if rec is None:
            return None
        if rec.get("blocked"):
            return {"blocked": {"hash": "", "sampled": False, "blocked": rec["blocked"]}}
        return {s["id"]: s for s in rec.get("eligible") or []}
    mh = (state["rounds"].get(str(r)) or {}).get("manuscript_hash")
    if not mh:
        return None
    ids = (list(exercise_ids.values()) if check == "MG-3"
           else ["continuity", "developmental"] if check == "MG-C" else ["manuscript"])
    return {i: {"id": i, "hash": mh, "sampled": False} for i in ids}


def compute_coverage(project: Project, run_dir: Path, state: dict, docs: list[dict],
                     round_no: int, checks: list[str], cfg: dict, blocked: dict[str, str],
                     exercise_ids: dict[int, str]) -> dict[str, dict]:
    """Per agent check: every eligible subject's state, from the evidence on disk."""
    out: dict[str, dict] = {}
    for check in checks:
        if check not in AGENT_CHECKS:
            if check in blocked:
                out[check] = {"entries": {"blocked": {"state": "pending", "reason": "blocked",
                                                      "detail": blocked[check]}}}
            continue
        if check == "MG-3" and not exercise_ids:
            out[check] = {"na": "this project has no exercises", "entries": {}}
            continue
        current = round_subjects(project, run_dir, state, check, round_no, exercise_ids)
        if current is None:
            out[check] = {"entries": {"blocked": {
                "state": "pending", "reason": "blocked",
                "detail": f"no coverage record for round {round_no} — run the round without "
                          f"--verdict-only"}}}
            continue
        if "blocked" in current:
            out[check] = {"entries": {"blocked": {"state": "pending", "reason": "blocked",
                                                  "detail": current["blocked"]["blocked"]}}}
            continue
        required = (int(cfg["passes_per_subject"]) if check in ("MG-1", "MG-2")
                    else max(2, int(cfg["passes_per_subject"]))
                    if project.literary and check in ("MG-4", "MG-C") else 1)
        by_round: dict[int, dict] = {}
        ev: dict[str, list[dict]] = {}
        for d in docs:
            if d.get("check") == check:
                ev.setdefault(subject_of(d, exercise_ids), []).append(d)
        entries: dict[str, dict] = {}
        for sid, subj in sorted(current.items()):
            files = ev.get(sid, [])
            if not files:
                entries[sid] = {"state": "pending", "reason": "never-audited", "hash": subj["hash"]}
                continue
            ra = max(d["_round"] for d in files)
            if ra not in by_round:
                by_round[ra] = round_subjects(project, run_dir, state, check, ra, exercise_ids) or {}
            h_a = (by_round[ra].get(sid) or {}).get("hash")
            if not h_a:
                entries[sid] = {"state": "pending", "reason": "audited-text-unknown",
                                "hash": subj["hash"], "round": ra}
                continue
            same = []
            for d in files:
                if d["_round"] not in by_round:
                    by_round[d["_round"]] = round_subjects(project, run_dir, state, check,
                                                           d["_round"], exercise_ids) or {}
                if (by_round[d["_round"]].get(sid) or {}).get("hash") == h_a:
                    same.append(d)
            passes = sorted({d["_pass"] for d in same})
            sampled = any(d.get("sampled") for d in same) or bool(
                (by_round[ra].get(sid) or {}).get("sampled"))
            entry = {"hash": subj["hash"], "round": ra, "passes": passes,
                     "state": f"{'sampled' if sampled else 'audited'}@{h_a}"}
            if h_a != subj["hash"]:
                entry.update(state="pending", reason="edited-since-audit")
            elif len(passes) < required:
                entry.update(state="pending", reason=f"passes {len(passes)}/{required}")
            entries[sid] = entry
        out[check] = {"entries": entries}
    return out


def coverage_summary(cov: dict[str, dict]) -> dict:
    pending = {c: sorted(i for i, e in v["entries"].items() if e["state"] == "pending")
               for c, v in cov.items()}
    sampled = {c: sorted(i for i, e in v["entries"].items() if e["state"].startswith("sampled@"))
               for c, v in cov.items()}
    lines = sorted([f"pending:{c}:{i}" for c, ids in pending.items() for i in ids]
                   + [f"sampled:{c}:{i}" for c, ids in sampled.items() for i in ids])
    sig = ("cov:" + hashlib.sha1("\n".join(lines).encode("utf-8")).hexdigest()[:12]) if lines else ""
    return {"pending": pending, "sampled": sampled, "signature": sig,
            "complete": not lines}


def coverage_label(check: str, v: dict) -> str:
    if v.get("na"):
        return f"{check} n/a ({v['na']})"
    e = v["entries"]
    if "blocked" in e:
        return f"{check} BLOCKED — {e['blocked']['detail']}"
    done = sum(1 for x in e.values() if x["state"].startswith(("audited@", "sampled@")))
    reasons: dict[str, int] = {}
    for x in e.values():
        if x["state"] == "pending":
            reasons[x["reason"]] = reasons.get(x["reason"], 0) + 1
    samp = sum(1 for x in e.values() if x["state"].startswith("sampled@"))
    tail = ", ".join(f"{n} {r}" for r, n in sorted(reasons.items()))
    return (f"{check} {done}/{len(e)} audited" + (f" ({samp} sampled)" if samp else "")
            + (f" — pending: {tail}" if tail else ""))


# ---------------------------------------------------------------------------
# Outputs: GROUNDING.md, PLAN.md, REPORT.md
# ---------------------------------------------------------------------------


def _doc_section(text: str, heading: str) -> str:
    m = re.search(rf"^## {re.escape(heading)}\b.*?(?=^## |\Z)", text, re.M | re.S)
    return m.group(0).strip() if m else ""


def write_grounding(project: Project, run_dir: Path, store: dict[str, dict]) -> None:
    """GROUNDING.md — what every auditor reads first. Regenerated every run."""
    spec = HERE.parent / "references" / "manuscript-gate.md"
    spec_text = read_text(spec) if spec.exists() else ""
    L = [f"# GROUNDING — {project.root.name} · manuscript gate", "",
         "<!-- generated by scripts/manuscript_gate.py on every run; do not edit -->", "",
         "Read this completely before auditing. It overrides your judgement and your memory.", "",
         f"- Profile: `{project.profile or 'unknown'}` · language: `{project.language_variant}`"]
    sources = sorted((project.root / "bible" / "sources").glob("**/*.md"))
    if sources:
        L.append(f"- Authority: `bible/sources/` ({len(sources)} file(s)). When the book and a "
                 f"source disagree the source wins — unless it is version drift, reported as "
                 f"drift. Cite path:line and a verbatim quote.")
    else:
        L.append("- Authority: no `bible/sources/`. Do not adjudicate against memory; what "
                 "you cannot settle goes to `deferred`.")
    L += ["- Voice is not a defect: the project's signed register (bible/voice-profile.md) — "
          "rhetorical absolutes, second person, humor, short sentences — is out of scope. An "
          "absolute about how the system (or the story world) behaves is a claim.", ""]
    for heading in ("The finding taxonomy", "False-positive suppressors"):
        sec = _doc_section(spec_text, heading)
        L += [sec if sec else f"## {heading}\n\nSee references/manuscript-gate.md § {heading}.", ""]
    accepted = [r for r in store.values() if r.get("status") in ("refuted", "accepted-risk")]
    L += ["## Accepted items — do not re-report", ""]
    L += ([f"- `{r['key']}` {r['check']} {r.get('relation')} at `{r.get('location')}` — "
           f"{r['status']}: {(r.get('human') or {}).get('note') or r.get('auto_note', '')}"
           for r in sorted(accepted, key=lambda r: r["key"])] or ["_None yet._"])
    L.append("")
    dnt = project.root / "bible" / "do-not-touch.md"
    L += ["## DO-NOT-TOUCH anchors", ""]
    if dnt.exists():
        anchors = _doc_section(read_text(dnt), "Anchors")
        L += [anchors or read_text(dnt).strip(), ""]
    idx = project.load_yaml("bible/claim-index.yaml")
    guarded = [(cid, c) for cid, c in (idx.get("concepts") or {}).items()
               if isinstance(c, dict) and (c.get("do_not_touch") or c.get("verified_against"))]
    L += [f"- concept `{cid}`: " + ("DO-NOT-TOUCH. " if c.get("do_not_touch") else "")
          + (f"verified against {c['verified_against']}. " if c.get("verified_against") else "")
          + str(c.get("note") or "").strip() for cid, c in guarded]
    if not dnt.exists() and not guarded:
        L.append("_None recorded._")
    (run_dir / "GROUNDING.md").write_text("\n".join(L).rstrip() + "\n", encoding="utf-8")


def append_verification_plan(project: Project, docs: list[dict], round_no: int) -> int:
    """Checkable `deferred` items → reviews/verification-plan/PLAN.md, APPEND-ONLY.

    The plan is where results are written by hand; regenerating it deleted them.
    New questions are inserted before "What was left out"; nothing existing moves.
    """
    items: list[dict] = []
    for d in docs:
        for q in d.get("deferred") or []:
            if q.get("needs") in CHECKABLE_NEEDS:
                items.append({**q, "_check": d.get("check"), "_subject": d.get("subject")})
    if not items:
        return 0
    path = project.reviews / "verification-plan" / "PLAN.md"
    text = read_text(path) if path.exists() else ""
    known = {norm(m.group(2)) for m in re.finditer(r"^### V-(\d+) — (.+)$", text, re.M)}
    n = max([int(m) for m in re.findall(r"^### V-(\d+)", text, re.M)] or [0])
    new, seen = [], set()
    for q in items:
        k = norm(str(q.get("question", "")))
        if k and k not in known and k not in seen:
            seen.add(k)
            new.append(q)
    if not new:
        return 0
    L = [f"## Added by the gate, round {round_no}", ""]
    for q in sorted(new, key=lambda q: (q["needs"], str(q.get("question")))):
        n += 1
        L += [f"### V-{n:02d} — {q.get('question')}", "",
              f"- **Needs:** {q['needs']} · **From:** {q['_check']} · {q['_subject']}",
              f"- **Claim:** {', '.join(as_list(q.get('sites'))) or '—'}",
              f"- **Why unresolved:** {q.get('why_unresolved', '—')}",
              f"- **How to check:** {q.get('how_to_check') or '**TODO** — an entry nobody can execute is not run'}",
              f"- **What the book expects:** {q.get('expected') or '**TODO**'}",
              f"- **Suspect a defect if:** {q.get('defect_if') or '**TODO** — write it BEFORE checking'}",
              "", "**Actual result:**", "", "", "---", ""]
    block = "\n".join(L)
    if not text:
        text = ("# Verification plan\n\nGenerated from the gate's `deferred` items and then "
                "maintained BY HAND: the gate only ever appends. Fill `**Actual result:**` "
                "with literal values, or `NOT RUN` and why. See "
                "references/verification-plan.md and templates/verification-plan.md.\n\n"
                "---\n\n" + block + "\n## What was left out, and why\n\n"
                "| Area | Why unchecked | What would change that |\n|---|---|---|\n")
    else:
        marker = re.search(r"^## What was left out", text, re.M)
        text = (text[:marker.start()] + block + "\n" + text[marker.start():]
                if marker else text.rstrip() + "\n\n" + block)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return len(new)


BEGIN = "<!-- BEGIN computed by scripts/manuscript_gate.py"
END = "<!-- END computed -->"


def write_report(project: Project, round_dir: Path, block: list[str]) -> Path:
    """round-N/REPORT.md: the computed block is replaced; everything else survives."""
    path = round_dir / "REPORT.md"
    computed = "\n".join(block + [END])
    if path.exists():
        text = read_text(path)
        s, e = text.find(BEGIN), text.find(END)
        text = (text[:s] + computed + text[e + len(END):]) if s != -1 and e != -1 \
            else computed + "\n\n" + text
    else:
        tpl = HERE.parent / "templates" / "manuscript-gate-report.md"
        body = read_text(tpl) if tpl.exists() else ""
        e = body.find(END)
        text = computed + ("\n" + body[e + len(END):] if e != -1 else "\n")
    path.write_text(text, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def parse_args(argv):
    ap = argparse.ArgumentParser(description="Phase 4.5 manuscript gate.")
    add_common_args(ap)
    ap.add_argument("--round", type=int, default=None,
                    help="Round number. Default: the latest recorded round, or 1.")
    ap.add_argument("--run-dir", default=None,
                    help="Run directory. Default: reviews/manuscript-gate-<--date>/, else "
                         "the latest existing run, else reviews/manuscript-gate-current/.")
    ap.add_argument("--date", default=None, help="Stamp for the run directory (YYYY-MM-DD).")
    ap.add_argument("--deterministic-only", action="store_true",
                    help="Deterministic checks only, into <run>/deterministic-only/. Touches "
                         "no round, no store. Exit 1 on an open critical/major.")
    ap.add_argument("--verdict-only", action="store_true",
                    help="Recompute from the findings on disk; sweep and prepare nothing.")
    ap.add_argument("--top-concepts", type=int, default=None)
    ap.add_argument("--top-rules", type=int, default=None)
    ap.add_argument("--resolve", metavar="KEY", default=None,
                    help="Set a finding's status in findings.jsonl (with --status, --note).")
    ap.add_argument("--status", choices=STATUSES, default=None)
    ap.add_argument("--note", default="")
    return ap.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        return _main(args)
    except GateError as exc:
        print(f"[gate] ERROR {exc}")
        return 2


def store_truncation(run_dir: Path, state: dict, store: dict[str, dict]) -> str:
    """'' unless findings.jsonl lost keys an earlier round recorded in
    state.json. The store only ever grows (a closed finding stays, with its
    status): a missing key means the file was truncated, replaced or deleted."""
    recorded: set[str] = set()
    for r in (state.get("rounds") or {}).values():
        recorded |= set(r.get("store_keys") or [])
    missing = sorted(recorded - set(store))
    if not missing:
        return ""
    return (f"findings store truncated: {len(missing)} finding(s) recorded in state.json are "
            f"missing from {run_dir.name}/findings.jsonl ({', '.join(missing[:5])}"
            f"{'…' if len(missing) > 5 else ''}) — restore findings.jsonl (version control), or "
            "start a new run directory (--date); the gate does not forget findings")


def _main(args) -> int:
    project = load_project(args.root, args.units)
    for problem in (LX.schema_problem(project.meta), LX.profile_problem(project.meta)):
        if problem:
            raise GateError(problem)
    cfg = gate_config(project)
    for k, v in (("top_concepts", args.top_concepts), ("top_rules", args.top_rules)):
        if v is not None:
            cfg[k] = v
    run_dir = resolve_run_dir(project, args)
    if args.resolve:
        if not args.status:
            raise GateError("--resolve needs --status")
        state0 = load_state(run_dir)
        why = store_truncation(run_dir, state0, load_store(run_dir))
        if why:
            raise GateError(why)
        return do_resolve(run_dir, args, project.literary, TextHashes(project, state0))

    unit_args = ["--root", str(project.root)]
    for u in args.units or []:
        unit_args += ["--units", u]
    checks = applicable_checks(project)
    errors: list[str] = []
    notes: list[str] = list(cfg["_notes"])
    live, waived, cfg_notes = config_records(project, cfg, checks)
    notes += cfg_notes
    active = [c for c in checks if cfg["checks"].get(c) is not False
              or (project.literary and c in LITERARY_ALWAYS_ON)]

    if args.deterministic_only:
        out = sweep(project, run_dir / "deterministic-only", unit_args, active, errors)
        recs = det_records(out) + live
        crit = sum(1 for r in recs if r["severity"] == "critical")
        major = sum(1 for r in recs if r["severity"] == "major")
        print(f"[gate] deterministic-only · {project.root.name} · {run_dir / 'deterministic-only'}")
        _print_sweep(out, recs)
        for b, why in out["blocked"].items():
            print(f"[gate] {b} BLOCKED — {why}")
        # Config-derived findings (an executable surface with no runner, a check
        # disabled without a waiver) have no report file of their own. Counting
        # them without naming them sends the reader hunting through JSON files
        # that do not contain them.
        for r in live:
            print(f"[gate] {r['check']} {r['severity']}: {r.get('detail') or r.get('subject')}")
        for n in notes:
            print(f"[gate] note: {n}")
        for e in errors:
            print(f"[gate] ERROR {e}")
        print(f"[gate] deterministic: {crit} critical · {major} major open")
        return 2 if errors else (1 if crit or major else 0)

    state = load_state(run_dir)
    state.update({"schema_version": "2.0", "profile": project.profile,
                  "run_dir": project.rel(run_dir)})
    rounds = [int(r) for r in state["rounds"]]
    round_no = args.round or (max(rounds) if rounds else 1)
    round_dir = run_dir / f"round-{round_no}"
    rkey = str(round_no)
    exercise_ids = {} if project.literary else exercise_units(project)
    live_hash = manuscript_hash(project)
    print(f"[gate] {project.root.name} · {project.profile or 'no profile'} · "
          f"round {round_no}/{cfg['max_rounds']} · {project.rel(run_dir)}")
    if project.literary:
        print("[gate] literary profile: MG-1, MG-2, MG-3, MG-6 are n/a (profile); "
              "MG-S, MG-T, MG-C apply — references/manuscript-gate-literary.md")

    todo: list[str] = []
    if not args.verdict_only and round_no > int(cfg["max_rounds"]):
        raise GateError(f"round {round_no} is beyond max_rounds {cfg['max_rounds']}: the gate "
                        "does not relax. Produce the escalation packet "
                        "(references/loopback-handoff.md), set `phase: "
                        "blocked-on-manuscript-gate`, and let the human decide.")
    if not args.verdict_only:
        if list((round_dir / "findings").glob("*.json")):
            raise GateError(f"round {round_no} already has findings files — re-preparing it "
                            f"would re-hash its subjects under them. Run --round {round_no} "
                            f"--verdict-only, or start --round {round_no + 1}.")
        out = sweep(project, round_dir, unit_args, active, errors)
        write_json(round_dir / "deterministic.json",
                   {"records": det_records(out), "blocked": out["blocked"],
                    "manuscript_hash": live_hash})
        state["rounds"][rkey] = {**state["rounds"].get(rkey, {}), "swept": True,
                                 "manuscript_hash": live_hash,
                                 "unit_hashes": {project.rel(p): text_hash(read_text(p))
                                                 for p in project.unit_paths}}
        _print_sweep(out, det_records(out))
        if not project.literary:
            docs0, _ = read_finding_docs(run_dir, round_no)
            pre = compute_coverage(project, run_dir, state, docs0, max(round_no - 1, 1),
                                   [c for c in active if c in ("MG-1", "MG-2")], cfg, {},
                                   exercise_ids) if round_no > 1 else {}
            save_manifest(run_dir / "subjects.json",
                          {c: v["entries"] for c, v in pre.items() if "blocked" not in v["entries"]})
            prepare(project, round_dir, run_dir, unit_args, cfg, round_no, active, errors)
    else:
        det = read_json(round_dir / "deterministic.json")
        if det is None or not (state["rounds"].get(rkey) or {}).get("swept"):
            errors.append(f"round {round_no} was never swept — run it without --verdict-only first")

    docs, doc_errors = read_finding_docs(run_dir, round_no)
    errors += doc_errors
    det_by_round: dict[int, list[dict]] = {}
    blocked: dict[str, str] = {}
    for r in swept_rounds(state, round_no):
        d = read_json(run_dir / f"round-{r}" / "deterministic.json")
        if d is None:
            errors.append(f"round-{r}/deterministic.json is missing — re-run round {r}")
            continue
        det_by_round[r] = d.get("records") or []
        if r == round_no:
            blocked = d.get("blocked") or {}
    agent, positives = agent_records(docs, exercise_ids)
    prev_store = load_store(run_dir)
    truncated = store_truncation(run_dir, state, prev_store)
    if truncated:
        errors.append(truncated)
    store = build_store(prev_store, agent, docs, det_by_round, live, round_no,
                        exercise_ids, project.literary, TextHashes(project, state))
    for r in store.values():
        if r.get("human_ignored"):
            notes.append(f"{r['key']}: human decision {r['human_ignored']}")

    cov = compute_coverage(project, run_dir, state, docs, round_no,
                           [c for c in active if c not in waived], cfg, blocked, exercise_ids)
    for c in ("MG-1", "MG-2"):
        rec = read_json(coverage_path(round_dir, c)) or {}
        notes += [f"{c}: {n}" for n in rec.get("notes") or []]
        if rec and rec.get("mode") not in (None, "", "lexicon"):
            notes.append(f"{c}: no language pack for `{rec.get('language')}` — ran in "
                         f"`{rec.get('mode')}` mode; add scripts/lexicons/{rec.get('language')}.yaml")
    save_manifest(run_dir / "subjects.json", {c: v["entries"] for c, v in cov.items()})
    cs = coverage_summary(cov)
    ladder = {"MG-1": "raise `home_cap` on its probe in bible/concept-probes-tuned.yaml",
              "MG-2": "narrow it in bible/rule-probes-tuned.yaml (worklist: "
                      "round-N/rule-probes-proposed.yaml)"}
    for c, ids in cs["sampled"].items():
        if ids and c in ladder:
            notes.append(f"{c}: {len(ids)} subject(s) judged from a SAMPLE — {ladder[c]}, or, "
                         f"if it really is that wide, accept it under the coverage waiver.")

    story_now = ""
    if project.literary and not errors:
        story_now = live_story_check(project, run_dir, errors)
    open_ = [r for r in store.values() if r.get("status") == "open"]
    n_crit = sum(1 for r in open_ if r.get("severity") == "critical")
    n_major = sum(1 for r in open_ if r.get("severity") == "major")
    n_minor = sum(1 for r in open_ if r.get("severity") == "minor")
    verdict = ("ERROR" if errors else "BLOCKED" if n_crit else "NEEDS-REVISION" if n_major
               else "PASS-PARTIAL" if not cs["complete"] else "PASS")
    ws = waivers(project)
    cov_waivers = [w for w in ws if w.get("check") == COVERAGE_WAIVER and not waiver_problem(w)]
    waiver_ok = bool(cs["signature"]) and any(
        str(w.get("signature", "")) == cs["signature"] for w in cov_waivers)
    if cov_waivers and cs["signature"] and not waiver_ok:
        notes.append(f"A `{COVERAGE_WAIVER}` waiver exists but no signature matches "
                     f"`{cs['signature']}` — it was written for different pending/sampled "
                     f"sets. Re-read them and update it, or drop it.")
    # Literary: the whole-book read (MG-4) and the continuity/developmental audit
    # (MG-C) are how R2 is checked on the page — no coverage waiver covers them.
    unwaivable = sorted(f"{c}:{i}" for c in ("MG-4", "MG-C") if project.literary
                        for i in cs["pending"].get(c, []) + cs["sampled"].get(c, []))
    if unwaivable and waiver_ok:
        waiver_ok = False
        notes.append(f"the `{COVERAGE_WAIVER}` waiver does not cover {', '.join(unwaivable)}: in "
                     "book-literary MG-4 and MG-C are read in full (two passes on the current "
                     "manuscript) — they are part of R2")

    swept = swept_rounds(state, round_no)
    nb = {r: new_blocking(store, r) for r in swept}
    need = int(cfg["rounds_without_new_to_close"])
    quiet = swept[-need:] if len(swept) >= need else []
    stale = live_hash != (state["rounds"].get(rkey) or {}).get("manuscript_hash")
    if stale:
        notes.append("final/ changed since this round's sweep: the deterministic results and "
                     "the whole-book hashes describe older text. Start the next round.")
    reason = ("ERROR" if errors else f"verdict {verdict}" if verdict in ("BLOCKED", "NEEDS-REVISION")
              else f"PASS-PARTIAL: book-literary needs MG-4 and MG-C fully audited (pending "
                   f"{', '.join(unwaivable)}) — no waiver covers them"
              if verdict == "PASS-PARTIAL" and unwaivable
              else f"PASS-PARTIAL needs a `{COVERAGE_WAIVER}` waiver signed `{cs['signature']}`"
              if verdict == "PASS-PARTIAL" and not waiver_ok
              else "final/ changed since the sweep" if stale
              else story_now if story_now
              else f"need {need} consecutive swept rounds with no new blocking finding "
                   f"(have {len(swept)} swept; new blocking by round: "
                   f"{', '.join(f'r{r}={nb[r]}' for r in swept) or '—'})"
              if not quiet or any(nb[r] for r in quiet) else "")
    converged = not reason

    recorded_keys: set[str] = set()
    for r in state["rounds"].values():
        recorded_keys |= set(r.get("store_keys") or [])
    state["rounds"][rkey] = {**state["rounds"].get(rkey, {}), "verdict": verdict,
                             "open": {"critical": n_crit, "major": n_major, "minor": n_minor},
                             "new_blocking": nb.get(round_no, 0), "signature": cs["signature"],
                             "coverage": {c: coverage_label(c, v) for c, v in cov.items()},
                             "errors": errors, "converged": converged,
                             "store_keys": sorted(set(store) | recorded_keys),
                             "store_count": len(store)}
    for r in swept:
        state["rounds"][str(r)]["new_blocking"] = nb[r]
    state["latest"] = {"round": round_no, "verdict": verdict, "converged": converged,
                       "open_critical": n_crit, "open_major": n_major,
                       "coverage_signature": cs["signature"]}
    run_dir.mkdir(parents=True, exist_ok=True)
    write_json(run_dir / "state.json", state)
    if not truncated:                    # never overwrite the evidence of a truncated store
        save_store(run_dir, store)
    write_grounding(project, run_dir, store)
    n_plan = append_verification_plan(project, docs, round_no)
    if n_plan:
        notes.append(f"{n_plan} new checkable question(s) appended to "
                     f"reviews/verification-plan/PLAN.md (existing entries untouched).")
    todo = dispatch_list(project, round_dir, cov, cfg)

    omissions = sum(1 for r in store.values() if r.get("relation") == "D9")
    contradictions = sum(1 for r in store.values() if r.get("relation") in ("D1", "D6"))
    if contradictions and not omissions and not project.literary:
        notes.append(f"Zero omission findings (D9) alongside {contradictions} contradiction(s). "
                     f"Reviewers are structurally blind to omitted preconditions — a clean "
                     f"sweep here is more likely a lens that skipped the class.")
    single = [r for r in open_ if r.get("kind") == "agent" and len(r.get("passes") or []) == 1
              and r.get("check") in ("MG-1", "MG-2") and int(cfg["passes_per_subject"]) > 1]
    if single:
        notes.append(f"{len(single)} open finding(s) came from only ONE pass — the cheapest "
                     f"false-positive signal; verify these first.")

    block = report_block(project, round_no, cfg, verdict, converged, reason, store, cov, cs,
                         waiver_ok, state, swept, nb, positives, todo, errors, notes)
    round_dir.mkdir(parents=True, exist_ok=True)
    report = write_report(project, round_dir, block)

    print(f"[gate] findings: {n_crit} critical · {n_major} major · {n_minor} minor open "
          f"({len(store)} in {project.rel(run_dir / 'findings.jsonl')}, "
          f"{sum(positives.values())} verified-correct)")
    for c, v in cov.items():
        print(f"[gate] coverage: {coverage_label(c, v)}")
    if cs["signature"]:
        print(f"[gate] coverage signature: {cs['signature']}"
              + ("  (waiver valid)" if waiver_ok else ""))
    for n in notes:
        print(f"[gate] NOTE {n}")
    for e in errors:
        print(f"[gate] ERROR {e}")
    print(f"\n[gate] VERDICT: {verdict}")
    if converged:
        print(f"[gate] CONVERGED — {verdict}" + (" with a valid coverage waiver"
                                                 if verdict == "PASS-PARTIAL" else "")
              + f"; the last {need} swept rounds introduced no new blocking finding. "
                f"The book can reach `complete`.")
    else:
        print(f"[gate] NOT converged — {reason}.")
        if round_no >= int(cfg["max_rounds"]) and verdict != "ERROR":
            print("[gate] MAX ROUNDS REACHED. Do NOT relax the criterion: produce the "
                  "escalation packet (references/loopback-handoff.md) and set "
                  "`phase: blocked-on-manuscript-gate`.")
    print(f"[gate] report → {project.rel(report)}")
    if todo:
        print("\n[gate] dispatch these, then re-run with --verdict-only:")
        for t in todo:
            print(f"  - {t}")
    return 2 if errors else (0 if converged else 1)


def live_story_check(project: Project, run_dir: Path, errors: list[str]) -> str:
    """Converged implies `check_story.py --manuscript` exits 0 NOW (the bible can
    change after a sweep). '' when it passes; the reason when it does not."""
    if not (HERE / "check_story.py").exists():
        errors.append("MG-S: scripts/check_story.py is not installed")
        return ""
    out = run_dir / "story-live.json"
    out.unlink(missing_ok=True)
    code, log = run_tool("check_story.py", ["--root", str(project.root), "--manuscript",
                                            "--json", str(out)])
    data = read_json(out)
    if code not in (0, 1) or data is None:
        errors.append(f"MG-S: check_story.py --manuscript exited {code}"
                      + (" and wrote no valid JSON" if data is None else "") + f" — {_tail(log)}")
        return ""
    if code == 1:
        bad = [f"{f.get('code')} {f.get('subject')}" for f in data.get("findings") or []
               if f.get("severity") in ("blocking", "major")]
        return ("`check_story.py --manuscript` exits 1 now (R1–R4: "
                + ", ".join(bad[:5]) + ("…" if len(bad) > 5 else "") + ")")
    return ""


def prepare(project: Project, round_dir: Path, run_dir: Path, unit_args: list[str],
            cfg: dict, round_no: int, active: list[str], errors: list[str]) -> None:
    """Technical agent inputs: MG-1 dossiers and MG-2 rule files."""
    manifest = ["--subjects", str(run_dir / "subjects.json"), "--round", str(round_no)]
    if "MG-1" in active:
        probes = project.root / "bible" / "concept-probes.yaml"
        if not probes.exists():
            code, log = run_tool("bootstrap_probes.py", unit_args)
            print(f"[gate] bootstrap_probes: {(log.strip().splitlines() or ['(no output)'])[0]}")
        cov = coverage_path(round_dir, "MG-1")
        code, log = run_tool("build_concept_dossier.py", [
            *unit_args, "--all", "--out", str(round_dir / "dossiers"),
            "--min-units", str(cfg["concept_min_units"]), "--top", str(cfg["top_concepts"]),
            "--coverage", str(cov), *manifest])
        if code != 0 or read_json(cov) is None:
            errors.append(f"MG-1: build_concept_dossier.py exited {code} and/or wrote no "
                          f"coverage record — {_tail(log)}")
        for line in log.splitlines():
            if line.startswith("[dossier]") and ("MG-1" in line or "language pack" in line):
                print(f"[gate] {line}")
    if "MG-2" in active:
        cov = coverage_path(round_dir, "MG-2")
        code, log = run_tool("extract_rule_candidates.py", [
            *unit_args, "--out", str(round_dir / "rules"), "--top", str(cfg["top_rules"]),
            "--coverage", str(cov), "--propose-probes",
            str(round_dir / "rule-probes-proposed.yaml"), *manifest])
        if code != 0 or read_json(cov) is None:
            errors.append(f"MG-2: extract_rule_candidates.py exited {code} and/or wrote no "
                          f"coverage record — {_tail(log)}")
        for line in log.splitlines():
            if line.startswith("[rules]") and ("MG-2" in line or "language pack" in line
                                               or "SAMPLED" in line):
                print(f"[gate] {line}")


def dispatch_list(project: Project, round_dir: Path, cov: dict, cfg: dict) -> list[str]:
    """What is still pending AND has an input this round (emitted, or whole-book)."""
    rel = project.rel(round_dir)
    passes = int(cfg["passes_per_subject"])
    pend = {c: [i for i, e in v["entries"].items() if e["state"] == "pending" and i != "blocked"]
            for c, v in cov.items()}
    for c in ("MG-1", "MG-2"):
        emitted = set((read_json(coverage_path(round_dir, c)) or {}).get("emitted") or [])
        pend[c] = [i for i in pend.get(c, []) if i in emitted]
    out: list[str] = []
    if pend.get("MG-1"):
        out.append(f"MG-1: concept-auditor over {len(pend['MG-1'])} dossier(s) in {rel}/dossiers/ "
                   f"(lenses pairs, numbers-and-absolutes, source), {passes} passes each → "
                   f"findings/<concept>.<lens>.p<N>.json")
    if pend.get("MG-2"):
        out.append(f"MG-2: rule-auditor over {len(pend['MG-2'])} rule file(s) in {rel}/rules/, "
                   f"{passes} passes each → findings/<rule-id>.rule-vs-instance.p<N>.json")
    if pend.get("MG-3"):
        out.append(f"MG-3: rule-auditor, exercise-coverage mode, over {', '.join(pend['MG-3'])} "
                   f"→ findings/<unit>.exercise-coverage.p1.json")
    if pend.get("MG-4"):
        if project.literary:
            out.append("MG-4: reader-pov literary whole-book mode over manuscript.md, TWO "
                       "independent reads (fresh subagents) → findings/manuscript."
                       "whole-book-read.p1.json and .p2.json")
        else:
            out.append("MG-4: reader-pov whole-book mode over manuscript.md → "
                       "findings/manuscript.whole-book-read.p1.json")
    for lens in pend.get("MG-C", []):
        out.append(f"MG-C: {lens} audit (references/manuscript-gate-literary.md), two "
                   f"independent passes → findings/manuscript.{lens}.p1.json and .p2.json")
    if out:
        out.append("Every dispatched subject writes a findings file, INCLUDING clean ones: "
                   "a subject with no file was not audited. Auditors read GROUNDING.md first.")
    return out


def report_block(project, round_no, cfg, verdict, converged, reason, store, cov, cs,
                 waiver_ok, state, swept, nb, positives, todo, errors, notes) -> list[str]:
    open_ = sorted((r for r in store.values() if r.get("status") == "open"),
                   key=lambda r: (SEV_RANK.get(r.get("severity"), 9), r["check"], r["key"]))
    never = sum(1 for v in cov.values() for e in v["entries"].values()
                if e["state"] == "pending" and e.get("reason") in ("never-audited", "blocked"))
    partly = sum(1 for v in cov.values() for e in v["entries"].values()
                 if e["state"].startswith("sampled@")
                 or (e["state"] == "pending" and str(e.get("reason", "")).startswith("passes")))
    edited = sum(1 for v in cov.values() for e in v["entries"].values()
                 if e.get("reason") == "edited-since-audit")
    L = [f"{BEGIN} — round {round_no}. Regenerated on every run; write outside this block. -->",
         "", f"**Verdict:** {verdict} · **Round:** {round_no}/{cfg['max_rounds']} · "
             f"**Converged:** {'yes' if converged else 'no — ' + reason}",
         f"**Open findings:** "
         + " · ".join(f"{sum(1 for r in open_ if r.get('severity') == s)} {s}"
                      for s in ("critical", "major", "minor"))
         + " (`findings.jsonl`)",
         f"**Coverage:** never opened {never} · partly read {partly} · re-queued (edited) {edited}"
         + (f" · signature `{cs['signature']}`" + (" — waiver valid" if waiver_ok else "")
            if cs["signature"] else " · complete"), "", "## What ran", "",
         "| Check | Scope | Open (crit/major/minor) | Status |", "|---|---|---|---|"]
    for c in applicable_checks(project):
        o = [r for r in open_ if r["check"] == c]
        counts = "/".join(str(sum(1 for r in o if r.get("severity") == s))
                          for s in ("critical", "major", "minor"))
        if c in cov:
            scope, status = coverage_label(c, cov[c]), "measured"
        elif c in ("MG-5", "MG-7", "MG-S", "MG-T", "MG-6"):
            scope, status = "whole book, every round", "complete"
        else:
            scope, status = "switched off", "waived"
        L.append(f"| {c} | {scope} | {counts} | {status} |")
    if project.literary:
        L.append("| MG-1/2/3/6 | n/a (profile) | — | n/a |")
    L += ["", f"Verified correct (N1/N2/D7a): "
              + (", ".join(f"{c} {n}" for c, n in sorted(positives.items())) or "none"), ""]
    pend = [(c, i, e) for c, v in cov.items() for i, e in sorted(v["entries"].items())
            if e["state"] == "pending" or e["state"].startswith("sampled@")]
    if pend:
        L += ["## Not fully audited", "", "| Check | Subject | State | Why |", "|---|---|---|---|"]
        L += [f"| {c} | `{i}` | {e['state'].split('@')[0]} | {e.get('reason') or e.get('detail') or ''} |"
              for c, i, e in pend[:60]]
        if len(pend) > 60:
            L.append(f"| … | {len(pend) - 60} more in `subjects.json` | | |")
        L.append("")
    if open_:
        L += ["## Open findings", "", "| Key | Check | Relation | Severity | Location | Note |",
              "|---|---|---|---|---|---|"]
        L += [f"| `{r['key']}` | {r['check']} | {r.get('relation')} | {r.get('severity')} | "
              f"`{r.get('location', '')}` | {(r.get('auto_note') or r.get('detail') or '')[:90]} |"
              for r in open_[:80]]
        L.append("")
    if todo:
        L += ["## Dispatch this round", ""] + [f"- {t}" for t in todo] + [""]
    if errors or notes:
        L += ["## Errors and notes", ""] + [f"- **ERROR** {e}" for e in errors] + \
             [f"- {n}" for n in notes] + [""]
    L += ["## Round history", "", "| Round | New blocking | Open crit/major | Verdict |",
          "|---:|---:|---|---|"]
    for r in swept:
        v = state["rounds"].get(str(r)) or {}
        o = v.get("open") or {}
        L.append(f"| {r} | {nb.get(r, 0)} | {o.get('critical', '—')}/{o.get('major', '—')} | "
                 f"{v.get('verdict', '—')} |")
    L.append("")
    return L


def _print_sweep(out: dict, recs: list[dict]) -> None:
    by = {}
    for r in recs:
        by.setdefault(r["check"], {}).setdefault(r["severity"], 0)
        by[r["check"]][r["severity"]] += 1
    for c in ("MG-5", "MG-7", "MG-S", "MG-T"):
        if c in (out.get("tools") or {}):
            s = by.get(c, {})
            print(f"[gate] {c}: {s.get('critical', 0)} critical · {s.get('major', 0)} major · "
                  f"{s.get('minor', 0)} minor"
                  + ("" if out["tools"][c] is not None else "  (TOOL FAILED)"))
    ci = out.get("claim_index")
    if ci is not None:
        counts = ci.get("counts") or {}
        print("[gate] claim index: " + ("not built yet" if ci.get("absent") else
                                        "  ".join(f"{k}={v}" for k, v in sorted(counts.items())))
              + f" · PROPAGATE={len(ci.get('propagate') or [])}")
    anc = (out.get("anchors") or {}).get("counts") or {}
    if anc:
        print("[gate] anchors: " + "  ".join(f"{k}={v}" for k, v in sorted(anc.items()))
              + ("  — run `resolve_anchors.py --heal` to repair DRIFT" if anc.get("DRIFT") else ""))


if __name__ == "__main__":
    sys.exit(main())
