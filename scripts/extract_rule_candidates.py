#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""extract_rule_candidates.py — pair every stated rule with every instance of it (MG-2).

The unit of analysis is the rule: one file per rule, holding the rule and EVERY
code block and example across the book its scope could reach, so the auditor
(references/agents/rule-auditor.md) judges them together. This script decides
nothing; it retrieves.

"Rule-shaped" = strong modality, or a universal quantifier plus a breaking verb
("any function on a loaded field breaks it") — PLUS a technical token. The token
separates a rule about the system from the book's voice. The word lists come from
the language pack (`scripts/lexicons/<lang>.yaml`: `modality`, `universal`,
`breaks`). With no pack for the book's language the extractor falls back to a
language-agnostic pairing: prose paragraphs naming a backticked identifier ↔ code
blocks using it — and says so, rather than reporting "0 rules" as a clean book.

Rule ids are content-derived (`<unit>-<term>-<hash6>`), so inserting lines above
a rule no longer orphans `bible/rule-probes-tuned.yaml` or the manifest.

Usage
  python scripts/extract_rule_candidates.py --out reviews/.../rules
  python scripts/extract_rule_candidates.py --report        # table only, writes nothing
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from bookkit.coverage import (  # noqa: E402
    CoverageRecord, Subject, add_coverage_args, composite_fingerprint,
    load_manifest, partition,
)
from bookkit.gitblame import blame_map, in_fix_run, is_repo  # noqa: E402
from bookkit.lexicon import compile_any, load as load_lexicon  # noqa: E402
from bookkit.project import Project, add_common_args, as_list, load_project  # noqa: E402
from bookkit.selection import Selection, stratified_top  # noqa: E402
from bookkit.segment import Record, code_blocks, paragraphs, prev_prose, segment  # noqa: E402
from bookkit.textmetrics import fingerprint, fingerprint_code  # noqa: E402

# A technical token: a code span, an ALL_CAPS identifier, or `name()`.
RX_CODE_SPAN = re.compile(r"`([^`]+)`")
RX_IDENTIFIER = re.compile(r"\b([A-Z][A-Z0-9_]{2,}|[A-Za-z_]\w*\(\))")
# A code span that DEMONSTRATES a construct (`{<Date={'2024'}>}`) rather than
# naming it: key on the identifiers inside the shape.
RX_SYNTACTIC = re.compile(r"[{}\[\]<>|$=]|::|->|=>")
RX_CALL = re.compile(r"^([A-Za-z_]\w*)\s*\(")
RX_EXAMPLE_HEADING = re.compile(
    r"\b(Examples?|Exercises?|Practice|Walkthrough|Recipe|Pattern|"
    r"Ejemplos?|Ejercicios?|Pr[aá]ctica|Receta|Patr[oó]n)\b", re.I)
NOISE_TOKENS = {"the", "and", "for", "not", "with", "from", "this", "that"}

# More instances than this cannot be judged in one agent run: the file ships
# flagged `tractable: false` and the audit is a SAMPLE. It is a debt, closed by
# narrowing in bible/rule-probes-tuned.yaml. Why: docs/rationale/gate.md#depth.
TRACTABLE_MAX_INSTANCES = 40

# Each failure mode gets its own quota; one ranking starves the rarer mode.
# Why: docs/rationale/gate.md#strata.
RULE_QUOTA_WEIGHTS = {"cross-unit": 1.0, "intra-unit": 1.0}


class RuleShape:
    """Rule-shaped test built from a language pack."""

    def __init__(self, lex: dict):
        self.modality = compile_any(lex.get("modality") or [], regex=True)
        self.universal = compile_any(lex.get("universal") or [], regex=True)
        self.breaks = compile_any(lex.get("breaks") or [], regex=True)
        requested, got = lex.get("_requested"), lex.get("_language")
        self.pack = got if (got == requested and self.modality) else None

    def __call__(self, text: str) -> bool:
        if self.modality and self.modality.search(text):
            return True
        return bool(self.universal and self.breaks
                    and self.universal.search(text) and self.breaks.search(text))


