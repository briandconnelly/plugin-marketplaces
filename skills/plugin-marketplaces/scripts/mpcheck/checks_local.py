"""Checks no official validator covers (spec §8, level 2)."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from mpcheck.discover import Catalog, Repo
from mpcheck.model import Finding, Severity
from mpcheck.policy import POLICY_FILE, Policy
from mpcheck.readers import (
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


LOCAL_CHECKS: list[Check] = [
    check_reader_coverage,
    check_unread_catalogs,
    check_source_types,
    check_local_paths,
]
