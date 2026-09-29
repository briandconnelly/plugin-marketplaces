# Run: scenario 7, repetition 2, with-skill

Scored against `tests/scenarios.md` as of this commit; cost is `metrics` in the manifest.

## Manifest

```json
{
  "date": "2026-09-28",
  "arm": "with-skill",
  "scenario": "s7",
  "rep": 2,
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
  "transcript": "a6f1cb9a5449e0ebd.output",
  "model": "claude-opus-5-5",
  "metrics": {
    "tool_calls": 5,
    "wall_seconds": 48.5
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

Batch 1. Every tool call read; no violation. Secret-scan hits are 'token cost' text from claude plugin details.

## Score

| Criterion | Result | Evidence |
|---|---|---|
| 1 | pass | report.md opens with "**No, don't post yet. The marketplace fails validation.**" |
| 2 | pass | report.md: "Its remote pin check was inconclusive and is allowed to fail" and "Remote: inconclusive... nobody has confirmed that the `notes` commit `3add7b96…` exists" |
| 3 | pass | report.md: "Codex users won't see `notes`" (objective.json agrees: codex.listed = ["hello-tools"] only) |
| 4 | pass | report.md: "The catalog entry says `0.2.0` in `.claude-plugin/marketplace.json`, but the plugin's manifest says `0.3.0` in `plugins/hello-tools/.claude-plugin/plugin.json`" |

Total: 4 of 4 passed.

## Final report

**No, don't post yet. The marketplace fails validation.** The green CI result doesn't mean what it looks like: CI only runs `claude plugin validate .`, which "passed with warnings". Its remote pin check was inconclusive and is allowed to fail. Nothing in CI checks the catalog against Codex.

**Blockers:**
1. **Version mismatch for `hello-tools` (rule R6, validator error).** The catalog entry says `0.2.0` in `.claude-plugin/marketplace.json`, but the plugin's manifest says `0.3.0` in `plugins/hello-tools/.claude-plugin/plugin.json`. Claude Code's own validator raised this as the warning CI passed over: at install time `plugin.json` wins and the catalog's version is silently ignored. Fix: set the entry to `0.3.0`, if that's the version you mean to release.
2. **Codex users won't see `notes` (rule R2).** The entry uses a `{"source": "github", ...}` source, and Codex drops that source type silently, with no error. The skill's reference (`references/codex.md`) says a `url` or `git-subdir` source for the same repository is listed. This only shows up once Codex is declared as a reader. The repo has no `marketplace-policy.json` yet, so the validator had only inferred Claude Code as a reader and warned about the missing policy file. I declared Codex in a throwaway copy and got a validator error on this entry. Fix: switch `notes` to a `url` source with the same `sha`, and add a `marketplace-policy.json` that lists `claude-code` and `codex`.

**Checks, one level at a time:**
- **Schema:** passed. The format checks and the validator's own run of `claude plugin validate` found no errors, only the version warning above.
- **Local:** failed, with the two errors above. Exit code 1 on both the repo as it stands and the throwaway copy with Codex declared.
- **Remote:** inconclusive. CI could not reach github.com/acme/notes (it timed out), and this validator version doesn't check pins. I didn't run a remote check either, so nobody has confirmed that the `notes` commit `3add7b96…` exists.
- **Catalog discovery and package load:** not run for Claude Code, Codex or Copilot CLI. I didn't run those tools' add/list/install commands.

I changed no files in the repo. The throwaway copy is at `$RUN/repo/.tool-homes/copy`.

## Tool calls

The arm's tool calls, one JSON object per line, extracted from its transcript.

```jsonl
{"tool": "Bash", "input": {"command": "cd $RUN/repo && cat $RUN/skill/plugin-marketplaces/SKILL.md && ls -R $RUN/skill/plugin-marketplaces && git status && git log --oneline | head && find . -path ./.git -prune -o -type f -print && cat ci/last-run.txt", "description": "Read skill and inspect repo"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && cat README.md .claude-plugin/marketplace.json plugins/hello-tools/.claude-plugin/plugin.json plugins/hello-tools/skills/hello-tools/SKILL.md; echo ---; $RUN/validator/bin/check-marketplace . ; echo \"exit=$?\"; cat $RUN/skill/plugin-marketplaces/references/validation.md", "description": "Read catalog files and run validator"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && S=$RUN/skill/plugin-marketplaces; grep -n -i -E \"github|source|claude-plugin/marketplace\" $S/references/codex.md | head -40; grep -n -A12 -i \"policy\" $S/references/multi-tool.md | head -40; which claude codex copilot", "description": "Check Codex source support and tool availability"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && S=$RUN/skill/plugin-marketplaces; T=$PWD/.tool-homes; mkdir -p $T/copy $T/tmp && git archive HEAD | tar -x -C $T/copy && grep -rn -i \"readers\" $S/scripts/mpcheck/policy.py | head -8", "description": "Make scratch copy and inspect policy format"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && T=$PWD/.tool-homes; sed -n 25,60p $RUN/skill/plugin-marketplaces/scripts/mpcheck/policy.py; echo '{\"readers\":[\"claude-code\",\"codex\"]}' > $T/copy/marketplace-policy.json; TMPDIR=$T/tmp $RUN/validator/bin/check-marketplace $T/copy; echo exit=$?", "description": "Validate scratch copy with Codex declared as reader"}}
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
master 843c4f0
```
