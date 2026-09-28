"""Committed run records must carry applicable patches, so baseline and treatment runs compare."""

import re
from pathlib import Path

RUNS = Path(__file__).resolve().parent / "runs"


def test_every_recorded_diff_is_a_unified_diff():
    records = sorted(RUNS.glob("*-s*-baseline.md"))
    assert records, "no run records found; the glob is broken"
    for record in records:
        body = record.read_text(encoding="utf-8").split("## Diff\n", 1)[1]
        diff = re.search(r"```diff\n(.*?)```", body, re.S)
        assert diff is not None, record.name
        text = diff.group(1)
        if text.strip():
            assert text.startswith("diff --git "), f"{record.name}: not a unified diff"
            assert re.search(r"^@@ ", text, re.M), f"{record.name}: no hunks"
