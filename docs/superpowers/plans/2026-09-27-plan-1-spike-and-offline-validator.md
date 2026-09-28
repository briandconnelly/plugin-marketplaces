# Plan 1: Phase-0 Spike and Offline Validator — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.
> Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Decide which of Copilot CLI and VS Code stay in scope (phase 0), then build the repository skeleton and the validator's offline levels (schema and local) with mutation-tested checks, calibrated on two real marketplaces (phase 1).

**Architecture:** `check_marketplace.py` is a PEP 723 `uv run` script whose logic lives in a sibling package `mpcheck/` (Python puts the script's directory on `sys.path`, so the script imports it directly).
Reader facts (catalog paths, accepted source types, name rules) live in one data file, `readers.json`; checks read it rather than hard-coding tool behaviour.
Each check is a function `(Repo, readers, Policy) -> list[Finding]`, tested by a clean fixture that must produce no findings and one mutation per finding id that must produce exactly that id.

**Tech Stack:** Python ≥ 3.12, `jsonschema`, pytest, uv, ruff, ty, prek, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-09-27-plugin-marketplaces-design.md` (read it first; this plan implements its §11 phases 0 and 1, plus the §8 schema and local levels).

Later plans (not this one): SKILL.md and references (phase 2), conformance probes and drift tooling (phase 3), remote and probe levels (phase 4), behavioural scenarios (phase 5), review and publication (phase 6).

## Global Constraints

- Python `>=3.12`; `jsonschema` is the validator's only third-party runtime dependency.
- Use `uv` for everything; never pip; dependencies live in `pyproject.toml`; no `requirements.txt`.
- `ruff` lints and formats; `ty` type-checks.
- Markdown: one sentence per line; `docs/research/` is archived evidence and is never edited or reformatted.
- Conventional commits; every commit message ends with the line `🤖 Generated with Claude Code`.
- Never `git add -A` or `git add .`; add explicit paths.
- The validator never installs into a real tool configuration and never executes plugin code (spec R15).
- A skipped or inconclusive check is reported as such, never as passed (spec R12).
- A tool is covered only if a runnable probe can check it; no reader entry, reference text, or test fixture for Copilot CLI or VS Code is written unless Task 1 records a passing probe for it.
- Do not create a GitHub repository or push anywhere; the owner approves that in a later plan.
- Paths below are relative to the repository root `~/projects/plugin-marketplaces`.

## Review Focus

Inputs the spec implies but its checks do not name, most likely first; each has a test in the owning task.

1. A repository with no catalog at all: the validator must fail with a clear finding, not report every level as passed (Task 5, `test_no_catalog_is_an_error`).
2. A catalog that is valid JSON but the wrong shape (`"plugins": {}`, an entry without `name` or `source`, a non-object entry): findings, not a traceback (Task 5, `test_catalog_shape_errors`).
3. A local source that is a symlink loop or points at a file: a path finding, not a crash (Task 7, `test_symlink_loop_is_reported`, `test_source_pointing_at_file`).
4. A catalog saved with a UTF-8 byte-order mark: a parse finding naming the file, not a crash (Task 5, `test_bom_is_reported`).
5. A parity exception that no longer matches any difference: a warning, so a stale exception cannot silently hide a future difference (Task 9, `test_unused_exception_warns`).

---

### Task 1: Phase-0 feasibility spike (throwaway)

This task produces a decision record, not kept code.
Scratch files live in a `mktemp -d` directory and are deleted at the end.

**Files:**
- Create: `docs/research/2026-09-27-phase0-probes.md` (a new, dated research record; it is written by this task, so the no-edit rule for archived reports applies only after it is committed)
- Modify: `docs/research/README.md` (add one table row for the new record)
- Modify: `docs/research/SHA256SUMS` (regenerate)

- [ ] **Step 1: Snapshot the real Copilot configuration so isolation can be proven afterwards**

```bash
export SPIKE=$(mktemp -d)
find ~/.copilot -type f -exec shasum -a 256 {} + 2>/dev/null | sort > "$SPIKE/copilot-before.txt"
wc -l "$SPIKE/copilot-before.txt"
```

- [ ] **Step 2: Build the fixture marketplace**

It has one plugin that must load, and two controls that Copilot's documented source types say it must not accept.

```bash
mkdir -p "$SPIKE/mkt/.claude-plugin" "$SPIKE/mkt/plugins/alpha/.claude-plugin" "$SPIKE/mkt/plugins/alpha/skills/hello"
cat > "$SPIKE/mkt/.claude-plugin/marketplace.json" <<'EOF'
{
  "name": "spike-mkt",
  "owner": {"name": "Spike"},
  "plugins": [
    {"name": "alpha", "source": "./plugins/alpha", "description": "must load"},
    {"name": "control-npm", "source": {"source": "npm", "package": "left-pad", "version": "1.3.0"}, "description": "npm is not a documented Copilot source type"},
    {"name": "control-bare", "source": "plugins/alpha", "description": "bare path without ./"}
  ]
}
EOF
echo '{"name": "alpha", "version": "0.1.0", "description": "Spike plugin"}' > "$SPIKE/mkt/plugins/alpha/.claude-plugin/plugin.json"
printf -- '---\nname: hello\ndescription: Say hello for the spike.\n---\n\nSay hello.\n' > "$SPIKE/mkt/plugins/alpha/skills/hello/SKILL.md"
```

- [ ] **Step 3: Probe Copilot CLI catalog discovery in an isolated home**

```bash
export COPILOT_HOME="$SPIKE/copilot-home" COPILOT_CACHE_HOME="$SPIKE/copilot-cache"
copilot --version
copilot plugin marketplace add "$SPIKE/mkt"; echo "add exit=$?"
copilot plugin marketplace list
copilot plugin marketplace browse spike-mkt --json | tee "$SPIKE/copilot-browse.json"; echo "browse exit=$?"
ls -R "$COPILOT_HOME" | head -40
```

Record: which entry names `browse` lists; whether either control is absent; whether any files appeared outside `$SPIKE`.

- [ ] **Step 4: Probe Copilot CLI package load in the same isolated home**

```bash
copilot plugin --help
copilot plugin install alpha@spike-mkt; echo "install exit=$?"
copilot plugin list --help
copilot plugin list --json 2>/dev/null || copilot plugin list
```

Record: whether an installed-plugin listing exposes the `hello` skill or any component (package-load observability, spec §8 level 4).
If `install` would run any hook or network step, stop and record that instead of proceeding.

- [ ] **Step 5: Prove the real Copilot configuration was untouched**

```bash
unset COPILOT_HOME COPILOT_CACHE_HOME
find ~/.copilot -type f -exec shasum -a 256 {} + 2>/dev/null | sort > "$SPIKE/copilot-after.txt"
diff "$SPIKE/copilot-before.txt" "$SPIKE/copilot-after.txt" && echo "real config unchanged"
```

Expected: `real config unchanged`.
If the diff is non-empty, the isolation variables do not isolate; record it, and Copilot CLI fails the gate (spec §12, "a probe that cannot be isolated is not written").

- [ ] **Step 6: Find the VS Code 1.139.1 marketplace settings and log lines in source**

The installed app is commit `04c0d99f4fb0d8afe6ce4f0c58e31e183ac3e4b1`.

```bash
C=04c0d99f4fb0d8afe6ce4f0c58e31e183ac3e4b1
F=src/vs/workbench/contrib/chat/common/plugins/pluginMarketplaceService.ts
gh api "repos/microsoft/vscode/contents/$F?ref=$C" --jq .content | base64 -d > "$SPIKE/pms.ts"
grep -nE "chat\.plugins|getValue|logService|\.(trace|debug|info|warn|error)\(" "$SPIKE/pms.ts" | head -60
```

Record: the exact setting key(s) that register a marketplace, and every log call that names an accepted or rejected entry.

- [ ] **Step 7: Attempt an isolated, machine-readable VS Code observation (timebox: 60 minutes)**

```bash
APP="/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code"
mkdir -p "$SPIKE/vsc/ud/User" "$SPIKE/vsc/ext" "$SPIKE/vsc/ws"
# Replace SETTING_KEY with the key found in Step 6; the value format follows the source.
cat > "$SPIKE/vsc/ud/User/settings.json" <<EOF
{ "SETTING_KEY": ["file://$SPIKE/mkt"] }
EOF
"$APP" --user-data-dir "$SPIKE/vsc/ud" --extensions-dir "$SPIKE/vsc/ext" --log trace --new-window "$SPIKE/vsc/ws" &
sleep 45
grep -rniE "marketplace|plugin" "$SPIKE/vsc/ud/logs" | head -60
```

Then close that window.
The gate passes only if a file under `$SPIKE/vsc` (a log or state file) machine-readably shows `alpha` accepted and at least one control rejected or absent.
A result visible only in the UI does not pass.
If the source in Step 6 shows no log line or persisted state that names entries, record that and stop without further attempts.

- [ ] **Step 8: Write the decision record**

Create `docs/research/2026-09-27-phase0-probes.md` with one section per tool, one sentence per line, containing: tool version, exact commands run, the verbatim relevant output (pasted from the files in `$SPIKE`, not retyped), the verdict for each of catalog discovery and package load (`pass`, `fail`, or `unproven`), and the observed behaviour for each control (`accepted`, `rejected`, `absent`).
End with a `## Decision` section listing which of Copilot CLI and VS Code remain in scope under spec §3.1.

Add this row to the table in `docs/research/README.md`:

```markdown
| [2026-09-27-phase0-probes.md](2026-09-27-phase0-probes.md) | Phase-0 gate: headless isolated probes for Copilot CLI and VS Code | copilot and VS Code 1.139.1 on this machine |
```

- [ ] **Step 9: Regenerate checksums, clean up, commit**

```bash
cd docs/research && shasum -a 256 2026-09-27-*.md > SHA256SUMS && shasum -a 256 -c SHA256SUMS && cd ../..
rm -rf "$SPIKE"
git add docs/research/2026-09-27-phase0-probes.md docs/research/README.md docs/research/SHA256SUMS
git commit -m "docs(research): record phase-0 probe results for Copilot CLI and VS Code

🤖 Generated with Claude Code"
```

---

### Task 2: Repository skeleton and tooling

**Files:**
- Create: `pyproject.toml`, `prek.toml`, `.gitignore`, `LICENSE`, `README.md`, `AGENTS.md`, `CLAUDE.md`, `.github/workflows/ci.yml`
- Create: `tools/check_skill_frontmatter.py` (copied), `tools/check_sentence_per_line.py`
- Test: `tests/test_sentence_per_line.py`, `tests/conftest.py`

**Interfaces:**
- Produces: `tools/check_sentence_per_line.py` exposing `violations(text: str) -> list[int]` (1-based line numbers) and `main(argv: list[str]) -> int`.
- Produces: `tests/conftest.py` autouse fixture `_isolate_git_env` that removes `GIT_DIR`, `GIT_INDEX_FILE`, `GIT_WORK_TREE` from the environment for every test.

- [ ] **Step 1: Write `pyproject.toml`**

```toml
[project]
name = "plugin-marketplaces"
version = "0.1.0"
description = "Agent skill for creating and maintaining user-hosted plugin marketplaces"
requires-python = ">=3.12"
license = "MIT"
dependencies = []

[dependency-groups]
dev = ["pytest>=8.3", "jsonschema>=4.23", "pyyaml>=6.0", "ruff", "ty"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["skills/plugin-marketplaces/scripts", "tests", "tools"]

[tool.ruff]
line-length = 100
extend-exclude = ["*.md", "docs/research"]

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "SIM"]
```

`*.md` is excluded because ruff 0.16+ reformats Python blocks inside Markdown, which would corrupt archived evidence.

- [ ] **Step 2: Write `.gitignore`, `LICENSE`, `CLAUDE.md`**

`.gitignore`:

```text
.venv/
__pycache__/
.pytest_cache/
.ruff_cache/
```

`LICENSE`: the standard MIT license text with the line `Copyright (c) 2026 Brian Connelly`.

`CLAUDE.md`:

```markdown
@AGENTS.md
```

- [ ] **Step 3: Write `AGENTS.md`**

```markdown
# Agent instructions

- Markdown uses one sentence per line, so diffs stay reviewable.
- Files under `docs/research/` are archived evidence: never edit or reformat them; add a new dated file instead.
- Commit messages follow conventional commits.
- A normative rule has exactly one home: the Rules section of `skills/plugin-marketplaces/SKILL.md`; every other file cites the rule id and does not restate it.
- The skill covers a tool only if a runnable probe can check its behaviour; a tool without one is excluded, not described as unverified.
- Tool behaviour facts live in `skills/plugin-marketplaces/scripts/readers.json` and the reference files, each with provenance; change a fact only after re-verifying it against its source.
- Use `uv` for all Python work; run `uv run pytest` and `prek run --all-files` before committing.
- Never run the validator or a probe against a real tool configuration; probes use throwaway config directories.
```

- [ ] **Step 4: Write `README.md`**

```markdown
# plugin-marketplaces

An agent skill for creating, auditing, maintaining, and releasing user-hosted plugin marketplaces for Claude Code, Codex, and tools that read the same catalog formats.

A user-hosted plugin marketplace is a catalog file that its maintainer writes and hosts, typically in a git repository; it is distinct from a vendor-hosted registry.

Status: under construction; see `docs/superpowers/specs/` for the design.

## Development

```bash
uv sync
uv run pytest
prek run --all-files
```
```

- [ ] **Step 5: Copy the frontmatter checker**

```bash
mkdir -p tools
cp ~/projects/skills/scripts/check-skill-frontmatter.py tools/check_skill_frontmatter.py
uv run python tools/check_skill_frontmatter.py --help || true
```

Expected: it prints usage or runs without an import error (pyyaml comes from the dev group after `uv sync`).

- [ ] **Step 6: Write the failing test for the one-sentence-per-line checker**

`tests/test_sentence_per_line.py`:

```python
from check_sentence_per_line import main, violations


def test_single_sentences_pass():
    assert violations("One sentence.\nAnother sentence here.\n") == []


def test_two_sentences_on_one_line_fail():
    assert violations("Intro line.\nFirst one. Second one.\n") == [2]


def test_abbreviations_are_not_sentence_breaks():
    assert violations("Use a source, e.g. Codex reads it.\nCompare A vs. B here.\n") == []


def test_list_markers_and_numbered_headings_are_not_sentences():
    assert violations("## 1. Purpose\n1. Core model: a catalog.\n  2. Second item here.\n") == []


def test_code_spans_fences_and_tables_are_ignored():
    text = (
        "Run `a. B` now.\n"
        "```\n"
        "x = 1. Y = 2.\n"
        "```\n"
        "| a. B | c. D |\n"
    )
    assert violations(text) == []


