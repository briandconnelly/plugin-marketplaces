# Test Scenarios for plugin-marketplaces

Behavioural scenarios for this skill, run baseline (no skill) and treatment (skill available) with fresh subagents.
A baseline run that already satisfies every criterion means the scenario is too easy; tighten it.
A criterion the treatment run misses is a finding against the skill, not against the agent.
Criteria are written in terms of files and real-tool behaviour, never in the skill's vocabulary, so a baseline can pass them.

## How to run

1. Copy `tests/fixtures/scenarios/sN/repo/` to a fresh directory outside this repository, add `.tool-homes/` to its `.git/info/exclude`, and commit it there as the starting point, so the final diff is exact and never contains tool state.
2. For scenarios 1 and 5, build the upstream mirror next to it with `uv run python tests/fixtures/scenarios/make_upstream.py <dir>/upstream-weather-mcp`.
3. Record a run manifest: date, arm (baseline or with-skill), model, the exact dispatch prompt, the fixture's starting git tree id, tool versions (`claude --version`, `codex --version`, `copilot --version`), and the plugins and skills present in the dispatching session; a treatment arm is comparable only to a baseline with the same tree id and dispatch prompt apart from the skill line.
4. Dispatch a fresh subagent with the arm preamble below, then the scenario's prompt verbatim; the treatment arm's preamble adds one line naming the skill's `SKILL.md`.
5. When the arm finishes, record its final report, the diff of its directory against the starting commit, `uv run python tests/eval/objective_checks.py <its directory>`, and every tool call from its transcript (extracted with `jq`, never retyped).
6. Check isolation from the tool calls: every file-tool path must be absolute and inside the arm's directory or the upstream mirror, every shell command must run after `cd` into the arm's directory, and every `claude`/`codex`/`copilot` command must set the throwaway variables; a run that fails the check is discarded and repeated.
7. Scan the recorded artefacts for tokens and credentials before storing them.
8. Dispatch a fresh scorer with the scenario's prompt, its criteria copied verbatim from this file, the original fixture, the final diff, the objective-check output, the tool calls, and the arm's final report; the scorer marks each criterion pass or fail with one line of evidence.
9. Store the scored run at `tests/runs/YYYY-MM-DD-sN-baseline.md` or `tests/runs/YYYY-MM-DD-sN-with-skill.md`, assembled programmatically from the recorded artefacts and manifest.

### Arm preamble

> You are working in `WORKDIR`, a git repository.
> Start by running `cd WORKDIR`, and give every file path as an absolute path.
> Work only inside `WORKDIR`; do not read or change files anywhere else, except that you may read `UPSTREAM` when the task mentions it.
> If you run `claude`, `codex`, or `copilot`, first create throwaway configuration directories under `WORKDIR/.tool-homes/` (Codex refuses a `CODEX_HOME` that does not exist), then point the tools at them by setting `CLAUDE_CONFIG_DIR`, `CODEX_HOME`, and both `COPILOT_HOME` and `COPILOT_CACHE_HOME`; never use your real configuration.
> Do not push, publish, or contact any remote service other than read-only documentation.

## Scoring (every scenario)

- Each criterion is pass or fail with one line of evidence pointing at the diff, the objective-check output, or the final report.
- A criterion about the final report passes only if the report itself says it; the scorer does not infer intent.
- "Codex lists X" means `objective_checks.py` shows X under `codex.listed`; "Claude Code accepts the marketplace" means `claude.success` is true and `claude.errors` is empty.

## Scenario 1: New marketplace for two tools

**Prompt:**

> This repo holds our team's plugins.
> Set it up as a plugin marketplace that people can add in both Claude Code and Codex.
> It should offer the local `hello-tools` plugin and our `weather-mcp` plugin, which lives at https://github.com/acme/weather-mcp — the release to ship is tag `v1.4.0` (commit `a64ff2993afcb34532f9971922275f68fee1046d`).
> A read-only mirror of the weather-mcp repository is at `UPSTREAM`.
> Tell me what you did and how you checked it.

**Success criteria:**

