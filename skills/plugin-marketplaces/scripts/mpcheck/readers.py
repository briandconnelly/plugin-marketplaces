"""Reader facts from readers.json, and classification of catalog sources."""

from __future__ import annotations

import json
import posixpath
import re
from dataclasses import dataclass
from pathlib import Path

DEFAULT_READERS_PATH = Path(__file__).resolve().parent / "data" / "readers.json"
GIT_SOURCE_TYPES = frozenset({"github", "url", "git-subdir"})


@dataclass(frozen=True)
class Reader:
    id: str
    reference: str
    catalog_paths: tuple[str, ...]
    source_types: frozenset[str]
    path_requires_dot_slash: bool
    path_prefix_exempt_catalogs: frozenset[str]
    honours_plugin_root: bool
    marketplace_name_re: re.Pattern[str] | None
    entry_name_re: re.Pattern[str] | None
    reads_entry_hooks: bool


def _compile(pattern: str | None) -> re.Pattern[str] | None:
    return re.compile(pattern) if pattern is not None else None


def load_readers(path: Path = DEFAULT_READERS_PATH) -> dict[str, Reader]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    readers: dict[str, Reader] = {}
    for reader_id, spec in raw.items():
        if reader_id.startswith("$"):
            continue
        readers[reader_id] = Reader(
            id=reader_id,
            reference=spec["reference"],
            catalog_paths=tuple(spec["catalog_paths"]),
            source_types=frozenset(spec["source_types"]),
            path_requires_dot_slash=spec["path_requires_dot_slash"],
            path_prefix_exempt_catalogs=frozenset(spec.get("path_prefix_exempt_catalogs", [])),
            honours_plugin_root=spec.get("honours_plugin_root", False),
            marketplace_name_re=_compile(spec.get("marketplace_name_pattern")),
            entry_name_re=_compile(spec.get("entry_name_pattern")),
            reads_entry_hooks=spec.get("reads_entry_hooks", False),
        )
    return readers


def source_type(source: object) -> str:
    if isinstance(source, str):
        return "path"
    if isinstance(source, dict):
        kind = source.get("source")
        if kind == "local":
            return "local-object"
        if isinstance(kind, str) and kind:
            return kind
    return "invalid"


def is_bare(rel: str) -> bool:
    """A local path that neither is '.' nor starts with './'."""
    return not (rel == "." or rel.startswith("./"))


def effective_path(rel: str, plugin_root: str | None) -> str:
    """A bare name without '/' resolves under the catalog's metadata.pluginRoot, when one is set."""
    if plugin_root and is_bare(rel) and "/" not in rel:
        return posixpath.join(plugin_root, rel)
    return rel


def source_path(source: object) -> str | None:
    if isinstance(source, str):
        return source
    if isinstance(source, dict) and source.get("source") == "local":
        path = source.get("path")
        return path if isinstance(path, str) else None
    return None
