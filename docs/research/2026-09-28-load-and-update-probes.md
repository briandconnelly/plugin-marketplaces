# Load-observation, update-delivery, and dual-packaging probes

Date: 2026-09-28.
This is a hand-written record of four probes run while writing plan 2c; command output is quoted verbatim from the capture files, trimmed where marked, with the scratch directory shown as `$PROBE`.
The probe scripts are archived beside this record in `2026-09-28-load-and-update-probes/`; the full captures are not, because they hold the probing machine's paths and, from `codex debug prompt-input`, its working directory's instructions.

## Method

Every tool ran with `HOME`, `XDG_CONFIG_HOME`, `TMPDIR`, `GIT_CONFIG_GLOBAL`, `CLAUDE_CONFIG_DIR`, `CODEX_HOME`, `COPILOT_HOME`, and `COPILOT_CACHE_HOME` pointing at throwaway directories under `$PROBE`, with `GIT_CONFIG_NOSYSTEM=1`, stdin from `/dev/null`, a `perl -e 'alarm N; exec @ARGV'` time limit, and inside `sandbox-exec -p '(version 1)(allow default)(deny network-outbound (remote ip))'`, which refuses outbound IP connections.
No command sent a prompt to a model or opened a model session.
`~/.codex`, `~/.copilot`, and `~/.claude/plugins` were snapshotted with `tests/eval/home_snapshot.py` before the first probe and after the last; the only changes were `~/.codex/logs_2.sqlite-shm`, `~/.codex/logs_2.sqlite-wal`, and `~/.codex/models_cache.json`, the files a running Codex app-server daemon writes, as in the plan-2b batches.

Versions: `2.1.284 (Claude Code)`, `codex-cli 0.157.1`, `GitHub Copilot CLI 1.0.89.`

## P1: observing a plugin's components without a model session

The fixture plugin `probe-kit` had one skill (`skills/hello`), one command with a `description` (`commands/review.md`), one agent (`agents/reviewer.md`), a `SessionStart` command hook that appends to a log, a `userConfig` option `api_key` with default `default-key`, a root `.mcp.json` declaring `root-srv`, and `mcpServers: "./config/mcp.json"` in `.claude-plugin/plugin.json` naming a second file that declares `named-srv`.
Each server was `sh -c 'echo "$0 $*" >> $PROBE/starts.log'` with the arguments `<server name>`, `${CLAUDE_PLUGIN_ROOT}`, and `${user_config.api_key}`, so every start was recorded with its arguments as the tool expanded them.
The catalogs were `.claude-plugin/marketplace.json` (source `./plugins/probe-kit`) and `.agents/plugins/marketplace.json` (source `{"source": "local", "path": "./plugins/probe-kit"}`).

### Claude Code

`claude plugin list --json` listed both servers, unexpanded, and started neither (trimmed to one server):

```json
    "mcpServers": {
      "root-srv": {
        "command": "sh",
        "args": [
          "-c",
          "echo \"$0 $*\" >> $PROBE/starts.log",
          "root-srv",
          "${CLAUDE_PLUGIN_ROOT}",
          "${user_config.api_key}"
        ]
      },
```

`claude plugin details probe-kit@probe-mkt` listed every component type, with the command counted as a skill, and started nothing:

```text
Component inventory
  Skills (2)  hello, review
  Agents (1)  reviewer
  Hooks (1)  SessionStart  (harness-only — no model context cost)
  MCP servers (2)  root-srv, named-srv  (tool schemas resolved at runtime; not counted)
  LSP servers (0)
```

`claude mcp list` health-checked, and so started, both servers, expanding both placeholders:

```text
plugin:probe-kit:root-srv: sh -c echo "$0 $*" >> $PROBE/starts.log root-srv $PROBE/mkt/plugins/probe-kit default-key - ✘ Failed to connect — CONNECTION_CLOSED: Connection closed
plugin:probe-kit:named-srv: sh -c echo "$0 $*" >> $PROBE/starts.log named-srv $PROBE/mkt/plugins/probe-kit default-key - ✘ Failed to connect — CONNECTION_CLOSED: Connection closed
```

### Codex

`codex mcp list --json` listed only `named-srv`, the server in the file the manifest names, unexpanded, and started nothing (trimmed):

```json
    "name": "named-srv",
    "enabled": true,
    "transport": {
      "type": "stdio",
      "command": "sh",
      "args": [
        "-c",
        "echo \"$0 $*\" >> $PROBE/starts.log",
        "named-srv",
        "${CLAUDE_PLUGIN_ROOT}",
        "${user_config.api_key}"
      ],
```

`codex debug prompt-input` rendered the model-visible prompt without contacting a model, and listed the skill and the migrated command but no agent:

```text
- probe-kit:hello: Say hello when asked to greet. (file: r2/hello/SKILL.md)
- probe-kit:source-command-review: Review the current diff (file: r1/source-command-review/SKILL.md)
```

