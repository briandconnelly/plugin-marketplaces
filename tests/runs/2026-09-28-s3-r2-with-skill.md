# Run: scenario 3, repetition 2, with-skill

Scored against `tests/scenarios.md` as of this commit; cost is `metrics` in the manifest.

## Manifest

```json
{
  "date": "2026-09-28",
  "arm": "with-skill",
  "scenario": "s3",
  "rep": 2,
  "fixture_tree": "50fa9cb7145a617760121a0ed90bce9b90865a60",
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
  "transcript": "a00dc5d0e7d18e370.output",
  "model": "claude-opus-5-5",
  "metrics": {
    "tool_calls": 11,
    "wall_seconds": 100.2
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

People want to install this plugin straight from its GitHub repository (acme/focus-timer) in both Claude Code and Codex.
Make the repository work as its own marketplace, and tell me what I'll need to do when I ship an update.
```

## Isolation

Flags raised by `tests/eval/isolation.py` (tests/scenarios.md, How to run, step 5):

```text
(none)
```

Batch 4. Every tool call read; no violation. s4: Copilot limited to plugin/skill/mcp subcommands; codex debug prompt-input only on stand-ins with stubbed scripts (plan-2c ledger).

## Score

| Criterion | Result | Evidence |
| --- | --- | --- |
| 1 | pass | objective.json: `claude.errors` is `[]` (exit 0, success true, no warnings). |
| 2 | pass | objective.json: `codex.listed` is `["focus-timer"]`. |
| 3 | pass | diff.patch: the plugin entry in both `.claude-plugin/marketplace.json` and `.agents/plugins/marketplace.json` is named `focus-timer`, which matches `name` in `.claude-plugin/plugin.json` and the new `plugin.json`. |
| 4 | pass | Final repo: `.claude-plugin/plugin.json` and `plugin.json` both record `"version": "1.1.0"`, and neither catalog records a version (grep over the repo finds only these two). |
| 5 | pass | report.md: the "Check results" table marks each check passed, not run ("Remote (fetching from GitHub)"), partly checked ("Load, Codex") or not a target ("Copilot CLI"). |
| 6 | pass | report.md, "When you ship an update" step 2: "Claude Code users won't get a change pushed without a bump (it answers 'already at the latest version')". A version is recorded, so this is the right advice. |

Total: 6 of 6 passed.

## Final report

The repository now works as its own marketplace for both Claude Code and Codex. The validator passes, and in isolated local runs both tools listed, installed and loaded the plugin at version 1.1.0. Nothing is committed or pushed, and I haven't tried installing from `acme/focus-timer` on GitHub.

**What I added** (all under `$RUN/repo`):
- `$RUN/repo/marketplace-policy.json` names the two target tools: `claude-code` and `codex`.
- `$RUN/repo/plugin.json` is a portable plugin manifest in the Agent Plugins format, with name `focus-timer` and version `1.1.0`. Codex reads this file; Claude Code keeps reading the existing `.claude-plugin/plugin.json`.
- `$RUN/repo/.claude-plugin/marketplace.json` is the catalog Claude Code reads. The marketplace is named `focus-timer`, and its one entry points at the repository root (`./`).
- `$RUN/repo/.agents/plugins/marketplace.json` is the catalog Codex reads, with the same entry in Codex's format.
- Neither catalog records a version, so there are fewer places to change at release time. Both entry descriptions say the plugin has only a skill: no hooks, MCP servers or external services.
- `$RUN/repo/README.md` now has install and release sections.
- `$RUN/repo/.gitignore` ignores `.tool-homes/`, where the checks kept their throwaway settings.

People will install it with:
- **Claude Code:** `claude plugin marketplace add acme/focus-timer`, then `claude plugin install focus-timer@focus-timer`.
- **Codex:** `codex plugin marketplace add acme/focus-timer`, then `codex plugin add focus-timer@focus-timer`.

