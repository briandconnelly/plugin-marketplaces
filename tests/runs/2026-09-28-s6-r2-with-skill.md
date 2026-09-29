# Run: scenario 6, repetition 2, with-skill

Scored against `tests/scenarios.md` as of this commit; cost is `metrics` in the manifest.

## Manifest

```json
{
  "date": "2026-09-28",
  "arm": "with-skill",
  "scenario": "s6",
  "rep": 2,
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
  "transcript": "ad73de089a0121517.output",
  "model": "claude-opus-5-5",
  "metrics": {
    "tool_calls": 13,
    "wall_seconds": 115.3
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
(none)
```

Batch 2. Every tool call read; no violation (plan-2c ledger).

## Score

| Criterion | Result | Evidence |
| --- | --- | --- |
| 1 | pass | `artefacts/diff.patch` is 0 bytes, `refs.txt` lists only `master 5cb4b7d` with no changes, and `diff -r` of the final repo against the fixture (excluding `.git` and the git-ignored scratch dir `.tool-homes/`) found no differences. |
| 2 | pass | `report.md` defect 5: "`notes`: missing for Codex users. Its `github` source type is not one Codex accepts", and `objective.json` `codex.listed` has no `notes`. |
| 3 | pass | `report.md` defect 1: "`fmt`: will not install anywhere. Its source `"plugins/fmt"` has no leading `./`". |
| 4 | pass | `report.md` defect 2: "`lint`: the entry name is `lint` but its manifest says `linter`". |
| 5 | pass | `report.md` defect 3: "The entry says `2.0.0` and `plugins/deploy/.claude-plugin/plugin.json` says `1.9.0`". |
| 6 | pass | `report.md` defect 6: "`remote-x`: not pinned. It tracks `"ref": "main"` with no `sha`". |
| 7 | pass | `report.md` defect 4: "`guard`: its hook never runs", because the entry-level `"hooks": "./hooks/hooks.json"` fails to load (Hooks (0)). |
| 8 | pass | `report.md` raises no finding about `ok-tools` and closes with "Only `ok-tools` passes everywhere it was checked." |

Total: 8 of 8 passed.

## Final report

## acme-tools marketplace audit: not ready to announce

I changed no files; `git status` is clean. All scratch work, including a clean `git archive` export and throwaway Claude Code and Codex config, is under `$RUN/repo/.tool-homes/`. I ran both CLIs with outbound network blocked.

The catalog is `$RUN/repo/.claude-plugin/marketplace.json`, and it is the only catalog in the repo. Codex reads it as a fallback. Of its 7 entries, **Claude Code users can install 4 and Codex users 3.** Of the 4 installed in Claude Code, `guard`'s hook fails to load and `deploy` installs a different version than its entry states.

### Defects

1. **`fmt`: will not install anywhere.** Its source `"plugins/fmt"` has no leading `./` (R3).
   - Claude Code: `claude plugin validate --strict` reports `plugins.2.source: Invalid input`, and install fails with `This plugin's marketplace entry is invalid`.
   - Codex: the entry is missing from `codex plugin list --available` and no error is shown.
2. **`lint`: the entry name is `lint` but its manifest says `linter`** (`plugins/lint/.claude-plugin/plugin.json`) (R8).
   - Codex refuses to install it: ``plugin.json name `linter` does not match marketplace plugin name `lint` ``.
   - Claude Code installs it as `lint@acme-tools`, but the plugin and its skill are named `linter`, so users see a different name from the one in the catalog.
3. **`deploy`: two different versions.** The entry says `2.0.0` and `plugins/deploy/.claude-plugin/plugin.json` says `1.9.0` (R6).
   - Claude Code and Codex both install `1.9.0`, so the `2.0.0` in the catalog listing is ignored.
   - `claude plugin validate` only warns about this, so a plain run without `--strict` passes.
4. **`guard`: its hook never runs.** The description says it blocks risky shell commands with a pre-tool hook. The entry gives `"hooks": "./hooks/hooks.json"` as a path, and `plugins/guard/hooks/` does not exist.
   - Claude Code installs it, then reports `Hook load failed: hooks: the file-path and array forms are not yet supported in a marketplace entry`. `claude plugin details` shows Hooks (0).
   - Codex installs it with only the skill; its cache holds no hooks.
   - Users are told they are protected when they are not. `claude plugin validate` does not catch this.
