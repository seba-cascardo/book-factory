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

from bookkit.coverage import coverage_path, load_ledger, save_ledger  # noqa: E402
from bookkit.project import Project, add_common_args, load_project  # noqa: E402

# D9 (omitted precondition) belongs here. Leaving it out would silently drop the
# one defect class reviewers are already blind to — the failure would compound
# rather than cancel.
DEFECT_RELATIONS = {"D1", "D2", "D3", "D4", "D4a", "D5", "D6", "D7", "D8", "D9"}
POSITIVE_RELATIONS = {"N1", "N2", "D7a"}
BLOCKING = ("critical", "major")

# The checks whose coverage can be partial. MG-5 and MG-6 are deterministic and
# always run over the whole book, so they have no coverage term.
SEMANTIC_CHECKS = ("MG-1", "MG-2", "MG-3", "MG-4")

# Coverage has two axes and they close by different work, so they waive
# separately. BREADTH — subjects nobody opened — closes by spending rounds; the
# emitters drain the pool automatically. DEPTH — subjects read only in part —
# closes by narrowing them in `bible/rule-probes-tuned.yaml` or raising a
# concept's `home_cap`, which is judgement about scope and cannot be automated.
#
# Collapsing them into one criterion made `PASS` unreachable by construction:
# measured on the reference book, 221 of 454 rules were over the tractability
# ceiling, so `sampled == 0` could never hold however many rounds anyone ran, and
# every project would have ended at a standing waiver. That is the same decay
# this design rejects for percentage floors.
#
# Both waivers carry a signature of the exact numbers, so one written against
# 40/169 does not silently keep covering 12/169 three rounds later.
COVERAGE_WAIVER = "manuscript_gate.coverage"   # breadth
DEPTH_WAIVER = "manuscript_gate.depth"         # depth

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
    coverage: dict = field(default_factory=dict)
    breadth_complete: bool = False
    depth_complete: bool = False
    breadth_signature: str = ""
    depth_signature: str = ""
    coverage_waived: bool = False
    depth_waived: bool = False
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

    # Anchors. Reported every round because references rot between rounds, not
    # during them — an inserted section shifts every line-keyed reference in the
    # book at once, and two of three observed breakages were exactly that.
    anchors_json = round_dir / "anchors.json"
    code, log = run_script("resolve_anchors.py", [
        *unit_args, "--json", str(anchors_json), "--quiet"])
    out["anchors"] = _read_json(anchors_json)
    if log.strip():
        print(log.strip())

    fd_json = round_dir / "fixed-defects.json"
    code, log = run_script("check_fixed_defects.py", [
        *unit_args, "--json", str(fd_json), "--quiet"])
    out["fixed_defects"] = _read_json(fd_json)
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
                   cfg: dict, propagation: list[str] | None,
                   round_no: int, ledger_path: Path) -> list[str]:
    """Build dossiers and rule candidates; return the dispatch checklist.

    Both emitters get `--audited`, so from round 2 they select the next slice of
    the pool instead of re-emitting round 1's. Without that, rounds 2+ audit
    nothing new, no new findings can appear, and "two consecutive quiet rounds"
    is satisfied by construction rather than by evidence.
    """
    todo: list[str] = []
    ledger_args = ["--audited", str(ledger_path), "--round", str(round_no)]

    probes = project.root / "bible" / "concept-probes.yaml"
    if not probes.exists():
        code, log = run_script("bootstrap_probes.py", unit_args)
        print(log.strip())

    dossiers = round_dir / "dossiers"
    if probes.exists():
        code, log = run_script("build_concept_dossier.py", [
            *unit_args, "--all", "--out", str(dossiers),
            "--min-units", str(cfg["concept_min_units"]),
            "--top", str(cfg["top_concepts"]),
            "--coverage", str(coverage_path(round_dir, "MG-1")), *ledger_args])
        for line in log.strip().splitlines():
            if line.startswith("[dossier]") and (
                    "skipped" in line or "NOT emitted" in line or "index" in line
                    or "coverage" in line or "ledger" in line):
                print(line)
        n = len(list(dossiers.glob("*.md"))) - 1 if dossiers.exists() else 0
        todo.append(f"MG-1: dispatch concept-auditor over {max(n, 0)} dossier(s) in "
                    f"{dossiers} — lenses `pairs`, `numbers-and-absolutes`, `source`. "
                    f"Read {dossiers / '_index.md'} first and start with the D2 rows.")
    else:
        # A skipped check has to leave a record. Without one the verdict sees
        # "unknown" and reports it as subjects nobody opened, which sends the
        # reader looking for auditors to dispatch when the real problem is a
        # missing input file. Silence reading as something else is the whole
        # defect class this gate exists for; it applies to the gate itself.
        coverage_path(round_dir, "MG-1").write_text(json.dumps({
            "check": "MG-1", "round": round_no, "eligible_candidates": 0,
            "selected": 0, "emitted": 0, "sampled_within": 0,
            "already_audited": [], "requeued": [], "strata": {}, "subjects": [],
            "cut": [],
            "blocked": "no bible/concept-probes.yaml and bootstrap_probes.py "
                       "produced none — MG-1 cannot run",
        }, indent=2), encoding="utf-8")
        todo.append("MG-1: SKIPPED — no bible/concept-probes.yaml and bootstrap "
                    "failed. Run scripts/bootstrap_probes.py by hand, or write "
                    "bible/concept-probes-tuned.yaml. Until then MG-1 has no "
                    "coverage and the gate cannot reach PASS.")

    rules = round_dir / "rules"
    proposed = round_dir / "rule-probes-proposed.yaml"
    code, log = run_script("extract_rule_candidates.py", [
        *unit_args, "--out", str(rules), "--top", str(cfg["top_rules"]),
        "--coverage", str(coverage_path(round_dir, "MG-2")),
        "--propose-probes", str(proposed), *ledger_args])
    for line in log.strip().splitlines():
        if line.startswith("[rules]"):
            print(line)
    todo.append(f"MG-2: dispatch rule-auditor over the rule files in {rules} "
                f"(read {rules / '_index.md'} first)")
    if proposed.exists() and "can only be SAMPLED" in log:
        todo.append(f"MG-2 depth: {proposed} lists the rules that can only be SAMPLED, "
                    f"ranked. Narrowing them in bible/rule-probes-tuned.yaml is the "
                    f"only way `PASS` is reachable — otherwise the gate stays at "
                    f"`PASS-SAMPLED` and the depth waiver becomes permanent. This is "
                    f"human work: narrowing is a claim about a rule's scope.")
    todo.append("Every dispatched subject needs a findings file, INCLUDING the ones "
                "that come back clean — an auditor that ran and found nothing is "
                "coverage; a subject with no file is a subject nobody looked at, and "
                "the verdict counts it that way.")
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


