# Run: scenario 4, repetition 4, with-skill

Scored against `tests/scenarios.md` as of this commit; cost is `metrics` in the manifest.

## Manifest

```json
{
  "date": "2026-09-28",
  "arm": "with-skill",
  "scenario": "s4",
  "rep": 4,
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
  "transcript": "ad632978b5464d48a.output",
  "model": "claude-opus-5-5",
  "metrics": {
    "tool_calls": 23,
    "wall_seconds": 276.8
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
| --- | --- | --- |
| 1 | pass | objective.json shows `claude.errors: []` (success true), and `.claude-plugin/plugin.json` is byte-identical to the fixture original (no diff in diff.patch, and `diff` against the fixture shows no difference). |
| 2 | pass | objective.json shows `codex.listed: ["review-kit"]` and `copilot.listed: ["review-kit"]`. |
| 3 | pass | report.md table: the Codex column reads "no" for the `reviewer` agent and "no" for the "API key prompt (`userConfig`)" row. |
| 4 | pass | report.md says Codex stopped loading `commands/` under the new manifest, "so this skill [`review-diff`] is how they get the review action". The command reaches Codex as a skill the agent converted, and the report does not call it unsupported. |
| 5 | pass | report.md has a "Checks" table and a "Not run" list (no remote repo, no model session, MCP server never started, `codex debug prompt-input` not run). Unobserved behaviour is labelled "not verified" (Codex exposing the skill to the model, Copilot agent and hook, API key passthrough). |

Total: 5 of 5 passed.

## Final report

## review-kit now installs in Codex and Copilot CLI, and Claude Code still loads everything it did before

The Claude Code files are unchanged, and no files were deleted. I committed nothing, and the working tree has the changes. All three installed tools match the versions the skill's references were checked against (claude 2.1.284, codex-cli 0.157.1, copilot 1.0.89).

**What I changed** (repo root `$RUN/repo`):
- **New `plugin.json`:** the portable manifest that Codex and Copilot CLI read. It uses the same name and version (`2.0.0`) as `.claude-plugin/plugin.json`.
- **New `mcp.json`:** declares the `review` server as `"type": "stdio"` with `"command": "./server/run.sh"`. It doesn't use `${CLAUDE_PLUGIN_ROOT}`, which the other two tools don't expand.
- **New `skills/review-diff/SKILL.md`:** a copy of the `/review` command written as a skill. Both Codex and Copilot CLI stopped loading `commands/` once the plugin had the new manifest (details below), so this skill is how they get the review action.
- **New `marketplace-policy.json`:** says all three tools read the one existing catalog. That works because its only entry is `"./"`, a source type all three accept.
- **Edited `.claude-plugin/marketplace.json`:** the entry's description now says the plugin runs an MCP server, calls an external review service and has a SessionStart hook.
- **Rewrote `README.md`:** install commands for each tool and the table below.

## What works in each tool

| Component | Claude Code | Codex | Copilot CLI |
| --- | --- | --- | --- |
| `/review` command | yes | no | no |
| `review-diff` skill | yes (new, see below) | the files are installed; that Codex shows it to the model is not verified | yes, listed |
| `reviewer` agent | yes | no | not verified |
| SessionStart hook | yes | no | not verified |
| `review` MCP server | yes, unchanged | yes, path now works | yes, path now works |
| API key prompt (`userConfig`) | yes | no | no |

- **The command:** before my change, Codex turned `/review` into a skill (`source-command-review`) and Copilot listed it as a skill. Once the plugin had the portable manifest, neither did either of those, which is why I added `review-diff`.
- **The MCP server path:** before, both Codex and Copilot were set up with the literal command `${CLAUDE_PLUGIN_ROOT}/server/run.sh`. After, it points at the real `server/run.sh` in each tool.
- **The API key:** in Codex and Copilot CLI nothing asks for the key, and the plugin gives the server no `REVIEW_API_KEY`. I haven't verified whether a key exported in the user's shell reaches the server, so the MCP server may not be usable in those two tools yet.
- **Codex hooks:** Codex could run the hook through `extensions["com.openai"].hooks` in `plugin.json`. I didn't add it because I couldn't verify the format Codex expects.
- **Unchecked in Copilot:** no command shows whether Copilot CLI loaded the agent or the hook, so those stay unverified.

**Decision for you:** Claude Code users now see one extra skill, `review-diff`, next to `/review`. Leaving it out of `skills/` isn't possible because Claude Code always loads `skills/`. The alternative is to drop the skill, and then Codex and Copilot users get only the MCP server. I also tried naming the skill `review`, but Claude Code then listed two entries both called `review`.

**Existing problem, not caused by this change:** `server/run.sh` runs `python3 -m review_server`, and there's no `review_server` module in this repo. So the server won't start in any tool unless that module comes from somewhere else.

## Checks

| Check | Result |
| --- | --- |
| Validator format checks, including the new portable files | passed |
| Validator repo rules (paths, names, versions) | passed, 0 errors |
| Validator's own `claude plugin validate` of the plugin files | inconclusive: it can't run on a folder that is also a catalog. I ran it myself on a copy without the catalog: 0 errors, 0 warnings |
| `claude plugin validate --strict` on the catalog | 0 errors, 0 warnings |
| Validator can catch problems | yes: on a deliberately broken copy it reported errors |

**Checked in each tool:** I ran every tool on a clean copy of the committed files plus my changes, with throwaway settings folders and outbound network blocked.
- **Claude Code:** it added the catalog, and `claude plugin details` listed the same components before and after, plus `review-diff`. I ran `details` with `--plugin-dir`. I didn't run `claude plugin install`, because the key setting is marked secret and would have touched the real system keychain.
- **Codex:** it added the catalog and listed `review-kit` at version 2.0.0. Installing gave version 2.0.0, and `codex mcp list` showed the real path to `server/run.sh`.
- **Copilot CLI:** it added and listed the catalog. Install said "Installed 1 skill", the plugin shows as 2.0.0 and enabled, `copilot skill list` shows `review-diff`, and `copilot mcp get review` shows the real path.

**Not run:**
- Checks against a published remote repository: there isn't one, and I did no network access.
- Any model session in any tool, so I never ran the plugin's code and never started the MCP server.
- `codex debug prompt-input`, which would show whether Codex presents `review-diff` to the model: it starts plugin MCP servers.

Scratch files are in `.tool-homes/`, which I added to `.git/info/exclude`.

## Tool calls

The arm's tool calls, one JSON object per line, extracted from its transcript.

```jsonl
{"tool": "Bash", "input": {"command": "cd $RUN/repo && git status && git log --oneline | head && find . -path ./.git -prune -o -type f -print | head -100; cat $RUN/skill/plugin-marketplaces/SKILL.md; ls -R $RUN/skill/plugin-marketplaces"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && for f in $(git ls-files); do echo \"=== $f\"; cat \"$f\"; done; ls -la"}}
{"tool": "Bash", "input": {"command": "cd $RUN/skill/plugin-marketplaces/references && cat multi-tool.md feature-matrix.md"}}
{"tool": "Bash", "input": {"command": "cd $RUN/skill/plugin-marketplaces/references && cat agent-plugins.md validation.md releases.md"}}
{"tool": "Bash", "input": {"command": "cd $RUN/skill/plugin-marketplaces/references && cat codex.md copilot-cli.md"}}
{"tool": "Bash", "input": {"command": "cd $RUN/skill/plugin-marketplaces && cat references/claude-code.md; cat scripts/mpcheck/policy.py | head -150; cat scripts/mpcheck/data/schemas/agent-plugins/1.0.0/*.json"}}
{"tool": "Bash", "input": {"command": "cd $RUN/skill/plugin-marketplaces/scripts/mpcheck && sed -n 150,260p policy.py; cat data/readers.json; which claude codex copilot git python3"}}
{"tool": "Bash", "input": {"command": "R=$RUN/repo; T=\"$R/.tool-homes\"; mkdir -p \"$T\"/{home,xdg,tmp,claude,codex,copilot,copilot-cache} && : > \"$T/gitconfig\" && echo \".tool-homes/\" >> \"$R/.git/info/exclude\"\nexport HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\"\n$RUN/validator/bin/check-marketplace \"$R\" </dev/null; echo exit=$?\nclaude --version </dev/null; codex --version </dev/null; copilot --version </dev/null"}}
{"tool": "Bash", "input": {"command": "R=$RUN/repo; T=\"$R/.tool-homes\"\nexport HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\"\nSB='(version 1)(allow default)(deny network-outbound (remote ip))'\nmkdir -p \"$T/before\" && git -C \"$R\" archive HEAD | tar -x -C \"$T/before\"\ncd \"$T\" || exit 1\necho \"--- codex before\"; sandbox-exec -p \"$SB\" codex plugin marketplace add \"$T/before\" </dev/null 2>&1 | tail -5\nsandbox-exec -p \"$SB\" codex plugin list --available --json </dev/null 2>&1 | head -40\nsandbox-exec -p \"$SB\" codex plugin add review-kit@review-kit --json </dev/null 2>&1 | tail -20\nfind \"$T/codex/plugins\" -maxdepth 6 2>/dev/null | head -40\nsandbox-exec -p \"$SB\" codex mcp list --json </dev/null 2>&1 | head -40"}}
{"tool": "Bash", "input": {"command": "T=$RUN/repo/.tool-homes; find \"$T/codex/plugins/cache/review-kit/review-kit/2.0.0/.codex-plugin\" -type f -exec sh -c 'echo \"== $1\"; cat \"$1\"' _ {} \\;"}}
{"tool": "Bash", "input": {"command": "R=$RUN/repo; T=\"$R/.tool-homes\"\nexport HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\"\nSB='(version 1)(allow default)(deny network-outbound (remote ip))'\ncd \"$T\" || exit 1\nsandbox-exec -p \"$SB\" copilot plugin marketplace add \"$T/before\" </dev/null 2>&1 | tail -5\nsandbox-exec -p \"$SB\" copilot plugin marketplace browse review-kit --json </dev/null 2>&1 | head -30\nsandbox-exec -p \"$SB\" copilot plugin install review-kit@review-kit </dev/null 2>&1 | tail -5\nsandbox-exec -p \"$SB\" copilot plugin list </dev/null 2>&1 | tail -8\nsandbox-exec -p \"$SB\" copilot skill list </dev/null 2>&1 | tail -15\nsandbox-exec -p \"$SB\" copilot mcp list </dev/null 2>&1 | tail -10\nsandbox-exec -p \"$SB\" copilot mcp get review </dev/null 2>&1 | tail -20"}}
{"tool": "Bash", "input": {"command": "R=$RUN/repo; cd \"$R\" || exit 1\ncat > plugin.json <<'EOF'\n{\n  \"$schema\": \"https://agent-plugins.org/schemas/1.0.0/plugin.schema.json\",\n  \"name\": \"review-kit\",\n  \"version\": \"2.0.0\",\n  \"description\": \"Code review helpers\",\n  \"author\": {\n    \"name\": \"Acme\"\n  }\n}\nEOF\ncat > mcp.json <<'EOF'\n{\n  \"$schema\": \"https://agent-plugins.org/schemas/1.0.0/mcp.schema.json\",\n  \"mcpServers\": {\n    \"review\": {\n      \"type\": \"stdio\",\n      \"command\": \"./server/run.sh\"\n    }\n  }\n}\nEOF\ncat > marketplace-policy.json <<'EOF'\n{\n  \"$comment\": \"One shared catalog, .claude-plugin/marketplace.json, read by all three tools: its only entry is a relative path, a source every reader accepts (R2). Add a native catalog per tool family before adding any source type one of them rejects.\",\n  \"readers\": [\"claude-code\", \"codex\", \"copilot-cli\"]\n}\nEOF\ncat > .claude-plugin/marketplace.json <<'EOF'\n{\n  \"name\": \"review-kit\",\n  \"owner\": {\n    \"name\": \"Acme\"\n  },\n  \"description\": \"review-kit\",\n  \"plugins\": [\n    {\n      \"name\": \"review-kit\",\n      \"description\": \"Code review helpers. Runs a local MCP server (server/run.sh) that talks to an external review service using your API key, and, in Claude Code, a SessionStart hook (scripts/start.sh).\",\n      \"source\": \"./\"\n    }\n  ]\n}\nEOF\nT=\"$R/.tool-homes\"; export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\"\n$RUN/validator/bin/check-marketplace \"$R\" </dev/null; echo exit=$?"}}
{"tool": "Bash", "input": {"command": "R=$RUN/repo; T=\"$R/.tool-homes\"; cd \"$R\" || exit 1\nexport HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\"\nrm -rf \"$T/after\" \"$T/neg\"; mkdir -p \"$T/after\" \"$T/neg\"\nGIT_INDEX_FILE=\"$T/idx\" git read-tree HEAD && GIT_INDEX_FILE=\"$T/idx\" git add -A && TREE=$(GIT_INDEX_FILE=\"$T/idx\" git write-tree) && git archive \"$TREE\" | tar -x -C \"$T/after\"\nls -A \"$T/after\"\ncp -R \"$T/after/.\" \"$T/neg/\"; python3 - \"$T/neg\" <<'EOF'\nimport json,sys,pathlib\np=pathlib.Path(sys.argv[1])\nm=json.loads((p/\"mcp.json\").read_text()); del m[\"mcpServers\"][\"review\"][\"type\"]; (p/\"mcp.json\").write_text(json.dumps(m))\ne=json.loads((p/\".claude-plugin/marketplace.json\").read_text()); e[\"plugins\"].append({\"name\":\"x\",\"source\":{\"source\":\"github\",\"repo\":\"a/b\"}}); (p/\".claude-plugin/marketplace.json\").write_text(json.dumps(e))\nEOF\n$RUN/validator/bin/check-marketplace \"$T/neg\" </dev/null | grep -E 'ERROR|WARN|failed'; echo neg-exit=$?"}}
{"tool": "Bash", "input": {"command": "R=$RUN/repo; T=\"$R/.tool-homes\"; mkdir -p \"$T/claude-b\" \"$T/claude-a\"\nexport HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\"\nSB='(version 1)(allow default)(deny network-outbound (remote ip))'\ncd \"$T\" || exit 1\nfor s in b:before a:after; do k=${s%%:*}; d=${s#*:}; echo \"===== $d\"\n export CLAUDE_CONFIG_DIR=\"$T/claude-$k\"\n sandbox-exec -p \"$SB\" claude plugin validate \"$T/$d\" --strict --json </dev/null 2>&1 | head -30\n sandbox-exec -p \"$SB\" claude plugin marketplace add \"$T/$d\" </dev/null 2>&1 | tail -3\n sandbox-exec -p \"$SB\" claude plugin details review-kit@review-kit </dev/null 2>&1 | head -40\ndone"}}
{"tool": "Bash", "input": {"command": "R=$RUN/repo; T=\"$R/.tool-homes\"\nexport HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude-a\"\nSB='(version 1)(allow default)(deny network-outbound (remote ip))'\ncd \"$T\" || exit 1\nsandbox-exec -p \"$SB\" claude plugin details --help </dev/null 2>&1 | head -30"}}
{"tool": "Bash", "input": {"command": "R=$RUN/repo; T=\"$R/.tool-homes\"\nexport HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1\nSB='(version 1)(allow default)(deny network-outbound (remote ip))'\ncd \"$T\" || exit 1\nfor d in before after; do echo \"===== $d\"; export CLAUDE_CONFIG_DIR=\"$T/claude-${d:0:1}\"\n sandbox-exec -p \"$SB\" claude --plugin-dir \"$T/$d\" plugin details review-kit </dev/null 2>&1 | head -40\ndone"}}
{"tool": "Bash", "input": {"command": "R=$RUN/repo; T=\"$R/.tool-homes\"; mkdir -p \"$T/codex-a\" \"$T/copilot-a\" \"$T/copilot-cache-a\"\nexport HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude-a\" CODEX_HOME=\"$T/codex-a\" COPILOT_HOME=\"$T/copilot-a\" COPILOT_CACHE_HOME=\"$T/copilot-cache-a\"\nSB='(version 1)(allow default)(deny network-outbound (remote ip))'\ncd \"$T\" || exit 1\necho \"--- codex after\"; sandbox-exec -p \"$SB\" codex plugin marketplace add \"$T/after\" </dev/null 2>&1 | tail -2\nsandbox-exec -p \"$SB\" codex plugin list --available --json </dev/null 2>&1 | grep -E '\"(name|version|pluginId)\"'\nsandbox-exec -p \"$SB\" codex plugin add review-kit@review-kit --json </dev/null 2>&1 | tail -8\nC=\"$T/codex-a/plugins/cache/review-kit/review-kit\"; ls \"$C\"; find \"$C\" -path '*/.codex-plugin*'\nsandbox-exec -p \"$SB\" codex mcp list --json </dev/null 2>&1\necho \"--- copilot after\"\nsandbox-exec -p \"$SB\" copilot plugin marketplace add \"$T/after\" </dev/null 2>&1 | tail -2\nsandbox-exec -p \"$SB\" copilot plugin marketplace browse review-kit --json </dev/null 2>&1\nsandbox-exec -p \"$SB\" copilot plugin install review-kit@review-kit </dev/null 2>&1 | tail -3\nsandbox-exec -p \"$SB\" copilot plugin list </dev/null 2>&1 | tail -4\nsandbox-exec -p \"$SB\" copilot skill list </dev/null 2>&1 | sed -n '1,4p'\nsandbox-exec -p \"$SB\" copilot mcp list </dev/null 2>&1 | sed -n '1,3p'\nsandbox-exec -p \"$SB\" copilot mcp get review </dev/null 2>&1"}}
{"tool": "Bash", "input": {"command": "R=$RUN/repo; T=\"$R/.tool-homes\"\nexport HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude-a\"\nSB='(version 1)(allow default)(deny network-outbound (remote ip))'\nfor n in review review-diff; do rm -rf \"$T/t-$n\"; cp -R \"$T/after\" \"$T/t-$n\"; mkdir -p \"$T/t-$n/skills/$n\"; printf -- '---\\nname: %s\\ndescription: Review the current diff\\n---\\n\\nReview the staged diff and list problems.\\n' $n > \"$T/t-$n/skills/$n/SKILL.md\"\necho \"== $n\"; (cd \"$T\" && sandbox-exec -p \"$SB\" claude --plugin-dir \"$T/t-$n\" plugin details review-kit </dev/null 2>&1 | sed -n '5,10p'); done"}}
{"tool": "Bash", "input": {"command": "R=$RUN/repo; cd \"$R\" || exit 1; mkdir -p skills/review-diff\ncat > skills/review-diff/SKILL.md <<'EOF'\n---\nname: review-diff\ndescription: Review the current diff\n---\n\nReview the staged diff and list problems.\nEOF\ncat > README.md <<'EOF'\n# review-kit\n\nCode review helpers for Claude Code, Codex, and GitHub Copilot CLI.\n\n## Install\n\nAdd this repository as a marketplace, then install `review-kit` from it:\n\n| Tool | Commands |\n| --- | --- |\n| Claude Code | `claude plugin marketplace add <owner/repo>` then `claude plugin install review-kit@review-kit` |\n| Codex | `codex plugin marketplace add <owner/repo>` then `codex plugin add review-kit@review-kit` |\n| GitHub Copilot CLI | `copilot plugin marketplace add <owner/repo>` then `copilot plugin install review-kit@review-kit` |\n\n## What each tool gets\n\n| Component | Claude Code | Codex | Copilot CLI |\n| --- | --- | --- | --- |\n| `/review` command (`commands/review.md`) | yes | no | no |\n| `review-diff` skill (`skills/review-diff/`) | yes | yes | yes |\n| `reviewer` agent (`agents/reviewer.md`) | yes | no | not verified |\n| SessionStart hook (`scripts/start.sh`) | yes | no | not verified |\n| `review` MCP server (`server/run.sh`) | yes | yes | yes |\n| API key prompt (`userConfig.api_key`) | yes | no | no |\n\nCodex and Copilot CLI read the portable manifest (`plugin.json`, `mcp.json`); Claude Code reads `.claude-plugin/plugin.json` and `.mcp.json`.\nKeep the two manifests' `name` and `version` equal, and the two MCP files' servers in step.\n\nCodex and Copilot CLI have no equivalent of Claude Code's `userConfig`, so they do not ask for the review service's API key or pass it to the MCP server as `REVIEW_API_KEY`.\nEOF\nT=\"$R/.tool-homes\"; export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude-a\"\n$RUN/validator/bin/check-marketplace \"$R\" </dev/null; echo exit=$?"}}
{"tool": "Bash", "input": {"command": "R=$RUN/repo; T=\"$R/.tool-homes\"; cd \"$R\" || exit 1\npython3 - \"$R/README.md\" <<'EOF'\nimport sys,pathlib\np=pathlib.Path(sys.argv[1]); s=p.read_text()\ns=s.replace(\"Codex and Copilot CLI have no equivalent of Claude Code's `userConfig`, so they do not ask for the review service's API key or pass it to the MCP server as `REVIEW_API_KEY`.\\n\",\n\"Codex and Copilot CLI have no equivalent of Claude Code's `userConfig`: they do not ask for the review service's API key, and the plugin sets no `REVIEW_API_KEY` for the MCP server there.\\nWhether a `REVIEW_API_KEY` exported in your shell reaches the server in those tools has not been verified.\\n\")\np.write_text(s)\nEOF\nrm -rf \"$T/final\" \"$T/final-plugin\"; mkdir -p \"$T/final\"; rm -f \"$T/idx\"\nGIT_INDEX_FILE=\"$T/idx\" git read-tree HEAD && GIT_INDEX_FILE=\"$T/idx\" git add -A && TREE=$(GIT_INDEX_FILE=\"$T/idx\" git write-tree) && git archive \"$TREE\" | tar -x -C \"$T/final\"\ncp -R \"$T/final\" \"$T/final-plugin\"; rm \"$T/final-plugin/.claude-plugin/marketplace.json\"\nfor x in claude-f codex-f copilot-f copilot-cache-f; do rm -rf \"$T/$x\"; mkdir -p \"$T/$x\"; done\nexport HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude-f\" CODEX_HOME=\"$T/codex-f\" COPILOT_HOME=\"$T/copilot-f\" COPILOT_CACHE_HOME=\"$T/copilot-cache-f\"\nSB='(version 1)(allow default)(deny network-outbound (remote ip))'\ncd \"$T\" || exit 1\necho \"### claude\"; sandbox-exec -p \"$SB\" claude plugin validate \"$T/final\" --strict --json </dev/null 2>&1 | grep -E '\"(success|errors|warnings)\"'\nsandbox-exec -p \"$SB\" claude plugin validate \"$T/final-plugin\" --strict --json </dev/null 2>&1 | head -40\nsandbox-exec -p \"$SB\" claude plugin marketplace add \"$T/final\" </dev/null 2>&1 | tail -1\nsandbox-exec -p \"$SB\" claude --plugin-dir \"$T/final\" plugin details review-kit </dev/null 2>&1 | sed -n '1,10p'\necho \"### codex\"; sandbox-exec -p \"$SB\" codex plugin marketplace add \"$T/final\" </dev/null 2>&1 | tail -1\nsandbox-exec -p \"$SB\" codex plugin list --available --json </dev/null 2>&1 | grep -E '\"(pluginId|version)\"'\nsandbox-exec -p \"$SB\" codex plugin add review-kit@review-kit --json </dev/null 2>&1 | grep -E 'version|error'\nC=\"$T/codex-f/plugins/cache/review-kit/review-kit/2.0.0\"; find \"$C/skills\" \"$C/.codex-plugin\" 2>&1\nsandbox-exec -p \"$SB\" codex mcp list --json </dev/null 2>&1 | grep -E '\"(name|command|cwd)\"|REVIEW'\necho \"### copilot\"; sandbox-exec -p \"$SB\" copilot plugin marketplace add \"$T/final\" </dev/null 2>&1 | tail -1\nsandbox-exec -p \"$SB\" copilot plugin marketplace browse review-kit --json </dev/null 2>&1 | grep name\nsandbox-exec -p \"$SB\" copilot plugin install review-kit@review-kit </dev/null 2>&1 | head -2\nsandbox-exec -p \"$SB\" copilot plugin list </dev/null 2>&1 | grep review-kit\nsandbox-exec -p \"$SB\" copilot skill list </dev/null 2>&1 | sed -n '1,3p'\nsandbox-exec -p \"$SB\" copilot mcp get review </dev/null 2>&1 | grep -E 'Command|REVIEW|Source plugin'"}}
{"tool": "Bash", "input": {"command": "R=$RUN/repo; T=\"$R/.tool-homes\"; cd \"$R\" || exit 1\npython3 - \"$R/README.md\" <<'EOF'\nimport sys,pathlib\np=pathlib.Path(sys.argv[1]); s=p.read_text()\ns=s.replace(\"Codex and Copilot CLI have no equivalent of Claude Code's `userConfig`, so they do not ask for the review service's API key or pass it to the MCP server as `REVIEW_API_KEY`.\\n\",\n\"Codex and Copilot CLI have no equivalent of Claude Code's `userConfig`: they do not ask for the review service's API key, and the plugin sets no `REVIEW_API_KEY` for the MCP server there.\\nWhether a `REVIEW_API_KEY` exported in your shell reaches the server in those tools has not been verified.\\n\")\np.write_text(s)\nEOF\ngrep -n verified README.md\nmkdir \"$T/final\" \"$T/claude-f\" \"$T/codex-f\" \"$T/copilot-f\" \"$T/copilot-cache-f\" || exit 1\nGIT_INDEX_FILE=\"$T/idx2\" git read-tree HEAD && GIT_INDEX_FILE=\"$T/idx2\" git add -A && TREE=$(GIT_INDEX_FILE=\"$T/idx2\" git write-tree) && git archive \"$TREE\" | tar -x -C \"$T/final\"\ncp -R \"$T/final\" \"$T/final-plugin\" && mv \"$T/final-plugin/.claude-plugin/marketplace.json\" \"$T/final-plugin-removed-marketplace.json\"\nls -A \"$T/final\" \"$T/final-plugin/.claude-plugin\""}}
{"tool": "Bash", "input": {"command": "R=$RUN/repo; T=\"$R/.tool-homes\"\nexport HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude-f\" CODEX_HOME=\"$T/codex-f\" COPILOT_HOME=\"$T/copilot-f\" COPILOT_CACHE_HOME=\"$T/copilot-cache-f\"\nSB='(version 1)(allow default)(deny network-outbound (remote ip))'\ncd \"$T\" || exit 1\necho \"### claude\"; sandbox-exec -p \"$SB\" claude plugin validate \"$T/final\" --strict --json </dev/null 2>&1 | grep -E '\"(success|errors|warnings)\"'\nsandbox-exec -p \"$SB\" claude plugin validate \"$T/final-plugin\" --strict --json </dev/null 2>&1 | grep -vE '\"(file|target)\"' | head -40; echo \"plugin-validate exit=${PIPESTATUS[0]}\"\nsandbox-exec -p \"$SB\" claude plugin marketplace add \"$T/final\" </dev/null 2>&1 | tail -1\nsandbox-exec -p \"$SB\" claude --plugin-dir \"$T/final\" plugin details review-kit </dev/null 2>&1 | sed -n '1,10p'\necho \"### codex\"; sandbox-exec -p \"$SB\" codex plugin marketplace add \"$T/final\" </dev/null 2>&1 | tail -1\nsandbox-exec -p \"$SB\" codex plugin list --available --json </dev/null 2>&1 | grep -E '\"(pluginId|version)\"'\nsandbox-exec -p \"$SB\" codex plugin add review-kit@review-kit --json </dev/null 2>&1 | grep -E 'version|error'\nC=\"$T/codex-f/plugins/cache/review-kit/review-kit/2.0.0\"; find \"$C/skills\" \"$C/.codex-plugin\" 2>&1\nsandbox-exec -p \"$SB\" codex mcp list --json </dev/null 2>&1 | grep -E '\"(name|command|cwd)\"|REVIEW'\necho \"### copilot\"; sandbox-exec -p \"$SB\" copilot plugin marketplace add \"$T/final\" </dev/null 2>&1 | tail -1\nsandbox-exec -p \"$SB\" copilot plugin marketplace browse review-kit --json </dev/null 2>&1 | grep '\"name\"'\nsandbox-exec -p \"$SB\" copilot plugin install review-kit@review-kit </dev/null 2>&1 | head -2\nsandbox-exec -p \"$SB\" copilot plugin list </dev/null 2>&1 | grep review-kit\nsandbox-exec -p \"$SB\" copilot skill list </dev/null 2>&1 | sed -n '1,3p'\nsandbox-exec -p \"$SB\" copilot mcp get review </dev/null 2>&1 | grep -E 'Command|REVIEW|Source plugin'"}}
{"tool": "Bash", "input": {"command": "R=$RUN/repo; T=\"$R/.tool-homes\"; export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude-f\"\n$RUN/validator/bin/check-marketplace \"$R\" </dev/null | head -9; echo exit=$?; git -C \"$R\" status --short"}}
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
index a015458..484d813 100644
--- a/.claude-plugin/marketplace.json
+++ b/.claude-plugin/marketplace.json
@@ -7,6 +7,7 @@
   "plugins": [
     {
       "name": "review-kit",
+      "description": "Code review helpers. Runs a local MCP server (server/run.sh) that talks to an external review service using your API key, and, in Claude Code, a SessionStart hook (scripts/start.sh).",
       "source": "./"
     }
   ]
