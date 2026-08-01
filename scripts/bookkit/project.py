#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Project discovery and configuration.

Every script takes the same two flags — `--root` and `--units` — and resolves
them through here, so a retrofit run over a book written by an older version of
the skill behaves identically to a run inside the pipeline.

Standalone mode is not a degraded special case bolted on the side: a book that
was never scaffolded by this skill is precisely the book most likely to be
carrying the defects these checks look for.
"""

from __future__ import annotations

import glob as _glob
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover - environment guard
    sys.exit("Missing PyYAML. Install with: pip install pyyaml")

# Tried in order. The first that yields files wins, so a v3 project resolves to
# final/unit-NN.md and an older one to whatever it actually named its chapters.
DEFAULT_UNIT_GLOBS = [
    "final/unit-*.md",
    "final/ch-*.md",
    "final/*.md",
]

_NUM_RE = re.compile(r"(\d+)")


@dataclass
class Project:
    root: Path
    unit_paths: list[Path]
    meta: dict = field(default_factory=dict)
    standalone: bool = False

    # -- convenience accessors, all tolerant of a missing/partial meta.yaml ----

    @property
    def profile(self) -> str:
        return str(self._meta_get("project.profile", "") or "")

    @property
    def schema_version(self) -> str:
        return str(self.meta.get("schema_version", "") or "")

    @property
    def language_variant(self) -> str:
        return str(self._meta_get("conventions.language_variant", "en-US") or "en-US")

    @property
    def bible(self) -> Path:
        return self.root / "bible"

    @property
    def reviews(self) -> Path:
        return self.root / "reviews"

    @property
    def manuscript(self) -> Path:
        return self.root / "manuscript.md"

    def rel(self, path: Path) -> str:
        try:
            return path.resolve().relative_to(self.root.resolve()).as_posix()
        except ValueError:
            return path.name

    def _meta_get(self, dotted: str, default=None):
        node = self.meta
        for part in dotted.split("."):
            if not isinstance(node, dict) or part not in node:
                return default
            node = node[part]
        return node

    def get(self, dotted: str, default=None):
        """Public dotted lookup into meta.yaml, e.g. `pipeline.manuscript_gate.max_rounds`."""
        return self._meta_get(dotted, default)

    def load_yaml(self, relpath: str) -> dict:
        """Read a YAML file under the project root; {} when absent."""
        p = self.root / relpath
        if not p.exists():
            return {}
        data = yaml.safe_load(p.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}


def load_project(root: str | Path | None = None,
                 units: str | list[str] | None = None,
                 require_meta: bool = False) -> Project:
    """Resolve a project from a root and an optional unit glob.

    `units` may be a glob string, a list of globs, or None (auto-detect).
    Globs are resolved relative to `root` unless they are absolute.
    """
    root_path = _resolve_root(root)
    meta = _load_meta(root_path)
    standalone = not meta or str(meta.get("schema_version", "")) < "3.0"

    if require_meta and not meta:
        sys.exit(f"No bible/meta.yaml under {root_path}. "
                 f"Pass --units to run in standalone mode.")

    patterns = _as_list(units) or DEFAULT_UNIT_GLOBS
    paths = _resolve_units(root_path, patterns)
    if not paths:
        sys.exit(f"No unit files matched {patterns} under {root_path}.")

    return Project(root=root_path, unit_paths=paths, meta=meta, standalone=standalone)


def unit_sort_key(path: Path):
    """Sort units the way a reader meets them: by the number in the filename.

    Plain lexicographic sorting puts ch-10 before ch-2, which silently corrupts
    every ordering claim the checks make — "concept used before it is taught"
    becomes meaningless if the order is wrong.
    """
    nums = [int(n) for n in _NUM_RE.findall(path.stem)]
    return (nums or [10**9], path.stem)


# ---------------------------------------------------------------------------


def _resolve_root(root: str | Path | None) -> Path:
    if root:
        p = Path(root).expanduser().resolve()
        if not p.exists():
            sys.exit(f"Root does not exist: {p}")
        return p
    # Walk up from cwd looking for a project marker, then fall back to cwd.
    here = Path.cwd().resolve()
    for cand in [here, *here.parents]:
        if (cand / "bible" / "meta.yaml").exists() or (cand / "final").is_dir():
            return cand
    return here


def _load_meta(root: Path) -> dict:
    p = root / "bible" / "meta.yaml"
    if not p.exists():
        return {}
    try:
        data = yaml.safe_load(p.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        sys.exit(f"bible/meta.yaml is not valid YAML: {exc}")
    return data if isinstance(data, dict) else {}


def _as_list(units: str | list[str] | None) -> list[str]:
    if units is None:
        return []
    if isinstance(units, str):
        return [units]
    return list(units)


def _resolve_units(root: Path, patterns: list[str]) -> list[Path]:
    for pattern in patterns:
        pat = Path(pattern)
        matches = (_glob.glob(str(pat)) if pat.is_absolute()
                   else _glob.glob(str(root / pattern)))
        paths = sorted((Path(m) for m in matches if Path(m).is_file()),
                       key=unit_sort_key)
        if paths:
            return paths
    return []


def add_common_args(parser) -> None:
    """The two flags every script in this toolkit accepts."""
    parser.add_argument(
        "--root", default=None,
        help="Project root. Defaults to the nearest ancestor with bible/meta.yaml or final/.")
    parser.add_argument(
        "--units", default=None, action="append",
        help="Glob for unit files, repeatable. Defaults to final/unit-*.md, "
             "then final/ch-*.md, then final/*.md. Use this for standalone runs "
             "over a book written by an earlier version of the skill.")
