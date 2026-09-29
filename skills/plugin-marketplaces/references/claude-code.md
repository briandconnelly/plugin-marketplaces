# Claude Code

What Claude Code reads from a user-hosted marketplace and its plugins.
Rules are cited by id from [SKILL.md](../SKILL.md); each fact cites a row of the Provenance table.

## Catalog

- The catalog is `<root>/.claude-plugin/marketplace.json`; relative sources resolve from `<root>`, the directory holding `.claude-plugin/` [E1].
- Required top-level fields are `name`, `owner` (with `owner.name`), and `plugins`; each entry is validated on its own, so one bad entry does not fail the catalog [E1].
- Unknown keys are ignored at load, so a typo loads silently; only `claude plugin validate` warns about them [E1].
- `metadata.pluginRoot` (v2.1.239+) lets a bare name such as `"foo"` resolve under it; without it a source needs `./` [E1].
- `renames` (v2.1.193+) maps an old plugin name to its new name or to `null`, and `forceRemoveDeletedPlugins: true` uninstalls plugins removed from the catalog (R9) [E1].
- There is no catalog field that turns on auto-update; users or admins enable it per marketplace, and it is off by default for third-party marketplaces [E3].

## Entries

- Required entry fields are `name` and `source`; an entry also accepts every `plugin.json` field [E1].
- The entry `name` is the install id (`<name>@<marketplace>`) and the `enabledPlugins` key, and the manifest `name` prefixes the plugin's components; a mismatch does not block install by the entry name: `claude plugin list` and the cache directory then use the entry name while `claude plugin details` heads its output with the manifest name, and installing by the manifest name fails with `Plugin "<x>" not found in marketplace` (R8) [E3] [E13] [E15]
- When the plugin has its own `plugin.json`, entry `mcpServers`, `lspServers`, `userConfig`, and `channels` are ignored, and entry display fields override the manifest's [E1].
- `strict` (default `true`) makes `plugin.json` the authority and appends entry component fields to it, except `hooks`, whose matchers replace the manifest's per event; with `strict: false`, an entry that declares any component field while `plugin.json` also exists fails with `conflicting manifests` [E1].
- Entry `hooks` must be an inline object: an entry giving `hooks` as a path or array passes `claude plugin validate`, installs, and then fails to load with "the file-path and array forms are not yet supported in a marketplace entry" [E1] [E5].
- The inline object is the event map itself (`{"SessionStart": [...]}`); `claude plugin validate` rejects the wrapped form a `hooks/hooks.json` file uses (`{"hooks": {...}}`) with `plugins.<n>.hooks: Invalid input` [E14].

## Sources

| Source | Shape | Pin |
| --- | --- | --- |
| Relative path | `"./plugins/foo"`; `"."` is the root; no `..`, no backslashes | none needed |
| `github` | `{"source": "github", "repo": "owner/repo", "ref"?, "sha"?}` | `sha`, 40 lowercase hex |
| `url` | `{"source": "url", "url": "https://…" or "git@…" or "file://…", "ref"?, "sha"?}` | `sha` |
| `git-subdir` | `{"source": "git-subdir", "url", "path", "ref"?, "sha"?}` | `sha` |
| `npm` | `{"source": "npm", "package", "version"?, "registry"?}` | exact `version` |
| `archive` (v2.1.224+) | `{"source": "archive", "url": "https://…zip", "sha256"?}` | `sha256` |
| `command` (v2.1.229+) | `{"source": "command", "command", "timeout"?, "mode"?}` | cannot be pinned |

The table's shapes and pins are from [E1]; when both `ref` and `sha` are set, `sha` is checked out, which works even after the `ref` is deleted while the commit is still reachable, except on hosts that cannot fetch a commit by SHA [E1].
Relative paths do not resolve when the catalog itself is fetched as a bare `marketplace.json` URL; host such a catalog in a git repository instead [E10].

## Manifest

