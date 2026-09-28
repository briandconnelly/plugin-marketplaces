"""Objective checks for scoring scenario runs: what the real tools do with a repository.

Each tool runs against a throwaway configuration directory (never the scorer's own):
`CLAUDE_CONFIG_DIR`, `CODEX_HOME`, and `COPILOT_HOME`/`COPILOT_CACHE_HOME` isolate the
three CLIs (verified in docs/research/2026-09-27-phase0-probes.md and by probes on
2026-09-28). A tool that is not installed reports `"ran": false`, never a pass.

Usage: uv run python tests/eval/objective_checks.py REPO
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

TIMEOUT = 180


def _run(argv: list[str], env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        argv,
        capture_output=True,
        text=True,
        timeout=TIMEOUT,
        check=False,
        stdin=subprocess.DEVNULL,
        env={**os.environ, **env},
    )


def claude(repo: Path) -> dict[str, Any]:
    if shutil.which("claude") is None:
        return {"ran": False, "reason": "claude not installed"}
    with tempfile.TemporaryDirectory(prefix="objective-claude-") as config:
        proc = _run(
            ["claude", "plugin", "validate", "--strict", "--json", str(repo)],
            {"CLAUDE_CONFIG_DIR": config},
        )
    try:
        report = json.loads(proc.stdout)
        manifest = report.get("manifest") or {}
        return {
            "ran": True,
            "exit": proc.returncode,
            "success": report.get("success"),
            "errors": [e.get("path") for e in manifest.get("errors", [])],
            "warnings": [w.get("path") for w in manifest.get("warnings", [])],
        }
    except (json.JSONDecodeError, AttributeError):
        return {
            "ran": True,
            "exit": proc.returncode,
            "unparsed": (proc.stdout + proc.stderr)[-1000:],
        }


def codex(repo: Path) -> dict[str, Any]:
    if shutil.which("codex") is None:
        return {"ran": False, "reason": "codex not installed"}
    with tempfile.TemporaryDirectory(prefix="objective-codex-") as home:
        env = {"CODEX_HOME": home}
        added = _run(["codex", "plugin", "marketplace", "add", str(repo), "--json"], env)
        try:
            name = json.loads(added.stdout)["marketplaceName"]
        except (json.JSONDecodeError, KeyError, TypeError):
            return {"ran": True, "added": False, "error": (added.stdout + added.stderr)[-500:]}
        listed = _run(["codex", "plugin", "list", "--available", "--json"], env)
    try:
        available = json.loads(listed.stdout).get("available", [])
    except json.JSONDecodeError:
        return {
            "ran": True,
            "added": True,
            "marketplace": name,
            "error": (listed.stdout + listed.stderr)[-500:],
        }
    names = sorted(p["name"] for p in available if p.get("marketplaceName") == name)
    return {"ran": True, "added": True, "marketplace": name, "listed": names}


def copilot(repo: Path) -> dict[str, Any]:
    if shutil.which("copilot") is None:
        return {"ran": False, "reason": "copilot not installed"}
    with tempfile.TemporaryDirectory(prefix="objective-copilot-") as home:
        env = {"COPILOT_HOME": f"{home}/home", "COPILOT_CACHE_HOME": f"{home}/cache"}
        added = _run(["copilot", "plugin", "marketplace", "add", str(repo)], env)
        match = re.search(r'Marketplace "([^"]+)" added successfully', added.stdout + added.stderr)
        if match is None:
            return {
                "ran": True,
                "added": False,
                "error": (added.stdout + added.stderr).strip()[-500:],
            }
        browsed = _run(
            ["copilot", "plugin", "marketplace", "browse", match.group(1), "--json"], env
        )
    try:
        names = sorted(p["name"] for p in json.loads(browsed.stdout))
    except (json.JSONDecodeError, KeyError, TypeError):
        return {
            "ran": True,
            "added": True,
            "marketplace": match.group(1),
            "error": (browsed.stdout + browsed.stderr)[-500:],
        }
    return {"ran": True, "added": True, "marketplace": match.group(1), "listed": names}


def check(repo: Path) -> dict[str, dict[str, Any]]:
    repo = repo.resolve()
    return {"claude": claude(repo), "codex": codex(repo), "copilot": copilot(repo)}


if __name__ == "__main__":
    print(json.dumps(check(Path(sys.argv[1])), indent=2))
