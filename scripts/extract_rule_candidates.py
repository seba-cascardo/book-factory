#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""extract_rule_candidates.py — pair every stated rule with every instance of it.

## Why the unit of analysis is the rule

Measured on the reference case: seven of ten intra-unit defects were the same
gesture — the unit states a rule in prose and violates it in its own example,
code block or bullet, a few lines later. Nothing in the per-unit pipeline crosses
the prose layer against the code layer, so this defect walked through every gate.

Auditing instance by instance reproduces that blindness in miniature. So this
extracts one file per rule, containing the rule and EVERY instance across the
whole book that its scope could reach, and the agent judges them together.

## What this does and does not decide

It decides nothing. It is a retrieval step: it finds rule-shaped passages and
candidate instances and puts them in one file. Whether an instance actually
violates the rule is a judgement that needs to read the surrounding section, and
that is `references/agents/rule-auditor.md`'s job.

The heuristic for "rule-shaped" is deliberately simple: strong modality PLUS at
least one technical token. That second condition is what separates voice from a
rule. "Never overthink it" is register; "Never use `CONCATENATE` on an optimized
load" is a rule about the system. Modality alone would flood the output with the
book's voice, which is exactly what the voice contract tells auditors to ignore.

Usage
  python scripts/extract_rule_candidates.py --out reviews/.../rules
  python scripts/extract_rule_candidates.py --report        # candidate table only
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from bookkit.gitblame import blame_map, in_fix_run, is_repo  # noqa: E402
from bookkit.project import Project, add_common_args, load_project  # noqa: E402
from bookkit.selection import Selection, stratified_top  # noqa: E402
from bookkit.segment import (  # noqa: E402
    Record, code_blocks, paragraphs, prev_prose, segment,
)
from bookkit.textmetrics import content_terms, stopwords_for  # noqa: E402

# Strong modality. Deliberately narrower than the claim-scoring modality set in
# build_concept_dossier: a rule PRESCRIBES, it does not merely describe.
RX_MODALITY = re.compile(
    r"\b(must(?:\s+not)?|never|always|cannot|can't|do not|don't|should(?:\s+not)?|"
    r"only ever|only when|only if|has to|have to|required to|forbidden|avoid|"
    r"is not allowed|will not work|won't work|no exceptions)\b", re.I)

# Prohibitions stated as CONSEQUENCES rather than as modals.
#
# MEASURED: modality alone missed both halves of a known defect pair — "Any
# function call on a loaded field breaks it" and "…or any load-time composition
# breaks it". Both are rules; neither contains a modal verb. Technical prose
# states prohibitions descriptively far more often than prescriptively, so a
# modality-only extractor silently skips the rules most likely to be violated by
# the book's own examples.
#
# Requiring a universal quantifier AND a breaking verb in the same sentence keeps
# this from matching ordinary description ("the engine reads the file").
RX_UNIVERSAL = re.compile(r"\b(any|every|all|no|none of|nothing|each)\b", re.I)
RX_BREAKS = re.compile(
    r"\b(breaks?|disables?|defeats?|prevents?|invalidates?|forces?|kills?|"
    r"silently (?:drops?|ignores?|fails?)|falls? back|degrades?|discards?|"
    r"loses?|voids?|blocks?|refuses?)\b", re.I)


def is_rule_shaped(text: str) -> bool:
    """A prescription, or a prohibition stated as a consequence."""
    if RX_MODALITY.search(text):
        return True
    return bool(RX_UNIVERSAL.search(text) and RX_BREAKS.search(text))

# A technical token: an inline code span, an ALL_CAPS identifier, or a
# CamelCase/function-shaped word. Without one of these, a modal sentence is
# almost always the book's voice rather than a rule about the system.
RX_CODE_SPAN = re.compile(r"`([^`]+)`")
RX_IDENTIFIER = re.compile(r"\b([A-Z][A-Z0-9_]{2,}|[A-Za-z_]\w*\(\))")