@dataclass
class Rule:
    rule_id: str
    unit: str
    path: str
    line: int
    text: str
    heading_path: str
    key_terms: list[str] = field(default_factory=list)
    blame_commit: str = ""
    in_fix_run: bool = False
    instances: list["Instance"] = field(default_factory=list)
    tuned: bool = False

    @property
    def loc(self) -> str:
        return f"{self.path}:{self.line}"


@dataclass
class Instance:
    kind: str          # code | example
    unit: str
    path: str
    line: int
    end_line: int
    heading_path: str
    text: str
    caption: str = ""
    matched_terms: list[str] = field(default_factory=list)
    blame_commit: str = ""
    in_fix_run: bool = False

    @property
    def loc(self) -> str:
        return (f"{self.path}:{self.line}-{self.end_line}"
                if self.end_line > self.line else f"{self.path}:{self.line}")

    @property
    def fp(self) -> str:
        return fingerprint_code(self.text) if self.kind == "code" else fingerprint(self.text)


def technical_tokens(text: str, spans_only: bool = False) -> list[str]:
    """Tokens that make a rule-shaped sentence a rule about the system.

    Each code span is reduced to something an instance can be MATCHED on:
    `Upper(Name)` → `Upper`; a syntactic shape → the identifiers inside it.
    """
    out: list[str] = []
    for raw in RX_CODE_SPAN.findall(text):
        span = raw.strip()
        call = RX_CALL.match(span)
        if call:
            out.append(call.group(1))
            continue
        if RX_SYNTACTIC.search(span):
            out += [w for w in re.findall(r"[A-Za-z_]\w{2,}", span)
                    if w.lower() not in NOISE_TOKENS]
            continue
        out.append((span.split()[0] if " " in span else span).strip("().,;:`"))
    if not spans_only:
        out += [m.group(1) for m in RX_IDENTIFIER.finditer(RX_CODE_SPAN.sub(" ", text))]
    cleaned = [t.strip("().,;:`") for t in out]
    seen: set[str] = set()
    return [t for t in cleaned
            if len(t) >= 3 and t.lower() not in NOISE_TOKENS
            and not (t.lower() in seen or seen.add(t.lower()))]


def rule_id(unit: str, text: str, terms: list[str]) -> str:
    """Content-derived: survives lines inserted above the rule."""
    head = re.sub(r"[^\w]+", "-", (terms[0] if terms else "rule").lower()).strip("-")[:40]
    return f"{unit}-{head}-{fingerprint(text)[:6]}"


def _example_heading(heading_path: str) -> bool:
    """Under an example/exercise heading — ignoring the chapter title (H1), whose
    "Design Patterns for Caching" would otherwise make every paragraph an example."""
    parts = [p for p in heading_path.split(" › ") if p]
    return any(RX_EXAMPLE_HEADING.search(p) for p in (parts[1:] if len(parts) > 1 else parts))


def find_rules(project: Project, records: dict[str, tuple[str, list[Record]]],
               use_blame: bool, shape: RuleShape) -> list[Rule]:
    agnostic = shape.pack is None
    rules: list[Rule] = []
    ids: dict[str, int] = {}
    for unit, (rel, recs) in records.items():
        blame = blame_map(project.root, rel, use_blame)
        for r in recs:
            if r.kind not in ("para", "bullet"):
                continue
            if not agnostic and not shape(r.text):
                continue
            terms = technical_tokens(r.text, spans_only=agnostic)
            if not terms:
                continue  # modality without a technical token is voice
            rid = rule_id(unit, r.text, terms)
            ids[rid] = ids.get(rid, 0) + 1
            if ids[rid] > 1:
                rid = f"{rid}-{ids[rid]}"
            rules.append(Rule(rule_id=rid, unit=unit, path=rel, line=r.line, text=r.text,
                              heading_path=r.heading_path, key_terms=terms,
                              blame_commit=blame.get(r.line, ("", ""))[0]))
    return rules


