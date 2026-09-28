## Agent plugin marketplace/catalog survey (2026-09-27)

I did not install anything or change any config. I checked each tool against its live docs and read source through `gh api`. `[read]` means I read it in source or docs. `[inferred]` means I did not confirm it directly.

GitHub code search hit its rate limit once, on the two Kiro queries, so I checked Kiro from its docs instead. For every "no match" result below, the same search did return known matches for another string in that repo, so an empty result is a real negative.

### The standard's baseline
Agent Plugins 1.0 has **no marketplace or catalog format** [read].
- Spec: `agentplugins/agent-plugins-spec@ff8ab5e`, `spec/1.0.0.md`. A 1.1.0 working draft exists.
- The package is `plugin.json` at the root (with a required `$schema`), plus `skills/`, `mcp.json`, and reverse-domain folders for client-specific extensions.
- §rationale explicitly rejects "registry-fetched bundles", and the site says distribution "remain[s] under each client's control".
- Compatible clients listed at https://agent-plugins.org/compatible-clients: VS Code, Cursor, GitHub Copilot, ChatGPT & Codex, Kiro, Hermes Agent, OpenClaw, Grok Bot, NanoClaw, OpenHands. Claude Code is not listed.

For reference, Codex (`openai/codex@659b35f`, `codex-rs/core-plugins/src/marketplace.rs:20-24`) reads four catalog paths [read]:
- `.agents/plugins/marketplace.json`
- `.agents/plugins/api_marketplace.json`
- `.claude-plugin/marketplace.json`
- `.cursor-plugin/marketplace.json`

For the Cursor file only, Codex relaxes its rule that local sources must start with `./` (lines 665-671).

### Per harness

**Cursor**
- (a) Catalog: **`.cursor-plugin/marketplace.json`**. Required: `name`, `owner{name,email?}`, `plugins[]`. Optional: `metadata{description,version,pluginRoot}`. The file can be up to 10 MB.
  - Each entry: `name`, `source` (a bare relative path like `"plugin-one"`, or an object with `path`), `description`, `version`, `author`, `license`, `keywords`, `category`, `tags`, `logo`, component paths, `hooks`, `mcpServers`, `variables`.
  - The entry is merged with the plugin's own manifest, and the manifest wins.
  - No remote git/npm source types are documented.
  - Team marketplaces are added in the dashboard by importing a GitHub, GitLab, Bitbucket or Azure DevOps repo.
  - Docs: https://cursor.com/docs/reference/plugins.md [read]
- (b) Manifest: `.cursor-plugin/plugin.json`, or a root `plugin.json` for Agent Plugins [read].
- (c) The docs never mention `.claude-plugin` or Codex formats. Cursor does expand `${CLAUDE_PLUGIN_ROOT}` in MCP config [read].
- (d) Agent Plugins: yes [read].

**VS Code agent plugins**
- (a) Catalog: the first match, in this order, of `marketplace.json`, `.plugin/marketplace.json`, `.github/plugin/marketplace.json`, `.claude-plugin/marketplace.json`.
  - Source: `microsoft/vscode@39e8a64`, `src/vs/workbench/contrib/chat/common/plugins/pluginMarketplaceService.ts:254-259` [read].
  - Source types (`parsePluginSource`): relative string, `github`, `url`, `git-subdir`, `npm`, `pip`. It honours `metadata.pluginRoot`.
  - Setting: `chat.plugins.marketplaces` accepts `owner/repo`, a git URL, scp-style, or `file:///`.
  - Defaults: `github/copilot-plugins` and `github/awesome-copilot`.
- (b) Manifest: Agent Plugins root `plugin.json`, `.plugin/plugin.json`, `.claude-plugin/plugin.json`, or `plugin.json` (Copilot format) [read].
- (c) Reads the Claude catalog and manifest: yes. Codex (`.agents/plugins`) and Cursor paths: not in the code.
- (d) Agent Plugins: yes [read].

