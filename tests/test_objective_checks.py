"""Calibrate the objective checks against fixtures whose real-tool behaviour was observed.

Observed on 2026-09-28 with claude 2.1.283, codex-cli 0.157.1, and copilot 1.0.88.
Run with: uv run pytest -m live tests/test_objective_checks.py
"""

import shutil
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent / "eval"))
from objective_checks import check  # noqa: E402

SCENARIOS = Path(__file__).resolve().parent / "fixtures" / "scenarios"
TOOLS = all(shutil.which(t) for t in ("claude", "codex", "copilot"))
pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(not TOOLS, reason="needs claude, codex, and copilot"),
]


def test_seeded_defects_are_seen_differently_by_each_tool():
    result = check(SCENARIOS / "s6" / "repo")
    assert result["claude"]["errors"] == ["plugins.2.source"]
    assert result["codex"]["listed"] == ["deploy", "guard", "lint", "ok-tools", "remote-x"]
    assert result["copilot"]["listed"] == [
        "deploy",
        "fmt",
        "guard",
        "lint",
        "notes",
        "ok-tools",
        "remote-x",
    ]


def test_codex_drops_a_github_source_that_claude_accepts():
    result = check(SCENARIOS / "s7" / "repo")
    assert result["claude"]["success"] is True
    assert result["codex"]["listed"] == ["hello-tools"]
    assert result["copilot"]["listed"] == ["hello-tools", "notes"]


def test_a_repository_without_a_catalog_is_refused():
    result = check(SCENARIOS / "s1" / "repo")
    assert result["claude"]["success"] is False
    assert result["codex"]["added"] is False
    assert result["copilot"]["added"] is False
