# Run: scenario 4, repetition 8, with-skill

Scored against `tests/scenarios.md` as of this commit; cost is `metrics` in the manifest.

## Manifest

```json
{
  "date": "2026-09-28",
  "arm": "with-skill",
  "scenario": "s4",
  "rep": 8,
  "fixture_tree": "5636a130e9dfed2c78f60f0a2718f62fef2c7d5c",
  "upstream_commits": null,
  "tools": {
    "claude": "2.1.284 (Claude Code)",
    "codex": "codex-cli 0.157.1",
    "copilot": "GitHub Copilot CLI 1.0.89."
  },
  "session_context": "dispatched from a Claude Code session (claude 2.1.284) with installed plugins including superpowers, plugin-dev, amicus, astral, obsidian, pr-review-toolkit, code-review, skill-creator, mcp-server-dev, claude-code-setup; user skills include agent-bot-identity, review-pr, fastmcp, prek, separating-context-from-constraints; the plugin-marketplaces skill reaches arms only through the run's skill copy (refinement round 1)",
  "prompt_file": "prompt.txt",
  "skill": "$RUN/skill/plugin-marketplaces",
  "validator": "$RUN/validator/bin/check-marketplace",
  "skill_tree": "6578ee9f85fa202a3ccb74c0ddffde54ef9fd429",
  "transcript": "a5baf6622629ca310.output",
  "model": "claude-opus-5-5",
  "metrics": {
    "tool_calls": 12,
    "wall_seconds": 131.2
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

Make review-kit available to Codex and GitHub Copilot CLI users too, without breaking it for Claude Code users.
Tell me what will and won't work in each tool.
```

## Isolation

Flags raised by `tests/eval/isolation.py` (tests/scenarios.md, How to run, step 5):

```text
after the run symlink-outside: $RUN/repo/.tool-homes/before/codex/tmp/arg0/codex-arg0i09gAE/applypatch -> /opt/homebrew/lib/node_modules/@openai/codex/node_modules/@openai/codex-darwin-arm64/vendor/aarch64-apple-darwin/bin/codex
after the run symlink-outside: $RUN/repo/.tool-homes/before/codex/tmp/arg0/codex-arg0i09gAE/apply_patch -> /opt/homebrew/lib/node_modules/@openai/codex/node_modules/@openai/codex-darwin-arm64/vendor/aarch64-apple-darwin/bin/codex
after the run symlink-outside: $RUN/repo/.tool-homes/before/codex/tmp/arg0/codex-arg0i09gAE/codex-execve-wrapper -> /opt/homebrew/lib/node_modules/@openai/codex/node_modules/@openai/codex-darwin-arm64/vendor/aarch64-apple-darwin/bin/codex
```

Batch 7, refinement round 1 (skill tree 6578ee9). Every tool call scanned; flagged and risky calls read in full; no violation (plan-2c ledger).

## Score

| Criterion | Result | Evidence |
| --- | --- | --- |
| 1 | pass | objective.json shows `claude.errors: []`. `.claude-plugin/plugin.json` is byte-identical to the original (`diff` printed SAME), so it still relies on the same default paths. |
| 2 | pass | objective.json shows `codex.listed: ["review-kit"]` and `copilot.listed: ["review-kit"]`. |
| 3 | pass | In report.md's table, the `reviewer` agent in Codex is "won't load" and the API key prompt (the plugin's `userConfig` api_key) in Codex is "no prompt". The "What changed" section also says the portable format "has no way to prompt for one". |
| 4 | pass | In the diff, `commands/review.md` is renamed to `skills/review/SKILL.md`. report.md lists the "`review` skill (was the `/review` command)" for Codex as "should work; it was installed". It does not call it unsupported. |
| 5 | fail | report.md has a Checks section with run and not-run items. But it states tool behaviour it neither observed nor cited, for example "Once a root `plugin.json` exists, Codex and Copilot CLI stop reading `commands/`", "Codex reads this one before the Claude catalog", and "Codex could run the hook if it were declared under `extensions["com.openai"].hooks`". tool-calls.jsonl shows no probe of any of these. |