diff --git a/README.md b/README.md
index 9246da6..3e8b9bd 100644
--- a/README.md
+++ b/README.md
@@ -1,3 +1,30 @@
 # review-kit
 
-Code review helpers for Claude Code.
+Code review helpers for Claude Code, Codex, and GitHub Copilot CLI.
+
+## Install
+
+Add this repository as a marketplace, then install `review-kit` from it:
+
+| Tool | Commands |
+| --- | --- |
+| Claude Code | `claude plugin marketplace add <owner/repo>` then `claude plugin install review-kit@review-kit` |
+| Codex | `codex plugin marketplace add <owner/repo>` then `codex plugin add review-kit@review-kit` |
+| GitHub Copilot CLI | `copilot plugin marketplace add <owner/repo>` then `copilot plugin install review-kit@review-kit` |
+
+## What each tool gets
+
+| Component | Claude Code | Codex | Copilot CLI |
+| --- | --- | --- | --- |
+| `/review` command (`commands/review.md`) | yes | no | no |
+| `review-diff` skill (`skills/review-diff/`) | yes | yes | yes |
+| `reviewer` agent (`agents/reviewer.md`) | yes | no | not verified |
+| SessionStart hook (`scripts/start.sh`) | yes | no | not verified |
+| `review` MCP server (`server/run.sh`) | yes | yes | yes |
+| API key prompt (`userConfig.api_key`) | yes | no | no |
+
+Codex and Copilot CLI read the portable manifest (`plugin.json`, `mcp.json`); Claude Code reads `.claude-plugin/plugin.json` and `.mcp.json`.
+Keep the two manifests' `name` and `version` equal, and the two MCP files' servers in step.
+
+Codex and Copilot CLI have no equivalent of Claude Code's `userConfig`: they do not ask for the review service's API key, and the plugin sets no `REVIEW_API_KEY` for the MCP server there.
+Whether a `REVIEW_API_KEY` exported in your shell reaches the server in those tools has not been verified.
diff --git a/marketplace-policy.json b/marketplace-policy.json
new file mode 100644
index 0000000..9bdbf26
--- /dev/null
+++ b/marketplace-policy.json
@@ -0,0 +1,4 @@
+{
+  "$comment": "One shared catalog, .claude-plugin/marketplace.json, read by all three tools: its only entry is a relative path, a source every reader accepts (R2). Add a native catalog per tool family before adding any source type one of them rejects.",
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
diff --git a/skills/review-diff/SKILL.md b/skills/review-diff/SKILL.md
new file mode 100644
index 0000000..b6b4fcb
--- /dev/null
+++ b/skills/review-diff/SKILL.md
@@ -0,0 +1,6 @@
+---
+name: review-diff
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
