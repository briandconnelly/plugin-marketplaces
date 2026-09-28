"""Find catalogs and local plugin manifests under a marketplace root."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from mpcheck.jsonload import DuplicateKeyError, load_json
from mpcheck.model import Finding, Severity
from mpcheck.readers import Reader, effective_path, source_path

PORTABLE_SCHEMA_PREFIX = "https://agent-plugins.org/schemas/"
MANIFEST_FILES = (".claude-plugin/plugin.json", ".codex-plugin/plugin.json")


@dataclass
class Catalog:
    relpath: str
    data: dict[str, object]
    entries: list[tuple[int, dict[str, object]]]
    plugin_root: str | None = None


@dataclass
class Plugin:
    directory: Path
    manifests: dict[str, dict[str, object]] = field(default_factory=dict)


@dataclass
class Repo:
    root: Path
    catalogs: dict[str, Catalog]
    reader_catalog: dict[str, str | None]
    plugins: dict[Path, Plugin]

    def readers_of(self, relpath: str, declared: tuple[str, ...]) -> list[str]:
        return [reader for reader in declared if self.reader_catalog.get(reader) == relpath]

    def plugin_for(self, entry: dict[str, object], catalog: Catalog) -> Plugin | None:
        directory = resolve_local(self.root, entry.get("source"), catalog.plugin_root)
        return self.plugins.get(directory) if directory is not None else None


def resolve_local(root: Path, source: object, plugin_root: str | None = None) -> Path | None:
    """The plugin directory for a valid local source inside root, else None."""
    rel = source_path(source)
    if rel is None:
        return None
    rel = effective_path(rel, plugin_root)
    if ".." in Path(rel).parts:
        return None
    try:
        resolved = (root / rel).resolve()
    except (OSError, RuntimeError):
        return None
    if not resolved.is_relative_to(root.resolve()) or not resolved.is_dir():
        return None
    return resolved


def _rel(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def _load(root: Path, path: Path, findings: list[Finding]) -> object | None:
    rel = _rel(root, path)
    try:
        return load_json(path)
    except DuplicateKeyError as exc:
        findings.append(
            Finding(
                "schema.parse.duplicate-key",
                Severity.ERROR,
                rel,
                f"{exc}; tools keep one of the values without warning",
            )
        )
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        findings.append(
            Finding("schema.parse.invalid-json", Severity.ERROR, rel, f"not valid JSON: {exc}")
        )
    return None


def _load_catalog(root: Path, rel: str, findings: list[Finding]) -> Catalog | None:
    data = _load(root, root / rel, findings)
    if data is None:
        return None
    plugins = data.get("plugins") if isinstance(data, dict) else None
    if not isinstance(data, dict) or not isinstance(plugins, list):
        findings.append(
            Finding(
                "schema.parse.catalog-shape",
                Severity.ERROR,
                rel,
                "a catalog must be a JSON object with a 'plugins' array",
            )
        )
        return None
    entries: list[tuple[int, dict[str, object]]] = []
    for index, entry in enumerate(plugins):
        if isinstance(entry, dict) and isinstance(entry.get("name"), str) and "source" in entry:
            entries.append((index, entry))
        else:
            findings.append(
                Finding(
                    "schema.parse.entry-shape",
                    Severity.ERROR,
                    rel,
                    "an entry must be an object with a string 'name' and a 'source'",
                    pointer=f"/plugins/{index}",
                )
            )
    metadata = data.get("metadata")
    plugin_root = metadata.get("pluginRoot") if isinstance(metadata, dict) else None
    return Catalog(rel, data, entries, plugin_root if isinstance(plugin_root, str) else None)


def _manifest_shape(root: Path, path: Path) -> Finding:
    return Finding(
        "schema.parse.manifest-shape",
        Severity.ERROR,
        _rel(root, path),
        "a plugin manifest must be a JSON object; tools ignore or reject this one",
    )


def _load_plugin(root: Path, directory: Path, findings: list[Finding]) -> Plugin:
    plugin = Plugin(directory)
    for rel in MANIFEST_FILES:
        path = directory / rel
        if path.is_file():
            data = _load(root, path, findings)
            if isinstance(data, dict):
                plugin.manifests[rel] = data
            elif data is not None:
                findings.append(_manifest_shape(root, path))
    portable = directory / "plugin.json"
    portable_rel = _rel(root, portable)
    if portable.is_symlink():
        findings.append(
            Finding(
                "local.portable-symlink",
                Severity.ERROR,
                portable_rel,
                "a symlinked root plugin.json disables manifest detection in Codex",
            )
        )
    elif portable.is_file():
        data = _load(root, portable, findings)
        if data is not None and not isinstance(data, dict):
            findings.append(_manifest_shape(root, portable))
        elif isinstance(data, dict):
            schema = data.get("$schema")
            if isinstance(schema, str) and schema.startswith(PORTABLE_SCHEMA_PREFIX):
                plugin.manifests["plugin.json"] = data
            else:
                findings.append(
                    Finding(
                        "local.portable-schema-missing",
                        Severity.WARNING,
                        portable_rel,
                        "root plugin.json lacks the Agent Plugins $schema, so portable readers "
                        "treat it as unrelated and fall back to other manifests",
                    )
                )
    return plugin


def discover(root: Path, readers: dict[str, Reader]) -> tuple[Repo, list[Finding]]:
    root = root.resolve()
    findings: list[Finding] = []
    candidates: list[str] = []
    for reader in readers.values():
        for rel in reader.catalog_paths:
            if rel not in candidates:
                candidates.append(rel)
    present = [rel for rel in candidates if (root / rel).is_file()]
    if not present:
        findings.append(
            Finding(
                "schema.parse.no-catalog",
                Severity.ERROR,
                ".",
                f"no catalog found; covered readers look for: {', '.join(candidates)}",
            )
        )
    catalogs: dict[str, Catalog] = {}
    for rel in present:
        catalog = _load_catalog(root, rel, findings)
        if catalog is not None:
            catalogs[rel] = catalog
    reader_catalog = {
        reader.id: next((rel for rel in reader.catalog_paths if rel in present), None)
        for reader in readers.values()
    }
    plugins: dict[Path, Plugin] = {}
    for catalog in catalogs.values():
        for _, entry in catalog.entries:
            directory = resolve_local(root, entry.get("source"), catalog.plugin_root)
            if directory is not None and directory not in plugins:
                plugins[directory] = _load_plugin(root, directory, findings)
    return Repo(root, catalogs, reader_catalog, plugins), findings
