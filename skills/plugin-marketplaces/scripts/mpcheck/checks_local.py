"""Checks no official validator covers (spec §8, level 2)."""

from __future__ import annotations

import posixpath
import re
from collections.abc import Callable
from pathlib import Path

from mpcheck.discover import Catalog, Repo
from mpcheck.model import Finding, Severity
from mpcheck.policy import POLICY_FILE, Policy
from mpcheck.readers import (
    GIT_SOURCE_TYPES,
    Reader,
    effective_path,
    is_bare,
    source_path,
    source_type,
)

Check = Callable[[Repo, dict[str, Reader], Policy], list[Finding]]


def active_catalogs(repo: Repo, policy: Policy) -> list[Catalog]:
    return [c for c in repo.catalogs.values() if repo.readers_of(c.relpath, policy.readers)]


def _readers_of(
    repo: Repo, readers: dict[str, Reader], policy: Policy, catalog: Catalog
) -> list[Reader]:
    return [readers[r] for r in repo.readers_of(catalog.relpath, policy.readers)]


def check_reader_coverage(repo: Repo, readers: dict[str, Reader], policy: Policy) -> list[Finding]:
    return [
        Finding(
            "local.reader-no-catalog",
            Severity.ERROR,
            POLICY_FILE,
            f"declared reader {r!r} finds no catalog; it reads the first of: "
            f"{', '.join(readers[r].catalog_paths)}",
            rule="R1",
            source=readers[r].reference,
        )
        for r in policy.readers
        if repo.reader_catalog.get(r) is None
    ]


def check_unread_catalogs(repo: Repo, readers: dict[str, Reader], policy: Policy) -> list[Finding]:
    active = {c.relpath for c in active_catalogs(repo, policy)}
    return [
        Finding(
            "local.unread-catalog",
            Severity.WARNING,
            rel,
            "no declared reader reads this catalog (another file takes precedence, "
            "or its readers are not declared); its entries are not checked for reader "
            "compatibility",
            rule="R1",
        )
        for rel in repo.catalogs
        if rel not in active
    ]


def check_source_types(repo: Repo, readers: dict[str, Reader], policy: Policy) -> list[Finding]:
    findings: list[Finding] = []
    for catalog in active_catalogs(repo, policy):
        for reader in _readers_of(repo, readers, policy, catalog):
            for index, entry in catalog.entries:
                kind = source_type(entry["source"])
                if kind not in reader.source_types:
                    findings.append(
                        Finding(
                            "local.source-type",
                            Severity.ERROR,
                            catalog.relpath,
                            f"{reader.id} does not accept source type {kind!r} "
                            f"(accepts: {', '.join(sorted(reader.source_types))}); "
                            f"it skips or rejects entry {entry['name']!r}",
                            rule="R2",
                            pointer=f"/plugins/{index}/source",
                            source=reader.reference,
                        )
                    )
    return findings


def check_local_paths(repo: Repo, readers: dict[str, Reader], policy: Policy) -> list[Finding]:
    findings: list[Finding] = []
    for catalog in active_catalogs(repo, policy):
        catalog_readers = _readers_of(repo, readers, policy, catalog)
        for index, entry in catalog.entries:
            rel = source_path(entry["source"])
            where = {"file": catalog.relpath, "pointer": f"/plugins/{index}/source", "rule": "R3"}
            if rel is None:
                if source_type(entry["source"]) == "local-object":
                    findings.append(
                        Finding(
                            "local.path-invalid",
                            Severity.ERROR,
                            message="a local source object needs a string 'path'",
                            **where,
                        )
                    )
                continue
            if is_bare(rel):
                # A bare name without '/' resolves under metadata.pluginRoot for readers
                # that honour it; every other reader that requires './' rejects it.
                under_root = bool(catalog.plugin_root) and "/" not in rel
                offenders = [
                    r.id
                    for r in catalog_readers
                    if r.path_requires_dot_slash
                    and catalog.relpath not in r.path_prefix_exempt_catalogs
                    and not (under_root and r.honours_plugin_root)
                ]
                if offenders:
                    hint = " (metadata.pluginRoot does not apply for them)" if under_root else ""
                    findings.append(
                        Finding(
                            "local.path-prefix",
                            Severity.ERROR,
                            message=f"local source {rel!r} must start with './' for "
                            f"{', '.join(offenders)}{hint}",
                            **where,
                        )
                    )
            rel = effective_path(rel, catalog.plugin_root)
            if ".." in Path(rel).parts:
                findings.append(
                    Finding(
                        "local.path-traversal",
                        Severity.ERROR,
                        message=f"local source {rel!r} contains '..'",
                        **where,
                    )
                )
                continue
            try:
                resolved = (repo.root / rel).resolve()
            except (OSError, RuntimeError):
                resolved = None
            if resolved is None:
                findings.append(
                    Finding(
                        "local.path-missing",
                        Severity.ERROR,
                        message=f"local source {rel!r} cannot be resolved (symlink loop?)",
                        **where,
                    )
                )
            elif not resolved.is_relative_to(repo.root):
                findings.append(
                    Finding(
                        "local.path-escape",
                        Severity.ERROR,
                        message=f"local source {rel!r} resolves outside the marketplace root, "
                        f"to {resolved}",
                        **where,
                    )
                )
            elif not resolved.is_dir():
                findings.append(
                    Finding(
                        "local.path-missing",
                        Severity.ERROR,
                        message=f"local source {rel!r} is not a directory under the marketplace root",
                        **where,
                    )
                )
    return findings


