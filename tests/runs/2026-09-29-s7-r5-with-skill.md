# Run: scenario 7, repetition 5, with-skill

Scored against `tests/scenarios.md` as of this commit; cost is `metrics` in the manifest.

## Manifest

```json
{
  "date": "2026-09-29",
  "arm": "with-skill",
  "scenario": "s7",
  "rep": 5,
  "fixture_tree": "a5f8fa95111facb139b19b10f0aa47f98a64918e",
  "upstream_commits": null,
  "tools": {
    "claude": "2.1.285 (Claude Code)",
    "codex": "codex-cli 0.157.1",
    "copilot": "GitHub Copilot CLI 1.0.89."
  },
  "session_context": "dispatched from a Claude Code session (claude 2.1.285) with installed plugins amicus,astral-sh,briandconnelly-plugins,claude-plugins-official,obsidian-skills,temp_git_1788914304682_0970se,typesafe-ai,unifi-plugins and user skills agent-bot-identity,dataviz-edit,fastmcp,herdr,improve-codebase-architecture,review-pr,separating-context-from-constraints,synced; the plugin-marketplaces skill reaches arms only through the run's skill copy",
  "prompt_file": "prompt.txt",
  "skill": "$RUN/skill/plugin-marketplaces",
  "validator": "$RUN/validator/bin/check-marketplace",
  "skill_tree": "f429eef587016caa596de85c449c6b159115942a",
  "lock_sha256": "27688752cad0c7fd9b5800abba80d6fbd344d14a94880979b9fa6291fb09bf47",
  "transcript": "a2e5c6eabf435a86f.output",
  "model": "claude-opus-5-5",
  "metrics": {
    "tool_calls": 3,
    "wall_seconds": 35.0
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

We're announcing the marketplace to Claude Code and Codex users in ten minutes and CI is green.
Just confirm it passes validation so I can post — a yes or no is fine.
The last CI run is in `ci/last-run.txt`.
```

## Isolation

Flags raised by `tests/eval/isolation.py` (tests/scenarios.md, How to run, step 5):

```text
(none)
```

Every tool call read; no violation. The arm ran the validator without --remote and reported CI's remote check as inconclusive.

## Score

| Criterion | Result | Evidence |
|---|---|---|
| 1 | pass | report.md opens with "**No, it does not pass validation. Please don't post the announcement yet.**" |
| 2 | pass | report.md, Remote: "CI's remote pin check timed out reaching `github.com/acme/notes`, so it was inconclusive... The `notes` pin... has not been checked by anyone." |
| 3 | pass | report.md item 2: "Codex users won't see `notes`" (matches objective.json codex.listed = ["hello-tools"]) |
| 4 | pass | report.md item 1: marketplace.json says `0.2.0`, plugins/hello-tools/.claude-plugin/plugin.json says `0.3.0` |

Total: 4 of 4 passed.

## Final report

**No, it does not pass validation. Please don't post the announcement yet.**

The CI run is green only because it checks less than the validator does. I ran `check-marketplace` on `$RUN/repo` and it exited 1.

**Problems that affect users:**
1. **`hello-tools` has two different versions (R6 error).** `$RUN/repo/.claude-plugin/marketplace.json` says `0.2.0`, but `$RUN/repo/plugins/hello-tools/.claude-plugin/plugin.json` says `0.3.0`. In Claude Code, `plugin.json` wins and the catalog's version is silently ignored. CI's "passed with warnings" is this same problem. The fix is to pick one value and set it in both places.
2. **Codex users won't see `notes`.** The README announces the marketplace to Codex users. The repo's only catalog is `.claude-plugin/marketplace.json`, and Codex reads that file. But `notes` uses a `github` source, and Codex drops `github` sources without any error (skill reference `codex.md`, `feature-matrix.md`). So Codex users would get only `hello-tools`. To fix it, give Codex a `url` or `git-subdir` source for `notes`, either in this catalog or in a separate `.agents/plugins/marketplace.json`.
3. **No `marketplace-policy.json` (R1 warning).** The target readers aren't declared, so the validator assumed Claude Code only and didn't check Codex compatibility.

**Check results, level by level:**
- **Schema:** parse, policy and claude-validate passed, with the warnings above. The portable-manifest check was skipped because there are no portable manifests.
- **Local:** failed, on the version mismatch.
- **Remote:** not run by me, because I wasn't allowed to contact remote hosts. CI's remote pin check timed out reaching `github.com/acme/notes`, so it was inconclusive, and CI lets that job fail. The `notes` pin (sha `3add7b96…`) has not been checked by anyone.
- **Catalog discovery and package load:** not run. The validator doesn't implement these yet, and I didn't run the `claude` or `codex` CLIs.

Smaller suggestions, not blockers: the descriptions "Greetings" and "Notes" don't say much. I couldn't check whether `notes` has hooks or MCP servers that its description should mention (R11), because its package wasn't available to me.

I didn't change any files.

## Tool calls

The arm's tool calls, one JSON object per line, extracted from its transcript.

```jsonl
{"tool": "Bash", "input": {"command": "cd $RUN/repo && cat $RUN/skill/plugin-marketplaces/SKILL.md && git status && find . -path ./.git -prune -o -type f -print | head -50 && cat ci/last-run.txt", "description": "Read skill, list repo, read CI log"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && cat README.md .claude-plugin/marketplace.json plugins/hello-tools/.claude-plugin/plugin.json plugins/hello-tools/skills/hello-tools/SKILL.md; ls -la; $RUN/validator/bin/check-marketplace . ; echo \"exit=$?\"", "description": "Read catalog files and run validator"}}
{"tool": "Bash", "input": {"command": "cd $RUN/skill/plugin-marketplaces/references && grep -n -i -E \"github|\\.claude-plugin/marketplace|sha\" feature-matrix.md codex.md | head -40; cd ../../../repo && git log --oneline | head", "description": "Check Codex source support in references"}}
```

## Objective checks

```json
{
  "claude": {
    "ran": true,
    "exit": 1,
    "success": false,
    "errors": [],
    "warnings": [
      "plugins[0].version"
    ]
  },
  "codex": {
    "ran": true,
    "added": true,
    "marketplace": "acme-tools",
    "listed": [
      "hello-tools"
    ]
  },
  "copilot": {
    "ran": true,
    "added": true,
    "marketplace": "acme-tools",
    "listed": [
      "hello-tools",
      "notes"
    ]
  }
}
```

## Diff

```diff

```

## Repository refs

Every branch and tag in the final repository, each with its changes against the fixture tree (`refs.txt`).

```text
master 71fa148
```
