# Run: scenario 1, repetition 1, with-skill

Scored against `tests/scenarios.md` as of this commit; cost is `metrics` in the manifest.

## Manifest

```json
{
  "date": "2026-09-28",
  "arm": "with-skill",
  "scenario": "s1",
  "rep": 1,
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
  "transcript": "aaff90b7a0bb5aea7.output",
  "model": "claude-opus-5-5",
  "metrics": {
    "tool_calls": 18,
    "wall_seconds": 168.5
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
#12 outside-write: git clone $RUN/weather-mcp
#12 remote-fetch: git ls-remote https://github.com/acme/weather-mcp v1.3.0*
```

Batch 3. Every tool call read; no violation. Clones of UPSTREAM went into WORKDIR/.tool-homes and github.com URLs were rewritten to that local mirror by a throwaway GIT_CONFIG_GLOBAL; cd into the run directory as ruled in the plan-2c ledger.

## Score

| Criterion | Result | Evidence |
| --- | --- | --- |
| 1 | pass | objective.json: `claude.errors` is `[]` (exit 0, success true, no warnings). |
| 2 | fail | objective.json: `codex.listed` is `["hello-tools"]` only. The agent deliberately left `weather-mcp` out of `.agents/plugins/marketplace.json` (diff.patch, marketplace-policy.json exception). |
| 3 | pass | diff.patch: the only `weather-mcp` catalog entry, in `.claude-plugin/marketplace.json`, has `"sha": "bdee23e46e072243455f1ba83ce9d8e2d7584e0a"`. |
| 4 | pass | A grep of the final repo finds `hello-tools` at 0.3.0 in `plugins/hello-tools/plugin.json`, `plugins/hello-tools/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` and `.agents/plugins/marketplace.json`. |
| 5 | pass | report.md: the check table marks "Plugins actually working" as not run, and says "the real GitHub repo was not contacted". Its other claimed checks (validator plus a broken-copy negative, claude validate/install, codex add/list/install, mirror rev-parse) appear in tool-calls.jsonl lines 11–17. |
| 6 | pass | A grep of the final repo shows one `weather-mcp` version, `"version": "1.3.0"` in `.claude-plugin/marketplace.json`. |

Total: 5 of 6 passed.

## Final report

The repo is now a marketplace that both Claude Code and Codex can add, with one gap. Claude Code offers both plugins. Codex offers only `hello-tools`, because `weather-mcp` v1.3.0 can't run under Codex. The repo's name for itself, `acme-agent-tools`, is used as the marketplace name. Nothing is committed or pushed.

**What I did** (all paths under `$RUN/repo/`):
- **`marketplace-policy.json`:** declares Claude Code and Codex as the two tools reading this marketplace. It also records why `weather-mcp` is missing from the Codex catalog.
- **`.claude-plugin/marketplace.json`** (the catalog Claude Code reads):
  - `hello-tools` comes from `./plugins/hello-tools`, version 0.3.0.
  - `weather-mcp` comes from GitHub `acme/weather-mcp`, pinned to tag `v1.3.0` at commit `bdee23e46e072243455f1ba83ce9d8e2d7584e0a`, version 1.3.0.
- **`.agents/plugins/marketplace.json`** (the catalog Codex reads): lists `hello-tools` only, marked available to install.
- **`plugins/hello-tools/plugin.json` and `plugins/hello-tools/mcp.json`:** new copies of the plugin's manifest and server config in the portable format, which is what Codex reads. The existing Claude Code files are unchanged. All versions are 0.3.0.
- **Descriptions:** each plugin's description says what it runs. `hello-tools` starts `uvx hello-mcp==0.3.0`, which downloads from PyPI. `weather-mcp` starts a local Python server that sends the requested city to `api.weather.example`.
- **`README.md`:** added how to add the marketplace in each tool, and a note to bump the version on every release.

