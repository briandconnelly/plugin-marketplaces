# Freshness

The covered tools change weekly; this file says how the references record what they were checked against and what to do when a tool is newer (R13).
Rules are cited by id from [SKILL.md](../SKILL.md); each fact cites a row of the Provenance table.

## Provenance blocks

Every reference ends with a `## Provenance` section holding:

- a line `Verified against: <tool and version, …> on <date>.`, naming the versions its facts were observed or read against;
- a line naming the conformance probes that re-check its facts, or `none yet`;
- a table of evidence rows `| E<n> | <evidence> | <kind> |`, where kind is `docs` (read in published documentation), `source` (read in a tool's source at a named commit), `probe` (observed by running the tool), or `run` (observed in a recorded evaluation run).

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
| E1 | `tests/test_skill_docs.py` | source |