def check_names(repo: Repo, readers: dict[str, Reader], policy: Policy) -> list[Finding]:
    findings: list[Finding] = []
    for catalog in active_catalogs(repo, policy):
        catalog_readers = _readers_of(repo, readers, policy, catalog)
        name = catalog.data.get("name")
        for reader in catalog_readers:
            pattern = reader.marketplace_name_re
            if pattern is not None and not (isinstance(name, str) and pattern.fullmatch(name)):
                findings.append(
                    Finding(
                        "local.marketplace-name",
                        Severity.ERROR,
                        catalog.relpath,
                        f"marketplace name {name!r} does not satisfy {reader.id}'s name rule "
                        f"({pattern.pattern})",
                        pointer="/name",
                        source=reader.reference,
                    )
                )
        seen: dict[str, int] = {}
        for index, entry in catalog.entries:
            entry_name = entry["name"]
            assert isinstance(entry_name, str)
            pointer = f"/plugins/{index}/name"
            if entry_name in seen:
                findings.append(
                    Finding(
                        "local.duplicate-entry",
                        Severity.ERROR,
                        catalog.relpath,
                        f"entry name {entry_name!r} is also used at /plugins/{seen[entry_name]}",
                        rule="R8",
                        pointer=pointer,
                    )
                )
            seen.setdefault(entry_name, index)
            for reader in catalog_readers:
                pattern = reader.entry_name_re
                if pattern is not None and not pattern.fullmatch(entry_name):
                    findings.append(
                        Finding(
                            "local.entry-name-pattern",
                            Severity.ERROR,
                            catalog.relpath,
                            f"entry name {entry_name!r} does not satisfy {reader.id}'s name rule "
                            f"({pattern.pattern})",
                            rule="R8",
                            pointer=pointer,
                            source=reader.reference,
                        )
                    )
            plugin = repo.plugin_for(entry, catalog)
            if plugin is None:
                continue
            prefix = plugin.directory.relative_to(repo.root).as_posix()
            for manifest_rel, manifest in plugin.manifests.items():
                manifest_name = manifest.get("name")
                if isinstance(manifest_name, str) and manifest_name != entry_name:
                    findings.append(
                        Finding(
                            "local.name-mismatch",
                            Severity.ERROR,
                            catalog.relpath,
                            f"entry {entry_name!r} but {prefix}/{manifest_rel} names the plugin "
                            f"{manifest_name!r}; tools install by one and namespace by the other",
                            rule="R8",
                            pointer=pointer,
                        )
                    )
    return findings


def _version_values(
    repo: Repo, catalog: Catalog, index: int, entry: dict[str, object]
) -> dict[str, str]:
    values: dict[str, str] = {}
    version = entry.get("version")
    if isinstance(version, str):
        values[f"{catalog.relpath}#/plugins/{index}/version"] = version
    plugin = repo.plugin_for(entry, catalog)
    if plugin is not None:
        prefix = plugin.directory.relative_to(repo.root).as_posix()
        for manifest_rel, manifest in plugin.manifests.items():
            manifest_version = manifest.get("version")
            if isinstance(manifest_version, str):
                values[f"{prefix}/{manifest_rel}#/version"] = manifest_version
    return values


