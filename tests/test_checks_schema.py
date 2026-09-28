import hashlib
import json
import shutil
import subprocess

import pytest
from helpers import AP_MCP_SCHEMA, AP_SCHEMA, read, write
from mpcheck.checks_schema import SCHEMAS_DIR, check_portable, run_claude_validate
from mpcheck.discover import discover
from mpcheck.model import Status
from mpcheck.readers import load_readers

READERS = load_readers()
FOUND = "/usr/local/bin/claude"


def repo_of(root):
    return discover(root, READERS)[0]


def ids(findings):
    return sorted(f.check for f in findings)


def portable(root):
    return check_portable(repo_of(root))[0]


def test_vendored_schemas_match_recorded_digests():
    sums = SCHEMAS_DIR.parent / "SHA256SUMS"
    lines = sums.read_text(encoding="utf-8").splitlines()
    recorded = {name: digest for digest, name in (line.split(maxsplit=1) for line in lines)}
    assert set(recorded) == {
        "agent-plugins/1.0.0/plugin.schema.json",
        "agent-plugins/1.0.0/mcp.schema.json",
    }
    for name, digest in recorded.items():
        assert hashlib.sha256((SCHEMAS_DIR.parent / name).read_bytes()).hexdigest() == digest


def test_clean_portable_manifest(market):
    assert portable(market) == []


def test_unknown_top_level_key_is_a_warning(market):
    write(
        market,
        "plugins/alpha/plugin.json",
        {"$schema": AP_SCHEMA, "name": "alpha", "version": "1.2.0", "bogus": 1},
    )
    assert [(f.check, f.severity) for f in portable(market)] == [
        ("schema.portable.manifest", "warning")
    ]


def test_bad_name_is_an_error(market):
    write(
        market,
        "plugins/alpha/plugin.json",
        {"$schema": AP_SCHEMA, "name": "Alpha", "version": "1.2.0"},
    )
    assert [(f.check, f.severity, f.pointer) for f in portable(market)] == [
        ("schema.portable.manifest", "error", "/name")
    ]


def test_unsupported_schema_version(market):
    write(
        market,
        "plugins/alpha/plugin.json",
        {"$schema": "https://agent-plugins.org/schemas/9.9.9/plugin.schema.json", "name": "alpha"},
    )
    assert ids(portable(market)) == ["schema.portable.unsupported-version"]


def test_invalid_server_is_skipped_not_fatal(market):
    servers = {"good": {"type": "stdio", "command": "uvx"}, "bad": {"command": "uvx"}}
    write(market, "plugins/alpha/mcp.json", {"$schema": AP_MCP_SCHEMA, "mcpServers": servers})
    assert [(f.check, f.pointer) for f in portable(market)] == [
        ("schema.portable.mcp-server", "/mcpServers/bad")
    ]


def test_mcp_envelope_error_disables_mcp(market):
    write(
        market,
        "plugins/alpha/mcp.json",
        {"$schema": AP_MCP_SCHEMA, "mcpServers": {}, "extra": 1},
    )
    assert ids(portable(market)) == ["schema.portable.mcp"]


def test_mcp_version_must_match_plugin(market):
    write(
        market,
        "plugins/alpha/mcp.json",
        {"$schema": "https://agent-plugins.org/schemas/1.1.0/mcp.schema.json", "mcpServers": {}},
    )
    assert ids(portable(market)) == ["schema.portable.mcp"]


def test_portable_counts_what_was_checked(market):
    servers = {"a": {"type": "stdio", "command": "uvx"}, "b": {"type": "stdio", "command": "uvx"}}
    write(market, "plugins/alpha/mcp.json", {"$schema": AP_MCP_SCHEMA, "mcpServers": servers})
    findings, counts = check_portable(repo_of(market))
    assert findings == []
    assert counts.note() == "manifests=1 mcp.json=1 servers=2"


def fake_runner(stdout, returncode=0):
    def run(argv):
        assert argv[:5] == ["claude", "plugin", "validate", "--strict", "--json"]
        return subprocess.CompletedProcess(argv, returncode, stdout=stdout, stderr="")

    return run


