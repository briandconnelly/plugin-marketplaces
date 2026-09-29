"""The remote level (spec §8 level 3): do pinned sources exist upstream and match their pins?

Opt-in with `--remote`. Git runs with the caller's own configuration, so credential helpers
and `insteadOf` mirrors apply, and with `GIT_TERMINAL_PROMPT=0`, so it never waits for a
password. Nothing is installed and no plugin code runs: a pinned commit is fetched without a
checkout into a temporary repository and only its manifests are read.

A failure to reach or read an upstream (network, authentication, a host that refuses to fetch
a commit by SHA, a registry that hides a private package) is `inconclusive`, never `failed`
and never `passed`; only a definite mismatch is an error.
"""

from __future__ import annotations

import hashlib
import http.client
import json
import os
import re
import subprocess
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from mpcheck.discover import Catalog, Repo
from mpcheck.model import Finding, Severity, Status
from mpcheck.readers import GIT_SOURCE_TYPES, source_type

SHA_RE = re.compile(r"^[0-9a-f]{40}$")
REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
HTTP_ERRORS = (urllib.error.URLError, OSError, ValueError, http.client.HTTPException)

GIT_TIMEOUT = 120
HTTP_TIMEOUT = 30
ARCHIVE_LIMIT = 512 * 1024 * 1024
DOCUMENT_LIMIT = 64 * 1024 * 1024
CHUNK = 1024 * 1024
NPM_REGISTRY = "https://registry.npmjs.org"
MANIFESTS = (".claude-plugin/plugin.json", "plugin.json", ".codex-plugin/plugin.json")
USER_AGENT = "check-marketplace"


class FetchError(Exception):
    """An HTTP fetch that failed; `status` is the HTTP code, or None for no response."""

    def __init__(self, status: int | None, message: str) -> None:
        super().__init__(message)
        self.status = status


Fetch = Callable[[str], bytes]


def http_get(url: str) -> bytes:
    try:
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT) as response:
            body = response.read(DOCUMENT_LIMIT + 1)
    except urllib.error.HTTPError as exc:
        raise FetchError(exc.code, f"HTTP {exc.code}") from None
    except HTTP_ERRORS as exc:
        raise FetchError(None, str(getattr(exc, "reason", exc))) from None
    if len(body) > DOCUMENT_LIMIT:
        raise FetchError(None, f"larger than {DOCUMENT_LIMIT} bytes")
    return body


def http_sha256(url: str) -> str:
    """The sha256 of a download, read in chunks so an archive is never held in memory."""
    digest, size = hashlib.sha256(), 0
    try:
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT) as response:
            while chunk := response.read(CHUNK):
                size += len(chunk)
                if size > ARCHIVE_LIMIT:
                    raise FetchError(None, f"larger than {ARCHIVE_LIMIT} bytes")
                digest.update(chunk)
    except urllib.error.HTTPError as exc:
        raise FetchError(exc.code, f"HTTP {exc.code}") from None
    except HTTP_ERRORS as exc:
        raise FetchError(None, str(getattr(exc, "reason", exc))) from None
    return digest.hexdigest()


def git_url(source: dict[str, object]) -> str:
    if source.get("source") == "github":
        return f"https://github.com/{source.get('repo')}.git"
    return str(source.get("url", ""))


@dataclass
class Use:
    """One catalog entry that uses a source."""

    catalog: Catalog
    index: int
    entry: dict[str, object]


@dataclass
class Group:
    kind: str
    key: tuple[str, ...]
    source: dict[str, object]
    uses: list[Use] = field(default_factory=list)


@dataclass
class Tally:
    passed: int = 0
    inconclusive: int = 0
    failed: int = 0
    findings: list[Finding] = field(default_factory=list)

    def add(self, status: Status, findings: list[Finding]) -> None:
        self.findings += findings
        if status == Status.FAILED:
            self.failed += 1
        elif status == Status.INCONCLUSIVE:
            self.inconclusive += 1
        else:
            self.passed += 1


def safe(value: object) -> bool:
    """A string git or a URL may receive: non-empty and never read as an option."""
    return isinstance(value, str) and bool(value) and not value.startswith("-")


