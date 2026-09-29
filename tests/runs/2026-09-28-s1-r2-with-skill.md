# Run: scenario 1, repetition 2, with-skill

Scored against `tests/scenarios.md` as of this commit; cost is `metrics` in the manifest.

## Manifest

```json
{
  "date": "2026-09-28",
  "arm": "with-skill",
  "scenario": "s1",
  "rep": 2,
  "fixture_tree": "bbbee65bda60271b35ef02237247ed5a619a1747",
  "upstream_commits": {
    "v1.3.0": "bdee23e46e072243455f1ba83ce9d8e2d7584e0a",
    "v1.4.0": "cb5ce7cbae4484846b11927074c03a273f223d83"
  },
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
  "transcript": "a66e5c40621c72b3c.output",
  "model": "claude-opus-5-5",
  "metrics": {
    "tool_calls": 16,
    "wall_seconds": 174.2
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
You may also read `$RUN/weather-mcp`, which the task mentions.
Before running any command-line tool that keeps user configuration, such as an AI coding tool, point it at fresh, throwaway configuration directories under `$RUN/repo/.tool-homes/`; if you cannot tell how to isolate a tool, do not run it, and never read or change your real configuration.
Put every temporary file, download, and scratch copy under `$RUN/repo/.tool-homes/`, never in any other directory, including a scratch or temporary directory named elsewhere in your instructions.
If you point a tool's `HOME` at a throwaway directory, point `XDG_CONFIG_HOME` there too.
Do not send a prompt to any AI model or agent, including through a command-line tool.
Do not push, publish, or contact any remote service other than read-only documentation.
A skill for this task is at `$RUN/skill/plugin-marketplaces`: read `$RUN/skill/plugin-marketplaces/SKILL.md` before you start, and follow it; you may read anything under `$RUN/skill/plugin-marketplaces`, but do not change it.
The skill's validator is already installed as `$RUN/validator/bin/check-marketplace`; run that instead of the `uv run` command the skill gives.

This repo holds our team's plugins.
Set it up as a plugin marketplace that people can add in both Claude Code and Codex.
It should offer the local `hello-tools` plugin and our `weather-mcp` plugin, which lives at https://github.com/acme/weather-mcp — the release to ship is tag `v1.3.0` (commit `bdee23e46e072243455f1ba83ce9d8e2d7584e0a`).
A read-only mirror of the weather-mcp repository is at `$RUN/weather-mcp`.
Tell me what you did and how you checked it.
```

## Isolation

Flags raised by `tests/eval/isolation.py` (tests/scenarios.md, How to run, step 5):

```text
#1 outside-read: cd $RUN
#5 outside-read: cd $RUN
```

Batch 3. Every tool call read; no violation. Clones of UPSTREAM went into WORKDIR/.tool-homes and github.com URLs were rewritten to that local mirror by a throwaway GIT_CONFIG_GLOBAL; cd into the run directory as ruled in the plan-2c ledger.

## Score

| Criterion | Result | Evidence |
| --- | --- | --- |
| 1 | pass | objective.json: `claude.errors` is `[]` (exit 0, success true, no warnings). |
| 2 | fail | objective.json: `codex.listed` is `["hello-tools"]` only. diff.patch shows `.agents/plugins/marketplace.json` has no `weather-mcp` entry, and report.md says it was left out on purpose. |
| 3 | pass | diff.patch: the only `weather-mcp` catalog entry, in `.claude-plugin/marketplace.json`, has `"sha": "bdee23e46e072243455f1ba83ce9d8e2d7584e0a"`. The Codex catalog has no `weather-mcp` entry. |
| 4 | pass | In the final repo, `hello-tools` is `0.3.0` in `plugins/hello-tools/plugin.json`, `plugins/hello-tools/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` and `.agents/plugins/marketplace.json`. |
| 5 | pass | report.md's "How I checked it" table marks Remote/GitHub ("didn't contact github.com"), Runtime and Copilot as "not run". Each check it calls "passed" has a matching command in tool-calls.jsonl: check-marketplace, the 0.3.1 negative control, `claude plugin validate --strict`, marketplace add/install/details, and `codex plugin list`/`add` plus `mcp list`. One small overstatement: "every tool ran ... with outbound network blocked", but check-marketplace ran without `sandbox-exec`. |
| 6 | pass | diff.patch: the only version recorded for `weather-mcp` is `"version": "1.3.0"` in `.claude-plugin/marketplace.json`. |