def test_claude_missing_is_skipped(market):
    findings, status, note = run_claude_validate(repo_of(market), which=lambda _: None)
    assert (findings, status) == ([], Status.SKIPPED)
    assert "not on PATH" in note


def test_claude_report_is_mapped(market):
    report = {
        "success": False,
        "manifest": {
            "file": str((market / ".claude-plugin/marketplace.json").resolve()),
            "errors": [{"path": "plugins.1.source", "message": "Invalid input"}],
            "warnings": [{"path": "plugins[0].x", "message": "Unknown field 'x'."}],
        },
        "contents": [],
    }
    runner = fake_runner(json.dumps(report), 1)
    findings, status, _ = run_claude_validate(repo_of(market), runner=runner, which=lambda _: FOUND)
    assert status == Status.FAILED
    errors = [f for f in findings if f.check == "schema.claude-validate.error"]
    assert errors and errors[0].file == ".claude-plugin/marketplace.json"
    assert errors[0].pointer == "plugins.1.source"
    assert any(f.check == "schema.claude-validate.warning" for f in findings)


def test_claude_garbage_is_inconclusive(market):
    runner = fake_runner("not json", 2)
    findings, status, _ = run_claude_validate(repo_of(market), runner=runner, which=lambda _: FOUND)
    assert status == Status.INCONCLUSIVE
    assert "schema.claude-validate.crashed" in ids(findings)


def test_claude_empty_report_is_inconclusive(market):
    runner = fake_runner("{}", 2)
    findings, status, _ = run_claude_validate(repo_of(market), runner=runner, which=lambda _: FOUND)
    assert status == Status.INCONCLUSIVE
    assert ids(findings) == ["schema.claude-validate.crashed"] * 2


def test_claude_success_flag_contradicting_exit_code_is_inconclusive(market):
    report = {"success": True, "manifest": {"errors": [], "warnings": []}, "contents": []}
    runner = fake_runner(json.dumps(report), 1)
    _, status, _ = run_claude_validate(repo_of(market), runner=runner, which=lambda _: FOUND)
    assert status == Status.INCONCLUSIVE


@pytest.mark.skipif(shutil.which("claude") is None, reason="claude not installed")
def test_real_claude_catches_a_known_defect(market):
    data = read(market, ".claude-plugin/marketplace.json")
    data["plugins"][0]["source"] = "plugins/alpha"
    write(market, ".claude-plugin/marketplace.json", data)
    findings, status, _ = run_claude_validate(repo_of(market))
    assert status == Status.FAILED
    assert any(
        f.check == "schema.claude-validate.error" and "plugins.0.source" in f.pointer
        for f in findings
    )


def recording_runner(calls, report=None):
    report = report or {"success": True, "manifest": {"errors": [], "warnings": []}, "contents": []}

    def run(argv):
        calls.append(argv[-1])
        return subprocess.CompletedProcess(argv, 0, stdout=json.dumps(report), stderr="")

    return run


def test_claude_validates_every_local_plugin_once(market):
    write(market, "plugins/gamma/skills/g/SKILL.md", "---\nname: g\ndescription: G.\n---\n\nG.\n")
    for catalog in (".claude-plugin/marketplace.json", ".agents/plugins/marketplace.json"):
        data = read(market, catalog)
        data["plugins"].append({"name": "gamma", "source": "./plugins/gamma"})
        write(market, catalog, data)
    calls = []
    _, status, note = run_claude_validate(
        repo_of(market), runner=recording_runner(calls), which=lambda _: FOUND
    )
    root = market.resolve()
    assert sorted(calls) == sorted(
        str(p) for p in (root, root / "plugins/alpha", root / "plugins/gamma")
    )
    assert (status, note) == (Status.PASSED, "")


def test_plugin_that_is_its_own_marketplace_is_reported_unreachable(tmp_path):
    write(
        tmp_path,
        ".claude-plugin/marketplace.json",
        {"name": "solo", "owner": {"name": "T"}, "plugins": [{"name": "solo", "source": "./"}]},
    )
    write(tmp_path, ".claude-plugin/plugin.json", {"name": "solo", "version": "1.0.0"})
    calls = []
    findings, status, note = run_claude_validate(
        repo_of(tmp_path), runner=recording_runner(calls), which=lambda _: FOUND
    )
    assert calls == [str(tmp_path.resolve())]
    assert ids(findings) == ["schema.claude-validate.unreachable"]
    assert status == Status.PASSED
    assert note == "plugin-level validation unreachable for: ."