def checkable(kind: str, source: dict[str, object]) -> bool:
    """Whether a remote source is well-formed enough to contact; the local level reports the rest."""
    if kind in GIT_SOURCE_TYPES:
        if kind == "github" and not (
            isinstance(source.get("repo"), str) and REPO_RE.fullmatch(str(source["repo"]))
        ):
            return False
        if kind != "github" and not safe(source.get("url")):
            return False
        if "sha" in source and not (
            isinstance(source["sha"], str) and SHA_RE.fullmatch(source["sha"])
        ):
            return False
        return all(key not in source or safe(source[key]) for key in ("ref", "path"))
    if kind == "npm":
        registry = source.get("registry")
        return (
            safe(source.get("package"))
            and safe(source.get("version"))
            and (
                registry is None
                or (isinstance(registry, str) and registry.startswith(("https://", "http://")))
            )
        )
    if kind == "archive":
        return isinstance(source.get("url"), str) and isinstance(source.get("sha256"), str)
    return False


def groups_of(catalogs: list[Catalog]) -> list[Group]:
    found: dict[tuple[str, ...], Group] = {}
    for catalog in catalogs:
        for index, entry in catalog.entries:
            source = entry.get("source")
            if not isinstance(source, dict):
                continue
            kind = source_type(source)
            if not checkable(kind, source):
                continue  # malformed: the local level reports it, and git must never see it
            if kind in GIT_SOURCE_TYPES:
                key = (kind, git_url(source), str(source.get("sha")), str(source.get("path", "")))
            elif kind == "npm":
                key = (
                    kind,
                    str(source.get("registry", "")),
                    str(source.get("package")),
                    str(source.get("version")),
                )
            elif kind == "archive":
                key = (kind, str(source.get("url")), str(source.get("sha256")))
            else:
                continue
            group = found.setdefault(key, Group(kind, key, source))
            group.uses.append(Use(catalog, index, entry))
    return list(found.values())


def check_remote(
    repo: Repo, catalogs: list[Catalog], fetch: Fetch | None = None
) -> tuple[list[Finding], Status, str]:
    groups = groups_of(catalogs)
    if not groups:
        return [], Status.SKIPPED, "no remote source in a catalog a declared reader reads"
    tally = Tally()
    for group in groups:
        if group.kind in GIT_SOURCE_TYPES:
            tally.add(*check_git(group))
        elif group.kind == "npm":
            tally.add(*check_npm(group, fetch or http_get))
        else:
            digest = (lambda url: hashlib.sha256(fetch(url)).hexdigest()) if fetch else http_sha256
            tally.add(*check_archive(group, digest))
    total = len(groups)
    note = (
        f"{total} source{'s' if total != 1 else ''}: {tally.passed} passed, "
        f"{tally.inconclusive} inconclusive, {tally.failed} failed"
    )
    if tally.failed:
        status = Status.FAILED
    elif tally.inconclusive:
        status = Status.INCONCLUSIVE
    else:
        status = Status.PASSED
    return tally.findings, status, note


def finding(check: str, severity: Severity, use: Use, message: str, rule: str | None) -> Finding:
    return Finding(
        check,
        severity,
        use.catalog.relpath,
        message,
        rule=rule,
        pointer=f"/plugins/{use.index}/source",
    )


def inconclusive(group: Group, why: str) -> tuple[Status, list[Finding]]:
    name = group.uses[0].entry.get("name")
    message = f"could not confirm the pin for {name!r}: {why}; report this check as inconclusive"
    return Status.INCONCLUSIVE, [
        finding("remote.inconclusive", Severity.WARNING, group.uses[0], message, "R12")
    ]


# ---- git


def git(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    # nothing may prompt: no terminal prompts, no askpass, and no controlling terminal for
    # ssh to ask on; the caller's own ssh command (GIT_SSH_COMMAND, core.sshCommand) stays
    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0", "SSH_ASKPASS_REQUIRE": "never"}
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        env=env,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=GIT_TIMEOUT,
        check=False,
        start_new_session=True,
    )


