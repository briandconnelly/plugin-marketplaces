# Feature matrix

What works where, side by side; each tool's reference has the detail.
Rules are cited by id from [SKILL.md](../SKILL.md); each cell cites a row of the Provenance table.
"Unproven" means no command shows the behaviour without a model session, so it has not been observed.

## Components

| Component | Claude Code | Codex | Copilot CLI | Agent Plugins 1.0 |
| --- | --- | --- | --- | --- |
| Skills | `skills/<name>/SKILL.md`; manifest `skills` adds directories [E1] | `skills/` [E2] [E3] | loaded, listed by `copilot skill list` [E3] | `skills/<dir>/SKILL.md`, fixed [E5] |
| Commands | `commands/`; listed among skills [E1] [E3] | migrated to a skill `source-command-<name>` when the command has a `description` [E2] [E6] | offered as skills [E3] | none [E5] |
| Agents | `agents/` [E1] | not loaded [E2] [E3] | unproven [E3] | none [E5] |
| Hooks | `hooks/hooks.json`, merged with manifest `hooks` [E1] | `hooks/hooks.json` (compatibility format) or `extensions["com.openai"].hooks` (portable), run after the user trusts them; no prompt or agent handlers [E2] | unproven [E3] | none [E5] |
| MCP servers | `.mcp.json` merged with manifest `mcpServers`; placeholders expanded [E1] [E3] | compatibility: manifest `mcpServers` replaces `.mcp.json`; portable: `mcp.json`; placeholders passed literally [E2] [E3] [E4] | root `.mcp.json` over the manifest's file; portable `mcp.json` when a root `plugin.json` exists; placeholders shown unexpanded [E3] [E4] | `mcp.json`, each server typed [E5] |
| `userConfig` | supported, `${user_config.KEY}` [E1] | not supported [E2] | not expanded [E3] | none [E5] |
| LSP servers | `.lsp.json` [E1] | not supported [E2] | unproven [E3] | none [E5] |

## Source types

| Source type | Claude Code | Codex | Copilot CLI |
| --- | --- | --- | --- |
| `path` | yes [E7] | yes [E8] | yes [E9] |
| `local-object` | no [E7] | yes [E8] | no [E9] |
| `github` | yes [E7] | no, dropped silently [E8] | yes [E9] |
| `url` | yes [E7] | yes [E8] | yes [E9] |
| `git-subdir` | yes [E7] | yes [E8] | no, whole catalog rejected [E9] |
| `npm` | yes [E7] | yes [E8] | no, whole catalog rejected [E9] |
| `archive` | yes [E7] | no [E8] | no [E9] |
| `command` | yes [E7] | no [E8] | no [E9] |

`path` is a relative path string, and `local-object` is Codex's `{"source": "local", "path": …}`; the validator reads this table's values from `scripts/mpcheck/data/readers.json`, and a test keeps the two equal.

## Names, versions, and caches

| Question | Claude Code | Codex | Copilot CLI |
| --- | --- | --- | --- |
| Marketplace name | no spaces, `/`, `\`, `..`; reserved names [E7] | `[A-Za-z0-9_-]+` [E8] | no documented rule [E9] |
| Entry vs manifest `name` | must match; installing by the entry name works but shows the manifest name, and installing by the manifest name gives `not found in marketplace` [E7] [E11] | must match, or install refuses [E8] | same-named manifests collapse into one plugin [E9] |
| Version it installs | `.claude-plugin/plugin.json`, then entry, then derived from the source [E7] [E4] | root `plugin.json` (portable), else the compatibility manifest, then entry [E8] [E4] | root `plugin.json` when present [E4] |
| Change without a version bump | not delivered [E10] | delivered by `codex plugin marketplace upgrade` [E10] | local catalogs load live; remote unproven [E9] |

## Provenance

Verified against: claude 2.1.284, codex-cli 0.157.1, copilot 1.0.89 on 2026-09-28.
Conformance probes: `codex-migrates-described-commands`, `codex-skips-github-source`, `copilot-rejects-catalog-with-git-subdir`.

| Id | Evidence | Kind |
| --- | --- | --- |
| E1 | https://code.claude.com/docs/en/plugins/manifest-reference, fetched 2026-09-27; `docs/research/2026-09-27-claude-code.md` §2 | docs |
| E2 | `openai/codex` at `659b35f1316eda27ef61850dd0832c4a4e95c120` and https://developers.openai.com/plugins/guides/submit-claude-plugin.md; `docs/research/2026-09-27-codex.md` §2 and §4 | source |
| E3 | probe P1; `docs/research/2026-09-28-load-and-update-probes.md` | probe |
| E4 | probe P4; `docs/research/2026-09-28-load-and-update-probes.md` | probe |
| E5 | Agent Plugins `spec/1.0.0.md` §6; `docs/research/2026-09-27-agent-plugins.md` §2 | docs |
| E6 | Codex command-migration probe; `docs/research/2026-09-28-codex-command-migration-probe.md` | probe |
| E7 | https://code.claude.com/docs/en/plugins/marketplace-reference and loading, fetched 2026-09-27; `docs/research/2026-09-27-claude-code.md` §1 and §3 | docs |
| E8 | `openai/codex` at `659b35f1316eda27ef61850dd0832c4a4e95c120` (`marketplace.rs`, `plugin_id.rs`, `store.rs`) and probes on codex-cli 0.157.1; `docs/research/2026-09-27-codex.md` §1 | source |
| E9 | Copilot CLI plugin reference and probes on copilot 1.0.88 and 1.0.89; `docs/research/2026-09-27-other-harnesses.md`, `docs/research/2026-09-27-phase0-probes.md`, and `docs/research/2026-09-28-load-and-update-probes.md` P3 | probe |
| E10 | probe P2; `docs/research/2026-09-28-load-and-update-probes.md` | probe |
| E11 | plan-2c with-skill runs of scenario 6; `tests/runs/evidence/2026-09-28-s6-r1-with-skill-tool-results.jsonl` | run |