def test_main_reports_and_fails(tmp_path, capsys):
    bad = tmp_path / "bad.md"
    bad.write_text("One. Two.\n", encoding="utf-8")
    assert main([str(bad)]) == 1
    assert "bad.md:1" in capsys.readouterr().out
```

- [ ] **Step 7: Write `tests/conftest.py` with the git-environment guard**

```python
"""Shared test configuration."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _isolate_git_env(monkeypatch: pytest.MonkeyPatch) -> None:
    # prek runs hooks under `git commit`; an inherited GIT_INDEX_FILE lets any git
    # subprocess started by a test rewrite the real index.
    for name in ("GIT_DIR", "GIT_INDEX_FILE", "GIT_WORK_TREE"):
        monkeypatch.delenv(name, raising=False)
```

- [ ] **Step 8: Run the test to verify it fails**

Run: `uv sync && uv run pytest tests/test_sentence_per_line.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'check_sentence_per_line'`.

- [ ] **Step 9: Write `tools/check_sentence_per_line.py`**

```python
"""Fail when a Markdown line holds more than one sentence (see AGENTS.md)."""

from __future__ import annotations

import re
import sys
from pathlib import Path

CODE_SPAN = re.compile(r"`[^`]*`")
LEAD = re.compile(r"^\s*(?:>\s*)?(?:#+\s*)?(?:\d+\.|[-*+])?\s*")
ABBREVIATIONS = ("e.g.", "i.e.", "etc.", "vs.", "cf.")
BREAK = re.compile(r"[a-z0-9)\]*_\"'][.!?] +[A-Z]")


def violations(text: str) -> list[int]:
    found: list[int] = []
    in_fence = False
    for number, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence or stripped.startswith("|"):
            continue
        prose = CODE_SPAN.sub("CODE", LEAD.sub("", line, count=1))
        for abbreviation in ABBREVIATIONS:
            prose = prose.replace(abbreviation, "ABBR")
        if BREAK.search(prose):
            found.append(number)
    return found


def main(argv: list[str]) -> int:
    status = 0
    for name in argv:
        for number in violations(Path(name).read_text(encoding="utf-8")):
            print(f"{name}:{number}: more than one sentence on this line")
            status = 1
    return status


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
```

- [ ] **Step 10: Run the test to verify it passes**

Run: `uv run pytest tests/test_sentence_per_line.py -v`
Expected: 6 passed.

- [ ] **Step 11: Write `prek.toml`**

```toml
minimum_prek_version = "0.3.0"

[[repos]]
repo = "builtin"
hooks = [
  { id = "trailing-whitespace", exclude = "^docs/research/" },
  { id = "end-of-file-fixer", exclude = "^docs/research/" },
  { id = "mixed-line-ending" },
  { id = "check-merge-conflict" },
  { id = "check-added-large-files" },
  { id = "check-yaml" },
  { id = "check-toml" },
]

[[repos]]
repo = "local"
hooks = [
  { id = "ruff-check", name = "ruff check", language = "system", entry = "uv run ruff check --fix", types = ["python"] },
  { id = "ruff-format", name = "ruff format", language = "system", entry = "uv run ruff format", types = ["python"] },
  { id = "ty", name = "ty check", language = "system", entry = "uv run ty check --extra-search-path skills/plugin-marketplaces/scripts --extra-search-path tests --extra-search-path tools", pass_filenames = false, types = ["python"] },
  { id = "pytest", name = "pytest", language = "system", entry = "uv run pytest -q", pass_filenames = false, files = "^(skills/|tests/|tools/|pyproject\\.toml$)" },
  { id = "sentence-per-line", name = "Markdown: one sentence per line", language = "system", entry = "uv run python tools/check_sentence_per_line.py", files = "\\.md$", exclude = "^docs/research/" },
  { id = "skill-frontmatter", name = "SKILL.md frontmatter (agentskills.io)", language = "system", entry = "uv run python tools/check_skill_frontmatter.py", files = "(^|/)SKILL\\.md$" },
]
```

- [ ] **Step 12: Write `.github/workflows/ci.yml`**

```yaml
name: ci

on:
  pull_request:
  push:
    branches: [main]

permissions:
  contents: read

jobs:
  checks:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v6
      - run: uv sync
      - run: uv tool install prek==0.5.3
      - run: prek run --all-files
```

- [ ] **Step 13: Run every hook, including on the existing spec and research files**

Run: `prek run --all-files`
Expected: all hooks pass.
If `sentence-per-line` flags lines in `docs/superpowers/`, split those lines (never touch `docs/research/`), then re-run.

- [ ] **Step 14: Commit**

```bash
git add pyproject.toml uv.lock prek.toml .gitignore LICENSE README.md AGENTS.md CLAUDE.md .github/workflows/ci.yml tools/check_skill_frontmatter.py tools/check_sentence_per_line.py tests/test_sentence_per_line.py tests/conftest.py docs/superpowers
git commit -m "chore: add repository skeleton, tooling, and Markdown sentence check

🤖 Generated with Claude Code"
```

---

### Task 3: Finding model and duplicate-key JSON loading

**Files:**
- Create: `skills/plugin-marketplaces/scripts/mpcheck/__init__.py` (empty), `skills/plugin-marketplaces/scripts/mpcheck/model.py`, `skills/plugin-marketplaces/scripts/mpcheck/jsonload.py`
- Test: `tests/test_model_and_jsonload.py`

**Interfaces:**
- Produces: `mpcheck.model.Severity` (`ERROR`, `WARNING`, `INFO`), `mpcheck.model.Status` (`PASSED`, `FAILED`, `SKIPPED`, `INCONCLUSIVE`, `UNPROVEN`), all `StrEnum`.
- Produces: `mpcheck.model.Finding(check: str, severity: Severity, file: str, message: str, rule: str | None = None, pointer: str = "", source: str = "")`, frozen, with properties `level -> str` and `group -> str` and method `to_dict() -> dict[str, object]`.
- Produces: `mpcheck.jsonload.load_json(path: Path) -> object`, raising `mpcheck.jsonload.DuplicateKeyError` (a `ValueError`) or `json.JSONDecodeError`.

- [ ] **Step 1: Write the failing tests**

```python
import json

import pytest

from mpcheck.jsonload import DuplicateKeyError, load_json
from mpcheck.model import Finding, Severity


def test_group_and_level():
    assert Finding("schema.portable.mcp", Severity.ERROR, "f", "m").group == "schema.portable"
    assert Finding("schema.portable.mcp", Severity.ERROR, "f", "m").level == "schema"
    assert Finding("local.path-escape", Severity.ERROR, "f", "m").group == "local"


def test_to_dict_is_json_serialisable():
    data = Finding("local.x", Severity.WARNING, "f", "m", rule="R3").to_dict()
    assert json.loads(json.dumps(data))["severity"] == "warning"
    assert data["group"] == "local"


def test_load_json_rejects_duplicate_keys(tmp_path):
    path = tmp_path / "a.json"
    path.write_text('{"name": "a", "name": "b"}', encoding="utf-8")
    with pytest.raises(DuplicateKeyError, match="'name'"):
        load_json(path)


def test_load_json_detects_nested_duplicates(tmp_path):
    path = tmp_path / "a.json"
    path.write_text('{"plugins": [{"source": 1, "source": 2}]}', encoding="utf-8")
    with pytest.raises(DuplicateKeyError):
        load_json(path)


def test_load_json_reads_valid_json(tmp_path):
    path = tmp_path / "a.json"
    path.write_text('{"a": [1, {"b": 2}]}', encoding="utf-8")
    assert load_json(path) == {"a": [1, {"b": 2}]}
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/test_model_and_jsonload.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'mpcheck'`.

- [ ] **Step 3: Implement `mpcheck/model.py`**

```python
"""Finding and status types shared by every check."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum


class Severity(StrEnum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class Status(StrEnum):
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    INCONCLUSIVE = "inconclusive"
    UNPROVEN = "unproven"


@dataclass(frozen=True)
class Finding:
    check: str
    severity: Severity
    file: str
    message: str
    rule: str | None = None
    pointer: str = ""
    source: str = ""

    @property
    def level(self) -> str:
        return self.check.split(".")[0]

    @property
    def group(self) -> str:
        parts = self.check.split(".")
        return ".".join(parts[:2]) if parts[0] == "schema" else parts[0]

    def to_dict(self) -> dict[str, object]:
        data: dict[str, object] = asdict(self)
        data["level"] = self.level
        data["group"] = self.group
        return data
```

- [ ] **Step 4: Implement `mpcheck/jsonload.py`**

```python
"""JSON loading that refuses duplicate keys, which tools resolve silently."""

from __future__ import annotations

import json
from pathlib import Path


class DuplicateKeyError(ValueError):
    pass


def _no_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate key {key!r}")
        result[key] = value
    return result


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_no_duplicates)
```

Create `skills/plugin-marketplaces/scripts/mpcheck/__init__.py` as an empty file.

- [ ] **Step 5: Run to verify pass**

Run: `uv run pytest tests/test_model_and_jsonload.py -v`
Expected: 5 passed.

- [ ] **Step 6: Commit**

```bash
git add skills/plugin-marketplaces/scripts/mpcheck/__init__.py skills/plugin-marketplaces/scripts/mpcheck/model.py skills/plugin-marketplaces/scripts/mpcheck/jsonload.py tests/test_model_and_jsonload.py
git commit -m "feat(validator): add finding model and duplicate-key-safe JSON loading

🤖 Generated with Claude Code"
```

---

### Task 4: Reader facts and source classification

**Files:**
- Create: `skills/plugin-marketplaces/scripts/readers.json`, `skills/plugin-marketplaces/scripts/mpcheck/readers.py`
- Test: `tests/test_readers.py`

**Interfaces:**
- Produces: `mpcheck.readers.Reader` frozen dataclass with fields `id: str`, `reference: str`, `catalog_paths: tuple[str, ...]`, `source_types: frozenset[str]`, `path_requires_dot_slash: bool`, `marketplace_name_re: re.Pattern[str] | None`, `entry_name_re: re.Pattern[str] | None`, `reads_entry_hooks: bool`.
- Produces: `load_readers(path: Path = DEFAULT_READERS_PATH) -> dict[str, Reader]`, `source_type(source: object) -> str`, `source_path(source: object) -> str | None`, `GIT_SOURCE_TYPES: frozenset[str]`.
- Source type vocabulary: `"path"` (a string), `"local-object"` (Codex `{"source": "local", "path": ...}`), the object's `"source"` value otherwise, `"invalid"` for anything else.

- [ ] **Step 1: Write the failing tests**

```python
from mpcheck.readers import load_readers, source_path, source_type


def test_covered_readers_load():
    readers = load_readers()
    assert {"claude-code", "codex"} <= set(readers)
    codex = readers["codex"]
    assert codex.catalog_paths[0] == ".agents/plugins/marketplace.json"
    assert ".claude-plugin/marketplace.json" in codex.catalog_paths
    assert "github" not in codex.source_types
    assert "local-object" in codex.source_types
    assert "local-object" not in readers["claude-code"].source_types


def test_name_patterns():
    readers = load_readers()
    assert readers["codex"].marketplace_name_re.fullmatch("my-market_1")
    assert not readers["codex"].marketplace_name_re.fullmatch("my.market")
    assert not readers["claude-code"].marketplace_name_re.fullmatch("has space")
    assert readers["codex"].entry_name_re.fullmatch("a.b-c")
    assert not readers["codex"].entry_name_re.fullmatch("a..b")


def test_source_type_classification():
    assert source_type("./plugins/a") == "path"
    assert source_type({"source": "local", "path": "./a"}) == "local-object"
    assert source_type({"source": "github", "repo": "o/r"}) == "github"
    assert source_type({"repo": "o/r"}) == "invalid"
    assert source_type(7) == "invalid"


