# Run: scenario 1, repetition 6, with-skill

Scored against `tests/scenarios.md` as of this commit; cost is `metrics` in the manifest.

## Manifest

```json
{
  "date": "2026-09-28",
  "arm": "with-skill",
  "scenario": "s1",
  "rep": 6,
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
  "session_context": "dispatched from a Claude Code session (claude 2.1.284) with installed plugins including superpowers, plugin-dev, amicus, astral, obsidian, pr-review-toolkit, code-review, skill-creator, mcp-server-dev, claude-code-setup; user skills include agent-bot-identity, review-pr, fastmcp, prek, separating-context-from-constraints; the plugin-marketplaces skill reaches arms only through the run's skill copy (refinement round 1)",
  "prompt_file": "prompt.txt",
  "skill": "$RUN/skill/plugin-marketplaces",
  "validator": "$RUN/validator/bin/check-marketplace",
  "skill_tree": "6578ee9f85fa202a3ccb74c0ddffde54ef9fd429",
  "transcript": "a7d7d3a1bb7dc9297.output",
  "model": "claude-opus-5-5",
  "metrics": {
    "tool_calls": 15,
    "wall_seconds": 143.7
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
#10 remote-fetch: git -C $T/fetch fetch -q --depth 1 https://github.com/acme/weather-mcp bdee23e46e072243455f1ba83ce9d8e2d7584e0a
#10 remote-fetch: git ls-remote https://github.com/acme/weather-mcp
```

Batch 6, refinement round 1 (skill tree 6578ee9). Every tool call scanned and every flagged or remote-URL call read in full; no violation. github.com URLs were rewritten by throwaway insteadOf rules to the run's own mirror (plan-2c ledger).

## Score

| Criterion | Result | Evidence |
| --- | --- | --- |
| 1 | pass | artefacts/objective.json: `claude.errors` is `[]` (and `warnings` is `[]`), success true. |
| 2 | pass | artefacts/objective.json: `codex.listed` is `["hello-tools", "weather-mcp"]`. |
| 3 | pass | diff.patch: both weather-mcp entries record `"sha": "bdee23e46e072243455f1ba83ce9d8e2d7584e0a"`, one in `.claude-plugin/marketplace.json` and one in `.agents/plugins/marketplace.json`. refs.txt shows only `master`. |
| 4 | pass | The final repo records hello-tools as 0.3.0 in all four places: both catalogs, the new `plugins/hello-tools/plugin.json` and the existing `plugins/hello-tools/.claude-plugin/plugin.json`. |
| 5 | pass | report.md's check table names what did not run: the live GitHub repo was "not checked", MCP servers were "Not run", Copilot CLI was "Not run", and the Codex hello-tools skill is "Not proven". The checks it claims all appear in tool-calls.jsonl (lines 8–13: check-marketplace plus the negative copy, the mirror fetch, `claude plugin validate --strict`, add/install, `codex plugin list`/`add`, `mcp list`). |
| 6 | pass | diff.patch: the only weather-mcp versions recorded are `"version": "1.3.0"`, one in each catalog. |

Total: 6 of 6 passed.

## Final report

The repo is now a plugin marketplace called `acme-agent-tools` that both Claude Code and Codex can add, and it offers `hello-tools` and `weather-mcp` pinned to v1.3.0. One problem remains: weather-mcp installs in Codex, but its weather server will not start there. That has to be fixed in the weather-mcp repo, not in this one.

Nothing is committed yet. All the new files are untracked in `$RUN/repo`.

## What I did
Following the plugin-marketplaces skill, I gave each tool its own catalog.
- **`marketplace-policy.json`**: says the marketplace is meant for Claude Code and Codex. The two catalogs list the same plugins at the same versions, so no differences needed a recorded reason.
- **`.claude-plugin/marketplace.json`** (read by Claude Code):
  - `hello-tools` points to the local folder `./plugins/hello-tools`, version 0.3.0.
  - `weather-mcp` points to `https://github.com/acme/weather-mcp` at `ref` v1.3.0 and the full commit `bdee23e46e072243455f1ba83ce9d8e2d7584e0a`, version 1.3.0.
