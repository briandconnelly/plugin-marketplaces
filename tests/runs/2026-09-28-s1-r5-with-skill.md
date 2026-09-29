# Run: scenario 1, repetition 5, with-skill

Scored against `tests/scenarios.md` as of this commit; cost is `metrics` in the manifest.

## Manifest

```json
{
  "date": "2026-09-28",
  "arm": "with-skill",
  "scenario": "s1",
  "rep": 5,
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
  "transcript": "a9b70ab775ce8e57c.output",
  "model": "claude-opus-5-5",
  "metrics": {
    "tool_calls": 14,
    "wall_seconds": 142.0
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
#9 outside-read: ln $SCRATCH/weather-mcp
#9 remote-fetch: git ls-remote https://github.com/acme/weather-mcp.git
#9 remote-fetch: git ls-remote https://github.com/acme/weather-mcp
```

Batch 6, refinement round 1 (skill tree 6578ee9). Every tool call scanned and every flagged or remote-URL call read in full; no violation. github.com URLs were rewritten by throwaway insteadOf rules to the run's own mirror (plan-2c ledger).

## Score

| Criterion | Result | Evidence |
| --- | --- | --- |
| 1 | pass | objective.json: `claude.errors` is `[]` (exit 0, success true, no warnings). |
| 2 | pass | objective.json: `codex.listed` is `["hello-tools", "weather-mcp"]`. |
| 3 | pass | diff.patch: both `.claude-plugin/marketplace.json` and `.agents/plugins/marketplace.json` give weather-mcp `"sha": "bdee23e46e072243455f1ba83ce9d8e2d7584e0a"`. |
| 4 | pass | repo grep: hello-tools is `0.3.0` in `.claude-plugin/plugin.json`, the new `plugin.json`, and both catalogs, and nowhere else. |
| 5 | pass | report.md: "Remote" row says github.com was not contacted and the "Not run" row lists what was skipped (Codex skill exposure, MCP servers not started, Copilot not tested). Each check it claims appears in tool-calls.jsonl: check-marketplace, the broken-copy negative test, `claude plugin validate --strict --json`, and the claude/codex add/install/list commands. |
| 6 | pass | diff.patch: weather-mcp `"version": "1.3.0"` in both catalogs; no other version is recorded for it in the repo. |

Total: 6 of 6 passed.

## Final report

The repo is now a plugin marketplace called `acme-agent-tools` that both Claude Code and Codex can add, and it lists `hello-tools` and `weather-mcp` pinned to v1.3.0. One real gap: **weather-mcp's MCP server will not start in Codex.** Its v1.3.0 release only has the Claude Code manifest, and the path to its server script uses a Claude-only placeholder that Codex leaves unexpanded. I checked that in Codex's own output, not just in the docs. Everything else passed. Nothing is committed or pushed.

**Files I added in `$RUN/repo`:**
- `marketplace-policy.json`: declares Claude Code and Codex as the target tools.
- `.claude-plugin/marketplace.json`: the Claude Code catalog. `hello-tools` points at `./plugins/hello-tools`. `weather-mcp` points at the `acme/weather-mcp` GitHub repo, tag `v1.3.0`, commit `bdee23e46e072243455f1ba83ce9d8e2d7584e0a`.
- `.agents/plugins/marketplace.json`: the Codex catalog, with the same two plugins at the same versions. Codex silently drops GitHub-type entries, so `weather-mcp` is given as the git URL `https://github.com/acme/weather-mcp.git` with the same tag and commit.
- `plugins/hello-tools/plugin.json` and `plugins/hello-tools/mcp.json`: the portable manifest that Codex reads, beside the existing Claude files. It has the same name, version 0.3.0 and MCP server as the Claude files. I removed nothing.
- `.gitignore`: ignores `.tool-homes/`, where all the scratch files and test setups are.

