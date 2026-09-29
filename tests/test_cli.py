import json
import subprocess
from pathlib import Path

import check_marketplace
import mpcheck.cli
from helpers import read, write
from mpcheck.model import Severity, Status
from mpcheck.run import run_checks

SCRIPT = Path(check_marketplace.__file__)


def test_clean_market_exits_zero(market, capsys):
    assert check_marketplace.main([str(market), "--no-claude"]) == 0
    out = capsys.readouterr().out
    assert "No findings." in out
    assert f"  {'schema.claude-validate':24} skipped  (disabled with --no-claude)" in out


def test_defect_exits_one_and_json_is_parseable(market, capsys):
    data = read(market, ".claude-plugin/marketplace.json")
    data["plugins"][0]["source"] = "plugins/alpha"
    write(market, ".claude-plugin/marketplace.json", data)
    assert check_marketplace.main([str(market), "--no-claude", "--format", "json"]) == 1
    report = json.loads(capsys.readouterr().out)
    assert report["statuses"]["local"]["status"] == "failed"
    assert any(f["check"] == "local.path-prefix" and f["rule"] == "R3" for f in report["findings"])


def test_warnings_fail_only_on_request(market):
    write(market, "marketplace-policy.json", {"readers": ["codex"]})
    assert check_marketplace.main([str(market), "--no-claude"]) == 0
    assert check_marketplace.main([str(market), "--no-claude", "--fail-on", "warning"]) == 1


def test_unimplemented_levels_are_skipped_not_passed(market):
    statuses = run_checks(market, use_claude=False).statuses
    for group in ("remote", "discovery", "package-load", "schema.claude-validate"):
        assert statuses[group][0] == Status.SKIPPED
    assert statuses["schema.portable"] == (Status.PASSED, "manifests=1 mcp.json=0 servers=0")


def test_no_portable_manifest_means_portable_skipped(market):
    (market / "plugins/alpha/plugin.json").unlink()
    assert run_checks(market, use_claude=False).statuses["schema.portable"][0] == Status.SKIPPED


def test_empty_repo_fails(tmp_path):
    report = run_checks(tmp_path, use_claude=False)
    assert report.exit_code(Severity.ERROR) == 1
    assert report.statuses["schema.parse"][0] == Status.FAILED
    assert report.statuses["local"][0] == Status.SKIPPED


def test_validator_crash_exits_two(market, monkeypatch, capsys):
    def boom(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(mpcheck.cli, "run_checks", boom)
    assert check_marketplace.main([str(market)]) == 2
    assert "validator failure" in capsys.readouterr().err


def test_runs_as_a_uv_script(market):
    proc = subprocess.run(
        ["uv", "run", "--script", str(SCRIPT), str(market), "--no-claude"],
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert "No findings." in proc.stdout


def test_claude_only_marketplace_is_not_checked_for_codex(tmp_path):
    source = {"source": "github", "repo": "example/beta", "sha": "a" * 40}
    write(
        tmp_path,
        ".claude-plugin/marketplace.json",
        {"name": "demo", "owner": {"name": "T"}, "plugins": [{"name": "beta", "source": source}]},
    )
    report = run_checks(tmp_path, use_claude=False)
    assert sorted(f.check for f in report.findings) == ["policy.inferred"]
    assert report.exit_code(Severity.ERROR) == 0


def test_a_missing_root_is_a_validator_failure(tmp_path, capsys):
    # PR #1 deferred: a mistyped path used to be reported as "no catalog found" and exit 1
    missing = tmp_path / "no-such-marketplace"
    assert check_marketplace.main([str(missing), "--no-claude"]) == 2
    assert "is not a directory" in capsys.readouterr().err


def test_policy_is_skipped_not_passed_when_no_reader_is_declared_or_inferred(tmp_path):
    # PR #1 deferred: with no readers there is nothing to check compatibility against
    statuses = run_checks(tmp_path, use_claude=False).statuses
    assert statuses["policy"][0] == Status.SKIPPED
    assert "no reader" in statuses["policy"][1]
