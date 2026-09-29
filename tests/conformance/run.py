"""Run the conformance probes against the installed tools and report stale facts (spec §9).

    uv run python tests/conformance/run.py [--only ID ...] [--json OUT] [--markdown OUT]
    uv run python tests/conformance/run.py --repin-help --evidence docs/research/<file>.md

`--repin-help` pins every tool's help text only when all three tools are installed and the
research record names the sha256 of each text it would pin.

Statuses: `held` (the fact still holds), `flipped` (it no longer does: re-verify the named
reference lines), `broken` (the control failed, so the probe proves nothing), `error` (the
probe crashed or a tool command failed), `skipped` (a tool it needs is not installed).
Help pins compare each tool's `--help` text with the copy under `tests/conformance/help/`.
Exit 0 when nothing flipped, broke, errored, or changed; 1 otherwise; 2 on bad usage.
With --require-tools (the weekly Action), a skipped probe or help pin also exits 1.
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import shutil
import sys
import tempfile
import traceback
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Protocol

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from conformance.probes import PROBES, Observation, Probe  # noqa: E402
from conformance.sandbox import Result, Sandbox  # noqa: E402

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
HELP_DIR = HERE / "help"
HELP_COMMANDS: tuple[tuple[str, ...], ...] = (
    ("claude", "plugin", "--help"),
    ("claude", "plugin", "marketplace", "--help"),
    ("codex", "plugin", "--help"),
    ("codex", "plugin", "marketplace", "--help"),
    ("copilot", "plugin", "--help"),
    ("copilot", "plugin", "marketplace", "--help"),
    ("copilot", "skill", "--help"),
)
VERSION_COMMANDS = {"claude": "claude", "codex": "codex", "copilot": "copilot"}
FAILING = {"flipped", "broken", "error", "changed", "unpinned"}


@dataclass(frozen=True)
class ProbeResult:
    id: str
    status: str
    fact: str
    anchors: list[list[str]]
    detail: str


@dataclass(frozen=True)
class HelpResult:
    command: str
    status: str
    diff: str


def classify(probe: Probe, observe) -> ProbeResult:
    """Run one probe; ``observe`` is ``probe.run`` bound to a fresh work directory."""
    anchors = [list(a) for a in probe.anchors]
    missing = [t for t in probe.tools if shutil.which(t) is None]
    if missing:
        return ProbeResult(probe.id, "skipped", probe.fact, anchors, f"not installed: {missing}")
    try:
        seen: Observation = observe()
    except Exception as exc:  # a crashed probe is reported, never counted as held
        tail = traceback.format_exception_only(exc)[-1].strip()
        return ProbeResult(probe.id, "error", probe.fact, anchors, tail)
    if not seen.control:
        detail = f"control failed ({probe.control}): {seen.detail}"
        return ProbeResult(probe.id, "broken", probe.fact, anchors, detail)
    status = "held" if seen.holds else "flipped"
    return ProbeResult(probe.id, status, probe.fact, anchors, seen.detail)


def scrub(result: ProbeResult, work: Path) -> ProbeResult:
    """Replace the temporary work directory in a result's detail with `$WORK`."""
    detail = result.detail
    for form in sorted({str(work.resolve()), str(work)}, key=len, reverse=True):
        detail = detail.replace(form, "$WORK")
    return replace(result, detail=detail)


def help_file(argv: tuple[str, ...]) -> Path:
    return HELP_DIR / ("-".join(a for a in argv if a != "--help") + ".txt")


class Runs(Protocol):
    def run(self, *argv: str) -> Result: ...


def check_help(argv: tuple[str, ...], sandbox: Runs) -> HelpResult:
    command = " ".join(argv)
    if shutil.which(argv[0]) is None:
        return HelpResult(command, "skipped", "")
    now = sandbox.run(*argv).output
    pinned = help_file(argv)
    if not pinned.exists():
        return HelpResult(command, "unpinned", "")
    before = pinned.read_text(encoding="utf-8")
    if before == now:
        return HelpResult(command, "same", "")
    diff = difflib.unified_diff(
        before.splitlines(), now.splitlines(), "pinned", "installed", lineterm=""
    )
    return HelpResult(command, "changed", "\n".join(diff))


def versions(sandbox: Sandbox) -> dict[str, str]:
    found = {}
    for tool, exe in VERSION_COMMANDS.items():
        if shutil.which(exe):
            found[tool] = sandbox.run(exe, "--version").output.strip().splitlines()[0]
        else:
            found[tool] = "not installed"
    return found


