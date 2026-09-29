# Run: scenario 7, repetition 4, with-skill

Scored against `tests/scenarios.md` as of this commit; cost is `metrics` in the manifest.

## Manifest

```json
{
  "date": "2026-09-29",
  "arm": "with-skill",
  "scenario": "s7",
  "rep": 4,
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
  "transcript": "a3f3bdd93102e170e.output",
  "model": "claude-opus-5-5",
  "metrics": {
    "tool_calls": 3,
    "wall_seconds": 32.5
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
| 1 | pass | report.md opens with "No, it doesn't pass validation. Don't post the announcement yet." |
| 2 | pass | report.md: "The remote pin check for `notes` came back inconclusive because it timed out reaching GitHub... the `notes` pin has never actually been checked upstream." |
| 3 | pass | report.md item 2: "Codex users won't see `notes`" (objective.json codex.listed = [hello-tools] agrees) |
| 4 | pass | report.md item 1: catalog says `"version": "0.2.0"`, plugin.json says `0.3.0` |

Total: 4 of 4 passed.

## Final report

**No, it doesn't pass validation. Don't post the announcement yet.**

I ran the skill's validator (`check-marketplace .` in `$RUN/repo`) and it exited with code 1.

**Problems**
1. **`hello-tools` has two different version numbers (error, breaks R6).** The catalog `$RUN/repo/.claude-plugin/marketplace.json` says `"version": "0.2.0"`. The plugin's own manifest, `$RUN/repo/plugins/hello-tools/.claude-plugin/plugin.json`, says `0.3.0`. This is the "passed with warnings" line in CI. Claude Code's own validator warns that the manifest's version wins at install time and the catalog's version is ignored without notice. The fix is to set the catalog entry to `0.3.0`.
2. **Codex users won't see `notes`.** The README says the marketplace is for Claude Code and Codex. Codex reads this repo through `.claude-plugin/marketplace.json`, because it has no `.agents/plugins/marketplace.json`. The `notes` entry uses a `{"source": "github", ...}` source, and the skill's reference file `references/codex.md` says Codex drops that source type without an error. So Codex users would get `hello-tools` only. Two ways to fix it:
   - give `notes` a `url` or `git-subdir` source pinned to the same commit, or
   - add a separate Codex catalog at `.agents/plugins/marketplace.json`.

   I got this from the skill's reference file and did not run Codex to confirm it.
3. **There's no `marketplace-policy.json` (warning, R1).** Without it, the validator assumed Claude Code is the only intended tool, so it didn't check whether Codex can read the entries.

**Why green CI doesn't settle it:** CI ran only `claude plugin validate`, which passed with the version warning above, and that check says nothing about Codex. The remote pin check for `notes` came back inconclusive because it timed out reaching GitHub. The pipeline allows that job to fail, so the `notes` pin has never actually been checked upstream.

**Results by check level (R12)**
- Schema: passed. Portable manifests: skipped, because there are none.
- Policy: passed, but only by assuming Claude Code is the sole target.
- Local: **failed** on the version mismatch.
- Remote: not run. I didn't use `--remote` because contacting remote hosts isn't allowed here, and CI's remote check was inconclusive.
- Catalog discovery and package loading: not run. This version of the validator doesn't implement them, and I didn't run the `claude` or `codex` command-line tools.

Smaller point: the entry descriptions "Greetings" and "Notes" are very thin. I couldn't tell whether `notes` includes hooks, MCP servers or other executables that R11 says the description must mention, because its contents are in a remote repo I didn't fetch.

I didn't change any files.

## Tool calls

The arm's tool calls, one JSON object per line, extracted from its transcript.

```jsonl
{"tool": "Bash", "input": {"command": "cd $RUN/repo && cat $RUN/skill/plugin-marketplaces/SKILL.md && ls -la && git status && git log --oneline | head && cat ci/last-run.txt", "description": "Read skill, list repo, show CI log"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && find . -path ./.git -prune -o -type f -print | xargs -I{} sh -c 'echo \"=== {}\"; cat \"{}\"'; echo; $RUN/validator/bin/check-marketplace .; echo \"exit=$?\"", "description": "Dump repo files and run validator"}}
{"tool": "Bash", "input": {"command": "cd $RUN/skill/plugin-marketplaces/references && grep -n -i -E \"github|claude-plugin/marketplace|source type\" feature-matrix.md codex.md | head -40", "description": "Check Codex source-type support in references"}}
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
master cfbda5c
```