# Syntactic evidence: a code span that DEMONSTRATES the construct instead of
# naming it.
#
# MEASURED: a rule fixing a date format inside a set modifier was written
# entirely out of field names and literals — `{<Date={'2024-01-01'}>}`. It names
# no keyword and no function, so an extractor requiring a named construct skipped
# it and the defect was invisible. A rule can show you the shape rather than call
# it by name, and in a book about a query language that is common, not exotic.
#
# So a code span carrying structural punctuation counts as a technical token in
# its own right, keyed on the span's shape rather than its vocabulary.
RX_SYNTACTIC = re.compile(r"[{}\[\]<>|$=]|::|->|=>")

RX_EXAMPLE_HEADING = re.compile(r"\b(Example|Examples|Exercise|Exercises|Practice|"
                                r"Walkthrough|Recipe|Pattern)\b", re.I)

# A rule with more instances than this cannot be judged exhaustively in one agent
# run. The file still ships, flagged `tractable: false`, and the auditor is told
# to report it as a sample. A sampled audit reported as complete is worse than no
# audit, so this flag is load-bearing.
TRACTABLE_MAX_INSTANCES = 40


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

    @property
    def loc(self) -> str:
        return f"{self.path}:{self.line}"


@dataclass
class Instance:
    kind: str          # code | example | prose
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


# A code span that is a call — `Upper(Name)`, `Date(OrderDate, 'YYYY-MM-DD')`.
# The term is the function, not the whole call: a rule about `Upper(Name)` is a
# rule about `Upper`, and matching on the full call finds only its verbatim
# repetitions. Missing this silently dropped every function-scoped rule, which in
# a technical book is the most common kind there is.
RX_CALL = re.compile(r"^([A-Za-z_]\w*)\s*\(")


NOISE_TOKENS = {"the", "and", "for", "not", "with", "from", "this", "that"}


def technical_tokens(text: str) -> list[str]:
    """Tokens that make a rule-shaped sentence a rule about the system.

    Each code span is reduced to something an instance can actually be MATCHED
    on. That last part is the whole job: a token like `{<OrderDate={'2024'}>}`
    is technically present but matches only its own verbatim repetition, so
    keeping it whole is the same as finding nothing.
    """
    out: list[str] = []

    for raw in RX_CODE_SPAN.findall(text):
        span = raw.strip()

        call = RX_CALL.match(span)
        if call:
            # `Upper(Name)` is a rule about `Upper`. Matching the full call finds
            # only verbatim repetitions, which silently dropped every
            # function-scoped rule — the most common kind in a technical book.
            out.append(call.group(1))
            continue

        if RX_SYNTACTIC.search(span):
            # The span DEMONSTRATES the construct instead of naming it. A rule
            # fixing a date format inside a set modifier is written entirely out
            # of field names and literals; it names no keyword, so an extractor
            # requiring one skips it and the defect stays invisible. Key on the
            # identifiers inside the shape.
            out += [w for w in re.findall(r"[A-Za-z_]\w{2,}", span)
                    if w.lower() not in NOISE_TOKENS]
            continue

        head = span.split()[0] if " " in span else span
        head = head.strip("().,;:`")
        out.append(head)

    out += [m.group(1) for m in RX_IDENTIFIER.finditer(re.sub(r"`[^`]*`", " ", text))]

    cleaned = [t.strip("().,;:`") for t in out]
    seen: set[str] = set()
    return [t for t in cleaned
            if len(t) >= 3 and t.lower() not in NOISE_TOKENS
            and not (t.lower() in seen or seen.add(t.lower()))]


def slug(unit: str, line: int, terms: list[str]) -> str:
    head = re.sub(r"[^\w]+", "-", (terms[0] if terms else "rule").lower()).strip("-")
    return f"{unit}-{line}-{head}"[:70]


