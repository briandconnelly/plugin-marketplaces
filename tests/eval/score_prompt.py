"""Write RUN/score-prompt.txt: the scorer's instructions, with criteria copied verbatim.

Usage: uv run python tests/eval/score_prompt.py RUNS/sN-rK
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from scenario_doc import DOC, ROOT, scenario, scoring


def score_prompt(run: Path) -> str:
    manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
    doc = DOC.read_text(encoding="utf-8")
    item = scenario(doc, int(manifest["scenario"].removeprefix("s")))
    art = run / "artefacts"
    fixture = ROOT / "tests" / "fixtures" / "scenarios" / manifest["scenario"] / "repo"
    task = "\n".join(f"> {line}" for line in item.prompt.splitlines())
    return f"""You are scoring one run of an AI agent on a task. Score it strictly against the criteria below; do not reward effort, and do not infer intent the evidence does not show.
Read-only: do not modify any file, and do not run the claude, codex, or copilot CLIs yourself; the objective tool results are already recorded.

The agent was given this task (placeholders WORKDIR/UPSTREAM were filled with its own directories):

{task}

{scoring(doc)}

{item.criteria}

Evidence (read these files):
- Original repository before the run: {fixture}
- The agent's final repository state: {run / "repo"} (its changes are in the diff below)
- Diff of the agent's changes: {art / "diff.patch"}
- Real-tool objective checks run on the final state: {art / "objective.json"}
- The agent's tool calls, one JSON object per line: {art / "tool-calls.jsonl"}
- The agent's final report to the user: {art / "report.md"}

Return only a Markdown table with columns: Criterion (its number), Result (pass or fail), Evidence (one line, pointing at a file and what it shows). Then one line: "Total: N of M passed."
"""


if __name__ == "__main__":
    run = Path(sys.argv[1]).resolve()
    (run / "score-prompt.txt").write_text(score_prompt(run), encoding="utf-8")
    print(run / "score-prompt.txt")
