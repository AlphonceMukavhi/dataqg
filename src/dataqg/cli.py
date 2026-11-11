"""Command-line interface: the only module that touches files and the console."""

from __future__ import annotations

import argparse
import csv
import logging
import sys
from collections.abc import Sequence
from pathlib import Path

from . import __version__
from .checks import Issue, Severity, check_header, check_rows
from .report import render_json, render_text
from .schema import SchemaError, load_schema

log = logging.getLogger("dataqg")

EXIT_OK = 0
EXIT_ISSUES = 1
EXIT_USAGE = 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="dataqg", description=__doc__)
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate", help="validate a CSV file")
    validate.add_argument("csv_file", type=Path)
    validate.add_argument("--schema", type=Path, required=True)
    validate.add_argument("--format", choices=("text", "json"), default="text")
    validate.add_argument("--max-issues", type=int, default=None)
    validate.add_argument("-v", "--verbose", action="store_true")
    return parser


def validate_file(csv_path: Path, schema_path: Path) -> list[Issue]:
    schema = load_schema(schema_path)
    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        header = list(reader.fieldnames or [])
        issues = list(check_header(header, schema))
        issues.extend(check_rows(reader, schema))
    return issues


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )
    try:
        log.debug("validating %s against %s", args.csv_file, args.schema)
        issues = validate_file(args.csv_file, args.schema)
    except (SchemaError, OSError, UnicodeDecodeError, csv.Error) as exc:
        print(f"dataqg: error: {exc}", file=sys.stderr)
        return EXIT_USAGE

    if args.format == "json":
        print(render_json(issues))
    else:
        print(render_text(issues, args.max_issues))

    has_errors = any(i.severity is Severity.ERROR for i in issues)
    return EXIT_ISSUES if has_errors else EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