**GitHub Copilot CLI**
- (a) Catalog: the first of `marketplace.json`, `.plugin/marketplace.json`, `.github/plugin/marketplace.json`, `.claude-plugin/marketplace.json`.
  - Fields: `name`, `owner`, `metadata`, `plugins[]`. Each entry has `name`, `description`, `version`, and `source`, which is a relative path or an object of type `github` or `url`, each with optional `ref` and `sha`.
  - Command: `copilot plugin marketplace add owner/repo[#ref]|URL|path`. Same two default marketplaces as VS Code.
  - Docs: https://docs.github.com/en/copilot/reference/cli-plugin-reference, the "File locations" table [read].
- (b) Manifest: Agent Plugins root `plugin.json`. Legacy locations: `.plugin/`, root, `.github/plugin/`, `.claude-plugin/plugin.json`.
- (c) Claude: yes. Codex/Cursor: not documented.
- (d) Agent Plugins: yes [read].

**Gemini CLI**
- (a) There is no catalog file for authors to write. The gallery is built by a crawler that finds repos with the GitHub topic `gemini-cli-extension` (`docs/extensions/releasing.md`).
  - The CLI's experimental browse UI reads a hosted JSON array from `https://geminicli.com/extensions.json`, overridable with `experimental.extensionRegistryURI`. Each item has fields like `id`, `url`, `fullName`, `extensionName`, `extensionVersion`, `extensionDescription`.
  - Source: `google-gemini/gemini-cli@2fe7c2d`, `packages/cli/src/config/extensionRegistryClient.ts` [read].
- (b) Manifest: `gemini-extension.json`.
- (c) Code search found no `claude-plugin`, `marketplace.json` or `agent-plugins.org` [read].
- (d) Agent Plugins: no evidence.

**Kiro**
- (a) There is a curated registry at kiro.dev/powers and "Import power from GitHub", which scans directories for `plugin.json` or `POWER.md`. No catalog file format is documented.
  - Docs: https://kiro.dev/docs/powers/installation.md [read]. The source is closed.
- (b) Manifest: root `plugin.json` (Agent Plugins, with a `dev.kiro/` extension folder), or legacy `POWER.md`.
- (c) The docs don't mention Claude or Codex formats.
- (d) Agent Plugins: yes [read].

**OpenCode**
- (a) No catalog. Plugins are npm packages listed in the `"plugin"` array in config, or local files in `.opencode/plugins/`, and there is an ecosystem docs page.
  - Source: `anomalyco/opencode@b471c2b` (dev branch) [read].
- (b) Manifest: none (npm/TypeScript modules).
- (c) Code search found no `claude-plugin` or `marketplace.json`.
- (d) Agent Plugins: no.

**Amp**
- (a) No catalog file. Plugins are TypeScript files in `.amp/plugins/`, installed with `amp plugins add <url>`. Plugins are shared through hosted, git-backed workspace repos.
  - Docs: https://ampcode.com/docs/markdown/customize/plugins and /global-plugins-and-skills [read].
- (c) The docs don't mention Claude formats.
- (d) Agent Plugins: no.

**Goose** (`aaif-goose/goose@04ed836`)
- (a) No plugin catalog. `goose plugin install <git-url>` clones a single repo. `documentation/static/servers.json` is an MCP-extension directory for the docs site, not a plugin catalog [read].
- (b) Manifest: `.goose-plugin/plugin.json`, `.plugin/plugin.json`, or `plugin.json`, which Goose calls "open-plugins" (`crates/goose/src/plugins/formats/open_plugins.rs:14-18`). It also imports Gemini's `gemini-extension.json` (`formats/gemini.rs:11`) [read].
- (c) No Claude or Codex reading found (search `claude-plugin`: 0 hits).
- (d) Not documented; it plausibly accepts a root `plugin.json` [inferred].

**Cline** (`cline/cline@252082b`)
- (a) A **central hosted catalog** at `https://cline.github.io/marketplace/catalog.json`, generated from the `cline/marketplace` repo (`apps/cline-hub/src/server/marketplace.ts:86-89`) [read].
  - Shape: `{version:1, generatedAt, baseUrl, counts, tags[], entries[]}`. Each entry has `type` (`mcp`, `skill` or `plugin`), `id`, `name`, `repo`, `install{command,args}`, `verified`, `featured`.
  - It is not a per-repo file that authors write.