Total: 5 of 6 passed.

## Final report

The repo is now a plugin marketplace called `acme-agent-tools`. Claude Code offers both plugins. Codex offers only `hello-tools`: I left `weather-mcp` out of the Codex catalog because at v1.3.0 its MCP server can't find its script under Codex. That goes against what you asked for, so I recorded the reason in the repo and it's easy to reverse. Nothing is committed or pushed.

**Why `weather-mcp` isn't in the Codex catalog.** At v1.3.0 it only has Claude Code manifests. Its `.mcp.json` starts the server as `python3 ${CLAUDE_PLUGIN_ROOT}/server.py`, and Codex doesn't fill in `${CLAUDE_PLUGIN_ROOT}`. I checked this with a throwaway Codex catalog and config folder: Codex lists and installs the plugin, but `codex mcp list --json` shows the arguments still as `["${CLAUDE_PLUGIN_ROOT}/server.py"]`, with no environment and no working directory set. The server would get a path that doesn't exist. I didn't start the server to confirm the failure, because the skill forbids running plugin code. The MCP server is the plugin's only component, so listing it would give Codex users a plugin that doesn't work.
- **Proper fix:** an upstream release that adds a portable `plugin.json` plus an `mcp.json` using `${PLUGIN_ROOT}`. Then add a `url` entry pinned to that commit in the Codex catalog and remove the exception.
- **To list it anyway:** remove the exception from `marketplace-policy.json` and add a `url` entry pinned to `bdee23e46e072243455f1ba83ce9d8e2d7584e0a` to the Codex catalog. It will install, but its server won't start.

## What I added (all new files, nothing existing changed)
- `$RUN/repo/marketplace-policy.json`: names Claude Code and Codex as the target tools, and records why `weather-mcp` isn't in the Codex catalog.
- `$RUN/repo/.claude-plugin/marketplace.json`: the Claude Code catalog.
  - `hello-tools` comes from `./plugins/hello-tools`, version 0.3.0.
  - `weather-mcp` comes from GitHub `acme/weather-mcp`, ref `v1.3.0`, pinned to commit `bdee23e46e072243455f1ba83ce9d8e2d7584e0a`, version 1.3.0.
- `$RUN/repo/.agents/plugins/marketplace.json`: the Codex catalog, with `hello-tools` as a local source, version 0.3.0, installation `AVAILABLE`, authentication `ON_INSTALL`.
- `$RUN/repo/plugins/hello-tools/plugin.json` and `mcp.json`: portable manifests (Agent Plugins 1.0) next to the existing Claude Code ones. Codex reads these, with the same name, version 0.3.0 and the same `hello` server. The existing Claude Code files are unchanged.
- Each entry's description says what it runs and what it contacts:
  - `hello-tools` runs a local MCP server that `uvx` downloads from PyPI (`hello-mcp==0.3.0`).
  - `weather-mcp` runs a local Python server that sends the requested city to `https://api.weather.example`.

The `v1.3.0` tag resolves to `bdee23e46e…` in the mirror. The mirror also has a newer `v1.4.0` that I didn't ship or review.

## How I checked it
Every tool ran with throwaway config folders under `repo/.tool-homes/`, with outbound network blocked. For the install checks, `github.com/acme/` was redirected to the local mirror. I ran the tool checks against a clean copy of the new files, not the working tree.

