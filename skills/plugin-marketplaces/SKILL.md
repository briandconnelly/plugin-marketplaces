---
name: plugin-marketplaces
description: >-
  User-hosted plugin marketplaces: catalog files a maintainer hosts in a git repository
  so Claude Code, Codex, and GitHub Copilot CLI users can add them.
  Use when creating, auditing, maintaining, or releasing such a marketplace or catalog;
  adding, pinning, bumping, renaming, or removing a plugin entry; diagnosing a tool that
  skips or fails to load catalog entries; or packaging one plugin for several of these
  tools (marketplace.json, plugin.json, .claude-plugin, .agents/plugins, .codex-plugin,
  .github/plugin, agent-plugins.org).
  Not for writing a plugin's hooks, agents, skills, or MCP servers, installing a plugin
  for personal use, or vendor-hosted registries such as the VS Code Marketplace or npm.
license: MIT
compatibility: >-
  The validator needs Python 3.12+ and uv, or the installed check-marketplace command.
  The claude, codex, and copilot CLIs are optional check instruments.
---

# Plugin marketplaces

A user-hosted plugin marketplace is a catalog file that its maintainer writes and hosts, typically in a git repository, and that users register with their tool.
This skill covers three readers — Claude Code, Codex, and GitHub Copilot CLI — and the Agent Plugins 1.0 package format; every fact about them is in `references/`, with provenance.

## Core model

- A **catalog** (`marketplace.json`) lists **entries**; each entry names a plugin and points at its package through a **source**.
- Each tool reads catalogs from its own paths in its own order, and accepts its own set of source types; one catalog file is often read by several tools ([feature-matrix.md](references/feature-matrix.md)).
- A **package** is a plugin directory with one or more manifests (`plugin.json`); tools differ in which manifest they read ([multi-tool.md](references/multi-tool.md)).
- A **version** is the cache key: it decides whether a user receives a change ([releases.md](references/releases.md)).
- Tools fail quietly: Codex skips an entry it cannot read, Copilot CLI rejects a whole catalog for one bad entry, and Claude Code ignores unknown keys; a clean `claude plugin validate` says nothing about the other two.

## Defaults

- Package a plugin meant for several tools as an Agent Plugins root `plugin.json` plus `mcp.json`, with a Claude Code adapter (`.claude-plugin/plugin.json` plus `.mcp.json`), because Claude Code reads only the adapter and Codex and Copilot CLI read only the portable pair.
- Publish one native catalog per tool family you target (`.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json`), parity-checked, because a single shared catalog is limited to the source types every reader of it accepts.
  A single `.claude-plugin/marketplace.json` is a valid choice when its entries use only sources all its declared readers accept; record that choice in `marketplace-policy.json`.
- Deliver a plugin's slash commands as skills (`skills/<name>/SKILL.md`), and convert an existing `commands/<name>.md` the same way when packaging for several tools, because Claude Code treats both as the same `/<name>`, and once a portable root `plugin.json` exists only a skill still reaches Codex and Copilot CLI users ([multi-tool.md](references/multi-tool.md)).

## Workflows

Run the validator from this skill: `check-marketplace <marketplace root>` when it is installed, otherwise `uv run <this skill's directory>/scripts/check_marketplace.py <marketplace root>`; add `--format json` for machine-readable output ([validation.md](references/validation.md)).

### Create a marketplace

1. Write `marketplace-policy.json` with the target readers (R1).
2. Choose catalogs (see Defaults) and source types every declared reader of each catalog accepts (R2, R3, R4).
3. Name entries after their plugins' manifests (R8), and disclose executable components in each description (R11).
4. List every plugin the request names in every catalog it names, even when a reader cannot run part of it; say in the report what will not work in which tool, and leave a plugin out of a catalog only when the user decides to.
5. Set versions (R6), then run the validator and the load checks in [validation.md](references/validation.md) for each reader, isolated (R15).
6. Report as R12 requires.

### Add a plugin

1. Read every manifest the plugin has, and every catalog in the repository.
2. If the plugin's manifests record different versions, do not add it as is: pick one value, set it in every place R6 names, and say in the report which values disagreed and which one you kept and why.
3. Add the entry to every catalog whose readers should offer it; leave a documented intentional difference alone and record any new one (R10).
4. Validate and load-check as in Create, then report as R12 requires.

### Release a plugin version

1. For a remote source, review the change between the pinned content and the new content before moving the pin (R5): list the commits and read the diff, looking for new network calls, data collection, executable components, and changed permissions.
   If the change adds behaviour users did not agree to, hold the release and report why instead of moving the pin.
