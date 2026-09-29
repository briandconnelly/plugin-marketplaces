"""The weekly Action's shape: no token left on disk, and a failure before the checks still
reaches the issue step, which reads a missing report as a finding (plan-3 final review)."""

from __future__ import annotations

from pathlib import Path

import yaml

WORKFLOW = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "upstream-drift.yml"


def steps() -> list[dict]:
    return yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))["jobs"]["drift"]["steps"]


def step(name: str) -> dict:
    return next(s for s in steps() if s.get("name") == name)


def test_checkout_leaves_no_token_in_the_git_config():
    # the probed CLIs and npm install scripts run as the same user and could read it
    checkout = next(s for s in steps() if str(s.get("uses", "")).startswith("actions/checkout"))
    assert checkout.get("with", {}).get("persist-credentials") is False


def test_a_failed_install_or_check_still_reaches_the_issue_step():
    assert step("Install the latest covered tools").get("continue-on-error") is True
    for name in (
        "Check upstream pins",
        "Run the conformance probes",
        "Open or update the drift issue",
    ):
        assert "!cancelled()" in str(step(name).get("if", "")), name


def test_the_probes_cannot_use_up_the_whole_job():
    job = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))["jobs"]["drift"]
    probe = step("Run the conformance probes")
    assert probe.get("timeout-minutes", job["timeout-minutes"]) < job["timeout-minutes"]
