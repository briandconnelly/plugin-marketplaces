# Run: scenario 2, repetition 1, with-skill

Scored against `tests/scenarios.md` as of this commit; cost is `metrics` in the manifest.

## Manifest

```json
{
  "date": "2026-09-28",
  "arm": "with-skill",
  "scenario": "s2",
  "rep": 1,
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
  "transcript": "a2e0f41b70a212ac6.output",
  "model": "claude-opus-5-5",
  "metrics": {
    "tool_calls": 12,
    "wall_seconds": 105.0
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
(none)
```

Batch 1. Every tool call read; no violation. Secret-scan hits are 'token cost' text from claude plugin details.

## Score

| Criterion | Result | Evidence |
|---|---|---|
| 1 | pass | objective.json `claude.errors` is `[]`; the final `.claude-plugin/marketplace.json` lists alpha-notes, branch-tidy, claude-hooks and lint-kit (diff.patch only adds lint-kit, so the original three are kept). |
| 2 | pass | objective.json `codex.listed` = alpha-notes, branch-tidy, codex-helper, lint-kit. |
| 3 | pass | objective.json `codex.listed` has no claude-hooks; the final `.claude-plugin/marketplace.json` has no codex-helper entry. |
| 4 | pass | The repo's only lint-kit versions are `plugins/lint-kit/plugin.json` and `plugins/lint-kit/.claude-plugin/plugin.json`, both 1.1.0 (diff.patch changes 1.0.0 to 1.1.0). report.md says "plugins/lint-kit/plugin.json said 1.1.0 and plugins/lint-kit/.claude-plugin/plugin.json said 1.0.0 ... I set both to **1.1.0**". |
| 5 | pass | report.md's "Checks" table names the checks run (format, local rules, Claude/Codex listing, Claude loading) and the ones not run (Codex skill-load command "I did not run", Copilot CLI "Not run", remote sources not applicable). |

Total: 5 of 5 passed.

## Final report

lint-kit is now in both marketplace catalogs, and Claude Code and Codex each list and install it at version 1.1.0. Nothing is committed.

**Decision for you: the version.** lint-kit's two manifests recorded different versions: `plugins/lint-kit/plugin.json` said 1.1.0 and `plugins/lint-kit/.claude-plugin/plugin.json` said 1.0.0. Left as is, Claude Code users would have received 1.0.0 and Codex users 1.1.0. I set both to **1.1.0**. It is the higher value, and lint-kit was not in any catalog yet, so nobody has installed either one. If 1.1.0 was a typo and 1.0.0 is right, change it in both manifests.

**Changes** (all under `$RUN/repo/`):
- **`.claude-plugin/marketplace.json`:** added the lint-kit entry pointing at `./plugins/lint-kit`, described as "Run the team's linters". lint-kit contains only a skill, so there are no hooks, servers or `bin/` to mention in the description.
- **`.agents/plugins/marketplace.json`:** added the lint-kit entry with the same fields as the existing entries.
- **`plugins/lint-kit/.claude-plugin/plugin.json`:** version changed from 1.0.0 to 1.1.0.
- **`marketplace-policy.json` (new):** lists the target tools as Claude Code and Codex. It also records why `claude-hooks` is only in the Claude Code catalog and `codex-helper` only in the Codex catalog, using the reasons already in `README.md`. The validator only accepts those reasons from this file, so it failed before I touched anything. This file is what makes it pass.

**Second decision:** GitHub Copilot CLI would also read `.claude-plugin/marketplace.json`. I did not add it to the policy file because nothing in the repo says whether you target it. If you do, add `"copilot-cli"` to `readers`.