- **`.agents/plugins/marketplace.json`** (read by Codex): the same two entries in Codex's format, with `policy` and `category` added.
  - I used a plain git URL source for weather-mcp in both catalogs because Codex silently drops GitHub-style sources.
- **`plugins/hello-tools/plugin.json` and `plugins/hello-tools/mcp.json`** (new): Codex reads these instead of the Claude files. I added them next to the existing Claude files and left those unchanged. Both say version 0.3.0 and describe the same `uvx hello-mcp==0.3.0` server.
- **Plugin descriptions**: each one says what code it runs. hello-tools starts an MCP server through uvx, fetched from PyPI. weather-mcp starts `python3 server.py`, which sends the city to `api.weather.example`.
- **`.gitignore`**: excludes `.tool-homes/`, where all my scratch files and throwaway tool settings live.

## What won't work
**weather-mcp in Codex:** it installs, but its server won't start. The package at v1.3.0 has only Claude-format files, and its server command uses `${CLAUDE_PLUGIN_ROOT}`. Codex passes that placeholder through as literal text: `codex mcp list --json` shows the arguments as `"${CLAUDE_PLUGIN_ROOT}/server.py"`, so the server path can't be found. I did not start the server. The fix belongs in weather-mcp: a new release that adds a portable `plugin.json` and an `mcp.json` using `${PLUGIN_ROOT}`, then moving the pin here to it. It works in Claude Code as it is.

**Reviewing the pinned version:** I read the v1.3.0 code. Its only network call sends the city to `api.weather.example`, and the city goes into the URL unescaped, which is a minor issue.

**Don't upgrade weather-mcp to v1.4.0 without deciding on this:** v1.4.0, the newest tag, adds a call to `metrics.acme.example/collect` that sends the city and the user's `$USER` login name. Users would need to be told before that ships.

## How I checked it
Every tool ran with throwaway settings under `.tool-homes/` and with outbound network blocked. GitHub was redirected to the local mirror through a throwaway git config. I sent no prompts to any model and ran no plugin code. The installed tools were Claude Code 2.1.284 and Codex 0.157.1, the versions the skill's notes were checked against.

