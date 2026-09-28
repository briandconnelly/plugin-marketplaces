# Phase-0 probe record

Date: 2026-09-27.
This is a hand-written record of the phase-0 gate (spec §11), not a subagent report; command output below is pasted verbatim from the probe's capture files, with the scratch directory shown as `$SPIKE`.

## Method

Coreutils `timeout` is absent on this macOS host, so every bounded command ran under `perl -e 'alarm N; exec @ARGV'`.
Every `copilot` command ran with `< /dev/null`.
The fixture marketplace (`$SPIKE/mkt/.claude-plugin/marketplace.json`) had four entries:

```json
{
  "name": "spike-mkt",
  "owner": {"name": "Spike"},
  "plugins": [
    {"name": "alpha", "source": "./plugins/alpha", "description": "must load"},
    {"name": "control-npm", "source": {"source": "npm", "package": "left-pad", "version": "1.3.0"}, "description": "npm is not a documented Copilot source type"},
    {"name": "control-bare", "source": "plugins/alpha", "description": "bare path without ./"},
    {"name": "control-unknown", "source": {"source": "not-a-source-type", "url": "https://example.com/x.git"}, "description": "a source type no tool defines; the known-rejected control for every tool"}
  ]
}
```

The plugin at `plugins/alpha` had `.claude-plugin/plugin.json` (`name` `alpha`, `version` `0.1.0`) and one skill, `skills/hello/SKILL.md`, and no hooks, MCP servers, or scripts.

## GitHub Copilot CLI 1.0.88

### Isolation

The real `~/.copilot` was hashed after every unisolated command had run, then a read-only `copilot plugin marketplace list` ran with `COPILOT_HOME` and `COPILOT_CACHE_HOME` set to throwaway directories.
The real configuration hashed identically afterwards, and the throwaway home gained log files, so the two variables isolate the CLI.
The real configuration also hashed identically after every later step, including the final check once the variables were unset.

### Catalog discovery: pass

Adding the four-entry fixture failed for the whole catalog, naming the two unsupported sources:

```text
Failed to add marketplace: Error: Request plugins.marketplaces.add failed with message: Invalid marketplace.json: plugins.1.source: Invalid input, plugins.3.source: Invalid input
Included with GitHub Copilot:
  ◆ copilot-plugins (GitHub: github/copilot-plugins)
  ◆ awesome-copilot (GitHub: github/awesome-copilot)
```

Copilot CLI validates every entry when a marketplace is added and rejects the entire catalog when any entry's source is invalid, unlike Codex, which skips the entry.
A second fixture holding only the two entries Copilot accepted (`alpha` and `control-bare`) was added and browsed:

```json
[
  {
    "name": "alpha",
    "description": "must load",
    "marketplace": "spike-mkt-a"
  },
  {
    "name": "control-bare",
    "description": "bare path without ./",
    "marketplace": "spike-mkt-a"
  }
]
```

### Package load: pass

Installing `alpha` reported a loaded component, and the installed listing carries the manifest's version:

```text
Plugin "alpha" installed successfully. Installed 1 skill.
Enabled "alpha@spike-mkt-a". It is loaded live from $SPIKE/mkt-a/plugins/alpha, so edits take effect on the next session — nothing was copied.
```

```json
[
  {
    "name": "alpha",
    "marketplace": "spike-mkt-a",
    "version": "0.1.0",
    "enabled": true,
    "source": "live",
    "installedFrom": "$SPIKE/mkt-a"
  }
]
```

A third fixture held one entry whose `./plugins/missing` directory does not exist; it was added and browsed without error, and its install failed:

```text
Failed to install plugin: Error: Request plugins.install failed with message: Plugin source directory not found: $SPIKE/mkt-b/plugins/missing
```

The failed install still left a listing entry, distinguishable only by `enabled: false` and the absence of `version`:

```json
[
  {
    "name": "alpha",
    "marketplace": "spike-mkt-a",
    "version": "0.1.0",
    "enabled": true,
    "source": "live",
    "installedFrom": "$SPIKE/mkt-a"
  },
  {
    "name": "control-missing",
    "marketplace": "spike-mkt-b",
    "enabled": false,
    "source": "live",
    "installedFrom": "$SPIKE/mkt-b"
  }
]
```

A package-load probe must therefore check `enabled` and `version`, not list membership alone.

### Controls

| Entry | Source | Observed |
| --- | --- | --- |
| `control-unknown` | `{"source": "not-a-source-type"}` | rejected at `marketplace add` (whole catalog) |
| `control-npm` | `npm` | rejected at `marketplace add` (whole catalog) |
| `control-bare` | `plugins/alpha` (no `./`) | accepted; installed and reported one skill, then collapsed into `alpha` in the listing because both resolve to a manifest named `alpha` |
| `control-missing` | `./plugins/missing` | accepted at `add` and `browse`; rejected at install |

The `control-bare` result shows Copilot CLI resolves bare relative paths, so its `path_requires_dot_slash` is false, and it shows the cost of an entry name that differs from the manifest name (spec R8).

## VS Code 1.139.1 (commit 04c0d99f)

### Source reading

The marketplace service reads `chat.plugins.enabled` and `chat.plugins.marketplaces`, and logs a warning naming each skipped entry, but it fetches catalogs only inside `fetchMarketplacePlugins`, which the plugin views call on demand (`src/vs/workbench/contrib/chat/common/plugins/pluginMarketplaceService.ts` at the installed commit):

```text
460: 		if (!this._configurationService.getValue<boolean>(ChatConfiguration.PluginsEnabled)) {
461: 			return [];
462: 		}
1213: 			logContext.logService.warn(`${logContext.logPrefix} Skipping plugin '${logContext.pluginName}': unknown source kind '${rawSource.source}'`);
```

### Launch attempt

VS Code was launched for 45 seconds with a throwaway `--user-data-dir` and `--extensions-dir`, `--log trace`, `chat.plugins.enabled: true`, and `chat.plugins.marketplaces` set to a `file://` git copy of the fixture.
The profile was created, but its log directory `logs/20260927T183826` held no files, and no marketplace line was written anywhere under the profile.

### Verdict

Catalog discovery: no headless observation obtained, because the catalog fetch runs only when a plugin view requests it and the launch produced no machine-readable output; this is an environment limit, not evidence that VS Code fails to read the catalog.
Package load: unproven (not attempted, per the plan).

## Decision

Copilot CLI remains in scope: it passed catalog discovery and package load with isolated, machine-readable probes.
VS Code leaves scope under spec §3.1 and the coverage rule, because no headless probe could observe its catalog handling.
