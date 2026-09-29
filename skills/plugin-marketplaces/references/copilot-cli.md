# GitHub Copilot CLI

What Copilot CLI reads from a user-hosted marketplace and its plugins.
Rules are cited by id from [SKILL.md](../SKILL.md); each fact cites a row of the Provenance table.

## Catalog

- Copilot CLI reads the first file that exists of `marketplace.json`, `.plugin/marketplace.json`, `.github/plugin/marketplace.json`, and `.claude-plugin/marketplace.json`; it does not read `.agents/plugins/marketplace.json` [E1].
- Users register a marketplace with `copilot plugin marketplace add <owner/repo[#ref] | URL | path>`; `github/copilot-plugins` and `github/awesome-copilot` are registered by default [E1].
- The catalog uses the Claude Code dialect: `name`, `owner`, `metadata`, and `plugins[]` whose entries have `name`, `description`, `version`, and `source` [E1].
- Accepted sources are relative paths, `github`, and `url`, each git source with optional `ref` and `sha` [E1] [E4].
- One entry with any other source — `git-subdir`, `npm`, or an unknown type — makes `copilot plugin marketplace add` reject the whole catalog, naming the entry: `Invalid marketplace.json: plugins.3.source: Invalid input` [E2] [E4].
- A relative path without `./` is accepted, and a bare name resolves under `metadata.pluginRoot` [E2] [E3].
- Two entries that resolve to manifests with the same `name` collapse into one listed plugin (R8) [E2].

## Plugins

- From a plugin that carries both a portable root `plugin.json` and `.claude-plugin/plugin.json`, Copilot CLI reads the root manifest's version and the portable `mcp.json` [E5].
- A plugin installed from a catalog added as a local directory is loaded live from that directory, not copied: "It is loaded live from …, so edits take effect on the next session — nothing was copied." [E2] [E6]
- A plugin's commands are offered as skills [E6].
- When a Claude-format plugin has a root `.mcp.json`, Copilot CLI configures the servers in it and ignores the file the manifest's `mcpServers` names [E6].
- Server arguments containing `${CLAUDE_PLUGIN_ROOT}` or `${user_config.*}` are shown unexpanded, and the server's environment carries `CLAUDE_PLUGIN_ROOT`, `COPILOT_PLUGIN_ROOT`, and `PLUGIN_ROOT`; whether the arguments are expanded when the server starts was not observed [E6].
- A failed install still leaves a listing entry, distinguishable only by `enabled: false` and no `version`, so check both, not list membership [E2].

## Isolation

- `COPILOT_HOME` and `COPILOT_CACHE_HOME` isolate Copilot CLI's configuration and cache [E2].
- They do not isolate its sign-in: a prompt, an interactive session, or `copilot --acp` from a throwaway home still uses the machine's GitHub account, and one such session reached GitHub's Copilot service; never open one to check a plugin (R15) [E7].

## Seeing what loaded

- `copilot plugin install` reports what it loaded (`Installed 1 skill.`), and `copilot plugin list` shows the version and whether the plugin is enabled [E2] [E6].
- `copilot skill list` lists plugin skills, including commands; `copilot mcp list` and `copilot mcp get <server>` show plugin MCP servers; none of them starts a server [E6].
- No command shows a plugin's agents or hooks, so those load checks are unproven for Copilot CLI [E6].

## Provenance

Verified against: copilot 1.0.88 (phase-0 and pluginRoot probes) and 1.0.89 (plan-2c probes) on 2026-09-28.
Conformance probes: `copilot-offers-commands-as-skills`, `copilot-prefers-github-catalog`, `copilot-rejects-catalog-with-git-subdir`.

| Id | Evidence | Kind |
| --- | --- | --- |
| E1 | https://docs.github.com/en/copilot/reference/cli-plugin-reference, "File locations", fetched 2026-09-27; `docs/research/2026-09-27-other-harnesses.md`, GitHub Copilot CLI; re-verified 2026-09-28, `docs/research/2026-09-28-documentation-reverification.md` | docs |
| E2 | phase-0 probes on copilot 1.0.88; `docs/research/2026-09-27-phase0-probes.md` | probe |
| E3 | `metadata.pluginRoot` probe on copilot 1.0.88; `docs/research/2026-09-27-copilot-pluginroot-probe.md` | probe |
| E4 | probe P3 on copilot 1.0.89; `docs/research/2026-09-28-load-and-update-probes.md` | probe |
| E5 | probe P4 on copilot 1.0.89; `docs/research/2026-09-28-load-and-update-probes.md` | probe |
| E6 | probe P1 on copilot 1.0.89; `docs/research/2026-09-28-load-and-update-probes.md` | probe |
| E7 | plan-2b s4 adjudications (s4-r7, call 33) and the scenario rules; `tests/runs/2026-09-28-baseline-summary-2b.md`, Isolation, and `tests/scenarios.md`, How to run | run |
