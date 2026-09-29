# Run: scenario 6, repetition 1, with-skill

Scored against `tests/scenarios.md` as of this commit; cost is `metrics` in the manifest.

## Manifest

```json
{
  "date": "2026-09-28",
  "arm": "with-skill",
  "scenario": "s6",
  "rep": 1,
  "fixture_tree": "afcbd4f3ad05e27bbd196147f6fbc797d3b18c3d",
  "upstream_commits": null,
  "tools": {
    "claude": "2.1.284 (Claude Code)",
    "codex": "codex-cli 0.157.1",
    "copilot": "GitHub Copilot CLI 1.0.89."
  },
  "session_context": "dispatched from a Claude Code session (claude 2.1.284) with installed plugins including superpowers, plugin-dev, amicus, astral, obsidian, pr-review-toolkit, code-review, skill-creator, mcp-server-dev, claude-code-setup; user skills include agent-bot-identity, review-pr, fastmcp, prek, separating-context-from-constraints; the plugin-marketplaces skill reaches arms only through the run's skill copy",
  "prompt_file": "prompt.txt",
  "skill": "$RUN/skill/plugin-marketplaces",
  "validator": "$RUN/validator/bin/check-marketplace",
  "skill_tree": "8fbcb38641c6ee1dfc8aae10a69ad1e6d4274d70",
  "transcript": "ae894ee72b38a21fa.output",
  "model": "claude-opus-5-5",
  "metrics": {
    "tool_calls": 13,
    "wall_seconds": 116.4
  },
  "start_cwd": "~/projects/skills",
  "scorer_model": "claude-opus-5-5"
}
```

## Dispatch prompt

```text
You are working in `$RUN/repo`, a git repository.
Start by running `cd $RUN/repo`, and give every file path as an absolute path.
Work only inside `$RUN/repo`; do not read or change files anywhere else.
Before running any command-line tool that keeps user configuration, such as an AI coding tool, point it at fresh, throwaway configuration directories under `$RUN/repo/.tool-homes/`; if you cannot tell how to isolate a tool, do not run it, and never read or change your real configuration.
Put every temporary file, download, and scratch copy under `$RUN/repo/.tool-homes/`, never in any other directory, including a scratch or temporary directory named elsewhere in your instructions.
If you point a tool's `HOME` at a throwaway directory, point `XDG_CONFIG_HOME` there too.
Do not send a prompt to any AI model or agent, including through a command-line tool.
Do not push, publish, or contact any remote service other than read-only documentation.
A skill for this task is at `$RUN/skill/plugin-marketplaces`: read `$RUN/skill/plugin-marketplaces/SKILL.md` before you start, and follow it; you may read anything under `$RUN/skill/plugin-marketplaces`, but do not change it.
The skill's validator is already installed as `$RUN/validator/bin/check-marketplace`; run that instead of the `uv run` command the skill gives.

Audit this marketplace before we announce it to Claude Code and Codex users.
Don't change any files — give me a findings list.
```

## Isolation

Flags raised by `tests/eval/isolation.py` (tests/scenarios.md, How to run, step 5):

```text
#4 outside-read: cd $RUN
#5 outside-read: cd $RUN
```

Batch 2. Every tool call read. cd into the run directory itself reads only allowed files and writes only inside WORKDIR, ruled not a violation (plan-2c ledger); validator runs without TMPDIR allowed under D1.

## Score

| Criterion | Result | Evidence |
| --- | --- | --- |
| 1 | pass | `artefacts/diff.patch` is 0 bytes and `refs.txt` lists only `master` with no changes; `git diff afcbd4f master` is empty. The only extra path is the scratch dir `.tool-homes/`, which is untracked and ignored via `.git/info/exclude`. The tool calls show no edit to that exclude file. |
| 2 | pass | report.md defect 2: "`notes`: its `github` source type is not accepted by Codex … missing from Codex's list" (objective.json `codex.listed` has no `notes`). |
| 3 | pass | report.md defect 1: "`fmt`: its source `"plugins/fmt"` has no leading `./`, which breaks it in both tools" (objective.json `claude.errors` = `plugins.2.source`). |
| 4 | pass | report.md defect 3: "`lint`: the entry name `lint` does not match the manifest name `linter`". |
| 5 | pass | report.md defect 4: "`deploy`: the entry says version `2.0.0` but the plugin's `plugin.json` says `1.9.0`". |
| 6 | pass | report.md defect 5: "`remote-x`: the `url` source uses `ref: "main"` with no `sha`". |
| 7 | pass | report.md defect 6: guard's entry `"hooks": "./hooks/hooks.json"` gives "Hook load failed … file-path … forms are not yet supported in a marketplace entry", and `Hooks (0)`. |
| 8 | pass | report.md mentions `ok-tools` only as installing and loading successfully (verdict line and Load rows); no defect or suggestion names it. |

