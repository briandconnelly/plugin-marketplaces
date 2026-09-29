# Run: scenario 2, repetition 3, with-skill

Scored against `tests/scenarios.md` as of this commit; cost is `metrics` in the manifest.

## Manifest

```json
{
  "date": "2026-09-28",
  "arm": "with-skill",
  "scenario": "s2",
  "rep": 3,
  "fixture_tree": "8640972fd67d9623c6fb9326a72c38420402842e",
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
  "transcript": "acd9f224efe963b4c.output",
  "model": "claude-opus-5-5",
  "metrics": {
    "tool_calls": 10,
    "wall_seconds": 91.6
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

Add the new `lint-kit` plugin (in `plugins/lint-kit`) to our marketplace.
```

## Isolation

Flags raised by `tests/eval/isolation.py` (tests/scenarios.md, How to run, step 5):

```text
#4 outside-read: cd $RUN
```

Batch 1. Every tool call read. Call #4 cd into the run directory itself: reads there are allowed and its only write (TMPDIR) is inside WORKDIR, ruled not a violation (plan-2c ledger). Secret-scan hits are 'token cost' text.

## Score

| Criterion | Result | Evidence |
| --- | --- | --- |
| 1 | pass | objective.json shows `claude.errors: []`. The final `.claude-plugin/marketplace.json` lists alpha-notes, branch-tidy, claude-hooks and lint-kit. |
| 2 | pass | objective.json `codex.listed` = alpha-notes, branch-tidy, codex-helper, lint-kit. |
| 3 | pass | `claude-hooks` is not in objective.json `codex.listed`, and `codex-helper` is not in the final `.claude-plugin/marketplace.json`. |
| 4 | pass | Both `plugins/lint-kit/plugin.json` and `plugins/lint-kit/.claude-plugin/plugin.json` now say `1.1.0` (diff.patch, repo grep), and neither catalog records a version. report.md says the manifests disagreed (1.1.0 vs 1.0.0) and that it kept `1.1.0`. |
| 5 | pass | report.md's Checks table marks each check as passed, partly checked (Codex load: `codex debug prompt-input` not run), not applicable (Remote) or not run (Copilot CLI). |

Total: 5 of 5 passed.

## Final report

I added `lint-kit` to both catalogs. Before adding it, I had to settle a version conflict in its manifests. The validator is now clean, and Claude Code and Codex both list and install it at 1.1.0 using throwaway configuration. Nothing is committed.

**Version conflict.** The plugin's two manifests disagreed. `plugins/lint-kit/plugin.json` (the Agent Plugins root, which Codex reads) said `1.1.0`. `plugins/lint-kit/.claude-plugin/plugin.json` (which Claude Code reads) said `1.0.0`. As they were, Codex users would have received 1.1.0 and Claude Code users 1.0.0, with no warning from either tool. I kept `1.1.0` and set the Claude manifest to match. It is the higher value, and the Claude manifest is the likelier one to have missed a bump. The repo has no history to confirm that, so please check 1.1.0 is the version you meant to ship. Neither catalog entry records a version, so no other place needed changing.

**Changes, all in `$RUN/repo`:**
- `.claude-plugin/marketplace.json`: added the `lint-kit` entry with source `./plugins/lint-kit` and description "Run the team's linters". The plugin has only a skill, with no hooks, MCP servers, LSP servers or `bin/`, so there is nothing to disclose in the description.
- `.agents/plugins/marketplace.json`: added the same entry as a local source, with the same policy and category as the other entries.
- `plugins/lint-kit/.claude-plugin/plugin.json`: version changed from 1.0.0 to 1.1.0.
- `marketplace-policy.json` (new): declares Claude Code and Codex as the tools this marketplace targets. It also records why two plugins are in only one catalog: `claude-hooks` is Claude-only and `codex-helper` is Codex-only. Those reasons were only in `README.md`, so the validator already failed on the repo before I touched it. I copied the reasons from the README and left the README unchanged, so the reasons now live in two places.

