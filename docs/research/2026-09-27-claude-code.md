## Claude Code plugin marketplace and plugin format reference (live docs, fetched 2026-09-27; local CLI 2.1.283)

Legend: **[R]** means I read it in the docs. **[P]** means I observed it by running a command. **[I]** means I inferred it.

**Docs moved.** The page you pointed me to (https://code.claude.com/docs/en/plugin-marketplaces) is now "Create a marketplace". Canonical pages sit under `/docs/en/plugins/…`: `create-marketplace`, `marketplace-reference`, `manifest-reference`, `host-marketplace`, `loading`, `cli-reference`, `org`, `dependencies`. Settings keys are documented at `/docs/en/settings-reference`. Adding `.md` to any URL returns raw markdown, and `https://code.claude.com/docs/llms.txt` is the index.

**Scratchpad hazard.** A sibling agent appears to share this scratchpad. My copy of `scratchpad/plugins.md` was overwritten with OpenAI/Codex plugin docs, which reference `agent-plugins.org` schemas. That content is not Claude documentation and I excluded it. The live page is correct: I re-fetched it and its title is "Plugins overview". Other agents should write into their own subdirectories.

---

### 1. marketplace.json
Sources: https://code.claude.com/docs/en/plugins/marketplace-reference and https://code.claude.com/docs/en/plugins/create-marketplace

**Location [R]**
- The file lives at `<root>/.claude-plugin/marketplace.json`.
- The "marketplace root" is the directory that contains `.claude-plugin/`. Relative plugin sources resolve from the root, not from `.claude-plugin/`.
- A file stored elsewhere is only reachable through `extraKnownMarketplaces` with `path` set on a `github` or `git` source. `claude plugin marketplace add` has no option for it.

**Unknown keys [R][P]**
- Unknown top-level or entry keys are ignored at load, so a typo loads silently.
- `validate` reports them as warnings (`Unknown field 'x'. Claude Code ignores it at load time.`).

**Top-level fields [R].** Required: `name`, `owner`, `plugins`.

| Field | Type | Notes |
|---|---|---|
| `name` | string | No spaces, control or bidi characters, `/`, `\` or `..`, and not `.`. Users type it after `@`. |
| `owner` | object | `name` is required; `email` and `url` are optional. |
| `plugins` | array | Each entry is validated on its own, so one bad entry doesn't fail the marketplace. |
| `$schema` | string | Editor autocomplete only; ignored at load. |
| `description` | string | `validate` warns when it's missing. |
| `version` | string | Marketplace manifest version. |
| `metadata.description`, `metadata.version` | string | Alternate location for `description` and `version`. |
| `metadata.pluginRoot` | string | Directory that bare-name sources resolve under (v2.1.239+). |
| `forceRemoveDeletedPlugins` | bool | When `true`, a plugin removed from `plugins` is uninstalled on users' machines. |
| `allowCrossMarketplaceDependenciesOn` | string[] | Marketplace names whose plugins may be installed as dependencies. |
| `renames` | object | Maps an old plugin name to its new name, or to `null` for a removed plugin (v2.1.193+). |

**Plugin entry fields [R].** Required: `name`, `source`. An entry also accepts every `plugin.json` field.
- `name`: string, no spaces. It is the install id `<entry-name>@<marketplace>` and the `enabledPlugins` key.
- `source`: string or object (variants below).
- `description`, `category`, `tags` (string[]), `displayName`.
- `version`: `plugin.json` wins over it, and `validate` warns on a mismatch.
- `strict`: bool, default `true`.
- `relevance`: object with `topic` and `signals`, used for plugin suggestions.
- `dependencies`: array.
- `defaultEnabled`: bool, default `true`. The entry value overrides `plugin.json`.
- `metadata`: free-form, not read by Claude Code (v2.1.222+).
- `headers` and `headersHelper`: only for `archive` sources (v2.1.238+). `headersHelper` also requires `"strict": false`.

**How an entry combines with `plugin.json` [R]**
- If the fetched plugin has no `plugin.json`, the entry is the manifest, whatever `strict` says.
- If `plugin.json` is present:
  - Entry `mcpServers`, `lspServers`, `userConfig` and `channels` are ignored; declare them in `plugin.json`.
  - Display fields (`displayName`, `description`, `author`, `homepage`, `repository`, `license`, `keywords`) on the entry override `plugin.json`.
  - Before install, `plugin.json` display fields are visible only for relative-path sources.
- Entry `hooks` must be an inline object. A file path or array passes `validate`, but those hooks never run and the plugin shows a "not yet supported in a marketplace entry" error.

**Strict mode [R].** It only matters when `plugin.json` exists and the entry declares component fields (`commands`, `agents`, `skills`, `hooks`, `outputStyles`, `themes`).
- `true` (default): `plugin.json` is the authority. The entry's component fields are appended to it, except `hooks`, where the entry's matchers replace the manifest's per event.
- `false`: an entry with no component fields behaves like `true`. An entry with any component field is a conflict, and the plugin fails with `Plugin <name> has conflicting manifests: both plugin.json and marketplace entry specify components`.

**Plugin `source` variants [R].** Object form is `"source": {"source": "<type>", ...}`.

- **Relative path string**, e.g. `"./plugins/foo"`.
  - Must start with `./`. `"."` alone means the root.
  - Must not contain `..`.
  - No backslashes on macOS or Linux.
  - Bare names like `"foo"` work only when `metadata.pluginRoot` is set, and a name containing `/` still needs `./`.
  - Relative paths don't resolve for a `url` marketplace source and are rejected for a `settings` source.
- **`github`**: `{"source":"github","repo":"owner/repo","ref"?,"sha"?}`.
- **`url`** (a git repo): `{"source":"url","url":"https://…|http://…|file://…|git@…","ref"?,"sha"?}`. No `.git` suffix needed and no `owner/repo` shorthand.
- **`git-subdir`**: `{"source":"git-subdir","url":"<git url or owner/repo>","path":"tools/foo","ref"?,"sha"?}`. Fetched with a sparse partial clone.
- **`npm`**: `{"source":"npm","package":"@org/foo","version"?:"^2.0.0","registry"?:"https://…"}`.
  - Install scripts never run.
  - Dependencies install from the lockfile only, with scripts disabled.
- **`archive`** (v2.1.224+): `{"source":"archive","url":"https://…zip","sha256"?:"<64 hex>"}`.
  - HTTPS only; no loopback or metadata hosts.
  - The plugin root may be at the top of the zip or one level down.
- **`command`** (v2.1.229+): `{"source":"command","command":"…","timeout"?:1-600 (default 60),"mode"?:"copy"|"link"}`.
  - The command runs on the user's machine and must print one absolute directory path.
  - It re-runs once per session.
  - `link` mode is refused on Windows.
- **No `pip` plugin source exists [R].** `pip` is only a reserved marketplace name.

**Pinning [R]**
- `ref` is a branch or tag; the default is the repo's default branch.
- `sha` must be a full 40-character lowercase SHA. When both are set, `sha` is checked out, which works even if `ref` was deleted (except on hosts like CodeCommit).

**Marketplace sources** (these go in settings or are built by `marketplace add`; different from plugin sources) [R]:
- `github`: `repo`, `ref`, `path`, `sparsePaths`.
- `git`: `url`, `ref`, `path`, `sparsePaths`.
- `url`: a direct link to a `marketplace.json`, with `headers` and `headersHelper`.
- `file`: `path` to the json file.
- `directory`: `path` to the marketplace root.
- `settings`: an inline catalog with `name`, `plugins`, `owner`. Its entries need object sources.
- `npm`: not implemented.
- Policy-only forms: `hostPattern`, `pathPattern`, `skills-dir`, and `repo: "owner/*"`.
- `path` defaults to `.claude-plugin/marketplace.json`.
- `skipLfs` is accepted and does nothing; LFS content is never fetched.

### 2. plugin.json
Source: https://code.claude.com/docs/en/plugins/manifest-reference

**Location [R]**
- `<plugin-root>/.claude-plugin/plugin.json`. Everything else goes at the plugin root, not inside `.claude-plugin/`.
- The manifest is optional. Without it, components are auto-discovered and the name comes from the marketplace entry, or from the directory name under `--plugin-dir`.

**Fields [R].** Only `name` is required.
- `$schema`
- `name`: kebab-case; no spaces, `@`, `:`, path separators, control or bidi characters.
- `displayName`
- `version`: a string not checked against semver.
- `description`
- `author`: `{name (required), email?, url?}`
- `homepage`: must parse as a URL, or the plugin fails to load.
- `repository`: not validated.
- `license`: SPDX identifier.
- `keywords`: string[].
- `metadata`: free-form.
- `defaultEnabled`: default `true`.
- `dependencies`: `"name"`, `"name@mkt"`, or `{name, marketplace?, version?: semver range}`.
- `settings`: only `agent` and `subagentStatusLine` take effect.
- `userConfig` and `channels`.
- Component fields: `skills`, `commands`, `agents`, `hooks`, `mcpServers`, `lspServers`, `outputStyles`, `workflows`.
- `experimental.{themes, monitors, evals}`. Top-level `themes` or `monitors` still load, with a warning.

**Strictness [R].** Unknown top-level keys are stripped with a warning. An unknown key inside a `userConfig` option, a `channels` entry, an `lspServers` config or a `monitors` entry is an error, and the plugin doesn't load.

**Default layout [R]**

| Component | Default location |
|---|---|
| Skills | `skills/<name>/SKILL.md` (a root `SKILL.md` with no `skills/` loads as a single skill) |
| Commands | `commands/` (legacy; prefer skills) |
| Agents | `agents/` |
| Hooks | `hooks/hooks.json` |
| MCP servers | `.mcp.json` |
| LSP servers | `.lsp.json` |
| Output styles | `output-styles/` |
| Workflows | `workflows/` |
| Themes | `themes/` |
| Monitors | `monitors/monitors.json` |
| Executables | `bin/` (added to the Bash tool's PATH; claude.ai and Cowork refuse plugins with a top-level `bin/`) |
| Settings | `settings.json` |

A root `CLAUDE.md` is not loaded, and `validate` warns about it.

**How component keys combine with the defaults [R]**
- Replace the default directory: `commands`, `agents`, `outputStyles`, `workflows`, `experimental.themes`, `experimental.monitors`. There is a warning if the default folder also exists.
- Add to the default: `skills`.
- Merge with the default file: `hooks`, `mcpServers`, `lspServers`. The default file loads first, and a later server name replaces an earlier one.

**Shapes [R]**
- `agents` must list `.md` files; directories are not accepted.
- `skills` entries must be directories.
- `commands` can also be a map of name to `{source | content, description?, argumentHint?, model?, allowedTools?}`, with exactly one of `source` or `content`.
- `mcpServers` also accepts `.mcpb` or `.dxt` bundle paths or HTTPS URLs.
- `lspServers` requires `command` and `extensionToLanguage`.

**Path rules [R]**
- Every path is relative to the plugin root and must start with `./`.
- Exceptions: `skills` also accepts `"."`, and `mcpServers` also accepts an `https://` bundle URL.
- Paths must resolve inside the plugin root and must exist. `..` fails `validate`, and a symlink leading outside the plugin is rejected with "path escapes plugin directory".

**Variables [R]**
- `${CLAUDE_PLUGIN_ROOT}` is the installed version's path. It changes on every update, so don't write state there.
- `${CLAUDE_PLUGIN_DATA}` is `~/.claude/plugins/data/<id>/`. It persists across updates and is deleted when the plugin is uninstalled from its last scope, unless `--keep-data` is passed.
- `${CLAUDE_PROJECT_DIR}` is the project root.
- Where they resolve:
  - Hooks: `command` and `args`.
  - MCP stdio servers: `command`, `args`, `env`.
  - MCP http, sse and ws servers: `url`, `headers`, `headersHelper`.
  - LSP servers: `command`, `args`, `env`, `workspaceFolder`.
  - Skill, command and agent bodies: anywhere in the Markdown body.
- None of them are present in Bash tool commands.
- Quote them in shell-form hooks; `validate` warns about unquoted uses.

**userConfig [R]**
- Keys are identifiers.
- Required fields per option: `type` (`string`, `number`, `boolean`, `directory`, `file`), `title`, `description`.
- Optional fields: `required`, `default`, `options` (v2.1.271+), `multiple`, `sensitive` (stored in the keychain), `min`, `max`.
- Non-sensitive values are stored under `pluginConfigs` in settings.
- Reference a value as `${user_config.KEY}` in MCP and LSP config, exec-form hook args, and skill or agent content.
- Hooks also get `CLAUDE_PLUGIN_OPTION_<KEY>` in their environment.
- Shell-form hooks, monitors and MCP `headersHelper` reject `${user_config.*}`.

**Dependencies** (https://code.claude.com/docs/en/plugins/dependencies) [R]
- A version range resolves against git tags named `<plugin>--v<version>`. `claude plugin tag --push` creates the tag and checks version agreement between `plugin.json` and the entry.
- For `npm`, `archive` and `command` sources, the range is checked against the dependency's `plugin.json` version instead.

### 3. Names, versioning, updates, auth, team distribution
Sources: https://code.claude.com/docs/en/plugins/loading, https://code.claude.com/docs/en/plugins/host-marketplace, https://code.claude.com/docs/en/settings-reference

**Reserved marketplace names [R]**
- Official names, reserved unless the source is under `github.com/anthropics/`: `claude-code-marketplace`, `claude-code-plugins`, `claude-plugins-official`, `anthropic-marketplace`, `anthropic-plugins`, `agent-skills`, `anthropic-agent-skills`, `life-sciences`, `knowledge-work-plugins`, `claude-for-legal`, `claude-for-financial-services`, `financial-services-plugins`, `first-party-plugins`, `claude-tag-plugins`.
- Community and directory names under the same rule: `claude-community`, `claude-plugins-community`, `healthcare`, `anthropic-plugin-directory`, `claude-plugin-directory`.
- Always reserved: `inline`, `builtin`, `skills-dir`, `synced`, `claude-plugin-test`.
- Reserved in any casing: `npm`, `pip`, `uv`, `cargo`, `github`, `gh`.
- The `claudeai-` prefix is reserved.
- Impersonating names (e.g. `official-claude-plugins`) and any non-ASCII name are rejected.
- Alternate spellings of a reserved name pass `validate` but fail on add (v2.1.280+).
- Claude Desktop is stricter: `[A-Za-z0-9._-]`, must start alphanumeric, at most 128 characters. `validate` warns about this.

**Entry name vs manifest name [R]**
- The entry name is the install id and the `enabledPlugins` key.
- The manifest name is the namespace prefix for components.
- Keep the two identical; a mismatch causes `Plugin "<x>" not found in marketplace`.

**Version resolution [R]** (all source types except `command`):
1. `plugin.json` `version`.
2. The entry's `version`.
3. Otherwise, derived from the source:
   - git-based sources: 12-character commit SHA (`git-subdir` adds a hash of the path).
   - `archive`: 12 characters of the sha256.
   - Relative path in a git-hosted marketplace: commit SHA.
   - Non-git local directory: `unknown`.
   - `npm`: `unknown`.

A `command` source's version is always a hash of its output, or `<manifest version>-<hash>`.

**Consequences for updates [R]**
- A pinned `"version"` holds every user on the cached copy until the string changes, no matter how many commits are pushed.
- Either bump `version` on each release or omit it everywhere to track commits.
- Don't set it in both `plugin.json` and the entry.
- `claude plugin update` skips a plugin whose computed version is unchanged.

**Caching [R]**
- Installed plugins are copied to `~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/`.
- Relative-path plugins from a marketplace added as a local directory load in place: edits apply on the next session or `/reload-plugins`, with no version bump.
- Old version directories are removed 14 days after being marked orphaned.
- Node dependencies install only when `package.json` and an npm or bun lockfile are both present: `npm ci --ignore-scripts` or `bun install --frozen-lockfile --ignore-scripts`, with a 60 s timeout.

**Auto-update [R]**
- Off by default for third-party marketplaces, and `marketplace.json` has no field to turn it on.
- A user toggles it under `/plugin` Marketplaces, or an admin sets `"autoUpdate": true` on the `extraKnownMarketplaces` entry.
- It runs up to 10 minutes after the first message.
- Manual updates: `/plugin marketplace update <name>` or `claude plugin update <plugin>@<mkt>`.
- Environment variables that disable it: `DISABLE_UPDATES`, `DISABLE_AUTOUPDATER`, `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC`. `FORCE_AUTOUPDATE_PLUGINS=1` overrides them.

**Private repos [R]**
- Claude Code runs non-interactive `git` with the machine's existing credentials; there is no token field.
- For `owner/repo`, it probes SSH first and falls back to HTTPS. `CLAUDE_CODE_PLUGIN_PREFER_HTTPS=1` skips the probe.
- SSH keys must already be in the agent and the host must be in `known_hosts`.
- HTTPS needs a credential helper that already holds a credential, e.g. `gh auth setup-git`. A bare `GITHUB_TOKEN` works only through a helper.
- `CLAUDE_CODE_PLUGIN_KEEP_MARKETPLACE_ON_FAILURE=1` keeps the existing checkout when a background update can't authenticate.

**Team distribution [R]**
- `extraKnownMarketplaces` maps a name to `{source, autoUpdate?}`.
  - It can go in any settings file.
  - Project-level entries apply only after the workspace trust dialog is accepted.
  - The highest-precedence file's entry replaces lower ones whole (v2.1.228+).
  - Alias: `additionalMarketplaces`.
- `enabledPlugins` maps `"plugin@marketplace"` to a boolean.
  - Project settings override user settings; opt out in `settings.local.json`.
  - A managed `false` blocks the plugin everywhere.
  - Plugins with relative-path sources load once the marketplace is registered.
  - Plugins with external sources still need each user to run `claude plugin install … --scope project`.
- `strictKnownMarketplaces` is a managed-only allowlist of source objects (alias `allowedMarketplaces`).
  - An empty array blocks every marketplace.
  - Any allowlist stops skills-dir plugins unless `{"source":"skills-dir"}` is listed.
- Other managed keys: `blockedMarketplaces`, `disableCommandPluginSources`.
- Shortcut: `claude plugin marketplace add owner/repo --scope project`, then commit `.claude/settings.json`.

### 4. Validation tooling
Source: https://code.claude.com/docs/en/plugins/cli-reference#plugin-validate

**Commands [R]**
- `claude plugin validate <path> [--strict] [--json]`. `--strict` needs v2.1.145+ and `--json` needs v2.1.259+.
- `/plugin validate <path>` inside a session prints the same report inline.

**What `<path>` selects [R]**
- `.claude-plugin/marketplace.json` if it exists.
- Otherwise `.claude-plugin/plugin.json`.
- Otherwise component files (skills, agents, commands directories), v2.1.233+.

**Exit codes [R]**
- `0`: passed, or passed with warnings.
- `1`: failed, or any warning under `--strict`.
- `2`: the validator itself failed.

**Checks, marketplace run [R]**
- JSON syntax, required fields and name rules.
- Duplicate plugin names.
- A source that is `Invalid input` (e.g. missing `./`) or contains `..`.
- `renames` chains that don't resolve.
- Warnings:
  - unknown fields;
  - missing `description`;
  - entry `version` differs from `plugin.json`;
  - `headers` on a non-archive entry;
  - a local source that is a symlink;
  - Desktop name incompatibilities.
- It also validates the `plugin.json` of each relative-path plugin (`plugins[N] plugin.json → …`).
- It does **not** open plugin skill, agent, command, hook or MCP files; validate each plugin directory separately for those.

**Checks, plugin run [R]**
- Type mismatches.
- Paths that are missing or escape the plugin root.
- Unknown keys in strict sub-objects.
- Skill, agent and command frontmatter.
- MCP entries (v2.1.281+).
- Warnings: non-kebab-case `name`; missing `version`, `description` or `author`; root `CLAUDE.md`; unquoted `${CLAUDE_PLUGIN_ROOT}` in shell hooks.
- Symlinks inside the directory are not followed.

**Not caught by `validate` [R]**
- An entry `hooks` written as a path or array.
- A relative source pointing at a directory that doesn't exist; this fails at install with `Source path does not exist`.
- Wrong repo or path in a remote source.
- The exact reserved official names; these fail at `marketplace add`.

**Probe results [P]** (claude 2.1.283, test marketplace in `scratchpad/mkt-agent/m`)
- `"source":"plugins/p2"` (no `./`) gave `plugins.1.source: Invalid input`.
- `"./../x"` gave `Path contains ".."`, with the hint that paths resolve from the marketplace root.
- An entry `version` of 2.0.0 against `plugin.json` 1.0.0 gave a warning citing "calculatePluginVersion precedence".
- An unknown `plugin.json` field was reported through the marketplace run.
- Exit code was 1.
- The missing-`description` warning did not appear while errors were present. It did appear on a clean run: `passed with warnings`, exit 0.
- The same clean run with `--strict` failed with exit 1.

**JSON Schema**
- `anthropics/claude-plugins-official/.claude-plugin/marketplace.json` declares `"$schema": "https://anthropic.com/claude-code/marketplace.schema.json"` [P, via `gh api`]. That URL returns **404** (it redirects to www.anthropic.com) [P]. `https://anthropic.com/claude-code/plugin.schema.json` is also a 404 [P].
- The docs say `$schema` is used only for editor autocomplete and name no URL [R].
- SchemaStore has working schemas [P]. They are community-maintained, not referenced by Anthropic docs [I], and their `$comment` says generated 2026-04-23, so they may lag the docs [I].
  - `https://json.schemastore.org/claude-code-marketplace.json`, matching `**/.claude-plugin/marketplace.json`.
  - `https://json.schemastore.org/claude-code-plugin-manifest.json`, matching `**/.claude-plugin/plugin.json`.

### 5. Best practices and gotchas
Sources: the host-marketplace, loading and manifest-reference pages linked above

**Files and paths [R]**
- Files outside the plugin directory are not copied to the cache, so `../shared` breaks at runtime.
- Symlinks in a cached copy:
  - pointing inside the plugin: kept as relative links;
  - pointing elsewhere in the same marketplace: the target's content is copied in;
  - pointing outside the marketplace: skipped.
- For local-path and `command`/copy installs, only links that stay inside the plugin are kept.
- Use forward slashes; backslash paths load only on Windows.

**Git and hosting [R]**
- Keep plugin files out of Git LFS; clones fetch only pointer files.
- A marketplace hosted as a bare `marketplace.json` URL can't use relative-path entries. Use object sources, or host it in a git repo.

**State and dependencies [R]**
- Put state and installed dependencies in `${CLAUDE_PLUGIN_DATA}`, not in `${CLAUDE_PLUGIN_ROOT}`.
- Include an npm lockfile. Yarn and pnpm lockfiles are skipped. npm-source plugins need `npm-shrinkwrap.json`, because npm drops `package-lock.json` from published packages.

**Releases [R]**
- Treat plugin names as permanent. Use `renames` to migrate users, and `forceRemoveDeletedPlugins` to uninstall removed plugins.
- Pin `sha256` on archives.
- `defaultEnabled` changes don't reach users who already have an `enabledPlugins` entry.
- After a mid-session update, run `/reload-plugins` to switch hooks, MCP and LSP servers to the new path. Monitors need a restart.
- Recommended pre-publish check: `claude plugin validate --strict ./your-plugin`. The Anthropic directory portal applies extra rules that the CLI doesn't check.
