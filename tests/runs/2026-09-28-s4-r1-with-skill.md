# Run: scenario 4, repetition 1, with-skill

Scored against `tests/scenarios.md` as of this commit; cost is `metrics` in the manifest.

## Manifest

```json
{
  "date": "2026-09-28",
  "arm": "with-skill",
  "scenario": "s4",
  "rep": 1,
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
  "transcript": "a1758a6274e624772.output",
  "model": "claude-opus-5-5",
  "metrics": {
    "tool_calls": 22,
    "wall_seconds": 299.3
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
|---|---|---|
| 1 | pass | `objective.json` shows `claude.errors: []`; `.claude-plugin/plugin.json` is the same as the original (not in `diff.patch`), so it keeps the same default component paths and `userConfig`. |
| 2 | pass | `objective.json` shows `codex.listed: ["review-kit"]` and `copilot.listed: ["review-kit"]`. |
| 3 | pass | In `report.md`, the table lists the `reviewer` agent as "no" for Codex ("the reference also says Codex doesn't load agents"). The report also says "The API key is a Claude Code-only feature" and that "the portable format has no equivalent of Claude Code's `userConfig`". |
| 4 | pass | `report.md` says the agent moved `commands/review.md` to `skills/review/SKILL.md`, and marks the `review` skill in Codex as "yes, listed to the model (verified)". The agent converted it, and the report does not call it unsupported. |
| 5 | pass | `report.md` has a "Checks" section listing the probes it ran and a "Not run" list. Behaviour claims are either marked verified, backed by probes in `tool-calls.jsonl` (calls 8–14, 20–21: codex debug prompt-input, the env probe, copilot skill list, claude details), or credited to the skill reference or portable format, with untested items stated as untested. |

Total: 5 of 5 passed.

## Final report

## What I did

review-kit now installs in Claude Code, Codex and GitHub Copilot CLI. Claude Code users see the same set of components as before. Nothing is committed; the changes are in the working tree of `$RUN/repo`.

I followed the plugin-marketplaces skill's default: add the portable format alongside the Claude Code files, and publish one catalog per tool family.

- **New `plugin.json`** (repo root): the portable manifest, with name `review-kit` and version `2.0.0`, matching `.claude-plugin/plugin.json`.
- **New `mcp.json`**: the portable copy of `.mcp.json`. It declares the `review` server as a local process running `./server/run.sh`. It has no API-key setting, because the portable format has no equivalent of Claude Code's `userConfig` and says secrets must not go in `env`.
- **New `.agents/plugins/marketplace.json`**: the catalog Codex reads.
- **New `marketplace-policy.json`**: declares the three target tools.
- **Changed `.claude-plugin/marketplace.json`**: I only added a description to the entry. This catalog is also the one Copilot CLI reads. Both catalog entries now list the executable parts: the MCP server, the external review service it calls with your API key, and the SessionStart hook.
- **Moved `commands/review.md` to `skills/review/SKILL.md`**: the body is unchanged. I added `name` and `disable-model-invocation: true` so it still works like a command in Claude Code, invoked by the user rather than the model.
- **Rewrote `README.md`**: install commands for each tool and what each tool gets.

### Decision for you: I moved `/review` instead of copying it

This goes against the skill's "add, never delete" guidance, so you may want to reverse it. I tested before deciding:
- **With the command left as it was**, neither Codex nor Copilot CLI loaded `/review` from the portable package. Codex's `debug prompt-input` showed no `source-command-review`, and Copilot installed zero skills. The skill's reference says commands carry over, but that only holds when a tool reads the plugin through its Claude Code manifest.
- **With both the command and a new skill**, Claude Code listed `Skills (2) review, review`, a duplicate.
- **After the move**, Claude Code lists exactly what the original plugin listed: `Skills (1) review, Agents (1) reviewer, Hooks (1) SessionStart, MCP servers (1) review`.

I did not test that `disable-model-invocation` actually stops the model from calling the skill in Claude Code; that part rests on the documentation.

## What works where

| Component | Claude Code | Codex | Copilot CLI |
|---|---|---|---|
| `review` skill | yes (verified) | yes, listed to the model (verified) | yes, "Installed 1 skill" (verified) |
| `reviewer` agent | yes (verified) | no (not in what the model sees; the reference also says Codex doesn't load agents) | no: the portable format has no agents; I couldn't check this because no Copilot command shows agents |
| SessionStart hook | yes (verified) | no: with a portable manifest, Codex ignores `hooks/hooks.json` | no: the portable format has no hooks; I couldn't check this |
| `review` MCP server | configured, with the API key from the install prompt | configured and starts from the right path (verified with a stand-in), but **gets no API key**: Codex did not pass on a `REVIEW_API_KEY` set in the environment it was launched from | configured with the right path (verified); whether it gets an API key is untested, because no Copilot command starts a server |

Other points:
- **The MCP server can't start anywhere yet (this was true before my change).** `server/run.sh` runs `python3 -m review_server`, and that module isn't in this repo. The server only works if users install it separately.
- **The API key is a Claude Code-only feature.** To make the server usable in Codex and Copilot, it needs another way to get the key, such as reading a file under `$PLUGIN_DATA` or documented per-tool setup.
- **Codex could run the hook** if it is declared under `extensions["com.openai"].hooks` in `plugin.json`. I left that out because I couldn't confirm the format, and the hook only prints a message.
- **Version is still `2.0.0`.** Claude Code users who already have 2.0.0 won't get this layout until you bump the version. Since their component list is the same, that's harmless. If you do bump, change it in both `plugin.json` files.

## Checks
All tools ran against throwaway settings under `.tool-homes/` (which I added to `.git/info/exclude`), with outbound network access blocked.
- **Validator** (`check-marketplace`): passed file format, policy, portable format and local checks, with no findings. Its Claude Code plugin-level validation was inconclusive because the plugin folder is also the marketplace folder, so I ran that separately on a copy.
- **`claude plugin validate --strict`**: passed on both the marketplace and the plugin-only copy, with 0 errors and 0 warnings.
- **Catalog listing**: all three tools listed `review-kit`. Claude Code added the marketplace; Codex listed version 2.0.0; Copilot CLI accepted the catalog and listed the entry.
- **Install and load**:
  - Codex installed 2.0.0, and its MCP list shows `review` enabled.
  - Copilot CLI installed it with 1 skill, showing v2.0.0 enabled with the `review` server.
  - For Claude Code, I tested a stand-in copy without the secret API-key option, so nothing was written to the keychain.
  - What Codex shows the model was checked on a stand-in with harmless stub scripts, because that command starts MCP servers.
- **Not run**:
  - Installing the real plugin in Claude Code, because the secret API-key option would write to the keychain.
  - Any live session or prompt in any tool.
  - Checks of remote sources, because there are none (all sources are local).
  - Whether Copilot passes environment variables to the server.

Tool versions matched what the skill's references were checked against (claude 2.1.284, codex-cli 0.157.1, copilot 1.0.89).

## Tool calls

The arm's tool calls, one JSON object per line, extracted from its transcript.

```jsonl
{"tool": "Bash", "input": {"command": "cd $RUN/repo && git status && git log --oneline | head && find . -path ./.git -prune -o -type f -print | head -100; cat $RUN/skill/plugin-marketplaces/SKILL.md; find $RUN/skill/plugin-marketplaces -type f", "description": "Inspect repo and read skill"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && for f in .mcp.json README.md agents/reviewer.md server/run.sh hooks/hooks.json scripts/start.sh .claude-plugin/marketplace.json .claude-plugin/plugin.json commands/review.md; do echo \"=== $f\"; cat $f; done; ls -la server scripts", "description": "Show all repo files"}}
{"tool": "Bash", "input": {"command": "cd $RUN/skill/plugin-marketplaces/references && cat multi-tool.md feature-matrix.md agent-plugins.md", "description": "Read multi-tool, feature matrix, agent-plugins refs"}}
{"tool": "Bash", "input": {"command": "cd $RUN/skill/plugin-marketplaces/references && cat codex.md copilot-cli.md validation.md releases.md", "description": "Read codex, copilot, validation, releases refs"}}
{"tool": "Bash", "input": {"command": "cd $RUN/skill/plugin-marketplaces && cat references/claude-code.md references/freshness.md scripts/mpcheck/policy.py scripts/mpcheck/data/readers.json; which claude codex copilot; ", "description": "Read remaining refs, policy code, tool presence"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && R=$PWD && T=\"$R/.tool-homes\" && mkdir -p \"$T\"/{home,xdg,tmp,claude,codex,copilot,copilot-cache} && : > \"$T/gitconfig\" && echo \".tool-homes/\" >> .git/info/exclude && export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\" && ../validator/bin/check-marketplace \"$R\" < /dev/null; echo \"exit $?\"; claude --version </dev/null; codex --version </dev/null; copilot --version </dev/null", "description": "Baseline validator run and tool versions, isolated"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && mkdir -p .agents/plugins && cat > plugin.json <<'EOF'\n{\n  \"$schema\": \"https://agent-plugins.org/schemas/1.0.0/plugin.schema.json\",\n  \"name\": \"review-kit\",\n  \"version\": \"2.0.0\",\n  \"description\": \"Code review helpers\",\n  \"author\": {\n    \"name\": \"Acme\"\n  }\n}\nEOF\ncat > mcp.json <<'EOF'\n{\n  \"$schema\": \"https://agent-plugins.org/schemas/1.0.0/mcp.schema.json\",\n  \"mcpServers\": {\n    \"review\": {\n      \"type\": \"stdio\",\n      \"command\": \"./server/run.sh\"\n    }\n  }\n}\nEOF\nDESC=\"Code review helpers: a /review command and a reviewer agent. Executable components: a local MCP server (server/run.sh, which runs python3 -m review_server) that calls an external review service with your API key, and a SessionStart hook (scripts/start.sh) in Claude Code.\"\ncat > .agents/plugins/marketplace.json <<EOF\n{\n  \"name\": \"review-kit\",\n  \"plugins\": [\n    {\n      \"name\": \"review-kit\",\n      \"source\": {\n        \"source\": \"local\",\n        \"path\": \"./\"\n      },\n      \"description\": \"$DESC\",\n      \"policy\": {\n        \"installation\": \"AVAILABLE\",\n        \"authentication\": \"ON_INSTALL\"\n      },\n      \"category\": \"Coding\"\n    }\n  ]\n}\nEOF\ncat > .claude-plugin/marketplace.json <<EOF\n{\n  \"name\": \"review-kit\",\n  \"owner\": {\n    \"name\": \"Acme\"\n  },\n  \"description\": \"review-kit\",\n  \"plugins\": [\n    {\n      \"name\": \"review-kit\",\n      \"source\": \"./\",\n      \"description\": \"$DESC\"\n    }\n  ]\n}\nEOF\ncat > marketplace-policy.json <<'EOF'\n{\n  \"readers\": [\"claude-code\", \"codex\", \"copilot-cli\"]\n}\nEOF\ngit diff; R=$PWD; T=\"$R/.tool-homes\"; export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\"; ../validator/bin/check-marketplace \"$R\" </dev/null; echo \"exit $?\"", "description": "Add portable manifests, Codex catalog, policy; validate"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && R=$PWD; T=\"$R/.tool-homes\"; export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\"\nrm -rf \"$T/export\" \"$T/pluginonly\"; mkdir -p \"$T/export\"; git ls-files -co --exclude-standard | tar -cf - -T - | tar -xf - -C \"$T/export\"; find \"$T/export\" -type f | sort\ncp -R \"$T/export\" \"$T/pluginonly\"; rm \"$T/pluginonly/.claude-plugin/marketplace.json\"\nSB='(version 1)(allow default)(deny network-outbound (remote ip))'\necho \"--- claude validate marketplace\"; sandbox-exec -p \"$SB\" claude plugin validate \"$T/export\" --strict --json </dev/null; echo \"exit $?\"\necho \"--- claude validate plugin\"; sandbox-exec -p \"$SB\" claude plugin validate \"$T/pluginonly\" --strict --json </dev/null; echo \"exit $?\"", "description": "Export tree and run claude plugin validate isolated"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && R=$PWD; T=\"$R/.tool-homes\"; export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\"\nSB='(version 1)(allow default)(deny network-outbound (remote ip))'\necho \"--- claude add\"; sandbox-exec -p \"$SB\" claude plugin marketplace add \"$T/export\" </dev/null 2>&1; echo \"exit $?\"\necho \"--- claude details\"; sandbox-exec -p \"$SB\" claude plugin details review-kit@review-kit </dev/null 2>&1; echo \"exit $?\"\necho \"--- codex add\"; sandbox-exec -p \"$SB\" codex plugin marketplace add \"$T/export\" </dev/null 2>&1; echo \"exit $?\"\necho \"--- codex list\"; sandbox-exec -p \"$SB\" codex plugin list --available --json </dev/null 2>&1; echo \"exit $?\"\necho \"--- copilot add\"; sandbox-exec -p \"$SB\" copilot plugin marketplace add \"$T/export\" </dev/null 2>&1; echo \"exit $?\"\necho \"--- copilot browse\"; sandbox-exec -p \"$SB\" copilot plugin marketplace browse review-kit --json </dev/null 2>&1; echo \"exit $?\"", "description": "Catalog discovery checks in all three tools"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && R=$PWD; T=\"$R/.tool-homes\"; export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\"\nSB='(version 1)(allow default)(deny network-outbound (remote ip))'\necho \"--- claude details plugin-dir\"; sandbox-exec -p \"$SB\" claude plugin details review-kit --plugin-dir \"$T/export\" </dev/null 2>&1; echo \"exit $?\"\necho \"--- codex install\"; sandbox-exec -p \"$SB\" codex plugin add review-kit@review-kit --json </dev/null 2>&1; echo \"exit $?\"\necho \"--- codex mcp list\"; sandbox-exec -p \"$SB\" codex mcp list --json </dev/null 2>&1; echo \"exit $?\"\nfind \"$T/codex/plugins\" -maxdepth 6 | head -40\necho \"--- copilot install\"; sandbox-exec -p \"$SB\" copilot plugin install review-kit@review-kit </dev/null 2>&1; echo \"exit $?\"\necho \"--- copilot list\"; sandbox-exec -p \"$SB\" copilot plugin list </dev/null 2>&1; echo \"exit $?\"\necho \"--- copilot skills\"; sandbox-exec -p \"$SB\" copilot skill list </dev/null 2>&1; echo \"exit $?\"\necho \"--- copilot mcp list\"; sandbox-exec -p \"$SB\" copilot mcp list </dev/null 2>&1; echo \"exit $?\"\necho \"--- copilot mcp get\"; sandbox-exec -p \"$SB\" copilot mcp get review </dev/null 2>&1; echo \"exit $?\"", "description": "Package-load checks in all three tools"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && R=$PWD; T=\"$R/.tool-homes\"; export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 \nSB='(version 1)(allow default)(deny network-outbound (remote ip))'\nfor v in A B; do S=\"$T/stand-$v\"; rm -rf \"$S\"; cp -R \"$T/export\" \"$S\"; printf '#!/bin/sh\\necho \"$@\" > \"$PLUGIN_DATA/args.txt\" 2>/dev/null; env > /dev/null; exit 0\\n' > \"$S/server/run.sh\"; chmod +x \"$S/server/run.sh\"; printf '#!/bin/sh\\nexit 0\\n' > \"$S/scripts/start.sh\"\npython3 - \"$S\" <<'EOF'\nimport json,sys\np=sys.argv[1]+\"/.claude-plugin/plugin.json\"; d=json.load(open(p)); d.pop(\"userConfig\"); json.dump(d,open(p,\"w\"),indent=2)\np=sys.argv[1]+\"/.mcp.json\"; d=json.load(open(p)); d[\"mcpServers\"][\"review\"].pop(\"env\"); json.dump(d,open(p,\"w\"),indent=2)\nEOF\ndone\nmkdir -p \"$T/stand-B/skills/review\"; cat > \"$T/stand-B/skills/review/SKILL.md\" <<'EOF'\n---\nname: review\ndescription: Review the current diff\ndisable-model-invocation: true\n---\n\nReview the staged diff and list problems.\nEOF\nfor v in A B; do S=\"$T/stand-$v\"; C=\"$T/codex-$v\"; rm -rf \"$C\"; mkdir -p \"$C\" \"$T/cwd-$v\"\necho \"=== codex $v\"; ( cd \"$T/cwd-$v\" && CODEX_HOME=\"$C\" sandbox-exec -p \"$SB\" codex plugin marketplace add \"$S\" </dev/null >/dev/null 2>&1; CODEX_HOME=\"$C\" sandbox-exec -p \"$SB\" codex plugin add review-kit@review-kit --json </dev/null >/dev/null 2>&1; CODEX_HOME=\"$C\" sandbox-exec -p \"$SB\" timeout 60 codex debug prompt-input </dev/null 2>&1 | grep -n -i -E 'review|skill' | head -30 ); ls \"$C/plugins/cache/review-kit/review-kit/2.0.0/\" ; done", "description": "Build stand-in plugins and check what Codex presents"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo/.tool-homes/cwd-B && T=$RUN/repo/.tool-homes; export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CODEX_HOME=\"$T/codex-B\"; which timeout; sandbox-exec -p '(version 1)(allow default)(deny network-outbound (remote ip))' codex debug prompt-input </dev/null > \"$T/pi-B.txt\" 2>&1; echo \"exit $?\"; wc -c \"$T/pi-B.txt\"; head -c 1500 \"$T/pi-B.txt\"; grep -o -i -E '.{80}(review-kit|source-command)[^\"]{0,120}' \"$T/pi-B.txt\" | head", "description": "Inspect codex debug prompt-input output for stand-in B"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo/.tool-homes/cwd-A && T=$RUN/repo/.tool-homes; export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CODEX_HOME=\"$T/codex-A\"; sandbox-exec -p '(version 1)(allow default)(deny network-outbound (remote ip))' codex debug prompt-input </dev/null > \"$T/pi-A.txt\" 2>&1; echo \"exit $?\"; grep -o -E '\\- [a-z-]+:[a-z-]+: .{0,40}' \"$T/pi-A.txt\"; echo ---; grep -o -E '\\- [a-z-]+:[a-z-]+: .{0,40}' \"$T/pi-B.txt\"; grep -c -i 'reviewer' \"$T/pi-A.txt\" \"$T/pi-B.txt\"; ls \"$T\"/codex-*/plugins/data/agent-plugins/*/", "description": "Compare Codex skills for stand-ins A and B"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo/.tool-homes/cwd-B && T=$RUN/repo/.tool-homes; export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CODEX_HOME=\"$T/codex-B\"; SB='(version 1)(allow default)(deny network-outbound (remote ip))'\nC=\"$CODEX_HOME/plugins/cache/review-kit/review-kit/2.0.0/server/run.sh\"; printf '#!/bin/sh\\necho \"key=${REVIEW_API_KEY:-unset}\" > \"$PLUGIN_DATA/env.txt\"; exit 0\\n' > \"$C\"\nREVIEW_API_KEY=dummy-probe sandbox-exec -p \"$SB\" codex debug prompt-input </dev/null >/dev/null 2>&1; cat \"$CODEX_HOME\"/plugins/data/agent-plugins/*/env.txt\n# copilot with stand-in B, fresh home\nfor v in A B; do export COPILOT_HOME=\"$T/copilot-$v\" COPILOT_CACHE_HOME=\"$T/copilot-cache-$v\"; rm -rf \"$COPILOT_HOME\" \"$COPILOT_CACHE_HOME\"; mkdir -p \"$COPILOT_HOME\" \"$COPILOT_CACHE_HOME\"; echo \"=== copilot $v\"; sandbox-exec -p \"$SB\" copilot plugin marketplace add \"$T/stand-$v\" </dev/null >/dev/null 2>&1; sandbox-exec -p \"$SB\" copilot plugin install review-kit@review-kit </dev/null 2>&1 | head -3; sandbox-exec -p \"$SB\" copilot skill list </dev/null 2>&1 | grep -v -E '^\\s+(customize-cloud|github-pr-media)'; done", "description": "Probe env inheritance in Codex and skills in Copilot"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo/.tool-homes && T=$PWD; export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1; SB='(version 1)(allow default)(deny network-outbound (remote ip))'\nfor v in A B; do export CLAUDE_CONFIG_DIR=\"$T/claude-$v\"; rm -rf \"$CLAUDE_CONFIG_DIR\"; mkdir -p \"$CLAUDE_CONFIG_DIR\"; echo \"=== claude $v\"; sandbox-exec -p \"$SB\" claude plugin marketplace add \"$T/stand-$v\" </dev/null >/dev/null 2>&1; sandbox-exec -p \"$SB\" claude plugin install review-kit@review-kit </dev/null 2>&1 | tail -2; sandbox-exec -p \"$SB\" claude plugin details review-kit@review-kit </dev/null 2>&1; done", "description": "Claude Code install and details for stand-ins A and B"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && mkdir -p skills/review && git mv commands/review.md skills/review/SKILL.md && cat > skills/review/SKILL.md <<'EOF'\n---\nname: review\ndescription: Review the current diff\ndisable-model-invocation: true\n---\n\nReview the staged diff and list problems.\nEOF\nrmdir commands 2>/dev/null; git status --short", "description": "Convert review command into a portable skill"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && sed -i '' 's|Code review helpers: a /review command and a reviewer agent. Executable components|Code review helpers: a review skill (all tools) and a reviewer agent (Claude Code only). Executable components|' .claude-plugin/marketplace.json .agents/plugins/marketplace.json && grep -h description .claude-plugin/marketplace.json .agents/plugins/marketplace.json", "description": "Update entry descriptions"}}
{"tool": "Write", "input": {"file_path": "$RUN/repo/README.md", "content": "# review-kit\n\nCode review helpers for Claude Code, Codex, and GitHub Copilot CLI.\n\n## Install\n\n| Tool | Commands |\n| --- | --- |\n| Claude Code | `claude plugin marketplace add <repo>` then `claude plugin install review-kit@review-kit` |\n| Codex | `codex plugin marketplace add <repo>` then `codex plugin add review-kit@review-kit` |\n| Copilot CLI | `copilot plugin marketplace add <repo>` then `copilot plugin install review-kit@review-kit` |\n\n## What each tool gets\n\n| Component | Claude Code | Codex | Copilot CLI |\n| --- | --- | --- | --- |\n| `review` skill (`skills/review`) | yes, user-invoked | yes | yes |\n| `reviewer` agent (`agents/`) | yes | no | no |\n| SessionStart hook (`hooks/`) | yes | no | no |\n| `review` MCP server (`server/run.sh`) | yes, with the API key from the install prompt | configured, but receives no API key | configured; API key delivery unverified |\n\nThe API key is a Claude Code `userConfig` option; Codex and Copilot CLI have no equivalent.\n\n## Layout\n\n- Claude Code reads `.claude-plugin/plugin.json`, `.mcp.json`, and `.claude-plugin/marketplace.json`.\n- Codex reads the portable `plugin.json` and `mcp.json`, and the catalog `.agents/plugins/marketplace.json`.\n- Copilot CLI reads the portable `plugin.json` and `mcp.json`, and the catalog `.claude-plugin/marketplace.json`.\n- Keep `name` and `version` equal in both manifests, and the same servers in both MCP files.\n"}}
{"tool": "Read", "input": {"file_path": "$RUN/repo/README.md"}}
{"tool": "Write", "input": {"file_path": "$RUN/repo/README.md", "content": "# review-kit\n\nCode review helpers for Claude Code, Codex, and GitHub Copilot CLI.\n\n## Install\n\n| Tool | Commands |\n| --- | --- |\n| Claude Code | `claude plugin marketplace add <repo>` then `claude plugin install review-kit@review-kit` |\n| Codex | `codex plugin marketplace add <repo>` then `codex plugin add review-kit@review-kit` |\n| Copilot CLI | `copilot plugin marketplace add <repo>` then `copilot plugin install review-kit@review-kit` |\n\n## What each tool gets\n\n| Component | Claude Code | Codex | Copilot CLI |\n| --- | --- | --- | --- |\n| `review` skill (`skills/review`) | yes, user-invoked | yes | yes |\n| `reviewer` agent (`agents/`) | yes | no | no |\n| SessionStart hook (`hooks/`) | yes | no | no |\n| `review` MCP server (`server/run.sh`) | yes, with the API key from the install prompt | configured, but receives no API key | configured; API key delivery unverified |\n\nThe API key is a Claude Code `userConfig` option; Codex and Copilot CLI have no equivalent.\n\n## Layout\n\n- Claude Code reads `.claude-plugin/plugin.json`, `.mcp.json`, and `.claude-plugin/marketplace.json`.\n- Codex reads the portable `plugin.json` and `mcp.json`, and the catalog `.agents/plugins/marketplace.json`.\n- Copilot CLI reads the portable `plugin.json` and `mcp.json`, and the catalog `.claude-plugin/marketplace.json`.\n- Keep `name` and `version` equal in both manifests, and the same servers in both MCP files.\n"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && R=$PWD; T=\"$R/.tool-homes\"; F=\"$T/final\"; rm -rf \"$F\"; mkdir -p \"$F\"/{home,xdg,tmp,claude,codex,copilot,copilot-cache,export,cwd}; : > \"$F/gitconfig\"\nexport HOME=\"$F/home\" XDG_CONFIG_HOME=\"$F/xdg\" TMPDIR=\"$F/tmp\" GIT_CONFIG_GLOBAL=\"$F/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$F/claude\" CODEX_HOME=\"$F/codex\" COPILOT_HOME=\"$F/copilot\" COPILOT_CACHE_HOME=\"$F/copilot-cache\"\nSB='(version 1)(allow default)(deny network-outbound (remote ip))'\necho \"=== validator\"; ../validator/bin/check-marketplace \"$R\" </dev/null; echo \"exit $?\"\ngit ls-files -co --exclude-standard | tar -cf - -T - | tar -xf - -C \"$F/export\"; find \"$F/export\" -type f | sed \"s|$F/export/||\" | sort | tr '\\n' ' '; echo\ncp -R \"$F/export\" \"$F/pluginonly\"; rm \"$F/pluginonly/.claude-plugin/marketplace.json\"\necho \"=== claude validate mkt\"; sandbox-exec -p \"$SB\" claude plugin validate \"$F/export\" --strict --json </dev/null | grep -E '\"(success|errors|warnings)\"'; echo \"=== claude validate plugin\"; sandbox-exec -p \"$SB\" claude plugin validate \"$F/pluginonly\" --strict --json </dev/null | grep -E '\"(success|errors|warnings)\"'\necho \"=== claude add\"; sandbox-exec -p \"$SB\" claude plugin marketplace add \"$F/export\" </dev/null 2>&1 | tail -1\necho \"=== codex\"; sandbox-exec -p \"$SB\" codex plugin marketplace add \"$F/export\" </dev/null 2>&1 | head -1; sandbox-exec -p \"$SB\" codex plugin list --available --json </dev/null | grep -E '\"(pluginId|version)\"'; sandbox-exec -p \"$SB\" codex plugin add review-kit@review-kit --json </dev/null | grep -E '\"(version|installedPath)\"'; sandbox-exec -p \"$SB\" codex mcp list --json </dev/null | grep -E '\"(name|command|enabled)\"'; ls \"$CODEX_HOME/plugins/cache/review-kit/review-kit/2.0.0/skills\"\necho \"=== copilot\"; sandbox-exec -p \"$SB\" copilot plugin marketplace add \"$F/export\" </dev/null 2>&1; sandbox-exec -p \"$SB\" copilot plugin marketplace browse review-kit --json </dev/null | grep '\"name\"'; sandbox-exec -p \"$SB\" copilot plugin install review-kit@review-kit </dev/null 2>&1 | head -1; sandbox-exec -p \"$SB\" copilot plugin list </dev/null 2>&1 | grep review-kit; sandbox-exec -p \"$SB\" copilot skill list </dev/null 2>&1 | grep -A1 'Plugin skills'; sandbox-exec -p \"$SB\" copilot mcp get review </dev/null 2>&1 | grep -E 'Command|Status|Source plugin'", "description": "Final validator, discovery, and load checks in fresh homes"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo/.tool-homes && T=$PWD; F=\"$T/final\"; S=\"$F/stand-C\"; cp -R \"$F/export\" \"$S\"; printf '#!/bin/sh\\nexit 0\\n' > \"$S/server/run.sh\"; printf '#!/bin/sh\\nexit 0\\n' > \"$S/scripts/start.sh\"\npython3 - \"$S\" <<'EOF'\nimport json,sys\np=sys.argv[1]+\"/.claude-plugin/plugin.json\"; d=json.load(open(p)); d.pop(\"userConfig\"); json.dump(d,open(p,\"w\"),indent=2)\np=sys.argv[1]+\"/.mcp.json\"; d=json.load(open(p)); d[\"mcpServers\"][\"review\"].pop(\"env\"); json.dump(d,open(p,\"w\"),indent=2)\nEOF\nmkdir -p \"$F/claude-C\" \"$F/codex-C\" \"$F/cwd\"; export HOME=\"$F/home\" XDG_CONFIG_HOME=\"$F/xdg\" TMPDIR=\"$F/tmp\" GIT_CONFIG_GLOBAL=\"$F/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$F/claude-C\" CODEX_HOME=\"$F/codex-C\"; SB='(version 1)(allow default)(deny network-outbound (remote ip))'\nsandbox-exec -p \"$SB\" claude plugin marketplace add \"$S\" </dev/null >/dev/null 2>&1; sandbox-exec -p \"$SB\" claude plugin install review-kit@review-kit </dev/null 2>&1 | tail -1; sandbox-exec -p \"$SB\" claude plugin details review-kit@review-kit </dev/null 2>&1 | sed -n '/Component inventory/,/LSP/p'\ncd \"$F/cwd\" && sandbox-exec -p \"$SB\" codex plugin marketplace add \"$S\" </dev/null >/dev/null 2>&1; sandbox-exec -p \"$SB\" codex plugin add review-kit@review-kit --json </dev/null >/dev/null 2>&1; sandbox-exec -p \"$SB\" codex debug prompt-input </dev/null 2>/dev/null | grep -o -E '\\- review-kit:review: .{0,80}'; sandbox-exec -p \"$SB\" codex debug prompt-input </dev/null 2>/dev/null | grep -c -E 'reviewer|source-command'", "description": "Load-check final tree via stand-in in Claude and Codex"}}
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
index 0000000..49ad8ba
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
+      "description": "Code review helpers: a review skill (all tools) and a reviewer agent (Claude Code only). Executable components: a local MCP server (server/run.sh, which runs python3 -m review_server) that calls an external review service with your API key, and a SessionStart hook (scripts/start.sh) in Claude Code.",
+      "policy": {
+        "installation": "AVAILABLE",
+        "authentication": "ON_INSTALL"
+      },
+      "category": "Coding"
+    }
+  ]
+}
diff --git a/.claude-plugin/marketplace.json b/.claude-plugin/marketplace.json
index a015458..b8578d5 100644
--- a/.claude-plugin/marketplace.json
+++ b/.claude-plugin/marketplace.json
@@ -7,7 +7,8 @@
   "plugins": [
     {
       "name": "review-kit",
-      "source": "./"
+      "source": "./",
+      "description": "Code review helpers: a review skill (all tools) and a reviewer agent (Claude Code only). Executable components: a local MCP server (server/run.sh, which runs python3 -m review_server) that calls an external review service with your API key, and a SessionStart hook (scripts/start.sh) in Claude Code."
     }
   ]
 }
