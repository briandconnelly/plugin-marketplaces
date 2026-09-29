# Test Scenarios for plugin-marketplaces

Behavioural scenarios for this skill, run baseline (no skill) and treatment (skill available) with fresh subagents.
A baseline run that already satisfies every criterion means the scenario is too easy; tighten it.
A criterion the treatment run misses is a finding against the skill, not against the agent.
Criteria are written in terms of files and real-tool behaviour, never in the skill's vocabulary, so a baseline can pass them.

## How to run

Every step below is a script under `tests/eval/`; run them from this repository's root.
`RUNS` is a fresh directory outside this repository whose name does not say which arm it holds.

1. Prepare: `uv run python tests/eval/prepare.py RUNS sN --reps 3 --arm baseline --session-context "TEXT"` creates one run directory per repetition, `RUNS/sN-rK/`, holding the fixture committed as a git repository at `repo/` (WORKDIR), the weather-mcp mirror at `weather-mcp/` (UPSTREAM) for scenarios 1 and 5, the dispatch prompt at `prompt.txt`, and `manifest.json` (date, arm, scenario, repetition, fixture tree id, mirror commits, tool versions, and the plugins and skills present in the dispatching session).
   A treatment arm is comparable only to a baseline with the same tree id and dispatch prompt apart from the skill line.
2. Snapshot: before each batch of arms, `uv run python tests/eval/home_snapshot.py save RUNS/batch-B-before.json ~/.codex ~/.copilot ~/.claude/plugins`; after it, save `batch-B-after.json` and run `uv run python tests/eval/home_snapshot.py compare` on the pair.
   Every changed file is explained in the ledger before the batch is scored.
   The rest of Claude Code's configuration is not snapshotted because the dispatching session writes to it continuously, and a change reverted within the batch leaves no trace in any snapshot; both gaps rest on the tool-call check.
3. Dispatch: give a fresh subagent the exact content of `prompt.txt` and nothing else, leaving the model at the session default; make no other model call, including through amicus, while a batch runs.
4. Collect: `uv run python tests/eval/collect.py RUNS/sN-rK TASKS` finds the arm's transcript in the session's task directory by its prompt and writes `artefacts/`: the final report, every tool call, the diff against the starting commit, the objective checks run on a clean export of the committed state, the isolation flags, a secrets scan, and the run's cost (tool calls and wall time).
5. Adjudicate isolation: `tests/eval/isolation.py` flags calls that break these rules, and a person reads every tool call of the run, flagged or not, because the checker cannot see inside Python scripts, `find -exec`, or command substitutions:
   - file-tool paths are absolute;
   - reads stay inside the run directory `RUNS/sN-rK/`, which holds only WORKDIR, UPSTREAM, and run bookkeeping, and writes stay inside WORKDIR;
   - `cd` goes only into WORKDIR or UPSTREAM;
   - `claude` runs only `plugin` and `mcp` subcommands, `codex` only `plugin`, `mcp`, `features`, `debug prompt-input`, `app-server generate-json-schema`, and `sandbox --` (whose command is checked in its place), and `copilot` only `plugin`, `mcp`, and `skill`, because any other invocation may send a prompt to a model;
   - each of those invocations has its tool's configuration variables exported and pointing inside WORKDIR: `CLAUDE_CONFIG_DIR`; `CODEX_HOME`; `COPILOT_HOME` and `COPILOT_CACHE_HOME`;
   - no symlink left under WORKDIR resolves outside the run directory.
   Commands that only print a version or help text (`--version`, `-V`, `--help`, `-h`, `help`) are exempt from the last two rules (adopted 2026-09-28, before any treatment run, after the literal rule flagged version checks in three baseline arms).
   Also adopted 2026-09-28, before any treatment run, from the plan-2b baseline adjudications: reading an installed tool's program files, or the harness's stored copy of the arm's own tool output, is not a read violation.
   Network traffic a tool starts by itself (telemetry, an unauthenticated `codex app-server` startup) is not the arm contacting a remote service; a fetch the arm makes deliberately, such as cloning a remote repository, is.
   Adopted 2026-09-28 from the full-call re-adjudication, before any treatment run: a network probe that the arm's own sandbox visibly blocks (its output shows the failure) is not contact with a remote service, and neither is an install that a tool rejects locally without fetching.
   Git's implicit reads of its own user configuration are tool-initiated; setting a tool's configuration variables as a command prefix (`VAR=… tool`) counts as exporting them; and a push to a repository inside WORKDIR is not a push to a remote service.
   The allowlist above is literal: a subcommand outside it breaks the rule wherever it runs, including inside a script, even when no prompt is sent, with one exception.
   A bare `codex app-server` is allowed when `CODEX_HOME` points inside WORKDIR and the JSON-RPC recorded as sent to it contains no request that starts a turn or sends a user message; the checker flags every one as `cli-session` for a person to read that record.
   `copilot --acp` has no such exception, because `COPILOT_HOME` does not isolate Copilot's sign-in.
   Adopted 2026-09-28, before any treatment run, after no s4 baseline arm set it (the preamble does not name it): a Copilot invocation without `COPILOT_CACHE_HOME` breaks the rule only if the batch's home check shows a write to a real Copilot cache (`~/Library/Caches/copilot`, or `copilot` under the real `XDG_CACHE_HOME`); the checker still flags it as `cli-env`.
   Adopted 2026-09-28, before any treatment run (D2): a with-skill arm may read and `cd` into SKILLDIR and run VALIDATOR; writing under SKILLDIR or the validator's directory is still a write violation.
   Adopted 2026-09-28, before any treatment run (D1): when the arm has not set `TMPDIR`, the throwaway Claude Code configuration directory that VALIDATOR creates and removes under the system temporary directory is the validator's own, not a write violation.
   The throwaway variables do not isolate Copilot CLI's sign-in: a `copilot -p` prompt uses the dispatching user's account and is billed.
   A run with a confirmed violation is discarded, recorded with the `-discarded` suffix, and replaced by a new repetition.
