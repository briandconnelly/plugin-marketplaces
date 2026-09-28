"""Offline tests for objective_checks error reporting (no real CLI is run)."""

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "eval"))
import objective_checks  # noqa: E402


def fake(outputs):
    calls = iter(outputs)

    def run(argv, env):
        stdout, stderr = next(calls)
        return subprocess.CompletedProcess(argv, 0, stdout=stdout, stderr=stderr)

    return run


def test_codex_list_parse_failure_keeps_stdout(monkeypatch, tmp_path):
    monkeypatch.setattr(objective_checks.shutil, "which", lambda _: "/usr/bin/codex")
    monkeypatch.setattr(
        objective_checks,
        "_run",
        fake([('{"marketplaceName": "m"}', ""), ("Error: unexpected listing format", "")]),
    )
    result = objective_checks.codex(tmp_path)
    assert "unexpected listing format" in result["error"]


def test_copilot_browse_parse_failure_keeps_stdout(monkeypatch, tmp_path):
    monkeypatch.setattr(objective_checks.shutil, "which", lambda _: "/usr/bin/copilot")
    monkeypatch.setattr(
        objective_checks,
        "_run",
        fake([('Marketplace "m" added successfully.', ""), ("Failed to browse: boom", "")]),
    )
    result = objective_checks.copilot(tmp_path)
    assert "Failed to browse: boom" in result["error"]