def tail(result: subprocess.CompletedProcess[str]) -> str:
    lines = [line for line in (result.stderr or result.stdout).splitlines() if line.strip()]
    return lines[-1].strip() if lines else f"git exited {result.returncode}"


def check_refs(group: Group, url: str, sha: str) -> list[Finding]:
    """Informational: whether each entry's `ref` still names the pinned commit."""
    notes: list[Finding] = []
    by_ref: dict[str, Use] = {}
    for use in group.uses:
        ref = ref_of(use)
        if ref:
            by_ref.setdefault(ref, use)
    for ref, use in sorted(by_ref.items()):
        try:
            result = git("ls-remote", "--exit-code", "--", url, ref, ref + "^{}")
        except subprocess.TimeoutExpired:
            continue
        if result.returncode == 2:
            notes.append(
                finding(
                    "remote.ref-missing",
                    Severity.INFO,
                    use,
                    f"ref {ref!r} no longer exists upstream; the pinned sha still decides what installs",
                    "R4",
                )
            )
            continue
        if result.returncode != 0:
            continue
        refs: dict[str, str] = {}
        for line in result.stdout.splitlines():
            oid, _, name = line.partition("\t")
            if name:
                refs[name] = oid
        resolved = next(
            (
                refs[name]
                for name in (f"refs/tags/{ref}^{{}}", f"refs/tags/{ref}", f"refs/heads/{ref}", ref)
                if name in refs
            ),
            None,
        )
        if resolved and resolved != sha:
            notes.append(
                finding(
                    "remote.ref-moved",
                    Severity.INFO,
                    use,
                    f"ref {ref!r} now points at {resolved[:12]}, not the pinned {sha[:12]}; review before moving the pin (R5)",
                    "R4",
                )
            )
    return notes


def ref_of(use: Use) -> str | None:
    source = use.entry.get("source")
    ref = source.get("ref") if isinstance(source, dict) else None
    return ref if isinstance(ref, str) and ref else None


def check_unpinned(group: Group, url: str) -> tuple[Status, list[Finding]]:
    """A source without a `sha` installs whatever its ref (or the default branch) names now,
    so the check is that the ref exists; the local level already reports the missing pin."""
    use = group.uses[0]
    ref = ref_of(use)
    try:
        result = git("ls-remote", "--exit-code", "--", url, *([ref] if ref else ["HEAD"]))
    except subprocess.TimeoutExpired:
        return inconclusive(group, f"git timed out after {GIT_TIMEOUT} s")
    if result.returncode == 0:
        return Status.PASSED, []
    if result.returncode == 2 and ref:
        message = f"unpinned source for {use.entry.get('name')!r} tracks ref {ref!r}, which does not exist upstream"
        return Status.FAILED, [
            finding("remote.unpinned-ref-missing", Severity.ERROR, use, message, "R4")
        ]
    return inconclusive(group, f"listing {url} failed ({tail(result)})")


