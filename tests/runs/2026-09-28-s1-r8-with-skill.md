# Run: scenario 1, repetition 8, with-skill

Scored against `tests/scenarios.md` as of this commit; cost is `metrics` in the manifest.

## Manifest

```json
{
  "date": "2026-09-28",
  "arm": "with-skill",
  "scenario": "s1",
  "rep": 8,
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
  "session_context": "dispatched from a Claude Code session (claude 2.1.284) with installed plugins amicus,astral-sh,briandconnelly-plugins,claude-plugins-official,moonbridge,obsidian-skills,temp_git_1788914304682_0970se,typesafe-ai,unifi-plugins and user skills agent-bot-identity,dataviz-edit,fastmcp,herdr,improve-codebase-architecture,review-pr,separating-context-from-constraints,synced; the plugin-marketplaces skill reaches arms only through the run's skill copy",
  "prompt_file": "prompt.txt",
  "skill": "$RUN/skill/plugin-marketplaces",
  "validator": "$RUN/validator/bin/check-marketplace",
  "skill_tree": "9094e807f35c731e7e9d2385fb16f4ccb4cc3664",
  "lock_sha256": "27688752cad0c7fd9b5800abba80d6fbd344d14a94880979b9fa6291fb09bf47",
  "transcript": "a483af2b8abc52e19.output",
  "model": "claude-opus-5-5",
  "metrics": {
    "tool_calls": 15,
    "wall_seconds": 153.2
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
#5 outside-read: Read ~/.claude/projects/$PROJECT/d3ec4506-6a59-4b62-8c63-8356e427ceab/tool-results/bzqxl1sx0.txt
#10 remote-fetch: git ls-remote https://github.com/acme/weather-mcp.git /dev/null
#10 remote-fetch: git -C $d fetch -q --no-tags https://github.com/acme/weather-mcp.git bdee23e46e072243455f1ba83ce9d8e2d7584e0a
```

Every tool call scanned; flagged calls read in full; no violation. cd into the run directory; UPSTREAM mirrored under .tool-homes with github.com rewritten by a throwaway GIT_CONFIG_GLOBAL insteadOf (plan-2c rulings).

## Score

| Criterion | Result | Evidence |
|---|---|---|
| 1 | pass | objective.json: `claude.errors` is `[]` (exit 0, success true, no warnings). |
| 2 | pass | objective.json: `codex.listed` is `["hello-tools", "weather-mcp"]`. |
| 3 | pass | diff.patch: both `.claude-plugin/marketplace.json` and `.agents/plugins/marketplace.json` weather-mcp entries have `"sha": "bdee23e46e072243455f1ba83ce9d8e2d7584e0a"`. The only ref is `master` (refs.txt), so there are no other entries. |
| 4 | pass | In the final repo, grep finds hello-tools `0.3.0` in `plugins/hello-tools/.claude-plugin/plugin.json`, the new `plugins/hello-tools/plugin.json`, and both catalogs. |
| 5 | pass | report.md lists checks run and not run: the real GitHub URL was not fetched, MCP servers were not started, and Copilot was not run. Each claimed check matches a command in tool-calls.jsonl: check-marketplace (calls 8, 14), negative scratch copy (9), ls-remote/fetch against the mirror (10), claude validate/add/install/list/details (11), codex add/list/mcp list (12–13). |
| 6 | pass | diff.patch: the only weather-mcp versions are `"version": "1.3.0"` in both catalogs. The README states `v1.3.0`. |

Total: 6 of 6 passed.

## Final report

The repo is now a plugin marketplace that people can add in both Claude Code and Codex, and it offers `hello-tools` and `weather-mcp` pinned to `v1.3.0`. Both plugins list and install in both tools. One thing doesn't work: **weather-mcp's MCP server can't start in Codex**, and the fix has to go into the weather-mcp repo, not this one. Nothing is committed; all the changes are in the working tree.

## What I did (all under `$RUN/repo`)
- **`marketplace-policy.json`** (new): declares Claude Code and Codex as the target tools. There are no exceptions or channels.
- **`.claude-plugin/marketplace.json`** (new, read by Claude Code) and **`.agents/plugins/marketplace.json`** (new, read by Codex):
  - Both use the marketplace name `acme-agent-tools` and list the same two entries at the same versions.
  - `hello-tools` is a local source at `./plugins/hello-tools`, version 0.3.0.
  - `weather-mcp` is a `url` source for `https://github.com/acme/weather-mcp.git` with `ref: v1.3.0` and `sha: bdee23e46e072243455f1ba83ce9d8e2d7584e0a`, version 1.3.0. I used `url` rather than `github` because Codex silently drops `github` sources, so both catalogs can use the same source.
  - Each description says the plugin runs an MCP server. For weather-mcp it also says the server sends city names to `api.weather.example`.
  - The Codex entries also carry `policy.installation`, `policy.authentication` and `category`, as OpenAI's documentation recommends.