- (b) Plugins are TS/npm packages (`cline/plugins/plugins/<name>/package.json` + `index.ts` + `skills/`).
- (c) Search found no `claude-plugin`.
- (d) Agent Plugins: no.

**Roo Code**: the repo `RooCodeInc/Roo-Code` is **archived** (last push 2026-05-15). I did not survey it further.

**Windsurf**: its docs index lists only a hosted MCP marketplace, Skills and Workflows, and no agent plugin bundle or catalog format [read, from the llms.txt index only]. Its "Plugins" are IDE extensions.

**Hermes Agent** (`NousResearch/hermes-agent@bac0c45`)
- (a) No catalog: code search for `marketplace.json` found 0 hits. It distributes through plugin directories, pip entry points, and "skill taps" [read].
- (b) Manifest: native `~/.hermes/plugins/<name>/plugin.yaml`, or Agent Plugins root `plugin.json`.
- (c) It **deliberately skips** `.claude-plugin`, `.codex-plugin`, `.cursor-plugin`, `.devin-plugin` and `.kimi-plugin` (`hermes_cli/plugins_discovery.py:33-35`, `_FOREIGN_HARNESS_MANIFEST_DIRS`) [read].
- (d) Agent Plugins: yes [read].

**OpenHands** (`OpenHands/software-agent-sdk@3311ba9`)
- (a) Catalog: `marketplace.json` under `.plugin/` or `.claude-plugin/` (`openhands-sdk/openhands/sdk/marketplace/types.py:21-22`) [read].
  - Fields: `name`, `owner`, `metadata`, `plugins[]`, plus a non-standard **`skills[]`** array.
  - Source types: a string (local path or GitHub URL), or an object `{source: "github"|"url", repo|url, ...}`.
- (b) Manifest: root `plugin.json` (Agent Plugins, which takes precedence), `.plugin/plugin.json`, or `.claude-plugin/plugin.json` [read].
- (c) Claude: yes. Codex/Cursor: no.
- (d) Agent Plugins: yes.

**Factory Droid** (docs in `Factory-AI/factory@485a0c3`)
- (a) Catalog: **`.factory-plugin/marketplace.json`**. Fields: `name`, `description`, `owner`, `plugins[]`. Each entry has `name`, `source`, `description`, `category`.
  - Source types: relative path, `github`, `url`, `git-subdir` (with `ref`/`sha`), and `npm` (pinned by `version`). `npm:` is not accepted as a *marketplace* source.
  - Command: `droid plugin marketplace add <url|path> [--ref|--sha]`.
  - Docs: `docs/guides/building/building-plugins.mdx` and `docs/cli/configuration/plugins.mdx` [read].
- (b) Manifest: `.factory-plugin/plugin.json`. It also accepts `.claude-plugin/plugin.json` layouts, "translated into Droid form" [read].
- (c) "Droid is compatible with plugins built for Claude Code" [read]. The docs' example ID `security-guidance@claude-plugins-official` implies it also reads `.claude-plugin/marketplace.json`, but no path list says so [inferred].
- (d) Agent Plugins: not mentioned.

**Kimi Code CLI** (`MoonshotAI/kimi-code@be7d5f5`; the older `MoonshotAI/kimi-cli` is archived)
- (a) Its **own catalog format**: `{version:"1", plugins:[{id, tier:official|curated|…, displayName, version?, description, keywords, homepage, source: "./path"|"https://github.com/…"}]}`.
  - Default location is hosted: `https://code.kimi.com/kimi-code/plugins/marketplace.json`, overridable with an env var (`packages/agent-core-v2/src/app/plugin/marketplace.ts:9`) [read].
- (b) Manifest: `kimi.plugin.json` or `.kimi-plugin/plugin.json` (`manifest.ts:16-17`) [read].
- (c) Claude/Codex: no.
- (d) Agent Plugins: no.

**OpenClaw** (`openclaw/openclaw@6bda31d`)
- (a) Catalog: `.claude-plugin/marketplace.json` or a root `marketplace.json` (`src/plugins/marketplace.ts:34-35`) [read].
  - Source kinds: `path`, `github`, `git`, `git-subdir`, `url` (archive).
  - It also has a separate signed (DSSE) hosted feed for ClawHub.
  - Commands: `openclaw plugins marketplace list <source>` and `plugins install <p> --marketplace <src>`.
