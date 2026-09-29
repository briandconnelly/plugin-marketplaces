# Run: scenario 4, repetition 2, with-skill

Scored against `tests/scenarios.md` as of this commit; cost is `metrics` in the manifest.

## Manifest

```json
{
  "date": "2026-09-28",
  "arm": "with-skill",
  "scenario": "s4",
  "rep": 2,
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
  "transcript": "a961bcca6083c4250.output",
  "model": "claude-opus-5-5",
  "metrics": {
    "tool_calls": 23,
    "wall_seconds": 238.7
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

Batch 4. Every tool call read; no violation. s4: Copilot limited to plugin/skill/mcp subcommands; codex debug prompt-input only on stand-ins with stubbed scripts (plan-2c ledger).

## Score

| Criterion | Result | Evidence |
| --- | --- | --- |
| 1 | pass | `objective.json` shows `claude.errors: []`. `.claude-plugin/plugin.json` is byte-identical to the original (`diff` gave no output) and does not appear in `diff.patch`, so its declared paths and defaults are unchanged. |
| 2 | pass | `objective.json` shows `codex.listed: ["review-kit"]` and `copilot.listed: ["review-kit"]`. |
| 3 | pass | The table in `report.md` marks the `reviewer` agent "no" for Codex. It also marks "`REVIEW_API_KEY` given to the server" as "yes, from the `api_key` setting" for Claude Code and "no" for Codex, so the `userConfig` setting does not work there. |
| 4 | fail | The table in `report.md` says "`/review` command \| yes \| no \| no", which calls it unsupported in Codex. The report says the original layout migrated it to `source-command-review`, but adds that the portable files "cost you `/review`" and that the agent removed its converted skill. |
| 5 | pass | The "Checks" section of `report.md` lists what was run (validator, `claude plugin validate --strict`, listing and install in all three tools) and what was not (remote checks, starting the real server, model sessions, Copilot agents and hooks). Claims are observed or match the skill's `feature-matrix.md` (Codex: agents "not loaded", `userConfig` "not supported"). |

Total: 4 of 5 passed.

## Final report

review-kit now installs in Codex and GitHub Copilot CLI, and nothing Claude Code reads has changed beyond the catalog entry's description. The limit is that only the MCP server reaches the other two tools, and the plugin can't give them the API key. Nothing is committed or pushed.

**What I changed** (all under `$RUN/repo/`):
- Added `plugin.json` at the repo root: a portable-format manifest (the format Codex and Copilot CLI read) with the same name and version (2.0.0) as `.claude-plugin/plugin.json`.
- Added `mcp.json`: the same `review` server in portable form, `"type": "stdio"`, `"command": "./server/run.sh"`, `"cwd": "${PLUGIN_ROOT}"`. There is no `env` block, because the portable format has no way to take the key from a user setting.
- Added `.agents/plugins/marketplace.json`: a separate catalog for Codex, with the same plugin, source `./`, and the install and category fields Codex's docs recommend.
- Added `marketplace-policy.json`, declaring Claude Code, Codex and Copilot CLI as the tools this marketplace serves.
- `.claude-plugin/marketplace.json`: the entry now has a description saying it runs a SessionStart hook and a local MCP server that calls an external service with an API key. That is the only change to anything Claude Code reads. Copilot CLI reads this catalog too.
- `README.md`: install commands for each tool, a per-tool table of what works, and which files each tool reads.

**What works in each tool** (checked on claude 2.1.284, codex-cli 0.157.1 and copilot 1.0.89, all with throwaway config and network blocked):

| | Claude Code | Codex | Copilot CLI |
|---|---|---|---|
| Plugin listed and installs (v2.0.0) | yes | yes | yes |
| `review` MCP server | yes, unchanged | yes, path resolves to the installed copy | yes, path resolves |
| `REVIEW_API_KEY` given to the server | yes, from the `api_key` setting | no | no |
| `/review` command | yes | no | no |
| `reviewer` agent | yes | no | unknown, no command shows it |
| SessionStart hook | yes | no | unknown, no command shows it |

- **Claude Code:** `claude plugin details` still shows 1 skill (`review`), 1 agent, 1 SessionStart hook and 1 MCP server, and `claude plugin list --json` still shows the original server config with `${user_config.api_key}`.
- **Codex:** `codex mcp list` shows the server with an empty environment passthrough, so the key doesn't arrive. How users should supply it to a plugin's server is still open.
- **Copilot CLI:** `copilot mcp get review` resolves the path.
- **Other tools need Python:** in all three, the server runs `python3 -m review_server`, which isn't in the repo, so it has to be installed separately.

**What adding the portable manifest costs.** I compared against the original repo, which Codex and Copilot CLI already read in its Claude format:
- In Codex that format turned `/review` into a skill (`source-command-review`) and would run the hook once the user trusts it. Copilot CLI also listed `review` as a skill.
- But in both tools the MCP server command stayed as the literal `${CLAUDE_PLUGIN_ROOT}/server/run.sh`, so the server couldn't start. In Codex a harmless test copy of the server didn't run in that format and did run with the portable files.
- So the portable files get you a working server and cost you `/review` and the hook.

**Things I tried and backed out:**
- **`/review` as a portable skill:** Claude Code users would then see `review` listed twice ("Skills (2) review, review"), so I removed it. Getting `/review` into the other tools needs a skill with a different name, which Claude Code users would also see. That's your call.
- **Hook for Codex:** I didn't add one. Codex can run hooks declared under a Codex-specific section of `plugin.json`, but I couldn't find that section's format, and the hook only prints "review-kit ready".

**Checks:**
- **Validator:** exit 0 on a clean copy of the repo. File formats, the policy file and the local rules passed, and the portable manifest and `mcp.json` passed their schemas. Claude Code's own plugin-level check couldn't run because the repo root is both marketplace and plugin.
- **`claude plugin validate --strict`:** 0 errors, 0 warnings.
- **Listing and install:** checked in all three tools with their own commands, as above.
- **Not run:**
  - Remote checks, since the source is local.
  - Starting the real server, since that runs plugin code.
  - Anything needing a model session.
  - Whether Copilot CLI loads agents or hooks, since no command shows them.

**To keep in step:** when you release, bump `version` in both `plugin.json` and `.claude-plugin/plugin.json`. Any change to the server has to be made in both `.mcp.json` and `mcp.json`.

All scratch files are in `$RUN/repo/.tool-homes/`. It doesn't appear in `git status` here, but it isn't in the repo's `.gitignore`.

## Tool calls

The arm's tool calls, one JSON object per line, extracted from its transcript.

```jsonl
{"tool": "Bash", "input": {"command": "cd $RUN/repo && git status && git log --oneline | head && find . -path ./.git -prune -o -type f -print | head -100; ls -R $RUN/skill/plugin-marketplaces"}}
{"tool": "Read", "input": {"file_path": "$RUN/skill/plugin-marketplaces/SKILL.md"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && for f in $(git ls-files); do echo \"=== $f\"; cat $f; done; ls -la server scripts"}}
{"tool": "Bash", "input": {"command": "cd $RUN/skill/plugin-marketplaces/references && cat multi-tool.md feature-matrix.md agent-plugins.md"}}
{"tool": "Bash", "input": {"command": "cd $RUN/skill/plugin-marketplaces/references && cat codex.md copilot-cli.md validation.md releases.md"}}
{"tool": "Bash", "input": {"command": "cd $RUN/skill/plugin-marketplaces; which claude codex copilot; cat scripts/mpcheck/policy.py | head -120; grep -rn \"com.openai\" references | head -20; cat scripts/mpcheck/data/schemas/agent-plugins/1.0.0/mcp.schema.json | head -150"}}
{"tool": "Bash", "input": {"command": "cd $RUN/skill/plugin-marketplaces; sed -n 120,250p scripts/mpcheck/policy.py; python3 -c \"import json;d=json.load(open('scripts/mpcheck/data/readers.json'));print(list(d) if isinstance(d,dict) else d)\" | head -30; grep -n \"PLUGIN_ROOT\\|stdio\\|command\" references/claude-code.md | head"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=\"$PWD/.tool-homes\"; mkdir -p \"$T\"/{home,xdg,tmp}; git archive HEAD | (mkdir -p $T/base && tar -x -C $T/base); HOME=$T/home XDG_CONFIG_HOME=$T/xdg TMPDIR=$T/tmp CLAUDE_CONFIG_DIR=$T/claude-v ../validator/bin/check-marketplace $T/base </dev/null; echo exit $?; grep -n tool-homes .gitignore 2>/dev/null"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && mkdir -p .agents/plugins && cat > plugin.json <<'EOF'\n{\n  \"$schema\": \"https://agent-plugins.org/schemas/1.0.0/plugin.schema.json\",\n  \"name\": \"review-kit\",\n  \"version\": \"2.0.0\",\n  \"description\": \"Code review helpers\",\n  \"author\": {\n    \"name\": \"Acme\"\n  }\n}\nEOF\ncat > mcp.json <<'EOF'\n{\n  \"$schema\": \"https://agent-plugins.org/schemas/1.0.0/mcp.schema.json\",\n  \"mcpServers\": {\n    \"review\": {\n      \"type\": \"stdio\",\n      \"command\": \"./server/run.sh\",\n      \"cwd\": \"${PLUGIN_ROOT}\"\n    }\n  }\n}\nEOF\ncat > .agents/plugins/marketplace.json <<'EOF'\n{\n  \"name\": \"review-kit\",\n  \"plugins\": [\n    {\n      \"name\": \"review-kit\",\n      \"source\": {\n        \"source\": \"local\",\n        \"path\": \"./\"\n      },\n      \"description\": \"Code review helpers. Runs a local MCP server (server/run.sh, python3 -m review_server) that calls an external review service with the key in REVIEW_API_KEY.\",\n      \"policy\": {\n        \"installation\": \"AVAILABLE\",\n        \"authentication\": \"ON_INSTALL\"\n      },\n      \"category\": \"Coding\"\n    }\n  ]\n}\nEOF\ncat > marketplace-policy.json <<'EOF'\n{\n  \"readers\": [\"claude-code\", \"codex\", \"copilot-cli\"]\n}\nEOF\npython3 - <<'EOF'\nimport json\np='.claude-plugin/marketplace.json'\nd=json.load(open(p))\nd['plugins'][0]['description']=\"Code review helpers. Runs a SessionStart hook (scripts/start.sh) and a local MCP server (server/run.sh, python3 -m review_server) that calls an external review service with your review API key.\"\njson.dump(d,open(p,'w'),indent=2); open(p,'a').write('\\n')\nEOF\ngit diff"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=\"$PWD/.tool-homes\"; rm -rf $T/export; mkdir -p $T/export; git ls-files -co --exclude-standard | grep -v '^.tool-homes/' | tar -cf - -T - | tar -x -C $T/export; find $T/export -type f | sed \"s|$T/export/||\"; HOME=$T/home XDG_CONFIG_HOME=$T/xdg TMPDIR=$T/tmp ../validator/bin/check-marketplace $T/export </dev/null; echo exit $?"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=\"$PWD/.tool-homes\"; mkdir -p \"$T\"/{home,xdg,tmp,claude,codex,copilot,copilot-cache}; : > \"$T/gitconfig\"; export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\"; SB='(version 1)(allow default)(deny network-outbound (remote ip))'\nfor t in claude codex copilot; do sandbox-exec -p \"$SB\" $t --version </dev/null; done\necho ---claude validate; sandbox-exec -p \"$SB\" claude plugin validate $T/export --strict --json </dev/null\necho ---claude add; sandbox-exec -p \"$SB\" claude plugin marketplace add $T/export </dev/null\necho ---claude details; sandbox-exec -p \"$SB\" claude plugin details review-kit@review-kit </dev/null"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=\"$PWD/.tool-homes\"; export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\"; SB='(version 1)(allow default)(deny network-outbound (remote ip))'\nsandbox-exec -p \"$SB\" claude plugin details --help </dev/null | head -20; echo; sandbox-exec -p \"$SB\" claude plugin details review-kit --plugin-dir $T/export </dev/null; echo ---baseline; sandbox-exec -p \"$SB\" claude plugin details review-kit --plugin-dir $T/base </dev/null"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=\"$PWD/.tool-homes\"; export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\"; SB='(version 1)(allow default)(deny network-outbound (remote ip))'\nsandbox-exec -p \"$SB\" claude plugin install review-kit@review-kit </dev/null; echo; sandbox-exec -p \"$SB\" claude plugin details review-kit@review-kit </dev/null; sandbox-exec -p \"$SB\" claude plugin list --json </dev/null"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=\"$PWD/.tool-homes\"; export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\"; SB='(version 1)(allow default)(deny network-outbound (remote ip))'\ncd $T/tmp && sandbox-exec -p \"$SB\" codex plugin marketplace add $T/export </dev/null; sandbox-exec -p \"$SB\" codex plugin list --available --json </dev/null; sandbox-exec -p \"$SB\" codex plugin add review-kit@review-kit --json </dev/null; echo; sandbox-exec -p \"$SB\" codex mcp list --json </dev/null; find $T/codex/plugins/cache -maxdepth 4"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo/.tool-homes && grep -rl \"source-command\" codex 2>/dev/null | head; find codex -iname \"*source-command*\" | head; cat codex/config.toml"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=\"$PWD/.tool-homes\"; export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\"; SB='(version 1)(allow default)(deny network-outbound (remote ip))'\nfor v in export base; do S=$T/standin-$v; rm -rf $S; cp -R $T/$v $S; printf '#!/bin/sh\\necho \"$0 $*\" >> %s/standin-%s.log\\nexit 0\\n' $T $v > $S/server/run.sh; cp $S/server/run.sh $S/scripts/start.sh; chmod +x $S/server/run.sh $S/scripts/start.sh\n CH=$T/codex-standin-$v; rm -rf $CH; mkdir -p $CH; W=$T/work-$v; mkdir -p $W; cd $W\n echo \"=== $v\"; CODEX_HOME=$CH sandbox-exec -p \"$SB\" codex plugin marketplace add $S </dev/null >/dev/null; CODEX_HOME=$CH sandbox-exec -p \"$SB\" codex plugin add review-kit@review-kit --json </dev/null | grep version\n CODEX_HOME=$CH timeout 60 sandbox-exec -p \"$SB\" codex debug prompt-input </dev/null > $T/prompt-$v.txt 2>&1; echo rc $?; grep -n -i \"review\\|source-command\\|hook\" $T/prompt-$v.txt | head -20; CODEX_HOME=$CH sandbox-exec -p \"$SB\" codex mcp list --json </dev/null | grep -E '\"command\"|REVIEW'; cd $T; done; cat $T/standin-*.log 2>/dev/null"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=\"$PWD/.tool-homes\"; export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1; SB='(version 1)(allow default)(deny network-outbound (remote ip))'\nfor v in export base; do CH=$T/codex-standin-$v; cd $T/work-$v; echo \"=== $v\"; CODEX_HOME=$CH sandbox-exec -p \"$SB\" codex debug prompt-input </dev/null > $T/prompt-$v.txt 2>&1; echo rc $?; wc -c $T/prompt-$v.txt; grep -n -i \"review\\|source-command\" $T/prompt-$v.txt | head -20; done; ls $T/*.log; cat $T/standin-*.log", "timeout": 180000}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=\"$PWD/.tool-homes\"; export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1; SB='(version 1)(allow default)(deny network-outbound (remote ip))'\nfor v in export base; do export COPILOT_HOME=$T/copilot-$v COPILOT_CACHE_HOME=$T/copilot-cache-$v; mkdir -p $COPILOT_HOME $COPILOT_CACHE_HOME; cd $T/work-$v; echo \"=== $v\"\nsandbox-exec -p \"$SB\" copilot plugin marketplace add $T/$v </dev/null; sandbox-exec -p \"$SB\" copilot plugin marketplace browse review-kit --json </dev/null; sandbox-exec -p \"$SB\" copilot plugin install review-kit@review-kit </dev/null; sandbox-exec -p \"$SB\" copilot plugin list </dev/null; sandbox-exec -p \"$SB\" copilot skill list </dev/null | grep -i -B1 -A1 review; sandbox-exec -p \"$SB\" copilot mcp list </dev/null; sandbox-exec -p \"$SB\" copilot mcp get review </dev/null; done", "timeout": 300000}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && mkdir -p skills/review && cat > skills/review/SKILL.md <<'EOF'\n---\nname: review\ndescription: Review the current diff\n---\n\nReview the staged diff and list problems.\nEOF\nT=\"$PWD/.tool-homes\"; rm -rf $T/export2; mkdir -p $T/export2; git ls-files -co --exclude-standard | grep -v '^.tool-homes/' | tar -cf - -T - | tar -x -C $T/export2\nexport HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude2\"; SB='(version 1)(allow default)(deny network-outbound (remote ip))'; mkdir -p $CLAUDE_CONFIG_DIR\nsandbox-exec -p \"$SB\" claude plugin marketplace add $T/export2 </dev/null; sandbox-exec -p \"$SB\" claude plugin install review-kit@review-kit </dev/null; sandbox-exec -p \"$SB\" claude plugin details review-kit@review-kit </dev/null | sed -n 1,12p"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && rm -rf skills && git status --short"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && cat > README.md <<'EOF'\n# review-kit\n\nCode review helpers for Claude Code, Codex, and GitHub Copilot CLI.\n\n## Install\n\n- Claude Code: `claude plugin marketplace add <this repo>`, then `claude plugin install review-kit@review-kit`.\n- Codex: `codex plugin marketplace add <this repo>`, then `codex plugin add review-kit@review-kit`.\n- GitHub Copilot CLI: `copilot plugin marketplace add <this repo>`, then `copilot plugin install review-kit@review-kit`.\n\n## What each tool gets\n\n| Component | Claude Code | Codex | Copilot CLI |\n| --- | --- | --- | --- |\n| `review` MCP server | yes | yes | yes |\n| Review API key passed to the server | yes, from the plugin's `api_key` setting | no: make `REVIEW_API_KEY` available to the server yourself | no: make `REVIEW_API_KEY` available to the server yourself |\n| `/review` command | yes | no | no |\n| `reviewer` agent | yes | no | no |\n| SessionStart hook | yes | no | no |\n\nThe MCP server runs `python3 -m review_server`, which must be importable in every tool.\n\n## Layout\n\n- Claude Code reads `.claude-plugin/marketplace.json`, `.claude-plugin/plugin.json`, and `.mcp.json`.\n- Codex reads `.agents/plugins/marketplace.json`, the root `plugin.json`, and `mcp.json`.\n- Copilot CLI reads `.claude-plugin/marketplace.json`, the root `plugin.json`, and `mcp.json`.\n- Keep `version` equal in `plugin.json` and `.claude-plugin/plugin.json`, and keep the server in `mcp.json` in step with `.mcp.json`.\nEOF\nT=\"$PWD/.tool-homes\"; rm -rf $T/final; mkdir -p $T/final; git ls-files -co --exclude-standard | grep -v '^.tool-homes/' | tar -cf - -T - | tar -x -C $T/final; diff -r $T/export $T/final; HOME=$T/home XDG_CONFIG_HOME=$T/xdg TMPDIR=$T/tmp ../validator/bin/check-marketplace $T/final </dev/null; echo exit $?"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && python3 - <<'EOF'\np='README.md'; s=open(p).read()\ns=s.replace(\"| Review API key passed to the server | yes, from the plugin's `api_key` setting | no: make `REVIEW_API_KEY` available to the server yourself | no: make `REVIEW_API_KEY` available to the server yourself |\",\n\"| Review API key passed to the server | yes, from the plugin's `api_key` setting | not by the plugin: set `REVIEW_API_KEY` for the server in your Codex configuration | not by the plugin: set `REVIEW_API_KEY` for the server yourself |\")\ns=s.replace(\"| `reviewer` agent | yes | no | no |\",\"| `reviewer` agent | yes | no | not known |\")\ns=s.replace(\"| SessionStart hook | yes | no | no |\",\"| SessionStart hook | yes | no | not known |\")\nopen(p,'w').write(s)\nEOF\ngrep -n \"known\\|not by\" README.md; git diff --stat; git status --short"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && sed -i '' 's/set `REVIEW_API_KEY` for the server in your Codex configuration/set `REVIEW_API_KEY` for the server yourself/' README.md && grep -n \"not by\" README.md"}}
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
index 0000000..a6b3891
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
+      "description": "Code review helpers. Runs a local MCP server (server/run.sh, python3 -m review_server) that calls an external review service with the key in REVIEW_API_KEY.",
+      "policy": {
+        "installation": "AVAILABLE",
+        "authentication": "ON_INSTALL"
+      },
+      "category": "Coding"
+    }
+  ]
+}
diff --git a/.claude-plugin/marketplace.json b/.claude-plugin/marketplace.json
index a015458..3c283b8 100644
--- a/.claude-plugin/marketplace.json
+++ b/.claude-plugin/marketplace.json
@@ -7,7 +7,8 @@
   "plugins": [
     {
       "name": "review-kit",
-      "source": "./"
+      "source": "./",
+      "description": "Code review helpers. Runs a SessionStart hook (scripts/start.sh) and a local MCP server (server/run.sh, python3 -m review_server) that calls an external review service with your review API key."
     }
   ]
 }
