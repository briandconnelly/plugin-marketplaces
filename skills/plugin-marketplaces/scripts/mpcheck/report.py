"""Render a report as text or JSON."""

from __future__ import annotations

import json

from mpcheck.model import Severity
from mpcheck.run import Report

ORDER = {Severity.ERROR: 0, Severity.WARNING: 1, Severity.INFO: 2}


def render_json(report: Report) -> str:
    return json.dumps(
        {
            "statuses": {g: {"status": s, "note": n} for g, (s, n) in report.statuses.items()},
            "findings": [f.to_dict() for f in report.findings],
        },
        indent=2,
    )


def render_text(report: Report) -> str:
    lines = ["Check levels:"]
    for group, (status, note) in report.statuses.items():
        lines.append(f"  {group:24} {status}" + (f"  ({note})" if note else ""))
    lines.append("")
    if not report.findings:
        lines.append("No findings.")
    for f in sorted(report.findings, key=lambda f: (ORDER[f.severity], f.file, f.pointer)):
        where = f.file + (f"#{f.pointer}" if f.pointer else "")
        rule = f" [{f.rule}]" if f.rule else ""
        lines.append(f"{f.severity.upper():7} {where}  {f.check}{rule}: {f.message}")
    return "\n".join(lines)