def _exercise_units(project: Project) -> list[str]:
    """MG-3's denominator: the units that actually declare exercises."""
    outline = project.load_yaml("outline/units.yaml")
    named = [str(u.get("id") or u.get("unit") or u.get("slug") or "")
             for u in (outline.get("units") or []) if u.get("exercises")]
    named = [n for n in named if n]
    if named:
        return named
    # The profile says every unit has exercises but the outline does not itemize
    # them. Fall back to the unit set rather than to zero: a denominator of zero
    # would report full coverage for a check that never ran.
    if _has_exercises(project):
        return [p.stem for p in project.unit_paths]
    return []


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


def read_finding_docs(round_dir: Path) -> list[dict]:
    """Every findings FILE in the round, parsed.

    Files, not findings. A subject audited clean writes a file with an empty
    `findings` list, and that file is the only evidence anybody looked at it.
    Counting findings instead of files would score a clean audit as no coverage —
    exactly backwards.
    """
    out: list[dict] = []
    fdir = round_dir / "findings"
    if not fdir.exists():
        return out
    for path in sorted(fdir.glob("*.json")):
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            print(f"[gate] UNREADABLE findings file {path.name}: {exc}")
            continue
        doc["_file"] = path.name
        out.append(doc)
    return out


# ---------------------------------------------------------------------------
# Coverage — the term the verdict was missing
# ---------------------------------------------------------------------------


