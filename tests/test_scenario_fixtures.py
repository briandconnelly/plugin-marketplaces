"""Pin what the offline validator reports on each scenario fixture.

The lists come from running the validator on the fixtures when they were designed
(2026-09-28); a change here means a fixture changed, which invalidates runs scored on it.
"""

import importlib.util
import os
import shutil
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest
from mpcheck.run import run_checks

SCENARIOS = Path(__file__).resolve().parent / "fixtures" / "scenarios"
EXPECTED = {
    "s1": ["local.reader-no-catalog", "local.reader-no-catalog", "schema.parse.no-catalog"],
    "s2": [],
    "s3": ["local.reader-no-catalog", "local.reader-no-catalog", "schema.parse.no-catalog"],
    "s4": [],
    "s5": [],
    "s6": [
        "local.entry-hooks-path",
        "local.name-mismatch",
        "local.path-prefix",
        "local.pin-missing",
        "local.source-type",
        "local.version-mismatch",
    ],
    "s7": ["local.source-type", "local.version-mismatch"],
}


@pytest.mark.parametrize("name", sorted(EXPECTED))
def test_fixture_validator_view(name):
    base = SCENARIOS / name
    report = run_checks(base / "repo", policy_path=base / "policy.json", use_claude=False)
    assert sorted(f.check for f in report.findings) == EXPECTED[name]


def _load(name: str) -> ModuleType:
    # Loaded by path: the fixture scripts are not a package, and `build` would collide
    # with the PyPI module of the same name.
    spec = importlib.util.spec_from_file_location(f"scenario_{name}", SCENARIOS / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_upstream_mirror_has_the_pinned_commits(tmp_path):
    fixtures, upstream = _load("build"), _load("make_upstream")
    expected = {"v1.3.0": fixtures.SHA_A, "v1.4.0": fixtures.SHA_B}
    assert upstream.build(tmp_path / "weather-mcp") == expected


def test_builder_is_deterministic(tmp_path):
    before = {p: p.read_bytes() for p in SCENARIOS.rglob("*") if p.is_file()}
    subprocess.run([sys.executable, str(SCENARIOS / "build.py")], check=True, timeout=60)
    after = {p: p.read_bytes() for p in SCENARIOS.rglob("*") if p.is_file()}
    assert before == after


# Git tree ids of each fixture's repo/ as plan 2b's baseline arms receive it (s1 and s3 are
# unchanged since the 2026-09-28 runs). A change to fixture text or file modes changes the
# id; update it deliberately, and rerun every baseline scored on the old tree.
BASELINE_TREES = {
    "s1": "bbbee65bda60271b35ef02237247ed5a619a1747",
    "s2": "8640972fd67d9623c6fb9326a72c38420402842e",
    "s3": "50fa9cb7145a617760121a0ed90bce9b90865a60",
    "s4": "5636a130e9dfed2c78f60f0a2718f62fef2c7d5c",
    "s5": "e094a00c209f1071c436a232253789e75e77ba26",
    "s6": "afcbd4f3ad05e27bbd196147f6fbc797d3b18c3d",
    "s7": "a5f8fa95111facb139b19b10f0aa47f98a64918e",
}


def fixture_tree(name: str, tmp_path: Path) -> str:
    work = tmp_path / name
    shutil.copytree(SCENARIOS / name / "repo", work)

    # Isolated from user and system git config, SHA-1, and force-added past any excludes,
    # so the id depends only on the fixture's content and modes.
    env = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}

    def git(*args: str) -> str:
        return subprocess.run(
            ["git", "-C", str(work), *args], check=True, capture_output=True, text=True, env=env
        ).stdout.strip()

    git("init", "-q", "--object-format=sha1")
    git("add", "-A", "-f")
    return git("write-tree")


@pytest.mark.parametrize("name", sorted(BASELINE_TREES))
def test_fixture_tree_matches_the_baseline_runs(name, tmp_path):
    assert fixture_tree(name, tmp_path) == BASELINE_TREES[name]


@pytest.fixture
def hostile_git(tmp_path, monkeypatch):
    """A user git config that would break naive fixture commands."""
    excludes = tmp_path / "global-excludes"
    excludes.write_text("*.json\n", encoding="utf-8")
    config = tmp_path / "gitconfig"
    config.write_text(
        "[init]\n\tdefaultObjectFormat = sha256\n"
        "[commit]\n\tgpgSign = true\n"
        "[core]\n\tautocrlf = true\n"
        f"[core]\n\texcludesFile = {excludes}\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(config))


def test_upstream_mirror_ignores_user_git_config(tmp_path, hostile_git):
    fixtures, upstream = _load("build"), _load("make_upstream")
    expected = {"v1.3.0": fixtures.SHA_A, "v1.4.0": fixtures.SHA_B}
    assert upstream.build(tmp_path / "weather-mcp") == expected


def test_fixture_tree_ignores_user_git_config(tmp_path, hostile_git):
    assert fixture_tree("s6", tmp_path) == BASELINE_TREES["s6"]


def test_s6_ok_tools_has_nothing_true_to_report():
    # criterion 8 ("no finding reports a problem with ok-tools") measures false positives
    # only if ok-tools itself is clean: one description everywhere and a real skill body
    import json

    repo = SCENARIOS / "s6" / "repo"
    catalog = json.loads((repo / ".claude-plugin" / "marketplace.json").read_text())
    entry = next(e for e in catalog["plugins"] if e["name"] == "ok-tools")
    manifest = json.loads((repo / "plugins/ok-tools/.claude-plugin/plugin.json").read_text())
    assert manifest["description"] == entry["description"]
    body = (repo / "plugins/ok-tools/skills/ok-tools/SKILL.md").read_text().split("---\n", 2)[2]
    assert len([line for line in body.splitlines() if line.strip()]) >= 4, body