def find_instances(project: Project, records: dict[str, tuple[str, list[Record]]],
                   use_blame: bool) -> list[Instance]:
    """Every code block and every example passage in the book, once."""
    out: list[Instance] = []
    for unit, (rel, recs) in records.items():
        by_line = {r.line: r for r in recs}
        blame = blame_map(project.root, rel, use_blame)
        for start, end, _lang, body in code_blocks(recs):
            caption = prev_prose(by_line, start)
            heading = by_line[start].heading_path if start in by_line else ""
            out.append(Instance("code", unit, rel, start, end, heading, body,
                                caption=caption.text if caption else "",
                                blame_commit=blame.get(start, ("", ""))[0]))
        for r in recs:
            if r.kind in ("para", "bullet", "table") and _example_heading(r.heading_path):
                out.append(Instance("example", unit, rel, r.line, r.line, r.heading_path,
                                    r.text, blame_commit=blame.get(r.line, ("", ""))[0]))
    return out


def _pat(term: str, flags: int = 0) -> re.Pattern:
    return re.compile(rf"(?<![\w]){re.escape(term)}(?![\w])", flags)


def term_document_frequency(rules: list[Rule], instances: list[Instance]) -> dict[str, int]:
    """How many instances mention each candidate term. A term that appears
    everywhere (the running example's field names) discriminates nothing."""
    df: dict[str, int] = {}
    pats = {t: _pat(t, re.I) for t in {t.lower() for r in rules for t in r.key_terms}}
    for inst in instances:
        hay = f"{inst.text}\n{inst.caption}"
        for t, p in pats.items():
            if p.search(hay):
                df[t] = df.get(t, 0) + 1
    return df


def attach_instances(rules: list[Rule], instances: list[Instance], fix_run: set[str],
                     df: dict[str, int], df_ceiling_ratio: float = 0.15) -> int:
    """An instance belongs to a rule when it uses one of the rule's rarest (≤3)
    DISCRIMINATING key terms. Over-includes on purpose: `OUT_OF_SCOPE` throws
    extras back cheaply; a missed instance ships. Returns rules dropped for
    having no discriminating term."""
    ceiling = max(3, min(int(len(instances) * df_ceiling_ratio), TRACTABLE_MAX_INSTANCES))
    dropped = 0
    for r in rules:
        r.in_fix_run = in_fix_run(r.blame_commit, fix_run)
        keep = sorted((t for t in r.key_terms if df.get(t.lower(), 0) <= ceiling),
                      key=lambda t: (df.get(t.lower(), 0), t))[:3]
        if not keep:
            dropped += 1
            r.key_terms = []
            continue
        r.key_terms = keep
        r.instances = _rematch(r, keep, instances, {}, fix_run)
    return dropped


# ---------------------------------------------------------------------------
# Tuned rule probes — narrowing, the ladder out of `tractable: false`
# ---------------------------------------------------------------------------


def load_rule_overrides(project: Project) -> dict[str, dict]:
    doc = project.load_yaml("bible/rule-probes-tuned.yaml")
    return {str(e["id"]): e for e in as_list(doc.get("rules"))
            if isinstance(e, dict) and e.get("id")}


