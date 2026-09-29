# Plan-3 probes: conformance first runs, help text, entry hooks, and upstream pins

Date: 2026-09-28.
This is a hand-written record of the observations made while writing plan 3, with the scratch directory shown as `$PROBE` or `$WORK`.
Every tool ran through `tests/conformance/sandbox.py`: throwaway `HOME`, `XDG_CONFIG_HOME`, `XDG_CACHE_HOME`, `TMPDIR`, `CLAUDE_CONFIG_DIR`, `CODEX_HOME`, `COPILOT_HOME`, and `COPILOT_CACHE_HOME`, an empty `GIT_CONFIG_GLOBAL` with `GIT_CONFIG_NOSYSTEM=1`, only `PATH` and locale variables passed through, and outbound IP traffic denied (`sandbox-exec` on macOS, `unshare -rn` on Linux).
No command sent a prompt to a model, and no fixture held a hook or an MCP server.

## Conformance probes, first runs

`uv run python tests/conformance/run.py` on macOS with the tools installed on this machine:

```text
Tools: claude 2.1.284 (Claude Code); codex codex-cli 0.157.1; copilot GitHub Copilot CLI 1.0.89.
Network denied during probes: True.
```

`python3 tests/conformance/run.py --require-tools` in a Docker `ubuntu:24.04` container (Python 3.12.3, Node 22) with the latest CLIs from `npm install -g @anthropic-ai/claude-code @openai/codex @github/copilot`, the throwaway environment the weekly Action uses:

```text
Tools: claude 2.1.284 (Claude Code); codex codex-cli 0.158.0; copilot GitHub Copilot CLI 1.0.89.
Network denied during probes: True.
```

All 13 probes reported `held` on both, including every Codex probe on codex-cli 0.158.0:

| Probe | macOS | Linux |
| --- | --- | --- |
| `claude-validate-misses-entry-hooks-path` | held | held |
| `claude-lists-commands-as-skills` | held | held |
| `claude-reads-adapter-not-portable-root` | held | held |
| `codex-reads-claude-catalog` | held | held |
| `codex-prefers-agents-catalog` | held | held |
| `codex-skips-github-source` | held | held |
| `codex-migrates-described-commands` | held | held |
| `codex-reads-portable-root` | held | held |
| `copilot-prefers-github-catalog` | held | held |
| `copilot-rejects-catalog-with-git-subdir` | held | held |
| `copilot-offers-commands-as-skills` | held | held |
| `copilot-portable-root-drops-commands` | held | held |
| `converted-command-reaches-every-tool` | held | held |

`copilot-rejects-catalog-with-git-subdir` observed: `Failed to add marketplace: Error: Request plugins.marketplaces.add failed with message: Invalid marketplace.json: plugins.1.source: Invalid input`.
`converted-command-reaches-every-tool` observed the skills `hello` and `review` in all three tools for a plugin with a portable root `plugin.json` whose command had been moved to `skills/review/SKILL.md`.

## Help text

Each command's output was identical in two fresh sandboxes, and identical between macOS (codex-cli 0.157.1) and Linux (codex-cli 0.158.0).
The sha256 of each text, as `tests/conformance/run.py --repin-help` computes it:

| sha256 | Command |
| --- | --- |
| `b0214cc3567a6eff8fc62215006a94043c8debaacc89c366d4e0ce8b70a0c5ab` | `claude plugin --help` |
| `e2c4fe9eb214da5b8136bcd09717609beef572de3b7b84f7492aceeeaee12894` | `claude plugin marketplace --help` |
| `a517a3a2d1801d812751d98c8bc4d27de6bb5367aafc67495e0cde3a99680124` | `codex plugin --help` |
| `d0da9efccab098da6b32bdd8e84f649bcf60fd4fb261eb80491ba1b02cda7487` | `codex plugin marketplace --help` |
| `5329cfea11820d22ec67a02bbb368983bc5f2939157e641a318380c100b5b82e` | `copilot plugin --help` |
| `fff2d4730d9ddeb93a7eff4aeee04e67dea23b4b410f5dceefd66c73d3909c69` | `copilot plugin marketplace --help` |
| `4d7363b82d0703a13021ada1194c92fa9d02176c2d4db1569f18ecda4a80d8e6` | `copilot skill --help` |

## Entry `hooks` forms and `claude plugin validate`

On claude 2.1.284, `claude plugin validate --strict --json` on one catalog with six entries that differ only in `hooks`, where `events` is `{"SessionStart": [{"hooks": [{"type": "command", "command": "true"}]}]}`:

| Entry `hooks` | Error |
| --- | --- |
| `"./hooks/hooks.json"` (a path) | none |
| `["./hooks/hooks.json"]` (an array) | none |
| `events` (an event map) | none |
| `{"hooks": events}` (wrapped as in `hooks/hooks.json`) | `plugins.3.hooks: Invalid input` |
| `{"hooks": {}}` | `plugins.4.hooks: Invalid input` |
| `{}` | none |

So the inline form `validate` accepts is the event map itself, and the wrapped form a `hooks/hooks.json` file uses is rejected; the path and array forms still pass `validate`, as `references/claude-code.md` states.
The probe `claude-validate-misses-entry-hooks-path` uses the wrapped form as its control.

## Copilot CLI and commands

On copilot 1.0.89, installing a Claude-format plugin with skill `hello` and command `commands/review.md` reported `Installed 1 skill.`, while `copilot skill list` listed both `hello` and `review` under `Plugin skills:`; the same plugin with a portable root `plugin.json` listed only `hello`.
With two installed plugins that each offer `hello`, `copilot skill list` prefixed the colliding names (`cmd:hello`, `port:hello`), so each probe installs one plugin into its own sandbox.

## Upstream pins, first check

`uv run python tests/check_upstream.py` on 2026-09-28: 30 pins, 12 not `same`.

- The 11 documentation pins carry no verified hash yet (`unverified`); each page returned identical bytes on two consecutive fetches, so a whole-page hash is stable, except that `settings-reference.md` (395,513 bytes) is pinned by its `## Plugins and skills` section only.
- `https://developers.openai.com/codex/plugins/build.md` returned the same bytes as `https://developers.openai.com/plugins/build/plugins.md` (sha256 prefix `4b003d3d35`), so one pin covers both URLs the references cite.
- `npm-codex` reported `released`: `@openai/codex` 0.158.0 is published; the references were verified against 0.157.1.
- Both vendored Agent Plugins 1.0.0 schemas equal the published ones (`plugin.schema.json` `0a4aad95ce…`, `mcp.schema.json` `6539175bfc…`).
- The nine `openai/codex` source pins, pinned at `659b35f1316eda27ef61850dd0832c4a4e95c120`, are unchanged at the latest release `rust-v0.158.0`; at `main` on the same day, `manager.rs`, `manifest.rs`, `marketplace.rs`, and `store.rs` differ, so the pins compare with the latest release, which is what users run.
  The same pin compared with `main` reported `changed` with a compare link, so an unchanged result is not a broken instrument.
- `agentplugins/agent-plugins-spec` and `agentplugins/agent-plugins-example` have not moved from `ff8ab5e392` and `5f3f5084a8`; `spec/` still holds `1.0.0.md` and `1.1.0.md`.
