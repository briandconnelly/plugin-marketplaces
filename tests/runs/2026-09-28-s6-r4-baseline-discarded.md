# Run: scenario 6, repetition 4, baseline (DISCARDED, not scored)

Scored against `tests/scenarios.md` as of this commit; cost is `metrics` in the manifest.

## Manifest

```json
{
  "date": "2026-09-28",
  "arm": "baseline",
  "scenario": "s6",
  "rep": 4,
  "fixture_tree": "d9320bcbf1a93e6e7320d6c448f5bd206524ea28",
  "upstream_commits": null,
  "tools": {
    "claude": "2.1.284 (Claude Code)",
    "codex": "codex-cli 0.157.1",
    "copilot": "GitHub Copilot CLI 1.0.88."
  },
  "session_context": "dispatched from a Claude Code session (claude 2.1.284) with installed plugins including superpowers, plugin-dev, amicus, astral, obsidian, pr-review-toolkit, code-review, skill-creator, mcp-server-dev, claude-code-setup; user skills include agent-bot-identity, review-pr, fastmcp, prek; the plugin-marketplaces skill is not installed anywhere",
  "prompt_file": "prompt.txt",
  "transcript": "a8997589f32e67ad9.output",
  "model": "claude-opus-5-5",
  "metrics": {
    "tool_calls": 17,
    "wall_seconds": 158.0
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
Do not send a prompt to any AI model or agent, including through a command-line tool.
Do not push, publish, or contact any remote service other than read-only documentation.

Audit this marketplace before we announce it to Claude Code and Codex users.
Don't change any files — give me a findings list.
```

## Isolation

Flags raised by `tests/eval/isolation.py` (tests/scenarios.md, How to run, step 5):

```text
#11 outside-write: redirect to /tmp/nul
```

DISCARDED: call #11 redirected stderr to /tmp/nul (a typo for /dev/null), creating a file outside the run directory. Harmless, but a violation of the write rule; discarded for consistency with s2-r2 and s6-r1. Every tool call was otherwise isolated, and Codex ran under sandbox-exec with outbound network denied. Replaced by s6-r5.

## Score

Not scored: this run was discarded (see Isolation). It is kept so any observation drawn from it can be audited; it is not evidence for the arm's score.

## Final report

Audit of the acme-tools marketplace at $RUN/repo. It is not ready to announce. On Claude Code the marketplace fails validation. On Codex, 2 of the 7 listed plugins are silently missing and a third won't install.

No tracked files were changed (`git status` and `git diff` are clean). All experiments ran on copies under `.tool-homes/`, which git ignores. Tool configuration was isolated:
- **Claude Code 2.1.284:** `CLAUDE_CONFIG_DIR` and `HOME` pointed at `.tool-homes/`.
- **Codex 0.157.1:** `CODEX_HOME` and `HOME` pointed at `.tool-homes/`, and every Codex command ran with outbound network blocked (`sandbox-exec`).
- No prompts were sent to any model, and no remote was contacted.

**Blocking**

1. **The marketplace fails Claude Code validation (`fmt` source).** In `$RUN/repo/.claude-plugin/marketplace.json`, `fmt` has `"source": "plugins/fmt"` with no `./` prefix.
   - Claude Code: `claude plugin validate .` reports `plugins.2.source: Invalid input` and exits 1.
   - Codex: the entry is silently left out of `codex plugin list`, and `codex plugin add fmt@acme-tools` says "not found".
   - Changing it to `./plugins/fmt` (tested on a copy) fixes both clients.
2. **`notes` never appears for Codex users.** Codex silently drops the `"source": "github"` form, with or without `ref`/`sha`, and gives no warning.
   - Claude Code accepts it.
   - On a copy, rewriting it as `{"source":"url","url":"https://github.com/acme/notes.git","ref":"v2.0.0","sha":"3add7b96…"}` was listed by Codex with the sha kept, and passed Claude validation.
   - I could not check that the sha actually matches tag v2.0.0, because that needs the remote.