Total: 4 of 5 passed.

## Final report

review-kit can now be installed from Codex and GitHub Copilot CLI, and Claude Code users get the same components as before. I checked this in all three tools (claude 2.1.284, codex-cli 0.157.1, copilot 1.0.89) using throwaway config under `.tool-homes/` and a clean export of the repo, with outbound network blocked. I didn't open any model session or run any plugin code.

The changes are staged but not committed, in `$RUN/repo`. I added `.tool-homes/` to `.git/info/exclude`.

## What changed
- **`plugin.json`** (new, repo root): the portable manifest that Codex and Copilot CLI read. Version 2.0.0, the same as `.claude-plugin/plugin.json`.
- **`mcp.json`** (new): the same `review` server as `.mcp.json`, started as `sh ${PLUGIN_ROOT}/server/run.sh`. It passes no API key, because the portable format has no way to prompt for one and says secrets must not go in its config.
- **`skills/review/SKILL.md`**: this is `commands/review.md`, moved with `git mv`, plus `name: review` in its frontmatter. Once a root `plugin.json` exists, Codex and Copilot CLI stop reading `commands/`. As a skill it reaches all three tools, and Claude Code still lists it exactly as it did before.
- **`.agents/plugins/marketplace.json`** (new): the Codex catalog. Codex reads this one before the Claude catalog.
- **`.claude-plugin/marketplace.json`**: now read by Claude Code and Copilot CLI. I added a description to its entry. It's the same in both catalogs and says the plugin runs a local MCP server (`python3`) that uses a review-service API key, and a SessionStart hook in Claude Code.
- **`marketplace-policy.json`** (new): lists all three tools as targets.
- **`README.md`**: install commands for each tool and a what-works-where table.
- I deleted nothing that Claude Code reads. `.claude-plugin/plugin.json`, `.mcp.json`, `agents/` and `hooks/` are untouched.

## What will and won't work
| | Claude Code | Codex | Copilot CLI |
|---|---|---|---|
| `review` skill (was the `/review` command) | works (checked) | should work; it was installed, but I didn't see it load | works (`copilot skill list` shows it) |
| `reviewer` agent | works (checked) | won't load | not verified |
| SessionStart hook | works (checked) | won't run | not verified |
| `review` MCP server | configured as before (checked) | configured with the real path (checked) | configured (checked) |
| API key prompt | works | no prompt | no prompt |

- **Loaded but not seen in Codex:** The `review` skill was copied into Codex's plugin folder, but the only command that shows loaded skills also starts the MCP server, so I didn't run it. Its status rests on the skill's reference docs.
- **Hooks in Codex:** Codex could run the hook if it were declared under `extensions["com.openai"].hooks` in `plugin.json`. I didn't add that because I couldn't confirm the format.
- **Agent and hook in Copilot CLI:** No Copilot command shows whether they loaded.
- **MCP path in Copilot CLI:** `copilot mcp get review` displays `${PLUGIN_ROOT}` unexpanded. The skill's references say it is expanded when the server starts, but I didn't see that myself.
- **API key in Codex and Copilot CLI:** There's no prompt, so users would have to set `REVIEW_API_KEY` in their own environment. Whether the tool passes it to the server is unverified. For Codex it looks likely not to: `codex mcp list` shows `env_vars: []`, so the user may need to allow the variable in Codex's config.
- **In all three tools:** the MCP server needs `python3` and the `review_server` module.

