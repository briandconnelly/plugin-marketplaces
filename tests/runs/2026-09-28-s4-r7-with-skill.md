# Run: scenario 4, repetition 7, with-skill

Scored against `tests/scenarios.md` as of this commit; cost is `metrics` in the manifest.

## Manifest

```json
{
  "date": "2026-09-28",
  "arm": "with-skill",
  "scenario": "s4",
  "rep": 7,
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
  "transcript": "aa12243e4b74bd6f1.output",
  "model": "claude-opus-5-5",
  "metrics": {
    "tool_calls": 16,
    "wall_seconds": 170.2
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
(none)
```

Batch 6, refinement round 1 (skill tree 6578ee9). Every tool call scanned and every flagged or remote-URL call read in full; no violation. github.com URLs were rewritten by throwaway insteadOf rules to the run's own mirror (plan-2c ledger).

## Score

| Criterion | Result | Evidence |
| --- | --- | --- |
| 1 | pass | `objective.json` shows `claude.errors: []`. `.claude-plugin/plugin.json` is not in `diff.patch` and is byte-identical to the original, so it declares the same defaults as before; the report says `claude plugin details` shows "1 skill, 1 agent, 1 hook, 1 MCP server". |
| 2 | pass | `objective.json` has `codex.listed: ["review-kit"]` and `copilot.listed: ["review-kit"]`. |
| 3 | pass | In `report.md`, the table row for the `reviewer` agent says Codex "no (Codex doesn't load agents)", and the `userConfig` row says Codex "no". |
| 4 | pass | `report.md` says `review` was "moved from `commands/review.md`" to `skills/review/SKILL.md` (the rename is in `diff.patch`), and the Codex column reads "yes, per the skill's references". The agent converted the command itself, so the report does not call it unsupported. |
| 5 | pass | `report.md` has a "Check results" table and a "Not run" list (`codex debug prompt-input`, agent and hook checks in Codex and Copilot CLI, a live MCP start). Behaviour it did not observe is marked "not observed", "unknown" or "unconfirmed", or comes from the skill references it read (`tool-calls.jsonl` shows it read feature-matrix.md, multi-tool.md and codex.md, which state these facts). |

Total: 5 of 5 passed.

## Final report

review-kit now installs in Claude Code, Codex and GitHub Copilot CLI from the same repository. It installed cleanly in all three isolated test setups (throwaway config, network blocked), and Claude Code shows exactly the same components it did before. Nothing is committed; all changes are in the working tree of `$RUN/repo`.

## What works where

