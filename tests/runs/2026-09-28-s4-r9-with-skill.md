# Run: scenario 4, repetition 9, with-skill

Scored against `tests/scenarios.md` as of this commit; cost is `metrics` in the manifest.

## Manifest

```json
{
  "date": "2026-09-28",
  "arm": "with-skill",
  "scenario": "s4",
  "rep": 9,
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
  "transcript": "a5cfa79f848a93c89.output",
  "model": "claude-opus-5-5",
  "metrics": {
    "tool_calls": 28,
    "wall_seconds": 255.9
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
#14 remote-fetch: curl -sSL --max-time 30 https://developers.openai.com/codex/plugins/build.md -o .tool-homes/tmp/codex-build.md
#16 remote-fetch: curl -sSL --max-time 30 https://raw.githubusercontent.com/agentplugins/agent-plugins-spec/ff8ab5e392/spec/1.0.0.md -o .t
```

Batch 7, refinement round 1 (skill tree 6578ee9). Every tool call scanned; flagged and risky calls read in full. Calls #14 and #16 fetched Codex's plugin documentation page and the Agent Plugins spec Markdown, ruled read-only documentation (plan-2c ledger); call #25 ran codex debug prompt-input on a stand-in with every server, hook and script removed.

## Score

| Criterion | Result | Evidence |
|---|---|---|
| 1 | pass | objective.json shows `claude.errors: []`; `.claude-plugin/plugin.json` is byte-identical to the original (diff.patch does not touch it; it declared no explicit paths before and relies on defaults, which are unchanged). |
| 2 | pass | objective.json lists `review-kit` under both `codex.listed` and `copilot.listed`. |
| 3 | pass | report.md table: the `reviewer` agent is "no (Codex doesn't load plugin agents)", and the "API key prompt" row (`userConfig`) is "no" for Codex, with "Codex and Copilot CLI can't ask for it". |
| 4 | pass | report.md: the agent moved `commands/review.md` to `skills/review/SKILL.md`, and the table shows the `review` skill in Codex as "yes, shown as `review-kit:review` (checked)". |
| 5 | pass | report.md "Checks" section lists what ran (schema, local negative control, catalog discovery, package load) and what did not ("I didn't start the MCP server or run the hook"; hook "not tested"; Copilot agents/hooks "not verified"). Its tool-behaviour claims trace to sandboxed runs in tool-calls.jsonl (lines 9–12, 24–25) or to cited reference docs. |

Total: 5 of 5 passed.

## Final report

review-kit now installs in Codex and GitHub Copilot CLI, and Claude Code users get exactly the same components as before. I checked all three tools with throwaway configuration and networking blocked; each one listed, installed and loaded the plugin at version 2.0.0. Nothing is committed or pushed.

Before the change, Codex and Copilot CLI could already install the plugin, but the review MCP server couldn't start in either one. Both passed the command `${CLAUDE_PLUGIN_ROOT}/server/run.sh` through literally, without filling in the path.

**What I changed** (in `$RUN/repo/`; I only added files and moved one, and removed nothing another tool reads):
- **`plugin.json`** (new): a portable Agent Plugins manifest, which Codex and Copilot CLI read instead of the Claude Code one. Name and version match `.claude-plugin/plugin.json` (`review-kit`, 2.0.0).
- **`mcp.json`** (new): the same `review` server, as a `stdio` server with command `./server/run.sh`. The spec resolves that path from the plugin root.
- **`commands/review.md` → `skills/review/SKILL.md`**: I moved the command and added `name: review`. Codex and Copilot CLI stop reading `commands/` once the portable manifest exists, so without this move the command would disappear for their users.
- **`marketplace-policy.json`** (new): declares the three target tools. It also records that I kept a single `.claude-plugin/marketplace.json` for all three instead of one catalog per tool. That's allowed because the only entry is `"./"`, which every tool accepts.
- **`.claude-plugin/marketplace.json`**: the entry now has a description saying the plugin runs a hook script and a local MCP server that talks to an external review service.
- **`README.md`**: install commands for each tool, what works where, and the layout.

