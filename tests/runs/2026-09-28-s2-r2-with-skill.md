# Run: scenario 2, repetition 2, with-skill

Scored against `tests/scenarios.md` as of this commit; cost is `metrics` in the manifest.

## Manifest

```json
{
  "date": "2026-09-28",
  "arm": "with-skill",
  "scenario": "s2",
  "rep": 2,
  "fixture_tree": "8640972fd67d9623c6fb9326a72c38420402842e",
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
  "transcript": "aa5e651b07ba8dcb8.output",
  "model": "claude-opus-5-5",
  "metrics": {
    "tool_calls": 9,
    "wall_seconds": 91.5
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

Add the new `lint-kit` plugin (in `plugins/lint-kit`) to our marketplace.
```

## Isolation

Flags raised by `tests/eval/isolation.py` (tests/scenarios.md, How to run, step 5):

```text
(none)
```

Batch 1. Every tool call read; no violation. Secret-scan hits are 'token cost' text from claude plugin details.

## Score

| Criterion | Result | Evidence |
|---|---|---|
| 1 | pass | objective.json shows `claude.errors: []` (exit 0). The final `.claude-plugin/marketplace.json` lists alpha-notes, branch-tidy, claude-hooks and lint-kit. |
| 2 | pass | objective.json `codex.listed` = alpha-notes, branch-tidy, codex-helper, lint-kit. |
| 3 | pass | objective.json `codex.listed` has no claude-hooks. The final `.claude-plugin/marketplace.json` has no codex-helper. |
| 4 | pass | Both `plugins/lint-kit/plugin.json` and `.claude-plugin/plugin.json` now read 1.1.0 (diff changes the adapter from 1.0.0). report.md says "two manifests disagreed … 1.1.0 … 1.0.0 … I kept 1.1.0". |
| 5 | pass | report.md has a Checks table that marks each check passed or not run (Copilot discovery and load were not run; Remote n/a; Codex skill loading not checked). |

Total: 5 of 5 passed.

## Final report

I added `lint-kit` to both catalogs in the repo. The validator, Claude Code and Codex all pass, and both tools install it at version 1.1.0. Nothing is committed.

**The version choice needs your confirmation.** lint-kit's two manifests disagreed: the portable `plugins/lint-kit/plugin.json` said 1.1.0, and the Claude adapter `plugins/lint-kit/.claude-plugin/plugin.json` said 1.0.0. As they were, Codex users would have got 1.1.0 and Claude Code users 1.0.0, with no warning from either tool. I kept 1.1.0 and changed the adapter to match. The repo has no changelog or history that says which value is right. I picked the higher one because a bump that missed one file seemed the likelier mistake. The plugin wasn't in any catalog yet, so no user has an installed copy either way. If 1.0.0 is correct, change the root `plugin.json` instead.

**Changes:**
- **Claude Code catalog** (`$RUN/repo/.claude-plugin/marketplace.json`): added a `lint-kit` entry pointing at `./plugins/lint-kit`, with the description "Run the team's linters". The plugin has only a skill (no hooks, servers or `bin/`), so there is nothing to disclose in the description.
- **Codex catalog** (`$RUN/repo/.agents/plugins/marketplace.json`): added a `lint-kit` entry with a local source, set up like the other entries (policy AVAILABLE / ON_INSTALL, category "Developer Tools").
- **Claude adapter** (`$RUN/repo/plugins/lint-kit/.claude-plugin/plugin.json`): version changed from 1.0.0 to 1.1.0.
- **New `marketplace-policy.json`** (`$RUN/repo/marketplace-policy.json`): this goes a little beyond the request. Without it the validator failed on two catalog differences that were already there, not on lint-kit. The file lists Claude Code and Codex as the tools this marketplace targets. It also records the two existing differences (`claude-hooks` is Claude-only, `codex-helper` is Codex-only), with the reasons copied from `README.md`. Please confirm that list of tools. Copilot CLI would also read `.claude-plugin/marketplace.json`; if you want it covered, add `copilot-cli` to the file and re-run the checks.

**Checks:**
```text
Schema     passed   check-marketplace: parse, policy, claude-validate and portable-manifest checks all passed, no findings (exit 0); claude plugin validate --strict --json: 0 errors, 0 warnings
Local      passed   check-marketplace: local passed; before the policy file it failed only on the two existing differences
Remote     n/a      no remote sources (all local paths); the validator reports this level as skipped
Discovery  Claude   passed: marketplace add succeeded
Discovery  Codex    passed: plugin list --available shows all 4 expected entries, lint-kit at 1.1.0
Discovery  Copilot  not run: Copilot CLI is not a declared target
Load       Claude   passed: installs; details shows 1.1.0 with 1 skill (lint-kit) and no agents, hooks, MCP or LSP servers
Load       Codex    install passed at 1.1.0; skill loading not checked (no command shows it without starting the plugin)
Load       Copilot  not run: Copilot CLI is not a declared target
```
All tool checks ran against a clean copy of the repo, with throwaway settings directories under `.tool-homes/` and outbound network blocked (`sandbox-exec`). The installed tool versions (claude 2.1.284, codex-cli 0.157.1, copilot 1.0.89) are the ones the skill's references were checked against.