Total: 8 of 8 passed.

## Final report

## Audit of the acme-tools marketplace for Claude Code and Codex

**Verdict: it's not ready to announce.** Only 3 of the 7 entries (`ok-tools`, `deploy`, `guard`) install for users of both tools. Two of those three have their own defects (`deploy`: mismatched versions; `guard`: missing hook). I changed no tracked files, and `git status` is clean.

The repo is `$RUN/repo`, and the catalog is `.claude-plugin/marketplace.json` under it. The readers come from the README ("For Claude Code and Codex users"). No `.agents/plugins/marketplace.json` exists, so Codex reads the same Claude catalog.

### Defects

1. **`fmt`: its source `"plugins/fmt"` has no leading `./`, which breaks it in both tools (R3).**
   - Claude Code: `claude plugin validate --strict` reports `plugins.2.source: Invalid input`. The plugin is listed with source `unsupported`, and `claude plugin install fmt@acme-tools` fails with "marketplace entry is invalid: source: Invalid input".
   - Codex: the entry is left out of `codex plugin list --available` with no error.
2. **`notes`: its `github` source type is not accepted by Codex (R2).** Codex drops it silently, so it is missing from Codex's list. Claude Code lists it, and it is pinned to a `sha` correctly.
3. **`lint`: the entry name `lint` does not match the manifest name `linter` (R8).**
   - Codex: `codex plugin add lint@acme-tools` fails with "plugin.json name `linter` does not match marketplace plugin name `lint`".
   - Claude Code: it installs as `lint@acme-tools`, but `plugin details` shows it as `linter 1.0.0` with skill `linter`. Install and uninstall work only under one name and the skills appear under the other, and `install linter@acme-tools` fails with "not found in marketplace".
4. **`deploy`: the entry says version `2.0.0` but the plugin's `plugin.json` says `1.9.0` (R6).** Both tools install 1.9.0: Claude Code's `plugin list` shows `version 1.9.0`, and Codex's cache path is `deploy/1.9.0`. Claude Code's install list still advertises 2.0.0 to users. `claude plugin validate` only warns about this, so the plain run passes and only `--strict` fails.
5. **`remote-x`: the `url` source uses `ref: "main"` with no `sha` (R4).** Users get whatever is pushed to `main` next. No channel is declared anywhere to allow this. Both tools list it (Codex shows `version: null`).
6. **`guard`: the promised pre-tool hook is never delivered.**
   - The entry gives `"hooks": "./hooks/hooks.json"` as a path. Claude Code only supports inline hooks in a catalog entry, and `plugins/guard/hooks/` doesn't exist anyway.
   - Claude Code: install succeeds, but `plugin list --json` shows the error "Hook load failed: hooks: the file-path and array forms are not yet supported in a marketplace entry", and `plugin details guard` shows `Hooks (0)`.
   - Codex: it installs with only `skills/`; Codex uses entry keys only as a fallback manifest (source reading, not probed).
   - The description "Block risky shell commands with a pre-tool hook" is therefore false in both tools. A user who relies on it for safety gets no protection.
7. **No `marketplace-policy.json` (R1).** Without one, the validator assumed only Claude Code reads this catalog, so it didn't check Codex compatibility. The `notes`/Codex problem only appeared after I declared `["claude-code","codex"]` in a scratch policy file.
8. **Descriptions of the remote plugins can't be checked (R11).** I couldn't inspect the contents of `notes` or `remote-x` because fetching them was out of scope. So I can't confirm their descriptions disclose hooks, MCP servers or external services. `remote-x` ("Summarize open pull requests") very likely calls GitHub, and its description doesn't say so.

### Suggestions

- The `guard` entry description ("with a pre-tool hook") differs from its `plugin.json` description ("before the agent runs them"). Make them match once the hook exists.
- The `fmt` skill body says "python and typescript" in lowercase.
- The README should say how to add the marketplace in each tool, and whether Copilot CLI is supported. Copilot CLI would also read this catalog; with it added as a reader, the validator reported no new errors.

