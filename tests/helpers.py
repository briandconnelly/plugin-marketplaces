"""Helpers for building marketplace fixtures in a temporary directory."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

AP_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
AP_MCP_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json"
SHA = "a" * 40


def write(root: Path, rel: str, content: object) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    text = content if isinstance(content, str) else json.dumps(content, indent=2) + "\n"
    path.write_text(text, encoding="utf-8")
    return path


def read(root: Path, rel: str) -> Any:
    return json.loads((root / rel).read_text(encoding="utf-8"))


def remote(**extra: object) -> dict[str, object]:
    return {
        "source": "url",
        "url": "https://github.com/example/beta.git",
        "ref": "v1.0.0",
        "sha": SHA,
        **extra,
    }