**Checks:**

| Check | Status | Evidence |
| --- | --- | --- |
| Schema | passed | Validator: parse, policy, `claude plugin validate --strict` and portable-manifest checks all passed. |
| Local | passed | Validator reported no findings. As a control, I put the old 1.0.0 back in a scratch copy and it raised a version-mismatch error for `lint-kit` in both catalogs, so the clean result is meaningful. |
| Remote | not applicable | All sources are local, and the validator does not run this level. |
| Discovery, Claude Code | passed | Validate reported 0 errors and 0 warnings, and `claude plugin marketplace add` succeeded (claude 2.1.284). |
| Discovery, Codex | passed | `codex plugin list --available` lists alpha-notes, branch-tidy, codex-helper and lint-kit 1.1.0 (codex-cli 0.157.1). |
| Load, Claude Code | passed | Installed; `plugin details` shows 1 skill (`lint-kit`) and no agents, hooks, MCP or LSP servers, at version 1.1.0. |
| Load, Codex | partly checked | Installed at 1.1.0, and the cache contains `skills/lint-kit/SKILL.md`. I did not run `codex debug prompt-input`, so whether Codex actually presents the skill is unconfirmed. |
| Copilot CLI | not run | Copilot CLI is not a target, so I ran no Copilot checks. |

All tool checks ran against a clean copy of the repo, with throwaway configuration under `.tool-homes/` and outbound network blocked. No prompt or session was opened.

Decision for you: Copilot CLI would also read `.claude-plugin/marketplace.json` if a user added this marketplace. I left it out of the policy because nothing in the repo targeted it, but that means the validator does not check the catalog against Copilot CLI's rules. If you do want to support it, add `copilot-cli` to the policy's readers. The Claude-only `claude-hooks` would then also be offered to Copilot CLI users, so you'd need to decide whether that's intended.

`.tool-homes/` is untracked and not in `.gitignore`, so keep it out of any commit.

## Tool calls

The arm's tool calls, one JSON object per line, extracted from its transcript.

