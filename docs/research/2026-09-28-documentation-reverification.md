# Documentation re-verification for the upstream pins

Date: 2026-09-28.
This is a hand-written record of plan 3's Task 7: every reference line that cites one of the 11 documentation pins was re-read against the page as fetched today, and only that content is pinned.
Each page was fetched once with `tests/check_upstream.py`'s own `doc_text` (the `## Plugins and skills` section only for `settings-reference.md`), and the sha256 below is of exactly that text.
Four read-only subagents judged the lines, one per group of pages, using only a file reader; their rows are copied below as returned, lightly trimmed of commentary.
A row reads `<reference>:<line> | verdict | the page's words`; `not stated (rests on other evidence)` means the line's claim is carried by another cited row, such as a source reading or a probe.

## Pages and verdicts

### `claude-marketplace-reference`

https://code.claude.com/docs/en/plugins/marketplace-reference.md, sha256 `9bce0af0615e2e15e2337b5bf641ca6cb61020cb7a6b521f39d2055ca1335b5c`.

Count: 21 confirmed / 2 changed / 4 not stated

- claude-code.md:8 | confirmed | "Save the marketplace file at `.claude-plugin/marketplace.json`… The directory that contains `.claude-plugin/` is called the marketplace root, and every relative plugin source resolves from it, not from `.claude-plugin/`."
- claude-code.md:9 | confirmed | "`name`, `owner`, and `plugins` are required."; owner: "`name` is required"; plugins: "Each entry is validated on its own, so one invalid entry doesn't fail the marketplace"
- claude-code.md:10 | confirmed | "Claude Code ignores an unknown top-level key or plugin-entry key rather than rejecting it, so a typo loads silently. `claude plugin validate` reports each unknown key as a warning."
- claude-code.md:11 | confirmed | "Must start with `./`, unless you write a bare name under `metadata.pluginRoot`"; "Directory that bare plugin source names resolve under… Requires Claude Code v2.1.239 or later"
- claude-code.md:12 | confirmed | `renames`: "Map from a former plugin `name` to its current name, or to `null` for a plugin you removed. Requires Claude Code v2.1.193 or later"; `forceRemoveDeletedPlugins`: "When `true`, a plugin you remove from `plugins` is uninstalled on users' machines"
- claude-code.md:17 | confirmed | "`name` and `source` are required. An entry also accepts every `plugin.json` field"
- claude-code.md:19 | confirmed | "Entry `mcpServers`, `lspServers`, `userConfig`, and `channels` don't apply."; "For a field you set on the entry, users see the entry's value, even when `plugin.json` sets a different one."
- claude-code.md:20 | changed | "With `strict: true`, the default, Claude Code appends the entry's component fields to `plugin.json`, except `hooks`, whose matchers replace the manifest's per event." The `strict: false` part is still confirmed: "Conflict. The plugin fails to load with `Plugin <name> has conflicting manifests…`"
- claude-code.md:21 | confirmed (this page's part only; the line also cites E5) | "Write entry `hooks` as an inline object… If you write a file path or an array instead, `claude plugin validate` passes it. Those hooks never run, and Claude Code reports a `not yet supported in a marketplace entry` error"
- claude-code.md:36 | changed | "When you set both `ref` and `sha`, Claude Code checks out `sha`. On most git hosts… installation succeeds even if the branch or tag named by `ref` has since been deleted… as long as the commit is still reachable… Some servers, such as AWS CodeCommit, don't support fetching commits by SHA."
- feature-matrix.md:23 (path: yes) | confirmed | "Relative path | the string itself | A directory inside the marketplace"
- feature-matrix.md:24 (local-object: no) | confirmed | The exhaustive "The table lists each plugin source type" has no local-object type, and "A `source` type that isn't one of the plugin sources" gives `Invalid input`.
- feature-matrix.md:25 (github: yes) | confirmed | "`github` | `repo`, `ref`, `sha` | GitHub repository in `owner/repo` form"
- feature-matrix.md:26 (url: yes) | confirmed | "`url` | `url`, `ref`, `sha` | Any git repository by URL"
- feature-matrix.md:27 (git-subdir: yes) | confirmed | "`git-subdir` | `url`, `path`, `ref`, `sha` | One subdirectory of a git repository"
- feature-matrix.md:28 (npm: yes) | confirmed | "`npm` | `package`, `version`, `registry` | npm package, fetched with your npm client"
- feature-matrix.md:29 (archive: yes) | confirmed | "`archive` | `url`, `sha256` | Zip archive over HTTPS. Requires Claude Code v2.1.224 or later"
- feature-matrix.md:30 (command: yes) | confirmed | "`command` | `command`, `timeout`, `mode` | … Requires Claude Code v2.1.229 or later"
- feature-matrix.md:38 (Claude column, E7 only) | confirmed | "No spaces, control characters, or bidirectional-formatting characters, no `/` or `\`, no `..`, and not `.`. See Reserved names."
- feature-matrix.md:39 (Claude column; the line also cites E11) | not stated | "Users type it before `@` when they install, even when the plugin's own `plugin.json` sets a different `name`". Side note: create-marketplace says the entry name is "what `claude plugin list` shows", which conflicts with "shows the manifest name".
- feature-matrix.md:40 (Claude column; the line also cites E4) | not stated | "When `plugin.json` also sets `version`, `plugin.json` takes precedence"; the fallback is left to the Plugin loading reference.
- releases.md:14 | not stated | an attribution line with no claim of its own.
- releases.md:15 (Claude part) | not stated | "For how each type is fetched, cached, and versioned, see Plugin loading reference."
- releases.md:16 (Claude part) | confirmed | "When `plugin.json` also sets `version`, `plugin.json` takes precedence and `claude plugin validate` warns"; "`Entry declares version "x" but <path>/plugin.json says "y". At install time, plugin.json wins` | Warning | … on a relative-path entry".
- releases.md:38 | confirmed | "Claude Code checks out `sha`… installation succeeds even if the branch or tag named by `ref` has since been deleted upstream, as long as the commit is still reachable… Some servers, such as AWS CodeCommit, don't support fetching commits by SHA."
- releases.md:42 | confirmed | Same `renames` and `forceRemoveDeletedPlugins` rows as :12 above.
- validation.md:16 | confirmed (only the SHA-host fact) | "Some servers, such as AWS CodeCommit, don't support fetching commits by SHA."

### `claude-create-marketplace`

https://code.claude.com/docs/en/plugins/create-marketplace.md, sha256 `3b079222bc97cf17a9231e163cb9df2d47acf79cc80f0c0b155de33c087dbca5`.

E1 names both marketplace-reference (MR) and create-marketplace (CM), so these lines were judged against both pages together.
Count: 8 confirmed / 2 changed / 0 not stated

- claude-code.md:8 | confirmed (MR and CM) | CM: "Write the entry's `source` as a path from the marketplace root. The root is `my-marketplace/`, the directory that contains `.claude-plugin/`."
- claude-code.md:9 | confirmed | CM: "The file requires a `name`, an `owner`, and a `plugins` array."; MR: "Each entry is validated on its own"
- claude-code.md:10 | confirmed | CM: "Unknown fields at the top level or in a plugin entry, as warnings"; MR: "ignores an unknown… key… so a typo loads silently"
- claude-code.md:11 | confirmed (MR only) | see MR row
- claude-code.md:12 | confirmed (MR only) | see MR row
- claude-code.md:17 | confirmed (both) | CM: "needs a `name` and a `source`"; "An entry can also set any `plugin.json` field"
- claude-code.md:19 | confirmed (MR only) | see MR row
- claude-code.md:20 | changed (MR; CM is silent) | MR: "appends the entry's component fields… except `hooks`, whose matchers replace the manifest's per event"
- claude-code.md:21 | confirmed (MR only; the line also cites E5) | see MR row
- claude-code.md:36 | changed (MR) | see MR row; the deleted-ref guarantee is limited to hosts that can fetch a commit by SHA.

### `claude-host-marketplace`

https://code.claude.com/docs/en/plugins/host-marketplace.md, sha256 `56123e008d0de5a876806dda15426e4990a4036e503f7c11209e1bbfa5379a53`.

Count: 5 confirmed / 0 changed / 5 not stated

- claude-code.md:13 | confirmed | "Background auto-update is off for your marketplace by default, and `marketplace.json` has no field to turn it on. A user or an admin turns it on"
- claude-code.md:18 (the line also cites E13) | not stated | "Users then install a plugin by its entry's `name` and the marketplace's `name`"; "Users reference it in the `enabledPlugins` and `pluginConfigs` settings keys". CM says the entry name is "what `claude plugin list` shows", which conflicts with "appears under the manifest name".
- claude-code.md:53 (the line also cites E4) | not stated | nothing on marketplace-name rules; MR states them, so the citation may point at the wrong page.
- claude-code.md:58 | not stated | "That version comes from `plugin.json` first, then from the marketplace entry"; the 12-character SHA is not stated here.
- claude-code.md:59 (the line also cites E8) | confirmed (this page's part) | "users stay on their cached copy until the string changes. If you set `"version": "1.0.0"` and push new commits without changing it, users don't receive them."
- claude-code.md:60 | confirmed | "Omit `version`: users track your commits instead. Leave `version` out of both `plugin.json` and the marketplace entry."; "Don't set `version` in both… Claude Code uses the `plugin.json` value without warning"
- claude-code.md:61 | not stated | "A plugin that users load in place from a marketplace they added as a local directory isn't controlled by `version`"; the cache path is not on this page.
- claude-code.md:62 | confirmed | "relies on whatever credentials that machine already holds. Claude Code has no git token of its own, and `marketplace.json` has no field for one."
- claude-code.md:37 | confirmed | "When users add your marketplace as a bare `marketplace.json` URL, Claude Code downloads only that file. An entry… whose `source` is a relative path… then fails at install… or host the marketplace in a git repository"
- claude-code.md:49 | not stated | "Elsewhere within the same marketplace: the symlink is dereferenced. The target's content is copied into the cache"; "Outside the marketplace: the symlink is skipped".

### `claude-cli-reference`

https://code.claude.com/docs/en/plugins/cli-reference.md, sha256 `f2e42471f2fd6a8b63aca5a1052826f4a7552ec8df86aff6cae46759b7a46831`.

Count: 3 confirmed / 0 changed / 2 not stated

- claude-code.md:53 (the line also cites E3) | not stated | no reserved-name rules on this page; MR states them.
- claude-code.md:66 | confirmed | "`claude plugin validate <path> [options]`" with `--strict` and `--json`; "`.claude-plugin/marketplace.json`, when it exists; Otherwise `.claude-plugin/plugin.json`"; the page adds "Otherwise the component files… requires Claude Code v2.1.233 or later".
- claude-code.md:67 | confirmed | "`0` | `Validation passed` or `Validation passed with warnings`"; "`1` | … An error, or a warning under `--strict`"; "`2` | … The validator itself failed"
- claude-code.md:68 (the line also cites E6) | confirmed (this page's part) | "`--strict` | Treat warnings as errors".
- claude-code.md:69 | not stated | only the last clause: "from a marketplace directory, Claude Code doesn't open the plugins' skill, agent, command, or hook files, or the MCP server files they bundle"; MR and CM state the rest.

### `claude-manifest-reference`

https://code.claude.com/docs/en/plugins/manifest-reference.md, sha256 `2ec613e87106d52bcba2883e4b58c222ce622676f4b14fee0db9c89eb2f8c270`.

Count: 14 confirmed / 1 changed / 0 not stated

- claude-code.md:41 | confirmed | "The manifest is optional. Without it, Claude Code loads the components it finds in the standard layout." and "Save the manifest at `.claude-plugin/plugin.json` under the plugin root"
- claude-code.md:42 | confirmed | "`name` is the only required key." and "A version string, not checked against semver."
- claude-code.md:44 | confirmed | the Standard layout table lists the line's paths; it also lists "`workflows/`", "`themes/`" and "`monitors/monitors.json`".
- claude-code.md:45 | confirmed | "Replaces the default: `commands`, `agents`, `outputStyles`, `workflows`, `experimental.themes`, `experimental.monitors`" / "Adds to the default: `skills`" / "Merges: `hooks`, `mcpServers`, `lspServers`. The default file loads first".
- claude-code.md:46 | changed | "Every component path in a manifest is relative to the plugin root and must start with `./`… `skills` and `mcpServers` each accept one form outside that rule: `skills`: also accepts `\".\"`… `mcpServers`: also accepts an `https://` bundle URL"; "Every component path must resolve inside the plugin root and must exist".
- claude-code.md:47 | confirmed | "`${CLAUDE_PLUGIN_ROOT}` | Absolute path of the plugin's installed version"; "`${CLAUDE_PLUGIN_DATA}`… kept across plugin updates"; hook commands, MCP `stdio` servers, LSP servers, and "Skill, command, and agent content | Anywhere in the Markdown body".
- claude-code.md:48 | confirmed | "`${user_config.KEY}`: substituted in MCP server config, LSP server config…" and "Sensitive values go to the platform's secure credential store instead".
- claude-code.md:54 | confirmed | "It must be non-empty, with no spaces, `@`, `:`, path separators, control characters, or bidirectional-formatting characters; use kebab-case."
- feature-matrix.md:11 | confirmed | "`skills`… Adds to the default `skills/` scan"
- feature-matrix.md:12 | confirmed | "Commands | `commands/` | Flat Markdown command files. Prefer `skills/` for new plugins"
- feature-matrix.md:13 | confirmed | "Agents | `agents/` | Agent Markdown files"
- feature-matrix.md:14 | confirmed | "Claude Code merges whatever you declare with `hooks/hooks.json` when that file exists."
- feature-matrix.md:15 | confirmed | "Claude Code loads `.mcp.json` at the plugin root first, then each declared shape in order"
- feature-matrix.md:16 | confirmed | "Reference a saved value… `${user_config.KEY}`"
- feature-matrix.md:17 | confirmed | "LSP servers | `.lsp.json` | LSP server configurations"

### `claude-loading`

https://code.claude.com/docs/en/plugins/loading.md, sha256 `2ae43ab16e376c9ed960f34c7d7e6faa4f917ae3d07ac358969f40e36082bb15`.

The claude-code.md rows cite E3; they were judged against the union of loading, settings-reference, and host-marketplace.
Count: 16 confirmed / 2 changed / 6 not stated

- claude-code.md:13 | confirmed | loading: "The default: on for Anthropic's official marketplaces… and off for every other marketplace".
- claude-code.md:18 | changed (one clause) | loading: "The entry name in `marketplace.json`: the install and enable key. It's what you write in `enabledPlugins`, what the cache directory is named after, and what `claude plugin list` shows" and "The `name` in the manifest: what the plugin's components are namespaced under".
- claude-code.md:53 | not stated | only "no marketplace can be named `inline`, `skills-dir`, or `synced`".
- claude-code.md:58 | confirmed | "1. The `version` field in the plugin's manifest comes first 2. Then the `version` field in the plugin's marketplace entry 3. When neither is set, the version comes from the source type"; "`github`, `url`, or `git-subdir` | The commit SHA of the source, shortened to 12 characters".
- claude-code.md:59 | confirmed | "a manifest that pins `\"version\": \"1.0.0\"` keeps every user on the cached copy until its author changes the string"
- claude-code.md:60 | confirmed | "To let users track commits instead, leave `version` out of both the manifest and the entry."
- claude-code.md:61 | confirmed | "`cache/<marketplace>/<plugin>/<version>/` | One directory per installed version"; "the plugin loads in place".
- claude-code.md:62 | confirmed | settings: "the same authentication that `git clone` would use on that machine".
- feature-matrix.md:23 | confirmed | "Relative path inside a Git-hosted marketplace"
- feature-matrix.md:24 | not stated | the page defers to "The marketplace reference lists the source types".
- feature-matrix.md:25 | confirmed | "`github`, `url`, or `git-subdir` | The commit SHA of the source"
- feature-matrix.md:26 | confirmed | same row
- feature-matrix.md:27 | confirmed | same row
- feature-matrix.md:28 | confirmed | "`npm` | `unknown`"
- feature-matrix.md:29 | confirmed | "`archive` | The SHA-256 digest, shortened to 12 characters"
- feature-matrix.md:30 | confirmed | "For a `command` source, Claude Code always derives the version from what the command produced"
- feature-matrix.md:38 | not stated | reserves only "`inline`, `skills-dir`, or `synced`".
- feature-matrix.md:39 | changed | "A marketplace plugin has two names, and they can differ"; the entry name is "what `claude plugin list` shows".
- feature-matrix.md:40 | confirmed | the three-step version order.
- releases.md:14 | not stated | an attribution line.
- releases.md:15 | confirmed | "When neither is set, the version comes from the source type… The commit SHA of the source".
- releases.md:16 | confirmed (partial) | loading: "The `version` field in the plugin's manifest comes first"; host-marketplace: "`claude plugin validate` reports the mismatch as `Entry declares version…`".
- releases.md:23 | not stated | neither page says a pinned `sha` survives the deletion of its `ref`; marketplace-reference does (see its releases.md:38 row).
- releases.md:42 | not stated (on loading) | host-marketplace confirms: "Map each former name to its current name, or to `null` when the plugin is gone".

### `claude-settings-plugins`

https://code.claude.com/docs/en/settings-reference.md, sha256 `5a16c83cbe9fb6df107cd9669dc7889754d5659c749cfa6ec456ed11802095f3`.

Count: 6 confirmed / 1 changed / 1 not stated

- claude-code.md:13 | confirmed | "When omitted, `claude-plugins-official` and most other official Anthropic marketplaces default to `true`, and third-party marketplaces default to `false`".
- claude-code.md:18 | changed (one clause) | "`enabledPlugins`… keyed by `plugin-name@marketplace-name`" confirms the key; the display clause conflicts with loading.
- claude-code.md:53 | not stated | no marketplace-name rules.
- claude-code.md:58 | confirmed | (loading)
- claude-code.md:59 | confirmed | (loading)
- claude-code.md:60 | confirmed | (loading and host-marketplace)
- claude-code.md:61 | confirmed | (loading)
- claude-code.md:62 | confirmed | "Claude Code clones the repository with the same authentication that `git clone` would use on that machine: configured credential helpers or SSH keys."

### `claude-skills`

https://code.claude.com/docs/en/skills.md, sha256 `ffe690866cdac3e163ebefbd270161e62796dc35399f3335e4067b43d2b23910`.

Count: 1 confirmed / 0 changed / 0 not stated

- multi-tool.md:32 | confirmed | "Custom commands have been merged into skills. A file at `.claude/commands/deploy.md` and a skill at `.claude/skills/deploy/SKILL.md` both create `/deploy`" and "a Markdown file in `.claude/commands/` is the older format and still works… Prefer a skill for new work".

### `openai-plugins-build`

https://developers.openai.com/plugins/build/plugins.md, sha256 `4b003d3d35ba8cca78d99e073ea1218e3ec7a4e44030e569261e67bd7039cc8a`.

Count: 16 confirmed / 0 changed / 3 not stated

- codex.md:8 | not stated (rests on other evidence) | "a repo marketplace at `$REPO_ROOT/.agents/plugins/marketplace.json`", "a legacy-compatible marketplace at `$REPO_ROOT/.claude-plugin/marketplace.json`"; no lookup order.
- codex.md:10 | confirmed | "Codex resolves `source.path` relative to the marketplace root, not relative to the `.agents/plugins/` folder."
- codex.md:17 | confirmed (the page's part) | "Always include `policy.installation`, `policy.authentication`, and `category` on each plugin entry."
- codex.md:35 | confirmed | "The root `plugin.json` is the portable entry point. OpenAI also accepts legacy and Claude-compatible manifests"
- codex.md:37 | confirmed | "Portable packages always discover skills in `skills/` and MCP servers in `mcp.json`."
- codex.md:39 | confirmed (page's part) | "Codex discovers `hooks/hooks.json` by default when the selected OpenAI extension or compatibility manifest doesn't define `hooks`"
- codex.md:40 | confirmed | "Use the `interface` object for install-surface metadata…"
- codex.md:44 | confirmed (page's part) | "Keep paths in `extensions.com.openai` or a compatibility manifest relative to the plugin root and start them with `./`."
- codex.md:52 | confirmed | "Plugin hook commands receive the Codex-specific environment variables `PLUGIN_ROOT` and `PLUGIN_DATA` ... Codex also sets `CLAUDE_PLUGIN_ROOT` and `CLAUDE_PLUGIN_DATA` for compatibility" and "Codex skips them until the user reviews and trusts the current hook definition."
- agent-plugins.md:10 | confirmed (Codex part only) | "For a portable Agent Plugins package, add `plugin.json` at the plugin root and declare the Agent Plugins schema."
- agent-plugins.md:22 | confirmed (the `com.openai` part only) | "Put OpenAI-specific presentation, registered MCP server mappings, and hook settings under `extensions.com.openai` in root `plugin.json`."; the page keeps client resources at the plugin root: "referenced hooks, `.app.json`, and other resources stay at the plugin root."
- agent-plugins.md:30 | confirmed (the `type` and `streamable-http` parts) | "Don't just rename `.mcp.json`: the portable MCP format also declares a transport `type` for each server."
- agent-plugins.md:31 | confirmed (page's part) | "Fixed package paths identify its portable components: `skills/` contains skills, and `mcp.json` configures MCP servers."
- agent-plugins.md:30 (duplicate line) | confirmed | as above.
- multi-tool.md:21 | confirmed (the root `$schema` part) | "Keep portable identity and metadata, such as `name`, `version`, and `description`, at the root."
- multi-tool.md:22 | confirmed (the `type` and `streamable-http` parts) | "Include the Agent Plugins MCP schema and a named entry under `mcpServers`"
- multi-tool.md:23 | confirmed (the Codex hooks mechanism), with a caveat | "To override that default, define `hooks` inside `extensions.com.openai` in root `plugin.json`." and "Codex discovers `hooks/hooks.json` by default when the selected OpenAI extension or compatibility manifest doesn't define `hooks`".
- multi-tool.md:24 | not stated | this page is not the migration guide.
- multi-tool.md:25 | not stated | no advice on additive migration.

### `openai-submit-claude-plugin`

https://developers.openai.com/plugins/guides/submit-claude-plugin.md, sha256 `f191c10e6d42c034a48780f52bf87cb970bc1f55cf3487dd9326b5d81302eb3a`.

Count: 6 confirmed / 0 changed / 3 not stated

- codex.md:48 | confirmed | "Convert reusable behavior to skills. Turn each Markdown command into a skill"; "OpenAI doesn't run Claude installation prompts or expand `user_config` variables"; "Codex doesn't run prompt or agent hook handlers".
- codex.md:49 | not stated (rests on other evidence) | "Turn each Markdown command into a skill"; automatic migration is not described.
- feature-matrix.md:11 | confirmed | "A direct Claude archive upload must include at least one skill at `skills/<skill-name>/SKILL.md`."
- feature-matrix.md:12 | not stated (rests on other evidence) | "Turn each Markdown command into a skill".
- feature-matrix.md:13 | confirmed | "`commands`, `commands/`, `agents`, or `agents/`: Convert reusable behavior to skills ... move reusable agent procedures into skills".
- feature-matrix.md:14 | confirmed | "Hook scripts must be available in the execution environment and trusted before they run… Codex doesn't run prompt or agent hook handlers."
- feature-matrix.md:15 | not stated (rests on other evidence) | "`.claude-plugin/marketplace.json`, `.mcp.json`, `mcpServers`, `.app.json`, or `apps`: Don't rely on these files or declarations."
- feature-matrix.md:16 | confirmed | "OpenAI doesn't run Claude installation prompts or expand `user_config` variables."
- feature-matrix.md:17 | confirmed | "`outputStyles`, `lspServers`, ... Move essential behavior into skills, then remove the Claude declaration."

### `copilot-cli-plugin-reference`

https://docs.github.com/api/article/body?pathname=/en/copilot/reference/cli-plugin-reference, sha256 `09090f796cdb82fc811c539be75b687c6567c2b4eca55a44797cff2f35a2a828`.

- copilot-cli.md:8 | confirmed for the path list and its order; not stated for the `.agents/plugins/marketplace.json` exclusion | File locations table: "Marketplace manifest | `marketplace.json`, `.plugin/marketplace.json`, `.github/plugin/marketplace.json`, or `.claude-plugin/marketplace.json` (checked in this order)". The page lists only these four paths and never mentions `.agents/plugins/`, so the "does not read" part is at most implied by omission.
- copilot-cli.md:9 | confirmed | "`add SOURCE` | Add a marketplace (`owner/repo`, `owner/repo#ref`, a URL, or a local path)"; "First-party plugins—those installed from the built-in `copilot-plugins` and `awesome-copilot` marketplaces"; "Built-in default marketplaces ship with the runtime and can't be removed". The `github/` owner prefix is not stated.
- copilot-cli.md:10 | confirmed for the fields; the "Claude Code dialect" label is not stated | Top-level fields `name`, `owner`, `plugins` required, `metadata` optional; entry fields `name`, `source` required, `description`, `version` optional; "Copilot CLI also looks for the `marketplace.json` file in the `.claude-plugin/` directory."
- copilot-cli.md:11 | confirmed (this page's part only) | "The `source` field on a plugin entry accepts a relative path string, or an object describing a GitHub repository or Git URL source"; "Both the `github` and `url` source types accept an optional `sha` field to pin installs to an exact commit, in addition to (or instead of) `ref`".
- multi-tool.md:36 | confirmed for the Copilot CLI part only; the "own catalog" conclusion is not stated | "`marketplace.json`, `.plugin/marketplace.json`, `.github/plugin/marketplace.json`, or `.claude-plugin/marketplace.json` (checked in this order)".
- multi-tool.md:45 | confirmed for the precedence claim; "third catalog" and R10 are this skill's own guidance | "(checked in this order)"; "creating a `marketplace.json` file and saving it to the `.github/plugin/` directory of the repository".

Count: 6 confirmed / 0 changed / 0 not stated (main claims).

## Entry and manifest names

The pages disagreed with `claude-code.md` about which name a plugin appears under when its entry and manifest names differ, so it was probed on claude 2.1.284 with `tests/conformance/sandbox.py` (throwaway homes, outbound traffic denied): an entry `lint` whose manifest names `linter`.

```text
$ claude plugin install linter@mkt
✘ Failed to install plugin "linter@mkt": Plugin "linter" not found in marketplace "mkt". Your local copy may be out of date — try `claude plugin marketplace update mkt`.
$ claude plugin install lint@mkt
✔ Successfully installed plugin: lint@mkt (scope: user)
$ claude plugin list --json
[{"id": "lint@mkt", "version": "0.1.0", "installPath": "$PROBE/claude/plugins/cache/mkt/lint/0.1.0", …}]
$ claude plugin details lint@mkt
linter 0.1.0
  Source: lint@mkt
```

So `claude plugin list` and the cache directory use the entry name, as the loading page says, and `claude plugin details` heads its output with the manifest name, which is what the plan-2c runs had seen.

## Edits made

- `claude-code.md`: the name-display clause (E15, the probe above); `strict: true` appends entry component fields except `hooks`, whose matchers replace the manifest's per event; a `sha` still installs after its `ref` is deleted only while the commit is reachable and on hosts that fetch by SHA; the default layout adds `workflows/`, `themes/`, and `monitors/monitors.json`; `workflows`, `experimental.themes`, and `experimental.monitors` also replace their default; `skills` also accepts `"."` and `mcpServers` an `https://` bundle URL; symlinks within the marketplace are dereferenced and ones leading outside it skipped; the marketplace-name rules also cite E1, the page that states them; `claude plugin validate` falls back to component files from claude 2.1.233.
- `feature-matrix.md`: the entry-versus-manifest name row (new E12, the probe above); Codex discovers `hooks/hooks.json` by default in both formats unless the manifest names another file.
- `multi-tool.md` and `codex.md`: Codex discovers `hooks/hooks.json` by default when `extensions["com.openai"]` defines no `hooks`, so a dual-packaged plugin's Claude hooks reach Codex users once they trust them.
- Every documentation evidence row the 11 pins affect now ends `re-verified 2026-09-28` with a pointer to this record.
- Not changed: `agent-plugins.md`'s client-file directory is what the Agent Plugins spec requires (§8: "Client-specific files MUST be represented under a top-level directory named for that namespace"), although OpenAI's page keeps its own files at the plugin root; `multi-tool.md`'s migration-guide lines rest on the guide, which E2 also names.
