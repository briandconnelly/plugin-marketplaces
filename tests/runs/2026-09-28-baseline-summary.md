# Baseline summary (plan 2a, RED phase)

Date: 2026-09-28.
Arms: fresh `general-purpose` subagents with no access to this repository or the skill, one run per scenario, dispatched from a Claude Code session with claude 2.1.283, codex-cli 0.157.1, and copilot 1.0.88 installed.
Per-run evidence is in `tests/runs/2026-09-28-sN-baseline.md` for scored runs and `tests/runs/2026-09-28-sN-baseline-discarded.md` for discarded ones, which are kept, unscored, so the observations drawn from them can be audited; the table below was generated from those records and the arms' transcripts.

## Results

| Scenario | Result | Criteria failed | Tool calls | Wall time (s) | Status |
| --- | --- | --- | --- | --- | --- |
| s1 | — | — | 26 | 249 | discarded (wrote outside workdir; fixture weakness) |
| s2 | 5/5 | none | 6 | 48 | scored |
| s3 | 5/5 | none | 14 | 116 | scored |
| s3-rep2 | — | — | 21 | 164 | extra rep, invalid (wrote outside workdir) |
| s4 | — | — | 59 | 777 | discarded (sent prompts to Copilot, Codex, and Claude Code; fixture flaw) |
| s5 | 3/6 | 1, 2, 6 | 3 | 33 | scored |
| s6 | 7/8 | 8 | 18 | 150 | scored |
| s7 | 3/3 | none | 10 | 74 | scored |

## What the baselines show

The baselines are strong: three of five scored arms passed every criterion, and s6 found all six seeded defects.
The arms got there by probing the real tools, not from prior knowledge: they loaded catalogs into throwaway Codex and Copilot homes, installed plugins, and diffed what each tool listed.
The scenarios as written therefore do not discriminate on outcome, and plan 2b must either change them or measure something else.

Three things likely inflate the baselines, and plan 2b should separate them before any treatment run:

1. The arm preamble names `claude`, `codex`, and `copilot` and explains how to isolate them, which invites live probing that an ordinary request would not.
2. The dispatching session carries installed plugins, including `plugin-dev` with Claude Code plugin skills.
3. One run per scenario cannot show variance, and the one repeated scenario diverged: s3 run 1 wrote one Claude-format catalog that Codex reads as "legacy-compatible", while its rerun wrote both native catalogs.

## Failures and costs the skill can address

- **Unreported gaps (s5, criterion 6):** the arm listed what it checked but not what it did not run.
- **Unsettled design choice (s1, s3, s3-rep2):** arms split between one Claude-format catalog read by both tools and two native catalogs, each citing different reasoning ("two copies can drift" versus "the Claude path is legacy for Codex"); the spec's §2 default is two catalogs, parity-checked, and SKILL.md should state it with its reason.
- **Cost of rediscovering facts:** every Codex- and Copilot-specific fact the arms relied on was rediscovered by trial, at up to 59 tool calls and 13 minutes (s4); the skill supplies these facts, so plan 2b should record tool calls and wall time as a second outcome.
- **Unsafe probing:** in pursuit of live evidence, s1 and s3-rep2 wrote outside their working directories, and s4 sent prompts to three tools: `copilot -p`, which spent the owner's credits because `COPILOT_HOME` does not isolate Copilot's sign-in; `codex exec` with a nonexistent model nine times, which reached the API and was refused; and `claude -p` with a nonexistent model under a throwaway `CLAUDE_CONFIG_DIR`, where whether the owner's sign-in was used is unknown.
  The skill's rule against touching real configuration (R15) needs the safe probing method spelled out, including these caveats, and plan 2b must establish whether `CLAUDE_CONFIG_DIR` isolates sign-in before any arm may run `claude -p`.
- **Good judgement the criteria penalised (s5, criteria 1–2; s1):** both arms that saw the v1.4.0 telemetry declined to ship it and asked for a decision; that is the behaviour R5 wants, so scenario 5 must score an explicit, reasoned hold as a pass.

## Facts observed by the arms (candidates for the references)

Each needs its own provenance entry before it enters a reference; the run record named here is the pointer to the evidence.

- Codex copies an entire `./`-sourced plugin root, including `.git`, into its cache, and a Codex home inside that root makes the copy recurse until it fails with "File name too long" (s3, s3-rep2).
- `codex plugin marketplace add` rejects a `file://` URL; a git marketplace can be configured in `config.toml` with `source_type = "git"` (s3-rep2).
- Codex does not expand `${CLAUDE_PLUGIN_ROOT}` in an MCP server `command`, and resolves a relative `cwd` against the installed plugin (s4).
- Codex passes only an allow-listed set of environment variables to plugin MCP servers (s4).
- Copilot CLI always reads a plugin's top-level `.mcp.json`, loads plugin agents (as `review-kit:reviewer`), and passes `${user_config.*}` through unexpanded (s4).
- Codex plugin hooks run only after the user approves them in `/hooks` (s4, documentation only).
- Claude Code reports "Hook load failed: hooks: the file-path and array forms are not yet supported in a marketplace entry" for entry-level `hooks` given as a path, which `claude plugin validate` does not flag (s6).
- Codex refuses an install whose manifest name differs from the catalog entry ("plugin.json name `linter` does not match marketplace plugin name `lint`"), while Claude Code installs it under the entry name (s6).

## Changes plan 2b must make before treatment runs

1. Fixtures: make the weather-mcp mirror a real plugin (the s1 arm installed the pinned tag in both tools and found no components, so a catalog-only solution was possible but the task was confusing) and pin s1 to a release without the telemetry; set the executable bit on s4's scripts; give s6's plugins realistic descriptions so criterion 8 measures defect false positives only.
2. Criteria: scenario 5 passes a reasoned hold on a suspicious release; tighten s2, s3, and s7, which baselines pass outright.
3. Preamble: drop the tool names, keep the isolation requirement generic, and forbid sending prompts to any model.
4. Outcomes: record tool calls and wall time per run, and run at least three repetitions per scenario and arm.
5. Rerun every baseline under the revised fixtures and preamble, so baseline and treatment arms stay comparable.
6. Tooling: commit the run scripts (artefact collection, scorer prompts, record assembly) under `tests/eval/`, and fix the isolation checker's blind spots found in review: relative paths such as `..`, commands after a heredoc, sourced environment files, and a blanket `/tmp` allowance.
7. Isolation evidence: hash the real `~/.codex` and `~/.copilot` before and after each batch of arms, so any change is attributable, and archive tool outputs as well as inputs for runs whose observations feed a reference.

## Correction (plan 2b)

Plan 2b's isolation checker (`tests/eval/isolation.py`), calibrated on these runs' recorded tool calls in `tests/test_eval_isolation.py`, found two violations that the plan-2a checker missed in the scored s3 run: call #0 listed the shared runs directory (`ls ../`), and call #7 copied the working directory to `../s3-copy-for-test` and then deleted it.
The s3 row above therefore rests on a run that was not isolated; it stays as recorded, and plan 2b's reruns replace every row.
The same checker flags `ls -la ..` in s6 (call #1), a read of the shared parent directory that revealed the other scenarios' directory names.
