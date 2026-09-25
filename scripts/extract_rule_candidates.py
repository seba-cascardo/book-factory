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

from bookkit.coverage import (  # noqa: E402
    CoverageRecord, Subject, add_coverage_args, composite_fingerprint,
    load_ledger, partition,
)
from bookkit.gitblame import blame_map, in_fix_run, is_repo  # noqa: E402
from bookkit.project import Project, add_common_args, load_project  # noqa: E402
from bookkit.selection import Selection, stratified_top  # noqa: E402
from bookkit.segment import (  # noqa: E402
    Record, code_blocks, paragraphs, prev_prose, segment,
)
from bookkit.textmetrics import content_terms, fingerprint, stopwords_for  # noqa: E402

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
#
# It is also a DEBT, not a fact about the world. `tractable: false` keeps the gate
# off `PASS` forever unless something can change it, and a criterion nothing can
# satisfy is the decay this toolkit argues against everywhere else — measured on
# the reference book, 221 of 454 rules were over this line, so a derived-only flag
# would have made `PASS` unreachable by construction.
#
# `bible/rule-probes-tuned.yaml` is what makes it reachable: narrowing a rule's
# terms, scoping it, or splitting it into sub-rules brings each subject under the
# ceiling, and then depth closes by WORK rather than by waiver.
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
    fix is a hand-written entry in `bible/rule-probes-tuned.yaml`, not a lower
    ceiling. See § Tuned rule probes below for the format.
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


# ---------------------------------------------------------------------------
# Tuned rule probes — the ladder for the depth axis
# ---------------------------------------------------------------------------
#
# `bible/concept-probes-tuned.yaml` has always let a human narrow a concept by
# hand. Rules had no equivalent, so `tractable: false` was purely derived from
# `len(instances)` and nothing a person could do would change it. That made the
# depth half of coverage a permanent debt: on the reference book 221 of 454 rules
# were over the ceiling, so `PASS` was unreachable however much work anyone did,
# and every project would have ended at a standing waiver. A criterion nobody can
# satisfy decays exactly like a percentage floor.
#
# So the same affordance, for rules. Four narrowings and one split:
#
#   key_terms       replace the derived terms outright
#   require_terms   an instance must ALSO contain all of these
#   exclude_pattern instances matching this regex are out of scope
#   scope_units     only instances in these units
#   scope_heading   only instances under a heading path containing this
#   split           partition one broad rule into scoped sub-rules
#
# Narrowing is a claim about the rule's SCOPE, not a way to make a number
# smaller. `scripts/manuscript_gate.py` writes a ranked worklist of every
# intractable rule to `round-N/rule-probes-proposed.yaml` so the work starts from
# the real list rather than from a blank file.


def load_rule_overrides(project: Project) -> dict[str, dict]:
    doc = project.load_yaml("bible/rule-probes-tuned.yaml")
    out: dict[str, dict] = {}
    for entry in (doc.get("rules") or []):
        if isinstance(entry, dict) and entry.get("id"):
            out[str(entry["id"])] = entry
    return out


def _term_pats(terms: list[str]) -> list[re.Pattern]:
    return [re.compile(rf"(?<![\w]){re.escape(t)}(?![\w])") for t in terms]


def _rematch(rule: Rule, terms: list[str], instances: list[Instance],
             spec: dict, fix_run: set[str]) -> list[Instance]:
    """Re-attach instances to one rule under a hand-written narrowing."""
    pats = _term_pats(terms)
    req = _term_pats([str(t) for t in (spec.get("require_terms") or [])])
    units = {str(u) for u in (spec.get("scope_units") or [])}
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
        if units and inst.unit not in units:
            continue
        if heading and heading not in inst.heading_path:
            continue
        hay = f"{inst.text}\n{inst.caption}"
        if excl and excl.search(hay):
            continue
        hit = [t for t, p in zip(terms, pats) if p.search(hay)]
        if not hit:
            continue
        if req and not all(p.search(hay) for p in req):
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
    notes: list[str] = []
    for unknown in sorted(set(overrides) - set(by_id)):
        # Loud, because a typo here silently does nothing — and the human will
        # believe they closed a rule they did not touch.
        notes.append(f"tuned probe for unknown rule id `{unknown}` — no such "
                     f"candidate. Check the id against the rule index.")

    out: list[Rule] = []
    for rule in rules:
        spec = overrides.get(rule.rule_id)
        if not spec:
            out.append(rule)
            continue

        splits = spec.get("split") or []
        if splits:
            for part in splits:
                suffix = re.sub(r"[^\w-]+", "-", str(part.get("suffix") or "part")).strip("-")
                sub = Rule(rule_id=f"{rule.rule_id}--{suffix}", unit=rule.unit,
                           path=rule.path, line=rule.line, text=rule.text,
                           heading_path=rule.heading_path,
                           key_terms=[str(t) for t in (part.get("key_terms")
                                                       or rule.key_terms)],
                           blame_commit=rule.blame_commit, in_fix_run=rule.in_fix_run)
                sub.instances = _rematch(sub, sub.key_terms, instances, part, fix_run)
                notes.append(f"{rule.rule_id} split -> {sub.rule_id}: "
                             f"{len(sub.instances)} instance(s)")
                out.append(sub)
            continue

        before = len(rule.instances)
        terms = [str(t) for t in (spec.get("key_terms") or rule.key_terms)]
        rule.key_terms = terms
        rule.instances = _rematch(rule, terms, instances, spec, fix_run)
        notes.append(f"{rule.rule_id} narrowed: {before} -> {len(rule.instances)} "
                     f"instance(s)"
                     + ("  [still over the ceiling]"
                        if len(rule.instances) > TRACTABLE_MAX_INSTANCES else "  [tractable]"))
        out.append(rule)
    return out, notes


