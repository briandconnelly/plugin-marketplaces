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
    # tool-results file under ~/.claude, and ran codex against homes outside WORKDIR; its two
    # `codex debug prompt-input` calls render locally and are allowed since the final
    # plan-2b review (as are s3-rep2 #14/#19 and s4 #10)
    "s1-baseline-discarded": {
        "outside-read": [7, 10, 11, 15, 17, 21, 22, 23, 24],
        "outside-write": [7, 15, 17, 21, 22, 23],
        "cli-env": [15, 17, 22, 23, 24],
        "remote-fetch": [7],  # curl of two documentation pages: flagged, allowed on reading
    },
    "s2-baseline": {},
    # listed the shared parent (#0) and copied itself to ../s3-copy-for-test (#7): plan 2a's
    # checker missed both, so this scored run was not isolated
    "s3-baseline": {"outside-read": [0], "outside-write": [7]},
    # `git init --bare ../s3-fake-remote.git` after a heredoc (#8), then `cd $RUN` and a bare
    # `rm -rf s3-fake-remote.git` (#9, a write since bare operands resolve against the cwd)
    "s3-rep2-baseline-discarded": {
        "outside-read": [1, 9],
        "outside-write": [8, 9],
    },
    # every CLI call sourced .tool-homes/env.sh, so no cli-env flag; #34 and #44 are prompt
    # text ("/review") read as paths; #54 runs a script the transcript never shows
    "s4-baseline-discarded": {
        "cli-prompt": [
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


def test_listing_git_refs_in_upstream_is_a_read():
    up = Layout("/R/s5-r1/repo", "/R/s5-r1/weather-mcp", "/R/s5-r1", "/Users/owner", "/start")
    reads = "cd /R/s5-r1/weather-mcp && git tag; git tag -l; git tag -n; git remote -v; git remote; git show-ref --tags -d"
    assert kinds(reads, up) == []
    writes = "cd /R/s5-r1/weather-mcp && git tag v9 && git remote add o x"
    assert kinds(writes, up) == ["outside-write", "outside-write"]


W = "cd /R/s2-r1/repo && "


def test_git_global_config_writes_are_checked_against_home_and_xdg():
    # plan-2b v1 s1-r3: a throwaway HOME with the real XDG_CONFIG_HOME wrote the owner's
    # ~/.config/git/config; the checker must not trust HOME alone
    assert kinds(W + "export HOME=$PWD/.tool-homes/h && git config --global url.x.insteadOf y") == [
        "outside-write"
    ]
    both = "export HOME=$PWD/.tool-homes/h XDG_CONFIG_HOME=$PWD/.tool-homes/x && "
    assert kinds(W + both + "git config --global url.x.insteadOf y") == []
    assert (
        kinds(W + "export GIT_CONFIG_GLOBAL=$PWD/.tool-homes/g && git config --global a.b c") == []
    )
    assert kinds(W + "git config --system a.b c") == ["outside-write"]


def test_the_v1_git_config_write_is_flagged():
    text = load(RUNS / "superseded-preamble-1" / "2026-09-28-s1-r3-baseline-discarded.md")
    text = (
        text.replace("$RUNS", "/R/runs").replace("$RUN", "/R/runs/s1-r3").replace("$SCRATCH", "/R")
    )
    lay = Layout(
        "/R/runs/s1-r3/repo", "/R/runs/s1-r3/weather-mcp", "/R/runs/s1-r3", "/Users/owner", "/start"
    )
    flags = check_calls(tool_calls(text), lay)
    assert any(f.call == 25 and f.kind == "outside-write" for f in flags), [
        str(f) for f in flags if f.call == 25
    ]


def test_executed_scripts_are_followed_or_flagged():
    written = {
        "tool": "Write",
        "input": {"file_path": "/R/s2-r1/repo/.tool-homes/probe.sh", "content": "copilot -p hi\n"},
    }
    run = {"tool": "Bash", "input": {"command": W + "./.tool-homes/probe.sh"}}
    assert "cli-prompt" in [f.kind for f in check_calls([written, run], private())]
    assert kinds(W + "./.tool-homes/made-elsewhere.sh") == ["sourced-unknown"]
    assert "cli-prompt" in kinds(W + "cat > p.sh <<'EOF'\ncopilot -p hi\nEOF\n./p.sh")


def test_local_only_subcommands_are_allowed_and_wrapped_commands_checked():
    env = "export CODEX_HOME=$PWD/h CLAUDE_CONFIG_DIR=$PWD/c COPILOT_HOME=$PWD/p COPILOT_CACHE_HOME=$PWD/q; "
    assert kinds(W + env + "codex debug prompt-input hi") == []
    assert kinds(W + env + "codex app-server generate-json-schema --out s") == []
    assert kinds(W + env + "codex --disable remote_plugin plugin list") == []
    assert kinds(W + env + "claude --plugin-dir $PWD/src mcp list") == []
    assert kinds(W + env + "copilot skill list") == []
    assert kinds(W + env + "codex sandbox -- codex plugin list") == []
    assert kinds(W + env + "codex sandbox -- copilot -p hi") == ["cli-prompt"]
    # a bare app-server is allowed only if its recorded JSON-RPC starts no turn: it is flagged
    # as a session so a person checks that, and `copilot --acp` stays forbidden
    assert kinds(W + env + "codex app-server") == ["cli-session"]
    assert kinds(W + env + "copilot --acp") == ["cli-prompt"]


def test_bare_write_operands_resolve_against_the_working_directory():
    # Copilot review of PR #3: a bare name written outside WORKDIR must flag
    assert kinds("touch stray") == ["outside-write"]
    assert kinds("cp /R/s2-r1/repo/README.md stray") == ["outside-write"]
    assert kinds("cd /R/s2-r1/repo && touch stray && cp README.md copy") == []


def test_unset_variables_no_longer_isolate_a_cli():
    env = "export CODEX_HOME=$PWD/h; "
    assert kinds(W + env + "codex plugin list") == []
    assert kinds(W + env + "env -u CODEX_HOME codex plugin list") == ["cli-env"]
    assert kinds(W + env + "unset CODEX_HOME; codex plugin list") == ["cli-env"]


def test_remote_fetches_are_flagged_for_adjudication():
    assert kinds(W + "git clone https://example.org/code.git clone") == ["remote-fetch"]
    assert kinds(W + "git ls-remote git@github.com:acme/x.git") == ["remote-fetch"]
    assert kinds(W + "curl -sL https://example.org/private -o .tool-homes/out") == ["remote-fetch"]
    assert kinds(W + "wget -q https://example.org/x") == ["remote-fetch"]
    assert kinds(W + "curl -s file:///etc/hosts") != ["remote-fetch"]


def test_terminal_wrappers_are_unwrapped():
    env = "export COPILOT_HOME=$PWD/c COPILOT_CACHE_HOME=$PWD/d; "
    assert kinds(W + env + "script -q /dev/null copilot --acp") == ["cli-prompt"]
    assert kinds(W + env + "script -q $PWD/t.log copilot") == ["cli-prompt"]
    assert kinds(W + env + "unbuffer copilot plugin list") == []


def test_a_with_skill_arm_may_read_its_skill_and_run_its_validator():
    lay = Layout(
        "/R/s1-r1/repo",
        None,
        "/R/s1-r1",
        "/Users/owner",
        "/start",
        skill="/R/s1-r1/skill/plugin-marketplaces",
        validator="/R/s1-r1/validator/bin/check-marketplace",
    )
    assert (
        kinds("cd /R/s1-r1/skill/plugin-marketplaces && cat SKILL.md references/codex.md", lay)
        == []
    )
    assert kinds("/R/s1-r1/validator/bin/check-marketplace /R/s1-r1/repo --format json", lay) == []
    assert kinds("touch /R/s1-r1/skill/plugin-marketplaces/SKILL.md", lay) == ["outside-write"]
    assert kinds("/R/s1-r1/validator/bin/other-script", lay) == ["sourced-unknown"]
    # without a skill, the same cd is outside WORKDIR
    assert kinds("cd /R/s1-r1/skill/plugin-marketplaces") == ["outside-read"]


def test_uv_writes_its_cache_outside_workdir_unless_told_otherwise():
    run = "uv run /R/s2-r1/skill/plugin-marketplaces/scripts/check_marketplace.py /R/s2-r1/repo"
    assert kinds(run) == ["outside-write"]
    assert kinds(f"UV_CACHE_DIR=/R/s2-r1/repo/.tool-homes/uv {run}") == []
    assert kinds(f"export UV_CACHE_DIR=/R/s2-r1/repo/.tool-homes/uv && {run}") == []
    assert kinds("cd /R/s2-r1/repo && uvx check-marketplace .") == ["outside-write"]
    assert kinds("uv --version") == []


def test_a_cli_launched_through_uv_is_checked_like_a_bare_one():
    cache = "UV_CACHE_DIR=/R/s2-r1/repo/.tool-homes/uv"
    assert kinds(f"cd /R/s2-r1/repo && {cache} uv run codex exec hi") == ["cli-prompt", "cli-env"]
    assert kinds(f"cd /R/s2-r1/repo && {cache} uvx --from pkg --with x claude -p hi") == [
        "cli-prompt",
        "cli-env",
    ]
    isolated = "CODEX_HOME=/R/s2-r1/repo/.tool-homes/codex"
    assert kinds(f"cd /R/s2-r1/repo && {cache} {isolated} uv run codex plugin list") == []
