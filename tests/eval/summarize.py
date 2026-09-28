"""Tabulate run records: one row per run, then one row per scenario.

Usage: uv run python tests/eval/summarize.py tests/runs/DATE-s?-r[0-9]*-ARM*.md

Only `sN-rK` record names are accepted; the plan-2a records in the same directory (for example
`DATE-s1-baseline-discarded.md`) use an older form and are rejected with a `ValueError`.
"""

from __future__ import annotations

import re
import statistics
import sys
from collections import Counter
from pathlib import Path

from records import failed_criteria, load, manifest, score


def run_id(path: Path) -> str:
    match = re.match(r"\d{4}-\d{2}-\d{2}-(s\d+-r\d+)-", path.name)
    if match is None:
        raise ValueError(f"not a run record name: {path.name}")
    return match.group(1)


def summarize(paths: list[Path]) -> str:
    rows = [
        "| Run | Result | Criteria failed | Tool calls | Wall time (s) | Status |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    per: dict[str, list[tuple[tuple[int, int], list[int], dict]]] = {}
    for path in sorted(paths, key=lambda p: [int(n) for n in re.findall(r"\d+", run_id(p))]):
        text = load(path)
        metrics = manifest(text).get("metrics", {})
        cost = f"{metrics.get('tool_calls', '—')} | {metrics.get('wall_seconds', '—')}"
        if path.stem.endswith("-discarded"):
            rows.append(f"| {run_id(path)} | — | — | {cost} | discarded |")
            continue
        result, failed = score(text), failed_criteria(text)
        if result is None:
            raise ValueError(f"{path.name}: no 'Total: N of M passed.' line")
        shown = ", ".join(map(str, failed)) or "none"
        rows.append(f"| {run_id(path)} | {result[0]}/{result[1]} | {shown} | {cost} | scored |")
        per.setdefault(run_id(path).split("-")[0], []).append((result, failed, metrics))
    rows += [
        "",
        "| Scenario | Scored runs | Full marks | Failures by criterion | Median tool calls | Median wall time (s) |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for name in sorted(per, key=lambda s: int(s[1:])):
        runs = per[name]
        counts = Counter(c for _, failed, _ in runs for c in failed)
        failures = ", ".join(f"{c}×{n}" for c, n in sorted(counts.items())) or "none"
        calls = statistics.median(m["tool_calls"] for *_, m in runs)
        wall = statistics.median(m["wall_seconds"] for *_, m in runs)
        full = sum(r[0] == r[1] for r, _, _ in runs)
        rows.append(f"| {name} | {len(runs)} | {full} | {failures} | {calls} | {wall} |")
    return "\n".join(rows)


if __name__ == "__main__":
    print(summarize([Path(p) for p in sys.argv[1:]]))
