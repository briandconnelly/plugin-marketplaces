#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["jsonschema>=4.23"]
# ///
"""Validate a user-hosted plugin marketplace (see references/validation.md)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from mpcheck.model import Severity
from mpcheck.report import render_json, render_text
from mpcheck.run import run_checks


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".", type=Path, help="marketplace root")
    parser.add_argument(
        "--policy", type=Path, help="policy file (default: marketplace-policy.json)"
    )
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--fail-on", choices=("error", "warning"), default="error")
    parser.add_argument("--no-claude", action="store_true", help="skip `claude plugin validate`")
    args = parser.parse_args(argv)
    try:
        report = run_checks(args.root, policy_path=args.policy, use_claude=not args.no_claude)
    except Exception as exc:  # noqa: BLE001 - exit 2 is the validator-failure contract
        print(f"check_marketplace: validator failure: {exc!r}", file=sys.stderr)
        return 2
    print(render_json(report) if args.format == "json" else render_text(report))
    return report.exit_code(Severity(args.fail_on))


if __name__ == "__main__":
    sys.exit(main())