def find_rules(project: Project, records: dict[str, tuple[str, list[Record]]],
               use_blame: bool) -> list[Rule]:
    rules: list[Rule] = []
    for unit, (rel, recs) in sorted(records.items()):
        blame = blame_map(project.root, rel, use_blame)
        for r in recs:
            if r.kind not in ("para", "bullet"):
                continue
            if not is_rule_shaped(r.text):
                continue
            terms = technical_tokens(r.text)
            if not terms:
                continue  # modality without a technical token is voice, not a rule
            bm = blame.get(r.line, ("", ""))
            rules.append(Rule(
                rule_id=slug(unit, r.line, terms),
                unit=unit, path=rel, line=r.line, text=r.text,
                heading_path=r.heading_path, key_terms=terms,
                blame_commit=bm[0], in_fix_run=False,
            ))
    return rules


def find_instances(project: Project,
                   records: dict[str, tuple[str, list[Record]]],
                   use_blame: bool) -> list[Instance]:
    """Every code block and every example passage in the book, once."""
    out: list[Instance] = []
    for unit, (rel, recs) in sorted(records.items()):
        by_line = {r.line: r for r in recs}
        blame = blame_map(project.root, rel, use_blame)

        for start, end, lang, body in code_blocks(recs):
            caption = prev_prose(by_line, start)
            heading = by_line.get(start).heading_path if start in by_line else ""
            bm = blame.get(start, ("", ""))
            out.append(Instance(
                kind="code", unit=unit, path=rel, line=start, end_line=end,
                heading_path=heading, text=body,
                caption=(caption.text if caption else ""),
                blame_commit=bm[0],
            ))

        for r in recs:
            if r.kind not in ("para", "bullet", "table"):
                continue
            if not RX_EXAMPLE_HEADING.search(r.heading_path):
                continue
            bm = blame.get(r.line, ("", ""))
            out.append(Instance(
                kind="example", unit=unit, path=rel, line=r.line, end_line=r.line,
                heading_path=r.heading_path, text=r.text, blame_commit=bm[0],
            ))
    return out


def term_document_frequency(rules: list[Rule],
                            instances: list[Instance]) -> dict[str, int]:
    """How many instances mention each candidate term.

    MEASURED: without this, the top rules on an 18-unit technical book were all
    keyed on data-model identifiers — the running example's field names — which
    appear in 168 of 767 code blocks. Every such rule "reached" a fifth of the
    book, and 349 rules with 168 instances each is not an audit, it is a dump.

    A term that appears everywhere discriminates nothing. This is the same idea
    as stopwords for prose, applied to identifiers.
    """
    df: dict[str, int] = {}
    terms = {t.lower() for r in rules for t in r.key_terms}
    pats = {t: re.compile(rf"(?<![\w]){re.escape(t)}(?![\w])", re.I) for t in terms}
    for inst in instances:
        hay = f"{inst.text}\n{inst.caption}"
        for t, p in pats.items():
            if p.search(hay):
                df[t] = df.get(t, 0) + 1
    return df


