# plugin-marketplaces skill — design

Date: 2026-09-27
Status: approved by owner 2026-09-27
Repository: `briandconnelly/plugin-marketplaces` (local only until the owner approves creating the GitHub repo)

## 1. Purpose

A skill that helps any maintainer create, audit, maintain, and release high-quality user-hosted plugin marketplaces, and package the plugins those marketplaces list.
A user-hosted plugin marketplace is a catalog file that its maintainer writes and hosts, typically in a git repository, and that users register with their tool; it is distinct from a vendor-hosted registry such as Kimi Code's, Cline's, or Gemini CLI's, where the vendor owns the catalog.
It teaches format-neutral best practices, and it carries a checked understanding of each covered tool's catalog and plugin formats.
It ships a validator, and it ships maintainer tooling that keeps its own facts current as the covered tools change several times a week.

Success means:

- An agent using the skill produces catalogs and manifests that load in every declared target tool, with pinned, reviewable remote sources and consistent versions.
- The agent reports each check level (schema, local, remote, install probe) separately and never reports a skipped or inconclusive check as passed.
- A change upstream that invalidates a fact in the skill surfaces as a GitHub issue within a week, naming the affected reference sections.

## 2. Decisions already made

| Decision | Choice | Source |
| --- | --- | --- |
| Audience | Any marketplace maintainer; the owner's `briandconnelly-plugins` and `data-reasoning` repos are calibration fixtures, not the target design | owner, Q1 |
| Plugin depth | Manifests, packaging, and a feature matrix of which component types each format supports and how each is declared; writing the components themselves is deferred to other skills | owner, Q2 |
| Validation | Wrap official validators where they exist, add checks for what they miss | owner, Q3 |
| New multi-tool plugin packaging default | Agent Plugins 1.0 root `plugin.json` + `mcp.json`, with a Claude Code adapter (`.claude-plugin/plugin.json` + `.mcp.json`) | owner, Q4 |
| Multi-tool catalog default | Separate native catalogs, parity-checked, with recorded reasons for intentional differences | owner, Q5 |
| Scripts in v1 | Validator only; no bump, sync, or scaffold helpers | owner, Q6 |
| Freshness automation | Provenance on every fact, conformance probes, upstream drift detector, weekly GitHub Action that opens or updates an issue | owner, Q7 |
| Repository | Its own repo, shipped as a plugin and acting as its own marketplace | owner, Q8 |
| Terminology | "User-hosted plugin marketplace" as the defining term, distinguishing author-controlled catalogs from vendor-hosted registries | owner, 2026-09-27 |
| Coverage rule | A tool is covered only if a runnable probe can check its behaviour; uncheckable tools are excluded, not listed as unverified | owner, 2026-09-27 |

## 3. Scope

### 3.1 Covered tools

| Tool | Role | Probe instrument |
| --- | --- | --- |
| Claude Code | catalog + plugin format | `claude plugin validate --strict --json`; `claude plugin marketplace add` into an isolated config dir |
| Codex | catalog + both plugin formats (portable and `.codex-plugin/` compat) | `codex plugin marketplace add` + `codex plugin list --available --json` under a throwaway `CODEX_HOME` |
| GitHub Copilot CLI | catalog reader + plugin format | `copilot plugin marketplace add` under an isolated config dir (phase-0 gate) |
| VS Code agent plugins | catalog reader + plugin format | app launched with a throwaway `--user-data-dir` and `chat.plugins.marketplaces` (phase-0 gate) |
| Agent Plugins 1.0 | portable plugin package format (no catalog) | vendored official JSON Schemas, plus load probes in the tools above that read portable manifests |

A tool whose phase-0 gate fails is removed from scope before any reference text about it is written.

### 3.2 Excluded, and why

- Cursor, OpenHands, OpenClaw, Factory Droid: they read Claude-dialect catalogs, but no probe can check them here (coverage rule).
- Kimi Code, Cline, Gemini CLI: vendor-hosted registries, not user-hosted marketplaces.
- Kiro, Hermes, OpenCode, Amp, Goose, Windsurf: no author-written catalog file.
- Writing plugin components (skills, hooks, agents, commands, MCP or LSP servers): defer to `plugin-dev`, `skill-creator`, and `agent-friendly-mcp`.
- Managed or enterprise policy (`strictKnownMarketplaces`, cloud-managed Codex config), and vendor directory submission portals: noted as future work.
- Installing plugins into a user's real configuration, or executing plugin code, under any circumstances.