`.tool-homes/` is untracked scratch space from these checks; keep it out of any commit.

## Tool calls

The arm's tool calls, one JSON object per line, extracted from its transcript.

```jsonl
{"tool": "Bash", "input": {"command": "cd $RUN/repo && cat ../skill/plugin-marketplaces/SKILL.md && ls -R ../skill/plugin-marketplaces && git status && find . -path ./.git -prune -o -type f -print | head -50", "description": "Read skill and survey repo"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && for f in README.md .claude-plugin/marketplace.json .agents/plugins/marketplace.json plugins/lint-kit/plugin.json plugins/lint-kit/.claude-plugin/plugin.json plugins/lint-kit/skills/lint-kit/SKILL.md plugins/*/.c*-plugin/plugin.json; do echo \"== $f\"; cat \"$f\"; done; ls -la plugins/lint-kit; git log --oneline | head", "description": "Show catalogs and lint-kit manifests"}}
{"tool": "Bash", "input": {"command": "cd $RUN/skill/plugin-marketplaces/references && cat releases.md validation.md", "description": "Read releases and validation references"}}
{"tool": "Bash", "input": {"command": "cd $RUN/skill/plugin-marketplaces && cat scripts/mpcheck/policy.py; grep -n -i -A3 \"policy\" references/*.md | head -80", "description": "Read policy format"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=\"$PWD/.tool-homes\"; mkdir -p \"$T\"/{home,xdg,tmp,claude,codex,copilot,copilot-cache}; : > \"$T/gitconfig\"; export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\"; ../validator/bin/check-marketplace . < /dev/null; echo \"exit $?\"; python3 -c \"import json;print(list(json.load(open('../skill/plugin-marketplaces/scripts/mpcheck/data/readers.json')).keys()) if isinstance(json.load(open('../skill/plugin-marketplaces/scripts/mpcheck/data/readers.json')),dict) else '')\"; head -c 600 ../skill/plugin-marketplaces/scripts/mpcheck/data/readers.json; which claude codex copilot", "description": "Run validator on baseline, list readers"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && python3 - <<'EOF'\nimport json\np='.claude-plugin/marketplace.json'; d=json.load(open(p))\nd['plugins'].append({\"name\":\"lint-kit\",\"source\":\"./plugins/lint-kit\",\"description\":\"Run the team's linters\"})\nopen(p,'w').write(json.dumps(d,indent=2)+\"\\n\")\np='.agents/plugins/marketplace.json'; d=json.load(open(p))\nd['plugins'].append({\"name\":\"lint-kit\",\"source\":{\"source\":\"local\",\"path\":\"./plugins/lint-kit\"},\"policy\":{\"installation\":\"AVAILABLE\",\"authentication\":\"ON_INSTALL\"},\"category\":\"Developer Tools\"})\nopen(p,'w').write(json.dumps(d,indent=2)+\"\\n\")\np='plugins/lint-kit/.claude-plugin/plugin.json'; d=json.load(open(p)); d['version']='1.1.0'\nopen(p,'w').write(json.dumps(d,indent=2)+\"\\n\")\njson.dump({\"readers\":[\"claude-code\",\"codex\"],\"exceptions\":[\n {\"plugin\":\"claude-hooks\",\"kind\":\"membership\",\"reason\":\"Listed for Claude Code only: Codex does not run its prompt hooks.\"},\n {\"plugin\":\"codex-helper\",\"kind\":\"membership\",\"reason\":\"Listed for Codex only: it wraps a Codex app integration.\"}]},\n open('marketplace-policy.json','w'),indent=2); open('marketplace-policy.json','a').write(\"\\n\")\nEOF\ngit diff; cat marketplace-policy.json", "description": "Add lint-kit entries, align version, write policy"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=\"$PWD/.tool-homes\"; export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\"; ../validator/bin/check-marketplace . < /dev/null; echo \"exit $?\"; rm -rf \"$T/export\"; mkdir -p \"$T/export\"; { git ls-files; git ls-files --others --exclude-standard | grep -v '^.tool-homes/'; } | sort -u | tar -cf - -T - | tar -xf - -C \"$T/export\"; find \"$T/export\" -type f | sed \"s|$T/export/||\"; claude --version </dev/null; codex --version </dev/null; copilot --version </dev/null", "description": "Validate and prepare clean export"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=\"$PWD/.tool-homes\"; export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\"; SB=(sandbox-exec -p '(version 1)(allow default)(deny network-outbound (remote ip))'); E=\"$T/export\"\necho \"== claude validate\"; \"${SB[@]}\" claude plugin validate \"$E\" --strict --json </dev/null; echo \"exit $?\"\necho \"== claude add\"; \"${SB[@]}\" claude plugin marketplace add \"$E\" </dev/null; echo \"exit $?\"\necho \"== claude install\"; \"${SB[@]}\" claude plugin install lint-kit@acme-tools </dev/null; echo \"exit $?\"\necho \"== claude details\"; \"${SB[@]}\" claude plugin details lint-kit@acme-tools </dev/null; echo \"exit $?\"\necho \"== claude list\"; \"${SB[@]}\" claude plugin list --json </dev/null; echo \"exit $?\"", "description": "Claude Code discovery and load checks, isolated"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=\"$PWD/.tool-homes\"; export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\"; SB=(sandbox-exec -p '(version 1)(allow default)(deny network-outbound (remote ip))'); E=\"$T/export\"\necho \"== codex add\"; \"${SB[@]}\" codex plugin marketplace add \"$E\" </dev/null; echo \"exit $?\"\necho \"== codex list\"; \"${SB[@]}\" codex plugin list --available --json </dev/null; echo \"exit $?\"\necho \"== codex install\"; \"${SB[@]}\" codex plugin add lint-kit@acme-tools --json </dev/null; echo \"exit $?\"", "description": "Codex discovery and load checks, isolated"}}
```