def check_versions(repo: Repo, readers: dict[str, Reader], policy: Policy) -> list[Finding]:
    findings: list[Finding] = []
    for catalog in active_catalogs(repo, policy):
        for index, entry in catalog.entries:
            values = _version_values(repo, catalog, index, entry)
            if len(set(values.values())) > 1:
                detail = "; ".join(f"{where} = {value}" for where, value in values.items())
                findings.append(
                    Finding(
                        "local.version-mismatch",
                        Severity.ERROR,
                        catalog.relpath,
                        f"plugin {entry['name']!r} records different versions: {detail}",
                        rule="R6",
                        pointer=f"/plugins/{index}",
                    )
                )
            elif values and (plugin := repo.plugin_for(entry, catalog)) is not None:
                prefix = plugin.directory.relative_to(repo.root).as_posix()
                recorded = next(iter(values.values()))
                for manifest_rel, manifest in plugin.manifests.items():
                    if not isinstance(manifest.get("version"), str):
                        findings.append(
                            Finding(
                                "local.version-field-missing",
                                Severity.WARNING,
                                catalog.relpath,
                                f"{prefix}/{manifest_rel} has no version while other fields "
                                f"record {recorded}; the reader that uses this manifest derives "
                                "a version of its own instead",
                                rule="R6",
                                pointer=f"/plugins/{index}",
                            )
                        )
            elif not values and repo.plugin_for(entry, catalog) is not None:
                findings.append(
                    Finding(
                        "local.version-missing",
                        Severity.WARNING,
                        catalog.relpath,
                        f"local plugin {entry['name']!r} has no version anywhere; tools fall back "
                        "to a commit SHA or a fixed cache directory name, so releases are not "
                        "distinguishable by version",
                        rule="R6",
                        pointer=f"/plugins/{index}",
                    )
                )
    return findings


def pin_of(source: object, plugin_root: str | None = None) -> str | None:
    rel = source_path(source)
    if rel is not None:
        return "path:" + posixpath.normpath(effective_path(rel, plugin_root))
    if isinstance(source, dict):
        for key in ("sha", "sha256"):
            value = source.get(key)
            if isinstance(value, str):
                return f"{key}:{value}"
        version = source.get("version")
        if source.get("source") == "npm" and isinstance(version, str):
            return "npm:" + version
    return None


def check_parity(repo: Repo, readers: dict[str, Reader], policy: Policy) -> list[Finding]:
    findings: list[Finding] = []
    used: set[tuple[str, str]] = set()
    active = active_catalogs(repo, policy)
    if len(active) >= 2:
        index_of = {c.relpath: {str(e["name"]): (i, e) for i, e in c.entries} for c in active}
        by_rel = {c.relpath: c for c in active}
        for name in sorted(set().union(*index_of.values())):
            present = [rel for rel, entries in index_of.items() if name in entries]
            missing = [rel for rel in index_of if rel not in present]
            if missing:
                if policy.excepts(name, "membership"):
                    used.add((name, "membership"))
                else:
                    findings.append(
                        Finding(
                            "local.parity-membership",
                            Severity.ERROR,
                            missing[0],
                            f"plugin {name!r} is in {', '.join(present)} but not in "
                            f"{', '.join(missing)}; add it, or record a 'membership' exception "
                            "with a reason",
                            rule="R10",
                        )
                    )
                continue
            versions: set[str] = set()
            pins: set[str] = set()
            for rel, (index, entry) in ((r, index_of[r][name]) for r in present):
                values = set(_version_values(repo, by_rel[rel], index, entry).values())
                if len(values) == 1:
                    versions |= values
                pin = pin_of(entry["source"], by_rel[rel].plugin_root)
                if pin is not None:
                    pins.add(pin)
            for kind, differing, check in (
                ("version", versions, "local.parity-version"),
                ("source", pins, "local.parity-source"),
            ):
                if len(differing) > 1:
                    if policy.excepts(name, kind):
                        used.add((name, kind))
                    else:
                        findings.append(
                            Finding(
                                check,
                                Severity.ERROR,
                                present[0],
                                f"plugin {name!r} differs in {kind} across catalogs "
                                f"({', '.join(sorted(differing))}); align them, or record a "
                                f"{kind!r} exception with a reason",
                                rule="R10",
                            )
                        )
    for exception in policy.exceptions:
        if (exception.plugin, exception.kind) not in used:
            findings.append(
                Finding(
                    "policy.unused-exception",
                    Severity.WARNING,
                    POLICY_FILE,
                    f"exception for {exception.plugin!r} ({exception.kind}) matches no current "
                    "difference; remove it so it cannot hide a future one",
                    rule="R10",
                )
            )
    return findings


SHA_RE = re.compile(r"^[0-9a-f]{40}$")

SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")

EXACT_SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$")


def _pin_finding(check: str, catalog: Catalog, index: int, message: str) -> Finding:
    return Finding(
        check,
        Severity.ERROR,
        catalog.relpath,
        message,
        rule="R4",
        pointer=f"/plugins/{index}/source",
    )


