"""Pin what the offline validator reports on each scenario fixture.

The lists come from running the validator on the fixtures when they were designed
(2026-09-28); a change here means a fixture changed, which invalidates runs scored on it.
"""

import importlib.util
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
    "s7": ["local.source-type"],
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
