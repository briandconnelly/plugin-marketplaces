import json
import subprocess
from pathlib import Path

import pytest
from prepare import ROOT, main, prepare
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


def test_a_with_skill_run_gets_the_committed_skill_and_an_installed_validator(tmp_path):
    (run,) = prepare(tmp_path, "s2", 1, "with-skill", "test session", tools=TOOLS)
    manifest = json.loads((run / "manifest.json").read_text())
    skill, validator = Path(manifest["skill"]), Path(manifest["validator"])
    assert skill == run / "skill" / "plugin-marketplaces"
    assert validator == run / "validator" / "bin" / "check-marketplace"
    committed = subprocess.run(
        ["git", "-C", str(ROOT), "show", "HEAD:skills/plugin-marketplaces/SKILL.md"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    assert (skill / "SKILL.md").read_text() == committed
    assert (
        manifest["skill_tree"]
        == subprocess.run(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD:skills/plugin-marketplaces"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    )
    assert not list(skill.rglob("__pycache__"))
    prompt = (run / "prompt.txt").read_text()
    assert f"`{skill}/SKILL.md`" in prompt and f"`{validator}`" in prompt

    def listing():
        return sorted((str(p), p.stat().st_mtime_ns) for p in (run / "validator").rglob("*"))

    before = listing()
    done = subprocess.run(
        [str(validator), str(run / "repo"), "--no-claude", "--format", "json"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert done.returncode in (0, 1) and json.loads(done.stdout)["statuses"]["local"]
    # compiled at install, so running the validator writes nothing outside the arm's WORKDIR
    assert listing() == before


def test_a_baseline_run_has_no_skill(tmp_path):
    (run,) = prepare(tmp_path, "s7", 1, "baseline", "test session", tools=TOOLS)
    manifest = json.loads((run / "manifest.json").read_text())
    assert "skill" not in manifest and not (run / "skill").exists()
    assert "SKILL.md" not in (run / "prompt.txt").read_text()


def test_a_with_skill_run_refuses_an_uncommitted_skill(tmp_path, monkeypatch):
    import prepare as module

    monkeypatch.setattr(module, "skill_is_committed", lambda: False)
    with pytest.raises(SystemExit) as stop:
        main([str(tmp_path), "s2", "--arm", "with-skill", "--session-context", "x"])
    assert stop.value.code == 2 and not list(tmp_path.iterdir())


def test_a_with_skill_validator_is_installed_from_the_committed_lock(tmp_path):
    import hashlib
    import tomllib

    (run,) = prepare(tmp_path, "s7", 1, "with-skill", "test session", tools=TOOLS)
    manifest = json.loads((run / "manifest.json").read_text())
    lock = subprocess.run(
        ["git", "-C", str(ROOT), "show", "HEAD:uv.lock"], capture_output=True, check=True
    ).stdout
    assert manifest["lock_sha256"] == hashlib.sha256(lock).hexdigest()
    locked = {p["name"]: p["version"] for p in tomllib.loads(lock.decode())["package"]}
    python = Path(manifest["validator"]).parent / "python"
    for package in ("jsonschema", "referencing", "rpds-py"):
        installed = subprocess.run(
            [str(python), "-c", f"import importlib.metadata as m; print(m.version('{package}'))"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        assert installed == locked[package], package
