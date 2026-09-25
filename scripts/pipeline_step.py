#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pipeline_step.py — the orchestrator's brackets: preconditions, outputs, logs.

Why this exists. On a real project agents came back `null`, a Critic gated
without `coherence.md`, another gated a `humanized.md` that did not exist, and a
cold reader read the author's HTML comments. Each of those is a missing or stale
file — cheap to detect, expensive to discover in a scorecard. Before every agent
the orchestrator runs `check`; after it, `done`. Nothing here judges prose.

Subcommands
  check unit-NN <agent> [--cycle N] [--human-override]
        Inputs of <agent> exist, are non-empty and fresh; on success records the
        dispatch time in drafts/unit-NN/.dispatch.json. Critic and Proofreader
        need checks.json, coherence.md and (literary, nonfiction `full`)
        reader-report.md newer than humanized.md; checks.json must have been
        computed on the CURRENT humanized.md (`source_sha1`), and the story
        check is re-run live on it — never a story block. Cycle > 1 reads the
        loop record (drafts/unit-NN/loop-state.json, written by `snapshot`): the
        worklist of its reason, newer than the agent's previous dispatch; the
        Writer's REVISE source. Literary writer: the full `ready` result (R3:
        outline approved, every sheet complete and signed, ending, seeds, human
        calibration, ledger) plus check_story --unit (no draft).
        Exit 0 ready / 1 not ready.
  done unit-NN <agent> --tier T --cycle N [--before PATH]
        Output exists, non-empty, not `null`, and written after the dispatch;
        appends runs.tsv; editor/humanizer/proofreader write
        role-diff-<agent>-c<N>.json; critic: the verdict is recomputed from
        scorecard.yaml (bookkit/verdict.py). Exit 0 ok · 1 re-dispatch (missing,
        empty, null, stale, no dispatch record) · 3 R3/R4 pause (literary
        writer: `ready` fails, or a story blocker on the page) · 4 contract
        violation (Editor added prose, Proofreader made a non-mechanical change,
        Critic header disagrees with its rows): re-dispatch once with the
        violation list; the second exit 4 for the same agent and cycle → escalate.
  clean unit-NN        humanized.md → humanized.clean.md, HTML comments removed.
  snapshot unit-NN --reason critic|tr|adversarial|human [--target writer|editor|humanizer]
        Before a loopback: copies whatever exists of humanized.md, draft.md,
        edit.md, scorecard.yaml to <name>.c<N> (N = the cycle being closed; no
        humanized.md yet is fine — a Technical Reviewer REVISE) and opens cycle
        N+1 in loop-state.json: reason, target, worklist, and the Writer's REVISE
        source (the last text BEFORE an agent that broke its role contract).
        Exit 0 / 2.
  checks unit-NN       count_rhet, check_identifiers (nonfiction), lint_fiction +
                       check_story (literary), latest role diffs → checks.json +
                       checks.md. Exit 0 / 2 a tool failed / 3 story blocker.
  ready                literary: check_story --ready-to-draft, outline approved;
                       nonfiction: outline approved, knowledge graph signed where
                       the profile requires one. Exit 0 / 1 + blockers.
  apply-edits EDITS.yaml [--dry-run]
                       anchor edits [{unit, find, replace, rule}] on final/; the
                       whole batch fails if any `find` does not match exactly once.
                       Literary: `ready` must pass, and every edited unit is
                       story-checked BEFORE anything is written (check_story
                       --unit blocking, lint_fiction unknown_name major /
                       mentioned_on_stage) — a tic pass cannot add a character.
  approve unit-NN [--force]
        After the human approves: proofread.md → final/unit-NN.md with HTML
        comments stripped (nonfiction keeps SOURCE/ARTIFACT markers). Refuses a
        stale proofread.md, an existing final file without --force, and — literary
        — a failing `ready` or any blocking check_story finding on proofread.md
        (R1–R4 are never overridable). Exit 0 / 1.
  sign <slug> --by NAME
        Literary. The human approved the character sheet: writes `status:
        complete`, `signed_on` (today), `signed_by` and `signed_hash` (a hash of
        name, slug, role, aliases, the required fields and the arc). Refuses an
        incomplete sheet. Any later change to those fields makes check_story
        report CHAR-UNSIGNED-CHANGE until the human re-signs. The orchestrator
        runs it ONLY when the human says the sheet is approved. Exit 0 / 1.

`check proofreader` requires the Critic's PASS, recomputed from scorecard.yaml
and matching critique.md, and no newer confirmed adversarial finding.
`--human-override` (the human approved over a red scorecard, recorded in
human-notes.md) turns a non-PASS verdict into a note — never a story block.

Every relative path (`--root` given or not) resolves against the project root.
The project's `schema_version` must be "3.4"; anything else is an earlier skill's
project (offer a fresh scaffold — references/init-scaffold.md). `project.profile`
is read stripped and lowercased and must name a known profile — missing or
unknown → exit 2 (read as "nonfiction", it switched the literary rules off).

Usage
  python scripts/pipeline_step.py check unit-03 critic
  python scripts/pipeline_step.py done unit-03 humanizer --tier creative --cycle 1
  python scripts/pipeline_step.py snapshot unit-03 --reason critic
  python scripts/pipeline_step.py check unit-03 writer --cycle 2
  python scripts/pipeline_step.py approve unit-03
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
import traceback
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from bookkit import lexicon as L  # noqa: E402
from bookkit import verdict as V  # noqa: E402

SCHEMA = "3.4"
LITERARY = "book-literary"
AGENTS = ("writer", "technical_reviewer", "editor", "humanizer", "reader_pov",
          "continuity_a", "critic", "adversarial", "proofreader", "continuity_b", "digest")
REASONS = ("critic", "tr", "adversarial", "human")
TARGETS = ("writer", "editor", "humanizer")
RUNS_HEADER = "unit\tagent\ttier\tcycle\ttimestamp_utc\toutput_bytes"
FULL_KG = ("book-technical", "scientific-paper")
TERMINOLOGY_KG = ("corporate-guide", "product-docs")
EXIT_OK, EXIT_REDISPATCH, EXIT_PAUSE, EXIT_CONTRACT = 0, 1, 3, 4