def _rematch(rule: Rule, terms: list[str], instances: list[Instance],
             spec: dict, fix_run: set[str]) -> list[Instance]:
    """Attach instances to one rule under its terms and an optional narrowing.
    Every list field goes through `as_list`: `scope_units: ch-03` is one unit."""
    pats = [_pat(str(t)) for t in terms]
    req = [_pat(str(t)) for t in as_list(spec.get("require_terms"))]
    units = {str(u) for u in as_list(spec.get("scope_units"))}
    heading = str(spec.get("scope_heading") or "")
    try:
        excl = re.compile(spec["exclude_pattern"]) if spec.get("exclude_pattern") else None
    except re.error as exc:
        print(f"[rules] BAD exclude_pattern on {rule.rule_id}: {exc}")
        excl = None
    out: list[Instance] = []
    for inst in instances:
        if inst.path == rule.path and inst.line == rule.line:
            continue
        if (units and inst.unit not in units) or (heading and heading not in inst.heading_path):
            continue
        hay = f"{inst.text}\n{inst.caption}"
        if excl and excl.search(hay):
            continue
        hit = [str(t) for t, p in zip(terms, pats) if p.search(hay)]
        if not hit or (req and not all(p.search(hay) for p in req)):
            continue
        copy = Instance(**{**inst.__dict__, "matched_terms": hit})
        copy.in_fix_run = in_fix_run(inst.blame_commit, fix_run)
        out.append(copy)
    return out


def apply_rule_overrides(rules: list[Rule], instances: list[Instance],
                         overrides: dict[str, dict],
                         fix_run: set[str]) -> tuple[list[Rule], list[str]]:
    """Apply hand-written narrowings. Returns (rules, notes)."""
    if not overrides:
        return rules, []
    by_id = {r.rule_id: r for r in rules}
    # Loud: a typo silently does nothing and the human believes a rule was closed.
    notes = [f"tuned probe for unknown rule id `{u}` — no such candidate (ids are "
             f"content-derived; check round-N/rules/_index.md)"
             for u in sorted(set(overrides) - set(by_id))]
    out: list[Rule] = []
    for rule in rules:
        spec = overrides.get(rule.rule_id)
        if not spec:
            out.append(rule)
            continue
        splits = [p for p in as_list(spec.get("split")) if isinstance(p, dict)]
        if splits:
            for part in splits:
                suffix = re.sub(r"[^\w-]+", "-", str(part.get("suffix") or "part")).strip("-")
                sub = Rule(rule_id=f"{rule.rule_id}--{suffix}", unit=rule.unit,
                           path=rule.path, line=rule.line, text=rule.text,
                           heading_path=rule.heading_path,
                           key_terms=[str(t) for t in (as_list(part.get("key_terms"))
                                                       or rule.key_terms)],
                           blame_commit=rule.blame_commit, in_fix_run=rule.in_fix_run,
                           tuned=True)
                sub.instances = _rematch(sub, sub.key_terms, instances, part, fix_run)
                notes.append(f"{rule.rule_id} split -> {sub.rule_id}: "
                             f"{len(sub.instances)} instance(s)")
                out.append(sub)
            continue
        before = len(rule.instances)
        rule.key_terms = [str(t) for t in (as_list(spec.get("key_terms")) or rule.key_terms)]
        rule.instances = _rematch(rule, rule.key_terms, instances, spec, fix_run)
        rule.tuned = True
        notes.append(f"{rule.rule_id} narrowed: {before} -> {len(rule.instances)} instance(s)"
                     + ("  [still over the ceiling]"
                        if len(rule.instances) > TRACTABLE_MAX_INSTANCES else "  [tractable]"))
        out.append(rule)
    return out, notes


def propose_rule_probes(rules: list[Rule], out_path: Path) -> int:
    """Write the ranked worklist of rules that can only be SAMPLED."""
    over = sorted((r for r in rules if len(r.instances) > TRACTABLE_MAX_INSTANCES),
                  key=lambda r: (-len(r.instances), r.rule_id))
    L = ["# rule-probes-proposed.yaml — GENERATED WORKLIST, not configuration.",
         f"# {len(over)} rule(s) have more than {TRACTABLE_MAX_INSTANCES} instances and can "
         f"only be SAMPLED (they keep MG-2 at PASS-PARTIAL).",
         "# Copy an entry into bible/rule-probes-tuned.yaml and uncomment ONE narrowing.",
         "# Narrowing is a claim about the rule's SCOPE — if it really reaches all these",
         "# instances, leave it sampled and waive coverage instead. See",
         "# templates/rule-probes-tuned.yaml.", "", "rules:"]
    for r in over:
        units = sorted({i.unit for i in r.instances})
        L += [f"  # {len(r.instances)} instances · terms: {', '.join(r.key_terms)} · "
              f"units: {', '.join(units[:8])}{' …' if len(units) > 8 else ''}",
              f"  # rule at {r.loc} — {r.heading_path}",
              f"  # - id: {r.rule_id}",
              f"  #   key_terms: [{r.key_terms[0] if r.key_terms else ''}]",
              "  #   require_terms: []", "  #   scope_units: []", '  #   note: ""', ""]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(L) + "\n", encoding="utf-8")
    return len(over)