def test_source_path():
    assert source_path("./a") == "./a"
    assert source_path({"source": "local", "path": "./b"}) == "./b"
    assert source_path({"source": "url", "url": "https://x"}) is None
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/test_readers.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'mpcheck.readers'`.

- [ ] **Step 3: Write `readers.json`**

Values come from `docs/research/2026-09-27-claude-code.md` and `docs/research/2026-09-27-codex.md`.
Only Claude Code and Codex appear here; Task 12 adds Copilot CLI and VS Code if and only if Task 1 recorded passing probes.

```json
{
  "$comment": "Facts per covered reader. Provenance: docs/research/2026-09-27-*.md until the reference named in 'reference' exists; change a value only after re-verifying it.",
  "claude-code": {
    "reference": "references/claude-code.md",
    "catalog_paths": [".claude-plugin/marketplace.json"],
    "source_types": ["path", "github", "url", "git-subdir", "npm", "archive", "command"],
    "path_requires_dot_slash": true,
    "marketplace_name_pattern": "^(?!\\.$)(?!.*\\.\\.)[^\\s/\\\\\\x00-\\x1f]+$",
    "entry_name_pattern": "^[^\\s]+$",
    "reads_entry_hooks": true
  },
  "codex": {
    "reference": "references/codex.md",
    "catalog_paths": [
      ".agents/plugins/marketplace.json",
      ".agents/plugins/api_marketplace.json",
      ".claude-plugin/marketplace.json",
      ".cursor-plugin/marketplace.json"
    ],
    "source_types": ["path", "local-object", "url", "git-subdir", "npm"],
    "path_requires_dot_slash": true,
    "marketplace_name_pattern": "^[A-Za-z0-9_-]+$",
    "entry_name_pattern": "^[A-Za-z0-9_-]+(\\.[A-Za-z0-9_-]+)*$",
    "reads_entry_hooks": false
  }
}
```

- [ ] **Step 4: Implement `mpcheck/readers.py`**

```python
"""Reader facts from readers.json, and classification of catalog sources."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

DEFAULT_READERS_PATH = Path(__file__).resolve().parent.parent / "readers.json"
GIT_SOURCE_TYPES = frozenset({"github", "url", "git-subdir"})


@dataclass(frozen=True)
class Reader:
    id: str
    reference: str
    catalog_paths: tuple[str, ...]
    source_types: frozenset[str]
    path_requires_dot_slash: bool
    marketplace_name_re: re.Pattern[str] | None
    entry_name_re: re.Pattern[str] | None
    reads_entry_hooks: bool


def _compile(pattern: str | None) -> re.Pattern[str] | None:
    return re.compile(pattern) if pattern is not None else None


def load_readers(path: Path = DEFAULT_READERS_PATH) -> dict[str, Reader]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    readers: dict[str, Reader] = {}
    for reader_id, spec in raw.items():
        if reader_id.startswith("$"):
            continue
        readers[reader_id] = Reader(
            id=reader_id,
            reference=spec["reference"],
            catalog_paths=tuple(spec["catalog_paths"]),
            source_types=frozenset(spec["source_types"]),
            path_requires_dot_slash=spec["path_requires_dot_slash"],
            marketplace_name_re=_compile(spec.get("marketplace_name_pattern")),
            entry_name_re=_compile(spec.get("entry_name_pattern")),
            reads_entry_hooks=spec.get("reads_entry_hooks", False),
        )
    return readers


def source_type(source: object) -> str:
    if isinstance(source, str):
        return "path"
    if isinstance(source, dict):
        kind = source.get("source")
        if kind == "local":
            return "local-object"
        if isinstance(kind, str) and kind:
            return kind
    return "invalid"


def source_path(source: object) -> str | None:
    if isinstance(source, str):
        return source
    if isinstance(source, dict) and source.get("source") == "local":
        path = source.get("path")
        return path if isinstance(path, str) else None
    return None
```

- [ ] **Step 5: Run to verify pass**

Run: `uv run pytest tests/test_readers.py -v`
Expected: 4 passed.

- [ ] **Step 6: Commit**

```bash
git add skills/plugin-marketplaces/scripts/readers.json skills/plugin-marketplaces/scripts/mpcheck/readers.py tests/test_readers.py
git commit -m "feat(validator): add reader facts for Claude Code and Codex

🤖 Generated with Claude Code"
```

---

### Task 5: Discovery of catalogs and local plugin manifests

**Files:**
- Create: `skills/plugin-marketplaces/scripts/mpcheck/discover.py`
- Test: `tests/test_discover.py`, `tests/helpers.py`

**Interfaces:**
- Consumes: `load_json`, `DuplicateKeyError` (Task 3); `Reader`, `source_path` (Task 4); `Finding`, `Severity` (Task 3).
- Produces: `Catalog(relpath: str, data: dict[str, object], entries: list[tuple[int, dict[str, object]]])`; every entry kept has a `str` `"name"` and a `"source"` key.
- Produces: `Plugin(directory: Path, manifests: dict[str, dict[str, object]])`; manifest keys are `".claude-plugin/plugin.json"`, `".codex-plugin/plugin.json"`, and `"plugin.json"` (present only when the root manifest declares the Agent Plugins `$schema`).
- Produces: `Repo(root: Path, catalogs: dict[str, Catalog], reader_catalog: dict[str, str | None], plugins: dict[Path, Plugin])` with methods `readers_of(relpath: str, declared: tuple[str, ...]) -> list[str]` and `plugin_for(entry: dict[str, object]) -> Plugin | None`.
- Produces: `resolve_local(root: Path, source: object) -> Path | None` and `discover(root: Path, readers: dict[str, Reader]) -> tuple[Repo, list[Finding]]`; `Repo.root` is always resolved.
- Produces: `tests/helpers.py` with `write(root, rel, content) -> Path`, `read(root, rel) -> object`, `remote(**extra) -> dict`, constants `AP_SCHEMA`, `SHA`.

- [ ] **Step 1: Write `tests/helpers.py`**

```python
"""Helpers for building marketplace fixtures in a temporary directory."""

from __future__ import annotations

import json
from pathlib import Path

AP_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
AP_MCP_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json"
SHA = "a" * 40


def write(root: Path, rel: str, content: object) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    text = content if isinstance(content, str) else json.dumps(content, indent=2) + "\n"
    path.write_text(text, encoding="utf-8")
    return path


def read(root: Path, rel: str) -> object:
    return json.loads((root / rel).read_text(encoding="utf-8"))


def remote(**extra: object) -> dict[str, object]:
    return {
        "source": "url",
        "url": "https://github.com/example/beta.git",
        "ref": "v1.0.0",
        "sha": SHA,
        **extra,
    }
```

- [ ] **Step 2: Write the failing tests**

`tests/test_discover.py`:

```python
from helpers import AP_SCHEMA, write

from mpcheck.discover import discover
from mpcheck.readers import load_readers

READERS = load_readers()


def ids(findings):
    return sorted(f.check for f in findings)


def catalog(**extra):
    return {"name": "demo", "owner": {"name": "T"}, "plugins": [], **extra}


def test_no_catalog_is_an_error(tmp_path):
    repo, findings = discover(tmp_path, READERS)
    assert ids(findings) == ["schema.parse.no-catalog"]
    assert repo.catalogs == {}


def test_codex_prefers_native_catalog(tmp_path):
    write(tmp_path, ".claude-plugin/marketplace.json", catalog())
    repo, _ = discover(tmp_path, READERS)
    assert repo.reader_catalog["codex"] == ".claude-plugin/marketplace.json"
    write(tmp_path, ".agents/plugins/marketplace.json", catalog())
    repo, _ = discover(tmp_path, READERS)
    assert repo.reader_catalog["codex"] == ".agents/plugins/marketplace.json"
    assert repo.reader_catalog["claude-code"] == ".claude-plugin/marketplace.json"


def test_duplicate_key_is_reported(tmp_path):
    write(tmp_path, ".claude-plugin/marketplace.json", '{"name": "a", "name": "b", "plugins": []}')
    _, findings = discover(tmp_path, READERS)
    assert ids(findings) == ["schema.parse.duplicate-key"]


def test_bom_is_reported(tmp_path):
    path = tmp_path / ".claude-plugin" / "marketplace.json"
    path.parent.mkdir(parents=True)
    path.write_bytes(b"\xef\xbb\xbf" + b'{"name": "a", "plugins": []}')
    _, findings = discover(tmp_path, READERS)
    assert ids(findings) == ["schema.parse.invalid-json"]
    assert findings[0].file == ".claude-plugin/marketplace.json"


def test_catalog_shape_errors(tmp_path):
    write(tmp_path, ".claude-plugin/marketplace.json", catalog(plugins={}))
    write(tmp_path, ".agents/plugins/marketplace.json", catalog(plugins=[
        {"name": "ok", "source": "./x"},
        {"source": "./y"},
        {"name": "no-source"},
        "not-an-object",
    ]))
    repo, findings = discover(tmp_path, READERS)
    assert ids(findings) == ["schema.parse.catalog-shape"] + ["schema.parse.entry-shape"] * 3
    assert [i for i, _ in repo.catalogs[".agents/plugins/marketplace.json"].entries] == [0]
    assert {f.pointer for f in findings if f.check.endswith("entry-shape")} == {
        "/plugins/1", "/plugins/2", "/plugins/3"
    }


def test_local_plugin_manifests_are_indexed(tmp_path):
    write(tmp_path, ".claude-plugin/marketplace.json", catalog(plugins=[{"name": "a", "source": "./p/a"}]))
    write(tmp_path, "p/a/.claude-plugin/plugin.json", {"name": "a"})
    write(tmp_path, "p/a/plugin.json", {"$schema": AP_SCHEMA, "name": "a"})
    repo, findings = discover(tmp_path, READERS)
    assert findings == []
    plugin = repo.plugin_for({"name": "a", "source": "./p/a"})
    assert plugin is not None
    assert set(plugin.manifests) == {".claude-plugin/plugin.json", "plugin.json"}


def test_root_plugin_json_without_portable_schema(tmp_path):
    write(tmp_path, ".claude-plugin/marketplace.json", catalog(plugins=[{"name": "a", "source": "./p/a"}]))
    write(tmp_path, "p/a/plugin.json", {"name": "a"})
    repo, findings = discover(tmp_path, READERS)
    assert ids(findings) == ["local.portable-schema-missing"]
    assert "plugin.json" not in repo.plugin_for({"source": "./p/a"}).manifests


def test_symlinked_root_plugin_json(tmp_path):
    write(tmp_path, ".claude-plugin/marketplace.json", catalog(plugins=[{"name": "a", "source": "./p/a"}]))
    real = write(tmp_path, "elsewhere.json", {"$schema": AP_SCHEMA, "name": "a"})
    (tmp_path / "p/a").mkdir(parents=True)
    (tmp_path / "p/a/plugin.json").symlink_to(real)
    _, findings = discover(tmp_path, READERS)
    assert ids(findings) == ["local.portable-symlink"]
```

- [ ] **Step 3: Run to verify failure**

Run: `uv run pytest tests/test_discover.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'mpcheck.discover'`.

- [ ] **Step 4: Implement `mpcheck/discover.py`**

```python
"""Find catalogs and local plugin manifests under a marketplace root."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from mpcheck.jsonload import DuplicateKeyError, load_json
from mpcheck.model import Finding, Severity
from mpcheck.readers import Reader, source_path

PORTABLE_SCHEMA_PREFIX = "https://agent-plugins.org/schemas/"
MANIFEST_FILES = (".claude-plugin/plugin.json", ".codex-plugin/plugin.json")


@dataclass
class Catalog:
    relpath: str
    data: dict[str, object]
    entries: list[tuple[int, dict[str, object]]]


@dataclass
class Plugin:
    directory: Path
    manifests: dict[str, dict[str, object]] = field(default_factory=dict)


@dataclass
class Repo:
    root: Path
    catalogs: dict[str, Catalog]
    reader_catalog: dict[str, str | None]
    plugins: dict[Path, Plugin]

    def readers_of(self, relpath: str, declared: tuple[str, ...]) -> list[str]:
        return [reader for reader in declared if self.reader_catalog.get(reader) == relpath]

    def plugin_for(self, entry: dict[str, object]) -> Plugin | None:
        directory = resolve_local(self.root, entry.get("source"))
        return self.plugins.get(directory) if directory is not None else None


def resolve_local(root: Path, source: object) -> Path | None:
    """The plugin directory for a valid local source inside root, else None."""
    rel = source_path(source)
    if rel is None or ".." in Path(rel).parts:
        return None
    try:
        resolved = (root / rel).resolve()
    except (OSError, RuntimeError):
        return None
    if not resolved.is_relative_to(root.resolve()) or not resolved.is_dir():
        return None
    return resolved