def check_coverage(project: Project, round_dir: Path, cfg: dict,
                   docs: list[dict], ledger: dict) -> dict[str, dict]:
    """How much of each semantic check's eligible surface has been audited.

    Cumulative, not per-round: the numerator is everything the ledger already
    recorded plus everything this round produced a findings file for. The
    denominator is the post-filter candidate count, and it never shrinks — a
    covered candidate leaves the pool, not the denominator.

    Two axes, reported separately. `covered/eligible` is breadth. `sampled` is
    depth: subjects whose emitted file was a sample of themselves rather than
    all of them. A run with full breadth and partial depth is not complete, and
    collapsing the two numbers is how that gets hidden.
    """
    enabled = cfg.get("checks") or {}
    out: dict[str, dict] = {}

    for check in SEMANTIC_CHECKS:
        if enabled.get(check) is False:
            out[check] = {"state": "waived", "counts": False,
                          "label": f"{check} disabled by config — needs a `waivers` entry"}
            continue

        subjects_seen = {str(d.get("subject") or "") for d in docs
                         if d.get("check") == check}
        sampled_now = {str(d.get("subject") or "") for d in docs
                       if d.get("check") == check and d.get("sampled")}
        prior = ledger.get(check, {})

        rec = _read_json(coverage_path(round_dir, check))
        if rec and rec.get("blocked"):
            # The check could not run at all. Breadth is not complete — but say
            # WHY, or the reader goes looking for auditors to dispatch when the
            # real problem is a missing input.
            out[check] = _record(check, 0, 1, 0, not_dispatched=[check])
            out[check]["state"] = "blocked"
            out[check]["label"] = f"{check} BLOCKED — {rec['blocked']}"
            continue
        if rec:
            emitted = {s["id"]: s for s in (rec.get("subjects") or [])}
            already = list(rec.get("already_audited") or [])
            covered_ids = set(already) | (set(emitted) & subjects_seen)
            eligible = int(rec.get("eligible_candidates", 0))
            sampled_ids = {i for i in covered_ids
                           if (emitted.get(i, {}).get("sampled")
                               or prior.get(i, {}).get("sampled")
                               or i in sampled_now)}
            not_dispatched = sorted(set(emitted) - subjects_seen)
            out[check] = _record(check, len(covered_ids), eligible, len(sampled_ids),
                                 cut=rec.get("cut") or [],
                                 requeued=list(rec.get("requeued") or []),
                                 not_dispatched=not_dispatched,
                                 selected=int(rec.get("selected", 0)),
                                 sampled_ids=sorted(sampled_ids))
            continue

        # No coverage record. Either prepare never ran for this round, or this is
        # a check no emitter produces (MG-3, MG-4) — handled below. Unknown is
        # NOT complete: the whole point is that silence stops meaning "clean".
        if check == "MG-3":
            units = _exercise_units(project)
            if not units:
                out[check] = {"state": "n/a", "counts": False,
                              "label": "MG-3 n/a — this profile has no exercises"}
                continue
            covered_ids = (set(prior) | subjects_seen) & set(units)
            sampled_ids = {u for u in covered_ids
                           if u in sampled_now or prior.get(u, {}).get("sampled")}
            out[check] = _record("MG-3", len(covered_ids), len(units),
                                 len(sampled_ids),
                                 not_dispatched=sorted(set(units) - covered_ids),
                                 selected=len(subjects_seen),
                                 sampled_ids=sorted(sampled_ids))
            continue

        if check == "MG-4":
            done = bool(subjects_seen) or bool(prior)
            sampled = bool(sampled_now) or any(v.get("sampled") for v in prior.values())
            out[check] = _record("MG-4", 1 if done else 0, 1, 1 if sampled else 0,
                                 not_dispatched=[] if done else ["manuscript"],
                                 selected=1 if subjects_seen else 0,
                                 sampled_ids=["manuscript"] if sampled else [])
            out[check]["label"] = ("MG-4 full read" if done and not sampled else
                                   "MG-4 partial read" if done else "MG-4 NOT RUN")
            continue

        out[check] = {
            "state": "unknown", "counts": True, "covered": 0, "eligible": 0,
            "sampled": 0, "sampled_ids": [], "cut": [], "requeued": [],
            "not_dispatched": [], "selected_this_round": 0,
            # Unknown breadth is not complete; depth over nothing is vacuously
            # fine. Reporting depth as short here would send someone narrowing
            # rules to fix a missing coverage record.
            "breadth_complete": False, "depth_complete": True, "complete": False,
            "label": f"{check} no coverage record — run the gate without --verdict-only",
        }
    return out


def _record(check: str, covered: int, eligible: int, sampled: int,
            cut: list | None = None, requeued: list | None = None,
            not_dispatched: list | None = None, selected: int = 0,
            sampled_ids: list | None = None) -> dict:
    """One check's coverage, with the two axes kept apart.

    They are kept apart because they close by different work, and one of them
    cannot always be closed at all. BREADTH closes by spending rounds — the
    emitters drain the pool on their own. DEPTH closes by narrowing a subject's
    scope by hand, which is judgement, and sometimes the honest answer is that
    the rule really does reach all those instances.

    Merging them made `PASS` unreachable by construction: 221 of 454 rules on the
    reference book were over the tractability ceiling, so `sampled == 0` could
    never hold and every project would have ended at a standing waiver.
    """
    breadth = covered >= eligible
    depth = sampled == 0
    return {
        "state": "measured", "counts": True,
        "covered": covered, "eligible": eligible, "sampled": sampled,
        "sampled_ids": sampled_ids or [],
        "cut": cut or [], "requeued": requeued or [],
        "not_dispatched": not_dispatched or [], "selected_this_round": selected,
        "breadth_complete": breadth, "depth_complete": depth,
        "complete": breadth and depth,
        "label": _coverage_label(check, covered, eligible, sampled),
    }


def update_ledger(ledger: dict, round_dir: Path, docs: list[dict],
                  round_no: int) -> dict:
    """Record what this round audited, keyed by subject id AND fingerprint.

    Cumulative and append-only in practice: an entry is only ever overwritten by
    a later, better audit of the same subject. Deleting the file re-audits
    everything, which is the honest way to start over.
    """
    for check in SEMANTIC_CHECKS:
        rec = _read_json(coverage_path(round_dir, check))
        emitted = {s["id"]: s for s in (rec.get("subjects") or [])}
        seen: dict[str, bool] = {}
        for d in docs:
            if d.get("check") != check:
                continue
            sid = str(d.get("subject") or "")
            if not sid:
                continue
            seen[sid] = seen.get(sid, False) or bool(d.get("sampled"))
        entry = ledger.setdefault(check, {})
        for sid, sampled_now in seen.items():
            info = emitted.get(sid, {})
            prev = entry.get(sid, {})
            entry[sid] = {
                "fingerprint": info.get("fingerprint") or prev.get("fingerprint", ""),
                # Not carried over from the previous entry: a re-audit that saw
                # the whole subject supersedes an earlier one that sampled it.
                "sampled": bool(sampled_now or info.get("sampled")),
                "round": round_no,
            }
    return ledger