2. Move every pin for the plugin in every catalog (R4), and change the version everywhere R6 names it (R7).
3. Validate and load-check, then report as R12 requires, including how the release reaches each tool's users ([releases.md](references/releases.md)).

### Audit a marketplace

1. Change no files unless asked.
2. For each declared reader, work out which catalog it reads and which entries it will offer, skip, or reject ([feature-matrix.md](references/feature-matrix.md)).
3. Run the validator, then the load checks the environment allows (R15).
4. Report findings in two lists: **defects** — anything that changes what a tool loads, installs, or delivers, or breaks a rule — each naming the entry, the tool, and the evidence; and **suggestions** — naming, wording, and style — kept out of the defect list.
5. Report every check level as R12 requires; a green CI run or a passing `claude plugin validate` is one check, not a verdict.

### Port a plugin to another tool

1. Read [feature-matrix.md](references/feature-matrix.md) for which of the plugin's components the target tool loads, and in what form.
2. Add the target's manifest additively; never delete another tool's files to make a plugin portable, except to convert commands to skills (see Defaults), and name each converted command in the report.
   A portable root `plugin.json` changes what Codex and Copilot CLI read, so check what the plugin gains and loses in each tool first ([multi-tool.md](references/multi-tool.md), "What adding the portable pair changes").
3. Load-check the port in each tool without opening a model session ([validation.md](references/validation.md), "Seeing what loaded").
4. Report, per tool, what loads, what loads in another form, and what does not load, citing the reference or the check for each claim.

## Rules

- **R1** Declare the target readers in `marketplace-policy.json` before choosing sources or layouts.
- **R2** Use only source types that every declared reader of that catalog accepts.
- **R3** Local sources start with `./`, contain no `..`, and resolve (after symlinks) inside the marketplace root.
- **R4** Every remote source is pinned to immutable content using its source type's mechanism: a full commit `sha` for git sources (`github`, `url`, `git-subdir`), `sha256` for `archive`, an exact version (not a range or dist-tag) for `npm`; `command` sources are not used in a published catalog because they cannot be pinned; the one exception is a git ref declared as a channel, with a reason, in `marketplace-policy.json`.
- **R5** A pin moves only after the change between the old and new pinned content has been reviewed.
- **R6** For each reader, the plugin's version is set in that reader's authoritative field (the per-reader table in [releases.md](references/releases.md)), and every version value recorded anywhere for that plugin is equal.
- **R7** A release changes the version value in every place R6 records it.
- **R8** A catalog entry's `name` equals the plugin manifest's `name`, and satisfies every declared reader's name rules.
- **R9** Treat a published plugin name as permanent; rename or remove through the reader's documented mechanism (`renames`, `forceRemoveDeletedPlugins`) where one exists.
- **R10** Every difference in membership or version between catalogs in one repo has a recorded reason in `marketplace-policy.json`.
- **R11** An entry's description discloses executable components (hooks, MCP servers, LSP servers, `bin/`) and external services.
- **R12** Report schema, local, remote, catalog-discovery, and package-load results separately; report skipped or inconclusive checks as such, and name every check that was not run.
- **R13** When a covered tool's installed version is newer than the version a reference was verified against, re-check any fact the current decision depends on against the live source before relying on it.
- **R14** When a reference and an official validator disagree, follow the validator and report the disagreement.
- **R15** Never install into the user's real tool configuration, execute plugin code, or open a model session while validating; run each tool with throwaway configuration as [validation.md](references/validation.md) describes, or do not run it.

## Reference map

- [claude-code.md](references/claude-code.md): Claude Code's catalog, entry, source, manifest, name, version, and validator facts; read before writing or checking anything Claude Code reads.
- [codex.md](references/codex.md): Codex's catalog paths, sources, both manifest formats, cache, updates, and Claude interop; read when Codex is a reader.
- [copilot-cli.md](references/copilot-cli.md): Copilot CLI's catalog paths, accepted sources, manifests, and MCP handling; read when Copilot CLI is a reader.
- [agent-plugins.md](references/agent-plugins.md): the portable package format; read when writing or checking a root `plugin.json` or `mcp.json`.
- [feature-matrix.md](references/feature-matrix.md): components, source types, and name and version rules side by side; read to decide what works where.
- [multi-tool.md](references/multi-tool.md): the packaging and catalog defaults, what each tool reads from a dual-packaged plugin, and when to deviate.
- [releases.md](references/releases.md): the per-reader version table (R6), pin moves, and how a change reaches each tool's users; read before any release.
- [validation.md](references/validation.md): check levels, the validator, safe isolated tool checks, seeing what loaded without a model session, and the report format.
- [freshness.md](references/freshness.md): provenance blocks and the R13 procedure; read when a tool is newer than a reference says.
