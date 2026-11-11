"""Schema loading: turn a JSON file into validated, typed objects."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

SUPPORTED_TYPES = {"int", "float", "str"}


class SchemaError(ValueError):
    """Raised when the schema file itself is invalid."""


@dataclass(frozen=True)
class ColumnRule:
    name: str
    type: str = "str"
    nullable: bool = False
    min: float | None = None
    max: float | None = None
    allowed: tuple[str, ...] = ()


@dataclass(frozen=True)
class Schema:
    columns: tuple[ColumnRule, ...]
    key: tuple[str, ...] = field(default=())


def parse_schema(raw: dict[str, Any]) -> Schema:
    """Build a Schema from a decoded JSON object, failing loudly on bad input."""
    columns_raw = raw.get("columns")
    if not isinstance(columns_raw, dict) or not columns_raw:
        raise SchemaError("schema needs a non-empty 'columns' object")

    rules: list[ColumnRule] = []
    for name, spec in columns_raw.items():
        col_type = spec.get("type", "str")
        if col_type not in SUPPORTED_TYPES:
            raise SchemaError(f"column {name!r}: unsupported type {col_type!r}")
        rules.append(
            ColumnRule(
                name=name,
                type=col_type,
                nullable=bool(spec.get("nullable", False)),
                min=spec.get("min"),
                max=spec.get("max"),
                allowed=tuple(spec.get("allowed", ())),
            )
        )

    key = tuple(raw.get("key", ()))
    unknown = [k for k in key if k not in columns_raw]
    if unknown:
        raise SchemaError(f"key columns not in schema: {unknown}")
    return Schema(columns=tuple(rules), key=key)


def load_schema(path: Path) -> Schema:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SchemaError(f"{path}: invalid JSON ({exc})") from exc
    return parse_schema(raw)