# ════════════════════════════════════════════════════════════════════════════
# REQUIREMENTS — per-agent input contract, per profile family.
# Derived from references/pipeline.md § Contracts. Keep this dict in sync with
# those tables; it is the only place the script encodes them. `{u}` = unit id.
#   ("file", path)            must exist, be non-empty and not `null`
#   ("dir", path)             must hold at least one file
#   ("opt", path)             reported when missing, never blocks
#   ("outline",)              outline/units.yaml has an entry for the unit
#   ("fresh", path, than)     `path` exists and is not older than `than`
#   ("story",)                check_story --unit --no-draft has no blocking finding
#   ("ready",)                `pipeline_step.py ready` passes (R3, literary)
# Cycles > 1 are resolved by `loop_requirements` from the loop record.
# ════════════════════════════════════════════════════════════════════════════
D = "drafts/{u}/"
H = D + "humanized.md"
REQUIREMENTS: dict[str, dict[str, list[tuple]]] = {
    "nonfiction": {
        "writer": [("file", "bible/style-guide.md"), ("file", "bible/glossary.md"),
                   ("file", "bible/scope.md"), ("file", "bible/voice-profile.md"),
                   ("outline",), ("opt", "bible/sources/"), ("opt", "bible/continuity-tracker.md")],
        "technical_reviewer": [("file", D + "draft.md"), ("file", D + "grounding-notes.md"),
                               ("file", "bible/scope.md"), ("file", "bible/glossary.md"),
                               ("outline",), ("opt", "bible/sources/"),
                               ("opt", D + "identifiers.json")],
        "editor": [("file", D + "draft.md"), ("file", D + "tech-review.md"), ("outline",)],
        "humanizer": [("file", D + "edit.md"), ("file", D + "tech-review.md"),
                      ("file", "bible/style-guide.md"), ("file", "bible/glossary.md")],
        "reader_pov": [("fresh", D + "humanized.clean.md", H), ("outline",)],
        "continuity_a": [("file", H), ("file", "bible/style-guide.md"),
                         ("file", "bible/glossary.md"), ("opt", "bible/continuity-tracker.md")],
        "critic": [("file", H), ("file", D + "draft.md"),
                   ("fresh", D + "checks.json", H), ("file", D + "checks.md"),
                   ("file", D + "tech-review.md"), ("fresh", D + "coherence.md", H), ("outline",),
                   ("file", "bible/style-guide.md"), ("file", "bible/glossary.md")],
        "adversarial": [("fresh", D + "humanized.clean.md", H), ("fresh", D + "critique.md", H)],
        "proofreader": [("file", H), ("fresh", D + "critique.md", H),
                        ("fresh", D + "scorecard.yaml", H), ("fresh", D + "checks.json", H),
                        ("fresh", D + "coherence.md", H),
                        ("file", "bible/style-guide.md"), ("file", "bible/glossary.md")],
        "continuity_b": [("file", "final/{u}.md"), ("file", "bible/continuity-tracker.md")],
        "digest": [("file", "final/{u}.md")],
    },
    "literary": {
        "writer": [("file", "bible/style-guide.md"), ("file", "bible/voice-profile.md"),
                   ("dir", "bible/characters/"), ("file", "bible/world.md"),
                   ("file", "bible/plot-structure.md"), ("file", "bible/arcs.md"),
                   ("file", "bible/story-ledger.yaml"), ("outline",), ("ready",), ("story",),
                   ("opt", "bible/timeline.md"), ("opt", "bible/continuity-tracker.md")],
        "editor": [("file", D + "draft.md"), ("outline",)],
        "humanizer": [("file", D + "edit.md"), ("file", "bible/style-guide.md"),
                      ("file", "bible/voice-profile.md")],
        "reader_pov": [("fresh", D + "humanized.clean.md", H),
                       ("opt", "bible/reader-journal.md")],
        "continuity_a": [("file", H), ("dir", "bible/characters/"),
                         ("file", "bible/world.md"), ("file", "bible/story-ledger.yaml"),
                         ("outline",), ("opt", "bible/characters/_extras.md"),
                         ("opt", "bible/continuity-tracker.md"), ("opt", "bible/timeline.md")],
        "critic": [("file", H), ("file", D + "draft.md"),
                   ("fresh", D + "checks.json", H), ("file", D + "checks.md"),
                   ("fresh", D + "reader-report.md", H), ("fresh", D + "coherence.md", H),
                   ("outline",), ("dir", "bible/characters/"), ("file", "bible/plot-structure.md"),
                   ("file", "bible/story-ledger.yaml"), ("file", "bible/style-guide.md")],
        "adversarial": [("fresh", D + "humanized.clean.md", H), ("fresh", D + "critique.md", H)],
        "proofreader": [("file", H), ("fresh", D + "critique.md", H),
                        ("fresh", D + "scorecard.yaml", H), ("fresh", D + "checks.json", H),
                        ("fresh", D + "coherence.md", H), ("fresh", D + "reader-report.md", H),
                        ("file", "bible/style-guide.md")],
        "continuity_b": [("file", "final/{u}.md"), ("file", "bible/continuity-tracker.md"),
                         ("file", "bible/story-ledger.yaml")],
        "digest": [("file", "final/{u}.md")],
    },
}
# Profile-specific additions (nonfiction).
PROFILE_EXTRA: dict[str, dict[str, list[tuple]]] = {
    "book-technical": {"writer": [("file", "bible/knowledge-graph.yaml")]},
    "scientific-paper": {"writer": [("file", "bible/knowledge-graph.yaml"),
                                    ("file", "bible/claims-map.yaml")],
                         "technical_reviewer": [("file", "bible/claims-map.yaml")]},
}
# Nonfiction `full` mode: the Critic and the Proofreader also need a fresh Reader-POV report.
FULL_MODE_EXTRA = {"critic": [("fresh", D + "reader-report.md", H)],
                   "proofreader": [("fresh", D + "reader-report.md", H)]}
# The report that triggered a loop — each target's worklist (pipeline.md § Loops).
WORKLIST = {"critic": D + "critique.md", "tr": D + "tech-review.md",
            "adversarial": D + "adversarial-report.md", "human": D + "human-notes.md"}
# What each agent writes (done). An Editor/Humanizer patch cycle writes humanized.md.
OUTPUTS = {
    "writer": [D + "draft.md"],
    "technical_reviewer": [D + "tech-review.md"],
    "editor": [D + "edit.md"],
    "humanizer": [H],
    "reader_pov": [D + "reader-report.md"],
    "continuity_a": [D + "coherence.md"],
    "critic": [D + "critique.md", D + "scorecard.yaml"],
    "adversarial": [D + "adversarial-report.md"],
    "proofreader": [D + "proofread.md"],
    "continuity_b": ["bible/continuity-tracker.md"],
    "digest": ["bible/digests/{u}.digest.md"],
}
NONFICTION_WRITER_EXTRA = [D + "grounding-notes.md"]
# Rubric rows that mean "the Humanizer broke its budget" (routed to the Writer).
HUMANIZER_BUDGET_ROWS = ("voice-6", "voice-8")
# ════════════════════════════════════════════════════════════════════════════


class Project:
    def __init__(self, root: Path):
        self.root = root
        self.meta = L.load_meta(root)
        self.profile = L.profile_of(self.meta)
        self.literary = self.profile == LITERARY
        self.family = "literary" if self.literary else "nonfiction"
        self.mode = str(L.meta_get(self.meta, "pipeline.mode", "fast") or "fast")

    def p(self, rel: str, unit: str = "") -> Path:
        return self.root / rel.format(u=unit)

    def drafts(self, unit: str) -> Path:
        return self.root / "drafts" / unit


def _content_ok(path: Path) -> tuple[bool, str]:
    if not path.exists():
        return False, "missing"
    if path.is_dir():
        return False, "is a directory"
    text = L.read_text(path).strip()
    if not text:
        return False, "empty"
    if text.lower() in ("null", "none", "~", "{}", "[]"):
        return False, f"contains only {text!r}"
    return True, ""