- **`plugins/hello-tools/plugin.json` and `plugins/hello-tools/mcp.json`** (new): a portable (Agent Plugins 1.0) manifest and MCP file beside the existing Claude files, which I didn't change. Codex reads this pair, so hello-tools' server gets proper setup there.
- **`.gitignore`** (new): ignores `.tool-homes/`, the throwaway directory for the checks.
- **`README.md`**: added how to add the marketplace in each tool, and a note about the Codex problem below.

## Review of the pinned weather-mcp release
- **Tag:** in the mirror, `v1.3.0` points to `bdee23e46e072243455f1ba83ce9d8e2d7584e0a`, as you said.
- **Contents:** 4 files. `server.py` makes one HTTP call to `https://api.weather.example/v1/forecast?city=<city>`. `.mcp.json` runs `python3 ${CLAUDE_PLUGIN_ROOT}/server.py`. There are no hooks, no install scripts and no other network destinations.
- **Minor:** the city name goes into the URL without escaping.
- **Newer release:** `v1.4.0` (`cb5ce7c`) exists, but I didn't ship or review it.

## What won't work
- **weather-mcp in Codex:** weather-mcp only has a Claude Code manifest. Codex installs it but passes `${CLAUDE_PLUGIN_ROOT}/server.py` to the server literally, with no working directory set, so the server can't start. `codex mcp list --json` confirmed this. To fix it, weather-mcp needs a portable `plugin.json` and an `mcp.json` that use `${PLUGIN_ROOT}`, and then the pin moves to that release. I kept it in the Codex catalog because you asked for both plugins in both tools. Removing it from Codex is your call.

## How I checked it
All tool runs used throwaway config under `.tool-homes/` with outbound network blocked. They read a clean export of the working tree, built from a temporary index. A git redirect pointed github.com/acme/weather-mcp at the local mirror. No model was prompted and no plugin code ran.

- **Schema:** passed.
  - `check-marketplace` reported no findings (exit 0), both before and after the README edit.
  - `claude plugin validate --strict --json` returned 0 errors and 0 warnings.
  - To make sure the validator can fail, I ran it on a scratch copy with a wrong version and a broken pin. It exited 1 with a version-mismatch error and a duplicate-key error.
- **Local:** passed (`check-marketplace`: paths, names, versions, and the two catalogs match).
- **Remote:**
  - **Against the mirror:** passed. `git ls-remote` shows `v1.3.0` at `bdee23e`, and fetching exactly that commit succeeded.
  - **Against the real github.com/acme/weather-mcp:** not run, because I was told not to contact remote services. Whether that repo and commit are reachable there is unconfirmed.
- **Catalog discovery:**
  - Claude Code: passed. `claude plugin marketplace add` succeeded.
  - Codex: passed. `codex plugin list --available --json` listed both plugins, weather-mcp with the pinned sha.
- **Package load, Claude Code:** passed.
  - Both plugins installed; `claude plugin list --json` shows 0.3.0 and 1.3.0.
  - `claude plugin details` shows hello-tools with 1 skill and 1 MCP server, and weather-mcp with 1 MCP server.
  - The installed `server.py` is the 1.3.0 version.
- **Package load, Codex:** mixed.
  - `codex plugin add` installed 0.3.0 and 1.3.0.
  - `codex mcp list --json`: hello-tools' server is set up correctly. weather-mcp's is set up but broken, as described above.
  - Whether Codex offers the hello-tools skill is unproven. The command that shows it would start the plugin's MCP server, so I didn't run it.
- **Not run:**
  - Starting either MCP server (`claude mcp list`, `codex debug prompt-input`), because that runs plugin code.
  - Copilot CLI, since it isn't one of the target tools.

The tool versions used (claude 2.1.284, codex-cli 0.157.1) match the versions the skill's references were verified against.

## Tool calls

The arm's tool calls, one JSON object per line, extracted from its transcript.