def propose_rule_probes(rules: list[Rule], out_path: Path) -> int:
    """Write the worklist of rules that can only be SAMPLED.

    An escape hatch nobody can find is not an escape hatch. Depth closes by
    narrowing intractable rules one at a time, so the toolkit owes whoever does
    that a concrete, ranked list instead of a blank file — the same reason the
    verification plan is generated from `deferred` rather than described.
    """
    over = sorted((r for r in rules if len(r.instances) > TRACTABLE_MAX_INSTANCES),
                  key=lambda r: -len(r.instances))
    L = ["# rule-probes-proposed.yaml — GENERATED WORKLIST, not configuration.",
         "#",
         f"# {len(over)} rule(s) have more than {TRACTABLE_MAX_INSTANCES} instances and can "
         f"therefore only be",
         "# SAMPLED. A sampled subject may never be reported clean, so each one keeps the",
         "# gate at `PASS-SAMPLED`.",
         "#",
         "# Copy the entries you want into `bible/rule-probes-tuned.yaml` and uncomment ONE",
         "# narrowing per rule. Narrowing is a claim about the rule's SCOPE — if the rule",
         "# really does reach all those instances, do not shrink it: leave it sampled and",
         "# waive the depth, which is the honest outcome.",
         "#",
         "# See templates/rule-probes-tuned.yaml for the full format.",
         "", "rules:"]
    for r in over:
        units = sorted({i.unit for i in r.instances})
        L += [f"  # {len(r.instances)} instances · terms: {', '.join(r.key_terms)} · "
              f"units: {', '.join(units[:8])}{' …' if len(units) > 8 else ''}",
              f"  # rule at {r.loc} — {r.heading_path}",
              f"  # - id: {r.rule_id}",
              f"  #   key_terms: [{r.key_terms[0] if r.key_terms else ''}]"
              f"        # keep only the term that carries the rule",
              f"  #   require_terms: []        # an instance must ALSO contain these",
              f"  #   scope_units: []          # only instances in these units",
              f"  #   note: \"\"",
              ""]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(L) + "\n", encoding="utf-8")
    return len(over)


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


