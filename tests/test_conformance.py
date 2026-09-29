"""The conformance probes' plumbing, offline: parsers, statuses, the sandbox allowlist,
help pins, and the link between each probe and the reference lines it re-checks (spec §9)."""

from __future__ import annotations

import re
import shutil
from pathlib import Path

import pytest
from conformance import run
from conformance.probes import (
    PROBES,
    Observation,
    Probe,
    claude_error_paths,
    claude_skills,
    claude_version,
    codex_available,
    copilot_browse,
    copilot_plugin_skills,
)
from conformance.sandbox import Result, Sandbox, check_allowed

ROOT = Path(__file__).resolve().parents[1]
REFS = ROOT / "skills" / "plugin-marketplaces" / "references"
CITE = re.compile(r"\[E\d+\]")

DETAILS = """cmd 0.1.0
  Source: cmd@mkt

Component inventory
  Skills (2)  hello, review
  Agents (0)
"""
SKILL_LIST = """Plugin skills:
  hello - Say hello when asked to greet.
  review - Review the current diff

Builtin skills:
  customize-cloud-agent - Skill for customizing the Copilot cloud agent
"""
VALIDATE = '{"manifest": {"errors": [{"path": "plugins.2.hooks", "message": "Invalid input"}]}}'


# ---- parsers, on output recorded from claude 2.1.284, codex-cli 0.157.1, copilot 1.0.89


def test_claude_details_parsers():
    assert claude_skills(DETAILS) == ["hello", "review"]
    assert claude_skills(DETAILS.replace("(2)  hello, review", "(1)  hello")) == ["hello"]
    assert claude_skills(DETAILS.replace("(2)  hello, review", "(0)")) == []
    assert claude_version(DETAILS, "cmd") == "0.1.0"
    with pytest.raises(ValueError):
        claude_skills("no inventory here")
    with pytest.raises(ValueError):
        claude_version(DETAILS, "other")


def test_claude_validate_parser():
    assert claude_error_paths(VALIDATE) == ["plugins.2.hooks"]
    assert claude_error_paths('{"manifest": {"errors": []}}') == []


def test_codex_and_copilot_list_parsers():
    listing = '{"installed": [], "available": [{"name": "a"}, {"name": "gh"}]}'
    assert codex_available(listing) == ["a", "gh"]
    assert copilot_browse('[{"name": "a", "marketplace": "m"}]') == ["a"]


def test_copilot_skill_list_parser_reads_only_plugin_skills():
    assert copilot_plugin_skills(SKILL_LIST) == ["hello", "review"]
    assert copilot_plugin_skills(
        SKILL_LIST.replace("  review - Review the current diff\n", "")
    ) == ["hello"]
    assert copilot_plugin_skills("Builtin skills:\n  x - y\n") == []
    prefixed = SKILL_LIST.replace("  hello", "  cmd:hello")
    assert copilot_plugin_skills(prefixed) == ["cmd:hello", "review"]


# ---- statuses: every status is reachable, so a run of all-held results means something


def probe(tools: tuple[str, ...] = ("sh",)) -> Probe:
    return Probe(
        "p",
        tools,
        (("codex.md", "x"),),
        "a fact",
        "a control",
        lambda _: Observation(True, True, ""),
    )


@pytest.mark.parametrize(
    ("seen", "status"),
    [
        (Observation(True, True, "d"), "held"),
        (Observation(True, False, "d"), "flipped"),
        (Observation(False, True, "d"), "broken"),
        (Observation(False, False, "d"), "broken"),
    ],
)
def test_classify_maps_observations_to_statuses(seen, status):
    assert run.classify(probe(), lambda: seen).status == status


def test_classify_reports_a_crash_as_error_not_held():
    def boom() -> Observation:
        raise RuntimeError("`codex plugin add` exited 1: nope")

    result = run.classify(probe(), boom)
    assert result.status == "error" and "exited 1" in result.detail


def test_classify_skips_when_a_tool_is_missing():
    result = run.classify(
        probe(("definitely-not-a-tool-xyz",)), lambda: Observation(True, True, "")
    )
    assert result.status == "skipped"


def test_scrub_removes_the_work_directory(tmp_path):
    result = run.ProbeResult("p", "held", "f", [], f"at {tmp_path.resolve()}/x and {tmp_path}/y")
    assert str(tmp_path) not in run.scrub(result, tmp_path).detail


def test_markdown_names_the_lines_to_reverify_for_a_flipped_probe():
    report = {
        "versions": {"codex": "codex-cli 0.158.0"},
        "network_denied": True,
        "probes": [
            {
                "id": "p",
                "status": "flipped",
                "fact": "F",
                "anchors": [["codex.md", "phrase"]],
                "detail": "a\nb | c",
            }
        ],
        "help": [],
    }
    text = run.markdown(report)
    assert "| `p` | flipped | a b / c |" in text
    assert "re-verify `codex.md`: the line containing “phrase”" in text


# ---- the sandbox never runs a command that may prompt a model or start plugin code


@pytest.mark.parametrize(
    "argv",
    [
        ("claude", "mcp", "list"),
        ("codex", "debug", "prompt-input"),
        ("codex", "exec", "hi"),
        ("copilot", "-p", "hi"),
        ("copilot", "--acp"),
        ("claude", "-p", "hi"),
        ("claude",),
        ("/usr/local/bin/codex", "login"),
    ],
)
def test_sandbox_refuses_commands_outside_the_allowlist(argv):
    with pytest.raises(ValueError):
        check_allowed(argv)


