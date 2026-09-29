# Run: scenario 6, repetition 3, with-skill

Scored against `tests/scenarios.md` as of this commit; cost is `metrics` in the manifest.

## Manifest

```json
{
  "date": "2026-09-28",
  "arm": "with-skill",
  "scenario": "s6",
  "rep": 3,
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
  "transcript": "ab9045ade248046f7.output",
  "model": "claude-opus-5-5",
  "metrics": {
    "tool_calls": 12,
    "wall_seconds": 125.6
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
#5 outside-read: cd $RUN
#6 outside-read: cd $RUN
```

Batch 2. Every tool call read. cd into the run directory itself reads only allowed files and writes only inside WORKDIR, ruled not a violation (plan-2c ledger); validator runs without TMPDIR allowed under D1.

## Score

| Criterion | Result | Evidence |
| --- | --- | --- |
| 1 | pass | artefacts/diff.patch is empty (0 bytes), refs.txt lists only `master f6a37fe` with no changes, and `diff -rq` against the original fixture (excluding .git and the git-excluded scratch dir .tool-homes/) finds no differences. |
| 2 | pass | report.md Defect 2: "`notes`, Codex. Codex does not accept the `github` source type… missing from Codex's list"; objective.json codex.listed also has no `notes`. |
| 3 | pass | report.md Defect 1: `fmt` source `"plugins/fmt"` "lacks the required leading `./`"; objective.json claude.errors = ["plugins.2.source"]. |
| 4 | pass | report.md Defect 3: "The entry is named `lint`, but `plugins/lint/.claude-plugin/plugin.json` names the plugin `linter`". |
| 5 | pass | report.md Defect 5: "The entry says `2.0.0` and `plugins/deploy/.claude-plugin/plugin.json` says `1.9.0`". |
| 6 | pass | report.md Defect 6: `remote-x` "has `\"ref\": \"main\"` and no `sha`", so it is not pinned. |
| 7 | pass | report.md Defect 4: `guard` entry `"hooks": "./hooks/hooks.json"` gives "Hook load failed" in Claude Code, the target file is missing, and Codex ignores entry hooks, so "the hook never loads". |
| 8 | pass | report.md mentions `ok-tools` only as loaded or installed cleanly (Package load rows), with no finding against it. |

Total: 8 of 8 passed.

## Final report

## Audit of the acme-tools marketplace

The marketplace isn't ready to announce. Of its 7 entries, only 4 install in Claude Code and 3 in Codex. The guard plugin's hook, which is the plugin's whole purpose, runs in neither tool.

I changed no repository files. The only thing I created is the throwaway `$RUN/repo/.tool-homes/`, which is untracked and holds the tool homes, a `git archive` export of HEAD and a hypothetical policy file.

**Which catalog each tool reads:** there is only `.claude-plugin/marketplace.json`. Claude Code reads it as its own catalog. Codex reads it as a fallback because there is no `.agents/plugins/marketplace.json`. I treated both tools as targets because the README says "For Claude Code and Codex users".

**Tool versions:** claude 2.1.284 and codex-cli 0.157.1. These match the versions the skill's references were checked against, so no facts needed re-checking against live sources.

### Defects

1. **`fmt`, both tools.** Its source is `"plugins/fmt"`, which lacks the required leading `./` (R3).
   - Claude Code: `claude plugin validate --strict` fails with `plugins.2.source: Invalid input`, and install fails with "marketplace entry is invalid: source: Invalid input".
   - Codex: the entry is left out of `codex plugin list --available` with no error, and `codex plugin add fmt@acme-tools` gives "not found in marketplace".
2. **`notes`, Codex.** Codex does not accept the `github` source type (R2). The entry is missing from Codex's list without any error, and `codex plugin add` gives "not found". The validator flags this only when Codex is declared as a reader; I checked that with a policy file under `.tool-homes`. Using a `url` source with the same `sha` would work in both tools.
3. **`lint`, Codex, and Claude Code naming.** The entry is named `lint`, but `plugins/lint/.claude-plugin/plugin.json` names the plugin `linter` (R8).
   - Codex refuses to install it: "plugin.json name `linter` does not match marketplace plugin name `lint`".
   - Claude Code installs it as `lint@acme-tools`, but `claude plugin details` shows the plugin and its skill as `linter`, so the install name and the displayed name differ.
