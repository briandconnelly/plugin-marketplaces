# Codex

What the Codex CLI reads from a user-hosted marketplace and its plugins.
Rules are cited by id from [SKILL.md](../SKILL.md); each fact cites a row of the Provenance table.

## Catalog

- Under a marketplace root, Codex reads the first file that exists of `.agents/plugins/marketplace.json`, `.agents/plugins/api_marketplace.json`, `.claude-plugin/marketplace.json`, and `.cursor-plugin/marketplace.json` [E1] [E2].
- So Codex reads a repository with both native catalogs through `.agents/plugins/marketplace.json` only, and a repository with only `.claude-plugin/marketplace.json` through that file [E2].
- Relative sources resolve from the marketplace root, the directory above `.agents/` or `.claude-plugin/` [E1] [E2].
- Required top-level fields are `name` and `plugins`; the marketplace `name` must match `[A-Za-z0-9_-]+`, so no dots; Claude's `owner` and `metadata` are ignored [E2].
- Invalid JSON or a missing `name` or `plugins` fails the whole file, but an entry that cannot be resolved is skipped with only a log warning, so compare what Codex lists against what the catalog holds [E2] [E6].

## Entries

- Required entry fields are `name` and `source`; `name` allows `[A-Za-z0-9._-]` with dots only between non-empty segments [E2].
- `policy.installation` (`AVAILABLE`, the default, `INSTALLED_BY_DEFAULT`, `NOT_AVAILABLE`), `policy.authentication` (`ON_INSTALL`, the default, or `ON_USE`), `policy.products`, and `category` are optional to the parser, though OpenAI's documentation says to always include the first two and `category` [E1] [E2].
- Other entry keys (`version`, `description`, `displayName`, `author`, …) are a fallback manifest, used when the plugin has none, so Claude-style `strict: false` entries work [E2].
- Install refuses an entry whose `name` differs from the plugin manifest's: ``plugin.json name `linter` does not match marketplace plugin name `lint` `` (R8) [E2] [E8].

## Sources

| Source | Shape |
| --- | --- |
| Local | `"./plugins/foo"` or `{"source": "local", "path": "./plugins/foo"}`; must start with `./` except in `.cursor-plugin/marketplace.json`; no `..` |
| `url` | `{"source": "url", "url", "path"?, "ref"?, "sha"?}`: a git repository, plugin at its root or at `path` |
| `git-subdir` | `{"source": "git-subdir", "url", "path", "ref"?, "sha"?}` |
| `npm` | `{"source": "npm", "package", "version"?, "registry"?}` |

The shapes are from [E2].
Any other source, including Claude Code's `{"source": "github", …}` with or without `ref` and `sha`, is dropped without an error; the same repository given as a `url` or `git-subdir` source is listed [E2] [E7].

## Manifests

Codex reads one of two formats [E3]:

- **Portable**: a root `plugin.json` that is a regular file (not a symlink) whose `$schema` is `https://agent-plugins.org/schemas/1.0.0/plugin.schema.json`; skills come from `skills/` and MCP servers from `mcp.json`, and nothing in the manifest can move them; hooks come from `hooks/hooks.json` unless `extensions["com.openai"].hooks` names another file [E3].
  OpenAI-specific settings go under `extensions["com.openai"]`, which, when present, replaces `.codex-plugin/plugin.json` as the overlay rather than merging with it.
- **Compatibility**: otherwise, the first of `.codex-plugin/plugin.json`, `.claude-plugin/plugin.json`, and `.cursor-plugin/plugin.json`; skills default to `skills/`, MCP to `.mcp.json`, hooks to `hooks/hooks.json` [E3].
- Display metadata lives in an `interface` object (`displayName`, `shortDescription`, `longDescription`, `developerName`, `category`, `capabilities`, `websiteURL`, `defaultPrompt`, `brandColor`, `logo`, and others), in `.codex-plugin/plugin.json` or under `extensions["com.openai"]`; OpenAI's directory submission checks stricter limits than the CLI [E3] [E6].
- A root `plugin.json` without the Agent Plugins `$schema` is ignored, and Codex falls back to the compatibility manifests [E6].
- When a plugin carries both a portable root `plugin.json` and `.claude-plugin/plugin.json`, Codex installs the root manifest's version and reads `mcp.json`, not `.mcp.json` [E9] [E14].
- In the compatibility format, a manifest `mcpServers` path replaces the default `.mcp.json`: only the named file's servers are configured [E12].
- Manifest paths must start with `./` and stay inside the plugin; a path that breaks this is ignored with a warning, not an error [E3] [E6].

## Claude Code plugins in Codex

- Not supported: `commands` as commands, `agents`, `userConfig` and `${user_config.*}`, `outputStyles`, `lspServers`, `channels`, `dependencies`, and prompt or agent hook handlers [E5].
- A command whose frontmatter has a non-empty `description` is migrated on install into a skill named `source-command-<name>`, capped at 4,000 bytes [E5] [E11] [E12].
- A plugin's agent does not appear among the components Codex presents to the model [E12].
- `${CLAUDE_PLUGIN_ROOT}` and `${user_config.*}` in an MCP server's arguments are passed to the server literally, not expanded [E10] [E12].
- Hook commands receive `PLUGIN_ROOT` and `PLUGIN_DATA`, plus `CLAUDE_PLUGIN_ROOT` and `CLAUDE_PLUGIN_DATA` for compatibility, and plugin hooks run only after the user trusts them [E3].