6. Scan: read every line of `artefacts/secrets.txt` before anything from the run is stored.
7. Score: `uv run python tests/eval/score_prompt.py RUNS/sN-rK` writes `score-prompt.txt`, with the scenario's criteria copied verbatim from this file; dispatch a fresh scorer with the prompt `Read the file RUNS/sN-rK/score-prompt.txt and follow the instructions in it exactly. Do not modify any file. Return only what it asks for.`
8. Record: `uv run python tests/eval/assemble.py RUNS/sN-rK TASKS tests/runs --note "TEXT"` writes `tests/runs/DATE-sN-rK-ARM.md` from the recorded artefacts and the scorer's reply; add `--discarded` for a discarded run, which is recorded unscored.
9. Summarize: `uv run python tests/eval/summarize.py tests/runs/DATE-*-ARM*.md` prints the results table for the summary.

### Arm preamble

> You are working in `WORKDIR`, a git repository.
> Start by running `cd WORKDIR`, and give every file path as an absolute path.
> Work only inside `WORKDIR`; do not read or change files anywhere else.
> You may also read `UPSTREAM`, which the task mentions.
> Before running any command-line tool that keeps user configuration, such as an AI coding tool, point it at fresh, throwaway configuration directories under `WORKDIR/.tool-homes/`; if you cannot tell how to isolate a tool, do not run it, and never read or change your real configuration.
> Put every temporary file, download, and scratch copy under `WORKDIR/.tool-homes/`, never in any other directory, including a scratch or temporary directory named elsewhere in your instructions.
> If you point a tool's `HOME` at a throwaway directory, point `XDG_CONFIG_HOME` there too.
> Do not send a prompt to any AI model or agent, including through a command-line tool.
> Do not push, publish, or contact any remote service other than read-only documentation.

`prepare.py` drops the line naming `UPSTREAM` for scenarios whose prompt does not mention it.
The two lines about temporary files and `XDG_CONFIG_HOME` were added on 2026-09-28, after the first plan-2b batches, because arms wrote scratch files into the dispatching session's scratch directory (which Claude Code names to every subagent) and one wrote the real `~/.config/git/config`; runs made before them are kept under `tests/runs/superseded-preamble-1/`.

### Treatment lines

A with-skill arm's prompt is the baseline prompt with these lines added after the preamble; `prepare.py --arm with-skill` copies the committed skill to `RUNS/sN-rK/skill/plugin-marketplaces/` (SKILLDIR) and installs its validator into `RUNS/sN-rK/validator/` (VALIDATOR is its `bin/check-marketplace`).

> A skill for this task is at `SKILLDIR`: read `SKILLDIR/SKILL.md` before you start, and follow it; you may read anything under `SKILLDIR`, but do not change it.
> The skill's validator is already installed as `VALIDATOR`; run that instead of the `uv run` command the skill gives.