## 4. Facts the design depends on

Each fact below was read in source or docs, or observed by a live probe, on 2026-09-27; the references will carry the full provenance.

- Claude's `.claude-plugin/marketplace.json` schema is a shared catalog dialect: Codex, Copilot CLI, and VS Code all read that path.
- Native catalog locations: Codex reads `.agents/plugins/marketplace.json`, `.agents/plugins/api_marketplace.json`, `.claude-plugin/marketplace.json`, `.cursor-plugin/marketplace.json`, first match wins; Copilot CLI and VS Code read `marketplace.json`, `.plugin/marketplace.json`, `.github/plugin/marketplace.json`, then `.claude-plugin/marketplace.json`, first match wins.
- Readers accept different `source` types: Codex accepts `./` paths, `url`, `git-subdir`, `npm` and silently skips `github`; Copilot CLI accepts paths, `github`, `url`; VS Code accepts paths, `github`, `url`, `git-subdir`, `npm`, `pip`; Claude Code accepts paths, `github`, `url`, `git-subdir`, `npm`, `archive`, `command`.
- Codex skips an unreadable catalog entry with only a log warning; Claude Code ignores unknown keys at load and only `validate` warns.
- Agent Plugins 1.0 defines a closed root `plugin.json` plus fixed `skills/` and `mcp.json`, client data under reverse-domain `extensions`, and no catalog format.
- Codex, Copilot CLI, and VS Code read the portable root `plugin.json`; Claude Code does not.
- `claude plugin validate` does not catch: entry `hooks` given as a path, a relative source pointing at a missing directory, or a wrong remote repo.
- Codex has no validate command; the practical local check is load-and-list under a throwaway `CODEX_HOME`.
- In Claude Code, an explicit `version` pins users to the cached copy until the string changes; in Codex, the manifest `version` names the cache directory.

## 5. Skill layout

```text
plugin-marketplaces/                     (repo root; also its own marketplace)
  .claude-plugin/marketplace.json         dogfood catalog (Claude dialect)
  .agents/plugins/marketplace.json        dogfood catalog (Codex native)
  plugin.json, .claude-plugin/plugin.json dogfood packaging, per the §2 default
  marketplace-policy.json                 dogfood policy file (declared readers, parity exceptions)
  skills/plugin-marketplaces/
    SKILL.md
    references/
      claude-code.md
      codex.md
      copilot-cli.md
      vscode.md
      agent-plugins.md
      feature-matrix.md
      multi-tool.md
      releases.md
      validation.md
      freshness.md
    scripts/
      check_marketplace.py
      schemas/agent-plugins/1.0.0/plugin.schema.json
      schemas/agent-plugins/1.0.0/mcp.schema.json
      schemas/SHA256SUMS
  tests/
    test_check_marketplace.py
    fixtures/
    conformance.py
    conformance/
    check_upstream.py
    upstream-pins.json
    test_check_upstream.py
    scenarios.md
    trigger_cases.md
  .github/workflows/
    ci.yml                                prek + pytest + validator on the repo's own catalogs
    upstream-drift.yml                    weekly drift check → issue
  prek.toml, pyproject.toml, README.md, AGENTS.md, CLAUDE.md, LICENSE (MIT)
```

The skill ships inside `skills/` so the repo is simultaneously a skill source (`gh skill`, `npx skills`) and a plugin.
Maintainer tooling (`tests/`) is not shipped in the plugin.

## 6. SKILL.md

Frontmatter conforms to the agentskills.io spec; the description leads with the term "user-hosted plugin marketplace" and names the triggers (creating, auditing, or releasing a marketplace or catalog; adding, pinning, or renaming a plugin entry; packaging a plugin for more than one tool; `marketplace.json`, `plugin.json`, `.claude-plugin`, `.agents/plugins`, `.codex-plugin`, `.github/plugin`, `agent-plugins.org`) and the non-triggers (writing hooks, agents, or MCP servers; installing a plugin for personal use).

Body sections:

