"""Open or update the one upstream-drift issue from the weekly reports (spec §9).

    python3 tests/drift_issue.py --upstream upstream.json --upstream-md upstream.md \
        --conformance conformance.json --conformance-md conformance.md [--run-url URL] [--dry-run]

Something to report means an upstream pin that is not `same` or `released`, a probe or help pin that
failed, or a report that is missing because its check crashed; a missing report is never
read as "nothing changed". With something to report, the open issue labelled
`upstream-drift` gets the new body and a comment, or a new issue is opened; with nothing,
no issue is touched. Needs `gh` with GH_TOKEN, except under --dry-run.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

LABEL = "upstream-drift"
TITLE = "Upstream drift: facts to re-verify"
QUIET = {"same", "released"}  # a newer npm release alone is listed in the body, not a finding
PROBE_FAILING = {"flipped", "broken", "error", "skipped"}
HELP_FAILING = {"changed", "unpinned", "skipped"}

Gh = Callable[[Sequence[str]], str]


def gh_cli(args: Sequence[str]) -> str:
    return subprocess.run(["gh", *args], check=True, capture_output=True, text=True).stdout


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def findings(
    upstream: list[dict[str, Any]] | None, conformance: dict[str, Any] | None
) -> list[str]:
    """One line per thing to report; empty means nothing changed."""
    found = []
    if upstream is None:
        found.append("the upstream check produced no report")
    else:
        found += [f"pin `{r['id']}` {r['status']}" for r in upstream if r["status"] not in QUIET]
    if conformance is None:
        found.append("the conformance probes produced no report")
    else:
        found += [
            f"probe `{p['id']}` {p['status']}"
            for p in conformance["probes"]
            if p["status"] in PROBE_FAILING
        ]
        found += [
            f"help `{h['command']}` {h['status']}"
            for h in conformance["help"]
            if h["status"] in HELP_FAILING
        ]
    return found


def body(found: list[str], upstream_md: Path, conformance_md: Path, run_url: str) -> str:
    parts = [
        "The weekly upstream check found facts that may be stale.",
        "Re-verify each one before changing a reference or a pin, as "
        "`skills/plugin-marketplaces/references/freshness.md` says.",
        "",
    ]
    if run_url:
        parts += [f"Run: {run_url}", ""]
    parts += ["## Summary", "", *[f"- {f}" for f in found], ""]
    for path in (upstream_md, conformance_md):
        if path.is_file():
            parts.append(path.read_text(encoding="utf-8"))
    text = "\n".join(parts)
    return text[:60000] + ("\n\n… truncated; see the run's artifacts." if len(text) > 60000 else "")


def publish(text: str, gh: Gh) -> str:
    open_issue = gh(
        [
            "issue",
            "list",
            "--label",
            LABEL,
            "--state",
            "open",
            "--json",
            "number",
            "--jq",
            ".[0].number",
        ]
    ).strip()
    if open_issue:
        gh(["issue", "edit", open_issue, "--body", text])
        gh(["issue", "comment", open_issue, "--body", "Updated by this week's upstream check."])
        return f"updated #{open_issue}"
    gh(
        [
            "label",
            "create",
            LABEL,
            "--color",
            "D93F0B",
            "--description",
            "Upstream facts to re-verify",
            "--force",
        ]
    )
    return gh(["issue", "create", "--title", TITLE, "--label", LABEL, "--body", text]).strip()


def main(argv: list[str] | None = None, gh: Gh = gh_cli) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--upstream", type=Path, required=True)
    parser.add_argument("--upstream-md", type=Path, required=True)
    parser.add_argument("--conformance", type=Path, required=True)
    parser.add_argument("--conformance-md", type=Path, required=True)
    parser.add_argument("--run-url", default="")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    found = findings(read_json(args.upstream), read_json(args.conformance))
    if not found:
        print("nothing changed; no issue touched")
        return 0
    text = body(found, args.upstream_md, args.conformance_md, args.run_url)
    if args.dry_run:
        print(text)
        return 0
    print(publish(text, gh))
    return 0


if __name__ == "__main__":
    sys.exit(main())