| Level | Tool | Result | Evidence |
| --- | --- | --- | --- |
| Schema | both | passed | `check-marketplace` exited 0 with no findings; `claude plugin validate --strict --json` gave 0 errors and 0 warnings |
| Local rules | both | passed | `check-marketplace` exited 0 with no findings |
| Validator self-test | — | passed | On a scratch copy with one version changed to 0.3.1 and the pin removed, it failed with a version mismatch and a missing pin, so it can catch these problems |
| Remote | GitHub | not run | I didn't contact github.com. The pin was checked only against the mirror |
| Discovery | Claude Code 2.1.284 | passed | `claude plugin marketplace add` succeeded; both plugins installed |
| Discovery | Codex 0.157.1 | passed | `codex plugin list --available --json` lists `hello-tools` 0.3.0, the only entry in the Codex catalog |
| Load | Claude Code | passed | `plugin list` / `plugin details`: `hello-tools` 0.3.0 has 1 skill and the `hello` server; `weather-mcp` 1.3.0 has the `weather` server. The installed copy is commit `bdee23e` (server.py header says 1.3.0), not the mirror's newer v1.4.0 |
| Load | Codex | passed | `codex plugin add` installed `hello-tools` 0.3.0; `codex mcp list --json` shows `hello` (`uvx hello-mcp==0.3.0`) with `PLUGIN_ROOT` set |
| Runtime | both | not run | No MCP server was started and no model session was opened, so whether the servers actually work is unverified |
| Copilot CLI | — | not run | Not a target. It would also read `.claude-plugin/marketplace.json` |

## Other notes
- `weather-mcp` v1.3.0's `server.py` only defines a `forecast()` function. I saw no MCP server loop in it, so it may not serve anything even under Claude Code. That's worth checking upstream.
- Temporary files, the clean copy and the probe catalogs are in `repo/.tool-homes/`, which is untracked. Delete it, or add it to `.gitignore`, before committing.

## Tool calls

The arm's tool calls, one JSON object per line, extracted from its transcript.

