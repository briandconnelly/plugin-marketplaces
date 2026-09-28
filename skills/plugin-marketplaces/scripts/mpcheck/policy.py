"""marketplace-policy.json: declared readers, parity exceptions, and channels (spec R1, R4, R10)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from mpcheck.jsonload import DuplicateKeyError, load_json
from mpcheck.model import Finding, Severity
from mpcheck.readers import Reader

POLICY_FILE = "marketplace-policy.json"
EXCEPTION_KINDS = frozenset({"membership", "version", "source"})


@dataclass(frozen=True)
class ParityException:
    plugin: str
    kind: str
    reason: str


@dataclass(frozen=True)
class Channel:
    """A git ref deliberately tracked without a pinned sha (a release channel)."""

    plugin: str
    ref: str
    reason: str


@dataclass(frozen=True)
class Policy:
    readers: tuple[str, ...]
    exceptions: tuple[ParityException, ...]
    declared: bool
    channels: tuple[Channel, ...] = ()

    def excepts(self, plugin: str, kind: str) -> bool:
        return any(e.plugin == plugin and e.kind == kind for e in self.exceptions)

    def channel(self, plugin: str, ref: object) -> Channel | None:
        return next((c for c in self.channels if c.plugin == plugin and c.ref == ref), None)


def _display(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix() if path.is_relative_to(root) else str(path)


def _text(item: dict[str, object], key: str) -> str | None:
    value = item.get(key)
    return value.strip() if isinstance(value, str) and value.strip() else None


def load_policy(
    root: Path,
    path: Path | None,
    readers: dict[str, Reader],
    reading: dict[str, str | None],
) -> tuple[Policy, list[Finding]]:
    root = root.resolve()
    path = (path if path is not None else root / POLICY_FILE).resolve()
    rel = _display(root, path)
    findings: list[Finding] = []
    if not path.is_file():
        # Infer only readers whose own first-choice catalog exists; a tool that merely
        # falls back to another tool's catalog is not assumed to be a target.
        inferred = tuple(
            r for r in sorted(readers) if reading.get(r) == readers[r].catalog_paths[0]
        )
        others = sorted(r for r in readers if reading.get(r) and r not in inferred)
        message = (
            "no policy file; inferred target readers from their native catalogs: "
            f"{', '.join(inferred) or 'none'}"
        )
        if others:
            message += (
                f"; {', '.join(others)} would also read a catalog here — declare them in "
                f"{POLICY_FILE} to check compatibility"
            )
        findings.append(Finding("policy.inferred", Severity.WARNING, rel, message, rule="R1"))
        return Policy(inferred, (), declared=False), findings
    try:
        raw = load_json(path)
    except (DuplicateKeyError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        findings.append(
            Finding("policy.invalid", Severity.ERROR, rel, f"cannot read policy: {exc}", rule="R1")
        )
        return Policy((), (), declared=True), findings
    raw = raw if isinstance(raw, dict) else {}
    readers_raw = raw.get("readers")
    if not (
        isinstance(readers_raw, list)
        and readers_raw
        and all(isinstance(r, str) for r in readers_raw)
    ):
        findings.append(
            Finding(
                "policy.invalid",
                Severity.ERROR,
                rel,
                "'readers' must be a non-empty array of reader ids",
                rule="R1",
                pointer="/readers",
            )
        )
        readers_raw = []
    declared: list[str] = []
    for reader_id in readers_raw:
        if reader_id in readers:
            declared.append(reader_id)
        else:
            findings.append(
                Finding(
                    "policy.unknown-reader",
                    Severity.ERROR,
                    rel,
                    f"unknown reader {reader_id!r}; covered readers: {', '.join(sorted(readers))}",
                    rule="R1",
                    pointer="/readers",
                )
            )
    exceptions: list[ParityException] = []
    for index, item in enumerate(_array(raw, "exceptions", rel, "R10", findings)):
        kind = item.get("kind") if isinstance(item, dict) else None
        plugin = _text(item, "plugin") if isinstance(item, dict) else None
        reason = _text(item, "reason") if isinstance(item, dict) else None
        if plugin and isinstance(kind, str) and kind in EXCEPTION_KINDS and reason:
            exceptions.append(ParityException(plugin, kind, reason))
        else:
            findings.append(
                Finding(
                    "policy.invalid-exception",
                    Severity.ERROR,
                    rel,
                    "an exception needs 'plugin', 'kind' (membership, version, or source), "
                    "and a non-empty 'reason'",
                    rule="R10",
                    pointer=f"/exceptions/{index}",
                )
            )
    channels: list[Channel] = []
    for index, item in enumerate(_array(raw, "channels", rel, "R4", findings)):
        plugin = _text(item, "plugin") if isinstance(item, dict) else None
        ref = _text(item, "ref") if isinstance(item, dict) else None
        reason = _text(item, "reason") if isinstance(item, dict) else None
        if plugin and ref and reason:
            channels.append(Channel(plugin, ref, reason))
        else:
            findings.append(
                Finding(
                    "policy.invalid-channel",
                    Severity.ERROR,
                    rel,
                    "a channel needs 'plugin', 'ref', and a non-empty 'reason'",
                    rule="R4",
                    pointer=f"/channels/{index}",
                )
            )
    return Policy(tuple(declared), tuple(exceptions), True, tuple(channels)), findings


def _array(
    raw: dict[str, object], key: str, rel: str, rule: str, findings: list[Finding]
) -> list[object]:
    value = raw.get(key, [])
    if isinstance(value, list):
        return value
    findings.append(
        Finding(
            "policy.invalid",
            Severity.ERROR,
            rel,
            f"'{key}' must be an array",
            rule=rule,
            pointer=f"/{key}",
        )
    )
    return []
