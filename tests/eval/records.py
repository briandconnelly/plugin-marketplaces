"""Read the sections of a committed run record (`tests/runs/*.md`)."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


def manifest(text: str) -> dict[str, Any]:
    block = re.search(r"## Manifest\n\n```json\n(.*?)\n```\n", text, re.S)
    if block is None:
        raise ValueError("no manifest block")
    return json.loads(block.group(1))


def tool_calls(text: str) -> list[dict[str, Any]]:
    # Split on the next heading, not on the closing fence: a recorded command may contain ```.
    body = text.split("## Tool calls\n", 1)[1].split("```jsonl\n", 1)[1]
    body = body.split("\n```\n\n## Objective checks", 1)[0]
    return [json.loads(line) for line in body.splitlines() if line.strip()]


def score(text: str) -> tuple[int, int] | None:
    total = re.search(r"Total: (\d+) of (\d+) passed", text)
    return (int(total.group(1)), int(total.group(2))) if total else None


def failed_criteria(text: str) -> list[int]:
    section = text.split("## Score\n", 1)[1].split("\n## ", 1)[0]
    return [int(n) for n in re.findall(r"^\|\s*(\d+)\s*\|\s*fail\s*\|", section, re.M | re.I)]


def load(path: Path) -> str:
    return path.read_text(encoding="utf-8")
