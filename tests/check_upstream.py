"""Report upstream documents, source files, and releases that changed since they were pinned.

    uv run python tests/check_upstream.py [--json OUT] [--markdown OUT]
    uv run python tests/check_upstream.py lines ID [ID ...]
    uv run python tests/check_upstream.py repin ID [ID ...] --evidence docs/research/<file>.md

Each pin in `tests/upstream-pins.json` names what the skill's references read upstream and
which evidence rows depend on it (spec §9). A check needs network access and nothing else:
no model and no tool CLIs. A fetch that fails is reported as `error`, never as unchanged.
`lines` prints every reference line that cites an evidence row a pin affects: the facts to
re-verify when that pin changes.
`repin` records the current upstream state for pins whose facts were re-verified; it refuses
unless the evidence file exists under `docs/research/` and names every pin it re-pins and the
exact value it would pin (a doc's sha256, a file's blob, a version, a directory's entries).
An npm pin whose package has a newer version reports `released`: listed, but not a finding.
Exit 0 when every pin is unchanged or only released, 1 when any changed or errored, 2 on bad usage.
"""

from __future__ import annotations

import argparse
import datetime
import difflib
import hashlib
import json
import os
import re
import sys
import urllib.request
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REFS = ROOT / "skills" / "plugin-marketplaces" / "references"
PINS = ROOT / "tests" / "upstream-pins.json"
SNAPSHOTS = ROOT / "tests" / "upstream-snapshots"
API = "https://api.github.com"
USER_AGENT = "plugin-marketplaces-upstream-check"
DIFF_LINES = 60
# a newer release alone invalidates no fact; it is listed, but is not a finding (R13 covers it)
QUIET = {"same", "released"}

Fetch = Callable[[str], str]


def http_fetch(url: str) -> str:
    headers = {"User-Agent": USER_AGENT}
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if url.startswith(API):
        headers["Accept"] = "application/vnd.github+json"
        if token:
            headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8")


@dataclass(frozen=True)
class PinResult:
    id: str
    kind: str
    status: str  # same, changed, unverified, error; released (npm, informational)
    pinned: str
    current: str
    affects: list[str]
    detail: str


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def section(text: str, heading: str) -> str:
    """The Markdown section headed exactly ``heading``, up to the next heading of its level
    or higher; raises ValueError when the heading is absent or repeated."""
    lines = text.splitlines(keepends=True)
    starts = [i for i, line in enumerate(lines) if line.rstrip("\n") == heading]
    if len(starts) != 1:
        raise ValueError(f"heading {heading!r} found {len(starts)} times")
    level = len(heading) - len(heading.lstrip("#"))
    end = len(lines)
    for i in range(starts[0] + 1, len(lines)):
        match = re.match(r"^(#+) ", lines[i])
        if match and len(match.group(1)) <= level:
            end = i
            break
    return "".join(lines[starts[0] : end])


def doc_text(pin: dict[str, Any], fetch: Fetch) -> str:
    text = fetch(pin["url"])
    return section(text, pin["section"]) if pin.get("section") else text


def resolve_ref(repo: str, compare: str, fetch: Fetch) -> str:
    if compare == "latest-release":
        return json.loads(fetch(f"{API}/repos/{repo}/releases/latest"))["tag_name"]
    if compare == "default-branch":
        return json.loads(fetch(f"{API}/repos/{repo}"))["default_branch"]
    raise ValueError(f"unknown compare target {compare!r}")


def commit_of(repo: str, ref: str, fetch: Fetch) -> str:
    return json.loads(fetch(f"{API}/repos/{repo}/commits/{ref}"))["sha"]


def blob_at(repo: str, path: str, ref: str, fetch: Fetch) -> str:
    return json.loads(fetch(f"{API}/repos/{repo}/contents/{path}?ref={ref}"))["sha"]


def entries_at(repo: str, path: str, ref: str, fetch: Fetch) -> list[str]:
    return sorted(
        e["name"] for e in json.loads(fetch(f"{API}/repos/{repo}/contents/{path}?ref={ref}"))
    )


def npm_latest(package: str, fetch: Fetch) -> str:
    return json.loads(fetch(f"https://registry.npmjs.org/{package}/latest"))["version"]


def snapshot_path(pin_id: str) -> Path:
    return SNAPSHOTS / f"{pin_id}.txt"