## Checks
- **Schema:** passed. The validator (`check-marketplace`) passed its parse, policy and portable-format checks, and `claude plugin validate --strict` on the catalog gave 0 errors and 0 warnings. The validator's own Claude run was inconclusive because the repo root is both a marketplace and a plugin, so Claude's validator didn't check the plugin's skills, agents, hooks or MCP files there. I confirmed the validator can fail: when I changed the version in `plugin.json` to 2.0.1 in a scratch copy, it reported the mismatch.
- **Local:** passed. Versions, paths, names and catalog parity all agree.
- **Remote:** not run. Both catalogs point at the repo itself, so there's nothing remote to check.
- **Discovery:** passed in all three tools. Claude Code added the marketplace, Codex listed the plugin as available at version 2.0.0, and Copilot CLI accepted the catalog and listed the plugin.
- **Package load:**
  - **Claude Code:** passed. `claude plugin details` shows the same inventory before and after the change: 1 skill (`review`), 1 agent, 1 SessionStart hook, 1 MCP server, version 2.0.0.
  - **Codex:** partly checked. Install passed at 2.0.0, and `codex mcp list` shows `sh <install dir>/server/run.sh`. Skills and agents weren't observed, for the reason above.
  - **Copilot CLI:** partly checked. Install passed ("Installed 1 skill.", v2.0.0), and the skill and the `review` server are listed. Agent and hook status is unknown.

For future releases, the version has to change in both `plugin.json` and `.claude-plugin/plugin.json`, and the servers in `mcp.json` and `.mcp.json` have to stay in step.

## Tool calls

The arm's tool calls, one JSON object per line, extracted from its transcript.

