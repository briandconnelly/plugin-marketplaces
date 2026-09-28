# Run: scenario 4, repetition 5, baseline (DISCARDED, not scored)

Scored against `tests/scenarios.md` as of this commit; cost is `metrics` in the manifest.

## Manifest

```json
{
  "date": "2026-09-28",
  "arm": "baseline",
  "scenario": "s4",
  "rep": 5,
  "fixture_tree": "5636a130e9dfed2c78f60f0a2718f62fef2c7d5c",
  "upstream_commits": null,
  "tools": {
    "claude": "2.1.284 (Claude Code)",
    "codex": "codex-cli 0.157.1",
    "copilot": "GitHub Copilot CLI 1.0.88."
  },
  "session_context": "dispatched from a Claude Code session (claude 2.1.284) with installed plugins including superpowers, plugin-dev, amicus, astral, obsidian, pr-review-toolkit, code-review, skill-creator, mcp-server-dev, claude-code-setup; user skills include agent-bot-identity, review-pr, fastmcp, prek; the plugin-marketplaces skill is not installed anywhere",
  "prompt_file": "prompt.txt",
  "transcript": "a3d9262261796034b.output",
  "model": "claude-opus-5-5",
  "metrics": {
    "tool_calls": 69,
    "wall_seconds": 973.6
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
#18 cli-prompt: copilot $c
#20 cli-prompt: copilot $c /dev/null
#21 cli-prompt: copilot $c /dev/null
#30 sourced-unknown: $T/v1/server/run.sh
#64 sourced-unknown: $T/bin/claude_run_cfg.sh
```

DISCARDED: call #46 runs a Python helper that launches `copilot --acp`, which step 5 forbids because COPILOT_HOME does not isolate Copilot's sign-in; calls #20 and #21 also run `copilot lsp`, `copilot instruction`, and `copilot instruction list`, outside the literal allowlist (the flagged #18 loops only over `mcp`, `skill`, and help, which are allowed). The executor verified these calls; the run was not otherwise read in full and not scored.

## Score

Not scored: this run was discarded (see Isolation). It is kept so any observation drawn from it can be audited; it is not evidence for the arm's score.

## Final report

review-kit now installs in Codex CLI and GitHub Copilot CLI, and Claude Code still sees the same plugin as before. Nothing is committed; the changes are in the working tree at `$RUN/repo`.

**Before the change:** both Codex and Copilot already accepted the repo as a marketplace and installed the plugin, but the review MCP server was broken in each.
- **Codex** does not expand `${CLAUDE_PLUGIN_ROOT}`, so the server failed with "No such file or directory".
- **Copilot** started the server, but passed it the literal text `${user_config.api_key}` as the API key.
- Neither tool has an equivalent of Claude's `userConfig`, the install-time setting Claude uses to ask for the key.

**What I changed:** each tool now gets its own manifest and MCP config, and Claude's files behave as before.
- **Claude Code:** the MCP config moved from the root `.mcp.json` into `mcpServers` in `.claude-plugin/plugin.json`, and `.mcp.json` is deleted. This was necessary because Copilot always reads a root `.mcp.json` ahead of its own config. Copilot and Claude Code also treat that file as project config when you work inside this repo.
- **Codex:** added `.codex-plugin/plugin.json` and `.codex-mcp.json`, which runs `./server/run.sh` with `"cwd": "."` and `"env_vars": ["REVIEW_API_KEY"]`. Codex expands no placeholders, but it resolves a relative `cwd` against the plugin directory.
- **Copilot:** added `.github/plugin/plugin.json` and `.copilot-mcp.json`, which uses `${PLUGIN_ROOT}/server/run.sh`. I avoided `.github/mcp.json` because Copilot also reads that as project config.
- **Drift check:** there are now three manifests, so I added `tools/check-manifests.py`. It fails when their name, version, description, author or MCP server names differ from the Claude manifest. It passed on the real tree and failed on a copy where I changed a version and renamed a server.
- **README:** now covers installing in each tool, the API key, and the table below.

## What works in each tool

| Part | Claude Code | Codex CLI 0.157.1 | Copilot CLI 1.0.86 |
|---|---|---|---|
| `/review` command | Yes, unchanged | Tested: becomes a skill, `review-kit:source-command-review`, with no slash command | Tested: `/review-kit:review`. Plain `/review` is Copilot's own review command |
| `reviewer` agent | Yes, unchanged | No: Codex plugins don't load agents | From the docs only; I couldn't test it |
| `SessionStart` hook | Yes, unchanged | Tested: loaded, but skipped until the user reviews and trusts it. Its text output reaches the model | From the docs only: it should run, but Copilot ignores plain-text output, so "review-kit ready" never reaches the model |
| `review` MCP server | Tested: starts and receives the key | Tested: starts and receives the key | Tested: starts and receives the key |
| API key | Asked for at install, as before | User must export `REVIEW_API_KEY` | User must export `REVIEW_API_KEY` |
| Server's working directory | Session directory | Plugin install directory | Plugin install directory |

I didn't change the hook to make its output visible in Copilot, because that would change what Claude receives and I couldn't test a Claude session.

## How I checked it

Everything ran on copies of the repo, with each tool's configuration in throwaway folders under `.tool-homes/`. A stand-in server recorded the key, arguments and working directory it was started with. No prompt went to any model or agent.
- **Claude Code:** `claude plugin validate`, install, `claude plugin details` and `claude mcp list` show the same parts before and after (1 skill, the `reviewer` agent, the `SessionStart` hook, the `review` server), and the server connects. To check the key without touching the real keychain, I made the key non-sensitive in a copy. It reached the server both from the old `.mcp.json` and from the new manifest.
- **Codex:** `codex app-server` requests without starting a turn, covering the plugin, its hooks, its skills and MCP status.
- **Copilot:** `copilot --acp` in offline mode with no model reachable, stopping after session creation. I also read `copilot mcp list --json`.

## Not verified
- **Copilot hooks and agents.** A hook that Copilot's docs say should fire at session start didn't fire in my setup either, so this test can't detect hooks. There was also no way to list agents without sending a prompt.
- **Hook execution in Claude Code and Codex.** I checked that each tool loads the hook, not that it runs in a live session.
- **The real server.** `server/run.sh` runs `python3 -m review_server`, which isn't in this repo, so all three tools need it installed separately. In Codex and Copilot it starts in the plugin directory, not your project. If it expects your project as its working directory, it will break there.

I added `.tool-homes/` to `.git/info/exclude`; the throwaway folders are still there.

## Tool calls

The arm's tool calls, one JSON object per line, extracted from its transcript.

