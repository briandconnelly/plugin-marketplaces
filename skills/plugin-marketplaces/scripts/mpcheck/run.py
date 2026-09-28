"""Run the requested checks and build a report."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from mpcheck.checks_local import LOCAL_CHECKS, active_catalogs
from mpcheck.checks_schema import Runner, check_portable, run_claude_validate
from mpcheck.discover import discover
from mpcheck.model import Finding, Severity, Status
from mpcheck.policy import load_policy
from mpcheck.readers import load_readers

GROUPS = (
    "schema.parse",
    "policy",
    "schema.claude-validate",
    "schema.portable",
    "local",
    "remote",
    "discovery",
    "package-load",
)
NOT_IMPLEMENTED = ("remote", "discovery", "package-load")


@dataclass
class Report:
    findings: list[Finding]
    statuses: dict[str, tuple[Status, str]]

    def exit_code(self, fail_on: Severity) -> int:
        failing = (
            {Severity.ERROR} if fail_on == Severity.ERROR else {Severity.ERROR, Severity.WARNING}
        )
        return 1 if any(f.severity in failing for f in self.findings) else 0


def run_checks(
    root: Path,
    policy_path: Path | None = None,
    use_claude: bool = True,
    runner: Runner | None = None,
) -> Report:
    readers = load_readers()
    repo, findings = discover(root, readers)
    policy, policy_findings = load_policy(repo.root, policy_path, readers, repo.reader_catalog)
    findings += policy_findings
    for check in LOCAL_CHECKS:
        findings += check(repo, readers, policy)
    portable_findings, portable_counts = check_portable(repo)
    findings += portable_findings
    if use_claude:
        claude_findings, claude_status, claude_note = (
            run_claude_validate(repo, runner) if runner else run_claude_validate(repo)
        )
        findings += claude_findings
    else:
        claude_status, claude_note = Status.SKIPPED, "disabled with --no-claude"

    def failed(group: str) -> bool:
        return any(f.group == group and f.severity == Severity.ERROR for f in findings)

    statuses: dict[str, tuple[Status, str]] = {
        group: (Status.FAILED if failed(group) else Status.PASSED, "") for group in GROUPS
    }
    statuses["schema.claude-validate"] = (claude_status, claude_note)
    if portable_counts.manifests == 0:
        statuses["schema.portable"] = (Status.SKIPPED, "no portable manifests")
    else:
        statuses["schema.portable"] = (statuses["schema.portable"][0], portable_counts.note())
    if not failed("local") and not active_catalogs(repo, policy):
        statuses["local"] = (Status.SKIPPED, "no catalog is read by a declared reader")
    for group in NOT_IMPLEMENTED:
        statuses[group] = (Status.SKIPPED, "not implemented in this version")
    return Report(findings, statuses)
