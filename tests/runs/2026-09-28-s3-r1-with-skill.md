# Run: scenario 3, repetition 1, with-skill

Scored against `tests/scenarios.md` as of this commit; cost is `metrics` in the manifest.

## Manifest

```json
{
  "date": "2026-09-28",
  "arm": "with-skill",
  "scenario": "s3",
  "rep": 1,
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
  "transcript": "a68413b23a3abc467.output",
  "model": "claude-opus-5-5",
  "metrics": {
    "tool_calls": 10,
    "wall_seconds": 89.7
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
after the run symlink-outside: $RUN/repo/.tool-homes/codex/tmp/arg0/codex-arg08Dxi9E/applypatch -> /opt/homebrew/lib/node_modules/@openai/codex/node_modules/@openai/codex-darwin-arm64/vendor/aarch64-apple-darwin/bin/codex
after the run symlink-outside: $RUN/repo/.tool-homes/codex/tmp/arg0/codex-arg08Dxi9E/apply_patch -> /opt/homebrew/lib/node_modules/@openai/codex/node_modules/@openai/codex-darwin-arm64/vendor/aarch64-apple-darwin/bin/codex
after the run symlink-outside: $RUN/repo/.tool-homes/codex/tmp/arg0/codex-arg08Dxi9E/codex-execve-wrapper -> /opt/homebrew/lib/node_modules/@openai/codex/node_modules/@openai/codex-darwin-arm64/vendor/aarch64-apple-darwin/bin/codex
```

Batch 4. Every tool call read; no violation. The symlink-outside flags are links Codex created in its throwaway CODEX_HOME/tmp/arg0 to its own installed binary, ruled not an escape (plan-2c ledger).

## Score

| Criterion | Result | Evidence |
| --- | --- | --- |
| 1 | pass | objective.json: `claude.errors` is `[]` (exit 0, success true). |
| 2 | pass | objective.json: `codex.listed` is `["focus-timer"]`. |
| 3 | pass | diff.patch: the plugin entry is `"name": "focus-timer"` in both `.claude-plugin/marketplace.json` and `.agents/plugins/marketplace.json`, which matches `.claude-plugin/plugin.json` `name`. |
| 4 | pass | A grep of the final repo finds `"version": "1.1.0"` in `.claude-plugin/plugin.json`, `plugin.json`, and both marketplace.json entries. There are no other version records. |
| 5 | pass | report.md: the "Checks" table marks each check as passed, partly checked, or not run (for example, the GitHub install was not tested, `codex debug prompt-input` was not run, and Copilot CLI was not run). |
| 6 | pass | report.md: under update step 2, "If you push without a bump, Claude Code users get 'already at the latest version' and never receive the change". The version is recorded as 1.1.0. |

Total: 6 of 6 passed.

## Final report

The repository is now its own marketplace for both Claude Code and Codex. Both tools listed and installed focus-timer 1.1.0 from a clean copy of the repo. I have not committed or pushed anything, and I did not test installing from GitHub itself.

**What I changed** (all under `$RUN/repo`):
- `marketplace-policy.json` (new): names Claude Code and Codex as the two target tools. It lists no exceptions and no tracking branches.
- `.claude-plugin/marketplace.json` (new): the catalog Claude Code reads. The marketplace is named `focus-timer` and has one `focus-timer` entry pointing at the repo root (`"./"`), at version 1.1.0. Its description says the plugin is skills only, with no hooks, MCP servers or external services.
- `.agents/plugins/marketplace.json` (new): the catalog Codex reads. It has the same entry and version, plus the `policy` fields and `category` that OpenAI recommends.
- `plugin.json` (new, at the repo root): a portable Agent Plugins manifest (name `focus-timer`, version 1.1.0). Codex and Copilot CLI read this file; Claude Code keeps reading `.claude-plugin/plugin.json`, which I left unchanged.
- `README.md`: added install and update commands for both tools.
- `.gitignore` (new): ignores `.tool-homes/`, the throwaway directory I used for tool state during the checks.