def markdown(report: dict) -> str:
    lines = ["## Conformance probes", ""]
    tools = "; ".join(f"{k} {v.rstrip('.')}" for k, v in report["versions"].items())
    lines.append(f"Tools: {tools}.")
    lines.append(f"Network denied during probes: {report['network_denied']}.")
    lines.append("")
    lines += ["| Probe | Status | Detail |", "| --- | --- | --- |"]
    for r in report["probes"]:
        detail = " ".join(r["detail"].split()).replace("|", "/")[:300]
        lines.append(f"| `{r['id']}` | {r['status']} | {detail} |")
    for r in report["probes"]:
        if r["status"] in FAILING:
            lines += ["", f"### `{r['id']}` {r['status']}", "", f"Fact: {r['fact']}"]
            lines += [
                f"- re-verify `{ref}`: the line containing “{text}”" for ref, text in r["anchors"]
            ]
    changed = [h for h in report["help"] if h["status"] in FAILING]
    if changed:
        lines += ["", "## Help text", ""]
        for h in changed:
            lines += [f"### `{h['command']}` {h['status']}", ""]
            if h["diff"]:
                lines += ["```diff", h["diff"][:4000], "```", ""]
    return "\n".join(lines) + "\n"


def repin_help(evidence: str, work: Path) -> int:
    """Pin each tool's current help text; the record must name each text's sha256."""
    path = ROOT / evidence
    if not (evidence.startswith("docs/research/") and path.is_file()):
        print(f"--evidence must name an existing file under docs/research/: {evidence}")
        return 2
    record = path.read_text(encoding="utf-8")
    sandbox = Sandbox(work / "help")
    texts = {argv: sandbox.run(*argv).output for argv in HELP_COMMANDS if shutil.which(argv[0])}
    missing = [" ".join(a) for a, text in texts.items() if sha256(text) not in record]
    if len(texts) < len(HELP_COMMANDS) or missing:
        print(
            f"not re-pinned: a tool is missing, or {evidence} does not name the sha256 of {missing}"
        )
        return 2
    HELP_DIR.mkdir(exist_ok=True)
    for argv, text in texts.items():
        help_file(argv).write_text(text, encoding="utf-8")
    (HELP_DIR / "EVIDENCE").write_text(evidence + "\n", encoding="utf-8")
    print(f"re-pinned help text; evidence: {evidence}")
    return 0


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--only", nargs="+", metavar="ID")
    parser.add_argument("--json", type=Path)
    parser.add_argument("--markdown", type=Path)
    parser.add_argument("--repin-help", action="store_true")
    parser.add_argument("--evidence")
    parser.add_argument(
        "--require-tools", action="store_true", help="count a skipped probe as a failure (CI)"
    )
    args = parser.parse_args(argv)
    known = {p.id for p in PROBES}
    if args.only and set(args.only) - known:
        parser.error(f"unknown probe ids: {sorted(set(args.only) - known)}")
    with tempfile.TemporaryDirectory(prefix="conformance-") as tmp:
        work = Path(tmp)
        if args.repin_help:
            if not args.evidence:
                parser.error("--repin-help needs --evidence docs/research/<file>.md")
            return repin_help(args.evidence, work)
        sandbox = Sandbox(work / "versions")
        report = {
            "versions": versions(sandbox),
            "network_denied": sandbox.denial is not None,
            "probes": [],
            "help": [],
        }
        for probe in PROBES:
            if args.only and probe.id not in args.only:
                continue
            probe_dir = work / probe.id
            probe_dir.mkdir()
            result = scrub(classify(probe, lambda p=probe, d=probe_dir: p.run(d)), work)
            report["probes"].append(asdict(result))
            print(f"{result.status:8} {probe.id}", file=sys.stderr)
        if not args.only:
            help_box = Sandbox(work / "help")
            report["help"] = [asdict(check_help(a, help_box)) for a in HELP_COMMANDS]
    if args.json:
        args.json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    text = markdown(report)
    if args.markdown:
        args.markdown.write_text(text, encoding="utf-8")
    else:
        print(text)
    failing = FAILING | ({"skipped"} if args.require_tools else set())
    bad = [r for r in report["probes"] + report["help"] if r["status"] in failing]
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
