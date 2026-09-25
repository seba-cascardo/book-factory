#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validate findings files against templates/gate-findings.schema.json.

A findings file that does not match the schema used to be dropped or misread in
silence — `"severity": "Critical"` counted as zero criticals. Now an invalid file
is an ERROR the gate reports by name.

Uses `jsonschema` when it is installed. Otherwise a minimal validator covering
the subset of JSON Schema the findings schema uses: type, enum, const, required,
properties, additionalProperties (boolean), items, $ref (local), oneOf, anyOf,
pattern, minLength, minimum, maximum.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

SCHEMA_PATH = Path(__file__).resolve().parents[2] / "templates" / "gate-findings.schema.json"

_TYPES = {
    "object": dict, "array": list, "string": str, "boolean": bool,
    "null": type(None),
}


def load_schema(path: Path | None = None) -> dict:
    return json.loads(Path(path or SCHEMA_PATH).read_text(encoding="utf-8"))


def validate(doc, schema: dict | None = None, *, force_fallback: bool = False) -> list[str]:
    """Error messages, empty when `doc` is valid."""
    schema = schema if schema is not None else load_schema()
    if not force_fallback:
        try:
            import jsonschema  # type: ignore
        except ImportError:
            jsonschema = None
        if jsonschema is not None:
            cls = jsonschema.validators.validator_for(schema)
            errs = sorted(cls(schema).iter_errors(doc), key=lambda e: list(e.absolute_path))
            return [f"{'/'.join(str(p) for p in e.absolute_path) or '(root)'}: {e.message}"
                    for e in errs]
    out: list[str] = []
    _check(doc, schema, schema, "", out)
    return out


def _is_type(value, name: str) -> bool:
    if name == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if name == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    return isinstance(value, _TYPES.get(name, object))


def _resolve(root: dict, ref: str) -> dict:
    node = root
    for part in ref.lstrip("#/").split("/"):
        node = node[part]
    return node


def _check(value, sch: dict, root: dict, path: str, out: list[str]) -> None:
    where = path or "(root)"
    if "$ref" in sch:
        _check(value, _resolve(root, sch["$ref"]), root, path, out)
        rest = {k: v for k, v in sch.items() if k not in ("$ref", "description")}
        if not rest:
            return
        sch = rest
    if "oneOf" in sch or "anyOf" in sch:
        options = sch.get("oneOf") or sch.get("anyOf")
        passing = 0
        for opt in options:
            errs: list[str] = []
            _check(value, opt, root, path, errs)
            passing += not errs
        if (passing != 1) if "oneOf" in sch else (passing == 0):
            out.append(f"{where}: does not match {'exactly one' if 'oneOf' in sch else 'any'} "
                       f"of the allowed shapes")
            return
    t = sch.get("type")
    if t is not None:
        names = t if isinstance(t, list) else [t]
        if not any(_is_type(value, n) for n in names):
            out.append(f"{where}: {json.dumps(value)[:60]} is not of type {t}")
            return
    if "enum" in sch and value not in sch["enum"]:
        out.append(f"{where}: {json.dumps(value)[:60]} is not one of {sch['enum']}")
    if "const" in sch and value != sch["const"]:
        out.append(f"{where}: must be {sch['const']!r}")
    if isinstance(value, str):
        if "minLength" in sch and len(value) < sch["minLength"]:
            out.append(f"{where}: shorter than {sch['minLength']}")
        if "pattern" in sch and not re.search(sch["pattern"], value):
            out.append(f"{where}: {value!r} does not match {sch['pattern']}")
    if _is_type(value, "number"):
        if "minimum" in sch and value < sch["minimum"]:
            out.append(f"{where}: {value} < {sch['minimum']}")
        if "maximum" in sch and value > sch["maximum"]:
            out.append(f"{where}: {value} > {sch['maximum']}")
    if isinstance(value, dict):
        for key in sch.get("required", []):
            if key not in value:
                out.append(f"{where}: missing required property {key!r}")
        props = sch.get("properties", {})
        for key, sub in value.items():
            if key in props:
                _check(sub, props[key], root, f"{path}/{key}".lstrip("/"), out)
            elif sch.get("additionalProperties") is False:
                out.append(f"{where}: unexpected property {key!r}")
    if isinstance(value, list) and "items" in sch:
        for i, item in enumerate(value):
            _check(item, sch["items"], root, f"{path}/{i}".lstrip("/"), out)