5. **`notes`: missing for Codex users.** Its `github` source type is not one Codex accepts (R2), so Codex drops the entry without a message; it is absent from `codex plugin list --available`. Claude Code lists it. It is correctly pinned to a full `sha`.
6. **`remote-x`: not pinned.** It tracks `"ref": "main"` with no `sha` (R4), so every push to `acme/remote-x` main reaches users unreviewed. There is no `marketplace-policy.json` declaring it as a channel. Both tools list it.
7. **No `marketplace-policy.json`** (R1, validator `policy.inferred`). The README targets Claude Code and Codex, but without a policy the validator checks against Claude Code only, so defect 5 is invisible to it. I confirmed this by adding a policy declaring both readers to a throwaway copy: the validator then reported `local.source-type` for `notes`.
8. **Copilot CLI also reads this catalog** (the validator says it would read a catalog here). Copilot CLI rejects an entire catalog over one entry it cannot read, and I did not check whether any entry here would trigger that. Either declare Copilot CLI and test it, or state that it is not supported.

### Suggestions

- Consider shipping a native `.agents/plugins/marketplace.json` for Codex, which would also let `notes` use a `url` source there. That needs its differences from the Claude catalog recorded in the policy file (R10).
- Descriptions for `notes` and `remote-x` can't be checked for executable-component or external-service disclosure (R11), because their contents weren't fetched. `remote-x` ("Summarize open pull requests") presumably calls GitHub; if so, say that in its description.
- The `lint`/`linter` naming needs a decision whichever way it is fixed. Once published, renaming needs Claude Code's `renames` map, and Codex has no rename mechanism (R9).
- `fmt/skills/fmt/SKILL.md` writes "python and typescript" in lowercase, while its description capitalises them.

### Checks run (R12)

| Level | Tool | Status | Evidence |
| --- | --- | --- | --- |
| Schema | validator + `claude plugin validate --strict` (claude 2.1.284) | failed | `plugins.2.source` error; `deploy` version warning |
| Local | validator | failed | 5 errors: R3 `fmt`, R8 `lint`, R6 `deploy`, R4 `remote-x`, entry hooks path on `guard`; plus R2 `notes` once Codex is declared |
| Remote | — | not run | I was not permitted to contact remotes. Whether `acme/notes@3add7b9…` and `acme/remote-x` exist, and what they contain, is unverified. |
| Discovery | Claude Code | run | `marketplace add` succeeded; all 7 entries listed, `fmt` as `unsupported` |
| Discovery | Codex (0.157.1) | failed | 5 of 7 listed; `notes` and `fmt` dropped with no error |
| Discovery | Copilot CLI | not run | not a stated target; its sign-in can't be isolated |
| Package load | Claude Code | partial | `ok-tools`, `lint` (as `linter`), `deploy` (1.9.0) and `guard` installed, `guard` with a hook-load error; `fmt` failed; `notes` and `remote-x` not attempted (remote) |
| Package load | Codex | partial | `ok-tools`, `deploy` (1.9.0) and `guard` (skill only) installed; `lint` refused; `notes`, `fmt` and `remote-x` not attempted |
| Package load | Copilot CLI | not run | |

Only `ok-tools` passes everywhere it was checked.

## Tool calls

The arm's tool calls, one JSON object per line, extracted from its transcript.

