"""Shared test configuration."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _isolate_git_env(monkeypatch: pytest.MonkeyPatch) -> None:
    # prek runs hooks under `git commit`; an inherited GIT_INDEX_FILE lets any git
    # subprocess started by a test rewrite the real index.
    for name in ("GIT_DIR", "GIT_INDEX_FILE", "GIT_WORK_TREE"):
        monkeypatch.delenv(name, raising=False)