def attach_instances(rules: list[Rule], instances: list[Instance],
                     fix_run: set[str], df: dict[str, int],
                     df_ceiling_ratio: float = 0.15) -> int:
    """An instance belongs to a rule when it uses one of the rule's DISCRIMINATING
    key terms.

    Term matching, not semantic matching. A rule about `CONCATENATE` reaches every
    code block containing `CONCATENATE`. This still over-includes — some of those
    are out of the rule's scope — and that is the right direction to err: the
    auditor's verdict set has `OUT_OF_SCOPE` in it precisely so extras can be
    thrown back cheaply, while a missed instance is a defect that ships.

    Returns the number of rules dropped for having no discriminating term at all.
    Those are usually real rules stated over the running example's vocabulary; the
    fix is a hand-written probe, not a lower ceiling.
    """
    # Two ceilings, take the tighter. The ratio adapts to corpus size; the
    # absolute one encodes that a term reaching more instances than an agent can
    # judge in one run is not a scope at all — it is the running example's
    # vocabulary, and no threshold tuning turns it into a rule boundary.
    ceiling = max(3, min(int(len(instances) * df_ceiling_ratio),
                         TRACTABLE_MAX_INSTANCES))
    dropped = 0

    for r in rules:
        r.in_fix_run = in_fix_run(r.blame_commit, fix_run)
        # Rarest terms only, and at most three.
        #
        # MEASURED: keeping every term under the ceiling still gave rules with 168
        # instances, because a sentence naming five terms reaches the union of all
        # five. A human scoping "never use CONCATENATE on an optimized load" keys
        # on CONCATENATE, not on the field name that happens to share the
        # sentence. Rarest-first reproduces that.
        keep = sorted((t for t in r.key_terms if df.get(t.lower(), 0) <= ceiling),
                      key=lambda t: df.get(t.lower(), 0))[:3]
        if not keep:
            dropped += 1
            r.key_terms = []
            continue
        r.key_terms = keep
        pats = [re.compile(rf"(?<![\w]){re.escape(t)}(?![\w])") for t in keep]
        for inst in instances:
            if inst.path == r.path and inst.line == r.line:
                continue
            hay = f"{inst.text}\n{inst.caption}"
            hit = [t for t, p in zip(keep, pats) if p.search(hay)]
            if hit:
                copy = Instance(**{**inst.__dict__, "matched_terms": hit})
                copy.in_fix_run = in_fix_run(inst.blame_commit, fix_run)
                r.instances.append(copy)
    return dropped


# Share of the emission quota per failure mode.
#
# The two modes are genuinely different defects, and one of them is far more
# numerous in the candidate pool while the other is more numerous in the actual
# defect list. Measured on the reference book: 7 of 10 intra-unit defects were
# rule-vs-its-own-example, while 92% of rule CANDIDATES reached across units.
# Ranking them on one scale therefore starves the intra-unit mode completely —
# a 40-slot quota emitted 40 cross-unit rules and zero intra-unit ones.
#
# So each mode carries its own quota. The split is a judgement, not a
# measurement: cross-unit rules are what no per-unit reviewer could ever have
# seen, intra-unit ones are the more common defect. Even is the honest default.
RULE_QUOTA_WEIGHTS = {"cross-unit": 1.0, "intra-unit": 1.0}


def rule_stratum(rule: Rule) -> str:
    return ("cross-unit" if {i.unit for i in rule.instances} - {rule.unit}
            else "intra-unit")


def rule_rank(rule: Rule) -> tuple:
    """Judgeable first, then reach, then fewer instances.

    A rule with more instances than an agent can judge in one run can only be
    SAMPLED, and a sampled rule may never be reported clean — so it sorts last
    inside its stratum rather than leading it.
    """
    return (len(rule.instances) > TRACTABLE_MAX_INSTANCES,
            -len({i.unit for i in rule.instances} - {rule.unit}),
            len(rule.instances))


def select_rules(rules: list[Rule], quota: int) -> Selection:
    """THE selection. Emission and every check on emission call this one function.

    A first version had the gate verify its calibration pairs against the
    candidate list while emission capped independently — the pairs ranked
    199/205, never reached the dossier, and the gate still said PASS. One
    function is the structural fix; do not add a second ranking anywhere.
    """
    return stratified_top(rules, rule_stratum, rule_rank, quota,
                          RULE_QUOTA_WEIGHTS)


