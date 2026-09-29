"""The remote level (spec §8 level 3): pinned sources exist upstream and match their pins.

Git sources are checked against real local repositories served over file://, so the tests
need no network; npm and archive sources go through an injected fetcher.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest
from helpers import write
from mpcheck.model import Severity, Status
from mpcheck.remote import FetchError, git_url
from mpcheck.run import run_checks

GIT_ENV = {"GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": "/dev/null"}


def git(cwd: Path, *args: str) -> str:
    done = subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
        env={"PATH": "/usr/bin:/bin:/opt/homebrew/bin", **GIT_ENV},
    )
    return done.stdout.strip()


@pytest.fixture
def upstream(tmp_path: Path) -> dict[str, str]:
    """A bare repository: `beta` at the root and `gamma` under plugins/gamma.

    Commit one carries the annotated tag v1.0.0; commit two moves `main` on.
    """
    src = tmp_path / "src"
    write(src, ".claude-plugin/plugin.json", {"name": "beta", "version": "1.0.0"})
    write(src, "plugins/gamma/.claude-plugin/plugin.json", {"name": "gamma", "version": "2.0.0"})
    git(src, "init", "-q", "-b", "main")
    git(src, "add", "-A")
    git(src, "commit", "-qm", "one")
    one = git(src, "rev-parse", "HEAD")
    # annotated, as release tags usually are: the tag object differs from the commit it names
    git(src, "tag", "-a", "v1.0.0", "-m", "v1.0.0")
    write(src, "README.md", "two\n")
    git(src, "add", "-A")
    git(src, "commit", "-qm", "two")
    two = git(src, "rev-parse", "HEAD")
    bare = tmp_path / "remote" / "beta.git"
    bare.parent.mkdir()
    git(tmp_path, "clone", "-q", "--bare", str(src), str(bare))
    return {"url": bare.as_uri(), "one": one, "two": two, "dir": str(bare.parent)}


def catalog(root: Path, *entries: dict[str, object]) -> Path:
    write(root, "marketplace-policy.json", {"readers": ["claude-code"]})
    write(
        root,
        ".claude-plugin/marketplace.json",
        {"name": "demo", "owner": {"name": "T"}, "plugins": list(entries)},
    )
    return root


def url_entry(name: str, url: str, sha: str, **extra: object) -> dict[str, object]:
    source: dict[str, object] = {"source": "url", "url": url, "sha": sha}
    source.update({k: v for k, v in extra.items() if k in ("ref", "path")})
    if "path" in extra:
        source["source"] = "git-subdir"
    entry: dict[str, object] = {"name": name, "source": source, "description": name}
    if "version" in extra:
        entry["version"] = extra["version"]
    return entry


def remote(root: Path, fetch=None) -> tuple[Status, str, dict[str, list[str]]]:
    report = run_checks(root, use_claude=False, remote=True, fetch=fetch)
    status, note = report.statuses["remote"]
    found: dict[str, list[str]] = {}
    for f in report.findings:
        if f.group == "remote":
            found.setdefault(f.check, []).append(f.severity.value)
    return status, note, found


# ---- git


def test_a_reachable_pin_with_matching_ref_name_and_version_passes(tmp_path, upstream):
    root = catalog(
        tmp_path / "m",
        url_entry("beta", upstream["url"], upstream["one"], ref="v1.0.0", version="1.0.0"),
    )
    status, note, found = remote(root)
    assert (status, found) == (Status.PASSED, {})
    assert "1 source" in note


def test_a_ref_that_moved_or_vanished_is_informational(tmp_path, upstream):
    moved = catalog(tmp_path / "a", url_entry("beta", upstream["url"], upstream["one"], ref="main"))
    gone = catalog(
        tmp_path / "b", url_entry("beta", upstream["url"], upstream["one"], ref="v9.9.9")
    )
    assert remote(moved)[0::2] == (Status.PASSED, {"remote.ref-moved": ["info"]})
    assert remote(gone)[0::2] == (Status.PASSED, {"remote.ref-missing": ["info"]})


def test_an_unreachable_repository_is_inconclusive_not_failed(tmp_path, upstream):
    missing = Path(upstream["dir"]) / "nope.git"
    root = catalog(tmp_path / "m", url_entry("beta", missing.as_uri(), upstream["one"]))
    status, note, found = remote(root)
    assert status == Status.INCONCLUSIVE
    assert found == {"remote.inconclusive": ["warning"]}
    assert "inconclusive" in note


def test_an_unknown_commit_on_a_reachable_host_is_inconclusive(tmp_path, upstream):
    # a host that refuses fetch-by-SHA answers exactly like one that lacks the commit
    root = catalog(tmp_path / "m", url_entry("beta", upstream["url"], "0" * 40))
    status, _, found = remote(root)
    assert status == Status.INCONCLUSIVE and "remote.inconclusive" in found


def test_a_git_subdir_path_missing_at_the_pin_fails(tmp_path, upstream):
    root = catalog(
        tmp_path / "m",
        url_entry("gamma", upstream["url"], upstream["one"], path="plugins/gama"),
    )
    status, _, found = remote(root)
    assert status == Status.FAILED and found["remote.path-missing"] == ["error"]


def test_the_manifest_at_the_pin_must_match_the_entry_name_and_version(tmp_path, upstream):
    root = catalog(
        tmp_path / "m",
        url_entry("gamma", upstream["url"], upstream["one"], path="plugins/gamma", version="2.0.0"),
        url_entry("gama", upstream["url"] + "/", upstream["one"], path="plugins/gamma"),
        url_entry("beta", upstream["url"] + "//", upstream["one"], version="1.1.0"),
    )
    report = run_checks(root, use_claude=False, remote=True)
    by_check = {f.check: f for f in report.findings if f.group == "remote"}
    assert by_check["remote.name-mismatch"].rule == "R8"
    assert "gama" in by_check["remote.name-mismatch"].message
    assert by_check["remote.version-mismatch"].rule == "R6"
    assert "1.1.0" in by_check["remote.version-mismatch"].message
    assert report.statuses["remote"][0] == Status.FAILED


def test_one_source_in_two_catalogs_is_fetched_once(tmp_path, upstream, monkeypatch):
    root = catalog(tmp_path / "m", url_entry("beta", upstream["url"], upstream["one"]))
    write(root, "marketplace-policy.json", {"readers": ["claude-code", "codex"]})
    codex_entry = url_entry("beta", upstream["url"], upstream["one"])
    codex_entry.update(policy={"installation": "AVAILABLE", "authentication": "ON_INSTALL"})
    write(root, ".agents/plugins/marketplace.json", {"name": "demo", "plugins": [codex_entry]})
    fetches: list[list[str]] = []
    real_run = subprocess.run

    def counting(argv, *args, **kwargs):
        if argv[:1] == ["git"] and "fetch" in argv:
            fetches.append(argv)
        return real_run(argv, *args, **kwargs)

    monkeypatch.setattr(subprocess, "run", counting)
    status, note, _ = remote(root)
    assert status == Status.PASSED and len(fetches) == 1 and "1 source" in note


def test_git_uses_the_callers_config_so_a_local_mirror_works(tmp_path, upstream, monkeypatch):
    # scenario 5's arms rewrite github.com to a local mirror in a throwaway GIT_CONFIG_GLOBAL;
    # the validator must keep that configuration and never wait for a credential prompt
    config = tmp_path / "gitconfig"
    config.write_text(
        f'[url "{Path(upstream["dir"]).as_uri()}/"]\n\tinsteadOf = https://github.com/acme/\n',
        encoding="utf-8",
    )
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(config))
    entry: dict[str, object] = {
        "name": "beta",
        "source": {
            "source": "github",
            "repo": "acme/beta",
            "ref": "v1.0.0",
            "sha": upstream["one"],
        },
        "description": "b",
    }
    status, _, found = remote(catalog(tmp_path / "m", entry))
    assert (status, found) == (Status.PASSED, {})


def test_github_sources_become_https_urls():
    assert git_url({"source": "github", "repo": "o/r"}) == "https://github.com/o/r.git"
    assert git_url({"source": "url", "url": "git@host:o/r.git"}) == "git@host:o/r.git"


# ---- npm and archive


class Fetcher:
    def __init__(self, pages: dict[str, bytes | int]) -> None:
        self.pages = pages
        self.seen: list[str] = []

    def __call__(self, url: str) -> bytes:
        self.seen.append(url)
        page = self.pages.get(url, "network")
        if page == "network":
            raise FetchError(None, "connection refused")
        if isinstance(page, int):
            raise FetchError(page, f"HTTP {page}")
        return page


NPM = "https://registry.npmjs.org"


def npm_entry(version: str, registry: str | None = None) -> dict[str, object]:
    source: dict[str, object] = {"source": "npm", "package": "@acme/fmt", "version": version}
    if registry:
        source["registry"] = registry
    return {"name": "fmt", "source": source, "description": "f"}


@pytest.mark.parametrize(
    ("pages", "status", "checks"),
    [
        ({f"{NPM}/@acme%2ffmt/1.2.0": b"{}"}, Status.PASSED, {}),
        (
            {f"{NPM}/@acme%2ffmt/1.2.0": 404, f"{NPM}/@acme%2ffmt": json.dumps({"versions": {"1.1.0": {}}}).encode()},
            Status.FAILED,
            {"remote.npm-version-missing": ["error"]},
        ),
        (
            {f"{NPM}/@acme%2ffmt/1.2.0": 404, f"{NPM}/@acme%2ffmt": 404},
            Status.INCONCLUSIVE,
            {"remote.inconclusive": ["warning"]},
        ),
        ({}, Status.INCONCLUSIVE, {"remote.inconclusive": ["warning"]}),
    ],
)  # fmt: skip
def test_npm_versions(tmp_path, pages, status, checks):
    got, _, found = remote(catalog(tmp_path / "m", npm_entry("1.2.0")), Fetcher(pages))
    assert (got, found) == (status, checks)


def test_npm_uses_the_entrys_registry(tmp_path):
    fetch = Fetcher({"https://npm.example.com/@acme%2ffmt/1.2.0": b"{}"})
    status, _, _ = remote(
        catalog(tmp_path / "m", npm_entry("1.2.0", "https://npm.example.com/")), fetch
    )
    assert status == Status.PASSED and fetch.seen == ["https://npm.example.com/@acme%2ffmt/1.2.0"]


def archive_entry(url: str, digest: str) -> dict[str, object]:
    return {
        "name": "zip",
        "source": {"source": "archive", "url": url, "sha256": digest},
        "description": "z",
    }


def test_archives_are_checked_against_their_sha256(tmp_path):
    body = b"archive bytes"
    good = hashlib.sha256(body).hexdigest()
    url = "https://example.com/p.zip"
    ok, _, _ = remote(catalog(tmp_path / "a", archive_entry(url, good)), Fetcher({url: body}))
    bad, _, found = remote(
        catalog(tmp_path / "b", archive_entry(url, "f" * 64)), Fetcher({url: body})
    )
    gone, _, _ = remote(catalog(tmp_path / "c", archive_entry(url, good)), Fetcher({}))
    assert ok == Status.PASSED
    assert bad == Status.FAILED and found == {"remote.archive-digest-mismatch": ["error"]}
    assert gone == Status.INCONCLUSIVE


# ---- when the level does not run


def test_remote_is_skipped_unless_requested_or_when_nothing_is_remote(tmp_path, market):
    statuses = run_checks(market, use_claude=False).statuses
    assert statuses["remote"] == (Status.SKIPPED, "not requested; run with --remote")
    root = catalog(tmp_path / "m", {"name": "a", "source": "./a", "description": "a"})
    write(root, "a/.claude-plugin/plugin.json", {"name": "a"})
    status, note, _ = remote(root)
    assert status == Status.SKIPPED and "no remote source" in note


def test_remote_findings_never_make_an_inconclusive_level_pass(tmp_path, upstream):
    missing = Path(upstream["dir"]) / "nope.git"
    root = catalog(
        tmp_path / "m",
        url_entry("beta", upstream["url"], upstream["one"]),
        url_entry("beta2", missing.as_uri(), upstream["one"]),
    )
    status, note, _ = remote(root)
    assert status == Status.INCONCLUSIVE and "1 passed" in note and "1 inconclusive" in note


def test_severity_of_inconclusive_is_a_warning(tmp_path, upstream):
    missing = Path(upstream["dir"]) / "nope.git"
    report = run_checks(
        catalog(tmp_path / "m", url_entry("beta", missing.as_uri(), upstream["one"])),
        use_claude=False,
        remote=True,
    )
    (finding,) = [f for f in report.findings if f.group == "remote"]
    assert finding.severity == Severity.WARNING and finding.rule == "R12"


def unpinned(name: str, url: str, ref: str | None) -> dict[str, object]:
    source: dict[str, object] = {"source": "url", "url": url}
    if ref:
        source["ref"] = ref
    return {"name": name, "source": source, "description": name}


def test_an_unpinned_source_is_checked_for_the_ref_it_installs(tmp_path, upstream):
    # a declared channel (R4) installs whatever its ref names: data-reasoning's `release`
    # branch was reported inconclusive on the first calibration run, which said nothing useful
    live = catalog(tmp_path / "a", unpinned("beta", upstream["url"], "main"))
    gone = catalog(tmp_path / "b", unpinned("beta", upstream["url"], "release"))
    head = catalog(tmp_path / "c", unpinned("beta", upstream["url"], None))
    down = catalog(
        tmp_path / "d", unpinned("beta", (Path(upstream["dir"]) / "x.git").as_uri(), "main")
    )
    assert remote(live)[0::2] == (Status.PASSED, {})
    assert remote(gone)[0::2] == (Status.FAILED, {"remote.unpinned-ref-missing": ["error"]})
    assert remote(head)[0::2] == (Status.PASSED, {})
    assert remote(down)[0] == Status.INCONCLUSIVE


def test_git_never_waits_for_a_password_or_passphrase(monkeypatch):
    # GIT_TERMINAL_PROMPT stops https prompts only; ssh must run in batch mode unless the
    # caller already chose an ssh command
    import mpcheck.remote as remote_module

    seen: dict[str, str] = {}

    def fake_run(argv, **kwargs):
        seen.update(kwargs["env"])
        return subprocess.CompletedProcess(argv, 0, "", "")

    monkeypatch.delenv("GIT_SSH_COMMAND", raising=False)
    monkeypatch.setattr(subprocess, "run", fake_run)
    remote_module.git("ls-remote", "git@example.com:o/r.git")
    assert seen["GIT_TERMINAL_PROMPT"] == "0" and "BatchMode=yes" in seen["GIT_SSH_COMMAND"]
    monkeypatch.setenv("GIT_SSH_COMMAND", "ssh -i my-key")
    remote_module.git("ls-remote", "git@example.com:o/r.git")
    assert seen["GIT_SSH_COMMAND"] == "ssh -i my-key"


def test_archives_are_hashed_as_a_stream(monkeypatch):
    # an archive is never held in memory whole: the default downloader hashes chunks
    import io

    import mpcheck.remote as remote_module

    body = b"x" * (3 * remote_module.CHUNK + 5)

    class Response(io.BytesIO):  # already a context manager that returns itself
        pass

    reads: list[int] = []
    real_read = Response.read

    def read(self, size=-1):
        reads.append(size)
        return real_read(self, size)

    monkeypatch.setattr(Response, "read", read)
    monkeypatch.setattr(remote_module.urllib.request, "urlopen", lambda *a, **k: Response(body))
    assert (
        remote_module.http_sha256("https://example.com/p.zip") == hashlib.sha256(body).hexdigest()
    )
    assert reads and all(0 < size <= remote_module.CHUNK for size in reads)