def check_pins(repo: Repo, readers: dict[str, Reader], policy: Policy) -> list[Finding]:
    findings: list[Finding] = []
    used_channels: set[tuple[str, str]] = set()
    for catalog in active_catalogs(repo, policy):
        for index, entry in catalog.entries:
            source = entry["source"]
            kind = source_type(source)
            name = entry["name"]
            if not isinstance(source, dict):
                continue
            if kind in GIT_SOURCE_TYPES:
                sha = source.get("sha")
                channel = policy.channel(str(name), source.get("ref")) if sha is None else None
                if channel is not None:
                    used_channels.add((channel.plugin, channel.ref))
                    findings.append(
                        Finding(
                            "local.pin-channel",
                            Severity.INFO,
                            catalog.relpath,
                            f"{name!r} tracks the declared channel ref {channel.ref!r}; users "
                            f"receive every push without a reviewed pin move ({channel.reason})",
                            rule="R4",
                            pointer=f"/plugins/{index}/source",
                        )
                    )
                elif sha is None:
                    findings.append(
                        _pin_finding(
                            "local.pin-missing",
                            catalog,
                            index,
                            f"git source for {name!r} has no 'sha'; a moving ref ships whatever is pushed next",
                        )
                    )
                elif not (isinstance(sha, str) and SHA_RE.fullmatch(sha)):
                    findings.append(
                        _pin_finding(
                            "local.pin-malformed",
                            catalog,
                            index,
                            f"'sha' for {name!r} must be a full 40-character lowercase commit SHA",
                        )
                    )
            elif kind == "archive":
                digest = source.get("sha256")
                if digest is None:
                    findings.append(
                        _pin_finding(
                            "local.pin-missing",
                            catalog,
                            index,
                            f"archive source for {name!r} has no 'sha256'",
                        )
                    )
                elif not (isinstance(digest, str) and SHA256_RE.fullmatch(digest)):
                    findings.append(
                        _pin_finding(
                            "local.pin-malformed",
                            catalog,
                            index,
                            f"'sha256' for {name!r} must be 64 hex characters",
                        )
                    )
            elif kind == "npm":
                version = source.get("version")
                if not (isinstance(version, str) and EXACT_SEMVER_RE.fullmatch(version)):
                    findings.append(
                        _pin_finding(
                            "local.pin-missing",
                            catalog,
                            index,
                            f"npm source for {name!r} needs an exact 'version', not a range or dist-tag",
                        )
                    )
            elif kind == "pip":
                findings.append(
                    Finding(
                        "local.pin-unverified",
                        Severity.WARNING,
                        catalog.relpath,
                        f"no pin rule for pip sources has been verified; review {name!r} by hand",
                        rule="R4",
                        pointer=f"/plugins/{index}/source",
                    )
                )
            elif kind == "command":
                findings.append(
                    _pin_finding(
                        "local.pin-unpinnable",
                        catalog,
                        index,
                        f"command source for {name!r} cannot be pinned and must not appear in a "
                        "published catalog",
                    )
                )
    for channel in policy.channels:
        if (channel.plugin, channel.ref) not in used_channels:
            findings.append(
                Finding(
                    "policy.unused-channel",
                    Severity.WARNING,
                    POLICY_FILE,
                    f"channel {channel.ref!r} for {channel.plugin!r} matches no unpinned git "
                    "source; remove it so it cannot excuse a future unpinned entry",
                    rule="R4",
                )
            )
    return findings


def check_entry_hooks(repo: Repo, readers: dict[str, Reader], policy: Policy) -> list[Finding]:
    findings: list[Finding] = []
    for catalog in active_catalogs(repo, policy):
        hook_readers = [
            r for r in _readers_of(repo, readers, policy, catalog) if r.reads_entry_hooks
        ]
        if not hook_readers:
            continue
        for index, entry in catalog.entries:
            if isinstance(entry.get("hooks"), (str, list)):
                findings.append(
                    Finding(
                        "local.entry-hooks-path",
                        Severity.ERROR,
                        catalog.relpath,
                        "entry 'hooks' must be an inline object; a path or array passes "
                        "`claude plugin validate` but the hooks never run",
                        pointer=f"/plugins/{index}/hooks",
                        source=hook_readers[0].reference,
                    )
                )
    return findings


def check_portable_mcp(repo: Repo, readers: dict[str, Reader], policy: Policy) -> list[Finding]:
    findings: list[Finding] = []
    for plugin in repo.plugins.values():
        directory = plugin.directory
        if (
            "plugin.json" in plugin.manifests
            and (directory / ".mcp.json").is_file()
            and not (directory / "mcp.json").is_file()
        ):
            findings.append(
                Finding(
                    "local.portable-mcp-missing",
                    Severity.WARNING,
                    (directory / ".mcp.json").relative_to(repo.root).as_posix(),
                    "portable readers load MCP servers only from mcp.json, with a transport "
                    "'type' on each server; these servers are invisible to them",
                    source="references/agent-plugins.md",
                )
            )
    return findings


LOCAL_CHECKS: list[Check] = [
    check_reader_coverage,
    check_unread_catalogs,
    check_source_types,
    check_local_paths,
    check_names,
    check_versions,
    check_parity,
    check_pins,
    check_entry_hooks,
    check_portable_mcp,
]
