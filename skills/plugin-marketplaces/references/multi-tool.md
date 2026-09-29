# Serving several tools

The packaging and catalog defaults in [SKILL.md](../SKILL.md), why they are the defaults, and when to deviate.
Rules are cited by id; each fact cites a row of the Provenance table.

## What each tool reads from a dual-packaged plugin

A dual-packaged plugin has a portable root `plugin.json` and `mcp.json` and a Claude Code adapter, `.claude-plugin/plugin.json` and `.mcp.json`, sharing one `skills/` directory.

| Tool | Manifest it reads | MCP file it reads |
| --- | --- | --- |
| Claude Code | `.claude-plugin/plugin.json` | `.mcp.json` |
| Codex | root `plugin.json` | `mcp.json` |
| Copilot CLI | root `plugin.json` | `mcp.json` |

The table is from [E1].
Each tool ignores the other pair, so the two manifests must agree on `name` (R8) and `version` (R6), and the two MCP files must declare the same servers.

## Writing the pair

- Root `plugin.json` holds only the Agent Plugins fields, with `$schema` set; everything Claude-specific stays in `.claude-plugin/plugin.json` [E2].
- `mcp.json` repeats each `.mcp.json` server with an explicit `type`, `"streamable-http"` for `"http"`, and `${PLUGIN_ROOT}` for `${CLAUDE_PLUGIN_ROOT}` [E2] [E3].
- Commands, agents, hooks, `userConfig`, and LSP servers have no portable form: keep them in the Claude adapter, and give Codex hooks through `extensions["com.openai"].hooks` in the root manifest if Codex should run them [E2] [E3].
- Migrate additively: add the portable pair beside the existing files and remove nothing another tool reads [E2].

## Why two native catalogs

- Codex reads `.agents/plugins/marketplace.json` before `.claude-plugin/marketplace.json`, and Copilot CLI reads `.github/plugin/marketplace.json` and two other paths before `.claude-plugin/marketplace.json`, so each tool family can have its own catalog [E4] [E5].
- The readers disagree on sources: Codex silently drops `github` entries, and Copilot CLI rejects a whole catalog that holds one `git-subdir` or `npm` entry [E4] [E6].
- A single shared catalog is therefore limited to the source types all its readers accept (R2): relative paths and `url`, for a `.claude-plugin/marketplace.json` read by all three tools [E4] [E6].
- Separate catalogs let each tool get its best source type, at the cost of keeping them in step, which the validator checks against the reasons recorded for differences (R10).

## When to deviate

- One `.claude-plugin/marketplace.json` is enough when every entry is a relative path or a `url` source and no reader needs a different membership; declare all three readers in `marketplace-policy.json` (R1) [E4] [E6].
- A plugin only Claude Code users will install needs no portable manifest.
- A `.github/plugin/marketplace.json` for Copilot CLI is a third catalog, taking precedence for Copilot CLI over `.claude-plugin/marketplace.json`; it needs the same parity records (R10) [E5].

## Provenance

Verified against: claude 2.1.284, codex-cli 0.157.1, copilot 1.0.89 on 2026-09-28.
Conformance probes: none yet.

| Id | Evidence | Kind |
| --- | --- | --- |
| E1 | probe P4; `docs/research/2026-09-28-load-and-update-probes.md` | probe |
| E2 | `agentplugins/agent-plugins-example` at `5f3f5084a8`, `migrate-agent-plugin` skill, and the Codex build documentation; `docs/research/2026-09-27-agent-plugins.md` §4 | docs |
| E3 | Agent Plugins `spec/1.0.0.md` §6 and §9; `docs/research/2026-09-27-agent-plugins.md` §2 | docs |
| E4 | `openai/codex` at `659b35f1316eda27ef61850dd0832c4a4e95c120`, `marketplace.rs`, and a probe on codex-cli 0.157.1; `docs/research/2026-09-27-codex.md` §1 | source |
| E5 | https://docs.github.com/en/copilot/reference/cli-plugin-reference, fetched 2026-09-27; `docs/research/2026-09-27-other-harnesses.md`, GitHub Copilot CLI | docs |
| E6 | probe P3 on copilot 1.0.89; `docs/research/2026-09-28-load-and-update-probes.md` | probe |
