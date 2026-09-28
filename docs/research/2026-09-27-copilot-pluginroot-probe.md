# Copilot CLI metadata.pluginRoot probe

Date: 2026-09-27.
This is a hand-written record of a follow-up probe prompted by a review comment on PR #1; command output is pasted verbatim from the capture files, with the scratch directory shown as `$PROBE`.

## Question

Does GitHub Copilot CLI 1.0.88 resolve a bare plugin name under the catalog's `metadata.pluginRoot`, as Claude Code does?
The validator's `copilot-cli` reader entry had assumed it does not, as a strict default that no probe had checked.

## Method

The same isolation as the phase-0 gate: `COPILOT_HOME` and `COPILOT_CACHE_HOME` set to throwaway directories, the real `~/.copilot` hashed before and after, and every command bounded with `perl -e 'alarm N; exec @ARGV'` and run with `< /dev/null`.
The fixture catalog set `metadata.pluginRoot` to `./plugins` and listed one entry, `alpha`, whose source is the bare name `alpha`; the plugin lived at `plugins/alpha` with `version` `0.1.0` and one skill.

```json
{"name":"proot-mkt","owner":{"name":"P"},"metadata":{"pluginRoot":"./plugins"},"plugins":[{"name":"alpha","source":"alpha","description":"bare name under pluginRoot"}]}
```

## Result

```text
Marketplace "proot-mkt" added successfully.
Plugin "alpha" installed successfully. Installed 1 skill.
Enabled "alpha@proot-mkt". It is loaded live from $PROBE/mkt/plugins/alpha, so edits take effect on the next session — nothing was copied.
```

```json
[
  {
    "name": "alpha",
    "marketplace": "proot-mkt",
    "version": "0.1.0",
    "enabled": true,
    "source": "live",
    "installedFrom": "$PROBE/mkt"
  }
]
```

The real configuration hashed identically afterwards.

## Conclusion

Copilot CLI resolved the bare name under `metadata.pluginRoot`, loaded the plugin from `plugins/alpha`, and listed it enabled with the manifest's version, so the reader entry's `honours_plugin_root` is true.
