# Codex command-migration probe

Date: 2026-09-28.
This is a hand-written record of a probe prompted by Codex's review of plan 2a; command output is pasted verbatim from the capture files, with the scratch directory shown as `$PROBE`.

## Question

Does Codex load a Claude Code plugin's `commands/` entry when the plugin is installed from a Claude-format catalog, and in what form?
`docs/research/2026-09-27-codex.md` §4 reported automatic command migration from reading the source; this probe observes it.

## Method

The plugin was a copy of `tests/fixtures/scenarios/s4/repo` (review-kit): a Claude Code plugin with `.claude-plugin/plugin.json`, a catalog entry with source `./`, `commands/review.md` whose frontmatter has `description: Review the current diff`, an agent, hooks, and an MCP server.
`CODEX_HOME` pointed at a throwaway directory created beforehand; a first attempt without creating it failed with `Error: failed to resolve CODEX_HOME`, so Codex requires the directory to exist.
The real `~/.codex` was hashed before and after, excluding its `log` and `sessions` directories.

```text
codex-cli 0.157.1
```

## Result

`codex plugin add review-kit@review-kit --json` installed the plugin:

```json
{
  "pluginId": "review-kit@review-kit",
  "name": "review-kit",
  "marketplaceName": "review-kit",
  "version": "2.0.0",
  "installedPath": "$PROBE/codex-home/plugins/cache/review-kit/review-kit/2.0.0",
  "authPolicy": "ON_INSTALL"
}
```

The installed copy contained these files:

```text
./.claude-plugin/marketplace.json
./.claude-plugin/plugin.json
./.codex-plugin/migrated-command-skills/source-command-review/SKILL.md
./.mcp.json
./agents/reviewer.md
./commands/review.md
./hooks/hooks.json
./README.md
./scripts/start.sh
./server/run.sh
```

The migrated command skill:

```markdown
---
name: "source-command-review"
description: "Review the current diff"
---

# source-command-review

Use this skill when the user asks to run the migrated source command `review`.

## Command Template

Review the staged diff and list problems.
```

Real config unchanged.

## Conclusion

Codex installs a Claude-format plugin and converts each command whose frontmatter has a non-empty `description` into a skill under `.codex-plugin/migrated-command-skills/`, named `source-command-<command>`, so a Claude Code command reaches Codex users as a skill without any change by the plugin author.
Codex also requires `CODEX_HOME` to exist before it runs.