```jsonl
{"tool": "Bash", "input": {"command": "cd $RUN/repo && cat ../skill/plugin-marketplaces/SKILL.md && ls -R ../skill/plugin-marketplaces && git status && git log --oneline | head && find . -path ./.git -prune -o -type f -print", "description": "Read skill and inspect repo"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && for f in README.md plugins/hello-tools/.mcp.json plugins/hello-tools/.claude-plugin/plugin.json plugins/hello-tools/skills/hello-tools/SKILL.md; do echo \"=== $f\"; cat $f; done; echo; cd ../weather-mcp && git log --oneline --all --decorate | head -20; git tag; find . -path ./.git -prune -o -type f -print", "description": "Read repo files and weather-mcp mirror"}}
{"tool": "Bash", "input": {"command": "cd $RUN/skill/plugin-marketplaces/references && cat multi-tool.md releases.md validation.md", "description": "Read key references"}}
{"tool": "Bash", "input": {"command": "cd $RUN/skill/plugin-marketplaces/references && cat claude-code.md codex.md feature-matrix.md agent-plugins.md", "description": "Read more references"}}
{"tool": "Bash", "input": {"command": "cd $RUN/weather-mcp && git rev-parse 'v1.3.0^{commit}' 'v1.4.0^{commit}'; git show v1.3.0 --stat; for f in server.py .mcp.json README.md .claude-plugin/plugin.json; do echo \"=== $f @v1.3.0\"; git show v1.3.0:$f; done; git ls-tree -r v1.3.0; git remote -v", "description": "Inspect weather-mcp at v1.3.0"}}
{"tool": "Read", "input": {"file_path": "~/.claude/projects/$PROJECT/d3ec4506-6a59-4b62-8c63-8356e427ceab/tool-results/bzqxl1sx0.txt"}}
{"tool": "Bash", "input": {"command": "cd $RUN/skill/plugin-marketplaces/scripts/mpcheck && cat policy.py; cat data/readers.json | head -80; grep -n \"policy\" -r ../../references/*.md | head -30", "description": "Read policy format"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && which claude codex copilot git; cat .gitignore 2>/dev/null; T=\"$PWD/.tool-homes\"; mkdir -p \"$T\"/{home,xdg,tmp,claude,codex,copilot,copilot-cache}; : > \"$T/gitconfig\"; export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\"; claude --version </dev/null; codex --version </dev/null", "description": "Check tool availability with throwaway config"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && mkdir -p .claude-plugin .agents/plugins\ncat > .gitignore <<'EOF'\n.tool-homes/\nEOF\ncat > marketplace-policy.json <<'EOF'\n{\n  \"readers\": [\"claude-code\", \"codex\"],\n  \"exceptions\": [],\n  \"channels\": []\n}\nEOF\ncat > plugins/hello-tools/plugin.json <<'EOF'\n{\n  \"$schema\": \"https://agent-plugins.org/schemas/1.0.0/plugin.schema.json\",\n  \"name\": \"hello-tools\",\n  \"version\": \"0.3.0\",\n  \"description\": \"Greet teammates by name\",\n  \"author\": {\n    \"name\": \"Acme\"\n  }\n}\nEOF\ncat > plugins/hello-tools/mcp.json <<'EOF'\n{\n  \"$schema\": \"https://agent-plugins.org/schemas/1.0.0/mcp.schema.json\",\n  \"mcpServers\": {\n    \"hello\": {\n      \"type\": \"stdio\",\n      \"command\": \"uvx\",\n      \"args\": [\n        \"hello-mcp==0.3.0\"\n      ]\n    }\n  }\n}\nEOF\ncat > .claude-plugin/marketplace.json <<'EOF'\n{\n  \"name\": \"acme-agent-tools\",\n  \"owner\": {\n    \"name\": \"Acme\"\n  },\n  \"metadata\": {\n    \"description\": \"Plugins our team uses with coding agents\"\n  },\n  \"plugins\": [\n    {\n      \"name\": \"hello-tools\",\n      \"source\": \"./plugins/hello-tools\",\n      \"description\": \"Greet teammates by name. Runs a local MCP server (uvx hello-mcp==0.3.0, fetched from PyPI on first start).\",\n      \"version\": \"0.3.0\"\n    },\n    {\n      \"name\": \"weather-mcp\",\n      \"source\": {\n        \"source\": \"url\",\n        \"url\": \"https://github.com/acme/weather-mcp.git\",\n        \"ref\": \"v1.3.0\",\n        \"sha\": \"bdee23e46e072243455f1ba83ce9d8e2d7584e0a\"\n      },\n      \"description\": \"Look up weather forecasts. Runs a local Python MCP server (python3 server.py) that sends city names to the external service api.weather.example.\",\n      \"version\": \"1.3.0\"\n    }\n  ]\n}\nEOF\ncat > .agents/plugins/marketplace.json <<'EOF'\n{\n  \"name\": \"acme-agent-tools\",\n  \"plugins\": [\n    {\n      \"name\": \"hello-tools\",\n      \"source\": {\n        \"source\": \"local\",\n        \"path\": \"./plugins/hello-tools\"\n      },\n      \"description\": \"Greet teammates by name. Runs a local MCP server (uvx hello-mcp==0.3.0, fetched from PyPI on first start).\",\n      \"version\": \"0.3.0\",\n      \"policy\": {\n        \"installation\": \"AVAILABLE\",\n        \"authentication\": \"ON_INSTALL\"\n      },\n      \"category\": \"Productivity\"\n    },\n    {\n      \"name\": \"weather-mcp\",\n      \"source\": {\n        \"source\": \"url\",\n        \"url\": \"https://github.com/acme/weather-mcp.git\",\n        \"ref\": \"v1.3.0\",\n        \"sha\": \"bdee23e46e072243455f1ba83ce9d8e2d7584e0a\"\n      },\n      \"description\": \"Look up weather forecasts. Runs a local Python MCP server (python3 server.py) that sends city names to the external service api.weather.example.\",\n      \"version\": \"1.3.0\",\n      \"policy\": {\n        \"installation\": \"AVAILABLE\",\n        \"authentication\": \"ON_INSTALL\"\n      },\n      \"category\": \"Productivity\"\n    }\n  ]\n}\nEOF\nT=\"$PWD/.tool-homes\"; export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\"\n../validator/bin/check-marketplace . </dev/null; echo \"exit=$?\"", "description": "Write catalogs, policy, portable manifests; run validator"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=\"$PWD/.tool-homes\"; export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\"\nrm -rf \"$T/neg\" && mkdir -p \"$T/neg\" && rsync -a --exclude .tool-homes --exclude .git ./ \"$T/neg/\" && sed -i '' 's/\"version\": \"0.3.0\"/\"version\": \"0.2.0\"/' \"$T/neg/.agents/plugins/marketplace.json\" && sed -i '' 's/\"sha\": \"bdee23e46e072243455f1ba83ce9d8e2d7584e0a\"/\"ref\": \"main\"/' \"$T/neg/.claude-plugin/marketplace.json\"; ../validator/bin/check-marketplace \"$T/neg\" </dev/null; echo \"exit=$?\"", "description": "Negative control for validator"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && R=\"$PWD\"; T=\"$R/.tool-homes\"; M=\"$(cd ../weather-mcp && pwd)\"\nexport HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\"\ncat > \"$T/gitconfig\" <<EOF\n[url \"file://$M\"]\n\tinsteadOf = https://github.com/acme/weather-mcp.git\n[safe]\n\tdirectory = *\nEOF\nrm -f \"$T/idx\"; cp .git/index \"$T/idx\"; GIT_INDEX_FILE=\"$T/idx\" git add -A; TREE=$(GIT_INDEX_FILE=\"$T/idx\" git write-tree); echo tree=$TREE\nrm -rf \"$T/export\" && mkdir -p \"$T/export\" && git archive $TREE | tar -x -C \"$T/export\" && find \"$T/export\" -type f | sed \"s|$T/export/||\"\ngit status --short\necho \"--- remote (mirror) check\"\ngit ls-remote https://github.com/acme/weather-mcp.git </dev/null\nd=\"$T/fetchcheck\"; rm -rf \"$d\"; git init -q \"$d\" && git -C \"$d\" fetch -q --no-tags https://github.com/acme/weather-mcp.git bdee23e46e072243455f1ba83ce9d8e2d7584e0a && git -C \"$d\" cat-file -p FETCH_HEAD | head -3", "description": "Build clean export and check pin against mirror"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && R=\"$PWD\"; T=\"$R/.tool-homes\"\nexport HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\"\nSB=(sandbox-exec -p '(version 1)(allow default)(deny network-outbound (remote ip))')\necho \"--- validate\"; \"${SB[@]}\" claude plugin validate \"$T/export\" --strict --json </dev/null; echo \"exit=$?\"\necho \"--- mkt add\"; \"${SB[@]}\" claude plugin marketplace add \"$T/export\" </dev/null; echo \"exit=$?\"\nfor p in hello-tools weather-mcp; do echo \"--- install $p\"; \"${SB[@]}\" claude plugin install \"$p@acme-agent-tools\" </dev/null; echo \"exit=$?\"; done\necho \"--- list\"; \"${SB[@]}\" claude plugin list --json </dev/null\nfor p in hello-tools weather-mcp; do echo \"--- details $p\"; \"${SB[@]}\" claude plugin details \"$p@acme-agent-tools\" </dev/null; done", "description": "Claude Code discovery and load checks, isolated"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=\"$PWD/.tool-homes\"; head -1 \"$T/claude/plugins/cache/acme-agent-tools/weather-mcp/1.3.0/server.py\"; ls -a \"$T/claude/plugins/cache/acme-agent-tools/weather-mcp/1.3.0\"\nexport HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\"\nSB=(sandbox-exec -p '(version 1)(allow default)(deny network-outbound (remote ip))')\necho \"--- codex mkt add\"; \"${SB[@]}\" codex plugin marketplace add \"$T/export\" </dev/null; echo \"exit=$?\"\necho \"--- codex list\"; \"${SB[@]}\" codex plugin list --available --json </dev/null; echo \"exit=$?\"", "description": "Check Claude cache content; Codex discovery"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=\"$PWD/.tool-homes\"\nexport HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\"\nSB=(sandbox-exec -p '(version 1)(allow default)(deny network-outbound (remote ip))')\nfor p in hello-tools weather-mcp; do echo \"--- codex add $p\"; \"${SB[@]}\" codex plugin add \"$p@acme-agent-tools\" --json </dev/null; echo \"exit=$?\"; done\necho \"--- codex mcp list\"; \"${SB[@]}\" codex mcp list --json </dev/null; echo \"exit=$?\"\nfind \"$T/codex/plugins/cache\" -maxdepth 4 | sed \"s|$T/codex/||\"", "description": "Codex install and MCP inspection"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && cat >> README.md <<'EOF'\n\n## Adding this marketplace\n\nClaude Code reads `.claude-plugin/marketplace.json`, and Codex reads `.agents/plugins/marketplace.json`; `marketplace-policy.json` declares both as readers.\n\n```bash\n# Claude Code\nclaude plugin marketplace add <this repo's git URL or local path>\nclaude plugin install hello-tools@acme-agent-tools\nclaude plugin install weather-mcp@acme-agent-tools\n\n# Codex\ncodex plugin marketplace add <this repo's git URL or local path>\ncodex plugin add hello-tools@acme-agent-tools\ncodex plugin add weather-mcp@acme-agent-tools\n```\n\n`weather-mcp` is pinned to `v1.3.0` (commit `bdee23e46e072243455f1ba83ce9d8e2d7584e0a`).\nIts MCP server does not start in Codex yet: the upstream package ships only a Claude Code manifest, and Codex passes `${CLAUDE_PLUGIN_ROOT}` to the server literally.\nEOF\nT=\"$PWD/.tool-homes\"; export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\"; ../validator/bin/check-marketplace . </dev/null | tail -3; git status --short", "description": "Document usage in README; re-run validator"}}
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
index 0000000..abf790e
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
+      "description": "Greet teammates by name. Runs a local MCP server (uvx hello-mcp==0.3.0, fetched from PyPI on first start).",
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
index 0000000..f86e18e
--- /dev/null
+++ b/.claude-plugin/marketplace.json
@@ -0,0 +1,28 @@
+{
+  "name": "acme-agent-tools",
+  "owner": {
+    "name": "Acme"
+  },
+  "metadata": {
+    "description": "Plugins our team uses with coding agents"
+  },
+  "plugins": [
+    {
+      "name": "hello-tools",
+      "source": "./plugins/hello-tools",
+      "description": "Greet teammates by name. Runs a local MCP server (uvx hello-mcp==0.3.0, fetched from PyPI on first start).",
+      "version": "0.3.0"
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
diff --git a/README.md b/README.md
index 93371c6..b3f6bd6 100644
--- a/README.md
+++ b/README.md
@@ -1,3 +1,22 @@
 # acme-agent-tools
 
 Plugins our team uses with coding agents.
+
+## Adding this marketplace
+
+Claude Code reads `.claude-plugin/marketplace.json`, and Codex reads `.agents/plugins/marketplace.json`; `marketplace-policy.json` declares both as readers.
+
+```bash
+# Claude Code
+claude plugin marketplace add <this repo's git URL or local path>
+claude plugin install hello-tools@acme-agent-tools
+claude plugin install weather-mcp@acme-agent-tools
+
+# Codex
+codex plugin marketplace add <this repo's git URL or local path>
+codex plugin add hello-tools@acme-agent-tools
+codex plugin add weather-mcp@acme-agent-tools
+```
+
+`weather-mcp` is pinned to `v1.3.0` (commit `bdee23e46e072243455f1ba83ce9d8e2d7584e0a`).
+Its MCP server does not start in Codex yet: the upstream package ships only a Claude Code manifest, and Codex passes `${CLAUDE_PLUGIN_ROOT}` to the server literally.
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
master 1cc98c7
```
