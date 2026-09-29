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

## What adding the portable pair changes

- Without a root `plugin.json`, Codex and Copilot CLI read the Claude-format manifest: Codex migrates each command with a `description` into a `source-command-<name>` skill and Copilot CLI offers commands as skills, but MCP server arguments keep `${CLAUDE_PLUGIN_ROOT}` literally, so a server started from a path under it cannot start [E6] [E8] [E9].
- With a root `plugin.json`, both tools read only the portable package: MCP servers from `mcp.json` get a real `${PLUGIN_ROOT}`, and `commands/` is no longer read, so commands stop reaching Codex and Copilot CLI users [E1] [E7].
- The one way observed to keep a command in every tool is to convert it: moving `commands/<name>.md` to `skills/<name>/SKILL.md` left Claude Code's component list unchanged and all three tools offered the skill, while keeping both the command and a same-named skill made Claude Code list the name twice [E7].
- That move changes a file Claude Code reads, so it is an exception to migrating additively: propose it and let the user decide, and otherwise report which tools lose the command [E7].

## Why two native catalogs

- Codex reads `.agents/plugins/marketplace.json` before `.claude-plugin/marketplace.json`, and Copilot CLI reads `.github/plugin/marketplace.json` and two other paths before `.claude-plugin/marketplace.json`, so each tool family can have its own catalog [E4] [E5].
- The readers disagree on sources: Codex silently drops `github` entries, and Copilot CLI rejects a whole catalog that holds one `git-subdir` or `npm` entry [E4] [E6].
- A single shared catalog is therefore limited to the source types all its readers accept (R2): relative paths and `url`, for a `.claude-plugin/marketplace.json` read by all three tools [E4] [E6].
- Separate catalogs let each tool get its best source type, at the cost of keeping them in step, which the validator checks against the reasons recorded for differences (R10) [E4].

## When to deviate

- One `.claude-plugin/marketplace.json` is enough when every entry is a relative path or a `url` source and no reader needs a different membership; declare all three readers in `marketplace-policy.json` (R1) [E4] [E6].
- A plugin only Claude Code users will install needs no portable manifest, because Claude Code reads only its adapter [E1].
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
| E7 | plan-2c with-skill runs of scenario 4 on claude 2.1.284, codex-cli 0.157.1, copilot 1.0.89, comparing the Claude-only and dual-packaged layouts; `tests/runs/evidence/2026-09-28-s4-r1-with-skill-tool-results.jsonl`, `tests/runs/evidence/2026-09-28-s4-r2-with-skill-tool-results.jsonl`, and `tests/runs/evidence/2026-09-28-s4-r5-with-skill-tool-results.jsonl` | run |
| E8 | Codex command-migration probe; `docs/research/2026-09-28-codex-command-migration-probe.md` | probe |
| E9 | probe P1; `docs/research/2026-09-28-load-and-update-probes.md` | probe |