1. Core model: a user-hosted marketplace is a catalog the maintainer controls; a catalog lists entries; an entry points at a package through a source; a version is the cache key that decides whether users receive a change.
2. Workflows, each a short numbered list with links: create a marketplace, add a plugin, release a plugin version, audit a marketplace, port or migrate a plugin between formats.
3. Rules, the single normative home for every binding rule in the skill, each worded so a reviewer can check it:
   - R1 Declare the target readers in `marketplace-policy.json` before choosing sources or layouts.
   - R2 Use only source types that every declared reader of that catalog accepts.
   - R3 Local sources start with `./`, contain no `..`, and resolve (after symlinks) inside the marketplace root.
   - R4 Every remote source is pinned to immutable content using its source type's mechanism: a full commit `sha` for git sources (`github`, `url`, `git-subdir`), `sha256` for `archive`, an exact version (not a range or dist-tag) for `npm`; `command` sources are not used in a published catalog because they cannot be pinned; the one exception is a git ref declared as a channel, with a reason, in `marketplace-policy.json` (owner, 2026-09-27).
   - R5 A pin moves only after the change between the old and new pinned content has been reviewed.
   - R6 For each reader, the plugin's version is set in that reader's authoritative field (the per-reader table in `releases.md`), and every version value recorded anywhere for that plugin is equal.
   - R7 A release changes the version value in every place R6 records it.
   - R8 A catalog entry's `name` equals the plugin manifest's `name`, and satisfies every declared reader's name rules.
   - R9 Treat a published plugin name as permanent; rename or remove through the reader's documented mechanism (`renames`, `forceRemoveDeletedPlugins`) where one exists.
   - R10 Every difference in membership or version between catalogs in one repo has a recorded reason in `marketplace-policy.json`.
   - R11 An entry's description discloses executable components (hooks, MCP servers, LSP servers, `bin/`) and external services.
   - R12 Report schema, local, remote, catalog-discovery, and package-load results separately; report skipped or inconclusive checks as such.
   - R13 When a covered tool's installed version is newer than the version a reference was verified against, re-check any fact the current decision depends on against the live source before relying on it.
   - R14 When a reference and an official validator disagree, follow the validator and report the disagreement.
   - R15 Never install into the user's real tool configuration or execute plugin code while validating.
4. Reference map: one line per reference file saying when to read it.

Rule text lives only in SKILL.md; references cite rules by id and never restate them.

## 7. References

Every reference opens with a provenance block: doc URLs, upstream repo and commit for any source-read fact, tool versions verified against, date verified, and the probe ids in `tests/conformance/` that cover it.