**Checks** (tools run with throwaway settings and network blocked):
| Check | Result |
|---|---|
| Format checks | Passed. The skill's validator ran clean, and `claude plugin validate --strict` gave 0 errors and 0 warnings. |
| Local rules | Passed. Before my edits this failed on the two undocumented membership differences. On a scratch copy with the 1.0.0 value put back, it did catch the version mismatch, so a pass here is meaningful. |
| Remote sources | Not applicable: every source is a local path. |
| Listing in Claude Code 2.1.284 | Passed: adding the marketplace succeeded. |
| Listing in Codex 0.157.1 | Passed: all four expected plugins are listed, including lint-kit at 1.1.0. |
| Loading in Claude Code | Passed: installed at 1.1.0, with its one skill and nothing else. |
| Loading in Codex | Installed at 1.1.0. I did not run the command that would show whether Codex actually loads the skill. |
| Copilot CLI | Not run, because it is not a declared target. |

The scratch copies and throwaway tool settings are in `$RUN/repo/.tool-homes/`. It is untracked and should not be committed.

## Tool calls

The arm's tool calls, one JSON object per line, extracted from its transcript.

```jsonl
{"tool": "Read", "input": {"file_path": "$RUN/skill/plugin-marketplaces/SKILL.md"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && git status && find . -path ./.git -prune -o -type f -print | head -50 && ls -R $RUN/skill/plugin-marketplaces"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && for f in README.md .claude-plugin/marketplace.json .agents/plugins/marketplace.json plugins/lint-kit/plugin.json plugins/lint-kit/.claude-plugin/plugin.json plugins/lint-kit/skills/lint-kit/SKILL.md plugins/*/.claude-plugin/plugin.json plugins/codex-helper/.codex-plugin/plugin.json; do echo \"=== $f\"; cat \"$f\"; done; ls -la plugins/lint-kit; git log --oneline | head"}}
{"tool": "Bash", "input": {"command": "cd $RUN/skill/plugin-marketplaces/references && cat releases.md validation.md"}}
{"tool": "Bash", "input": {"command": "cd $RUN/skill/plugin-marketplaces && cat scripts/mpcheck/policy.py; cat references/multi-tool.md; grep -n -i \"policy\" references/*.md | head -40"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=\"$PWD/.tool-homes\"; mkdir -p \"$T/tmp\"; export TMPDIR=\"$T/tmp\"; which claude codex copilot; $RUN/validator/bin/check-marketplace . ; echo \"exit $?\""}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && python3 - <<'EOF'\nimport json\ndef rw(p, f):\n    d = json.load(open(p)); f(d)\n    open(p, \"w\").write(json.dumps(d, indent=2) + \"\\n\")\nrw(\"plugins/lint-kit/.claude-plugin/plugin.json\", lambda d: d.__setitem__(\"version\", \"1.1.0\"))\nrw(\".claude-plugin/marketplace.json\", lambda d: d[\"plugins\"].append(\n    {\"name\": \"lint-kit\", \"source\": \"./plugins/lint-kit\", \"description\": \"Run the team's linters\"}))\nrw(\".agents/plugins/marketplace.json\", lambda d: d[\"plugins\"].append(\n    {\"name\": \"lint-kit\", \"source\": {\"source\": \"local\", \"path\": \"./plugins/lint-kit\"},\n     \"policy\": {\"installation\": \"AVAILABLE\", \"authentication\": \"ON_INSTALL\"},\n     \"category\": \"Developer Tools\"}))\nEOF\ncat > marketplace-policy.json <<'EOF'\n{\n  \"readers\": [\"claude-code\", \"codex\"],\n  \"exceptions\": [\n    {\n      \"plugin\": \"claude-hooks\",\n      \"kind\": \"membership\",\n      \"reason\": \"Listed for Claude Code only: Codex does not run its prompt hooks (README.md, Catalog notes).\"\n    },\n    {\n      \"plugin\": \"codex-helper\",\n      \"kind\": \"membership\",\n      \"reason\": \"Listed for Codex only: it wraps a Codex app integration (README.md, Catalog notes).\"\n    }\n  ]\n}\nEOF\ngit diff; T=\"$PWD/.tool-homes\"; export TMPDIR=\"$T/tmp\"; $RUN/validator/bin/check-marketplace . ; echo \"exit $?\""}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=\"$PWD/.tool-homes\"; export TMPDIR=\"$T/tmp\"; rm -rf \"$T/neg\" \"$T/export\"; mkdir -p \"$T/neg\" \"$T/export\"; rsync -a --exclude .git --exclude .tool-homes ./ \"$T/export/\"; rsync -a \"$T/export/\" \"$T/neg/\"; sed -i '' 's/\"1.1.0\"/\"1.0.0\"/' \"$T/neg/plugins/lint-kit/.claude-plugin/plugin.json\"; $RUN/validator/bin/check-marketplace \"$T/neg\" | grep -E \"local|ERROR\"; echo \"exit ${PIPESTATUS[0]}\""}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=\"$PWD/.tool-homes\" && mkdir -p \"$T\"/{home,xdg,tmp,claude,codex,copilot,copilot-cache} && : > \"$T/gitconfig\" && export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\" && SB=\"sandbox-exec -p (version 1)(allow default)(deny network-outbound (remote ip))\" && E=\"$T/export\" &&\necho \"--- claude version\"; $SB claude --version </dev/null\necho \"--- claude validate\"; $SB claude plugin validate \"$E\" --strict --json </dev/null; echo \"rc=$?\"\necho \"--- claude add\"; $SB claude plugin marketplace add \"$E\" </dev/null; echo \"rc=$?\"\necho \"--- claude install\"; $SB claude plugin install lint-kit@acme-tools </dev/null; echo \"rc=$?\"\necho \"--- claude details\"; $SB claude plugin details lint-kit@acme-tools </dev/null; echo \"rc=$?\"\necho \"--- claude list\"; $SB claude plugin list --json </dev/null; echo \"rc=$?\"", "timeout": 300000}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=\"$PWD/.tool-homes\" && export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\" && sb(){ sandbox-exec -p '(version 1)(allow default)(deny network-outbound (remote ip))' \"$@\" </dev/null; } && E=\"$T/export\" &&\necho \"--- claude version\"; sb claude --version\necho \"--- claude validate\"; sb claude plugin validate \"$E\" --strict --json; echo \"rc=$?\"\necho \"--- claude add\"; sb claude plugin marketplace add \"$E\"; echo \"rc=$?\"\necho \"--- claude install\"; sb claude plugin install lint-kit@acme-tools; echo \"rc=$?\"\necho \"--- claude details\"; sb claude plugin details lint-kit@acme-tools; echo \"rc=$?\"\necho \"--- claude list\"; sb claude plugin list --json; echo \"rc=$?\"", "timeout": 300000}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=\"$PWD/.tool-homes\" && export HOME=\"$T/home\" XDG_CONFIG_HOME=\"$T/xdg\" TMPDIR=\"$T/tmp\" GIT_CONFIG_GLOBAL=\"$T/gitconfig\" GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR=\"$T/claude\" CODEX_HOME=\"$T/codex\" COPILOT_HOME=\"$T/copilot\" COPILOT_CACHE_HOME=\"$T/copilot-cache\" && sb(){ sandbox-exec -p '(version 1)(allow default)(deny network-outbound (remote ip))' \"$@\" </dev/null; } && E=\"$T/export\" &&\necho \"--- codex version\"; sb codex --version\necho \"--- codex add\"; sb codex plugin marketplace add \"$E\"; echo \"rc=$?\"\necho \"--- codex list\"; sb codex plugin list --available --json; echo \"rc=$?\"\necho \"--- codex install\"; sb codex plugin add lint-kit@acme-tools --json; echo \"rc=$?\"", "timeout": 300000}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && git status --short"}}
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
index 0000000..abf9af5
--- /dev/null
+++ b/marketplace-policy.json
@@ -0,0 +1,15 @@
+{
+  "readers": ["claude-code", "codex"],
+  "exceptions": [
+    {
+      "plugin": "claude-hooks",
+      "kind": "membership",
+      "reason": "Listed for Claude Code only: Codex does not run its prompt hooks (README.md, Catalog notes)."
+    },
+    {
+      "plugin": "codex-helper",
+      "kind": "membership",
+      "reason": "Listed for Codex only: it wraps a Codex app integration (README.md, Catalog notes)."
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
master f26c685
```