def rule_stratum(rule: Rule) -> str:
    return "cross-unit" if {i.unit for i in rule.instances} - {rule.unit} else "intra-unit"


def rule_rank(rule: Rule) -> tuple:
    """Judgeable first, then reach, then fewer instances, then id (stable)."""
    return (len(rule.instances) > TRACTABLE_MAX_INSTANCES,
            -len({i.unit for i in rule.instances} - {rule.unit}),
            len(rule.instances), rule.rule_id)


def rule_subject(rule: Rule) -> Subject:
    """What an audit of the rule read: the sentence AND every instance shown."""
    shown = sorted(rule.instances, key=lambda i: (i.path, i.line))[:TRACTABLE_MAX_INSTANCES]
    return Subject(id=rule.rule_id,
                   hash=composite_fingerprint([fingerprint(rule.text)] + [i.fp for i in shown]),
                   stratum=rule_stratum(rule), instances=len(rule.instances),
                   sampled=len(rule.instances) > TRACTABLE_MAX_INSTANCES, site=rule.loc)


def select_rules(rules: list[Rule], quota: int) -> Selection:
    """THE selection. Emission and every check on emission call this one function."""
    return stratified_top(rules, rule_stratum, rule_rank, quota, RULE_QUOTA_WEIGHTS)


def emit_rule_file(rule: Rule) -> str:
    tractable = len(rule.instances) <= TRACTABLE_MAX_INSTANCES
    cross_unit = sorted({i.unit for i in rule.instances} - {rule.unit})
    d2 = [i.loc for i in rule.instances if rule.in_fix_run and not i.in_fix_run][:10]
    L = ["---", f"rule_id: {rule.rule_id}", f"rule_site: {rule.loc}",
         f"home_unit: {rule.unit}", f"key_terms: [{', '.join(rule.key_terms)}]",
         f"instances_total: {len(rule.instances)}",
         f"instances_cross_unit: [{', '.join(cross_unit)}]",
         f"tractable: {'true' if tractable else 'false'}"]
    if not tractable:
        L.append(f"# more than {TRACTABLE_MAX_INSTANCES} instances — the list below is a "
                 f"SAMPLE. Set sampled:true in your findings and do not report the rule clean.")
    if d2:
        L.append("d2_candidates:   # rule touched in a fix run, these instances were not")
        L += [f"  - {loc}" for loc in d2]
    L += ["---", "", "## The rule", "", f"`{rule.loc}` — {rule.heading_path}", "",
          f"> {rule.text}", "",
          "**State this rule in your own words before judging anything**: what it forbids "
          "or requires, and over what scope. If you cannot state the scope, say so and stop.",
          "", "## Instances", ""]
    if not rule.instances:
        L += ["_No instance uses this rule's key terms: the rule is stated and never "
              "exercised, or the key terms are wrong._", ""]
        return "\n".join(L)
    for inst in sorted(rule.instances[:TRACTABLE_MAX_INSTANCES], key=lambda i: (i.path, i.line)):
        flags = [inst.kind] + (["CROSS-UNIT"] if inst.unit != rule.unit else []) + (
            ["D2"] if rule.in_fix_run and not inst.in_fix_run else [])
        L.append(f"### {inst.loc}  [{' '.join(flags)}]  [matched: {', '.join(inst.matched_terms)}]")
        L += [f"> {inst.heading_path}", ""]
        if inst.caption:
            L += [f"*(caption)* {inst.caption}", ""]
        L += (["````", inst.text[:2000], "````", ""] if inst.kind == "code" else [inst.text, ""])
    L += ["", "For each instance: `COMPLIES` (N1) · `VIOLATES` (D6) · `OMITS` (D9) · "
              "`DECLARED_EXCEPTION` (N2) · `OUT_OF_SCOPE` (N2, state both scopes)."]
    return "\n".join(L)