| Part of review-kit | Claude Code | Codex | Copilot CLI |
| --- | --- | --- | --- |
| `review` (was a command, now a skill) | yes (checked) | yes, per the skill's references; no safe command shows it | yes (checked: listed as a skill) |
| `reviewer` agent | yes (checked) | no (Codex doesn't load agents) | unknown: no command shows agents |
| SessionStart hook (`scripts/start.sh`) | yes (checked) | no | no; no command shows hooks, so this is not observed |
| `review` MCP server | yes (checked) | set up with the real plugin path (checked) | set up (checked), but `${PLUGIN_ROOT}` is shown unexpanded, so whether it gets the real path is unconfirmed |
| API key setting (`userConfig`) | yes (checked; install says it still needs a value) | no | no |

- **API key:** in Codex and Copilot CLI the MCP server never receives `REVIEW_API_KEY`. The portable format has no settings feature and says secrets shouldn't go in `env`.
- **Existing problem:** `server/run.sh` runs `python3 -m review_server`, but that module isn't in the repo. The server can only start where it's installed separately, in every tool including Claude Code.

## What changed

- **`plugin.json` and `mcp.json`** (new, in the repo root): the portable manifest (`review-kit`, version 2.0.0) that Codex and Copilot CLI read. The server runs as `sh ${PLUGIN_ROOT}/server/run.sh`.
  - Claude Code ignores this pair, so the Claude files are unchanged.
  - Keep `name`, `version` and the server list the same in both pairs.
- **`skills/review/SKILL.md`**: moved from `commands/review.md`, with the same text plus `name: review`.
  - Once the portable manifest exists, Codex and Copilot CLI stop reading `commands/`, so without the move `/review` would have disappeared for them.
  - Claude Code lists the same components as before (checked).
  - One Claude Code difference: as a skill, `review` can now be picked by the model on its own, not only when the user types it.
- **`.agents/plugins/marketplace.json`** (new): a Codex catalog with the same single `./` entry. Copilot CLI keeps reading `.claude-plugin/marketplace.json`.
- **`marketplace-policy.json`** (new): lists Claude Code, Codex and Copilot CLI as the tools this marketplace targets.
- **Both catalogs:** the entry description now says the plugin includes a hook, a local MCP server and an external service that needs a key, and which parts are Claude Code only.
- **`README.md`**: install steps for each tool and the table above.

## Check results

Tool versions matched the ones the skill's references were checked against: claude 2.1.284, codex-cli 0.157.1, copilot 1.0.89.

| Check | Result |
| --- | --- |
| Format (the skill's `check-marketplace` validator) | passed, exit 0 |
| Format (`claude plugin validate --strict`) | passed, 0 errors and 0 warnings |
| Rules (paths, names, versions, catalogs agreeing) | passed, `check-marketplace` |
| Remote | not applicable: there are no remote sources |
| Listing: Claude Code | marketplace added, plugin installed |
| Listing: Codex | plugin listed as `review-kit@review-kit` 2.0.0 |
| Listing: Copilot CLI | marketplace added; plugin appears in browse |
| Loading: Claude Code | `claude plugin details`: 1 skill, 1 agent, 1 hook, 1 MCP server, the same as before the change |
| Loading: Codex | installed 2.0.0; `codex mcp list` shows the server with the plugin path filled in |
| Loading: Copilot CLI | "Installed 1 skill", version 2.0.0, enabled; `copilot mcp get review` shows the server with `${PLUGIN_ROOT}` unexpanded |

**Not run:**
- `codex debug prompt-input` (the only way to see Codex's skills), because it would start the plugin's own server code.
- Any check of agents or hooks in Codex or Copilot CLI, because no command shows them.
- A live MCP server start in any tool.

## Left for you to decide

- **Codex hook:** Codex can run hooks from an `extensions["com.openai"].hooks` field in `plugin.json`, but I couldn't confirm what that field should look like, so I didn't add it.
- **Copilot MCP path:** changing the server to `sh -c 'exec "$PLUGIN_ROOT/server/run.sh"'` would work whether or not Copilot CLI expands `${PLUGIN_ROOT}`. I kept the documented form.
- **Committing:** I haven't committed anything; say if you want it committed.

## Tool calls

The arm's tool calls, one JSON object per line, extracted from its transcript.

```jsonl
{"tool": "Bash", "input": {"command": "cd $RUN/repo && cat $RUN/skill/plugin-marketplaces/SKILL.md && ls -R $RUN/skill/plugin-marketplaces && git status && git log --oneline | head && find . -path ./.git -prune -o -type f -print"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && for f in .mcp.json README.md agents/reviewer.md server/run.sh hooks/hooks.json scripts/start.sh .claude-plugin/marketplace.json .claude-plugin/plugin.json commands/review.md; do echo \"=== $f\"; cat $f; done; ls -la server scripts"}}
{"tool": "Bash", "input": {"command": "cd $RUN/skill/plugin-marketplaces/references && cat multi-tool.md feature-matrix.md"}}
{"tool": "Bash", "input": {"command": "cd $RUN/skill/plugin-marketplaces/references && cat agent-plugins.md validation.md releases.md"}}
{"tool": "Bash", "input": {"command": "cd $RUN/skill/plugin-marketplaces/references && cat codex.md copilot-cli.md claude-code.md"}}
{"tool": "Bash", "input": {"command": "cd $RUN/skill/plugin-marketplaces/references && cat codex.md copilot-cli.md"}}
{"tool": "Bash", "input": {"command": "cd $RUN/skill/plugin-marketplaces && cat references/claude-code.md; cat scripts/mpcheck/policy.py | head -150; grep -rn \"com.openai\" -r . | head -30; which claude codex copilot git python3"}}
{"tool": "Bash", "input": {"command": "cd $RUN/skill/plugin-marketplaces && head -c 1500 scripts/mpcheck/data/readers.json; echo; sed -n 150,260p scripts/mpcheck/policy.py; cat references/freshness.md | head -40"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=\"$PWD/.tool-homes\" && mkdir -p \"$T\"/{home,xdg,tmp,claude,codex,copilot,copilot-cache} && : > \"$T/gitconfig\" && export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\" && claude --version </dev/null; codex --version </dev/null; copilot --version </dev/null; cat .gitignore 2>/dev/null; echo; git check-ignore .tool-homes || echo notignored"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && mkdir -p skills/review .agents/plugins && git mv commands/review.md skills/review/SKILL.md && cat > skills/review/SKILL.md <<'EOF'\n---\nname: review\ndescription: Review the current diff\n---\n\nReview the staged diff and list problems.\nEOF\ncat > plugin.json <<'EOF'\n{\n  \"$schema\": \"https://agent-plugins.org/schemas/1.0.0/plugin.schema.json\",\n  \"name\": \"review-kit\",\n  \"version\": \"2.0.0\",\n  \"description\": \"Code review helpers\",\n  \"author\": {\n    \"name\": \"Acme\"\n  }\n}\nEOF\ncat > mcp.json <<'EOF'\n{\n  \"$schema\": \"https://agent-plugins.org/schemas/1.0.0/mcp.schema.json\",\n  \"mcpServers\": {\n    \"review\": {\n      \"type\": \"stdio\",\n      \"command\": \"sh\",\n      \"args\": [\"${PLUGIN_ROOT}/server/run.sh\"]\n    }\n  }\n}\nEOF\nDESC=\"Code review helpers: a review skill, a reviewer agent (Claude Code only), a SessionStart hook that runs scripts/start.sh (Claude Code only), and a local MCP server (server/run.sh, runs python3 -m review_server) that uses a review service API key.\"\npython3 - \"$DESC\" <<'EOF'\nimport json,sys\nd=sys.argv[1]\np='.claude-plugin/marketplace.json'\nm=json.load(open(p)); m['plugins'][0]['description']=d\nopen(p,'w').write(json.dumps(m,indent=2)+\"\\n\")\na={\"name\":\"review-kit\",\"interface\":{\"displayName\":\"review-kit\"},\"plugins\":[{\"name\":\"review-kit\",\"source\":{\"source\":\"local\",\"path\":\"./\"},\"description\":d,\"policy\":{\"installation\":\"AVAILABLE\",\"authentication\":\"ON_INSTALL\"},\"category\":\"Coding\"}]}\nopen('.agents/plugins/marketplace.json','w').write(json.dumps(a,indent=2)+\"\\n\")\nEOF\ncat > marketplace-policy.json <<'EOF'\n{\n  \"readers\": [\"claude-code\", \"codex\", \"copilot-cli\"]\n}\nEOF\ncat .claude-plugin/marketplace.json .agents/plugins/marketplace.json"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && python3 - <<'EOF'\nimport json\np='.agents/plugins/marketplace.json'\nm=json.load(open(p)); del m['interface']\nopen(p,'w').write(json.dumps(m,indent=2)+\"\\n\")\nEOF\nT=\"$PWD/.tool-homes\"; export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\"; $RUN/validator/bin/check-marketplace . ; echo exit=$?"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=\"$PWD/.tool-homes\"; rm -rf \"$T/export\"; mkdir -p \"$T/export\"; git ls-files -co --exclude-standard | grep -v '^commands/' | while read f; do [ -e \"$f\" ] && mkdir -p \"$T/export/$(dirname \"$f\")\" && cp -p \"$f\" \"$T/export/$f\"; done; find \"$T/export\" -type f | sort; cd \"$T/export\" && git init -q && git add -A && git -c user.name=t -c user.email=t@t commit -qm export && echo committed\nexport HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\"\nSB='(version 1)(allow default)(deny network-outbound (remote ip))'\necho \"== claude validate\"; sandbox-exec -p \"$SB\" claude plugin validate \"$T/export\" --strict --json </dev/null; echo exit=$?\necho \"== claude add\"; sandbox-exec -p \"$SB\" claude plugin marketplace add \"$T/export\" </dev/null; echo exit=$?\necho \"== claude install\"; sandbox-exec -p \"$SB\" claude plugin install review-kit@review-kit </dev/null; echo exit=$?\necho \"== claude details\"; sandbox-exec -p \"$SB\" claude plugin details review-kit@review-kit </dev/null; echo exit=$?\necho \"== claude list\"; sandbox-exec -p \"$SB\" claude plugin list --json </dev/null"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=\"$PWD/.tool-homes\"; export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\"\nSB='(version 1)(allow default)(deny network-outbound (remote ip))'\necho \"== codex add\"; sandbox-exec -p \"$SB\" codex plugin marketplace add \"$T/export\" </dev/null; echo exit=$?\necho \"== codex list\"; sandbox-exec -p \"$SB\" codex plugin list --available --json </dev/null; echo exit=$?\necho \"== codex install\"; sandbox-exec -p \"$SB\" codex plugin add review-kit@review-kit --json </dev/null; echo exit=$?\necho \"== codex mcp\"; sandbox-exec -p \"$SB\" codex mcp list --json </dev/null; echo exit=$?\nfind \"$T/codex/plugins/cache\" -maxdepth 5 | head -30"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=\"$PWD/.tool-homes\"; export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\"\nSB='(version 1)(allow default)(deny network-outbound (remote ip))'\necho \"== add\"; sandbox-exec -p \"$SB\" copilot plugin marketplace add \"$T/export\" </dev/null; echo exit=$?\necho \"== browse\"; sandbox-exec -p \"$SB\" copilot plugin marketplace browse review-kit --json </dev/null; echo exit=$?\necho \"== install\"; sandbox-exec -p \"$SB\" copilot plugin install review-kit@review-kit </dev/null; echo exit=$?\necho \"== list\"; sandbox-exec -p \"$SB\" copilot plugin list </dev/null; echo exit=$?\necho \"== skills\"; sandbox-exec -p \"$SB\" copilot skill list </dev/null; echo exit=$?\necho \"== mcp\"; sandbox-exec -p \"$SB\" copilot mcp list </dev/null; sandbox-exec -p \"$SB\" copilot mcp get review </dev/null; echo exit=$?"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=\"$PWD/.tool-homes\"; rm -rf \"$T/base\" \"$T/claude-base\"; mkdir -p \"$T/base\" \"$T/claude-base\"; git archive HEAD | tar -x -C \"$T/base\"; (cd \"$T/base\" && git init -q && git add -A && git -c user.name=t -c user.email=t@t commit -qm base)\nexport HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude-base\"\nSB='(version 1)(allow default)(deny network-outbound (remote ip))'\nsandbox-exec -p \"$SB\" claude plugin marketplace add \"$T/base\" </dev/null >/dev/null; sandbox-exec -p \"$SB\" claude plugin install review-kit@review-kit </dev/null >/dev/null; sandbox-exec -p \"$SB\" claude plugin details review-kit@review-kit </dev/null | sed -n 1,12p"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && cat > README.md <<'EOF'\n# review-kit\n\nCode review helpers for Claude Code, Codex, and GitHub Copilot CLI.\n\n## Install\n\n- Claude Code: `claude plugin marketplace add <this repo>`, then `claude plugin install review-kit@review-kit`.\n- Codex: `codex plugin marketplace add <this repo>`, then `codex plugin add review-kit@review-kit`.\n- Copilot CLI: `copilot plugin marketplace add <this repo>`, then `copilot plugin install review-kit@review-kit`.\n\n## What works where\n\n| Component | Claude Code | Codex | Copilot CLI |\n| --- | --- | --- | --- |\n| `review` skill | yes | yes | yes |\n| `reviewer` agent | yes | no | not verified |\n| SessionStart hook (`scripts/start.sh`) | yes | no | no |\n| `review` MCP server | yes | yes, without the API key | yes, without the API key |\n| API key prompt (`userConfig`) | yes | no | no |\n\nClaude Code reads `.claude-plugin/plugin.json` and `.mcp.json`; Codex and Copilot CLI read the portable `plugin.json` and `mcp.json` (Agent Plugins 1.0).\nKeep `name`, `version`, and the MCP server list the same in both pairs.\nIn Codex and Copilot CLI the MCP server does not receive `REVIEW_API_KEY` from the plugin.\nThe MCP server runs `python3 -m review_server`, which this repository does not ship; it must be installed separately in every tool.\nEOF\nT=\"$PWD/.tool-homes\"; export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" CLAUDE_CONFIG_DIR=\"$T/claude\"; $RUN/validator/bin/check-marketplace . ; echo exit=$?; git status --short"}}
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
index 0000000..888538c
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
+      "description": "Code review helpers: a review skill, a reviewer agent (Claude Code only), a SessionStart hook that runs scripts/start.sh (Claude Code only), and a local MCP server (server/run.sh, runs python3 -m review_server) that uses a review service API key.",
+      "policy": {
+        "installation": "AVAILABLE",
+        "authentication": "ON_INSTALL"
+      },
+      "category": "Coding"
+    }
+  ]
+}
diff --git a/.claude-plugin/marketplace.json b/.claude-plugin/marketplace.json
index a015458..958a11c 100644
--- a/.claude-plugin/marketplace.json
+++ b/.claude-plugin/marketplace.json
@@ -7,7 +7,8 @@
   "plugins": [
     {
       "name": "review-kit",
-      "source": "./"
+      "source": "./",
+      "description": "Code review helpers: a review skill, a reviewer agent (Claude Code only), a SessionStart hook that runs scripts/start.sh (Claude Code only), and a local MCP server (server/run.sh, runs python3 -m review_server) that uses a review service API key."
     }
   ]
 }
diff --git a/README.md b/README.md
index 9246da6..438aa41 100644
--- a/README.md
+++ b/README.md
@@ -1,3 +1,24 @@
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
+| `review` skill | yes | yes | yes |
+| `reviewer` agent | yes | no | not verified |
+| SessionStart hook (`scripts/start.sh`) | yes | no | no |
+| `review` MCP server | yes | yes, without the API key | yes, without the API key |
+| API key prompt (`userConfig`) | yes | no | no |
+
+Claude Code reads `.claude-plugin/plugin.json` and `.mcp.json`; Codex and Copilot CLI read the portable `plugin.json` and `mcp.json` (Agent Plugins 1.0).
+Keep `name`, `version`, and the MCP server list the same in both pairs.
+In Codex and Copilot CLI the MCP server does not receive `REVIEW_API_KEY` from the plugin.
+The MCP server runs `python3 -m review_server`, which this repository does not ship; it must be installed separately in every tool.
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
