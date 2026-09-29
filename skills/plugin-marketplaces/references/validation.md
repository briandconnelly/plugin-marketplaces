# Validation

How to check a marketplace, what each check can prove, and how to report the result (R12).
Rules are cited by id from [SKILL.md](../SKILL.md); each fact cites a row of the Provenance table.

## Check levels

| Level | Question | Instrument |
| --- | --- | --- |
| Schema | Do the catalogs and manifests parse and match their formats? | the validator; `claude plugin validate --strict` |
| Local | Do paths, sources, names, versions, and catalog parity follow the rules? | the validator |
| Remote | Do pinned sources exist and match their pins? | `git ls-remote`, a no-checkout fetch of the pinned `sha`, the npm registry |
| Catalog discovery | Does each tool list every entry it should? | each tool's add-and-list commands, isolated |
| Package load | Does each tool load the plugin's components? | each tool's install and inspection commands, isolated |

A network or authentication failure, or a host that refuses to fetch a commit by SHA, makes a remote check inconclusive, not failed and not passed [E1].

## The validator

- Run `check-marketplace <root>` (or `uv run <skill directory>/scripts/check_marketplace.py <root>`); `--format json` gives `statuses` per level and `findings`, each with `check`, `rule`, `severity`, `file`, `pointer`, and `message` [E2].
- It reads `marketplace-policy.json` for the declared readers; without one it infers readers only from each tool's own first-choice catalog and says so in a `policy.inferred` finding, so declare readers to check compatibility with every tool that reads a catalog (R1) [E2].
- It runs `claude plugin validate --strict --json` itself when `claude` is on `PATH`, with a throwaway `CLAUDE_CONFIG_DIR` created under `TMPDIR`; set `TMPDIR` to your throwaway directory when temporary files must stay inside it [E2].
- It never installs anything or runs plugin code; in this version its remote, discovery, and package-load levels report `skipped`, so those levels need the tool checks below or must be reported as not run (R12) [E2].
- Exit status is 0 with no error findings, 1 with error findings, and 2 when the validator itself failed [E2].

## Running a tool safely (R15)

Point every tool at throwaway state before its first command, including `--version`:

```bash
T="$PWD/.tool-homes"            # a throwaway directory; keep it out of commits
mkdir -p "$T"/{home,xdg,tmp,claude,codex,copilot,copilot-cache}
: > "$T/gitconfig"
export HOME="$T/home" XDG_CONFIG_HOME="$T/xdg" TMPDIR="$T/tmp" \
  GIT_CONFIG_GLOBAL="$T/gitconfig" GIT_CONFIG_NOSYSTEM=1 \
  CLAUDE_CONFIG_DIR="$T/claude" CODEX_HOME="$T/codex" \
  COPILOT_HOME="$T/copilot" COPILOT_CACHE_HOME="$T/copilot-cache"
```

- Export the variables in the same shell call that runs the tool; a failed `cd` or a new shell loses them [E3].
- Set `XDG_CONFIG_HOME` whenever you set `HOME`: git reads `$XDG_CONFIG_HOME/git/config`, so a git configuration write with only `HOME` changed lands in the real configuration [E3].
- `CODEX_HOME` must exist before Codex runs [E4].
- To make a tool fetch `github.com/owner/repo` from a local mirror, add `insteadOf` rules to the throwaway `GIT_CONFIG_GLOBAL`, never to the real one [E5]:

  ```ini
  [url "file:///absolute/path/to/mirrors/"]
  	insteadOf = https://github.com/owner/
  	insteadOf = git@github.com:owner/
  ```

- On macOS, deny outbound network traffic to a tool you only mean to run locally: `sandbox-exec -p '(version 1)(allow default)(deny network-outbound (remote ip))' <command>` [E5].
- Run tools with stdin from `/dev/null`, so none waits for input.
- Never send a prompt or open a session — `claude -p`, `codex exec`, `copilot -p`, an interactive session, or `copilot --acp` — to check a plugin: the throwaway variables do not isolate Copilot CLI's sign-in, and a session runs the plugin's code [E3] [E6].
- Avoid `sensitive` `userConfig` values in checks: Claude Code stores them in the system keychain, which `CLAUDE_CONFIG_DIR` does not isolate [E3].

## Catalog discovery