def load_records(project: Project) -> dict[str, tuple[str, list[Record]]]:
    """Units in reading order (natural sort), as logical paragraphs."""
    records: dict[str, tuple[str, list[Record]]] = {}
    for path in project.unit_paths:
        rel = project.rel(path)
        recs = segment(path, rel_to=project.root)
        for r in recs:
            r.path = rel
        records[path.stem] = (rel, paragraphs(recs))
    return records


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Extract rule candidates and their instances.")
    add_common_args(ap)
    ap.add_argument("--out", default=None, help="Output dir for rule files.")
    ap.add_argument("--report", action="store_true",
                    help="Print the candidate table only. Writes NO files (not even "
                         "--coverage or --propose-probes).")
    ap.add_argument("--min-instances", type=int, default=2,
                    help="Skip rules with fewer instances (default 2) — a rule with one "
                         "instance is the unit's own example, which the Critic saw. Rules "
                         "narrowed in bible/rule-probes-tuned.yaml are always kept.")
    ap.add_argument("--top", type=int, default=0,
                    help="Emit only the top N rules (0 = all). The cost dial; what is cut "
                         "is reported.")
    ap.add_argument("--no-blame", action="store_true")
    ap.add_argument("--fix-run-commit", action="append", default=[])
    ap.add_argument("--df-ceiling", type=float, default=0.15,
                    help="Ignore key terms in more than this fraction of instances "
                         "(default 0.15).")
    ap.add_argument("--round", type=int, default=1, help="Round number, for the record.")
    ap.add_argument("--propose-probes", metavar="PATH", default=None,
                    help="Write the ranked worklist of rules that can only be SAMPLED.")
    add_coverage_args(ap)
    args = ap.parse_args(argv)

    project = load_project(args.root, args.units)
    audit = project.load_yaml("bible/audit-config.yaml")
    fix_run = {str(c) for c in as_list(audit.get("fix_run_commits"))}
    fix_run |= {c.strip() for c in args.fix_run_commit if c.strip()}
    use_blame = (not args.no_blame) and is_repo(project.root)

    lex = load_lexicon(project.language_variant, project.root)
    shape = RuleShape(lex)
    mode = "lexicon" if shape.pack else "language-agnostic"
    if not shape.pack:
        print(f"[rules] no language pack for `{project.language}` — using the "
              f"language-agnostic pairing (prose naming a backticked identifier ↔ code "
              f"using it). Add scripts/lexicons/{project.language}.yaml for rule shapes.")

    records = load_records(project)
    rules = find_rules(project, records, use_blame, shape)
    instances = find_instances(project, records, use_blame)
    dropped = attach_instances(rules, instances, fix_run,
                               term_document_frequency(rules, instances), args.df_ceiling)
    rules, tuned_notes = apply_rule_overrides(rules, instances,
                                              load_rule_overrides(project), fix_run)
    for note in tuned_notes:
        print(f"[rules] tuned: {note}")

    # ELIGIBLE = post-filter. A hand-narrowed rule stays eligible whatever its
    # instance count: narrowing is a claim about scope, never a way to make a
    # subject vanish from the denominator.
    kept = [r for r in rules if r.tuned or len(r.instances) >= args.min_instances]
    subjects = {r.rule_id: rule_subject(r) for r in kept}
    manifest = load_manifest(args.subjects).get("MG-2", {})
    pool_subjects, already, requeued = partition(list(subjects.values()), manifest)
    pool_ids = {s.id for s in pool_subjects}
    selection = select_rules([r for r in kept if r.rule_id in pool_ids], args.top)

    print(f"[rules] {len(rules)} rule candidate(s), {len(instances)} instance(s) in "
          f"{len(records)} unit(s); {len(kept)} eligible ({mode})")
    if already or requeued:
        print(f"[rules] manifest: {len(already)} already audited at their current text "
              f"(skipped, still counted), {len(requeued)} re-queued (edited since).")
    for line in selection.report_lines("rule"):
        print(f"[rules] {line}")
    if dropped:
        print(f"[rules] {dropped} rule(s) dropped — every key term appears in more than "
              f"{args.df_ceiling:.0%} of instances. Give them a hand-written probe.")

    if args.report or not args.out:
        print(f"\n{'rule_id':44} {'inst':>5} {'x-unit':>7} {'mode':11} site")
        print("-" * 108)
        for r in selection.emitted[:60]:
            print(f"{r.rule_id:44} {len(r.instances):>5} "
                  f"{len({i.unit for i in r.instances} - {r.unit}):>7} "
                  f"{rule_stratum(r):11} {r.loc}")
        if args.report:
            return 0

    if args.coverage:
        for r in selection.emitted:
            subjects[r.rule_id].stratum, subjects[r.rule_id].rank = selection.rank_of(r)
        rec = CoverageRecord(
            check="MG-2", round=args.round, language=project.language, pack=shape.pack,
            mode=mode, eligible=list(subjects.values()),
            emitted=[r.rule_id for r in selection.emitted],
            already_audited=already, requeued=requeued,
            cut=[{"id": c.item.rule_id, "rank": c.rank, "stratum": c.stratum,
                  "instances": len(c.item.instances), "site": c.item.loc}
                 for c in selection.cut])
        if not kept and not shape.pack:
            rec.blocked = (f"no language pack for `{project.language}` and the "
                           f"language-agnostic pairing found no rule candidate")
        elif not kept:
            rec.notes.append("zero eligible rules: full coverage of an empty set, or a "
                             "mis-tuned extractor — read the extractor's own report")
        rec.write(args.coverage)
        print(f"[rules] {rec.report_line('rule')} → {args.coverage}")

    if args.propose_probes:
        n_over = propose_rule_probes(kept, Path(args.propose_probes))
        if n_over:
            print(f"[rules] {n_over} rule(s) can only be SAMPLED (> {TRACTABLE_MAX_INSTANCES} "
                  f"instances). Ranked worklist → {args.propose_probes}")

    if not args.out:
        return 0
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    for r in selection.emitted:
        (out_dir / f"{r.rule_id}.md").write_text(emit_rule_file(r), encoding="utf-8")
    cut = selection.dropped_total
    idx = ["# Rule candidate index", "",
           f"Ranked judgeable-first. Rules with more than {TRACTABLE_MAX_INSTANCES} instances "
           f"can only be SAMPLED and may never be reported clean.", ""]
    if already:
        idx += [f"> {len(already)} rule(s) already audited at their current text are not "
                f"listed; they still count. {len(requeued)} came back because their text "
                f"was edited.", ""]
    if cut:
        idx += [f"> **{cut} rule(s) below the cut were not emitted** (`--top {args.top}`) — "
                f"{cut / max(len(kept), 1):.0%} of the eligible surface waits for a later "
                f"round.", ""]
    idx += ["| Rule | Site | Instances | Cross-unit | Tractable |", "|---|---|---:|---:|---|"]
    idx += [f"| [{r.rule_id}]({r.rule_id}.md) | `{r.loc}` | {len(r.instances)} | "
            f"{len({i.unit for i in r.instances} - {r.unit})} | "
            f"{'yes' if len(r.instances) <= TRACTABLE_MAX_INSTANCES else 'NO — sample'} |"
            for r in selection.emitted]
    (out_dir / "_index.md").write_text("\n".join(idx) + "\n", encoding="utf-8")
    print(f"[rules] {len(selection.emitted)} rule file(s) → {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