def _rel(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def _load(root: Path, path: Path, findings: list[Finding]) -> object | None:
    rel = _rel(root, path)
    try:
        return load_json(path)
    except DuplicateKeyError as exc:
        findings.append(
            Finding(
                "schema.parse.duplicate-key",
                Severity.ERROR,
                rel,
                f"{exc}; tools keep one of the values without warning",
            )
        )
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        findings.append(
            Finding("schema.parse.invalid-json", Severity.ERROR, rel, f"not valid JSON: {exc}")
        )
    return None


def _load_catalog(root: Path, rel: str, findings: list[Finding]) -> Catalog | None:
    data = _load(root, root / rel, findings)
    if data is None:
        return None
    plugins = data.get("plugins") if isinstance(data, dict) else None
    if not isinstance(data, dict) or not isinstance(plugins, list):
        findings.append(
            Finding(
                "schema.parse.catalog-shape",
                Severity.ERROR,
                rel,
                "a catalog must be a JSON object with a 'plugins' array",
            )
        )
        return None
    entries: list[tuple[int, dict[str, object]]] = []
    for index, entry in enumerate(plugins):
        if isinstance(entry, dict) and isinstance(entry.get("name"), str) and "source" in entry:
            entries.append((index, entry))
        else:
            findings.append(
                Finding(
                    "schema.parse.entry-shape",
                    Severity.ERROR,
                    rel,
                    "an entry must be an object with a string 'name' and a 'source'",
                    pointer=f"/plugins/{index}",
                )
            )
    return Catalog(rel, data, entries)


def _load_plugin(root: Path, directory: Path, findings: list[Finding]) -> Plugin:
    plugin = Plugin(directory)
    for rel in MANIFEST_FILES:
        path = directory / rel
        if path.is_file():
            data = _load(root, path, findings)
            if isinstance(data, dict):
                plugin.manifests[rel] = data
    portable = directory / "plugin.json"
    portable_rel = _rel(root, portable)
    if portable.is_symlink():
        findings.append(
            Finding(
                "local.portable-symlink",
                Severity.ERROR,
                portable_rel,
                "a symlinked root plugin.json disables manifest detection in Codex",
            )
        )
    elif portable.is_file():
        data = _load(root, portable, findings)
        if isinstance(data, dict):
            schema = data.get("$schema")
            if isinstance(schema, str) and schema.startswith(PORTABLE_SCHEMA_PREFIX):
                plugin.manifests["plugin.json"] = data
            else:
                findings.append(
                    Finding(
                        "local.portable-schema-missing",
                        Severity.WARNING,
                        portable_rel,
                        "root plugin.json lacks the Agent Plugins $schema, so portable readers "
                        "treat it as unrelated and fall back to other manifests",
                    )
                )
    return plugin


def discover(root: Path, readers: dict[str, Reader]) -> tuple[Repo, list[Finding]]:
    root = root.resolve()
    findings: list[Finding] = []
    candidates: list[str] = []
    for reader in readers.values():
        for rel in reader.catalog_paths:
            if rel not in candidates:
                candidates.append(rel)
    present = [rel for rel in candidates if (root / rel).is_file()]
    if not present:
        findings.append(
            Finding(
                "schema.parse.no-catalog",
                Severity.ERROR,
                ".",
                f"no catalog found; covered readers look for: {', '.join(candidates)}",
            )
        )
    catalogs: dict[str, Catalog] = {}
    for rel in present:
        catalog = _load_catalog(root, rel, findings)
        if catalog is not None:
            catalogs[rel] = catalog
    reader_catalog = {
        reader.id: next((rel for rel in reader.catalog_paths if rel in present), None)
        for reader in readers.values()
    }
    plugins: dict[Path, Plugin] = {}
    for catalog in catalogs.values():
        for _, entry in catalog.entries:
            directory = resolve_local(root, entry.get("source"))
            if directory is not None and directory not in plugins:
                plugins[directory] = _load_plugin(root, directory, findings)
    return Repo(root, catalogs, reader_catalog, plugins), findings
```

- [ ] **Step 5: Run to verify pass**

Run: `uv run pytest tests/test_discover.py -v`
Expected: 8 passed.

- [ ] **Step 6: Commit**

```bash
git add skills/plugin-marketplaces/scripts/mpcheck/discover.py tests/test_discover.py tests/helpers.py
git commit -m "feat(validator): discover catalogs, reader precedence, and local manifests

🤖 Generated with Claude Code"
```

---

### Task 6: Policy file

**Files:**
- Create: `skills/plugin-marketplaces/scripts/mpcheck/policy.py`
- Test: `tests/test_policy.py`

**Interfaces:**
- Consumes: `load_json`, `DuplicateKeyError`, `Finding`, `Severity`.
- Produces: `POLICY_FILE = "marketplace-policy.json"`, `ParityException(plugin: str, kind: str, reason: str)` where `kind` is one of `"membership"`, `"version"`, `"source"`.
- Produces: `Policy(readers: tuple[str, ...], exceptions: tuple[ParityException, ...], declared: bool)` with method `excepts(plugin: str, kind: str) -> bool`.
- Produces: `load_policy(root: Path, path: Path | None, known: set[str], reading: dict[str, str | None]) -> tuple[Policy, list[Finding]]`.

Policy file format:

```json
{
  "readers": ["claude-code", "codex"],
  "exceptions": [
    {"plugin": "voice-notify", "kind": "membership", "reason": "macOS hook plugin; Codex does not run command hooks from this catalog"}
  ]
}
```

- [ ] **Step 1: Write the failing tests**

```python
from helpers import write

from mpcheck.policy import load_policy

KNOWN = {"claude-code", "codex"}
READING = {"claude-code": ".claude-plugin/marketplace.json", "codex": None}


def ids(findings):
    return sorted(f.check for f in findings)


def test_missing_policy_infers_readers_and_warns(tmp_path):
    policy, findings = load_policy(tmp_path, None, KNOWN, READING)
    assert policy.readers == ("claude-code",)
    assert policy.declared is False
    assert ids(findings) == ["policy.inferred"]


def test_valid_policy(tmp_path):
    write(tmp_path, "marketplace-policy.json", {
        "readers": ["claude-code", "codex"],
        "exceptions": [{"plugin": "x", "kind": "membership", "reason": "Claude only"}],
    })
    policy, findings = load_policy(tmp_path, None, KNOWN, READING)
    assert findings == []
    assert policy.readers == ("claude-code", "codex")
    assert policy.excepts("x", "membership")
    assert not policy.excepts("x", "version")


def test_unknown_reader(tmp_path):
    write(tmp_path, "marketplace-policy.json", {"readers": ["claude-code", "cursor"]})
    policy, findings = load_policy(tmp_path, None, KNOWN, READING)
    assert ids(findings) == ["policy.unknown-reader"]
    assert policy.readers == ("claude-code",)


def test_exception_without_reason(tmp_path):
    write(tmp_path, "marketplace-policy.json", {
        "readers": ["codex"],
        "exceptions": [{"plugin": "x", "kind": "membership", "reason": "  "}, {"plugin": "y", "kind": "bogus", "reason": "r"}],
    })
    policy, findings = load_policy(tmp_path, None, KNOWN, READING)
    assert ids(findings) == ["policy.invalid-exception", "policy.invalid-exception"]
    assert policy.exceptions == ()


def test_invalid_policy_shapes(tmp_path):
    write(tmp_path, "marketplace-policy.json", {"readers": [], "exceptions": {}})
    _, findings = load_policy(tmp_path, None, KNOWN, READING)
    assert ids(findings) == ["policy.invalid", "policy.invalid"]


def test_explicit_policy_path(tmp_path):
    custom = write(tmp_path, "config/policy.json", {"readers": ["codex"]})
    policy, findings = load_policy(tmp_path, custom, KNOWN, READING)
    assert findings == []
    assert policy.readers == ("codex",)
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/test_policy.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'mpcheck.policy'`.

- [ ] **Step 3: Implement `mpcheck/policy.py`**

```python
"""marketplace-policy.json: declared target readers and parity exceptions (spec R1, R10)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from mpcheck.jsonload import DuplicateKeyError, load_json
from mpcheck.model import Finding, Severity

POLICY_FILE = "marketplace-policy.json"
EXCEPTION_KINDS = frozenset({"membership", "version", "source"})


@dataclass(frozen=True)
class ParityException:
    plugin: str
    kind: str
    reason: str


@dataclass(frozen=True)
class Policy:
    readers: tuple[str, ...]
    exceptions: tuple[ParityException, ...]
    declared: bool

    def excepts(self, plugin: str, kind: str) -> bool:
        return any(e.plugin == plugin and e.kind == kind for e in self.exceptions)


def _display(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix() if path.is_relative_to(root) else str(path)


def load_policy(
    root: Path, path: Path | None, known: set[str], reading: dict[str, str | None]
) -> tuple[Policy, list[Finding]]:
    root = root.resolve()
    path = (path if path is not None else root / POLICY_FILE).resolve()
    rel = _display(root, path)
    findings: list[Finding] = []
    if not path.is_file():
        inferred = tuple(r for r in sorted(known) if reading.get(r) is not None)
        findings.append(
            Finding(
                "policy.inferred",
                Severity.WARNING,
                rel,
                "no policy file; inferred target readers from the catalogs present: "
                f"{', '.join(inferred) or 'none'}",
                rule="R1",
            )
        )
        return Policy(inferred, (), declared=False), findings
    try:
        raw = load_json(path)
    except (DuplicateKeyError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        findings.append(
            Finding("policy.invalid", Severity.ERROR, rel, f"cannot read policy: {exc}", rule="R1")
        )
        return Policy((), (), declared=True), findings
    raw = raw if isinstance(raw, dict) else {}
    readers_raw = raw.get("readers")
    if not (
        isinstance(readers_raw, list)
        and readers_raw
        and all(isinstance(r, str) for r in readers_raw)
    ):
        findings.append(
            Finding(
                "policy.invalid",
                Severity.ERROR,
                rel,
                "'readers' must be a non-empty array of reader ids",
                rule="R1",
                pointer="/readers",
            )
        )
        readers_raw = []
    readers: list[str] = []
    for reader_id in readers_raw:
        if reader_id in known:
            readers.append(reader_id)
        else:
            findings.append(
                Finding(
                    "policy.unknown-reader",
                    Severity.ERROR,
                    rel,
                    f"unknown reader {reader_id!r}; covered readers: {', '.join(sorted(known))}",
                    rule="R1",
                    pointer="/readers",
                )
            )
    exceptions_raw = raw.get("exceptions", [])
    if not isinstance(exceptions_raw, list):
        findings.append(
            Finding(
                "policy.invalid",
                Severity.ERROR,
                rel,
                "'exceptions' must be an array",
                rule="R10",
                pointer="/exceptions",
            )
        )
        exceptions_raw = []
    exceptions: list[ParityException] = []
    for index, item in enumerate(exceptions_raw):
        valid = (
            isinstance(item, dict)
            and isinstance(item.get("plugin"), str)
            and item.get("kind") in EXCEPTION_KINDS
            and isinstance(item.get("reason"), str)
            and item["reason"].strip()
        )
        if valid:
            exceptions.append(ParityException(item["plugin"], item["kind"], item["reason"].strip()))
        else:
            findings.append(
                Finding(
                    "policy.invalid-exception",
                    Severity.ERROR,
                    rel,
                    "an exception needs 'plugin', 'kind' (membership, version, or source), "
                    "and a non-empty 'reason'",
                    rule="R10",
                    pointer=f"/exceptions/{index}",
                )
            )
    return Policy(tuple(readers), tuple(exceptions), declared=True), findings
```

- [ ] **Step 4: Run to verify pass**

Run: `uv run pytest tests/test_policy.py -v`
Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
git add skills/plugin-marketplaces/scripts/mpcheck/policy.py tests/test_policy.py
git commit -m "feat(validator): load marketplace policy with declared readers and exceptions

🤖 Generated with Claude Code"
```

---

### Task 7: Local checks — readers, sources, and paths (R1, R2, R3)

**Files:**
- Create: `skills/plugin-marketplaces/scripts/mpcheck/checks_local.py`
- Modify: `tests/conftest.py` (add the `market` fixture)
- Test: `tests/test_checks_paths.py`

**Interfaces:**
- Consumes: `Repo`, `Catalog`, `resolve_local`, `discover` (Task 5); `Policy`, `POLICY_FILE`, `load_policy` (Task 6); `Reader`, `source_path`, `source_type`, `load_readers` (Task 4).
- Produces: in `mpcheck.checks_local`, functions with the signature `(repo: Repo, readers: dict[str, Reader], policy: Policy) -> list[Finding]`: `check_reader_coverage`, `check_unread_catalogs`, `check_source_types`, `check_local_paths`; helper `active_catalogs(repo: Repo, policy: Policy) -> list[Catalog]`; list `LOCAL_CHECKS` that later tasks append to.
- Produces: `tests/helpers.py` function `local_ids(root: Path) -> list[str]` returning sorted check ids from discovery, policy, and every function in `LOCAL_CHECKS`.

- [ ] **Step 1: Add the clean fixture and helper**

Append to `tests/conftest.py`:

```python
from pathlib import Path

from helpers import AP_SCHEMA, remote, write


@pytest.fixture
def market(tmp_path: Path) -> Path:
    """A clean two-catalog marketplace that every check must accept."""
    install = {"installation": "AVAILABLE", "authentication": "ON_INSTALL"}
    write(tmp_path, ".claude-plugin/marketplace.json", {
        "name": "demo",
        "owner": {"name": "Tester"},
        "description": "Demo marketplace",
        "plugins": [
            {"name": "alpha", "source": "./plugins/alpha", "description": "Alpha"},
            {"name": "beta", "source": remote(), "version": "1.0.0", "description": "Beta"},
        ],
    })
    write(tmp_path, ".agents/plugins/marketplace.json", {
        "name": "demo",
        "interface": {"displayName": "Demo"},
        "plugins": [
            {"name": "alpha", "source": {"source": "local", "path": "./plugins/alpha"},
             "policy": install, "category": "Developer Tools"},
            {"name": "beta", "source": remote(), "version": "1.0.0",
             "policy": install, "category": "Developer Tools"},
        ],
    })
    write(tmp_path, "plugins/alpha/.claude-plugin/plugin.json",
          {"name": "alpha", "version": "1.2.0", "description": "Alpha", "author": {"name": "Tester"}})
    write(tmp_path, "plugins/alpha/plugin.json",
          {"$schema": AP_SCHEMA, "name": "alpha", "version": "1.2.0", "description": "Alpha"})
    write(tmp_path, "plugins/alpha/skills/hello/SKILL.md",
          "---\nname: hello\ndescription: Say hello.\n---\n\nSay hello.\n")
    write(tmp_path, "marketplace-policy.json", {"readers": ["claude-code", "codex"], "exceptions": []})
    return tmp_path
```

Move the `from __future__ import annotations` and `import pytest` lines so all imports sit at the top of `conftest.py`.

Append to `tests/helpers.py`:

```python
def local_ids(root: Path) -> list[str]:
    """Sorted check ids from discovery, policy, and every local check."""
    from mpcheck.checks_local import LOCAL_CHECKS
    from mpcheck.discover import discover
    from mpcheck.policy import load_policy
    from mpcheck.readers import load_readers

    readers = load_readers()
    repo, findings = discover(root, readers)
    policy, policy_findings = load_policy(repo.root, None, set(readers), repo.reader_catalog)
    findings += policy_findings
    for check in LOCAL_CHECKS:
        findings += check(repo, readers, policy)
    return sorted(f.check for f in findings)
```

- [ ] **Step 2: Write the failing tests**

`tests/test_checks_paths.py`:

```python
import os

from helpers import local_ids, read, remote, write

CLAUDE = ".claude-plugin/marketplace.json"
CODEX = ".agents/plugins/marketplace.json"


def set_entry(root, catalog, index, **changes):
    data = read(root, catalog)
    data["plugins"][index].update(changes)
    write(root, catalog, data)


def test_clean_market_has_no_local_findings(market):
    assert local_ids(market) == []


def test_declared_reader_without_catalog(market):
    (market / CLAUDE).unlink()
    assert local_ids(market) == ["local.reader-no-catalog"]


def test_unread_catalog_warns(market):
    write(market, "marketplace-policy.json", {"readers": ["codex"]})
    assert local_ids(market) == ["local.unread-catalog"]


def test_github_source_in_catalog_codex_reads(market):
    (market / CODEX).unlink()
    set_entry(market, CLAUDE, 1, source={"source": "github", "repo": "example/beta", "sha": "a" * 40})
    assert local_ids(market) == ["local.source-type"]


def test_local_object_in_catalog_claude_reads(market):
    set_entry(market, CLAUDE, 0, source={"source": "local", "path": "./plugins/alpha"})
    assert local_ids(market) == ["local.source-type"]


def test_bare_path(market):
    set_entry(market, CLAUDE, 0, source="plugins/alpha")
    assert local_ids(market) == ["local.path-prefix"]


def test_traversal(market):
    set_entry(market, CLAUDE, 0, source="./plugins/../plugins/alpha")
    assert local_ids(market) == ["local.path-traversal"]


def test_symlink_escape(market, tmp_path_factory):
    outside = tmp_path_factory.mktemp("outside")
    os.symlink(outside, market / "plugins" / "escape")
    set_entry(market, CLAUDE, 0, source="./plugins/escape")
    assert "local.path-escape" in local_ids(market)


def test_missing_directory(market):
    set_entry(market, CLAUDE, 0, source="./plugins/nope")
    assert "local.path-missing" in local_ids(market)


def test_source_pointing_at_file(market):
    write(market, "plugins/file.txt", "x")
    set_entry(market, CLAUDE, 0, source="./plugins/file.txt")
    assert "local.path-missing" in local_ids(market)


def test_symlink_loop_is_reported(market):
    os.symlink(market / "plugins" / "loop", market / "plugins" / "loop")
    set_entry(market, CLAUDE, 0, source="./plugins/loop")
    assert "local.path-missing" in local_ids(market)


def test_remote_sources_skip_path_checks(market):
    set_entry(market, CLAUDE, 1, source=remote())
    assert local_ids(market) == []
```

- [ ] **Step 3: Run to verify failure**

Run: `uv run pytest tests/test_checks_paths.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'mpcheck.checks_local'`.

- [ ] **Step 4: Implement the first part of `mpcheck/checks_local.py`**

```python
"""Checks no official validator covers (spec §8, level 2)."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from mpcheck.discover import Catalog, Repo
from mpcheck.model import Finding, Severity
from mpcheck.policy import POLICY_FILE, Policy
from mpcheck.readers import Reader, source_path, source_type

Check = Callable[[Repo, dict[str, Reader], Policy], list[Finding]]


def active_catalogs(repo: Repo, policy: Policy) -> list[Catalog]:
    return [c for c in repo.catalogs.values() if repo.readers_of(c.relpath, policy.readers)]


def _readers_of(repo: Repo, readers: dict[str, Reader], policy: Policy, catalog: Catalog) -> list[Reader]:
    return [readers[r] for r in repo.readers_of(catalog.relpath, policy.readers)]


def check_reader_coverage(repo: Repo, readers: dict[str, Reader], policy: Policy) -> list[Finding]:
    return [
        Finding(
            "local.reader-no-catalog",
            Severity.ERROR,
            POLICY_FILE,
            f"declared reader {r!r} finds no catalog; it reads the first of: "
            f"{', '.join(readers[r].catalog_paths)}",
            rule="R1",
            source=readers[r].reference,
        )
        for r in policy.readers
        if repo.reader_catalog.get(r) is None
    ]


def check_unread_catalogs(repo: Repo, readers: dict[str, Reader], policy: Policy) -> list[Finding]:
    active = {c.relpath for c in active_catalogs(repo, policy)}
    return [
        Finding(
            "local.unread-catalog",
            Severity.WARNING,
            rel,
            "no declared reader reads this catalog (another file takes precedence, "
            "or its readers are not declared); it is not checked further",
            rule="R1",
        )
        for rel in repo.catalogs
        if rel not in active
    ]


def check_source_types(repo: Repo, readers: dict[str, Reader], policy: Policy) -> list[Finding]:
    findings: list[Finding] = []
    for catalog in active_catalogs(repo, policy):
        for reader in _readers_of(repo, readers, policy, catalog):
            for index, entry in catalog.entries:
                kind = source_type(entry["source"])
                if kind not in reader.source_types:
                    findings.append(
                        Finding(
                            "local.source-type",
                            Severity.ERROR,
                            catalog.relpath,
                            f"{reader.id} does not accept source type {kind!r} "
                            f"(accepts: {', '.join(sorted(reader.source_types))}); "
                            f"it skips or rejects entry {entry['name']!r}",
                            rule="R2",
                            pointer=f"/plugins/{index}/source",
                            source=reader.reference,
                        )
                    )
    return findings


def check_local_paths(repo: Repo, readers: dict[str, Reader], policy: Policy) -> list[Finding]:
    findings: list[Finding] = []
    for catalog in active_catalogs(repo, policy):
        needs_prefix = [
            r.id for r in _readers_of(repo, readers, policy, catalog) if r.path_requires_dot_slash
        ]
        for index, entry in catalog.entries:
            rel = source_path(entry["source"])
            if rel is None:
                continue
            where = {"file": catalog.relpath, "pointer": f"/plugins/{index}/source", "rule": "R3"}
            if needs_prefix and not (rel == "." or rel.startswith("./")):
                findings.append(
                    Finding(
                        "local.path-prefix",
                        Severity.ERROR,
                        message=f"local source {rel!r} must start with './' for "
                        f"{', '.join(needs_prefix)}",
                        **where,
                    )
                )
            if ".." in Path(rel).parts:
                findings.append(
                    Finding(
                        "local.path-traversal",
                        Severity.ERROR,
                        message=f"local source {rel!r} contains '..'",
                        **where,
                    )
                )
                continue
            try:
                resolved = (repo.root / rel).resolve()
            except (OSError, RuntimeError):
                resolved = None
            if resolved is None:
                findings.append(
                    Finding(
                        "local.path-missing",
                        Severity.ERROR,
                        message=f"local source {rel!r} cannot be resolved (symlink loop?)",
                        **where,
                    )
                )
            elif not resolved.is_relative_to(repo.root):
                findings.append(
                    Finding(
                        "local.path-escape",
                        Severity.ERROR,
                        message=f"local source {rel!r} resolves outside the marketplace root, "
                        f"to {resolved}",
                        **where,
                    )
                )
            elif not resolved.is_dir():
                findings.append(
                    Finding(
                        "local.path-missing",
                        Severity.ERROR,
                        message=f"local source {rel!r} is not a directory under the marketplace root",
                        **where,
                    )
                )
    return findings


LOCAL_CHECKS: list[Check] = [
    check_reader_coverage,
    check_unread_catalogs,
    check_source_types,
    check_local_paths,
]
```

Note for the symlink-loop test: on Python 3.12 `Path.resolve()` in non-strict mode may return the looping path rather than raise; then `is_dir()` is false and the `local.path-missing` branch fires, which is the asserted behaviour either way.

- [ ] **Step 5: Run to verify pass**

Run: `uv run pytest tests/test_checks_paths.py -v`
Expected: 12 passed.

- [ ] **Step 6: Commit**

```bash
git add skills/plugin-marketplaces/scripts/mpcheck/checks_local.py tests/conftest.py tests/helpers.py tests/test_checks_paths.py
git commit -m "feat(validator): check declared readers, source types, and local paths

🤖 Generated with Claude Code"
```

---

### Task 8: Local checks — names (R8)

**Files:**
- Modify: `skills/plugin-marketplaces/scripts/mpcheck/checks_local.py` (add `check_names`, append to `LOCAL_CHECKS`)
- Test: `tests/test_checks_names.py`

**Interfaces:**
- Consumes: `active_catalogs`, `_readers_of`, `Repo.plugin_for` (Tasks 5, 7).
- Produces: `check_names(repo, readers, policy) -> list[Finding]` emitting `local.marketplace-name`, `local.duplicate-entry`, `local.entry-name-pattern`, `local.name-mismatch`.

- [ ] **Step 1: Write the failing tests**

```python
from helpers import local_ids, read, write

CLAUDE = ".claude-plugin/marketplace.json"
CODEX = ".agents/plugins/marketplace.json"


def test_dotted_marketplace_name_fails_codex(market):
    data = read(market, CODEX)
    data["name"] = "demo.market"
    write(market, CODEX, data)
    assert local_ids(market) == ["local.marketplace-name"]


def test_duplicate_entry(market):
    data = read(market, CLAUDE)
    data["plugins"].append(dict(data["plugins"][1]))
    write(market, CLAUDE, data)
    assert local_ids(market) == ["local.duplicate-entry"]


def test_entry_name_with_space(market):
    for catalog in (CLAUDE, CODEX):
        data = read(market, catalog)
        data["plugins"][1]["name"] = "be ta"
        write(market, catalog, data)
    assert local_ids(market) == ["local.entry-name-pattern", "local.entry-name-pattern"]


def test_manifest_name_mismatch(market):
    write(market, "plugins/alpha/.claude-plugin/plugin.json",
          {"name": "alpha-renamed", "version": "1.2.0", "description": "Alpha", "author": {"name": "T"}})
    assert local_ids(market) == ["local.name-mismatch", "local.name-mismatch"]
```

The duplicate is an exact copy of `beta`, so it stays equal on version and pin and must not trigger the parity checks Task 9 adds.

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/test_checks_names.py -v`
Expected: FAIL — the four tests report missing ids (for example `assert [] == ['local.marketplace-name']`).

- [ ] **Step 3: Implement `check_names`**

Add to `checks_local.py`, before `LOCAL_CHECKS`:

```python
def check_names(repo: Repo, readers: dict[str, Reader], policy: Policy) -> list[Finding]:
    findings: list[Finding] = []
    for catalog in active_catalogs(repo, policy):
        catalog_readers = _readers_of(repo, readers, policy, catalog)
        name = catalog.data.get("name")
        for reader in catalog_readers:
            pattern = reader.marketplace_name_re
            if pattern is not None and not (isinstance(name, str) and pattern.fullmatch(name)):
                findings.append(
                    Finding(
                        "local.marketplace-name",
                        Severity.ERROR,
                        catalog.relpath,
                        f"marketplace name {name!r} does not satisfy {reader.id}'s name rule "
                        f"({pattern.pattern})",
                        pointer="/name",
                        source=reader.reference,
                    )
                )
        seen: dict[str, int] = {}
        for index, entry in catalog.entries:
            entry_name = entry["name"]
            assert isinstance(entry_name, str)
            pointer = f"/plugins/{index}/name"
            if entry_name in seen:
                findings.append(
                    Finding(
                        "local.duplicate-entry",
                        Severity.ERROR,
                        catalog.relpath,
                        f"entry name {entry_name!r} is also used at /plugins/{seen[entry_name]}",
                        rule="R8",
                        pointer=pointer,
                    )
                )
            seen.setdefault(entry_name, index)
            for reader in catalog_readers:
                pattern = reader.entry_name_re
                if pattern is not None and not pattern.fullmatch(entry_name):
                    findings.append(
                        Finding(
                            "local.entry-name-pattern",
                            Severity.ERROR,
                            catalog.relpath,
                            f"entry name {entry_name!r} does not satisfy {reader.id}'s name rule "
                            f"({pattern.pattern})",
                            rule="R8",
                            pointer=pointer,
                            source=reader.reference,
                        )
                    )
            plugin = repo.plugin_for(entry)
            if plugin is None:
                continue
            prefix = plugin.directory.relative_to(repo.root).as_posix()
            for manifest_rel, manifest in plugin.manifests.items():
                manifest_name = manifest.get("name")
                if isinstance(manifest_name, str) and manifest_name != entry_name:
                    findings.append(
                        Finding(
                            "local.name-mismatch",
                            Severity.ERROR,
                            catalog.relpath,
                            f"entry {entry_name!r} but {prefix}/{manifest_rel} names the plugin "
                            f"{manifest_name!r}; tools install by one and namespace by the other",
                            rule="R8",
                            pointer=pointer,
                        )
                    )
    return findings
```

Append `check_names` to `LOCAL_CHECKS`.

- [ ] **Step 4: Run to verify pass, then the whole suite**

Run: `uv run pytest tests/test_checks_names.py -v && uv run pytest -q`
Expected: 4 passed; the full suite passes (the clean fixture still yields no findings).

- [ ] **Step 5: Commit**

```bash
git add skills/plugin-marketplaces/scripts/mpcheck/checks_local.py tests/test_checks_names.py
git commit -m "feat(validator): check marketplace and entry names against every reader

🤖 Generated with Claude Code"
```

---

### Task 9: Local checks — versions and parity (R6, R10)

**Files:**
- Modify: `skills/plugin-marketplaces/scripts/mpcheck/checks_local.py` (add `check_versions`, `check_parity`)
- Test: `tests/test_checks_versions.py`

**Interfaces:**
- Produces: `check_versions` emitting `local.version-mismatch` (error, R6) and `local.version-missing` (warning, R6); `check_parity` emitting `local.parity-membership`, `local.parity-version`, `local.parity-source` (errors, R10) and `policy.unused-exception` (warning, R10).
- Produces: helper `pin_of(source: object) -> str | None` returning `"path:<posix path>"`, `"sha:<sha>"`, `"sha256:<digest>"`, `"npm:<version>"`, or `None`.

Design note: R6 applies within one catalog and the manifests its entry points at; a difference *between* catalogs is R10's concern and can carry a recorded reason.

- [ ] **Step 1: Write the failing tests**

```python
from helpers import local_ids, read, remote, write

CLAUDE = ".claude-plugin/marketplace.json"
CODEX = ".agents/plugins/marketplace.json"
POLICY = "marketplace-policy.json"


def set_entry(root, catalog, index, **changes):
    data = read(root, catalog)
    data["plugins"][index].update(changes)
    write(root, catalog, data)


def test_manifest_versions_disagree(market):
    write(market, "plugins/alpha/plugin.json", {
        "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
        "name": "alpha", "version": "1.3.0", "description": "Alpha"})
    assert local_ids(market) == ["local.version-mismatch", "local.version-mismatch"]


def test_entry_version_disagrees_with_manifest(market):
    set_entry(market, CLAUDE, 0, version="9.9.9")
    assert local_ids(market) == ["local.version-mismatch"]


def test_local_plugin_without_any_version_warns(market):
    for rel in ("plugins/alpha/.claude-plugin/plugin.json", "plugins/alpha/plugin.json"):
        data = read(market, rel)
        del data["version"]
        write(market, rel, data)
    assert local_ids(market) == ["local.version-missing", "local.version-missing"]


def test_membership_difference(market):
    data = read(market, CODEX)
    data["plugins"] = data["plugins"][:1]
    write(market, CODEX, data)
    assert local_ids(market) == ["local.parity-membership"]


def test_membership_exception_suppresses(market):
    data = read(market, CODEX)
    data["plugins"] = data["plugins"][:1]
    write(market, CODEX, data)
    write(market, POLICY, {"readers": ["claude-code", "codex"], "exceptions": [
        {"plugin": "beta", "kind": "membership", "reason": "Claude-only for now"}]})
    assert local_ids(market) == []


def test_version_difference_between_catalogs(market):
    set_entry(market, CODEX, 1, version="0.9.0")
    assert local_ids(market) == ["local.parity-version"]


def test_source_pin_difference_between_catalogs(market):
    set_entry(market, CODEX, 1, source=remote(sha="b" * 40))
    assert local_ids(market) == ["local.parity-source"]


def test_unused_exception_warns(market):
    write(market, POLICY, {"readers": ["claude-code", "codex"], "exceptions": [
        {"plugin": "alpha", "kind": "version", "reason": "stale"}]})
    assert local_ids(market) == ["policy.unused-exception"]


def test_single_catalog_has_no_parity_findings(market):
    (market / CODEX).unlink()
    write(market, POLICY, {"readers": ["claude-code"]})
    assert local_ids(market) == []
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/test_checks_versions.py -v`
Expected: FAIL — missing ids (for example `assert [] == ['local.version-mismatch', ...]`).

- [ ] **Step 3: Implement version and parity checks**

Add to `checks_local.py`, before `LOCAL_CHECKS`:

```python
def _version_values(repo: Repo, catalog: Catalog, index: int, entry: dict[str, object]) -> dict[str, str]:
    values: dict[str, str] = {}
    version = entry.get("version")
    if isinstance(version, str):
        values[f"{catalog.relpath}#/plugins/{index}/version"] = version
    plugin = repo.plugin_for(entry)
    if plugin is not None:
        prefix = plugin.directory.relative_to(repo.root).as_posix()
        for manifest_rel, manifest in plugin.manifests.items():
            manifest_version = manifest.get("version")
            if isinstance(manifest_version, str):
                values[f"{prefix}/{manifest_rel}#/version"] = manifest_version
    return values


def check_versions(repo: Repo, readers: dict[str, Reader], policy: Policy) -> list[Finding]:
    findings: list[Finding] = []
    for catalog in active_catalogs(repo, policy):
        for index, entry in catalog.entries:
            values = _version_values(repo, catalog, index, entry)
            if len(set(values.values())) > 1:
                detail = "; ".join(f"{where} = {value}" for where, value in values.items())
                findings.append(
                    Finding(
                        "local.version-mismatch",
                        Severity.ERROR,
                        catalog.relpath,
                        f"plugin {entry['name']!r} records different versions: {detail}",
                        rule="R6",
                        pointer=f"/plugins/{index}",
                    )
                )
            elif not values and source_path(entry["source"]) is not None:
                findings.append(
                    Finding(
                        "local.version-missing",
                        Severity.WARNING,
                        catalog.relpath,
                        f"local plugin {entry['name']!r} has no version anywhere; tools fall back "
                        "to a commit SHA or a fixed cache directory name, so releases are not "
                        "distinguishable by version",
                        rule="R6",
                        pointer=f"/plugins/{index}",
                    )
                )
    return findings


def pin_of(source: object) -> str | None:
    rel = source_path(source)
    if rel is not None:
        return "path:" + Path(rel).as_posix()
    if isinstance(source, dict):
        for key in ("sha", "sha256"):
            value = source.get(key)
            if isinstance(value, str):
                return f"{key}:{value}"
        version = source.get("version")
        if source.get("source") == "npm" and isinstance(version, str):
            return "npm:" + version
    return None


def check_parity(repo: Repo, readers: dict[str, Reader], policy: Policy) -> list[Finding]:
    findings: list[Finding] = []
    used: set[tuple[str, str]] = set()
    active = active_catalogs(repo, policy)
    if len(active) >= 2:
        index_of = {c.relpath: {str(e["name"]): (i, e) for i, e in c.entries} for c in active}
        by_rel = {c.relpath: c for c in active}
        for name in sorted(set().union(*index_of.values())):
            present = [rel for rel, entries in index_of.items() if name in entries]
            missing = [rel for rel in index_of if rel not in present]
            if missing:
                if policy.excepts(name, "membership"):
                    used.add((name, "membership"))
                else:
                    findings.append(
                        Finding(
                            "local.parity-membership",
                            Severity.ERROR,
                            missing[0],
                            f"plugin {name!r} is in {', '.join(present)} but not in "
                            f"{', '.join(missing)}; add it, or record a 'membership' exception "
                            "with a reason",
                            rule="R10",
                        )
                    )
                continue
            versions: set[str] = set()
            pins: set[str] = set()
            for rel, (index, entry) in ((r, index_of[r][name]) for r in present):
                values = set(_version_values(repo, by_rel[rel], index, entry).values())
                if len(values) == 1:
                    versions |= values
                pin = pin_of(entry["source"])
                if pin is not None:
                    pins.add(pin)
            for kind, differing, check in (
                ("version", versions, "local.parity-version"),
                ("source", pins, "local.parity-source"),
            ):
                if len(differing) > 1:
                    if policy.excepts(name, kind):
                        used.add((name, kind))
                    else:
                        findings.append(
                            Finding(
                                check,
                                Severity.ERROR,
                                present[0],
                                f"plugin {name!r} differs in {kind} across catalogs "
                                f"({', '.join(sorted(differing))}); align them, or record a "
                                f"{kind!r} exception with a reason",
                                rule="R10",
                            )
                        )
    for exception in policy.exceptions:
        if (exception.plugin, exception.kind) not in used:
            findings.append(
                Finding(
                    "policy.unused-exception",
                    Severity.WARNING,
                    POLICY_FILE,
                    f"exception for {exception.plugin!r} ({exception.kind}) matches no current "
                    "difference; remove it so it cannot hide a future one",
                    rule="R10",
                )
            )
    return findings
```

Append `check_versions` and `check_parity` to `LOCAL_CHECKS`.

Note on `test_source_pin_difference_between_catalogs`: local entries compare as `path:plugins/alpha` in both catalogs (the Claude string and the Codex local object normalise to the same pin), so only the changed remote SHA differs.

- [ ] **Step 4: Run to verify pass, then the whole suite**

Run: `uv run pytest tests/test_checks_versions.py -v && uv run pytest -q`
Expected: 9 passed; the full suite passes.

- [ ] **Step 5: Commit**

```bash
git add skills/plugin-marketplaces/scripts/mpcheck/checks_local.py tests/test_checks_versions.py
git commit -m "feat(validator): check version agreement and cross-catalog parity

🤖 Generated with Claude Code"
```

---

### Task 10: Local checks — pins, entry hooks, portable MCP (R4, Claude hooks gap)

**Files:**
- Modify: `skills/plugin-marketplaces/scripts/mpcheck/checks_local.py` (add `check_pins`, `check_entry_hooks`, `check_portable_mcp`)
- Test: `tests/test_checks_pins.py`

**Interfaces:**
- Produces: `check_pins` emitting `local.pin-missing`, `local.pin-malformed`, `local.pin-unpinnable` (errors, R4); `check_entry_hooks` emitting `local.entry-hooks-path` (error); `check_portable_mcp` emitting `local.portable-mcp-missing` (warning).

- [ ] **Step 1: Write the failing tests**

```python
from helpers import local_ids, read, remote, write

CLAUDE = ".claude-plugin/marketplace.json"
CODEX = ".agents/plugins/marketplace.json"


def set_both(root, index, **changes):
    for catalog in (CLAUDE, CODEX):
        data = read(root, catalog)
        data["plugins"][index].update(changes)
        write(root, catalog, data)


def test_git_source_without_sha(market):
    source = remote()
    del source["sha"]
    set_both(market, 1, source=source)
    assert local_ids(market) == ["local.pin-missing", "local.pin-missing"]


def test_short_sha(market):
    set_both(market, 1, source=remote(sha="abc1234"))
    assert local_ids(market) == ["local.pin-malformed", "local.pin-malformed"]


def test_npm_range_is_not_a_pin(market):
    set_both(market, 1, source={"source": "npm", "package": "@x/beta", "version": "^1.0.0"})
    assert local_ids(market) == ["local.pin-missing", "local.pin-missing"]


def test_npm_exact_version_passes(market):
    set_both(market, 1, source={"source": "npm", "package": "@x/beta", "version": "1.0.0"})
    assert local_ids(market) == []


def test_archive_without_sha256(market):
    (market / CODEX).unlink()
    write(market, "marketplace-policy.json", {"readers": ["claude-code"]})
    data = read(market, CLAUDE)
    data["plugins"][1]["source"] = {"source": "archive", "url": "https://example.com/b.zip"}
    write(market, CLAUDE, data)
    assert local_ids(market) == ["local.pin-missing"]


def test_command_source_is_unpinnable(market):
    (market / CODEX).unlink()
    write(market, "marketplace-policy.json", {"readers": ["claude-code"]})
    data = read(market, CLAUDE)
    data["plugins"][1]["source"] = {"source": "command", "command": "echo /tmp/x"}
    write(market, CLAUDE, data)
    assert local_ids(market) == ["local.pin-unpinnable"]


def test_entry_hooks_as_path(market):
    data = read(market, CLAUDE)
    data["plugins"][0]["hooks"] = "./hooks/hooks.json"
    write(market, CLAUDE, data)
    assert local_ids(market) == ["local.entry-hooks-path"]


def test_entry_hooks_inline_object_passes(market):
    data = read(market, CLAUDE)
    data["plugins"][0]["hooks"] = {"SessionStart": []}
    write(market, CLAUDE, data)
    assert local_ids(market) == []


def test_portable_plugin_with_only_dot_mcp(market):
    write(market, "plugins/alpha/.mcp.json", {"mcpServers": {"x": {"command": "uvx", "args": ["x"]}}})
    assert local_ids(market) == ["local.portable-mcp-missing"]
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/test_checks_pins.py -v`
Expected: FAIL — missing ids.

- [ ] **Step 3: Implement the three checks**

Add imports at the top of `checks_local.py`:

```python
import re

from mpcheck.readers import GIT_SOURCE_TYPES
```

Add before `LOCAL_CHECKS`:

```python
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")
EXACT_SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$")


def _pin_finding(check: str, catalog: Catalog, index: int, message: str) -> Finding:
    return Finding(check, Severity.ERROR, catalog.relpath, message, rule="R4",
                   pointer=f"/plugins/{index}/source")


def check_pins(repo: Repo, readers: dict[str, Reader], policy: Policy) -> list[Finding]:
    findings: list[Finding] = []
    for catalog in active_catalogs(repo, policy):
        for index, entry in catalog.entries:
            source = entry["source"]
            kind = source_type(source)
            name = entry["name"]
            if not isinstance(source, dict):
                continue
            if kind in GIT_SOURCE_TYPES:
                sha = source.get("sha")
                if sha is None:
                    findings.append(_pin_finding("local.pin-missing", catalog, index,
                        f"git source for {name!r} has no 'sha'; a moving ref ships whatever is pushed next"))
                elif not (isinstance(sha, str) and SHA_RE.fullmatch(sha)):
                    findings.append(_pin_finding("local.pin-malformed", catalog, index,
                        f"'sha' for {name!r} must be a full 40-character lowercase commit SHA"))
            elif kind == "archive":
                digest = source.get("sha256")
                if digest is None:
                    findings.append(_pin_finding("local.pin-missing", catalog, index,
                        f"archive source for {name!r} has no 'sha256'"))
                elif not (isinstance(digest, str) and SHA256_RE.fullmatch(digest)):
                    findings.append(_pin_finding("local.pin-malformed", catalog, index,
                        f"'sha256' for {name!r} must be 64 hex characters"))
            elif kind == "npm":
                version = source.get("version")
                if not (isinstance(version, str) and EXACT_SEMVER_RE.fullmatch(version)):
                    findings.append(_pin_finding("local.pin-missing", catalog, index,
                        f"npm source for {name!r} needs an exact 'version', not a range or dist-tag"))
            elif kind == "command":
                findings.append(_pin_finding("local.pin-unpinnable", catalog, index,
                    f"command source for {name!r} cannot be pinned and must not appear in a "
                    "published catalog"))
    return findings


def check_entry_hooks(repo: Repo, readers: dict[str, Reader], policy: Policy) -> list[Finding]:
    findings: list[Finding] = []
    for catalog in active_catalogs(repo, policy):
        hook_readers = [r for r in _readers_of(repo, readers, policy, catalog) if r.reads_entry_hooks]
        if not hook_readers:
            continue
        for index, entry in catalog.entries:
            if isinstance(entry.get("hooks"), (str, list)):
                findings.append(
                    Finding(
                        "local.entry-hooks-path",
                        Severity.ERROR,
                        catalog.relpath,
                        "entry 'hooks' must be an inline object; a path or array passes "
                        "`claude plugin validate` but the hooks never run",
                        pointer=f"/plugins/{index}/hooks",
                        source=hook_readers[0].reference,
                    )
                )
    return findings


def check_portable_mcp(repo: Repo, readers: dict[str, Reader], policy: Policy) -> list[Finding]:
    findings: list[Finding] = []
    for plugin in repo.plugins.values():
        directory = plugin.directory
        if (
            "plugin.json" in plugin.manifests
            and (directory / ".mcp.json").is_file()
            and not (directory / "mcp.json").is_file()
        ):
            findings.append(
                Finding(
                    "local.portable-mcp-missing",
                    Severity.WARNING,
                    (directory / ".mcp.json").relative_to(repo.root).as_posix(),
                    "portable readers load MCP servers only from mcp.json, with a transport "
                    "'type' on each server; these servers are invisible to them",
                    source="references/agent-plugins.md",
                )
            )
    return findings
```

Append `check_pins`, `check_entry_hooks`, `check_portable_mcp` to `LOCAL_CHECKS`.
Run `uv run ruff format skills/plugin-marketplaces/scripts/mpcheck/checks_local.py` to normalise the wrapped calls.

- [ ] **Step 4: Run to verify pass, then the whole suite**

Run: `uv run pytest tests/test_checks_pins.py -v && uv run pytest -q`
Expected: 9 passed; the full suite passes.

- [ ] **Step 5: Commit**

```bash
git add skills/plugin-marketplaces/scripts/mpcheck/checks_local.py tests/test_checks_pins.py
git commit -m "feat(validator): check source pins, entry hooks, and portable MCP placement

🤖 Generated with Claude Code"
```

---

### Task 11: Schema level — vendored Agent Plugins schemas and Claude's validator

**Files:**
- Create: `skills/plugin-marketplaces/scripts/schemas/agent-plugins/1.0.0/plugin.schema.json`, `.../1.0.0/mcp.schema.json`, `skills/plugin-marketplaces/scripts/schemas/SHA256SUMS`
- Create: `skills/plugin-marketplaces/scripts/mpcheck/checks_schema.py`
- Test: `tests/test_checks_schema.py`

**Interfaces:**
- Produces: `check_portable(repo: Repo) -> list[Finding]` emitting `schema.portable.unsupported-version`, `schema.portable.manifest` (warning when tolerated by the spec, error otherwise), `schema.portable.mcp`, `schema.portable.mcp-server`.
- Produces: `run_claude_validate(repo: Repo, runner: Runner = ..., which: Callable[[str], str | None] = shutil.which) -> tuple[list[Finding], Status, str]` emitting `schema.claude-validate.error`, `schema.claude-validate.warning`, `schema.claude-validate.crashed`; the `str` is a note for the status table.
- `Runner = Callable[[list[str]], subprocess.CompletedProcess[str]]`.

- [ ] **Step 1: Vendor the schemas and record their digests**

```bash
D=skills/plugin-marketplaces/scripts/schemas
mkdir -p $D/agent-plugins/1.0.0
for n in plugin mcp; do curl -sfo $D/agent-plugins/1.0.0/$n.schema.json https://agent-plugins.org/schemas/1.0.0/$n.schema.json; done
(cd $D && shasum -a 256 agent-plugins/1.0.0/*.json > SHA256SUMS && cat SHA256SUMS)
```

Expected: two lines; on 2026-09-27 the digests began `0a4aad95ce337878` (plugin) and `6539175bfcdf4308` (mcp).
If they differ, the upstream schema changed since the design; stop and report rather than proceeding.

- [ ] **Step 2: Write the failing tests**

```python
import json
import shutil
import subprocess
from pathlib import Path

import pytest
from helpers import AP_MCP_SCHEMA, AP_SCHEMA, write

from mpcheck.checks_schema import SCHEMAS_DIR, check_portable, run_claude_validate
from mpcheck.discover import discover
from mpcheck.model import Status
from mpcheck.readers import load_readers

READERS = load_readers()


def repo_of(root):
    return discover(root, READERS)[0]


def ids(findings):
    return sorted(f.check for f in findings)


def test_vendored_schemas_match_recorded_digests():
    import hashlib

    for line in (SCHEMAS_DIR.parent / "SHA256SUMS").read_text().splitlines():
        digest, name = line.split(maxsplit=1)
        assert hashlib.sha256((SCHEMAS_DIR.parent / name).read_bytes()).hexdigest() == digest


def test_clean_portable_manifest(market):
    assert check_portable(repo_of(market)) == []


def test_unknown_top_level_key_is_a_warning(market):
    write(market, "plugins/alpha/plugin.json", {"$schema": AP_SCHEMA, "name": "alpha", "version": "1.2.0", "bogus": 1})
    findings = check_portable(repo_of(market))
    assert [(f.check, f.severity) for f in findings] == [("schema.portable.manifest", "warning")]


def test_bad_name_is_an_error(market):
    write(market, "plugins/alpha/plugin.json", {"$schema": AP_SCHEMA, "name": "Alpha", "version": "1.2.0"})
    findings = check_portable(repo_of(market))
    assert [(f.check, f.severity, f.pointer) for f in findings] == [("schema.portable.manifest", "error", "/name")]


def test_unsupported_schema_version(market):
    write(market, "plugins/alpha/plugin.json", {"$schema": "https://agent-plugins.org/schemas/9.9.9/plugin.schema.json", "name": "alpha"})
    assert ids(check_portable(repo_of(market))) == ["schema.portable.unsupported-version"]


def test_invalid_server_is_skipped_not_fatal(market):
    write(market, "plugins/alpha/mcp.json", {"$schema": AP_MCP_SCHEMA, "mcpServers": {
        "good": {"type": "stdio", "command": "uvx"}, "bad": {"command": "uvx"}}})
    findings = check_portable(repo_of(market))
    assert [(f.check, f.pointer) for f in findings] == [("schema.portable.mcp-server", "/mcpServers/bad")]


def test_mcp_version_must_match_plugin(market):
    write(market, "plugins/alpha/mcp.json", {"$schema": "https://agent-plugins.org/schemas/1.1.0/mcp.schema.json", "mcpServers": {}})
    assert ids(check_portable(repo_of(market))) == ["schema.portable.mcp"]


def fake_runner(stdout, returncode=0):
    def run(argv):
        assert argv[:5] == ["claude", "plugin", "validate", "--strict", "--json"]
        return subprocess.CompletedProcess(argv, returncode, stdout=stdout, stderr="")
    return run


def test_claude_missing_is_skipped(market):
    findings, status, note = run_claude_validate(repo_of(market), which=lambda _: None)
    assert (findings, status) == ([], Status.SKIPPED)
    assert "not on PATH" in note


def test_claude_report_is_mapped(market):
    report = {"success": False, "manifest": {
        "file": str((market / ".claude-plugin/marketplace.json").resolve()),
        "errors": [{"path": "plugins.1.source", "message": "Invalid input"}],
        "warnings": [{"path": "plugins[0].x", "message": "Unknown field 'x'."}]},
        "contents": []}
    findings, status, _ = run_claude_validate(repo_of(market), runner=fake_runner(json.dumps(report), 1), which=lambda _: "/bin/claude")
    assert status == Status.PASSED
    errors = [f for f in findings if f.check == "schema.claude-validate.error"]
    assert errors and errors[0].file == ".claude-plugin/marketplace.json"
    assert errors[0].pointer == "plugins.1.source"
    assert any(f.check == "schema.claude-validate.warning" for f in findings)


def test_claude_garbage_is_inconclusive(market):
    findings, status, _ = run_claude_validate(repo_of(market), runner=fake_runner("not json", 2), which=lambda _: "/bin/claude")
    assert status == Status.INCONCLUSIVE
    assert "schema.claude-validate.crashed" in ids(findings)


@pytest.mark.skipif(shutil.which("claude") is None, reason="claude not installed")
def test_real_claude_catches_a_known_defect(market):
    from helpers import read
    data = read(market, ".claude-plugin/marketplace.json")
    data["plugins"][0]["source"] = "plugins/alpha"
    write(market, ".claude-plugin/marketplace.json", data)
    findings, status, _ = run_claude_validate(repo_of(market))
    assert status == Status.PASSED
    assert any(f.check == "schema.claude-validate.error" and "plugins.0.source" in f.pointer for f in findings)
```

`test_real_claude_catches_a_known_defect` is the known positive for the wrapper: it proves the real tool's output reaches the findings, so a clean result elsewhere is not a broken instrument.

- [ ] **Step 3: Run to verify failure**

Run: `uv run pytest tests/test_checks_schema.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'mpcheck.checks_schema'`.

- [ ] **Step 4: Implement `mpcheck/checks_schema.py`**

```python
"""Schema level: the vendored Agent Plugins schemas and Claude Code's own validator."""

from __future__ import annotations

import json
import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path

from jsonschema import Draft202012Validator

from mpcheck.discover import Repo
from mpcheck.jsonload import DuplicateKeyError, load_json
from mpcheck.model import Finding, Severity, Status

SCHEMAS_DIR = Path(__file__).resolve().parent.parent / "schemas" / "agent-plugins"
PORTABLE_REF = "references/agent-plugins.md"
CLAUDE_REF = "references/claude-code.md"

Runner = Callable[[list[str]], subprocess.CompletedProcess[str]]


def _default_runner(argv: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, capture_output=True, text=True, timeout=120, check=False)


def _schema(version: str, name: str) -> dict[str, object]:
    return json.loads((SCHEMAS_DIR / version / f"{name}.schema.json").read_text(encoding="utf-8"))


def _version_of(schema_url: object) -> str | None:
    if not isinstance(schema_url, str):
        return None
    parts = schema_url.rstrip("/").split("/")
    return parts[-2] if len(parts) >= 2 else None


def _pointer(path: list[object]) -> str:
    return "/" + "/".join(str(part) for part in path) if path else ""


def _check_mcp(directory: Path, prefix: str, version: str) -> list[Finding]:
    path = directory / "mcp.json"
    if not path.is_file():
        return []
    rel = f"{prefix}/mcp.json"
    try:
        data = load_json(path)
    except (DuplicateKeyError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        return [Finding("schema.portable.mcp", Severity.ERROR, rel,
                        f"MCP disabled by conforming clients: not valid JSON: {exc}", source=PORTABLE_REF)]
    schema_url = data.get("$schema") if isinstance(data, dict) else None
    if _version_of(schema_url) != version:
        return [Finding("schema.portable.mcp", Severity.ERROR, rel,
                        "MCP disabled by conforming clients: mcp.json $schema must use the same "
                        f"spec version as plugin.json ({version})", pointer="/$schema", source=PORTABLE_REF)]
    findings: list[Finding] = []
    for error in Draft202012Validator(_schema(version, "mcp")).iter_errors(data):
        path_parts = list(error.absolute_path)
        if len(path_parts) >= 2 and path_parts[0] == "mcpServers":
            findings.append(Finding("schema.portable.mcp-server", Severity.ERROR, rel,
                                    f"server {path_parts[1]!r} skipped by conforming clients: {error.message}",
                                    pointer=_pointer(path_parts[:2]), source=PORTABLE_REF))
        else:
            findings.append(Finding("schema.portable.mcp", Severity.ERROR, rel,
                                    f"MCP disabled by conforming clients: {error.message}",
                                    pointer=_pointer(path_parts), source=PORTABLE_REF))
    return findings


def check_portable(repo: Repo) -> list[Finding]:
    findings: list[Finding] = []
    vendored = sorted(p.name for p in SCHEMAS_DIR.iterdir() if p.is_dir())
    for plugin in repo.plugins.values():
        manifest = plugin.manifests.get("plugin.json")
        if manifest is None:
            continue
        prefix = plugin.directory.relative_to(repo.root).as_posix()
        rel = f"{prefix}/plugin.json"
        version = _version_of(manifest.get("$schema"))
        if version not in vendored:
            findings.append(Finding("schema.portable.unsupported-version", Severity.ERROR, rel,
                                    f"unsupported Agent Plugins schema {manifest.get('$schema')!r}; "
                                    f"vendored versions: {', '.join(vendored)}",
                                    pointer="/$schema", source=PORTABLE_REF))
            continue
        assert version is not None
        for error in Draft202012Validator(_schema(version, "plugin")).iter_errors(manifest):
            path_parts = list(error.absolute_path)
            tolerated = (error.validator == "additionalProperties" and not path_parts) or (
                path_parts == ["extensions"] and error.validator == "type"
            )
            prefix_text = ("reported and ignored by conforming clients: " if tolerated
                           else "plugin rejected by conforming clients: ")
            findings.append(Finding("schema.portable.manifest",
                                    Severity.WARNING if tolerated else Severity.ERROR, rel,
                                    prefix_text + error.message, pointer=_pointer(path_parts),
                                    source=PORTABLE_REF))
        findings.extend(_check_mcp(plugin.directory, prefix, version))
    return findings


def _rel(root: Path, path: Path) -> str:
    resolved = path.resolve()
    return resolved.relative_to(root).as_posix() if resolved.is_relative_to(root) else str(path)


def run_claude_validate(
    repo: Repo,
    runner: Runner = _default_runner,
    which: Callable[[str], str | None] = shutil.which,
) -> tuple[list[Finding], Status, str]:
    targets: list[Path] = []
    if (repo.root / ".claude-plugin/marketplace.json").is_file():
        targets.append(repo.root)
    targets += [p.directory for p in repo.plugins.values() if ".claude-plugin/plugin.json" in p.manifests]
    if not targets:
        return [], Status.SKIPPED, "no Claude Code catalog or plugin manifest"
    if which("claude") is None:
        return [], Status.SKIPPED, "claude not on PATH"
    findings: list[Finding] = []
    status = Status.PASSED
    for target in targets:
        try:
            proc = runner(["claude", "plugin", "validate", "--strict", "--json", str(target)])
            report = json.loads(proc.stdout)
            if not isinstance(report, dict):
                raise ValueError("report is not a JSON object")
        except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError, ValueError) as exc:
            findings.append(Finding("schema.claude-validate.crashed", Severity.ERROR, _rel(repo.root, target),
                                    f"claude plugin validate produced no report: {exc}", source=CLAUDE_REF))
            status = Status.INCONCLUSIVE
            continue
        items = [report.get("manifest") or {}, *(report.get("contents") or [])]
        for item in items:
            if not isinstance(item, dict):
                continue
            file = _rel(repo.root, Path(str(item.get("file", target))))
            for key, severity, suffix in (("errors", Severity.ERROR, "error"),
                                          ("warnings", Severity.WARNING, "warning")):
                for issue in item.get(key) or []:
                    findings.append(Finding(f"schema.claude-validate.{suffix}", severity, file,
                                            str(issue.get("message", "")),
                                            pointer=str(issue.get("path", "")), source=CLAUDE_REF))
    return findings, status, ""
```

Run `uv run ruff format skills/plugin-marketplaces/scripts/mpcheck/checks_schema.py`.

- [ ] **Step 5: Run to verify pass**

Run: `uv run pytest tests/test_checks_schema.py -v`
Expected: 11 passed (10 if `claude` is not installed, with 1 skipped).

- [ ] **Step 6: Commit**

```bash
git add skills/plugin-marketplaces/scripts/schemas skills/plugin-marketplaces/scripts/mpcheck/checks_schema.py tests/test_checks_schema.py
git commit -m "feat(validator): add schema level with vendored Agent Plugins schemas and claude validate

🤖 Generated with Claude Code"
```

---

### Task 12: Report, CLI, and the uv script entry point

**Files:**
- Create: `skills/plugin-marketplaces/scripts/mpcheck/run.py`, `skills/plugin-marketplaces/scripts/mpcheck/report.py`, `skills/plugin-marketplaces/scripts/check_marketplace.py`
- Test: `tests/test_cli.py`

**Interfaces:**
- Consumes: everything above.
- Produces: `mpcheck.run.GROUPS: tuple[str, ...]`, `mpcheck.run.Report(findings: list[Finding], statuses: dict[str, tuple[Status, str]])` with `exit_code(fail_on: Severity) -> int`, and `run_checks(root: Path, policy_path: Path | None = None, use_claude: bool = True, runner: Runner | None = None) -> Report`.
- Produces: `mpcheck.report.render_text(report) -> str`, `render_json(report) -> str`.
- Produces: `check_marketplace.main(argv: list[str] | None = None) -> int`; exit 0 no failing findings, 1 failing findings, 2 validator failure.

- [ ] **Step 1: Write the failing tests**

```python
import json
import subprocess
import sys
from pathlib import Path

from helpers import read, write

import check_marketplace
from mpcheck.model import Severity, Status
from mpcheck.run import run_checks

SCRIPT = Path(check_marketplace.__file__)


def test_clean_market_exits_zero(market, capsys):
    assert check_marketplace.main([str(market), "--no-claude"]) == 0
    out = capsys.readouterr().out
    assert "No findings." in out
    assert "schema.claude-validate" in out and "skipped" in out


def test_defect_exits_one_and_json_is_parseable(market, capsys):
    data = read(market, ".claude-plugin/marketplace.json")
    data["plugins"][0]["source"] = "plugins/alpha"
    write(market, ".claude-plugin/marketplace.json", data)
    assert check_marketplace.main([str(market), "--no-claude", "--format", "json"]) == 1
    report = json.loads(capsys.readouterr().out)
    assert report["statuses"]["local"]["status"] == "failed"
    assert any(f["check"] == "local.path-prefix" and f["rule"] == "R3" for f in report["findings"])


def test_warnings_fail_only_on_request(market):
    write(market, "marketplace-policy.json", {"readers": ["codex"]})
    assert check_marketplace.main([str(market), "--no-claude"]) == 0
    assert check_marketplace.main([str(market), "--no-claude", "--fail-on", "warning"]) == 1


def test_unimplemented_levels_are_skipped_not_passed(market):
    statuses = run_checks(market, use_claude=False).statuses
    for group in ("remote", "discovery", "package-load", "schema.claude-validate"):
        assert statuses[group][0] == Status.SKIPPED


def test_no_portable_manifest_means_portable_skipped(market):
    (market / "plugins/alpha/plugin.json").unlink()
    assert run_checks(market, use_claude=False).statuses["schema.portable"][0] == Status.SKIPPED


def test_empty_repo_fails(tmp_path):
    report = run_checks(tmp_path, use_claude=False)
    assert report.exit_code(Severity.ERROR) == 1
    assert report.statuses["schema.parse"][0] == Status.FAILED


def test_validator_crash_exits_two(market, monkeypatch, capsys):
    def boom(*args, **kwargs):
        raise RuntimeError("boom")
    monkeypatch.setattr(check_marketplace, "run_checks", boom)
    assert check_marketplace.main([str(market)]) == 2
    assert "validator failure" in capsys.readouterr().err


def test_runs_as_a_uv_script(market):
    proc = subprocess.run(
        ["uv", "run", "--script", str(SCRIPT), str(market), "--no-claude"],
        capture_output=True, text=True, timeout=300, check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert "No findings." in proc.stdout
```

`test_runs_as_a_uv_script` proves the PEP 723 header and sibling-package import work outside pytest's `pythonpath`.

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/test_cli.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'check_marketplace'`.

- [ ] **Step 3: Implement `mpcheck/run.py`**

```python
"""Run the requested checks and build a report."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from mpcheck.checks_local import LOCAL_CHECKS
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
        failing = {Severity.ERROR} if fail_on == Severity.ERROR else {Severity.ERROR, Severity.WARNING}
        return 1 if any(f.severity in failing for f in self.findings) else 0


def run_checks(
    root: Path,
    policy_path: Path | None = None,
    use_claude: bool = True,
    runner: Runner | None = None,
) -> Report:
    readers = load_readers()
    repo, findings = discover(root, readers)
    policy, policy_findings = load_policy(repo.root, policy_path, set(readers), repo.reader_catalog)
    findings += policy_findings
    for check in LOCAL_CHECKS:
        findings += check(repo, readers, policy)
    findings += check_portable(repo)
    if use_claude:
        claude_findings, claude_status, claude_note = (
            run_claude_validate(repo, runner) if runner else run_claude_validate(repo)
        )
        findings += claude_findings
    else:
        claude_status, claude_note = Status.SKIPPED, "disabled with --no-claude"
    statuses: dict[str, tuple[Status, str]] = {}
    for group in GROUPS:
        failed = any(f.group == group and f.severity == Severity.ERROR for f in findings)
        statuses[group] = (Status.FAILED if failed else Status.PASSED, "")
    if claude_status in (Status.SKIPPED, Status.INCONCLUSIVE):
        statuses["schema.claude-validate"] = (claude_status, claude_note)
    if not any("plugin.json" in p.manifests for p in repo.plugins.values()):
        statuses["schema.portable"] = (Status.SKIPPED, "no portable manifests")
    for group in NOT_IMPLEMENTED:
        statuses[group] = (Status.SKIPPED, "not implemented in this version")
    return Report(findings, statuses)
```

- [ ] **Step 4: Implement `mpcheck/report.py`**

```python
"""Render a report as text or JSON."""

from __future__ import annotations

import json

from mpcheck.model import Severity
from mpcheck.run import Report

ORDER = {Severity.ERROR: 0, Severity.WARNING: 1, Severity.INFO: 2}


def render_json(report: Report) -> str:
    return json.dumps(
        {
            "statuses": {g: {"status": s, "note": n} for g, (s, n) in report.statuses.items()},
            "findings": [f.to_dict() for f in report.findings],
        },
        indent=2,
    )


def render_text(report: Report) -> str:
    lines = ["Check levels:"]
    for group, (status, note) in report.statuses.items():
        lines.append(f"  {group:24} {status}" + (f"  ({note})" if note else ""))
    lines.append("")
    if not report.findings:
        lines.append("No findings.")
    for f in sorted(report.findings, key=lambda f: (ORDER[f.severity], f.file, f.pointer)):
        where = f.file + (f"#{f.pointer}" if f.pointer else "")
        rule = f" [{f.rule}]" if f.rule else ""
        lines.append(f"{f.severity.upper():7} {where}  {f.check}{rule}: {f.message}")
    return "\n".join(lines)
```

- [ ] **Step 5: Implement `check_marketplace.py`**

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["jsonschema>=4.23"]
# ///
"""Validate a user-hosted plugin marketplace (see references/validation.md)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from mpcheck.model import Severity
from mpcheck.report import render_json, render_text
from mpcheck.run import run_checks


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".", type=Path, help="marketplace root")
    parser.add_argument("--policy", type=Path, help="policy file (default: marketplace-policy.json)")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--fail-on", choices=("error", "warning"), default="error")
    parser.add_argument("--no-claude", action="store_true", help="skip `claude plugin validate`")
    args = parser.parse_args(argv)
    try:
        report = run_checks(args.root, policy_path=args.policy, use_claude=not args.no_claude)
    except Exception as exc:  # noqa: BLE001 - exit 2 is the validator-failure contract
        print(f"check_marketplace: validator failure: {exc!r}", file=sys.stderr)
        return 2
    print(render_json(report) if args.format == "json" else render_text(report))
    return report.exit_code(Severity(args.fail_on))