def rule_subject(rule: Rule) -> Subject:
    """The ledger's view of a rule: what an audit of it would have read.

    The fingerprint spans the rule sentence AND every instance shown with it. An
    auditor's verdict was reached against those instances, so editing one of them
    invalidates the verdict and the rule returns to the pool.
    """
    shown = sorted(rule.instances, key=lambda i: (i.unit, i.line))[:TRACTABLE_MAX_INSTANCES]
    return Subject(
        id=rule.rule_id,
        fingerprint=composite_fingerprint(
            [fingerprint(rule.text)] + [fingerprint(i.text) for i in shown]),
        stratum=rule_stratum(rule),
        instances=len(rule.instances),
        sampled=len(rule.instances) > TRACTABLE_MAX_INSTANCES,
    )


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
    ap.add_argument("--round", type=int, default=1, help="Round number, for the record.")
    ap.add_argument("--propose-probes", metavar="PATH", default=None,
                    help="Write the ranked worklist of rules that can only be SAMPLED "
                         "(round-N/rule-probes-proposed.yaml). Depth closes by narrowing "
                         "these one at a time; a blank file is not a starting point.")
    add_coverage_args(ap)
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

    # Hand-written narrowings, BEFORE the min-instances filter and before
    # tractability is computed — they are what makes `tractable: false` a debt a
    # person can pay down rather than a permanent fact.
    rules, tuned_notes = apply_rule_overrides(
        rules, instances, load_rule_overrides(project), fix_run)
    for note in tuned_notes:
        print(f"[rules] tuned: {note}")

    # ELIGIBLE = post-filter. Everything that survived --min-instances, the
    # --df-ceiling term drop and the imperative/voice discard. This is the
    # denominator, and it does not include raw candidates: a denominator with
    # noise in it inflates the percentage in the comfortable direction.
    kept = [r for r in rules if len(r.instances) >= args.min_instances]
    subjects = {r.rule_id: rule_subject(r) for r in kept}

    # The ledger takes what earlier rounds already audited OUT OF THE POOL and
    # leaves it IN THE DENOMINATOR. That is what turns --top back into the cost
    # dial its comment always claimed it was, instead of a permanent ceiling.
    ledger = load_ledger(args.audited).get("MG-2", {})
    _pool_subjects, already, requeued = partition(list(subjects.values()), ledger)
    pool_ids = {s.id for s in _pool_subjects}
    pool = [r for r in kept if r.rule_id in pool_ids]

    selection = select_rules(pool, args.top)

    print(f"[rules] {len(rules)} rule candidate(s), {len(instances)} instance(s) in "
          f"{len(records)} unit(s); {len(kept)} rule(s) with >= "
          f"{args.min_instances} instance(s)")
    if already or requeued:
        print(f"[rules] ledger: {len(already)} rule(s) already audited under an "
              f"unchanged fingerprint (skipped, still counted), {len(requeued)} "
              f"re-queued because their text changed since.")
    for line in selection.report_lines("rule"):
        print(f"[rules] {line}")

    if args.coverage:
        eligible_by_stratum: dict[str, int] = {}
        for r in kept:
            st = subjects[r.rule_id].stratum
            eligible_by_stratum[st] = eligible_by_stratum.get(st, 0) + 1
        selected_by_stratum: dict[str, int] = {}
        emitted_subjects: list[Subject] = []
        for r in selection.emitted:
            s = subjects[r.rule_id]
            s.stratum, s.rank = selection.rank_of(r)
            selected_by_stratum[s.stratum] = selected_by_stratum.get(s.stratum, 0) + 1
            emitted_subjects.append(s)
        rec = CoverageRecord(
            check="MG-2",
            round=args.round,
            eligible_candidates=len(kept),
            selected=len(selection.emitted),
            emitted=len(selection.emitted),
            sampled_within=sum(1 for s in emitted_subjects if s.sampled),
            already_audited=already,
            requeued=requeued,
            strata={k: {"eligible": v, "selected": selected_by_stratum.get(k, 0)}
                    for k, v in sorted(eligible_by_stratum.items())},
            subjects=emitted_subjects,
            # Ranked, so a human can promote three specific rules into the next
            # round without recalibrating anything.
            cut=[{"id": c.item.rule_id, "rank": c.rank, "stratum": c.stratum,
                  "instances": len(c.item.instances), "site": c.item.loc}
                 for c in selection.cut],
        )
        rec.write(args.coverage)
        print(f"[rules] {rec.report_line('rule')} → {args.coverage}")

    if args.propose_probes:
        n_over = propose_rule_probes(kept, Path(args.propose_probes))
        if n_over:
            print(f"[rules] {n_over} rule(s) can only be SAMPLED "
                  f"(> {TRACTABLE_MAX_INSTANCES} instances). Ranked worklist → "
                  f"{args.propose_probes}. Narrow them in bible/rule-probes-tuned.yaml "
                  f"to close the depth axis, or waive it — but do not report them clean.")
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
    if already:
        idx += [f"> {len(already)} rule(s) are not in this round's list because an "
                f"earlier round already audited them and their text has not changed. "
                f"They still count as covered. {len(requeued)} rule(s) came BACK into "
                f"the pool because their text was edited since.", ""]
    if cut:
        per = ", ".join(f"{k}: {v}" for k, v in sorted(selection.dropped.items()))
        share = cut / max(len(kept), 1)
        idx += [f"> **{cut} rule(s) below the cut were not emitted** (`--top "
                f"{args.top}` — dropped {per}) — {share:.0%} of the eligible surface "
                f"will not be looked at this round. MG-2 coverage is partial; the "
                f"verdict is `PASS-PARTIAL` until the pool drains.", "",
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
        print(f"[rules] {cut} rule(s) NOT emitted because of --top {args.top} — "
              f"{cut / max(len(kept), 1):.0%} of the eligible surface. MG-2 coverage "
              f"is partial this round; run another round to drain the pool.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