3. **`lint` won't install on Codex.** The marketplace entry is named `lint`, but `$RUN/repo/plugins/lint/.claude-plugin/plugin.json` says `"name": "linter"`.
   - Codex fails with: `plugin.json name 'linter' does not match marketplace plugin name 'lint'`.
   - Claude Code installs it without complaint, and `claude plugin validate` does not catch the mismatch either.
   - The skill inside is also called `linter`.
4. **`guard` fails to load on Claude Code, and has no hook anyway.** The marketplace entry has `"hooks": "./hooks/hooks.json"`.
   - After installing it into an isolated Claude config, `claude plugin list` shows "✘ failed to load" with this error: "the file-path and array forms are not yet supported in a marketplace entry".
   - The validator passes it, so this only shows up at install time.
   - No `hooks/` directory exists at the repo root or in `plugins/guard`. The plugin contains only a one-line SKILL.md.
   - Codex installs it and silently ignores the field.
   - So the advertised "Block risky shell commands with a pre-tool hook" does nothing in either client, and users would think they are protected when they are not.

**Should fix**

5. **`remote-x` is not pinned.** It uses `"ref": "main"` with no `sha`, so what users install can change at any time. Pin a tag and a sha, as `notes` does.
6. **`deploy` has conflicting versions.** The marketplace entry says `2.0.0` but `plugins/deploy/.claude-plugin/plugin.json` says `1.9.0`. The Claude validator warns that plugin.json wins, and both clients installed 1.9.0. Users will see a version that doesn't match what the listing says.
7. **The skills are one-line stubs.** Each SKILL.md in `$RUN/repo/plugins/*/skills/*/SKILL.md` just repeats its description.
   - None says which linters or formatters to run, what "team style" means, or how or where to deploy.
   - Once installed, none of these plugins can do what it advertises.
8. **`deploy` has side effects but the model can invoke it on its own.** Its description ("Use when you want to deploy…") lets the model trigger it without being asked. Consider requiring an explicit user request (on Claude Code, `disable-model-invocation: true`) and adding real guardrails to the skill body. This is a judgement call; I didn't test it.

**Minor**

9. **Descriptions are written in several places and have drifted.** The marketplace says "Markdown" and "Python and TypeScript", while plugin.json and the SKILL.md bodies say "markdown" and "python and typescript". Guard's text differs between files too.
10. **The README is a stub.** `$RUN/repo/README.md` has no install commands for either client (`/plugin marketplace add …`, `codex plugin marketplace add …`), no plugin list, and no support contact. `owner` in the marketplace file has only a name.

**What was verified and what wasn't**
- `claude plugin validate` passed all five local plugin manifests, but it missed findings 3 and 4 at the marketplace level. Those only showed up when actually installing into isolated Claude Code and Codex configs.
- Neither remote plugin (`notes`, `remote-x`) was fetched or inspected.
- No skills were run in a model session, so nothing here says whether they trigger.

## Tool calls

The arm's tool calls, one JSON object per line, extracted from its transcript.