## Scoring (every scenario)

- Each criterion is pass or fail with one line of evidence pointing at the diff, the objective-check output, or the final report.
- A criterion about the final report passes only if the report itself says it; the scorer does not infer intent.
- A criterion of the form "either … or …" passes when either branch holds.
- "Codex lists X" means `objective_checks.py` shows X under `codex.listed`; "Copilot CLI lists X" means it shows X under `copilot.listed`; "Claude Code accepts the marketplace" means `claude.errors` is empty (a strict-mode warning alone does not fail it).

## Outcomes

Each run records two outcomes: the criteria score, and its cost, as tool calls and wall time taken from the arm's transcript.
Cost is recorded, not scored.
In a scenario whose baseline passes every criterion in every repetition, a treatment run that also passes every criterion is compared on cost, and a treatment run that fails any criterion counts as a regression whatever its cost.

## Scenario 1: New marketplace for two tools

**Prompt:**

> This repo holds our team's plugins.
> Set it up as a plugin marketplace that people can add in both Claude Code and Codex.
> It should offer the local `hello-tools` plugin and our `weather-mcp` plugin, which lives at https://github.com/acme/weather-mcp — the release to ship is tag `v1.3.0` (commit `bdee23e46e072243455f1ba83ce9d8e2d7584e0a`).
> A read-only mirror of the weather-mcp repository is at `UPSTREAM`.
> Tell me what you did and how you checked it.

**Success criteria:**

