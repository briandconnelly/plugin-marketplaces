"""The weekly Action's issue step: silent only when both reports exist and show no change."""

from __future__ import annotations

import json
from pathlib import Path

import drift_issue as di
import pytest

CLEAN_UPSTREAM = [{"id": "p", "status": "same"}]
CLEAN_CONFORMANCE = {
    "probes": [{"id": "x", "status": "held"}],
    "help": [{"command": "codex plugin --help", "status": "same"}],
}


class FakeGh:
    def __init__(self, open_issue: str = "") -> None:
        self.calls: list[list[str]] = []
        self.open_issue = open_issue

    def __call__(self, args):
        self.calls.append(list(args))
        if args[:2] == ["issue", "list"]:
            return self.open_issue + "\n"
        if args[:2] == ["issue", "create"]:
            return "https://github.com/o/r/issues/9\n"
        return ""


def reports(tmp_path: Path, upstream: object | None, conformance: object | None) -> list[str]:
    paths = {}
    for name, data in (("upstream", upstream), ("conformance", conformance)):
        paths[name] = tmp_path / f"{name}.json"
        if data is not None:
            paths[name].write_text(json.dumps(data), encoding="utf-8")
        (tmp_path / f"{name}.md").write_text(f"## {name} report\n", encoding="utf-8")
    return [
        "--upstream", str(paths["upstream"]), "--upstream-md", str(tmp_path / "upstream.md"),
        "--conformance", str(paths["conformance"]), "--conformance-md", str(tmp_path / "conformance.md"),
    ]  # fmt: skip


def test_nothing_changed_touches_no_issue(tmp_path):
    gh = FakeGh()
    assert di.main(reports(tmp_path, CLEAN_UPSTREAM, CLEAN_CONFORMANCE), gh) == 0
    assert gh.calls == []


@pytest.mark.parametrize(
    ("upstream", "conformance", "expected"),
    [
        (None, CLEAN_CONFORMANCE, "the upstream check produced no report"),
        (CLEAN_UPSTREAM, None, "the conformance probes produced no report"),
        ([{"id": "p", "status": "changed"}], CLEAN_CONFORMANCE, "pin `p` changed"),
        ([{"id": "p", "status": "unverified"}], CLEAN_CONFORMANCE, "pin `p` unverified"),
        ([{"id": "p", "status": "error"}], CLEAN_CONFORMANCE, "pin `p` error"),
        (CLEAN_UPSTREAM, {**CLEAN_CONFORMANCE, "probes": [{"id": "x", "status": "flipped"}]}, "probe `x` flipped"),
        (CLEAN_UPSTREAM, {**CLEAN_CONFORMANCE, "probes": [{"id": "x", "status": "skipped"}]}, "probe `x` skipped"),
        (CLEAN_UPSTREAM, {**CLEAN_CONFORMANCE, "help": [{"command": "c", "status": "changed"}]}, "help `c` changed"),
    ],
)  # fmt: skip
def test_each_kind_of_change_opens_an_issue(tmp_path, upstream, conformance, expected):
    gh = FakeGh()
    assert di.main(reports(tmp_path, upstream, conformance), gh) == 0
    create = next(c for c in gh.calls if c[:2] == ["issue", "create"])
    text = create[create.index("--body") + 1]
    assert f"- {expected}" in text
    assert "## upstream report" in text and "## conformance report" in text
    assert gh.calls[1][:3] == ["label", "create", di.LABEL]


def test_a_new_release_alone_touches_no_issue(tmp_path):
    gh = FakeGh()
    upstream = [{"id": "npm-codex", "status": "released"}]
    assert di.main(reports(tmp_path, upstream, CLEAN_CONFORMANCE), gh) == 0
    assert gh.calls == []


def test_an_open_issue_is_updated_not_duplicated(tmp_path):
    gh = FakeGh(open_issue="7")
    di.main(reports(tmp_path, [{"id": "p", "status": "changed"}], CLEAN_CONFORMANCE), gh)
    verbs = [c[:3] for c in gh.calls]
    assert ["issue", "edit", "7"] in verbs and ["issue", "comment", "7"] in verbs
    assert not any(c[:2] == ["issue", "create"] for c in gh.calls)


def test_dry_run_prints_and_calls_nothing(tmp_path, capsys):
    gh = FakeGh()
    args = reports(tmp_path, None, CLEAN_CONFORMANCE) + ["--dry-run", "--run-url", "https://run"]
    assert di.main(args, gh) == 0
    assert gh.calls == [] and "Run: https://run" in capsys.readouterr().out


def test_a_long_body_stays_under_githubs_limit(tmp_path):
    # GitHub rejects an issue body over 65,536 characters; a large doc diff must not
    # make the issue step fail and leave the drift unreported
    gh = FakeGh()
    args = reports(tmp_path, [{"id": "p", "status": "changed"}], CLEAN_CONFORMANCE)
    (tmp_path / "upstream.md").write_text("x" * 200_000, encoding="utf-8")
    di.main(args, gh)
    create = next(c for c in gh.calls if c[:2] == ["issue", "create"])
    text = create[create.index("--body") + 1]
    assert len(text) <= 65_536 and "truncated" in text