## Install, cache, and updates

- `codex plugin marketplace add <path | owner/repo[@ref] | git URL>` registers a marketplace in `config.toml`; a git marketplace is cloned to `$CODEX_HOME/.tmp/marketplaces/<name>` [E4] [E13].
- `codex plugin add <plugin>@<marketplace>` copies the plugin to `$CODEX_HOME/plugins/cache/<marketplace>/<plugin>/<version>/`, where `<version>` is the manifest's `version`, else `local` (compatibility) or `1.0.0` (portable) [E4].
- The whole plugin directory is copied, not only the files its manifest names, so load-check a clean export (`git archive`) rather than a working tree with build output in it [E12].
- `codex plugin marketplace upgrade [<name>]` refreshes a git marketplace and replaces installed copies in place, delivering a pushed change even when the version did not change [E13].
- There is no project auto-discovery to rely on in the CLI: in a fresh repository `codex plugin marketplace list` printed no marketplaces until one was added [E4].

## Checking

- There is no `validate` command; the local check is `codex plugin marketplace add <root>` then `codex plugin list --available --json`, compared entry by entry with the catalog [E6].
- `CODEX_HOME` must exist before Codex runs, and even `codex --version` and `--help` write temporary state into it, so point it at a throwaway directory first (R15) [E11] [E15].
- `codex mcp list --json` shows each configured plugin MCP server, unexpanded, and starts nothing [E12] [E14].
- `codex debug prompt-input` lists the skills Codex would present, including migrated commands, without contacting a model, but it starts plugin MCP servers and includes the working directory's `AGENTS.md`; run it only on a stand-in plugin you wrote, from inside the throwaway directory (R15) [E12].

## Provenance

Verified against: codex-cli 0.157.1 (source reading and probes) on 2026-09-28.
Conformance probes: `codex-migrates-described-commands`, `codex-prefers-agents-catalog`, `codex-reads-claude-catalog`, `codex-reads-portable-root`, `codex-skips-github-source`.

| Id | Evidence | Kind |
| --- | --- | --- |
| E1 | https://developers.openai.com/plugins/build/plugins.md, fetched 2026-09-27; `docs/research/2026-09-27-codex.md` §1; re-verified 2026-09-28, `docs/research/2026-09-28-documentation-reverification.md` | docs |
| E2 | `openai/codex` at `659b35f1316eda27ef61850dd0832c4a4e95c120`: `codex-rs/core-plugins/src/marketplace.rs`, `core-plugins/src/store.rs`, `core-plugin-common/src/plugin_id.rs`, and a probe on codex-cli 0.157.1; `docs/research/2026-09-27-codex.md` §1 | source |
| E3 | the same commit: `utils/plugins/src/plugin_namespace.rs`, `core-plugins/src/agent_plugin_manifest.rs`, `core-plugins/src/manifest.rs`, and https://developers.openai.com/plugins/build/plugins.md; `docs/research/2026-09-27-codex.md` §2; re-verified 2026-09-28, `docs/research/2026-09-28-documentation-reverification.md` | source |
| E4 | the same commit (`installed_marketplaces.rs`, `store.rs`, `manager.rs`) and probes on codex-cli 0.157.1; `docs/research/2026-09-27-codex.md` §3 | source |
| E5 | https://developers.openai.com/plugins/guides/submit-claude-plugin.md, fetched 2026-09-27, and `core-plugins/src/command_migration*.rs` at the same commit; `docs/research/2026-09-27-codex.md` §4; re-verified 2026-09-28, `docs/research/2026-09-28-documentation-reverification.md` | docs |
| E6 | `docs/research/2026-09-27-codex.md` §5 | source |
| E7 | plan-2b baseline s7-r3, call 9: `github` entries dropped, `url` and `git-subdir` listed; `tests/runs/evidence/2026-09-28-s7-r3-tool-results.jsonl` | run |
| E8 | plan-2b baseline s6-r2, call 8; `tests/runs/evidence/2026-09-28-s6-r2-tool-results.jsonl` | run |
| E9 | plan-2b baseline s2-r3, call 7; `tests/runs/evidence/2026-09-28-s2-r3-tool-results.jsonl` | run |
| E10 | plan-2b baseline s1-r2, call 22; `tests/runs/evidence/2026-09-28-s1-r2-tool-results.jsonl` | run |
| E11 | Codex command-migration probe on codex-cli 0.157.1; `docs/research/2026-09-28-codex-command-migration-probe.md` | probe |
| E12 | probe P1 on codex-cli 0.157.1; `docs/research/2026-09-28-load-and-update-probes.md` | probe |
| E13 | probe P2 on codex-cli 0.157.1; `docs/research/2026-09-28-load-and-update-probes.md` | probe |
| E14 | probe P4 on codex-cli 0.157.1; `docs/research/2026-09-28-load-and-update-probes.md` | probe |
| E15 | plan-2b home snapshots: temporary state from exempt `codex --version` and `--help` calls; `tests/runs/2026-09-28-baseline-summary-2b.md`, Isolation | run |
