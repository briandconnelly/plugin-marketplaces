import json
import subprocess

import pytest
from prepare import main, prepare
from scenario_doc import DOC, scenario
from score_prompt import score_prompt

TOOLS = {"claude": "x", "codex": "x", "copilot": "x"}


def test_prepare_makes_a_committed_pinned_run(tmp_path):
    (run,) = prepare(tmp_path, "s5", 1, "baseline", "test session", tools=TOOLS)
    assert run == tmp_path / "s5-r1"
    manifest = json.loads((run / "manifest.json").read_text())
    assert manifest["upstream_commits"]["v1.4.0"] == "cb5ce7cbae4484846b11927074c03a273f223d83"
    status = subprocess.run(
        ["git", "-C", str(run / "repo"), "status", "--porcelain"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    assert status == ""
    prompt = (run / "prompt.txt").read_text()
    assert prompt.startswith(f"You are working in `{run / 'repo'}`")
    assert prompt.endswith("Release it to our marketplace users.")
    with pytest.raises(FileExistsError):
        prepare(tmp_path, "s5", 1, "baseline", "test session", tools=TOOLS)


def test_score_prompt_carries_the_criteria_verbatim(tmp_path):
    (run,) = prepare(tmp_path, "s7", 1, "baseline", "test session", tools=TOOLS)
    text = score_prompt(run)
    assert scenario(DOC.read_text(encoding="utf-8"), 7).criteria in text
    assert str(run / "artefacts" / "diff.patch") in text
    # changes left on another branch are evidence too
    tree = json.loads((run / "manifest.json").read_text())["fixture_tree"]
    assert str(run / "artefacts" / "refs.txt") in text and f"diff --no-ext-diff {tree}" in text


def test_a_relative_runs_directory_becomes_absolute_in_the_prompt(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("prepare.tool_versions", lambda: TOOLS)
    assert main(["runs", "s2", "--reps", "1", "--arm", "baseline", "--session-context", "t"]) == 0
    prompt = (tmp_path / "runs" / "s2-r1" / "prompt.txt").read_text()
    assert f"`{tmp_path.resolve() / 'runs' / 's2-r1' / 'repo'}`" in prompt