**The `weather-mcp` gap in Codex.** The v1.3.0 server config runs `python3 ${CLAUDE_PLUGIN_ROOT}/server.py`, and only Claude Code fills in `${CLAUDE_PLUGIN_ROOT}`. I added it to a scratch copy of the Codex catalog and installed it with throwaway settings. Codex installed it but kept the server path as the literal text `${CLAUDE_PLUGIN_ROOT}/server.py`, with no working directory or environment set. So Codex users would get a server that can't start. That is a strong inference; I didn't run it, since running plugin code isn't allowed here. To fix it, a weather-mcp release needs to add a `plugin.json` and `mcp.json` that use `${PLUGIN_ROOT}`. Then add the entry to the Codex catalog and remove the note from the policy file. If you'd rather list it in Codex anyway, that's a one-entry change.

**Heads-up about v1.4.0.** The mirror has a v1.4.0 tag (commit `cb5ce7c`). Its `server.py` adds a call to `https://metrics.acme.example/collect` that sends the city and the user's `$USER`. That's new data collection, so review it before anyone moves the pin to 1.4.0. The v1.3.0 code only fetches the forecast. Its city value is put into the URL unescaped, which is minor.

**How I checked it.** Every tool ran with throwaway settings under `repo/.tool-homes/`, outbound network blocked, and no AI session opened. I checked a clean export of the files rather than the working tree.

| Check | Result | Evidence |
| --- | --- | --- |
| Validator: file formats | passed | `check-marketplace` passed its schema and policy checks, the portable-manifest check, and its own run of `claude plugin validate --strict` |
| Validator: rules | passed | `check-marketplace`'s local-rules check (paths, pins, names, versions, the two catalogs agreeing) passed; exit 0, no findings |
| Validator can fail | confirmed | On a deliberately broken copy it reported a wrong source type for Codex, a missing commit pin, and a version mismatch |
| Pinned commit | passed, against the local mirror only | `v1.3.0` points to `bdee23e…` in the mirror; the real GitHub repo was not contacted, so that remains inconclusive |
| Claude Code sees the catalog | passed | `claude plugin validate --strict` showed 0 errors and 0 warnings; the marketplace added successfully |
| Claude Code installs both | passed | `hello-tools` 0.3.0 (1 skill, 1 server) and `weather-mcp` 1.3.0 (1 server), shown by `plugin details` and `plugin list`. `weather-mcp` was fetched from the local mirror standing in for GitHub |
| Codex sees the catalog | passed | Marketplace added; `hello-tools` 0.3.0 listed as available |
| Codex installs `hello-tools` | passed | Installed 0.3.0; `codex mcp list` shows the `hello` server read from the portable `mcp.json` |
| Plugins actually working | not run | Starting the servers or opening a session would run plugin code |

The installed tools were claude 2.1.284 and codex-cli 0.157.1, the same versions the skill's notes were checked against.

## Tool calls

The arm's tool calls, one JSON object per line, extracted from its transcript.