def emit_rule_file(rule: Rule) -> str:
    tractable = len(rule.instances) <= TRACTABLE_MAX_INSTANCES
    cross_unit = sorted({i.unit for i in rule.instances} - {rule.unit})

    # Rule touched in a fix pass with instances that were not — the mechanical
    # signature of a rule that was corrected while its examples were left behind.
    d2 = [i.loc for i in rule.instances if rule.in_fix_run and not i.in_fix_run][:10]

    L = ["---",
         f"rule_id: {rule.rule_id}",
         f"rule_site: {rule.loc}",
         f"home_unit: {rule.unit}",
         f"key_terms: [{', '.join(rule.key_terms)}]",
         f"instances_total: {len(rule.instances)}",
         f"instances_cross_unit: [{', '.join(cross_unit)}]",
         f"tractable: {'true' if tractable else 'false'}"]
    if not tractable:
        L.append(f"# more than {TRACTABLE_MAX_INSTANCES} instances — the list below is a "
                 f"SAMPLE. Set sampled:true in your findings and do not report the rule clean.")
    if d2:
        L.append("d2_candidates:   # rule touched in a fix run, these instances were not")
        L += [f"  - {loc}" for loc in d2]
    L += ["---", "",
          "## The rule", "",
          f"`{rule.loc}` — {rule.heading_path}", "",
          f"> {rule.text}", "",
          "**State this rule in your own words before judging anything**: what it "
          "forbids or requires, and over what scope. If you cannot state the scope, "
          "you cannot judge instances against it — say so and stop.", "",
          "## Instances", ""]

    if not rule.instances:
        L += ["_No instance uses this rule's key terms. Either the rule is stated and "
              "never exercised — which is worth noting on its own — or the key terms "
              "are wrong._", ""]
        return "\n".join(L)

    shown = rule.instances[:TRACTABLE_MAX_INSTANCES]
    for inst in sorted(shown, key=lambda i: (i.unit, i.line)):
        flags = [inst.kind]
        if inst.unit != rule.unit:
            flags.append("CROSS-UNIT")
        if rule.in_fix_run and not inst.in_fix_run:
            flags.append("D2")
        L.append(f"### {inst.loc}  [{' '.join(flags)}]  "
                 f"[matched: {', '.join(inst.matched_terms)}]")
        L += [f"> {inst.heading_path}", ""]
        if inst.caption:
            L += [f"*(caption)* {inst.caption}", ""]
        if inst.kind == "code":
            L += ["```", inst.text[:2000], "```", ""]
        else:
            L += [inst.text, ""]

    L += ["",
          "For each instance: `COMPLIES` (N1) · `VIOLATES` (D6) · "
          "`DECLARED_EXCEPTION` (N2) · `OUT_OF_SCOPE` (N2, state both scopes).", "",
          "Before any `D6`: open the unit and read AROUND the instance, grep the whole "
          "unit to fill `other_sites`, and separate an engine claim from voice. "
          "In doubt between `D6` and `N2`, choose `N2`."]
    return "\n".join(L)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Extract rule candidates and their instances.")
    add_common_args(ap)
    ap.add_argument("--out", default=None, help="Output dir for rule files.")
    ap.add_argument("--report", action="store_true", help="Candidate table only, no files.")
    ap.add_argument("--min-instances", type=int, default=2,
                    help="Skip rules with fewer instances than this (default 2). A rule "
                         "with one instance is the unit's own example, which the Critic "
                         "already saw.")
    ap.add_argument("--top", type=int, default=0,
                    help="Emit only the top N rules by the ranking below (0 = all). One "
                         "agent run per rule, so this is the cost dial. Whatever is cut "
                         "is reported — a silent truncation reads as full coverage.")
    ap.add_argument("--no-blame", action="store_true")
    ap.add_argument("--fix-run-commit", action="append", default=[])
    ap.add_argument("--df-ceiling", type=float, default=0.15,
                    help="A key term appearing in more than this fraction of instances "
                         "discriminates nothing and is ignored (default 0.15). Raise it "
                         "only if too many rules come back with no terms at all.")
    args = ap.parse_args(argv)

    project = load_project(args.root, args.units)
    audit = project.load_yaml("bible/audit-config.yaml")
    fix_run = {str(c) for c in (audit.get("fix_run_commits") or [])}
    fix_run |= {c.strip() for c in args.fix_run_commit if c.strip()}
    use_blame = (not args.no_blame) and is_repo(project.root)

    records: dict[str, tuple[str, list[Record]]] = {}
    for path in project.unit_paths:
        rel = project.rel(path)
        recs = segment(path, rel_to=project.root)
        for r in recs:
            r.path = rel
        # Logical paragraphs, not physical lines: a rule does not stop at column
        # 80, and on a hard-wrapped book the line-level view finds fragments.
        records[path.stem] = (rel, paragraphs(recs))

    rules = find_rules(project, records, use_blame)
    instances = find_instances(project, records, use_blame)
    df = term_document_frequency(rules, instances)
    dropped = attach_instances(rules, instances, fix_run, df, args.df_ceiling)

    kept = [r for r in rules if len(r.instances) >= args.min_instances]
    selection = select_rules(kept, args.top)

    print(f"[rules] {len(rules)} rule candidate(s), {len(instances)} instance(s) in "
          f"{len(records)} unit(s); {len(kept)} rule(s) with >= "
          f"{args.min_instances} instance(s)")
    for line in selection.report_lines("rule"):
        print(f"[rules] {line}")
    if dropped:
        print(f"[rules] {dropped} rule(s) dropped — every key term appears in more than "
              f"{args.df_ceiling:.0%} of instances, so nothing narrows them. These are "
              f"usually real rules phrased over the running example's vocabulary; give "
              f"them a hand-written probe rather than raising --df-ceiling.")

    if args.report or not args.out:
        # The report lists what WILL be emitted, from the same selection.
        # Showing a different list here is exactly the failure that let two
        # calibration pairs rank 199/205 and still pass a gate.
        print(f"\n{'rule_id':40} {'inst':>5} {'x-unit':>7} {'mode':11} site")
        print("-" * 104)
        for r in selection.emitted[:60]:
            print(f"{r.rule_id:40} {len(r.instances):>5} "
                  f"{len({i.unit for i in r.instances} - {r.unit}):>7} "
                  f"{rule_stratum(r):11} {r.loc}")
        if not args.out:
            return 0

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    emitted = selection.emitted
    cut = selection.dropped_total
    for r in emitted:
        (out_dir / f"{r.rule_id}.md").write_text(emit_rule_file(r), encoding="utf-8")

    idx = ["# Rule candidate index", "",
           "Ranked judgeable-first: a rule whose instances span several units is where "
           "a per-unit reviewer was structurally unable to help, but a rule with more "
           f"than {TRACTABLE_MAX_INSTANCES} instances can only be SAMPLED, and a sampled "
           "rule may never be reported clean.", ""]
    if cut:
        per = ", ".join(f"{k}: {v}" for k, v in sorted(selection.dropped.items()))
        idx += [f"> **{cut} rule(s) below the cut were not emitted** (`--top "
                f"{args.top}` — dropped {per}). Coverage of MG-2 this round is "
                f"partial, and the gate report must say so.", "",
                "Each failure mode carries its own quota. Blending them into one "
                "score starves the intra-unit mode — the more numerous defect — "
                "because cross-unit candidates dominate the pool.", ""]
    idx += ["| Rule | Site | Instances | Cross-unit | Tractable |",
            "|---|---|---:|---:|---|"]
    idx += [f"| [{r.rule_id}]({r.rule_id}.md) | `{r.loc}` | {len(r.instances)} | "
            f"{len({i.unit for i in r.instances} - {r.unit})} | "
            f"{'yes' if len(r.instances) <= TRACTABLE_MAX_INSTANCES else 'NO — sample'} |"
            for r in emitted]
    (out_dir / "_index.md").write_text("\n".join(idx) + "\n", encoding="utf-8")
    print(f"[rules] {len(emitted)} rule file(s) → {out_dir}")
    if cut:
        print(f"[rules] {cut} rule(s) NOT emitted because of --top {args.top}. "
              f"MG-2 coverage is partial this round.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
