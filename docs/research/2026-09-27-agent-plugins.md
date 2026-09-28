## Agent Plugins specification: reference (researched 2026-09-27)

Legend: **[R]** means I read it in a live source. **[I]** means I inferred it.

### Sources and pinned revisions

- Site: https://agent-plugins.org/ (the Markdown form is at /docs.md). The site source is `agentplugins/agent-plugins-site`, HEAD `f399975c2a` (2026-09-22).
- `specification-source.json` in the site repo says the site renders spec **1.0.0**, status "published", from spec commit `bd383552095128f6effe895b9257cfd580a6d179`. [R]
- Spec repo: https://github.com/agentplugins/agent-plugins-spec, HEAD `ff8ab5e392` (2026-08-19, "Start the 1.1.0 working draft").
  - It contains `spec/1.0.0.md`, `spec/1.1.0.md`, `schemas/{1.0.0,1.1.0}/{plugin,mcp}.schema.json`, `GOVERNANCE.md`, `MAINTAINERS.md`, `FUTURE_CONSIDERATIONS.md` and `CONTRIBUTING.md`. [R]
- Official example: `agentplugins/agent-plugins-example` @ `5f3f5084a8` (2026-08-05).
  - It is a plugin with one skill, `migrate-agent-plugin`.
  - That skill carries the only official migration and mapping guidance. [R]

### 1. Version, status, governance, maturity

**Versions** [R]
- **1.0.0** is Published. Commit `1fc1b6270e` ("Publish Agent Plugins Specification 1.0.0", 2026-07-24) was merged via `f24daf8292` on 2026-07-27.
- **1.1.0** is a "Working Draft" (`a2afd7ec7e`, 2026-08-12).
- The 1.1.0 draft differs from 1.0.0 only in version strings and schema IDs. I diffed both: prose and schemas are otherwise byte-identical.

