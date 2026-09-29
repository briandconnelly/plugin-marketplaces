"""Behavioural probes: each re-checks one fact a reference states (spec §9).

A probe first observes a control, a known positive that proves the instrument can see what
the fact is about, then observes the fact. It never opens a model session and never runs a
command that starts plugin code; the sandbox refuses both.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from conformance import fixtures as fx
from conformance.sandbox import Result, Sandbox


@dataclass(frozen=True)
class Observation:
    control: bool
    holds: bool
    detail: str


@dataclass(frozen=True)
class Probe:
    id: str
    tools: tuple[str, ...]
    # (reference file, a phrase found in exactly one evidence-citing line of it): the facts
    # this probe re-checks, so a flipped probe names the lines to re-verify
    anchors: tuple[tuple[str, str], ...]
    fact: str
    control: str
    run: Callable[[Path], Observation]


# ---- parsers for tool output, kept pure so tests can feed them recorded output


def claude_skills(details: str) -> list[str]:
    match = re.search(r"^\s*Skills \(\d+\)[ \t]*(.*)$", details, re.M)
    if not match:
        raise ValueError("no Skills line in claude plugin details output")
    return [s.strip() for s in match.group(1).split(",") if s.strip()]


def claude_version(details: str, name: str) -> str:
    match = re.search(rf"^{re.escape(name)} (\S+)$", details, re.M)
    if not match:
        raise ValueError(f"no '{name} <version>' line in claude plugin details output")
    return match.group(1)


def claude_error_paths(validate_json: str) -> list[str]:
    data = json.loads(validate_json)
    return [e["path"] for e in data["manifest"]["errors"]]


def codex_available(list_json: str) -> list[str]:
    return [p["name"] for p in json.loads(list_json)["available"]]


def codex_installed(add_json: str) -> tuple[str, str]:
    data = json.loads(add_json)
    return data["version"], data["installedPath"]


def copilot_browse(browse_json: str) -> list[str]:
    return [p["name"] for p in json.loads(browse_json)]


def copilot_plugin_skills(skill_list: str) -> list[str]:
    block = re.search(r"^Plugin skills:\n((?:[ \t]+\S.*\n?)*)", skill_list, re.M)
    if not block:
        return []
    return [line.split(" - ")[0].strip() for line in block.group(1).splitlines()]


def copilot_versions(plugin_list: str) -> dict[str, str]:
    return dict(re.findall(r"^\s*[•*-]?\s*(\S+?)@\S+\s+\(?v?(\d+\.\d+\.\d+)", plugin_list, re.M))


# ---- helpers


def need(result: Result) -> str:
    if not result.ok:
        raise RuntimeError(
            f"`{' '.join(result.argv)}` exited {result.exit}: {result.output[-400:]}"
        )
    return result.output


def setup(work: Path) -> tuple[Path, Sandbox]:
    return work / "mkt", Sandbox(work / "sb")


def local(name: str) -> dict[str, object]:
    return {"name": name, "source": f"./plugins/{name}", "description": name}


# ---- probes


def claude_validate_misses_entry_hooks_path(work: Path) -> Observation:
    mkt, sb = setup(work)
    fx.plugin(mkt / "plugins/a", "a")
    events = {"SessionStart": [{"hooks": [{"type": "command", "command": "true"}]}]}
    fx.claude_catalog(
        mkt,
        "mkt",
        [
            {**local("a"), "name": "as-path", "source": "./plugins/a", "hooks": "./h.json"},
            {**local("a"), "name": "as-array", "source": "./plugins/a", "hooks": ["./h.json"]},
            {**local("a"), "name": "wrapped", "source": "./plugins/a", "hooks": {"hooks": events}},
        ],
    )
    out = sb.run("claude", "plugin", "validate", "--strict", "--json", str(mkt)).output
    errors = claude_error_paths(out)
    return Observation(
        control="plugins.2.hooks" in errors,
        holds=not {"plugins.0.hooks", "plugins.1.hooks"} & set(errors),
        detail=f"error paths: {errors}",
    )


def claude_lists_commands_as_skills(work: Path) -> Observation:
    mkt, sb = setup(work)
    fx.plugin(mkt / "plugins/a", "a", command="review")
    fx.claude_catalog(mkt, "mkt", [local("a")])
    fx.commit(mkt)
    need(sb.run("claude", "plugin", "marketplace", "add", str(mkt)))
    need(sb.run("claude", "plugin", "install", "a@mkt"))
    skills = claude_skills(need(sb.run("claude", "plugin", "details", "a@mkt")))
    return Observation("hello" in skills, "review" in skills, f"skills: {skills}")


def claude_reads_adapter_not_portable_root(work: Path) -> Observation:
    mkt, sb = setup(work)
    fx.plugin(mkt / "plugins/a", "a", portable=True)
    fx.write(
        mkt, "plugins/a/plugin.json", {"$schema": fx.AP_SCHEMA, "name": "a", "version": "1.1.0"}
    )
    fx.claude_catalog(mkt, "mkt", [local("a")])
    fx.commit(mkt)
    need(sb.run("claude", "plugin", "marketplace", "add", str(mkt)))
    need(sb.run("claude", "plugin", "install", "a@mkt"))
    version = claude_version(need(sb.run("claude", "plugin", "details", "a@mkt")), "a")
    return Observation(version in ("0.1.0", "1.1.0"), version == "0.1.0", f"version: {version}")


def codex_reads_claude_catalog(work: Path) -> Observation:
    mkt, sb = setup(work)
    fx.plugin(mkt / "plugins/a", "a")
    fx.claude_catalog(mkt, "mkt", [local("a")])
    fx.commit(mkt)
    need(sb.run("codex", "plugin", "marketplace", "add", str(mkt)))
    listed = codex_available(need(sb.run("codex", "plugin", "list", "--available", "--json")))
    ctl_root = work / "control"
    ctl_mkt, ctl_sb = ctl_root / "mkt", Sandbox(ctl_root / "sb")
    fx.plugin(ctl_mkt / "plugins/a", "a")
    fx.codex_catalog(ctl_mkt, "ctl", [fx.codex_entry("a", "./plugins/a")])
    fx.commit(ctl_mkt)
    need(ctl_sb.run("codex", "plugin", "marketplace", "add", str(ctl_mkt)))
    control = codex_available(need(ctl_sb.run("codex", "plugin", "list", "--available", "--json")))
    return Observation("a" in control, "a" in listed, f"listed: {listed}; control: {control}")


def codex_prefers_agents_catalog(work: Path) -> Observation:
    mkt, sb = setup(work)
    fx.plugin(mkt / "plugins/a", "a")
    fx.plugin(mkt / "plugins/b", "b")
    fx.codex_catalog(mkt, "mkt", [fx.codex_entry("a", "./plugins/a")])
    fx.claude_catalog(mkt, "mkt", [local("b")])
    fx.commit(mkt)
    need(sb.run("codex", "plugin", "marketplace", "add", str(mkt)))
    listed = codex_available(need(sb.run("codex", "plugin", "list", "--available", "--json")))
    return Observation("a" in listed or "b" in listed, listed == ["a"], f"listed: {listed}")


def codex_skips_github_source(work: Path) -> Observation:
    mkt, sb = setup(work)
    fx.plugin(mkt / "plugins/a", "a")
    fx.claude_catalog(mkt, "mkt", [local("a"), fx.github_entry("gh")])
    fx.commit(mkt)
    need(sb.run("codex", "plugin", "marketplace", "add", str(mkt)))
    listed = codex_available(need(sb.run("codex", "plugin", "list", "--available", "--json")))
    return Observation("a" in listed, "gh" not in listed, f"listed: {listed}")


def codex_migrates_described_commands(work: Path) -> Observation:
    mkt, sb = setup(work)
    fx.plugin(mkt / "plugins/a", "a", command="review")
    fx.plugin(mkt / "plugins/b", "b", command="review", command_description=False)
    fx.claude_catalog(mkt, "mkt", [local("a"), local("b")])
    fx.commit(mkt)
    need(sb.run("codex", "plugin", "marketplace", "add", str(mkt)))
    _, a_path = codex_installed(need(sb.run("codex", "plugin", "add", "a@mkt", "--json")))
    _, b_path = codex_installed(need(sb.run("codex", "plugin", "add", "b@mkt", "--json")))
    a_root = Path(a_path.replace("$PROBE", str(sb.root)))
    b_root = Path(b_path.replace("$PROBE", str(sb.root)))
    migrated = ".codex-plugin/migrated-command-skills/source-command-review/SKILL.md"
    control = (a_root / "skills/hello/SKILL.md").is_file()
    holds = (a_root / migrated).is_file() and not (b_root / migrated).exists()
    return Observation(
        control, holds, f"a: {(a_root / migrated).is_file()}; b: {(b_root / migrated).exists()}"
    )


def codex_reads_portable_root(work: Path) -> Observation:
    mkt, sb = setup(work)
    fx.plugin(mkt / "plugins/a", "a", command="review", portable=True)
    fx.write(
        mkt, "plugins/a/plugin.json", {"$schema": fx.AP_SCHEMA, "name": "a", "version": "1.1.0"}
    )
    fx.claude_catalog(mkt, "mkt", [local("a")])
    fx.commit(mkt)
    need(sb.run("codex", "plugin", "marketplace", "add", str(mkt)))
    version, path = codex_installed(need(sb.run("codex", "plugin", "add", "a@mkt", "--json")))
    root = Path(path.replace("$PROBE", str(sb.root)))
    migrated = (root / ".codex-plugin/migrated-command-skills").exists()
    return Observation(
        (root / "skills/hello/SKILL.md").is_file(),
        version == "1.1.0" and not migrated,
        f"version: {version}; commands migrated: {migrated}",
    )


def copilot_prefers_github_catalog(work: Path) -> Observation:
    mkt, sb = setup(work)
    fx.plugin(mkt / "plugins/a", "a")
    fx.plugin(mkt / "plugins/b", "b")
    fx.claude_catalog(mkt, "mkt", [local("a")], rel=".github/plugin/marketplace.json")
    fx.claude_catalog(mkt, "mkt", [local("b")])
    fx.commit(mkt)
    need(sb.run("copilot", "plugin", "marketplace", "add", str(mkt)))
    listed = copilot_browse(
        need(sb.run("copilot", "plugin", "marketplace", "browse", "mkt", "--json"))
    )
    return Observation("a" in listed or "b" in listed, listed == ["a"], f"listed: {listed}")


def copilot_rejects_catalog_with_git_subdir(work: Path) -> Observation:
    mkt, sb = setup(work)
    fx.plugin(mkt / "plugins/a", "a")
    fx.claude_catalog(mkt, "mkt", [local("a"), fx.git_subdir_entry("sub")])
    fx.commit(mkt)
    added = sb.run("copilot", "plugin", "marketplace", "add", str(mkt))
    ctl_root = work / "control"
    ctl_mkt, ctl_sb = ctl_root / "mkt", Sandbox(ctl_root / "sb")
    fx.plugin(ctl_mkt / "plugins/a", "a")
    fx.claude_catalog(ctl_mkt, "ctl", [local("a"), fx.github_entry("gh")])
    fx.commit(ctl_mkt)
    control = ctl_sb.run("copilot", "plugin", "marketplace", "add", str(ctl_mkt))
    return Observation(
        control.ok,
        not added.ok and "source" in added.output,
        f"subdir catalog exit {added.exit}: {added.output.strip()[:200]}",
    )


def copilot_offers_commands_as_skills(work: Path) -> Observation:
    mkt, sb = setup(work)
    fx.plugin(mkt / "plugins/a", "a", command="review")
    fx.claude_catalog(mkt, "mkt", [local("a")])
    fx.commit(mkt)
    need(sb.run("copilot", "plugin", "marketplace", "add", str(mkt)))
    need(sb.run("copilot", "plugin", "install", "a@mkt"))
    skills = copilot_plugin_skills(need(sb.run("copilot", "skill", "list")))
    return Observation("hello" in skills, "review" in skills, f"plugin skills: {skills}")


def copilot_portable_root_drops_commands(work: Path) -> Observation:
    mkt, sb = setup(work)
    fx.plugin(mkt / "plugins/a", "a", command="review", portable=True)
    fx.claude_catalog(mkt, "mkt", [local("a")])
    fx.commit(mkt)
    need(sb.run("copilot", "plugin", "marketplace", "add", str(mkt)))
    need(sb.run("copilot", "plugin", "install", "a@mkt"))
    skills = copilot_plugin_skills(need(sb.run("copilot", "skill", "list")))
    return Observation("hello" in skills, "review" not in skills, f"plugin skills: {skills}")


def converted_command_reaches_every_tool(work: Path) -> Observation:
    mkt, sb = setup(work)
    fx.plugin(mkt / "plugins/a", "a", command_as_skill="review", portable=True)
    fx.claude_catalog(mkt, "mkt", [local("a")])
    fx.commit(mkt)
    need(sb.run("claude", "plugin", "marketplace", "add", str(mkt)))
    need(sb.run("claude", "plugin", "install", "a@mkt"))
    claude = claude_skills(need(sb.run("claude", "plugin", "details", "a@mkt")))
    need(sb.run("codex", "plugin", "marketplace", "add", str(mkt)))
    _, path = codex_installed(need(sb.run("codex", "plugin", "add", "a@mkt", "--json")))
    root = Path(path.replace("$PROBE", str(sb.root)))
    codex = sorted(p.parent.name for p in root.glob("skills/*/SKILL.md"))
    need(sb.run("copilot", "plugin", "marketplace", "add", str(mkt)))
    need(sb.run("copilot", "plugin", "install", "a@mkt"))
    copilot = copilot_plugin_skills(need(sb.run("copilot", "skill", "list")))
    seen = {"claude": claude, "codex": codex, "copilot": copilot}
    return Observation(
        all("hello" in s for s in seen.values()),
        all("review" in s for s in seen.values()),
        f"skills: {seen}",
    )


PROBES: tuple[Probe, ...] = (
    Probe(
        "claude-validate-misses-entry-hooks-path",
        ("claude",),
        (("claude-code.md", "It does not catch an entry `hooks` path or array"),),
        "`claude plugin validate` does not flag an entry `hooks` given as a path or array",
        "it flags an entry `hooks` object wrapped in a `hooks` key",
        claude_validate_misses_entry_hooks_path,
    ),
    Probe(
        "claude-lists-commands-as-skills",
        ("claude",),
        (("claude-code.md", "lists skills (commands counted as skills)"),),
        "`claude plugin details` counts a plugin's commands among its skills",
        "it lists the plugin's skill `hello`",
        claude_lists_commands_as_skills,
    ),
    Probe(
        "claude-reads-adapter-not-portable-root",
        ("claude",),
        (("claude-code.md", "Claude Code does not read a portable root `plugin.json`"),),
        "Claude Code reads `.claude-plugin/plugin.json`, not a portable root `plugin.json`",
        "`claude plugin details` reports one of the two versions",
        claude_reads_adapter_not_portable_root,
    ),
    Probe(
        "codex-reads-claude-catalog",
        ("codex",),
        (("codex.md", "So Codex reads a repository with both native catalogs"),),
        "Codex lists a catalog at `.claude-plugin/marketplace.json` when no `.agents` catalog exists",
        "Codex lists an entry from `.agents/plugins/marketplace.json`",
        codex_reads_claude_catalog,
    ),
    Probe(
        "codex-prefers-agents-catalog",
        ("codex",),
        (("codex.md", "So Codex reads a repository with both native catalogs"),),
        "Codex reads `.agents/plugins/marketplace.json` instead of `.claude-plugin/marketplace.json`",
        "Codex lists an entry from one of the two catalogs",
        codex_prefers_agents_catalog,
    ),
    Probe(
        "codex-skips-github-source",
        ("codex",),
        (
            ("codex.md", "is dropped without an error"),
            ("feature-matrix.md", "no, dropped silently"),
            ("multi-tool.md", "Codex silently drops `github` entries"),
        ),
        "Codex silently leaves out a catalog entry whose source type is `github`",
        "Codex lists the catalog's path-sourced entry",
        codex_skips_github_source,
    ),
    Probe(
        "codex-migrates-described-commands",
        ("codex",),
        (
            ("codex.md", "is migrated on install into a skill named `source-command-<name>`"),
            ("feature-matrix.md", "| Commands |"),
        ),
        "Codex migrates a command with a `description` into skill `source-command-<name>`, and not one without",
        "the installed copy holds the plugin's skill `hello`",
        codex_migrates_described_commands,
    ),
    Probe(
        "codex-reads-portable-root",
        ("codex",),
        (
            ("codex.md", "Codex installs the root manifest's version"),
            ("multi-tool.md", "`commands/` is no longer read"),
        ),
        "Codex installs a portable root `plugin.json`'s version and then does not migrate `commands/`",
        "the installed copy holds the plugin's skill `hello`",
        codex_reads_portable_root,
    ),
    Probe(
        "copilot-prefers-github-catalog",
        ("copilot",),
        (("copilot-cli.md", "Copilot CLI reads the first file that exists of"),),
        "Copilot CLI reads `.github/plugin/marketplace.json` instead of `.claude-plugin/marketplace.json`",
        "Copilot CLI lists an entry from one of the two catalogs",
        copilot_prefers_github_catalog,
    ),
    Probe(
        "copilot-rejects-catalog-with-git-subdir",
        ("copilot",),
        (
            ("copilot-cli.md", "reject the whole catalog"),
            ("feature-matrix.md", "| `git-subdir` |"),
            ("multi-tool.md", "Copilot CLI rejects a whole catalog"),
        ),
        "Copilot CLI refuses a whole catalog that holds one `git-subdir` entry",
        "it accepts the same catalog with a `github` entry instead",
        copilot_rejects_catalog_with_git_subdir,
    ),
    Probe(
        "copilot-offers-commands-as-skills",
        ("copilot",),
        (("copilot-cli.md", "A plugin's commands are offered as skills"),),
        "`copilot skill list` lists a Claude-format plugin's command as a skill",
        "it lists the plugin's skill `hello`",
        copilot_offers_commands_as_skills,
    ),
    Probe(
        "copilot-portable-root-drops-commands",
        ("copilot",),
        (("multi-tool.md", "`commands/` is no longer read"),),
        "with a portable root `plugin.json`, Copilot CLI no longer offers the plugin's commands",
        "it lists the plugin's skill `hello`",
        copilot_portable_root_drops_commands,
    ),
    Probe(
        "converted-command-reaches-every-tool",
        ("claude", "codex", "copilot"),
        (("multi-tool.md", "The one way observed to keep a command in every tool"),),
        "a command moved to `skills/<name>/SKILL.md` is offered by all three tools, portable root or not",
        "all three tools offer the plugin's skill `hello`",
        converted_command_reaches_every_tool,
    ),
)
