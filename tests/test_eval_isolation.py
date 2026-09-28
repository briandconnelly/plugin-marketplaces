"""Calibrate the isolation checker on the plan-2a arms, whose violations were adjudicated by hand.

Records rewrite the run directory to `$RUN` and its parent to `$SCRATCH`; the test maps them
back to fixed paths. Plan-2a arms shared one parent directory, so `run_dir` is None and any
read of the parent is flagged. Each expected set is exact: a checker change that adds or
drops a flag on these arms must update this table deliberately.
"""

from pathlib import Path

import pytest
from isolation import Layout, check_calls, symlink_flags
from records import load, tool_calls

RUNS = Path(__file__).resolve().parent / "runs"
EXPECTED = {
    # wrote probe directories into the parent of its runs directory, read the harness's
    # tool-results file under ~/.claude, ran codex against homes outside WORKDIR, and
    # ran `codex debug prompt-input` twice
    "s1-baseline-discarded": {
        "outside-read": [7, 10, 11, 15, 17, 21, 22, 23, 24],
        "outside-write": [15, 17, 21, 22, 23],
        "cli-env": [15, 17, 22, 23, 24],
        "cli-prompt": [21, 25],
    },
    "s2-baseline": {},
    # listed the shared parent (#0) and copied itself to ../s3-copy-for-test (#7): plan 2a's
    # checker missed both, so this scored run was not isolated
    "s3-baseline": {"outside-read": [0], "outside-write": [7]},
    # `git init --bare ../s3-fake-remote.git` after a heredoc (#8), then `cd $RUN` (#9)
    "s3-rep2-baseline-discarded": {
        "outside-read": [1, 9],
        "outside-write": [8],
        "cli-prompt": [14, 19],
    },
    # every CLI call sourced .tool-homes/env.sh, so no cli-env flag; #34 and #44 are prompt
    # text ("/review") read as paths; #54 runs a script the transcript never shows
    "s4-baseline-discarded": {
        "cli-prompt": [
            10,
            17,
            18,
            19,
            24,
            25,
            26,
            30,
            31,
            32,
            33,
            34,
            35,
            36,
            39,
            41,
            43,
            44,
            47,
            50,
            53,
        ],
        "outside-read": [34, 44],
        "sourced-unknown": [54],
    },
    "s5-baseline": {},
    "s6-baseline": {"outside-read": [1]},  # `ls -la ..` listed the shared parent
    "s7-baseline": {},
}


def layout(scenario: str) -> Layout:
    return Layout(
        work=f"/R/run/{scenario}",
        upstream=f"/R/run/{scenario}-upstream",
        run_dir=None,
        home="/Users/owner",
        start_cwd="/Users/owner/projects/skills",
    )


@pytest.mark.parametrize("name", sorted(EXPECTED))
def test_flags_on_the_plan_2a_arms(name):
    text = load(RUNS / f"2026-09-28-{name}.md").replace("$RUN", "/R/run").replace("$SCRATCH", "/R")
    flags = check_calls(tool_calls(text), layout(name.split("-")[0]))
    found: dict[str, list[int]] = {}
    for flag in flags:
        if flag.call not in found.setdefault(flag.kind, []):
            found[flag.kind].append(flag.call)
    assert {k: sorted(v) for k, v in found.items()} == EXPECTED[name]


def private(tmp: str = "/R/s2-r1") -> Layout:
    return Layout(f"{tmp}/repo", None, tmp, "/Users/owner", "/Users/owner/projects/skills")


def kinds(command: str, lay: Layout | None = None) -> list[str]:
    return [
        f.kind
        for f in check_calls([{"tool": "Bash", "input": {"command": command}}], lay or private())
    ]


def test_a_private_run_directory_may_be_listed_but_not_written():
    assert kinds("cd /R/s2-r1/repo && ls .. && cat ../manifest.json") == []
    assert kinds("cd /R/s2-r1/repo && touch ../stray") == ["outside-write"]
    assert kinds("cd /R/s2-r1/repo && ls ../../s3-r1") == ["outside-read"]


def test_commands_after_a_heredoc_are_checked_and_its_body_is_not():
    command = "cd /R/s2-r1/repo && cat > notes.md <<'EOF'\nsee /etc/passwd\nEOF\ntouch /tmp/x"
    assert kinds(command) == ["outside-write"]


def test_a_sourced_heredoc_file_sets_the_tool_variables():
    command = (
        "cd /R/s2-r1/repo && cat > .tool-homes/env.sh <<'EOF'\n"
        "export CODEX_HOME=$PWD/.tool-homes/codex\nEOF\n"
        ". .tool-homes/env.sh; codex plugin list"
    )
    assert kinds(command) == []
    assert kinds("cd /R/s2-r1/repo && CODEX_HOME=/tmp/c codex plugin list") == ["cli-env"]
    # assigned but not exported: codex never sees it
    assert kinds("cd /R/s2-r1/repo && CODEX_HOME=$PWD/h; codex plugin list") == ["cli-env"]


def test_prompts_are_flagged_and_version_checks_are_not():
    base = "cd /R/s2-r1/repo && export CLAUDE_CONFIG_DIR=$PWD/h; "
    assert kinds(base + "claude -p hi") == ["cli-prompt"]
    assert kinds(base + "perl -e 'alarm 9; exec @ARGV' claude --print hi") == ["cli-prompt"]
    assert kinds("claude --version; codex --help") == []
    # a prompt wrapped in a shell string is still a prompt
    assert kinds(base + "sh -c 'claude -p hi'") == ["cli-prompt"]
    assert kinds("cd /R/s2-r1/repo && CODEX_HOME=$PWD/h bash -c 'codex plugin list'") == []


def test_tmp_is_not_allowed():
    assert kinds("cd /R/s2-r1/repo && ls /tmp/scratch") == ["outside-read"]


def test_a_symlink_out_of_the_run_directory_is_flagged(tmp_path):
    run = tmp_path / "s2-r1"
    (run / "repo" / ".tool-homes").mkdir(parents=True)
    (run / "weather-mcp").mkdir()
    (run / "repo" / "inside").symlink_to(run / "weather-mcp")
    (run / "repo" / ".tool-homes" / "codex").symlink_to(tmp_path / "real-home")
    flags = symlink_flags(run / "repo", run)
    assert [(f.call, f.kind) for f in flags] == [(-1, "symlink-outside")]
    assert str(flags[0]).startswith("after the run symlink-outside: ")


def test_an_assigned_home_is_used_for_home_expansion():
    # arms isolate tools by exporting HOME under .tool-homes/, then create it
    assert kinds("cd /R/s2-r1/repo && export HOME=$PWD/.tool-homes/home; mkdir -p $HOME ~/x") == []
    assert kinds("cd /R/s2-r1/repo && mkdir -p $HOME") == ["outside-write"]