**Lineage** [R]
- It began as the "Open Plugin Specification v1.0.0" by John Lindquist (`c01f3921f2`, 2026-04-03) under vercel-labs.
- The project was renamed "Agent Plugins" in `d83795f91a` (2026-07-17). Discussion #27 confirms that open-plugins.com now redirects to agent-plugins.org.
- The 2026-07-10 "revamp" by Jonathan Hefner (PR #9) cut the scope hard:
  - `f0d7a31cbe` "Limit v1 to skills and MCP".
  - `3936286741` "Add governance charter and remove marketplace appendix".
  - `6a505752f0` "Remove host-specific hook event catalog".

**Governance** [R]
- `GOVERNANCE.md` is a Technical Charter with a TSC of Core Maintainers plus a Lead Core Maintainer.
- "No single vendor may control a majority of Core Maintainer seats."
- Voting: quorum is 50%, decisions need a majority, and charter amendments need 2/3 of the TSC.
- TSC members (`MAINTAINERS.md`): Clare Liguori (Amazon), Roshan Sadanani (Cursor), Harald Kirschner (Microsoft), Gav Verma (OpenAI) and Jonathan Hefner (Vercel). Hefner is Lead (`c11dff7217`, 2026-07-27).
- **Anthropic is not on the TSC.**
- Licences: CC-BY-4.0 for spec text and docs, Apache-2.0 for schemas and code.
- The DCO requirement was removed in `03c816caf2`.
- Proposals go to GitHub Discussions first; `CONTRIBUTING.md` says "A technically complete pull request is not, by itself, evidence of implementor consensus".

**Maturity signals** [R]
- Repo stats: 1,332 stars and 74 forks. The repo was created 2026-04-03 and last pushed 2026-08-19.
- Essentially every commit since July is by Hefner. There have been no spec commits since 2026-08-19.
- Open PRs:
  - #82: make malformed `extensions` fatal in 1.1
  - #79 and #80: regex-portable patterns
  - #67: namespaced skill discovery
  - #66: `displayName` and icons
  - #17 and #19: older versions of the same ideas
- Open issues with teeth:
  - **#76**: the `name` pattern uses a lookahead, so it fails to compile in RE2/Go.
  - **#77**: the schema rejects two manifests that §5.2 and §8.1 require clients to accept.
  - #40: no portable workspace root for MCP.
- There are 34 discussions, mostly ideas (hooks, subagents, marketplace, signing, secrets).
- Closed as out of scope: #50/#52 (marketplace index) and #57 (default repo-local plugin location).
  - Hefner's reply: "marketplaces are a distribution artifact, and I think distribution is outside the scope of the Agent Plugins spec". He personally points to AI Catalog / ARD.

**Compatible clients** [R] — these are self-claims recorded in the site's `lib/compatible-clients.ts`. Every listed client claims skills plus MCP:

| Client | MCP transports claimed |
| --- | --- |
| VS Code | stdio, streamable-http, sse |
| Cursor | stdio, streamable-http, sse |
| GitHub Copilot | stdio, streamable-http, sse |
| ChatGPT & Codex | stdio, streamable-http |
| Kiro | stdio, streamable-http, sse |
| Hermes Agent (Nous) | stdio, streamable-http |
| OpenClaw | stdio, streamable-http, sse |
| Grok Bot (xAI) | stdio, streamable-http, sse |
| NanoClaw | stdio, streamable-http |
| OpenHands (added 2026-09-19, `b3301d7e35`) | stdio, streamable-http |

- **Claude Code is not listed.**
- There is no conformance test suite, so these claims are unverified.

### 2. Plugin manifest (spec 1.0.0) [R]

**Location** [R]
- Exactly one manifest: `plugin.json` at the plugin root (§5.1).
- "No other file can replace, supplement, or override the core fields."
- Clients load it before discovering any components.

**Schema is closed** (§5.2). The only permitted top-level keys are:
`$schema`, `name`, `version`, `description`, `author`, `homepage`, `repository`, `license`, `keywords`, `extensions`.

| Field | Req | Type / constraint |
| --- | --- | --- |
| `$schema` | yes | const `https://agent-plugins.org/schemas/1.0.0/plugin.schema.json`. Selects the version. Clients MUST NOT fetch it and MUST reject unsupported versions. |
| `name` | yes | 1–64 chars from `[a-z0-9.-]`, alphanumeric at start and end, no `--` or `..`. Pattern `^(?!.*(?:--|\.\.))[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?$`. Described as "Human-readable plugin name". |
| `version` | no | string. SemVer is RECOMMENDED but must not be enforced. |
| `description` | no | string |
| `author` | no | object with only `name`, `email`, `url` (all strings, all optional). Any extra key is fatal. |
| `homepage`, `repository` | no | string. Not URL-validated. |
| `license` | no | string. SPDX is recommended but not enforced. |
| `keywords` | no | string[] |
| `extensions` | no | object keyed by reverse-domain namespace, with object values |

**Failure semantics**
- An unknown top-level key is a schema violation, but clients MUST "report and ignore" it and keep loading.
- A non-object `extensions` is reported and ignored.
- Any other violation is fatal: the whole plugin is rejected.

**Components** [R]
- v1 defines **exactly two** component types, and their locations are fixed. `plugin.json` cannot override them or inline them (§6.1).
- **Skills**: `skills/<dir>/SKILL.md`, immediate children only, no recursion. They must conform to the Agent Skills spec at agentskills.io. An invalid skill is skipped on its own.
- **MCP servers**: `mcp.json` at the root, and nowhere else.
  - Top level is `$schema` (`.../schemas/1.0.0/mcp.schema.json`, whose version must match `plugin.json`) plus `mcpServers`. No other keys are allowed.
  - Each server is a closed union keyed on `type`:
    - `"stdio"`: `command` (required; a single token, either a bare name or `./path`, with no placeholder expansion), plus optional `args` (string[]), `env` (string map, which must not contain `PLUGIN_ROOT` or `PLUGIN_DATA`) and `cwd`.
    - `cwd` must be `./…`, `${PLUGIN_ROOT}[/…]` or `${PLUGIN_DATA}[/…]`. It defaults to the plugin root.
    - `"streamable-http"` and `"sse"` (legacy 2024-11-05 transport): `url` (required; absolute; HTTPS unless the host is loopback; no userinfo or fragment) plus optional `headers`.
    - URLs and headers get no expansion. Secrets must not go in `headers` or `env`.
  - A client must support at least one of stdio or streamable-http; `sse` is optional. There is no transport fallback.
- **Other types are explicitly excluded.** Commands, hooks, agents, rules and LSP are "too client-specific" (Design Decisions).

**Environment** (§9)
- For stdio servers the client must set `PLUGIN_ROOT` and `PLUGIN_DATA`.
- `PLUGIN_DATA` must be persistent and writable, and survive updates.
- `${PLUGIN_ROOT}` and `${PLUGIN_DATA}` are expanded only in `args`, `env` values and `cwd`, in a single non-recursive pass.

**Path containment** (§4.1)
- Every package path must resolve inside the plugin root, including through symlinks.
- Configured paths must start with `./`.
- Failure boundaries are graded: reject the plugin, drop a component type, skip one skill, skip one server, or deny access.

**Client extensions** (§8)
- Client data goes under `extensions."<reverse-domain>"`.
- Client files go in a top-level directory named exactly after the namespace (e.g. `com.example.client/hooks/`).
- The spec assigns no semantics to either, and clients ignore namespaces they don't implement.

**Versioning** (§10)
- Every spec release republishes both schemas under the new version.
- A published schema ID is never reassigned.

### 3. Marketplace / registry

**The spec defines none.** [R]
- The site's implementer guide lists "installation sources, registries, or marketplaces" under behaviour it "does not prescribe".
- History: the pre-revamp Open Plugin draft (`3feb5e55a3`) had a non-normative "Appendix B: Marketplace Indexes". It was removed in `3936286741`. That appendix described:
  - a root `marketplace.json` with `name`, `plugins[]`, `owner`, `metadata.pluginRoot`;
  - entries with `name`, `source` (a `./` path), `description`, `version`, `author`, `license`, `keywords`, `skills`.

**Codex's own marketplace format** [R, developers.openai.com/codex/plugins/build.md]. This is vendor-specific, not part of the spec.
- Locations: `$REPO_ROOT/.agents/plugins/marketplace.json` and `~/.agents/plugins/marketplace.json`. Codex also reads a "legacy-compatible" `$REPO_ROOT/.claude-plugin/marketplace.json`.
- Top-level fields: `name`, `interface.displayName`, `plugins[]`.
- Each entry has `name`, `source`, `policy.installation` (`AVAILABLE` / `INSTALLED_BY_DEFAULT` / `NOT_AVAILABLE`), `policy.authentication` (e.g. `ON_INSTALL`) and `category`. OpenAI says to "Always include" all three of the last.
- `source` variants:
  - `{"source":"local","path":"./…"}` or a plain string path;
  - `{"source":"url",…}` for a repo root;
  - `{"source":"git-subdir","url","path","ref"|"sha"}`;
  - `{"source":"npm","package","version"?,"registry"?}`.
- CLI: `codex plugin marketplace add|list|upgrade|remove`.
- Discussion #35 criticises this for putting a vendor catalog under the shared `.agents/` namespace.

### 4. Relationship to Claude Code and Codex

**The spec text and the site never mention Claude Code or Codex.** [R] I grepped the spec, the site repo and the example repo manifest. The only official mapping lives in the example repo's `migrate-agent-plugin` skill (`references/migration-guide.md`).
- It lists `.claude-plugin/plugin.json`, `.plugin/plugin.json`, `.github/plugin/plugin.json` and `.codex-plugin/plugin.json` as legacy manifests.
- Its mapping table:

| Existing artifact | Agent Plugins destination |
| --- | --- |
| identity and metadata | root `plugin.json` |
| skill | `skills/<name>/SKILL.md` |
| MCP (`.mcp.json`, inline) | root `mcp.json` with an explicit `type` |
| hooks, custom agents, LSP, UI/app | "No portable v1 destination": use a client extension namespace or keep a compatibility package |
| command or prompt | convert to a skill if appropriate, otherwise keep the client feature |
| marketplace, install policy, signing | "Outside the portable package" |

- Its advice: migrate additively; make the portable files the source of truth and generate legacy adapters from them; "Do not invent a vendor namespace"; do not put `hooks` or `agents` at the manifest top level.

**Codex / OpenAI** [R] — it has native, documented support:
- Root `plugin.json` with the Agent Plugins `$schema` is the recommended format.
- OpenAI-specific settings go under `extensions.com.openai`:
  - `apps` (`./.app.json`), `hooks` (`./hooks/hooks.json`), and `interface`.
  - `interface` holds `displayName`, `shortDescription`, `longDescription`, `developerName`, `category`, `capabilities`, `websiteURL`, `privacyPolicyURL`, `termsOfServiceURL`, `defaultPrompt`, `brandColor`, `composerIcon`, `logo`, `screenshots`.
- "Existing `.codex-plugin/plugin.json` files remain supported as a compatibility fallback."
- When `extensions.com.openai` is an object, it "replaces the entire `.codex-plugin/plugin.json` overlay … the two aren't merged."
- For portable packages, `skills` and `mcpServers` declarations in the overlay "can't replace, disable, or add to" the root `skills/` and `mcp.json`.
- "OpenAI also accepts legacy and Claude-compatible manifests."
- Caveat: the `@plugin-creator` scaffold still emits the `.codex-plugin/` compatibility layout.
- Note: OpenAI uses the namespace `com.openai`, not a domain-derived `com.openai.codex`.

**Claude Code** [R, code.claude.com/docs/en/plugins-reference.md and plugin-marketplaces.md] — the docs don't mention Agent Plugins or `agent-plugins.org`.
- The manifest is `.claude-plugin/plugin.json`, which is optional. MCP lives in `.mcp.json`.
- The manifest is open, with many component keys: `commands`, `agents`, `hooks`, `mcpServers`, `lspServers`, `outputStyles`, `workflows`, `skills`, `dependencies`, `userConfig`, `channels`, `settings`, `displayName`, `defaultEnabled`, `metadata`, `experimental.*`.
- `$schema` "is ignored at load time". `author.name` is required, and `homepage` must parse as a URL.
- Remote MCP entries use `type: "http"`, `"sse"` or `"ws"`. They do not use `"streamable-http"`.

**Field mapping, Claude Code to Agent Plugins** [I, derived from the two field lists]
- These map 1:1: `name` (Agent Plugins' charset is stricter, lowercase plus `.` and `-`), `version`, `description`, `author` (drop the requirement that `name` be present), `homepage`, `repository`, `license`, `keywords`.
- `$schema` must be set to the Agent Plugins constant.
- Everything else, including `displayName`, has no portable home. It goes under `extensions.<namespace>` or stays in `.claude-plugin/`.
  - Anthropic publishes no namespace, and `displayName` is only a proposal (#16/#66).
- Directory changes: `.mcp.json` becomes `mcp.json`. Each server gets an explicit `type`, and `"http"` becomes `"streamable-http"`. `${CLAUDE_PLUGIN_ROOT}` becomes `${PLUGIN_ROOT}`, and `CLAUDE_PLUGIN_DATA` becomes `PLUGIN_DATA`.
- `skills/` is already the same.
- A single directory can plausibly carry both a root `plugin.json` and `.claude-plugin/plugin.json`: Claude Code reads only the latter, and Agent Plugins clients read only the former. This is unverified — I did not run it in Claude Code.

### 5. Validation tooling and best practices

**Schemas** [R]
- https://agent-plugins.org/schemas/1.0.0/plugin.schema.json and https://agent-plugins.org/schemas/1.0.0/mcp.schema.json, both JSON Schema draft 2020-12.
- Probe results: the 1.0.0 URL served the schema, and `/schemas/1.1.0/plugin.schema.json` returned **404**.
- `mcp.schema.json` exposes `#/$defs/server` so that each server entry can be validated on its own.
- The spec text is authoritative over the schema.
- Known schema defects:
  - #76: the lookahead breaks RE2/Go validators.
  - #77: validating strictly against the schema wrongly rejects unknown fields or a bad `extensions`. A conformant loader must layer the §5.2/§8.1 exceptions on top.

**No official CLI, linter or conformance suite.** `FUTURE_CONSIDERATIONS.md` lists "A standard plugin linter or validator command" and "Conformance test suites" as future work. [R]

**Community tools** (from Discussions; I did not evaluate them):
- `rchaganti/agent-plugins-validator` (Go CLI, #56)
- a browser, API and MCP validator (#75)
- AIAgentConform v0.1.1, with 20 static rules (#83)
- `agent-plugins-conformance-kit`, 133 client-loader fixtures (#81)
- `stbenjam/skillsaw`, a linter (#35)

**Best practices** (from the spec and the example checklist) [R]
- Use a minimal closed manifest.
- The skill `name` must equal its directory name.
- stdio `command` must be one token. Bundled binaries must use `./path`.
- Use `${PLUGIN_DATA}` for installed dependencies and state.
- No secrets in `env` or `headers`.
- Don't depend on inherited environment variables or `PATH` beyond the bare-command lookup.
- Keep the `plugin.json` and `mcp.json` versions matched.
- Test every target client separately.
- Remove legacy manifests only after the replacements pass the same checks.

**Explicitly unaddressed** [R]: permissions, sandboxing, signing and provenance, secrets, enterprise policy, audit events, dependencies, distribution and marketplaces.

Local copies of everything fetched are in `/private/tmp/claude-501/-Users-bdc-projects-skills/15d3be1b-5676-4473-b859-077aa7a251cf/scratchpad/`: `spec/` (the spec repo), `site/all.txt`, `ex/all.txt`, `codex.md`, `cc.md`, `ccm.md`, `old-readme.md`, `first.md`.
