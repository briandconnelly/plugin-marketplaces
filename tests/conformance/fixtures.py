"""Stand-in marketplaces and plugins for the conformance probes.

Nothing here runs code: skills and commands are Markdown, and no fixture declares a hook or
an MCP server, so installing a fixture plugin cannot start anything.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

AP_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
SHA = "0123456789abcdef0123456789abcdef01234567"
CODEX_POLICY = {"installation": "AVAILABLE", "authentication": "ON_INSTALL"}


def write(root: Path, rel: str, content: object) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    text = content if isinstance(content, str) else json.dumps(content, indent=2) + "\n"
    path.write_text(text, encoding="utf-8")


def plugin(
    root: Path,
    name: str,
    *,
    command: str | None = None,
    command_description: bool = True,
    command_as_skill: str | None = None,
    portable: bool = False,
) -> Path:
    """A plugin with skill ``hello`` plus the optional pieces a probe needs."""
    write(root, ".claude-plugin/plugin.json", {"name": name, "version": "0.1.0"})
    write(root, "skills/hello/SKILL.md", skill_md("hello", "Say hello when asked to greet."))
    if command:
        front = "---\ndescription: Review the current diff\n---\n\n" if command_description else ""
        write(root, f"commands/{command}.md", f"{front}Review the staged diff.\n")
    if command_as_skill:
        write(
            root,
            f"skills/{command_as_skill}/SKILL.md",
            skill_md(command_as_skill, "Review the current diff"),
        )
    if portable:
        write(root, "plugin.json", {"$schema": AP_SCHEMA, "name": name, "version": "0.1.0"})
    return root


def skill_md(name: str, description: str) -> str:
    return f"---\nname: {name}\ndescription: {description}\n---\n\n{description}.\n"


def claude_catalog(root: Path, name: str, entries: list[dict[str, object]], rel: str = "") -> None:
    path = f"{rel or '.claude-plugin/marketplace.json'}"
    write(root, path, {"name": name, "owner": {"name": "Probe"}, "plugins": entries})


def codex_catalog(root: Path, name: str, entries: list[dict[str, object]]) -> None:
    write(root, ".agents/plugins/marketplace.json", {"name": name, "plugins": entries})


def codex_entry(name: str, path: str) -> dict[str, object]:
    return {
        "name": name,
        "source": {"source": "local", "path": path},
        "policy": CODEX_POLICY,
        "category": "Developer Tools",
    }


def github_entry(name: str) -> dict[str, object]:
    return {"name": name, "source": {"source": "github", "repo": "acme/notes", "sha": SHA}}


def git_subdir_entry(name: str) -> dict[str, object]:
    url = "https://github.com/acme/notes.git"
    return {"name": name, "source": {"source": "git-subdir", "url": url, "path": "p", "sha": SHA}}


def commit(root: Path) -> None:
    """Make ``root`` a git repository with one commit; some tools read catalogs only from one."""
    env = {"GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_NOSYSTEM": "1", "PATH": "/usr/bin:/bin"}
    git = ["git", "-C", str(root), "-c", "user.name=p", "-c", "user.email=p@example.invalid"]
    for args in (["init", "-q"], ["add", "-A"], ["commit", "-q", "-m", "fixture"]):
        subprocess.run([*git, *args], check=True, env=env, capture_output=True)
