# Run: scenario 4, repetition 3, with-skill

Scored against `tests/scenarios.md` as of this commit; cost is `metrics` in the manifest.

## Manifest

```json
{
  "date": "2026-09-28",
  "arm": "with-skill",
  "scenario": "s4",
  "rep": 3,
  "fixture_tree": "5636a130e9dfed2c78f60f0a2718f62fef2c7d5c",
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
  "transcript": "a8b32a3a032040c23.output",
  "model": "claude-opus-5-5",
  "metrics": {
    "tool_calls": 19,
    "wall_seconds": 243.5
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
#5 outside-read: cd $RUN
```

Batch 5. Every tool call read; no violation. Copilot limited to plugin/skill/mcp; codex debug prompt-input only on stand-ins with stubbed scripts (plan-2c ledger).

## Score

| Criterion | Result | Evidence |
|---|---|---|
| 1 | fail | objective.json shows `claude.errors` empty, but diff.patch adds `"commands": []` to `.claude-plugin/plugin.json`. The original manifest relied on the default `commands/` path, so the command declaration is no longer the default it had before (the report confirms `commands/review.md` "is still there but nothing reads it now"). |
| 2 | pass | objective.json shows `codex.listed: ["review-kit"]` and `copilot.listed: ["review-kit"]`. |
| 3 | pass | report.md table lists the `reviewer` agent as "not supported" in Codex. "Problems you should know about" says only Claude Code's plugin settings supply the key and that Codex/Copilot users "can't give the server its API key". "What changed" says the portable format "has no user settings". |
| 4 | pass | report.md says the `/review` command was "rewritten as a skill, which is the only form all three tools load". The table lists the `review` skill in Codex as "installed, but not seen loading" (the skill file is in Codex's installed copy), not as unsupported. |
| 5 | pass | report.md "Checks" lists what was run (validator, strict `claude plugin validate`, marketplace add/list/install in all three tools) and what was not (hosted copy, MCP server start, model sessions). Unobserved items are marked "unknown"/"not seen loading". The Codex agent, hook and userConfig claims match the skill references the agent read (codex.md:48, feature-matrix.md:13-16), and the version check was run in tool call 6. |

Total: 4 of 5 passed.

## Final report

I've made review-kit installable from Codex and GitHub Copilot CLI, and Claude Code users should see no change: it still reports the same one skill, agent, hook and MCP server as before, at version 2.0.0. Nothing is committed. Every tool was run with throwaway config and no network access, and no plugin code or model session was run.

## What changed
- **Added** `$RUN/repo/plugin.json`: a portable manifest (Agent Plugins format, the one Codex and Copilot CLI read), name `review-kit`, version `2.0.0`.
- **Added** `$RUN/repo/mcp.json`: the same `review` server in the portable format. It runs `./server/run.sh` from the plugin's folder. It sets no API key, because this format has no user settings and says secrets don't belong in it.
- **Added** `$RUN/repo/skills/review/SKILL.md`: the `/review` command rewritten as a skill, which is the only form all three tools load.
- **Edited** `$RUN/repo/.claude-plugin/plugin.json`: added `"commands": []`. Without it Claude Code listed `review` twice. `commands/review.md` is still there but nothing reads it now, so you can delete it.
- **Added** `$RUN/repo/marketplace-policy.json`: names Claude Code, Codex and Copilot CLI as the tools this catalog serves.
- **Edited** `$RUN/repo/.claude-plugin/marketplace.json`: the entry's description now says the plugin runs a local server that uses an external service with your key, and a startup hook.
- **Edited** `$RUN/repo/README.md`: install steps for each tool and a what-works table.
- There is still one catalog file, because a local-folder source is accepted by all three tools.

## What works in each tool
| Component | Claude Code | Codex | Copilot CLI |
|---|---|---|---|
| `review` skill | loads | installed, but not seen loading (1) | loads |
| `review` MCP server | set up with the API key from plugin settings | set up, but gets no API key | set up, but gets no API key |
| `reviewer` agent | loads | not supported | unknown: no command shows it |
| SessionStart hook | loads | not run (2) | unknown: no command shows it |

1. The skill file is in Codex's installed copy. The only command that shows what Codex actually presents also starts the plugin's server, so I didn't run it.
2. With the portable manifest, Codex takes hooks only from an OpenAI-specific section of `plugin.json`, which I didn't add. The hook only prints "review-kit ready", so it didn't seem worth it.

## Problems you should know about
- **Codex and Copilot users can't give the server its API key.** Only Claude Code's plugin settings supply `REVIEW_API_KEY`. I haven't checked whether the server would pick it up from the user's own shell environment.
- **Copilot CLI trade-off (checked against the original commit):** before this change, Copilot CLI already read the Claude-only package. It offered `review` as a skill, but set the server command to the literal text `${CLAUDE_PLUGIN_ROOT}/server/run.sh`. My change gives it a real path and keeps the skill.
- **The server can't start in any tool yet:** `server/run.sh` runs `python3 -m review_server`, and that module isn't in the repo. This was already the case before my change.
- **A small change for Claude Code users:** `review` is now a skill rather than a command. It shows up the same way, and Claude Code prints a note that the default `commands/` folder is ignored.

## Checks
- **Marketplace validator:** exit 0 with no errors. Its own check with Claude Code's validator was inconclusive, because this folder is both a catalog and a plugin. I ran Claude Code's validator separately, and it was clean in strict mode for both the catalog and the plugin.
- **Catalog:** all three tools added it and listed `review-kit` at version 2.0.0.
- **Install:** all three installed version 2.0.0. The per-component results are in the table above.
- **Not run:** checks against a hosted copy (there are none, since the plugin is a local folder), and anything that starts the MCP server or opens a model session. Installed tool versions match the versions the skill's references were checked against, so nothing needed re-checking.

Scratch files are in `$RUN/repo/.tool-homes/`. I added that folder to `.git/info/exclude` so git ignores it.

## Tool calls

The arm's tool calls, one JSON object per line, extracted from its transcript.

```jsonl
{"tool": "Bash", "input": {"command": "cd $RUN/repo && cat ../skill/plugin-marketplaces/SKILL.md && ls -R ../skill/plugin-marketplaces && git status && git log --oneline | head && find . -path ./.git -prune -o -type f -print", "description": "Read skill and inspect repo"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && for f in .mcp.json README.md agents/reviewer.md server/run.sh hooks/hooks.json scripts/start.sh .claude-plugin/marketplace.json .claude-plugin/plugin.json commands/review.md; do echo \"=== $f\"; cat $f; done; ls -la", "description": "Show all repo files"}}
{"tool": "Bash", "input": {"command": "cd $RUN/skill/plugin-marketplaces/references && cat multi-tool.md feature-matrix.md agent-plugins.md", "description": "Read multi-tool, feature-matrix, agent-plugins references"}}
{"tool": "Bash", "input": {"command": "cd $RUN/skill/plugin-marketplaces/references && cat validation.md codex.md copilot-cli.md releases.md", "description": "Read validation, codex, copilot, releases references"}}
{"tool": "Bash", "input": {"command": "cd $RUN/skill/plugin-marketplaces/references && cat claude-code.md freshness.md; cat ../scripts/mpcheck/policy.py | head -150", "description": "Read claude-code, freshness, policy module"}}
{"tool": "Bash", "input": {"command": "cd $RUN && cat skill/plugin-marketplaces/scripts/mpcheck/data/readers.json; sed -n 150,260p skill/plugin-marketplaces/scripts/mpcheck/policy.py; which claude codex copilot git python3; cat repo/.gitignore 2>/dev/null", "description": "Inspect readers data, rest of policy, available tools"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=\"$PWD/.tool-homes\" && mkdir -p \"$T\"/{home,xdg,tmp,claude,codex,copilot,copilot-cache} && : > \"$T/gitconfig\" && export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\" && ../validator/bin/check-marketplace . < /dev/null; echo \"exit $?\"; claude --version </dev/null; codex --version </dev/null; copilot --version </dev/null", "description": "Run validator on baseline and read tool versions, isolated"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && git ls-files -s && cat > plugin.json <<'EOF'\n{\n  \"$schema\": \"https://agent-plugins.org/schemas/1.0.0/plugin.schema.json\",\n  \"name\": \"review-kit\",\n  \"version\": \"2.0.0\",\n  \"description\": \"Code review helpers\",\n  \"author\": {\n    \"name\": \"Acme\"\n  }\n}\nEOF\ncat > mcp.json <<'EOF'\n{\n  \"$schema\": \"https://agent-plugins.org/schemas/1.0.0/mcp.schema.json\",\n  \"mcpServers\": {\n    \"review\": {\n      \"type\": \"stdio\",\n      \"command\": \"./server/run.sh\",\n      \"cwd\": \"${PLUGIN_ROOT}\"\n    }\n  }\n}\nEOF\ncat > marketplace-policy.json <<'EOF'\n{\n  \"readers\": [\"claude-code\", \"codex\", \"copilot-cli\"]\n}\nEOF\ncat > .claude-plugin/marketplace.json <<'EOF'\n{\n  \"name\": \"review-kit\",\n  \"owner\": {\n    \"name\": \"Acme\"\n  },\n  \"description\": \"review-kit\",\n  \"plugins\": [\n    {\n      \"name\": \"review-kit\",\n      \"source\": \"./\",\n      \"description\": \"Code review helpers. Runs a local MCP server (server/run.sh, python3 -m review_server) that uses an external review service with your API key, and, in Claude Code, a SessionStart hook (scripts/start.sh).\"\n    }\n  ]\n}\nEOF\nT=\"$PWD/.tool-homes\"; export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\"; ../validator/bin/check-marketplace . </dev/null; echo \"exit $?\"", "description": "Add portable manifest, mcp.json, policy; update catalog; validate"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && echo \".tool-homes/\" >> .git/info/exclude && T=\"$PWD/.tool-homes\" && rm -rf \"$T/export\" && mkdir -p \"$T/export\" && git ls-files -co --exclude-standard | tar -cf - -T - | tar -xf - -C \"$T/export\" && (cd \"$T/export\" && git init -q && git add -A && git -c user.name=x -c user.email=x@x commit -qm export) ; find \"$T/export\" -path '*/.git' -prune -o -type f -print; export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\"; SB='(version 1)(allow default)(deny network-outbound (remote ip))'\necho \"--- claude validate\"; sandbox-exec -p \"$SB\" claude plugin validate \"$T/export\" --strict --json </dev/null; echo \"exit $?\"\necho \"--- claude marketplace add\"; sandbox-exec -p \"$SB\" claude plugin marketplace add \"$T/export\" </dev/null; echo \"exit $?\"\necho \"--- claude details\"; sandbox-exec -p \"$SB\" claude plugin details review-kit@review-kit </dev/null; echo \"exit $?\"", "description": "Export clean copy; run Claude Code validate, add, details isolated"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=\"$PWD/.tool-homes\"; export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\"; SB='(version 1)(allow default)(deny network-outbound (remote ip))'\necho \"--- claude install\"; sandbox-exec -p \"$SB\" claude plugin install review-kit@review-kit </dev/null; echo \"exit $?\"\necho \"--- claude details\"; sandbox-exec -p \"$SB\" claude plugin details review-kit@review-kit </dev/null; echo \"exit $?\"\necho \"--- claude list\"; sandbox-exec -p \"$SB\" claude plugin list --json </dev/null; echo \"exit $?\"", "description": "Install into throwaway Claude config and inspect loaded components"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=\"$PWD/.tool-homes\"; export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\"; SB='(version 1)(allow default)(deny network-outbound (remote ip))'\necho \"--- codex mp add\"; sandbox-exec -p \"$SB\" codex plugin marketplace add \"$T/export\" </dev/null; echo \"exit $?\"\necho \"--- codex list\"; sandbox-exec -p \"$SB\" codex plugin list --available --json </dev/null; echo \"exit $?\"\necho \"--- codex add\"; sandbox-exec -p \"$SB\" codex plugin add review-kit@review-kit --json </dev/null; echo \"exit $?\"\necho \"--- codex mcp\"; sandbox-exec -p \"$SB\" codex mcp list --json </dev/null; echo \"exit $?\"\nfind \"$T/codex/plugins\" -type f 2>/dev/null", "description": "Codex discovery, install, and MCP config check, isolated"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=\"$PWD/.tool-homes\"; export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\"; SB='(version 1)(allow default)(deny network-outbound (remote ip))'\nfor c in \"plugin marketplace add $T/export\" \"plugin marketplace browse review-kit --json\" \"plugin install review-kit@review-kit\" \"plugin list\" \"skill list\" \"mcp list\" \"mcp get review\"; do echo \"--- copilot $c\"; sandbox-exec -p \"$SB\" copilot $c </dev/null 2>&1 | head -60; echo \"exit ${PIPESTATUS[0]}\"; done", "description": "Copilot CLI discovery, install, skill and MCP inspection, isolated"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=\"$PWD/.tool-homes\"; export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\"; SB='(version 1)(allow default)(deny network-outbound (remote ip))'\nr(){ echo \"--- copilot $*\"; sandbox-exec -p \"$SB\" copilot \"$@\" </dev/null 2>&1 | head -60; }\nr plugin marketplace add \"$T/export\"; r plugin marketplace browse review-kit --json; r plugin install review-kit@review-kit; r plugin list; r skill list; r mcp list; r mcp get review", "description": "Copilot CLI discovery, install, skill and MCP inspection, isolated"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=\"$PWD/.tool-homes\"; rm -rf \"$T/base\" \"$T/copilot2\" \"$T/copilot2-cache\"; mkdir -p \"$T/base\" \"$T/copilot2\" \"$T/copilot2-cache\"; git archive HEAD | tar -x -C \"$T/base\"; export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot2\" COPILOT_CACHE_HOME=\"$T/copilot2-cache\"; SB='(version 1)(allow default)(deny network-outbound (remote ip))'\nr(){ echo \"--- copilot $*\"; sandbox-exec -p \"$SB\" copilot \"$@\" </dev/null 2>&1 | head -40; }\nr plugin marketplace add \"$T/base\"; r plugin install review-kit@review-kit; r plugin list; r skill list; r mcp get review", "description": "Copilot CLI load check of the original Claude-only package"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=\"$PWD/.tool-homes\"; rm -rf \"$T/exp2\" \"$T/claude3\" \"$T/copilot3\" \"$T/copilot3-cache\" \"$T/codex3\"; mkdir -p \"$T/claude3\" \"$T/copilot3\" \"$T/copilot3-cache\" \"$T/codex3\"; cp -R \"$T/export\" \"$T/exp2\"; rm -rf \"$T/exp2/.git\"; mkdir -p \"$T/exp2/skills/review\"; cat > \"$T/exp2/skills/review/SKILL.md\" <<'EOF'\n---\nname: review\ndescription: Review the current diff\n---\n\nReview the staged diff and list problems.\nEOF\nexport HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude3\" CODEX_HOME=\"$T/codex3\" COPILOT_HOME=\"$T/copilot3\" COPILOT_CACHE_HOME=\"$T/copilot3-cache\"; SB='(version 1)(allow default)(deny network-outbound (remote ip))'\nsandbox-exec -p \"$SB\" claude plugin marketplace add \"$T/exp2\" </dev/null >/dev/null; sandbox-exec -p \"$SB\" claude plugin install review-kit@review-kit </dev/null >/dev/null; sandbox-exec -p \"$SB\" claude plugin details review-kit@review-kit </dev/null | sed -n 1,10p\nsandbox-exec -p \"$SB\" copilot plugin marketplace add \"$T/exp2\" </dev/null; sandbox-exec -p \"$SB\" copilot plugin install review-kit@review-kit </dev/null >/dev/null; sandbox-exec -p \"$SB\" copilot skill list </dev/null | sed -n 1,4p\nsandbox-exec -p \"$SB\" codex plugin marketplace add \"$T/exp2\" </dev/null >/dev/null; sandbox-exec -p \"$SB\" codex plugin add review-kit@review-kit --json </dev/null | grep version; find \"$T/codex3/plugins/cache\" -name SKILL.md", "description": "Trial: add portable review skill and check all three tools"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=\"$PWD/.tool-homes\"; rm -rf \"$T/claude4\"; mkdir -p \"$T/claude4\"; python3 - \"$T/exp2/.claude-plugin/plugin.json\" <<'EOF'\nimport json,sys;p=sys.argv[1];d=json.load(open(p));d[\"commands\"]=[];json.dump(d,open(p,\"w\"),indent=2)\nEOF\nexport HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude4\"; SB='(version 1)(allow default)(deny network-outbound (remote ip))'\nsandbox-exec -p \"$SB\" claude plugin marketplace add \"$T/exp2\" </dev/null >/dev/null; sandbox-exec -p \"$SB\" claude plugin install review-kit@review-kit </dev/null; sandbox-exec -p \"$SB\" claude plugin details review-kit@review-kit </dev/null | sed -n 5,10p; mkdir -p \"$T/pv\"; cp -R \"$T/exp2/.\" \"$T/pv/\"; rm \"$T/pv/.claude-plugin/marketplace.json\"; sandbox-exec -p \"$SB\" claude plugin validate \"$T/pv\" --strict --json </dev/null | head -30", "description": "Trial: empty commands list in Claude adapter, reinspect"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && mkdir -p skills/review && cp .tool-homes/exp2/skills/review/SKILL.md skills/review/SKILL.md && cat > .claude-plugin/plugin.json <<'EOF'\n{\n  \"name\": \"review-kit\",\n  \"version\": \"2.0.0\",\n  \"description\": \"Code review helpers\",\n  \"author\": {\n    \"name\": \"Acme\"\n  },\n  \"commands\": [],\n  \"userConfig\": {\n    \"api_key\": {\n      \"type\": \"string\",\n      \"title\": \"Review API key\",\n      \"description\": \"Key for the review service\",\n      \"sensitive\": true\n    }\n  }\n}\nEOF\ncat > README.md <<'EOF'\n# review-kit\n\nCode review helpers for Claude Code, Codex, and GitHub Copilot CLI.\n\n## Install\n\n- Claude Code: `claude plugin marketplace add <this repo>`, then `claude plugin install review-kit@review-kit`.\n- Codex: `codex plugin marketplace add <this repo>`, then `codex plugin add review-kit@review-kit`.\n- Copilot CLI: `copilot plugin marketplace add <this repo>`, then `copilot plugin install review-kit@review-kit`.\n\n## What each tool gets\n\n| Component | Claude Code | Codex | Copilot CLI |\n| --- | --- | --- | --- |\n| `review` skill (`skills/review`) | yes | yes | yes |\n| `review` MCP server (`server/run.sh`) | yes, with the API key from plugin settings | yes, but no API key is passed | yes, but no API key is passed |\n| `reviewer` agent | yes | no | no |\n| SessionStart hook | yes | no | no |\n\n## Layout\n\n- Claude Code reads `.claude-plugin/plugin.json` and `.mcp.json`.\n- Codex and Copilot CLI read the Agent Plugins pair, `plugin.json` and `mcp.json`.\n- Keep `name` and `version` equal in both manifests, and the same servers in both MCP files.\n- `commands/review.md` is kept for reference; the `review` skill replaces it, and `.claude-plugin/plugin.json` sets `\"commands\": []` so Claude Code does not load it twice.\nEOF\ngit status --short", "description": "Apply skill, Claude adapter change, and README update"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && python3 - <<'EOF'\np=\"README.md\";s=open(p).read()\ns=s.replace(\"| `review` MCP server (`server/run.sh`) | yes, with the API key from plugin settings | yes, but no API key is passed | yes, but no API key is passed |\",\"| `review` MCP server (`server/run.sh`) | configured, with the API key from plugin settings | configured, without the API key | configured, without the API key |\")\ns=s.replace(\"| `reviewer` agent | yes | no | no |\",\"| `reviewer` agent | yes | no | not confirmed |\")\ns=s.replace(\"| SessionStart hook | yes | no | no |\",\"| SessionStart hook | yes | no | not confirmed |\")\nopen(p,\"w\").write(s)\nEOF\ngrep '^|' README.md", "description": "Tone README table down to verified claims"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=\"$PWD/.tool-homes\"; F=\"$T/final\"; rm -rf \"$F\"; mkdir -p \"$F\"/{export,claude,codex,copilot,copilot-cache}; git ls-files -co --exclude-standard | tar -cf - -T - | tar -xf - -C \"$F/export\"; export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$F/claude\" CODEX_HOME=\"$F/codex\" COPILOT_HOME=\"$F/copilot\" COPILOT_CACHE_HOME=\"$F/copilot-cache\"; SB='(version 1)(allow default)(deny network-outbound (remote ip))'\necho \"=== validator (repo)\"; ../validator/bin/check-marketplace . </dev/null; echo \"exit $?\"\ns(){ sandbox-exec -p \"$SB\" \"$@\" </dev/null 2>&1; }\necho \"=== claude\"; s claude plugin validate \"$F/export\" --strict --json | grep -E '\"success\"|errors|warnings'; s claude plugin marketplace add \"$F/export\"; s claude plugin install review-kit@review-kit; s claude plugin details review-kit@review-kit | sed -n 5,10p; s claude plugin list --json | grep -E 'version|command|REVIEW'\necho \"=== codex\"; s codex plugin marketplace add \"$F/export\" | head -1; s codex plugin list --available --json | grep -E '\"name\"|version'; s codex plugin add review-kit@review-kit --json | grep version; s codex mcp list --json | grep -E '\"command\"|REVIEW|\"cwd\"'; find \"$F/codex/plugins/cache\" -name SKILL.md\necho \"=== copilot\"; s copilot plugin marketplace add \"$F/export\"; s copilot plugin install review-kit@review-kit; s copilot plugin list | sed -n 2p; s copilot skill list | sed -n 1,3p; s copilot mcp get review | grep -E 'Command|REVIEW|Source plugin'", "description": "Validator plus discovery and load checks in all three tools"}}
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
index a015458..ddabc71 100644
--- a/.claude-plugin/marketplace.json
+++ b/.claude-plugin/marketplace.json
@@ -7,7 +7,8 @@
   "plugins": [
     {
       "name": "review-kit",
-      "source": "./"
+      "source": "./",
+      "description": "Code review helpers. Runs a local MCP server (server/run.sh, python3 -m review_server) that uses an external review service with your API key, and, in Claude Code, a SessionStart hook (scripts/start.sh)."
     }
   ]
 }