- The manifest is `<plugin>/.claude-plugin/plugin.json`, and it is optional: without it, components are auto-discovered and the name comes from the entry [E2].
- Only `name` is required; `version` is any string, not checked as semver [E2].
- Claude Code does not read a portable root `plugin.json` or `mcp.json`; from a plugin carrying both formats it reads only `.claude-plugin/plugin.json` and `.mcp.json` [E9].
- Default component locations are `skills/<name>/SKILL.md`, `commands/`, `agents/`, `hooks/hooks.json`, `.mcp.json`, `.lsp.json`, `output-styles/`, `workflows/`, `themes/`, `monitors/monitors.json`, `bin/`, and `settings.json` [E2].
- Declaring `commands`, `agents`, `outputStyles`, `workflows`, `experimental.themes`, or `experimental.monitors` replaces the default directory, `skills` adds to it, and `hooks`, `mcpServers`, and `lspServers` merge with the default file, which loads first [E2] [E7].
- Every manifest path starts with `./` and must exist inside the plugin root, except that `skills` also accepts `"."` and `mcpServers` an `https://` bundle URL; `..` fails validation and a symlink leading outside is rejected [E2].
- `${CLAUDE_PLUGIN_ROOT}` (the installed copy, which changes on every update) and `${CLAUDE_PLUGIN_DATA}` (persistent) expand in hook commands, MCP and LSP server `command`, `args`, and `env`, and skill, command, and agent bodies [E2] [E7].
- `userConfig` values are referenced as `${user_config.KEY}`; `sensitive` options are stored in the system keychain, which `CLAUDE_CONFIG_DIR` does not isolate [E2] [E11].
- Files outside the plugin directory are not copied into the cache, so a path such as `../shared` breaks after install; a symlink inside the plugin to elsewhere in the same marketplace is dereferenced and its target copied, and one leading outside the marketplace is skipped [E10].

## Names