| Check | Result |
| --- | --- |
| File format (skill's `check-marketplace` validator) | Passed, no findings, exit 0. On a scratch copy with a wrong version and a GitHub-style source in the Codex catalog, it failed with 3 errors, so it does catch these problems. |
| File format (`claude plugin validate --strict --json`) | Passed, 0 errors and 0 warnings. |
| Local rules (validator: paths, names, versions, catalogs match) | Passed. |
| Pinned weather-mcp commit | Checked against the local mirror only: tag v1.3.0 is that commit, and its manifest says `weather-mcp` 1.3.0. I did not contact the real GitHub repo, so the live repo is not checked. |
| Claude Code sees both plugins | Passed: adding the marketplace (from a clean export of the files) succeeded and both plugins installed. |
| Codex sees both plugins | Passed: adding succeeded, `codex plugin list --available --json` listed both at the right versions, and both installed. |
| What loads in Claude Code | hello-tools 0.3.0: 1 skill, 1 MCP server. weather-mcp 1.3.0: 1 MCP server. |
| What loads in Codex | Both versions are right and both MCP servers are listed, but weather's is broken as described above. Not proven: that Codex offers the hello-tools skill. The only command that shows this would have started the plugin's server. |
| MCP servers actually starting | Not run in either tool; that would run plugin code. |
| GitHub Copilot CLI | Not run, since you didn't ask for it. It would also read `.claude-plugin/marketplace.json`, but that is untested. |

The first Codex install of weather-mcp failed only because of how I pointed GitHub at the mirror (Codex adds `.git` to the URL). I fixed that in the throwaway setup and it installed.

## Tool calls

The arm's tool calls, one JSON object per line, extracted from its transcript.

```jsonl
{"tool": "Bash", "input": {"command": "cd $RUN/repo && cat ../skill/plugin-marketplaces/SKILL.md && ls -R ../skill/plugin-marketplaces && git status && git log --oneline | head && find . -path ./.git -prune -o -type f -print"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && for f in README.md plugins/hello-tools/.mcp.json plugins/hello-tools/.claude-plugin/plugin.json plugins/hello-tools/skills/hello-tools/SKILL.md; do echo \"== $f\"; cat $f; done; cd ../weather-mcp && git log --oneline --decorate -5 2>&1; git tag; find . -path ./.git -prune -o -type f -print"}}
{"tool": "Bash", "input": {"command": "cd $RUN/skill/plugin-marketplaces/references && cat multi-tool.md feature-matrix.md releases.md"}}
{"tool": "Bash", "input": {"command": "cd $RUN/skill/plugin-marketplaces/references && cat validation.md codex.md"}}
{"tool": "Bash", "input": {"command": "cd $RUN/weather-mcp && git rev-parse 'v1.3.0^{commit}' v1.4.0^{commit}; for f in server.py .mcp.json README.md .claude-plugin/plugin.json; do echo \"== $f\"; git show v1.3.0:$f; done; echo ===DIFF; git diff v1.3.0 v1.4.0 --stat"}}
{"tool": "Bash", "input": {"command": "cd $RUN/skill/plugin-marketplaces && cat references/claude-code.md references/agent-plugins.md; cat scripts/mpcheck/policy.py; cat scripts/mpcheck/data/readers.json | head -80"}}
{"tool": "Bash", "input": {"command": "cd $RUN/skill/plugin-marketplaces && sed -n 1,200p scripts/mpcheck/checks_local.py | grep -n \"check\\|rule\" | head -60; which claude codex copilot; git -C ../../weather-mcp diff v1.3.0 v1.4.0 --stat"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && mkdir -p .claude-plugin .agents/plugins\ncat > marketplace-policy.json <<'EOF'\n{\n  \"readers\": [\"claude-code\", \"codex\"],\n  \"exceptions\": [],\n  \"channels\": []\n}\nEOF\ncat > .claude-plugin/marketplace.json <<'EOF'\n{\n  \"name\": \"acme-agent-tools\",\n  \"owner\": {\n    \"name\": \"Acme\"\n  },\n  \"metadata\": {\n    \"description\": \"Plugins our team uses with coding agents.\"\n  },\n  \"plugins\": [\n    {\n      \"name\": \"hello-tools\",\n      \"source\": \"./plugins/hello-tools\",\n      \"version\": \"0.3.0\",\n      \"description\": \"Greet teammates by name. Runs an MCP server (hello-mcp 0.3.0, fetched from PyPI and started with uvx).\"\n    },\n    {\n      \"name\": \"weather-mcp\",\n      \"source\": {\n        \"source\": \"url\",\n        \"url\": \"https://github.com/acme/weather-mcp\",\n        \"ref\": \"v1.3.0\",\n        \"sha\": \"bdee23e46e072243455f1ba83ce9d8e2d7584e0a\"\n      },\n      \"version\": \"1.3.0\",\n      \"description\": \"Look up weather forecasts. Runs a local Python MCP server (python3 server.py) that sends the requested city to the external service api.weather.example.\"\n    }\n  ]\n}\nEOF\ncat > .agents/plugins/marketplace.json <<'EOF'\n{\n  \"name\": \"acme-agent-tools\",\n  \"plugins\": [\n    {\n      \"name\": \"hello-tools\",\n      \"source\": {\n        \"source\": \"local\",\n        \"path\": \"./plugins/hello-tools\"\n      },\n      \"version\": \"0.3.0\",\n      \"description\": \"Greet teammates by name. Runs an MCP server (hello-mcp 0.3.0, fetched from PyPI and started with uvx).\",\n      \"policy\": {\n        \"installation\": \"AVAILABLE\",\n        \"authentication\": \"ON_INSTALL\"\n      },\n      \"category\": \"Productivity\"\n    },\n    {\n      \"name\": \"weather-mcp\",\n      \"source\": {\n        \"source\": \"url\",\n        \"url\": \"https://github.com/acme/weather-mcp\",\n        \"ref\": \"v1.3.0\",\n        \"sha\": \"bdee23e46e072243455f1ba83ce9d8e2d7584e0a\"\n      },\n      \"version\": \"1.3.0\",\n      \"description\": \"Look up weather forecasts. Runs a local Python MCP server (python3 server.py) that sends the requested city to the external service api.weather.example.\",\n      \"policy\": {\n        \"installation\": \"AVAILABLE\",\n        \"authentication\": \"ON_INSTALL\"\n      },\n      \"category\": \"Productivity\"\n    }\n  ]\n}\nEOF\ncat > plugins/hello-tools/plugin.json <<'EOF'\n{\n  \"$schema\": \"https://agent-plugins.org/schemas/1.0.0/plugin.schema.json\",\n  \"name\": \"hello-tools\",\n  \"version\": \"0.3.0\",\n  \"description\": \"Greet teammates by name\",\n  \"author\": {\n    \"name\": \"Acme\"\n  }\n}\nEOF\ncat > plugins/hello-tools/mcp.json <<'EOF'\n{\n  \"$schema\": \"https://agent-plugins.org/schemas/1.0.0/mcp.schema.json\",\n  \"mcpServers\": {\n    \"hello\": {\n      \"type\": \"stdio\",\n      \"command\": \"uvx\",\n      \"args\": [\n        \"hello-mcp==0.3.0\"\n      ]\n    }\n  }\n}\nEOF\n$RUN/validator/bin/check-marketplace --help | head -30"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && echo \".tool-homes/\" > .gitignore\nT=\"$PWD/.tool-homes\"; mkdir -p \"$T\"/{home,xdg,tmp,claude,codex,copilot,copilot-cache}; : > \"$T/gitconfig\"\nexport HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\"\n$RUN/validator/bin/check-marketplace \"$PWD\" < /dev/null; echo \"exit=$?\""}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=\"$PWD/.tool-homes\"\nexport HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\"\nrm -rf \"$T/neg\" && mkdir -p \"$T/neg\" && cp -R .claude-plugin .agents plugins marketplace-policy.json \"$T/neg/\"\nsed -i '' 's/\"version\": \"0.3.0\"/\"version\": \"0.4.0\"/' \"$T/neg/plugins/hello-tools/plugin.json\"\npython3 - \"$T/neg/.agents/plugins/marketplace.json\" <<'EOF'\nimport json,sys;p=sys.argv[1];d=json.load(open(p));d[\"plugins\"][1][\"source\"]={\"source\":\"github\",\"repo\":\"acme/weather-mcp\",\"sha\":\"bdee23e46e072243455f1ba83ce9d8e2d7584e0a\"};json.dump(d,open(p,\"w\"),indent=2)\nEOF\n$RUN/validator/bin/check-marketplace \"$T/neg\" < /dev/null; echo \"exit=$?\""}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=\"$PWD/.tool-homes\"\nexport HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\"\nM=$RUN\nprintf '[url \"file://%s/\"]\\n\\tinsteadOf = https://github.com/acme/\\n' \"$M\" > \"$T/gitconfig\"; cat \"$T/gitconfig\"\n# remote-level check against mirror\nrm -rf \"$T/fetch\" && git init -q \"$T/fetch\" && git -C \"$T/fetch\" fetch -q --depth 1 https://github.com/acme/weather-mcp bdee23e46e072243455f1ba83ce9d8e2d7584e0a && git -C \"$T/fetch\" show FETCH_HEAD:.claude-plugin/plugin.json && git -C \"$T/fetch\" rev-parse FETCH_HEAD\ngit ls-remote https://github.com/acme/weather-mcp\n# clean export via temp index\nGIT_INDEX_FILE=\"$T/idx\" git add -A && TREE=$(GIT_INDEX_FILE=\"$T/idx\" git write-tree) && rm -rf \"$T/export\" && mkdir -p \"$T/export\" && git archive $TREE | tar -x -C \"$T/export\" && find \"$T/export\" -type f | sed \"s|$T/export/||\"\nclaude --version < /dev/null; codex --version < /dev/null"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=\"$PWD/.tool-homes\"\nexport HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\"\nSB='(version 1)(allow default)(deny network-outbound (remote ip))'\nrun(){ echo \"\\$ $*\"; sandbox-exec -p \"$SB\" \"$@\" < /dev/null 2>&1; echo \"[exit $?]\"; }\nrun claude plugin validate \"$T/export\" --strict --json\nrun claude plugin marketplace add \"$T/export\"\nrun claude plugin install hello-tools@acme-agent-tools\nrun claude plugin install weather-mcp@acme-agent-tools\nrun claude plugin details hello-tools@acme-agent-tools\nrun claude plugin details weather-mcp@acme-agent-tools\nrun claude plugin list --json"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=\"$PWD/.tool-homes\"\nexport HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\"\ngit -C \"$T/claude/plugins/cache/acme-agent-tools/weather-mcp/1.3.0\" rev-parse HEAD 2>&1; ls -a \"$T/claude/plugins/cache/acme-agent-tools/weather-mcp/1.3.0\"; head -1 \"$T/claude/plugins/cache/acme-agent-tools/weather-mcp/1.3.0/server.py\"\nSB='(version 1)(allow default)(deny network-outbound (remote ip))'\nrun(){ echo \"\\$ $*\"; sandbox-exec -p \"$SB\" \"$@\" < /dev/null 2>&1; echo \"[exit $?]\"; }\nrun codex plugin marketplace add \"$T/export\"\nrun codex plugin list --available --json\nrun codex plugin add hello-tools@acme-agent-tools --json\nrun codex plugin add weather-mcp@acme-agent-tools --json\nrun codex mcp list --json\nfind \"$T/codex/plugins/cache\" -maxdepth 3"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=\"$PWD/.tool-homes\"\nexport HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\"\nM=$RUN/weather-mcp\nmkdir -p \"$T/mirrors\" && ln -sfn \"$M\" \"$T/mirrors/weather-mcp\" && ln -sfn \"$M\" \"$T/mirrors/weather-mcp.git\"\nprintf '[url \"file://%s/mirrors/\"]\\n\\tinsteadOf = https://github.com/acme/\\n' \"$T\" > \"$T/gitconfig\"\nSB='(version 1)(allow default)(deny network-outbound (remote ip))'\nrun(){ echo \"\\$ $*\"; sandbox-exec -p \"$SB\" \"$@\" < /dev/null 2>&1; echo \"[exit $?]\"; }\nrun codex plugin add weather-mcp@acme-agent-tools --json\nrun codex mcp list --json\nW=\"$T/codex/plugins/cache/acme-agent-tools/weather-mcp/1.3.0\"; ls -a \"$W\"; head -1 \"$W/server.py\""}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && git status --short && git -C ../weather-mcp diff v1.3.0 v1.4.0 -- server.py | head -20"}}
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
      "hello-tools",
      "weather-mcp"
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
index 0000000..27049df
--- /dev/null
+++ b/.agents/plugins/marketplace.json
@@ -0,0 +1,35 @@
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
+      "description": "Greet teammates by name. Runs an MCP server (hello-mcp 0.3.0, fetched from PyPI and started with uvx).",
+      "policy": {
+        "installation": "AVAILABLE",
+        "authentication": "ON_INSTALL"
+      },
+      "category": "Productivity"
+    },
+    {
+      "name": "weather-mcp",
+      "source": {
+        "source": "url",
+        "url": "https://github.com/acme/weather-mcp",
+        "ref": "v1.3.0",
+        "sha": "bdee23e46e072243455f1ba83ce9d8e2d7584e0a"
+      },
+      "version": "1.3.0",
+      "description": "Look up weather forecasts. Runs a local Python MCP server (python3 server.py) that sends the requested city to the external service api.weather.example.",
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
index 0000000..c9579f8
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
+      "description": "Greet teammates by name. Runs an MCP server (hello-mcp 0.3.0, fetched from PyPI and started with uvx)."
+    },
+    {
+      "name": "weather-mcp",
+      "source": {
+        "source": "url",
+        "url": "https://github.com/acme/weather-mcp",
+        "ref": "v1.3.0",
+        "sha": "bdee23e46e072243455f1ba83ce9d8e2d7584e0a"
+      },
+      "version": "1.3.0",
+      "description": "Look up weather forecasts. Runs a local Python MCP server (python3 server.py) that sends the requested city to the external service api.weather.example."
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
index 0000000..9bac8af
--- /dev/null
+++ b/plugins/hello-tools/plugin.json
@@ -0,0 +1,9 @@
+{
+  "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
+  "name": "hello-tools",
+  "version": "0.3.0",
+  "description": "Greet teammates by name",
+  "author": {
+    "name": "Acme"
+  }
+}
```

## Repository refs

Every branch and tag in the final repository, each with its changes against the fixture tree (`refs.txt`).

```text
master 369c4bc
```