diff --git a/README.md b/README.md
index 9246da6..e9a6779 100644
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
+- GitHub Copilot CLI: `copilot plugin marketplace add <this repo>`, then `copilot plugin install review-kit@review-kit`.
+
+## What each tool gets
+
+| Component | Claude Code | Codex | Copilot CLI |
+| --- | --- | --- | --- |
+| `review` MCP server | yes | yes | yes |
+| Review API key passed to the server | yes, from the plugin's `api_key` setting | not by the plugin: set `REVIEW_API_KEY` for the server yourself | not by the plugin: set `REVIEW_API_KEY` for the server yourself |
+| `/review` command | yes | no | no |
+| `reviewer` agent | yes | no | not known |
+| SessionStart hook | yes | no | not known |
+
+The MCP server runs `python3 -m review_server`, which must be importable in every tool.
+
+## Layout
+
+- Claude Code reads `.claude-plugin/marketplace.json`, `.claude-plugin/plugin.json`, and `.mcp.json`.
+- Codex reads `.agents/plugins/marketplace.json`, the root `plugin.json`, and `mcp.json`.
+- Copilot CLI reads `.claude-plugin/marketplace.json`, the root `plugin.json`, and `mcp.json`.
+- Keep `version` equal in `plugin.json` and `.claude-plugin/plugin.json`, and keep the server in `mcp.json` in step with `.mcp.json`.
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
```

## Repository refs

Every branch and tag in the final repository, each with its changes against the fixture tree (`refs.txt`).

```text
master 17d0334
```
