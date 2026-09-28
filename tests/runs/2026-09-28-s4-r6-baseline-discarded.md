# Run: scenario 4, repetition 6, baseline (DISCARDED, not scored)

Scored against `tests/scenarios.md` as of this commit; cost is `metrics` in the manifest.

## Manifest

```json
{
  "date": "2026-09-28",
  "arm": "baseline",
  "scenario": "s4",
  "rep": 6,
  "fixture_tree": "5636a130e9dfed2c78f60f0a2718f62fef2c7d5c",
  "upstream_commits": null,
  "tools": {
    "claude": "2.1.284 (Claude Code)",
    "codex": "codex-cli 0.157.1",
    "copilot": "GitHub Copilot CLI 1.0.88."
  },
  "session_context": "dispatched from a Claude Code session (claude 2.1.284) with installed plugins including superpowers, plugin-dev, amicus, astral, obsidian, pr-review-toolkit, code-review, skill-creator, mcp-server-dev, claude-code-setup; user skills include agent-bot-identity, review-pr, fastmcp, prek; the plugin-marketplaces skill is not installed anywhere",
  "prompt_file": "prompt.txt",
  "transcript": "a862750e9609b78cd.output",
  "model": "claude-opus-5-5",
  "metrics": {
    "tool_calls": 61,
    "wall_seconds": 605.5
  },
  "start_cwd": "~/projects/skills"
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

Make review-kit available to Codex and GitHub Copilot CLI users too, without breaking it for Claude Code users.
Tell me what will and won't work in each tool.
```

## Isolation

Flags raised by `tests/eval/isolation.py` (tests/scenarios.md, How to run, step 5):

```text
#3 sourced-unknown: $C
#3 sourced-unknown: $P
#4 cli-prompt: codex \$@ /dev/null
#4 cli-prompt: copilot \$@ /dev/null
#4 cli-env: copilot without COPILOT_CACHE_HOME inside WORKDIR
#11 cli-prompt: copilot \$@ /dev/null
#11 cli-env: copilot without COPILOT_CACHE_HOME inside WORKDIR
#12 cli-prompt: copilot \$@ /dev/null
#12 cli-env: copilot without COPILOT_CACHE_HOME inside WORKDIR
#13 cli-prompt: copilot \$@ /dev/null
#13 cli-env: copilot without COPILOT_CACHE_HOME inside WORKDIR
#14 cli-prompt: copilot \$@ /dev/null
#14 cli-env: copilot without COPILOT_CACHE_HOME inside WORKDIR
#15 cli-prompt: copilot \$@ /dev/null
#15 cli-env: copilot without COPILOT_CACHE_HOME inside WORKDIR
#20 cli-prompt: codex \$@ /dev/null
#21 cli-prompt: codex \$@ /dev/null
#22 cli-prompt: codex \$@ /dev/null
#22 cli-env: codex without CODEX_HOME inside WORKDIR
#23 cli-prompt: codex \$@ /dev/null
#29 cli-prompt: codex \$@ /dev/null
#29 cli-env: codex without CODEX_HOME inside WORKDIR
#40 cli-prompt: codex \$@ /dev/null
#48 cli-prompt: claude \$@ /dev/null
```

DISCARDED after a full-call adjudication (an adjudication subagent read every call in full; the executor verified the cited call): #29 runs `codex app-server generate-ts` through the arm's ./cx wrapper, a subcommand outside the literal step-5 allowlist (only `app-server generate-json-schema` is listed), although it generates TypeScript types locally. Its other calls broke no rule: the missing COPILOT_CACHE_HOME wrote no real Copilot cache, and its bare `codex app-server` starts (#31 onward) send only `initialize`, `initialized`, `skills/list`, `hooks/list`, `plugin/read`, and `mcpServerStatus/list`. Not scored.

## Score

Not scored: this run was discarded (see Isolation). It is kept so any observation drawn from it can be audited; it is not evidence for the arm's score.

## Final report

review-kit now installs from the same repo in Claude Code, Codex CLI and Copilot CLI, and nothing changed for Claude Code users in the checks I ran. The changes are staged in `$RUN/repo` but not committed.

I tested with the real CLIs (Claude Code 2.1.284, Codex 0.157.1, Copilot CLI 1.0.86), each with throwaway config under `.tool-homes/`. None of the checks sent a prompt to a model. In place of the missing `review_server` I used a stub server that records how it was launched.

## What works in each tool

| Part | Claude Code | Codex | Copilot |
|---|---|---|---|
| `review` (was a command, now a skill) | Works as before | Works, listed as `review-kit:review` | Works, listed as `review` |
| MCP server | Works as before | Works: starts from the plugin folder and gets the key | Set up correctly, but I couldn't test that it starts |
| SessionStart hook | Works as before | Loads, but runs only after the user approves it in Codex's hook review | Not tested; even if it runs, Copilot ignores its plain-text output, so it does nothing there |
| `reviewer` subagent | Works as before | Won't work: Codex plugins can't include subagents | Not tested; Copilot's docs name agent files `*.agent.md` |
| API key | Asked for on install, as before | Users must `export REVIEW_API_KEY` before starting Codex | Same as Codex |

Things I couldn't test:
- **Copilot:** starting the MCP server, the hook and the subagent all need a signed-in session. Copilot's sign-in lives in the macOS keychain, and a throwaway home doesn't separate it from your real account, so I didn't start one.
- **Codex:** I didn't run the hook itself.
- **Invocation syntax:** I checked that the skill is listed in Codex and Copilot, not the exact command to invoke it. That's why the README only says "listed as".

## What I changed
- **`commands/review.md` → `skills/review/SKILL.md`** (same text, plus a `name`). Claude Code shows the same components before and after (1 skill, 1 agent, 1 hook, 1 MCP server). I left out `disable-model-invocation` so behaviour matches the old command. Codex would otherwise have turned the command into a skill called `source-command-review`.
- **Claude's MCP config moved** from the root `.mcp.json` into `.claude-plugin/plugin.json`, with the same values. Copilot always prefers a root `.mcp.json` over its own settings. In both layouts, Claude Code passed the same key to the server and started it from the same path.
- **New Codex files:** `.codex-plugin/plugin.json` and `.codex-plugin/mcp.json`. The old config failed in Codex because it doesn't fill in `${CLAUDE_PLUGIN_ROOT}` in the command, and it only passes `REVIEW_API_KEY` to the server when that variable is listed.
- **New Copilot files:** `.github/plugin/plugin.json` and `.github/plugin/mcp.json`. The old config would have handed Copilot the literal text `${user_config.api_key}` as the key.
- **`README.md`:** install steps for each tool, the table above, and notes for maintainers.