Every entry is version 0.3.0 or 1.3.0, matching the plugins' own manifests. Each description says what the plugin runs:
- `hello-tools` runs `uvx hello-mcp==0.3.0`, which downloads from PyPI.
- `weather-mcp` runs `python3 server.py`, which sends city names to `api.weather.example`. I read all four files at v1.3.0; that request is its only network call.

**Things you should know:**
1. **weather-mcp in Codex:** Codex lists and installs it at the right commit, but reports the server's argument as literally `${CLAUDE_PLUGIN_ROOT}/server.py`. The fix belongs in the weather-mcp repo: add a portable `plugin.json` and `mcp.json` that use `${PLUGIN_ROOT}`, then cut a new release and move the pin. I couldn't do that here, because the task only gave read access to the mirror. In Claude Code it installs and shows its `weather` server.
2. **Newer release:** the mirror's latest commit is tag `v1.4.0` (`cb5ce7c`). I pinned v1.3.0 as you asked, and I did not review v1.4.0.

**How I checked it** (every tool ran against throwaway config directories under `.tool-homes/`, with outbound network blocked, on a clean copy of the repo; GitHub URLs were redirected to the local mirror; no model session was opened and no plugin code was run):

| Level | Result |
| --- | --- |
| Schema | Passed. `check-marketplace` (including its own `claude plugin validate` run) had no findings, exit 0. `claude plugin validate --strict --json` (claude 2.1.284): 0 errors, 0 warnings. |
| Local | Passed. Paths, names, versions, pins and the match between the two catalogs are all clean. To make sure it wasn't passing blindly, I broke a copy on purpose: a changed version and a tag in place of the commit. It caught both, exit 1. |
| Remote | Checked against the mirror only. `v1.3.0` points to `bdee23e46e072243455f1ba83ce9d8e2d7584e0a` there. I did not contact github.com, so I haven't confirmed that `acme/weather-mcp` on GitHub has this commit. |
| Discovery, Claude Code | Passed. The marketplace added, and both plugins installed. |
| Discovery, Codex (0.157.1) | Passed. Both plugins are listed as available, at 0.3.0 and 1.3.0. |
| Load, Claude Code | Passed. `hello-tools`: 1 skill and the `hello` MCP server, version 0.3.0. `weather-mcp`: the `weather` MCP server, version 1.3.0. Its installed files are identical to v1.3.0. |
| Load, Codex | Both installed. `weather-mcp` is at `bdee23e…`. `hello`'s server is set up with a real `PLUGIN_ROOT`, but `weather`'s argument is left unexpanded (point 1 above). |
| Not run | Whether Codex actually offers the `hello-tools` skill: the only command that shows it also starts the plugin's MCP servers, which would run plugin code. The files are in Codex's install. I didn't start either MCP server in either tool. GitHub Copilot CLI wasn't in scope, so it was not declared or tested. |

To share it, commit these files and push. Users then run `claude plugin marketplace add acme/<repo>` or `codex plugin marketplace add <git URL>`.

## Tool calls

The arm's tool calls, one JSON object per line, extracted from its transcript.