def _coverage_label(check: str, covered: int, eligible: int, sampled: int) -> str:
    noun = {"MG-1": "concepts", "MG-2": "rules", "MG-3": "exercise units"}.get(check, "")
    tail = f" ({sampled} sampled)" if sampled else ""
    return f"{check} {covered}/{eligible} {noun}{tail}".strip()


# The ladder out of each axis, named where the reader is standing. An escape
# hatch nobody can find is not an escape hatch — and until v3.3 the depth axis
# had no hatch at all, only a script comment pointing at a "hand-written probe"
# that did not exist for rules.
LADDER = {
    "MG-1": "raise `home_cap` on the probe, or narrow it, in "
            "bible/concept-probes-tuned.yaml",
    "MG-2": "narrow, scope or split the rule in bible/rule-probes-tuned.yaml — "
            "round-N/rule-probes-proposed.yaml is the ranked worklist",
    "MG-3": "audit the exercise units that have no findings file yet",
    "MG-4": "re-run the whole-book read without sampling",
}


def coverage_signature(coverage: dict[str, dict], axis: str = "breadth") -> str:
    """A stable string over the exact numbers, for a waiver to pin.

    Without it a waiver written when coverage was 40/169 keeps covering the book
    after someone lowers the quota to 5 — a waiver that outlives its own facts is
    the mechanism this gate spends its whole design budget preventing.

    One signature per axis, because the axes waive separately: they are different
    debts, closed by different work, and a single number would let one hide
    behind the other.
    """
    if axis == "depth":
        parts = [f"{c}:{v['sampled']}s/{v['covered']}"
                 for c, v in sorted(coverage.items()) if v.get("counts")]
    else:
        parts = [f"{c}:{v['covered']}/{v['eligible']}"
                 for c, v in sorted(coverage.items()) if v.get("counts")]
    return "|".join(parts)


