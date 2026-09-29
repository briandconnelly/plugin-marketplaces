"""Prepare scenario runs: RUNS/sN-rK/ with the fixture repository, mirror, prompt, and manifest.

Usage: uv run python tests/eval/prepare.py RUNS sN --reps 3 --arm baseline|with-skill
         --session-context "TEXT" [--first-rep 1]

A with-skill run also gets the committed skill (never the working copy) at
RUNS/sN-rK/skill/plugin-marketplaces/ and its validator installed, byte-compiled, into
RUNS/sN-rK/validator/, so running it writes nothing outside the arm's WORKDIR.
"""

from __future__ import annotations

import argparse
import datetime
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path
from types import ModuleType

from scenario_doc import DOC, ROOT, dispatch_prompt
from scenario_doc import scenario as scenario_of

SCENARIOS = ROOT / "tests" / "fixtures" / "scenarios"
SKILL_PATH = "skills/plugin-marketplaces"
# Git ignores the user's and the system's configuration here: no signing, no external diff
# tool, no excludes, SHA-1 objects; only the fixture decides the tree id.
GIT_ENV = {
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_AUTHOR_NAME": "fixture",
    "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
    "GIT_COMMITTER_NAME": "fixture",
    "GIT_COMMITTER_EMAIL": "fixture@example.invalid",
}


def git(repo: Path, *args: str) -> str:
    env = {**os.environ, **GIT_ENV}
    for key in ("GIT_DIR", "GIT_INDEX_FILE", "GIT_WORK_TREE"):
        env.pop(key, None)
    return subprocess.run(
        ["git", "-C", str(repo), *args], env=env, check=True, capture_output=True, text=True
    ).stdout


def _load(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(f"loaded_{path.stem}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _extract(tree: str, dest: Path) -> None:
    """Write a tree-ish of this repository to `dest`, as committed."""
    archive = subprocess.run(
        ["git", "-C", str(ROOT), "archive", "--format=tar", tree],
        check=True,
        capture_output=True,
    ).stdout
    dest.mkdir(parents=True)
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        tar.extractall(dest, filter="data")


def skill_tree() -> str:
    return subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", f"HEAD:{SKILL_PATH}"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def skill_is_committed() -> bool:
    status = subprocess.run(
        ["git", "-C", str(ROOT), "status", "--porcelain", "--", SKILL_PATH, "pyproject.toml"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return status == ""


def install_skill(run: Path) -> tuple[Path, Path, str]:
    """Copy the committed skill into the run and install its validator beside it."""
    tree = skill_tree()
    skill = run / "skill" / "plugin-marketplaces"
    _extract(tree, skill)
    env = {
        k: v for k, v in os.environ.items() if k not in ("VIRTUAL_ENV", "UV_PROJECT_ENVIRONMENT")
    }
    venv = run / "validator"
    with tempfile.TemporaryDirectory(prefix="validator-src-") as src:
        _extract("HEAD", Path(src) / "repo")
        subprocess.run(["uv", "venv", "--quiet", str(venv)], env=env, check=True)
        subprocess.run(
            [
                "uv",
                "pip",
                "install",
                "--quiet",
                "--compile-bytecode",
                "--python",
                str(venv / "bin" / "python"),
                f"{src}/repo",
            ],
            env=env,
            check=True,
        )
    return skill, venv / "bin" / "check-marketplace", tree


def tool_versions() -> dict[str, str]:
    versions: dict[str, str] = {}
    with tempfile.TemporaryDirectory(prefix="versions-") as home:
        env = {
            **os.environ,
            "CLAUDE_CONFIG_DIR": f"{home}/claude",
            "CODEX_HOME": home,
            "COPILOT_HOME": f"{home}/copilot",
            "COPILOT_CACHE_HOME": f"{home}/copilot-cache",
        }
        for tool in ("claude", "codex", "copilot"):
            if shutil.which(tool) is None:
                versions[tool] = "not installed"
                continue
            proc = subprocess.run(
                [tool, "--version"],
                env=env,
                capture_output=True,
                text=True,
                timeout=60,
                stdin=subprocess.DEVNULL,
                check=False,
            )
            versions[tool] = (proc.stdout or proc.stderr).strip().splitlines()[0]
    return versions


def prepare(
    runs: Path,
    scenario: str,
    reps: int,
    arm: str,
    session_context: str,
    first_rep: int = 1,
    tools: dict[str, str] | None = None,
) -> list[Path]:
    number = int(scenario.removeprefix("s"))
    doc = DOC.read_text(encoding="utf-8")
    pinned = _load(ROOT / "tests" / "test_scenario_fixtures.py").BASELINE_TREES[scenario]
    tools = tool_versions() if tools is None else tools
    made = []
    for rep in range(first_rep, first_rep + reps):
        run = runs / f"{scenario}-r{rep}"
        run.mkdir(parents=True)  # never reuse a run directory
        work = run / "repo"
        shutil.copytree(SCENARIOS / scenario / "repo", work)
        git(work, "init", "-q", "--object-format=sha1")
        (work / ".git" / "info" / "exclude").write_text(".tool-homes/\n", encoding="utf-8")
        git(work, "add", "-A")
        git(work, "commit", "-q", "-m", f"fixture {scenario}")
        tree = git(work, "rev-parse", "HEAD^{tree}").strip()
        if tree != pinned:
            raise RuntimeError(f"{scenario}: fixture tree {tree} is not the pinned {pinned}")
        upstream, commits = None, None
        if scenario_of(doc, number).has_upstream:
            upstream = run / "weather-mcp"
            commits = _load(SCENARIOS / "make_upstream.py").build(upstream)
        skill = validator = tree_of_skill = None
        if arm == "with-skill":
            skill, validator, tree_of_skill = install_skill(run)
        prompt = dispatch_prompt(doc, number, work, upstream, skill=skill, validator=validator)
        (run / "prompt.txt").write_text(prompt, encoding="utf-8")
        manifest = {
            "date": datetime.date.today().isoformat(),
            "arm": arm,
            "scenario": scenario,
            "rep": rep,
            "fixture_tree": tree,
            "upstream_commits": commits,
            "tools": tools,
            "session_context": session_context,
            "prompt_file": "prompt.txt",
        }
        if skill is not None:
            manifest.update(skill=str(skill), validator=str(validator), skill_tree=tree_of_skill)
        (run / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        made.append(run)
    return made


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prepare scenario runs.")
    parser.add_argument("runs", type=Path)
    parser.add_argument("scenario", choices=[f"s{n}" for n in range(1, 8)])
    parser.add_argument("--reps", type=int, default=3)
    parser.add_argument("--first-rep", type=int, default=1)
    parser.add_argument("--arm", choices=("baseline", "with-skill"), required=True)
    parser.add_argument("--session-context", required=True)
    args = parser.parse_args(argv)
    if args.arm == "with-skill" and not skill_is_committed():
        parser.error(
            f"commit {SKILL_PATH} and pyproject.toml first: a run uses the committed skill"
        )
    for run in prepare(
        args.runs.resolve(),
        args.scenario,
        args.reps,
        args.arm,
        args.session_context,
        args.first_rep,
    ):
        print(run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