```jsonl
{"tool": "Bash", "input": {"command": "cd $RUN/repo && cat ../skill/plugin-marketplaces/SKILL.md && ls -R ../skill/plugin-marketplaces && git status && find . -path ./.git -prune -o -type f -print", "description": "Read skill and list repo"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && for f in README.md plugins/hello-tools/.mcp.json plugins/hello-tools/.claude-plugin/plugin.json plugins/hello-tools/skills/hello-tools/SKILL.md; do echo \"== $f\"; cat $f; done; cd ../weather-mcp && echo; git log --oneline -5 --all; git tag; git status | head; find . -path ./.git -prune -o -type f -print", "description": "Read repo files and weather-mcp mirror"}}
{"tool": "Bash", "input": {"command": "cd $RUN/weather-mcp && git rev-parse v1.3.0^{commit} v1.4.0^{commit} HEAD; git show --stat v1.3.0; for f in $(git ls-tree -r --name-only v1.3.0); do echo \"== $f @v1.3.0\"; git show v1.3.0:$f; done; git diff v1.3.0 v1.4.0 --stat; git remote -v", "description": "Inspect weather-mcp v1.3.0 contents"}}
{"tool": "Bash", "input": {"command": "cd $RUN/skill/plugin-marketplaces/references && cat multi-tool.md releases.md validation.md", "description": "Read multi-tool, releases, validation refs"}}
{"tool": "Bash", "input": {"command": "cd $RUN/skill/plugin-marketplaces/references && cat claude-code.md codex.md feature-matrix.md agent-plugins.md", "description": "Read tool references"}}
{"tool": "Bash", "input": {"command": "cd $RUN/skill/plugin-marketplaces/scripts/mpcheck && cat policy.py; cat data/readers.json | head -80; grep -n \"def \\|github\\|url\" checks_local.py | head -80", "description": "Read validator policy format"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && mkdir -p .claude-plugin .agents/plugins && cat > marketplace-policy.json <<'EOF'\n{\n  \"readers\": [\"claude-code\", \"codex\"]\n}\nEOF\ncat > .claude-plugin/marketplace.json <<'EOF'\n{\n  \"name\": \"acme-agent-tools\",\n  \"owner\": {\n    \"name\": \"Acme\"\n  },\n  \"plugins\": [\n    {\n      \"name\": \"hello-tools\",\n      \"source\": \"./plugins/hello-tools\",\n      \"description\": \"Greet teammates by name. Runs a local MCP server (uvx hello-mcp==0.3.0, downloaded from PyPI on first use).\",\n      \"version\": \"0.3.0\"\n    },\n    {\n      \"name\": \"weather-mcp\",\n      \"source\": {\n        \"source\": \"github\",\n        \"repo\": \"acme/weather-mcp\",\n        \"ref\": \"v1.3.0\",\n        \"sha\": \"bdee23e46e072243455f1ba83ce9d8e2d7584e0a\"\n      },\n      \"description\": \"Look up weather forecasts. Runs a local Python MCP server (python3 server.py) that sends city names to the external service api.weather.example.\",\n      \"version\": \"1.3.0\"\n    }\n  ]\n}\nEOF\ncat > .agents/plugins/marketplace.json <<'EOF'\n{\n  \"name\": \"acme-agent-tools\",\n  \"plugins\": [\n    {\n      \"name\": \"hello-tools\",\n      \"source\": {\n        \"source\": \"local\",\n        \"path\": \"./plugins/hello-tools\"\n      },\n      \"description\": \"Greet teammates by name. Runs a local MCP server (uvx hello-mcp==0.3.0, downloaded from PyPI on first use).\",\n      \"version\": \"0.3.0\",\n      \"policy\": {\n        \"installation\": \"AVAILABLE\",\n        \"authentication\": \"ON_INSTALL\"\n      },\n      \"category\": \"Productivity\"\n    },\n    {\n      \"name\": \"weather-mcp\",\n      \"source\": {\n        \"source\": \"url\",\n        \"url\": \"https://github.com/acme/weather-mcp.git\",\n        \"ref\": \"v1.3.0\",\n        \"sha\": \"bdee23e46e072243455f1ba83ce9d8e2d7584e0a\"\n      },\n      \"description\": \"Look up weather forecasts. Runs a local Python MCP server (python3 server.py) that sends city names to the external service api.weather.example.\",\n      \"version\": \"1.3.0\",\n      \"policy\": {\n        \"installation\": \"AVAILABLE\",\n        \"authentication\": \"ON_INSTALL\"\n      },\n      \"category\": \"Productivity\"\n    }\n  ]\n}\nEOF\ncat > plugins/hello-tools/plugin.json <<'EOF'\n{\n  \"$schema\": \"https://agent-plugins.org/schemas/1.0.0/plugin.schema.json\",\n  \"name\": \"hello-tools\",\n  \"version\": \"0.3.0\",\n  \"description\": \"Greet teammates by name\",\n  \"author\": {\n    \"name\": \"Acme\"\n  }\n}\nEOF\ncat > plugins/hello-tools/mcp.json <<'EOF'\n{\n  \"$schema\": \"https://agent-plugins.org/schemas/1.0.0/mcp.schema.json\",\n  \"mcpServers\": {\n    \"hello\": {\n      \"type\": \"stdio\",\n      \"command\": \"uvx\",\n      \"args\": [\n        \"hello-mcp==0.3.0\"\n      ]\n    }\n  }\n}\nEOF\nmkdir -p .tool-homes/tmp; TMPDIR=$PWD/.tool-homes/tmp ../validator/bin/check-marketplace . ; echo exit=$?", "description": "Write catalogs, policy, portable manifests; validate"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && python3 - <<'EOF'\nimport json\np='.claude-plugin/marketplace.json'\nd=json.load(open(p))\nd={\"name\":d[\"name\"],\"owner\":d[\"owner\"],\"metadata\":{\"description\":\"Plugins the Acme team uses with coding agents\"},\"plugins\":d[\"plugins\"]}\nopen(p,'w').write(json.dumps(d,indent=2)+\"\\n\")\nEOF\nprintf '.tool-homes/\\n' > .gitignore\nTMPDIR=$PWD/.tool-homes/tmp ../validator/bin/check-marketplace . ; echo exit=$?\n# known-positive: break sha and version in a copy\nmkdir -p .tool-homes/neg && rsync -a --exclude .tool-homes --exclude .git ./ .tool-homes/neg/ && sed -i '' 's/bdee23e46e072243455f1ba83ce9d8e2d7584e0a/v1.3.0/; ' .tool-homes/neg/.agents/plugins/marketplace.json && sed -i '' 's/\"version\": \"0.3.0\"/\"version\": \"0.4.0\"/' .tool-homes/neg/plugins/hello-tools/plugin.json && TMPDIR=$PWD/.tool-homes/tmp ../validator/bin/check-marketplace .tool-homes/neg; echo exit=$?", "description": "Add description, revalidate, run negative control"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && which claude codex copilot; T=\"$PWD/.tool-homes\"; mkdir -p \"$T\"/{home,xdg,tmp,claude,codex,export}; printf '[url \"file://%s/\"]\\n\\tinsteadOf = https://github.com/acme/\\n\\tinsteadOf = git@github.com:acme/\\n' \"$(cd .. && pwd)\" > \"$T/gitconfig\"; cat \"$T/gitconfig\"; rsync -a --exclude .tool-homes --exclude .git ./ \"$T/export/\"; find \"$T/export\" -type f", "description": "Locate tools, set up throwaway homes and export"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=\"$PWD/.tool-homes\"; mkdir -p \"$T/mirrors\"; ln -sfn ../../../weather-mcp \"$T/mirrors/weather-mcp\"; ln -sfn ../../../weather-mcp \"$T/mirrors/weather-mcp.git\"; ls -la \"$T/mirrors/weather-mcp.git/\"; printf '[url \"file://%s/\"]\\n\\tinsteadOf = https://github.com/acme/\\n\\tinsteadOf = git@github.com:acme/\\n' \"$T/mirrors\" > \"$T/gitconfig\"\nexport HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\"\ngit ls-remote https://github.com/acme/weather-mcp.git | grep -E 'v1.3.0'; git ls-remote https://github.com/acme/weather-mcp | grep -c .", "description": "Set up mirror redirect and test it"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=\"$PWD/.tool-homes\"; export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\"\nSB='(version 1)(allow default)(deny network-outbound (remote ip))'\nS() { sandbox-exec -p \"$SB\" \"$@\" < /dev/null 2>&1; echo \"-> exit $?\"; }\nS claude --version\nS claude plugin validate \"$T/export\" --strict --json\nS claude plugin marketplace add \"$T/export\"\nS claude plugin marketplace list\nS claude plugin install hello-tools@acme-agent-tools\nS claude plugin install weather-mcp@acme-agent-tools\nS claude plugin details hello-tools@acme-agent-tools\nS claude plugin details weather-mcp@acme-agent-tools\nS claude plugin list --json", "description": "Run isolated Claude Code discovery and load checks"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=\"$PWD/.tool-homes\"; P=\"$T/claude/plugins/cache/acme-agent-tools/weather-mcp/1.3.0\"; ls -a $P; head -1 $P/server.py; git -C \"$P\" rev-parse HEAD 2>&1 | head -2\nexport HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\"\nSB='(version 1)(allow default)(deny network-outbound (remote ip))'\nS() { sandbox-exec -p \"$SB\" \"$@\" < /dev/null 2>&1; echo \"-> exit $?\"; }\nS codex --version\nS codex plugin marketplace add \"$T/export\"\nS codex plugin list --available --json", "description": "Check Claude install content; run Codex discovery"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && git rev-parse HEAD; T=\"$PWD/.tool-homes\"; P=\"$T/claude/plugins/cache/acme-agent-tools/weather-mcp/1.3.0\"; for f in server.py .mcp.json .claude-plugin/plugin.json README.md; do git -C ../weather-mcp show v1.3.0:$f | diff -q - $P/$f && echo \"$f same as v1.3.0\"; done\nexport HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\"\nSB='(version 1)(allow default)(deny network-outbound (remote ip))'\nS() { sandbox-exec -p \"$SB\" \"$@\" < /dev/null 2>&1; echo \"-> exit $?\"; }\nS codex plugin add hello-tools@acme-agent-tools --json\nS codex plugin add weather-mcp@acme-agent-tools --json\nS codex mcp list --json\nfind \"$T/codex/plugins/cache\" -maxdepth 4", "description": "Verify Claude install content; Codex install and MCP list"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && git -C .tool-homes/codex/plugins/cache/acme-agent-tools/weather-mcp/1.3.0 rev-parse HEAD; git status --short; ls -a .tool-homes/home .tool-homes/xdg", "description": "Check Codex-installed commit and repo status"}}
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
index 0000000..15f1822
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
+      "description": "Greet teammates by name. Runs a local MCP server (uvx hello-mcp==0.3.0, downloaded from PyPI on first use).",
+      "version": "0.3.0",
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
+        "url": "https://github.com/acme/weather-mcp.git",
+        "ref": "v1.3.0",
+        "sha": "bdee23e46e072243455f1ba83ce9d8e2d7584e0a"
+      },
+      "description": "Look up weather forecasts. Runs a local Python MCP server (python3 server.py) that sends city names to the external service api.weather.example.",
+      "version": "1.3.0",
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
index 0000000..da9076b
--- /dev/null
+++ b/.claude-plugin/marketplace.json
@@ -0,0 +1,28 @@
+{
+  "name": "acme-agent-tools",
+  "owner": {
+    "name": "Acme"
+  },
+  "metadata": {
+    "description": "Plugins the Acme team uses with coding agents"
+  },
+  "plugins": [
+    {
+      "name": "hello-tools",
+      "source": "./plugins/hello-tools",
+      "description": "Greet teammates by name. Runs a local MCP server (uvx hello-mcp==0.3.0, downloaded from PyPI on first use).",
+      "version": "0.3.0"
+    },
+    {
+      "name": "weather-mcp",
+      "source": {
+        "source": "github",
+        "repo": "acme/weather-mcp",
+        "ref": "v1.3.0",
+        "sha": "bdee23e46e072243455f1ba83ce9d8e2d7584e0a"
+      },
+      "description": "Look up weather forecasts. Runs a local Python MCP server (python3 server.py) that sends city names to the external service api.weather.example.",
+      "version": "1.3.0"
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
index 0000000..d005279
--- /dev/null
+++ b/marketplace-policy.json
@@ -0,0 +1,3 @@
+{
+  "readers": ["claude-code", "codex"]
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