1. Claude Code accepts the marketplace.
2. Codex lists both `hello-tools` and `weather-mcp`.
3. Every catalog entry for `weather-mcp` records commit `a64ff2993afcb34532f9971922275f68fee1046d`.
4. `hello-tools` has the same version wherever the repository records one.
5. The final report says which checks were run and which were not (for example that the catalog's GitHub URL itself was not fetched), and claims no check it did not run.

**Expected baseline failure:** a catalog that only Claude Code reads correctly, such as a `github`-typed source that Codex skips without an error, or a remote entry pinned only by tag; and a report that calls the marketplace working in Codex without having loaded it there.

## Scenario 2: Adding a plugin to catalogs that differ on purpose

**Prompt:**

> Add the new `lint-kit` plugin (in `plugins/lint-kit`) to our marketplace.

**Success criteria:**

1. Claude Code accepts the marketplace, and both `lint-kit` and the three previously listed Claude plugins are in its catalog.
2. Codex lists `lint-kit` alongside its three previously listed plugins.
3. `claude-hooks` is still absent from what Codex lists, and `codex-helper` is still absent from the Claude catalog.
4. `lint-kit` has the same version wherever the repository records one.
5. The final report says which checks were run and which were not.

**Expected baseline failure:** adding `lint-kit` to only one catalog, or "tidying" the intentional differences by adding `claude-hooks` to Codex or `codex-helper` to Claude.

## Scenario 3: A plugin repository that is its own marketplace

**Prompt:**

> People want to install this plugin straight from its GitHub repository (acme/focus-timer) in both Claude Code and Codex.
> Make the repository work as its own marketplace.

**Success criteria:**

1. Claude Code accepts the marketplace.
2. Codex lists `focus-timer`.
3. The catalog entry is named `focus-timer`, matching the plugin's own name.
4. The plugin's version is the same wherever the repository records one.
5. The final report says which checks were run and which were not.

**Expected baseline failure:** a Claude-only catalog with a `github` source pointing back at the repository, which Codex skips, or an entry name that differs from the plugin name.

## Scenario 4: Porting a Claude Code plugin to Codex and Copilot CLI

**Prompt:**

> Make review-kit available to Codex and GitHub Copilot CLI users too, without breaking it for Claude Code users.
> Tell me what will and won't work in each tool.

**Success criteria:**

1. Claude Code still accepts the marketplace, and `.claude-plugin/plugin.json` still declares the command, agent, hook, and MCP server paths or defaults it declared before.
2. Codex lists `review-kit`, and Copilot CLI lists `review-kit`.
3. The final report says Codex does not load the plugin's custom agent (`agents/reviewer.md`) and does not support its `userConfig` setting (both per OpenAI's plugin documentation, `docs/research/2026-09-27-codex.md` §4).
4. The final report says the `review` command reaches Codex users as a skill, either because Codex migrates it automatically (observed with codex-cli 0.157.1, `docs/research/2026-09-28-codex-command-migration-probe.md`) or because the agent converted it; a report that calls it unsupported in Codex fails this criterion.
5. The final report says which checks were run and which were not, and claims no tool behaviour it did not observe or cite.

**Expected baseline failure:** asserting that Codex runs the agent, honours `userConfig`, or expands `${CLAUDE_PLUGIN_ROOT}` in MCP configuration, without evidence; or deleting Claude-specific files to "make it portable".

## Scenario 5: Releasing a new version of a remote plugin

**Prompt:**

> weather-mcp v1.4.0 is tagged upstream (commit `a64ff2993afcb34532f9971922275f68fee1046d`).
> A read-only mirror of the weather-mcp repository is at `UPSTREAM`.
> Release it to our marketplace users.

**Success criteria:**

1. Every catalog entry for `weather-mcp` records commit `a64ff2993afcb34532f9971922275f68fee1046d` and no longer records `d4e6332dbbee7a28c282ac5210f02db086084d3c`.
2. Every version the repository records for `weather-mcp` is `1.4.0`, or no version is recorded for it anywhere.
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

**Expected baseline failure:** answering yes on the strength of the green pipeline, which runs only Claude Code's validator and lets the inconclusive remote check pass.
