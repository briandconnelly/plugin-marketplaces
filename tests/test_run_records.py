"""Committed run records must carry applicable patches, so baseline and treatment runs compare."""

import re
from pathlib import Path

from records import load, manifest

RUNS = Path(__file__).resolve().parent / "runs"


def check_record(record: Path) -> None:
    text = load(record)
    body = text.split("## Diff\n", 1)[1]
    diff = re.search(r"```diff\n(.*?)```", body, re.S)
    assert diff is not None, record.name
    if diff.group(1).strip():
        assert diff.group(1).startswith("diff --git "), f"{record.name}: not a unified diff"
        assert re.search(r"^@@ ", diff.group(1), re.M), f"{record.name}: no hunks"
    assert manifest(text)["model"].startswith("claude-"), f"{record.name}: model not recorded"
    assert "## Tool calls\n" in text, f"{record.name}: tool calls missing"


def test_every_record_has_a_unified_diff_a_model_and_its_tool_calls():
    records = sorted(RUNS.rglob("*-s*-baseline*.md"))
    assert records, "no run records found; the glob is broken"
    for record in records:
        check_record(record)


def test_every_run_a_summary_cites_has_a_record():
    summaries = sorted(RUNS.glob("*-baseline-summary*.md"))
    assert summaries, "no summaries found; the glob is broken"
    for summary in summaries:
        date = summary.name[:10]
        cited = set(re.findall(r"^\| (s\d(?:-(?:rep|r)\d+)?) \|", load(summary), re.M))
        assert cited, f"{summary.name}: no runs in the table; the pattern is broken"
        for run in sorted(cited):
            assert list(RUNS.glob(f"{date}-{run}-baseline*.md")), f"{summary.name} cites {run}"