def find_waiver(project: Project, check: str, signature: str) -> tuple[bool, str]:
    """(valid, note). A waiver whose signature does not match is stale."""
    status = project.load_yaml("project-status.yaml")
    for w in (status.get("waivers") or []):
        if w.get("check") != check:
            continue
        if str(w.get("signature", "")) == signature:
            return True, ""
        return False, (
            f"A `{check}` waiver exists but its signature is stale — it was written "
            f"for `{w.get('signature')}` and the numbers are now `{signature}`. "
            f"Re-read them and update it, or drop it.")
    return False, ""


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
    for doc in read_finding_docs(round_dir):
        for f in (doc.get("findings") or []):
            f["_file"] = doc.get("_file")
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
                    prior_rounds: list[dict], cfg: dict,
                    coverage: dict[str, dict] | None = None,
                    fixed_defects: dict | None = None) -> GateState:
    st = GateState()
    st.coverage = coverage or {}

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

    # MG-7 — a fixed defect came back. Deterministic and, by default, critical:
    # a formulation that took four passes to catch the first time does not get to
    # re-enter quietly.
    fd = (fixed_defects or {}).get("counts") or {}
    st.open_critical += int(fd.get("critical", 0))
    st.open_major += int(fd.get("major", 0))
    if int(fd.get("critical", 0)) or int(fd.get("major", 0)):
        st.notes.append(
            "MG-7: a defect recorded in `bible/fixed-defects.yaml` reappeared. Before "
            "editing prose, check the entry's `allow_in` — text that teaches against "
            "the wrong form is supposed to quote it, and a pin on the code rather "
            "than on the claim fires on the fix itself.")

    blocking_runners = [r for r in (runners.get("surfaces") or []) if r.get("blocking")]
    st.open_major += len(blocking_runners)
    for r in blocking_runners:
        st.notes.append(
            f"MG-6: surface `{r['surface']}` is executable but its runner is "
            f"`{r['runner']}`, and there is no waiver. Either run it, or record a "
            f"waiver with the verification plan as declared debt (references/verification-plan.md).")
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

    # Coverage is a TERM OF THE VERDICT, not a note somebody remembers to write.
    #
    # A verdict computed only from findings cannot distinguish "we looked at all
    # of it and it is clean" from "we looked at 6% of it and that 6% is clean".
    # Those are different states and only one of them is PASS.
    #
    # Each criterion is binary rather than a percentage floor, on purpose. A floor
    # invites arguing the number, and the day the number is expensive it gets
    # waived out of habit.
    #
    # But the two axes are SEPARATE terms, and that separation is load-bearing.
    # BREADTH — subjects nobody opened — closes on its own as rounds drain the
    # pool. DEPTH — subjects read only in part — closes only by narrowing them by
    # hand, and sometimes the honest answer is that the subject really is that
    # wide. Requiring both for `PASS` made `PASS` unreachable by construction:
    # 221 of 454 rules on the reference book were over the tractability ceiling.
    # A criterion nobody can satisfy decays exactly like a floor nobody defends.
    counting = {c: v for c, v in st.coverage.items() if v.get("counts")}
    st.breadth_complete = bool(counting) and all(
        v.get("breadth_complete") for v in counting.values())
    st.depth_complete = bool(counting) and all(
        v.get("depth_complete") for v in counting.values())
    st.breadth_signature = coverage_signature(st.coverage, "breadth")
    st.depth_signature = coverage_signature(st.coverage, "depth")
    if not counting:
        st.breadth_complete = False
        st.depth_complete = True
        st.notes.append(
            "No coverage record for any semantic check. Coverage unknown reads as "
            "coverage incomplete — that asymmetry is the point.")

    st.verdict = ("BLOCKED" if st.open_critical
                  else "NEEDS-REVISION" if st.open_major
                  else "PASS-PARTIAL" if not st.breadth_complete
                  else "PASS-SAMPLED" if not st.depth_complete
                  else "PASS")

    if st.verdict == "PASS-PARTIAL":
        short = [v["label"] for v in counting.values()
                 if not v.get("breadth_complete")]
        st.notes.append(
            "PASS-PARTIAL — no blocking findings, but there are subjects NOBODY "
            "OPENED: " + " · ".join(short) + ". This does not block the work; it "
            "blocks the CLAIM. Run another round — the emitters skip what is already "
            "audited, so this closes by spending rounds — or record a "
            f"`{COVERAGE_WAIVER}` waiver with signature `{st.breadth_signature}`.")
    elif st.verdict == "PASS-SAMPLED":
        short = [f"{v['label']} — {LADDER.get(c, '')}"
                 for c, v in sorted(counting.items()) if not v.get("depth_complete")]
        st.notes.append(
            "PASS-SAMPLED — every subject was opened, but some were judged from a "
            "SAMPLE of themselves rather than all of it:\n    "
            + "\n    ".join(short)
            + f"\n    Narrow them so they fit in one agent run, or record a "
              f"`{DEPTH_WAIVER}` waiver with signature `{st.depth_signature}`. "
              f"Narrowing is a claim about a subject's SCOPE — if it really does "
              f"reach all those instances, waiving is the honest answer, not a "
              f"smaller number.")
    for check, v in counting.items():
        if v.get("not_dispatched"):
            st.notes.append(
                f"{check}: {len(v['not_dispatched'])} subject(s) have no findings file "
                f"— nobody audited them, so they do NOT count as covered: "
                f"{', '.join(v['not_dispatched'][:6])}"
                + (" …" if len(v["not_dispatched"]) > 6 else ""))
        if v.get("state") == "measured" and not v.get("eligible"):
            st.notes.append(
                f"{check}: zero eligible candidates. That is full coverage of an empty "
                f"set, and it is also what a mis-tuned extractor looks like — check "
                f"the emitter's own report before reading this as clean.")

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
    """`phase: complete` needs PASS, or a signed waiver for each axis that is short.

    The waiver route is deliberate and deliberately awkward. Partial coverage is
    a legitimate budget decision on a long book; asserting a clean bill of health
    over the part nobody read is not. So the book can still finish — but only
    with a human's name on a waiver that pins the exact numbers.

    Depth is waived separately and is the routine one: on a large technical book
    some rules genuinely reach more instances than one agent run can judge, and
    that is a fact about the book rather than a shortfall in the audit. Breadth is
    the one that should feel expensive, because it means nobody looked.
    """
    if st.rounds_without_new < cfg["rounds_without_new_to_close"]:
        return False
    if not st.breadth_complete and not st.coverage_waived:
        return False
    if not st.depth_complete and not st.depth_waived:
        return False
    return True


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
    # Cost dials, overridable per run. `pipeline.manuscript_gate` in meta.yaml is
    # the normal home, but a standalone run over a book written by an earlier
    # version has no such block — and defaults sized for a v3 project mean a few
    # hundred agent runs on a first pass. Start small, calibrate, then scale.
    ap.add_argument("--top-concepts", type=int, default=None,
                    help="Override pipeline.manuscript_gate.top_concepts for this run.")
    ap.add_argument("--top-rules", type=int, default=None,
                    help="Override pipeline.manuscript_gate.top_rules for this run.")
    args = ap.parse_args(argv)

    project = load_project(args.root, args.units)
    cfg = gate_config(project)
    if args.top_concepts is not None:
        cfg["top_concepts"] = args.top_concepts
    if args.top_rules is not None:
        cfg["top_rules"] = args.top_rules
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
               "claim_index": _read_json(round_dir / "claim-index.json"),
               "anchors": _read_json(round_dir / "anchors.json"),
               "fixed_defects": _read_json(round_dir / "fixed-defects.json")}
    runners = audit_runners(project)
    (round_dir / "runners.json").write_text(
        json.dumps(runners, indent=2, ensure_ascii=False), encoding="utf-8")

    if args.deterministic_only:
        _print_deterministic(det, runners)
        return 0

    prior = load_state(run_dir)
    ledger_path = run_dir / "audited.yaml"
    todo: list[str] = []
    if not args.verdict_only:
        prop = propagation_set(project, det.get("claim_index") or {}) if args.round > 1 else []
        if prop:
            (round_dir / "propagation.json").write_text(
                json.dumps({"sites": prop}, indent=2), encoding="utf-8")
        todo = prepare_inputs(project, round_dir, unit_args, cfg, prop,
                              args.round, ledger_path)

    docs = read_finding_docs(round_dir)
    findings = read_findings(round_dir)
    ledger = load_ledger(ledger_path)
    coverage = check_coverage(project, round_dir, cfg, docs, ledger)
    st = compute_verdict(findings, det.get("lint_render") or {}, runners, prior, cfg,
                         coverage, det.get("fixed_defects") or {})
    st.round = args.round
    st.coverage_waived, note_b = find_waiver(project, COVERAGE_WAIVER,
                                             st.breadth_signature)
    st.depth_waived, note_d = find_waiver(project, DEPTH_WAIVER, st.depth_signature)
    for note in (note_b, note_d):
        if note:
            st.notes.append(note)

    # Persist what this round actually audited, so the next one selects the NEXT
    # slice instead of re-reading this one. Written from the findings files, not
    # from what was dispatched: a subject nobody filed for was not audited.
    ledger = update_ledger(ledger, round_dir, docs, args.round)
    save_ledger(ledger_path, ledger)

    deferred = collect_deferred(round_dir)
    st.deferred = len(deferred)
    plan_path = project.reviews / "verification-plan" / "PLAN.md"
    n_checkable = emit_verification_plan(deferred, plan_path)
    if n_checkable:
        st.notes.append(
            f"{n_checkable} unsettled question(s) that reality could answer → "
            f"skeleton at {project.rel(plan_path)}. Unresolved here is usually not "
            f"unknowable, just unknown in this session; write the check down rather "
            f"than softening the claim or asserting it anyway.")

    summary_path = round_dir / "coverage-summary.md"
    emit_coverage_summary(st, cfg, det, runners, docs, summary_path)

    print()
    _print_deterministic(det, runners)
    print(f"[gate] findings read: {len(findings)} "
          f"({st.positives} verified-correct, {st.deferred} deferred)")
    print(f"[gate] open: {st.open_critical} critical · {st.open_major} major · "
          f"{st.open_minor} minor · new blocking this round: {st.new_blocking}")
    print(f"[gate] coverage: {coverage_header(st)}")
    for note in st.notes:
        print(f"[gate] NOTE {note}")

    print(f"\n[gate] VERDICT: {st.verdict}")
    print(f"[gate] report header + What-ran table (computed) → "
          f"{project.rel(summary_path)}")
    if converged(st, cfg):
        waived = [w for w, ok in ((COVERAGE_WAIVER, not st.breadth_complete),
                                  (DEPTH_WAIVER, not st.depth_complete)) if ok]
        how = st.verdict + (f" with a {' and '.join(waived)} waiver" if waived else "")
        print(f"[gate] CONVERGED — {how} with {st.rounds_without_new} consecutive "
              f"round(s) with no new blocking findings. The book can reach `complete`.")
    elif st.verdict == "PASS-PARTIAL":
        need = max(cfg["rounds_without_new_to_close"] - st.rounds_without_new, 0)
        print(f"[gate] NOT converged — no blocking findings, but there are subjects "
              f"nobody opened. Run another round: the emitters skip what is already "
              f"in audited.yaml, so breadth grows monotonically. "
              + (f"({need} more quiet round(s) also needed.) " if need else "")
              + f"To finish here instead, add a `{COVERAGE_WAIVER}` waiver with "
                f"signature `{st.breadth_signature}`.")
    elif st.verdict == "PASS-SAMPLED":
        need = max(cfg["rounds_without_new_to_close"] - st.rounds_without_new, 0)
        print(f"[gate] NOT converged — every subject was opened, but some were read "
              f"only in part. Narrow them (see the notes above for where), "
              + (f"or wait {need} more quiet round(s), " if need else "")
              + f"or add a `{DEPTH_WAIVER}` waiver with signature "
                f"`{st.depth_signature}`.")
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
        # Kept per round so the report can show coverage GROWING, which is the
        # only evidence that the pool is draining rather than the same slice
        # being re-read.
        "coverage": {c: {k: v[k] for k in ("covered", "eligible", "sampled") if k in v}
                     for c, v in st.coverage.items() if v.get("counts")},
        "breadth_signature": st.breadth_signature,
        "depth_signature": st.depth_signature,
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
    return len(collect_deferred(round_dir))