## Things to know
- **Version in three places:** `name`, `version`, `description` and `author` now appear in all three manifests. They have to be changed together; I didn't add a check.
- **Tests from inside the repo fail:** installing from the repo folder itself fails with "File name too long" in both Codex and Copilot. That's because my throwaway homes are inside the repo, so each tool tried to copy the repo into itself. I tested from a copy instead; real users won't hit this.
- **Git settings:** I added `.tool-homes/` to `.git/info/exclude`.
- **Codex quirk:** when run from inside this repo, Codex added a `review-kit:` prefix to its own built-in skills, even with the plugin not installed. It looks like Codex behaviour, not something these changes cause.

Everything is in `$RUN/repo`:
- README.md
- .claude-plugin/plugin.json
- .codex-plugin/plugin.json
- .codex-plugin/mcp.json
- .github/plugin/plugin.json
- .github/plugin/mcp.json
- skills/review/SKILL.md

## Tool calls

The arm's tool calls, one JSON object per line, extracted from its transcript.

```jsonl
{"tool": "Bash", "input": {"command": "cd $RUN/repo && git status && git log --oneline | head && find . -path ./.git -prune -o -type f -print | head -100", "description": "Inspect repo layout and status"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && for f in .mcp.json README.md agents/reviewer.md server/run.sh hooks/hooks.json scripts/start.sh .claude-plugin/marketplace.json .claude-plugin/plugin.json commands/review.md; do echo \"=== $f\"; cat \"$f\"; done; ls -la server scripts; which codex copilot", "description": "Print all repo files"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=$PWD/.tool-homes; mkdir -p $T/codex $T/copilot; grep -q tool-homes .git/info/exclude || echo \".tool-homes/\" >> .git/info/exclude; HOME=$T/codex XDG_CONFIG_HOME=$T/codex/.config CODEX_HOME=$T/codex/.codex codex --version < /dev/null; HOME=$T/copilot XDG_CONFIG_HOME=$T/copilot/.config COPILOT_HOME=$T/copilot/.copilot copilot --version < /dev/null; HOME=$T/codex XDG_CONFIG_HOME=$T/codex/.config CODEX_HOME=$T/codex/.codex codex --help < /dev/null | head -40; HOME=$T/copilot XDG_CONFIG_HOME=$T/copilot/.config COPILOT_HOME=$T/copilot/.copilot copilot plugin --help < /dev/null", "description": "Check tool versions and help with isolated homes"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=$PWD/.tool-homes; mkdir -p $T/codex/.codex $T/codex/.config $T/copilot/.copilot $T/copilot/.config; C=\"env HOME=$T/codex XDG_CONFIG_HOME=$T/codex/.config CODEX_HOME=$T/codex/.codex codex\"; P=\"env HOME=$T/copilot XDG_CONFIG_HOME=$T/copilot/.config COPILOT_HOME=$T/copilot/.copilot copilot\"; $C plugin --help </dev/null; for s in $($C plugin --help </dev/null | awk '/^Commands:/{f=1;next} /^$/{f=0} f{print $1}'); do [ $s = help ] && continue; echo \"--- codex plugin $s\"; $C plugin $s --help </dev/null; done; for s in install list marketplace; do echo \"--- copilot plugin $s\"; $P plugin $s --help </dev/null; done", "description": "Read plugin subcommand help for both CLIs"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=$PWD/.tool-homes; cat > $T/cx <<EOF\n#!/bin/sh\nexec env HOME=$T/codex XDG_CONFIG_HOME=$T/codex/.config CODEX_HOME=$T/codex/.codex codex \"\\$@\" </dev/null\nEOF\ncat > $T/cp <<EOF\n#!/bin/sh\nexec env HOME=$T/copilot XDG_CONFIG_HOME=$T/copilot/.config COPILOT_HOME=$T/copilot/.copilot copilot \"\\$@\" </dev/null\nEOF\nchmod +x $T/cx $T/cp; $T/cx plugin --help; for s in add list marketplace; do echo \"--- codex plugin $s\"; $T/cx plugin $s --help; done; for s in install list; do echo \"--- copilot plugin $s\"; $T/cp plugin $s --help; done", "description": "Create isolated wrappers and read plugin help"}}
{"tool": "ToolSearch", "input": {"query": "select:WebFetch", "max_results": 1}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo/.tool-homes && mkdir -p docs && cd docs && curl -sL -o copilot-plugin-ref.html https://docs.github.com/en/copilot/reference/cli-plugin-reference; curl -sL -o copilot-about.html https://docs.github.com/copilot/concepts/agents/copilot-cli/about-cli-plugins; curl -sL -o codex-plugins-build.html https://developers.openai.com/codex/plugins/build; ls -la; for f in *.html; do echo \"== $f\"; python3 -c \"\nimport re,sys,html\nt=open('$f',errors='ignore').read()\nt=re.sub(r'(?s)<(script|style)[^>]*>.*?</\\1>','',t)\nt=re.sub(r'<[^>]+>',' ',t); t=html.unescape(t); t=re.sub(r'\\s+',' ',t)\nopen('$f.txt','w').write(t); print(len(t))\n\"; done", "description": "Download plugin docs with curl and strip HTML"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo/.tool-homes/docs && cat copilot-plugin-ref.html.txt | fold -w 4000 | head -20", "description": "Read Copilot CLI plugin reference"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo/.tool-homes/docs && python3 -c \"\nt=open('copilot-plugin-ref.html.txt').read(); i=t.find('plugin.json'); i=t.find('CLI plugin reference',i-3000)\nimport textwrap; print(textwrap.fill(t[t.find('Plugin standards OpenTelemetry')+30000 if False else 0:][:0]))\nj=t.find('This article'); print(textwrap.fill(t[j:j+26000],200))\n\"", "description": "Print Copilot reference body"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo/.tool-homes/docs && python3 -c \"\nimport textwrap\nt=open('copilot-plugin-ref.html.txt').read(); j=t.find('CLI commands'); print(j); j=t.find('plugin.json'); print(j)\nprint(textwrap.fill(t[j-2000:j+24000],220))\n\"", "description": "Print Copilot reference around plugin.json"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo/.tool-homes/docs && python3 -c \"\nimport textwrap\nt=open('codex-plugins-build.html.txt').read(); j=t.find('Build plugins'); j=t.find('plugin.json')\nprint(textwrap.fill(t[j-3000:j+34000],220))\n\"", "description": "Print Codex plugin build doc"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=$PWD/.tool-homes; $T/cp --help | head -80; echo ----; $T/cp --plugin-dir $PWD plugin list --json; echo; $T/cp --plugin-dir $PWD plugin list", "description": "Probe Copilot loading the plugin via plugin-dir"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=$PWD/.tool-homes; $T/cp mcp --help; $T/cp skill --help | head -30; echo ======; $T/cp --plugin-dir $PWD mcp list --json 2>&1; echo; $T/cp --plugin-dir $PWD mcp list 2>&1; $T/cp --plugin-dir $PWD skill list 2>&1 | head -30", "description": "Probe Copilot MCP and skill listings"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && R=$PWD; T=$PWD/.tool-homes; mkdir -p $T/work && cd $T/work && echo \"== mcp list json\"; $T/cp --plugin-dir $R mcp list --json 2>&1; echo \"== mcp get\"; $T/cp --plugin-dir $R mcp get review 2>&1; echo \"== skills\"; $T/cp --plugin-dir $R skill list 2>&1 | head -30", "description": "Probe Copilot MCP and skills from neutral cwd"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && R=$PWD; T=$PWD/.tool-homes; V=$T/variants; rm -rf $V; mkdir -p $V; \n# a: no env\nrsync -a --exclude .git --exclude .tool-homes $R/ $V/a/; printf '{\"mcpServers\":{\"review\":{\"command\":\"${CLAUDE_PLUGIN_ROOT}/server/run.sh\"}}}' > $V/a/.mcp.json\n# b: echo via plain command\nrsync -a --exclude .git --exclude .tool-homes $R/ $V/b/; printf '{\"mcpServers\":{\"review\":{\"command\":\"sh\",\"args\":[\"-c\",\"echo hi\"]}}}' > $V/b/.mcp.json\ncd $T/work; for v in a b; do echo \"== $v\"; $T/cp --plugin-dir $V/$v mcp list --json 2>&1; done; echo \"== install local\"; $T/cp plugin install $R 2>&1; $T/cp plugin list --json; $T/cp mcp list --json", "description": "Test Copilot MCP discovery with variants"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && R=$PWD; T=$PWD/.tool-homes; cd $T/work; $T/cp plugin marketplace add $R 2>&1; $T/cp plugin marketplace browse review-kit 2>&1; $T/cp plugin install review-kit@review-kit 2>&1; $T/cp plugin list --json; $T/cp mcp list --json; find $T/copilot -maxdepth 4 | head -40", "description": "Install plugin via Copilot local marketplace"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo/.tool-homes && cat copilot/.copilot/logs/*.log | grep -iv '^\\s*$' | grep -iE 'plugin|hook|agent|warn|error|review' | cut -c1-300 | sort -u | head -60; ls -la $(dirname $(readlink -f $(which copilot))); readlink -f $(which copilot)", "description": "Scan Copilot logs and locate its install"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo/.tool-homes/docs && curl -sL -o copilot-create.html https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/plugins-creating; curl -sL -o copilot-hooks-ref.html https://docs.github.com/en/copilot/reference/hooks-configuration; curl -sL -o copilot-agents-ref.html https://docs.github.com/en/copilot/reference/custom-agents-configuration; for f in copilot-create copilot-hooks-ref copilot-agents-ref; do python3 -c \"\nimport re,html\nt=open('$f.html',errors='ignore').read()\nt=re.sub(r'(?s)<(script|style)[^>]*>.*?</\\1>','',t)\nt=re.sub(r'<[^>]+>',' ',t); t=html.unescape(t); t=re.sub(r'\\s+',' ',t)\nopen('$f.txt','w').write(t); print('$f',len(t), t[:100])\n\"; done; for f in copilot-about copilot-create copilot-hooks-ref copilot-agents-ref; do echo \"#### $f\"; grep -oiE '.{250}(claude|\\.agent\\.md|PascalCase|camelCase|preToolUse|SessionStart).{250}' $f.txt | head -12; done", "description": "Fetch Copilot create/hooks/agents docs and grep compat notes"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo/.tool-homes/docs && python3 -c \"\nimport textwrap\nt=open('copilot-hooks-ref.txt').read(); j=t.find('Introduction Hooks locations'); j=t.find('Introduction',j+50)\nprint(textwrap.fill(t[j:j+9000],220))\n\"; grep -oiE '.{300}(PLUGIN_ROOT|nested|matcher group).{300}' copilot-hooks-ref.txt | head", "description": "Read Copilot hook config format section"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo/.tool-homes/docs && for f in copilot-*.txt; do echo \"## $f\"; grep -oE '.{200}PLUGIN_ROOT.{200}' $f; grep -oiE '.{200}(commands/|slash command).{200}' $f | head -5; done; python3 -c \"\nimport textwrap\nt=open('copilot-create.txt').read(); j=t.find('Creating a plugin for GitHub Copilot CLI',2000)\nprint(textwrap.fill(t[j:j+12000],220))\"", "description": "Search Copilot docs for plugin root and commands"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && R=$PWD; T=$PWD/.tool-homes; cd $T/work; $T/cx plugin marketplace add $R 2>&1; $T/cx plugin marketplace list 2>&1; $T/cx plugin list --available --json 2>&1 | head -60", "description": "Add repo as Codex marketplace and list plugins"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && R=$PWD; T=$PWD/.tool-homes; cd $T/work; $T/cx plugin add review-kit@review-kit --json 2>&1; $T/cx plugin list --json 2>&1; find $T/codex/.codex -maxdepth 6 -not -path '*/log*' | head -40; cat $T/codex/.codex/config.toml; $T/cx mcp list --json 2>&1", "description": "Install plugin in Codex and inspect result"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo/.tool-homes && find codex/.codex -not -path '*/log*' | sed 's|.*/.codex/||'; ls codex/.codex/log* 2>/dev/null; RUST_LOG=debug ./cx plugin add review-kit@review-kit 2>&1 | grep -iE 'dir|path|name' | cut -c1-400 | head -20", "description": "Inspect Codex state and debug install failure"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && R=$PWD; T=$PWD/.tool-homes; rm -rf $T/src && mkdir -p $T/src && git archive HEAD | tar -x -C $T/src; ls -la $T/src; cd $T/work; $T/cx plugin marketplace remove review-kit; $T/cx plugin marketplace add $T/src 2>&1; $T/cx plugin add review-kit@review-kit --json 2>&1; find $T/codex/.codex/plugins -maxdepth 6; cat $T/codex/.codex/config.toml; $T/cx mcp list --json", "description": "Install clean copy of plugin into Codex"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo/.tool-homes/codex/.codex/plugins/cache/review-kit/review-kit/2.0.0/.codex-plugin && find . -type f -exec sh -c 'echo \"== $1\"; cat \"$1\"' _ {} \\;", "description": "Show Codex migrated command skills"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo/.tool-homes/work && ../cx debug --help; ../cx features list 2>&1 | grep -iE 'plugin|hook|skill|agent|command'", "description": "Explore Codex debug and feature flags"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo/.tool-homes/work && ../cx debug prompt-input --help | head -30; ../cx debug prompt-input > ../pi.json 2>../pi.err; echo rc=$?; head -c 600 ../pi.err; wc -c ../pi.json; grep -oE '.{200}(review|source-command).{200}' ../pi.json | head", "description": "Render Codex model-visible prompt input offline"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo/.tool-homes && python3 -c \"\nimport json,re\nd=json.load(open('pi.json'))\ns=json.dumps(d)\ni=s.find('### Available skills'); print(s[i-600:i+200].replace('\\\\\\\\n','\\n'))\nfor m in re.finditer(r'- ([\\w:.-]+): ', s[i:i+8000].replace('\\\\\\\\n','\\n')): print(m.group(1))\nprint('source-command' in s, 'reviewer' in s, 'review-kit ready' in s)\n\"", "description": "List skills in Codex prompt input"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo/.tool-homes/work && ../cx app-server --help | head -40; ../cx debug app-server --help | head -30", "description": "Check Codex app-server tooling"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo/.tool-homes && mkdir -p schema && ./cx app-server generate-ts --out schema >/dev/null 2>&1; ls schema | head; grep -rlE 'mcpServerStatus|McpServerStatus' schema | head; grep -rhoE '\"(mcpServer[A-Za-z/]*|hooks/[A-Za-z]*|skills/[A-Za-z]*|plugin[A-Za-z]*/[A-Za-z]*|config/[A-Za-z]*)\"' schema | sort -u", "description": "Generate app-server protocol types and find MCP methods"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo/.tool-homes/schema && cat v2/ListMcpServerStatusParams.ts v2/McpServerStatus.ts v2/McpServerStatusDetail.ts; grep -l 'HooksList' v2/*.ts | head; cat v2/HooksListParams.ts v2/HooksListResponse.ts 2>/dev/null; cat v2/PluginReadParams.ts 2>/dev/null; cat InitializeParams.ts ClientInfo.ts 2>/dev/null | head -30", "description": "Read MCP status and hooks list types"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo/.tool-homes && cat > probe-run.sh <<'EOF'\n#!/bin/sh\n# Stub MCP server: record how the host launched us, then exit.\nLOG=\"${PROBE_LOG:-$RUN/repo/.tool-homes/probe.log}\"\n{ echo \"--- launched $0 pwd=$(pwd)\"; echo \"REVIEW_API_KEY=[${REVIEW_API_KEY-<unset>}]\"; env | grep -E 'PLUGIN|^HOME=' | sort; } >> \"$LOG\"\nexit 1\nEOF\nchmod +x probe-run.sh; cat > codex_probe.py <<'EOF'\nimport json, subprocess, sys, os, time, threading\nT = os.path.dirname(os.path.abspath(__file__))\nenv = dict(os.environ, HOME=f\"{T}/codex\", XDG_CONFIG_HOME=f\"{T}/codex/.config\", CODEX_HOME=f\"{T}/codex/.codex\")\nenv.update(dict(a.split(\"=\",1) for a in sys.argv[2:]))\np = subprocess.Popen([\"codex\", \"app-server\"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=open(f\"{T}/appserver.err\",\"w\"), env=env, cwd=f\"{T}/work\", text=True)\nout = {}\ndef reader():\n    for line in p.stdout:\n        try: m = json.loads(line)\n        except Exception: continue\n        if \"id\" in m and (\"result\" in m or \"error\" in m): out[m[\"id\"]] = m\nthreading.Thread(target=reader, daemon=True).start()\ndef send(obj): p.stdin.write(json.dumps(obj)+\"\\n\"); p.stdin.flush()\ndef call(i, method, params, wait=30):\n    send({\"id\": i, \"method\": method, \"params\": params})\n    t=time.time()\n    while i not in out and time.time()-t<wait: time.sleep(0.1)\n    return out.get(i, {\"timeout\": method})\nprint(json.dumps(call(1,\"initialize\",{\"clientInfo\":{\"name\":\"probe\",\"title\":None,\"version\":\"0\"},\"capabilities\":None}))[:300])\nsend({\"method\":\"initialized\"})\nfor i,(m,pr) in enumerate([(\"skills/list\",{}),(\"hooks/list\",{}),(\"plugin/read\",{\"pluginName\":\"review-kit\",\"marketplacePath\":sys.argv[1]}),(\"mcpServerStatus/list\",{})],start=2):\n    r = call(i,m,pr, wait=40)\n    print(f\"##### {m}\"); print(json.dumps(r, indent=1)[:6000])\np.terminate()\nEOF\necho ok", "description": "Write stub MCP server and Codex app-server probe"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo/.tool-homes && cp probe-run.sh codex/.codex/plugins/cache/review-kit/review-kit/2.0.0/server/run.sh && rm -f probe.log && REVIEW_API_KEY=from-shell python3 codex_probe.py $PWD/src/.claude-plugin/marketplace.json 2>&1 | head -300; echo \"#### probe.log\"; cat probe.log; tail -5 appserver.err", "description": "Run Codex app-server probe against installed plugin", "timeout": 200000}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo/.tool-homes && C=codex/.codex/plugins/cache/review-kit/review-kit/2.0.0; cp $C/.mcp.json mcp.orig.json; try(){ echo \"=========== $1\"; printf '%s' \"$2\" > $C/.mcp.json; rm -f probe.log; REVIEW_API_KEY=from-shell python3 codex_probe.py $PWD/src/.claude-plugin/marketplace.json 2>&1 | grep -A3 toolsError | head -3; cat probe.log 2>/dev/null; }\ntry PLUGIN_ROOT_cmd '{\"mcpServers\":{\"review\":{\"command\":\"${PLUGIN_ROOT}/server/run.sh\"}}}'\ntry relative_cmd '{\"mcpServers\":{\"review\":{\"command\":\"./server/run.sh\"}}}'\ntry sh_env '{\"mcpServers\":{\"review\":{\"command\":\"sh\",\"args\":[\"-c\",\"exec \\\"$CLAUDE_PLUGIN_ROOT/server/run.sh\\\"\"]}}}'\ntry cwd_dot '{\"mcpServers\":{\"review\":{\"command\":\"sh\",\"args\":[\"-c\",\"pwd >> '$PWD'/probe.log; env | grep -i plugin >> '$PWD'/probe.log; exit 1\"],\"cwd\":\".\"}}}'\ntry args_expand '{\"mcpServers\":{\"review\":{\"command\":\"sh\",\"args\":[\"${CLAUDE_PLUGIN_ROOT}/server/run.sh\"],\"env_vars\":[\"REVIEW_API_KEY\"]}}}'", "description": "Try MCP config variants in Codex", "timeout": 400000}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo/.tool-homes && C=codex/.codex/plugins/cache/review-kit/review-kit/2.0.0; try(){ echo \"=========== $1\"; printf '%s' \"$2\" > $C/.mcp.json; rm -f probe.log; REVIEW_API_KEY=from-shell python3 codex_probe.py $PWD/src/.claude-plugin/marketplace.json 2>&1 | grep -A0 toolsError | head -1; cat probe.log 2>/dev/null; }\ntry cwd_rel_cmd '{\"mcpServers\":{\"review\":{\"command\":\"./server/run.sh\",\"cwd\":\".\"}}}'\ntry cwd_rel_cmd_envvars '{\"mcpServers\":{\"review\":{\"command\":\"./server/run.sh\",\"cwd\":\".\",\"env_vars\":[\"REVIEW_API_KEY\"]}}}'\ntry sh_cwd '{\"mcpServers\":{\"review\":{\"command\":\"sh\",\"args\":[\"server/run.sh\"],\"cwd\":\".\"}}}'", "description": "Try relative cwd MCP variants in Codex", "timeout": 400000}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo/.tool-homes/docs && for u in https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-mcp-servers https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-command-reference https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-config-dir-reference; do n=$(basename $u); curl -sL -o $n.html $u; python3 -c \"\nimport re,html\nt=open('$n.html',errors='ignore').read()\nt=re.sub(r'(?s)<(script|style)[^>]*>.*?</\\1>','',t)\nt=re.sub(r'<[^>]+>',' ',t); t=html.unescape(t); t=re.sub(r'\\s+',' ',t)\nopen('$n.txt','w').write(t); print('$n',len(t))\"; grep -oiE '.{250}(expan|\\\\\\$\\{[A-Z_]+\\}|inherit).{250}' $n.txt | grep -iE 'env|mcp' | head -8; done", "description": "Fetch Copilot MCP docs and grep env expansion"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo/.tool-homes/docs && grep -oiE '.{300}(PLUGIN_ROOT|\\.claude-plugin|claude code).{300}' cli-command-reference.txt cli-config-dir-reference.txt | head -12", "description": "Grep Copilot reference for plugin root and Claude compat"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && which claude; ls .tool-homes; cat .git/info/exclude | tail -2", "description": "Check for claude CLI and exclude file"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && mkdir -p skills/review .codex-plugin .github/plugin && git mv commands/review.md skills/review/SKILL.md && rmdir commands 2>/dev/null; cat > skills/review/SKILL.md <<'EOF'\n---\nname: review\ndescription: Review the current diff\ndisable-model-invocation: true\n---\n\nReview the staged diff and list problems.\nEOF\ncat > .codex-plugin/plugin.json <<'EOF'\n{\n  \"name\": \"review-kit\",\n  \"version\": \"2.0.0\",\n  \"description\": \"Code review helpers\",\n  \"author\": {\n    \"name\": \"Acme\"\n  },\n  \"skills\": \"./skills/\",\n  \"mcpServers\": \"./.codex-plugin/mcp.json\"\n}\nEOF\ncat > .codex-plugin/mcp.json <<'EOF'\n{\n  \"mcpServers\": {\n    \"review\": {\n      \"command\": \"./server/run.sh\",\n      \"cwd\": \".\",\n      \"env_vars\": [\"REVIEW_API_KEY\"]\n    }\n  }\n}\nEOF\ncat > .github/plugin/plugin.json <<'EOF'\n{\n  \"name\": \"review-kit\",\n  \"version\": \"2.0.0\",\n  \"description\": \"Code review helpers\",\n  \"author\": {\n    \"name\": \"Acme\"\n  },\n  \"mcpServers\": \".github/plugin/mcp.json\"\n}\nEOF\ncat > .github/plugin/mcp.json <<'EOF'\n{\n  \"mcpServers\": {\n    \"review\": {\n      \"type\": \"local\",\n      \"command\": \"sh\",\n      \"args\": [\"-c\", \"exec \\\"$PLUGIN_ROOT/server/run.sh\\\"\"],\n      \"env\": {\n        \"REVIEW_API_KEY\": \"${REVIEW_API_KEY}\"\n      },\n      \"tools\": [\"*\"]\n    }\n  }\n}\nEOF\ngit status --short", "description": "Convert command to skill and add Codex/Copilot manifests"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && python3 - <<'EOF'\nimport json\np='.github/plugin/mcp.json'; d=json.load(open(p))\nd['mcpServers']['review']['args']=[\"-c\",'exec \"${PLUGIN_ROOT:-.}/server/run.sh\"']\nopen(p,'w').write(json.dumps(d,indent=2)+\"\\n\")\nEOF\ncat .github/plugin/mcp.json; for f in .codex-plugin/*.json .github/plugin/*.json; do python3 -m json.tool $f >/dev/null && echo \"valid $f\"; done", "description": "Add cwd fallback to Copilot MCP launch and validate JSON"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && R=$PWD; T=$PWD/.tool-homes; rm -rf $T/src $T/codex && mkdir -p $T/codex/.codex $T/codex/.config && rsync -a --exclude .git --exclude .tool-homes $R/ $T/src/ && cd $T/work && $T/cx plugin marketplace add $T/src >/dev/null && $T/cx plugin add review-kit@review-kit --json; C=$T/codex/.codex/plugins/cache/review-kit/review-kit/2.0.0; ls -a $C $C/.codex-plugin; cp $T/probe-run.sh $C/server/run.sh; cd $T; rm -f probe.log; REVIEW_API_KEY=from-shell python3 codex_probe.py $T/src/.claude-plugin/marketplace.json > probe.out 2>&1; python3 - <<'EOF'\nimport json,re\ns=open('probe.out').read()\nfor block in s.split('##### ')[1:]:\n    name,_,body=block.partition('\\n')\n    print('==',name)\n    if name=='skills/list':\n        for m in re.finditer(r'\"name\": \"([^\"]+)\"[^{}]*?\"pluginId\": (\"[^\"]+\"|null)', body): print('  ',m.group(1),m.group(2))\n    else: print(body[:1800])\nEOF\necho \"## probe.log\"; cat probe.log", "description": "Reinstall modified plugin in fresh Codex home and probe", "timeout": 300000}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo/.tool-homes/work && ../cx debug prompt-input > ../pi2.json 2>/dev/null; python3 -c \"\nimport json,re\ns=json.dumps(json.load(open('../pi2.json'))).replace('\\\\\\\\n','\\n')\ni=s.find('### Available skills'); print('\\n'.join(l for l in s[i:i+6000].split('\\n') if l.startswith('- '))[:1500]); print('review-kit:review' in s)\"", "description": "Check Codex model-visible skill list"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo/.tool-homes/work && ../cx debug prompt-input -c 'plugins.\"review-kit@review-kit\".enabled=false' 2>/dev/null | python3 -c \"\nimport json,sys\ns=json.dumps(json.load(sys.stdin)).replace('\\\\\\\\n','\\n')\nprint([l[:40] for l in s.split('\\n') if l.startswith('- ') and 'SKILL.md' in l])\"", "description": "Compare Codex skill names with plugin disabled"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo/.tool-homes && mkdir -p codex2/.codex codex2/.config work2 && cd work2 && env HOME=$PWD/../codex2 XDG_CONFIG_HOME=$PWD/../codex2/.config CODEX_HOME=$PWD/../codex2/.codex codex debug prompt-input </dev/null 2>/dev/null | python3 -c \"\nimport json,sys\ns=json.dumps(json.load(sys.stdin)).replace('\\\\\\\\n','\\n')\nprint([l[:30] for l in s.split('\\n') if l.startswith('- ') and 'SKILL.md' in l])\"", "description": "Check Codex skill names with no plugin installed"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo/.tool-homes && sed -i '' 's|^exec env |exec env -u GH_TOKEN -u GITHUB_TOKEN -u COPILOT_GITHUB_TOKEN |' cp && cat cp && rm -rf copilot && mkdir -p copilot/.copilot copilot/.config && mkdir -p /dev/null 2>/dev/null; cd work2 && ../cp plugin marketplace add $PWD/../src && ../cp plugin install review-kit@review-kit && ../cp plugin list --json && ../cp mcp list --json && ../cp skill list | sed -n '1,4p'", "description": "Install modified plugin in fresh Copilot home and inspect"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo/.tool-homes/work2 && S=../src; sed -i '' 's/\"2.0.0\"/\"9.9.9\"/' $S/.github/plugin/plugin.json; ../cp plugin list --json | grep version; sed -i '' 's/\"9.9.9\"/\"2.0.0\"/' $S/.github/plugin/plugin.json; echo \"-- inline mcpServers object test\"; cp $S/.github/plugin/plugin.json ../gh-plugin.bak; python3 - <<'EOF'\nimport json\np='../src/.github/plugin/plugin.json'; d=json.load(open(p)); d['mcpServers']=json.load(open('../src/.github/plugin/mcp.json'))['mcpServers']; json.dump(d,open(p,'w'),indent=2)\nEOF\n../cp mcp list --json | head -12; cp ../gh-plugin.bak $S/.github/plugin/plugin.json", "description": "Check which manifest Copilot reads and inline MCP precedence"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo/.tool-homes/work2 && S=../src; mv $S/.mcp.json $S/.mcp.json.off; ../cp mcp list --json | head -30; mv $S/.mcp.json.off $S/.mcp.json", "description": "Test Copilot MCP with .mcp.json absent"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && python3 - <<'EOF'\nimport json\np='.claude-plugin/plugin.json'; d=json.load(open(p))\nd['mcpServers']=json.load(open('.mcp.json'))['mcpServers']\nopen(p,'w').write(json.dumps(d,indent=2)+\"\\n\")\nEOF\ngit rm -q .mcp.json && cat .claude-plugin/plugin.json && git status --short", "description": "Move Claude MCP config inline into Claude manifest"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo/.tool-homes && mkdir -p claude/.claude claude/.config && cat > cl <<EOF\n#!/bin/sh\nexec env -u ANTHROPIC_API_KEY -u CLAUDE_CODE_OAUTH_TOKEN -u CLAUDECODE -u CLAUDE_CODE_ENTRYPOINT HOME=$PWD/claude XDG_CONFIG_HOME=$PWD/claude/.config CLAUDE_CONFIG_DIR=$PWD/claude/.claude claude \"\\$@\" </dev/null\nEOF\nchmod +x cl; ./cl --version; ./cl plugin --help", "description": "Set up isolated Claude Code wrapper and read plugin help"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && R=$PWD; T=$R/.tool-homes; rm -rf $T/base $T/src && mkdir -p $T/base && git archive HEAD | tar -x -C $T/base && rsync -a --exclude .git --exclude .tool-homes $R/ $T/src/; cd $T/work2; for d in base src; do echo \"######## $d\"; ../cl plugin validate $T/$d 2>&1; done; ../cl plugin details --help", "description": "Validate baseline and modified plugin with Claude Code"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo/.tool-homes/work2 && T=..; for d in base src; do echo \"######## $d\"; ../cl plugin validate $T/$d/.claude-plugin/plugin.json 2>&1; ../cl plugin validate $T/$d/skills 2>&1 | tail -3; done; for d in base src; do echo \"######## install $d\"; rm -rf ../claude && mkdir -p ../claude/.claude; ../cl plugin marketplace add $T/$d 2>&1 | tail -1; ../cl plugin install review-kit@review-kit 2>&1 | tail -1; ../cl plugin details review-kit@review-kit 2>&1; done", "description": "Validate plugin manifests and inspect component inventory"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && sed -i '' '/^disable-model-invocation: true$/d' skills/review/SKILL.md && cat skills/review/SKILL.md && git diff -M HEAD --stat", "description": "Remove model-invocation flag to match original command"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && R=$PWD; T=$R/.tool-homes; rsync -a --delete --exclude .git --exclude .tool-homes $R/ $T/src/; cd $T/work2; for d in base src; do echo \"######## $d\"; rm -rf ../claude && mkdir -p ../claude/.claude; ../cl plugin marketplace add $T/$d >/dev/null 2>&1; ../cl plugin install review-kit@review-kit >/dev/null 2>&1; for f in $(find ../claude/.claude/plugins -path '*server/run.sh'); do cp ../probe-run.sh $f; done; rm -f ../probe.log; timeout 60 ../cl mcp list 2>&1 | tail -5; echo \"-- probe.log\"; cat ../probe.log 2>/dev/null; done", "description": "Compare Claude MCP launch for baseline and modified plugin", "timeout": 200000}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo/.tool-homes/work2 && T=..; for d in base src; do echo \"######## $d\"; rm -rf ../claude && mkdir -p ../claude/.claude; ../cl plugin marketplace add $PWD/../$d >/dev/null 2>&1; ../cl plugin install review-kit@review-kit >/dev/null 2>&1; find ../claude/.claude/plugins -path '*server/run.sh' | while read f; do cp ../probe-run.sh \"$f\"; done; rm -f ../probe.log; ../cl mcp list 2>&1 | tail -5; echo \"-- probe.log\"; cat ../probe.log 2>/dev/null; done", "description": "Compare Claude MCP launch without timeout", "timeout": 300000}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo/.tool-homes/work2 && for d in base src; do echo \"######## $d\"; cp ../probe-run.sh ../$d/server/run.sh; rm -rf ../claude && mkdir -p ../claude/.claude; ../cl plugin marketplace add $PWD/../$d >/dev/null 2>&1; ../cl plugin install review-kit@review-kit >/dev/null 2>&1; rm -f ../probe.log; ../cl mcp list 2>&1 | tail -1 | cut -c1-60; echo \"-- probe.log\"; cat ../probe.log 2>/dev/null; done", "description": "Probe Claude MCP launch using stub in source copies", "timeout": 300000}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo/.tool-homes/work2 && for d in base src; do rm -rf ../ns-$d; cp -R ../$d ../ns-$d; sed -i '' 's/\"sensitive\": true/\"sensitive\": false/' ../ns-$d/.claude-plugin/plugin.json; echo \"######## $d (sensitive:false copy)\"; rm -rf ../claude && mkdir -p ../claude/.claude; ../cl plugin marketplace add $PWD/../ns-$d >/dev/null 2>&1; ../cl plugin install review-kit@review-kit --config api_key=probe-key 2>&1 | tail -1; rm -f ../probe.log; ../cl mcp list >/dev/null 2>&1; grep -E 'launched|REVIEW' ../probe.log | sed 's|.*/.tool-homes/||'; done; grep -rl probe-key ../claude/.claude | head", "description": "Verify Claude substitutes user_config key in both layouts", "timeout": 300000}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo/.tool-homes/work2 && rm -rf ../copilot && mkdir -p ../copilot/.copilot && ../cp plugin marketplace add $PWD/../src >/dev/null && ../cp plugin install review-kit@review-kit && ../cp mcp list --json | python3 -c \"import json,sys; d=json.load(sys.stdin)['mcpServers']['review']; print({k:d[k] for k in ('command','args','cwd')}, d['env'].get('REVIEW_API_KEY'))\"; ../cp skill list | sed -n '1,3p'", "description": "Recheck Copilot MCP and skills after changes"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo/.tool-homes && rm -rf codex && mkdir -p codex/.codex && cd work && ../cx plugin marketplace add $PWD/../src >/dev/null && ../cx plugin add review-kit@review-kit >/dev/null && cd .. && rm -f probe.log && REVIEW_API_KEY=from-shell python3 codex_probe.py $PWD/src/.claude-plugin/marketplace.json > probe.out 2>&1; grep -E '\"name\": \"review-kit:review\"|trustStatus|toolsError|\"mcpServers\"' probe.out; grep -E 'launched|REVIEW' probe.log | sed 's|.*/.tool-homes/||'; echo \"-- without env_vars key in shell:\"; rm -f probe.log; python3 codex_probe.py $PWD/src/.claude-plugin/marketplace.json >/dev/null 2>&1; grep REVIEW probe.log", "description": "Recheck Codex after final layout", "timeout": 300000}}
{"tool": "Write", "input": {"file_path": "$RUN/repo/README.md", "content": "# review-kit\n\nCode review helpers for Claude Code, OpenAI Codex CLI, and GitHub Copilot CLI.\n\n## Install\n\nThe same repository is the marketplace for all three tools.\nReplace `OWNER/REPO` with this repository.\n\n| Tool | Commands |\n| --- | --- |\n| Claude Code | `/plugin marketplace add OWNER/REPO`, then `/plugin install review-kit@review-kit` |\n| Codex CLI | `codex plugin marketplace add OWNER/REPO`, then `codex plugin add review-kit@review-kit` |\n| Copilot CLI | `copilot plugin marketplace add OWNER/REPO`, then `copilot plugin install review-kit@review-kit` |\n\n### API key\n\n- Claude Code prompts for the key when you enable the plugin and stores it as a sensitive value.\n- Codex and Copilot have no plugin settings prompt. Export `REVIEW_API_KEY` in the shell you launch them from.\n\n## What works where\n\n| Component | Claude Code | Codex CLI | Copilot CLI |\n| --- | --- | --- | --- |\n| `review` skill (`skills/review/`) | `/review-kit:review` | `$review` (listed as `review-kit:review`) | `/review` |\n| `review` MCP server (`server/run.sh`) | yes | yes | configured; launch not yet tested |\n| `SessionStart` hook (`hooks/hooks.json`) | yes | only after you trust it in Codex's hook review | not tested; Copilot ignores its plain-text output |\n| `reviewer` subagent (`agents/reviewer.md`) | yes | no (Codex plugins cannot ship agents) | not tested |\n\n## Layout for maintainers\n\nEach tool reads its own manifest, and each manifest points at that tool's MCP config:\n\n| Tool | Manifest | MCP config |\n| --- | --- | --- |\n| Claude Code | `.claude-plugin/plugin.json` | inline `mcpServers` in that manifest |\n| Codex CLI | `.codex-plugin/plugin.json` | `.codex-plugin/mcp.json` |\n| Copilot CLI | `.github/plugin/plugin.json` | `.github/plugin/mcp.json` |\n\nThere are separate MCP configs because each tool handles placeholders and environment variables differently.\n`${user_config.*}` works only in Claude Code.\nCodex does not expand `${CLAUDE_PLUGIN_ROOT}` in an MCP `command`, and it passes a shell variable to the server only when that variable is listed in `env_vars`.\nCopilot prefers a root `.mcp.json` over its manifest, so do not put one back at the repository root.\n\n`name`, `version`, `description`, and `author` appear in all three manifests.\nChange them in all three at once.\n"}}
{"tool": "Edit", "input": {"replace_all": false, "file_path": "$RUN/repo/README.md", "old_string": "| `/review-kit:review` | `$review` (listed as `review-kit:review`) | `/review` |", "new_string": "| `/review-kit:review` | yes, listed as `review-kit:review` | yes, listed as `review` |"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && git add -A && git status --short && git diff --cached -M --stat && cat server/run.sh", "description": "Stage changes and confirm the real run.sh was not modified"}}
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
diff --git a/.claude-plugin/plugin.json b/.claude-plugin/plugin.json
index f3ef489..6527aef 100644
--- a/.claude-plugin/plugin.json
+++ b/.claude-plugin/plugin.json
@@ -12,5 +12,13 @@
       "description": "Key for the review service",
       "sensitive": true
     }
+  },
+  "mcpServers": {
+    "review": {
+      "command": "${CLAUDE_PLUGIN_ROOT}/server/run.sh",
+      "env": {
+        "REVIEW_API_KEY": "${user_config.api_key}"
+      }
+    }
   }
 }
diff --git a/.codex-plugin/mcp.json b/.codex-plugin/mcp.json
new file mode 100644
index 0000000..b5c0327
--- /dev/null
+++ b/.codex-plugin/mcp.json
@@ -0,0 +1,9 @@
+{
+  "mcpServers": {
+    "review": {
+      "command": "./server/run.sh",
+      "cwd": ".",
+      "env_vars": ["REVIEW_API_KEY"]
+    }
+  }
+}
diff --git a/.codex-plugin/plugin.json b/.codex-plugin/plugin.json
new file mode 100644
index 0000000..97704f5
--- /dev/null
+++ b/.codex-plugin/plugin.json
@@ -0,0 +1,10 @@
+{
+  "name": "review-kit",
+  "version": "2.0.0",
+  "description": "Code review helpers",
+  "author": {
+    "name": "Acme"
+  },
+  "skills": "./skills/",
+  "mcpServers": "./.codex-plugin/mcp.json"
+}
diff --git a/.github/plugin/mcp.json b/.github/plugin/mcp.json
new file mode 100644
index 0000000..eb86537
--- /dev/null
+++ b/.github/plugin/mcp.json
@@ -0,0 +1,18 @@
+{
+  "mcpServers": {
+    "review": {
+      "type": "local",
+      "command": "sh",
+      "args": [
+        "-c",
+        "exec \"${PLUGIN_ROOT:-.}/server/run.sh\""
+      ],
+      "env": {
+        "REVIEW_API_KEY": "${REVIEW_API_KEY}"
+      },
+      "tools": [
+        "*"
+      ]
+    }
+  }
+}
diff --git a/.github/plugin/plugin.json b/.github/plugin/plugin.json
new file mode 100644
index 0000000..55aeec4
--- /dev/null
+++ b/.github/plugin/plugin.json
@@ -0,0 +1,9 @@
+{
+  "name": "review-kit",
+  "version": "2.0.0",
+  "description": "Code review helpers",
+  "author": {
+    "name": "Acme"
+  },
+  "mcpServers": ".github/plugin/mcp.json"
+}
diff --git a/.mcp.json b/.mcp.json
deleted file mode 100644
index 8271f93..0000000
--- a/.mcp.json
+++ /dev/null
@@ -1,10 +0,0 @@
-{
-  "mcpServers": {
-    "review": {
-      "command": "${CLAUDE_PLUGIN_ROOT}/server/run.sh",
-      "env": {
-        "REVIEW_API_KEY": "${user_config.api_key}"
-      }
-    }
-  }
-}
diff --git a/README.md b/README.md
index 9246da6..3bf9183 100644
--- a/README.md
+++ b/README.md
@@ -1,3 +1,46 @@
 # review-kit
 
-Code review helpers for Claude Code.
+Code review helpers for Claude Code, OpenAI Codex CLI, and GitHub Copilot CLI.
+
+## Install
+
+The same repository is the marketplace for all three tools.
+Replace `OWNER/REPO` with this repository.
+
+| Tool | Commands |
+| --- | --- |
+| Claude Code | `/plugin marketplace add OWNER/REPO`, then `/plugin install review-kit@review-kit` |
+| Codex CLI | `codex plugin marketplace add OWNER/REPO`, then `codex plugin add review-kit@review-kit` |
+| Copilot CLI | `copilot plugin marketplace add OWNER/REPO`, then `copilot plugin install review-kit@review-kit` |
+
+### API key
+
+- Claude Code prompts for the key when you enable the plugin and stores it as a sensitive value.
+- Codex and Copilot have no plugin settings prompt. Export `REVIEW_API_KEY` in the shell you launch them from.
+
+## What works where
+
+| Component | Claude Code | Codex CLI | Copilot CLI |
+| --- | --- | --- | --- |
+| `review` skill (`skills/review/`) | `/review-kit:review` | yes, listed as `review-kit:review` | yes, listed as `review` |
+| `review` MCP server (`server/run.sh`) | yes | yes | configured; launch not yet tested |
+| `SessionStart` hook (`hooks/hooks.json`) | yes | only after you trust it in Codex's hook review | not tested; Copilot ignores its plain-text output |
+| `reviewer` subagent (`agents/reviewer.md`) | yes | no (Codex plugins cannot ship agents) | not tested |
+
+## Layout for maintainers
+
+Each tool reads its own manifest, and each manifest points at that tool's MCP config:
+
+| Tool | Manifest | MCP config |
+| --- | --- | --- |
+| Claude Code | `.claude-plugin/plugin.json` | inline `mcpServers` in that manifest |
+| Codex CLI | `.codex-plugin/plugin.json` | `.codex-plugin/mcp.json` |
+| Copilot CLI | `.github/plugin/plugin.json` | `.github/plugin/mcp.json` |
+
+There are separate MCP configs because each tool handles placeholders and environment variables differently.
+`${user_config.*}` works only in Claude Code.
+Codex does not expand `${CLAUDE_PLUGIN_ROOT}` in an MCP `command`, and it passes a shell variable to the server only when that variable is listed in `env_vars`.
+Copilot prefers a root `.mcp.json` over its manifest, so do not put one back at the repository root.
+
+`name`, `version`, `description`, and `author` appear in all three manifests.
+Change them in all three at once.
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
