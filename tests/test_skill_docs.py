"""Consistency of SKILL.md and its references (spec §6, §7, §10 Consistency).

Rules live only in SKILL.md's Rules section; references cite rule ids and evidence ids and
never restate a rule; every fact a reference states cites a row of its own Provenance table.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "plugin-marketplaces"
SKILL = SKILL_DIR / "SKILL.md"
REFS = SKILL_DIR / "references"
READERS = SKILL_DIR / "scripts" / "mpcheck" / "data" / "readers.json"
EXPECTED_REFS = {
    "agent-plugins.md",
    "claude-code.md",
    "codex.md",
    "copilot-cli.md",
    "feature-matrix.md",
    "freshness.md",
    "multi-tool.md",
    "releases.md",
    "validation.md",
}
RULE_DEF = re.compile(r"^- \*\*(R\d+)\*\* ", re.M)
RULE_CITE = re.compile(r"\bR(\d+)\b")
EVIDENCE_ROW = re.compile(r"^\| (E\d+) \| (.+) \| (docs|source|probe|run) \|$", re.M)
EVIDENCE_CITE = re.compile(r"\[(E\d+)\]")
LINK = re.compile(r"\]\(([^)\s]+)\)")
REPO_PATH = re.compile(r"`((?:docs|tests)/[^`\s]+)`")
READER_COLUMNS = {"Claude Code": "claude-code", "Codex": "codex", "Copilot CLI": "copilot-cli"}


def section(text: str, heading: str) -> str:
    start = text.index(f"\n{heading}\n")
    following = re.search(r"^## ", text[start + len(heading) + 2 :], re.M)
    end = start + len(heading) + 2 + following.start() if following else len(text)
    return text[start:end]


def docs() -> list[Path]:
    return [SKILL, *sorted(REFS.glob("*.md"))]


def rules() -> list[str]:
    return RULE_DEF.findall(section(SKILL.read_text(encoding="utf-8"), "## Rules"))


def test_the_references_are_exactly_the_planned_files():
    assert {p.name for p in REFS.glob("*.md")} == EXPECTED_REFS


def test_rules_are_numbered_once_and_in_order():
    assert rules() == [f"R{n}" for n in range(1, 16)]
    whole = SKILL.read_text(encoding="utf-8")
    assert len(RULE_DEF.findall(whole)) == 15, "a rule is defined outside the Rules section"


@pytest.mark.parametrize("path", [p.name for p in docs()])
def test_every_cited_rule_exists(path):
    target = SKILL if path == "SKILL.md" else REFS / path
    defined = set(rules())
    cited = {f"R{n}" for n in RULE_CITE.findall(target.read_text(encoding="utf-8"))}
    assert cited <= defined, sorted(cited - defined)


@pytest.mark.parametrize("name", sorted(EXPECTED_REFS))
def test_references_never_define_a_rule(name):
    assert not RULE_DEF.findall((REFS / name).read_text(encoding="utf-8"))


@pytest.mark.parametrize("name", sorted(EXPECTED_REFS))
def test_every_reference_carries_provenance_and_every_citation_resolves(name):
    text = (REFS / name).read_text(encoding="utf-8")
    prov = section(text, "## Provenance")
    assert re.search(r"^Verified against: .+ on \d{4}-\d{2}-\d{2}\.$", prov, re.M), name
    rows = EVIDENCE_ROW.findall(prov)
    ids = [row[0] for row in rows]
    assert ids == [f"E{n}" for n in range(1, len(ids) + 1)], "ids must run E1, E2, ... once"
    body = text.replace(prov, "")
    cited = set(EVIDENCE_CITE.findall(body))
    assert cited == set(ids), {"uncited": set(ids) - cited, "undefined": cited - set(ids)}


@pytest.mark.parametrize("name", sorted(EXPECTED_REFS))
def test_evidence_paths_exist(name):
    prov = section((REFS / name).read_text(encoding="utf-8"), "## Provenance")
    for _, evidence, _ in EVIDENCE_ROW.findall(prov):
        for path in REPO_PATH.findall(evidence):
            assert (ROOT / path).exists(), f"{name}: {path}"


@pytest.mark.parametrize("path", [p.name for p in docs()])
def test_relative_links_resolve(path):
    target = SKILL if path == "SKILL.md" else REFS / path
    for link in LINK.findall(target.read_text(encoding="utf-8")):
        if re.match(r"^[a-z]+:", link) or link.startswith("#"):
            continue
        assert (target.parent / link.split("#")[0]).exists(), f"{path}: {link}"


def test_the_reference_map_lists_every_reference_once():
    mapped = re.findall(
        r"\(references/([^)]+)\)", section(SKILL.read_text(encoding="utf-8"), "## Reference map")
    )
    assert sorted(mapped) == sorted(EXPECTED_REFS)


def test_the_source_type_table_matches_readers_json():
    readers = json.loads(READERS.read_text(encoding="utf-8"))
    table = section((REFS / "feature-matrix.md").read_text(encoding="utf-8"), "## Source types")
    lines = [line for line in table.splitlines() if line.startswith("|")]
    header = [cell.strip() for cell in lines[0].strip("|").split("|")]
    assert header[0] == "Source type" and set(header[1:]) == set(READER_COLUMNS)
    seen = set()
    for line in lines[2:]:
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        source = cells[0].strip("`")
        seen.add(source)
        for column, cell in zip(header[1:], cells[1:], strict=True):
            accepted = source in readers[READER_COLUMNS[column]]["source_types"]
            verdict = re.match(r"(yes|no)\b", cell)
            assert verdict and verdict.group(1) == ("yes" if accepted else "no"), (
                f"{source} / {column}"
            )
    everything = {s for key, r in readers.items() if key != "$comment" for s in r["source_types"]}
    assert seen == everything


@pytest.mark.parametrize("name", sorted(EXPECTED_REFS - {"freshness.md"}))
def test_every_fact_bullet_cites_evidence(name):
    # a set-level check misses an uncited line whose id is cited elsewhere; check each bullet
    text = (REFS / name).read_text(encoding="utf-8")
    body = text[: text.index("\n## Provenance\n")]
    fence, uncited = False, []
    for number, line in enumerate(body.splitlines(), start=1):
        if line.lstrip().startswith("```"):
            fence = not fence
        elif not fence and line.lstrip().startswith("- ") and not EVIDENCE_CITE.search(line):
            uncited.append(f"{name}:{number}: {line.strip()[:80]}")
    assert uncited == []