- Marketplace names may not contain spaces, `/`, `\`, `..`, or control characters; a list of official names, `npm`, `github`, and similar words, and the `claudeai-` prefix are reserved, and some reserved spellings pass `validate` but fail at `marketplace add` [E1] [E3] [E4].
- Plugin names are kebab-case with no spaces, `@`, `:`, or path separators [E2].

## Versions and updates

- The installed version is, in order: `plugin.json` `version`, the entry's `version`, otherwise a value derived from the source (a 12-character commit SHA for git sources and for relative paths in a git-hosted catalog) [E3].
- An explicit version holds every user on the cached copy until the string changes: a pushed change without a bump is refused with `already at the latest version`, and a bumped one is delivered by `claude plugin update` [E3] [E8].
- To deliver every commit instead, omit `version` everywhere; setting it in both `plugin.json` and the entry invites disagreement (R6) [E3].
- Installed plugins are copied to `~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/`; a relative-path plugin from a catalog added as a local directory loads in place [E3].
- Private repositories are fetched with the machine's existing git credentials; there is no token field [E3].

## `claude plugin validate`

- `claude plugin validate <path> [--strict] [--json]` checks the catalog at `<path>/.claude-plugin/marketplace.json` if present, otherwise the plugin manifest, otherwise (from claude 2.1.233) the component files the directory's name implies [E4].
- Exit codes: 0 passed or passed with warnings, 1 failed or any warning under `--strict`, 2 validator failure [E4].
- A catalog entry version that differs from its manifest is a warning, so the plain run passes and `--strict` fails [E4] [E6].
- It does not catch an entry `hooks` path or array, a relative source whose directory does not exist, a wrong remote repository or path, or exact reserved names; it does not open plugin skill, agent, command, hook, or MCP files from a catalog run [E4].
- It writes `.claude.json` into its configuration directory, so run it with a throwaway `CLAUDE_CONFIG_DIR` (R15) [E12].

## Seeing what loaded

- `claude plugin details <plugin>@<marketplace>` lists skills (commands counted as skills), agents, hooks, MCP servers, and LSP servers, and starts nothing [E7].
- `claude plugin list --json` shows each installed plugin's version and MCP server configuration, and starts nothing [E7].
- `claude mcp list` health-checks every server, which starts plugin MCP servers and so runs plugin code; use it only on a stand-in plugin you wrote (R15) [E7].

## Provenance

Verified against: claude 2.1.283 (documentation reading) and 2.1.284 (probes) on 2026-09-28.
Conformance probes: `claude-lists-commands-as-skills`, `claude-reads-adapter-not-portable-root`, `claude-validate-misses-entry-hooks-path`.

| Id | Evidence | Kind |
| --- | --- | --- |
| E1 | https://code.claude.com/docs/en/plugins/marketplace-reference and https://code.claude.com/docs/en/plugins/create-marketplace, fetched 2026-09-27; `docs/research/2026-09-27-claude-code.md` §1; re-verified 2026-09-28, `docs/research/2026-09-28-documentation-reverification.md` | docs |
| E2 | https://code.claude.com/docs/en/plugins/manifest-reference, fetched 2026-09-27; `docs/research/2026-09-27-claude-code.md` §2; re-verified 2026-09-28, `docs/research/2026-09-28-documentation-reverification.md` | docs |
| E3 | https://code.claude.com/docs/en/plugins/loading, https://code.claude.com/docs/en/plugins/host-marketplace, and https://code.claude.com/docs/en/settings-reference, fetched 2026-09-27; `docs/research/2026-09-27-claude-code.md` §3; re-verified 2026-09-28, `docs/research/2026-09-28-documentation-reverification.md` | docs |
| E4 | https://code.claude.com/docs/en/plugins/cli-reference#plugin-validate, fetched 2026-09-27, and probes on claude 2.1.283; `docs/research/2026-09-27-claude-code.md` §4; re-verified 2026-09-28, `docs/research/2026-09-28-documentation-reverification.md` | docs |
| E5 | plan-2b baseline s6-r2, call 11: install of an entry with `hooks` as a path; `tests/runs/evidence/2026-09-28-s6-r2-tool-results.jsonl` | run |
| E6 | plan-2b baselines s7-r1 to s7-r3, objective checks; `tests/runs/2026-09-28-s7-r1-baseline.md` | run |
| E7 | probe P1 on claude 2.1.284; `docs/research/2026-09-28-load-and-update-probes.md` | probe |
| E8 | probe P2 on claude 2.1.284; `docs/research/2026-09-28-load-and-update-probes.md` | probe |
| E9 | probe P4 on claude 2.1.284; `docs/research/2026-09-28-load-and-update-probes.md` | probe |
| E10 | https://code.claude.com/docs/en/plugins/host-marketplace, fetched 2026-09-27; `docs/research/2026-09-27-claude-code.md` §5; re-verified 2026-09-28, `docs/research/2026-09-28-documentation-reverification.md` | docs |
| E11 | plan-2b baselines s4-r4, s4-r7, s4-r8, and s4-r9: `claude plugin install --config` with a sensitive value tried the macOS keychain; `tests/runs/2026-09-28-baseline-summary-2b.md`, Isolation | run |
| E12 | observed in plan 1 and recorded where the validator isolates it: `skills/plugin-marketplaces/scripts/mpcheck/checks_schema.py`, `_default_runner` | source |
| E13 | plan-2c with-skill runs of scenario 6 on claude 2.1.284 (`install lint@acme-tools` succeeded and `details` showed `linter`; `install linter@acme-tools` gave not found); `tests/runs/evidence/2026-09-28-s6-r1-with-skill-tool-results.jsonl` and `tests/runs/evidence/2026-09-28-s6-r3-with-skill-tool-results.jsonl` | run |
| E14 | plan-3 probes on claude 2.1.284; `docs/research/2026-09-28-plan-3-probes.md`, Entry `hooks` forms | probe |
| E15 | probe on claude 2.1.284 (entry `lint`, manifest `linter`); `docs/research/2026-09-28-documentation-reverification.md`, Entry and manifest names | probe |