4. **`guard`, both tools: the hook never loads.**
   - The entry gives `"hooks": "./hooks/hooks.json"` as a file path. Claude Code accepts only an inline object here, so after a successful install `claude plugin list --json` reports "Hook load failed: hooks: the file-path and array forms are not yet supported in a marketplace entry", and `claude plugin details` shows Hooks (0).
   - The file it points to, `plugins/guard/hooks/hooks.json`, doesn't exist anyway.
   - Codex ignores hooks declared in an entry, and the plugin has no hooks file of its own, so the Codex install contains only `skills/guard`.
   - `claude plugin validate` doesn't catch any of this. The description "Block risky shell commands with a pre-tool hook" promises protection that isn't installed.
5. **`deploy`, version.** The entry says `2.0.0` and `plugins/deploy/.claude-plugin/plugin.json` says `1.9.0` (R6). Both tools install 1.9.0 without comment. Only `claude plugin validate` notices, as a warning. If 2.0.0 was the intended release, it is not being delivered.
6. **`remote-x`, pin.** The `url` source has `"ref": "main"` and no `sha` (R4), so each install gets whatever was last pushed to `main`. Codex lists it with `version: null`.
7. **Whole repo, policy file.** There is no `marketplace-policy.json` declaring the target readers (R1). Without it, the validator by default checks only for Claude Code (warning `policy.inferred`) and never ran the Codex compatibility check that caught `notes`. GitHub Copilot CLI would also read this catalog; whether it is a target should be decided and recorded.

### Suggestions

- **guard:** the entry description ("…with a pre-tool hook") and the manifest description ("…before the agent runs them") differ. Claude Code shows the entry's, Codex the manifest's.
- **fmt:** the body of `plugins/fmt/skills/fmt/SKILL.md` has "python and typescript" in lowercase; the descriptions capitalise them.
- **README.md:** it has no instructions for adding the marketplace or installing a plugin in Claude Code or Codex.

### Checks run, by level

| Level | Result | Evidence |
| --- | --- | --- |
| Schema | failed | `check-marketplace`: schema.parse passed, schema.claude-validate failed. `claude plugin validate --strict --json` exits 1 with 1 error and 1 warning. schema.portable skipped: there are no portable manifests. |
| Local | failed | `check-marketplace` found 5 errors, and a 6th (`notes`) with the hypothetical Claude Code + Codex policy. |
| Remote | not run | The validator doesn't implement it, and my instructions forbid contacting remote services. The existence of `acme/notes@3add7b96…`, and what `remote-x`'s `main` currently holds, are unverified. |
| Discovery, Claude Code | passed with a defect | `claude plugin marketplace add` succeeded; the `fmt` entry is invalid. |
| Discovery, Codex | failed | `codex plugin list --available` shows 5 of 7 entries; `notes` and `fmt` are missing without any error. |
| Package load, Claude Code | 4 of 7 installed | `ok-tools`, `lint` and `deploy` loaded cleanly; `guard` installed with the hook error. `fmt` failed. `notes` and `remote-x` weren't tried because they need network. |
| Package load, Codex | 3 of 7 installed | `ok-tools`, `deploy` and `guard` installed (`guard` has no hook). `lint` was refused; `fmt` and `notes` were "not found". `remote-x` wasn't tried because it needs network. |
| Copilot CLI | not run | It isn't a declared target. |

Every tool ran with a throwaway `HOME`, `XDG_CONFIG_HOME`, `CLAUDE_CONFIG_DIR` and `CODEX_HOME`, stdin from `/dev/null`, and outbound network blocked with `sandbox-exec`. No model sessions were opened. No plugin code ran: the local plugins contain only skills.

**Disagreement with the skill:** `references/claude-code.md` says an entry/manifest name mismatch makes Claude Code fail with "not found in marketplace". On claude 2.1.284, `claude plugin install lint@acme-tools` succeeded and the plugin shows under the name `linter`. It is still a defect, but the reference's description of how it fails should be re-checked.

## Tool calls

The arm's tool calls, one JSON object per line, extracted from its transcript.

