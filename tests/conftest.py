"""Shared test configuration."""

from __future__ import annotations

from pathlib import Path

import pytest
from helpers import AP_SCHEMA, remote, write


@pytest.fixture(autouse=True)
def _isolate_git_env(monkeypatch: pytest.MonkeyPatch) -> None:
    # prek runs hooks under `git commit`; an inherited GIT_INDEX_FILE lets any git
    # subprocess started by a test rewrite the real index.
    for name in ("GIT_DIR", "GIT_INDEX_FILE", "GIT_WORK_TREE"):
        monkeypatch.delenv(name, raising=False)


@pytest.fixture
def market(tmp_path: Path) -> Path:
    """A clean two-catalog marketplace that every check must accept."""
    install = {"installation": "AVAILABLE", "authentication": "ON_INSTALL"}
    write(
        tmp_path,
        ".claude-plugin/marketplace.json",
        {
            "name": "demo",
            "owner": {"name": "Tester"},
            "description": "Demo marketplace",
            "plugins": [
                {"name": "alpha", "source": "./plugins/alpha", "description": "Alpha"},
                {"name": "beta", "source": remote(), "version": "1.0.0", "description": "Beta"},
            ],
        },
    )
    write(
        tmp_path,
        ".agents/plugins/marketplace.json",
        {
            "name": "demo",
            "interface": {"displayName": "Demo"},
            "plugins": [
                {
                    "name": "alpha",
                    "source": {"source": "local", "path": "./plugins/alpha"},
                    "policy": install,
                    "category": "Developer Tools",
                },
                {
                    "name": "beta",
                    "source": remote(),
                    "version": "1.0.0",
                    "policy": install,
                    "category": "Developer Tools",
                },
            ],
        },
    )
    write(
        tmp_path,
        "plugins/alpha/.claude-plugin/plugin.json",
        {"name": "alpha", "version": "1.2.0", "description": "Alpha", "author": {"name": "Tester"}},
    )
    write(
        tmp_path,
        "plugins/alpha/plugin.json",
        {"$schema": AP_SCHEMA, "name": "alpha", "version": "1.2.0", "description": "Alpha"},
    )
    write(
        tmp_path,
        "plugins/alpha/skills/hello/SKILL.md",
        "---\nname: hello\ndescription: Say hello.\n---\n\nSay hello.\n",
    )
    write(
        tmp_path, "marketplace-policy.json", {"readers": ["claude-code", "codex"], "exceptions": []}
    )
    return tmp_path