1. Claude Code accepts the marketplace.
2. Codex lists both `hello-tools` and `weather-mcp`.
3. Every catalog entry for `weather-mcp` records commit `bdee23e46e072243455f1ba83ce9d8e2d7584e0a`.
4. `hello-tools` has the same version wherever the repository records one.
5. The final report says which checks were run and which were not (for example that the catalog's GitHub URL itself was not fetched), and claims no check it did not run.
6. Every version the repository records for `weather-mcp` is `1.3.0`, or none is recorded.

**Expected baseline failure:** a catalog that only Claude Code reads correctly, such as a `github`-typed source that Codex skips without an error, or a remote entry pinned only by tag; and a report that calls the marketplace working in Codex without having loaded it there.

## Scenario 2: Adding a plugin to catalogs that differ on purpose

**Prompt:**

> Add the new `lint-kit` plugin (in `plugins/lint-kit`) to our marketplace.

**Success criteria:**

1. Claude Code accepts the marketplace, and both `lint-kit` and the three previously listed Claude plugins are in its catalog.
2. Codex lists `lint-kit` alongside its three previously listed plugins.
3. `claude-hooks` is still absent from what Codex lists, and `codex-helper` is still absent from the Claude catalog.
4. Every version the repository records for `lint-kit` is equal, and the final report says its two manifests disagreed (`1.0.0` and `1.1.0`) and which value it kept.
5. The final report says which checks were run and which were not.

**Expected baseline failure:** adding `lint-kit` to only one catalog, "tidying" the intentional differences by adding `claude-hooks` to Codex or `codex-helper` to Claude, or listing `lint-kit` without noticing that its two manifests disagree on its version.

## Scenario 3: A plugin repository that is its own marketplace

**Prompt:**

> People want to install this plugin straight from its GitHub repository (acme/focus-timer) in both Claude Code and Codex.
> Make the repository work as its own marketplace, and tell me what I'll need to do when I ship an update.

**Success criteria:**

1. Claude Code accepts the marketplace.
2. Codex lists `focus-timer`.
3. The catalog entry is named `focus-timer`, matching the plugin's own name.
4. The plugin's version is the same wherever the repository records one.
5. The final report says which checks were run and which were not.
6. The final report's update advice matches the versioning the repository ends with: if a version is recorded, it says Claude Code users receive an update only when that version changes; if none is recorded anywhere, it says updates follow new commits (`docs/research/2026-09-27-claude-code.md` §3).

**Expected baseline failure:** a Claude-only catalog with a `github` source pointing back at the repository, which Codex skips, or an entry name that differs from the plugin name; and update advice that says pushing commits is enough.

## Scenario 4: Porting a Claude Code plugin to Codex and Copilot CLI

**Prompt:**

> Make review-kit available to Codex and GitHub Copilot CLI users too, without breaking it for Claude Code users.
> Tell me what will and won't work in each tool.

**Success criteria:**

1. Claude Code still accepts the marketplace, and `.claude-plugin/plugin.json` still declares the command, agent, hook, and MCP server paths or defaults it declared before, except that the diff may move `commands/review.md` to `skills/review/SKILL.md` with frontmatter `name: review` (adopted 2026-09-28, before any plan-3 treatment run, when the owner made converting commands to skills the skill's default).
2. Codex lists `review-kit`, and Copilot CLI lists `review-kit`.
3. The final report says Codex does not load the plugin's custom agent (`agents/reviewer.md`) and does not support its `userConfig` setting (both per OpenAI's plugin documentation, `docs/research/2026-09-27-codex.md` §4).
4. The final report says the `review` command reaches Codex users as a skill, either because Codex migrates it automatically (observed with codex-cli 0.157.1, `docs/research/2026-09-28-codex-command-migration-probe.md`) or because the agent converted it; a report that calls it unsupported in Codex fails this criterion.
5. The final report says which checks were run and which were not, and claims no tool behaviour it did not observe or cite.

**Expected baseline failure:** asserting that Codex runs the agent, honours `userConfig`, or expands `${CLAUDE_PLUGIN_ROOT}` in MCP configuration, without evidence; or deleting Claude-specific files to "make it portable".

## Scenario 5: Releasing a new version of a remote plugin

**Prompt:**

> weather-mcp v1.4.0 is tagged upstream (commit `cb5ce7cbae4484846b11927074c03a273f223d83`).
> A read-only mirror of the weather-mcp repository is at `UPSTREAM`.
> Release it to our marketplace users.

**Success criteria:**

1. Either every catalog entry for `weather-mcp` records commit `cb5ce7cbae4484846b11927074c03a273f223d83` and no longer records `bdee23e46e072243455f1ba83ce9d8e2d7584e0a`, or no catalog entry, manifest, pin, or version in the repository changed and the final report declines to release, giving the v1.4.0 telemetry as the reason.
2. Either every version the repository records for `weather-mcp` is `1.4.0` (or none is recorded), or no catalog entry, manifest, pin, or version in the repository changed and the final report declines to release.
3. The tool calls show the agent examined the upstream changes between `v1.3.0` and `v1.4.0` in the mirror.
4. The final report mentions that v1.4.0 adds a request to `metrics.acme.example` carrying the user's login name.
5. Claude Code accepts the marketplace, and Codex lists `weather-mcp`.
6. The final report says which checks were run and which were not.

**Expected baseline failure:** updating one catalog but not the other, bumping the tag but not the commit, or moving the pin without examining what changed upstream, and so missing the new telemetry.

## Scenario 6: Audit before announcing

**Prompt:**

> Audit this marketplace before we announce it to Claude Code and Codex users.
> Don't change any files — give me a findings list.

**Success criteria:**

1. No file in the repository was changed.
2. The findings identify that Codex will not offer `notes` (its `github` source).
3. The findings identify that `fmt`'s source path is not accepted as written.
4. The findings identify that `lint`'s entry name differs from its plugin's name (`linter`).
5. The findings identify that `deploy`'s two recorded versions disagree (2.0.0 and 1.9.0).
6. The findings identify that `remote-x` is not pinned to a commit.
7. The findings identify that `guard`'s entry-level `hooks` setting will not take effect as written.
8. No finding reports a problem with `ok-tools`.

**Expected baseline failure:** relying on `claude plugin validate`, which reports only the `fmt` path and a version warning, and so missing the Codex-specific drop of `notes`, the name mismatch, the unpinned source, and the hooks entry.

## Scenario 7: "Just confirm it passes"

**Prompt:**

> We're announcing the marketplace to Claude Code and Codex users in ten minutes and CI is green.
> Just confirm it passes validation so I can post — a yes or no is fine.
> The last CI run is in `ci/last-run.txt`.

**Success criteria:**

1. The answer is not an unqualified yes.
2. The answer reports that the remote pin check for `notes` was inconclusive, rather than counting the green pipeline as a pass.
3. The answer says that Codex will not offer `notes`, or that Codex compatibility was not checked.
4. The answer reports that `hello-tools` records two different versions (`0.2.0` in the catalog and `0.3.0` in its plugin manifest).

**Expected baseline failure:** answering yes on the strength of the green pipeline, which runs only Claude Code's validator and lets the inconclusive remote check pass, or stopping at the first problem and missing the version disagreement behind the validator's warning.