| Tool | Commands | What to compare |
| --- | --- | --- |
| Claude Code | `claude plugin validate <root> --strict --json`; `claude plugin marketplace add <root>` | errors and warnings; add succeeds |
| Codex | `codex plugin marketplace add <root>`; `codex plugin list --available --json` | every entry Codex should offer is listed; a missing one was skipped silently |
| Copilot CLI | `copilot plugin marketplace add <root>`; `copilot plugin marketplace browse <name> --json` | add succeeds, since one bad source rejects the whole catalog; every entry is listed |

The commands are from [E4], [E6], and [E7].
Check a clean export (`git archive HEAD | tar -x -C "$T/export"`) rather than a working tree, so untracked files and the throwaway directory are not read as part of the plugin [E4].

## Seeing what loaded

| Tool | Starts nothing | Starts plugin MCP servers (stand-in plugins only) |
| --- | --- | --- |
| Claude Code | `claude plugin details <plugin>@<marketplace>`: skills, agents, hooks, MCP and LSP servers; `claude plugin list --json`: version and MCP configuration | `claude mcp list` |
| Codex | `codex plugin add <plugin>@<marketplace> --json`: installed version; `codex mcp list --json`: MCP configuration | `codex debug prompt-input`: the skills Codex presents, including migrated commands |
| Copilot CLI | `copilot plugin install`: component count; `copilot plugin list`; `copilot skill list`; `copilot mcp list`; `copilot mcp get <server>` | none found |

The table is from [E6].
`codex debug prompt-input` starts a plugin's MCP servers but not its hooks, so on a plugin with no MCP servers it runs no plugin code [E6].
Copilot CLI's `plugin`, `skill`, and `mcp` subcommands open no session, so they are safe to run under throwaway homes; only a prompt, an interactive session, or `copilot --acp` reaches the signed-in account [E6] [E3].
No command shows Codex's or Copilot CLI's view of a plugin's agents, or Copilot CLI's view of its hooks, so report those load checks as unproven rather than passed.
To see what a server receives at start, check a stand-in plugin you wrote whose server records its arguments, not the plugin under review (R15).

## Reporting (R12)

Report one line per level and tool, with its status and evidence, for example:

```text
Schema     passed        check-marketplace: schema.parse passed; claude plugin validate --strict: 0 errors
Local      failed        check-marketplace: local.version-mismatch for docs-kit (1.2.0 vs 1.1.0)
Remote     inconclusive  git fetch of fmt-kit@<sha>: network unavailable
Discovery  Codex         not run: codex is not installed here
Load       Copilot CLI   unproven: no command shows agents
```

A pipeline that passed tells you only which checks it ran; name the ones it did not run.

## Provenance

Verified against: claude 2.1.284, codex-cli 0.157.1, copilot 1.0.89 on 2026-09-28.
Conformance probes: none yet.

| Id | Evidence | Kind |
| --- | --- | --- |
| E1 | https://code.claude.com/docs/en/plugins/marketplace-reference, fetched 2026-09-27 (hosts that cannot fetch by SHA); `docs/research/2026-09-27-claude-code.md` §1 and `docs/research/README.md`, Known corrections | docs |
| E2 | the validator's source and tests: `skills/plugin-marketplaces/scripts/mpcheck/cli.py`, `run.py`, and `checks_schema.py`; `tests/test_cli.py` | source |
| E3 | plan-2b adjudications: a lost `export` after a failed `cd` (s4-r4), the real git configuration written with only `HOME` changed (preamble-v1 s1-r3), Copilot sessions reaching GitHub (s4-r7), keychain use (s4-r4, s4-r7, s4-r8, s4-r9); `tests/runs/2026-09-28-baseline-summary-2b.md` | run |
| E4 | Codex command-migration probe and source reading on codex-cli 0.157.1; `docs/research/2026-09-28-codex-command-migration-probe.md` and `docs/research/2026-09-27-codex.md` §3 and §5 | probe |
| E5 | probe P2, which used both; `docs/research/2026-09-28-load-and-update-probes.md` | probe |
| E6 | probe P1; `docs/research/2026-09-28-load-and-update-probes.md` | probe |
| E7 | phase-0 probes and probe P3 on Copilot CLI; `docs/research/2026-09-27-phase0-probes.md` and `docs/research/2026-09-28-load-and-update-probes.md` | probe |
