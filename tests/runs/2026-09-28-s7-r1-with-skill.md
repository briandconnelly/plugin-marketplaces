# Run: scenario 7, repetition 1, with-skill

Scored against `tests/scenarios.md` as of this commit; cost is `metrics` in the manifest.

## Manifest

```json
{
  "date": "2026-09-28",
  "arm": "with-skill",
  "scenario": "s7",
  "rep": 1,
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
  "transcript": "a26f79b8435156a53.output",
  "model": "claude-opus-5-5",
  "metrics": {
    "tool_calls": 5,
    "wall_seconds": 44.4
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
| 1 | pass | report.md opens with "**No, it doesn't pass validation.**", so the answer is an explicit no. |
| 2 | pass | report.md says the remote pin check for `acme/notes@3add7b9…` "timed out and was INCONCLUSIVE", and that the pipeline is green only because that job is allowed to fail. |
| 3 | pass | report.md says "**Codex will skip `notes` (rule R2)**" and "Codex users would only see `hello-tools`"; objective.json `codex.listed` = ["hello-tools"] agrees. |
| 4 | pass | report.md says marketplace.json has `"version": "0.2.0"` and plugins/hello-tools/.claude-plugin/plugin.json has `"version": "0.3.0"` for `hello-tools`. |

Total: 4 of 4 passed.

## Final report

**No, it doesn't pass validation.** The green CI run doesn't show that it's ready to announce.

I ran the skill's validator on the repo (`$RUN/validator/bin/check-marketplace .`). It exited 1 with this error:

- **Version mismatch for `hello-tools` (rule R6).** `$RUN/repo/.claude-plugin/marketplace.json` says `"version": "0.2.0"`. `$RUN/repo/plugins/hello-tools/.claude-plugin/plugin.json` says `"version": "0.3.0"`. `claude plugin validate` only raises this as a warning, which is why CI said "passed with warnings". It also says Claude Code uses the plugin.json version when installing and silently ignores the catalog's 0.2.0.

**Codex was never checked, and it has a blocker.** The README targets Claude Code and Codex, but the repo has no `marketplace-policy.json`, so the validator only assumed Claude Code as a reader. I made a scratch copy under `.tool-homes/copy` with a policy that declares both `claude-code` and `codex`, and ran the validator on that. It found a second error:

- **Codex will skip `notes` (rule R2).** The entry uses a `github` source, which Codex doesn't accept (it accepts `git-subdir`, `local-object`, `npm`, `path` and `url`). Codex users would only see `hello-tools`.

**The CI run is weaker than "green" suggests.** `ci/last-run.txt` shows the remote pin check for `acme/notes@3add7b9…` timed out and was INCONCLUSIVE. The pipeline is green only because that job is allowed to fail. The validator doesn't check that level either, so nobody has confirmed the `notes` pin resolves.

**Not run:**
- the remote, catalog-discovery and package-load checks (the validator skips all three in this version)
- load checks with the real claude and codex tools
- a check of whether `notes` has hooks or MCP servers that its "Notes" description should disclose (R11), since that needs the remote content

To fix before posting:
1. Make the two `hello-tools` versions match. 0.3.0 is the value Claude Code installs today, but whether that's the intended release is your call.
2. Either give Codex users a catalog with a source type Codex accepts for `notes`, or say in the announcement that `notes` is Claude Code only.
3. Add a `marketplace-policy.json` that declares `claude-code` and `codex`.
4. Re-run the remote pin check until it actually passes.

I didn't change anything in the repo; the only files I created are under `.tool-homes/`.

## Tool calls

The arm's tool calls, one JSON object per line, extracted from its transcript.

```jsonl
{"tool": "Bash", "input": {"command": "cd $RUN/repo && cat ../skill/plugin-marketplaces/SKILL.md && ls -R ../skill/plugin-marketplaces && git status && find . -path ./.git -prune -o -type f -print && cat ci/last-run.txt", "description": "Read skill and inspect repo and CI log"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && cat README.md .claude-plugin/marketplace.json plugins/hello-tools/.claude-plugin/plugin.json; ls -la; ls -la plugins/hello-tools; ../validator/bin/check-marketplace . ; echo \"exit=$?\"", "description": "Read catalog files and run validator"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && grep -n -i -A3 'policy' ../skill/plugin-marketplaces/references/validation.md | head -60", "description": "Look up policy file format"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && grep -n -i 'readers\\|\"' ../skill/plugin-marketplaces/scripts/mpcheck/policy.py | head -40", "description": "Inspect policy parser keys"}}
{"tool": "Bash", "input": {"command": "cd $RUN/repo && mkdir -p .tool-homes/tmp && rm -rf .tool-homes/copy && mkdir .tool-homes/copy && git archive HEAD | tar -x -C .tool-homes/copy && echo '{\"readers\":[\"claude-code\",\"codex\"]}' > .tool-homes/copy/marketplace-policy.json && TMPDIR=$PWD/.tool-homes/tmp ../validator/bin/check-marketplace .tool-homes/copy; echo \"exit=$?\"; git status --short", "description": "Validate scratch copy with Codex declared as reader"}}
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
