# Freshness

The covered tools change weekly; this file says how the references record what they were checked against and what to do when a tool is newer (R13).
Rules are cited by id from [SKILL.md](../SKILL.md); each fact cites a row of the Provenance table.

## Provenance blocks

Every reference ends with a `## Provenance` section holding:

- a line `Verified against: <tool and version, …> on <date>.`, naming the versions its facts were observed or read against [E1];
- a line naming the conformance probes that re-check its facts, or `none yet` [E1];
- a table of evidence rows `| E<n> | <evidence> | <kind> |`, where kind is `docs` (read in published documentation), `source` (read in a tool's source at a named commit), `probe` (observed by running the tool), or `run` (observed in a recorded evaluation run) [E1].

Each fact in the reference cites one or more rows as `[E<n>]`, and a test in this skill's repository fails when a citation, a row, or a cited repository path is missing [E1].

## When a tool is newer than a reference (R13)

1. Read the tool's installed version with its version command, isolated as [validation.md](validation.md) describes (R15).
2. Compare it with the reference's `Verified against:` line.
3. If it is newer, list the facts your current decision depends on, and re-check each one against the evidence kind it cites: re-read the documentation page, re-read the source at the new release, or re-run the observation in a throwaway configuration.
4. Use what you observed, and say in the report which facts you re-checked, which changed, and which you relied on without re-checking.
5. If a fact changed, tell the maintainer of this skill; a validator disagreement is handled by R14.

## Refreshing a fact (for maintainers of this skill)

- A weekly GitHub Action opens one issue labelled `upstream-drift`, or updates the open one, when an upstream page or source file changed, a conformance probe failed, or a check could not run; a newer tool release is listed in the issue but does not open one by itself, and nothing is touched when nothing changed [E2] [E3] [E4].
- `tests/check_upstream.py` compares each pin in `tests/upstream-pins.json` with its upstream and names the evidence rows the pin affects; it needs only network access, and a fetch that fails is reported as `error`, never as unchanged [E2].
- `tests/conformance/run.py` runs each behavioural probe in throwaway configuration and reports it `held`, `flipped`, `broken` (its control failed), `error`, or `skipped`, naming the reference lines a flipped probe re-checks; it also compares each tool's `--help` text with the copy under `tests/conformance/help/` [E3].
- The references' `Conformance probes:` lines and the probes' anchors are kept in step by a test [E1].

To act on the issue:

1. List the facts a changed pin affects with `uv run python tests/check_upstream.py lines <id>`, and re-verify each against its source before editing anything; re-pinning a hash or version without re-verification is the failure this procedure exists to prevent.
2. Record the new observation as a dated file under `docs/research/`, never by editing an old one, and name in it, in backticks, every pin id you re-verified and the sha256, blob, or version of the content you read.
3. Update the fact, its evidence row, and the reference's `Verified against:` line together; if the fact is a reader's source types or catalog paths, update `scripts/mpcheck/data/readers.json` in the same change.
4. Re-pin with `uv run python tests/check_upstream.py repin <id> … --evidence docs/research/<file>.md`, which refuses unless the record names each pin and the exact value it would pin (a page's sha256, a file's blob, a version); re-pin help text with `uv run python tests/conformance/run.py --repin-help --evidence docs/research/<file>.md`, which refuses unless the record names each text's sha256.
5. When a probe flipped, change the probe's expectation only in the same change as the reference lines it anchors.

## Provenance blocks

Every reference ends with a `## Provenance` section holding:

- a line `Verified against: <tool and version, …> on <date>.`, naming the versions its facts were observed or read against [E1];
- a line naming the conformance probes that re-check its facts, or `none yet` [E1];
- a table of evidence rows `| E<n> | <evidence> | <kind> |`, where kind is `docs` (read in published documentation), `source` (read in a tool's source at a named commit), `probe` (observed by running the tool), or `run` (observed in a recorded evaluation run) [E1].

Each fact in the reference cites one or more rows as `[E<n>]`, and a test in this skill's repository fails when a citation, a row, or a cited repository path is missing [E1].

## When a tool is newer than a reference (R13)

1. Read the tool's installed version with its version command, isolated as [validation.md](validation.md) describes (R15).
2. Compare it with the reference's `Verified against:` line.
3. If it is newer, list the facts your current decision depends on, and re-check each one against the evidence kind it cites: re-read the documentation page, re-read the source at the new release, or re-run the observation in a throwaway configuration.
4. Use what you observed, and say in the report which facts you re-checked, which changed, and which you relied on without re-checking.
5. If a fact changed, tell the maintainer of this skill; a validator disagreement is handled by R14.

## Refreshing a fact (for maintainers of this skill)

1. Re-verify the fact against its source before editing anything; re-pinning a hash or version without re-verification is the failure this procedure exists to prevent.
2. Record the new observation as a dated file under `docs/research/`, never by editing an old one.
3. Update the fact, its evidence row, and the reference's `Verified against:` line together; if the fact is a reader's source types or catalog paths, update `scripts/mpcheck/data/readers.json` in the same change.

## Provenance

Verified against: the repository's own tests on 2026-09-28.
Conformance probes: none yet.

| Id | Evidence | Kind |
| --- | --- | --- |
| E1 | `tests/test_skill_docs.py` and `tests/test_conformance.py` | source |
| E2 | `tests/check_upstream.py`, `tests/upstream-pins.json`, and `tests/test_check_upstream.py` | source |
| E3 | `tests/conformance/run.py`, `tests/conformance/probes.py`, and `tests/test_conformance.py` | source |
| E4 | `.github/workflows/upstream-drift.yml`, `tests/drift_issue.py`, and `tests/test_drift_issue.py` | source |