```jsonl
{"tool": "Bash", "input": {"command": "cd $RUN/repo && git status && git log --oneline | head && find . -path ./.git -prune -o -type f -print | head -100; cat $RUN/skill/plugin-marketplaces/SKILL.md; ls -R $RUN/skill/plugin-marketplaces"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && for f in .mcp.json README.md agents/reviewer.md server/run.sh hooks/hooks.json scripts/start.sh .claude-plugin/marketplace.json .claude-plugin/plugin.json commands/review.md; do echo \"=== $f\"; cat $f; done; ls -la server scripts"}}
{"tool": "Bash", "input": {"command": "cd $RUN/skill/plugin-marketplaces/references && cat multi-tool.md feature-matrix.md agent-plugins.md"}}
{"tool": "Bash", "input": {"command": "cd $RUN/skill/plugin-marketplaces/references && cat validation.md releases.md codex.md copilot-cli.md"}}
{"tool": "Bash", "input": {"command": "cd $RUN/skill/plugin-marketplaces/scripts/mpcheck && cat policy.py data/readers.json | head -250; grep -n \"policy\" ../../references/*.md | head -30; which claude codex copilot; "}}
{"tool": "Bash", "input": {"command": "cd $RUN/skill/plugin-marketplaces/references && sed -n 1,200p claude-code.md | grep -n -i -E \"skill|command|userConfig|sensitive|mcp\" | head -30"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=\"$PWD/.tool-homes/before\" && mkdir -p \"$T\"/{home,xdg,tmp,claude,codex,copilot,copilot-cache,export} && : > \"$T/gitconfig\" && git archive HEAD | tar -x -C \"$T/export\" && export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\" && echo .tool-homes/ >> .git/info/exclude && S='(version 1)(allow default)(deny network-outbound (remote ip))' && claude --version </dev/null; codex --version </dev/null; copilot --version </dev/null; sandbox-exec -p \"$S\" claude plugin marketplace add \"$T/export\" </dev/null; sandbox-exec -p \"$S\" claude plugin install review-kit@review-kit </dev/null; sandbox-exec -p \"$S\" claude plugin details review-kit@review-kit </dev/null"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && mkdir -p skills/review .agents/plugins && git mv commands/review.md skills/review/SKILL.md && cat > skills/review/SKILL.md <<'EOF'\n---\nname: review\ndescription: Review the current diff\n---\n\nReview the staged diff and list problems.\nEOF\ncat > plugin.json <<'EOF'\n{\n  \"$schema\": \"https://agent-plugins.org/schemas/1.0.0/plugin.schema.json\",\n  \"name\": \"review-kit\",\n  \"version\": \"2.0.0\",\n  \"description\": \"Code review helpers\",\n  \"author\": {\n    \"name\": \"Acme\"\n  }\n}\nEOF\ncat > mcp.json <<'EOF'\n{\n  \"$schema\": \"https://agent-plugins.org/schemas/1.0.0/mcp.schema.json\",\n  \"mcpServers\": {\n    \"review\": {\n      \"type\": \"stdio\",\n      \"command\": \"sh\",\n      \"args\": [\"${PLUGIN_ROOT}/server/run.sh\"]\n    }\n  }\n}\nEOF\ncat > marketplace-policy.json <<'EOF'\n{\n  \"readers\": [\"claude-code\", \"codex\", \"copilot-cli\"]\n}\nEOF\nDESC=\"Code review helpers: a review skill and a reviewer agent. Runs a local MCP server (server/run.sh, python3 -m review_server) that uses a review service API key, and in Claude Code a SessionStart hook (scripts/start.sh).\"\npython3 - \"$DESC\" <<'EOF'\nimport json,sys\nd=sys.argv[1]\np=\".claude-plugin/marketplace.json\"\nm=json.load(open(p))\nm[\"plugins\"][0][\"description\"]=d\njson.dump(m,open(p,\"w\"),indent=2); open(p,\"a\").write(\"\\n\")\ncodex={\"name\":\"review-kit\",\"interface\":{\"displayName\":\"review-kit\"},\"plugins\":[{\"name\":\"review-kit\",\"source\":{\"source\":\"local\",\"path\":\"./\"},\"description\":d,\"policy\":{\"installation\":\"AVAILABLE\",\"authentication\":\"ON_INSTALL\"},\"category\":\"Coding\"}]}\njson.dump(codex,open(\".agents/plugins/marketplace.json\",\"w\"),indent=2); open(\".agents/plugins/marketplace.json\",\"a\").write(\"\\n\")\nEOF\ncat .claude-plugin/marketplace.json .agents/plugins/marketplace.json; git status --short"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && python3 - <<'EOF'\nimport json\np=\".agents/plugins/marketplace.json\"; m=json.load(open(p)); m.pop(\"interface\")\njson.dump(m,open(p,\"w\"),indent=2); open(p,\"a\").write(\"\\n\")\nEOF\ngit add -A && T=\"$PWD/.tool-homes/val\" && mkdir -p \"$T/tmp\" && TMPDIR=\"$T/tmp\" CLAUDE_CONFIG_DIR=\"$T/claude\" $RUN/validator/bin/check-marketplace . </dev/null; echo exit=$?"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=\"$PWD/.tool-homes/after\" && mkdir -p \"$T\"/{home,xdg,tmp,claude,codex,copilot,copilot-cache,export} && : > \"$T/gitconfig\" && git archive $(git write-tree) | tar -x -C \"$T/export\" && export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\" && S='(version 1)(allow default)(deny network-outbound (remote ip))' && cd \"$T\" && \necho \"== claude validate\"; sandbox-exec -p \"$S\" claude plugin validate \"$T/export\" --strict --json </dev/null\necho \"== claude\"; sandbox-exec -p \"$S\" claude plugin marketplace add \"$T/export\" </dev/null; sandbox-exec -p \"$S\" claude plugin install review-kit@review-kit </dev/null; sandbox-exec -p \"$S\" claude plugin details review-kit@review-kit </dev/null | sed -n 1,12p; sandbox-exec -p \"$S\" claude plugin list --json </dev/null\necho \"== codex\"; sandbox-exec -p \"$S\" codex plugin marketplace add \"$T/export\" </dev/null; sandbox-exec -p \"$S\" codex plugin list --available --json </dev/null; sandbox-exec -p \"$S\" codex plugin add review-kit@review-kit --json </dev/null; sandbox-exec -p \"$S\" codex mcp list --json </dev/null; find \"$T/codex/plugins\" -maxdepth 4\necho \"== copilot\"; sandbox-exec -p \"$S\" copilot plugin marketplace add \"$T/export\" </dev/null; sandbox-exec -p \"$S\" copilot plugin marketplace browse review-kit --json </dev/null; sandbox-exec -p \"$S\" copilot plugin install review-kit@review-kit </dev/null; sandbox-exec -p \"$S\" copilot plugin list </dev/null; sandbox-exec -p \"$S\" copilot skill list </dev/null; sandbox-exec -p \"$S\" copilot mcp list </dev/null; sandbox-exec -p \"$S\" copilot mcp get review </dev/null"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=\"$PWD/.tool-homes/neg\" && mkdir -p \"$T/tmp\" && cp -R .tool-homes/after/export \"$T/copy\" && sed -i '' 's/\"2.0.0\"/\"2.0.1\"/' \"$T/copy/plugin.json\" && TMPDIR=\"$T/tmp\" CLAUDE_CONFIG_DIR=\"$T/claude\" $RUN/validator/bin/check-marketplace \"$T/copy\" </dev/null | grep -v '^ ' ; echo exit=$?; ls -la .tool-homes/before/home .tool-homes/after/home"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && cat > README.md <<'EOF'\n# review-kit\n\nCode review helpers for Claude Code, Codex, and GitHub Copilot CLI.\n\n## Install\n\n- Claude Code: `claude plugin marketplace add <this repo>`, then `claude plugin install review-kit@review-kit`.\n- Codex: `codex plugin marketplace add <this repo>`, then `codex plugin add review-kit@review-kit`.\n- Copilot CLI: `copilot plugin marketplace add <this repo>`, then `copilot plugin install review-kit@review-kit`.\n\n## What works where\n\n| Component | Claude Code | Codex | Copilot CLI |\n| --- | --- | --- | --- |\n| `review` skill (was the `/review` command) | yes | yes | yes |\n| `reviewer` agent | yes | no | not verified |\n| SessionStart hook (`scripts/start.sh`) | yes | no | not verified |\n| `review` MCP server | yes | yes | yes |\n| API key prompt (`userConfig`) | yes | no: set `REVIEW_API_KEY` yourself | no: set `REVIEW_API_KEY` yourself |\n\nThe MCP server runs `python3 -m review_server`, so `python3` and the `review_server` module must be available.\n\n## Layout\n\n- Claude Code reads `.claude-plugin/plugin.json`, `.mcp.json`, and `.claude-plugin/marketplace.json`.\n- Codex reads the Agent Plugins manifest `plugin.json`, `mcp.json`, and `.agents/plugins/marketplace.json`.\n- Copilot CLI reads `plugin.json`, `mcp.json`, and `.claude-plugin/marketplace.json`.\n- Keep `version` equal in `plugin.json` and `.claude-plugin/plugin.json`, and keep the servers in `mcp.json` and `.mcp.json` the same.\nEOF\ngit add -A && git status --short"}}
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
    "marketplace": "review-kit",
    "listed": [
      "review-kit"
    ]
  },
  "copilot": {
    "ran": true,
    "added": true,
    "marketplace": "review-kit",
    "listed": [
      "review-kit"
    ]
  }
}
```