People will install it with:
- **Claude Code:** `claude plugin marketplace add acme/focus-timer`, then `claude plugin install focus-timer@focus-timer`
- **Codex:** `codex plugin marketplace add acme/focus-timer`, then `codex plugin add focus-timer@focus-timer`

**Checks**
| Check | Result | Evidence |
| --- | --- | --- |
| Catalog and manifest format | passed | `check-marketplace`: all format checks passed. `claude plugin validate --strict` (2.1.284): 0 errors, 0 warnings, after I added a marketplace description it asked for. The validator can't validate the plugin's own files here, because the repo root is also the marketplace. |
| Local rules | passed | `check-marketplace` exit 0. As a control, a copy with a different root `plugin.json` version produced `local.version-mismatch` errors, so the check does catch mismatches. |
| Pinned remote sources | not applicable / not run | There are no remote sources. I pushed nothing and did not test installing from GitHub. |
| Catalog listing, Claude Code | passed | `claude plugin marketplace add` on a clean copy succeeded. |
| Catalog listing, Codex | passed | `codex plugin list --available --json` (0.157.1) listed `focus-timer@focus-timer` at 1.1.0. |
| Plugin load, Claude Code | passed | Install succeeded. `claude plugin details` showed version 1.1.0 and 1 skill (`focus-timer`), with no agents, hooks, MCP servers or LSP servers. |
| Plugin load, Codex | partly checked | `codex plugin add --json` installed version 1.1.0, and the installed copy contains `skills/focus-timer/SKILL.md`. I did not run `codex debug prompt-input`, so Codex actually offering the skill is unproven. |
| Copilot CLI | not run | It isn't a target. |

All tool runs used throwaway configuration under `.tool-homes/` with outbound network blocked. No model sessions were started.

**What you'll need to do when you ship an update**
1. Change the version to the same value in all four places:
   - `.claude-plugin/plugin.json`
   - `plugin.json`
   - the entry in `.claude-plugin/marketplace.json`
   - the entry in `.agents/plugins/marketplace.json`
   
   Claude Code takes its version from `.claude-plugin/plugin.json` and Codex from the root `plugin.json`. If they disagree, each tool quietly installs a different version.
2. Bump the version on every release. If you push without a bump, Claude Code users get "already at the latest version" and never receive the change. Codex users would still get it, because `codex plugin marketplace upgrade` replaces the installed copy even without a new version.
3. Run `check-marketplace` on the repo (it flags any version mismatch), then commit and push.
4. How users get the update:
   - **Claude Code:** `claude plugin marketplace update focus-timer`, then `claude plugin update focus-timer@focus-timer`. They can also turn on auto-update, which is off by default for third-party marketplaces.
   - **Codex:** `codex plugin marketplace upgrade focus-timer`.
5. If you ever add hooks, MCP servers, `bin/` scripts or external services, update both catalog descriptions to say so. If you add MCP servers, declare them both in `.mcp.json` (for Claude Code) and in a portable `mcp.json` (for Codex).

## Tool calls

The arm's tool calls, one JSON object per line, extracted from its transcript.

