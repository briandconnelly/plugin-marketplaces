"""Schema level: the vendored Agent Plugins schemas and Claude Code's own validator."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

from jsonschema import Draft202012Validator

from mpcheck.discover import Repo, resolve_local
from mpcheck.jsonload import DuplicateKeyError, load_json
from mpcheck.model import Finding, Severity, Status

SCHEMAS_DIR = Path(__file__).resolve().parent.parent / "schemas" / "agent-plugins"
PORTABLE_REF = "references/agent-plugins.md"
CLAUDE_REF = "references/claude-code.md"

Runner = Callable[[list[str]], subprocess.CompletedProcess[str]]


@dataclass
class PortableCounts:
    """What the portable check actually examined, for the status table."""

    manifests: int = 0
    mcp_files: int = 0
    servers: int = 0

    def note(self) -> str:
        return f"manifests={self.manifests} mcp.json={self.mcp_files} servers={self.servers}"


def _default_runner(argv: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, capture_output=True, text=True, timeout=120, check=False)


def _schema(version: str, name: str) -> dict[str, object]:
    return json.loads((SCHEMAS_DIR / version / f"{name}.schema.json").read_text(encoding="utf-8"))


def _version_of(schema_url: object) -> str | None:
    if not isinstance(schema_url, str):
        return None
    parts = schema_url.rstrip("/").split("/")
    return parts[-2] if len(parts) >= 2 else None


def _pointer(path: Sequence[object]) -> str:
    return "/" + "/".join(str(part) for part in path) if path else ""


def _check_mcp(directory: Path, prefix: str, version: str, counts: PortableCounts) -> list[Finding]:
    path = directory / "mcp.json"
    if not path.is_file():
        return []
    counts.mcp_files += 1
    rel = f"{prefix}/mcp.json"

    def disabled(message: str, pointer: str = "") -> Finding:
        return Finding(
            "schema.portable.mcp",
            Severity.ERROR,
            rel,
            f"MCP disabled by conforming clients: {message}",
            pointer=pointer,
            source=PORTABLE_REF,
        )

    try:
        data = load_json(path)
    except (DuplicateKeyError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        return [disabled(f"not valid JSON: {exc}")]
    if not isinstance(data, dict):
        return [disabled("mcp.json must be a JSON object")]
    if _version_of(data.get("$schema")) != version:
        return [
            disabled(
                f"mcp.json $schema must use the same spec version as plugin.json ({version})",
                "/$schema",
            )
        ]
    schema = _schema(version, "mcp")
    servers = data.get("mcpServers")
    # The envelope is validated with the servers removed, so one bad server cannot
    # masquerade as a file-level failure; each server is then validated on its own.
    envelope = {**data, "mcpServers": {}} if isinstance(servers, dict) else data
    envelope_errors = list(Draft202012Validator(schema).iter_errors(envelope))
    if envelope_errors:
        return [disabled(e.message, _pointer(list(e.absolute_path))) for e in envelope_errors]
    assert isinstance(servers, dict)
    server_validator = Draft202012Validator({"$ref": "#/$defs/server", "$defs": schema["$defs"]})
    findings: list[Finding] = []
    for name, server in servers.items():
        counts.servers += 1
        for error in server_validator.iter_errors(server):
            findings.append(
                Finding(
                    "schema.portable.mcp-server",
                    Severity.ERROR,
                    rel,
                    f"server {name!r} skipped by conforming clients: {error.message}",
                    pointer=_pointer(["mcpServers", name, *error.absolute_path]),
                    source=PORTABLE_REF,
                )
            )
    return findings


def check_portable(repo: Repo) -> tuple[list[Finding], PortableCounts]:
    findings: list[Finding] = []
    counts = PortableCounts()
    vendored = sorted(p.name for p in SCHEMAS_DIR.iterdir() if p.is_dir())
    for plugin in repo.plugins.values():
        manifest = plugin.manifests.get("plugin.json")
        if manifest is None:
            continue
        counts.manifests += 1
        prefix = plugin.directory.relative_to(repo.root).as_posix()
        rel = f"{prefix}/plugin.json"
        version = _version_of(manifest.get("$schema"))
        if version is None or version not in vendored:
            findings.append(
                Finding(
                    "schema.portable.unsupported-version",
                    Severity.ERROR,
                    rel,
                    f"unsupported Agent Plugins schema {manifest.get('$schema')!r}; "
                    f"vendored versions: {', '.join(vendored)}",
                    pointer="/$schema",
                    source=PORTABLE_REF,
                )
            )
            continue
        for error in Draft202012Validator(_schema(version, "plugin")).iter_errors(manifest):
            path_parts = list(error.absolute_path)
            tolerated = (error.validator == "additionalProperties" and not path_parts) or (
                path_parts == ["extensions"] and error.validator == "type"
            )
            outcome = (
                "reported and ignored by conforming clients: "
                if tolerated
                else "plugin rejected by conforming clients: "
            )
            findings.append(
                Finding(
                    "schema.portable.manifest",
                    Severity.WARNING if tolerated else Severity.ERROR,
                    rel,
                    outcome + error.message,
                    pointer=_pointer(path_parts),
                    source=PORTABLE_REF,
                )
            )
        findings.extend(_check_mcp(plugin.directory, prefix, version, counts))
    return findings, counts


def _rel(root: Path, path: Path) -> str:
    resolved = path.resolve()
    return resolved.relative_to(root).as_posix() if resolved.is_relative_to(root) else str(path)


def _crashed(repo: Repo, target: Path, reason: str) -> Finding:
    return Finding(
        "schema.claude-validate.crashed",
        Severity.ERROR,
        _rel(repo.root, target),
        f"claude plugin validate produced no usable report: {reason}",
        source=CLAUDE_REF,
    )


CLAUDE_CATALOG = ".claude-plugin/marketplace.json"
# The marketplace run repeats each relative plugin's manifest issues as
# "plugins[N] plugin.json → field"; those are dropped when plugin N is validated directly.
NESTED_MANIFEST = re.compile(r"^plugins\[(\d+)\] plugin\.json →")


def _claude_targets(repo: Repo) -> tuple[list[Path], list[Path]]:
    """Directories to validate, and plugin directories whose own validation is unreachable."""
    targets: list[Path] = []
    unreachable: list[Path] = []
    if (repo.root / CLAUDE_CATALOG).is_file():
        targets.append(repo.root)
    for directory in repo.plugins:
        # `claude plugin validate DIR` selects DIR/.claude-plugin/marketplace.json when it
        # exists, so a plugin that is also a marketplace cannot be validated as a plugin.
        if (directory / CLAUDE_CATALOG).is_file():
            unreachable.append(directory)
        elif directory not in targets:
            targets.append(directory)
    return targets, unreachable


def _directly_validated_indexes(repo: Repo, targets: list[Path]) -> set[int]:
    catalog = repo.catalogs.get(CLAUDE_CATALOG)
    if catalog is None:
        return set()
    # The root is only ever the marketplace run; a plugin at the root is unreachable,
    # so its nested issues must stay in the marketplace run's findings.
    plugin_targets = [target for target in targets if target != repo.root]
    return {
        index
        for index, entry in catalog.entries
        if resolve_local(repo.root, entry.get("source"), catalog.plugin_root) in plugin_targets
    }


def run_claude_validate(
    repo: Repo,
    runner: Runner = _default_runner,
    which: Callable[[str], str | None] = shutil.which,
) -> tuple[list[Finding], Status, str]:
    targets, unreachable = _claude_targets(repo)
    findings = [
        Finding(
            "schema.claude-validate.unreachable",
            Severity.INFO,
            _rel(repo.root, directory) if directory != repo.root else ".",
            "plugin-level `claude plugin validate` cannot run here because the directory is "
            "also a marketplace; its skills, agents, hooks, and MCP files are not validated",
            source=CLAUDE_REF,
        )
        for directory in unreachable
    ]
    note = (
        "plugin-level validation unreachable for: " + ", ".join(f.file for f in findings)
        if findings
        else ""
    )
    if not targets:
        return findings, Status.SKIPPED, note or "no Claude Code catalog or local plugin"
    if which("claude") is None:
        return findings, Status.SKIPPED, "claude not on PATH"
    direct = _directly_validated_indexes(repo, targets)
    inconclusive = False
    for target in targets:
        try:
            proc = runner(["claude", "plugin", "validate", "--strict", "--json", str(target)])
            report = json.loads(proc.stdout)
        except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError) as exc:
            findings.append(_crashed(repo, target, str(exc)))
            inconclusive = True
            continue
        # Exit 0 means success and 1 means failure; anything else, or a report whose
        # shape or success flag disagrees with the exit code, is not evidence either way.
        # A directory without .claude-plugin/plugin.json reports "manifest": null and lists
        # its component files (skills, agents, commands) under "contents".
        if (
            not isinstance(report, dict)
            or "manifest" not in report
            or not (report["manifest"] is None or isinstance(report["manifest"], dict))
            or not isinstance(report.get("success"), bool)
            or proc.returncode not in (0, 1)
            or report["success"] != (proc.returncode == 0)
        ):
            findings.append(
                _crashed(repo, target, f"exit {proc.returncode} with an unexpected report shape")
            )
            inconclusive = True
            continue
        surviving = len(findings)
        for item in [report["manifest"] or {}, *(report.get("contents") or [])]:
            if not isinstance(item, dict):
                continue
            file = _rel(repo.root, Path(str(item.get("file", target))))
            for key, severity, suffix in (
                ("errors", Severity.ERROR, "error"),
                ("warnings", Severity.WARNING, "warning"),
            ):
                for issue in item.get(key) or []:
                    pointer = str(issue.get("path", ""))
                    nested = NESTED_MANIFEST.match(pointer)
                    if target == repo.root and nested and int(nested.group(1)) in direct:
                        continue
                    findings.append(
                        Finding(
                            f"schema.claude-validate.{suffix}",
                            severity,
                            file,
                            str(issue.get("message", "")),
                            pointer=pointer,
                            source=CLAUDE_REF,
                        )
                    )
        if not report["success"] and len(findings) == surviving:
            # A reported failure with no issue left after filtering is not evidence of a pass.
            findings.append(_crashed(repo, target, "it reported failure but no issue survived"))
            inconclusive = True
    if inconclusive:
        return findings, Status.INCONCLUSIVE, "a validator run produced no usable report"
    if any(f.severity == Severity.ERROR for f in findings):
        return findings, Status.FAILED, note
    return findings, Status.PASSED, note