def test_nested_manifest_issues_are_not_reported_twice(market):
    nested = {"path": "plugins[0] plugin.json → author", "message": "No author information"}
    report = {"success": True, "manifest": {"errors": [], "warnings": [nested]}, "contents": []}
    findings, _, _ = run_claude_validate(
        repo_of(market), runner=recording_runner([], report), which=lambda _: FOUND
    )
    # plugin 0 (alpha) is validated directly, so only its direct run may report the issue;
    # the recording runner returns the same report for every target, hence one copy.
    assert [f.pointer for f in findings] == ["plugins[0] plugin.json → author"]


def test_manifestless_plugin_report_is_evidence(market):
    # Shape observed from `claude plugin validate --strict --json` 2.1.283 on a plugin
    # directory with a skill but no .claude-plugin/plugin.json.
    skill = str((market / "plugins/alpha/skills/hello/SKILL.md").resolve())
    report = {
        "success": False,
        "manifest": None,
        "contents": [
            {
                "file": skill,
                "type": "skill",
                "errors": [],
                "warnings": [{"path": "description", "message": "No description in frontmatter."}],
            }
        ],
    }
    findings, status, _ = run_claude_validate(
        repo_of(market), runner=fake_runner(json.dumps(report), 1), which=lambda _: FOUND
    )
    assert status == Status.PASSED
    assert "schema.claude-validate.crashed" not in ids(findings)
    assert any(f.file == "plugins/alpha/skills/hello/SKILL.md" for f in findings)


def test_report_without_manifest_key_is_inconclusive(market):
    report = {"success": True, "contents": []}
    _, status, _ = run_claude_validate(
        repo_of(market), runner=fake_runner(json.dumps(report), 0), which=lambda _: FOUND
    )
    assert status == Status.INCONCLUSIVE


def root_plugin_repo(root):
    write(
        root,
        ".claude-plugin/marketplace.json",
        {"name": "solo", "owner": {"name": "T"}, "plugins": [{"name": "solo", "source": "./"}]},
    )
    write(root, ".claude-plugin/plugin.json", {"name": "solo", "version": "1.0.0"})
    return repo_of(root)


def test_nested_error_is_kept_when_the_plugin_run_is_unreachable(tmp_path):
    # Shape observed from claude 2.1.283 on a repo whose root is marketplace and plugin.
    nested = {"path": "plugins[0] plugin.json → version", "message": "Invalid input"}
    report = {"success": False, "manifest": {"errors": [nested], "warnings": []}, "contents": []}
    runner = fake_runner(json.dumps(report), 1)
    findings, status, _ = run_claude_validate(
        root_plugin_repo(tmp_path), runner=runner, which=lambda _: FOUND
    )
    assert status == Status.FAILED
    assert [f.pointer for f in findings if f.check == "schema.claude-validate.error"] == [
        "plugins[0] plugin.json → version"
    ]


def test_reported_failure_with_nothing_surviving_is_inconclusive(market):
    # Every issue is a nested manifest issue for a directly validated plugin, so all are
    # filtered from the marketplace run; a failure with no surviving issue is not a pass.
    nested = {"path": "plugins[0] plugin.json → author", "message": "No author information"}
    failing = {"success": False, "manifest": {"errors": [], "warnings": [nested]}, "contents": []}
    passing = {"success": True, "manifest": {"errors": [], "warnings": []}, "contents": []}

    def run(argv):
        report, code = (failing, 1) if argv[-1] == str(market.resolve()) else (passing, 0)
        return subprocess.CompletedProcess(argv, code, stdout=json.dumps(report), stderr="")

    findings, status, _ = run_claude_validate(repo_of(market), runner=run, which=lambda _: FOUND)
    assert status == Status.INCONCLUSIVE
    assert "schema.claude-validate.crashed" in ids(findings)