```jsonl
{"tool": "Bash", "input": {"command": "cd $RUN/repo && git status && git log --oneline | head && find . -path ./.git -prune -o -type f -print | head -100", "description": "Inspect repo layout and history"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && for f in README.md .claude-plugin/marketplace.json plugins/*/.claude-plugin/plugin.json plugins/*/skills/*/SKILL.md; do echo \"=== $f\"; cat -A \"$f\" | head -80; done; ls -la plugins/*", "description": "Print all files with hidden chars"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && for f in README.md .claude-plugin/marketplace.json plugins/*/.claude-plugin/plugin.json plugins/*/skills/*/SKILL.md; do echo \"=== $f\"; cat -vet \"$f\"; done; git remote -v", "description": "Print all files with visible control chars"}}
{"tool": "Bash", "input": {"command": "which claude codex jq python3; claude --version; codex --version 2>&1 | head -2", "description": "Check available CLIs"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && mkdir -p .tool-homes/claude .tool-homes/home && export HOME=$PWD/.tool-homes/home CLAUDE_CONFIG_DIR=$PWD/.tool-homes/claude && claude plugin validate . 2>&1; echo \"exit=$?\"; for p in plugins/*; do echo \"--- $p\"; claude plugin validate $p 2>&1; echo \"exit=$?\"; done", "description": "Run Claude plugin validator with isolated config"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && R=$PWD && mkdir -p .tool-homes/copy && rsync -a --exclude .tool-homes --exclude .git ./ .tool-homes/copy/ && cd .tool-homes/copy && jq '.plugins[2].source=\"./plugins/fmt\"' .claude-plugin/marketplace.json > m && mv m .claude-plugin/marketplace.json && export HOME=$R/.tool-homes/home CLAUDE_CONFIG_DIR=$R/.tool-homes/claude && claude plugin validate . 2>&1; echo exit=$?; ls plugins/guard; ls hooks 2>&1", "description": "Validate a scratch copy with the fmt source fixed"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && R=$PWD && export HOME=$R/.tool-homes/home CLAUDE_CONFIG_DIR=$R/.tool-homes/claude && claude plugin marketplace add $R/.tool-homes/copy 2>&1; for p in guard lint fmt ok-tools deploy; do echo \"--- $p\"; claude plugin install $p@acme-tools 2>&1; done; claude plugin list 2>&1", "description": "Install local plugins into isolated Claude config"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && R=$PWD && export HOME=$R/.tool-homes/home CLAUDE_CONFIG_DIR=$R/.tool-homes/claude && claude plugin list --json 2>&1 | head -80; find .tool-homes/claude -maxdepth 4 | head -40", "description": "Inspect installed plugin details"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && R=$PWD && mkdir -p .tool-homes/codex && export HOME=$R/.tool-homes/home CODEX_HOME=$R/.tool-homes/codex && codex --help 2>&1 | head -40; codex plugin --help 2>&1; codex plugin marketplace --help 2>&1", "description": "Explore Codex plugin commands with isolated home"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && R=$PWD && export HOME=$R/.tool-homes/home CODEX_HOME=$R/.tool-homes/codex && codex plugin add --help 2>&1 | sed -n 1,25p; codex plugin list --help 2>&1 | sed -n 1,25p; codex plugin marketplace add --help | sed -n 1,20p", "description": "Read Codex plugin subcommand help"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && R=$PWD && rm -rf .tool-homes/orig && rsync -a --exclude .tool-homes ./ .tool-homes/orig/ && export HOME=$R/.tool-homes/home CODEX_HOME=$R/.tool-homes/codex && NB=\"sandbox-exec -p (version\\ 1)(allow\\ default)(deny\\ network-outbound\\ (remote\\ ip))\" ; SB='(version 1)(allow default)(deny network-outbound (remote ip))'; sandbox-exec -p \"$SB\" codex plugin marketplace add $R/.tool-homes/orig 2>&1; echo exit=$?; sandbox-exec -p \"$SB\" codex plugin marketplace list 2>&1; sandbox-exec -p \"$SB\" codex plugin list -m acme-tools --json --available 2>&1 | head -80", "description": "Add as-shipped marketplace to isolated Codex, network denied"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && R=$PWD && export HOME=$R/.tool-homes/home CODEX_HOME=$R/.tool-homes/codex && SB='(version 1)(allow default)(deny network-outbound (remote ip))'; sandbox-exec -p \"$SB\" codex plugin list -m acme-tools --json --available 2>/tmp/nul | jq -c '.available[]|{pluginId,version,source}'; sandbox-exec -p \"$SB\" codex plugin list -m acme-tools --json --available 2>&1 >/dev/null | head; for p in ok-tools lint deploy guard fmt; do echo \"--- $p\"; sandbox-exec -p \"$SB\" codex plugin add $p@acme-tools 2>&1 | tail -5; done; ls -R $CODEX_HOME | head -60", "description": "List and install Codex plugins offline"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && R=$PWD && export HOME=$R/.tool-homes/home CODEX_HOME=$R/.tool-homes/codex RUST_LOG=warn && SB='(version 1)(allow default)(deny network-outbound (remote ip))'; sandbox-exec -p \"$SB\" codex plugin list -m acme-tools --json --available 2>&1 1>/dev/null | head -20; echo ---; sandbox-exec -p \"$SB\" codex plugin add notes@acme-tools 2>&1 | tail -3; sandbox-exec -p \"$SB\" codex plugin list -m acme-tools 2>&1 | head -30; cat $CODEX_HOME/config.toml", "description": "Check Codex warnings for dropped entries"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && R=$PWD && SB='(version 1)(allow default)(deny network-outbound (remote ip))'; export HOME=$R/.tool-homes/home; for v in nosha noref fmtdot; do rm -rf .tool-homes/v-$v .tool-homes/codex-$v; rsync -a --exclude .tool-homes --exclude .git ./ .tool-homes/v-$v/; mkdir .tool-homes/codex-$v; m=.tool-homes/v-$v/.claude-plugin/marketplace.json; case $v in nosha) f='del(.plugins[1].source.sha)';; noref) f='.plugins[1].source={\"source\":\"github\",\"repo\":\"acme/notes\"}';; fmtdot) f='.plugins[2].source=\"./plugins/fmt\"';; esac; jq \"$f\" $m > $m.t && mv $m.t $m; echo \"== $v\"; CODEX_HOME=$R/.tool-homes/codex-$v sandbox-exec -p \"$SB\" codex plugin marketplace add $R/.tool-homes/v-$v >/dev/null 2>&1; CODEX_HOME=$R/.tool-homes/codex-$v sandbox-exec -p \"$SB\" codex plugin list -m acme-tools 2>&1 | awk 'NR>3{print $1}'; done", "description": "Test Codex handling of source variants"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && R=$PWD && SB='(version 1)(allow default)(deny network-outbound (remote ip))'; export HOME=$R/.tool-homes/home; v=urlsha; rm -rf .tool-homes/v-$v .tool-homes/codex-$v; rsync -a --exclude .tool-homes --exclude .git ./ .tool-homes/v-$v/; mkdir .tool-homes/codex-$v; m=.tool-homes/v-$v/.claude-plugin/marketplace.json; jq '.plugins[1].source={\"source\":\"url\",\"url\":\"https://github.com/acme/notes.git\",\"ref\":\"v2.0.0\",\"sha\":\"3add7b9612102f2a7dbe4ed4fe886e07e847c24d\"}' $m > $m.t && mv $m.t $m; export CODEX_HOME=$R/.tool-homes/codex-$v; sandbox-exec -p \"$SB\" codex plugin marketplace add $R/.tool-homes/v-$v >/dev/null 2>&1; sandbox-exec -p \"$SB\" codex plugin list -m acme-tools --json --available 2>/dev/null | jq -c '.available[]|select(.name==\"notes\")|.source'", "description": "Test Codex url source with sha"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && R=$PWD && export HOME=$R/.tool-homes/home CLAUDE_CONFIG_DIR=$R/.tool-homes/claude-v && mkdir -p $CLAUDE_CONFIG_DIR && m=.tool-homes/v-urlsha/.claude-plugin/marketplace.json && jq '.plugins[2].source=\"./plugins/fmt\"' $m > $m.t && mv $m.t $m && claude plugin validate .tool-homes/v-urlsha 2>&1 | tail -6; git status --short", "description": "Validate url+sha variant with Claude"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && git status --short --untracked-files=all | head; git diff --stat; cat .git/info/exclude | tail -3", "description": "Confirm tracked files unchanged"}}
```

## Objective checks

```json
{
  "claude": {
    "ran": true,
    "exit": 1,
    "success": false,
    "errors": [
      "plugins.2.source"
    ],
    "warnings": [
      "plugins[4].version"
    ]
  },
  "codex": {
    "ran": true,
    "added": true,
    "marketplace": "acme-tools",
    "listed": [
      "deploy",
      "guard",
      "lint",
      "ok-tools",
      "remote-x"
    ]
  },
  "copilot": {
    "ran": true,
    "added": true,
    "marketplace": "acme-tools",
    "listed": [
      "deploy",
      "fmt",
      "guard",
      "lint",
      "notes",
      "ok-tools",
      "remote-x"
    ]
  }
}
```

## Diff

```diff

```