## Objective checks

```json
{
  "claude": {
    "ran": true,
    "exit": 0,
    "success": true,
    "errors": [],
    "warnings": []
  },
  "codex": {
    "ran": true,
    "added": true,
    "marketplace": "acme-tools",
    "listed": [
      "alpha-notes",
      "branch-tidy",
      "codex-helper",
      "lint-kit"
    ]
  },
  "copilot": {
    "ran": true,
    "added": true,
    "marketplace": "acme-tools",
    "listed": [
      "alpha-notes",
      "branch-tidy",
      "claude-hooks",
      "lint-kit"
    ]
  }
}
```

## Diff

```diff
diff --git a/.agents/plugins/marketplace.json b/.agents/plugins/marketplace.json
index 2f8b183..9e0daf8 100644
--- a/.agents/plugins/marketplace.json
+++ b/.agents/plugins/marketplace.json
@@ -39,6 +39,18 @@
         "authentication": "ON_INSTALL"
       },
       "category": "Developer Tools"
+    },
+    {
+      "name": "lint-kit",
+      "source": {
+        "source": "local",
+        "path": "./plugins/lint-kit"
+      },
+      "policy": {
+        "installation": "AVAILABLE",
+        "authentication": "ON_INSTALL"
+      },
+      "category": "Developer Tools"
     }
   ]
 }
diff --git a/.claude-plugin/marketplace.json b/.claude-plugin/marketplace.json
index 082fa96..2032e08 100644
--- a/.claude-plugin/marketplace.json
+++ b/.claude-plugin/marketplace.json
@@ -19,6 +19,11 @@
       "name": "claude-hooks",
       "source": "./plugins/claude-hooks",
       "description": "claude-hooks"
+    },
+    {
+      "name": "lint-kit",
+      "source": "./plugins/lint-kit",
+      "description": "Run the team's linters"
     }
   ]
 }
diff --git a/marketplace-policy.json b/marketplace-policy.json
new file mode 100644
index 0000000..d71c605
--- /dev/null
+++ b/marketplace-policy.json
@@ -0,0 +1,18 @@
+{
+  "readers": [
+    "claude-code",
+    "codex"
+  ],
+  "exceptions": [
+    {
+      "plugin": "claude-hooks",
+      "kind": "membership",
+      "reason": "Listed for Claude Code only: Codex does not run its prompt hooks."
+    },
+    {
+      "plugin": "codex-helper",
+      "kind": "membership",
+      "reason": "Listed for Codex only: it wraps a Codex app integration."
+    }
+  ]
+}
diff --git a/plugins/lint-kit/.claude-plugin/plugin.json b/plugins/lint-kit/.claude-plugin/plugin.json
index ed531df..8a4782d 100644
--- a/plugins/lint-kit/.claude-plugin/plugin.json
+++ b/plugins/lint-kit/.claude-plugin/plugin.json
@@ -1,6 +1,6 @@
 {
   "name": "lint-kit",
-  "version": "1.0.0",
+  "version": "1.1.0",
   "description": "Run the team's linters",
   "author": {
     "name": "Acme"
```

## Repository refs

Every branch and tag in the final repository, each with its changes against the fixture tree (`refs.txt`).

```text
master 7e24375
```
