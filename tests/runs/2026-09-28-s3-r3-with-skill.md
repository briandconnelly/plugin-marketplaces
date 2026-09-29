# Run: scenario 3, repetition 3, with-skill

Scored against `tests/scenarios.md` as of this commit; cost is `metrics` in the manifest.

## Manifest

```json
{
  "date": "2026-09-28",
  "arm": "with-skill",
  "scenario": "s3",
  "rep": 3,
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
  "transcript": "ad80ffb0ce2db53d8.output",
  "model": "claude-opus-5-5",
  "metrics": {
    "tool_calls": 10,
    "wall_seconds": 90.1
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
|---|---|---|
| 1 | pass | objective.json: `claude.errors` is `[]` (success true, no warnings). |
| 2 | pass | objective.json: `codex.listed` is `["focus-timer"]`. |
| 3 | pass | diff.patch: the entries in both `.claude-plugin/marketplace.json` and `.agents/plugins/marketplace.json` are named `focus-timer`, which matches `name` in `.claude-plugin/plugin.json`. |
| 4 | pass | final repo: `version` appears only in `plugin.json` and `.claude-plugin/plugin.json`, and both say 1.1.0. Neither catalog records a version. |
| 5 | pass | report.md: "Check results" lists what ran (validator, Claude Code 2.1.284, Codex 0.157.1) and has a "Not run" list (GitHub install, Copilot CLI). |
| 6 | pass | report.md, update step 3: Claude Code users get the update "only if the version string changed. A push without a version change reaches Codex users but not Claude Code users". This matches the recorded version 1.1.0. |

Total: 6 of 6 passed.

## Final report

The repository now works as its own marketplace for both Claude Code and Codex. I tested it with each tool against a local copy, but not yet from GitHub. Nothing is committed or pushed.

**What I added** (all in `$RUN/repo/`):
- `marketplace-policy.json` says the marketplace targets Claude Code and Codex.
- `.claude-plugin/marketplace.json` is the Claude Code catalog. It is named `focus-timer` and lists one plugin, `focus-timer`, found at the repository root.
- `.agents/plugins/marketplace.json` is the Codex catalog, with the same plugin at the root. Codex reads this file before the Claude one, and it has the settings Codex expects.
- `plugin.json` at the root is a portable manifest (Agent Plugins 1.0) at version 1.1.0. Codex reads this one, and Claude Code keeps reading `.claude-plugin/plugin.json`.
- The plugin descriptions in both catalogs state that it contains only a skill, with no hooks, MCP servers, or external services.
- `README.md` now has install and update commands for both tools.
- `.gitignore` excludes `.tool-homes/`, where the test setup lives.

The catalogs don't record a version, so only the two `plugin.json` files carry one.

**Check results:**
- **Validator:** passed with no errors. The Claude Code check of the catalog passed, and the portable manifest check passed. The validator couldn't run Claude Code's plugin-level check because the root is both the plugin and the marketplace, so the skill files weren't validated by it.
- **Claude Code 2.1.284:** `claude plugin validate --strict` gave no errors or warnings. Adding the marketplace and installing `focus-timer@focus-timer` worked. It installed version 1.1.0 with 1 skill and no agents, hooks, MCP servers or LSP servers.
- **Codex 0.157.1:** adding the marketplace worked, and the plugin was listed at version 1.1.0. Installing it placed version 1.1.0 in the Codex cache.
- **Not run:**
  - Installing from `acme/focus-timer` on GitHub, because I wasn't allowed to contact remote services. The first real test is running the README commands once this is pushed.
  - Copilot CLI, which wasn't a target.

Both tools used throwaway settings with network access blocked, and the tool versions match the ones the skill's references were checked against.

**When you ship an update:**
1. Change `version` in both `$RUN/repo/plugin.json` and `$RUN/repo/.claude-plugin/plugin.json` to the same new value. If they differ, Claude Code users get one version and Codex users get the other, and nothing reports it. If you ever add a `version` to either catalog entry, it has to match too.
2. Run `check-marketplace .` before pushing; it flags versions that don't match.
3. Push. Claude Code users get the update with `claude plugin update focus-timer@focus-timer` or through auto-update, but only if the version string changed. A push without a version change reaches Codex users but not Claude Code users. Codex users get it with `codex plugin marketplace upgrade focus-timer`.
4. If you ever rename the plugin, Claude Code can redirect users through a `renames` entry in its catalog. Codex has no equivalent, so to Codex users a renamed plugin is a new plugin.

## Tool calls

The arm's tool calls, one JSON object per line, extracted from its transcript.

```jsonl
{"tool": "Bash", "input": {"command": "cd $RUN/repo && git status && find . -path ./.git -prune -o -type f -print | head -50 && cat $RUN/skill/plugin-marketplaces/SKILL.md && ls -R $RUN/skill/plugin-marketplaces", "description": "Inspect repo and read skill"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && cat README.md .claude-plugin/plugin.json skills/focus-timer/SKILL.md; git log --oneline | head; S=$RUN/skill/plugin-marketplaces/references; cat $S/multi-tool.md $S/releases.md", "description": "Read repo files and references"}}
{"tool": "Bash", "input": {"command": "S=$RUN/skill/plugin-marketplaces/references; cat $S/validation.md $S/codex.md $S/claude-code.md", "description": "Read validation, codex, claude-code refs"}}
{"tool": "Bash", "input": {"command": "S=$RUN/skill/plugin-marketplaces; cat $S/references/agent-plugins.md $S/references/feature-matrix.md; cat $S/scripts/mpcheck/policy.py; cat $S/scripts/mpcheck/data/readers.json | head -80", "description": "Read agent-plugins, feature matrix, policy code"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && mkdir -p .agents/plugins && cat > marketplace-policy.json <<'EOF'\n{\n  \"readers\": [\"claude-code\", \"codex\"],\n  \"exceptions\": [],\n  \"channels\": []\n}\nEOF\ncat > plugin.json <<'EOF'\n{\n  \"$schema\": \"https://agent-plugins.org/schemas/1.0.0/plugin.schema.json\",\n  \"name\": \"focus-timer\",\n  \"version\": \"1.1.0\",\n  \"description\": \"Run focus sessions\",\n  \"author\": {\n    \"name\": \"Acme\"\n  },\n  \"repository\": \"https://github.com/acme/focus-timer\"\n}\nEOF\ncat > .claude-plugin/marketplace.json <<'EOF'\n{\n  \"name\": \"focus-timer\",\n  \"owner\": {\n    \"name\": \"Acme\"\n  },\n  \"plugins\": [\n    {\n      \"name\": \"focus-timer\",\n      \"source\": \"./\",\n      \"description\": \"Run focus sessions. Skills only: no hooks, MCP servers, or external services.\"\n    }\n  ]\n}\nEOF\ncat > .agents/plugins/marketplace.json <<'EOF'\n{\n  \"name\": \"focus-timer\",\n  \"plugins\": [\n    {\n      \"name\": \"focus-timer\",\n      \"source\": {\n        \"source\": \"local\",\n        \"path\": \"./\"\n      },\n      \"description\": \"Run focus sessions. Skills only: no hooks, MCP servers, or external services.\",\n      \"policy\": {\n        \"installation\": \"AVAILABLE\",\n        \"authentication\": \"ON_INSTALL\"\n      },\n      \"category\": \"Productivity\"\n    }\n  ]\n}\nEOF\nT=$PWD/.tool-homes; mkdir -p $T/{home,xdg,tmp}; echo \".tool-homes/\" > .gitignore\nHOME=$T/home XDG_CONFIG_HOME=$T/xdg TMPDIR=$T/tmp $RUN/validator/bin/check-marketplace . ; echo exit=$?; which claude codex copilot", "description": "Write catalogs, policy, portable manifest; run validator"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && python3 - <<'EOF'\nimport json\np='.claude-plugin/marketplace.json'\nd=json.load(open(p))\nd={\"name\":d[\"name\"],\"description\":\"Marketplace for the focus-timer plugin\",\"owner\":d[\"owner\"],\"plugins\":d[\"plugins\"]}\nopen(p,'w').write(json.dumps(d,indent=2)+\"\\n\")\nEOF\nT=$PWD/.tool-homes; HOME=$T/home XDG_CONFIG_HOME=$T/xdg TMPDIR=$T/tmp $RUN/validator/bin/check-marketplace . ; echo exit=$?", "description": "Add marketplace description and re-validate"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=\"$PWD/.tool-homes\"; rm -rf \"$T/export\"; mkdir -p \"$T\"/{home,xdg,tmp,claude,codex,export}; : > \"$T/gitconfig\"\ngit ls-files -co --exclude-standard | grep -v '^.tool-homes' | tar -cf - -T - | tar -xf - -C \"$T/export\"; find \"$T/export\" -type f\nexport HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\"\nSB=\"sandbox-exec -p (version 1)(allow default)(deny network-outbound (remote ip))\"\ncd \"$T\"\necho \"--- versions\"; $SB claude --version </dev/null; $SB codex --version </dev/null\necho \"--- claude validate marketplace\"; $SB claude plugin validate \"$T/export\" --strict --json </dev/null; echo exit=$?\necho \"--- claude marketplace add\"; $SB claude plugin marketplace add \"$T/export\" </dev/null; echo exit=$?\necho \"--- claude install\"; $SB claude plugin install focus-timer@focus-timer </dev/null; echo exit=$?\necho \"--- claude details\"; $SB claude plugin details focus-timer@focus-timer </dev/null; echo exit=$?\necho \"--- claude list\"; $SB claude plugin list --json </dev/null", "description": "Isolated Claude Code discovery and load checks"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=\"$PWD/.tool-homes\"\nexport HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\"\nsb() { sandbox-exec -p '(version 1)(allow default)(deny network-outbound (remote ip))' \"$@\" </dev/null; }\ncd \"$T\"\necho \"--- versions\"; sb claude --version; sb codex --version\necho \"--- claude validate marketplace\"; sb claude plugin validate \"$T/export\" --strict --json; echo exit=$?\necho \"--- claude marketplace add\"; sb claude plugin marketplace add \"$T/export\"; echo exit=$?\necho \"--- claude install\"; sb claude plugin install focus-timer@focus-timer; echo exit=$?\necho \"--- claude details\"; sb claude plugin details focus-timer@focus-timer; echo exit=$?\necho \"--- claude list\"; sb claude plugin list --json", "description": "Isolated Claude Code discovery and load checks"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=\"$PWD/.tool-homes\"\nexport HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\"\nsb() { sandbox-exec -p '(version 1)(allow default)(deny network-outbound (remote ip))' \"$@\" </dev/null; }\ncd \"$T\"\necho \"--- codex marketplace add\"; sb codex plugin marketplace add \"$T/export\"; echo exit=$?\necho \"--- codex list available\"; sb codex plugin list --available --json; echo exit=$?\necho \"--- codex add\"; sb codex plugin add focus-timer@focus-timer --json; echo exit=$?\nfind \"$T/codex/plugins/cache\" -maxdepth 4 2>/dev/null", "description": "Isolated Codex discovery and load checks"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && cat > README.md <<'EOF'\n# focus-timer\n\nA plugin that runs focus sessions, for Claude Code and Codex.\nThis repository is its own marketplace.\n\n## Install\n\nClaude Code:\n\n```bash\nclaude plugin marketplace add acme/focus-timer\nclaude plugin install focus-timer@focus-timer\n```\n\nCodex:\n\n```bash\ncodex plugin marketplace add acme/focus-timer\ncodex plugin add focus-timer@focus-timer\n```\n\n## Update\n\nClaude Code: `claude plugin update focus-timer@focus-timer` (a new version is delivered only when the plugin's version changes).\n\nCodex: `codex plugin marketplace upgrade focus-timer`.\nEOF\nT=$PWD/.tool-homes; HOME=$T/home XDG_CONFIG_HOME=$T/xdg TMPDIR=$T/tmp $RUN/validator/bin/check-marketplace . | head -8; git status --short", "description": "Update README and recheck status"}}
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
index 0000000..0884713
--- /dev/null
+++ b/.claude-plugin/marketplace.json
@@ -0,0 +1,14 @@
+{
+  "name": "focus-timer",
+  "description": "Marketplace for the focus-timer plugin",
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
index d672c1a..1109069 100644
--- a/README.md
+++ b/README.md
@@ -1,3 +1,26 @@
 # focus-timer
 
-A Claude Code plugin that runs focus sessions.
+A plugin that runs focus sessions, for Claude Code and Codex.
+This repository is its own marketplace.
+
+## Install
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
+## Update
+
+Claude Code: `claude plugin update focus-timer@focus-timer` (a new version is delivered only when the plugin's version changes).
+
+Codex: `codex plugin marketplace upgrade focus-timer`.
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
master e525bd9
```
