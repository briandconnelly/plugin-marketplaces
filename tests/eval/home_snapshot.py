"""Snapshot real tool homes around a batch of scenario arms, so any change is attributable.

Usage:
  uv run python tests/eval/home_snapshot.py save OUT.json DIR...
  uv run python tests/eval/home_snapshot.py compare BEFORE.json AFTER.json

`save` records every file under each DIR as its SHA-256 (symlinks by target, never
followed). `compare` prints each added, removed, or changed file and exits 1 if there is
any, so a clean comparison is a checked result, not an absence of output.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path


def snapshot(roots: list[Path]) -> dict[str, dict[str, str] | None]:
    out: dict[str, dict[str, str] | None] = {}
    for root in roots:
        if not root.is_dir():
            out[str(root)] = None
            continue
        files: dict[str, str] = {}
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if not (Path(dirpath) / d).is_symlink()]
            links = [
                Path(dirpath) / d for d in os.listdir(dirpath) if (Path(dirpath) / d).is_symlink()
            ]
            for path in [
                Path(dirpath) / f for f in filenames if not (Path(dirpath) / f).is_symlink()
            ]:
                try:
                    files[str(path.relative_to(root))] = hashlib.sha256(
                        path.read_bytes()
                    ).hexdigest()
                except OSError as exc:  # a socket or unreadable file is still recorded
                    files[str(path.relative_to(root))] = f"unreadable: {exc.strerror}"
            for link in links:
                files[str(link.relative_to(root))] = f"symlink: {os.readlink(link)}"
        out[str(root)] = files
    return out


def compare(before: dict, after: dict) -> list[str]:
    changes: list[str] = []
    for root in sorted(set(before) | set(after)):
        old, new = before.get(root) or {}, after.get(root) or {}
        if (before.get(root) is None) != (after.get(root) is None):
            changes.append(f"{'created' if before.get(root) is None else 'deleted'} {root}")
        for rel in sorted(set(old) | set(new)):
            if rel not in old:
                changes.append(f"added {root}/{rel}")
            elif rel not in new:
                changes.append(f"removed {root}/{rel}")
            elif old[rel] != new[rel]:
                changes.append(f"changed {root}/{rel}")
    return changes


def main(argv: list[str]) -> int:
    if len(argv) >= 3 and argv[0] == "save":
        data = snapshot([Path(p).expanduser() for p in argv[2:]])
        Path(argv[1]).write_text(
            json.dumps(data, indent=1, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(f"saved {sum(len(v or {}) for v in data.values())} files from {len(data)} roots")
        return 0
    if len(argv) == 3 and argv[0] == "compare":
        before, after = (json.loads(Path(p).read_text(encoding="utf-8")) for p in argv[1:])
        changes = compare(before, after)
        print("\n".join(changes) if changes else "no changes")
        return 1 if changes else 0
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