# Things reality can answer. `human-decision` is deliberately absent: no
# observation settles a choice, so it goes to the human packet, not the plan.
CHECKABLE_NEEDS = {"runner", "live-system", "measurement", "person",
                   "document-of-record"}


def collect_deferred(round_dir: Path) -> list[dict]:
    out: list[dict] = []
    fdir = round_dir / "findings"
    if not fdir.exists():
        return out
    for path in sorted(fdir.glob("*.json")):
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        for d in (doc.get("deferred") or []):
            d["_check"] = doc.get("check")
            d["_subject"] = doc.get("subject")
            out.append(d)
    return out


def emit_verification_plan(deferred: list[dict], out_path: Path) -> int:
    """Turn unsettled questions into a plan somebody can execute.

    A `deferred` list is an honest answer to "could you verify this?" and a dead
    end if it stops there. Every item whose `needs` names something reality can
    answer becomes a numbered entry with an empty result slot.

    The pipeline can settle a lot; what it cannot settle is not automatically
    unknowable — usually it is just unknown HERE. Writing the check down is what
    keeps a claim nobody verified from shipping as though somebody had.
    """
    checkable = [d for d in deferred if d.get("needs") in CHECKABLE_NEEDS]
    if not checkable:
        return 0

    by_need: dict[str, list[dict]] = {}
    for d in checkable:
        by_need.setdefault(d["needs"], []).append(d)

    L = ["# Verification plan — generated skeleton", "",
         "Generated by `scripts/manuscript_gate.py` from the round's `deferred` "
         "items. **This is a skeleton, not a plan.** Before anyone can run it you "
         "still owe the shared setup, the paste-ready form of each check, and the "
         "ordering — see `references/verification-plan.md` and "
         "`templates/verification-plan.md`.", "",
         f"**{len(checkable)} check(s)** the pipeline could not settle and reality "
         f"can. {len(deferred) - len(checkable)} further item(s) need a human "
         f"decision rather than an observation; those go to the human packet.", "",
         "Fill `**Actual result:**` in this file, with literal values. Skipping "
         "one? Write `NOT RUN` and why — an empty slot is ambiguous.", "",
         "---", ""]

    n = 0
    for need in sorted(by_need):
        L += [f"## Needs: {need}", ""]
        for d in by_need[need]:
            n += 1
            L += [f"### V-{n:02d} — {d.get('question', '(no question stated)')}", ""]
            if d.get("sites"):
                L.append(f"- **Claim:** {', '.join(d['sites'])}")
            L.append(f"- **From:** {d.get('_check', '?')} · {d.get('_subject', '?')}")
            how = d.get("how_to_check") or (
                "**TODO** — an entry nobody can execute is an entry nobody runs")
            expected = d.get("expected") or "**TODO**"
            defect_if = d.get("defect_if") or (
                "**TODO** — write this BEFORE checking, or the result gets read "
                "as confirmation")
            L.append(f"- **Why unresolved:** {d.get('why_unresolved', '—')}")
            L.append(f"- **How to check:** {how}")
            L.append(f"- **What the book expects:** {expected}")
            L.append(f"- **Suspect a defect if:** {defect_if}")
            L += ["", "**Actual result:**", "", "", "---", ""]

    L += ["## What was left out, and why", "",
          "| Area | Why unchecked | What would change that |", "|---|---|---|", "",
          "## Results roll-up", "",
          "| Check | Result | Verdict | Where it goes |", "|---|---|---|---|", "",
          "Confirmed defect → a finding in the current round, check id as "
          "`authority`. Confirmed correct → `verified_against` in "
          "`bible/claim-index.yaml` (this half matters as much: a verified-correct "
          "result that is not persisted gets re-litigated next pass). Still "
          "surprising → back to `deferred`."]

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(L) + "\n", encoding="utf-8")
    return len(checkable)


