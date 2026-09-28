"""Record one arm's artefacts: report, tool calls and results, diff, checks, isolation, cost.

Usage: uv run python tests/eval/collect.py RUNS/sN-rK TASKS

TASKS is the dispatching session's task directory; the arm's transcript is the one whose
first message is exactly RUN/prompt.txt, so no agent id is copied by hand.
"""

from __future__ import annotations

import json
import re
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

from isolation import Layout, check_calls, symlink_flags
from objective_checks import check
from prepare import git
from transcript import find, load

SECRET = re.compile(
    r"(ghp_|ghs_|gho_|github_pat_|sk-[A-Za-z0-9]{20}|BEGIN [A-Z ]*PRIVATE KEY|token)", re.I
)


def collect(
    run: Path, tasks: Path, objective: Callable[[Path], dict[str, Any]] = check
) -> dict[str, Any]:
    manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
    path = find(tasks, (run / "prompt.txt").read_text(encoding="utf-8"))
    t = load(path)
    art = run / "artefacts"
    art.mkdir(exist_ok=True)
    (art / "report.md").write_text(t.report.rstrip() + "\n", encoding="utf-8")
    (art / "tool-calls.jsonl").write_text(
        "".join(json.dumps(c) + "\n" for c in t.calls), encoding="utf-8"
    )
    (art / "tool-results.jsonl").write_text(
        "".join(json.dumps(r) + "\n" for r in t.results), encoding="utf-8"
    )
    work = run / "repo"
    git(work, "add", "-A")
    # Against the fixture's tree, not HEAD: an arm may commit, or switch branches.
    diff = git(work, "diff", "--no-ext-diff", "--cached", manifest["fixture_tree"])
    (art / "diff.patch").write_text(diff, encoding="utf-8")
    refs = [
        f"{line}\n{git(work, 'diff', '--no-ext-diff', '--stat', manifest['fixture_tree'], line.split()[0])}"
        for line in git(
            work, "for-each-ref", "--format=%(refname:short) %(objectname:short)"
        ).splitlines()
    ]
    (art / "refs.txt").write_text("\n".join(refs), encoding="utf-8")
    # The objective checks see what would be committed, not the arm's .tool-homes/.
    with tempfile.TemporaryDirectory(prefix="export-") as export:
        git(work, "checkout-index", "-a", f"--prefix={export}/")
        result = objective(Path(export))
    (art / "objective.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    upstream = run / "weather-mcp"
    layout = Layout(
        work=str(work),
        upstream=str(upstream) if upstream.is_dir() else None,
        run_dir=str(run),
        home=str(Path.home()),
        start_cwd=t.start_cwd,
    )
    flags = check_calls(t.calls, layout) + symlink_flags(work, run)
    (art / "isolation-flags.txt").write_text("".join(f"{f}\n" for f in flags), encoding="utf-8")
    hits = [
        f"{item.name}:{number}: {line.strip()[:200]}"
        for item in sorted(art.iterdir())
        if item.name != "secrets.txt"
        for number, line in enumerate(item.read_text(encoding="utf-8").splitlines(), start=1)
        if SECRET.search(line)
    ]
    (art / "secrets.txt").write_text("".join(f"{h}\n" for h in hits), encoding="utf-8")
    manifest.update(
        transcript=path.name, model=",".join(t.models), metrics=t.metrics(), start_cwd=t.start_cwd
    )
    (run / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    summary = {
        "run": run.name,
        **t.metrics(),
        "diff_lines": len(diff.splitlines()),
        "isolation_flags": len(flags),
        "secret_lines": len(hits),
    }
    print(json.dumps(summary))
    return summary


if __name__ == "__main__":
    collect(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