```jsonl
{"tool": "Bash", "input": {"command": "cd $RUN/repo && cat ../skill/plugin-marketplaces/SKILL.md && ls -R ../skill/plugin-marketplaces && git status && find . -path ./.git -prune -o -type f -print", "description": "Read skill and list repo files"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && for f in README.md .claude-plugin/marketplace.json .agents/plugins/marketplace.json plugins/lint-kit/plugin.json plugins/lint-kit/.claude-plugin/plugin.json plugins/lint-kit/skills/lint-kit/SKILL.md plugins/*/.claude-plugin/plugin.json plugins/codex-helper/.codex-plugin/plugin.json; do echo \"=== $f\"; cat \"$f\"; done; ls -la plugins/lint-kit; git log --oneline | head", "description": "Show catalogs and manifests"}}
{"tool": "Bash", "input": {"command": "cd $RUN/skill/plugin-marketplaces/references && cat releases.md validation.md", "description": "Read releases and validation references"}}
{"tool": "Bash", "input": {"command": "cd $RUN/skill/plugin-marketplaces && cat scripts/mpcheck/policy.py; cat multi-tool.md 2>/dev/null; cat references/multi-tool.md", "description": "Read policy loader and multi-tool reference"}}
{"tool": "Bash", "input": {"command": "cd $RUN && python3 -c \"import json;d=json.load(open('skill/plugin-marketplaces/scripts/mpcheck/data/readers.json'));print(json.dumps({k:{kk:v[kk] for kk in v if kk in('catalog_paths','sources','name')} for k,v in (d.items() if isinstance(d,dict) else [])},indent=1)[:3000])\"; T=repo/.tool-homes; mkdir -p $T/tmp; TMPDIR=$PWD/$T/tmp validator/bin/check-marketplace repo; echo exit=$?; which claude codex copilot", "description": "Inspect reader ids and run baseline validator"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && cat > marketplace-policy.json <<'EOF'\n{\n  \"readers\": [\"claude-code\", \"codex\"],\n  \"exceptions\": [\n    {\n      \"plugin\": \"claude-hooks\",\n      \"kind\": \"membership\",\n      \"reason\": \"Listed for Claude Code only: Codex does not run its prompt hooks.\"\n    },\n    {\n      \"plugin\": \"codex-helper\",\n      \"kind\": \"membership\",\n      \"reason\": \"Listed for Codex only: it wraps a Codex app integration.\"\n    }\n  ]\n}\nEOF\npython3 - <<'EOF'\nimport json\np='plugins/lint-kit/.claude-plugin/plugin.json'\nd=json.load(open(p)); d['version']='1.1.0'; open(p,'w').write(json.dumps(d,indent=2)+'\\n')\np='.claude-plugin/marketplace.json'\nd=json.load(open(p)); d['plugins'].append({\"name\":\"lint-kit\",\"source\":\"./plugins/lint-kit\",\"description\":\"Run the team's linters\"}); open(p,'w').write(json.dumps(d,indent=2)+'\\n')\np='.agents/plugins/marketplace.json'\nd=json.load(open(p)); d['plugins'].append({\"name\":\"lint-kit\",\"source\":{\"source\":\"local\",\"path\":\"./plugins/lint-kit\"},\"policy\":{\"installation\":\"AVAILABLE\",\"authentication\":\"ON_INSTALL\"},\"category\":\"Developer Tools\"}); open(p,'w').write(json.dumps(d,indent=2)+'\\n')\nEOF\ngit diff; T=$PWD/.tool-homes; TMPDIR=$T/tmp ../validator/bin/check-marketplace . ; echo exit=$?", "description": "Write policy, align versions, add entries, validate"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=$PWD/.tool-homes && rm -rf $T/export $T/neg && mkdir -p $T/export $T/neg $T/tmp && git ls-files -co --exclude-standard | grep -v '^.tool-homes/' | tar -cf - -T - | tar -xf - -C $T/export && cp -R $T/export/. $T/neg/ && sed -i '' 's/\"1.1.0\"/\"1.0.0\"/' $T/neg/plugins/lint-kit/.claude-plugin/plugin.json && TMPDIR=$T/tmp ../validator/bin/check-marketplace $T/neg | grep -E 'local|lint-kit'; find $T/export -type f | sed \"s|$T/export/||\"", "description": "Negative-control validator run and clean export"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=$PWD/.tool-homes && mkdir -p \"$T\"/{home,xdg,tmp,claude,codex,copilot,copilot-cache} && : > \"$T/gitconfig\" && export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\" && SB=\"sandbox-exec -p (version\\ 1)(allow\\ default)(deny\\ network-outbound\\ (remote\\ ip))\" && S='(version 1)(allow default)(deny network-outbound (remote ip))' && E=$T/export && \necho \"== claude version\"; sandbox-exec -p \"$S\" claude --version </dev/null\necho \"== claude validate\"; sandbox-exec -p \"$S\" claude plugin validate $E --strict --json </dev/null; echo rc=$?\necho \"== claude add\"; sandbox-exec -p \"$S\" claude plugin marketplace add $E </dev/null; echo rc=$?\necho \"== claude install\"; sandbox-exec -p \"$S\" claude plugin install lint-kit@acme-tools </dev/null; echo rc=$?\necho \"== claude details\"; sandbox-exec -p \"$S\" claude plugin details lint-kit@acme-tools </dev/null; echo rc=$?\necho \"== claude list\"; sandbox-exec -p \"$S\" claude plugin list --json </dev/null; echo rc=$?", "description": "Isolated Claude Code discovery and load check", "timeout": 300000}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=$PWD/.tool-homes && export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\" && S='(version 1)(allow default)(deny network-outbound (remote ip))' && E=$T/export && \necho \"== codex version\"; sandbox-exec -p \"$S\" codex --version </dev/null\necho \"== codex add\"; sandbox-exec -p \"$S\" codex plugin marketplace add $E </dev/null 2>&1; echo rc=$?\necho \"== codex list\"; sandbox-exec -p \"$S\" codex plugin list --available --json </dev/null 2>&1; echo rc=$?\necho \"== codex install\"; sandbox-exec -p \"$S\" codex plugin add lint-kit@acme-tools --json </dev/null 2>&1; echo rc=$?", "description": "Isolated Codex discovery and load check", "timeout": 300000}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && find .tool-homes/codex/plugins/cache/acme-tools/lint-kit/1.1.0 -type f; git status --short", "description": "Check Codex install contents and git status"}}
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
    "marketplace": "acme-tools",
    "listed": [
      "alpha-notes",
      "branch-tidy",
      "codex-helper",
      "lint-kit"
    ]
  },
  "copilot": {
    "ran": true,
    "added": true,
    "marketplace": "acme-tools",
    "listed": [
      "alpha-notes",
      "branch-tidy",
      "claude-hooks",
      "lint-kit"
    ]
  }
}
```

