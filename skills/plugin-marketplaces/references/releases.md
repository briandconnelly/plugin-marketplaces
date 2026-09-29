# Releases

Versions, pins, and how a change reaches each tool's users.
Rules are cited by id from [SKILL.md](../SKILL.md); each fact cites a row of the Provenance table.

## Where each reader takes the version from (R6)

| Reader | Authoritative field | Also recorded, and must be equal |
| --- | --- | --- |
| Claude Code | `.claude-plugin/plugin.json` `version`; the catalog entry's `version` only when the manifest has none | entry `version` in `.claude-plugin/marketplace.json` |
| Codex | root `plugin.json` `version` when it carries the Agent Plugins `$schema`, else the first of `.codex-plugin/plugin.json` and `.claude-plugin/plugin.json`; the entry's `version` only as a fallback manifest | entry `version` in `.agents/plugins/marketplace.json` |
| Copilot CLI | root `plugin.json` `version` when present, else the Claude-format manifest | entry `version` in the catalog it reads |

The rows are from [E1], [E2], [E3], and, for Copilot CLI's Claude-format fallback, [E6].
Omitting `version` everywhere is also consistent: Claude Code then derives it from the commit, and Codex names its cache directory `local` or `1.0.0` [E1] [E2].
When two recorded values disagree, no tool reports it except `claude plugin validate`, as a warning: each tool silently installs the value from its own authoritative field, so users of different tools get different versions [E1] [E4].

## How a change reaches users

| Reader | Pushed change, version unchanged | Pushed change, version bumped |
| --- | --- | --- |
| Claude Code | not delivered: `already at the latest version` | delivered by `claude plugin update`, or by auto-update where the user enabled it |
| Codex | delivered by `codex plugin marketplace upgrade`, which replaces the installed copy in place | delivered the same way |
| Copilot CLI | a catalog added as a local directory loads live; remote catalogs unproven | unproven |

The Claude Code and Codex rows are from [E5]; the Copilot CLI row is from [E6].
So a maintainer who publishes without a bump reaches Codex users and not Claude Code users; bump on every release (R7) unless you deliberately omit `version` everywhere.

## Moving a pin (R4, R5)

1. Fetch the new tag or commit into a local clone or mirror, and confirm the tag points at the commit you were given: `git -C <clone> rev-parse <tag>^{commit}`.
2. Review what changed: `git -C <clone> log --oneline <old sha>..<new sha>` and `git -C <clone> diff <old sha> <new sha>`.
   Look for new network destinations, collected data, new executable components or install scripts, widened permissions, and changed MCP server commands.
3. Record in the report what the review found, including "nothing notable" when that is the finding.
4. Change `sha` (and `ref`, if the entry has one) in every catalog that lists the plugin, then the version everywhere R6 records it.
5. A `ref` without `sha` is allowed only as a declared channel in `marketplace-policy.json` (R4).

A pinned `sha` still installs after its `ref` is deleted or moved, except on hosts that cannot fetch a commit by SHA [E1].

## Renames and removals (R9)

- Claude Code: add the old name to the catalog's `renames` map with the new name, or `null` for a removal; `forceRemoveDeletedPlugins: true` uninstalls removed plugins for users [E1].
- Codex and Copilot CLI document no rename mechanism; a renamed plugin is a new plugin to their users [E2] [E6].

## Provenance

Verified against: claude 2.1.284, codex-cli 0.157.1, copilot 1.0.89 on 2026-09-28.
Conformance probes: none yet.

| Id | Evidence | Kind |
| --- | --- | --- |
| E1 | https://code.claude.com/docs/en/plugins/marketplace-reference and loading, fetched 2026-09-27; `docs/research/2026-09-27-claude-code.md` §1 and §3; re-verified 2026-09-28, `docs/research/2026-09-28-documentation-reverification.md` | docs |
| E2 | `openai/codex` at `659b35f1316eda27ef61850dd0832c4a4e95c120`, `plugin_namespace.rs`, `store.rs`, and `manager.rs`; `docs/research/2026-09-27-codex.md` §2 and §3 | source |
| E3 | probe P4 on all three tools; `docs/research/2026-09-28-load-and-update-probes.md` | probe |
| E4 | plan-2b baselines s2-r1 to s2-r3 (lint-kit's disagreeing manifests) and s7 objective checks; `tests/runs/evidence/2026-09-28-s2-r3-tool-results.jsonl` and `tests/runs/2026-09-28-s7-r1-baseline.md` | run |
| E5 | probe P2 on claude 2.1.284 and codex-cli 0.157.1; `docs/research/2026-09-28-load-and-update-probes.md` | probe |
| E6 | phase-0 probes and probe P1 on Copilot CLI; `docs/research/2026-09-27-phase0-probes.md` and `docs/research/2026-09-28-load-and-update-probes.md` | probe |