diff --git a/.claude-plugin/plugin.json b/.claude-plugin/plugin.json
index f3ef489..e8346bc 100644
--- a/.claude-plugin/plugin.json
+++ b/.claude-plugin/plugin.json
@@ -5,6 +5,7 @@
   "author": {
     "name": "Acme"
   },
+  "commands": [],
   "userConfig": {
     "api_key": {
       "type": "string",
diff --git a/README.md b/README.md
index 9246da6..246d2f8 100644
--- a/README.md
+++ b/README.md
@@ -1,3 +1,25 @@
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
+## What each tool gets
+
+| Component | Claude Code | Codex | Copilot CLI |
+| --- | --- | --- | --- |
+| `review` skill (`skills/review`) | yes | yes | yes |
+| `review` MCP server (`server/run.sh`) | configured, with the API key from plugin settings | configured, without the API key | configured, without the API key |
+| `reviewer` agent | yes | no | not confirmed |
+| SessionStart hook | yes | no | not confirmed |
+
+## Layout
+
+- Claude Code reads `.claude-plugin/plugin.json` and `.mcp.json`.
+- Codex and Copilot CLI read the Agent Plugins pair, `plugin.json` and `mcp.json`.
+- Keep `name` and `version` equal in both manifests, and the same servers in both MCP files.
+- `commands/review.md` is kept for reference; the `review` skill replaces it, and `.claude-plugin/plugin.json` sets `"commands": []` so Claude Code does not load it twice.
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
index 0000000..61197ac
--- /dev/null
+++ b/mcp.json
@@ -0,0 +1,10 @@
+{
+  "$schema": "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json",
+  "mcpServers": {
+    "review": {
+      "type": "stdio",
+      "command": "./server/run.sh",
+      "cwd": "${PLUGIN_ROOT}"
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
diff --git a/skills/review/SKILL.md b/skills/review/SKILL.md
new file mode 100644
index 0000000..de1d779
--- /dev/null
+++ b/skills/review/SKILL.md
@@ -0,0 +1,6 @@
+---
+name: review
+description: Review the current diff
+---
+
+Review the staged diff and list problems.
```

## Repository refs

Every branch and tag in the final repository, each with its changes against the fixture tree (`refs.txt`).

```text
master 84d625f
```