### Check levels (R12)

| Level | Status | Evidence |
| --- | --- | --- |
| Schema | failed | `check-marketplace`: `schema.parse` passed, `schema.claude-validate` failed. `claude plugin validate --strict --json`: 1 error (`fmt` source), 1 warning (`deploy` version). `schema.portable` skipped: there are no portable manifests. |
| Local | failed | `check-marketplace` with readers claude-code and codex: 7 errors (defects 1–6). |
| Remote | not run | `notes` sha `3add7b9…` and `remote-x` not fetched, because contacting remote services was out of scope. The validator skips this level. |
| Discovery, Claude Code | failed | `marketplace add` succeeded. All 7 entries are listed, but `fmt` shows as `unsupported`. |
| Discovery, Codex | failed | `marketplace add` succeeded. 5 of 7 are listed; `notes` and `fmt` were skipped silently. |
| Load, Claude Code | failed | `ok-tools`, `lint` (loads as `linter`) and `deploy` (1.9.0) installed, and `plugin details` shows one skill each. `guard` installed but its hook failed to load. `fmt` failed to install. `notes` and `remote-x` not installed (remote). |
| Load, Codex | failed | `ok-tools`, `deploy` (1.9.0) and `guard` (no hooks) installed. `lint` was refused. `notes` and `remote-x` not installed. |
| Copilot CLI | not run | Not a stated reader. |

### How the checks ran

- Installed versions are claude 2.1.284 and codex-cli 0.157.1, the same versions the skill's references were verified against. So I didn't need to re-check any of the references' facts against newer releases (R13).
- The tool checks ran against a clean `git archive` export in `.tool-homes/export`. Every tool used throwaway config under `.tool-homes/`, and outbound network was blocked with `sandbox-exec`. No prompt or model session was opened, no plugin code ran, and nothing was installed into your real config.
- One slip: my very first validator run didn't set `TMPDIR`. Its internal `claude plugin validate` call probably put its temporary config dir under the system temp directory rather than `.tool-homes/`. I set up isolation before every later run.

## Tool calls

The arm's tool calls, one JSON object per line, extracted from its transcript.

