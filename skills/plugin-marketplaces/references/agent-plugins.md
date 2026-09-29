# Agent Plugins 1.0

The portable plugin package format published at agent-plugins.org.
Rules are cited by id from [SKILL.md](../SKILL.md); each fact cites a row of the Provenance table.

## Status

- Spec 1.0.0 is published; 1.1.0 is a working draft that differs only in version strings and schema ids [E1].
- The spec defines a package, not a catalog: marketplaces and distribution are out of its scope, so each tool supplies its own catalog [E1].
- Codex and Copilot CLI read the portable manifest; Claude Code does not, and is not listed as a compatible client [E1] [E2].
- A technical steering committee with members from Amazon, Cursor, Microsoft, OpenAI, and Vercel governs the spec, and no single vendor may hold a majority; Anthropic is not a member [E1].
- There is no official validator or conformance suite; the published JSON Schemas are the only machine check, and the spec text wins where they disagree [E3].

## `plugin.json`

- Exactly one manifest, `plugin.json` at the plugin root; no other file can replace or supplement its core fields [E4].
- The top level is closed: `$schema`, `name`, `version`, `description`, `author` (`name`, `email`, `url` only), `homepage`, `repository`, `license`, `keywords`, `extensions` [E4].
- `$schema` is required and must be `https://agent-plugins.org/schemas/1.0.0/plugin.schema.json`; clients must not fetch it and must reject unsupported versions [E4].
- `name` is required: 1 to 64 characters from `[a-z0-9.-]`, alphanumeric at both ends, with no `--` or `..` [E4].
- `version` is any string; SemVer is recommended, not enforced [E4].
- An unknown top-level key, or an `extensions` value that is not an object, is reported and ignored; any other violation rejects the whole plugin [E4].
- Client-specific data goes under `extensions."<reverse-domain>"` (OpenAI uses `com.openai`), and client files under a top-level directory named after that namespace [E4] [E2].

## Components

- Only two component types exist, at fixed locations: skills at `skills/<dir>/SKILL.md` (immediate children only) and MCP servers in the root `mcp.json` [E4].
- `mcp.json` holds `$schema` (`https://agent-plugins.org/schemas/1.0.0/mcp.schema.json`, same version as `plugin.json`) and `mcpServers`, nothing else [E4].
- Every server declares `type`: `stdio` (`command` as one token, a bare name or `./path`, plus `args`, `env`, `cwd`), `streamable-http`, or `sse` (`url`, `headers`) [E4].
- `${PLUGIN_ROOT}` and `${PLUGIN_DATA}` expand only in `args`, `env` values, and `cwd`; URLs and headers get no expansion, and secrets belong in neither `env` nor `headers` [E4].
- A Claude Code `.mcp.json` does not become a valid `mcp.json` by renaming: add `type` to each server, write `"http"` as `"streamable-http"`, and replace `${CLAUDE_PLUGIN_ROOT}` with `${PLUGIN_ROOT}` [E2] [E5].
- Commands, hooks, agents, and LSP servers have no portable form; keep them in a tool's own package or under that tool's extension namespace [E4] [E2].
- Failure is graded: a bad manifest rejects the plugin, a bad `mcp.json` drops MCP while skills still load, a bad server entry skips that server, and a bad skill skips that skill [E4].
- Every package path must resolve inside the plugin root, including through symlinks [E4].

## Known schema defects

- Issue #76: the `name` pattern uses a lookahead, which RE2 and Go regular expressions cannot compile [E3].
- Issue #77: strict schema validation rejects manifests the spec requires clients to accept (unknown keys, a non-object `extensions`), so a loader must apply the report-and-ignore exceptions on top of the schema [E3].

## Provenance

Verified against: agent-plugins-spec at `ff8ab5e392` and the published 1.0.0 schemas on 2026-09-27.
Conformance probes: none yet.

| Id | Evidence | Kind |
| --- | --- | --- |
| E1 | https://agent-plugins.org/ and `agentplugins/agent-plugins-spec` at `ff8ab5e392`, including `FUTURE_CONSIDERATIONS.md` and discussions #50, #52, #57; `docs/research/2026-09-27-agent-plugins.md` §1 and §3 | docs |
| E2 | `agentplugins/agent-plugins-example` at `5f3f5084a8`, `migrate-agent-plugin` skill, and https://developers.openai.com/codex/plugins/build.md; `docs/research/2026-09-27-agent-plugins.md` §4; re-verified 2026-09-28, `docs/research/2026-09-28-documentation-reverification.md` | docs |
| E3 | https://agent-plugins.org/schemas/1.0.0/plugin.schema.json and mcp.schema.json, issues #76 and #77; `docs/research/2026-09-27-agent-plugins.md` §5 | docs |
| E4 | `spec/1.0.0.md` at `agentplugins/agent-plugins-spec@ff8ab5e392`, §4 to §10; `docs/research/2026-09-27-agent-plugins.md` §2 | docs |
| E5 | `https://developers.openai.com/plugins/build/plugins.md`, the portable-format note that each server needs a transport `type`; `docs/research/2026-09-27-codex.md` §5; re-verified 2026-09-28, `docs/research/2026-09-28-documentation-reverification.md` | docs |