def _mtime(path: Path) -> int:
    return path.stat().st_mtime_ns


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _rel(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


# ---------------------------------------------------------------------------
# State files: the dispatch record and the loop record
# ---------------------------------------------------------------------------


def _load(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        data = json.loads(L.read_text(path))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def dispatches(prj: Project, unit: str) -> dict:
    return _load(prj.drafts(unit) / ".dispatch.json").setdefault("agents", {}) or {}


def _save_dispatches(prj: Project, unit: str, agents: dict) -> None:
    L.write_json(prj.drafts(unit) / ".dispatch.json", {"unit": unit, "agents": agents})


def _fs_now(prj: Project, unit: str) -> int:
    """The filesystem's clock, not Python's: an output written after this call
    has an mtime >= the returned value on the same volume and granularity."""
    stamp = prj.drafts(unit) / ".dispatch.stamp"
    stamp.parent.mkdir(parents=True, exist_ok=True)
    with open(stamp, "w", encoding="utf-8") as fh:
        fh.write(_utc())
    return _mtime(stamp)


def record_dispatch(prj: Project, unit: str, agent: str, cycle: int) -> None:
    """A re-dispatch in the same cycle keeps the contract-violation count."""
    agents = dispatches(prj, unit)
    old = (agents.get(agent) or {}).get(str(cycle)) or {}
    agents.setdefault(agent, {})[str(cycle)] = {"ns": _fs_now(prj, unit), "utc": _utc(),
                                                "violations": int(old.get("violations") or 0)}
    _save_dispatches(prj, unit, agents)


def previous_dispatch(prj: Project, unit: str, agent: str, cycle: int) -> dict | None:
    by = dispatches(prj, unit).get(agent) or {}
    older = [int(c) for c in by if int(c) < cycle]
    return by[str(max(older))] if older else None


def loop_state(prj: Project, unit: str) -> dict:
    data = _load(prj.drafts(unit) / "loop-state.json")
    data.setdefault("cycles", {})
    return data


def _save_loop(prj: Project, unit: str, data: dict) -> None:
    data["unit"] = unit
    L.write_json(prj.drafts(unit) / "loop-state.json", data)


def loop_entry(prj: Project, unit: str, cycle: int | None) -> dict | None:
    if not cycle or cycle <= 1:
        return None
    return loop_state(prj, unit)["cycles"].get(str(cycle))


def patch_cycle(entry: dict | None) -> bool:
    """Editor/Humanizer patch humanized.md in place only when the loop targets
    them; after a Writer loop the whole chain re-runs from a new draft."""
    return bool(entry) and entry.get("target") in ("editor", "humanizer")


# ---------------------------------------------------------------------------
# check
# ---------------------------------------------------------------------------


def requirements(prj: Project, agent: str, cycle: int, entry: dict | None) -> list[tuple] | None:
    """The input list for `agent`, or None when the agent has no slot in this profile."""
    if agent not in REQUIREMENTS[prj.family]:
        return None
    reqs = list(REQUIREMENTS[prj.family][agent])
    if not prj.literary:
        reqs += PROFILE_EXTRA.get(prj.profile, {}).get(agent, [])
        if prj.mode == "full":
            reqs += FULL_MODE_EXTRA.get(agent, [])
    if cycle > 1 and agent in ("editor", "humanizer") and patch_cycle(entry):
        reqs = [r for r in reqs if not (r[0] == "file" and r[1].endswith(("draft.md", "edit.md")))]
        reqs.append(("file", H))
    return reqs


def _gate_passed(prj: Project, unit: str) -> list[str]:
    """Why the Proofreader may not run yet: the Critic did not PASS (recomputed
    from the rows), or a confirmed adversarial finding suspended the PASS."""
    d = prj.drafts(unit)
    out = []
    res = V.check(d / "scorecard.yaml", d / "critique.md", V.tolerance(prj.meta))
    if res["problems"]:
        out += [f"Critic output invalid: {p}" for p in res["problems"]]
    elif res["computed"]["verdict"] != "PASS":
        out.append(f"the scorecard computes {res['computed']['verdict']}, not PASS "
                   f"({res['computed']['basis']}) — the Proofreader runs after a Critic PASS")
    adv, crit = d / "adversarial-report.md", d / "critique.md"
    if adv.exists() and crit.exists() and _mtime(adv) >= _mtime(crit) \
            and re.search(r"CONFIRMED\s*(?:→|->)\s*REVISE", L.read_text(adv)):
        out.append("adversarial-report.md has a confirmed finding (CONFIRMED → REVISE) newer "
                   "than the critique — the PASS is suspended; loop first")
    return out


def ready_blocks(prj: Project) -> list[str]:
    """R3 — the full `ready` result, for every literary step that drafts or
    ships text: the Writer's check and done, approve, apply-edits. A unit's own
    cast being complete is not enough: the outline must be approved, every
    sheet complete and signed, the ending, seeds, calibration and ledger set."""
    if not prj.literary:
        return []
    return [f"R3 (`pipeline_step.py ready` fails): {b}" for b in ready(prj)["blockers"]]


def checks_provenance(prj: Project, unit: str) -> list[str]:
    """checks.json must describe the CURRENT humanized.md: its `source_sha1`
    matches, and no tool failed. A copied or hand-edited checks.json from
    another text is refused, whatever its mtime."""
    d = prj.drafts(unit)
    cj, src = d / "checks.json", d / "humanized.md"
    if not cj.exists() or not src.exists():
        return []                       # the `fresh` requirement already reports it
    data = _load(cj)
    sha = hashlib.sha1(src.read_bytes()).hexdigest()[:12]
    out = []
    if data.get("source_sha1") != sha:
        out.append(f"checks.json was computed on another text (source_sha1 "
                   f"{data.get('source_sha1')!r}, humanized.md is {sha!r}) — re-run checks: "
                   f"`pipeline_step.py checks {unit}`")
    if data.get("errors"):
        out += [f"checks.json: {e.get('tool')} failed — {e.get('error')} (never gate on a check "
                "that did not run)" for e in data["errors"]]
    return out


def story_blocks(prj: Project, unit: str, text: Path | None = None) -> list[str]:
    """R1–R4 blockers for this unit: checks.json → blocking, plus (literary, with
    `text`) a live check_story --unit on that text. Never overridable."""
    out = []
    cj = prj.drafts(unit) / "checks.json"
    if cj.exists():
        data = _load(cj)
        out += [f"{f.get('code')} {f.get('subject')}: {f.get('detail')}"
                for f in data.get("blocking") or []]
    if prj.literary and text is not None and text.exists():
        import check_story as CS
        res = CS.run(prj.root, "unit", unit, text)
        for f in res["findings"]:
            line = f"{f['code']} {f['subject']}: {f['detail']}"
            if f["severity"] == "blocking" and line not in out:
                out.append(line)
    return out


def _worklist_problems(prj: Project, unit: str, agent: str, cycle: int,
                       entry: dict) -> list[str]:
    rel = WORKLIST.get(entry.get("reason", ""))
    if rel is None:
        return [f"loop-state.json cycle {cycle}: unknown reason {entry.get('reason')!r}"]
    path = prj.p(rel, unit)
    ok, why = _content_ok(path)
    if not ok:
        return [f"worklist {rel.format(u=unit)} ({entry['reason']} loop): {why}"]
    prev = previous_dispatch(prj, unit, agent, cycle)
    if prev and _mtime(path) < int(prev["ns"]):
        return [f"worklist {rel.format(u=unit)} is older than the {agent}'s previous dispatch "
                f"({prev['utc']}) — it is not the report that triggered cycle {cycle}"]
    return []


def check(prj: Project, unit: str, agent: str, cycle: int | None = None,
          human_override: bool = False, record: bool = True) -> dict:
    problems: list[str] = []
    notes: list[str] = []
    c = cycle or 1
    entry = loop_entry(prj, unit, c)
    if c > 1 and entry is None:
        problems.append(f"no loop record for cycle {c} in drafts/{unit}/loop-state.json — run "
                        f"`pipeline_step.py snapshot {unit} --reason …` before the loopback")
    reqs = requirements(prj, agent, c, entry)
    if reqs is None:
        return {"unit": unit, "agent": agent, "cycle": c, "ready": False,
                "problems": [f"{agent} has no slot in the {prj.family} pipeline"], "notes": []}
    if agent == "reader_pov" and not prj.literary and prj.mode != "full":
        notes.append("reader_pov runs per unit only in `full` mode (fast: batch polish pass)")
    outline_ids = set(_outline_ids(prj))
    for req in reqs:
        kind = req[0]
        if kind == "file":
            ok, why = _content_ok(prj.p(req[1], unit))
            if not ok:
                problems.append(f"{req[1].format(u=unit)}: {why}")
        elif kind == "dir":
            d = prj.p(req[1], unit)
            if not d.is_dir() or not any(x.is_file() for x in d.iterdir()):
                problems.append(f"{req[1].format(u=unit)}: missing or empty directory")
        elif kind == "opt":
            p = prj.p(req[1], unit)
            if not p.exists() or (p.is_dir() and not any(p.iterdir())):
                notes.append(f"{req[1].format(u=unit)}: absent (optional — say so in the "
                             "dispatch, never silently)")
        elif kind == "outline":
            if unit not in outline_ids:
                problems.append(f"outline/units.yaml: no entry for {unit}")
        elif kind == "fresh":
            path, than = prj.p(req[1], unit), prj.p(req[2], unit)
            ok, why = _content_ok(path)
            if not ok:
                problems.append(f"{req[1].format(u=unit)}: {why}" + _how(req[1]))
            elif than.exists() and _mtime(path) < _mtime(than):
                problems.append(f"{req[1].format(u=unit)}: stale (older than "
                                f"{req[2].format(u=unit)})" + _how(req[1]))
        elif kind == "story":
            import check_story as CS
            res = CS.run(prj.root, "unit", unit, scan_draft=False)
            for f in res["findings"]:
                line = f"{f['code']} {f['subject']}: {f['detail']}"
                if f["severity"] == "blocking" and not any(line in p for p in problems):
                    problems.append(line)
        elif kind == "ready":
            problems += ready_blocks(prj)

    if entry is not None:
        target = entry.get("target")
        if agent == target or (agent in ("editor", "humanizer") and patch_cycle(entry)):
            problems += _worklist_problems(prj, unit, agent, c, entry)
        if agent == "writer":
            if target != "writer":
                notes.append(f"cycle {c} re-enters at the {target}; the Writer does not re-run")
            elif entry.get("mode") == "rework":
                notes.append("REWORK: a fresh draft from the outline entry and the critique")
            else:
                src = entry.get("writer_source")
                ok, why = _content_ok(prj.root / src) if src else (False, "not recorded")
                if not ok:
                    problems.append(f"Writer REVISE source {src or '(none)'}: {why}")
                else:
                    notes.append(f"Writer REVISE input: {src}"
                                 + (f" — {entry['writer_source_why']}"
                                    if entry.get("writer_source_why") else ""))

    if agent in ("critic", "proofreader"):
        problems += checks_provenance(prj, unit)
    if agent == "critic":
        problems += [f"story block (R1–R4, never overridable): {b}"
                     for b in story_blocks(prj, unit, prj.drafts(unit) / "humanized.md")]
    if agent == "proofreader":
        blocks = story_blocks(prj, unit, prj.drafts(unit) / "humanized.md")
        problems += [f"story block (R1–R4, never overridable): {b}" for b in blocks]
        why = _gate_passed(prj, unit)
        if why and human_override and not any(w.startswith("Critic output invalid") for w in why):
            notes += [f"human override: {w}" for w in why]
        else:
            problems += [w + " (a human override over a red scorecard: record it in "
                         "human-notes.md, then pass --human-override)" for w in why]

    ready = not problems
    if ready and record:
        record_dispatch(prj, unit, agent, c)
        if agent == "writer" and entry is not None and entry.get("writer_source"):
            st = loop_state(prj, unit)
            st["cycles"][str(c)]["writer_source_checked_utc"] = _utc()
            _save_loop(prj, unit, st)
    return {"unit": unit, "agent": agent, "cycle": c, "ready": ready,
            "problems": problems, "notes": notes}


def _how(rel: str) -> str:
    if rel.endswith("humanized.clean.md"):
        return " — run `pipeline_step.py clean <unit>`"
    if rel.endswith("checks.json"):
        return " — run `pipeline_step.py checks <unit>`"
    if rel.endswith(("coherence.md", "reader-report.md", "critique.md", "scorecard.yaml")):
        return " — humanized.md changed after it: re-run that agent"
    return ""


def _outline_ids(prj: Project) -> list[str]:
    try:
        data = L.read_yaml(prj.root / "outline" / "units.yaml")
    except ValueError:
        return []
    entries = data.get("units") if isinstance(data, dict) else data
    return [L.unit_id(e.get("unit", e.get("id"))) for e in entries or []
            if isinstance(e, dict) and L.unit_id(e.get("unit", e.get("id")))]


def _outline_entry(prj: Project, unit: str) -> dict:
    try:
        data = L.read_yaml(prj.root / "outline" / "units.yaml")
    except ValueError:
        return {}
    entries = data.get("units") if isinstance(data, dict) else data
    for e in entries or []:
        if isinstance(e, dict) and L.unit_id(e.get("unit", e.get("id"))) == unit:
            return e
    return {}


# ---------------------------------------------------------------------------
# done
# ---------------------------------------------------------------------------


def outputs(prj: Project, unit: str, agent: str, entry: dict | None) -> list[str]:
    if agent == "editor" and patch_cycle(entry):
        return [H]
    outs = list(OUTPUTS[agent])
    if agent == "writer" and not prj.literary:
        outs += NONFICTION_WRITER_EXTRA
    if agent == "continuity_b" and prj.literary:
        cards = [b for b in _outline_entry(prj, unit).get("beats") or [] if isinstance(b, dict)]
        if any((b.get("ledger") or {}).get(k) for b in cards for k in ("plants", "pays")
               if isinstance(b.get("ledger"), dict)):
            outs.append("bible/story-ledger.yaml")     # the unit plants or pays: CG B updates it
    return outs


def done(prj: Project, unit: str, agent: str, tier: str, cycle: int,
         before: Path | None = None) -> tuple[int, list[str]]:
    msgs: list[str] = []
    entry = loop_entry(prj, unit, cycle)
    disp = (dispatches(prj, unit).get(agent) or {}).get(str(cycle))
    if disp is None:
        return EXIT_REDISPATCH, [f"no dispatch record for {agent} cycle {cycle}: run "
                                 f"`pipeline_step.py check {unit} {agent}"
                                 + (f" --cycle {cycle}" if cycle > 1 else "")
                                 + "` before dispatching, then dispatch again"]
    outs = outputs(prj, unit, agent, entry)
    total, bad = 0, []
    for rel in outs:
        path = prj.p(rel, unit)
        ok, why = _content_ok(path)
        if not ok:
            bad.append(f"{rel.format(u=unit)}: {why}")
        elif _mtime(path) < int(disp["ns"]):
            bad.append(f"{rel.format(u=unit)}: stale — not written after the dispatch at "
                       f"{disp['utc']}")
        else:
            total += path.stat().st_size
    if bad:
        return EXIT_REDISPATCH, [f"output not usable → re-dispatch once; a second failure → "
                                 f"stop and tell the human: {'; '.join(bad)}"]

    runs = prj.root / "runs.tsv"
    # Tolerant of a scaffolded file: header only, CRLF, BOM, no final newline.
    old = L.read_text(runs) if runs.exists() else ""
    has_header = old.lstrip().startswith("unit\tagent")
    with open(runs, "a", encoding="utf-8", newline="\n") as fh:
        if old and not old.endswith("\n"):
            fh.write("\n")
        if not has_header and not old.strip():
            fh.write(RUNS_HEADER + "\n")
        fh.write(f"{unit}\t{agent}\t{tier}\t{cycle}\t{_utc()}\t{total}\n")
    msgs.append(f"runs.tsv ← {unit} {agent} {tier} c{cycle} {total} bytes")

    violations: list[str] = []
    if agent in ("editor", "humanizer", "proofreader"):
        pair = _diff_pair(prj, unit, agent, entry, before)
        if pair is None:
            msgs.append(f"role diff skipped: no 'before' text for {agent}")
        else:
            import check_role_diff as RD
            a, b = pair
            budget = RD.default_budget(prj.root) if agent == "humanizer" else None
            res = RD.diff_files(a, b, agent, budget)
            res["before"], res["after"] = _rel(a, prj.root), _rel(b, prj.root)
            res["cycle"] = cycle
            out = prj.drafts(unit) / f"role-diff-{agent}-c{cycle}.json"
            L.write_json(out, res)
            msgs.append(f"role diff → {_rel(out, prj.root)} (added "
                        f"{res['added_words_ratio']:.1%}, touched {res['touched_ratio']:.1%})")
            for v in res["violations"]:
                msgs.append(f"VIOLATION {v}")
            if agent in ("editor", "proofreader"):
                violations = list(res["violations"])
            elif res.get("over_budget"):
                msgs.append("humanizer over budget: the Critic fails "
                            + ("voice-6" if prj.literary else "voice-8")
                            + " and the Writer revises the text BEFORE the Humanizer "
                              "(snapshot records it)")

    if any(o == H for o in outs):
        c = clean(prj, unit)
        msgs.append(f"clean copy refreshed → {_rel(c, prj.root)}")

    if agent == "critic":
        res = V.check(prj.drafts(unit) / "scorecard.yaml", prj.drafts(unit) / "critique.md",
                      V.tolerance(prj.meta))
        msgs += [f"note: {n}" for n in res["notes"]]
        if res["computed"]:
            msgs.append(f"verdict recomputed from scorecard.yaml: {res['computed']['verdict']} → "
                        f"{res['computed']['target']} ({res['computed']['basis']})")
        violations = [f"critic: {p}" for p in res["problems"]]
        msgs += [f"CONTRACT {v}" for v in violations]
        if not violations and res["computed"]["verdict"] == "ESCALATE":
            msgs.append("ESCALATE: no loop. Produce the escalation packet "
                        "(references/loopback-handoff.md) and pause the unit (on_hold) until "
                        "the human decides.")

    if agent == "writer" and prj.literary:
        import check_story as CS
        r3 = ready_blocks(prj)
        res = CS.run(prj.root, "unit", unit, prj.p(D + "draft.md", unit))
        blockers = [f"{f['code']} {f['subject']}: {f['detail']}" for f in res["findings"]
                    if f["severity"] == "blocking"]
        blockers = r3 + [b for b in blockers if not any(b in x for x in r3)]
        if blockers:
            msgs += blockers
            msgs.append("R3/R4: the unit pauses. Run references/character-questionnaire.md "
                        "with the human for what is missing; update sheet, arcs, outline and "
                        "story ledger; the human signs; the unit restarts at the Writer.")
            return EXIT_PAUSE, msgs

    if violations:
        agents = dispatches(prj, unit)
        rec = agents.setdefault(agent, {}).setdefault(str(cycle), dict(disp))
        rec["violations"] = int(rec.get("violations") or 0) + 1
        _save_dispatches(prj, unit, agents)
        if rec["violations"] >= 2:
            msgs.append(f"second contract violation by the {agent} in cycle {cycle} → ESCALATE: "
                        "stop and tell the human (references/loopback-handoff.md)")
        else:
            msgs.append(f"contract violation → re-dispatch the {agent} once with this list "
                        "(check, dispatch, done); a second violation escalates")
        return EXIT_CONTRACT, msgs
    return EXIT_OK, msgs


def _diff_pair(prj: Project, unit: str, agent: str, entry: dict | None,
               before: Path | None) -> tuple[Path, Path] | None:
    d = prj.drafts(unit)
    if agent == "proofreader":
        a, b = d / "humanized.md", d / "proofread.md"
    elif patch_cycle(entry):          # the target patched humanized.md after a snapshot
        snap = d / f"humanized.c{entry.get('snapshot')}.md"
        a, b = (snap if snap.exists() else None), d / "humanized.md"
    elif agent == "editor":
        a, b = d / "draft.md", d / "edit.md"
    else:
        a, b = d / "edit.md", d / "humanized.md"
    if before is not None:
        a = before
    return (a, b) if a is not None and a.exists() and b.exists() else None


# ---------------------------------------------------------------------------
# clean / snapshot / approve
# ---------------------------------------------------------------------------

_FENCE = re.compile(r"^\s*(`{3,}|~{3,})")


def clean_text(text: str, keep: tuple[str, ...] = ()) -> str:
    """HTML comments out (outside code fences); comment-only lines disappear.

    `keep`: comment tags that survive (e.g. SOURCE, ARTIFACT — `<!-- SOURCE: … -->`).
    Blank-line runs left behind collapse to one, outside code fences only.
    """
    kept_comments: list[str] = []
    if keep:
        rx = re.compile(r"<!--\s*(?:" + "|".join(map(re.escape, keep)) + r")\b.*?-->", re.S | re.I)

        def _stash(m: re.Match) -> str:
            kept_comments.append(m.group(0))
            return f"\x00KEEP{len(kept_comments) - 1}\x00"
        text = rx.sub(_stash, text)
    out: list[str] = []
    in_code, in_comment = False, False
    for line in text.splitlines():
        if not in_comment and _FENCE.match(line):
            in_code = not in_code
            out.append(line)
            continue
        if in_code:
            out.append(line)
            continue
        if not line.strip() and not in_comment and out and not out[-1].strip():
            continue                     # one blank line at most, outside code
        kept, i = "", 0
        had_comment = in_comment
        while i < len(line):
            if in_comment:
                j = line.find("-->", i)
                if j < 0:
                    i = len(line)
                    break
                in_comment, i = False, j + 3
            else:
                j = line.find("<!--", i)
                if j < 0:
                    kept += line[i:]
                    break
                kept += line[i:j]
                in_comment, had_comment, i = True, True, j + 4
        if had_comment and not kept.strip():
            continue
        kept = kept.rstrip() if had_comment else kept
        if not kept.strip() and out and not out[-1].strip():
            continue
        out.append(kept)
    joined = "\n".join(out).strip("\n")
    for i, c in enumerate(kept_comments):
        joined = joined.replace(f"\x00KEEP{i}\x00", c)
    return joined + "\n"


def clean(prj: Project, unit: str) -> Path:
    src = prj.drafts(unit) / "humanized.md"
    dst = prj.drafts(unit) / "humanized.clean.md"
    with open(dst, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(clean_text(L.read_text(src)))
    return dst


SHIPPED_COMMENTS = ("SOURCE", "ARTIFACT")   # nonfiction: invisible-citation markers ship


def approve(prj: Project, unit: str, force: bool = False) -> tuple[int, list[str]]:
    """The human approved: proofread.md → final/unit-NN.md, comments stripped."""
    d = prj.drafts(unit)
    src, dst = d / "proofread.md", prj.root / "final" / f"{unit}.md"
    ok, why = _content_ok(src)
    if not ok:
        return 1, [f"drafts/{unit}/proofread.md: {why} — the Proofreader runs before approval"]
    hum = d / "humanized.md"
    if hum.exists() and _mtime(hum) > _mtime(src):
        return 1, [f"drafts/{unit}/proofread.md is older than humanized.md — the human must "
                   "approve the text that ships: re-run the Proofreader"]
    if prj.literary:
        blocks = ready_blocks(prj)
        blocks += [b for b in story_blocks(prj, unit, src) if not any(b in x for x in blocks)]
        if blocks:
            return 1, [f"story block on the text that would ship — R1–R4 are never "
                       f"overridable, not by a human approval and not by --force: {b}"
                       for b in blocks] + ["Run references/character-questionnaire.md; the "
                                           "unit restarts at the Writer."]
    if dst.exists() and not force:
        return 1, [f"final/{unit}.md exists — pass --force to replace it (late edits to an "
                   "approved unit go through `apply-edits`)"]
    raw = L.read_text(src)
    keep = () if prj.literary else SHIPPED_COMMENTS
    text = clean_text(raw, keep)
    dst.parent.mkdir(parents=True, exist_ok=True)
    with open(dst, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    removed = raw.count("<!--") - text.count("<!--")
    return 0, [f"final/{unit}.md ← drafts/{unit}/proofread.md ({removed} HTML comment(s) "
               f"stripped{'' if prj.literary else '; SOURCE/ARTIFACT markers kept'})",
               "Next: CG Mode B → digest → "
               + ("reader-journal update → " if prj.literary else "") + "archive."]


_SNAP = re.compile(r"^(humanized|draft|edit|scorecard)\.c(\d+)\.(md|yaml)$")
SNAP_SOURCES = (("humanized", "humanized.md"), ("draft", "draft.md"), ("edit", "edit.md"),
                ("scorecard", "scorecard.yaml"))


def _closing_cycle(prj: Project, unit: str) -> int:
    st = loop_state(prj, unit)
    return max([int(c) for c in st["cycles"]] or [1])


def _latest_role_diff(prj: Project, unit: str, agent: str, cycle: int) -> dict | None:
    p = prj.drafts(unit) / f"role-diff-{agent}-c{cycle}.json"
    return _load(p) if p.exists() else None


def _snapshot_of(rel_before: str, made: dict[str, str], unit: str) -> str | None:
    """The immutable snapshot of a role diff's 'before' text."""
    name = Path(rel_before).name
    if _SNAP.match(name):
        return f"drafts/{unit}/{name}"
    kind = {"draft.md": "draft", "edit.md": "edit", "humanized.md": "humanized"}.get(name)
    return made.get(kind) if kind else None


def snapshot(prj: Project, unit: str, reason: str,
             target: str | None = None) -> tuple[int, list[str]]:
    """Close the current cycle: snapshot its texts, open the next in loop-state.json."""
    d = prj.drafts(unit)
    n = _closing_cycle(prj, unit)
    if n > 1 and not any(str(n) in (by or {}) for by in dispatches(prj, unit).values()):
        return 2, [f"cycle {n} is open and nothing ran in it yet — run its agents with "
                   f"--cycle {n} before the next loopback"]
    if any((d / f"{k}.c{n}.{src.rsplit('.', 1)[1]}").exists() for k, src in SNAP_SOURCES):
        return 2, [f"cycle {n} is already snapshotted — cycle {n + 1} is open: run its agents "
                   f"with --cycle {n + 1}"]
    crit = d / "critique.md"
    head = V.header(L.read_text(crit)) if crit.exists() else {"verdict": None, "target": None}
    if reason == "critic":
        if (head["verdict"] or "").upper() == "ESCALATE" or (head["target"] or "").lower() in (
                "escalate", "none"):
            return 2, [f"the Critic's verdict is {head['verdict']} (target {head['target']}): no "
                       "loop. ESCALATE → escalation packet (references/loopback-handoff.md), "
                       "the unit is paused; PASS → the Proofreader"]
    if target is None:
        if reason == "critic":
            target = (head["target"] or "").lower() or None
        elif reason == "adversarial" and (d / "adversarial-report.md").exists():
            m = re.search(r"CONFIRMED\s*(?:→|->)\s*REVISE\s*\((\w+)\)",
                          L.read_text(d / "adversarial-report.md"))
            target = m.group(1).lower() if m else None
        target = target or "writer"
    if target not in TARGETS:
        return 2, [f"loop target {target!r} is not one of {', '.join(TARGETS)}"]

    made: dict[str, str] = {}
    for kind, src in SNAP_SOURCES:
        if (d / src).exists():
            dst = d / f"{kind}.c{n}.{src.rsplit('.', 1)[1]}"
            shutil.copyfile(d / src, dst)       # copyfile: the snapshot gets a fresh mtime
            made[kind] = _rel(dst, prj.root)
    if not made:
        return 2, [f"drafts/{unit}/ has no draft.md, edit.md or humanized.md to snapshot"]
    msgs = [f"snapshot → {v}" for v in made.values()]
    if "humanized" not in made:
        msgs.append("note: no humanized.md yet (the loop re-entered before the Humanizer ran) — "
                    "the next cycle re-runs the whole chain from a new draft")

    entry = {"reason": reason, "target": target, "snapshot": n, "files": made,
             "worklist": WORKLIST[reason].format(u=unit), "created_utc": _utc(),
             "mode": "rework" if reason == "critic" and (head["verdict"] or "").upper()
             == "REWORK" else "revise"}
    if target == "writer":
        failing = []
        sc = d / "scorecard.yaml"
        if reason == "critic" and sc.exists():
            try:
                items = (L.read_yaml(sc) or {}).get("items") or []
            except ValueError:
                items = []
            failing = [str(i.get("id")) for i in items
                       if isinstance(i, dict) and i.get("status") == "fail"]
        ed = _latest_role_diff(prj, unit, "editor", n)
        hu = _latest_role_diff(prj, unit, "humanizer", n)
        editor_bad = bool(ed and ed.get("violations"))
        humanizer_bad = bool(hu and hu.get("over_budget")) or any(
            f in HUMANIZER_BUDGET_ROWS for f in failing)
        src, why = None, ""
        if editor_bad and ed:
            src = _snapshot_of(str(ed.get("before") or ""), made, unit)
            why = "the Editor broke its contract (added prose): revise the text before the Editor"
        elif humanizer_bad:
            src = _snapshot_of(str((hu or {}).get("before") or "edit.md"), made, unit)
            why = ("the Humanizer went over budget: revise the text before the Humanizer, "
                   "not its rewrite")
        if src is None:
            src = made.get("humanized") or made.get("draft")
        entry.update(failing=failing, writer_source=src, writer_source_why=why,
                     role_violations={"editor": list((ed or {}).get("violations") or []),
                                      "humanizer_over_budget": humanizer_bad})
        msgs.append(f"Writer {'REWORK' if entry['mode'] == 'rework' else 'REVISE'} input: "
                    f"{src}" + (f" — {why}" if why else ""))
    st = loop_state(prj, unit)
    st["cycles"][str(n + 1)] = entry
    _save_loop(prj, unit, st)
    msgs.append(f"cycle {n + 1} opened ({reason} → {target}); worklist "
                f"{entry['worklist']}. Every agent of the cycle runs with --cycle {n + 1}.")
    return 0, msgs


# ---------------------------------------------------------------------------
# checks
# ---------------------------------------------------------------------------


def checks(prj: Project, unit: str) -> tuple[int, dict]:
    src = prj.drafts(unit) / "humanized.md"
    if not src.exists():
        raise FileNotFoundError(src)
    result: dict = {
        "unit": unit, "profile": prj.profile, "source": _rel(src, prj.root),
        "source_sha1": hashlib.sha1(src.read_bytes()).hexdigest()[:12],
        "generated_utc": _utc(),
        "counts": None, "identifiers": None, "fiction": None, "story": None,
        "role_diff": {}, "tics": None, "blocking": [], "errors": [],
    }
    import count_rhet as CR
    try:
        rep = CR.compute(prj.root, unit, src, prj.meta)
        result.update(language=rep["language"], pack=rep["pack"], words=rep["words"],
                      counts=rep["counts"])
        result["notes"] = rep["notes"]
    except Exception as exc:  # noqa: BLE001 — a failed tool is reported, loudly
        result["errors"].append(_err("count_rhet", exc))

    if prj.literary:
        import lint_fiction as LF
        import check_story as CS
        ctx = None
        try:
            ctx = LF.build_context(prj.root, prj.meta)
            fic = LF.lint_unit(prj.root, unit, src, ctx)
            result["fiction"] = {"findings": [f for f in fic["findings"] if f["severity"] != "info"],
                                 "stats": fic["stats"]["units"].get(unit, {}),
                                 "severity": fic["stats"]["severity"]}
            result["tics"] = {
                "gestures": result["fiction"]["stats"].get("tics", {}),
                "repeated_ngrams": [f["subject"] for f in fic["findings"]
                                    if f["rule"] == "repeated_ngram"],
                "over_quota": sorted({f["subject"] for f in fic["findings"]
                                      if f["rule"] == "gesture_tic"}),
            }
        except Exception as exc:  # noqa: BLE001
            result["errors"].append(_err("lint_fiction", exc))
        try:
            story = CS.run(prj.root, "unit", unit, src, ctx=ctx)
            result["story"] = story
            result["blocking"] = [f for f in story["findings"] if f["severity"] == "blocking"]
        except Exception as exc:  # noqa: BLE001
            result["errors"].append(_err("check_story", exc))
    else:
        import check_identifiers as CI
        try:
            result["identifiers"] = CI.check(prj.root, [src], meta=prj.meta)
        except Exception as exc:  # noqa: BLE001
            result["errors"].append(_err("check_identifiers", exc))

    for agent in ("editor", "humanizer", "proofreader"):
        files = []
        for p in prj.drafts(unit).glob(f"role-diff-{agent}-c*.json"):
            m = re.fullmatch(rf"role-diff-{agent}-c(\d+)\.json", p.name)
            if m:
                files.append((int(m.group(1)), p))
        if files:
            n, p = max(files)
            data = json.loads(L.read_text(p))
            summary = {k: v for k, v in data.items() if k != "changes"}
            summary["changes_count"] = len(data.get("changes") or [])
            summary["file"] = _rel(p, prj.root)
            result["role_diff"][agent] = summary

    d = prj.drafts(unit)
    L.write_json(d / "checks.json", result)
    with open(d / "checks.md", "w", encoding="utf-8", newline="\n") as fh:
        fh.write(render_checks(result))
    code = 2 if result["errors"] else (3 if result["blocking"] else 0)
    return code, result


def _err(tool: str, exc: Exception) -> dict:
    return {"tool": tool, "error": f"{type(exc).__name__}: {exc}",
            "trace": traceback.format_exc(limit=3)}


def render_checks(r: dict) -> str:
    out = [f"# Checks — {r['unit']}", "",
           f"Source: `{r['source']}` (sha1 {r['source_sha1']}), {r.get('words', '?')} words, "
           f"language {r.get('language', '?')} (pack {r.get('pack', '?')}). Generated "
           f"{r['generated_utc']} by `pipeline_step.py checks`. **Copy these numbers; do not "
           f"recount.**", ""]
    if r["errors"]:
        out += ["## ERRORS — a check did not run", ""]
        out += [f"- **{e['tool']}**: {e['error']}" for e in r["errors"]] + [""]
    if r["blocking"]:
        out += ["## Blocking (story — R1–R4, never overridable)", ""]
        out += [f"- **{f['code']}** {f['subject']}: {f['detail']}" for f in r["blocking"]] + [""]
    if r["counts"]:
        out += ["## Counts", "", "| item | count | quota | over |", "|---|---|---|---|"]
        for k in sorted(r["counts"]):
            c = r["counts"][k]
            if "count" in c:
                out.append(f"| {k} | {c['count']} | {c.get('quota', '—')} | "
                           f"{'**yes**' if c.get('over') else 'no'} |")
            elif k == "rhet-4":
                out.append(f"| rhet-4 | hit={c['hit']} | {c.get('quota')} | "
                           f"{'**yes**' if c.get('over') else 'no'} |")
            elif k == "rhet-5":
                out.append(f"| rhet-5 | {c['bolds']} bolds ({c['per_1000']}/1000) | "
                           f"{c['quota']}/1000 | {'**yes**' if c.get('over') else 'no'} |")
            elif k == "rhet-7":
                out.append(f"| rhet-7 | {len(c['headings'])} template heading(s) | — | — |")
            elif k == "sentence_length":
                out.append(f"| sentence_length | mean {c['mean']}, sd {c['sd']}, "
                           f"flat runs {c['flat_runs']} | — | — |")
        out.append("")
        for k in ("rhet-2", "rhet-3", "ai_vocab", "speech_verbs_ornate"):
            c = r["counts"].get(k) or {}
            hits = c.get("matches") or c.get("terms") or c.get("hits") or []
            if hits:
                out.append(f"- {k}: " + "; ".join(f"l.{h['line']} “{h.get('text') or h.get('term')}”"
                                                  for h in hits[:10]))
        out.append("")
    if r["identifiers"] is not None:
        ids = r["identifiers"]
        out += ["## Identifiers (tech_a-4)", "",
                f"{ids['checked']} checked against {ids['index_size']} indexed "
                f"({ids['index_state']}); **{len(ids['unknown'])} unknown**.", ""]
        out += [f"- `{e['identifier']}` at {', '.join(e['locations'])}" for e in ids["unknown"]]
        out += [f"- note: {n}" for n in ids.get("notes", [])] + [""]
    if r["fiction"] is not None:
        fic = r["fiction"]
        out += ["## Fiction lint", ""]
        for sev in ("major", "minor"):
            rows = [f for f in fic["findings"] if f["severity"] == sev]
            if rows:
                out.append(f"**{sev}** ({len(rows)})")
                out += [f"- {f['rule']} l.{f['line'] or '—'}: {f['detail']}" for f in rows]
                out.append("")
        tics = (r.get("tics") or {}).get("gestures") or {}
        if tics:
            out.append("Gesture tics: " + ", ".join(
                f"{k} ×{v['count']} (quota {v['quota']}{', OVER' if v['over'] else ''})"
                for k, v in sorted(tics.items())))
            out.append("")
    if r["story"] is not None:
        st = r["story"]
        ctx = st.get("context") or {}
        out += ["## Story (check_story --unit)", ""]
        for key in ("arcs_resolving_here", "turning_points_here", "ledger_due_here",
                    "ledger_planted_here", "extras_here", "characters_on_page"):
            if ctx.get(key):
                out.append(f"- {key}: {', '.join(ctx[key])}")
        if ctx.get("is_final_unit"):
            out.append("- **final unit: the ending in plot-structure must be delivered "
                       "(ending-1)**")
        out += [f"- {f['severity']} {f['code']} {f['subject']}: {f['detail']}"
                for f in st["findings"] if f["severity"] != "blocking"] + [""]
    if r["role_diff"]:
        out += ["## Role diffs", ""]
        for agent, d in r["role_diff"].items():
            out.append(f"- {agent}: added {d['added_words_ratio']:.1%}, touched "
                       f"{d['touched_ratio']:.1%}"
                       + (f", budget {d['budget']:.0%}" if d.get("budget") is not None else "")
                       + (", **OVER BUDGET**" if d.get("over_budget") else "")
                       + f" — {d['changes_count']} change(s), `{d['file']}`")
            out += [f"  - VIOLATION {v}" for v in d.get("violations") or []]
        out.append("")
    return "\n".join(out).rstrip() + "\n"


# ---------------------------------------------------------------------------
# ready
# ---------------------------------------------------------------------------


def ready(prj: Project) -> dict:
    blockers: list[str] = []
    notes: list[str] = []
    ids = _outline_ids(prj)
    if not ids:
        blockers.append("OUTLINE-MISSING: outline/units.yaml has no unit entries")
    status = {}
    try:
        status = L.read_yaml(prj.root / "project-status.yaml") or {}
        outline_doc = L.read_yaml(prj.root / "outline" / "units.yaml") or {}
    except ValueError as exc:
        blockers.append(f"YAML error: {exc}")
        outline_doc = {}
    approved = (L.meta_get(status, "outline.approved") is True
                or (isinstance(outline_doc, dict) and outline_doc.get("approved") is True))
    if ids and not approved:
        blockers.append("OUTLINE-NOT-APPROVED: set project-status.yaml → outline.approved: "
                        "true when the human approves the outline")
    story = None
    if prj.literary:
        import check_story as CS
        story = CS.run(prj.root, "ready")
        for f in story["findings"]:
            if f["severity"] == "blocking":
                blockers.append(f"{f['code']} {f['subject']}: {f['detail']}")
            else:
                notes.append(f"{f['severity']} {f['code']} {f['subject']}: {f['detail']}")
    elif prj.profile in FULL_KG + TERMINOLOGY_KG:
        kg_path = prj.root / "bible" / "knowledge-graph.yaml"
        try:
            kg = L.read_yaml(kg_path)
        except ValueError as exc:
            kg = None
            blockers.append(f"KG-INVALID: {exc}")
        if not isinstance(kg, dict):
            blockers.append("KG-MISSING: bible/knowledge-graph.yaml is required for "
                            f"{prj.profile}")
        else:
            if prj.profile in FULL_KG and \
                    L.meta_get(kg, "constraints.every_concept_assigned_to_unit") is not True:
                blockers.append("KG-UNASSIGNED: knowledge-graph constraints."
                                "every_concept_assigned_to_unit is not true — write "
                                "introduced_in back from the outline")
            verified = L.meta_get(status, "knowledge_graph.last_verified")
            if not verified or str(verified).strip().startswith("["):
                blockers.append("KG-NOT-SIGNED: project-status.yaml → "
                                "knowledge_graph.last_verified is empty")
    return {"profile": prj.profile, "ready": not blockers, "blockers": blockers,
            "notes": notes, "story": story}


# ---------------------------------------------------------------------------
# sign
# ---------------------------------------------------------------------------

_SIGN_KEYS = re.compile(r"^(?:status|signed_on|signed_by|signed_hash)\s*:")


def sign(prj: Project, slug: str, by: str) -> tuple[int, list[str]]:
    """The human approved a character sheet: bind the approval to its content.

    Writes `status: complete`, `signed_on` (today), `signed_by` and
    `signed_hash` into the sheet's front matter (other lines untouched).
    Refuses a sheet that is not complete — R1 fields, placeholders, 3-word
    minimum — because a signature on an unanswered questionnaire means nothing."""
    import datetime as _dt
    from bookkit.placeholder import is_placeholder
    import check_story as CS
    import lint_fiction as LF
    if not prj.literary:
        return 1, [f"sign is for book-literary character sheets (profile {prj.profile!r})"]
    if is_placeholder(by):
        return 1, ["--by names the human who approved the sheet (not a placeholder)"]
    matches = [ch for ch in LF.load_cast(prj.root) if ch.slug == slug or ch.path.stem == slug]
    if len(matches) != 1:
        return 1, [f"{len(matches)} sheet(s) in bible/characters/ match '{slug}' — one sheet per "
                   "slug (CHAR-DUPLICATE)" if matches else
                   f"no sheet bible/characters/{slug}.md (or with `slug: {slug}`)"]
    ch = matches[0]
    if ch.error or not ch.has_front_matter:
        return 1, [f"{_rel(ch.path, prj.root)}: {ch.error or 'no YAML front matter'} — fix the "
                   "sheet (templates/character-sheet.md) before signing"]
    today = _dt.date.today().isoformat()
    digest = CS.sheet_hash(ch.data, ch.slug)
    trial = LF.Character(slug=ch.slug, path=ch.path, has_front_matter=True,
                         data={**ch.data, "status": "complete", "signed_on": today,
                               "signed_hash": digest})
    st = CS.Story(prj.root)
    gaps = [f"{f['code']}: {f['detail']}" for f in CS.sheet_findings(st, trial, st.outline_ids)
            if f["code"] in ("CHAR-INCOMPLETE", "CHAR-NO-ARC")]
    if gaps:
        return 1, [f"{_rel(ch.path, prj.root)} is not complete — nothing signed. Run the "
                   "questionnaire blocks for:"] + [f"  {g}" for g in gaps]
    raw = L.read_text(ch.path)
    m = L._FM_RE.match(raw)
    nl = "\r\n" if "\r\n" in raw else "\n"
    fm = [ln for ln in m.group(1).replace("\r\n", "\n").split("\n") if not _SIGN_KEYS.match(ln)]
    at = next((i + 1 for i, ln in enumerate(fm) if re.match(r"^role\s*:", ln)), len(fm))
    fm[at:at] = ["status: complete", f'signed_on: "{today}"',
                 f"signed_by: {json.dumps(str(by).strip(), ensure_ascii=False)}",
                 f'signed_hash: "{digest}"']
    text = raw[:m.start(1)] + nl.join(fm) + raw[m.end(1):]
    with open(ch.path, "w", encoding="utf-8", newline="") as fh:
        fh.write(text if nl == "\n" else text.replace("\r\n", "\n").replace("\n", "\r\n"))
    data, _body, err = L.front_matter(L.read_text(ch.path))
    if err or CS.sheet_hash(data or {}, ch.slug) != digest:
        return 1, [f"{_rel(ch.path, prj.root)}: the signed sheet does not re-read to the same "
                   f"content ({err or 'hash mismatch'}) — check the front matter by hand"]
    return 0, [f"{_rel(ch.path, prj.root)} signed by {by} on {today} ({digest}). Any change to "
               "name, role, aliases, the required fields or the arc needs the questionnaire "
               "block again and a new signature."]


# ---------------------------------------------------------------------------
# apply-edits
# ---------------------------------------------------------------------------


def edited_story_blocks(prj: Project, texts: dict[Path, str]) -> list[str]:
    """Literary: check every edited unit AS IT WOULD BE WRITTEN — check_story
    --unit (blocking) and lint_fiction (unknown_name major, mentioned_on_stage)
    on a temporary copy; final/ is untouched until all of them pass."""
    import tempfile
    import check_story as CS
    import lint_fiction as LF
    out: list[str] = []
    ctx = LF.build_context(prj.root, prj.meta)
    with tempfile.TemporaryDirectory(prefix="bf-apply-") as td:
        for path, text in texts.items():
            uid = L.unit_id(path.stem) or path.stem
            tmp = Path(td) / f"{uid}.md"
            with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(text)
            res = CS.run(prj.root, "unit", uid, tmp, ctx=ctx)
            out += [f"{uid}: {f['code']} {f['subject']}: {f['detail']}" for f in res["findings"]
                    if f["severity"] == "blocking"]
            lint = LF.lint_unit(prj.root, uid, tmp, ctx)
            for f in lint["findings"]:
                if (f["rule"] == "unknown_name" and f["severity"] == "major") \
                        or f["rule"] == "mentioned_on_stage":
                    line = f"{uid}: lint_fiction {f['rule']} {f.get('subject')}: {f['detail']}"
                    if not any(str(f.get("subject")) in o and uid in o for o in out):
                        out.append(line)
    return out


def apply_edits(prj: Project, edits_path: Path, dry_run: bool) -> tuple[int, list[str]]:
    try:
        data = L.read_yaml(edits_path)
    except ValueError as exc:
        return 1, [str(exc)]
    edits = data.get("edits") if isinstance(data, dict) else data
    if not isinstance(edits, list) or not edits:
        return 1, [f"{edits_path}: expected a list of {{unit, find, replace, rule}}"]

    texts: dict[Path, str] = {}
    newlines: dict[Path, str] = {}
    errors: list[str] = []
    applied: list[str] = []
    for i, e in enumerate(edits, 1):
        if not isinstance(e, dict) or "find" not in e or "replace" not in e:
            errors.append(f"edit {i}: needs unit, find, replace")
            continue
        uid = L.unit_id(e.get("unit"))
        path = prj.root / "final" / f"{uid}.md" if uid else None
        if path is None or not path.exists():
            errors.append(f"edit {i}: no final/{uid or e.get('unit')}.md")
            continue
        if path not in texts:
            raw = path.read_bytes()
            newlines[path] = "\r\n" if b"\r\n" in raw else "\n"
            texts[path] = L.read_text(path)
        find = unicodedata.normalize("NFC", str(e["find"]))
        replace = unicodedata.normalize("NFC", str(e["replace"]))
        n = texts[path].count(find)
        if n != 1:
            errors.append(f"edit {i} ({uid}, rule {e.get('rule', '?')}): `find` matches "
                          f"{n} times, must match exactly once — {find[:60]!r}")
            continue
        texts[path] = texts[path].replace(find, replace, 1)
        applied.append(f"edit {i} ({uid}, {e.get('rule', '?')}): {find[:40]!r} → "
                       f"{replace[:40]!r}")
    if errors:
        return 1, ["batch rejected — nothing written:"] + errors
    if prj.literary:
        errors = ready_blocks(prj) + edited_story_blocks(prj, texts)
        if errors:
            return 1, ["batch rejected — nothing written (R1–R4 are never overridable; a "
                       "polish edit cannot add a character):"] + errors
    if dry_run:
        return 0, ["dry run — all edits match exactly once:"] + applied
    for path, text in texts.items():
        with open(path, "w", encoding="utf-8", newline=newlines[path]) as fh:
            fh.write(text)
    return 0, applied + [f"{len(applied)} edit(s) applied to {len(texts)} file(s). Next: "
                         "`python scripts/validate_claim_index.py` (nonfiction) and CG Mode B "
                         "on every changed unit."]


# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Pipeline brackets: preconditions, outputs, "
                                             "runs log, clean text, snapshots, checks.")
    ap.add_argument("--root", default=None,
                    help="Project root (default: nearest ancestor with bible/meta.yaml).")
    sub = ap.add_subparsers(dest="cmd", required=True)
    # `--root` is accepted after the subcommand too (`ready --root X`): that is how
    # people type it, and a usage error there reads as "the tool is broken".
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--root", default=argparse.SUPPRESS,
                        help="Project root (default: nearest ancestor with bible/meta.yaml).")

    def _p(*a, **k):
        return sub.add_parser(*a, parents=[common], **k)

    c = _p("check", help="Inputs of an agent exist, are non-empty and fresh.")
    c.add_argument("unit")
    c.add_argument("agent", choices=AGENTS)
    c.add_argument("--cycle", type=int, default=None,
                   help="Cycle number; > 1 reads the loop record written by `snapshot`.")
    c.add_argument("--human-override", action="store_true",
                   help="proofreader: the human approved over a red scorecard (recorded in "
                        "human-notes.md); a non-PASS verdict becomes a note. Never a story block.")
    c.add_argument("--json", metavar="OUT")

    d = _p("done", help="Verify an agent's output, log it, record role diffs.")
    d.add_argument("unit")
    d.add_argument("agent", choices=AGENTS)
    d.add_argument("--tier", required=True)
    d.add_argument("--cycle", type=int, required=True)
    d.add_argument("--before", default=None,
                   help="Override the 'before' text of the role diff.")

    for name, text in (("clean", "humanized.md → humanized.clean.md"),
                       ("checks", "script counts → checks.json + checks.md")):
        s = _p(name, help=text)
        s.add_argument("unit")
    sn = _p("snapshot", help="Close the cycle: snapshot texts, open the next loop.")
    sn.add_argument("unit")
    sn.add_argument("--reason", required=True, choices=REASONS,
                    help="What triggered the loop: critic, tr (Technical Reviewer REVISE), "
                         "adversarial (confirmed finding), human (rejection).")
    sn.add_argument("--target", choices=TARGETS, default=None,
                    help="Who re-enters (default: the critique's loopback target, the "
                         "adversarial report's, else writer).")

    r = _p("ready", help="May drafting start?")
    r.add_argument("--json", metavar="OUT")

    a = _p("apply-edits", help="Apply anchor edits to final/.")
    a.add_argument("edits")
    a.add_argument("--dry-run", action="store_true")

    ap_ = _p("approve", help="proofread.md → final/unit-NN.md, HTML comments "
                                         "stripped (after the human approves).")
    ap_.add_argument("unit")
    ap_.add_argument("--force", action="store_true",
                     help="Replace an existing final/unit-NN.md.")

    sg = _p("sign", help="The human approved a character sheet: status complete, signed_on, "
                         "signed_by, signed_hash (literary).")
    sg.add_argument("slug")
    sg.add_argument("--by", required=True, help="Who approved it (the human's name).")

    args = ap.parse_args(argv)
    root = L.find_root(args.root)
    if not (root / "bible" / "meta.yaml").exists():
        print(f"[pipeline_step] no bible/meta.yaml under {root}", file=sys.stderr)
        return 2
    prj = Project(root)
    for problem in (L.schema_problem(prj.meta), L.profile_problem(prj.meta)):
        if problem:
            print(f"[pipeline_step] {problem}", file=sys.stderr)
            return 2
    unit = L.unit_id(getattr(args, "unit", None)) if getattr(args, "unit", None) else None

    if args.cmd == "check":
        res = check(prj, unit, args.agent, args.cycle, args.human_override)
        head = "READY" if res["ready"] else "NOT READY"
        print(f"[pipeline_step] check {unit} {args.agent} c{res['cycle']}: {head}")
        for p in res["problems"]:
            print(f"  ✗ {p}")
        for n in res["notes"]:
            print(f"  · {n}")
        if args.json:
            L.write_json(L.at_root(root, args.json), res)
        return 0 if res["ready"] else 1

    if args.cmd == "done":
        before = L.at_root(root, args.before)
        code, msgs = done(prj, unit, args.agent, args.tier, args.cycle, before)
        label = {EXIT_OK: "OK", EXIT_REDISPATCH: "RE-DISPATCH", EXIT_PAUSE: "PAUSE (R4)",
                 EXIT_CONTRACT: "CONTRACT VIOLATION"}[code]
        print(f"[pipeline_step] done {unit} {args.agent}: {label}")
        for m in msgs:
            print(f"  {m}")
        return code

    if args.cmd == "clean":
        if not (prj.drafts(unit) / "humanized.md").exists():
            print(f"[pipeline_step] no drafts/{unit}/humanized.md", file=sys.stderr)
            return 2
        print(f"[pipeline_step] clean → {_rel(clean(prj, unit), root)}")
        return 0

    if args.cmd == "snapshot":
        code, msgs = snapshot(prj, unit, args.reason, args.target)
        print(f"[pipeline_step] snapshot {unit}: {'OK' if code == 0 else 'REFUSED'}")
        for m in msgs:
            print(f"  {m}")
        return code

    if args.cmd == "checks":
        try:
            code, res = checks(prj, unit)
        except FileNotFoundError as exc:
            print(f"[pipeline_step] checks: missing {exc}", file=sys.stderr)
            return 2
        print(f"[pipeline_step] checks {unit} → drafts/{unit}/checks.json + checks.md")
        for e in res["errors"]:
            print(f"  ERROR {e['tool']}: {e['error']}")
        for f in res["blocking"]:
            print(f"  BLOCKING {f['code']} {f['subject']}: {f['detail']}")
        if code == 3:
            print("  R4/R1: the unit pauses — run references/character-questionnaire.md "
                  "with the human before the Critic.")
        return code

    if args.cmd == "ready":
        res = ready(prj)
        print(f"[pipeline_step] ready ({prj.profile or 'no profile'}): "
              f"{'YES' if res['ready'] else 'NO'}")
        for b in res["blockers"]:
            print(f"  ✗ {b}")
        for n in res["notes"]:
            print(f"  · {n}")
        if not res["ready"] and prj.literary:
            print("  → R3: drafting waits. Run references/character-questionnaire.md for "
                  "what is missing (short answers are fine; empty ones are not).")
        if args.json:
            L.write_json(L.at_root(root, args.json), res)
        return 0 if res["ready"] else 1

    if args.cmd == "apply-edits":
        path = L.at_root(root, args.edits)
        if not path.exists():
            print(f"[pipeline_step] no such file: {path}", file=sys.stderr)
            return 2
        code, msgs = apply_edits(prj, path, args.dry_run)
        for m in msgs:
            print(f"[pipeline_step] {m}" if m is msgs[0] else f"  {m}")
        return code

    if args.cmd == "approve":
        code, msgs = approve(prj, unit, args.force)
        print(f"[pipeline_step] approve {unit}: {'OK' if code == 0 else 'REFUSED'}")
        for m in msgs:
            print(f"  {m}")
        return code

    if args.cmd == "sign":
        code, msgs = sign(prj, args.slug, args.by)
        print(f"[pipeline_step] sign {args.slug}: {'OK' if code == 0 else 'REFUSED'}")
        for m in msgs:
            print(f"  {m}")
        return code
    return 2


if __name__ == "__main__":
    sys.exit(main())
