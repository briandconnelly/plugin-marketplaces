# Remote-level probes: git, npm, and the calibration marketplaces

Date: 2026-09-29.
This is a hand-written record of the observations behind the validator's remote level (`check-marketplace --remote`), made while writing plan 4a with git 2.55.0 and `GIT_TERMINAL_PROMPT=0`.
Every call was read-only: `git ls-remote`, a shallow `git fetch` of one commit into a temporary repository with no checkout, and HTTPS GETs to the npm registry.

## Git

Against `https://github.com/agentplugins/agent-plugins-spec.git`:

| Call | Result |
| --- | --- |
| `git ls-remote --exit-code <url> refs/heads/main` | `ff8ab5e392cc87bd88d87c060815a87490e51003	refs/heads/main`, exit 0 |
| `git ls-remote --exit-code <url> refs/tags/no-such-tag` | no output, exit 2 |
| `git fetch -q --depth 1 --no-tags <url> ff8ab5e392cc87bd88d87c060815a87490e51003` into an empty repository | exit 0; `git cat-file -e FETCH_HEAD:spec/1.0.0.md` succeeds, and a missing path gives `fatal: path 'no/such/path' does not exist in 'FETCH_HEAD'` |
| the same fetch of `0123456789abcdef0123456789abcdef01234567` | `fatal: remote error: upload-pack: not our ref 0123456789abcdef0123456789abcdef01234567` |

Against `https://github.com/acme/notes.git`, which does not exist: `remote: Repository not found.` and `fatal: repository 'https://github.com/acme/notes.git/' not found`.

So exit 2 from `ls-remote --exit-code` is a definite "reachable, but the ref is absent", while a failed fetch of a commit is not definite: GitHub gives the same `not our ref` for a commit it lacks as a host that refuses to fetch by SHA does, and the same `not found` for a missing repository as for a private one without credentials.
The validator reports the definite cases as findings and the others as inconclusive.

A local bare repository served over `file://` answered a shallow fetch of a commit that no branch or tag points at (exit 0), so the validator's tests use real git without the network.

## Annotated tags

`git ls-remote https://github.com/briandconnelly/amicus.git 'v0.8.0*'` gives:

```text
fce847cecff15114f6d451f71e78821e96178963	refs/tags/v0.8.0
620f4322e52cac811a8003d4b4b98b45ba4b576e	refs/tags/v0.8.0^{}
```

`refs/tags/v0.8.0` names the tag object and `refs/tags/v0.8.0^{}` the commit it points to; `git ls-remote <url> v0.8.0` returns only the first line, so a ref check must also ask for `v0.8.0^{}`.
The first calibration run, before that fix, reported `briandconnelly-plugins`' correct `amicus` pin as a moved ref.

## npm

| Request | Status |
| --- | --- |
| `https://registry.npmjs.org/@openai%2Fcodex/0.157.1` | 200 |
| `https://registry.npmjs.org/@openai%2Fcodex/9.9.9` | 404 |
| `https://registry.npmjs.org/no-such-package-xyz-123/1.0.0` | 404 |

A missing version and a missing package both answer 404, and a private package looks missing to an unauthenticated client, so a 404 for the version is definite only when the package document itself is readable and lacks the version.

## Calibration

`check-marketplace <repo> --no-claude --remote`, run on the owners' checkouts in place (read only):

| Repository | Commit | `remote` status |
| --- | --- | --- |
| `briandconnelly/briandconnelly-plugins` | `51f4c97` | passed: 4 sources, 4 passed |
| `briandconnelly/data-reasoning` | `5159b1c` | passed: 1 source (the declared `release` channel), 1 passed |

A copy of `briandconnelly-plugins` at `51f4c97` with three seeded defects gave `failed: 5 sources: 2 passed, 1 inconclusive, 2 failed`:

- `amicus` given entry version `0.0.1`: `remote.version-mismatch`, "entry 'amicus' records version '0.0.1' but the manifest at the pin says '0.8.0'";
- `data-reasoning` pinned to `0123456789abcdef0123456789abcdef01234567`: `remote.inconclusive` (the fetch answered `not our ref`), plus `remote.ref-moved` saying `release` points at `851025766e86`;
- `codex-in-claude`'s unpinned ref changed to `no-such-branch-xyz`: `remote.unpinned-ref-missing`.