def check_git(group: Group) -> tuple[Status, list[Finding]]:
    source = group.source
    url, sha = git_url(source), source.get("sha")
    if not isinstance(sha, str):
        return check_unpinned(group, url)
    findings = check_refs(group, url, sha)
    with tempfile.TemporaryDirectory(prefix="mpcheck-remote-") as tmp:
        work = Path(tmp)
        try:
            init = git("init", "-q", str(work))
            fetched = (
                git("fetch", "-q", "--depth", "1", "--no-tags", "--", url, sha, cwd=work)
                if init.returncode == 0
                else init
            )
        except subprocess.TimeoutExpired:
            status, extra = inconclusive(group, f"git timed out after {GIT_TIMEOUT} s")
            return status, findings + extra
        if fetched.returncode != 0:
            status, extra = inconclusive(
                group, f"fetching {sha[:12]} from {url} failed ({tail(fetched)})"
            )
            return status, findings + extra
        base = str(source.get("path", "")).strip("/") if group.kind == "git-subdir" else ""
        if base and git("cat-file", "-e", f"FETCH_HEAD:{base}", cwd=work).returncode != 0:
            use = group.uses[0]
            findings.append(
                finding(
                    "remote.path-missing",
                    Severity.ERROR,
                    use,
                    f"path {base!r} does not exist at the pinned commit {sha[:12]}",
                    "R4",
                )
            )
            return Status.FAILED, findings
        path, manifest = read_manifest(work, base)
    if path is not None and manifest is None:
        message = (
            f"{path} at the pinned commit {sha[:12]} is not a JSON object, so no tool can load it"
        )
        return Status.FAILED, [
            *findings,
            finding("remote.manifest-invalid", Severity.ERROR, group.uses[0], message, "R4"),
        ]
    failed = False
    if manifest is not None:
        for use in group.uses:
            name, version = use.entry.get("name"), use.entry.get("version")
            if isinstance(manifest.get("name"), str) and name != manifest["name"]:
                failed = True
                findings.append(
                    finding(
                        "remote.name-mismatch",
                        Severity.ERROR,
                        use,
                        f"entry {name!r} pins a plugin whose manifest names it {manifest['name']!r}",
                        "R8",
                    )
                )
            if (
                isinstance(version, str)
                and isinstance(manifest.get("version"), str)
                and version != manifest["version"]
            ):
                failed = True
                findings.append(
                    finding(
                        "remote.version-mismatch",
                        Severity.ERROR,
                        use,
                        f"entry {name!r} records version {version!r} but the manifest at the pin says {manifest['version']!r}",
                        "R6",
                    )
                )
    return (Status.FAILED if failed else Status.PASSED), findings


def read_manifest(work: Path, base: str) -> tuple[str | None, dict[str, object] | None]:
    """(path, data) for the first manifest at the pin; data is None when it is unreadable,
    and path is None when there is none, which is allowed (an entry can be the manifest)."""
    for rel in MANIFESTS:
        path = f"{base}/{rel}" if base else rel
        shown = git("show", f"FETCH_HEAD:{path}", cwd=work)
        if shown.returncode == 0:
            try:
                data = json.loads(shown.stdout)
            except json.JSONDecodeError:
                return path, None
            return path, data if isinstance(data, dict) else None
    return None, None


# ---- npm and archive


def check_npm(group: Group, fetch: Fetch) -> tuple[Status, list[Finding]]:
    source, use = group.source, group.uses[0]
    registry = str(source.get("registry") or NPM_REGISTRY).rstrip("/")
    package = urllib.parse.quote(str(source.get("package")), safe="@").replace("%2F", "%2f")
    version = str(source.get("version"))
    try:
        fetch(f"{registry}/{package}/{version}")
        return Status.PASSED, []
    except FetchError as exc:
        if exc.status != 404:
            return inconclusive(group, f"the registry did not answer ({exc})")
    try:
        document = json.loads(fetch(f"{registry}/{package}"))
    except FetchError as exc:
        return inconclusive(
            group, f"the registry does not show the package ({exc}); it may be private"
        )
    except json.JSONDecodeError:
        return inconclusive(group, "the registry returned an unreadable package document")
    if version in (document.get("versions") or {}):
        return Status.PASSED, []
    message = f"npm package {source.get('package')!r} has no published version {version!r}"
    return Status.FAILED, [
        finding("remote.npm-version-missing", Severity.ERROR, use, message, "R4")
    ]


def check_archive(group: Group, digest: Callable[[str], str]) -> tuple[Status, list[Finding]]:
    source, use = group.source, group.uses[0]
    url, expected = str(source.get("url")), str(source.get("sha256", "")).lower()
    if not url.startswith("https://"):
        return inconclusive(group, f"only https archives are checked, not {url!r}")
    try:
        actual = digest(url)
    except FetchError as exc:
        return inconclusive(group, f"downloading {url} failed ({exc})")
    if actual == expected:
        return Status.PASSED, []
    message = f"the archive at {url} has sha256 {actual[:16]}…, not the pinned {expected[:16]}…"
    return Status.FAILED, [
        finding("remote.archive-digest-mismatch", Severity.ERROR, use, message, "R4")
    ]
