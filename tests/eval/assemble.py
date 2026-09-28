"""Write a run record, tests/runs/DATE-sN-rK-ARM.md, from a run's recorded artefacts.

Usage: uv run python tests/eval/assemble.py RUNS/sN-rK TASKS OUT_DIR --note "TEXT" [--discarded]

The scorer's reply comes from its transcript (the one whose prompt names this run's
score-prompt.txt); a discarded run is recorded unscored. `redact` rewrites the run's
directories, the dispatching session's directory and id, the home directory, and the
harness's encoded project path, so a record names no local user or session.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from transcript import find_containing, load

DISCARDED = (
    "Not scored: this run was discarded (see Isolation). It is kept so any observation drawn "
    "from it can be audited; it is not evidence for the arm's score."
)


UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")


def redact(doc: str, run: Path) -> str:
    session = run.parent.parent.parent
    for path, name in (
        (run, "$RUN"),
        (run.parent, "$RUNS"),
        (run.parent.parent, "$SCRATCH"),
        (session, "$SESSION"),
        (Path.home(), "~"),
    ):
        doc = doc.replace(str(path), name)
    doc = re.sub(r"\.claude/projects/[^/\s\"'`]+", ".claude/projects/$PROJECT", doc)
    if UUID.fullmatch(session.name):
        doc = doc.replace(session.name, "$SESSION_ID")
    return doc


def assemble(run: Path, tasks: Path, out: Path, note: str, discarded: bool = False) -> Path:
    manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
    art = run / "artefacts"
    table = DISCARDED
    if not discarded:
        scorer = load(find_containing(tasks, str(run / "score-prompt.txt")))
        table, manifest["scorer_model"] = scorer.report, ",".join(scorer.models)
    flags = (art / "isolation-flags.txt").read_text(encoding="utf-8").strip() or "(none)"
    title = f"# Run: scenario {manifest['scenario'][1:]}, repetition {manifest['rep']}, {manifest['arm']}"
    doc = f"""{title}{" (DISCARDED, not scored)" if discarded else ""}

Scored against `tests/scenarios.md` as of this commit; cost is `metrics` in the manifest.

## Manifest

```json
{json.dumps(manifest, indent=2)}
```

## Dispatch prompt

```text
{(run / "prompt.txt").read_text(encoding="utf-8").strip()}
```

## Isolation

Flags raised by `tests/eval/isolation.py` (tests/scenarios.md, How to run, step 5):

```text
{flags}
```

{note}

## Score

{table.strip()}

## Final report

{(art / "report.md").read_text(encoding="utf-8").strip()}

## Tool calls

The arm's tool calls, one JSON object per line, extracted from its transcript.

```jsonl
{(art / "tool-calls.jsonl").read_text(encoding="utf-8").rstrip()}
```

## Objective checks

```json
{(art / "objective.json").read_text(encoding="utf-8").strip()}
```

## Diff

```diff
{(art / "diff.patch").read_text(encoding="utf-8").rstrip()}
```

## Repository refs

Every branch and tag in the final repository, each with its changes against the fixture tree (`refs.txt`).

```text
{(art / "refs.txt").read_text(encoding="utf-8").rstrip()}
```
"""
    doc = redact(doc, run)
    suffix = "-discarded" if discarded else ""
    target = (
        out
        / f"{manifest['date']}-{manifest['scenario']}-r{manifest['rep']}-{manifest['arm']}{suffix}.md"
    )
    target.write_text(doc, encoding="utf-8")
    return target


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Assemble a run record.")
    parser.add_argument("run", type=Path)
    parser.add_argument("tasks", type=Path)
    parser.add_argument("out", type=Path)
    parser.add_argument("--note", required=True, help="the isolation adjudication")
    parser.add_argument("--discarded", action="store_true")
    args = parser.parse_args(argv)
    print(assemble(args.run.resolve(), args.tasks.resolve(), args.out, args.note, args.discarded))
    return 0


if __name__ == "__main__":
    sys.exit(main())