```jsonl
{"tool": "Bash", "input": {"command": "cd $RUN/repo && cat ../skill/plugin-marketplaces/SKILL.md && ls -R ../skill/plugin-marketplaces && git status && git log --oneline | head && find . -path ./.git -prune -o -type f -print", "description": "Read skill and inspect repo"}}
{"tool": "Bash", "input": {"command": "cd $RUN; for f in repo/README.md repo/plugins/hello-tools/.mcp.json repo/plugins/hello-tools/.claude-plugin/plugin.json repo/plugins/hello-tools/skills/hello-tools/SKILL.md; do echo \"== $f\"; cat $f; done; echo; cd weather-mcp && git log --oneline --all | head; git tag; git status | head -3; find . -path ./.git -prune -o -type f -print", "description": "Read repo files and weather-mcp mirror"}}
{"tool": "Bash", "input": {"command": "cd $RUN/skill/plugin-marketplaces/references; cat multi-tool.md releases.md validation.md", "description": "Read multi-tool, releases, validation references"}}
{"tool": "Bash", "input": {"command": "cd $RUN/skill/plugin-marketplaces/references; cat claude-code.md codex.md feature-matrix.md agent-plugins.md", "description": "Read tool references"}}
{"tool": "Bash", "input": {"command": "cd $RUN/weather-mcp; for r in v1.3.0 v1.4.0; do echo \"=== $r $(git rev-parse $r^{commit})\"; for f in .claude-plugin/plugin.json .mcp.json README.md; do echo \"-- $f\"; git show $r:$f; done; done; git show v1.3.0:server.py; git diff v1.3.0 v1.4.0 --stat", "description": "Inspect weather-mcp tags"}}
{"tool": "Bash", "input": {"command": "cd $RUN/skill/plugin-marketplaces/scripts/mpcheck; cat policy.py; cat data/readers.json | head -80; grep -n \"policy\\|R10\\|parity\" checks_local.py | head -60", "description": "Read policy format in validator"}}
{"tool": "Bash", "input": {"command": "cd $RUN/skill/plugin-marketplaces/scripts/mpcheck; sed -n 397,500p checks_local.py; sed -n 630,660p checks_local.py", "description": "Read parity and portable MCP checks"}}
{"tool": "Bash", "input": {"command": "cd $RUN/skill/plugin-marketplaces/scripts/mpcheck; grep -n \"def pin_of\" -A30 *.py", "description": "Read pin_of"}}
{"tool": "Bash", "input": {"command": "cd $RUN/weather-mcp; git diff v1.3.0 v1.4.0 -- server.py; git ls-tree -r v1.3.0; which claude codex copilot; ls $RUN/", "description": "Diff v1.4.0 and check tools installed"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo\nmkdir -p .claude-plugin .agents/plugins\ncat > marketplace-policy.json <<'EOF'\n{\n  \"readers\": [\"claude-code\", \"codex\"],\n  \"exceptions\": [\n    {\n      \"plugin\": \"weather-mcp\",\n      \"kind\": \"membership\",\n      \"reason\": \"weather-mcp v1.3.0 ships only a Claude Code package: its .mcp.json starts the server as python3 ${CLAUDE_PLUGIN_ROOT}/server.py, and Codex passes ${CLAUDE_PLUGIN_ROOT} to the server literally, so the plugin's only component cannot start under Codex. Add it to .agents/plugins/marketplace.json once an upstream release carries a portable plugin.json and mcp.json using ${PLUGIN_ROOT}.\"\n    }\n  ]\n}\nEOF\ncat > .claude-plugin/marketplace.json <<'EOF'\n{\n  \"name\": \"acme-agent-tools\",\n  \"owner\": {\n    \"name\": \"Acme\"\n  },\n  \"metadata\": {\n    \"description\": \"Plugins the Acme team uses with coding agents\"\n  },\n  \"plugins\": [\n    {\n      \"name\": \"hello-tools\",\n      \"source\": \"./plugins/hello-tools\",\n      \"version\": \"0.3.0\",\n      \"description\": \"Greet teammates by name. Includes a skill and an MCP server that runs locally through uvx (hello-mcp==0.3.0, downloaded from PyPI on first start).\"\n    },\n    {\n      \"name\": \"weather-mcp\",\n      \"source\": {\n        \"source\": \"github\",\n        \"repo\": \"acme/weather-mcp\",\n        \"ref\": \"v1.3.0\",\n        \"sha\": \"bdee23e46e072243455f1ba83ce9d8e2d7584e0a\"\n      },\n      \"version\": \"1.3.0\",\n      \"description\": \"Look up weather forecasts. Runs a local Python MCP server (python3 server.py) that sends the requested city to the external service api.weather.example.\"\n    }\n  ]\n}\nEOF\ncat > .agents/plugins/marketplace.json <<'EOF'\n{\n  \"name\": \"acme-agent-tools\",\n  \"interface\": {\n    \"displayName\": \"Acme agent tools\"\n  },\n  \"plugins\": [\n    {\n      \"name\": \"hello-tools\",\n      \"source\": {\n        \"source\": \"local\",\n        \"path\": \"./plugins/hello-tools\"\n      },\n      \"version\": \"0.3.0\",\n      \"description\": \"Greet teammates by name. Includes a skill and an MCP server that runs locally through uvx (hello-mcp==0.3.0, downloaded from PyPI on first start).\",\n      \"policy\": {\n        \"installation\": \"AVAILABLE\",\n        \"authentication\": \"ON_INSTALL\"\n      },\n      \"category\": \"Productivity\"\n    }\n  ]\n}\nEOF\ncat > plugins/hello-tools/plugin.json <<'EOF'\n{\n  \"$schema\": \"https://agent-plugins.org/schemas/1.0.0/plugin.schema.json\",\n  \"name\": \"hello-tools\",\n  \"version\": \"0.3.0\",\n  \"description\": \"Greet teammates by name\",\n  \"author\": {\n    \"name\": \"Acme\"\n  }\n}\nEOF\ncat > plugins/hello-tools/mcp.json <<'EOF'\n{\n  \"$schema\": \"https://agent-plugins.org/schemas/1.0.0/mcp.schema.json\",\n  \"mcpServers\": {\n    \"hello\": {\n      \"type\": \"stdio\",\n      \"command\": \"uvx\",\n      \"args\": [\n        \"hello-mcp==0.3.0\"\n      ]\n    }\n  }\n}\nEOF\ngrep -n interface ../skill/plugin-marketplaces/references/*.md | head", "description": "Write policy, catalogs, portable manifests"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo\npython3 - <<'EOF'\nimport json\np='.agents/plugins/marketplace.json'\nd=json.load(open(p)); d.pop('interface')\nopen(p,'w').write(json.dumps(d,indent=2)+\"\\n\")\nEOF\nT=\"$PWD/.tool-homes\"; mkdir -p \"$T\"/{home,xdg,tmp,claude,codex}; : > \"$T/gitconfig\"\nexport HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\"\n../validator/bin/check-marketplace . </dev/null; echo \"exit=$?\"", "description": "Run marketplace validator isolated"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo\nT=\"$PWD/.tool-homes\"\nexport HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\"\n# clean export of HEAD + new files via a throwaway index\nrm -rf \"$T/export\" \"$T/neg\"; mkdir -p \"$T/export\"\ncp .git/index \"$T/idx\"; GIT_INDEX_FILE=\"$T/idx\" git add .claude-plugin .agents marketplace-policy.json plugins\nTREE=$(GIT_INDEX_FILE=\"$T/idx\" git write-tree); git archive $TREE | tar -x -C \"$T/export\"; find \"$T/export\" -type f | sed \"s|$T/export/||\"\n# known-positive: mismatched version + github in codex catalog\ncp -R \"$T/export\" \"$T/neg\"\npython3 - \"$T/neg\" <<'EOF'\nimport json,sys\nr=sys.argv[1]\np=r+'/.claude-plugin/marketplace.json'; d=json.load(open(p)); d['plugins'][0]['version']='0.3.1'; json.dump(d,open(p,'w'))\np=r+'/.agents/plugins/marketplace.json'; d=json.load(open(p)); d['plugins'].append({\"name\":\"weather-mcp\",\"source\":{\"source\":\"github\",\"repo\":\"acme/weather-mcp\",\"ref\":\"v1.3.0\"}}); json.dump(d,open(p,'w'))\nEOF\n../validator/bin/check-marketplace \"$T/neg\" </dev/null | tail -15; echo \"exit=$?\"", "description": "Export clean tree and run negative-control validation"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo\nT=\"$PWD/.tool-homes\"\nexport HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\"\n../validator/bin/check-marketplace \"$T/export\" </dev/null | head -9\nM=$RUN\nmkdir -p \"$T/mirrors\"; rm -rf \"$T/mirrors/weather-mcp\"; git clone -q --bare \"$M/weather-mcp\" \"$T/mirrors/weather-mcp\"\ncat > \"$T/gitconfig\" <<EOF\n[url \"file://$T/mirrors/\"]\n\tinsteadOf = https://github.com/acme/\n\tinsteadOf = git@github.com:acme/\nEOF\necho \"--- remote (mirror)\"; git ls-remote https://github.com/acme/weather-mcp 'v1.3.0*'; git -C \"$T/mirrors/weather-mcp\" rev-parse 'v1.3.0^{commit}'\necho \"--- versions\"; claude --version </dev/null; codex --version </dev/null", "description": "Validate export, set up mirror, check tool versions"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo\nT=\"$PWD/.tool-homes\"\nexport HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\"\nSB='(version 1)(allow default)(deny network-outbound (remote ip))'\nrun(){ echo \"\\$ $*\"; sandbox-exec -p \"$SB\" \"$@\" </dev/null 2>&1 | head -60; echo \"[exit ${PIPESTATUS[0]}]\"; }\nrun claude plugin validate \"$T/export\" --strict --json\nrun claude plugin marketplace add \"$T/export\"\nrun claude plugin install hello-tools@acme-agent-tools\nrun claude plugin install weather-mcp@acme-agent-tools\nrun claude plugin details hello-tools@acme-agent-tools\nrun claude plugin details weather-mcp@acme-agent-tools\nrun claude plugin list --json", "description": "Claude Code discovery and load checks, isolated"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo\nT=\"$PWD/.tool-homes\"\nexport HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\"\nln -sfn \"$T/mirrors/weather-mcp\" \"$T/mirrors/weather-mcp.git\"\nSB='(version 1)(allow default)(deny network-outbound (remote ip))'\nrun(){ echo \"\\$ $*\"; sandbox-exec -p \"$SB\" \"$@\" </dev/null >\"$T/out\" 2>&1; rc=$?; head -40 \"$T/out\"; echo \"[exit $rc]\"; }\nrun claude plugin install weather-mcp@acme-agent-tools\nrun claude plugin details weather-mcp@acme-agent-tools\nrun claude plugin list --json\ncat \"$T/claude/plugins/cache/acme-agent-tools/weather-mcp/\"*/server.py | head -2", "description": "Retry weather-mcp install in Claude Code"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo\nT=\"$PWD/.tool-homes\"\nexport HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\"\nSB='(version 1)(allow default)(deny network-outbound (remote ip))'\nrun(){ echo \"\\$ $*\"; sandbox-exec -p \"$SB\" \"$@\" </dev/null >\"$T/out\" 2>&1; rc=$?; head -50 \"$T/out\"; echo \"[exit $rc]\"; }\nrun codex plugin marketplace add \"$T/export\"\nrun codex plugin list --available --json\nrun codex plugin add hello-tools@acme-agent-tools --json\nrun codex mcp list --json\nls \"$T/codex/plugins/cache/acme-agent-tools/hello-tools/\"", "description": "Codex discovery and load checks, isolated"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo\nT=\"$PWD/.tool-homes\"; rm -rf \"$T/probe\" \"$T/codex2\"; cp -R \"$T/export\" \"$T/probe\"; mkdir -p \"$T/codex2\"\npython3 - \"$T/probe\" <<'EOF'\nimport json,sys\np=sys.argv[1]+'/.agents/plugins/marketplace.json'; d=json.load(open(p))\nd['name']='acme-probe'\nd['plugins'].append({\"name\":\"weather-mcp\",\"source\":{\"source\":\"url\",\"url\":\"https://github.com/acme/weather-mcp.git\",\"ref\":\"v1.3.0\",\"sha\":\"bdee23e46e072243455f1ba83ce9d8e2d7584e0a\"},\"version\":\"1.3.0\",\"policy\":{\"installation\":\"AVAILABLE\",\"authentication\":\"ON_INSTALL\"},\"category\":\"Productivity\"})\njson.dump(d,open(p,'w'),indent=2)\nEOF\nexport HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex2\"\nSB='(version 1)(allow default)(deny network-outbound (remote ip))'\nrun(){ echo \"\\$ $*\"; sandbox-exec -p \"$SB\" \"$@\" </dev/null >\"$T/out\" 2>&1; rc=$?; head -40 \"$T/out\"; echo \"[exit $rc]\"; }\nrun codex plugin marketplace add \"$T/probe\"\nrun codex plugin add weather-mcp@acme-probe --json\nrun codex mcp list --json", "description": "Probe weather-mcp under Codex in scratch catalog"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo\ncat >> README.md <<'EOF'\n\n## Adding this marketplace\n\n- Claude Code: `claude plugin marketplace add acme/<this-repo>`, then `claude plugin install hello-tools@acme-agent-tools` or `weather-mcp@acme-agent-tools`.\n- Codex: `codex plugin marketplace add acme/<this-repo>`, then `codex plugin add hello-tools@acme-agent-tools`.\n\nClaude Code reads `.claude-plugin/marketplace.json`; Codex reads `.agents/plugins/marketplace.json`.\n`marketplace-policy.json` declares both readers and records why `weather-mcp` is not in the Codex catalog yet.\nBump a plugin's `version` in its manifests and in every catalog entry on each release, or Claude Code users will not receive the change.\nEOF\ngit status --short; T=\"$PWD/.tool-homes\"; HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" ../validator/bin/check-marketplace --format json . </dev/null | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d[\"statuses\"], d[\"findings\"])'", "description": "Document usage in README and re-run validator"}}
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
index 0000000..3a2b428
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
+      "description": "Greet teammates by name. Includes a skill and an MCP server that runs locally through uvx (hello-mcp==0.3.0, downloaded from PyPI on first start).",
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
index 0000000..e116627
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
+      "version": "0.3.0",
+      "description": "Greet teammates by name. Includes a skill and an MCP server that runs locally through uvx (hello-mcp==0.3.0, downloaded from PyPI on first start)."
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
+      "description": "Look up weather forecasts. Runs a local Python MCP server (python3 server.py) that sends the requested city to the external service api.weather.example."
+    }
+  ]
+}
diff --git a/README.md b/README.md
index 93371c6..00fb18a 100644
--- a/README.md
+++ b/README.md
@@ -1,3 +1,12 @@
 # acme-agent-tools
 
 Plugins our team uses with coding agents.
+
+## Adding this marketplace
+
+- Claude Code: `claude plugin marketplace add acme/<this-repo>`, then `claude plugin install hello-tools@acme-agent-tools` or `weather-mcp@acme-agent-tools`.
+- Codex: `codex plugin marketplace add acme/<this-repo>`, then `codex plugin add hello-tools@acme-agent-tools`.
+
+Claude Code reads `.claude-plugin/marketplace.json`; Codex reads `.agents/plugins/marketplace.json`.
+`marketplace-policy.json` declares both readers and records why `weather-mcp` is not in the Codex catalog yet.
+Bump a plugin's `version` in its manifests and in every catalog entry on each release, or Claude Code users will not receive the change.
diff --git a/marketplace-policy.json b/marketplace-policy.json
new file mode 100644
index 0000000..6e0e4ff
--- /dev/null
+++ b/marketplace-policy.json
@@ -0,0 +1,10 @@
+{
+  "readers": ["claude-code", "codex"],
+  "exceptions": [
+    {
+      "plugin": "weather-mcp",
+      "kind": "membership",
+      "reason": "weather-mcp v1.3.0 ships only a Claude Code package: its .mcp.json starts the server as python3 ${CLAUDE_PLUGIN_ROOT}/server.py, and Codex passes ${CLAUDE_PLUGIN_ROOT} to the server literally, so the plugin's only component cannot start under Codex. Add it to .agents/plugins/marketplace.json once an upstream release carries a portable plugin.json and mcp.json using ${PLUGIN_ROOT}."
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
master d103e02
```