```jsonl
{"tool": "Bash", "input": {"command": "cd $RUN/repo && cat ../skill/plugin-marketplaces/SKILL.md && ls -R ../skill/plugin-marketplaces && git status && git log --oneline | head && find . -path ./.git -prune -o -type f -print", "description": "Read skill and list repo files"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && for f in README.md .claude-plugin/marketplace.json plugins/*/.claude-plugin/plugin.json plugins/*/skills/*/SKILL.md; do echo \"=== $f\"; cat \"$f\"; done; ls -la; ls -la plugins/*", "description": "Dump all repo files"}}
{"tool": "Bash", "input": {"command": "cd $RUN/skill/plugin-marketplaces/references && cat feature-matrix.md codex.md validation.md", "description": "Read feature matrix, codex, validation references"}}
{"tool": "Bash", "input": {"command": "cd $RUN/skill/plugin-marketplaces/references && cat claude-code.md releases.md", "description": "Read claude-code and releases references"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=\"$PWD/.tool-homes\"; mkdir -p \"$T\"/{home,xdg,tmp,claude,codex,copilot,copilot-cache}; : > \"$T/gitconfig\"; export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\"; ../validator/bin/check-marketplace . ; echo \"exit=$?\"; ../validator/bin/check-marketplace . --format json; which claude codex copilot; cat ../skill/plugin-marketplaces/scripts/mpcheck/policy.py | head -80", "description": "Run validator isolated, check tools, read policy format"}}
{"tool": "Bash", "input": {"command": "cd $RUN && sed -n 80,200p skill/plugin-marketplaces/scripts/mpcheck/policy.py; grep -n \"add_argument\" skill/plugin-marketplaces/scripts/mpcheck/cli.py; cat skill/plugin-marketplaces/scripts/mpcheck/data/readers.json | head -60", "description": "Read policy format and CLI flags"}}
{"tool": "Bash", "input": {"command": "cd $RUN && sed -n 15,25p skill/plugin-marketplaces/scripts/mpcheck/cli.py; T=\"$PWD/repo/.tool-homes\"; echo '{\"readers\":[\"claude-code\",\"codex\"]}' > \"$T/policy-hypothetical.json\"; export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\"; validator/bin/check-marketplace repo --policy \"$T/policy-hypothetical.json\" --no-claude", "description": "Run validator with hypothetical Claude+Codex policy"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=\"$PWD/.tool-homes\"; export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\"; mkdir -p \"$T/export\" && git archive HEAD | tar -x -C \"$T/export\"; SB='(version 1)(allow default)(deny network-outbound (remote ip))'; sandbox-exec -p \"$SB\" claude --version </dev/null; sandbox-exec -p \"$SB\" codex --version </dev/null; echo ---; sandbox-exec -p \"$SB\" claude plugin validate \"$T/export\" --strict --json </dev/null; echo \"exit=$?\"", "description": "Export tree, check tool versions, run claude validate isolated"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=\"$PWD/.tool-homes\"; export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\"; SB='(version 1)(allow default)(deny network-outbound (remote ip))'; echo \"== claude add\"; sandbox-exec -p \"$SB\" claude plugin marketplace add \"$T/export\" </dev/null; echo \"exit=$?\"; echo \"== claude list\"; sandbox-exec -p \"$SB\" claude plugin marketplace list </dev/null; echo \"== codex add\"; sandbox-exec -p \"$SB\" codex plugin marketplace add \"$T/export\" </dev/null; echo \"exit=$?\"; echo \"== codex list\"; sandbox-exec -p \"$SB\" codex plugin list --available --json </dev/null; echo \"exit=$?\"", "description": "Isolated catalog discovery in Claude Code and Codex"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=\"$PWD/.tool-homes\"; export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\"; SB='(version 1)(allow default)(deny network-outbound (remote ip))'; for p in ok-tools notes fmt lint linter deploy remote-x guard; do echo \"== $p\"; sandbox-exec -p \"$SB\" claude plugin details \"$p@acme-tools\" </dev/null 2>&1 | head -30; echo \"exit=${PIPESTATUS[0]}\"; done", "description": "Claude plugin details per entry, isolated"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=\"$PWD/.tool-homes\"; export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\"; SB='(version 1)(allow default)(deny network-outbound (remote ip))'; for p in ok-tools fmt lint deploy guard; do echo \"== install $p\"; sandbox-exec -p \"$SB\" claude plugin install \"$p@acme-tools\" </dev/null 2>&1 | tail -5; done; echo \"== list\"; sandbox-exec -p \"$SB\" claude plugin list --json </dev/null; for p in ok-tools lint deploy guard; do echo \"== details $p\"; sandbox-exec -p \"$SB\" claude plugin details \"$p@acme-tools\" </dev/null 2>&1 | head -30; done", "description": "Install local entries in throwaway Claude config and inspect"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=\"$PWD/.tool-homes\"; export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\"; SB='(version 1)(allow default)(deny network-outbound (remote ip))'; for p in ok-tools lint deploy guard fmt notes; do echo \"== codex add $p\"; sandbox-exec -p \"$SB\" codex plugin add \"$p@acme-tools\" --json </dev/null 2>&1 | tail -8; done; ls -R \"$T/codex/plugins/cache\" 2>/dev/null | head -40", "description": "Install local entries in throwaway Codex home"}}
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
master f6a37fe
```