if __name__ == "__main__":
    sys.exit(main())
```

```bash
chmod +x skills/plugin-marketplaces/scripts/check_marketplace.py
```

- [ ] **Step 6: Run to verify pass, then every hook**

Run: `uv run pytest -q && prek run --all-files`
Expected: all tests pass; all hooks pass (fix any ruff or ty findings in the new code, then re-run).

- [ ] **Step 7: Commit**

```bash
git add skills/plugin-marketplaces/scripts/check_marketplace.py skills/plugin-marketplaces/scripts/mpcheck/run.py skills/plugin-marketplaces/scripts/mpcheck/report.py tests/test_cli.py
git commit -m "feat(validator): add report rendering and the check_marketplace CLI

🤖 Generated with Claude Code"
```

---

### Task 13: Copilot CLI and VS Code reader entries (conditional on Task 1)

Do this task only for a tool whose section in `docs/research/2026-09-27-phase0-probes.md` records a catalog-discovery `pass`.
If neither passed, skip to Task 14 and record the skip in the Task 14 calibration note.

**Files:**
- Modify: `skills/plugin-marketplaces/scripts/readers.json`
- Test: `tests/test_readers.py`, `tests/test_checks_paths.py`

**Interfaces:**
- Produces: reader ids `"copilot-cli"` and/or `"vscode"` with the same fields as Task 4.

Values below come from `docs/research/2026-09-27-other-harnesses.md`; any field the probe contradicted takes the probe's value, and `path_requires_dot_slash` takes the probe's observed behaviour for the `control-bare` entry.
Leave `marketplace_name_pattern` and `entry_name_pattern` as `null` unless the probe or a cited source establishes the rule.

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_readers.py` (keep only the lines for tools that passed):