diff --git a/README.md b/README.md
index 9246da6..d443ac7 100644
--- a/README.md
+++ b/README.md
@@ -1,3 +1,29 @@
 # review-kit
 
-Code review helpers for Claude Code.
+Code review helpers for Claude Code, Codex, and GitHub Copilot CLI.
+
+## Install
+
+| Tool | Commands |
+| --- | --- |
+| Claude Code | `claude plugin marketplace add <repo>` then `claude plugin install review-kit@review-kit` |
+| Codex | `codex plugin marketplace add <repo>` then `codex plugin add review-kit@review-kit` |
+| Copilot CLI | `copilot plugin marketplace add <repo>` then `copilot plugin install review-kit@review-kit` |
+
+## What each tool gets
+
+| Component | Claude Code | Codex | Copilot CLI |
+| --- | --- | --- | --- |
+| `review` skill (`skills/review`) | yes, user-invoked | yes | yes |
+| `reviewer` agent (`agents/`) | yes | no | no |
+| SessionStart hook (`hooks/`) | yes | no | no |
+| `review` MCP server (`server/run.sh`) | yes, with the API key from the install prompt | configured, but receives no API key | configured; API key delivery unverified |
+
+The API key is a Claude Code `userConfig` option; Codex and Copilot CLI have no equivalent.
+
+## Layout
+
+- Claude Code reads `.claude-plugin/plugin.json`, `.mcp.json`, and `.claude-plugin/marketplace.json`.
+- Codex reads the portable `plugin.json` and `mcp.json`, and the catalog `.agents/plugins/marketplace.json`.
+- Copilot CLI reads the portable `plugin.json` and `mcp.json`, and the catalog `.claude-plugin/marketplace.json`.
+- Keep `name` and `version` equal in both manifests, and the same servers in both MCP files.
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
similarity index 66%
rename from commands/review.md
rename to skills/review/SKILL.md
index 8fc96bb..93f9ad4 100644
--- a/commands/review.md
+++ b/skills/review/SKILL.md
@@ -1,5 +1,7 @@
 ---
+name: review
 description: Review the current diff
+disable-model-invocation: true
 ---
 
 Review the staged diff and list problems.
```

## Repository refs

Every branch and tag in the final repository, each with its changes against the fixture tree (`refs.txt`).

```text
master 17d0334
```
