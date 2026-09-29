"""The upstream drift detector against a fake upstream (spec §10: a "no change" result is
known to be able to fail), and the link between pins and the references' evidence rows."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import check_upstream as cu
import pytest

ROOT = Path(__file__).resolve().parents[1]
REFS = ROOT / "skills" / "plugin-marketplaces" / "references"
ROW = re.compile(r"^\| (E\d+) \| (.+) \| (docs|source|probe|run) \|$", re.M)
API = cu.API


class FakeUpstream:
    """A dict of URL -> body; a missing URL raises like a failed fetch."""

    def __init__(self, pages: dict[str, str]) -> None:
        self.pages = pages

    def __call__(self, url: str) -> str:
        if url not in self.pages:
            raise OSError(f"HTTP Error 404: {url}")
        return self.pages[url]


def doc_pin(text: str | None, **extra: Any) -> dict[str, Any]:
    return {
        "id": "d",
        "kind": "doc",
        "url": "https://docs.example/p.md",
        "sha256": None if text is None else cu.sha256(text),
        "affects": ["codex.md#E1"],
        **extra,
    }


def file_pin(blob: str) -> dict[str, Any]:
    return {
        "id": "f",
        "kind": "github-file",
        "repo": "o/r",
        "path": "src/a.rs",
        "pinned_at": "abc",
        "blob": blob,
        "compare": "latest-release",
        "affects": ["codex.md#E2"],
    }


RELEASE = {
    f"{API}/repos/o/r/releases/latest": '{"tag_name": "v2"}',
    f"{API}/repos/o/r/contents/src/a.rs?ref=v2": '{"sha": "b2"}',
}


@pytest.mark.parametrize(
    ("pin", "pages", "status"),
    [
        (doc_pin("A\n"), {"https://docs.example/p.md": "A\n"}, "same"),
        (doc_pin("A\n"), {"https://docs.example/p.md": "B\n"}, "changed"),
        (doc_pin(None), {"https://docs.example/p.md": "A\n"}, "unverified"),
        (doc_pin("A\n"), {}, "error"),
        (file_pin("b2"), RELEASE, "same"),
        (file_pin("b1"), RELEASE, "changed"),
        (file_pin("b1"), {}, "error"),
    ],
)
def test_each_pin_kind_reports_same_changed_and_error(pin, pages, status):
    assert cu.check_pin(pin, FakeUpstream(pages)).status == status


def test_a_changed_doc_carries_a_diff(tmp_path, monkeypatch):
    monkeypatch.setattr(cu, "SNAPSHOTS", tmp_path)
    (tmp_path / "d.txt").write_text("line one\nline two\n", encoding="utf-8")
    pin = doc_pin("line one\nline two\n")
    result = cu.check_pin(pin, FakeUpstream({"https://docs.example/p.md": "line one\nline 2\n"}))
    assert result.status == "changed"
    assert "-line two" in result.detail and "+line 2" in result.detail


def test_a_section_pin_ignores_changes_outside_its_section():
    page = "# T\n\n## Other\nx\n\n## Plugins\nkeep\n### Sub\nkeep too\n\n## After\ny\n"
    pin = doc_pin(cu.section(page, "## Plugins"), section="## Plugins")
    elsewhere = page.replace("x\n", "x changed\n").replace("y\n", "y changed\n")
    inside = page.replace("keep too", "edited")
    assert cu.check_pin(pin, FakeUpstream({pin["url"]: elsewhere})).status == "same"
    assert cu.check_pin(pin, FakeUpstream({pin["url"]: inside})).status == "changed"
    assert cu.check_pin(pin, FakeUpstream({pin["url"]: "# T\n"})).status == "error"


def test_section_stops_at_a_heading_of_the_same_level():
    text = "## A\n1\n### B\n2\n## C\n3\n"
    assert cu.section(text, "## A") == "## A\n1\n### B\n2\n"
    with pytest.raises(ValueError):
        cu.section(text + "## A\n", "## A")


def test_directory_and_npm_pins():
    listing = json.dumps([{"name": "1.0.0.md"}, {"name": "1.1.0.md"}, {"name": "1.2.0.md"}])
    pages = {
        f"{API}/repos/o/r": '{"default_branch": "main"}',
        f"{API}/repos/o/r/contents/spec?ref=main": listing,
        "https://registry.npmjs.org/@o/cli/latest": '{"version": "2.0.0"}',
    }
    base = {"repo": "o/r", "path": "spec", "compare": "default-branch", "affects": []}
    dir_pin = {"id": "s", "kind": "github-dir", "entries": ["1.0.0.md", "1.1.0.md"], **base}
    changed = cu.check_pin(dir_pin, FakeUpstream(pages))
    assert changed.status == "changed" and "1.2.0.md" in changed.detail
    dir_pin["entries"].append("1.2.0.md")
    assert cu.check_pin(dir_pin, FakeUpstream(pages)).status == "same"
    npm = {"id": "n", "kind": "npm", "package": "@o/cli", "version": "1.9.0", "affects": []}
    assert cu.check_pin(npm, FakeUpstream(pages)).status == "released"
    npm["version"] = "2.0.0"
    assert cu.check_pin(npm, FakeUpstream(pages)).status == "same"


def test_main_exits_nonzero_on_any_change_or_error(tmp_path, monkeypatch):
    pins = tmp_path / "pins.json"
    monkeypatch.setattr(cu, "PINS", pins)
    pins.write_text(json.dumps({"pins": [doc_pin("A\n")]}), encoding="utf-8")
    out = tmp_path / "out.md"
    assert (
        cu.main(["--markdown", str(out)], FakeUpstream({"https://docs.example/p.md": "A\n"})) == 0
    )
    assert "0 changed or failed" in out.read_text(encoding="utf-8")
    npm = {"id": "n", "kind": "npm", "package": "@o/cli", "version": "1.0.0", "affects": []}
    pins.write_text(json.dumps({"pins": [doc_pin("A\n"), npm]}), encoding="utf-8")
    released = FakeUpstream(
        {
            "https://docs.example/p.md": "A\n",
            "https://registry.npmjs.org/@o/cli/latest": '{"version": "1.1.0"}',
        }
    )
    assert cu.main(["--markdown", str(out)], released) == 0, "a release alone is not a finding"
    assert "n 1.0.0 → 1.1.0" in out.read_text(encoding="utf-8")
    assert cu.main(["--markdown", str(out)], FakeUpstream({})) == 1
    assert "`d` error" in out.read_text(encoding="utf-8")


def test_repin_refuses_without_evidence_naming_the_pin_and_its_content(tmp_path, monkeypatch):
    monkeypatch.setattr(cu, "ROOT", tmp_path)
    monkeypatch.setattr(cu, "PINS", tmp_path / "pins.json")
    monkeypatch.setattr(cu, "SNAPSHOTS", tmp_path / "snaps")
    (tmp_path / "pins.json").write_text(json.dumps({"pins": [doc_pin(None)]}), encoding="utf-8")
    research = tmp_path / "docs" / "research"
    research.mkdir(parents=True)
    fetch = FakeUpstream({"https://docs.example/p.md": "A\n"})
    assert cu.repin(["d"], "docs/research/missing.md", fetch) == 2
    (research / "r.md").write_text("re-verified nothing\n", encoding="utf-8")
    assert cu.repin(["d"], "docs/research/r.md", fetch) == 2
    (research / "r.md").write_text("re-verified `d` against the page\n", encoding="utf-8")
    assert cu.repin(["d"], "docs/research/r.md", fetch) == 2, "the record must name the content"
    assert not (tmp_path / "snaps").exists(), "a refused repin writes nothing"
    digest = cu.sha256("A\n")
    (research / "r.md").write_text(f"re-verified `d`, sha256 {digest}\n", encoding="utf-8")
    assert cu.repin(["d"], "docs/research/r.md", fetch, today="2026-10-01") == 0
    pin = json.loads((tmp_path / "pins.json").read_text(encoding="utf-8"))["pins"][0]
    assert pin["sha256"] == cu.sha256("A\n") and pin["verified"] == "2026-10-01"
    assert (tmp_path / "snaps" / "d.txt").read_text(encoding="utf-8") == "A\n"
    assert cu.check_pin(pin, fetch).status == "same"


# ---- the real pins file


def test_lines_lists_every_citing_line_of_every_affected_row():
    pin = {"affects": ["codex.md#E7", "releases.md#verified"]}
    lines = cu.affected_lines(pin)
    codex = (REFS / "codex.md").read_text(encoding="utf-8").split("\n## Provenance\n")[0]
    expected = sum("[E7]" in line for line in codex.splitlines())
    assert expected and sum(x.startswith("codex.md:") for x in lines) == expected
    assert any(x.startswith("releases.md: Verified against: ") for x in lines)
    assert not any("[E17]" in x for x in lines), "E1 must not match E17"


@pytest.mark.parametrize("pin_id", [p["id"] for p in json.loads(cu.PINS.read_text())["pins"]])
def test_every_pin_has_lines_to_reverify(pin_id):
    pin = next(p for p in pins_file()["pins"] if p["id"] == pin_id)
    assert cu.affected_lines(pin), pin_id


def pins_file() -> dict:
    return json.loads(cu.PINS.read_text(encoding="utf-8"))


def evidence_rows() -> dict[str, str]:
    rows = {}
    for path in REFS.glob("*.md"):
        prov = path.read_text(encoding="utf-8").split("\n## Provenance\n")[1]
        for eid, _, kind in ROW.findall(prov):
            rows[f"{path.name}#{eid}"] = kind
    return rows


def test_pin_ids_are_unique_and_kinds_known():
    pins = pins_file()["pins"]
    assert len({p["id"] for p in pins}) == len(pins)
    assert {p["kind"] for p in pins} <= {"doc", "github-file", "github-dir", "npm"}


def test_every_pin_affects_a_real_row_or_verified_line():
    rows = evidence_rows()
    for pin in pins_file()["pins"]:
        assert pin["affects"], pin["id"]
        for target in pin["affects"]:
            ref, anchor = target.split("#")
            if anchor == "verified":
                text = (REFS / ref).read_text(encoding="utf-8")
                assert re.search(r"^Verified against: ", text, re.M), target
            else:
                assert target in rows, f"{pin['id']}: {target}"


def test_every_docs_or_source_row_has_a_pin_or_a_recorded_reason():
    data = pins_file()
    covered = {t for p in data["pins"] for t in p["affects"]}
    upstream = {r for r, kind in evidence_rows().items() if kind in ("docs", "source")}
    missing = upstream - covered - set(data["local_rows"])
    assert missing == set()
    assert set(data["local_rows"]) <= upstream, "a local_rows entry is not a docs or source row"


def test_npm_pins_cover_every_reference_that_names_a_tool_version():
    data = pins_file()
    covered = {t for p in data["pins"] if p["kind"] == "npm" for t in p["affects"]}
    for path in REFS.glob("*.md"):
        verified = re.search(r"^Verified against: (.+)$", path.read_text(encoding="utf-8"), re.M)
        if verified and re.search(r"\b(claude|codex-cli|copilot) \d", verified.group(1)):
            assert f"{path.name}#verified" in covered, path.name


def test_pinned_snapshots_match_their_hashes():
    for pin in pins_file()["pins"]:
        if pin["kind"] != "doc" or pin["sha256"] is None:
            continue
        snap = ROOT / pin["snapshot"] if pin.get("snapshot") else cu.snapshot_path(pin["id"])
        assert cu.sha256(snap.read_text(encoding="utf-8")) == pin["sha256"], pin["id"]
        assert pin["verified"] and (ROOT / pin["evidence"]).is_file(), pin["id"]


@pytest.mark.live
def test_the_live_upstream_can_be_read():
    results = cu.check(pins_file()["pins"], cu.http_fetch)
    assert [r.id for r in results if r.status == "error"] == []


@pytest.mark.parametrize(
    ("pinned", "latest", "status"),
    [
        ("1.9.0", "1.10.0", "released"),  # numeric, not string, order
        ("1.10.0", "1.9.0", "changed"),  # a dist-tag moved backward
        ("2.1.0", "2.0.0", "changed"),
        ("2.0.0", "2.0.0-beta.1", "changed"),  # not a plain forward release
        ("2.0.0", "not-a-version", "changed"),
    ],
)
def test_only_a_strictly_newer_npm_release_is_quiet(pinned, latest, status):
    # Copilot review of PR #5: a rollback of `latest` is drift, not a harmless release
    pages = {"https://registry.npmjs.org/@o/cli/latest": json.dumps({"version": latest})}
    pin = {"id": "n", "kind": "npm", "package": "@o/cli", "version": pinned, "affects": []}
    assert cu.check_pin(pin, FakeUpstream(pages)).status == status
