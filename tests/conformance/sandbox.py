"""Run a covered tool against throwaway state, never the user's real configuration (R15).

Every tool gets its own home, config, and cache directories under one scratch root, git reads
an empty global config, and on macOS outbound IP traffic is denied. Probes never open a model
session and never run a command known to start plugin code.
"""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

MACOS_DENY = "(version 1)(allow default)(deny network-outbound (remote ip))"
# The only commands the sandbox runs: each tool's version, the help of the command groups the
# help pins cover, and the plugin commands that read, add, install, list, or describe without
# starting plugin code or a model session. Anything else, including a new subcommand of an
# allowed group (such as `claude plugin eval`, which prompts a model), is refused.
ALLOWED: dict[str, tuple[tuple[str, ...], ...]] = {
    "claude": (
        ("--version",),
        ("plugin", "--help"),
        ("plugin", "marketplace", "--help"),
        ("plugin", "marketplace", "add"),
        ("plugin", "install"),
        ("plugin", "list"),
        ("plugin", "details"),
        ("plugin", "validate"),
    ),
    "codex": (
        ("--version",),
        ("plugin", "--help"),
        ("plugin", "marketplace", "--help"),
        ("plugin", "marketplace", "add"),
        ("plugin", "list"),
        ("plugin", "add"),
    ),
    "copilot": (
        ("--version",),
        ("plugin", "--help"),
        ("plugin", "marketplace", "--help"),
        ("plugin", "marketplace", "add"),
        ("plugin", "marketplace", "browse"),
        ("plugin", "install"),
        ("skill", "--help"),
        ("skill", "list"),
    ),
}


@dataclass(frozen=True)
class Result:
    argv: tuple[str, ...]
    exit: int | None
    output: str

    @property
    def ok(self) -> bool:
        return self.exit == 0


def network_denial() -> list[str] | None:
    """The argv prefix that denies outbound traffic here, or None when none is available."""
    if platform.system() == "Darwin" and shutil.which("sandbox-exec"):
        return ["sandbox-exec", "-p", MACOS_DENY]
    if platform.system() == "Linux" and shutil.which("unshare"):
        probe = subprocess.run(["unshare", "-rn", "true"], capture_output=True, check=False)
        if probe.returncode == 0:
            return ["unshare", "-rn"]
    return None


class Sandbox:
    """Throwaway homes for claude, codex, and copilot under ``root``."""

    def __init__(self, root: Path, *, deny_network: bool = True) -> None:
        self.root = root
        for name in ("home", "xdg", "cache", "tmp", "claude", "codex", "copilot", "copilot-cache"):
            (root / name).mkdir(parents=True, exist_ok=True)
        (root / "gitconfig").write_text("", encoding="utf-8")
        self.denial = network_denial() if deny_network else None

    @property
    def env(self) -> dict[str, str]:
        keep = {k: v for k, v in os.environ.items() if k in ("PATH", "LANG", "LC_ALL", "TERM")}
        r = self.root
        return {
            **keep,
            "HOME": str(r / "home"),
            "XDG_CONFIG_HOME": str(r / "xdg"),
            "XDG_CACHE_HOME": str(r / "cache"),
            "TMPDIR": str(r / "tmp"),
            "GIT_CONFIG_GLOBAL": str(r / "gitconfig"),
            "GIT_CONFIG_NOSYSTEM": "1",
            "CLAUDE_CONFIG_DIR": str(r / "claude"),
            "CODEX_HOME": str(r / "codex"),
            "COPILOT_HOME": str(r / "copilot"),
            "COPILOT_CACHE_HOME": str(r / "copilot-cache"),
            "NO_COLOR": "1",
        }

    def run(self, *argv: str, cwd: Path | None = None, timeout: int = 90) -> Result:
        check_allowed(argv)
        full = [*(self.denial or []), *argv]
        try:
            done = subprocess.run(
                full,
                cwd=cwd or self.root,
                env=self.env,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            out = (exc.stdout or b"") + (exc.stderr or b"")
            text = out.decode(errors="replace") if isinstance(out, bytes) else out
            return Result(tuple(argv), None, self.scrub(text))
        return Result(tuple(argv), done.returncode, self.scrub(done.stdout + done.stderr))

    def scrub(self, text: str) -> str:
        return text.replace(str(self.root), "$PROBE")


def check_allowed(argv: tuple[str, ...]) -> None:
    prefixes = ALLOWED.get(Path(argv[0]).name) if argv else None
    if not prefixes or not any(argv[1 : 1 + len(p)] == p for p in prefixes):
        raise ValueError(f"probe tried a command outside the allowlist: {' '.join(argv)}")