def coverage_header(st: GateState) -> str:
    """The one line that has to be true before anything else in the report is read."""
    parts = [v["label"] for v in st.coverage.values() if v.get("label")]
    return " · ".join(parts) if parts else "not measured"


def emit_coverage_summary(st: GateState, cfg: dict, det: dict, runners: dict,
                          docs: list[dict], out_path: Path) -> None:
    """Write the report's header and `What ran` table, COMPUTED.

    v3.1 left the Sampling line as prose for an agent to fill, which makes the
    honest number depend on the agent remembering — the exact mechanism the
    waiver section exists to eliminate. So the report does not ask anyone to
    write these; it asks them to paste this file.
    """
    found = {}
    deferred = {}
    for d in docs:
        c = d.get("check")
        found[c] = found.get(c, 0) + len(d.get("findings") or [])
        deferred[c] = deferred.get(c, 0) + len(d.get("deferred") or [])

    lint = (det.get("lint_render") or {}).get("counts") or {}
    rows = []
    for check, title in (("MG-1", "concept audit"), ("MG-2", "rule vs instances"),
                         ("MG-3", "exercise vs content"), ("MG-4", "whole-book read")):
        v = st.coverage.get(check, {})
        rows.append((f"{check} {title}", v.get("label", "—"),
                     found.get(check, 0), deferred.get(check, 0),
                     "complete" if v.get("complete") else v.get("state", "—")))
    rows.append(("MG-5 render lint", "all units, always complete",
                 sum(int(x) for x in lint.values()), "—", "complete"))
    n_surf = len(runners.get("surfaces") or [])
    n_block = sum(1 for r in (runners.get("surfaces") or []) if r.get("blocking"))
    rows.append(("MG-6 executable code", f"{n_surf} surface(s), always complete",
                 n_block, "—", "complete"))
    fd = det.get("fixed_defects") or {}
    rows.append(("MG-7 fixed-defect regression",
                 f"{fd.get('entries', 0)} entry(ies), whole book, always complete",
                 sum(int(x) for x in (fd.get("counts") or {}).values()), "—",
                 "complete"))

    L = [f"<!-- generated by scripts/manuscript_gate.py — round {st.round}. "
         f"Paste into REPORT.md; do not hand-write these numbers. -->", "",
         f"**Verdict:** {st.verdict}",
         f"**Coverage:** {coverage_header(st)}",
         f"**Breadth signature:** `{st.breadth_signature}`"
         + ("  ✓ waived" if st.coverage_waived else ""),
         f"**Depth signature:** `{st.depth_signature}`"
         + ("  ✓ waived" if st.depth_waived else ""),
         f"**Convergence:** {st.rounds_without_new} consecutive round(s) with no new "
         f"critical/major (need {cfg['rounds_without_new_to_close']})", "",
         "## What ran", "",
         "| Check | Scope this round | Findings | Deferred | Status |",
         "|---|---|---:|---:|---|"]
    L += [f"| {a} | {b} | {c} | {d} | {e} |" for a, b, c, d, e in rows]

    sampled = {c: v for c, v in sorted(st.coverage.items())
               if v.get("counts") and v.get("sampled")}
    if not sampled:
        L += ["", "**Depth:** every audited subject was read in full.", ""]
    else:
        L += ["", "## Depth — subjects read only in part", "",
              "These were opened, so they count toward breadth. They were judged from "
              "a SAMPLE of themselves, so they may not be reported clean. Each line "
              "names the way out; if a subject genuinely is that wide, waiving is the "
              "honest answer rather than a smaller number.", "",
              "| Check | Sampled | Of covered | How to close it |",
              "|---|---:|---:|---|"]
        L += [f"| {c} | {v['sampled']} | {v['covered']} | {LADDER.get(c, '')} |"
              for c, v in sampled.items()]
        L.append("")
        for c, v in sampled.items():
            ids = v.get("sampled_ids") or []
            if ids:
                L += [f"`{c}` sampled subjects: "
                      + ", ".join(f"`{i}`" for i in ids[:25])
                      + (f" … (+{len(ids) - 25})" if len(ids) > 25 else ""), ""]

    # §The economy, stated as a decision rather than as a setting. "30 of 474"
    # reads like configuration; "444 candidate rules will not be looked at — 94%
    # of the surface" reads like something a person chose.
    for check, v in sorted(st.coverage.items()):
        cut = v.get("cut") or []
        if not cut:
            continue
        eligible = max(v.get("eligible", 0), 1)
        L += [f"## {check} — what will NOT be looked at", "",
              f"**{len(cut)} candidate(s) below the cut — {len(cut) / eligible:.0%} of "
              f"the eligible surface.** They are ranked: promoting three specific ones "
              f"into the next round needs no recalibration, just a higher quota or a "
              f"hand-run.", "",
              "| Rank | Id | Stratum | Instances | Site |", "|---:|---|---|---:|---|"]
        for c in cut[:20]:
            L.append(f"| {c.get('rank')} | `{c.get('id')}` | {c.get('stratum')} | "
                     f"{c.get('instances')} | `{c.get('site', '')}` |")
        if len(cut) > 20:
            L.append(f"| … | _{len(cut) - 20} more in "
                     f"`coverage-{check}.json`_ | | | |")
        L.append("")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(L) + "\n", encoding="utf-8")


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
    fd = det.get("fixed_defects") or {}
    fdc = fd.get("counts") or {}
    print(f"[gate] MG-7 fixed defects: {fd.get('entries', 0)} entry(ies) pinned · "
          f"{fdc.get('critical', 0)} critical · {fdc.get('major', 0)} major "
          f"reappearance(s)")
    anc = (det.get("anchors") or {}).get("counts") or {}
    if anc:
        print("[gate] anchors: " + "  ".join(f"{k}={v}" for k, v in sorted(anc.items()))
              + ("  — run `resolve_anchors.py --heal` to repair DRIFT"
                 if anc.get("DRIFT") else ""))


if __name__ == "__main__":
    sys.exit(main())
