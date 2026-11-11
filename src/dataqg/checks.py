"""The validation rules. Pure functions: no printing, no file access."""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from enum import StrEnum

from .schema import ColumnRule, Schema


class Severity(StrEnum):
    ERROR = "error"
    WARNING = "warning"


@dataclass(frozen=True)
class Issue:
    severity: Severity
    message: str
    column: str | None = None
    row: int | None = None  # 1-based data row (the header is not counted)


def _convert(value: str, col_type: str) -> int | float | str:
    if col_type == "int":
        return int(value)
    if col_type == "float":
        return float(value)
    return value


def check_header(header: list[str], schema: Schema) -> Iterator[Issue]:
    expected = {rule.name for rule in schema.columns}
    for name in sorted(expected - set(header)):
        yield Issue(Severity.ERROR, f"missing column {name!r}", column=name)
    for name in sorted(set(header) - expected):
        yield Issue(Severity.WARNING, f"unexpected column {name!r}", column=name)


def check_cell(value: str, rule: ColumnRule, row: int) -> Iterator[Issue]:
    if value.strip() == "":
        if not rule.nullable:
            yield Issue(
                Severity.ERROR, "empty value in non-nullable column", rule.name, row
            )
        return

    try:
        converted = _convert(value, rule.type)
    except ValueError:
        yield Issue(
            Severity.ERROR, f"{value!r} is not a valid {rule.type}", rule.name, row
        )
        return

    if isinstance(converted, int | float):
        if rule.min is not None and converted < rule.min:
            yield Issue(
                Severity.ERROR, f"{converted} is below min {rule.min}", rule.name, row
            )
        if rule.max is not None and converted > rule.max:
            yield Issue(
                Severity.ERROR, f"{converted} is above max {rule.max}", rule.name, row
            )
    if rule.allowed and value not in rule.allowed:
        yield Issue(Severity.ERROR, f"{value!r} not in allowed values", rule.name, row)


def check_rows(rows: Iterable[dict[str, str]], schema: Schema) -> Iterator[Issue]:
    seen_keys: dict[tuple[str, ...], int] = {}
    for row_number, row in enumerate(rows, start=1):
        for rule in schema.columns:
            if rule.name in row:
                yield from check_cell(row[rule.name] or "", rule, row_number)
        if schema.key and all(k in row for k in schema.key):
            key = tuple(row[k] for k in schema.key)
            if key in seen_keys:
                yield Issue(
                    Severity.ERROR,
                    f"duplicate key {key} (first seen on row {seen_keys[key]})",
                    row=row_number,
                )
            else:
                seen_keys[key] = row_number