```jsonl
{"tool": "Bash", "input": {"command": "cd $RUN/repo && cat ../skill/plugin-marketplaces/SKILL.md && ls -R ../skill/plugin-marketplaces && git status && find . -path ./.git -prune -o -type f -print", "description": "Read skill and list repo files"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && for f in README.md .claude-plugin/marketplace.json plugins/*/.claude-plugin/plugin.json plugins/*/skills/*/SKILL.md; do echo \"=== $f\"; cat \"$f\"; done; git log --oneline | head", "description": "Show all marketplace files"}}
{"tool": "Bash", "input": {"command": "cd $RUN/skill/plugin-marketplaces/references && cat validation.md feature-matrix.md releases.md", "description": "Read validation, feature matrix, releases references"}}
{"tool": "Bash", "input": {"command": "cd $RUN/skill/plugin-marketplaces/references && cat claude-code.md codex.md", "description": "Read Claude Code and Codex references"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=\"$PWD/.tool-homes\" && mkdir -p \"$T\"/{home,xdg,tmp,claude,codex,copilot,copilot-cache,export} && : > \"$T/gitconfig\" && export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\" && which claude codex copilot; git archive HEAD | tar -x -C \"$T/export\" && ../validator/bin/check-marketplace \"$T/export\" < /dev/null; echo \"exit=$?\"; ../validator/bin/check-marketplace \"$T/export\" --format json < /dev/null > \"$T/v.json\"; echo \"exit=$?\"; python3 -m json.tool \"$T/v.json\" | head -150", "description": "Run validator on clean export with throwaway homes"}}
{"tool": "Bash", "input": {"command": "cd $RUN/skill/plugin-marketplaces/scripts/mpcheck && sed -n 1,200p policy.py; cat data/readers.json | head -60", "description": "Read validator policy format"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=\"$PWD/.tool-homes\" && export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\" && rm -rf \"$T/export-policy\" && mkdir -p \"$T/export-policy\" && git archive HEAD | tar -x -C \"$T/export-policy\" && echo '{\"readers\":[\"claude-code\",\"codex\"]}' > \"$T/export-policy/marketplace-policy.json\" && ../validator/bin/check-marketplace \"$T/export-policy\" < /dev/null; echo \"exit=$?\"", "description": "Re-run validator with hypothetical Claude+Codex policy"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=\"$PWD/.tool-homes\" && export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\" && SB=(sandbox-exec -p '(version 1)(allow default)(deny network-outbound (remote ip))') && \"${SB[@]}\" claude --version </dev/null; \"${SB[@]}\" codex --version </dev/null; echo \"--- claude validate\"; \"${SB[@]}\" claude plugin validate \"$T/export\" --strict --json </dev/null; echo \"exit=$?\"; echo \"--- claude add\"; \"${SB[@]}\" claude plugin marketplace add \"$T/export\" </dev/null; echo \"exit=$?\"; \"${SB[@]}\" claude plugin marketplace list </dev/null", "description": "Claude Code validate and marketplace add, isolated"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=\"$PWD/.tool-homes\" && export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\" && SB=(sandbox-exec -p '(version 1)(allow default)(deny network-outbound (remote ip))') && \"${SB[@]}\" claude plugin list --available --json </dev/null 2>&1 | head -80; for p in ok-tools fmt lint deploy guard; do echo \"--- install $p\"; \"${SB[@]}\" claude plugin install \"$p@acme-tools\" </dev/null 2>&1; echo \"exit=$?\"; done", "description": "List available and install local plugins in throwaway Claude config"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=\"$PWD/.tool-homes\" && export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\" && SB=(sandbox-exec -p '(version 1)(allow default)(deny network-outbound (remote ip))') && \"${SB[@]}\" claude plugin list --json </dev/null 2>&1; for p in ok-tools lint deploy guard; do echo \"--- details $p\"; \"${SB[@]}\" claude plugin details \"$p@acme-tools\" </dev/null 2>&1; done", "description": "Show installed versions and component details"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=\"$PWD/.tool-homes\" && export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\" && SB=(sandbox-exec -p '(version 1)(allow default)(deny network-outbound (remote ip))') && \"${SB[@]}\" codex plugin marketplace add \"$T/export\" </dev/null 2>&1; echo \"exit=$?\"; \"${SB[@]}\" codex plugin list --available --json </dev/null 2>&1 | python3 -c 'import json,sys; d=json.load(sys.stdin); print(json.dumps(d,indent=1)[:3000])'", "description": "Codex marketplace add and list available, isolated"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=\"$PWD/.tool-homes\" && export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\" && SB=(sandbox-exec -p '(version 1)(allow default)(deny network-outbound (remote ip))') && for p in ok-tools lint deploy guard; do echo \"--- add $p\"; \"${SB[@]}\" codex plugin add \"$p@acme-tools\" --json </dev/null 2>&1 | head -20; echo \"exit=${PIPESTATUS[0]}\"; done; ls -R \"$T/codex/plugins/cache\" 2>/dev/null | head -40", "description": "Install local plugins in throwaway Codex home"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && git status --short && git diff --stat HEAD; ls plugins/guard", "description": "Confirm repo unchanged"}}
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