- `claude-code.md`: catalog fields, entry fields, source variants, `strict` semantics, plugin.json fields and component path rules, name rules and reserved names, version resolution and caching, auto-update, private-repo auth, `validate` behaviour and its known gaps.
- `codex.md`: catalog locations and precedence, entry fields and `policy`, source variants, both plugin formats and detection order, the `extensions.com.openai` overlay, `interface` fields, cache directory naming, discovery and `config.toml` marketplaces, Claude interop and what it drops.
- `copilot-cli.md`, `vscode.md`: catalog locations and precedence, accepted source types, manifest locations, portable-format support, marketplace registration (command or setting), defaults.
- `agent-plugins.md`: manifest and `mcp.json` shapes, failure semantics, path containment, `PLUGIN_ROOT`/`PLUGIN_DATA`, extensions, known schema defects (#76, #77), governance and maturity signals, and the explicit absence of a catalog format.
- `feature-matrix.md`: three tables, every cell linked to its provenance:
  - components × formats (supported, how declared, default path, merge-or-replace semantics);
  - source types × readers;
  - name, version, and cache rules × tools.
- `multi-tool.md`: the §2 packaging and catalog defaults, why, what each tool reads from a dual-packaged plugin, and when to deviate.
- `releases.md`: bump discipline per tool, pinning, reviewing a pin move, pin drift, renames and removals, how a change reaches users in each tool.
- `validation.md`: the four check levels, what each instrument can and cannot prove, how to read the validator's output, and how to run the probes.
- `freshness.md`: the provenance block format, the R13 procedure, and how a maintainer refreshes a fact and its pin.

## 8. Validator: `scripts/check_marketplace.py`

Runtime: a `uv run` script with PEP 723 inline metadata, Python ≥ 3.12, `jsonschema` as the only third-party dependency.
It never installs into real tool configuration and never executes plugin code (R15).

Inputs: a repository path; optional `--policy` (defaults to `marketplace-policy.json` at the root); `--remote`; `--probe <tool>...`; `--format json|text`.

`marketplace-policy.json` declares the target `readers`, `exceptions` (plugin, kind, reason) for R10, and `channels` (plugin, ref, reason) for R4; which catalog each reader reads follows from its documented precedence.
When the file is absent, the validator infers a reader only from that reader's own first-choice catalog, names any other tool that would also read a catalog there, and reports the inference as a finding (owner, 2026-09-27).

Check levels:

1. Schema, offline.
   - Parse every catalog and manifest with duplicate-key detection.
   - Run `claude plugin validate --strict --json` on the repo and on each local plugin when `claude` is on `PATH`; report `skipped` otherwise.
   - Validate portable manifests at the spec's own failure granularity: root `plugin.json` (plugin rejected or loaded, with the report-and-ignore exceptions for unknown top-level keys and non-object `extensions`), `mcp.json` as a whole (MCP disabled, other components still load), and each MCP server entry (that server skipped); report status per plugin, component, and entry.
2. Local, offline — the checks no official validator covers:
   - R3 path rules, including symlink escape and nonexistent targets.
   - R2 source types against each declared reader's accepted set.
   - R6 authoritative version field present per reader, and every recorded version value equal across `.claude-plugin/plugin.json`, root `plugin.json`, `.codex-plugin/plugin.json`, and catalog entries.
   - R8 entry-name equals manifest-name, and name-rule intersection.
   - R10 catalog membership and version parity, against recorded exceptions.
   - R4 remote sources missing their source type's pin (`sha`, `sha256`, exact npm version), and `command` sources in a catalog.
   - Claude entry `hooks` given as a path or array.
   - The portable-format pitfalls: root `plugin.json` without the Agent Plugins `$schema`, symlinked root manifest, `.mcp.json` servers lacking a transport `type` when mirrored to `mcp.json`.
3. Remote, opt-in (`--remote`), with source-specific checks reported as separate results:
   - git, ref drift: `git ls-remote` reports whether `ref` exists and whether it still points at the pinned `sha`; a missing or moved ref is informational, because a pinned `sha` can still install.
   - git, pin reachability: a no-checkout fetch of the pinned `sha`; a host that refuses fetch-by-SHA, or any network or auth failure, is `inconclusive`, never `failed`.
   - npm: the registry lists the exact pinned version.
   - archive: the URL is reachable over HTTPS and its content matches `sha256`.
4. Probes, opt-in (`--probe <tool>`), each in a throwaway config directory, with two distinct levels:
   - Catalog discovery: the tool lists the catalog's entries; entries it silently skipped become findings; a fixture entry known to be rejected must be absent, or the probe reports itself broken.
   - Package load: the tool loads a plugin and exposes an observable component (for example a listed skill); a tool that offers no such observation reports this level as `unproven`, never `passed`.

Each check id maps to the rule id and the provenance anchor it implements.
Output: findings `{check, level, rule, severity, file, pointer, message, source}` plus a per-level status table (`passed`, `failed`, `skipped`, `inconclusive`).
Exit codes: 0 no error findings, 1 error findings, 2 validator failure.

Encoding discipline: the validator re-encodes only cross-file invariants and documented rules the official tools do not enforce; field catalogs stay with the official validators and schemas.
Reader source-type tables live in one data file, `scripts/readers.json`, which `feature-matrix.md` is checked against (§10).

## 9. Freshness tooling

- `tests/upstream-pins.json`: each pinned upstream (doc `.md` page with a content hash; `openai/codex`, `microsoft/vscode`, Copilot CLI docs, `agentplugins/agent-plugins-spec` files at a commit with a blob sha; each tool's `--help` output hash) maps to the reference sections and `readers.json` keys that depend on it.
- `tests/check_upstream.py`: fetches current state, reports every pin whose content changed and the sections it affects; needs network, no model, no tool CLIs.
- `.github/workflows/upstream-drift.yml`: weekly schedule plus manual dispatch; runs `check_upstream.py`; opens one issue, or updates the open one, listing changes and affected sections; does nothing when nothing changed.
- `tests/conformance.py`: runs behavioural probes against the locally installed tools, each probe encoding one fact (for example "Codex skips a `github` source", "Codex reads `.claude-plugin/marketplace.json`", "`claude plugin validate` does not flag entry `hooks` given as a path"); a flipped expectation names the stale fact and its reference section; a missing tool yields `skipped`.
- The refresh procedure in `freshness.md` re-verifies a fact before re-pinning it; re-pinning without re-verification is the failure this tooling exists to prevent.

## 10. Testing

- Validator: pytest with one mutation fixture per check proving the check can fire, one clean fixture per check proving it does not over-fire, plus network-failure and intentional-divergence cases.
- Drift detector: tests against a fake upstream showing both a changed and an unchanged pin, so a "no change" result is known to be able to fail.
- Consistency: a test that `feature-matrix.md`'s source-type table matches `readers.json`, and that every rule id cited in references resolves to SKILL.md.
- Calibration: run the validator on `briandconnelly-plugins` and `data-reasoning` and record the findings; the 11-vs-9 catalog membership difference is the expected known positive.
- Dogfood: CI runs the validator on this repo's own catalogs.
- prek hooks: ruff, ty, pytest for the offline suites, frontmatter check, one-sentence-per-line check for Markdown.
- Behaviour: `tests/scenarios.md`, baseline versus with-skill, using this owner's established conventions:
  1. Create a marketplace for Claude Code and Codex with one local and one remote plugin.
  2. Maintain a catalog pair whose memberships differ intentionally; the agent must not force parity.
  3. A single-plugin repo that is its own marketplace.
  4. Port a Claude plugin with commands, agents, and hooks to Codex and Copilot CLI.
  5. Release a new version of a remote-sourced plugin (pin move, version bump).
  6. Audit a marketplace with seeded defects (a `github` source in a catalog Codex reads, missing `./`, name mismatch, version disagreement).
  7. Pressure case: "just confirm it passes" when the remote check is inconclusive.
- `tests/trigger_cases.md`: should-trigger and should-not-trigger prompts.

## 11. Delivery phases

0. Feasibility spike (throwaway), exit criterion per tool: a headless, isolated probe that shows an accepted fixture entry and omits a known-rejected control entry; any tool without one leaves scope (§3.1) before its reference is written.
   - When a tool lists every catalog entry and rejects the control only at install time, discovery is recorded `unproven` and the install-time rejection serves as the package-load level's negative control (owner, 2026-09-27).
   - Copilot CLI: set `COPILOT_HOME` and `COPILOT_CACHE_HOME` to temporary directories, `copilot plugin marketplace add <fixture path>`, then `copilot plugin marketplace browse <name> --json`.
   - VS Code: `code` 1.139.1 has no plugin-marketplace command, so the spike must demonstrate a read-only observation of the workbench plugin marketplace service (for example an extension-host test run with a throwaway `--user-data-dir`) that asserts both controls; launching the app without a machine-readable result does not satisfy the criterion.
   - Package-load observability is recorded per tool; where none exists, that tool's package-load level stays `unproven` (§8).
1. Repository skeleton, vendored schemas, `readers.json`, validator with offline levels and its tests, calibration run.
2. References and SKILL.md, each fact backed by a provenance entry.
3. Conformance probes and upstream drift tooling with the weekly Action.
4. Remote and install-probe levels.
5. Behavioural scenarios and trigger cases, baseline and with-skill.
6. Review: Codex cross-check, then GitHub repo creation (owner approval), PR, and listing in `briandconnelly-plugins`.

## 12. Risks

- Upstream churn: mitigated by provenance, probes, and the weekly drift issue; residual risk is a behavioural change that does not touch any pinned file.
- The validator becoming a stale second spec: mitigated by the encoding discipline in §8 and by probes that exercise the real tools.
- Probe side effects: every probe uses a throwaway config directory; a probe that cannot be isolated is not written.
- VS Code probe fragility: headless loading of the workbench may be brittle; phase 0 decides whether VS Code stays in scope.
- Agent Plugins governance: 1.0 is published but young, with known schema defects; the reference tracks the open issues that affect validation.
- Scope size: phases let the skill ship after phase 3 with remote and probe levels following.

## 13. Open questions

- None; the skill and repo name `plugin-marketplaces` is settled, with "user-hosted plugin marketplace" as the defining term (owner, 2026-09-27).