- (b) Manifest: it loads Claude (`.claude-plugin`), Codex (`.codex-plugin`), Cursor (`.cursor-plugin`) and Agent Plugins bundles (docs.openclaw.ai/plugins/bundles) [read].
- (c) Claude catalog: yes. Codex/Cursor catalogs: not found in the code.
- (d) Agent Plugins: yes.

**NanoClaw**: Agent Plugins `plugin.json` templates. Its "registry" is just the directory layout of the `nanocoai/nanoclaw-templates` repo (`docs/templates.md`), with no catalog file [read].

**Not verified**: Grok Bot (my docs fetch failed). The `.devin-plugin` directory appears only as a name in Hermes' skip list; I did not check it.

### Compatibility table

| Harness | Native catalog file | Reads `.claude-plugin/marketplace.json` | Reads Codex `.agents/plugins` | Reads `.cursor-plugin` catalog | Agent Plugins 1.0 |
|---|---|---|---|---|---|
| Codex (ref) | `.agents/plugins/marketplace.json` | yes | — | yes | yes |
| Cursor | `.cursor-plugin/marketplace.json` | no (undocumented) | no | — | yes |
| VS Code | `.github/plugin/`, `.plugin/`, root | **yes** | no | no | yes |
| Copilot CLI | `.github/plugin/`, `.plugin/`, root | **yes** | no | no | yes |
| OpenHands | `.plugin/marketplace.json` (+`skills[]`) | **yes** | no | no | yes |
| OpenClaw | root `marketplace.json` + signed feed | **yes** | no | no | yes |
| Factory Droid | `.factory-plugin/marketplace.json` | likely [inferred] | no | no | not stated |
| Kimi Code | hosted `marketplace.json` (own schema) | no | no | no | no |
| Cline | hosted `catalog.json` (own schema) | no | no | no | no |
| Gemini CLI | hosted `extensions.json` (crawler) | no | no | no | no |
| Kiro | none (curated registry) | no | no | no | yes |
| Hermes | none | skips it on purpose | no | no | yes |
| Goose / OpenCode / Amp / NanoClaw | none | no | no | no | Goose ?; NanoClaw yes |
| Windsurf | hosted MCP marketplace only | no | no | no | no |

### Shared dialects
1. **The Claude `marketplace.json` schema is the de facto shared catalog format.**
   - Readers at the Claude path: Codex, VS Code, Copilot CLI, OpenHands and OpenClaw, and probably Factory.
   - Same schema under other directories: Cursor, Factory, Copilot/VS Code (`.github/plugin/`), and `.plugin/`.
   - The common fields are `name`, `owner`, `metadata.pluginRoot`, and `plugins[]` with `name`/`source`.
   - Source-type support differs by harness:

     | Harness | `source` types it accepts |
     |---|---|
     | Copilot CLI | path, `github`, `url` |
     | VS Code | path, `github`, `url`, `git-subdir`, `npm`, `pip` |
     | Factory | path, `github`, `url`, `git-subdir`, `npm` |
     | Cursor | path strings only (a bare path is allowed) |

2. **The legacy "open-plugins" `.plugin/` directory** holds `plugin.json` in VS Code, Copilot CLI, OpenHands and Goose, and `marketplace.json` in VS Code, Copilot CLI and OpenHands.
3. **The Agent Plugins root `plugin.json`** is the shared *package* format. It deliberately has no catalog, so each harness supplies its own marketplace layer.
4. **Own, non-interoperable catalogs**: Kimi (`id`/`tier`/`displayName`), Cline (typed `entries[]`), and Gemini (`extensions.json`, generated by a crawler). Gemini's `gemini-extension.json` *manifest* is itself read by Goose.

A portable catalog should be `.claude-plugin/marketplace.json` using relative or `github` sources, which reaches the most readers. Add a mirrored `.cursor-plugin/marketplace.json` only if Cursor users matter, since Cursor ignores the Claude path.
