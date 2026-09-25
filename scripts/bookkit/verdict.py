"""verdict — the Critic's verdict, recomputed from the scorecard.

`references/rubric.md` § Verdict computation is the only description of the
rule; this module is its only implementation. `pipeline_step.py done unit-NN
critic` and `check unit-NN proofreader` call `check()`: a `critique.md` header
that disagrees with the rows, or a scorecard with no rows, is a contract
violation — the rows are the truth, the header is a render.

    from bookkit import verdict as V
    res = V.check(root / "drafts/unit-03/scorecard.yaml",
                  root / "drafts/unit-03/critique.md", tolerance="full")
    res["computed"]  # {"verdict": "REVISE", "target": "Writer", "basis": "..."}
    res["problems"]  # [] when the Critic's header matches
"""

from __future__ import annotations

import re
from pathlib import Path

from . import lexicon as L

SEVERITIES = ("critical", "significant", "minor")
STATUSES = ("pass", "fail", "not_applicable")
TARGETS = ("Writer", "Editor", "Humanizer", "escalate")
_RANK = {s: i for i, s in enumerate(SEVERITIES)}
_HEADER = {
    "verdict": re.compile(r"^##\s*Verdict:\s*\**\s*([A-Za-z][A-Za-z-]*)", re.M),
    "target": re.compile(r"^##\s*Loopback target:\s*\**\s*([A-Za-z_]+)", re.M),
}


def tolerance(meta: dict) -> str:
    """`full` for book-literary and nonfiction `full` mode; `fast` otherwise."""
    if L.profile_of(meta) == "book-literary":
        return "full"
    return "full" if str(L.meta_get(meta, "pipeline.mode", "fast")) == "full" else "fast"


def _target(value) -> str | None:
    s = str(value or "").strip()
    for t in TARGETS:
        if s.lower() == t.lower():
            return t
    return None


def validate(items) -> list[str]:
    """Problems with the rows themselves (schema: references/rubric.md)."""
    if not isinstance(items, list) or not items:
        return ["scorecard.yaml has no `items` — a verdict needs rows"]
    out = []
    for i, it in enumerate(items, 1):
        if not isinstance(it, dict):
            out.append(f"item {i}: not a mapping")
            continue
        rid = it.get("id") or f"#{i}"
        if str(it.get("severity")) not in SEVERITIES:
            out.append(f"{rid}: severity {it.get('severity')!r} is not "
                       f"{' | '.join(SEVERITIES)}")
        if str(it.get("status")) not in STATUSES:
            out.append(f"{rid}: status {it.get('status')!r} is not {' | '.join(STATUSES)}")
        if it.get("status") == "fail" and _target(it.get("loopback_target")) is None:
            out.append(f"{rid}: a failing row needs loopback_target "
                       f"{' | '.join(TARGETS)} (got {it.get('loopback_target')!r})")
    return out


def compute(items: list[dict], tol: str) -> dict:
    """references/rubric.md § Verdict computation, and the REVISE target rules."""
    fails = [it for it in items if isinstance(it, dict) and it.get("status") == "fail"]
    n = {s: sum(1 for it in fails if it.get("severity") == s) for s in SEVERITIES}
    ids = lambda sev: ", ".join(str(it.get("id")) for it in fails  # noqa: E731
                                if it.get("severity") == sev)
    if any(_target(it.get("loopback_target")) == "escalate" for it in fails):
        esc = ", ".join(str(it.get("id")) for it in fails
                        if _target(it.get("loopback_target")) == "escalate")
        return {"verdict": "ESCALATE", "target": "escalate", "counts": n,
                "basis": f"a failing row targets escalate ({esc}) → ESCALATE"}
    if n["critical"] >= 2:
        return {"verdict": "REWORK", "target": "Writer", "counts": n,
                "basis": f">=2 critical fails ({ids('critical')}) → REWORK"}
    if n["critical"] == 1:
        verdict, basis = "REVISE", f"1 critical fail ({ids('critical')}) → REVISE"
    elif n["significant"] >= 1:
        verdict, basis = "REVISE", f">=1 significant fail ({ids('significant')}) → REVISE"
    elif n["minor"] >= 3 and tol == "full":
        verdict, basis = "REVISE", f">=3 minor fails with tolerance full ({ids('minor')}) → REVISE"
    elif n["minor"]:
        return {"verdict": "PASS", "target": "none", "counts": n,
                "basis": f"minor fails only ({ids('minor')}) → PASS, with notes"}
    else:
        return {"verdict": "PASS", "target": "none", "counts": n, "basis": "no fails → PASS"}
    targets = {_target(it.get("loopback_target")) for it in fails}
    if len(targets) == 1:
        target = targets.pop()
    else:
        top = min(_RANK.get(str(it.get("severity")), 9) for it in fails)
        tops = {_target(it.get("loopback_target")) for it in fails
                if _RANK.get(str(it.get("severity")), 9) == top}
        target = tops.pop() if len(tops) == 1 else "Writer"
    return {"verdict": verdict, "target": target, "counts": n, "basis": basis}


def header(text: str) -> dict:
    """`## Verdict:` and `## Loopback target:` of a critique.md (None when absent)."""
    out = {}
    for key, rx in _HEADER.items():
        m = rx.search(text)
        out[key] = m.group(1) if m else None
    return out


def check(scorecard: Path, critique: Path | None, tolerance: str) -> dict:
    """Recompute the verdict and compare it with the Critic's header and cache."""
    problems: list[str] = []
    if not Path(scorecard).exists():
        return {"computed": None, "problems": ["scorecard.yaml is missing"], "notes": []}
    try:
        data = L.read_yaml(scorecard)
    except ValueError as exc:
        return {"computed": None, "problems": [str(exc)], "notes": []}
    if not isinstance(data, dict):
        return {"computed": None, "problems": [f"{Path(scorecard).name}: not a YAML mapping"],
                "notes": []}
    items = data.get("items")
    problems += validate(items)
    if problems:
        return {"computed": None, "problems": problems, "notes": []}
    comp = compute(items, tolerance)
    notes = []
    if data.get("tolerance") and str(data.get("tolerance")) != tolerance:
        notes.append(f"scorecard says tolerance {data.get('tolerance')!r}; the project's is "
                     f"{tolerance!r} (used)")
    cache = str(data.get("computed_verdict") or "").strip().upper()
    if cache and cache != comp["verdict"]:
        problems.append(f"scorecard.yaml computed_verdict {cache} disagrees with its rows "
                        f"({comp['basis']})")
    if critique is not None:
        if not Path(critique).exists():
            problems.append("critique.md is missing")
        else:
            h = header(L.read_text(critique))
            if h["verdict"] is None:
                problems.append("critique.md has no `## Verdict:` line")
            elif h["verdict"].upper() != comp["verdict"]:
                problems.append(f"critique.md says `## Verdict: {h['verdict']}`; the rows "
                                f"compute {comp['verdict']} ({comp['basis']})")
            want = comp["target"]
            got = (h["target"] or "").strip()
            if h["target"] is None:
                problems.append("critique.md has no `## Loopback target:` line")
            elif got.lower() != want.lower():
                problems.append(f"critique.md says `## Loopback target: {got}`; the rows "
                                f"resolve to {want} (references/rubric.md § REVISE target)")
    return {"computed": comp, "problems": problems, "notes": notes}