It also started `named-srv`, with both placeholders passed through literally, and its prompt carried the `AGENTS.md` of the directory it ran in (`/Users/bdc/projects/skills`), so it reads the working directory's instructions:

```text
named-srv ${CLAUDE_PLUGIN_ROOT} ${user_config.api_key}
```

### Copilot CLI

Install reported one skill, and `copilot skill list` showed the command as a skill; no command listed the agent or the hook:

```text
Plugin "probe-kit" installed successfully. Installed 1 skill.
```

```text
Plugin skills:
  hello - Say hello when asked to greet.
  review - Review the current diff
```

`copilot mcp list` listed only `root-srv`, from the root `.mcp.json`, although the manifest names `./config/mcp.json`; `copilot mcp get named-srv` failed with `Error: Server "named-srv" not found.`
`copilot mcp get root-srv` showed the placeholders unexpanded in the command and three root variables set in the environment, and started nothing:

```text
root-srv
  Status: Enabled
  Type: local
  Command: sh -c echo "$0 $*" >> $PROBE/starts.log root-srv ${CLAUDE_PLUGIN_ROOT} ${user_config.api_key}
  Environment:
    CLAUDE_PLUGIN_ROOT: ***
    COPILOT_PLUGIN_ROOT: ***
    PLUGIN_ROOT: ***
```

### Starts and hooks

The start log held exactly three lines, two from `claude mcp list` and one from `codex debug prompt-input`; the hook log stayed empty.

## P2: does a pushed change reach users without a version bump?

The fixture was a single-plugin repository that is its own marketplace (`source` `./` in both native catalogs, `version` `1.0.0` in `.claude-plugin/plugin.json`, and a skill whose last line names the revision), pushed to a local bare repository.
A throwaway `GIT_CONFIG_GLOBAL` rewrote `https://github.com/acme/`, `git@github.com:acme/`, and `ssh://git@github.com/acme/` to that repository with `insteadOf`, and `CLAUDE_CODE_PLUGIN_PREFER_HTTPS=1` was set, so both tools believed they cloned `github.com/acme/focus-timer`.

| Step | Claude Code installed copy | Codex installed copy |
| --- | --- | --- |
| Add and install revision A, version 1.0.0 | `1.0.0`: revision A | `1.0.0`: revision A |
| Push revision B, version unchanged; `claude plugin marketplace update` and `claude plugin update`; `codex plugin marketplace upgrade` | `1.0.0`: revision A | `1.0.0`: revision B |
| Push revision C, version 1.0.1; the same commands | `1.0.1`: revision C | `1.0.1`: revision C |

Claude Code refused the unbumped change:

```text
✔ focus-timer is already at the latest version (1.0.0).
```

and took the bumped one:

```text
✔ Plugin "focus-timer" updated from 1.0.0 to 1.0.1 for scope user. Restart to apply changes.
```

`codex plugin marketplace upgrade focus-timer --json` replaced the installed copy in place in both cases, with no reinstall:

```json
{
  "selectedMarketplaces": [
    "focus-timer"
  ],
  "upgradedRoots": [
    "$PROBE/codex/.tmp/marketplaces/focus-timer"
  ],
  "errors": []
}
```

## P3: Copilot CLI catalog handling on 1.0.89

The phase-0 control catalog (`docs/research/2026-09-27-phase0-probes.md`) was rejected whole, as on 1.0.88:

```text
Failed to add marketplace: Error: Request plugins.marketplaces.add failed with message: Invalid marketplace.json: plugins.1.source: Invalid input, plugins.3.source: Invalid input
```

A catalog with a local entry and `github`, `url`, and `git-subdir` entries was also rejected whole, naming the `git-subdir` entry:

```text
Failed to add marketplace: Error: Request plugins.marketplaces.add failed with message: Invalid marketplace.json: plugins.3.source: Invalid input
```

Without the `git-subdir` entry the catalog was added, and `copilot plugin marketplace browse ctl-remote2 --json` listed `alpha`, `gh` (`github`), and `viaurl` (`url`).

## P4: which manifest each tool reads from a dual-packaged plugin

The plugin `dual` carried a portable root `plugin.json` (Agent Plugins `$schema`, `version` `1.1.0`) with `mcp.json` declaring `portable-srv`, and a Claude adapter `.claude-plugin/plugin.json` (`version` `1.0.0`) with `.mcp.json` declaring `claude-srv`.

| Tool | Version installed | MCP server listed | Command |
| --- | --- | --- | --- |
| Claude Code | `1.0.0` | `claude-srv` | `claude plugin details dual@dual-mkt` |
| Codex | `1.1.0` | `portable-srv`, with `PLUGIN_ROOT` and `PLUGIN_DATA` set | `codex plugin add dual@dual-mkt --json`, `codex mcp list --json` |
| Copilot CLI | `1.1.0` | `portable-srv` | `copilot plugin list`, `copilot mcp list` |
