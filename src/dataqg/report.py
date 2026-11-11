"""Turn a list of issues into text or JSON. No validation logic here."""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import asdict

from .checks import Issue, Severity


def summarize(issues: Sequence[Issue]) -> dict[str, int]:
    errors = sum(1 for i in issues if i.severity is Severity.ERROR)
    return {"errors": errors, "warnings": len(issues) - errors}


def render_text(issues: Sequence[Issue], limit: int | None = None) -> str:
    shown = issues if limit is None else issues[:limit]
    lines = []
    for issue in shown:
        where = f"row {issue.row}" if issue.row is not None else "header"
        column = f" [{issue.column}]" if issue.column else ""
        label = issue.severity.value.upper()
        lines.append(f"{label:7} {where}{column}: {issue.message}")
    hidden = len(issues) - len(shown)
    if hidden > 0:
        lines.append(f"... and {hidden} more issue(s) not shown")
    totals = summarize(issues)
    lines.append(f"{totals['errors']} error(s), {totals['warnings']} warning(s)")
    return "\n".join(lines)


def render_json(issues: Sequence[Issue]) -> str:
    payload = {
        "summary": summarize(issues),
        "issues": [asdict(i) for i in issues],
    }
    return json.dumps(payload, indent=2, default=str)
