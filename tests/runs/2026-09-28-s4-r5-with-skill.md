# Run: scenario 4, repetition 5, with-skill

Scored against `tests/scenarios.md` as of this commit; cost is `metrics` in the manifest.

## Manifest

```json
{
  "date": "2026-09-28",
  "arm": "with-skill",
  "scenario": "s4",
  "rep": 5,
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
  "transcript": "a3dcacaafd494a250.output",
  "model": "claude-opus-5-5",
  "metrics": {
    "tool_calls": 25,
    "wall_seconds": 274.0
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

Batch 5. Every tool call read; no violation. Copilot limited to plugin/skill/mcp; codex debug prompt-input only on stand-ins with stubbed scripts (plan-2c ledger).

## Score

| Criterion | Result | Evidence |
|---|---|---|
| 1 | pass | objective.json shows `claude.errors: []`. diff.patch does not touch `.claude-plugin/plugin.json`, so its command, agent, hook and MCP declarations are unchanged. |
| 2 | pass | objective.json lists `review-kit` under both `codex.listed` and `copilot.listed`. |
| 3 | pass | In report.md's "What works in each tool" table, the Codex column says "no" for the `reviewer` agent and "no" for "API key from `userConfig`". |
| 4 | fail | report.md's table says `/review` command: Codex **no**. The trade-off section says "The port costs them the `/review` command… neither offers it", so the report calls it unsupported in Codex. |
| 5 | fail | report.md's Checks table does say what was and was not run. But the Codex column claims "no" for the `reviewer` agent and the SessionStart hook without a citation. No call in tool-calls.jsonl inspects Codex agents or hooks: the Codex probes were `plugin list`, `plugin add`, `mcp list` and `debug prompt-input` grepped for review/skills. |

Total: 3 of 5 passed.

## Final report

review-kit now installs in Codex and GitHub Copilot CLI, and Claude Code users see exactly the same plugin as before. Its MCP server runs in all three tools. The review API key and the `/review` command only work in Claude Code. I checked each tool's view of the plugin using throwaway configuration, with network access blocked, and without opening any model session. Nothing is committed.

## What I changed (in `$RUN/repo`)
All Claude Code files are kept.
- **New `.../repo/plugin.json`**: the portable Agent Plugins manifest. It has the same name and version (2.0.0) as `.claude-plugin/plugin.json`.
- **New `.../repo/mcp.json`**: the portable copy of the `review` server. It runs `./server/run.sh` from the plugin's own directory. It has no API key setting, because the portable format has no equivalent of Claude Code's `userConfig`.
- **New `.../repo/.agents/plugins/marketplace.json`**: a catalog that only Codex reads, with the same single entry.
- **New `.../repo/marketplace-policy.json`**: lists the three target tools. Before, the validator was only guessing Claude Code as the target.
- **`.../repo/.claude-plugin/marketplace.json`**: the entry now has a description saying it runs an MCP server and a SessionStart hook and uses an external service with your API key. Copilot CLI reads this catalog too.
- **`.../repo/README.md`**: install commands for each tool and a table of what works where.

## What works in each tool
| | Claude Code | Codex | Copilot CLI |
|---|---|---|---|
| `review` MCP server | yes | yes | yes |
| API key from `userConfig` | yes | **no**: the server starts without `REVIEW_API_KEY` | **no**: same |
| `/review` command | yes | **no** | **no** |
| `reviewer` agent | yes | no | unproven (no command can show it) |
| SessionStart hook | yes | no | unproven (no command can show it) |

**Claude Code: nothing changed.** It lists the same review, reviewer, SessionStart hook and review server before and after the port. `claude plugin validate --strict` gives 0 errors and 0 warnings, both for the catalog and for the plugin on its own.

## The trade-off you should know about
- **Without the port, the MCP server was broken in the other tools.** Copilot CLI was handed the literal command `${CLAUDE_PLUGIN_ROOT}/server/run.sh`, which it can't run. With the port, both Codex and Copilot CLI get the real path to `server/run.sh`.
- **The port costs them the `/review` command.** Before, Codex turned it into a skill (`source-command-review`) and Copilot CLI showed it as the `review` skill. With the port, neither offers it. I compared both layouts on a copy of the plugin with its scripts replaced by empty ones, so no plugin code ran.
- **To keep `review` everywhere**, move `commands/review.md` to `skills/review/SKILL.md`. I tested this on a scratch copy:
  - Claude Code shows the same list of components as before.
  - Codex and Copilot CLI both offer `review`.
  - I did not apply it, because it removes a Claude Code file and the porting guidance says not to do that without your agreement.
  - Adding the skill and keeping the command instead makes Claude Code list `review` twice.
  - Moving it may also let Claude invoke `review` itself, not just when you type it; I didn't test that.
- **The API key never reaches the server in Codex or Copilot CLI.** Codex's settings for the server show no inherited environment, only the plugin's own paths. The server needs another way to get the key, such as reading it from a file. I didn't check how users could supply it.
- **Separate from the port:** `server/run.sh` runs `python3 -m review_server`, and there is no `review_server` module in this repo. It is the same in every tool.

## Checks
| Check | Result |
|---|---|
| Structure (`check-marketplace`) | passed, including the new portable files. I also confirmed it catches a deliberately wrong version. |
| Structure (`claude plugin validate --strict`) | passed. The validator's own run of `claude plugin validate` could not check the plugin itself here; I ran it on a copy without the catalog, and it passed. |
| Paths, names and versions (`check-marketplace`) | passed |
| Remote sources | not applicable: the only source is a local path (`./`) |
| Catalog listing: Claude Code | `claude plugin marketplace add` succeeded |
| Catalog listing: Codex | lists `review-kit` at version 2.0.0 |
| Catalog listing: Copilot CLI | the catalog was accepted and lists `review-kit` |
| Loading: Claude Code | all four components listed, the same as the original |
| Loading: Codex | installed 2.0.0; the `review` server is set up from `mcp.json`; no plugin skills |
| Loading: Copilot CLI | installed and enabled at 2.0.0; `review` server set up; no plugin skills |
| Loading: agents and hooks in Copilot CLI | unproven: no command shows them |
| Actually starting the MCP server | not run on the real plugin, because that would run plugin code |

All the throwaway state is under `.tool-homes/`, and I added that directory to `.git/info/exclude`.

## Tool calls

The arm's tool calls, one JSON object per line, extracted from its transcript.

```jsonl
{"tool": "Bash", "input": {"command": "cd $RUN/repo && git status && git log --oneline | head -5 && find . -path ./.git -prune -o -type f -print | head -100; ls -R $RUN/skill/plugin-marketplaces"}}
{"tool": "Read", "input": {"file_path": "$RUN/skill/plugin-marketplaces/SKILL.md"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && for f in $(git ls-files); do echo \"=== $f\"; cat \"$f\"; done"}}
{"tool": "Bash", "input": {"command": "cd $RUN/skill/plugin-marketplaces/references && cat multi-tool.md feature-matrix.md agent-plugins.md"}}
{"tool": "Bash", "input": {"command": "cd $RUN/skill/plugin-marketplaces/references && cat validation.md codex.md copilot-cli.md releases.md"}}
{"tool": "Bash", "input": {"command": "cd $RUN/skill/plugin-marketplaces && cat scripts/mpcheck/policy.py | head -150; grep -rn \"policy\" references/*.md | grep -i \"marketplace-policy\" | head; cat references/claude-code.md | head -80"}}
{"tool": "Bash", "input": {"command": "cd $RUN/skill/plugin-marketplaces && which claude codex copilot git python3; cat scripts/mpcheck/data/readers.json | head -60; sed -n 150,260p scripts/mpcheck/policy.py"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && R=$PWD; T=\"$R/.tool-homes\"; mkdir -p \"$T\"/{home,xdg,tmp,claude,codex,copilot,copilot-cache}; : > \"$T/gitconfig\"; grep -q tool-homes .git/info/exclude || echo \".tool-homes/\" >> .git/info/exclude\nexport HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\"\nclaude --version </dev/null; codex --version </dev/null; copilot --version </dev/null\n$RUN/validator/bin/check-marketplace \"$R\" </dev/null; echo exit=$?"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && mkdir -p .agents/plugins\ncat > plugin.json <<'EOF'\n{\n  \"$schema\": \"https://agent-plugins.org/schemas/1.0.0/plugin.schema.json\",\n  \"name\": \"review-kit\",\n  \"version\": \"2.0.0\",\n  \"description\": \"Code review helpers\",\n  \"author\": {\n    \"name\": \"Acme\"\n  }\n}\nEOF\ncat > mcp.json <<'EOF'\n{\n  \"$schema\": \"https://agent-plugins.org/schemas/1.0.0/mcp.schema.json\",\n  \"mcpServers\": {\n    \"review\": {\n      \"type\": \"stdio\",\n      \"command\": \"./server/run.sh\",\n      \"cwd\": \"${PLUGIN_ROOT}\"\n    }\n  }\n}\nEOF\nDESC=\"Code review helpers. Runs a local MCP server (server/run.sh) that talks to an external review service using your API key; in Claude Code it also runs a SessionStart hook (scripts/start.sh).\"\ncat > .agents/plugins/marketplace.json <<EOF\n{\n  \"name\": \"review-kit\",\n  \"plugins\": [\n    {\n      \"name\": \"review-kit\",\n      \"source\": {\n        \"source\": \"local\",\n        \"path\": \"./\"\n      },\n      \"description\": \"$DESC\",\n      \"policy\": {\n        \"installation\": \"AVAILABLE\",\n        \"authentication\": \"ON_INSTALL\"\n      },\n      \"category\": \"Coding\"\n    }\n  ]\n}\nEOF\npython3 - \"$DESC\" <<'EOF'\nimport json,sys\np='.claude-plugin/marketplace.json'\nd=json.load(open(p))\nd['plugins'][0]['description']=sys.argv[1]\nopen(p,'w').write(json.dumps(d,indent=2)+\"\\n\")\nEOF\ncat > marketplace-policy.json <<'EOF'\n{\n  \"readers\": [\"claude-code\", \"codex\", \"copilot-cli\"]\n}\nEOF\ncat .claude-plugin/marketplace.json; $RUN/validator/bin/check-marketplace . </dev/null; echo exit=$?"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && R=$PWD; T=\"$R/.tool-homes\"\nexport HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\"\nrm -rf \"$T/idx\" \"$T/export\" \"$T/neg\"; mkdir -p \"$T/export\" \"$T/neg\"\nGIT_INDEX_FILE=\"$T/idx\" git read-tree HEAD && GIT_INDEX_FILE=\"$T/idx\" git add -A && TREE=$(GIT_INDEX_FILE=\"$T/idx\" git write-tree)\ngit archive $TREE | tar -x -C \"$T/export\"; git archive $TREE | tar -x -C \"$T/neg\"\nfind \"$T/export\" -type f | sort\n# negative control: version mismatch + portable name mismatch\nsed -i '' 's/\"2.0.0\"/\"2.0.1\"/' \"$T/neg/plugin.json\"\n$RUN/validator/bin/check-marketplace \"$T/neg\" </dev/null | tail -4; echo exit=$?"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && R=$PWD; T=\"$R/.tool-homes\"\nexport HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\"\nSB=\"sandbox-exec -p (version 1)(allow default)(deny network-outbound (remote ip))\"\necho \"--- marketplace validate\"; $SB claude plugin validate \"$T/export\" --strict --json </dev/null; echo exit=$?\nrm -rf \"$T/pluginonly\"; cp -R \"$T/export\" \"$T/pluginonly\"; rm \"$T/pluginonly/.claude-plugin/marketplace.json\"\necho \"--- plugin validate\"; $SB claude plugin validate \"$T/pluginonly\" --strict --json </dev/null; echo exit=$?\necho \"--- add\"; $SB claude plugin marketplace add \"$T/export\" </dev/null; echo exit=$?\necho \"--- details\"; $SB claude plugin details review-kit@review-kit </dev/null; echo exit=$?"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && R=$PWD; T=\"$R/.tool-homes\"\nexport HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\"\nsb(){ sandbox-exec -p '(version 1)(allow default)(deny network-outbound (remote ip))' \"$@\" </dev/null; }\necho \"--- marketplace validate\"; sb claude plugin validate \"$T/export\" --strict --json; echo exit=$?\necho \"--- plugin validate\"; sb claude plugin validate \"$T/pluginonly\" --strict --json; echo exit=$?\necho \"--- add\"; sb claude plugin marketplace add \"$T/export\"; echo exit=$?\necho \"--- details\"; sb claude plugin details review-kit@review-kit; echo exit=$?"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && R=$PWD; T=\"$R/.tool-homes\"\nexport HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\"\nsb(){ sandbox-exec -p '(version 1)(allow default)(deny network-outbound (remote ip))' \"$@\" </dev/null; }\nsb claude plugin details --help | head -20; echo; sb claude plugin details review-kit --plugin-dir \"$T/export\"; echo exit=$?"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && R=$PWD; T=\"$R/.tool-homes\"\nexport HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\"\nsb(){ sandbox-exec -p '(version 1)(allow default)(deny network-outbound (remote ip))' \"$@\" </dev/null; }\nsb claude --plugin-dir \"$T/export\" plugin details review-kit; echo exit=$?"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && R=$PWD; T=\"$R/.tool-homes\"\nexport HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\"\nsb(){ sandbox-exec -p '(version 1)(allow default)(deny network-outbound (remote ip))' \"$@\" </dev/null; }\nrm -rf \"$T/orig\"; mkdir -p \"$T/orig\"; git archive HEAD | tar -x -C \"$T/orig\"\nsb claude --plugin-dir \"$T/orig\" plugin details review-kit | sed -n 1,10p\necho \"=== codex\"; sb codex plugin marketplace add \"$T/export\"; echo exit=$?\nsb codex plugin list --available --json; echo exit=$?"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && R=$PWD; T=\"$R/.tool-homes\"\nexport HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\"\nsb(){ sandbox-exec -p '(version 1)(allow default)(deny network-outbound (remote ip))' \"$@\" </dev/null; }\nsb codex plugin add review-kit@review-kit --json; echo exit=$?\nfind \"$T/codex/plugins/cache\" -type f | sed \"s|$T/codex/plugins/cache/||\" | sort\necho \"--- mcp\"; sb codex mcp list --json; echo exit=$?"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && R=$PWD; T=\"$R/.tool-homes\"\nsb(){ sandbox-exec -p '(version 1)(allow default)(deny network-outbound (remote ip))' \"$@\" </dev/null; }\nfor v in orig export; do\n  S=\"$T/stand-$v\"; H=\"$T/sh-$v\"; rm -rf \"$S\" \"$H\"; cp -R \"$T/$v\" \"$S\"; mkdir -p \"$H\"/{home,xdg,tmp,codex,work}\n  printf '#!/bin/sh\\nexit 0\\n' > \"$S/server/run.sh\"; printf '#!/bin/sh\\nexit 0\\n' > \"$S/scripts/start.sh\"\n  ( export HOME=\"$H/home\" XDG_CONFIG_HOME=\"$H/xdg\" TMPDIR=\"$H/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CODEX_HOME=\"$H/codex\"\n    cd \"$H/work\" && sb codex plugin marketplace add \"$S\" >/dev/null && sb codex plugin add review-kit@review-kit --json | grep version\n    echo \"== $v prompt-input skills:\"; sb codex debug prompt-input 2>&1 | grep -iE \"review|source-command\" | head -20 )\ndone"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && R=$PWD; T=\"$R/.tool-homes\"\nexport HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\"\nsb(){ sandbox-exec -p '(version 1)(allow default)(deny network-outbound (remote ip))' \"$@\" </dev/null; }\nrm -rf \"$T/try\"; cp -R \"$T/export\" \"$T/try\"; mkdir -p \"$T/try/skills/review\"\nprintf -- '---\\nname: review\\ndescription: Review the current diff\\n---\\n\\nReview the staged diff and list problems.\\n' > \"$T/try/skills/review/SKILL.md\"\nsb claude --plugin-dir \"$T/try\" plugin details review-kit | sed -n 5,8p\nsb claude --plugin-dir \"$T/try\" plugin details review-kit | grep -A6 Per-component"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && R=$PWD; T=\"$R/.tool-homes\"\nexport HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\"\nsb(){ sandbox-exec -p '(version 1)(allow default)(deny network-outbound (remote ip))' \"$@\" </dev/null; }\ncd \"$T/tmp\"\necho \"--- add\"; sb copilot plugin marketplace add \"$T/export\"; echo exit=$?\necho \"--- browse\"; sb copilot plugin marketplace browse review-kit --json; echo exit=$?\necho \"--- install\"; sb copilot plugin install review-kit@review-kit; echo exit=$?\necho \"--- list\"; sb copilot plugin list; echo exit=$?\necho \"--- skills\"; sb copilot skill list 2>&1 | grep -i -B1 -A1 review; \necho \"--- mcp\"; sb copilot mcp list; sb copilot mcp get review; echo exit=$?"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && R=$PWD; T=\"$R/.tool-homes\"\nsb(){ sandbox-exec -p '(version 1)(allow default)(deny network-outbound (remote ip))' \"$@\" </dev/null; }\nfor v in export orig; do H=\"$T/cp-$v\"; rm -rf \"$H\"; mkdir -p \"$H\"/{home,xdg,tmp,copilot,cache}\n( export HOME=\"$H/home\" XDG_CONFIG_HOME=\"$H/xdg\" TMPDIR=\"$H/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 COPILOT_HOME=\"$H/copilot\" COPILOT_CACHE_HOME=\"$H/cache\"\n  cd \"$H/tmp\"; sb copilot plugin marketplace add \"$T/$v\" >/dev/null; sb copilot plugin install review-kit@review-kit | head -1\n  echo \"== $v skill list:\"; sb copilot skill list 2>&1 | head -30; echo \"== $v mcp:\"; sb copilot mcp get review | grep -E \"Command|Args\" )\ndone"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && R=$PWD; T=\"$R/.tool-homes\"\nsb(){ sandbox-exec -p '(version 1)(allow default)(deny network-outbound (remote ip))' \"$@\" </dev/null; }\nV=\"$T/mv\"; rm -rf \"$V\"; cp -R \"$T/export\" \"$V\"; mkdir -p \"$V/skills/review\"\nprintf -- '---\\nname: review\\ndescription: Review the current diff\\n---\\n\\nReview the staged diff and list problems.\\n' > \"$V/skills/review/SKILL.md\"; rm -r \"$V/commands\"\n( export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" CLAUDE_CONFIG_DIR=\"$T/claude\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1; sb claude --plugin-dir \"$V\" plugin details review-kit | sed -n 5,10p )\nS=\"$T/stand-mv\"; H=\"$T/sh-mv\"; rm -rf \"$S\" \"$H\"; cp -R \"$V\" \"$S\"; mkdir -p \"$H\"/{home,xdg,tmp,codex,work,copilot,cache}\nprintf '#!/bin/sh\\nexit 0\\n' > \"$S/server/run.sh\"; printf '#!/bin/sh\\nexit 0\\n' > \"$S/scripts/start.sh\"\n( export HOME=\"$H/home\" XDG_CONFIG_HOME=\"$H/xdg\" TMPDIR=\"$H/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CODEX_HOME=\"$H/codex\" COPILOT_HOME=\"$H/copilot\" COPILOT_CACHE_HOME=\"$H/cache\"\n  cd \"$H/work\"; sb codex plugin marketplace add \"$S\" >/dev/null; sb codex plugin add review-kit@review-kit --json >/dev/null\n  echo \"== codex:\"; sb codex debug prompt-input 2>&1 | grep -oE \"review-kit:review[^(]*\\(file: [^)]*\\)\"\n  sb copilot plugin marketplace add \"$S\" >/dev/null; sb copilot plugin install review-kit@review-kit | head -1\n  echo \"== copilot:\"; sb copilot skill list | sed -n 1,3p )"}}
{"tool": "Write", "input": {"file_path": "$RUN/repo/README.md", "content": "# review-kit\n\nCode review helpers for Claude Code, Codex, and GitHub Copilot CLI.\n\n## Install\n\nClaude Code:\n\n```sh\nclaude plugin marketplace add <owner>/<repo>\nclaude plugin install review-kit@review-kit\n```\n\nCodex:\n\n```sh\ncodex plugin marketplace add <owner>/<repo>\ncodex plugin add review-kit@review-kit\n```\n\nGitHub Copilot CLI:\n\n```sh\ncopilot plugin marketplace add <owner>/<repo>\ncopilot plugin install review-kit@review-kit\n```\n\n## What each tool gets\n\n| Component | Claude Code | Codex | Copilot CLI |\n| --- | --- | --- | --- |\n| `review` MCP server | yes | yes | yes |\n| Review API key (`userConfig`) | yes, prompted at install | no: the server starts without `REVIEW_API_KEY` | no: the server starts without `REVIEW_API_KEY` |\n| `/review` command | yes | no | no |\n| `reviewer` agent | yes | no | not confirmed |\n| `SessionStart` hook | yes | no | not confirmed |\n\n## Layout\n\n- Claude Code reads `.claude-plugin/plugin.json`, `.mcp.json`, `commands/`, `agents/`, and `hooks/`.\n- Codex and Copilot CLI read the portable [Agent Plugins](https://agent-plugins.org/) pair, `plugin.json` and `mcp.json`.\n- Codex reads the catalog `.agents/plugins/marketplace.json`; Claude Code and Copilot CLI read `.claude-plugin/marketplace.json`.\n- `marketplace-policy.json` declares the three target tools.\n- Keep `name` and `version` equal in `plugin.json` and `.claude-plugin/plugin.json`, and keep the servers in `mcp.json` and `.mcp.json` the same.\n"}}
{"tool": "Read", "input": {"file_path": "$RUN/repo/README.md"}}
{"tool": "Write", "input": {"file_path": "$RUN/repo/README.md", "content": "# review-kit\n\nCode review helpers for Claude Code, Codex, and GitHub Copilot CLI.\n\n## Install\n\nClaude Code:\n\n```sh\nclaude plugin marketplace add <owner>/<repo>\nclaude plugin install review-kit@review-kit\n```\n\nCodex:\n\n```sh\ncodex plugin marketplace add <owner>/<repo>\ncodex plugin add review-kit@review-kit\n```\n\nGitHub Copilot CLI:\n\n```sh\ncopilot plugin marketplace add <owner>/<repo>\ncopilot plugin install review-kit@review-kit\n```\n\n## What each tool gets\n\n| Component | Claude Code | Codex | Copilot CLI |\n| --- | --- | --- | --- |\n| `review` MCP server | yes | yes | yes |\n| Review API key (`userConfig`) | yes, prompted at install | no: the server starts without `REVIEW_API_KEY` | no: the server starts without `REVIEW_API_KEY` |\n| `/review` command | yes | no | no |\n| `reviewer` agent | yes | no | not confirmed |\n| `SessionStart` hook | yes | no | not confirmed |\n\n## Layout\n\n- Claude Code reads `.claude-plugin/plugin.json`, `.mcp.json`, `commands/`, `agents/`, and `hooks/`.\n- Codex and Copilot CLI read the portable [Agent Plugins](https://agent-plugins.org/) pair, `plugin.json` and `mcp.json`.\n- Codex reads the catalog `.agents/plugins/marketplace.json`; Claude Code and Copilot CLI read `.claude-plugin/marketplace.json`.\n- `marketplace-policy.json` declares the three target tools.\n- Keep `name` and `version` equal in `plugin.json` and `.claude-plugin/plugin.json`, and keep the servers in `mcp.json` and `.mcp.json` the same.\n"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && $RUN/validator/bin/check-marketplace . </dev/null | head -9; echo exit=${pipestatus[1]}; git status --short; git diff --stat"}}
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
index 0000000..a239709
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
+      "description": "Code review helpers. Runs a local MCP server (server/run.sh) that talks to an external review service using your API key; in Claude Code it also runs a SessionStart hook (scripts/start.sh).",
+      "policy": {
+        "installation": "AVAILABLE",
+        "authentication": "ON_INSTALL"
+      },
+      "category": "Coding"
+    }
+  ]
+}
diff --git a/.claude-plugin/marketplace.json b/.claude-plugin/marketplace.json
index a015458..6701410 100644
--- a/.claude-plugin/marketplace.json
+++ b/.claude-plugin/marketplace.json
@@ -7,7 +7,8 @@
   "plugins": [
     {
       "name": "review-kit",
-      "source": "./"
+      "source": "./",
+      "description": "Code review helpers. Runs a local MCP server (server/run.sh) that talks to an external review service using your API key; in Claude Code it also runs a SessionStart hook (scripts/start.sh)."
     }
   ]
 }
diff --git a/README.md b/README.md
index 9246da6..55fef3e 100644
--- a/README.md
+++ b/README.md
@@ -1,3 +1,44 @@
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
+| `review` MCP server | yes | yes | yes |
+| Review API key (`userConfig`) | yes, prompted at install | no: the server starts without `REVIEW_API_KEY` | no: the server starts without `REVIEW_API_KEY` |
+| `/review` command | yes | no | no |
+| `reviewer` agent | yes | no | not confirmed |
+| `SessionStart` hook | yes | no | not confirmed |
+
+## Layout
+
+- Claude Code reads `.claude-plugin/plugin.json`, `.mcp.json`, `commands/`, `agents/`, and `hooks/`.
+- Codex and Copilot CLI read the portable [Agent Plugins](https://agent-plugins.org/) pair, `plugin.json` and `mcp.json`.
+- Codex reads the catalog `.agents/plugins/marketplace.json`; Claude Code and Copilot CLI read `.claude-plugin/marketplace.json`.
+- `marketplace-policy.json` declares the three target tools.
+- Keep `name` and `version` equal in `plugin.json` and `.claude-plugin/plugin.json`, and keep the servers in `mcp.json` and `.mcp.json` the same.
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
master 84d625f
```