def check_pin(pin: dict[str, Any], fetch: Fetch) -> PinResult:
    kind = pin["kind"]

    def result(status: str, pinned: str, current: str, detail: str = "") -> PinResult:
        return PinResult(pin["id"], kind, status, pinned, current, pin["affects"], detail)

    try:
        if kind == "doc":
            text = doc_text(pin, fetch)
            now = sha256(text)
            if pin["sha256"] is None:
                return result("unverified", "", now, "no verified pin yet: re-verify, then repin")
            if now == pin["sha256"]:
                return result("same", pin["sha256"], now)
            snap = ROOT / pin["snapshot"] if pin.get("snapshot") else snapshot_path(pin["id"])
            before = snap.read_text(encoding="utf-8") if snap.exists() else ""
            diff = list(
                difflib.unified_diff(
                    before.splitlines(), text.splitlines(), "pinned", "current", lineterm="", n=1
                )
            )
            more = f"\n… {len(diff) - DIFF_LINES} more diff lines" if len(diff) > DIFF_LINES else ""
            return result("changed", pin["sha256"], now, "\n".join(diff[:DIFF_LINES]) + more)
        if kind == "github-file":
            ref = resolve_ref(pin["repo"], pin["compare"], fetch)
            now = blob_at(pin["repo"], pin["path"], ref, fetch)
            if now == pin["blob"]:
                return result("same", pin["blob"], now)
            url = f"https://github.com/{pin['repo']}/compare/{pin['pinned_at']}...{ref}"
            return result("changed", pin["blob"], now, f"`{pin['path']}` differs at {ref}: {url}")
        if kind == "github-dir":
            ref = resolve_ref(pin["repo"], pin["compare"], fetch)
            now_entries = entries_at(pin["repo"], pin["path"], ref, fetch)
            pinned, now = ", ".join(pin["entries"]), ", ".join(now_entries)
            if now_entries == sorted(pin["entries"]):
                return result("same", pinned, now)
            added = sorted(set(now_entries) - set(pin["entries"]))
            removed = sorted(set(pin["entries"]) - set(now_entries))
            return result("changed", pinned, now, f"added {added}, removed {removed} at {ref}")
        if kind == "npm":
            now = npm_latest(pin["package"], fetch)
            if now == pin["version"]:
                return result("same", pin["version"], now)
            return result("released", pin["version"], now, f"{pin['package']} {now} is published")
        return result("error", "", "", f"unknown pin kind {kind!r}")
    except Exception as exc:  # any failure to observe upstream is reported, never "same"
        return result("error", "", "", f"{type(exc).__name__}: {exc}")


def check(pins: list[dict[str, Any]], fetch: Fetch) -> list[PinResult]:
    return [check_pin(pin, fetch) for pin in pins]


def markdown(results: list[PinResult]) -> str:
    changed = [r for r in results if r.status not in QUIET]
    released = [r for r in results if r.status == "released"]
    lines = ["## Upstream pins", ""]
    lines.append(f"{len(results)} pins checked; {len(changed)} changed or failed.")
    if released:
        newer = ", ".join(f"{r.id} {r.pinned} → {r.current}" for r in released)
        lines.append(f"Newer releases than the references were verified against: {newer}.")
    for r in changed:
        lines += ["", f"### `{r.id}` {r.status}", ""]
        if r.status == "changed":
            lines.append(f"Pinned `{r.pinned[:40]}`, now `{r.current[:40]}`.")
        lines.append("Affects: " + ", ".join(f"`{a}`" for a in r.affects) + ".")
        if r.detail:
            if r.kind == "doc" and r.status == "changed":
                lines += ["", "```diff", r.detail, "```"]
            else:
                lines += ["", r.detail]
    return "\n".join(lines) + "\n"


def load() -> dict[str, Any]:
    return json.loads(PINS.read_text(encoding="utf-8"))


