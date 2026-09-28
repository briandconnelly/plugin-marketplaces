"""Committed run records must carry applicable patches, so baseline and treatment runs compare."""

import json
import re
from pathlib import Path

RUNS = Path(__file__).resolve().parent / "runs"


def test_every_recorded_diff_is_a_unified_diff():
    records = sorted(RUNS.glob("*-s*-baseline*.md"))
    assert records, "no run records found; the glob is broken"
    for record in records:
        body = record.read_text(encoding="utf-8").split("## Diff\n", 1)[1]
        diff = re.search(r"```diff\n(.*?)```", body, re.S)
        assert diff is not None, record.name
        text = diff.group(1)
        if text.strip():
            assert text.startswith("diff --git "), f"{record.name}: not a unified diff"
            assert re.search(r"^@@ ", text, re.M), f"{record.name}: no hunks"


def test_every_record_names_its_model_and_carries_its_tool_calls():
    for record in sorted(RUNS.glob("*-s*-baseline*.md")):
        text = record.read_text(encoding="utf-8")
        block = re.search(r"## Manifest\n\n```json\n(.*?)```", text, re.S)
        assert block is not None, f"{record.name}: manifest missing"
        manifest = json.loads(block.group(1))
        assert manifest["model"].startswith("claude-"), f"{record.name}: model not recorded"
        assert "## Tool calls\n" in text, f"{record.name}: tool calls missing"


def test_every_run_the_summary_cites_has_a_record():
    summary = (RUNS / "2026-09-28-baseline-summary.md").read_text(encoding="utf-8")
    cited = set(re.findall(r"^\| (s\d(?:-rep\d)?) \|", summary, re.M))
    assert cited, "no runs found in the summary table; the pattern is broken"
    for run in sorted(cited):
        matches = list(RUNS.glob(f"2026-09-28-{run}-baseline*.md"))
        assert matches, f"summary cites {run} but no record exists"