**When you ship an update:**
1. Change `version` in both `plugin.json` and `.claude-plugin/plugin.json`, and keep the two values the same. Each tool reads only its own file, and a disagreement installs different versions for Claude Code and Codex users with no error.
2. Always bump the version. Claude Code users won't get a change pushed without a bump (it answers "already at the latest version"), while Codex users get it anyway.
3. Run `check-marketplace .` before pushing. It fails when the two versions disagree; I confirmed this by setting a copy's `plugin.json` to 1.2.0.
4. After you push, Claude Code users get the update with `claude plugin update` (or auto-update, if they turned it on; it's off by default for third-party marketplaces). Codex users get it with `codex plugin marketplace upgrade`.
5. If you ever add hooks, MCP servers or an external service, say so in both catalog entry descriptions. An MCP server also needs a `.mcp.json` for Claude Code and an `mcp.json` for Codex.

**Check results** (Claude Code 2.1.284 and Codex 0.157.1, run against a clean copy of the repository with throwaway settings and network access blocked):

| Check | Result | Evidence |
| --- | --- | --- |
| File format | passed | Validator exited 0. `claude plugin validate --strict` passed with 0 errors and 0 warnings, on both the catalog and the plugin manifest. |
| Rules (paths, names, versions, the two catalogs matching) | passed | Validator. |
| Remote (fetching from GitHub) | not run | No network, and the plugin is referenced by a local path, so nothing is pinned. |
| Discovery, Claude Code | passed | `claude plugin marketplace add` succeeded. |
| Discovery, Codex | passed | `codex plugin list --available` listed `focus-timer@focus-timer` at 1.1.0. |
| Load, Claude Code | passed | Installed at 1.1.0; `claude plugin details` shows 1 skill (`focus-timer`) and no agents, hooks or servers. |
| Load, Codex | partly checked | Installed at 1.1.0, and `codex mcp list` showed no servers. I didn't confirm that Codex offers the skill, because the only command that shows this opens the plugin in a session, which the skill's rules forbid for a plugin I didn't write. |
| Copilot CLI | not a target | Not checked. |

The README install commands above are the tools' documented forms; I haven't run them against GitHub.

## Tool calls

The arm's tool calls, one JSON object per line, extracted from its transcript.

```jsonl
{"tool": "Bash", "input": {"command": "cd $RUN/repo && git status && find . -path ./.git -prune -o -type f -print | head -50 && cat $RUN/skill/plugin-marketplaces/SKILL.md && ls -R $RUN/skill/plugin-marketplaces"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && cat README.md .claude-plugin/plugin.json skills/focus-timer/SKILL.md; git log --oneline; S=$RUN/skill/plugin-marketplaces/references; cat $S/multi-tool.md $S/releases.md"}}
{"tool": "Bash", "input": {"command": "S=$RUN/skill/plugin-marketplaces/references; cat $S/codex.md $S/validation.md"}}
{"tool": "Bash", "input": {"command": "S=$RUN/skill/plugin-marketplaces; cat $S/references/claude-code.md $S/references/agent-plugins.md $S/references/feature-matrix.md; cat $S/scripts/mpcheck/policy.py"}}
{"tool": "Bash", "input": {"command": "S=$RUN/skill/plugin-marketplaces/scripts/mpcheck; cat $S/data/readers.json; grep -n '\"\\./\\?\"\\|== \"\\.\"\\|startswith' $S/checks_local.py | head -30; which claude codex copilot"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && mkdir -p .agents/plugins && cat > marketplace-policy.json <<'EOF'\n{\n  \"readers\": [\"claude-code\", \"codex\"],\n  \"exceptions\": [],\n  \"channels\": []\n}\nEOF\ncat > plugin.json <<'EOF'\n{\n  \"$schema\": \"https://agent-plugins.org/schemas/1.0.0/plugin.schema.json\",\n  \"name\": \"focus-timer\",\n  \"version\": \"1.1.0\",\n  \"description\": \"Run focus sessions\",\n  \"author\": {\n    \"name\": \"Acme\"\n  },\n  \"repository\": \"https://github.com/acme/focus-timer\"\n}\nEOF\ncat > .claude-plugin/marketplace.json <<'EOF'\n{\n  \"name\": \"focus-timer\",\n  \"owner\": {\n    \"name\": \"Acme\"\n  },\n  \"plugins\": [\n    {\n      \"name\": \"focus-timer\",\n      \"source\": \"./\",\n      \"description\": \"Run focus sessions. Skills only: no hooks, MCP servers, or external services.\"\n    }\n  ]\n}\nEOF\ncat > .agents/plugins/marketplace.json <<'EOF'\n{\n  \"name\": \"focus-timer\",\n  \"plugins\": [\n    {\n      \"name\": \"focus-timer\",\n      \"source\": {\n        \"source\": \"local\",\n        \"path\": \"./\"\n      },\n      \"description\": \"Run focus sessions. Skills only: no hooks, MCP servers, or external services.\",\n      \"policy\": {\n        \"installation\": \"AVAILABLE\",\n        \"authentication\": \"ON_INSTALL\"\n      },\n      \"category\": \"Productivity\"\n    }\n  ]\n}\nEOF\necho \".tool-homes/\" > .gitignore\nT=$PWD/.tool-homes; mkdir -p $T/{home,xdg,tmp,claude,codex,copilot,copilot-cache}; : > $T/gitconfig\nexport HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\"\n$RUN/validator/bin/check-marketplace . < /dev/null; echo exit=$?"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && python3 - <<'EOF'\nimport json\np='.claude-plugin/marketplace.json'\nd=json.load(open(p))\nd={\"name\":d[\"name\"],\"description\":\"Acme's focus-timer plugin, served from its own repository\",\"owner\":d[\"owner\"],\"plugins\":d[\"plugins\"]}\nopen(p,'w').write(json.dumps(d,indent=2)+\"\\n\")\nEOF\nT=$PWD/.tool-homes\nexport HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\"\n$RUN/validator/bin/check-marketplace . < /dev/null; echo exit=$?\nrm -rf $T/export && mkdir -p $T/export && git ls-files -co --exclude-standard | tar -cf - -T - | tar -xf - -C $T/export && find $T/export -type f"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=$PWD/.tool-homes\nexport HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\"\nSB='(version 1)(allow default)(deny network-outbound (remote ip))'\nE=$T/export\nclaude --version </dev/null; codex --version </dev/null\necho \"--- claude validate marketplace\"; sandbox-exec -p \"$SB\" claude plugin validate $E --strict --json </dev/null; echo exit=$?\nrm -rf $T/pluginonly && mkdir $T/pluginonly && cp -R $E/. $T/pluginonly && rm $T/pluginonly/.claude-plugin/marketplace.json\necho \"--- claude validate plugin\"; sandbox-exec -p \"$SB\" claude plugin validate $T/pluginonly --strict --json </dev/null; echo exit=$?\necho \"--- claude add\"; sandbox-exec -p \"$SB\" claude plugin marketplace add $E </dev/null; echo exit=$?\necho \"--- claude install\"; sandbox-exec -p \"$SB\" claude plugin install focus-timer@focus-timer </dev/null; echo exit=$?\necho \"--- claude details\"; sandbox-exec -p \"$SB\" claude plugin details focus-timer@focus-timer </dev/null; echo exit=$?\nsandbox-exec -p \"$SB\" claude plugin list --json </dev/null"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=$PWD/.tool-homes\nexport HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\"\nSB='(version 1)(allow default)(deny network-outbound (remote ip))'\nE=$T/export\necho \"--- codex add\"; sandbox-exec -p \"$SB\" codex plugin marketplace add $E </dev/null; echo exit=$?\necho \"--- codex list\"; sandbox-exec -p \"$SB\" codex plugin list --available --json </dev/null; echo exit=$?\necho \"--- codex install\"; sandbox-exec -p \"$SB\" codex plugin add focus-timer@focus-timer --json </dev/null; echo exit=$?\nfind $T/codex/plugins/cache -maxdepth 4 | head; sandbox-exec -p \"$SB\" codex mcp list --json </dev/null"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=$PWD/.tool-homes; export TMPDIR=$T/tmp CLAUDE_CONFIG_DIR=$T/claude HOME=$T/home XDG_CONFIG_HOME=$T/xdg\nrm -rf $T/neg && cp -R $T/export $T/neg && sed -i '' 's/\"1.1.0\"/\"1.2.0\"/' $T/neg/plugin.json\n$RUN/validator/bin/check-marketplace $T/neg </dev/null | grep -iE 'local|version'; echo exit=$?\ngit status --short"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && cat > README.md <<'EOF'\n# focus-timer\n\nA plugin for Claude Code and Codex that runs focus sessions.\n\n## Install\n\nThis repository is its own marketplace.\n\nClaude Code:\n\n```bash\nclaude plugin marketplace add acme/focus-timer\nclaude plugin install focus-timer@focus-timer\n```\n\nCodex:\n\n```bash\ncodex plugin marketplace add acme/focus-timer\ncodex plugin add focus-timer@focus-timer\n```\n\n## Releasing\n\nSet the same new `version` in both `plugin.json` (read by Codex) and `.claude-plugin/plugin.json` (read by Claude Code), then run the marketplace validator before pushing.\nEOF\ngit status --short"}}
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
    "marketplace": "focus-timer",
    "listed": [
      "focus-timer"
    ]
  },
  "copilot": {
    "ran": true,
    "added": true,
    "marketplace": "focus-timer",
    "listed": [
      "focus-timer"
    ]
  }
}
```

## Diff

```diff
diff --git a/.agents/plugins/marketplace.json b/.agents/plugins/marketplace.json
new file mode 100644
index 0000000..11b5483
--- /dev/null
+++ b/.agents/plugins/marketplace.json
@@ -0,0 +1,18 @@
+{
+  "name": "focus-timer",
+  "plugins": [
+    {
+      "name": "focus-timer",
+      "source": {
+        "source": "local",
+        "path": "./"
+      },
+      "description": "Run focus sessions. Skills only: no hooks, MCP servers, or external services.",
+      "policy": {
+        "installation": "AVAILABLE",
+        "authentication": "ON_INSTALL"
+      },
+      "category": "Productivity"
+    }
+  ]
+}
diff --git a/.claude-plugin/marketplace.json b/.claude-plugin/marketplace.json
new file mode 100644
index 0000000..f4ccd0d
--- /dev/null
+++ b/.claude-plugin/marketplace.json
@@ -0,0 +1,14 @@
+{
+  "name": "focus-timer",
+  "description": "Acme's focus-timer plugin, served from its own repository",
+  "owner": {
+    "name": "Acme"
+  },
+  "plugins": [
+    {
+      "name": "focus-timer",
+      "source": "./",
+      "description": "Run focus sessions. Skills only: no hooks, MCP servers, or external services."
+    }
+  ]
+}
diff --git a/.gitignore b/.gitignore
new file mode 100644
index 0000000..f47da48
--- /dev/null
+++ b/.gitignore
@@ -0,0 +1 @@
+.tool-homes/
diff --git a/README.md b/README.md
index d672c1a..c7ef1ed 100644
--- a/README.md
+++ b/README.md
@@ -1,3 +1,25 @@
 # focus-timer
 
-A Claude Code plugin that runs focus sessions.
+A plugin for Claude Code and Codex that runs focus sessions.
+
+## Install
+
+This repository is its own marketplace.
+
+Claude Code:
+
+```bash
+claude plugin marketplace add acme/focus-timer
+claude plugin install focus-timer@focus-timer
+```
+
+Codex:
+
+```bash
+codex plugin marketplace add acme/focus-timer
+codex plugin add focus-timer@focus-timer
+```
+
+## Releasing
+
+Set the same new `version` in both `plugin.json` (read by Codex) and `.claude-plugin/plugin.json` (read by Claude Code), then run the marketplace validator before pushing.
diff --git a/marketplace-policy.json b/marketplace-policy.json
new file mode 100644
index 0000000..59c9f83
--- /dev/null
+++ b/marketplace-policy.json
@@ -0,0 +1,5 @@
+{
+  "readers": ["claude-code", "codex"],
+  "exceptions": [],
+  "channels": []
+}
diff --git a/plugin.json b/plugin.json
new file mode 100644
index 0000000..5ce4eca
--- /dev/null
+++ b/plugin.json
@@ -0,0 +1,10 @@
+{
+  "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
+  "name": "focus-timer",
+  "version": "1.1.0",
+  "description": "Run focus sessions",
+  "author": {
+    "name": "Acme"
+  },
+  "repository": "https://github.com/acme/focus-timer"
+}
```

## Repository refs

Every branch and tag in the final repository, each with its changes against the fixture tree (`refs.txt`).

```text
master 1522a01
```