```jsonl
{"tool": "Bash", "input": {"command": "cd $RUN/repo && git status && git log --oneline | head && find . -path ./.git -prune -o -type f -print | head -100", "description": "Inspect repo layout"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && for f in .mcp.json README.md agents/reviewer.md server/run.sh hooks/hooks.json scripts/start.sh .claude-plugin/marketplace.json .claude-plugin/plugin.json commands/review.md; do echo \"=== $f\"; cat \"$f\"; done; ls -la server scripts; which codex copilot claude", "description": "Print all repo files"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=$PWD/.tool-homes; mkdir -p $T/codex $T/copilot $T/home; grep -q tool-homes .git/info/exclude || echo \".tool-homes/\" >> .git/info/exclude\nexport HOME=$T/home XDG_CONFIG_HOME=$T/home/.config CODEX_HOME=$T/codex COPILOT_HOME=$T/copilot\ncodex --version; codex plugin --help 2>&1 | head -40; echo ----; copilot --version; copilot plugin --help 2>&1 | head -40", "description": "Check CLI versions and plugin help with isolated homes"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=$PWD/.tool-homes\nexport HOME=$T/home XDG_CONFIG_HOME=$T/home/.config CODEX_HOME=$T/codex COPILOT_HOME=$T/copilot\ncodex plugin marketplace --help; codex plugin marketplace add --help; codex plugin add --help; echo ====; copilot plugin install --help; copilot plugin marketplace add --help", "description": "Read subcommand help for both CLIs"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=$PWD/.tool-homes\nexport HOME=$T/home XDG_CONFIG_HOME=$T/home/.config CODEX_HOME=$T/codex COPILOT_HOME=$T/copilot\nrm -rf $T/base && mkdir -p $T/base && git archive HEAD | tar -x -C $T/base\necho \"--- codex\"; codex plugin marketplace add $T/base --json 2>&1; codex plugin list 2>&1 | head -20\necho \"--- copilot\"; copilot plugin install --help 2>&1 | head -30", "description": "Baseline Codex install probe on unmodified copy"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=$PWD/.tool-homes\nexport HOME=$T/home XDG_CONFIG_HOME=$T/home/.config CODEX_HOME=$T/codex COPILOT_HOME=$T/copilot\ncodex plugin add review-kit@review-kit --json 2>&1; echo \"exit $?\"; find $T/codex -type f | grep -v sqlite | head -30; cat $T/codex/config.toml", "description": "Install baseline plugin in Codex"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=$PWD/.tool-homes\nexport HOME=$T/home XDG_CONFIG_HOME=$T/home/.config CODEX_HOME=$T/codex COPILOT_HOME=$T/copilot\ncat $T/codex/plugins/cache/review-kit/review-kit/2.0.0/.codex-plugin/migrated-command-skills/source-command-review/SKILL.md; echo; codex mcp list 2>&1; codex --help | head -40; codex debug --help 2>&1 | head -30", "description": "Inspect Codex migrated skill and MCP list"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=$PWD/.tool-homes\nexport HOME=$T/home XDG_CONFIG_HOME=$T/home/.config CODEX_HOME=$T/codex COPILOT_HOME=$T/copilot\ncodex mcp get review --json 2>&1; codex debug prompt-input --help 2>&1 | sed -n 1,20p; cd $T && codex debug prompt-input \"hi\" > $T/prompt-base.json 2>&1; echo \"exit $?\"; wc -c $T/prompt-base.json; grep -o 'review[-a-z:]*' $T/prompt-base.json | sort | uniq -c", "description": "Check Codex MCP config and rendered prompt input"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo/.tool-homes && python3 -c \"\nimport json;d=json.load(open('prompt-base.json'))\nfor it in d:\n  for c in it.get('content',[]) if isinstance(it.get('content'),list) else []:\n    t=c.get('text','')\n    if 'skill' in t.lower() or 'plugin' in t.lower() or 'review' in t.lower(): print('-----',it.get('role'));print(t[:6000])\n\"", "description": "Show skill and plugin sections of Codex prompt"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=$PWD/.tool-homes\nexport HOME=$T/home XDG_CONFIG_HOME=$T/home/.config CODEX_HOME=$T/codex COPILOT_HOME=$T/copilot\ncodex features list 2>&1 | grep -iE 'hook|plugin|agent|mcp|skill'", "description": "List relevant Codex feature flags"}}
{"tool": "ToolSearch", "input": {"query": "select:WebFetch,WebSearch", "max_results": 2}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo/.tool-homes && mkdir -p docs && curl -sL -o docs/codex-plugins-build.html https://developers.openai.com/codex/plugins/build; curl -sL -o docs/codex-hooks.html https://developers.openai.com/codex/hooks; curl -sL -o docs/copilot-plugins.html https://docs.github.com/en/copilot/reference/cli-plugin-reference; ls -la docs; for f in docs/*.html; do python3 -c \"\nimport re,sys,html;t=open('$f',errors='ignore').read();t=re.sub(r'<script.*?</script>|<style.*?</style>','',t,flags=re.S);t=html.unescape(re.sub(r'<[^>]+>',' ',t));t=re.sub(r'\\s+',' ',t);open('$f.txt','w').write(t);print('$f',len(t))\"; done", "description": "Download Codex and Copilot plugin docs as text"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo/.tool-homes/docs && fold -w 200 codex-plugins-build.html.txt | grep -n -iE 'CLAUDE_PLUGIN|PLUGIN_ROOT|claude-plugin|hooks|mcp|agents|commands|user_config|userConfig|\\$\\{' | head -80", "description": "Grep Codex plugin doc for compatibility details"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo/.tool-homes/docs && fold -w 200 codex-plugins-build.html.txt | sed -n '57,66p;84,100p;108,146p;150,172p;184,215p'", "description": "Read relevant Codex plugin doc sections"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo/.tool-homes/docs && python3 - <<'E'\nt=open('copilot-plugins.html.txt').read()\ni=t.find('CLI plugin reference',2000)\nimport textwrap\ns=t[t.find('plugin.json'):]\nprint(textwrap.fill(t[max(0,t.find('plugin.json')-3000):][:30000],200))\nE", "description": "Read Copilot CLI plugin reference text"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo/.tool-homes/docs && python3 - <<'E'\nimport textwrap\nt=open('copilot-plugins.html.txt').read()\ni=t.find('CLI plugin reference Copy')\nif i<0: i=t.rfind('CLI plugin reference',0,len(t)//2+20000)\nprint(i)\nprint(textwrap.fill(t[i:i+22000],200))\nE", "description": "Print Copilot plugin reference body"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo/.tool-homes/docs && python3 - <<'E'\nimport textwrap\nt=open('copilot-plugins.html.txt').read()\ni=t.find('Agents Legacy plugins: agents/')\nprint(textwrap.fill(t[i:i+7000],200))\nE", "description": "Print rest of Copilot plugin reference"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=$PWD/.tool-homes\nexport HOME=$T/home XDG_CONFIG_HOME=$T/home/.config CODEX_HOME=$T/codex COPILOT_HOME=$T/copilot COPILOT_CACHE_HOME=$T/copilot-cache COPILOT_AUTO_UPDATE=false\ncopilot plugin marketplace add $T/base 2>&1; copilot plugin install review-kit@review-kit 2>&1; copilot plugin list 2>&1; copilot --help | grep -E '^\\s+(mcp|skill|agent|hook|instruction|plugin|lsp)' ; find $T/copilot -maxdepth 4 | head -30", "description": "Baseline Copilot marketplace install probe"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=$PWD/.tool-homes\nexport HOME=$T/home XDG_CONFIG_HOME=$T/home/.config CODEX_HOME=$T/codex COPILOT_HOME=$T/copilot COPILOT_CACHE_HOME=$T/copilot-cache COPILOT_AUTO_UPDATE=false\ncd $T; for c in \"mcp list\" \"mcp list --json\" \"skill list\" \"instruction --help\" \"mcp --help\" \"skill --help\"; do echo \"### copilot $c\"; copilot $c 2>&1 | head -40; done", "description": "List Copilot MCP servers and skills from plugin"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=$PWD/.tool-homes\nexport HOME=$T/home XDG_CONFIG_HOME=$T/home/.config COPILOT_HOME=$T/copilot COPILOT_CACHE_HOME=$T/copilot-cache COPILOT_AUTO_UPDATE=false\ncopilot --help 2>&1 | sed -n '/Commands/,$p' | head -40; copilot help mcp 2>&1 | head -30", "description": "Inspect Copilot command help"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=$PWD/.tool-homes\nexport HOME=$T/home XDG_CONFIG_HOME=$T/home/.config COPILOT_HOME=$T/copilot COPILOT_CACHE_HOME=$T/copilot-cache COPILOT_AUTO_UPDATE=false\nfor c in mcp skill lsp instruction; do echo \"## $c\"; copilot $c < /dev/null 2>&1 | head -25; done; echo \"## plugin list json\"; copilot plugin list --json; tail -30 $(ls -t $T/copilot/logs/*.log | head -1)", "description": "Try Copilot resource subcommands"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=$PWD/.tool-homes\nexport HOME=$T/home XDG_CONFIG_HOME=$T/home/.config COPILOT_HOME=$T/copilot COPILOT_CACHE_HOME=$T/copilot-cache COPILOT_AUTO_UPDATE=false\ncd $T/home; for c in \"mcp list\" \"mcp get review\" \"skill list\" \"instruction list\"; do echo \"## $c\"; copilot $c < /dev/null 2>&1 | head -40; done; copilot mcp list --help </dev/null; copilot skill list --help </dev/null", "description": "List Copilot MCP servers and skills with stdin closed"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=$PWD/.tool-homes\nexport HOME=$T/home XDG_CONFIG_HOME=$T/home/.config COPILOT_HOME=$T/copilot COPILOT_CACHE_HOME=$T/copilot-cache COPILOT_AUTO_UPDATE=false\ncopilot mcp list --json </dev/null; ls -t $T/copilot/logs/*.log | head -1 | xargs cat | grep -viE 'managedSettings' | tail -20", "description": "Check Copilot log for mcp list failure"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=$PWD/.tool-homes\nexport HOME=$T/home XDG_CONFIG_HOME=$T/home/.config CODEX_HOME=$T/codex\ncodex app-server --help 2>&1 | head -30; codex app-server generate-json-schema --out $T/codex-schema 2>&1 | tail -2; ls $T/codex-schema | head; grep -rlo -i 'mcpServerStatus\\|mcpServer' $T/codex-schema | head", "description": "Explore Codex app-server schema"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo/.tool-homes && python3 -c \"\nimport json;d=json.load(open('codex-schema/ClientRequest.json'))\nfor o in d.get('oneOf',[]):\n  m=o['properties']['method'].get('enum',[None])[0]; print(m)\n\" | grep -iE 'mcp|plugin|hook|skill|init|thread/start|agent'; ls codex-schema/v2 | grep -iE 'mcp|hook|plugin' ", "description": "List app-server methods related to MCP, hooks, plugins"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo/.tool-homes/codex-schema && for f in v2/HooksListParams.json v2/ListMcpServerStatusParams.json v2/PluginReadParams.json v1/InitializeParams.json; do echo \"== $f\"; python3 -c \"import json;d=json.load(open('$f'));print(json.dumps({k:d.get(k) for k in ('properties','required')})[:1500])\"; done", "description": "Read app-server parameter schemas"}}
{"tool": "Bash", "input": {"command": "mkdir -p $RUN/repo/.tool-homes/bin && cat > $RUN/repo/.tool-homes/bin/codex_probe.py <<'E'\n\"\"\"Drive `codex app-server` over stdio: no turns are started, so no prompt reaches a model.\"\"\"\nimport json, subprocess, sys, threading, queue, time\nmp = sys.argv[1]  # marketplace root\ncwd = sys.argv[2] if len(sys.argv) > 2 else mp\np = subprocess.Popen([\"codex\", \"app-server\"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=cwd)\nq = queue.Queue()\nthreading.Thread(target=lambda: [q.put(l) for l in p.stdout], daemon=True).start()\nn = [0]\ndef call(method, params, wait=20):\n    n[0] += 1; i = n[0]\n    p.stdin.write(json.dumps({\"id\": i, \"method\": method, \"params\": params}) + \"\\n\"); p.stdin.flush()\n    end = time.time() + wait\n    while time.time() < end:\n        try: l = q.get(timeout=0.5)\n        except queue.Empty: continue\n        m = json.loads(l)\n        if m.get(\"id\") == i and \"method\" not in m: return m\n        if \"method\" in m and \"mcp\" in m[\"method\"].lower(): print(\"NOTIFY\", json.dumps(m)[:600])\n    return {\"timeout\": method}\ncall(\"initialize\", {\"clientInfo\": {\"name\": \"probe\", \"version\": \"0\"}})\np.stdin.write(json.dumps({\"method\": \"initialized\"}) + \"\\n\"); p.stdin.flush()\nfor m, a in [(\"plugin/read\", {\"pluginName\": \"review-kit\", \"marketplacePath\": mp + \"/\" + sys.argv[3]}),\n             (\"hooks/list\", {\"cwds\": [cwd]}),\n             (\"skills/list\", {\"cwds\": [cwd]}),\n             (\"mcpServerStatus/list\", {})]:\n    r = call(m, a, 40)\n    print(\"=====\", m); print(json.dumps(r, indent=1)[:6000])\np.kill()\nE\ncd $RUN/repo && T=$PWD/.tool-homes\nexport HOME=$T/home XDG_CONFIG_HOME=$T/home/.config CODEX_HOME=$T/codex\npython3 $T/bin/codex_probe.py $T/base $T/home .claude-plugin/marketplace.json 2>&1 | head -300", "description": "Probe Codex app-server for plugin, hooks, skills, MCP status"}}
{"tool": "Bash", "input": {"command": "cat > $RUN/repo/.tool-homes/bin/stub_server.py <<'E'\n\"\"\"Minimal MCP stdio server for probing: reports what it was launched with as tool names.\"\"\"\nimport json, os, sys, re\ndef clean(s): return re.sub(r'[^A-Za-z0-9_-]', '_', s)[-60:]\ninfo = {\"key\": os.environ.get(\"REVIEW_API_KEY\", \"<unset>\"), \"root\": os.environ.get(\"PLUGIN_ROOT\", \"<unset>\"), \"croot\": os.environ.get(\"CLAUDE_PLUGIN_ROOT\", \"<unset>\"), \"argv\": \" \".join(sys.argv[1:]), \"cwd\": os.getcwd()}\ntools = [{\"name\": clean(f\"{k}={v}\"), \"description\": f\"{k}={v}\", \"inputSchema\": {\"type\": \"object\"}} for k, v in info.items()]\nfor line in sys.stdin:\n    m = json.loads(line)\n    if \"id\" not in m: continue\n    if m[\"method\"] == \"initialize\":\n        r = {\"protocolVersion\": m[\"params\"][\"protocolVersion\"], \"capabilities\": {\"tools\": {}}, \"serverInfo\": {\"name\": \"stub\", \"version\": \"0\"}}\n    elif m[\"method\"] == \"tools/list\": r = {\"tools\": tools}\n    else: r = {}\n    print(json.dumps({\"jsonrpc\": \"2.0\", \"id\": m[\"id\"], \"result\": r}), flush=True)\nE\necho ok", "description": "Write stub MCP server for probing launches"}}
{"tool": "Bash", "input": {"command": "cat > $RUN/repo/.tool-homes/bin/codex_variant.sh <<'E'\n#!/bin/sh\n# usage: codex_variant.sh <variant-dir>  (installs the variant into a fresh CODEX_HOME and probes it)\nset -e\nT=$RUN/repo/.tool-homes\nV=$1; N=$(basename $V)\nexport HOME=$T/home XDG_CONFIG_HOME=$T/home/.config CODEX_HOME=$T/codex-$N REVIEW_API_KEY=${REVIEW_API_KEY-}\nrm -rf $CODEX_HOME; mkdir -p $CODEX_HOME\ncodex plugin marketplace add $V >/dev/null\ncodex plugin add review-kit@review-kit >/dev/null\nMP=$(ls $V/.agents/plugins/marketplace.json 2>/dev/null && echo .agents/plugins/marketplace.json || echo .claude-plugin/marketplace.json)\npython3 $T/bin/codex_probe.py $V $T/home $(echo \"$MP\" | tail -1) | python3 -c \"\nimport sys,json,re\ntxt=sys.stdin.read()\nfor blk in txt.split('===== ')[1:]:\n    name,body=blk.split('\\n',1)\n    try: r=json.loads(body)['result']\n    except Exception: print(name,'UNPARSED',body[:300]); continue\n    if name=='plugin/read': p=r['plugin']; print('plugin/read skills=',[s.get('name') for s in p['skills']],'hooks=',[h['key'] for h in p['hooks']],'mcp=',p['mcpServers'])\n    if name=='hooks/list': print('hooks=',[(h['key'],h['command'],h['trustStatus']) for d in r['data'] for h in d['hooks']], [d['errors'] or d['warnings'] for d in r['data']])\n    if name=='skills/list': print('plugin skills=',[s['name'] for d in r['data'] for s in d['skills'] if s.get('pluginId')], [d.get('errors') for d in r['data']])\n    if name=='mcpServerStatus/list':\n        for s in r['data']: print('mcp',s['name'],'err=',s['toolsError'],'tools=',sorted(t.get('description','') for t in s['tools'].values()) if isinstance(s['tools'],dict) else s['tools'])\n\"\nE\nchmod +x $RUN/repo/.tool-homes/bin/codex_variant.sh\ncd $RUN/repo && T=$PWD/.tool-homes\nmk(){ rm -rf $T/$1; mkdir -p $T/$1; git archive HEAD | tar -x -C $T/$1; printf '#!/bin/sh\\nexec python3 %s \"$@\"\\n' $T/bin/stub_server.py > $T/$1/server/run.sh; }\nmk v0; REVIEW_API_KEY=sekrit $T/bin/codex_variant.sh $T/v0", "description": "Probe baseline with stub server in Codex"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=$PWD/.tool-homes\nsed -i '' 's/indent=1)\\[:6000\\]/indent=1)/' $T/bin/codex_probe.py\nmk(){ rm -rf $T/$1; mkdir -p $T/$1; git archive HEAD | tar -x -C $T/$1; printf '#!/bin/sh\\nexec python3 %s \"$@\"\\n' $T/bin/stub_server.py > $T/$1/server/run.sh; }\n# v1: legacy codex overlay with separate MCP file; test several launch forms at once\nmk v1; mkdir -p $T/v1/.codex-plugin\ncat > $T/v1/.codex-plugin/plugin.json <<'E'\n{\"name\":\"review-kit\",\"version\":\"2.0.0\",\"description\":\"Code review helpers\",\"mcpServers\":\"./.codex-mcp.json\"}\nE\ncat > $T/v1/.codex-mcp.json <<'E'\n{\"mcpServers\":{\n \"a_cmd_croot\":{\"command\":\"${CLAUDE_PLUGIN_ROOT}/server/run.sh\"},\n \"b_cmd_root\":{\"command\":\"${PLUGIN_ROOT}/server/run.sh\"},\n \"c_sh_args_root\":{\"command\":\"sh\",\"args\":[\"${PLUGIN_ROOT}/server/run.sh\",\"argroot\"],\"env_vars\":[\"REVIEW_API_KEY\"]},\n \"d_sh_args_croot\":{\"command\":\"sh\",\"args\":[\"${CLAUDE_PLUGIN_ROOT}/server/run.sh\"]},\n \"e_relative\":{\"command\":\"./server/run.sh\"},\n \"f_env_expand\":{\"command\":\"sh\",\"args\":[\"${PLUGIN_ROOT}/server/run.sh\"],\"env\":{\"REVIEW_API_KEY\":\"${REVIEW_API_KEY}\"}}\n}}\nE\nREVIEW_API_KEY=sekrit $T/bin/codex_variant.sh $T/v1", "description": "Probe Codex MCP launch forms via overlay manifest"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=$PWD/.tool-homes\nprintf '%s\\n' '{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"initialize\",\"params\":{\"protocolVersion\":\"2025-06-18\"}}' '{\"jsonrpc\":\"2.0\",\"id\":2,\"method\":\"tools/list\"}' | REVIEW_API_KEY=x sh $T/v1/server/run.sh a b | head -c 600; echo\nL=$T/diag.log; rm -f $L\ncat > $T/v1/.codex-mcp.json <<E\n{\"mcpServers\":{\n \"g_diag\":{\"command\":\"sh\",\"args\":[\"-c\",\"echo \\\"pwd=\\$PWD PR=\\$PLUGIN_ROOT CPR=\\$CLAUDE_PLUGIN_ROOT KEY=\\$REVIEW_API_KEY a1=\\$0 a2=\\$1\\\" >> $L\",\"\\${PLUGIN_ROOT}/x\",\"\\${CLAUDE_PLUGIN_ROOT}/y\"],\"env_vars\":[\"REVIEW_API_KEY\"]},\n \"h_diag_env\":{\"command\":\"sh\",\"args\":[\"-c\",\"echo \\\"h: KEY=\\$REVIEW_API_KEY\\\" >> $L\"],\"env\":{\"REVIEW_API_KEY\":\"\\${REVIEW_API_KEY}\"}},\n \"i_diag_none\":{\"command\":\"sh\",\"args\":[\"-c\",\"echo \\\"i: KEY=\\$REVIEW_API_KEY\\\" >> $L\"]}\n}}\nE\ncat $T/v1/.codex-mcp.json; REVIEW_API_KEY=sekrit $T/bin/codex_variant.sh $T/v1 >/dev/null; cat $L", "description": "Diagnose Codex MCP env, cwd, and arg expansion"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=$PWD/.tool-homes\nL=$T/diag.log; rm -f $L\ncat > $T/v1/.codex-mcp.json <<E\n{\"mcpServers\":{\n \"j_cwd_dot\":{\"command\":\"sh\",\"args\":[\"-c\",\"echo \\\"j: pwd=\\$PWD\\\" >> $L\"],\"cwd\":\".\"},\n \"k_cwd_rel\":{\"command\":\"sh\",\"args\":[\"-c\",\"echo \\\"k: pwd=\\$PWD\\\" >> $L\"],\"cwd\":\"./server\"},\n \"l_rel_cmd_cwd\":{\"command\":\"./server/run.sh\",\"cwd\":\".\",\"env_vars\":[\"REVIEW_API_KEY\"]},\n \"m_sh_rel_cwd\":{\"command\":\"sh\",\"args\":[\"./server/run.sh\"],\"cwd\":\".\",\"env_vars\":[\"REVIEW_API_KEY\"]}\n}}\nE\nREVIEW_API_KEY=sekrit $T/bin/codex_variant.sh $T/v1 | grep '^mcp'; cat $L", "description": "Test Codex MCP cwd resolution relative to plugin"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=$PWD/.tool-homes\nexport HOME=$T/home XDG_CONFIG_HOME=$T/home/.config COPILOT_HOME=$T/copilot COPILOT_CACHE_HOME=$T/copilot-cache COPILOT_AUTO_UPDATE=false\ncopilot --help </dev/null | grep -iE -A2 'acp|plugin-dir|server|additional-mcp|headless|stdio' | head -40\nfold -w 200 $T/docs/codex-hooks.html.txt | grep -n -iE 'SessionStart|stdout|additionalContext' | head -15", "description": "Find Copilot server modes and Codex hook stdout semantics"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo/.tool-homes && fold -w 200 docs/codex-hooks.html.txt | sed -n '155,175p' | grep -i -B1 -A3 'plain text\\|SessionStart' | head -30", "description": "Read Codex SessionStart output semantics"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=$PWD/.tool-homes\nexport HOME=$T/home XDG_CONFIG_HOME=$T/home/.config COPILOT_HOME=$T/copilot COPILOT_CACHE_HOME=$T/copilot-cache COPILOT_AUTO_UPDATE=false\ncd $T/home; copilot skill list --json </dev/null | head -60; copilot --help </dev/null | grep -iE -- '--(acp|server|headless|agent)' ", "description": "List Copilot skills from baseline plugin"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo/.tool-homes/copilot-cache && du -sh pkg; ls pkg/darwin-arm64/1.0.86 | head; grep -rl 'CLAUDE_PLUGIN_ROOT' pkg | head", "description": "Locate Copilot runtime code referencing plugin root"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo/.tool-homes/copilot-cache/pkg/darwin-arm64/1.0.86 && python3 - <<'E'\nimport json\nc=json.load(open('changelog.json'))\ns=json.dumps(c)\nimport re\nitems=re.findall(r'\"([^\"]{0,400}(?:CLAUDE_PLUGIN_ROOT|PLUGIN_ROOT|Claude Code (?:plugin|hook)|hooks\\.json|user_config|userConfig|\\.agent\\.md)[^\"]{0,300})\"',s)\nfor i in items[:40]: print('-',i)\nE", "description": "Search Copilot changelog for plugin compatibility notes"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo/.tool-homes/copilot-cache/pkg/darwin-arm64/1.0.86 && python3 - <<'E'\nimport json,re\ns=json.dumps(json.load(open('changelog.json')))\nfor pat in [r'MCP[^\"]{0,200}plugin|plugin[^\"]{0,200}MCP', r'[Hh]ook[^\"]{0,200}(Claude|PascalCase|SessionStart|sessionStart|format)', r'agents?/[^\"]{0,150}\\.md|\\.md[^\"]{0,100}agent', r'env(ironment)? var[^\"]{0,150}(expan|\\$\\{)|\\$\\{[A-Z_]+\\}[^\"]{0,150}']:\n  print('##',pat)\n  for i in sorted(set(re.findall(r'\"([^\"]*(?:'+pat+r')[^\"]*)\"',s)))[:25]: print('-',i[:300] if isinstance(i,str) else i)\nE", "description": "Search Copilot changelog for MCP, hooks, agents notes"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=$PWD/.tool-homes\nexport HOME=$T/home XDG_CONFIG_HOME=$T/home/.config COPILOT_HOME=$T/copilot COPILOT_CACHE_HOME=$T/copilot-cache COPILOT_AUTO_UPDATE=false\ncopilot --help </dev/null | grep -B4 -A2 'MCP server environments'; copilot help environment </dev/null | grep -iE -B2 -A4 'mcp|plugin' | head -60; copilot help config </dev/null | grep -iE -B2 -A6 'mcp|env' | head -60", "description": "Read Copilot help on MCP env handling"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=$PWD/.tool-homes\npython3 - <<E\np='$T/bin/stub_server.py'\ns=open(p).read()\ns=s.replace('tools = [', 'open(\"$T/diag.log\",\"a\").write(\"STUB \" + json.dumps(info) + \"\\\\\\\\n\")\\ntools = [',1)\nopen(p,'w').write(s)\nE\ngrep -n 'STUB' $T/bin/stub_server.py\ncat > $T/bin/copilot_probe.py <<'E'\n\"\"\"Start an interactive Copilot session in a PTY, offline, with no model reachable; send no prompt; kill after N s.\"\"\"\nimport os, pty, sys, time, select, signal\nT = \"$RUN/repo/.tool-homes\"\nhome = sys.argv[1]; cwd = sys.argv[2]; extra = sys.argv[3:]\nenv = {k: v for k, v in os.environ.items() if not k.startswith((\"GH_\", \"GITHUB_\", \"COPILOT_\"))}\nenv.update(HOME=f\"{T}/home\", XDG_CONFIG_HOME=f\"{T}/home/.config\", COPILOT_HOME=home, COPILOT_CACHE_HOME=f\"{T}/copilot-cache\",\n           COPILOT_AUTO_UPDATE=\"false\", COPILOT_OFFLINE=\"true\", COPILOT_PROVIDER_BASE_URL=\"http://127.0.0.1:9/v1\",\n           COPILOT_MODEL=\"probe-none\", TERM=\"xterm-256color\")\npid, fd = pty.fork()\nif pid == 0:\n    os.chdir(cwd); os.execvpe(\"copilot\", [\"copilot\", *extra], env)\nout = b\"\"; end = time.time() + float(os.environ.get(\"WAIT\", \"20\"))\nwhile time.time() < end:\n    r, _, _ = select.select([fd], [], [], 0.5)\n    if r:\n        try: out += os.read(fd, 65536)\n        except OSError: break\nos.kill(pid, signal.SIGKILL)\nopen(f\"{T}/copilot-screen.txt\", \"wb\").write(out)\nimport re\nprint(re.sub(rb'\\x1b\\[[0-9;?]*[a-zA-Z]|\\x1b\\][^\\x07]*\\x07', b'', out).decode(errors='ignore')[-3000:])\nE\necho written", "description": "Write offline Copilot PTY probe and add launch logging to stub"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=$PWD/.tool-homes\nrm -f $T/diag.log; mkdir -p $T/ws $T/cp-v0; WAIT=15 python3 $T/bin/copilot_probe.py $T/cp-v0 $T/ws --plugin-dir $T/v0 2>&1 | tail -40; echo ---; cat $T/diag.log 2>&1", "description": "Run offline Copilot session probe on baseline"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=$PWD/.tool-homes\npython3 - <<E\np='$T/bin/copilot_probe.py'\ns=open(p).read()\ns=s.replace('out = b\"\"; end','sent = False; t0 = time.time()\\nout = b\"\"; end')\ns=s.replace('    r, _, _ = select','    if not sent and os.environ.get(\"SEND\") and time.time() - t0 > float(os.environ.get(\"SEND_AT\", \"8\")):\\n        os.write(fd, os.environ[\"SEND\"].encode().decode(\"unicode_escape\").encode()); sent = True\\n    r, _, _ = select')\nopen(p,'w').write(s)\nE\nmk(){ rm -rf $T/$1; mkdir -p $T/$1; git archive HEAD | tar -x -C $T/$1; printf '#!/bin/sh\\nexec python3 %s \"$@\"\\n' $T/bin/stub_server.py > $T/$1/server/run.sh; printf '#!/bin/sh\\necho \"HOOK ran root=$CLAUDE_PLUGIN_ROOT\" >> %s\\necho review-kit ready\\n' $T/diag.log > $T/$1/scripts/start.sh; }\nmk v0; rm -rf $T/diag.log $T/cp-v0; mkdir -p $T/cp-v0\nSEND='/env\\r' WAIT=20 python3 $T/bin/copilot_probe.py $T/cp-v0 $T/ws --plugin-dir $T/v0 > $T/screen-v0.txt 2>&1; tail -c 2500 $T/screen-v0.txt; echo; echo ---; cat $T/diag.log", "description": "Probe Copilot with /env and hook logging"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo/.tool-homes && ls cp-v0 cp-v0/logs; cat cp-v0/logs/*.log | grep -viE 'managedSettings|telemetry' | cut -c1-300 | head -80", "description": "Read Copilot session log from probe"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo/.tool-homes && find cp-v0/session-state cp-v0/servers cp-v0/plugin-data -type f | head; cat cp-v0/config.json; for f in $(find cp-v0/session-state -type f | head -3); do echo \"== $f\"; head -c 3000 $f | tr -d '\\000' | grep -aoE '\"(type|name|agent[a-zA-Z]*|hook[a-zA-Z]*)\":[^,]{0,120}' | sort | uniq -c | head -40; done", "description": "Inspect Copilot session state for loaded components"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=$PWD/.tool-homes\nsed -i '' 's/TERM=\"xterm-256color\")/TERM=\"xterm-256color\")\\nif os.environ.get(\"PROBE_ALLOW_ALL\"): env[\"COPILOT_ALLOW_ALL\"] = \"true\"/' $T/bin/copilot_probe.py\nrm -rf $T/diag.log $T/cp-v0; mkdir -p $T/cp-v0\nPROBE_ALLOW_ALL=1 WAIT=15 python3 $T/bin/copilot_probe.py $T/cp-v0 $T/ws --plugin-dir $T/v0 > /dev/null 2>&1; cat $T/diag.log; grep -ihE 'hook|agent|trust' $T/cp-v0/logs/*.log | cut -c1-250 | head", "description": "Probe Copilot hooks with trusted directory"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=$PWD/.tool-homes\nmkdir -p $T/ws/.github/hooks; cd $T/ws && git init -q 2>/dev/null; cat > $T/ws/.github/hooks/probe.json <<E\n{\"version\":1,\"hooks\":{\"sessionStart\":[{\"type\":\"command\",\"bash\":\"echo NATIVE-REPO-HOOK >> $T/diag.log\"}],\n \"SessionStart\":[{\"hooks\":[{\"type\":\"command\",\"command\":\"echo CLAUDE-FMT-REPO-HOOK >> $T/diag.log\"}]}]}}\nE\nrm -rf $T/diag.log $T/cp-v0; mkdir -p $T/cp-v0\nPROBE_ALLOW_ALL=1 WAIT=15 python3 $T/bin/copilot_probe.py $T/cp-v0 $T/ws --plugin-dir $T/v0 > /dev/null 2>&1; cat $T/diag.log | cut -c1-80", "description": "Positive control for Copilot hook firing"}}
{"tool": "Bash", "input": {"command": "cat > $RUN/repo/.tool-homes/bin/copilot_acp.py <<'E'\n\"\"\"Copilot in ACP mode, offline: initialize + session/new only (no session/prompt, so nothing reaches a model).\"\"\"\nimport json, os, subprocess, sys, time, threading, queue\nT = \"$RUN/repo/.tool-homes\"\nhome, cwd, *extra = sys.argv[1:]\nenv = {k: v for k, v in os.environ.items() if not k.startswith((\"GH_\", \"GITHUB_\", \"COPILOT_\"))}\nenv.update(HOME=f\"{T}/home\", XDG_CONFIG_HOME=f\"{T}/home/.config\", COPILOT_HOME=home, COPILOT_CACHE_HOME=f\"{T}/copilot-cache\",\n           COPILOT_AUTO_UPDATE=\"false\", COPILOT_OFFLINE=\"true\", COPILOT_PROVIDER_BASE_URL=\"http://127.0.0.1:9/v1\", COPILOT_MODEL=\"probe-none\",\n           REVIEW_API_KEY=os.environ.get(\"REVIEW_API_KEY\", \"\"))\nif os.environ.get(\"PROBE_ALLOW_ALL\"): env[\"COPILOT_ALLOW_ALL\"] = \"true\"\np = subprocess.Popen([\"copilot\", \"--acp\", *extra], cwd=cwd, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)\nq = queue.Queue(); threading.Thread(target=lambda: [q.put(l) for l in p.stdout], daemon=True).start()\ndef call(i, m, params, wait=20):\n    p.stdin.write(json.dumps({\"jsonrpc\": \"2.0\", \"id\": i, \"method\": m, \"params\": params}) + \"\\n\"); p.stdin.flush()\n    end = time.time() + wait\n    while time.time() < end:\n        try: msg = json.loads(q.get(timeout=0.5))\n        except queue.Empty: continue\n        if msg.get(\"id\") == i: return msg\n        print(\"NOTE\", json.dumps(msg)[:1500])\nprint(json.dumps(call(1, \"initialize\", {\"protocolVersion\": 1, \"clientCapabilities\": {}}))[:800])\nprint(json.dumps(call(2, \"session/new\", {\"cwd\": cwd, \"mcpServers\": []}))[:3000])\ntime.sleep(float(os.environ.get(\"WAIT\", \"6\")))\nwhile not q.empty(): print(\"NOTE\", q.get()[:1500])\np.kill()\nE\ncd $RUN/repo && T=$PWD/.tool-homes\nrm -rf $T/diag.log $T/cp-v0; mkdir -p $T/cp-v0\nPROBE_ALLOW_ALL=1 python3 $T/bin/copilot_acp.py $T/cp-v0 $T/ws --plugin-dir $T/v0 2>&1 | cut -c1-1500; echo ---; cut -c1-100 $T/diag.log", "description": "Probe Copilot via ACP session creation, offline"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=$PWD/.tool-homes\nrm -rf $T/cp-v0; mkdir -p $T/cp-v0\nPROBE_ALLOW_ALL=1 python3 $T/bin/copilot_acp.py $T/cp-v0 $T/ws --plugin-dir $T/v0 2>&1 | grep '^NOTE' | sed 's/^NOTE //' | python3 -c \"\nimport sys,json\nfor l in sys.stdin:\n  try: m=json.loads(l)\n  except: print('trunc',l[:100]); continue\n  u=m['params']['update']\n  if u.get('availableCommands'): print(sorted(c['name'] for c in u['availableCommands']))\n  else: print(json.dumps(u)[:400])\n\" | tail -3", "description": "List Copilot ACP available commands"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=$PWD/.tool-homes\nsed -i '' 's/print(\"NOTE\", json.dumps(msg)\\[:1500\\])/print(\"NOTE\", json.dumps(msg))/; s/print(\"NOTE\", q.get()\\[:1500\\])/print(\"NOTE\", q.get().strip())/' $T/bin/copilot_acp.py\nrm -rf $T/cp-v0; mkdir -p $T/cp-v0\nPROBE_ALLOW_ALL=1 python3 $T/bin/copilot_acp.py $T/cp-v0 $T/ws --plugin-dir $T/v0 2>&1 | grep '^NOTE' | sed 's/^NOTE //' | python3 -c \"\nimport sys,json\nfor l in sys.stdin:\n  m=json.loads(l); u=m['params']['update']\n  if u.get('availableCommands'): print(sorted(c['name'] for c in u['availableCommands']))\n  else: print(json.dumps(u)[:400])\n\" | tail -2", "description": "List Copilot ACP available commands untruncated"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=$PWD/.tool-homes\nfor a in review-kit:reviewer review-kit:nosuch; do rm -rf $T/cp-a; mkdir -p $T/cp-a; echo \"### $a\"; WAIT=3 python3 $T/bin/copilot_acp.py $T/cp-a $T/ws --plugin-dir $T/v0 --agent $a 2>&1 | grep -v '^NOTE' | cut -c1-300; grep -ihE 'agent' $T/cp-a/logs/*.log | grep -viE 'user-agent|sub-agent records' | cut -c1-300 | head -5; done", "description": "Probe Copilot agent resolution with control"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo/.tool-homes/docs && curl -sL -o cphooks.html https://docs.github.com/en/copilot/reference/hooks-configuration; curl -sL -o cpagents.html https://docs.github.com/en/copilot/reference/custom-agents-configuration; for f in cphooks cpagents; do python3 -c \"\nimport re,html;t=open('$f.html',errors='ignore').read();t=re.sub(r'<script.*?</script>|<style.*?</style>','',t,flags=re.S);t=html.unescape(re.sub(r'<[^>]+>',' ',t));t=re.sub(r'\\s+',' ',t);open('$f.txt','w').write(t);print('$f',len(t))\"; done; fold -w 200 cphooks.txt | grep -n -iE 'sessionStart|output is|ignored|additionalContext|PascalCase|Claude' | head -20", "description": "Fetch Copilot hooks and agents reference docs"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo/.tool-homes/docs && fold -w 200 cpagents.txt | grep -n -iE '\\.agent\\.md|\\.md |file name|filename|plugin|claude' | head -20; fold -w 200 cphooks.txt | sed -n '100,113p' | grep -i -E 'stdout|plain' | head", "description": "Check Copilot agent file naming rules"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=$PWD/.tool-homes\nmk(){ rm -rf $T/$1; mkdir -p $T/$1; git archive HEAD | tar -x -C $T/$1; printf '#!/bin/sh\\nexec python3 %s \"$@\"\\n' $T/bin/stub_server.py > $T/$1/server/run.sh; printf '#!/bin/sh\\necho \"HOOK ran root=$CLAUDE_PLUGIN_ROOT\" >> %s\\necho review-kit ready\\n' $T/diag.log > $T/$1/scripts/start.sh; }\nmk c1; mkdir -p $T/c1/.github/plugin\ncat > $T/c1/.github/plugin/plugin.json <<'E'\n{\"name\":\"review-kit\",\"version\":\"2.0.0\",\"description\":\"Code review helpers\",\"author\":{\"name\":\"Acme\"},\"mcpServers\":\"./.github/mcp.json\"}\nE\ncat > $T/c1/.github/mcp.json <<'E'\n{\"mcpServers\":{\n \"review\":{\"command\":\"${CLAUDE_PLUGIN_ROOT}/server/run.sh\",\"args\":[\"from-github-inherit\"]},\n \"review_b\":{\"command\":\"${CLAUDE_PLUGIN_ROOT}/server/run.sh\",\"args\":[\"from-github-expand\"],\"env\":{\"REVIEW_API_KEY\":\"${REVIEW_API_KEY}\"}}\n}}\nE\nrm -rf $T/diag.log $T/cp-c1; mkdir -p $T/cp-c1\nREVIEW_API_KEY=sekrit PROBE_ALLOW_ALL=1 WAIT=4 python3 $T/bin/copilot_acp.py $T/cp-c1 $T/ws --plugin-dir $T/c1 2>&1 | grep '^NOTE' | sed 's/^NOTE //' | python3 -c \"\nimport sys,json\nfor l in sys.stdin:\n  u=json.loads(l)['params']['update']\n  if u.get('availableCommands'): print([c['name'] for c in u['availableCommands'] if 'review' in c['name']])\n\" | tail -1; cat $T/diag.log | python3 -c \"\nimport sys,json\nfor l in sys.stdin:\n  if l.startswith('STUB'): d=json.loads(l[5:]); print('STUB argv=',d['argv'],'key=',d['key'],'cwd_is_root=',d['cwd']==d['root'])\n  else: print(l.strip())\"\ncd $T/home && env HOME=$T/home XDG_CONFIG_HOME=$T/home/.config COPILOT_HOME=$T/cp-c1 COPILOT_CACHE_HOME=$T/copilot-cache copilot mcp list --json </dev/null | head -5", "description": "Test Copilot-specific manifest and MCP env forms"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=$PWD/.tool-homes\ncat > $T/bin/cp_run.sh <<'E'\n#!/bin/sh\n# usage: cp_run.sh <plugin-dir>  -> prints plugin commands containing \"review\" and stub launches\nT=$RUN/repo/.tool-homes\nrm -rf $T/diag.log $T/cp-run; mkdir -p $T/cp-run\nREVIEW_API_KEY=sekrit PROBE_ALLOW_ALL=1 WAIT=4 python3 $T/bin/copilot_acp.py $T/cp-run $T/ws --plugin-dir $1 2>&1 | grep '^NOTE' | sed 's/^NOTE //' | python3 -c \"\nimport sys,json\nfor l in sys.stdin:\n  u=json.loads(l)['params']['update']\n  if u.get('availableCommands'): r=[c['name'] for c in u['availableCommands'] if 'review' in c['name']]\nprint('commands:',r)\"\n[ -f $T/diag.log ] && python3 -c \"\nimport sys,json\nfor l in open('$T/diag.log'):\n  if l.startswith('STUB'): d=json.loads(l[5:]); print('STUB argv=',repr(d['argv']),'key=',d['key'],'cwd_is_root=',d['cwd']==d['root'])\n  else: print(l.strip())\" || echo \"no MCP launch logged\"\nE\nchmod +x $T/bin/cp_run.sh\nsed -i '' 's/\"name\":\"review-kit\"/\"name\":\"review-kit-gh\"/' $T/c1/.github/plugin/plugin.json; $T/bin/cp_run.sh $T/c1", "description": "Check which manifest Copilot uses"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=$PWD/.tool-homes\ncat > $T/c1/.github/plugin/plugin.json <<'E'\n{\"name\":\"review-kit\",\"version\":\"2.0.0\",\"description\":\"Code review helpers\",\"author\":{\"name\":\"Acme\"},\"mcpServers\":{\n \"review\":{\"command\":\"${CLAUDE_PLUGIN_ROOT}/server/run.sh\",\"args\":[\"inline-inherit\"]},\n \"review_b\":{\"command\":\"${CLAUDE_PLUGIN_ROOT}/server/run.sh\",\"args\":[\"inline-expand\"],\"env\":{\"REVIEW_API_KEY\":\"${REVIEW_API_KEY}\"}}}}\nE\n$T/bin/cp_run.sh $T/c1; echo; echo \"--- same, without root .mcp.json\"; mv $T/c1/.mcp.json $T/c1/.mcp.json.off; $T/bin/cp_run.sh $T/c1; mv $T/c1/.mcp.json.off $T/c1/.mcp.json", "description": "Test inline mcpServers in Copilot manifest"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=$PWD/.tool-homes; mkdir -p $T/claude-home\nexport HOME=$T/home XDG_CONFIG_HOME=$T/home/.config CLAUDE_CONFIG_DIR=$T/claude-home CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1 DISABLE_AUTOUPDATER=1\nunset ANTHROPIC_API_KEY CLAUDE_CODE_OAUTH_TOKEN\nclaude --version </dev/null; claude plugin --help </dev/null 2>&1 | head -30; claude plugin validate $T/base </dev/null 2>&1", "description": "Check Claude Code plugin CLI with isolated config"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=$PWD/.tool-homes\nexport HOME=$T/home XDG_CONFIG_HOME=$T/home/.config CLAUDE_CONFIG_DIR=$T/claude-home CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1 DISABLE_AUTOUPDATER=1\nunset ANTHROPIC_API_KEY CLAUDE_CODE_OAUTH_TOKEN\nclaude plugin details --help </dev/null 2>&1 | head -20; claude plugin validate $T/base/.claude-plugin/plugin.json </dev/null 2>&1 | tail -3; claude mcp --help </dev/null | head -20", "description": "Read Claude plugin details and mcp help"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=$PWD/.tool-homes\ncat > $T/bin/claude_run.sh <<'E'\n#!/bin/sh\n# usage: claude_run.sh <marketplace-dir>: fresh isolated Claude config, install plugin, list plugin inventory + MCP health\nT=$RUN/repo/.tool-homes\nexport HOME=$T/home XDG_CONFIG_HOME=$T/home/.config CLAUDE_CONFIG_DIR=$T/claude-run CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1 DISABLE_AUTOUPDATER=1 REVIEW_API_KEY=sekrit\nunset ANTHROPIC_API_KEY CLAUDE_CODE_OAUTH_TOKEN\nrm -rf $CLAUDE_CONFIG_DIR $T/diag.log; mkdir -p $CLAUDE_CONFIG_DIR\ncd $T/ws\nclaude plugin validate $1 </dev/null 2>&1 | tail -2\nclaude plugin validate $1/.claude-plugin/plugin.json </dev/null 2>&1 | tail -2\nclaude plugin marketplace add $1 </dev/null 2>&1 | tail -1\nclaude plugin install review-kit@review-kit </dev/null 2>&1 | tail -2\nclaude plugin details review-kit@review-kit </dev/null 2>&1\nclaude mcp list </dev/null 2>&1 | tail -5\n[ -f $T/diag.log ] && python3 -c \"\nimport json\nfor l in open('$T/diag.log'):\n  if l.startswith('STUB'): d=json.loads(l[5:]); print('STUB argv=',repr(d['argv']),'key=',d['key'],'croot=',d['croot'][-40:],'cwd=',d['cwd'][-40:])\n  else: print(l.strip())\" || echo \"no MCP launch logged\"\nE\nchmod +x $T/bin/claude_run.sh; $T/bin/claude_run.sh $T/v0", "description": "Baseline Claude Code plugin inventory and MCP launch"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=$PWD/.tool-homes\nsed -i '' 's/claude mcp list <\\/dev\\/null 2>&1 | tail -5/claude mcp list <\\/dev\\/null 2>\\&1 | grep -v \"^$\"/' $T/bin/claude_run.sh; $T/bin/claude_run.sh $T/v0 2>&1 | sed -n '/Checking\\|plugin:\\|review/p' | grep -v 'Validation\\|Skills\\|reviewer\\|Source\\|marketplace\\|Installing\\|userConfig\\|^review-kit 2'", "description": "Show Claude MCP list for plugin server"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=$PWD/.tool-homes; grep -n 'mcp list' $T/bin/claude_run.sh; $T/bin/claude_run.sh $T/v0 2>&1 | tail -12", "description": "Show tail of Claude run output"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=$PWD/.tool-homes\nmk(){ rm -rf $T/$1; mkdir -p $T/$1; git archive HEAD | tar -x -C $T/$1; printf '#!/bin/sh\\nexec python3 %s \"$@\"\\n' $T/bin/stub_server.py > $T/$1/server/run.sh; printf '#!/bin/sh\\necho \"HOOK ran root=$CLAUDE_PLUGIN_ROOT\" >> %s\\necho review-kit ready\\n' $T/diag.log > $T/$1/scripts/start.sh; }\ninline(){ python3 - \"$1\" <<'E'\nimport json,sys\nd=sys.argv[1]; m=json.load(open(d+'/.claude-plugin/plugin.json')); mc=json.load(open(d+'/.mcp.json'))\nmc['mcpServers']['review']['args']=['claude-form']\nm['mcpServers']=mc['mcpServers']; json.dump(m,open(d+'/.claude-plugin/plugin.json','w'),indent=2)\nimport os; os.remove(d+'/.mcp.json')\nE\n}\nmk t1; inline $T/t1; mkdir -p $T/t1/.github; echo '{\"mcpServers\":{\"review\":{\"command\":\"${PLUGIN_ROOT}/server/run.sh\",\"args\":[\"github-mcp\"]}}}' > $T/t1/.github/mcp.json\necho \"## T1\"; $T/bin/cp_run.sh $T/t1\nmk t2; inline $T/t2; mkdir -p $T/t2/.github/plugin; echo '{\"mcpServers\":{\"review\":{\"command\":\"${PLUGIN_ROOT}/server/run.sh\",\"args\":[\"copilot-field\"]}}}' > $T/t2/.copilot-mcp.json\necho '{\"name\":\"review-kit\",\"version\":\"2.0.0\",\"description\":\"Code review helpers\",\"author\":{\"name\":\"Acme\"},\"mcpServers\":\"./.copilot-mcp.json\"}' > $T/t2/.github/plugin/plugin.json\necho \"## T2\"; $T/bin/cp_run.sh $T/t2", "description": "Test Copilot MCP config precedence variants"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=$PWD/.tool-homes\nmkdir -p $T/ws2/.github && cd $T/ws2 && git init -q && cp $T/t1/.github/mcp.json .github/mcp.json && rm -rf $T/cp-w && mkdir -p $T/cp-w && env HOME=$T/home XDG_CONFIG_HOME=$T/home/.config COPILOT_HOME=$T/cp-w COPILOT_CACHE_HOME=$T/copilot-cache COPILOT_ALLOW_ALL=true copilot mcp list --json </dev/null; echo; echo '{\"mcpServers\":{\"rootprobe\":{\"command\":\"true\"}}}' > .mcp.json; env HOME=$T/home XDG_CONFIG_HOME=$T/home/.config COPILOT_HOME=$T/cp-w COPILOT_CACHE_HOME=$T/copilot-cache COPILOT_ALLOW_ALL=true copilot mcp list --json </dev/null", "description": "Check if Copilot reads repo .github/mcp.json as workspace config"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && git mv .mcp.json .mcp.json.tmp && cat > .claude-plugin/plugin.json <<'E'\n{\n  \"name\": \"review-kit\",\n  \"version\": \"2.0.0\",\n  \"description\": \"Code review helpers\",\n  \"author\": {\n    \"name\": \"Acme\"\n  },\n  \"userConfig\": {\n    \"api_key\": {\n      \"type\": \"string\",\n      \"title\": \"Review API key\",\n      \"description\": \"Key for the review service\",\n      \"sensitive\": true\n    }\n  },\n  \"mcpServers\": {\n    \"review\": {\n      \"command\": \"${CLAUDE_PLUGIN_ROOT}/server/run.sh\",\n      \"env\": {\n        \"REVIEW_API_KEY\": \"${user_config.api_key}\"\n      }\n    }\n  }\n}\nE\ngit rm -q --cached .mcp.json.tmp && rm .mcp.json.tmp\nmkdir -p .codex-plugin .github/plugin\ncat > .codex-plugin/plugin.json <<'E'\n{\n  \"name\": \"review-kit\",\n  \"version\": \"2.0.0\",\n  \"description\": \"Code review helpers\",\n  \"author\": {\n    \"name\": \"Acme\"\n  },\n  \"mcpServers\": \"./.codex-mcp.json\"\n}\nE\ncat > .codex-mcp.json <<'E'\n{\n  \"mcpServers\": {\n    \"review\": {\n      \"command\": \"./server/run.sh\",\n      \"cwd\": \".\",\n      \"env_vars\": [\"REVIEW_API_KEY\"]\n    }\n  }\n}\nE\ncat > .github/plugin/plugin.json <<'E'\n{\n  \"name\": \"review-kit\",\n  \"version\": \"2.0.0\",\n  \"description\": \"Code review helpers\",\n  \"author\": {\n    \"name\": \"Acme\"\n  },\n  \"mcpServers\": \"./.copilot-mcp.json\"\n}\nE\ncat > .copilot-mcp.json <<'E'\n{\n  \"mcpServers\": {\n    \"review\": {\n      \"command\": \"${PLUGIN_ROOT}/server/run.sh\"\n    }\n  }\n}\nE\ngit status --short", "description": "Write per-tool manifests and MCP configs"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=$PWD/.tool-homes\ncat > $T/bin/mkw.sh <<'E'\n#!/bin/sh\n# mkw.sh <name> [stub]: copy the working tree (excluding .git and .tool-homes) to .tool-homes/<name>; \"stub\" swaps in the probe server + hook logger\nT=$RUN/repo/.tool-homes\nR=$(dirname $T); rm -rf $T/$1; mkdir -p $T/$1\n(cd $R && git ls-files -co --exclude-standard | grep -v '^.tool-homes/' | cpio -pdm --quiet $T/$1)\nif [ \"$2\" = stub ]; then\n  printf '#!/bin/sh\\nexec python3 %s \"$@\"\\n' $T/bin/stub_server.py > $T/$1/server/run.sh\n  printf '#!/bin/sh\\necho \"HOOK ran root=$CLAUDE_PLUGIN_ROOT\" >> %s\\necho review-kit ready\\n' $T/diag.log > $T/$1/scripts/start.sh\nfi\nE\nchmod +x $T/bin/mkw.sh; $T/bin/mkw.sh w1 stub; find $T/w1 -type f | sed \"s|$T/w1/||\" | sort\necho \"######## CLAUDE\"; $T/bin/claude_run.sh $T/w1 2>&1 | grep -vE '^\\s*$|Token counts|On-invoke|component|Per-comp|Projected|Always-on|help configuring|diagnostics|Project config|Location:|CLAUDE_PLUGIN_ROOT$|^review: '\necho \"######## CODEX\"; REVIEW_API_KEY=sekrit $T/bin/codex_variant.sh $T/w1\necho \"######## COPILOT\"; $T/bin/cp_run.sh $T/w1", "description": "Verify final layout in all three tools"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=$PWD/.tool-homes\nfor d in v0 w1; do cp -R $T/$d $T/$d-ns; python3 - $T/$d-ns/.claude-plugin/plugin.json <<'E'\nimport json,sys; p=sys.argv[1]; m=json.load(open(p)); m['userConfig']['api_key']['sensitive']=False; json.dump(m,open(p,'w'),indent=2)\nE\nsed 's/claude plugin install review-kit@review-kit/claude plugin install review-kit@review-kit --config api_key=probe-key/' $T/bin/claude_run.sh > $T/bin/claude_run_cfg.sh; chmod +x $T/bin/claude_run_cfg.sh\necho \"## $d (non-sensitive copy)\"; $T/bin/claude_run_cfg.sh $T/$d-ns 2>&1 | grep -E 'STUB|Connected|Failed|userConfig|Installing'; grep -rl probe-key $T/claude-run 2>/dev/null | head -2; done", "description": "Verify Claude user_config substitution before and after"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && mkdir -p tools && cat > tools/check-manifests.py <<'E'\n#!/usr/bin/env python3\n\"\"\"Fail if the per-tool plugin manifests or MCP configs drift apart.\n\nreview-kit ships one manifest per tool (Claude Code, Codex, Copilot CLI).\n.claude-plugin/plugin.json is the source of truth; the others must match it.\n\"\"\"\nimport json\nimport sys\nfrom pathlib import Path\n\nroot = Path(__file__).resolve().parent.parent\nload = lambda p: json.loads((root / p).read_text())\n\nclaude = load(\".claude-plugin/plugin.json\")\nothers = {\n    \".codex-plugin/plugin.json\": load(\".codex-plugin/plugin.json\"),\n    \".github/plugin/plugin.json\": load(\".github/plugin/plugin.json\"),\n}\nservers = {\n    \".claude-plugin/plugin.json\": set(claude[\"mcpServers\"]),\n    \".codex-mcp.json\": set(load(\".codex-mcp.json\")[\"mcpServers\"]),\n    \".copilot-mcp.json\": set(load(\".copilot-mcp.json\")[\"mcpServers\"]),\n}\n\nerrors = []\nfor path, manifest in others.items():\n    for key in (\"name\", \"version\", \"description\", \"author\"):\n        if manifest.get(key) != claude.get(key):\n            errors.append(f\"{path}: {key} is {manifest.get(key)!r}, .claude-plugin/plugin.json has {claude.get(key)!r}\")\nwant = servers[\".claude-plugin/plugin.json\"]\nfor path, names in servers.items():\n    if names != want:\n        errors.append(f\"{path}: MCP servers {sorted(names)}, .claude-plugin/plugin.json has {sorted(want)}\")\n\nfor e in errors:\n    print(e, file=sys.stderr)\nsys.exit(1 if errors else 0)\nE\nchmod +x tools/check-manifests.py; python3 tools/check-manifests.py; echo \"clean exit=$?\"\nT=$PWD/.tool-homes; $T/bin/mkw.sh chk; sed -i '' 's/\"2.0.0\"/\"2.0.1\"/' $T/chk/.github/plugin/plugin.json; python3 - $T/chk/.codex-mcp.json <<'E'\nimport json,sys;p=sys.argv[1];d=json.load(open(p));d['mcpServers']['other']=d['mcpServers'].pop('review');json.dump(d,open(p,'w'))\nE\npython3 $T/chk/tools/check-manifests.py; echo \"drifted exit=$?\"", "description": "Add manifest drift check and test both outcomes"}}
{"tool": "Write", "input": {"file_path": "$RUN/repo/README.md", "content": "# review-kit\n\nCode review helpers for Claude Code, OpenAI Codex CLI, and GitHub Copilot CLI.\n\n## Install\n\nAll three tools read the same marketplace file, `.claude-plugin/marketplace.json`.\n\n| Tool | Install |\n| --- | --- |\n| Claude Code | `claude plugin marketplace add <repo>` then `claude plugin install review-kit@review-kit` |\n| Codex CLI | `codex plugin marketplace add <repo>` then `codex plugin add review-kit@review-kit` |\n| Copilot CLI | `copilot plugin marketplace add <repo>` then `copilot plugin install review-kit@review-kit` |\n\n### API key\n\nClaude Code asks for the key at install time (`userConfig`) and stores it as a sensitive value.\nCodex and Copilot have no equivalent, so export `REVIEW_API_KEY` in the shell that launches them.\nCodex passes only that variable to the server (`env_vars`); Copilot passes its environment through.\n\n## What works where\n\n| Component | Claude Code | Codex CLI | Copilot CLI |\n| --- | --- | --- | --- |\n| `/review` command | `/review-kit:review` | Converted to the skill `review-kit:source-command-review` (no slash command) | `/review-kit:review` (plain `/review` is Copilot's own built-in) |\n| `reviewer` agent | Yes | No (Codex plugins do not load agents) | Loaded from `agents/`, per Copilot docs |\n| `SessionStart` hook | Yes | Yes, once you review and trust it (Codex skips untrusted plugin hooks) | Runs, per Copilot docs, but Copilot ignores plain-text output, so `review-kit ready` does not reach the model |\n| `review` MCP server | Yes | Yes | Yes |\n| MCP server working directory | Session directory | Plugin install directory | Plugin install directory |\n\n## Layout\n\nEach tool reads its own manifest and MCP config:\n\n| Tool | Manifest | MCP config |\n| --- | --- | --- |\n| Claude Code | `.claude-plugin/plugin.json` | inline `mcpServers` in that manifest |\n| Codex CLI | `.codex-plugin/plugin.json` | `.codex-mcp.json` |\n| Copilot CLI | `.github/plugin/plugin.json` | `.copilot-mcp.json` |\n\nThere is no root `.mcp.json`.\nCopilot would read it ahead of its own config and pass the unexpanded `${user_config.api_key}` to the server.\nClaude Code and Copilot would also treat it as project config when you work inside this repo.\n\nThe three tools expand placeholders differently, so the MCP configs differ:\nClaude Code expands `${CLAUDE_PLUGIN_ROOT}` and `${user_config.*}`,\nCopilot expands `${PLUGIN_ROOT}`,\nand Codex expands neither but resolves `command` and `cwd` against the plugin directory.\n\n`.claude-plugin/plugin.json` is the source of truth for name, version, description, author, and MCP server names.\nAfter changing any of them, run `python3 tools/check-manifests.py`; it exits non-zero when the other manifests have drifted.\n"}}
{"tool": "Edit", "input": {"replace_all": false, "file_path": "$RUN/repo/README.md", "old_string": "and Codex expands neither but resolves `command` and `cwd` against the plugin directory.", "new_string": "and Codex expands neither but resolves a relative `cwd` against the plugin directory, so `./server/run.sh` works there."}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=$PWD/.tool-homes\n$T/bin/mkw.sh w2 stub\necho \"## CLAUDE\"; $T/bin/claude_run.sh $T/w2 2>&1 | grep -E 'Validation|Skills|Agents|Hooks|MCP servers \\(|Connected|Failed|STUB'\necho \"## CODEX\"; REVIEW_API_KEY=sekrit $T/bin/codex_variant.sh $T/w2 | cut -c1-200\necho \"## COPILOT\"; $T/bin/cp_run.sh $T/w2\npython3 tools/check-manifests.py && echo check-ok; git status --short", "description": "Re-run all three tool probes on final tree"}}
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
diff --git a/.codex-mcp.json b/.codex-mcp.json
new file mode 100644
index 0000000..b5c0327
--- /dev/null
+++ b/.codex-mcp.json
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
index 0000000..9ce9c3b
--- /dev/null
+++ b/.codex-plugin/plugin.json
@@ -0,0 +1,9 @@
+{
+  "name": "review-kit",
+  "version": "2.0.0",
+  "description": "Code review helpers",
+  "author": {
+    "name": "Acme"
+  },
+  "mcpServers": "./.codex-mcp.json"
+}
diff --git a/.copilot-mcp.json b/.copilot-mcp.json
new file mode 100644
index 0000000..ff660de
--- /dev/null
+++ b/.copilot-mcp.json
@@ -0,0 +1,7 @@
+{
+  "mcpServers": {
+    "review": {
+      "command": "${PLUGIN_ROOT}/server/run.sh"
+    }
+  }
+}
diff --git a/.github/plugin/plugin.json b/.github/plugin/plugin.json
new file mode 100644
index 0000000..c537bc8
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
+  "mcpServers": "./.copilot-mcp.json"
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
index 9246da6..9a3a245 100644
--- a/README.md
+++ b/README.md
@@ -1,3 +1,51 @@
 # review-kit
 
-Code review helpers for Claude Code.
+Code review helpers for Claude Code, OpenAI Codex CLI, and GitHub Copilot CLI.
+
+## Install
+
+All three tools read the same marketplace file, `.claude-plugin/marketplace.json`.
+
+| Tool | Install |
+| --- | --- |
+| Claude Code | `claude plugin marketplace add <repo>` then `claude plugin install review-kit@review-kit` |
+| Codex CLI | `codex plugin marketplace add <repo>` then `codex plugin add review-kit@review-kit` |
+| Copilot CLI | `copilot plugin marketplace add <repo>` then `copilot plugin install review-kit@review-kit` |
+
+### API key
+
+Claude Code asks for the key at install time (`userConfig`) and stores it as a sensitive value.
+Codex and Copilot have no equivalent, so export `REVIEW_API_KEY` in the shell that launches them.
+Codex passes only that variable to the server (`env_vars`); Copilot passes its environment through.
+
+## What works where
+
+| Component | Claude Code | Codex CLI | Copilot CLI |
+| --- | --- | --- | --- |
+| `/review` command | `/review-kit:review` | Converted to the skill `review-kit:source-command-review` (no slash command) | `/review-kit:review` (plain `/review` is Copilot's own built-in) |
+| `reviewer` agent | Yes | No (Codex plugins do not load agents) | Loaded from `agents/`, per Copilot docs |
+| `SessionStart` hook | Yes | Yes, once you review and trust it (Codex skips untrusted plugin hooks) | Runs, per Copilot docs, but Copilot ignores plain-text output, so `review-kit ready` does not reach the model |
+| `review` MCP server | Yes | Yes | Yes |
+| MCP server working directory | Session directory | Plugin install directory | Plugin install directory |
+
+## Layout
+
+Each tool reads its own manifest and MCP config:
+
+| Tool | Manifest | MCP config |
+| --- | --- | --- |
+| Claude Code | `.claude-plugin/plugin.json` | inline `mcpServers` in that manifest |
+| Codex CLI | `.codex-plugin/plugin.json` | `.codex-mcp.json` |
+| Copilot CLI | `.github/plugin/plugin.json` | `.copilot-mcp.json` |
+
+There is no root `.mcp.json`.
+Copilot would read it ahead of its own config and pass the unexpanded `${user_config.api_key}` to the server.
+Claude Code and Copilot would also treat it as project config when you work inside this repo.
+
+The three tools expand placeholders differently, so the MCP configs differ:
+Claude Code expands `${CLAUDE_PLUGIN_ROOT}` and `${user_config.*}`,
+Copilot expands `${PLUGIN_ROOT}`,
+and Codex expands neither but resolves a relative `cwd` against the plugin directory, so `./server/run.sh` works there.
+
+`.claude-plugin/plugin.json` is the source of truth for name, version, description, author, and MCP server names.
+After changing any of them, run `python3 tools/check-manifests.py`; it exits non-zero when the other manifests have drifted.
diff --git a/tools/check-manifests.py b/tools/check-manifests.py
new file mode 100755
index 0000000..06de0d4
--- /dev/null
+++ b/tools/check-manifests.py
@@ -0,0 +1,37 @@
+#!/usr/bin/env python3
+"""Fail if the per-tool plugin manifests or MCP configs drift apart.
+
+review-kit ships one manifest per tool (Claude Code, Codex, Copilot CLI).
+.claude-plugin/plugin.json is the source of truth; the others must match it.
+"""
+import json
+import sys
+from pathlib import Path
+
+root = Path(__file__).resolve().parent.parent
+load = lambda p: json.loads((root / p).read_text())
+
+claude = load(".claude-plugin/plugin.json")
+others = {
+    ".codex-plugin/plugin.json": load(".codex-plugin/plugin.json"),
+    ".github/plugin/plugin.json": load(".github/plugin/plugin.json"),
+}
+servers = {
+    ".claude-plugin/plugin.json": set(claude["mcpServers"]),
+    ".codex-mcp.json": set(load(".codex-mcp.json")["mcpServers"]),
+    ".copilot-mcp.json": set(load(".copilot-mcp.json")["mcpServers"]),
+}
+
+errors = []
+for path, manifest in others.items():
+    for key in ("name", "version", "description", "author"):
+        if manifest.get(key) != claude.get(key):
+            errors.append(f"{path}: {key} is {manifest.get(key)!r}, .claude-plugin/plugin.json has {claude.get(key)!r}")
+want = servers[".claude-plugin/plugin.json"]
+for path, names in servers.items():
+    if names != want:
+        errors.append(f"{path}: MCP servers {sorted(names)}, .claude-plugin/plugin.json has {sorted(want)}")
+
+for e in errors:
+    print(e, file=sys.stderr)
+sys.exit(1 if errors else 0)
```

## Repository refs

Every branch and tag in the final repository, each with its changes against the fixture tree (`refs.txt`).

```text
master a9b754a
```
