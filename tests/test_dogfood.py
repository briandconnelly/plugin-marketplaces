"""This repository is its own marketplace (spec §5): its catalogs must pass the validator."""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

from mpcheck.model import Severity
from mpcheck.run import run_checks

ROOT = Path(__file__).resolve().parents[1]


def test_the_repository_marketplace_has_no_error_findings():
    report = run_checks(ROOT, policy_path=None, use_claude=False)
    errors = [f for f in report.findings if f.severity == Severity.ERROR]
    assert errors == []
    assert report.statuses["local"][0] == "passed"
    assert report.statuses["policy"][0] == "passed"


def test_every_recorded_version_is_the_package_version():
    version = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"][
        "version"
    ]
    for manifest in ("plugin.json", ".claude-plugin/plugin.json"):
        assert json.loads((ROOT / manifest).read_text(encoding="utf-8"))["version"] == version