```jsonl
{"tool": "Bash", "input": {"command": "cd $RUN/repo && cat $RUN/skill/plugin-marketplaces/SKILL.md && ls -R $RUN/skill/plugin-marketplaces && git status && git log --oneline | head && find . -path ./.git -prune -o -type f -print"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && cat README.md .claude-plugin/plugin.json skills/focus-timer/SKILL.md; S=$RUN/skill/plugin-marketplaces/references; cat $S/multi-tool.md $S/releases.md $S/codex.md"}}
{"tool": "Bash", "input": {"command": "S=$RUN/skill/plugin-marketplaces/references; cat $S/claude-code.md $S/validation.md $S/agent-plugins.md $S/feature-matrix.md"}}
{"tool": "Bash", "input": {"command": "cd $RUN/skill/plugin-marketplaces/scripts/mpcheck && cat policy.py; cat data/readers.json | head -80; grep -n '\"\\.\"\\|\"\\./\"\\|startswith' checks_local.py | head -30; which claude codex copilot git"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && mkdir -p .agents/plugins && cat > marketplace-policy.json <<'EOF'\n{\n  \"readers\": [\"claude-code\", \"codex\"],\n  \"exceptions\": [],\n  \"channels\": []\n}\nEOF\ncat > plugin.json <<'EOF'\n{\n  \"$schema\": \"https://agent-plugins.org/schemas/1.0.0/plugin.schema.json\",\n  \"name\": \"focus-timer\",\n  \"version\": \"1.1.0\",\n  \"description\": \"Run focus sessions\",\n  \"author\": {\n    \"name\": \"Acme\"\n  }\n}\nEOF\ncat > .claude-plugin/marketplace.json <<'EOF'\n{\n  \"name\": \"focus-timer\",\n  \"owner\": {\n    \"name\": \"Acme\"\n  },\n  \"plugins\": [\n    {\n      \"name\": \"focus-timer\",\n      \"source\": \"./\",\n      \"description\": \"Run focus sessions. Skills only: no hooks, MCP servers, or external services.\",\n      \"version\": \"1.1.0\"\n    }\n  ]\n}\nEOF\ncat > .agents/plugins/marketplace.json <<'EOF'\n{\n  \"name\": \"focus-timer\",\n  \"plugins\": [\n    {\n      \"name\": \"focus-timer\",\n      \"source\": {\n        \"source\": \"local\",\n        \"path\": \"./\"\n      },\n      \"description\": \"Run focus sessions. Skills only: no hooks, MCP servers, or external services.\",\n      \"version\": \"1.1.0\",\n      \"policy\": {\n        \"installation\": \"AVAILABLE\",\n        \"authentication\": \"ON_INSTALL\"\n      },\n      \"category\": \"Productivity\"\n    }\n  ]\n}\nEOF\ngrep -qx '.tool-homes/' .gitignore 2>/dev/null || echo '.tool-homes/' >> .gitignore\nT=\"$PWD/.tool-homes\"; mkdir -p \"$T\"/{home,xdg,tmp,claude,codex}; : > \"$T/gitconfig\"\nexport HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\"\n$RUN/validator/bin/check-marketplace . < /dev/null; echo exit=$?"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && python3 - <<'EOF'\nimport json\np='.claude-plugin/marketplace.json'\nd=json.load(open(p))\nd={\"name\":d[\"name\"],\"owner\":d[\"owner\"],\"metadata\":{\"description\":\"Acme's focus-timer plugin, served from its own repository.\"},\"plugins\":d[\"plugins\"]}\nopen(p,'w').write(json.dumps(d,indent=2)+\"\\n\")\nEOF\nT=\"$PWD/.tool-homes\"\nexport HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\"\nV=$RUN/validator/bin/check-marketplace\n$V . < /dev/null; echo exit=$?\n# positive control: version mismatch in a scratch copy\nrm -rf \"$T/neg\"; mkdir -p \"$T/neg\"; rsync -a --exclude .git --exclude .tool-homes ./ \"$T/neg/\"\nsed -i '' 's/\"version\": \"1.1.0\"/\"version\": \"1.2.0\"/' \"$T/neg/plugin.json\"\n$V \"$T/neg\" < /dev/null | tail -5; echo exit=$?"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=\"$PWD/.tool-homes\"\nexport HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\"\nE=\"$T/export\"; rm -rf \"$E\"; mkdir -p \"$E\"; rsync -a --exclude .git --exclude .tool-homes ./ \"$E/\"; find \"$E\" -type f\nSB='(version 1)(allow default)(deny network-outbound (remote ip))'\necho --- claude; claude --version </dev/null\nsandbox-exec -p \"$SB\" claude plugin validate \"$E\" --strict --json </dev/null; echo exit=$?\nsandbox-exec -p \"$SB\" claude plugin marketplace add \"$E\" </dev/null; echo exit=$?\nsandbox-exec -p \"$SB\" claude plugin install focus-timer@focus-timer </dev/null; echo exit=$?\nsandbox-exec -p \"$SB\" claude plugin details focus-timer@focus-timer </dev/null; echo exit=$?\nsandbox-exec -p \"$SB\" claude plugin list --json </dev/null; echo exit=$?"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=\"$PWD/.tool-homes\"\nexport HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\"\nE=\"$T/export\"; SB='(version 1)(allow default)(deny network-outbound (remote ip))'\ncodex --version </dev/null\nsandbox-exec -p \"$SB\" codex plugin marketplace add \"$E\" </dev/null; echo exit=$?\nsandbox-exec -p \"$SB\" codex plugin list --available --json </dev/null; echo exit=$?\nsandbox-exec -p \"$SB\" codex plugin add focus-timer@focus-timer --json </dev/null; echo exit=$?\nsandbox-exec -p \"$SB\" codex mcp list --json </dev/null; echo exit=$?\nls -R \"$CODEX_HOME/plugins/cache\" | head -20"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && cat >> README.md <<'EOF'\n\n## Install\n\nThis repository is its own marketplace, named `focus-timer`.\n\nClaude Code:\n\n```bash\nclaude plugin marketplace add acme/focus-timer\nclaude plugin install focus-timer@focus-timer\n```\n\nCodex:\n\n```bash\ncodex plugin marketplace add acme/focus-timer\ncodex plugin add focus-timer@focus-timer\n```\n\n## Update\n\nClaude Code: `claude plugin marketplace update focus-timer`, then `claude plugin update focus-timer@focus-timer`.\nCodex: `codex plugin marketplace upgrade focus-timer`.\nEOF\ngit status --short; cat .gitignore"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=\"$PWD/.tool-homes\"; export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\"; claude plugin marketplace --help </dev/null | grep -i update; claude plugin --help </dev/null | grep -i update; codex plugin marketplace --help </dev/null | grep -i upgrade"}}
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
index 0000000..b79028f
--- /dev/null
+++ b/.agents/plugins/marketplace.json
@@ -0,0 +1,19 @@
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
+      "version": "1.1.0",
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
index 0000000..7c5c92e
--- /dev/null
+++ b/.claude-plugin/marketplace.json
@@ -0,0 +1,17 @@
+{
+  "name": "focus-timer",
+  "owner": {
+    "name": "Acme"
+  },
+  "metadata": {
+    "description": "Acme's focus-timer plugin, served from its own repository."
+  },
+  "plugins": [
+    {
+      "name": "focus-timer",
+      "source": "./",
+      "description": "Run focus sessions. Skills only: no hooks, MCP servers, or external services.",
+      "version": "1.1.0"
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
index d672c1a..a6743c9 100644
--- a/README.md
+++ b/README.md
@@ -1,3 +1,26 @@
 # focus-timer
 
 A Claude Code plugin that runs focus sessions.
+
+## Install
+
+This repository is its own marketplace, named `focus-timer`.
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
+Claude Code: `claude plugin marketplace update focus-timer`, then `claude plugin update focus-timer@focus-timer`.
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
index 0000000..86b412e
--- /dev/null
+++ b/plugin.json
@@ -0,0 +1,9 @@
+{
+  "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
+  "name": "focus-timer",
+  "version": "1.1.0",
+  "description": "Run focus sessions",
+  "author": {
+    "name": "Acme"
+  }
+}
```

## Repository refs

Every branch and tag in the final repository, each with its changes against the fixture tree (`refs.txt`).

```text
master 1522a01
```