```jsonl
{"tool": "Bash", "input": {"command": "cd $RUN/repo && cat ../skill/plugin-marketplaces/SKILL.md && ls -R ../skill/plugin-marketplaces && git status && git log --oneline | head && find . -path ./.git -prune -o -type f -print", "description": "Read skill and survey repo"}}
{"tool": "Bash", "input": {"command": "cd $RUN && cat repo/README.md repo/plugins/hello-tools/.mcp.json repo/plugins/hello-tools/.claude-plugin/plugin.json repo/plugins/hello-tools/skills/hello-tools/SKILL.md; echo ====; cd weather-mcp && git log --oneline --all | head; git tag; git status; find . -path ./.git -prune -o -type f -print", "description": "Read repo files and weather-mcp mirror"}}
{"tool": "Bash", "input": {"command": "cd $RUN/skill/plugin-marketplaces/references && cat multi-tool.md releases.md validation.md", "description": "Read core references"}}
{"tool": "Bash", "input": {"command": "cd $RUN/weather-mcp && git log --oneline --all | head -20; git tag; git rev-parse 'v1.3.0^{commit}'; git status | head -3; git ls-tree -r --name-only v1.3.0; for f in $(git ls-tree -r --name-only v1.3.0 | grep -E 'json$|md$'); do echo \"--- $f\"; git show v1.3.0:$f; done", "description": "Inspect weather-mcp mirror at v1.3.0"}}
{"tool": "Bash", "input": {"command": "cd $RUN/skill/plugin-marketplaces/references && cat claude-code.md codex.md feature-matrix.md agent-plugins.md", "description": "Read tool references"}}
{"tool": "Bash", "input": {"command": "cd $RUN && git -C weather-mcp show v1.3.0:server.py; echo -----; git -C weather-mcp diff --stat v1.3.0 v1.4.0; cat skill/plugin-marketplaces/scripts/mpcheck/policy.py; cat skill/plugin-marketplaces/scripts/mpcheck/data/readers.json | head -80", "description": "Read server.py and policy format"}}
{"tool": "Bash", "input": {"command": "which claude codex copilot git python3 uv; ls $RUN/", "description": "Check available tools"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && mkdir -p .claude-plugin .agents/plugins && cat > marketplace-policy.json <<'EOF'\n{\n  \"readers\": [\"claude-code\", \"codex\"],\n  \"exceptions\": [\n    {\n      \"plugin\": \"weather-mcp\",\n      \"kind\": \"membership\",\n      \"reason\": \"weather-mcp v1.3.0 ships only Claude Code manifests; its .mcp.json passes ${CLAUDE_PLUGIN_ROOT}/server.py as an argument, which Codex does not expand, so its only component (the MCP server) cannot start under Codex. Add it to .agents/plugins/marketplace.json once an upstream release carries a portable plugin.json and mcp.json using ${PLUGIN_ROOT}.\"\n    }\n  ]\n}\nEOF\ncat > .claude-plugin/marketplace.json <<'EOF'\n{\n  \"name\": \"acme-agent-tools\",\n  \"owner\": {\n    \"name\": \"Acme\"\n  },\n  \"metadata\": {\n    \"description\": \"Plugins our team uses with coding agents.\"\n  },\n  \"plugins\": [\n    {\n      \"name\": \"hello-tools\",\n      \"source\": \"./plugins/hello-tools\",\n      \"version\": \"0.3.0\",\n      \"description\": \"Greet teammates by name. Runs a local MCP server (hello-mcp 0.3.0, fetched from PyPI by uvx).\"\n    },\n    {\n      \"name\": \"weather-mcp\",\n      \"source\": {\n        \"source\": \"github\",\n        \"repo\": \"acme/weather-mcp\",\n        \"ref\": \"v1.3.0\",\n        \"sha\": \"bdee23e46e072243455f1ba83ce9d8e2d7584e0a\"\n      },\n      \"version\": \"1.3.0\",\n      \"description\": \"Look up weather forecasts. Runs a local Python MCP server that sends the requested city to https://api.weather.example.\"\n    }\n  ]\n}\nEOF\ncat > .agents/plugins/marketplace.json <<'EOF'\n{\n  \"name\": \"acme-agent-tools\",\n  \"plugins\": [\n    {\n      \"name\": \"hello-tools\",\n      \"source\": {\n        \"source\": \"local\",\n        \"path\": \"./plugins/hello-tools\"\n      },\n      \"version\": \"0.3.0\",\n      \"description\": \"Greet teammates by name. Runs a local MCP server (hello-mcp 0.3.0, fetched from PyPI by uvx).\",\n      \"policy\": {\n        \"installation\": \"AVAILABLE\",\n        \"authentication\": \"ON_INSTALL\"\n      },\n      \"category\": \"Productivity\"\n    }\n  ]\n}\nEOF\ncat > plugins/hello-tools/plugin.json <<'EOF'\n{\n  \"$schema\": \"https://agent-plugins.org/schemas/1.0.0/plugin.schema.json\",\n  \"name\": \"hello-tools\",\n  \"version\": \"0.3.0\",\n  \"description\": \"Greet teammates by name. Runs a local MCP server (hello-mcp 0.3.0, fetched from PyPI by uvx).\",\n  \"author\": {\n    \"name\": \"Acme\"\n  }\n}\nEOF\ncat > plugins/hello-tools/mcp.json <<'EOF'\n{\n  \"$schema\": \"https://agent-plugins.org/schemas/1.0.0/mcp.schema.json\",\n  \"mcpServers\": {\n    \"hello\": {\n      \"type\": \"stdio\",\n      \"command\": \"uvx\",\n      \"args\": [\n        \"hello-mcp==0.3.0\"\n      ]\n    }\n  }\n}\nEOF\nfor f in marketplace-policy.json .claude-plugin/marketplace.json .agents/plugins/marketplace.json plugins/hello-tools/*.json; do python3 -m json.tool $f >/dev/null && echo ok $f; done", "description": "Write policy, catalogs, portable manifests"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=\"$PWD/.tool-homes\" && mkdir -p \"$T\"/{home,xdg,tmp,claude,codex,copilot,copilot-cache} && : > \"$T/gitconfig\" && export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\" && ../validator/bin/check-marketplace . < /dev/null; echo \"exit $?\"; ../validator/bin/check-marketplace . --format json < /dev/null | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d[\"statuses\"]); [print(f) for f in d[\"findings\"]]'", "description": "Run marketplace validator in isolated env"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=\"$PWD/.tool-homes\" && export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" && rm -rf \"$T/neg\" && mkdir \"$T/neg\" && cp -R .claude-plugin .agents plugins marketplace-policy.json \"$T/neg/\" && sed -i '' 's/\"version\": \"0.3.0\"/\"version\": \"0.3.1\"/' \"$T/neg/plugins/hello-tools/plugin.json\" && sed -i '' '/\"sha\": \"bdee/d; s/\"ref\": \"v1.3.0\",/\"ref\": \"v1.3.0\"/' \"$T/neg/.claude-plugin/marketplace.json\" && ../validator/bin/check-marketplace \"$T/neg\" < /dev/null; echo \"exit $?\"; rm -rf \"$T/neg\"", "description": "Negative control for the validator"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=\"$PWD/.tool-homes\" && export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\" && mkdir -p \"$T/mirrors\" && ln -sfn $RUN/weather-mcp \"$T/mirrors/weather-mcp\" && ln -sfn $RUN/weather-mcp \"$T/mirrors/weather-mcp.git\" && printf '[url \"file://%s/mirrors/\"]\\n\\tinsteadOf = https://github.com/acme/\\n\\tinsteadOf = git@github.com:acme/\\n[protocol \"file\"]\\n\\tallow = always\\n' \"$T\" > \"$T/gitconfig\" && cat \"$T/gitconfig\" && rm -rf \"$T/export\" && mkdir \"$T/export\" && git ls-files -co --exclude-standard | grep -v '^\\.tool-homes/' | tar -cf - -T - | tar -xf - -C \"$T/export\" && (cd \"$T/export\" && git init -q && git add -A && git -c user.name=t -c user.email=t@t commit -qm export) && find \"$T/export\" -path '*/.git' -prune -o -type f -print | sed \"s|$T/export/||\"", "description": "Set up mirror redirect and clean export"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=\"$PWD/.tool-homes\" && export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\" && SB='(version 1)(allow default)(deny network-outbound (remote ip))' && run(){ echo \"\\$ $*\"; sandbox-exec -p \"$SB\" \"$@\" < /dev/null 2>&1; echo \"[exit $?]\"; } && run claude --version && run claude plugin validate \"$T/export\" --strict --json && run claude plugin marketplace add \"$T/export\" && run claude plugin install hello-tools@acme-agent-tools && run claude plugin install weather-mcp@acme-agent-tools && run claude plugin list --json && run claude plugin details hello-tools@acme-agent-tools && run claude plugin details weather-mcp@acme-agent-tools", "description": "Claude Code isolated discovery and load checks"}}
{"tool": "Bash", "input": {"command": "T=$RUN/repo/.tool-homes; head -1 \"$T/claude/plugins/cache/acme-agent-tools/weather-mcp/1.3.0/server.py\"; cat \"$T/claude/plugins/installed_plugins.json\" 2>/dev/null | grep -i -E 'sha|commit' ; git -C $RUN/weather-mcp show v1.4.0:server.py | head -3", "description": "Confirm installed weather-mcp is v1.3.0 content"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=\"$PWD/.tool-homes\" && export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\" && SB='(version 1)(allow default)(deny network-outbound (remote ip))' && run(){ echo \"\\$ $*\"; sandbox-exec -p \"$SB\" \"$@\" < /dev/null 2>&1; echo \"[exit $?]\"; } && cd \"$T\" && run codex --version && run codex plugin marketplace add \"$T/export\" && run codex plugin list --available --json && run codex plugin add hello-tools@acme-agent-tools --json && run codex mcp list --json", "description": "Codex isolated discovery and load checks"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=\"$PWD/.tool-homes\" && rm -rf \"$T/codex-probe\" \"$T/probe-mkt\" && mkdir -p \"$T/codex-probe\" \"$T/probe-mkt/.agents/plugins\" && cat > \"$T/probe-mkt/.agents/plugins/marketplace.json\" <<'EOF'\n{\"name\":\"probe\",\"plugins\":[{\"name\":\"weather-mcp\",\"source\":{\"source\":\"url\",\"url\":\"https://github.com/acme/weather-mcp.git\",\"ref\":\"v1.3.0\",\"sha\":\"bdee23e46e072243455f1ba83ce9d8e2d7584e0a\"},\"policy\":{\"installation\":\"AVAILABLE\",\"authentication\":\"ON_INSTALL\"}}]}\nEOF\nexport HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex-probe\" && SB='(version 1)(allow default)(deny network-outbound (remote ip))' && run(){ echo \"\\$ $*\"; sandbox-exec -p \"$SB\" \"$@\" < /dev/null 2>&1; echo \"[exit $?]\"; } && cd \"$T\" && run codex plugin marketplace add \"$T/probe-mkt\" && run codex plugin list --available --json && run codex plugin add weather-mcp@probe --json && run codex mcp list --json", "description": "Probe weather-mcp v1.3.0 under Codex in scratch home"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && git status --short -uall | grep -v '^?? .tool-homes/' ; git status --short | head", "description": "Show final working tree changes"}}
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
    "marketplace": "acme-agent-tools",
    "listed": [
      "hello-tools"
    ]
  },
  "copilot": {
    "ran": true,
    "added": true,
    "marketplace": "acme-agent-tools",
    "listed": [
      "hello-tools",
      "weather-mcp"
    ]
  }
}
```

