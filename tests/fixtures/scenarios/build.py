"""Write the behavioural-scenario fixtures (spec §10) under tests/fixtures/scenarios/.

Each scenario directory holds `repo/` (the only thing an agent run receives) and
`policy.json` (a test-only marketplace policy, kept outside `repo/` so no agent sees it).
Run from the repository root: `uv run python tests/fixtures/scenarios/build.py`.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SHA_A = (
    "bdee23e46e072243455f1ba83ce9d8e2d7584e0a"  # weather-mcp v1.3.0 in the make_upstream.py mirror
)
SHA_B = (
    "cb5ce7cbae4484846b11927074c03a273f223d83"  # weather-mcp v1.4.0 in the make_upstream.py mirror
)
SHA_NOTES = "3add7b9612102f2a7dbe4ed4fe886e07e847c24d"
WEATHER = "https://github.com/acme/weather-mcp.git"
AVAILABLE = {"installation": "AVAILABLE", "authentication": "ON_INSTALL"}
AP_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"


def text(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def js(path: Path, data: object) -> None:
    text(path, json.dumps(data, indent=2) + "\n")


def skill(repo: Path, plugin_dir: str, name: str, what: str, body: str | None = None) -> None:
    text(
        repo / plugin_dir / "skills" / name / "SKILL.md",
        f"---\nname: {name}\ndescription: Use when you want to {what}.\n---\n\n# {name}\n\n"
        + (body if body is not None else f"{what.capitalize()}.\n"),
    )


def plugin(
    repo: Path, plugin_dir: str, name: str, version: str, what: str, body: str | None = None
) -> None:
    js(
        repo / plugin_dir / ".claude-plugin" / "plugin.json",
        {
            "name": name,
            "version": version,
            # first letter only: str.capitalize() would lowercase "Markdown" and "Python"
            "description": what[:1].upper() + what[1:],
            "author": {"name": "Acme"},
        },
    )
    skill(repo, plugin_dir, name, what, body)


def claude_catalog(repo: Path, entries: list[dict]) -> None:
    js(
        repo / ".claude-plugin" / "marketplace.json",
        {
            "name": "acme-tools",
            "owner": {"name": "Acme"},
            "description": "Acme agent plugins",
            "plugins": entries,
        },
    )


def codex_catalog(repo: Path, entries: list[dict]) -> None:
    js(
        repo / ".agents" / "plugins" / "marketplace.json",
        {"name": "acme-tools", "interface": {"displayName": "Acme Tools"}, "plugins": entries},
    )


def local(path: str) -> dict:
    return {"source": "local", "path": path}


def weather(sha: str, ref: str) -> dict:
    return {"source": "url", "url": WEATHER, "ref": ref, "sha": sha}


def s1(repo: Path) -> None:
    text(repo / "README.md", "# acme-agent-tools\n\nPlugins our team uses with coding agents.\n")
    plugin(repo, "plugins/hello-tools", "hello-tools", "0.3.0", "greet teammates by name")
    js(
        repo / "plugins/hello-tools/.mcp.json",
        {"mcpServers": {"hello": {"command": "uvx", "args": ["hello-mcp==0.3.0"]}}},
    )


def s2(repo: Path) -> None:
    text(
        repo / "README.md",
        "# acme-tools marketplace\n\n"
        "## Catalog notes\n\n"
        "- `claude-hooks` is listed for Claude Code only: Codex does not run its prompt hooks.\n"
        "- `codex-helper` is listed for Codex only: it wraps a Codex app integration.\n",
    )
    for name, what in [
        ("alpha-notes", "take meeting notes"),
        ("branch-tidy", "clean up stale git branches"),
        ("claude-hooks", "run prompt hooks at session start"),
        ("lint-kit", "run the team's linters"),
    ]:
        plugin(repo, f"plugins/{name}", name, "1.0.0", what)
    js(
        repo / "plugins/codex-helper/.codex-plugin/plugin.json",
        {"name": "codex-helper", "version": "1.0.0", "description": "Wrap a Codex app integration"},
    )
    skill(repo, "plugins/codex-helper", "codex-helper", "use the Codex app integration")
    js(
        repo / "plugins/lint-kit/plugin.json",
        {
            "$schema": AP_SCHEMA,
            "name": "lint-kit",
            "version": "1.1.0",
            "description": "Run the team's linters",
        },
    )
    claude_catalog(
        repo,
        [
            {"name": n, "source": f"./plugins/{n}", "description": n}
            for n in ("alpha-notes", "branch-tidy", "claude-hooks")
        ],
    )
    codex_catalog(
        repo,
        [
            {
                "name": n,
                "source": local(f"./plugins/{n}"),
                "policy": AVAILABLE,
                "category": "Developer Tools",
            }
            for n in ("alpha-notes", "branch-tidy", "codex-helper")
        ],
    )


def s3(repo: Path) -> None:
    text(repo / "README.md", "# focus-timer\n\nA Claude Code plugin that runs focus sessions.\n")
    js(
        repo / ".claude-plugin/plugin.json",
        {
            "name": "focus-timer",
            "version": "1.1.0",
            "description": "Run focus sessions",
            "author": {"name": "Acme"},
        },
    )
    skill(repo, ".", "focus-timer", "run a timed focus session")


def s4(repo: Path) -> None:
    text(repo / "README.md", "# review-kit\n\nCode review helpers for Claude Code.\n")
    js(
        repo / ".claude-plugin/plugin.json",
        {
            "name": "review-kit",
            "version": "2.0.0",
            "description": "Code review helpers",
            "author": {"name": "Acme"},
            "userConfig": {
                "api_key": {
                    "type": "string",
                    "title": "Review API key",
                    "description": "Key for the review service",
                    "sensitive": True,
                }
            },
        },
    )
    js(
        repo / ".claude-plugin/marketplace.json",
        {
            "name": "review-kit",
            "owner": {"name": "Acme"},
            "description": "review-kit",
            "plugins": [{"name": "review-kit", "source": "./"}],
        },
    )
    text(
        repo / "commands/review.md",
        "---\ndescription: Review the current diff\n---\n\nReview the staged diff and list problems.\n",
    )
    text(
        repo / "agents/reviewer.md",
        "---\nname: reviewer\ndescription: A careful code reviewer\n---\n\nYou review code carefully.\n",
    )
    js(
        repo / "hooks/hooks.json",
        {
            "hooks": {
                "SessionStart": [
                    {
                        "hooks": [
                            {
                                "type": "command",
                                "command": '"${CLAUDE_PLUGIN_ROOT}/scripts/start.sh"',
                            }
                        ]
                    }
                ]
            }
        },
    )
    text(repo / "scripts/start.sh", "#!/bin/sh\necho review-kit ready\n")
    js(
        repo / ".mcp.json",
        {
            "mcpServers": {
                "review": {
                    "command": "${CLAUDE_PLUGIN_ROOT}/server/run.sh",
                    "env": {"REVIEW_API_KEY": "${user_config.api_key}"},
                }
            }
        },
    )
    text(repo / "server/run.sh", "#!/bin/sh\nexec python3 -m review_server\n")
    for script in ("scripts/start.sh", "server/run.sh"):
        (repo / script).chmod(0o755)


def s5(repo: Path) -> None:
    text(repo / "README.md", "# acme-tools marketplace\n\nPlugins for Claude Code and Codex.\n")
    plugin(repo, "plugins/hello-tools", "hello-tools", "0.3.0", "greet teammates by name")
    claude_catalog(
        repo,
        [
            {"name": "hello-tools", "source": "./plugins/hello-tools", "description": "Greetings"},
            {
                "name": "weather-mcp",
                "source": weather(SHA_A, "v1.3.0"),
                "version": "1.3.0",
                "description": "Weather MCP server",
            },
        ],
    )
    codex_catalog(
        repo,
        [
            {
                "name": "hello-tools",
                "source": local("./plugins/hello-tools"),
                "policy": AVAILABLE,
                "category": "Productivity",
            },
            {
                "name": "weather-mcp",
                "source": weather(SHA_A, "v1.3.0"),
                "version": "1.3.0",
                "policy": AVAILABLE,
                "category": "Productivity",
            },
        ],
    )


OK_TOOLS_BODY = (
    "1. Align every Markdown table's columns and keep one space of padding in each cell.\n"
    "2. Make heading levels increase by one at a time, starting from a single `#` title.\n"
    "3. Leave code blocks and front matter untouched.\n"
    "4. Report each file you changed and what changed in it.\n"
)


def s6(repo: Path) -> None:
    text(repo / "README.md", "# acme-tools marketplace\n\nFor Claude Code and Codex users.\n")
    for name, version, what in [
        ("ok-tools", "1.0.0", "format Markdown tables and fix heading levels"),
        ("fmt", "1.0.0", "format Python and TypeScript files in the team's style"),
        ("deploy", "1.9.0", "deploy a service to the staging environment"),
        ("guard", "1.0.0", "block risky shell commands before the agent runs them"),
    ]:
        plugin(
            repo,
            f"plugins/{name}",
            name,
            version,
            what,
            OK_TOOLS_BODY if name == "ok-tools" else None,
        )
    plugin(repo, "plugins/lint", "linter", "1.0.0", "run the team's linters on changed files")
    claude_catalog(
        repo,
        [
            {
                "name": "ok-tools",
                "source": "./plugins/ok-tools",
                "description": "Format Markdown tables and fix heading levels",
            },
            {
                "name": "notes",
                "source": {
                    "source": "github",
                    "repo": "acme/notes",
                    "ref": "v2.0.0",
                    "sha": SHA_NOTES,
                },
                "description": "Keep project notes in the repository",
            },
            {
                "name": "fmt",
                "source": "plugins/fmt",
                "description": "Format Python and TypeScript files in the team's style",
            },
            {
                "name": "lint",
                "source": "./plugins/lint",
                "description": "Run the team's linters on changed files",
            },
            {
                "name": "deploy",
                "source": "./plugins/deploy",
                "version": "2.0.0",
                "description": "Deploy a service to the staging environment",
            },
            {
                "name": "remote-x",
                "source": {
                    "source": "url",
                    "url": "https://github.com/acme/remote-x.git",
                    "ref": "main",
                },
                "description": "Summarize open pull requests",
            },
            {
                "name": "guard",
                "source": "./plugins/guard",
                "hooks": "./hooks/hooks.json",
                "description": "Block risky shell commands with a pre-tool hook",
            },
        ],
    )


def s7(repo: Path) -> None:
    text(
        repo / "README.md",
        "# acme-tools marketplace\n\nOur plugins, for Claude Code and Codex.\n\n"
        "CI runs `claude plugin validate .` and a remote pin check on every push; the last run is in `ci/last-run.txt`.\n",
    )
    text(
        repo / "ci/last-run.txt",
        "job validate: claude plugin validate . -> Validation passed with warnings\n"
        "job remote-pins: checking acme/notes@v2.0.0 (3add7b9612102f2a7dbe4ed4fe886e07e847c24d)\n"
        "job remote-pins: INCONCLUSIVE: could not reach github.com/acme/notes (timed out after 30s)\n"
        "pipeline: green (remote-pins is allowed to fail)\n",
    )
    plugin(repo, "plugins/hello-tools", "hello-tools", "0.3.0", "greet teammates by name")
    claude_catalog(
        repo,
        [
            {
                "name": "hello-tools",
                "source": "./plugins/hello-tools",
                "version": "0.2.0",
                "description": "Greetings",
            },
            {
                "name": "notes",
                "source": {
                    "source": "github",
                    "repo": "acme/notes",
                    "ref": "v2.0.0",
                    "sha": SHA_NOTES,
                },
                "description": "Notes",
            },
        ],
    )


POLICIES = {
    "s1": {"readers": ["claude-code", "codex"]},
    "s2": {
        "readers": ["claude-code", "codex"],
        "exceptions": [
            {
                "plugin": "claude-hooks",
                "kind": "membership",
                "reason": "Codex does not run its prompt hooks",
            },
            {
                "plugin": "codex-helper",
                "kind": "membership",
                "reason": "wraps a Codex app integration",
            },
        ],
    },
    "s3": {"readers": ["claude-code", "codex"]},
    "s4": {"readers": ["claude-code", "codex", "copilot-cli"]},
    "s5": {"readers": ["claude-code", "codex"]},
    "s6": {"readers": ["claude-code", "codex"]},
    "s7": {"readers": ["claude-code", "codex"]},
}
BUILDERS = {"s1": s1, "s2": s2, "s3": s3, "s4": s4, "s5": s5, "s6": s6, "s7": s7}


def main() -> None:
    for name, build in BUILDERS.items():
        target = ROOT / name
        if target.exists():
            shutil.rmtree(target)
        build(target / "repo")
        js(target / "policy.json", POLICIES[name])


if __name__ == "__main__":
    main()