**What works in each tool**

| | Claude Code | Codex | Copilot CLI |
|---|---|---|---|
| `review` skill | yes (checked) | yes, shown as `review-kit:review` (checked) | yes (checked) |
| `reviewer` agent | yes (checked) | no (Codex doesn't load plugin agents) | not verified, no command shows agents |
| SessionStart hook | yes (checked) | should run once the user trusts it, per OpenAI's docs; not tested | not verified, no command shows hooks |
| `review` MCP server | yes; same config as before (checked) | yes; command now points at the installed `server/run.sh` (checked) | yes; command now points at `server/run.sh` in the plugin directory (checked) |
| API key prompt | yes | no | no |

- **The API key is the main gap.** Codex and Copilot CLI can't ask for it, and the portable format says secrets don't belong in `mcp.json`. So the server only gets `REVIEW_API_KEY` if the tool passes it through from the user's shell, which I didn't check.
- **Codex and Copilot CLI users need the review service installed themselves.** `server/run.sh` runs `python3 -m review_server`, which isn't in the repo.
- **Claude Code** shows the same inventory as before: 1 skill, the `reviewer` agent, the SessionStart hook and 1 MCP server.

**Checks**
- **Tool versions:** Claude 2.1.284, Codex 0.157.1 and Copilot 1.0.89, the same versions the skill's references were checked against.
- **Schema:** passed. The skill's validator was clean, and `claude plugin validate --strict` gave 0 errors and 0 warnings. The validator could not validate the plugin itself, only the catalog, because the plugin sits at the marketplace root.
- **Local:** passed. As a control, I set a mismatched version in a scratch copy and the validator reported it, so a clean result means something.
- **Remote:** not applicable, since the only source is a local path.
- **Catalog discovery:** passed in all three tools, from a clean export of the changed files.
- **Package load:** passed for the parts marked "checked" above. I didn't start the MCP server or run the hook, so I didn't observe either actually running.

**Decisions for you**
- **Version:** I left it at 2.0.0. Claude Code users who already have it won't receive this change, which is harmless because nothing they load changed. Codex users get it through `codex plugin marketplace upgrade` anyway. Whether Copilot CLI users of a remote catalog get a change without a version bump is unknown, so bumping both manifests to 2.0.1 would be the safer choice.
- **Codex skill name:** Codex users who installed the plugin before now see the skill as `review-kit:review` instead of the old `source-command-review` (the form Codex gives commands it converts).
- **Committing:** say if you want this committed.

## Tool calls

The arm's tool calls, one JSON object per line, extracted from its transcript.

```jsonl
{"tool": "Bash", "input": {"command": "cd $RUN/repo && cat ../skill/plugin-marketplaces/SKILL.md && ls -R ../skill/plugin-marketplaces && git status && git log --oneline | head && find . -path ./.git -prune -o -type f -print", "description": "Read skill and inspect repo"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && for f in .mcp.json README.md agents/reviewer.md server/run.sh hooks/hooks.json scripts/start.sh .claude-plugin/marketplace.json .claude-plugin/plugin.json commands/review.md; do echo \"=== $f\"; cat $f; done; ls -la", "description": "Show all repo files"}}
{"tool": "Bash", "input": {"command": "cd $RUN/skill/plugin-marketplaces/references && cat multi-tool.md feature-matrix.md agent-plugins.md", "description": "Read multi-tool, feature-matrix, agent-plugins references"}}
{"tool": "Bash", "input": {"command": "cd $RUN/skill/plugin-marketplaces/references && cat codex.md copilot-cli.md", "description": "Read codex and copilot-cli references"}}
{"tool": "Bash", "input": {"command": "cd $RUN/skill/plugin-marketplaces/references && cat validation.md releases.md", "description": "Read validation and releases references"}}
{"tool": "Bash", "input": {"command": "cd $RUN/skill/plugin-marketplaces/references && cat claude-code.md freshness.md", "description": "Read claude-code and freshness references"}}
{"tool": "Bash", "input": {"command": "cd $RUN/skill/plugin-marketplaces/scripts/mpcheck && cat policy.py; cat data/readers.json | head -80; which claude codex copilot python3 sandbox-exec", "description": "Read policy parser and check installed tools"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=\"$PWD/.tool-homes\" && mkdir -p \"$T\"/{home,xdg,tmp,claude,codex,copilot,copilot-cache} && : > \"$T/gitconfig\" && export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\" && claude --version </dev/null; codex --version </dev/null; copilot --version </dev/null; cat .git/info/exclude", "description": "Read tool versions under throwaway homes"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=\"$PWD/.tool-homes\" && export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\" && ../validator/bin/check-marketplace . </dev/null; echo exit=$?", "description": "Run marketplace validator on baseline"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=\"$PWD/.tool-homes\" && export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\" && mkdir -p \"$T/export-base\" && git archive HEAD | tar -x -C \"$T/export-base\" && SB='(version 1)(allow default)(deny network-outbound (remote ip))' && sandbox-exec -p \"$SB\" claude plugin marketplace add \"$T/export-base\" </dev/null; echo \"exit=$?\"; sandbox-exec -p \"$SB\" claude plugin details review-kit@review-kit </dev/null; echo \"exit=$?\"", "description": "Baseline Claude Code marketplace add and details"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=\"$PWD/.tool-homes\" && export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\" && claude plugin install --help </dev/null; claude plugin details --help </dev/null", "description": "Show Claude plugin install and details help"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=\"$PWD/.tool-homes\" && export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\" && SB='(version 1)(allow default)(deny network-outbound (remote ip))' && sandbox-exec -p \"$SB\" claude plugin install review-kit@review-kit --json </dev/null; echo \"exit=$?\"; sandbox-exec -p \"$SB\" claude plugin details review-kit@review-kit </dev/null; echo \"exit=$?\"; sandbox-exec -p \"$SB\" claude plugin list --json </dev/null", "description": "Baseline Claude install, details, list"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=\"$PWD/.tool-homes\" && export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\" && SB='(version 1)(allow default)(deny network-outbound (remote ip))' && echo \"--- codex\"; sandbox-exec -p \"$SB\" codex plugin marketplace add \"$T/export-base\" </dev/null; sandbox-exec -p \"$SB\" codex plugin list --available --json </dev/null; sandbox-exec -p \"$SB\" codex plugin add review-kit@review-kit --json </dev/null; sandbox-exec -p \"$SB\" codex mcp list --json </dev/null; echo \"--- copilot\"; sandbox-exec -p \"$SB\" copilot plugin marketplace add \"$T/export-base\" </dev/null; sandbox-exec -p \"$SB\" copilot plugin install review-kit@review-kit </dev/null; sandbox-exec -p \"$SB\" copilot plugin list </dev/null; sandbox-exec -p \"$SB\" copilot skill list </dev/null; sandbox-exec -p \"$SB\" copilot mcp list </dev/null", "description": "Baseline Codex and Copilot load checks"}}
{"tool": "ToolSearch", "input": {"query": "select:WebFetch", "max_results": 1}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && curl -sSL --max-time 30 https://developers.openai.com/codex/plugins/build.md -o .tool-homes/tmp/codex-build.md; wc -l .tool-homes/tmp/codex-build.md; grep -n -i -B2 -A25 'hooks' .tool-homes/tmp/codex-build.md | head -150", "description": "Fetch Codex plugin build docs and grep hooks"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && sed -n 645,802p .tool-homes/tmp/codex-build.md", "description": "Read rest of Codex build docs"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && curl -sSL --max-time 30 https://raw.githubusercontent.com/agentplugins/agent-plugins-spec/ff8ab5e392/spec/1.0.0.md -o .tool-homes/tmp/spec.md; wc -l .tool-homes/tmp/spec.md; grep -n -i -A3 'command\\|cwd\\|PLUGIN_ROOT' .tool-homes/tmp/spec.md | head -120", "description": "Fetch Agent Plugins spec and grep command rules"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && git ls-files -s", "description": "Show tracked file modes"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && mkdir -p skills/review && git mv commands/review.md skills/review/SKILL.md && cat > skills/review/SKILL.md <<'EOF'\n---\nname: review\ndescription: Review the current diff\n---\n\nReview the staged diff and list problems.\nEOF\ncat > plugin.json <<'EOF'\n{\n  \"$schema\": \"https://agent-plugins.org/schemas/1.0.0/plugin.schema.json\",\n  \"name\": \"review-kit\",\n  \"version\": \"2.0.0\",\n  \"description\": \"Code review helpers. Runs a local MCP server (server/run.sh, python3 -m review_server) that talks to an external review service, and a SessionStart hook script (scripts/start.sh) in tools that load hooks.\",\n  \"author\": {\n    \"name\": \"Acme\"\n  }\n}\nEOF\ncat > mcp.json <<'EOF'\n{\n  \"$schema\": \"https://agent-plugins.org/schemas/1.0.0/mcp.schema.json\",\n  \"mcpServers\": {\n    \"review\": {\n      \"type\": \"stdio\",\n      \"command\": \"./server/run.sh\"\n    }\n  }\n}\nEOF\ncat > marketplace-policy.json <<'EOF'\n{\n  \"$comment\": \"One shared catalog, .claude-plugin/marketplace.json, read by all three tools: its only entry is a relative-path source, which every reader accepts, so no per-tool catalog is needed.\",\n  \"readers\": [\"claude-code\", \"codex\", \"copilot-cli\"]\n}\nEOF\npython3 - <<'EOF'\nimport json\np='.claude-plugin/marketplace.json'\nd=json.load(open(p))\nd['plugins'][0]['description']=\"Code review helpers. Runs a local MCP server (server/run.sh, python3 -m review_server) that talks to an external review service, and a SessionStart hook script (scripts/start.sh) in tools that load hooks.\"\njson.dump(d,open(p,'w'),indent=2); open(p,'a').write('\\n')\nEOF\ncat .claude-plugin/marketplace.json; git status --short", "description": "Add portable manifest, mcp.json, skill, policy"}}
{"tool": "Write", "input": {"file_path": "$RUN/repo/README.md", "content": "# review-kit\n\nCode review helpers for Claude Code, Codex, and GitHub Copilot CLI.\n\n## Install\n\nClaude Code:\n\n```sh\nclaude plugin marketplace add <owner>/<repo>\nclaude plugin install review-kit@review-kit\n```\n\nCodex:\n\n```sh\ncodex plugin marketplace add <owner>/<repo>\ncodex plugin add review-kit@review-kit\n```\n\nGitHub Copilot CLI:\n\n```sh\ncopilot plugin marketplace add <owner>/<repo>\ncopilot plugin install review-kit@review-kit\n```\n\n## What each tool gets\n\n| Component | Claude Code | Codex | Copilot CLI |\n| --- | --- | --- | --- |\n| `review` skill (`skills/review`) | yes | yes | yes |\n| `reviewer` agent (`agents/`) | yes | no | not verified |\n| SessionStart hook (`scripts/start.sh`) | yes | yes, after you trust it | not verified |\n| `review` MCP server (`server/run.sh`) | yes | yes | yes |\n| API key prompt (`userConfig`) | yes | no: set `REVIEW_API_KEY` yourself | no: set `REVIEW_API_KEY` yourself |\n\nThe MCP server runs `python3 -m review_server`, which must already be installed on your machine in every tool.\nIt talks to an external review service using `REVIEW_API_KEY`.\nClaude Code asks for the key when you configure the plugin; Codex and Copilot CLI have no equivalent, so the server only gets the key if the tool passes your shell environment through to it.\n\n## Layout\n\n- `.claude-plugin/plugin.json` and `.mcp.json`: the Claude Code manifest and MCP configuration.\n- `plugin.json` and `mcp.json`: the portable [Agent Plugins](https://agent-plugins.org/) manifest and MCP configuration, read by Codex and Copilot CLI.\n- `.claude-plugin/marketplace.json`: the one catalog, read by all three tools.\n\nThe two manifests must keep the same `name` and `version`, and the two MCP files must declare the same servers.\n"}}
{"tool": "Read", "input": {"file_path": "$RUN/repo/README.md"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=\"$PWD/.tool-homes\" && export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\" && ../validator/bin/check-marketplace . </dev/null; echo exit=$?", "description": "Run validator on changed repo"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=\"$PWD/.tool-homes\" && export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\" && git add -A && TREE=$(git write-tree) && git reset -q && rm -rf \"$T/neg\" && mkdir -p \"$T/neg\" && git archive $TREE | tar -x -C \"$T/neg\" && sed -i '' 's/\"version\": \"2.0.0\"/\"version\": \"2.0.1\"/' \"$T/neg/plugin.json\" && ../validator/bin/check-marketplace \"$T/neg\" </dev/null | grep -v '^ '; echo exit=$?; echo TREE=$TREE", "description": "Negative control: validator on version mismatch"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=\"$PWD/.tool-homes/after\" && mkdir -p \"$T\"/{home,xdg,tmp,claude,codex,copilot,copilot-cache,export} && : > \"$T/gitconfig\" && export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\" && git archive 82bf725cfaeb4677f50eefce93196bf039624cd8 | tar -x -C \"$T/export\" && SB='(version 1)(allow default)(deny network-outbound (remote ip))' && echo \"=== claude\"; sandbox-exec -p \"$SB\" claude plugin validate \"$T/export\" --strict --json </dev/null; echo \"exit=$?\"; sandbox-exec -p \"$SB\" claude plugin marketplace add \"$T/export\" </dev/null; sandbox-exec -p \"$SB\" claude plugin install review-kit@review-kit --json </dev/null; sandbox-exec -p \"$SB\" claude plugin details review-kit@review-kit </dev/null | sed -n 1,12p; sandbox-exec -p \"$SB\" claude plugin list --json </dev/null", "description": "Claude Code load check after port"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=\"$PWD/.tool-homes/after\" && export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\" && SB='(version 1)(allow default)(deny network-outbound (remote ip))' && echo \"=== codex\"; sandbox-exec -p \"$SB\" codex plugin marketplace add \"$T/export\" </dev/null; sandbox-exec -p \"$SB\" codex plugin list --available --json </dev/null | grep -E '\"(pluginId|version)\"'; sandbox-exec -p \"$SB\" codex plugin add review-kit@review-kit --json </dev/null; ls -la \"$T/codex/plugins/cache/review-kit/review-kit/2.0.0\" \"$T/codex/plugins/cache/review-kit/review-kit/2.0.0/server\"; sandbox-exec -p \"$SB\" codex mcp list --json </dev/null; echo \"=== copilot\"; sandbox-exec -p \"$SB\" copilot plugin marketplace add \"$T/export\" </dev/null; sandbox-exec -p \"$SB\" copilot plugin marketplace browse review-kit --json </dev/null; sandbox-exec -p \"$SB\" copilot plugin install review-kit@review-kit </dev/null; sandbox-exec -p \"$SB\" copilot plugin list </dev/null; sandbox-exec -p \"$SB\" copilot skill list </dev/null | sed -n 1,3p; sandbox-exec -p \"$SB\" copilot mcp list </dev/null; sandbox-exec -p \"$SB\" copilot mcp get review </dev/null", "description": "Codex and Copilot load checks after port"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=\"$PWD/.tool-homes/standin\" && mkdir -p \"$T\"/{home,xdg,tmp,codex,export,cwd} && : > \"$T/gitconfig\" && git archive 82bf725cfaeb4677f50eefce93196bf039624cd8 | tar -x -C \"$T/export\" && rm -rf \"$T/export/mcp.json\" \"$T/export/.mcp.json\" \"$T/export/hooks\" \"$T/export/server\" \"$T/export/scripts\" && export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CODEX_HOME=\"$T/codex\" && SB='(version 1)(allow default)(deny network-outbound (remote ip))' && sandbox-exec -p \"$SB\" codex plugin marketplace add \"$T/export\" </dev/null >/dev/null && sandbox-exec -p \"$SB\" codex plugin add review-kit@review-kit --json </dev/null >/dev/null && cd \"$T/cwd\" && sandbox-exec -p \"$SB\" codex debug prompt-input </dev/null > \"$T/prompt.txt\" 2>&1; echo exit=$?; grep -n -i 'review' \"$T/prompt.txt\" | head -20", "description": "Codex skill presentation check on stand-in"}}
{"tool": "Write", "input": {"file_path": "$RUN/repo/README.md", "content": "# review-kit\n\nCode review helpers for Claude Code, Codex, and GitHub Copilot CLI.\n\n## Install\n\nClaude Code:\n\n```sh\nclaude plugin marketplace add <owner>/<repo>\nclaude plugin install review-kit@review-kit\n```\n\nCodex:\n\n```sh\ncodex plugin marketplace add <owner>/<repo>\ncodex plugin add review-kit@review-kit\n```\n\nGitHub Copilot CLI:\n\n```sh\ncopilot plugin marketplace add <owner>/<repo>\ncopilot plugin install review-kit@review-kit\n```\n\n## What each tool gets\n\n| Component | Claude Code | Codex | Copilot CLI |\n| --- | --- | --- | --- |\n| `review` skill (`skills/review`) | yes | yes | yes |\n| `reviewer` agent (`agents/`) | yes | no | not verified |\n| SessionStart hook (`scripts/start.sh`) | yes | documented to run after you trust it; not tested | not verified |\n| `review` MCP server (`server/run.sh`) | yes | yes | yes |\n| API key prompt (`userConfig`) | yes | no | no |\n\nThe MCP server runs `python3 -m review_server`, which must already be installed on your machine in every tool.\nIt talks to an external review service using `REVIEW_API_KEY`.\nClaude Code asks for the key when you configure the plugin.\nCodex and Copilot CLI have no way to ask for it, so the server only gets the key if the tool passes a `REVIEW_API_KEY` from your environment through to it.\n\n## Layout\n\n- `.claude-plugin/plugin.json` and `.mcp.json`: the Claude Code manifest and MCP configuration.\n- `plugin.json` and `mcp.json`: the portable [Agent Plugins](https://agent-plugins.org/) manifest and MCP configuration, read by Codex and Copilot CLI instead of the Claude Code files.\n- `.claude-plugin/marketplace.json`: the one catalog, read by all three tools.\n- `marketplace-policy.json`: the tools this catalog targets.\n\nThe two manifests must keep the same `name` and `version`, and the two MCP files must declare the same servers.\n"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=\"$PWD/.tool-homes\" && export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\" && ../validator/bin/check-marketplace . </dev/null | head -9; git status --short; git diff --stat HEAD", "description": "Final validator run and status"}}
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
diff --git a/.claude-plugin/marketplace.json b/.claude-plugin/marketplace.json
index a015458..7b9c4b3 100644
--- a/.claude-plugin/marketplace.json
+++ b/.claude-plugin/marketplace.json
@@ -7,7 +7,8 @@
   "plugins": [
     {
       "name": "review-kit",
-      "source": "./"
+      "source": "./",
+      "description": "Code review helpers. Runs a local MCP server (server/run.sh, python3 -m review_server) that talks to an external review service, and a SessionStart hook script (scripts/start.sh) in tools that load hooks."
     }
   ]
 }
diff --git a/README.md b/README.md
index 9246da6..fc23598 100644
--- a/README.md
+++ b/README.md
@@ -1,3 +1,50 @@
 # review-kit
 
-Code review helpers for Claude Code.
+Code review helpers for Claude Code, Codex, and GitHub Copilot CLI.
+
+## Install
+
+Claude Code:
+
+```sh
+claude plugin marketplace add <owner>/<repo>
+claude plugin install review-kit@review-kit
+```
+
+Codex:
+
+```sh
+codex plugin marketplace add <owner>/<repo>
+codex plugin add review-kit@review-kit
+```
+
+GitHub Copilot CLI:
+
+```sh
+copilot plugin marketplace add <owner>/<repo>
+copilot plugin install review-kit@review-kit
+```
+
+## What each tool gets
+
+| Component | Claude Code | Codex | Copilot CLI |
+| --- | --- | --- | --- |
+| `review` skill (`skills/review`) | yes | yes | yes |
+| `reviewer` agent (`agents/`) | yes | no | not verified |
+| SessionStart hook (`scripts/start.sh`) | yes | documented to run after you trust it; not tested | not verified |
+| `review` MCP server (`server/run.sh`) | yes | yes | yes |
+| API key prompt (`userConfig`) | yes | no | no |
+
+The MCP server runs `python3 -m review_server`, which must already be installed on your machine in every tool.
+It talks to an external review service using `REVIEW_API_KEY`.
+Claude Code asks for the key when you configure the plugin.
+Codex and Copilot CLI have no way to ask for it, so the server only gets the key if the tool passes a `REVIEW_API_KEY` from your environment through to it.
+
+## Layout
+
+- `.claude-plugin/plugin.json` and `.mcp.json`: the Claude Code manifest and MCP configuration.
+- `plugin.json` and `mcp.json`: the portable [Agent Plugins](https://agent-plugins.org/) manifest and MCP configuration, read by Codex and Copilot CLI instead of the Claude Code files.
+- `.claude-plugin/marketplace.json`: the one catalog, read by all three tools.
+- `marketplace-policy.json`: the tools this catalog targets.
+
+The two manifests must keep the same `name` and `version`, and the two MCP files must declare the same servers.
diff --git a/marketplace-policy.json b/marketplace-policy.json
new file mode 100644
index 0000000..7f1452d
--- /dev/null
+++ b/marketplace-policy.json
@@ -0,0 +1,4 @@
+{
+  "$comment": "One shared catalog, .claude-plugin/marketplace.json, read by all three tools: its only entry is a relative-path source, which every reader accepts, so no per-tool catalog is needed.",
+  "readers": ["claude-code", "codex", "copilot-cli"]
+}
diff --git a/mcp.json b/mcp.json
new file mode 100644
index 0000000..e4b58e7
--- /dev/null
+++ b/mcp.json
@@ -0,0 +1,9 @@
+{
+  "$schema": "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json",
+  "mcpServers": {
+    "review": {
+      "type": "stdio",
+      "command": "./server/run.sh"
+    }
+  }
+}
diff --git a/plugin.json b/plugin.json
new file mode 100644
index 0000000..1ae793b
--- /dev/null
+++ b/plugin.json
@@ -0,0 +1,9 @@
+{
+  "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
+  "name": "review-kit",
+  "version": "2.0.0",
+  "description": "Code review helpers. Runs a local MCP server (server/run.sh, python3 -m review_server) that talks to an external review service, and a SessionStart hook script (scripts/start.sh) in tools that load hooks.",
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