## Diff

```diff
diff --git a/.agents/plugins/marketplace.json b/.agents/plugins/marketplace.json
index 2f8b183..9e0daf8 100644
--- a/.agents/plugins/marketplace.json
+++ b/.agents/plugins/marketplace.json
@@ -39,6 +39,18 @@
         "authentication": "ON_INSTALL"
       },
       "category": "Developer Tools"
+    },
+    {
+      "name": "lint-kit",
+      "source": {
+        "source": "local",
+        "path": "./plugins/lint-kit"
+      },
+      "policy": {
+        "installation": "AVAILABLE",
+        "authentication": "ON_INSTALL"
+      },
+      "category": "Developer Tools"
     }
   ]
 }
diff --git a/.claude-plugin/marketplace.json b/.claude-plugin/marketplace.json
index 082fa96..2032e08 100644
--- a/.claude-plugin/marketplace.json
+++ b/.claude-plugin/marketplace.json
@@ -19,6 +19,11 @@
       "name": "claude-hooks",
       "source": "./plugins/claude-hooks",
       "description": "claude-hooks"
+    },
+    {
+      "name": "lint-kit",
+      "source": "./plugins/lint-kit",
+      "description": "Run the team's linters"
     }
   ]
 }
diff --git a/marketplace-policy.json b/marketplace-policy.json
new file mode 100644
index 0000000..245c58d
--- /dev/null
+++ b/marketplace-policy.json
@@ -0,0 +1,15 @@
+{
+  "readers": ["claude-code", "codex"],
+  "exceptions": [
+    {
+      "plugin": "claude-hooks",
+      "kind": "membership",
+      "reason": "Listed for Claude Code only: Codex does not run its prompt hooks."
+    },
+    {
+      "plugin": "codex-helper",
+      "kind": "membership",
+      "reason": "Listed for Codex only: it wraps a Codex app integration."
+    }
+  ]
+}
diff --git a/plugins/lint-kit/.claude-plugin/plugin.json b/plugins/lint-kit/.claude-plugin/plugin.json
index ed531df..8a4782d 100644
--- a/plugins/lint-kit/.claude-plugin/plugin.json
+++ b/plugins/lint-kit/.claude-plugin/plugin.json
@@ -1,6 +1,6 @@
 {
   "name": "lint-kit",
-  "version": "1.0.0",
+  "version": "1.1.0",
   "description": "Run the team's linters",
   "author": {
     "name": "Acme"
```

## Repository refs

Every branch and tag in the final repository, each with its changes against the fixture tree (`refs.txt`).

```text
master 7e24375
```