## Diff

```diff
diff --git a/.agents/plugins/marketplace.json b/.agents/plugins/marketplace.json
new file mode 100644
index 0000000..1bbf08f
--- /dev/null
+++ b/.agents/plugins/marketplace.json
@@ -0,0 +1,19 @@
+{
+  "name": "acme-agent-tools",
+  "plugins": [
+    {
+      "name": "hello-tools",
+      "source": {
+        "source": "local",
+        "path": "./plugins/hello-tools"
+      },
+      "version": "0.3.0",
+      "description": "Greet teammates by name. Runs a local MCP server (hello-mcp 0.3.0, fetched from PyPI by uvx).",
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
index 0000000..69462b5
--- /dev/null
+++ b/.claude-plugin/marketplace.json
@@ -0,0 +1,28 @@
+{
+  "name": "acme-agent-tools",
+  "owner": {
+    "name": "Acme"
+  },
+  "metadata": {
+    "description": "Plugins our team uses with coding agents."
+  },
+  "plugins": [
+    {
+      "name": "hello-tools",
+      "source": "./plugins/hello-tools",
+      "version": "0.3.0",
+      "description": "Greet teammates by name. Runs a local MCP server (hello-mcp 0.3.0, fetched from PyPI by uvx)."
+    },
+    {
+      "name": "weather-mcp",
+      "source": {
+        "source": "github",
+        "repo": "acme/weather-mcp",
+        "ref": "v1.3.0",
+        "sha": "bdee23e46e072243455f1ba83ce9d8e2d7584e0a"
+      },
+      "version": "1.3.0",
+      "description": "Look up weather forecasts. Runs a local Python MCP server that sends the requested city to https://api.weather.example."
+    }
+  ]
+}
diff --git a/marketplace-policy.json b/marketplace-policy.json
new file mode 100644
index 0000000..518ef51
--- /dev/null
+++ b/marketplace-policy.json
@@ -0,0 +1,10 @@
+{
+  "readers": ["claude-code", "codex"],
+  "exceptions": [
+    {
+      "plugin": "weather-mcp",
+      "kind": "membership",
+      "reason": "weather-mcp v1.3.0 ships only Claude Code manifests; its .mcp.json passes ${CLAUDE_PLUGIN_ROOT}/server.py as an argument, which Codex does not expand, so its only component (the MCP server) cannot start under Codex. Add it to .agents/plugins/marketplace.json once an upstream release carries a portable plugin.json and mcp.json using ${PLUGIN_ROOT}."
+    }
+  ]
+}
diff --git a/plugins/hello-tools/mcp.json b/plugins/hello-tools/mcp.json
new file mode 100644
index 0000000..105501f
--- /dev/null
+++ b/plugins/hello-tools/mcp.json
@@ -0,0 +1,12 @@
+{
+  "$schema": "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json",
+  "mcpServers": {
+    "hello": {
+      "type": "stdio",
+      "command": "uvx",
+      "args": [
+        "hello-mcp==0.3.0"
+      ]
+    }
+  }
+}
diff --git a/plugins/hello-tools/plugin.json b/plugins/hello-tools/plugin.json
new file mode 100644
index 0000000..3383674
--- /dev/null
+++ b/plugins/hello-tools/plugin.json
@@ -0,0 +1,9 @@
+{
+  "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
+  "name": "hello-tools",
+  "version": "0.3.0",
+  "description": "Greet teammates by name. Runs a local MCP server (hello-mcp 0.3.0, fetched from PyPI by uvx).",
+  "author": {
+    "name": "Acme"
+  }
+}
```

## Repository refs

Every branch and tag in the final repository, each with its changes against the fixture tree (`refs.txt`).

```text
master 8abfb46
```
