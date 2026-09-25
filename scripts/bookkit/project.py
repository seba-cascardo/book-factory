#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Project discovery and configuration.

Every script takes the same two flags — `--root` and `--units` — and resolves
them here, so a retrofit run over a book an older version of the skill wrote
behaves exactly like a run inside the pipeline.
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

from .textio import read_text, safe_rel

# Tried in order; the first that yields files wins.
DEFAULT_UNIT_GLOBS = ["final/unit-*.md", "final/ch-*.md", "final/*.md"]

_NUM_RE = re.compile(r"(\d+)")


@dataclass
class Project:
    root: Path
    unit_paths: list[Path]
    meta: dict = field(default_factory=dict)

    @property
    def profile(self) -> str:
        return str(self.get("project.profile", "") or "").strip().lower()

    @property
    def literary(self) -> bool:
        return self.profile == "book-literary"

    @property
    def schema_version(self) -> str:
        return str(self.meta.get("schema_version", "") or "")

    @property
    def language_variant(self) -> str:
        """`project.language_variant` → `conventions.language_variant` →
        `project.language` → `en-US`.

        The template writes it under `project:`; reading only `conventions:`
        made an es-AR book run with English stopwords and spelling rules.
        """
        for key in ("project.language_variant", "conventions.language_variant",
                    "project.language"):
            val = self.get(key)
            if val:
                return str(val)
        return "en-US"

    @property
    def language(self) -> str:
        """Base language: `es-AR` → `es`."""
        return self.language_variant.strip().lower().replace("_", "-").split("-")[0] or "en"

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
        return safe_rel(path, self.root)

    def get(self, dotted: str, default=None):
        """Dotted lookup into meta.yaml, e.g. `pipeline.manuscript_gate.max_rounds`."""
        node = self.meta
        for part in dotted.split("."):
            if not isinstance(node, dict) or part not in node:
                return default
            node = node[part]
        return node

    def load_yaml(self, relpath: str) -> dict:
        """A YAML file under the project root; {} when absent or not a mapping."""
        return load_yaml_file(self.root / relpath)


def load_yaml_file(path: Path):
    p = Path(path)
    if not p.exists():
        return {}
    try:
        data = yaml.safe_load(read_text(p))
    except yaml.YAMLError as exc:
        sys.exit(f"{p} is not valid YAML: {exc}")
    return data if isinstance(data, dict) else {}


def load_project(root: str | Path | None = None,
                 units: str | list[str] | None = None) -> Project:
    """Resolve a project from a root and an optional unit glob (or list of globs)."""
    root_path = _resolve_root(root)
    meta = load_yaml_file(root_path / "bible" / "meta.yaml")
    patterns = as_list(units) or DEFAULT_UNIT_GLOBS
    paths = _resolve_units(root_path, patterns)
    if not paths:
        sys.exit(f"No unit files matched {patterns} under {root_path}.")
    return Project(root=root_path, unit_paths=paths, meta=meta)


def natural_key(name: str):
    """Sort key that puts ch-2 before ch-10."""
    nums = [int(n) for n in _NUM_RE.findall(str(name))]
    return (nums or [10**9], str(name))


def unit_sort_key(path: Path):
    """Sort units the way a reader meets them: by the number in the filename.

    Lexicographic order puts ch-10 before ch-2, which silently corrupts every
    ordering claim the checks make.
    """
    return natural_key(Path(path).stem)


def unit_number(value) -> int | None:
    """The number in a unit id, however it was written: `unit-01`, `ch-1`, `01`, 1.

    PyYAML reads `unit: 01` as the integer 1, while findings say `unit-01`;
    comparing strings meant MG-3 never matched a single exercise unit.
    """
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return value
    nums = _NUM_RE.findall(str(value))
    return int(nums[-1]) if nums else None


def as_list(value) -> list:
    """A config value as a list. A bare string is ONE item, never its letters."""
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return list(value)
    return [value]


def _resolve_root(root: str | Path | None) -> Path:
    if root:
        p = Path(root).expanduser().absolute()
        if not p.exists():
            sys.exit(f"Root does not exist: {p}")
        return p
    here = Path.cwd().absolute()
    for cand in [here, *here.parents]:
        if (cand / "bible" / "meta.yaml").exists() or (cand / "final").is_dir():
            return cand
    return here


def _resolve_units(root: Path, patterns: list[str]) -> list[Path]:
    for pattern in patterns:
        pat = Path(pattern)
        matches = (_glob.glob(str(pat)) if pat.is_absolute()
                   else _glob.glob(str(root / pattern)))
        paths = sorted((Path(m) for m in matches if Path(m).is_file()), key=unit_sort_key)
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
        help="Glob for unit files, repeatable. Defaults to final/unit-*.md, then "
             "final/ch-*.md, then final/*.md. Use it for a retrofit over a book an "
             "earlier version of the skill wrote.")