## Diff

```diff
diff --git a/.agents/plugins/marketplace.json b/.agents/plugins/marketplace.json
new file mode 100644
index 0000000..582f5e7
--- /dev/null
+++ b/.agents/plugins/marketplace.json
@@ -0,0 +1,18 @@
+{
+  "name": "review-kit",
+  "plugins": [
+    {
+      "name": "review-kit",
+      "source": {
+        "source": "local",
+        "path": "./"
+      },
+      "description": "Code review helpers: a review skill and a reviewer agent. Runs a local MCP server (server/run.sh, python3 -m review_server) that uses a review service API key, and in Claude Code a SessionStart hook (scripts/start.sh).",
+      "policy": {
+        "installation": "AVAILABLE",
+        "authentication": "ON_INSTALL"
+      },
+      "category": "Coding"
+    }
+  ]
+}
diff --git a/.claude-plugin/marketplace.json b/.claude-plugin/marketplace.json
index a015458..954f857 100644
--- a/.claude-plugin/marketplace.json
+++ b/.claude-plugin/marketplace.json
@@ -7,7 +7,8 @@
   "plugins": [
     {
       "name": "review-kit",
-      "source": "./"
+      "source": "./",
+      "description": "Code review helpers: a review skill and a reviewer agent. Runs a local MCP server (server/run.sh, python3 -m review_server) that uses a review service API key, and in Claude Code a SessionStart hook (scripts/start.sh)."
     }
   ]
 }
diff --git a/README.md b/README.md
index 9246da6..5a5db75 100644
--- a/README.md
+++ b/README.md
@@ -1,3 +1,28 @@
 # review-kit
 
-Code review helpers for Claude Code.
+Code review helpers for Claude Code, Codex, and GitHub Copilot CLI.
+
+## Install
+
+- Claude Code: `claude plugin marketplace add <this repo>`, then `claude plugin install review-kit@review-kit`.
+- Codex: `codex plugin marketplace add <this repo>`, then `codex plugin add review-kit@review-kit`.
+- Copilot CLI: `copilot plugin marketplace add <this repo>`, then `copilot plugin install review-kit@review-kit`.
+
+## What works where
+
+| Component | Claude Code | Codex | Copilot CLI |
+| --- | --- | --- | --- |
+| `review` skill (was the `/review` command) | yes | yes | yes |
+| `reviewer` agent | yes | no | not verified |
+| SessionStart hook (`scripts/start.sh`) | yes | no | not verified |
+| `review` MCP server | yes | yes | yes |
+| API key prompt (`userConfig`) | yes | no: set `REVIEW_API_KEY` yourself | no: set `REVIEW_API_KEY` yourself |
+
+The MCP server runs `python3 -m review_server`, so `python3` and the `review_server` module must be available.
+
+## Layout
+
+- Claude Code reads `.claude-plugin/plugin.json`, `.mcp.json`, and `.claude-plugin/marketplace.json`.
+- Codex reads the Agent Plugins manifest `plugin.json`, `mcp.json`, and `.agents/plugins/marketplace.json`.
+- Copilot CLI reads `plugin.json`, `mcp.json`, and `.claude-plugin/marketplace.json`.
+- Keep `version` equal in `plugin.json` and `.claude-plugin/plugin.json`, and keep the servers in `mcp.json` and `.mcp.json` the same.
diff --git a/marketplace-policy.json b/marketplace-policy.json
new file mode 100644
index 0000000..c274060
--- /dev/null
+++ b/marketplace-policy.json
@@ -0,0 +1,3 @@
+{
+  "readers": ["claude-code", "codex", "copilot-cli"]
+}
diff --git a/mcp.json b/mcp.json
new file mode 100644
index 0000000..b1208fc
--- /dev/null
+++ b/mcp.json
@@ -0,0 +1,10 @@
+{
+  "$schema": "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json",
+  "mcpServers": {
+    "review": {
+      "type": "stdio",
+      "command": "sh",
+      "args": ["${PLUGIN_ROOT}/server/run.sh"]
+    }
+  }
+}
diff --git a/plugin.json b/plugin.json
new file mode 100644
index 0000000..db6fca3
--- /dev/null
+++ b/plugin.json
@@ -0,0 +1,9 @@
+{
+  "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
+  "name": "review-kit",
+  "version": "2.0.0",
+  "description": "Code review helpers",
+  "author": {
+    "name": "Acme"
+  }
+}
diff --git a/commands/review.md b/skills/review/SKILL.md
similarity index 87%
rename from commands/review.md
rename to skills/review/SKILL.md
index 8fc96bb..de1d779 100644
--- a/commands/review.md
+++ b/skills/review/SKILL.md
@@ -1,4 +1,5 @@
 ---
+name: review
 description: Review the current diff
 ---
```

## Repository refs

Every branch and tag in the final repository, each with its changes against the fixture tree (`refs.txt`).

```text
master 099f32d
```