```python
def test_copilot_reader():
    copilot = load_readers()["copilot-cli"]
    assert copilot.catalog_paths[-1] == ".claude-plugin/marketplace.json"
    assert copilot.source_types == {"path", "github", "url"}


def test_vscode_reader():
    vscode = load_readers()["vscode"]
    assert vscode.catalog_paths[-1] == ".claude-plugin/marketplace.json"
    assert {"git-subdir", "npm", "pip"} <= vscode.source_types
```

Add to `tests/test_checks_paths.py` (Copilot passed):

```python
def test_git_subdir_rejected_for_copilot(market):
    write(market, "marketplace-policy.json", {"readers": ["claude-code", "codex", "copilot-cli"]})
    set_entry(market, CLAUDE, 1, source={"source": "git-subdir", "url": "https://github.com/o/r.git", "path": "p", "sha": "a" * 40})
    assert "local.source-type" in local_ids(market)
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/test_readers.py tests/test_checks_paths.py -v`
Expected: FAIL with `KeyError: 'copilot-cli'` (and/or `'vscode'`).

- [ ] **Step 3: Add the entries to `readers.json`**

```json
  "copilot-cli": {
    "reference": "references/copilot-cli.md",
    "catalog_paths": ["marketplace.json", ".plugin/marketplace.json", ".github/plugin/marketplace.json", ".claude-plugin/marketplace.json"],
    "source_types": ["path", "github", "url"],
    "path_requires_dot_slash": true,
    "marketplace_name_pattern": null,
    "entry_name_pattern": null,
    "reads_entry_hooks": false
  },
  "vscode": {
    "reference": "references/vscode.md",
    "catalog_paths": ["marketplace.json", ".plugin/marketplace.json", ".github/plugin/marketplace.json", ".claude-plugin/marketplace.json"],
    "source_types": ["path", "github", "url", "git-subdir", "npm", "pip"],
    "path_requires_dot_slash": true,
    "marketplace_name_pattern": null,
    "entry_name_pattern": null,
    "reads_entry_hooks": false
  }
```