@pytest.mark.parametrize(
    "argv",
    [
        ("claude", "plugin", "details", "a@m"),
        ("codex", "plugin", "list"),
        ("copilot", "skill", "list"),
        ("git", "status"),
    ],
)
def test_sandbox_allows_plugin_commands(argv):
    check_allowed(argv)


def test_every_probe_command_is_allowed():
    # the probes' own argv, read from their source, must pass the allowlist
    source = (ROOT / "tests" / "conformance" / "probes.py").read_text(encoding="utf-8")
    calls = re.findall(r'\.run\(\s*("(?:claude|codex|copilot)"(?:,\s*"[^"]+")+)', source)
    assert calls
    for call in calls:
        check_allowed(tuple(re.findall(r'"([^"]+)"', call)))


def test_the_sandbox_passes_no_credentials_and_keeps_every_home_inside_it(tmp_path, monkeypatch):
    for name in (
        "GITHUB_TOKEN",
        "GH_TOKEN",
        "ANTHROPIC_API_KEY",
        "OPENAI_API_KEY",
        "COPILOT_TOKEN",
    ):
        monkeypatch.setenv(name, "secret")
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", "/real/claude")
    env = Sandbox(tmp_path, deny_network=False).env
    assert not {k for k, v in env.items() if v == "secret"}
    homes = ("HOME", "XDG_CONFIG_HOME", "XDG_CACHE_HOME", "TMPDIR", "GIT_CONFIG_GLOBAL",
             "CLAUDE_CONFIG_DIR", "CODEX_HOME", "COPILOT_HOME", "COPILOT_CACHE_HOME")  # fmt: skip
    for name in homes:
        assert Path(env[name]).is_relative_to(tmp_path), name


# ---- help pins


class FakeSandbox:
    def __init__(self, output: str) -> None:
        self.output = output

    def run(self, *argv: str) -> Result:
        return Result(argv, 0, self.output)


@pytest.fixture
def help_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(run, "HELP_DIR", tmp_path)
    monkeypatch.setattr(shutil, "which", lambda _: "/bin/true")
    return tmp_path


def test_help_pin_same_changed_and_unpinned(help_dir):
    argv = ("codex", "plugin", "--help")
    assert run.check_help(argv, FakeSandbox("x")).status == "unpinned"
    (help_dir / "codex-plugin.txt").write_text("Usage: a\n", encoding="utf-8")
    assert run.check_help(argv, FakeSandbox("Usage: a\n")).status == "same"
    changed = run.check_help(argv, FakeSandbox("Usage: b\n"))
    assert (
        changed.status == "changed" and "-Usage: a" in changed.diff and "+Usage: b" in changed.diff
    )


def test_help_pins_exist_for_every_help_command():
    pinned = {p.name for p in (ROOT / "tests" / "conformance" / "help").glob("*.txt")}
    assert pinned == {run.help_file(a).name for a in run.HELP_COMMANDS}
    evidence = (ROOT / "tests" / "conformance" / "help" / "EVIDENCE").read_text().strip()
    assert evidence.startswith("docs/research/") and (ROOT / evidence).is_file()
    record = (ROOT / evidence).read_text(encoding="utf-8")
    for path in (ROOT / "tests" / "conformance" / "help").glob("*.txt"):
        assert run.sha256(path.read_text(encoding="utf-8")) in record, path.name


def test_repin_help_refuses_unless_the_record_names_each_text(help_dir, monkeypatch):
    research = help_dir / "docs" / "research"
    research.mkdir(parents=True)
    monkeypatch.setattr(run, "ROOT", help_dir)
    monkeypatch.setattr(run, "Sandbox", lambda _: FakeSandbox("Usage: x\n"))
    (research / "r.md").write_text("help re-read\n", encoding="utf-8")
    assert run.repin_help("docs/research/r.md", help_dir) == 2
    assert not list(help_dir.glob("*.txt"))
    (research / "r.md").write_text(
        f"help sha256 {run.sha256('Usage: x' + chr(10))}\n", encoding="utf-8"
    )
    assert run.repin_help("docs/research/r.md", help_dir) == 0
    assert len(list(help_dir.glob("*.txt"))) == len(run.HELP_COMMANDS)


# ---- each probe points at reference lines, and each reference names its probes


def test_probe_ids_are_unique():
    ids = [p.id for p in PROBES]
    assert len(ids) == len(set(ids))


@pytest.mark.parametrize("p", PROBES, ids=lambda p: p.id)
def test_each_anchor_is_one_cited_line(p):
    for ref, phrase in p.anchors:
        lines = [ln for ln in (REFS / ref).read_text(encoding="utf-8").splitlines() if phrase in ln]
        assert len(lines) == 1, f"{ref}: {phrase!r} matches {len(lines)} lines"
        assert CITE.search(lines[0]), f"{ref}: the anchored line cites no evidence"


def test_each_reference_lists_the_probes_that_recheck_it():
    expected: dict[str, set[str]] = {}
    for p in PROBES:
        for ref, _ in p.anchors:
            expected.setdefault(ref, set()).add(p.id)
    for path in sorted(REFS.glob("*.md")):
        line = re.search(r"^Conformance probes: (.+)\.$", path.read_text(encoding="utf-8"), re.M)
        assert line, f"{path.name} has no 'Conformance probes:' line"
        listed = (
            set() if line.group(1) == "none yet" else set(re.findall(r"`([^`]+)`", line.group(1)))
        )
        assert listed == expected.get(path.name, set()), path.name


@pytest.mark.live
def test_every_probe_holds_against_the_installed_tools(tmp_path):
    for p in PROBES:
        work = tmp_path / p.id
        work.mkdir()
        result = run.classify(p, lambda p=p, w=work: p.run(w))
        assert result.status in ("held", "skipped"), (p.id, result.status, result.detail)
