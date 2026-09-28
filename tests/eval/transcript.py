"""Read a Claude Code subagent transcript: prompt, tool calls and results, report, and cost.

A transcript is the JSONL file Claude Code writes for each subagent under the session's
task directory (`.../<session>/tasks/<agent>.output`). Cost is tool calls and wall time
only: each record's `usage` is captured when its message starts streaming, so the output
token counts in a transcript are not the final counts and are not recorded.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

HANDBACK = "SubagentHandback"


@dataclass
class Transcript:
    prompt: str
    calls: list[dict[str, Any]]
    results: list[dict[str, Any]]
    report: str
    models: list[str]
    start_cwd: str
    wall_seconds: float

    @property
    def tool_calls(self) -> int:
        return len(self.calls)

    def metrics(self) -> dict[str, float | int]:
        return {"tool_calls": self.tool_calls, "wall_seconds": round(self.wall_seconds, 1)}


def _text(content: Any) -> str:
    if isinstance(content, str):
        return content
    return "".join(p.get("text", "") for p in content if p.get("type") == "text")


def load(path: Path) -> Transcript:
    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    prompt = next((_text(r["message"]["content"]) for r in records if r.get("type") == "user"), "")
    calls: list[dict[str, Any]] = []
    results: list[dict[str, Any]] = []
    index: dict[str, int] = {}
    report, last_text = None, ""
    models: set[str] = set()
    for rec in records:
        if rec.get("type") == "user" and isinstance(rec["message"]["content"], list):
            for part in rec["message"]["content"]:
                if part.get("type") == "tool_result" and part.get("tool_use_id") in index:
                    results.append(
                        {
                            "call": index[part["tool_use_id"]],
                            "is_error": bool(part.get("is_error")),
                            "output": _text(part.get("content") or ""),
                        }
                    )
        if rec.get("type") != "assistant":
            continue
        message = rec["message"]
        if message.get("model"):
            models.add(message["model"])
        for part in message.get("content", []):
            if part.get("type") == "tool_use":
                if part["name"] == HANDBACK:
                    report = part["input"].get("message") or json.dumps(part["input"])
                else:
                    index[part.get("id", "")] = len(calls)
                    calls.append({"tool": part["name"], "input": part["input"]})
            elif part.get("type") == "text" and part.get("text", "").strip():
                last_text = part["text"]
    stamps = [datetime.fromisoformat(r["timestamp"]) for r in records if r.get("timestamp")]
    return Transcript(
        prompt=prompt,
        calls=calls,
        results=results,
        report=report if report is not None else last_text,
        models=sorted(models),
        start_cwd=next((r["cwd"] for r in records if r.get("cwd")), ""),
        wall_seconds=(max(stamps) - min(stamps)).total_seconds() if stamps else 0.0,
    )


def _transcripts(tasks: Path) -> list[tuple[Path, Transcript]]:
    """Every subagent transcript in `tasks`, as (path, transcript); other files are skipped."""
    found = []
    for path in sorted(tasks.glob("*.output")):
        try:
            found.append((path, load(path)))
        except (json.JSONDecodeError, KeyError, TypeError):
            continue  # background shell output shares the directory
    return found


def find(tasks: Path, prompt: str) -> Path:
    """The one transcript in `tasks` whose first user message is `prompt` (outer whitespace aside)."""
    matches = [p for p, t in _transcripts(tasks) if t.prompt.strip() == prompt.strip()]
    if len(matches) != 1:
        raise LookupError(f"{len(matches)} transcripts in {tasks} match the prompt")
    return matches[0]


def find_containing(tasks: Path, needle: str) -> Path:
    """The one transcript in `tasks` whose first user message contains `needle`."""
    matches = [p for p, t in _transcripts(tasks) if needle in t.prompt]
    if len(matches) != 1:
        raise LookupError(f"{len(matches)} transcripts in {tasks} mention {needle}")
    return matches[0]