Set each `path_requires_dot_slash` to the value the probe observed.

- [ ] **Step 4: Run to verify pass, then the whole suite**

Run: `uv run pytest -q`
Expected: all pass; the clean `market` fixture still yields no findings because its policy declares only `claude-code` and `codex`.

- [ ] **Step 5: Commit**

```bash
git add skills/plugin-marketplaces/scripts/readers.json tests/test_readers.py tests/test_checks_paths.py
git commit -m "feat(validator): add probe-verified reader facts for Copilot CLI and VS Code

🤖 Generated with Claude Code"
```

---

### Task 14: Calibration on real marketplaces

**Files:**
- Create: `docs/calibration/2026-09-27-plan-1.md`, `docs/calibration/briandconnelly-plugins.json`, `docs/calibration/data-reasoning.json`

- [ ] **Step 1: Fetch the calibration repositories at pinned commits**

```bash
export CAL=$(mktemp -d)
gh repo clone briandconnelly/briandconnelly-plugins "$CAL/bcp" -- -q
gh repo clone briandconnelly/data-reasoning "$CAL/dr" -- -q
git -C "$CAL/bcp" rev-parse HEAD
git -C "$CAL/dr" rev-parse HEAD
```

Record both SHAs for the note.

- [ ] **Step 2: Run the validator, with Claude's validator enabled, and keep the raw output**

