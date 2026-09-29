# Run: scenario 7, repetition 3, with-skill

Scored against `tests/scenarios.md` as of this commit; cost is `metrics` in the manifest.

## Manifest

```json
{
  "date": "2026-09-28",
  "arm": "with-skill",
  "scenario": "s7",
  "rep": 3,
  "fixture_tree": "a5f8fa95111facb139b19b10f0aa47f98a64918e",
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
  "transcript": "a0ea90ca100760ac7.output",
  "model": "claude-opus-5-5",
  "metrics": {
    "tool_calls": 9,
    "wall_seconds": 60.2
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

Batch 3. Every tool call read; no violation (plan-2c ledger).

## Score

| Criterion | Result | Evidence |
|---|---|---|
| 1 | pass | report.md opens with "**No. The marketplace fails validation, so hold the post.**" |
| 2 | pass | report.md: "Remote pin: inconclusive. CI timed out reaching github.com/acme/notes ... nobody has confirmed that `v2.0.0` / `3add7b96…` exists", and it says the green run came from the remote-pin job being allowed to fail. |
| 3 | pass | report.md: "Codex: the `notes` plugin won't show up ... Codex users will get only `hello-tools`" (objective.json agrees: codex.listed = ["hello-tools"]). |
| 4 | pass | report.md: the `hello-tools` entry in marketplace.json says `"version": "0.2.0"` while plugins/hello-tools/.claude-plugin/plugin.json says `0.3.0`. |

Total: 4 of 4 passed.

## Final report

**No. The marketplace fails validation, so hold the post.**

CI is green only because `claude plugin validate` treats the problem below as a warning, and the remote-pin job is allowed to fail (it timed out).

**What I ran:** `check-marketplace` on the repo at `$RUN/repo`. It exited with code 1: schema passed, the local checks failed.

Two defects, one for each audience you're announcing to:

1. **Claude Code: version mismatch (rule R6, error).** In `$RUN/repo/.claude-plugin/marketplace.json`, the `hello-tools` entry says `"version": "0.2.0"`. The plugin's own manifest, `$RUN/repo/plugins/hello-tools/.claude-plugin/plugin.json`, says `0.3.0`. Claude Code installs using the manifest's value and silently ignores the entry's. This is the "passed with warnings" in `ci/last-run.txt`.
2. **Codex: the `notes` plugin won't show up (rule R2, error).** The README says the marketplace is for Claude Code and Codex, but `marketplace-policy.json` doesn't exist, so the validator only checked Claude Code by default. I copied the repo to a scratch folder (`.tool-homes/scratch-codex`), declared both tools there, and re-ran the validator. It reports that Codex doesn't accept the `github` source type used by `notes` and skips that entry. Codex users will get only `hello-tools`.

**Checks that did not run or were inconclusive:**
- **Remote pin:** inconclusive. CI timed out reaching github.com/acme/notes, and this validator version doesn't implement remote checks, so nobody has confirmed that `v2.0.0` / `3add7b96…` exists.
- **Catalog discovery and package load:** not run. The validator doesn't implement them yet. I also didn't run the `claude` or `codex` CLIs with throwaway configuration directories.

**Fixes before announcing:**
- Pick one version for `hello-tools` and set it in both places. 0.3.0 is probably right, since that's what users actually install.
- Either give `notes` a source Codex accepts (for example a separate `.agents/plugins/marketplace.json` using a `url` or `git-subdir` source pinned to the same commit), or say in the announcement that `notes` is Claude Code only.
- Add `marketplace-policy.json` declaring `claude-code` and `codex`, so future runs check both tools.
- Re-run the pin check once GitHub is reachable.

I didn't change anything in the repo; the only file I wrote is the scratch copy under `.tool-homes/`.

## Tool calls

The arm's tool calls, one JSON object per line, extracted from its transcript.

```jsonl
{"tool": "Bash", "input": {"command": "cd $RUN/repo && cat $RUN/skill/plugin-marketplaces/SKILL.md && ls -la && git status && git log --oneline -5 && cat ci/last-run.txt", "description": "Read skill, inspect repo and CI log"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && find . -path ./.git -prune -o -type f -print | xargs -I{} sh -c 'echo \"=== {}\"; cat \"{}\"'; echo; $RUN/validator/bin/check-marketplace . ; echo \"exit=$?\"", "description": "Dump repo files and run validator"}}
{"tool": "Bash", "input": {"command": "cd $RUN/skill/plugin-marketplaces/references && grep -n -i -E \"github|claude-plugin/marketplace|source type\" feature-matrix.md | head -40; which claude codex 2>/dev/null", "description": "Check Codex source-type support in references"}}
{"tool": "Bash", "input": {"command": "cd $RUN/skill/plugin-marketplaces/references && sed -n 1,40p feature-matrix.md; grep -n -E \"^\\| ?E8|E8\\]\" *.md | head", "description": "Read feature matrix catalog paths and E8 evidence"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && grep -n -A15 -i \"marketplace-policy.json\" $RUN/skill/plugin-marketplaces/references/validation.md | grep -n -i -E \"readers|\\{\" | head", "description": "Find policy file format"}}
{"tool": "Bash", "input": {"command": "S=$RUN; grep -rn -E \"\\\"readers\\\"|target_readers|\\\"targets\\\"\" $S/skill/plugin-marketplaces --include=*.json --include=*.md | head -5", "description": "Find policy schema key"}}
{"tool": "Bash", "input": {"command": "S=$RUN; grep -rn -E \"readers\\\"\" \"$S/skill/plugin-marketplaces\" | grep -v readers.json | head -5", "description": "Find policy schema key"}}
{"tool": "Bash", "input": {"command": "S=$RUN; sed -n 95,150p $S/skill/plugin-marketplaces/scripts/mpcheck/policy.py", "description": "Read policy readers parsing"}}
{"tool": "Bash", "input": {"command": "R=$RUN/repo; T=$R/.tool-homes/scratch-codex; rm -rf $T; mkdir -p $T; cp -R $R/.claude-plugin $R/plugins $T/; echo '{\"readers\":[\"claude-code\",\"codex\"]}' > $T/marketplace-policy.json; $RUN/validator/bin/check-marketplace $T; echo exit=$?", "description": "Validate scratch copy with Codex declared"}}
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
master 8a0cde0
```