def repin(ids: list[str], evidence: str, fetch: Fetch, today: str | None = None) -> int:
    path = ROOT / evidence
    if not (evidence.startswith("docs/research/") and path.is_file()):
        print(f"--evidence must name an existing file under docs/research/: {evidence}")
        return 2
    record = path.read_text(encoding="utf-8")
    unnamed = [i for i in ids if f"`{i}`" not in record]
    if unnamed:
        print(f"{evidence} does not name these pins (as `id`): {unnamed}")
        return 2
    data = load()
    by_id = {p["id"]: p for p in data["pins"]}
    unknown = sorted(set(ids) - set(by_id))
    if unknown:
        print(f"unknown pin ids: {unknown}")
        return 2
    # observe everything first; write nothing unless the record names every new value
    updates: dict[str, dict[str, Any]] = {}
    texts: dict[str, str] = {}
    for pin_id in ids:
        pin = by_id[pin_id]
        if pin["kind"] == "doc":
            texts[pin_id] = doc_text(pin, fetch)
            updates[pin_id] = {"sha256": sha256(texts[pin_id])}
            named = [updates[pin_id]["sha256"]]
        elif pin["kind"] == "github-file":
            ref = resolve_ref(pin["repo"], pin["compare"], fetch)
            at = commit_of(pin["repo"], ref, fetch)
            updates[pin_id] = {
                "pinned_at": at,
                "blob": blob_at(pin["repo"], pin["path"], at, fetch),
            }
            named = [updates[pin_id]["blob"]]
        elif pin["kind"] == "github-dir":
            ref = resolve_ref(pin["repo"], pin["compare"], fetch)
            updates[pin_id] = {"entries": entries_at(pin["repo"], pin["path"], ref, fetch)}
            named = updates[pin_id]["entries"]
        else:
            updates[pin_id] = {"version": npm_latest(pin["package"], fetch)}
            named = [updates[pin_id]["version"]]
        missing = [value for value in named if value not in record]
        if missing:
            print(f"{evidence} does not name what `{pin_id}` would pin now: {missing}")
            print("re-verify the current upstream content and record it before re-pinning")
            return 2
    for pin_id, update in updates.items():
        pin = by_id[pin_id]
        if pin_id in texts:
            snap = ROOT / pin["snapshot"] if pin.get("snapshot") else snapshot_path(pin_id)
            snap.parent.mkdir(parents=True, exist_ok=True)
            snap.write_text(texts[pin_id], encoding="utf-8")
        pin.update(update)
        pin["verified"] = today or datetime.date.today().isoformat()
        pin["evidence"] = evidence
    PINS.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"re-pinned {len(ids)} pins; evidence: {evidence}")
    return 0


def affected_lines(pin: dict[str, Any]) -> list[str]:
    """``ref:line: text`` for each reference line citing an evidence row the pin affects, and
    each ``Verified against:`` line for a ``ref#verified`` target."""
    found = []
    for target in pin["affects"]:
        ref, anchor = target.split("#")
        text = (REFS / ref).read_text(encoding="utf-8")
        if anchor == "verified":
            found += [
                f"{ref}: {x}" for x in text.splitlines() if x.startswith("Verified against: ")
            ]
            continue
        body = text.split("\n## Provenance\n")[0]
        for number, line in enumerate(body.splitlines(), start=1):
            if re.search(rf"\[{anchor}\]", line):
                found.append(f"{ref}:{number}: {line.strip()}")
    return found


def main(argv: list[str] | None = None, fetch: Fetch = http_fetch) -> int:
    args = sys.argv[1:] if argv is None else argv
    if args[:1] == ["lines"]:
        by_id = {p["id"]: p for p in load()["pins"]}
        unknown = [i for i in args[1:] if i not in by_id]
        if unknown or len(args) < 2:
            print(f"usage: check_upstream.py lines ID [ID ...]; unknown: {unknown}")
            return 2
        for pin_id in args[1:]:
            print(f"## {pin_id}")
            print("\n".join(affected_lines(by_id[pin_id])) or "(no citing lines)")
        return 0
    if args[:1] == ["repin"]:
        parser = argparse.ArgumentParser(prog="check_upstream.py repin")
        parser.add_argument("ids", nargs="+")
        parser.add_argument("--evidence", required=True)
        parsed = parser.parse_args(args[1:])
        return repin(parsed.ids, parsed.evidence, fetch)
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--json", type=Path)
    parser.add_argument("--markdown", type=Path)
    parsed = parser.parse_args(args)
    results = check(load()["pins"], fetch)
    if parsed.json:
        parsed.json.write_text(
            json.dumps([asdict(r) for r in results], indent=2) + "\n", encoding="utf-8"
        )
    text = markdown(results)
    if parsed.markdown:
        parsed.markdown.write_text(text, encoding="utf-8")
    else:
        print(text)
    return 0 if all(r.status in QUIET for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