```jsonl
{"tool": "Bash", "input": {"command": "cd $RUN/repo && cat ../skill/plugin-marketplaces/SKILL.md && ls -R ../skill/plugin-marketplaces && git status && find . -path ./.git -prune -o -type f -print", "description": "Read skill and list repo files"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && for f in README.md .claude-plugin/marketplace.json plugins/*/.claude-plugin/plugin.json plugins/*/skills/*/SKILL.md; do echo \"=== $f\"; cat \"$f\"; done; git log --oneline | head", "description": "Print all repo files"}}
{"tool": "Bash", "input": {"command": "cd $RUN/skill/plugin-marketplaces/references && cat feature-matrix.md validation.md releases.md", "description": "Read key references"}}
{"tool": "Bash", "input": {"command": "cd $RUN/skill/plugin-marketplaces/references && cat codex.md claude-code.md multi-tool.md freshness.md", "description": "Read tool references"}}
{"tool": "Bash", "input": {"command": "cd $RUN && ./validator/bin/check-marketplace repo; echo \"exit=$?\"; ./validator/bin/check-marketplace repo --format json; echo \"exit=$?\"", "description": "Run marketplace validator"}}
{"tool": "Bash", "input": {"command": "cd $RUN && sed -n 1,200p skill/plugin-marketplaces/scripts/mpcheck/policy.py; cat skill/plugin-marketplaces/scripts/mpcheck/data/readers.json | head -80; which claude codex copilot git", "description": "Read policy format and check installed tools"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && ../validator/bin/check-marketplace --help 2>&1 | head -30", "description": "Show validator options"}}
{"tool": "Bash", "input": {"command": "R=$RUN/repo; T=\"$R/.tool-homes\"; mkdir -p \"$T\"/{home,xdg,tmp,claude,codex,copilot,copilot-cache,export} && : > \"$T/gitconfig\" && echo '{\"readers\":[\"claude-code\",\"codex\"]}' > \"$T/policy-cc-codex.json\" && echo '{\"readers\":[\"claude-code\",\"codex\",\"copilot-cli\"]}' > \"$T/policy-all.json\" && git -C \"$R\" archive HEAD | tar -x -C \"$T/export\" && export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\" && V=$R/../validator/bin/check-marketplace; echo \"--- cc+codex\"; sandbox-exec -p '(version 1)(allow default)(deny network-outbound (remote ip))' $V \"$T/export\" --policy \"$T/policy-cc-codex.json\" </dev/null; echo \"exit=$?\"; echo \"--- all three\"; $V \"$T/export\" --policy \"$T/policy-all.json\" --no-claude </dev/null; echo \"exit=$?\"", "description": "Rerun validator isolated with declared readers on export"}}
{"tool": "Bash", "input": {"command": "R=$RUN/repo; T=\"$R/.tool-homes\"; export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\"; SB='(version 1)(allow default)(deny network-outbound (remote ip))'; sandbox-exec -p \"$SB\" claude --version </dev/null; sandbox-exec -p \"$SB\" codex --version </dev/null; echo \"--- claude validate\"; sandbox-exec -p \"$SB\" claude plugin validate \"$T/export\" --strict --json </dev/null; echo \"exit=$?\"; echo \"--- claude add\"; sandbox-exec -p \"$SB\" claude plugin marketplace add \"$T/export\" </dev/null 2>&1; echo \"exit=$?\"", "description": "Isolated tool versions and Claude discovery checks", "timeout": 180000}}
{"tool": "Bash", "input": {"command": "R=$RUN/repo; T=\"$R/.tool-homes\"; export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\"; SB='(version 1)(allow default)(deny network-outbound (remote ip))'; c(){ echo \"--- claude $*\"; sandbox-exec -p \"$SB\" claude \"$@\" </dev/null 2>&1; echo \"exit=$?\"; }; c plugin list --available --json; for p in ok-tools fmt lint linter deploy guard; do c plugin install \"$p@acme-tools\"; done; c plugin list --json", "description": "Isolated Claude listing and installs of local plugins", "timeout": 300000}}
{"tool": "Bash", "input": {"command": "R=$RUN/repo; T=\"$R/.tool-homes\"; export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\"; SB='(version 1)(allow default)(deny network-outbound (remote ip))'; for p in lint guard deploy ok-tools; do echo \"--- details $p\"; sandbox-exec -p \"$SB\" claude plugin details \"$p@acme-tools\" </dev/null 2>&1; done; echo \"--- codex add\"; sandbox-exec -p \"$SB\" codex plugin marketplace add \"$T/export\" </dev/null 2>&1; echo \"exit=$?\"; echo \"--- codex list\"; sandbox-exec -p \"$SB\" codex plugin list --available --json </dev/null 2>&1; echo \"exit=$?\"", "description": "Claude plugin details and Codex discovery, isolated", "timeout": 300000}}
{"tool": "Bash", "input": {"command": "R=$RUN/repo; T=\"$R/.tool-homes\"; export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\"; SB='(version 1)(allow default)(deny network-outbound (remote ip))'; for p in ok-tools lint deploy guard; do echo \"--- codex add $p\"; sandbox-exec -p \"$SB\" codex plugin add \"$p@acme-tools\" --json </dev/null 2>&1; echo \"exit=$?\"; done; ls -R \"$T/codex/plugins/cache\" 2>/dev/null | head -40", "description": "Isolated Codex installs of local plugins", "timeout": 300000}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && git status --short && ls plugins/guard", "description": "Confirm tracked files unchanged"}}
```

## Objective checks

```json
{
  "claude": {
    "ran": true,
    "exit": 1,
    "success": false,
    "errors": [
      "plugins.2.source"
    ],
    "warnings": [
      "plugins[4].version"
    ]
  },
  "codex": {
    "ran": true,
    "added": true,
    "marketplace": "acme-tools",
    "listed": [
      "deploy",
      "guard",
      "lint",
      "ok-tools",
      "remote-x"
    ]
  },
  "copilot": {
    "ran": true,
    "added": true,
    "marketplace": "acme-tools",
    "listed": [
      "deploy",
      "fmt",
      "guard",
      "lint",
      "notes",
      "ok-tools",
      "remote-x"
    ]
  }
}
```

## Diff

```diff

```

## Repository refs

Every branch and tag in the final repository, each with its changes against the fixture tree (`refs.txt`).

```text
master 5cb4b7d
```