```bash
S=skills/plugin-marketplaces/scripts/check_marketplace.py
uv run --script $S "$CAL/bcp" --format json > docs/calibration/briandconnelly-plugins.json; echo "bcp exit=$?"
uv run --script $S "$CAL/dr" --format json > docs/calibration/data-reasoning.json; echo "dr exit=$?"
jq -r '.findings | group_by(.check) | map("\(.[0].check)\t\(length)") | .[]' docs/calibration/briandconnelly-plugins.json
jq -r '.findings | group_by(.check) | map("\(.[0].check)\t\(length)") | .[]' docs/calibration/data-reasoning.json
jq '.statuses' docs/calibration/briandconnelly-plugins.json
```

- [ ] **Step 3: Check the known positive**

The design expected `local.parity-membership` findings for `briandconnelly-plugins` (11 Claude entries versus 9 Codex entries on 2026-09-27).

```bash
jq '[.findings[] | select(.check == "local.parity-membership")] | length' docs/calibration/briandconnelly-plugins.json
jq '[.plugins[].name] | length' "$CAL/bcp/.claude-plugin/marketplace.json" "$CAL/bcp/.agents/plugins/marketplace.json"
```

Expected: the parity count equals the number of names present in one catalog but not the other.
If it is zero while the entry counts differ, the instrument is broken; stop and debug with superpowers:systematic-debugging before writing the note.

- [ ] **Step 4: Write the calibration note**

Create `docs/calibration/2026-09-27-plan-1.md` (one sentence per line) with: the validator commit (`git rev-parse HEAD`), `claude --version`, the two calibration repo SHAs, the per-check counts pasted from Step 2's `jq` output (not retyped), the status table, the known-positive result from Step 3, and for each distinct check id a one-line verdict: `true positive`, `false positive`, or `needs owner judgement`, with the reason.
False positives become new failing tests and fixes in a follow-up commit before this plan is marked complete.
If Task 13 was skipped for a tool, say so here with the reason recorded in the phase-0 record.

- [ ] **Step 5: Clean up and commit**

```bash
rm -rf "$CAL"
git add docs/calibration/2026-09-27-plan-1.md docs/calibration/briandconnelly-plugins.json docs/calibration/data-reasoning.json
git commit -m "docs(calibration): run the offline validator on two real marketplaces

🤖 Generated with Claude Code"
```
