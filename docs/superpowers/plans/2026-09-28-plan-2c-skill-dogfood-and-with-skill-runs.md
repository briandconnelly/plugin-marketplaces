# Plan 2c: The Skill, the Dogfood Marketplace, and the With-Skill Runs — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.
> Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Write SKILL.md and its nine references against the plan-2b baseline failures, with provenance on every fact; make this repository its own marketplace; then run every scenario and every trigger case with the skill and compare against the baselines.

**Architecture:** Four new probes (run while writing this plan, isolated and without any model session) settle the facts the baselines left open, and are archived as a dated research record.
The skill's rules live only in SKILL.md; each reference cites rules by id and facts by evidence rows, and `tests/test_skill_docs.py` enforces both.
The evaluation gains a with-skill arm (the committed skill copied into each run, its validator installed beside it, and two treatment lines added to the unchanged baseline prompt) and a trigger-case runner; runs then use only the scripts, as in plan 2b.

**Tech Stack:** Python ≥ 3.12, uv, pytest, ruff, ty, prek, git, the `claude`/`codex`/`copilot` CLIs (probes and objective checks only), Claude Code subagents (arms, scorers, trigger replies).

**Spec:** `docs/superpowers/specs/2026-09-27-plugin-marketplaces-design.md` (§5 layout, §6 SKILL.md, §7 references, §10 Consistency, Dogfood, and Behaviour, §11 phase 2c); the failure list this plan writes against is `tests/runs/2026-09-28-baseline-summary-2b.md`, "Failures and costs the skill can address" and "Inputs for plan 2c".

**How this plan was made:** every file below was written and tested in a scratch clone of `main` at `446ce07` (313 tests passing, `prek run --all-files` clean), and the plan's code blocks were generated from that clone; Task 11 replays them.
The probes in Task 2 were run on 2026-09-28 with claude 2.1.284, codex-cli 0.157.1, and copilot 1.0.89; their record is the file Task 2 commits.

## Owner decisions needed before Task 7

- **D1, validator temporary directory.** The installed validator runs `claude plugin validate` with a throwaway `CLAUDE_CONFIG_DIR` under `TMPDIR`, which is the system temporary directory unless the arm sets it; `validation.md` tells agents to set `TMPDIR`.
  Proposed ruling: that directory, created and removed by the validator, is not a write violation.
- **D2, reading and entering the skill copy.** Proposed ruling: a with-skill arm may read and `cd` into SKILLDIR and run VALIDATOR (Task 5 makes the checker allow both); writing there is still a violation.
- **D3, Copilot CLI 1.0.88 → 1.0.89.** Copilot updated itself after the baselines; probe P3 re-checked the catalog behaviour scenario 4's criterion 2 depends on and found it unchanged.
  Proposed: proceed, record the version in every manifest (already automatic), and treat s4 score comparisons as descriptive, as the baseline summary already requires.
- **D4, repetitions.** Proposed: three with-skill runs for s1, s2, s3, s5, s6, and s7, and five for s4, whose outcome is its isolation rate (baseline 1 of 10); trigger cases three repetitions each.

## Global Constraints

- Everything in plans 1, 2a, and 2b's Global Constraints still applies (uv only, ruff and ty, one sentence per Markdown line, conventional commits with the session's attribution lines, explicit `git add` paths, R15 isolation, the coverage rule, no `.github/workflows/` change).
- Work on branch `feat/plan-2c` from `main` at `446ce07`.
- Run every command from the repository root: each shell call starts in `~/projects/skills`, so begin with `cd ~/projects/plugin-marketplaces`.
- Run `uv run ruff format . && uv run ruff check --fix .` and `uv run pytest -q` before every commit; stage files before `prek run --all-files` (prek sees only tracked files); gate each ledger line on the commit's own exit status.
- Global git sets `diff.external = difft`: any hand-run diff uses `git -c diff.external= diff --no-ext-diff`.
- Write files with quoted heredoc delimiters (`<<'PLAN2C_EOF'`) only; an unquoted delimiter executes backtick text.
- Nobody sends a prompt to a model CLI or opens a Copilot session in any form: not an arm, not a scorer, not the executor.
- No amicus or Codex call while a batch of arms runs.
- Arms must not see this repository, its research, its plans, or the criteria; a with-skill arm sees only its run directory, which holds the committed skill copy and the installed validator.
- Scenario criteria and prompts do not change in this plan: `test_baseline_prompts_are_what_the_baselines_received` pins every baseline prompt to its recorded text.
- Rules live only in SKILL.md's Rules section; references cite rule ids and never restate a rule (AGENTS.md).
- The ledger for this plan is `handoff/plan-2c-ledger.md` (untracked).
- zsh does not word-split `set -- $var`, and coreutils `timeout` is absent (use `perl -e 'alarm N; exec @ARGV'`).

## Review Focus

1. A with-skill arm that runs `uv run SKILLDIR/scripts/check_marketplace.py` instead of the installed validator writes the real uv cache and may fetch from PyPI: the checker flags every `uv`/`uvx` call whose `UV_CACHE_DIR` is outside WORKDIR (Task 5's `test_uv_writes_its_cache_outside_workdir_unless_told_otherwise`), and the treatment line names the installed validator.
2. A run prepared from an edited but uncommitted skill would be compared as if it were the committed one: `prepare.py` refuses (`test_a_with_skill_run_refuses_an_uncommitted_skill`), copies the committed tree only, and records `skill_tree` in the manifest (`test_a_with_skill_run_gets_the_committed_skill_and_an_installed_validator`).
3. A running validator that byte-compiles its modules writes outside WORKDIR: the validator is installed with `--compile-bytecode`, and the test compares the validator directory before and after a run (a run without byte-compiling changed 66 paths when checked).
4. An edit to `tests/scenarios.md` that changes what a baseline arm received would make every comparison invalid: `test_baseline_prompts_are_what_the_baselines_received` compares each scenario's prompt with its recorded plan-2b dispatch prompt.
5. A reference fact with no evidence, a citation to a missing row, or a restated rule would pass unnoticed: `tests/test_skill_docs.py` checks every citation, row, evidence path, rule id, link, and the source-type table against `readers.json`, and Task 3 shows it failing on a removed citation.

---

### Task 1: Branch, ledger, and preflight

**Files:**
- Create: `handoff/plan-2c-ledger.md` (untracked)

- [ ] **Step 1: Create the branch and the ledger**

~~~~bash
cd ~/projects/plugin-marketplaces
git switch main && git pull --ff-only
test "$(git rev-parse --short HEAD)" = 446ce07 && git switch -c feat/plan-2c
cat > handoff/plan-2c-ledger.md <<'PLAN2C_EOF'
# Plan 2c ledger

Rulings, deviations, batch notes, and their cost if wrong, in execution order.
PLAN2C_EOF
~~~~

Expected: the switch succeeds; if `main` is not at `446ce07`, stop and record why in the ledger before going on.

- [ ] **Step 2: Record tool versions**

~~~~bash
T=$(mktemp -d) && mkdir -p "$T"/{claude,codex,copilot,cc}
CLAUDE_CONFIG_DIR=$T/claude CODEX_HOME=$T/codex COPILOT_HOME=$T/copilot COPILOT_CACHE_HOME=$T/cc \
  sh -c 'claude --version; codex --version; copilot --version' < /dev/null | tee -a handoff/plan-2c-ledger.md
rm -rf "$T"
~~~~

Expected: `2.1.284 (Claude Code)`, `codex-cli 0.157.1`, `GitHub Copilot CLI 1.0.89.`.
A different claude or codex version means the baselines' tools changed: record it and ask the owner before Task 8; a newer Copilot is covered by D3 only for 1.0.89.

- [ ] **Step 3: Confirm the probe material is present**

~~~~bash
ls handoff/plan-2c-probes/
~~~~

Expected: `p1.out p1.sh p2.out p2.sh p3.out p3.sh p4.out p4.sh` (the captures from 2026-09-28; untracked, never committed, because they hold local paths and this machine's instructions).

### Task 2: Archive the plan-2c probes

The references cite four probes run on 2026-09-28: P1 (seeing what loaded without a model session), P2 (update delivery with and without a version bump), P3 (Copilot CLI source handling on 1.0.89), and P4 (which manifest each tool reads from a dual-packaged plugin).
This task re-runs them to confirm the record, then commits the record and the scripts.

**Files:**
- Create: `docs/research/2026-09-28-load-and-update-probes.md`
- Create: `docs/research/2026-09-28-load-and-update-probes/p1.sh`, `p2.sh`, `p3.sh`, `p4.sh`
- Modify: `docs/research/SHA256SUMS`, `docs/research/README.md`

- [ ] **Step 1: Write the probe scripts**

~~~~bash
mkdir -p 'docs/research/2026-09-28-load-and-update-probes'
cat > 'docs/research/2026-09-28-load-and-update-probes/p1.sh' <<'PLAN2C_EOF'
#!/bin/bash
# P1: which commands show a plugin's skills, commands, agents, hooks, and MCP servers
# without a model session, and which of them start the plugin's MCP servers.
# Every tool runs with throwaway homes under $P and with outbound IP traffic denied.
set -u
P="$1"
rm -rf "$P" && mkdir -p "$P"
MARK="$P/starts.log"
HOOKMARK="$P/hooks.log"
: > "$MARK"; : > "$HOOKMARK"
MKT="$P/mkt"
PK="$MKT/plugins/probe-kit"
mkdir -p "$MKT/.claude-plugin" "$MKT/.agents/plugins" "$PK/.claude-plugin" "$PK/config" \
  "$PK/skills/hello" "$PK/commands" "$PK/agents" "$PK/hooks"
cat > "$MKT/.claude-plugin/marketplace.json" <<EOF
{"name": "probe-mkt", "owner": {"name": "Probe"}, "plugins": [
  {"name": "probe-kit", "source": "./plugins/probe-kit", "description": "load-observability probe"}]}
EOF
cat > "$MKT/.agents/plugins/marketplace.json" <<EOF
{"name": "probe-mkt", "plugins": [
  {"name": "probe-kit", "source": {"source": "local", "path": "./plugins/probe-kit"},
   "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"}, "category": "Developer Tools"}]}
EOF
cat > "$PK/.claude-plugin/plugin.json" <<EOF
{"name": "probe-kit", "version": "0.1.0", "description": "load-observability probe",
 "author": {"name": "Probe"}, "mcpServers": "./config/mcp.json",
 "userConfig": {"api_key": {"type": "string", "title": "API key", "description": "probe value",
   "required": false, "default": "default-key"}}}
EOF
server() {  # a stand-in stdio server that records its argv, then exits
  printf '{"mcpServers": {"%s": {"command": "sh", "args": ["-c", "echo \\"$0 $*\\" >> %s", "%s", "${CLAUDE_PLUGIN_ROOT}", "${user_config.api_key}"]}}}\n' "$1" "$MARK" "$1"
}
server root-srv > "$PK/.mcp.json"
server named-srv > "$PK/config/mcp.json"
printf -- '---\nname: hello\ndescription: Say hello when asked to greet.\n---\n\nSay hello.\n' > "$PK/skills/hello/SKILL.md"
printf -- '---\ndescription: Review the current diff\n---\n\nReview the diff.\n' > "$PK/commands/review.md"
printf -- '---\nname: reviewer\ndescription: Reviews diffs.\n---\n\nYou review diffs.\n' > "$PK/agents/reviewer.md"
cat > "$PK/hooks/hooks.json" <<EOF
{"hooks": {"SessionStart": [{"hooks": [{"type": "command", "command": "echo hook >> $HOOKMARK"}]}]}}
EOF
git -C "$MKT" init -q && git -C "$MKT" add -A && \
  git -C "$MKT" -c user.name=p -c user.email=p@example.invalid commit -q -m fixture

mkdir -p "$P/home" "$P/xdg" "$P/claude" "$P/codex" "$P/copilot" "$P/copilot-cache" "$P/tmp"
: > "$P/gitconfig"
export HOME="$P/home" XDG_CONFIG_HOME="$P/xdg" TMPDIR="$P/tmp" GIT_CONFIG_GLOBAL="$P/gitconfig" \
  GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR="$P/claude" CODEX_HOME="$P/codex" \
  COPILOT_HOME="$P/copilot" COPILOT_CACHE_HOME="$P/copilot-cache"
SB='(version 1)(allow default)(deny network-outbound (remote ip))'
run() {
  echo "### \$ $*"
  sandbox-exec -p "$SB" perl -e 'alarm 90; exec @ARGV' "$@" < /dev/null 2>&1 | sed "s#$P#\$PROBE#g"
  echo "[exit ${PIPESTATUS[0]}; server starts so far: $(wc -l < "$MARK" | tr -d ' '); hook runs: $(wc -l < "$HOOKMARK" | tr -d ' ')]"
}
echo "## versions"; run claude --version; run codex --version; run copilot --version
echo "## claude"
run claude plugin marketplace add "$MKT"
run claude plugin install probe-kit@probe-mkt
run claude plugin list --json
run claude plugin details probe-kit@probe-mkt
run claude mcp list
echo "## codex"
run codex plugin marketplace add "$MKT"
run codex plugin add probe-kit@probe-mkt --json
run codex plugin list --json
run codex mcp list --json
run codex debug prompt-input
echo "## copilot"
run copilot plugin marketplace add "$MKT"
run copilot plugin install probe-kit@probe-mkt
run copilot plugin list
run copilot skill list
run copilot mcp list
run copilot mcp get root-srv
run copilot mcp get named-srv
echo "## recorded server starts"; sed "s#$P#\$PROBE#g" "$MARK"
echo "## recorded hook runs"; cat "$HOOKMARK"
PLAN2C_EOF
~~~~

~~~~bash
mkdir -p 'docs/research/2026-09-28-load-and-update-probes'
cat > 'docs/research/2026-09-28-load-and-update-probes/p2.sh' <<'PLAN2C_EOF'
#!/bin/bash
# P2: does a pushed change reach Claude Code and Codex users with and without a version bump?
# The "remote" is a local bare repository reached through throwaway insteadOf rules, so the
# tools believe they fetch github.com/acme/focus-timer; outbound IP traffic is denied.
set -u
P="$1"
rm -rf "$P" && mkdir -p "$P"
SRC="$P/src"
mkdir -p "$SRC/.claude-plugin" "$SRC/.agents/plugins" "$SRC/skills/focus"
cat > "$SRC/.claude-plugin/marketplace.json" <<EOF
{"name": "focus-timer", "owner": {"name": "Acme"}, "plugins": [
  {"name": "focus-timer", "source": "./", "description": "focus timer"}]}
EOF
cat > "$SRC/.agents/plugins/marketplace.json" <<EOF
{"name": "focus-timer", "plugins": [
  {"name": "focus-timer", "source": {"source": "local", "path": "./"},
   "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"}, "category": "Productivity"}]}
EOF
manifest() { printf '{"name": "focus-timer", "version": "%s", "description": "focus timer", "author": {"name": "Acme"}}\n' "$1" > "$SRC/.claude-plugin/plugin.json"; }
marker() { printf -- '---\nname: focus\ndescription: Start a focus timer.\n---\n\nrevision %s\n' "$1" > "$SRC/skills/focus/SKILL.md"; }
G=(git -C "$SRC" -c user.name=p -c user.email=p@example.invalid -c commit.gpgsign=false)
manifest 1.0.0; marker A
"${G[@]}" init -q -b main && "${G[@]}" add -A && "${G[@]}" commit -q -m A
git clone -q --bare "$SRC" "$P/remote/focus-timer.git"
"${G[@]}" remote add origin "$P/remote/focus-timer.git"

mkdir -p "$P/home" "$P/xdg" "$P/claude" "$P/codex" "$P/tmp"
cat > "$P/gitconfig" <<EOF
[url "file://$P/remote/"]
	insteadOf = https://github.com/acme/
	insteadOf = git@github.com:acme/
	insteadOf = ssh://git@github.com/acme/
EOF
export HOME="$P/home" XDG_CONFIG_HOME="$P/xdg" TMPDIR="$P/tmp" GIT_CONFIG_GLOBAL="$P/gitconfig" \
  GIT_CONFIG_NOSYSTEM=1 CLAUDE_CONFIG_DIR="$P/claude" CODEX_HOME="$P/codex" \
  CLAUDE_CODE_PLUGIN_PREFER_HTTPS=1
SB='(version 1)(allow default)(deny network-outbound (remote ip))'
run() {
  echo "### \$ $*"
  sandbox-exec -p "$SB" perl -e 'alarm 120; exec @ARGV' "$@" < /dev/null 2>&1 | sed "s#$P#\$PROBE#g"
  echo "[exit ${PIPESTATUS[0]}]"
}
installed() {  # the revision each tool would load now, from its installed copy
  echo "### installed copies"
  for f in $(find "$P/claude/plugins/cache" "$P/codex/plugins/cache" -path '*skills/focus/SKILL.md' 2>/dev/null | sort); do
    echo "${f#$P/}: $(tail -1 "$f")"
  done
  run claude plugin list --json
  run codex plugin list --json
}
publish() { manifest "$1"; marker "$2"; "${G[@]}" commit -qam "$2" && "${G[@]}" push -q origin main; }

echo "## versions"; run claude --version; run codex --version
echo "## step 1: add and install at revision A (version 1.0.0)"
run claude plugin marketplace add acme/focus-timer
run claude plugin install focus-timer@focus-timer
run codex plugin marketplace add acme/focus-timer
run codex plugin add focus-timer@focus-timer --json
installed
echo "## step 2: push revision B without a version bump"
publish 1.0.0 B
run claude plugin marketplace update focus-timer
run claude plugin update focus-timer@focus-timer
run codex plugin marketplace upgrade focus-timer --json
installed
echo "## step 2b: reinstall in Codex"
run codex plugin add focus-timer@focus-timer --json
installed
echo "## step 3: push revision C with version 1.0.1"
publish 1.0.1 C
run claude plugin marketplace update focus-timer
run claude plugin update focus-timer@focus-timer
run codex plugin marketplace upgrade focus-timer --json
installed
echo "## step 3b: reinstall in Codex"
run codex plugin add focus-timer@focus-timer --json
installed
PLAN2C_EOF
~~~~

~~~~bash
mkdir -p 'docs/research/2026-09-28-load-and-update-probes'
cat > 'docs/research/2026-09-28-load-and-update-probes/p3.sh' <<'PLAN2C_EOF'
#!/bin/bash
# P3: Copilot CLI catalog handling on the installed version (phase-0 controls, plus github and url sources).
set -u
P="$1"; rm -rf "$P"; mkdir -p "$P"
mk() {  # mk NAME ENTRIES-JSON
  mkdir -p "$P/$1/.claude-plugin" "$P/$1/plugins/alpha/.claude-plugin" "$P/$1/plugins/alpha/skills/hello"
  printf '{"name": "%s", "owner": {"name": "P"}, "plugins": %s}\n' "$1" "$2" > "$P/$1/.claude-plugin/marketplace.json"
  printf '{"name": "alpha", "version": "0.1.0"}\n' > "$P/$1/plugins/alpha/.claude-plugin/plugin.json"
  printf -- '---\nname: hello\ndescription: Say hello.\n---\n\nHello.\n' > "$P/$1/plugins/alpha/skills/hello/SKILL.md"
}
mk ctl-all '[{"name":"alpha","source":"./plugins/alpha"},{"name":"control-npm","source":{"source":"npm","package":"left-pad","version":"1.3.0"}},{"name":"control-bare","source":"plugins/alpha"},{"name":"control-unknown","source":{"source":"not-a-source-type","url":"https://example.com/x.git"}}]'
mk ctl-remote '[{"name":"alpha","source":"./plugins/alpha"},{"name":"gh","source":{"source":"github","repo":"acme/notes","sha":"0123456789abcdef0123456789abcdef01234567"}},{"name":"viaurl","source":{"source":"url","url":"https://github.com/acme/notes.git","sha":"0123456789abcdef0123456789abcdef01234567"}},{"name":"subdir","source":{"source":"git-subdir","url":"https://github.com/acme/notes.git","path":"p"}}]'
mkdir -p "$P/copilot" "$P/copilot-cache" "$P/home" "$P/xdg" "$P/tmp"
export COPILOT_HOME="$P/copilot" COPILOT_CACHE_HOME="$P/copilot-cache" HOME="$P/home" XDG_CONFIG_HOME="$P/xdg" TMPDIR="$P/tmp"
SB='(version 1)(allow default)(deny network-outbound (remote ip))'
run() { echo "### \$ $*"; sandbox-exec -p "$SB" perl -e 'alarm 90; exec @ARGV' "$@" < /dev/null 2>&1 | sed "s#$P#\$PROBE#g"; echo "[exit ${PIPESTATUS[0]}]"; }
run copilot --version
run copilot plugin marketplace add "$P/ctl-all"
run copilot plugin marketplace add "$P/ctl-remote"
run copilot plugin marketplace browse ctl-remote --json
mk ctl-remote2 '[{"name":"alpha","source":"./plugins/alpha"},{"name":"gh","source":{"source":"github","repo":"acme/notes","sha":"0123456789abcdef0123456789abcdef01234567"}},{"name":"viaurl","source":{"source":"url","url":"https://github.com/acme/notes.git","sha":"0123456789abcdef0123456789abcdef01234567"}}]'
run copilot plugin marketplace add "$P/ctl-remote2"
run copilot plugin marketplace browse ctl-remote2 --json
PLAN2C_EOF
~~~~

~~~~bash
mkdir -p 'docs/research/2026-09-28-load-and-update-probes'
cat > 'docs/research/2026-09-28-load-and-update-probes/p4.sh' <<'PLAN2C_EOF'
#!/bin/bash
# P4: a dual-packaged plugin (portable root plugin.json 1.1.0 + mcp.json, and a Claude adapter
# .claude-plugin/plugin.json 1.0.0 + .mcp.json): which manifest and MCP file does each tool read?
set -u
P="$1"; rm -rf "$P"; mkdir -p "$P"
MKT="$P/mkt"; PK="$MKT/plugins/dual"
mkdir -p "$MKT/.claude-plugin" "$MKT/.agents/plugins" "$PK/.claude-plugin" "$PK/skills/hello"
printf '{"name": "dual-mkt", "owner": {"name": "P"}, "plugins": [{"name": "dual", "source": "./plugins/dual", "description": "dual-packaged"}]}\n' > "$MKT/.claude-plugin/marketplace.json"
printf '{"name": "dual-mkt", "plugins": [{"name": "dual", "source": {"source": "local", "path": "./plugins/dual"}, "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"}, "category": "Developer Tools"}]}\n' > "$MKT/.agents/plugins/marketplace.json"
printf '{"$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json", "name": "dual", "version": "1.1.0", "description": "portable manifest"}\n' > "$PK/plugin.json"
printf '{"name": "dual", "version": "1.0.0", "description": "claude adapter"}\n' > "$PK/.claude-plugin/plugin.json"
printf '{"$schema": "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json", "mcpServers": {"portable-srv": {"type": "stdio", "command": "true"}}}\n' > "$PK/mcp.json"
printf '{"mcpServers": {"claude-srv": {"command": "true"}}}\n' > "$PK/.mcp.json"
printf -- '---\nname: hello\ndescription: Say hello.\n---\n\nHello.\n' > "$PK/skills/hello/SKILL.md"
mkdir -p "$P/home" "$P/xdg" "$P/tmp" "$P/claude" "$P/codex" "$P/copilot" "$P/copilot-cache"; : > "$P/gitconfig"
export HOME="$P/home" XDG_CONFIG_HOME="$P/xdg" TMPDIR="$P/tmp" GIT_CONFIG_GLOBAL="$P/gitconfig" GIT_CONFIG_NOSYSTEM=1 \
  CLAUDE_CONFIG_DIR="$P/claude" CODEX_HOME="$P/codex" COPILOT_HOME="$P/copilot" COPILOT_CACHE_HOME="$P/copilot-cache"
SB='(version 1)(allow default)(deny network-outbound (remote ip))'
run() { echo "### \$ $*"; sandbox-exec -p "$SB" perl -e 'alarm 90; exec @ARGV' "$@" < /dev/null 2>&1 | sed "s#$P#\$PROBE#g"; echo "[exit ${PIPESTATUS[0]}]"; }
run claude plugin marketplace add "$MKT"; run claude plugin install dual@dual-mkt; run claude plugin details dual@dual-mkt
run codex plugin marketplace add "$MKT"; run codex plugin add dual@dual-mkt --json; run codex mcp list --json
run copilot plugin marketplace add "$MKT"; run copilot plugin install dual@dual-mkt; run copilot plugin list; run copilot mcp list
PLAN2C_EOF
~~~~

- [ ] **Step 2: Re-run the probes, isolated, with the real homes snapshotted**

Each script builds its fixture under the directory it is given, exports throwaway homes, denies outbound IP traffic with `sandbox-exec`, and sends no prompt to any model.

~~~~bash
S=$(mktemp -d -t plan2c-probes)
uv run python tests/eval/home_snapshot.py save "$S/before.json" ~/.codex ~/.copilot ~/.claude/plugins
for n in 1 2 3 4; do bash docs/research/2026-09-28-load-and-update-probes/p$n.sh "$S/p$n" > "$S/p$n.out" 2>&1; done
uv run python tests/eval/home_snapshot.py save "$S/after.json" ~/.codex ~/.copilot ~/.claude/plugins
uv run python tests/eval/home_snapshot.py compare "$S/before.json" "$S/after.json"
~~~~

Expected: the compare lists at most `~/.codex/logs_2.sqlite-shm`, `~/.codex/logs_2.sqlite-wal`, and `~/.codex/models_cache.json` (a running Codex app-server daemon); anything else is a leak to explain in the ledger before going on.

- [ ] **Step 3: Check the re-run against the record**

~~~~bash
for pat in 'Skills (2)  hello, review' 'Agents (1)  reviewer' '"name": "named-srv"' \
  'probe-kit:source-command-review' 'Installed 1 skill.' 'Error: Server "named-srv" not found.' \
  'COPILOT_PLUGIN_ROOT'; do grep -qF -- "$pat" "$S/p1.out" && echo "ok   P1 $pat" || echo "DIFF P1 $pat"; done
test "$(grep -c . "$S/p1/starts.log")" = 3 && echo "ok   P1 three starts" || echo "DIFF P1 starts"
for pat in 'already at the latest version (1.0.0)' 'updated from 1.0.0 to 1.0.1' \
  'codex/plugins/cache/focus-timer/focus-timer/1.0.0/skills/focus/SKILL.md: revision B'; do
  grep -qF -- "$pat" "$S/p2.out" && echo "ok   P2 $pat" || echo "DIFF P2 $pat"; done
for pat in 'plugins.1.source: Invalid input, plugins.3.source: Invalid input' \
  'Invalid marketplace.json: plugins.3.source: Invalid input' '"name": "viaurl"'; do
  grep -qF -- "$pat" "$S/p3.out" && echo "ok   P3 $pat" || echo "DIFF P3 $pat"; done
for pat in 'MCP servers (1)  claude-srv' '"version": "1.1.0"' '"name": "portable-srv"' 'dual@dual-mkt (v1.1.0)'; do
  grep -qF -- "$pat" "$S/p4.out" && echo "ok   P4 $pat" || echo "DIFF P4 $pat"; done
~~~~

Expected: every line starts with `ok`.
A `DIFF` means a tool changed since 2026-09-28: do not commit the record as written; record the new observation in a new dated file under `docs/research/`, correct every reference fact that cites it in Task 3, and note it in the ledger.

- [ ] **Step 4: Write the record and index it**

~~~~bash
mkdir -p 'docs/research'
cat > 'docs/research/2026-09-28-load-and-update-probes.md' <<'PLAN2C_EOF'
# Load-observation, update-delivery, and dual-packaging probes

Date: 2026-09-28.
This is a hand-written record of four probes run while writing plan 2c; command output is quoted verbatim from the capture files, trimmed where marked, with the scratch directory shown as `$PROBE`.
The probe scripts are archived beside this record in `2026-09-28-load-and-update-probes/`; the full captures are not, because they hold the probing machine's paths and, from `codex debug prompt-input`, its working directory's instructions.

## Method

Every tool ran with `HOME`, `XDG_CONFIG_HOME`, `TMPDIR`, `GIT_CONFIG_GLOBAL`, `CLAUDE_CONFIG_DIR`, `CODEX_HOME`, `COPILOT_HOME`, and `COPILOT_CACHE_HOME` pointing at throwaway directories under `$PROBE`, with `GIT_CONFIG_NOSYSTEM=1`, stdin from `/dev/null`, a `perl -e 'alarm N; exec @ARGV'` time limit, and inside `sandbox-exec -p '(version 1)(allow default)(deny network-outbound (remote ip))'`, which refuses outbound IP connections.
No command sent a prompt to a model or opened a model session.
`~/.codex`, `~/.copilot`, and `~/.claude/plugins` were snapshotted with `tests/eval/home_snapshot.py` before the first probe and after the last; the only changes were `~/.codex/logs_2.sqlite-shm`, `~/.codex/logs_2.sqlite-wal`, and `~/.codex/models_cache.json`, the files a running Codex app-server daemon writes, as in the plan-2b batches.

Versions: `2.1.284 (Claude Code)`, `codex-cli 0.157.1`, `GitHub Copilot CLI 1.0.89.`

## P1: observing a plugin's components without a model session

The fixture plugin `probe-kit` had one skill (`skills/hello`), one command with a `description` (`commands/review.md`), one agent (`agents/reviewer.md`), a `SessionStart` command hook that appends to a log, a `userConfig` option `api_key` with default `default-key`, a root `.mcp.json` declaring `root-srv`, and `mcpServers: "./config/mcp.json"` in `.claude-plugin/plugin.json` naming a second file that declares `named-srv`.
Each server was `sh -c 'echo "$0 $*" >> $PROBE/starts.log'` with the arguments `<server name>`, `${CLAUDE_PLUGIN_ROOT}`, and `${user_config.api_key}`, so every start was recorded with its arguments as the tool expanded them.
The catalogs were `.claude-plugin/marketplace.json` (source `./plugins/probe-kit`) and `.agents/plugins/marketplace.json` (source `{"source": "local", "path": "./plugins/probe-kit"}`).

### Claude Code

`claude plugin list --json` listed both servers, unexpanded, and started neither (trimmed to one server):

```json
    "mcpServers": {
      "root-srv": {
        "command": "sh",
        "args": [
          "-c",
          "echo \"$0 $*\" >> $PROBE/starts.log",
          "root-srv",
          "${CLAUDE_PLUGIN_ROOT}",
          "${user_config.api_key}"
        ]
      },
```

`claude plugin details probe-kit@probe-mkt` listed every component type, with the command counted as a skill, and started nothing:

```text
Component inventory
  Skills (2)  hello, review
  Agents (1)  reviewer
  Hooks (1)  SessionStart  (harness-only — no model context cost)
  MCP servers (2)  root-srv, named-srv  (tool schemas resolved at runtime; not counted)
  LSP servers (0)
```

`claude mcp list` health-checked, and so started, both servers, expanding both placeholders:

```text
plugin:probe-kit:root-srv: sh -c echo "$0 $*" >> $PROBE/starts.log root-srv $PROBE/mkt/plugins/probe-kit default-key - ✘ Failed to connect — CONNECTION_CLOSED: Connection closed
plugin:probe-kit:named-srv: sh -c echo "$0 $*" >> $PROBE/starts.log named-srv $PROBE/mkt/plugins/probe-kit default-key - ✘ Failed to connect — CONNECTION_CLOSED: Connection closed
```

### Codex

`codex mcp list --json` listed only `named-srv`, the server in the file the manifest names, unexpanded, and started nothing (trimmed):

```json
    "name": "named-srv",
    "enabled": true,
    "transport": {
      "type": "stdio",
      "command": "sh",
      "args": [
        "-c",
        "echo \"$0 $*\" >> $PROBE/starts.log",
        "named-srv",
        "${CLAUDE_PLUGIN_ROOT}",
        "${user_config.api_key}"
      ],
```

`codex debug prompt-input` rendered the model-visible prompt without contacting a model, and listed the skill and the migrated command but no agent:

```text
- probe-kit:hello: Say hello when asked to greet. (file: r2/hello/SKILL.md)
- probe-kit:source-command-review: Review the current diff (file: r1/source-command-review/SKILL.md)
```

It also started `named-srv`, with both placeholders passed through literally, and its prompt carried the `AGENTS.md` of the directory it ran in (`/Users/bdc/projects/skills`), so it reads the working directory's instructions:

```text
named-srv ${CLAUDE_PLUGIN_ROOT} ${user_config.api_key}
```

### Copilot CLI

Install reported one skill, and `copilot skill list` showed the command as a skill; no command listed the agent or the hook:

```text
Plugin "probe-kit" installed successfully. Installed 1 skill.
```

```text
Plugin skills:
  hello - Say hello when asked to greet.
  review - Review the current diff
```

`copilot mcp list` listed only `root-srv`, from the root `.mcp.json`, although the manifest names `./config/mcp.json`; `copilot mcp get named-srv` failed with `Error: Server "named-srv" not found.`
`copilot mcp get root-srv` showed the placeholders unexpanded in the command and three root variables set in the environment, and started nothing:

```text
root-srv
  Status: Enabled
  Type: local
  Command: sh -c echo "$0 $*" >> $PROBE/starts.log root-srv ${CLAUDE_PLUGIN_ROOT} ${user_config.api_key}
  Environment:
    CLAUDE_PLUGIN_ROOT: ***
    COPILOT_PLUGIN_ROOT: ***
    PLUGIN_ROOT: ***
```

### Starts and hooks

The start log held exactly three lines, two from `claude mcp list` and one from `codex debug prompt-input`; the hook log stayed empty.

## P2: does a pushed change reach users without a version bump?

The fixture was a single-plugin repository that is its own marketplace (`source` `./` in both native catalogs, `version` `1.0.0` in `.claude-plugin/plugin.json`, and a skill whose last line names the revision), pushed to a local bare repository.
A throwaway `GIT_CONFIG_GLOBAL` rewrote `https://github.com/acme/`, `git@github.com:acme/`, and `ssh://git@github.com/acme/` to that repository with `insteadOf`, and `CLAUDE_CODE_PLUGIN_PREFER_HTTPS=1` was set, so both tools believed they cloned `github.com/acme/focus-timer`.

| Step | Claude Code installed copy | Codex installed copy |
| --- | --- | --- |
| Add and install revision A, version 1.0.0 | `1.0.0`: revision A | `1.0.0`: revision A |
| Push revision B, version unchanged; `claude plugin marketplace update` and `claude plugin update`; `codex plugin marketplace upgrade` | `1.0.0`: revision A | `1.0.0`: revision B |
| Push revision C, version 1.0.1; the same commands | `1.0.1`: revision C | `1.0.1`: revision C |

Claude Code refused the unbumped change:

```text
✔ focus-timer is already at the latest version (1.0.0).
```

and took the bumped one:

```text
✔ Plugin "focus-timer" updated from 1.0.0 to 1.0.1 for scope user. Restart to apply changes.
```

`codex plugin marketplace upgrade focus-timer --json` replaced the installed copy in place in both cases, with no reinstall:

```json
{
  "selectedMarketplaces": [
    "focus-timer"
  ],
  "upgradedRoots": [
    "$PROBE/codex/.tmp/marketplaces/focus-timer"
  ],
  "errors": []
}
```

## P3: Copilot CLI catalog handling on 1.0.89

The phase-0 control catalog (`docs/research/2026-09-27-phase0-probes.md`) was rejected whole, as on 1.0.88:

```text
Failed to add marketplace: Error: Request plugins.marketplaces.add failed with message: Invalid marketplace.json: plugins.1.source: Invalid input, plugins.3.source: Invalid input
```

A catalog with a local entry and `github`, `url`, and `git-subdir` entries was also rejected whole, naming the `git-subdir` entry:

```text
Failed to add marketplace: Error: Request plugins.marketplaces.add failed with message: Invalid marketplace.json: plugins.3.source: Invalid input
```

Without the `git-subdir` entry the catalog was added, and `copilot plugin marketplace browse ctl-remote2 --json` listed `alpha`, `gh` (`github`), and `viaurl` (`url`).

## P4: which manifest each tool reads from a dual-packaged plugin

The plugin `dual` carried a portable root `plugin.json` (Agent Plugins `$schema`, `version` `1.1.0`) with `mcp.json` declaring `portable-srv`, and a Claude adapter `.claude-plugin/plugin.json` (`version` `1.0.0`) with `.mcp.json` declaring `claude-srv`.

| Tool | Version installed | MCP server listed | Command |
| --- | --- | --- | --- |
| Claude Code | `1.0.0` | `claude-srv` | `claude plugin details dual@dual-mkt` |
| Codex | `1.1.0` | `portable-srv`, with `PLUGIN_ROOT` and `PLUGIN_DATA` set | `codex plugin add dual@dual-mkt --json`, `codex mcp list --json` |
| Copilot CLI | `1.1.0` | `portable-srv` | `copilot plugin list`, `copilot mcp list` |
PLAN2C_EOF
~~~~

~~~~bash
git apply <<'PLAN2C_EOF'
diff --git a/docs/research/README.md b/docs/research/README.md
index 72accaf..8e7077d 100644
--- a/docs/research/README.md
+++ b/docs/research/README.md
@@ -13,6 +13,7 @@ They are archived evidence, so they are exempt from this repo's one-sentence-per
 | [2026-09-27-phase0-probes.md](2026-09-27-phase0-probes.md) | Phase-0 gate: headless isolated probes for Copilot CLI and VS Code | copilot and VS Code 1.139.1 on this machine |
 | [2026-09-27-copilot-pluginroot-probe.md](2026-09-27-copilot-pluginroot-probe.md) | Whether Copilot CLI honours `metadata.pluginRoot` | copilot 1.0.88 on this machine |
 | [2026-09-28-codex-command-migration-probe.md](2026-09-28-codex-command-migration-probe.md) | How Codex loads a Claude Code plugin's commands (hand-written record) | codex-cli 0.157.1 on this machine |
+| [2026-09-28-load-and-update-probes.md](2026-09-28-load-and-update-probes.md) | Seeing what loaded without a model session, update delivery without a version bump, Copilot CLI source handling, and dual-packaged plugins (hand-written record; scripts in [2026-09-28-load-and-update-probes/](2026-09-28-load-and-update-probes/)) | claude 2.1.284, codex-cli 0.157.1, copilot 1.0.89 on this machine |

 These reports are inputs, not references: the skill's references re-verify every fact they use and carry their own provenance.

PLAN2C_EOF
~~~~

~~~~bash
( cd docs/research && shasum -a 256 2026-09-28-load-and-update-probes.md >> SHA256SUMS && sort -k2 SHA256SUMS -o SHA256SUMS )
uv run pytest -q tests/test_research_archive.py
uv run python tools/check_sentence_per_line.py docs/research/2026-09-28-load-and-update-probes.md
~~~~

Expected: `2 passed`; the sentence checker prints nothing and exits 0.

- [ ] **Step 5: Commit**

~~~~bash
git add docs/research/2026-09-28-load-and-update-probes.md docs/research/2026-09-28-load-and-update-probes docs/research/SHA256SUMS docs/research/README.md
git commit -q -m "docs(research): archive load, update, Copilot source, and dual-packaging probes" -m "🤖 Generated with Claude Code"
~~~~

### Task 3: SKILL.md and the references, test-first

The skill is written against the baseline failures: R12 and the workflows bind reporting of unrun checks (s2 criterion 5, s5 criterion 6); the add-a-plugin and release workflows bind version reconciliation (s2 criterion 4); the audit workflow separates defects from suggestions (s6 criterion 8); the references carry the facts arms re-derived by probing (cost in s1, s3, s4), each with provenance; and `validation.md` teaches the safe probing method and how to see what loaded without a model session (every s4 discard).
Two rules extend the spec's wording: R12 adds "name every check that was not run", and R15 adds "or open a model session".

**Files:**
- Create: `tests/test_skill_docs.py`
- Create: `skills/plugin-marketplaces/SKILL.md`
- Create: `skills/plugin-marketplaces/references/{agent-plugins,claude-code,codex,copilot-cli,feature-matrix,freshness,multi-tool,releases,validation}.md`
- Modify: `docs/superpowers/specs/2026-09-27-plugin-marketplaces-design.md` (§6, one line)

**Interfaces:**
- Produces: the provenance format `## Provenance` / `Verified against: … on YYYY-MM-DD.` / rows `| E<n> | evidence | docs|source|probe|run |`, cited as `[E<n>]`; rules as list items `- **R<n>** …` in SKILL.md's `## Rules`; the `## Source types` table in `feature-matrix.md` keyed by `readers.json` source-type names.

- [ ] **Step 1: Write the failing test**

~~~~bash
mkdir -p 'tests'
cat > 'tests/test_skill_docs.py' <<'PLAN2C_EOF'
"""Consistency of SKILL.md and its references (spec §6, §7, §10 Consistency).

Rules live only in SKILL.md's Rules section; references cite rule ids and evidence ids and
never restate a rule; every fact a reference states cites a row of its own Provenance table.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "plugin-marketplaces"
SKILL = SKILL_DIR / "SKILL.md"
REFS = SKILL_DIR / "references"
READERS = SKILL_DIR / "scripts" / "mpcheck" / "data" / "readers.json"
EXPECTED_REFS = {
    "agent-plugins.md",
    "claude-code.md",
    "codex.md",
    "copilot-cli.md",
    "feature-matrix.md",
    "freshness.md",
    "multi-tool.md",
    "releases.md",
    "validation.md",
}
RULE_DEF = re.compile(r"^- \*\*(R\d+)\*\* ", re.M)
RULE_CITE = re.compile(r"\bR(\d+)\b")
EVIDENCE_ROW = re.compile(r"^\| (E\d+) \| (.+) \| (docs|source|probe|run) \|$", re.M)
EVIDENCE_CITE = re.compile(r"\[(E\d+)\]")
LINK = re.compile(r"\]\(([^)\s]+)\)")
REPO_PATH = re.compile(r"`((?:docs|tests)/[^`\s]+)`")
READER_COLUMNS = {"Claude Code": "claude-code", "Codex": "codex", "Copilot CLI": "copilot-cli"}


def section(text: str, heading: str) -> str:
    start = text.index(f"\n{heading}\n")
    following = re.search(r"^## ", text[start + len(heading) + 2 :], re.M)
    end = start + len(heading) + 2 + following.start() if following else len(text)
    return text[start:end]


def docs() -> list[Path]:
    return [SKILL, *sorted(REFS.glob("*.md"))]


def rules() -> list[str]:
    return RULE_DEF.findall(section(SKILL.read_text(encoding="utf-8"), "## Rules"))


def test_the_references_are_exactly_the_planned_files():
    assert {p.name for p in REFS.glob("*.md")} == EXPECTED_REFS


def test_rules_are_numbered_once_and_in_order():
    assert rules() == [f"R{n}" for n in range(1, 16)]
    whole = SKILL.read_text(encoding="utf-8")
    assert len(RULE_DEF.findall(whole)) == 15, "a rule is defined outside the Rules section"


@pytest.mark.parametrize("path", [p.name for p in docs()])
def test_every_cited_rule_exists(path):
    target = SKILL if path == "SKILL.md" else REFS / path
    defined = set(rules())
    cited = {f"R{n}" for n in RULE_CITE.findall(target.read_text(encoding="utf-8"))}
    assert cited <= defined, sorted(cited - defined)


@pytest.mark.parametrize("name", sorted(EXPECTED_REFS))
def test_references_never_define_a_rule(name):
    assert not RULE_DEF.findall((REFS / name).read_text(encoding="utf-8"))


@pytest.mark.parametrize("name", sorted(EXPECTED_REFS))
def test_every_reference_carries_provenance_and_every_citation_resolves(name):
    text = (REFS / name).read_text(encoding="utf-8")
    prov = section(text, "## Provenance")
    assert re.search(r"^Verified against: .+ on \d{4}-\d{2}-\d{2}\.$", prov, re.M), name
    rows = EVIDENCE_ROW.findall(prov)
    ids = [row[0] for row in rows]
    assert ids == [f"E{n}" for n in range(1, len(ids) + 1)], "ids must run E1, E2, ... once"
    body = text.replace(prov, "")
    cited = set(EVIDENCE_CITE.findall(body))
    assert cited == set(ids), {"uncited": set(ids) - cited, "undefined": cited - set(ids)}


@pytest.mark.parametrize("name", sorted(EXPECTED_REFS))
def test_evidence_paths_exist(name):
    prov = section((REFS / name).read_text(encoding="utf-8"), "## Provenance")
    for _, evidence, _ in EVIDENCE_ROW.findall(prov):
        for path in REPO_PATH.findall(evidence):
            assert (ROOT / path).exists(), f"{name}: {path}"


@pytest.mark.parametrize("path", [p.name for p in docs()])
def test_relative_links_resolve(path):
    target = SKILL if path == "SKILL.md" else REFS / path
    for link in LINK.findall(target.read_text(encoding="utf-8")):
        if re.match(r"^[a-z]+:", link) or link.startswith("#"):
            continue
        assert (target.parent / link.split("#")[0]).exists(), f"{path}: {link}"


def test_the_reference_map_lists_every_reference_once():
    mapped = re.findall(
        r"\(references/([^)]+)\)", section(SKILL.read_text(encoding="utf-8"), "## Reference map")
    )
    assert sorted(mapped) == sorted(EXPECTED_REFS)


def test_the_source_type_table_matches_readers_json():
    readers = json.loads(READERS.read_text(encoding="utf-8"))
    table = section((REFS / "feature-matrix.md").read_text(encoding="utf-8"), "## Source types")
    lines = [line for line in table.splitlines() if line.startswith("|")]
    header = [cell.strip() for cell in lines[0].strip("|").split("|")]
    assert header[0] == "Source type" and set(header[1:]) == set(READER_COLUMNS)
    seen = set()
    for line in lines[2:]:
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        source = cells[0].strip("`")
        seen.add(source)
        for column, cell in zip(header[1:], cells[1:], strict=True):
            accepted = source in readers[READER_COLUMNS[column]]["source_types"]
            verdict = re.match(r"(yes|no)\b", cell)
            assert verdict and verdict.group(1) == ("yes" if accepted else "no"), (
                f"{source} / {column}"
            )
    everything = {s for key, r in readers.items() if key != "$comment" for s in r["source_types"]}
    assert seen == everything
PLAN2C_EOF
~~~~

- [ ] **Step 2: Run it to see it fail**

Run: `uv run pytest -q tests/test_skill_docs.py`
Expected: errors or failures on every test, because `skills/plugin-marketplaces/SKILL.md` and `references/` do not exist.

- [ ] **Step 3: Write SKILL.md**

~~~~bash
mkdir -p 'skills/plugin-marketplaces'
cat > 'skills/plugin-marketplaces/SKILL.md' <<'PLAN2C_EOF'
---
name: plugin-marketplaces
description: >-
  User-hosted plugin marketplaces: catalog files a maintainer hosts in a git repository
  so Claude Code, Codex, and GitHub Copilot CLI users can add them.
  Use when creating, auditing, maintaining, or releasing such a marketplace or catalog;
  adding, pinning, bumping, renaming, or removing a plugin entry; diagnosing a tool that
  skips or fails to load catalog entries; or packaging one plugin for several of these
  tools (marketplace.json, plugin.json, .claude-plugin, .agents/plugins, .codex-plugin,
  .github/plugin, agent-plugins.org).
  Not for writing a plugin's hooks, agents, skills, or MCP servers, installing a plugin
  for personal use, or vendor-hosted registries such as the VS Code Marketplace or npm.
license: MIT
compatibility: >-
  The validator needs Python 3.12+ and uv, or the installed check-marketplace command.
  The claude, codex, and copilot CLIs are optional check instruments.
---

# Plugin marketplaces

A user-hosted plugin marketplace is a catalog file that its maintainer writes and hosts, typically in a git repository, and that users register with their tool.
This skill covers three readers — Claude Code, Codex, and GitHub Copilot CLI — and the Agent Plugins 1.0 package format; every fact about them is in `references/`, with provenance.

## Core model

- A **catalog** (`marketplace.json`) lists **entries**; each entry names a plugin and points at its package through a **source**.
- Each tool reads catalogs from its own paths in its own order, and accepts its own set of source types; one catalog file is often read by several tools ([feature-matrix.md](references/feature-matrix.md)).
- A **package** is a plugin directory with one or more manifests (`plugin.json`); tools differ in which manifest they read ([multi-tool.md](references/multi-tool.md)).
- A **version** is the cache key: it decides whether a user receives a change ([releases.md](references/releases.md)).
- Tools fail quietly: Codex skips an entry it cannot read, Copilot CLI rejects a whole catalog for one bad entry, and Claude Code ignores unknown keys; a clean `claude plugin validate` says nothing about the other two.

## Defaults

- Package a plugin meant for several tools as an Agent Plugins root `plugin.json` plus `mcp.json`, with a Claude Code adapter (`.claude-plugin/plugin.json` plus `.mcp.json`), because Claude Code reads only the adapter and Codex and Copilot CLI read only the portable pair.
- Publish one native catalog per tool family you target (`.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json`), parity-checked, because a single shared catalog is limited to the source types every reader of it accepts.
  A single `.claude-plugin/marketplace.json` is a valid choice when its entries use only sources all its declared readers accept; record that choice in `marketplace-policy.json`.

## Workflows

Run the validator from this skill: `check-marketplace <marketplace root>` when it is installed, otherwise `uv run <this skill's directory>/scripts/check_marketplace.py <marketplace root>`; add `--format json` for machine-readable output ([validation.md](references/validation.md)).

### Create a marketplace

1. Write `marketplace-policy.json` with the target readers (R1).
2. Choose catalogs (see Defaults) and source types every declared reader of each catalog accepts (R2, R3, R4).
3. Name entries after their plugins' manifests (R8), and disclose executable components in each description (R11).
4. Set versions (R6), then run the validator and the load checks in [validation.md](references/validation.md) for each reader, isolated (R15).
5. Report as R12 requires.

### Add a plugin

1. Read every manifest the plugin has, and every catalog in the repository.
2. If the plugin's manifests record different versions, do not add it as is: pick one value, set it in every place R6 names, and say in the report which values disagreed and which one you kept and why.
3. Add the entry to every catalog whose readers should offer it; leave a documented intentional difference alone and record any new one (R10).
4. Validate and load-check as in Create, then report as R12 requires.

### Release a plugin version

1. For a remote source, review the change between the pinned content and the new content before moving the pin (R5): list the commits and read the diff, looking for new network calls, data collection, executable components, and changed permissions.
   If the change adds behaviour users did not agree to, hold the release and report why instead of moving the pin.
2. Move every pin for the plugin in every catalog (R4), and change the version everywhere R6 names it (R7).
3. Validate and load-check, then report as R12 requires, including how the release reaches each tool's users ([releases.md](references/releases.md)).

### Audit a marketplace

1. Change no files unless asked.
2. For each declared reader, work out which catalog it reads and which entries it will offer, skip, or reject ([feature-matrix.md](references/feature-matrix.md)).
3. Run the validator, then the load checks the environment allows (R15).
4. Report findings in two lists: **defects** — anything that changes what a tool loads, installs, or delivers, or breaks a rule — each naming the entry, the tool, and the evidence; and **suggestions** — naming, wording, and style — kept out of the defect list.
5. Report every check level as R12 requires; a green CI run or a passing `claude plugin validate` is one check, not a verdict.

### Port a plugin to another tool

1. Read [feature-matrix.md](references/feature-matrix.md) for which of the plugin's components the target tool loads, and in what form.
2. Add the target's manifest additively; never delete another tool's files to make a plugin portable.
3. Load-check the port in each tool without opening a model session ([validation.md](references/validation.md), "Seeing what loaded").
4. Report, per tool, what loads, what loads in another form, and what does not load, citing the reference or the check for each claim.

## Rules

- **R1** Declare the target readers in `marketplace-policy.json` before choosing sources or layouts.
- **R2** Use only source types that every declared reader of that catalog accepts.
- **R3** Local sources start with `./`, contain no `..`, and resolve (after symlinks) inside the marketplace root.
- **R4** Every remote source is pinned to immutable content using its source type's mechanism: a full commit `sha` for git sources (`github`, `url`, `git-subdir`), `sha256` for `archive`, an exact version (not a range or dist-tag) for `npm`; `command` sources are not used in a published catalog because they cannot be pinned; the one exception is a git ref declared as a channel, with a reason, in `marketplace-policy.json`.
- **R5** A pin moves only after the change between the old and new pinned content has been reviewed.
- **R6** For each reader, the plugin's version is set in that reader's authoritative field (the per-reader table in [releases.md](references/releases.md)), and every version value recorded anywhere for that plugin is equal.
- **R7** A release changes the version value in every place R6 records it.
- **R8** A catalog entry's `name` equals the plugin manifest's `name`, and satisfies every declared reader's name rules.
- **R9** Treat a published plugin name as permanent; rename or remove through the reader's documented mechanism (`renames`, `forceRemoveDeletedPlugins`) where one exists.
- **R10** Every difference in membership or version between catalogs in one repo has a recorded reason in `marketplace-policy.json`.
- **R11** An entry's description discloses executable components (hooks, MCP servers, LSP servers, `bin/`) and external services.
- **R12** Report schema, local, remote, catalog-discovery, and package-load results separately; report skipped or inconclusive checks as such, and name every check that was not run.
- **R13** When a covered tool's installed version is newer than the version a reference was verified against, re-check any fact the current decision depends on against the live source before relying on it.
- **R14** When a reference and an official validator disagree, follow the validator and report the disagreement.
- **R15** Never install into the user's real tool configuration, execute plugin code, or open a model session while validating; run each tool with throwaway configuration as [validation.md](references/validation.md) describes, or do not run it.

## Reference map

- [claude-code.md](references/claude-code.md): Claude Code's catalog, entry, source, manifest, name, version, and validator facts; read before writing or checking anything Claude Code reads.
- [codex.md](references/codex.md): Codex's catalog paths, sources, both manifest formats, cache, updates, and Claude interop; read when Codex is a reader.
- [copilot-cli.md](references/copilot-cli.md): Copilot CLI's catalog paths, accepted sources, manifests, and MCP handling; read when Copilot CLI is a reader.
- [agent-plugins.md](references/agent-plugins.md): the portable package format; read when writing or checking a root `plugin.json` or `mcp.json`.
- [feature-matrix.md](references/feature-matrix.md): components, source types, and name and version rules side by side; read to decide what works where.
- [multi-tool.md](references/multi-tool.md): the packaging and catalog defaults, what each tool reads from a dual-packaged plugin, and when to deviate.
- [releases.md](references/releases.md): the per-reader version table (R6), pin moves, and how a change reaches each tool's users; read before any release.
- [validation.md](references/validation.md): check levels, the validator, safe isolated tool checks, seeing what loaded without a model session, and the report format.
- [freshness.md](references/freshness.md): provenance blocks and the R13 procedure; read when a tool is newer than a reference says.
PLAN2C_EOF
~~~~

- [ ] **Step 4: Write the tool references**

~~~~bash
mkdir -p 'skills/plugin-marketplaces/references'
cat > 'skills/plugin-marketplaces/references/claude-code.md' <<'PLAN2C_EOF'
# Claude Code

What Claude Code reads from a user-hosted marketplace and its plugins.
Rules are cited by id from [SKILL.md](../SKILL.md); each fact cites a row of the Provenance table.

## Catalog

- The catalog is `<root>/.claude-plugin/marketplace.json`; relative sources resolve from `<root>`, the directory holding `.claude-plugin/` [E1].
- Required top-level fields are `name`, `owner` (with `owner.name`), and `plugins`; each entry is validated on its own, so one bad entry does not fail the catalog [E1].
- Unknown keys are ignored at load, so a typo loads silently; only `claude plugin validate` warns about them [E1].
- `metadata.pluginRoot` (v2.1.239+) lets a bare name such as `"foo"` resolve under it; without it a source needs `./` [E1].
- `renames` (v2.1.193+) maps an old plugin name to its new name or to `null`, and `forceRemoveDeletedPlugins: true` uninstalls plugins removed from the catalog (R9) [E1].
- There is no catalog field that turns on auto-update; users or admins enable it per marketplace, and it is off by default for third-party marketplaces [E3].

## Entries

- Required entry fields are `name` and `source`; an entry also accepts every `plugin.json` field [E1].
- The entry `name` is the install id (`<name>@<marketplace>`) and the `enabledPlugins` key, and the manifest `name` prefixes the plugin's components; a mismatch gives `Plugin "<x>" not found in marketplace` (R8) [E3].
- When the plugin has its own `plugin.json`, entry `mcpServers`, `lspServers`, `userConfig`, and `channels` are ignored, and entry display fields override the manifest's [E1].
- `strict` (default `true`) makes `plugin.json` the authority and appends entry component fields to it; with `strict: false`, an entry that declares any component field while `plugin.json` also exists fails with `conflicting manifests` [E1].
- Entry `hooks` must be an inline object: an entry giving `hooks` as a path or array passes `claude plugin validate`, installs, and then fails to load with "the file-path and array forms are not yet supported in a marketplace entry" [E1] [E5].

## Sources

| Source | Shape | Pin |
| --- | --- | --- |
| Relative path | `"./plugins/foo"`; `"."` is the root; no `..`, no backslashes | none needed |
| `github` | `{"source": "github", "repo": "owner/repo", "ref"?, "sha"?}` | `sha`, 40 lowercase hex |
| `url` | `{"source": "url", "url": "https://…" or "git@…" or "file://…", "ref"?, "sha"?}` | `sha` |
| `git-subdir` | `{"source": "git-subdir", "url", "path", "ref"?, "sha"?}` | `sha` |
| `npm` | `{"source": "npm", "package", "version"?, "registry"?}` | exact `version` |
| `archive` (v2.1.224+) | `{"source": "archive", "url": "https://…zip", "sha256"?}` | `sha256` |
| `command` (v2.1.229+) | `{"source": "command", "command", "timeout"?, "mode"?}` | cannot be pinned |

The table's shapes and pins are from [E1]; when both `ref` and `sha` are set, `sha` is checked out, which works even after the `ref` is deleted [E1].
Relative paths do not resolve when the catalog itself is fetched as a bare `marketplace.json` URL; host such a catalog in a git repository instead [E10].

## Manifest

- The manifest is `<plugin>/.claude-plugin/plugin.json`, and it is optional: without it, components are auto-discovered and the name comes from the entry [E2].
- Only `name` is required; `version` is any string, not checked as semver [E2].
- Claude Code does not read a portable root `plugin.json` or `mcp.json`; from a plugin carrying both formats it reads only `.claude-plugin/plugin.json` and `.mcp.json` [E9].
- Default component locations are `skills/<name>/SKILL.md`, `commands/`, `agents/`, `hooks/hooks.json`, `.mcp.json`, `.lsp.json`, `output-styles/`, `bin/`, and `settings.json` [E2].
- Declaring `commands`, `agents`, or `outputStyles` replaces the default directory, `skills` adds to it, and `hooks`, `mcpServers`, and `lspServers` merge with the default file, which loads first [E2] [E7].
- Every manifest path starts with `./` and must exist inside the plugin root; `..` fails validation and a symlink leading outside is rejected [E2].
- `${CLAUDE_PLUGIN_ROOT}` (the installed copy, which changes on every update) and `${CLAUDE_PLUGIN_DATA}` (persistent) expand in hook commands, MCP and LSP server `command`, `args`, and `env`, and skill, command, and agent bodies [E2] [E7].
- `userConfig` values are referenced as `${user_config.KEY}`; `sensitive` options are stored in the system keychain, which `CLAUDE_CONFIG_DIR` does not isolate [E2] [E11].
- Files outside the plugin directory are not copied into the cache, so a path such as `../shared` breaks after install [E10].

## Names

- Marketplace names may not contain spaces, `/`, `\`, `..`, or control characters; a list of official names, `npm`, `github`, and similar words, and the `claudeai-` prefix are reserved, and some reserved spellings pass `validate` but fail at `marketplace add` [E3] [E4].
- Plugin names are kebab-case with no spaces, `@`, `:`, or path separators [E2].

## Versions and updates

- The installed version is, in order: `plugin.json` `version`, the entry's `version`, otherwise a value derived from the source (a 12-character commit SHA for git sources and for relative paths in a git-hosted catalog) [E3].
- An explicit version holds every user on the cached copy until the string changes: a pushed change without a bump is refused with `already at the latest version`, and a bumped one is delivered by `claude plugin update` [E3] [E8].
- To deliver every commit instead, omit `version` everywhere; setting it in both `plugin.json` and the entry invites disagreement (R6) [E3].
- Installed plugins are copied to `~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/`; a relative-path plugin from a catalog added as a local directory loads in place [E3].
- Private repositories are fetched with the machine's existing git credentials; there is no token field [E3].

## `claude plugin validate`

- `claude plugin validate <path> [--strict] [--json]` checks the catalog at `<path>/.claude-plugin/marketplace.json` if present, otherwise the plugin manifest [E4].
- Exit codes: 0 passed or passed with warnings, 1 failed or any warning under `--strict`, 2 validator failure [E4].
- A catalog entry version that differs from its manifest is a warning, so the plain run passes and `--strict` fails [E4] [E6].
- It does not catch an entry `hooks` path or array, a relative source whose directory does not exist, a wrong remote repository or path, or exact reserved names; it does not open plugin skill, agent, command, hook, or MCP files from a catalog run [E4].
- It writes `.claude.json` into its configuration directory, so run it with a throwaway `CLAUDE_CONFIG_DIR` (R15) [E12].

## Seeing what loaded

- `claude plugin details <plugin>@<marketplace>` lists skills (commands counted as skills), agents, hooks, MCP servers, and LSP servers, and starts nothing [E7].
- `claude plugin list --json` shows each installed plugin's version and MCP server configuration, and starts nothing [E7].
- `claude mcp list` health-checks every server, which starts plugin MCP servers and so runs plugin code; use it only on a stand-in plugin you wrote (R15) [E7].

## Provenance

Verified against: claude 2.1.283 (documentation reading) and 2.1.284 (probes) on 2026-09-28.
Conformance probes: none yet.

| Id | Evidence | Kind |
| --- | --- | --- |
| E1 | https://code.claude.com/docs/en/plugins/marketplace-reference and https://code.claude.com/docs/en/plugins/create-marketplace, fetched 2026-09-27; `docs/research/2026-09-27-claude-code.md` §1 | docs |
| E2 | https://code.claude.com/docs/en/plugins/manifest-reference, fetched 2026-09-27; `docs/research/2026-09-27-claude-code.md` §2 | docs |
| E3 | https://code.claude.com/docs/en/plugins/loading, https://code.claude.com/docs/en/plugins/host-marketplace, and https://code.claude.com/docs/en/settings-reference, fetched 2026-09-27; `docs/research/2026-09-27-claude-code.md` §3 | docs |
| E4 | https://code.claude.com/docs/en/plugins/cli-reference#plugin-validate, fetched 2026-09-27, and probes on claude 2.1.283; `docs/research/2026-09-27-claude-code.md` §4 | docs |
| E5 | plan-2b baseline s6-r2, call 11: install of an entry with `hooks` as a path; `tests/runs/evidence/2026-09-28-s6-r2-tool-results.jsonl` | run |
| E6 | plan-2b baselines s7-r1 to s7-r3, objective checks; `tests/runs/2026-09-28-s7-r1-baseline.md` | run |
| E7 | probe P1 on claude 2.1.284; `docs/research/2026-09-28-load-and-update-probes.md` | probe |
| E8 | probe P2 on claude 2.1.284; `docs/research/2026-09-28-load-and-update-probes.md` | probe |
| E9 | probe P4 on claude 2.1.284; `docs/research/2026-09-28-load-and-update-probes.md` | probe |
| E10 | https://code.claude.com/docs/en/plugins/host-marketplace, fetched 2026-09-27; `docs/research/2026-09-27-claude-code.md` §5 | docs |
| E11 | plan-2b baselines s4-r4, s4-r7, s4-r8, and s4-r9: `claude plugin install --config` with a sensitive value tried the macOS keychain; `tests/runs/2026-09-28-baseline-summary-2b.md`, Isolation | run |
| E12 | observed in plan 1 and recorded where the validator isolates it: `skills/plugin-marketplaces/scripts/mpcheck/checks_schema.py`, `_default_runner` | source |
PLAN2C_EOF
~~~~

~~~~bash
mkdir -p 'skills/plugin-marketplaces/references'
cat > 'skills/plugin-marketplaces/references/codex.md' <<'PLAN2C_EOF'
# Codex

What the Codex CLI reads from a user-hosted marketplace and its plugins.
Rules are cited by id from [SKILL.md](../SKILL.md); each fact cites a row of the Provenance table.

## Catalog

- Under a marketplace root, Codex reads the first file that exists of `.agents/plugins/marketplace.json`, `.agents/plugins/api_marketplace.json`, `.claude-plugin/marketplace.json`, and `.cursor-plugin/marketplace.json` [E1] [E2].
- So Codex reads a repository with both native catalogs through `.agents/plugins/marketplace.json` only, and a repository with only `.claude-plugin/marketplace.json` through that file [E2].
- Relative sources resolve from the marketplace root, the directory above `.agents/` or `.claude-plugin/` [E1] [E2].
- Required top-level fields are `name` and `plugins`; the marketplace `name` must match `[A-Za-z0-9_-]+`, so no dots; Claude's `owner` and `metadata` are ignored [E2].
- Invalid JSON or a missing `name` or `plugins` fails the whole file, but an entry that cannot be resolved is skipped with only a log warning, so compare what Codex lists against what the catalog holds [E2] [E6].

## Entries

- Required entry fields are `name` and `source`; `name` allows `[A-Za-z0-9._-]` with dots only between non-empty segments [E2].
- `policy.installation` (`AVAILABLE`, the default, `INSTALLED_BY_DEFAULT`, `NOT_AVAILABLE`), `policy.authentication` (`ON_INSTALL`, the default, or `ON_USE`), `policy.products`, and `category` are optional to the parser, though OpenAI's documentation says to always include the first two and `category` [E1] [E2].
- Other entry keys (`version`, `description`, `displayName`, `author`, …) are a fallback manifest, used when the plugin has none, so Claude-style `strict: false` entries work [E2].
- Install refuses an entry whose `name` differs from the plugin manifest's: ``plugin.json name `linter` does not match marketplace plugin name `lint` `` (R8) [E2] [E8].

## Sources

| Source | Shape |
| --- | --- |
| Local | `"./plugins/foo"` or `{"source": "local", "path": "./plugins/foo"}`; must start with `./` except in `.cursor-plugin/marketplace.json`; no `..` |
| `url` | `{"source": "url", "url", "path"?, "ref"?, "sha"?}`: a git repository, plugin at its root or at `path` |
| `git-subdir` | `{"source": "git-subdir", "url", "path", "ref"?, "sha"?}` |
| `npm` | `{"source": "npm", "package", "version"?, "registry"?}` |

The shapes are from [E2].
Any other source, including Claude Code's `{"source": "github", …}` with or without `ref` and `sha`, is dropped without an error; the same repository given as a `url` or `git-subdir` source is listed [E2] [E7].

## Manifests

Codex reads one of two formats [E3]:

- **Portable**: a root `plugin.json` that is a regular file (not a symlink) whose `$schema` is `https://agent-plugins.org/schemas/1.0.0/plugin.schema.json`; skills come from `skills/` and MCP servers from `mcp.json`, and nothing in the manifest can move them.
  OpenAI-specific settings go under `extensions["com.openai"]`, which, when present, replaces `.codex-plugin/plugin.json` as the overlay rather than merging with it.
- **Compatibility**: otherwise, the first of `.codex-plugin/plugin.json`, `.claude-plugin/plugin.json`, and `.cursor-plugin/plugin.json`; skills default to `skills/`, MCP to `.mcp.json`, hooks to `hooks/hooks.json`.
- Display metadata lives in an `interface` object (`displayName`, `shortDescription`, `longDescription`, `developerName`, `category`, `capabilities`, `websiteURL`, `defaultPrompt`, `brandColor`, `logo`, and others), in `.codex-plugin/plugin.json` or under `extensions["com.openai"]`; OpenAI's directory submission checks stricter limits than the CLI [E3] [E6].
- A root `plugin.json` without the Agent Plugins `$schema` is ignored, and Codex falls back to the compatibility manifests [E6].
- When a plugin carries both a portable root `plugin.json` and `.claude-plugin/plugin.json`, Codex installs the root manifest's version and reads `mcp.json`, not `.mcp.json` [E9] [E14].
- In the compatibility format, a manifest `mcpServers` path replaces the default `.mcp.json`: only the named file's servers are configured [E12].
- Manifest paths must start with `./` and stay inside the plugin; a path that breaks this is ignored with a warning, not an error [E3] [E6].

## Claude Code plugins in Codex

- Not supported: `commands` as commands, `agents`, `userConfig` and `${user_config.*}`, `outputStyles`, `lspServers`, `channels`, `dependencies`, and prompt or agent hook handlers [E5].
- A command whose frontmatter has a non-empty `description` is migrated on install into a skill named `source-command-<name>`, capped at 4,000 bytes [E5] [E11] [E12].
- A plugin's agent does not appear among the components Codex presents to the model [E12].
- `${CLAUDE_PLUGIN_ROOT}` and `${user_config.*}` in an MCP server's arguments are passed to the server literally, not expanded [E10] [E12].
- Hook commands receive `PLUGIN_ROOT` and `PLUGIN_DATA`, plus `CLAUDE_PLUGIN_ROOT` and `CLAUDE_PLUGIN_DATA` for compatibility, and plugin hooks run only after the user trusts them [E3].

## Install, cache, and updates

- `codex plugin marketplace add <path | owner/repo[@ref] | git URL>` registers a marketplace in `config.toml`; a git marketplace is cloned to `$CODEX_HOME/.tmp/marketplaces/<name>` [E4] [E13].
- `codex plugin add <plugin>@<marketplace>` copies the plugin to `$CODEX_HOME/plugins/cache/<marketplace>/<plugin>/<version>/`, where `<version>` is the manifest's `version`, else `local` (compatibility) or `1.0.0` (portable) [E4].
- The whole plugin directory is copied, not only the files its manifest names, so load-check a clean export (`git archive`) rather than a working tree with build output in it [E12].
- `codex plugin marketplace upgrade [<name>]` refreshes a git marketplace and replaces installed copies in place, delivering a pushed change even when the version did not change [E13].
- There is no project auto-discovery to rely on in the CLI: in a fresh repository `codex plugin marketplace list` printed no marketplaces until one was added [E4].

## Checking

- There is no `validate` command; the local check is `codex plugin marketplace add <root>` then `codex plugin list --available --json`, compared entry by entry with the catalog [E6].
- `CODEX_HOME` must exist before Codex runs, and even `codex --version` and `--help` write temporary state into it, so point it at a throwaway directory first (R15) [E11] [E15].
- `codex mcp list --json` shows each configured plugin MCP server, unexpanded, and starts nothing [E12] [E14].
- `codex debug prompt-input` lists the skills Codex would present, including migrated commands, without contacting a model, but it starts plugin MCP servers and includes the working directory's `AGENTS.md`; run it only on a stand-in plugin you wrote, from inside the throwaway directory (R15) [E12].

## Provenance

Verified against: codex-cli 0.157.1 (source reading and probes) on 2026-09-28.
Conformance probes: none yet.

| Id | Evidence | Kind |
| --- | --- | --- |
| E1 | https://developers.openai.com/plugins/build/plugins.md, fetched 2026-09-27; `docs/research/2026-09-27-codex.md` §1 | docs |
| E2 | `openai/codex` at `659b35f1316eda27ef61850dd0832c4a4e95c120`: `codex-rs/core-plugins/src/marketplace.rs`, `core-plugins/src/store.rs`, `core-plugin-common/src/plugin_id.rs`, and a probe on codex-cli 0.157.1; `docs/research/2026-09-27-codex.md` §1 | source |
| E3 | the same commit: `utils/plugins/src/plugin_namespace.rs`, `core-plugins/src/agent_plugin_manifest.rs`, `core-plugins/src/manifest.rs`, and https://developers.openai.com/plugins/build/plugins.md; `docs/research/2026-09-27-codex.md` §2 | source |
| E4 | the same commit (`installed_marketplaces.rs`, `store.rs`, `manager.rs`) and probes on codex-cli 0.157.1; `docs/research/2026-09-27-codex.md` §3 | source |
| E5 | https://developers.openai.com/plugins/guides/submit-claude-plugin.md, fetched 2026-09-27, and `core-plugins/src/command_migration*.rs` at the same commit; `docs/research/2026-09-27-codex.md` §4 | docs |
| E6 | `docs/research/2026-09-27-codex.md` §5 | source |
| E7 | plan-2b baseline s7-r3, call 9: `github` entries dropped, `url` and `git-subdir` listed; `tests/runs/evidence/2026-09-28-s7-r3-tool-results.jsonl` | run |
| E8 | plan-2b baseline s6-r2, call 8; `tests/runs/evidence/2026-09-28-s6-r2-tool-results.jsonl` | run |
| E9 | plan-2b baseline s2-r3, call 7; `tests/runs/evidence/2026-09-28-s2-r3-tool-results.jsonl` | run |
| E10 | plan-2b baseline s1-r2, call 22; `tests/runs/evidence/2026-09-28-s1-r2-tool-results.jsonl` | run |
| E11 | Codex command-migration probe on codex-cli 0.157.1; `docs/research/2026-09-28-codex-command-migration-probe.md` | probe |
| E12 | probe P1 on codex-cli 0.157.1; `docs/research/2026-09-28-load-and-update-probes.md` | probe |
| E13 | probe P2 on codex-cli 0.157.1; `docs/research/2026-09-28-load-and-update-probes.md` | probe |
| E14 | probe P4 on codex-cli 0.157.1; `docs/research/2026-09-28-load-and-update-probes.md` | probe |
| E15 | plan-2b home snapshots: temporary state from exempt `codex --version` and `--help` calls; `tests/runs/2026-09-28-baseline-summary-2b.md`, Isolation | run |
PLAN2C_EOF
~~~~

~~~~bash
mkdir -p 'skills/plugin-marketplaces/references'
cat > 'skills/plugin-marketplaces/references/copilot-cli.md' <<'PLAN2C_EOF'
# GitHub Copilot CLI

What Copilot CLI reads from a user-hosted marketplace and its plugins.
Rules are cited by id from [SKILL.md](../SKILL.md); each fact cites a row of the Provenance table.

## Catalog

- Copilot CLI reads the first file that exists of `marketplace.json`, `.plugin/marketplace.json`, `.github/plugin/marketplace.json`, and `.claude-plugin/marketplace.json`; it does not read `.agents/plugins/marketplace.json` [E1].
- Users register a marketplace with `copilot plugin marketplace add <owner/repo[#ref] | URL | path>`; `github/copilot-plugins` and `github/awesome-copilot` are registered by default [E1].
- The catalog uses the Claude Code dialect: `name`, `owner`, `metadata`, and `plugins[]` whose entries have `name`, `description`, `version`, and `source` [E1].
- Accepted sources are relative paths, `github`, and `url`, each git source with optional `ref` and `sha` [E1] [E4].
- One entry with any other source — `git-subdir`, `npm`, or an unknown type — makes `copilot plugin marketplace add` reject the whole catalog, naming the entry: `Invalid marketplace.json: plugins.3.source: Invalid input` [E2] [E4].
- A relative path without `./` is accepted, and a bare name resolves under `metadata.pluginRoot` [E2] [E3].
- Two entries that resolve to manifests with the same `name` collapse into one listed plugin (R8) [E2].

## Plugins

- From a plugin that carries both a portable root `plugin.json` and `.claude-plugin/plugin.json`, Copilot CLI reads the root manifest's version and the portable `mcp.json` [E5].
- A plugin installed from a catalog added as a local directory is loaded live from that directory, not copied: "It is loaded live from …, so edits take effect on the next session — nothing was copied." [E2] [E6]
- A plugin's commands are offered as skills [E6].
- When a Claude-format plugin has a root `.mcp.json`, Copilot CLI configures the servers in it and ignores the file the manifest's `mcpServers` names [E6].
- Server arguments containing `${CLAUDE_PLUGIN_ROOT}` or `${user_config.*}` are shown unexpanded, and the server's environment carries `CLAUDE_PLUGIN_ROOT`, `COPILOT_PLUGIN_ROOT`, and `PLUGIN_ROOT` [E6].
- A failed install still leaves a listing entry, distinguishable only by `enabled: false` and no `version`, so check both, not list membership [E2].

## Isolation

- `COPILOT_HOME` and `COPILOT_CACHE_HOME` isolate Copilot CLI's configuration and cache [E2].
- They do not isolate its sign-in: a prompt, an interactive session, or `copilot --acp` from a throwaway home still uses the machine's GitHub account, and one such session reached GitHub's Copilot service; never open one to check a plugin (R15) [E7].

## Seeing what loaded

- `copilot plugin install` reports what it loaded (`Installed 1 skill.`), and `copilot plugin list` shows the version and whether the plugin is enabled [E2] [E6].
- `copilot skill list` lists plugin skills, including commands; `copilot mcp list` and `copilot mcp get <server>` show plugin MCP servers; none of them starts a server [E6].
- No command shows a plugin's agents or hooks, so those load checks are unproven for Copilot CLI [E6].

## Provenance

Verified against: copilot 1.0.88 (phase-0 and pluginRoot probes) and 1.0.89 (plan-2c probes) on 2026-09-28.
Conformance probes: none yet.

| Id | Evidence | Kind |
| --- | --- | --- |
| E1 | https://docs.github.com/en/copilot/reference/cli-plugin-reference, "File locations", fetched 2026-09-27; `docs/research/2026-09-27-other-harnesses.md`, GitHub Copilot CLI | docs |
| E2 | phase-0 probes on copilot 1.0.88; `docs/research/2026-09-27-phase0-probes.md` | probe |
| E3 | `metadata.pluginRoot` probe on copilot 1.0.88; `docs/research/2026-09-27-copilot-pluginroot-probe.md` | probe |
| E4 | probe P3 on copilot 1.0.89; `docs/research/2026-09-28-load-and-update-probes.md` | probe |
| E5 | probe P4 on copilot 1.0.89; `docs/research/2026-09-28-load-and-update-probes.md` | probe |
| E6 | probe P1 on copilot 1.0.89; `docs/research/2026-09-28-load-and-update-probes.md` | probe |
| E7 | plan-2b s4 adjudications (s4-r7, call 33) and the scenario rules; `tests/runs/2026-09-28-baseline-summary-2b.md`, Isolation, and `tests/scenarios.md`, How to run | run |
PLAN2C_EOF
~~~~

~~~~bash
mkdir -p 'skills/plugin-marketplaces/references'
cat > 'skills/plugin-marketplaces/references/agent-plugins.md' <<'PLAN2C_EOF'
# Agent Plugins 1.0

The portable plugin package format published at agent-plugins.org.
Rules are cited by id from [SKILL.md](../SKILL.md); each fact cites a row of the Provenance table.

## Status

- Spec 1.0.0 is published; 1.1.0 is a working draft that differs only in version strings and schema ids [E1].
- The spec defines a package, not a catalog: marketplaces and distribution are out of its scope, so each tool supplies its own catalog [E1].
- Codex and Copilot CLI read the portable manifest; Claude Code does not, and is not listed as a compatible client [E1] [E2].
- A technical steering committee with members from Amazon, Cursor, Microsoft, OpenAI, and Vercel governs the spec, and no single vendor may hold a majority; Anthropic is not a member [E1].
- There is no official validator or conformance suite; the published JSON Schemas are the only machine check, and the spec text wins where they disagree [E3].

## `plugin.json`

- Exactly one manifest, `plugin.json` at the plugin root; no other file can replace or supplement its core fields [E4].
- The top level is closed: `$schema`, `name`, `version`, `description`, `author` (`name`, `email`, `url` only), `homepage`, `repository`, `license`, `keywords`, `extensions` [E4].
- `$schema` is required and must be `https://agent-plugins.org/schemas/1.0.0/plugin.schema.json`; clients must not fetch it and must reject unsupported versions [E4].
- `name` is required: 1 to 64 characters from `[a-z0-9.-]`, alphanumeric at both ends, with no `--` or `..` [E4].
- `version` is any string; SemVer is recommended, not enforced [E4].
- An unknown top-level key, or an `extensions` value that is not an object, is reported and ignored; any other violation rejects the whole plugin [E4].
- Client-specific data goes under `extensions."<reverse-domain>"` (OpenAI uses `com.openai`), and client files under a top-level directory named after that namespace [E4] [E2].

## Components

- Only two component types exist, at fixed locations: skills at `skills/<dir>/SKILL.md` (immediate children only) and MCP servers in the root `mcp.json` [E4].
- `mcp.json` holds `$schema` (`https://agent-plugins.org/schemas/1.0.0/mcp.schema.json`, same version as `plugin.json`) and `mcpServers`, nothing else [E4].
- Every server declares `type`: `stdio` (`command` as one token, a bare name or `./path`, plus `args`, `env`, `cwd`), `streamable-http`, or `sse` (`url`, `headers`) [E4].
- `${PLUGIN_ROOT}` and `${PLUGIN_DATA}` expand only in `args`, `env` values, and `cwd`; URLs and headers get no expansion, and secrets belong in neither `env` nor `headers` [E4].
- A Claude Code `.mcp.json` does not become a valid `mcp.json` by renaming: add `type` to each server, write `"http"` as `"streamable-http"`, and replace `${CLAUDE_PLUGIN_ROOT}` with `${PLUGIN_ROOT}` [E2] [E5].
- Commands, hooks, agents, and LSP servers have no portable form; keep them in a tool's own package or under that tool's extension namespace [E4] [E2].
- Failure is graded: a bad manifest rejects the plugin, a bad `mcp.json` drops MCP while skills still load, a bad server entry skips that server, and a bad skill skips that skill [E4].
- Every package path must resolve inside the plugin root, including through symlinks [E4].

## Known schema defects

- Issue #76: the `name` pattern uses a lookahead, which RE2 and Go regular expressions cannot compile [E3].
- Issue #77: strict schema validation rejects manifests the spec requires clients to accept (unknown keys, a non-object `extensions`), so a loader must apply the report-and-ignore exceptions on top of the schema [E3].

## Provenance

Verified against: agent-plugins-spec at `ff8ab5e392` and the published 1.0.0 schemas on 2026-09-27.
Conformance probes: none yet.

| Id | Evidence | Kind |
| --- | --- | --- |
| E1 | https://agent-plugins.org/ and `agentplugins/agent-plugins-spec` at `ff8ab5e392`, including `FUTURE_CONSIDERATIONS.md` and discussions #50, #52, #57; `docs/research/2026-09-27-agent-plugins.md` §1 and §3 | docs |
| E2 | `agentplugins/agent-plugins-example` at `5f3f5084a8`, `migrate-agent-plugin` skill, and https://developers.openai.com/codex/plugins/build.md; `docs/research/2026-09-27-agent-plugins.md` §4 | docs |
| E3 | https://agent-plugins.org/schemas/1.0.0/plugin.schema.json and mcp.schema.json, issues #76 and #77; `docs/research/2026-09-27-agent-plugins.md` §5 | docs |
| E4 | `spec/1.0.0.md` at `agentplugins/agent-plugins-spec@ff8ab5e392`, §4 to §10; `docs/research/2026-09-27-agent-plugins.md` §2 | docs |
| E5 | `https://developers.openai.com/plugins/build/plugins.md`, the portable-format note that each server needs a transport `type`; `docs/research/2026-09-27-codex.md` §5 | docs |
PLAN2C_EOF
~~~~

- [ ] **Step 5: Write the cross-tool references**

~~~~bash
mkdir -p 'skills/plugin-marketplaces/references'
cat > 'skills/plugin-marketplaces/references/feature-matrix.md' <<'PLAN2C_EOF'
# Feature matrix

What works where, side by side; each tool's reference has the detail.
Rules are cited by id from [SKILL.md](../SKILL.md); each cell cites a row of the Provenance table.
"Unproven" means no command shows the behaviour without a model session, so it has not been observed.

## Components

| Component | Claude Code | Codex | Copilot CLI | Agent Plugins 1.0 |
| --- | --- | --- | --- | --- |
| Skills | `skills/<name>/SKILL.md`; manifest `skills` adds directories [E1] | `skills/` [E2] [E3] | loaded, listed by `copilot skill list` [E3] | `skills/<dir>/SKILL.md`, fixed [E5] |
| Commands | `commands/`; listed among skills [E1] [E3] | migrated to a skill `source-command-<name>` when the command has a `description` [E2] [E6] | offered as skills [E3] | none [E5] |
| Agents | `agents/` [E1] | not loaded [E2] [E3] | unproven [E3] | none [E5] |
| Hooks | `hooks/hooks.json`, merged with manifest `hooks` [E1] | `hooks/hooks.json` (compatibility format) or `extensions["com.openai"].hooks` (portable), run after the user trusts them; no prompt or agent handlers [E2] | unproven [E3] | none [E5] |
| MCP servers | `.mcp.json` merged with manifest `mcpServers`; placeholders expanded [E1] [E3] | compatibility: manifest `mcpServers` replaces `.mcp.json`; portable: `mcp.json`; placeholders passed literally [E2] [E3] [E4] | root `.mcp.json` over the manifest's file; portable `mcp.json` when a root `plugin.json` exists; placeholders shown unexpanded [E3] [E4] | `mcp.json`, each server typed [E5] |
| `userConfig` | supported, `${user_config.KEY}` [E1] | not supported [E2] | not expanded [E3] | none [E5] |
| LSP servers | `.lsp.json` [E1] | not supported [E2] | unproven [E3] | none [E5] |

## Source types

| Source type | Claude Code | Codex | Copilot CLI |
| --- | --- | --- | --- |
| `path` | yes [E7] | yes [E8] | yes [E9] |
| `local-object` | no [E7] | yes [E8] | no [E9] |
| `github` | yes [E7] | no, dropped silently [E8] | yes [E9] |
| `url` | yes [E7] | yes [E8] | yes [E9] |
| `git-subdir` | yes [E7] | yes [E8] | no, whole catalog rejected [E9] |
| `npm` | yes [E7] | yes [E8] | no, whole catalog rejected [E9] |
| `archive` | yes [E7] | no [E8] | no [E9] |
| `command` | yes [E7] | no [E8] | no [E9] |

`path` is a relative path string, and `local-object` is Codex's `{"source": "local", "path": …}`; the validator reads this table's values from `scripts/mpcheck/data/readers.json`, and a test keeps the two equal.

## Names, versions, and caches

| Question | Claude Code | Codex | Copilot CLI |
| --- | --- | --- | --- |
| Marketplace name | no spaces, `/`, `\`, `..`; reserved names [E7] | `[A-Za-z0-9_-]+` [E8] | no documented rule [E9] |
| Entry vs manifest `name` | must match, or `not found in marketplace` [E7] | must match, or install refuses [E8] | same-named manifests collapse into one plugin [E9] |
| Version it installs | `.claude-plugin/plugin.json`, then entry, then derived from the source [E7] [E4] | root `plugin.json` (portable), else the compatibility manifest, then entry [E8] [E4] | root `plugin.json` when present [E4] |
| Change without a version bump | not delivered [E10] | delivered by `codex plugin marketplace upgrade` [E10] | local catalogs load live; remote unproven [E9] |

## Provenance

Verified against: claude 2.1.284, codex-cli 0.157.1, copilot 1.0.89 on 2026-09-28.
Conformance probes: none yet.

| Id | Evidence | Kind |
| --- | --- | --- |
| E1 | https://code.claude.com/docs/en/plugins/manifest-reference, fetched 2026-09-27; `docs/research/2026-09-27-claude-code.md` §2 | docs |
| E2 | `openai/codex` at `659b35f1316eda27ef61850dd0832c4a4e95c120` and https://developers.openai.com/plugins/guides/submit-claude-plugin.md; `docs/research/2026-09-27-codex.md` §2 and §4 | source |
| E3 | probe P1; `docs/research/2026-09-28-load-and-update-probes.md` | probe |
| E4 | probe P4; `docs/research/2026-09-28-load-and-update-probes.md` | probe |
| E5 | Agent Plugins `spec/1.0.0.md` §6; `docs/research/2026-09-27-agent-plugins.md` §2 | docs |
| E6 | Codex command-migration probe; `docs/research/2026-09-28-codex-command-migration-probe.md` | probe |
| E7 | https://code.claude.com/docs/en/plugins/marketplace-reference and loading, fetched 2026-09-27; `docs/research/2026-09-27-claude-code.md` §1 and §3 | docs |
| E8 | `openai/codex` at `659b35f1316eda27ef61850dd0832c4a4e95c120` (`marketplace.rs`, `plugin_id.rs`, `store.rs`) and probes on codex-cli 0.157.1; `docs/research/2026-09-27-codex.md` §1 | source |
| E9 | Copilot CLI plugin reference and probes on copilot 1.0.88 and 1.0.89; `docs/research/2026-09-27-other-harnesses.md`, `docs/research/2026-09-27-phase0-probes.md`, and `docs/research/2026-09-28-load-and-update-probes.md` P3 | probe |
| E10 | probe P2; `docs/research/2026-09-28-load-and-update-probes.md` | probe |
PLAN2C_EOF
~~~~

~~~~bash
mkdir -p 'skills/plugin-marketplaces/references'
cat > 'skills/plugin-marketplaces/references/multi-tool.md' <<'PLAN2C_EOF'
# Serving several tools

The packaging and catalog defaults in [SKILL.md](../SKILL.md), why they are the defaults, and when to deviate.
Rules are cited by id; each fact cites a row of the Provenance table.

## What each tool reads from a dual-packaged plugin

A dual-packaged plugin has a portable root `plugin.json` and `mcp.json` and a Claude Code adapter, `.claude-plugin/plugin.json` and `.mcp.json`, sharing one `skills/` directory.

| Tool | Manifest it reads | MCP file it reads |
| --- | --- | --- |
| Claude Code | `.claude-plugin/plugin.json` | `.mcp.json` |
| Codex | root `plugin.json` | `mcp.json` |
| Copilot CLI | root `plugin.json` | `mcp.json` |

The table is from [E1].
Each tool ignores the other pair, so the two manifests must agree on `name` (R8) and `version` (R6), and the two MCP files must declare the same servers.

## Writing the pair

- Root `plugin.json` holds only the Agent Plugins fields, with `$schema` set; everything Claude-specific stays in `.claude-plugin/plugin.json` [E2].
- `mcp.json` repeats each `.mcp.json` server with an explicit `type`, `"streamable-http"` for `"http"`, and `${PLUGIN_ROOT}` for `${CLAUDE_PLUGIN_ROOT}` [E2] [E3].
- Commands, agents, hooks, `userConfig`, and LSP servers have no portable form: keep them in the Claude adapter, and give Codex hooks through `extensions["com.openai"].hooks` in the root manifest if Codex should run them [E2] [E3].
- Migrate additively: add the portable pair beside the existing files and remove nothing another tool reads [E2].

## Why two native catalogs

- Codex reads `.agents/plugins/marketplace.json` before `.claude-plugin/marketplace.json`, and Copilot CLI reads `.github/plugin/marketplace.json` and two other paths before `.claude-plugin/marketplace.json`, so each tool family can have its own catalog [E4] [E5].
- The readers disagree on sources: Codex silently drops `github` entries, and Copilot CLI rejects a whole catalog that holds one `git-subdir` or `npm` entry [E4] [E6].
- A single shared catalog is therefore limited to the source types all its readers accept (R2): relative paths and `url`, for a `.claude-plugin/marketplace.json` read by all three tools [E4] [E6].
- Separate catalogs let each tool get its best source type, at the cost of keeping them in step, which the validator checks against the reasons recorded for differences (R10).

## When to deviate

- One `.claude-plugin/marketplace.json` is enough when every entry is a relative path or a `url` source and no reader needs a different membership; declare all three readers in `marketplace-policy.json` (R1) [E4] [E6].
- A plugin only Claude Code users will install needs no portable manifest.
- A `.github/plugin/marketplace.json` for Copilot CLI is a third catalog, taking precedence for Copilot CLI over `.claude-plugin/marketplace.json`; it needs the same parity records (R10) [E5].

## Provenance

Verified against: claude 2.1.284, codex-cli 0.157.1, copilot 1.0.89 on 2026-09-28.
Conformance probes: none yet.

| Id | Evidence | Kind |
| --- | --- | --- |
| E1 | probe P4; `docs/research/2026-09-28-load-and-update-probes.md` | probe |
| E2 | `agentplugins/agent-plugins-example` at `5f3f5084a8`, `migrate-agent-plugin` skill, and the Codex build documentation; `docs/research/2026-09-27-agent-plugins.md` §4 | docs |
| E3 | Agent Plugins `spec/1.0.0.md` §6 and §9; `docs/research/2026-09-27-agent-plugins.md` §2 | docs |
| E4 | `openai/codex` at `659b35f1316eda27ef61850dd0832c4a4e95c120`, `marketplace.rs`, and a probe on codex-cli 0.157.1; `docs/research/2026-09-27-codex.md` §1 | source |
| E5 | https://docs.github.com/en/copilot/reference/cli-plugin-reference, fetched 2026-09-27; `docs/research/2026-09-27-other-harnesses.md`, GitHub Copilot CLI | docs |
| E6 | probe P3 on copilot 1.0.89; `docs/research/2026-09-28-load-and-update-probes.md` | probe |
PLAN2C_EOF
~~~~

~~~~bash
mkdir -p 'skills/plugin-marketplaces/references'
cat > 'skills/plugin-marketplaces/references/releases.md' <<'PLAN2C_EOF'
# Releases

Versions, pins, and how a change reaches each tool's users.
Rules are cited by id from [SKILL.md](../SKILL.md); each fact cites a row of the Provenance table.

## Where each reader takes the version from (R6)

| Reader | Authoritative field | Also recorded, and must be equal |
| --- | --- | --- |
| Claude Code | `.claude-plugin/plugin.json` `version`; the catalog entry's `version` only when the manifest has none | entry `version` in `.claude-plugin/marketplace.json` |
| Codex | root `plugin.json` `version` when it carries the Agent Plugins `$schema`, else the first of `.codex-plugin/plugin.json` and `.claude-plugin/plugin.json`; the entry's `version` only as a fallback manifest | entry `version` in `.agents/plugins/marketplace.json` |
| Copilot CLI | root `plugin.json` `version` when present, else the Claude-format manifest | entry `version` in the catalog it reads |

The rows are from [E1], [E2], [E3], and, for Copilot CLI's Claude-format fallback, [E6].
Omitting `version` everywhere is also consistent: Claude Code then derives it from the commit, and Codex names its cache directory `local` or `1.0.0` [E1] [E2].
When two recorded values disagree, no tool reports it except `claude plugin validate`, as a warning: each tool silently installs the value from its own authoritative field, so users of different tools get different versions [E1] [E4].

## How a change reaches users

| Reader | Pushed change, version unchanged | Pushed change, version bumped |
| --- | --- | --- |
| Claude Code | not delivered: `already at the latest version` | delivered by `claude plugin update`, or by auto-update where the user enabled it |
| Codex | delivered by `codex plugin marketplace upgrade`, which replaces the installed copy in place | delivered the same way |
| Copilot CLI | a catalog added as a local directory loads live; remote catalogs unproven | unproven |

The Claude Code and Codex rows are from [E5]; the Copilot CLI row is from [E6].
So a maintainer who publishes without a bump reaches Codex users and not Claude Code users; bump on every release (R7) unless you deliberately omit `version` everywhere.

## Moving a pin (R4, R5)

1. Fetch the new tag or commit into a local clone or mirror, and confirm the tag points at the commit you were given: `git -C <clone> rev-parse <tag>^{commit}`.
2. Review what changed: `git -C <clone> log --oneline <old sha>..<new sha>` and `git -C <clone> diff <old sha> <new sha>`.
   Look for new network destinations, collected data, new executable components or install scripts, widened permissions, and changed MCP server commands.
3. Record in the report what the review found, including "nothing notable" when that is the finding.
4. Change `sha` (and `ref`, if the entry has one) in every catalog that lists the plugin, then the version everywhere R6 records it.
5. A `ref` without `sha` is allowed only as a declared channel in `marketplace-policy.json` (R4).

A pinned `sha` still installs after its `ref` is deleted or moved, except on hosts that cannot fetch a commit by SHA [E1].

## Renames and removals (R9)

- Claude Code: add the old name to the catalog's `renames` map with the new name, or `null` for a removal; `forceRemoveDeletedPlugins: true` uninstalls removed plugins for users [E1].
- Codex and Copilot CLI document no rename mechanism; a renamed plugin is a new plugin to their users [E2] [E6].

## Provenance

Verified against: claude 2.1.284, codex-cli 0.157.1, copilot 1.0.89 on 2026-09-28.
Conformance probes: none yet.

| Id | Evidence | Kind |
| --- | --- | --- |
| E1 | https://code.claude.com/docs/en/plugins/marketplace-reference and loading, fetched 2026-09-27; `docs/research/2026-09-27-claude-code.md` §1 and §3 | docs |
| E2 | `openai/codex` at `659b35f1316eda27ef61850dd0832c4a4e95c120`, `plugin_namespace.rs`, `store.rs`, and `manager.rs`; `docs/research/2026-09-27-codex.md` §2 and §3 | source |
| E3 | probe P4 on all three tools; `docs/research/2026-09-28-load-and-update-probes.md` | probe |
| E4 | plan-2b baselines s2-r1 to s2-r3 (lint-kit's disagreeing manifests) and s7 objective checks; `tests/runs/evidence/2026-09-28-s2-r3-tool-results.jsonl` and `tests/runs/2026-09-28-s7-r1-baseline.md` | run |
| E5 | probe P2 on claude 2.1.284 and codex-cli 0.157.1; `docs/research/2026-09-28-load-and-update-probes.md` | probe |
| E6 | phase-0 probes and probe P1 on Copilot CLI; `docs/research/2026-09-27-phase0-probes.md` and `docs/research/2026-09-28-load-and-update-probes.md` | probe |
PLAN2C_EOF
~~~~

~~~~bash
mkdir -p 'skills/plugin-marketplaces/references'
cat > 'skills/plugin-marketplaces/references/validation.md' <<'PLAN2C_EOF'
# Validation

How to check a marketplace, what each check can prove, and how to report the result (R12).
Rules are cited by id from [SKILL.md](../SKILL.md); each fact cites a row of the Provenance table.

## Check levels

| Level | Question | Instrument |
| --- | --- | --- |
| Schema | Do the catalogs and manifests parse and match their formats? | the validator; `claude plugin validate --strict` |
| Local | Do paths, sources, names, versions, and catalog parity follow the rules? | the validator |
| Remote | Do pinned sources exist and match their pins? | `git ls-remote`, a no-checkout fetch of the pinned `sha`, the npm registry |
| Catalog discovery | Does each tool list every entry it should? | each tool's add-and-list commands, isolated |
| Package load | Does each tool load the plugin's components? | each tool's install and inspection commands, isolated |

A network or authentication failure, or a host that refuses to fetch a commit by SHA, makes a remote check inconclusive, not failed and not passed [E1].

## The validator

- Run `check-marketplace <root>` (or `uv run <skill directory>/scripts/check_marketplace.py <root>`); `--format json` gives `statuses` per level and `findings`, each with `check`, `rule`, `severity`, `file`, `pointer`, and `message` [E2].
- It reads `marketplace-policy.json` for the declared readers; without one it infers readers only from each tool's own first-choice catalog and says so in a `policy.inferred` finding, so declare readers to check compatibility with every tool that reads a catalog (R1) [E2].
- It runs `claude plugin validate --strict --json` itself when `claude` is on `PATH`, with a throwaway `CLAUDE_CONFIG_DIR` created under `TMPDIR`; set `TMPDIR` to your throwaway directory when temporary files must stay inside it [E2].
- It never installs anything or runs plugin code; in this version its remote, discovery, and package-load levels report `skipped`, so those levels need the tool checks below or must be reported as not run (R12) [E2].
- Exit status is 0 with no error findings, 1 with error findings, and 2 when the validator itself failed [E2].

## Running a tool safely (R15)

Point every tool at throwaway state before its first command, including `--version`:

```bash
T="$PWD/.tool-homes"            # a throwaway directory; keep it out of commits
mkdir -p "$T"/{home,xdg,tmp,claude,codex,copilot,copilot-cache}
: > "$T/gitconfig"
export HOME="$T/home" XDG_CONFIG_HOME="$T/xdg" TMPDIR="$T/tmp" \
  GIT_CONFIG_GLOBAL="$T/gitconfig" GIT_CONFIG_NOSYSTEM=1 \
  CLAUDE_CONFIG_DIR="$T/claude" CODEX_HOME="$T/codex" \
  COPILOT_HOME="$T/copilot" COPILOT_CACHE_HOME="$T/copilot-cache"
```

- Export the variables in the same shell call that runs the tool; a failed `cd` or a new shell loses them [E3].
- Set `XDG_CONFIG_HOME` whenever you set `HOME`: git reads `$XDG_CONFIG_HOME/git/config`, so a git configuration write with only `HOME` changed lands in the real configuration [E3].
- `CODEX_HOME` must exist before Codex runs [E4].
- To make a tool fetch `github.com/owner/repo` from a local mirror, add `insteadOf` rules to the throwaway `GIT_CONFIG_GLOBAL`, never to the real one [E5]:

  ```ini
  [url "file:///absolute/path/to/mirrors/"]
  	insteadOf = https://github.com/owner/
  	insteadOf = git@github.com:owner/
  ```

- On macOS, deny outbound network traffic to a tool you only mean to run locally: `sandbox-exec -p '(version 1)(allow default)(deny network-outbound (remote ip))' <command>` [E5].
- Run tools with stdin from `/dev/null`, so none waits for input.
- Never send a prompt or open a session — `claude -p`, `codex exec`, `copilot -p`, an interactive session, or `copilot --acp` — to check a plugin: the throwaway variables do not isolate Copilot CLI's sign-in, and a session runs the plugin's code [E3] [E6].
- Avoid `sensitive` `userConfig` values in checks: Claude Code stores them in the system keychain, which `CLAUDE_CONFIG_DIR` does not isolate [E3].

## Catalog discovery

| Tool | Commands | What to compare |
| --- | --- | --- |
| Claude Code | `claude plugin validate <root> --strict --json`; `claude plugin marketplace add <root>` | errors and warnings; add succeeds |
| Codex | `codex plugin marketplace add <root>`; `codex plugin list --available --json` | every entry Codex should offer is listed; a missing one was skipped silently |
| Copilot CLI | `copilot plugin marketplace add <root>`; `copilot plugin marketplace browse <name> --json` | add succeeds, since one bad source rejects the whole catalog; every entry is listed |

The commands are from [E4], [E6], and [E7].
Check a clean export (`git archive HEAD | tar -x -C "$T/export"`) rather than a working tree, so untracked files and the throwaway directory are not read as part of the plugin [E4].

## Seeing what loaded

| Tool | Starts nothing | Starts plugin MCP servers (stand-in plugins only) |
| --- | --- | --- |
| Claude Code | `claude plugin details <plugin>@<marketplace>`: skills, agents, hooks, MCP and LSP servers; `claude plugin list --json`: version and MCP configuration | `claude mcp list` |
| Codex | `codex plugin add <plugin>@<marketplace> --json`: installed version; `codex mcp list --json`: MCP configuration | `codex debug prompt-input`: the skills Codex presents, including migrated commands |
| Copilot CLI | `copilot plugin install`: component count; `copilot plugin list`; `copilot skill list`; `copilot mcp list`; `copilot mcp get <server>` | none found |

The table is from [E6].
No command shows Codex's or Copilot CLI's view of a plugin's agents, or Copilot CLI's view of its hooks, so report those load checks as unproven rather than passed.
To see what a server receives at start, check a stand-in plugin you wrote whose server records its arguments, not the plugin under review (R15).

## Reporting (R12)

Report one line per level and tool, with its status and evidence, for example:

```text
Schema     passed        check-marketplace: schema.parse passed; claude plugin validate --strict: 0 errors
Local      failed        check-marketplace: local.version-mismatch for docs-kit (1.2.0 vs 1.1.0)
Remote     inconclusive  git fetch of fmt-kit@<sha>: network unavailable
Discovery  Codex         not run: codex is not installed here
Load       Copilot CLI   unproven: no command shows agents
```

A pipeline that passed tells you only which checks it ran; name the ones it did not run.

## Provenance

Verified against: claude 2.1.284, codex-cli 0.157.1, copilot 1.0.89 on 2026-09-28.
Conformance probes: none yet.

| Id | Evidence | Kind |
| --- | --- | --- |
| E1 | https://code.claude.com/docs/en/plugins/marketplace-reference, fetched 2026-09-27 (hosts that cannot fetch by SHA); `docs/research/2026-09-27-claude-code.md` §1 and `docs/research/README.md`, Known corrections | docs |
| E2 | the validator's source and tests: `skills/plugin-marketplaces/scripts/mpcheck/cli.py`, `run.py`, and `checks_schema.py`; `tests/test_cli.py` | source |
| E3 | plan-2b adjudications: a lost `export` after a failed `cd` (s4-r4), the real git configuration written with only `HOME` changed (preamble-v1 s1-r3), Copilot sessions reaching GitHub (s4-r7), keychain use (s4-r4, s4-r7, s4-r8, s4-r9); `tests/runs/2026-09-28-baseline-summary-2b.md` | run |
| E4 | Codex command-migration probe and source reading on codex-cli 0.157.1; `docs/research/2026-09-28-codex-command-migration-probe.md` and `docs/research/2026-09-27-codex.md` §3 and §5 | probe |
| E5 | probe P2, which used both; `docs/research/2026-09-28-load-and-update-probes.md` | probe |
| E6 | probe P1; `docs/research/2026-09-28-load-and-update-probes.md` | probe |
| E7 | phase-0 probes and probe P3 on Copilot CLI; `docs/research/2026-09-27-phase0-probes.md` and `docs/research/2026-09-28-load-and-update-probes.md` | probe |
PLAN2C_EOF
~~~~

~~~~bash
mkdir -p 'skills/plugin-marketplaces/references'
cat > 'skills/plugin-marketplaces/references/freshness.md' <<'PLAN2C_EOF'
# Freshness

The covered tools change weekly; this file says how the references record what they were checked against and what to do when a tool is newer (R13).
Rules are cited by id from [SKILL.md](../SKILL.md); each fact cites a row of the Provenance table.

## Provenance blocks

Every reference ends with a `## Provenance` section holding:

- a line `Verified against: <tool and version, …> on <date>.`, naming the versions its facts were observed or read against;
- a line naming the conformance probes that re-check its facts, or `none yet`;
- a table of evidence rows `| E<n> | <evidence> | <kind> |`, where kind is `docs` (read in published documentation), `source` (read in a tool's source at a named commit), `probe` (observed by running the tool), or `run` (observed in a recorded evaluation run).

Each fact in the reference cites one or more rows as `[E<n>]`, and a test in this skill's repository fails when a citation, a row, or a cited repository path is missing [E1].

## When a tool is newer than a reference (R13)

1. Read the tool's installed version with its version command, isolated as [validation.md](validation.md) describes (R15).
2. Compare it with the reference's `Verified against:` line.
3. If it is newer, list the facts your current decision depends on, and re-check each one against the evidence kind it cites: re-read the documentation page, re-read the source at the new release, or re-run the observation in a throwaway configuration.
4. Use what you observed, and say in the report which facts you re-checked, which changed, and which you relied on without re-checking.
5. If a fact changed, tell the maintainer of this skill; a validator disagreement is handled by R14.

## Refreshing a fact (for maintainers of this skill)

1. Re-verify the fact against its source before editing anything; re-pinning a hash or version without re-verification is the failure this procedure exists to prevent.
2. Record the new observation as a dated file under `docs/research/`, never by editing an old one.
3. Update the fact, its evidence row, and the reference's `Verified against:` line together; if the fact is a reader's source types or catalog paths, update `scripts/mpcheck/data/readers.json` in the same change.

## Provenance

Verified against: the repository's own tests on 2026-09-28.
Conformance probes: none yet.

| Id | Evidence | Kind |
| --- | --- | --- |
| E1 | `tests/test_skill_docs.py` | source |
PLAN2C_EOF
~~~~

- [ ] **Step 6: Run the test to see it pass**

Run: `uv run pytest -q tests/test_skill_docs.py`
Expected: `51 passed`.

- [ ] **Step 7: Show the test can fail on a missing citation and a restated rule**

~~~~bash
B=$(mktemp -t codexmd) && cp skills/plugin-marketplaces/references/codex.md "$B"
sed -i '' 's/ \[E15\]//' skills/plugin-marketplaces/references/codex.md
uv run pytest -q tests/test_skill_docs.py -k "codex" 2>&1 | tail -1
printf -- '- **R3** restated here\n' >> skills/plugin-marketplaces/references/codex.md
uv run pytest -q tests/test_skill_docs.py -k "never_define and codex" 2>&1 | tail -1
cp "$B" skills/plugin-marketplaces/references/codex.md && uv run pytest -q tests/test_skill_docs.py | tail -1
~~~~

Expected: `1 failed, 4 passed` (E15 uncited), then `1 failed` (a rule defined in a reference), then `51 passed`.

- [ ] **Step 8: Point the spec at SKILL.md for the extended rules**

~~~~bash
uv run python - <<'PLAN2C_EOF'
p = "docs/superpowers/specs/2026-09-27-plugin-marketplaces-design.md"
s = open(p, encoding="utf-8").read()
old = "Rule text lives only in SKILL.md; references cite rules by id and never restate them.\n"
new = old + "Plan 2c extended R12 (name every check that was not run) and R15 (no model session while validating); SKILL.md holds the current text (owner review of plan 2c).\n"
assert s.count(old) == 1
open(p, "w", encoding="utf-8").write(s.replace(old, new))
PLAN2C_EOF
~~~~

- [ ] **Step 9: Check and commit**

~~~~bash
uv run python tools/check_sentence_per_line.py skills/plugin-marketplaces/SKILL.md skills/plugin-marketplaces/references/*.md docs/superpowers/specs/2026-09-27-plugin-marketplaces-design.md
uv run python tools/check_skill_frontmatter.py skills/plugin-marketplaces/SKILL.md
uv run ruff format . && uv run ruff check --fix . && uv run pytest -q
git add tests/test_skill_docs.py skills/plugin-marketplaces/SKILL.md skills/plugin-marketplaces/references docs/superpowers/specs/2026-09-27-plugin-marketplaces-design.md
prek run --all-files
git commit -q -m "feat(skill): write SKILL.md and the references with provenance on every fact" -m "🤖 Generated with Claude Code"
~~~~

Expected: both checkers exit 0 silently; pytest reports no failures; prek passes.

### Task 4: The repository as its own marketplace

Spec §5 layout, with the §2 defaults: a portable root `plugin.json` plus a Claude adapter, and two native catalogs; `marketplace-policy.json` declares all three readers, because Copilot CLI reads `.claude-plugin/marketplace.json`.
The plugin's source is `./` (the repository root), so the plugin is also its own package; the whole repository (about 3 MB tracked) is copied into Codex's cache on install.

**Files:**
- Create: `plugin.json`, `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json`, `marketplace-policy.json`
- Create: `tests/test_dogfood.py`
- Modify: `README.md`

- [ ] **Step 1: Write the failing test**

~~~~bash
mkdir -p 'tests'
cat > 'tests/test_dogfood.py' <<'PLAN2C_EOF'
"""This repository is its own marketplace (spec §5): its catalogs must pass the validator."""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

from mpcheck.model import Severity
from mpcheck.run import run_checks

ROOT = Path(__file__).resolve().parents[1]


def test_the_repository_marketplace_has_no_error_findings():
    report = run_checks(ROOT, policy_path=None, use_claude=False)
    errors = [f for f in report.findings if f.severity == Severity.ERROR]
    assert errors == []
    assert report.statuses["local"][0] == "passed"
    assert report.statuses["policy"][0] == "passed"


def test_every_recorded_version_is_the_package_version():
    version = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"][
        "version"
    ]
    for manifest in ("plugin.json", ".claude-plugin/plugin.json"):
        assert json.loads((ROOT / manifest).read_text(encoding="utf-8"))["version"] == version
PLAN2C_EOF
~~~~

Run: `uv run pytest -q tests/test_dogfood.py`
Expected: FAIL (`plugin.json` not found, and the validator finds no catalog).

- [ ] **Step 2: Write the manifests, catalogs, and policy**

~~~~bash
cat > 'plugin.json' <<'PLAN2C_EOF'
{
  "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
  "name": "plugin-marketplaces",
  "version": "0.1.0",
  "description": "Create, audit, maintain, and release user-hosted plugin marketplaces for Claude Code, Codex, and GitHub Copilot CLI.",
  "author": {"name": "Brian Connelly"},
  "homepage": "https://github.com/briandconnelly/plugin-marketplaces",
  "repository": "https://github.com/briandconnelly/plugin-marketplaces",
  "license": "MIT",
  "keywords": ["plugins", "marketplace", "claude-code", "codex", "copilot-cli", "agent-plugins"]
}
PLAN2C_EOF
~~~~

~~~~bash
mkdir -p '.claude-plugin'
cat > '.claude-plugin/plugin.json' <<'PLAN2C_EOF'
{
  "name": "plugin-marketplaces",
  "version": "0.1.0",
  "description": "Create, audit, maintain, and release user-hosted plugin marketplaces for Claude Code, Codex, and GitHub Copilot CLI.",
  "author": {"name": "Brian Connelly"},
  "homepage": "https://github.com/briandconnelly/plugin-marketplaces",
  "repository": "https://github.com/briandconnelly/plugin-marketplaces",
  "license": "MIT",
  "keywords": ["plugins", "marketplace", "claude-code", "codex", "copilot-cli", "agent-plugins"]
}
PLAN2C_EOF
~~~~

~~~~bash
mkdir -p '.claude-plugin'
cat > '.claude-plugin/marketplace.json' <<'PLAN2C_EOF'
{
  "name": "plugin-marketplaces",
  "owner": {"name": "Brian Connelly"},
  "description": "The plugin-marketplaces skill, published from its own repository.",
  "plugins": [
    {
      "name": "plugin-marketplaces",
      "source": "./",
      "description": "Skill for user-hosted plugin marketplaces. It ships a Python validator that the agent runs on request; no hooks, MCP servers, LSP servers, or bin/, and no external services."
    }
  ]
}
PLAN2C_EOF
~~~~

~~~~bash
mkdir -p '.agents/plugins'
cat > '.agents/plugins/marketplace.json' <<'PLAN2C_EOF'
{
  "name": "plugin-marketplaces",
  "interface": {"displayName": "Plugin marketplaces"},
  "plugins": [
    {
      "name": "plugin-marketplaces",
      "source": {"source": "local", "path": "./"},
      "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
      "category": "Developer Tools",
      "description": "Skill for user-hosted plugin marketplaces. It ships a Python validator that the agent runs on request; no hooks, MCP servers, LSP servers, or bin/, and no external services."
    }
  ]
}
PLAN2C_EOF
~~~~

~~~~bash
cat > 'marketplace-policy.json' <<'PLAN2C_EOF'
{
  "readers": ["claude-code", "codex", "copilot-cli"],
  "exceptions": []
}
PLAN2C_EOF
~~~~

Run: `uv run pytest -q tests/test_dogfood.py`
Expected: `2 passed`.

- [ ] **Step 3: Show the test can fail**

~~~~bash
sed -i '' 's#"source": "./",#"source": "./nope",#' .claude-plugin/marketplace.json
uv run pytest -q tests/test_dogfood.py 2>&1 | tail -1
sed -i '' 's#"source": "./nope",#"source": "./",#' .claude-plugin/marketplace.json
sed -i '' 's/"version": "0.1.0"/"version": "0.1.1"/' .claude-plugin/plugin.json
uv run pytest -q tests/test_dogfood.py 2>&1 | tail -1
sed -i '' 's/"version": "0.1.1"/"version": "0.1.0"/' .claude-plugin/plugin.json
uv run pytest -q tests/test_dogfood.py 2>&1 | tail -1
~~~~

Expected: `1 failed, 1 passed` (`local.path-missing`), then `2 failed` (the version test and the validator's `local.version-mismatch`), then `2 passed`.

- [ ] **Step 4: Update the README**

~~~~bash
git apply <<'PLAN2C_EOF'
diff --git a/README.md b/README.md
index ac2ecc3..b691d33 100644
--- a/README.md
+++ b/README.md
@@ -4,7 +4,31 @@ An agent skill for creating, auditing, maintaining, and releasing user-hosted pl

 A user-hosted plugin marketplace is a catalog file that its maintainer writes and hosts, typically in a git repository; it is distinct from a vendor-hosted registry.

-Status: under construction; see `docs/superpowers/specs/` for the design.
+Status: the skill and its offline validator are written and being evaluated; see `docs/superpowers/specs/` for the design and `tests/runs/` for the evaluation records.
+
+## Install
+
+This repository is its own marketplace, with one plugin, `plugin-marketplaces`.
+
+```bash
+# Claude Code
+claude plugin marketplace add briandconnelly/plugin-marketplaces
+claude plugin install plugin-marketplaces@plugin-marketplaces
+
+# Codex
+codex plugin marketplace add briandconnelly/plugin-marketplaces
+codex plugin add plugin-marketplaces@plugin-marketplaces
+
+# GitHub Copilot CLI
+copilot plugin marketplace add briandconnelly/plugin-marketplaces
+copilot plugin install plugin-marketplaces@plugin-marketplaces
+```
+
+The validator also runs on its own, for example in another repository's CI:
+
+```bash
+uvx --from git+https://github.com/briandconnelly/plugin-marketplaces check-marketplace .
+```

 ## Development

PLAN2C_EOF
~~~~

- [ ] **Step 5: Commit**

~~~~bash
uv run python tools/check_sentence_per_line.py README.md
uv run ruff format . && uv run ruff check --fix . && uv run pytest -q
git add plugin.json .claude-plugin/plugin.json .claude-plugin/marketplace.json .agents/plugins/marketplace.json marketplace-policy.json tests/test_dogfood.py README.md
prek run --all-files
git commit -q -m "feat: publish the repository as its own marketplace for Claude Code, Codex, and Copilot CLI" -m "🤖 Generated with Claude Code"
~~~~

- [ ] **Step 6: Load-check the committed marketplace in all three tools**

From a clean export, isolated, with outbound IP traffic denied; no model session.

~~~~bash
P=$(mktemp -d -t plan2c-dogfood)
mkdir -p "$P"/{export,home,xdg,tmp,claude,codex,copilot,copilot-cache} && : > "$P/gitconfig"
git archive HEAD | tar -x -C "$P/export"
( export HOME=$P/home XDG_CONFIG_HOME=$P/xdg TMPDIR=$P/tmp GIT_CONFIG_GLOBAL=$P/gitconfig GIT_CONFIG_NOSYSTEM=1 \
    CLAUDE_CONFIG_DIR=$P/claude CODEX_HOME=$P/codex COPILOT_HOME=$P/copilot COPILOT_CACHE_HOME=$P/copilot-cache
  SB='(version 1)(allow default)(deny network-outbound (remote ip))'
  run() { echo "### $*"; sandbox-exec -p "$SB" perl -e 'alarm 90; exec @ARGV' "$@" < /dev/null 2>&1; }
  cd "$P"
  run claude plugin validate "$P/export" --strict
  run claude plugin marketplace add "$P/export"
  run claude plugin install plugin-marketplaces@plugin-marketplaces
  run claude plugin details plugin-marketplaces@plugin-marketplaces
  run codex plugin marketplace add "$P/export"
  run codex plugin list --available --json
  run codex plugin add plugin-marketplaces@plugin-marketplaces --json
  run copilot plugin marketplace add "$P/export"
  run copilot plugin install plugin-marketplaces@plugin-marketplaces
  run copilot plugin list ) | tee "$P/load.out"
~~~~

Expected, as observed from the scratch clone on 2026-09-28: `✔ Validation passed`; Claude Code `Skills (1)  plugin-marketplaces` at `0.1.0`; Codex lists `plugin-marketplaces` at `0.1.0` and installs it; Copilot CLI `Installed 1 skill.` and `plugin-marketplaces@plugin-marketplaces (v0.1.0) (enabled)`.
Record the result lines in the ledger; any difference is a finding to fix before Task 8.

### Task 5: With-skill arms in the evaluation

A with-skill run gets the committed skill at `RUNS/sN-rK/skill/plugin-marketplaces/` and its validator installed, byte-compiled, at `RUNS/sN-rK/validator/`; its prompt is the unchanged baseline prompt plus the two treatment lines in `tests/scenarios.md`.
The isolation checker learns the skill and validator paths, and flags `uv`/`uvx` calls that would write the real uv cache.

**Files:**
- Modify: `tests/eval/scenario_doc.py`, `tests/eval/prepare.py`, `tests/eval/isolation.py`, `tests/eval/collect.py`, `tests/scenarios.md`
- Test: `tests/test_eval_scenarios.py`, `tests/test_eval_prepare.py`, `tests/test_eval_isolation.py`

**Interfaces:**
- Produces: `scenario_doc.treatment(text) -> list[str]`; `scenario_doc.dispatch_prompt(text, number, workdir, upstream, skill=None, validator=None) -> str` (raises `ValueError` when `skill` is given without `validator`); `prepare.install_skill(run) -> (skill_dir, validator_exe, skill_tree)`, `prepare.skill_is_committed() -> bool`; manifest keys `skill`, `validator`, `skill_tree` on with-skill runs only; `isolation.Layout(..., skill=None, validator=None)`.

- [ ] **Step 1: Write the failing tests**

~~~~bash
git apply <<'PLAN2C_EOF'
diff --git a/tests/test_eval_isolation.py b/tests/test_eval_isolation.py
index 602132a..e0506ee 100644
--- a/tests/test_eval_isolation.py
+++ b/tests/test_eval_isolation.py
@@ -246,3 +246,33 @@ def test_terminal_wrappers_are_unwrapped():
     assert kinds(W + env + "script -q /dev/null copilot --acp") == ["cli-prompt"]
     assert kinds(W + env + "script -q $PWD/t.log copilot") == ["cli-prompt"]
     assert kinds(W + env + "unbuffer copilot plugin list") == []
+
+
+def test_a_with_skill_arm_may_read_its_skill_and_run_its_validator():
+    lay = Layout(
+        "/R/s1-r1/repo",
+        None,
+        "/R/s1-r1",
+        "/Users/owner",
+        "/start",
+        skill="/R/s1-r1/skill/plugin-marketplaces",
+        validator="/R/s1-r1/validator/bin/check-marketplace",
+    )
+    assert (
+        kinds("cd /R/s1-r1/skill/plugin-marketplaces && cat SKILL.md references/codex.md", lay)
+        == []
+    )
+    assert kinds("/R/s1-r1/validator/bin/check-marketplace /R/s1-r1/repo --format json", lay) == []
+    assert kinds("touch /R/s1-r1/skill/plugin-marketplaces/SKILL.md", lay) == ["outside-write"]
+    assert kinds("/R/s1-r1/validator/bin/other-script", lay) == ["sourced-unknown"]
+    # without a skill, the same cd is outside WORKDIR
+    assert kinds("cd /R/s1-r1/skill/plugin-marketplaces") == ["outside-read"]
+
+
+def test_uv_writes_its_cache_outside_workdir_unless_told_otherwise():
+    run = "uv run /R/s2-r1/skill/plugin-marketplaces/scripts/check_marketplace.py /R/s2-r1/repo"
+    assert kinds(run) == ["outside-write"]
+    assert kinds(f"UV_CACHE_DIR=/R/s2-r1/repo/.tool-homes/uv {run}") == []
+    assert kinds(f"export UV_CACHE_DIR=/R/s2-r1/repo/.tool-homes/uv && {run}") == []
+    assert kinds("cd /R/s2-r1/repo && uvx check-marketplace .") == ["outside-write"]
+    assert kinds("uv --version") == []
diff --git a/tests/test_eval_prepare.py b/tests/test_eval_prepare.py
index 588dd5f..59afca5 100644
--- a/tests/test_eval_prepare.py
+++ b/tests/test_eval_prepare.py
@@ -1,8 +1,9 @@
 import json
 import subprocess
+from pathlib import Path

 import pytest
-from prepare import main, prepare
+from prepare import ROOT, main, prepare
 from scenario_doc import DOC, scenario
 from score_prompt import score_prompt

@@ -44,3 +45,60 @@ def test_a_relative_runs_directory_becomes_absolute_in_the_prompt(tmp_path, monk
     assert main(["runs", "s2", "--reps", "1", "--arm", "baseline", "--session-context", "t"]) == 0
     prompt = (tmp_path / "runs" / "s2-r1" / "prompt.txt").read_text()
     assert f"`{tmp_path.resolve() / 'runs' / 's2-r1' / 'repo'}`" in prompt
+
+
+def test_a_with_skill_run_gets_the_committed_skill_and_an_installed_validator(tmp_path):
+    (run,) = prepare(tmp_path, "s2", 1, "with-skill", "test session", tools=TOOLS)
+    manifest = json.loads((run / "manifest.json").read_text())
+    skill, validator = Path(manifest["skill"]), Path(manifest["validator"])
+    assert skill == run / "skill" / "plugin-marketplaces"
+    assert validator == run / "validator" / "bin" / "check-marketplace"
+    committed = subprocess.run(
+        ["git", "-C", str(ROOT), "show", "HEAD:skills/plugin-marketplaces/SKILL.md"],
+        capture_output=True,
+        text=True,
+        check=True,
+    ).stdout
+    assert (skill / "SKILL.md").read_text() == committed
+    assert (
+        manifest["skill_tree"]
+        == subprocess.run(
+            ["git", "-C", str(ROOT), "rev-parse", "HEAD:skills/plugin-marketplaces"],
+            capture_output=True,
+            text=True,
+            check=True,
+        ).stdout.strip()
+    )
+    assert not list(skill.rglob("__pycache__"))
+    prompt = (run / "prompt.txt").read_text()
+    assert f"`{skill}/SKILL.md`" in prompt and f"`{validator}`" in prompt
+
+    def listing():
+        return sorted((str(p), p.stat().st_mtime_ns) for p in (run / "validator").rglob("*"))
+
+    before = listing()
+    done = subprocess.run(
+        [str(validator), str(run / "repo"), "--no-claude", "--format", "json"],
+        capture_output=True,
+        text=True,
+        check=False,
+    )
+    assert done.returncode in (0, 1) and json.loads(done.stdout)["statuses"]["local"]
+    # compiled at install, so running the validator writes nothing outside the arm's WORKDIR
+    assert listing() == before
+
+
+def test_a_baseline_run_has_no_skill(tmp_path):
+    (run,) = prepare(tmp_path, "s7", 1, "baseline", "test session", tools=TOOLS)
+    manifest = json.loads((run / "manifest.json").read_text())
+    assert "skill" not in manifest and not (run / "skill").exists()
+    assert "SKILL.md" not in (run / "prompt.txt").read_text()
+
+
+def test_a_with_skill_run_refuses_an_uncommitted_skill(tmp_path, monkeypatch):
+    import prepare as module
+
+    monkeypatch.setattr(module, "skill_is_committed", lambda: False)
+    with pytest.raises(SystemExit) as stop:
+        main([str(tmp_path), "s2", "--arm", "with-skill", "--session-context", "x"])
+    assert stop.value.code == 2 and not list(tmp_path.iterdir())
diff --git a/tests/test_eval_scenarios.py b/tests/test_eval_scenarios.py
index 52cd22c..b5c8ebf 100644
--- a/tests/test_eval_scenarios.py
+++ b/tests/test_eval_scenarios.py
@@ -1,5 +1,7 @@
+from pathlib import Path
+
 import pytest
-from scenario_doc import DOC, dispatch_prompt, preamble, scenario, scoring
+from scenario_doc import DOC, dispatch_prompt, preamble, scenario, scoring, treatment

 TEXT = DOC.read_text(encoding="utf-8")

@@ -42,3 +44,39 @@ def test_the_preamble_confines_temporary_files_and_xdg_config():
     text = " ".join(preamble(TEXT))
     assert "temporary file" in text and "`WORKDIR/.tool-homes/`" in text
     assert "XDG_CONFIG_HOME" in text
+
+
+def _recorded_prompt(number):
+    """The dispatch prompt of the first valid plan-2b baseline record for a scenario."""
+    runs = Path(__file__).resolve().parent / "runs"
+    path = sorted(runs.glob(f"2026-09-28-s{number}-r[0-9]*-baseline.md"))[0]
+    text = path.read_text(encoding="utf-8")
+    start = text.index("## Dispatch prompt\n\n```text\n") + len("## Dispatch prompt\n\n```text\n")
+    return text[start : text.index("\n```\n", start)]
+
+
+@pytest.mark.parametrize("number", range(1, 8))
+def test_baseline_prompts_are_what_the_baselines_received(number):
+    # a treatment arm is comparable only if the baseline text it extends is unchanged
+    upstream = Path("$RUN/weather-mcp") if scenario(TEXT, number).has_upstream else None
+    assert dispatch_prompt(TEXT, number, Path("$RUN/repo"), upstream) == _recorded_prompt(number)
+
+
+def test_a_treatment_prompt_is_the_baseline_plus_the_skill_lines(tmp_path):
+    work, up = tmp_path / "repo", tmp_path / "weather-mcp"
+    skill, validator = (
+        tmp_path / "skill" / "plugin-marketplaces",
+        tmp_path / "validator" / "bin" / "check-marketplace",
+    )
+    base = dispatch_prompt(TEXT, 1, work, up)
+    treated = dispatch_prompt(TEXT, 1, work, up, skill=skill, validator=validator)
+    lines = treatment(TEXT)
+    assert len(lines) == 2 and "SKILLDIR" in lines[0] and "VALIDATOR" in lines[1]
+    rendered = [
+        line.replace("SKILLDIR", str(skill)).replace("VALIDATOR", str(validator)) for line in lines
+    ]
+    assert treated == base.replace("\n\n", "\n" + "\n".join(rendered) + "\n\n", 1)
+    assert "SKILLDIR" not in treated and "VALIDATOR" not in treated
+    assert f"`{skill}/SKILL.md`" in treated
+    with pytest.raises(ValueError):
+        dispatch_prompt(TEXT, 1, work, up, skill=skill)
PLAN2C_EOF
~~~~

- [ ] **Step 2: Run them to see them fail**

Run: `uv run pytest -q tests/test_eval_scenarios.py tests/test_eval_prepare.py tests/test_eval_isolation.py`
Expected: a collection error, `cannot import name 'treatment' from 'scenario_doc'`.

- [ ] **Step 3: Implement**

~~~~bash
git apply <<'PLAN2C_EOF'
diff --git a/tests/eval/collect.py b/tests/eval/collect.py
index bd3ca47..19f9cdd 100644
--- a/tests/eval/collect.py
+++ b/tests/eval/collect.py
@@ -82,6 +82,8 @@ def collect(
         run_dir=str(run),
         home=str(Path.home()),
         start_cwd=t.start_cwd,
+        skill=manifest.get("skill"),
+        validator=manifest.get("validator"),
     )
     flags = check_calls(t.calls, layout) + symlink_flags(work, run)
     (art / "isolation-flags.txt").write_text("".join(f"{f}\n" for f in flags), encoding="utf-8")
diff --git a/tests/eval/isolation.py b/tests/eval/isolation.py
index efdf0a7..fdbc9fc 100644
--- a/tests/eval/isolation.py
+++ b/tests/eval/isolation.py
@@ -9,8 +9,10 @@ It follows `sh -c` strings, but cannot see inside Python or other interpreter sc
 and reads every call that mentions `claude`, `codex`, or `copilot`.

 Flag kinds:
-- `outside-read`: a path outside the arm's run directory (reads) or outside WORKDIR (cd).
-- `outside-write`: a path written outside WORKDIR, including UPSTREAM.
+- `outside-read`: a path outside the arm's run directory (reads), or a `cd` outside WORKDIR,
+  UPSTREAM, and a with-skill arm's skill copy.
+- `outside-write`: a path written outside WORKDIR, including UPSTREAM, or a `uv`/`uvx` call
+  whose `UV_CACHE_DIR` is not inside WORKDIR.
 - `cli-prompt`: a claude/codex/copilot invocation outside the allowlist, which may send a prompt.
 - `cli-session`: a bare `codex app-server`, allowed only if the JSON-RPC it was sent starts
   no turn; a person checks that.
@@ -153,6 +155,8 @@ class Layout:
     run_dir: str | None
     home: str
     start_cwd: str
+    skill: str | None = None  # a with-skill arm's read-only copy of the skill
+    validator: str | None = None  # the validator installed for a with-skill arm


 @dataclass
@@ -358,7 +362,10 @@ class Checker:
             target = self.resolve(args[1], shell) if len(args) > 1 else self.layout.home
             if target is None:
                 return
-            if not (_inside(target, self.layout.work) or _inside(target, self.layout.upstream)):
+            if not any(
+                _inside(target, root)
+                for root in (self.layout.work, self.layout.upstream, self.layout.skill)
+            ):
                 self.flag("outside-read", f"cd {target}")
             shell.cwd = target
             return
@@ -376,7 +383,9 @@ class Checker:
             self.follow(args[1:2], shell, _Shell(shell.cwd, dict(shell.env), set(shell.exported)))
         elif args[0].startswith(("/", "./", "$")) and not name.startswith("python"):
             path = self.resolve(args[0], shell)
-            if path is not None and path in self.files:
+            if path is not None and path == self.layout.validator:
+                pass  # the installed validator: known code that runs no model and no tool config
+            elif path is not None and path in self.files:
                 self.follow(
                     args[0:1], shell, _Shell(shell.cwd, dict(shell.env), set(shell.exported))
                 )
@@ -385,6 +394,14 @@ class Checker:
         if name in ("git", "curl", "wget") and any(REMOTE.match(a) for a in args[1:]):
             # step 5: a deliberate remote fetch is contact unless it is read-only documentation
             self.flag("remote-fetch", " ".join(args)[:120])
+        if name in ("uv", "uvx") and not HELP_WORDS & set(args[1:2]):
+            cache = inline.get("UV_CACHE_DIR") or (
+                shell.env.get("UV_CACHE_DIR") if "UV_CACHE_DIR" in shell.exported else None
+            )
+            target = self.resolve(cache, shell) if cache else None
+            if not (target and _inside(target, self.layout.work)):
+                # uv writes its cache (and may fetch packages) outside WORKDIR by default
+                self.flag("outside-write", f"{name} cache: {' '.join(args)[:100]}")
         if name in CLI_VARS:
             self.cli(name, args[1:], shell, inline)
         self.paths(name, args, shell)
diff --git a/tests/eval/prepare.py b/tests/eval/prepare.py
index 9dcaf91..a654122 100644
--- a/tests/eval/prepare.py
+++ b/tests/eval/prepare.py
@@ -1,7 +1,11 @@
 """Prepare scenario runs: RUNS/sN-rK/ with the fixture repository, mirror, prompt, and manifest.

-Usage: uv run python tests/eval/prepare.py RUNS sN --reps 3 --arm baseline
+Usage: uv run python tests/eval/prepare.py RUNS sN --reps 3 --arm baseline|with-skill
          --session-context "TEXT" [--first-rep 1]
+
+A with-skill run also gets the committed skill (never the working copy) at
+RUNS/sN-rK/skill/plugin-marketplaces/ and its validator installed, byte-compiled, into
+RUNS/sN-rK/validator/, so running it writes nothing outside the arm's WORKDIR.
 """

 from __future__ import annotations
@@ -9,11 +13,13 @@ from __future__ import annotations
 import argparse
 import datetime
 import importlib.util
+import io
 import json
 import os
 import shutil
 import subprocess
 import sys
+import tarfile
 import tempfile
 from pathlib import Path
 from types import ModuleType
@@ -22,6 +28,7 @@ from scenario_doc import DOC, ROOT, dispatch_prompt
 from scenario_doc import scenario as scenario_of

 SCENARIOS = ROOT / "tests" / "fixtures" / "scenarios"
+SKILL_PATH = "skills/plugin-marketplaces"
 # Git ignores the user's and the system's configuration here: no signing, no external diff
 # tool, no excludes, SHA-1 objects; only the fixture decides the tree id.
 GIT_ENV = {
@@ -51,6 +58,66 @@ def _load(path: Path) -> ModuleType:
     return module


+def _extract(tree: str, dest: Path) -> None:
+    """Write a tree-ish of this repository to `dest`, as committed."""
+    archive = subprocess.run(
+        ["git", "-C", str(ROOT), "archive", "--format=tar", tree],
+        check=True,
+        capture_output=True,
+    ).stdout
+    dest.mkdir(parents=True)
+    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
+        tar.extractall(dest, filter="data")
+
+
+def skill_tree() -> str:
+    return subprocess.run(
+        ["git", "-C", str(ROOT), "rev-parse", f"HEAD:{SKILL_PATH}"],
+        check=True,
+        capture_output=True,
+        text=True,
+    ).stdout.strip()
+
+
+def skill_is_committed() -> bool:
+    status = subprocess.run(
+        ["git", "-C", str(ROOT), "status", "--porcelain", "--", SKILL_PATH, "pyproject.toml"],
+        check=True,
+        capture_output=True,
+        text=True,
+    ).stdout
+    return status == ""
+
+
+def install_skill(run: Path) -> tuple[Path, Path, str]:
+    """Copy the committed skill into the run and install its validator beside it."""
+    tree = skill_tree()
+    skill = run / "skill" / "plugin-marketplaces"
+    _extract(tree, skill)
+    env = {
+        k: v for k, v in os.environ.items() if k not in ("VIRTUAL_ENV", "UV_PROJECT_ENVIRONMENT")
+    }
+    venv = run / "validator"
+    with tempfile.TemporaryDirectory(prefix="validator-src-") as src:
+        _extract("HEAD", Path(src) / "repo")
+        subprocess.run(["uv", "venv", "--quiet", str(venv)], env=env, check=True)
+        subprocess.run(
+            [
+                "uv",
+                "pip",
+                "install",
+                "--quiet",
+                "--compile-bytecode",
+                "--python",
+                str(venv / "bin" / "python"),
+                f"{src}/repo",
+            ],
+            env=env,
+            check=True,
+        )
+    return skill, venv / "bin" / "check-marketplace", tree
+
+
 def tool_versions() -> dict[str, str]:
     versions: dict[str, str] = {}
     with tempfile.TemporaryDirectory(prefix="versions-") as home:
@@ -108,7 +175,10 @@ def prepare(
         if scenario_of(doc, number).has_upstream:
             upstream = run / "weather-mcp"
             commits = _load(SCENARIOS / "make_upstream.py").build(upstream)
-        prompt = dispatch_prompt(doc, number, work, upstream)
+        skill = validator = tree_of_skill = None
+        if arm == "with-skill":
+            skill, validator, tree_of_skill = install_skill(run)
+        prompt = dispatch_prompt(doc, number, work, upstream, skill=skill, validator=validator)
         (run / "prompt.txt").write_text(prompt, encoding="utf-8")
         manifest = {
             "date": datetime.date.today().isoformat(),
@@ -121,6 +191,8 @@ def prepare(
             "session_context": session_context,
             "prompt_file": "prompt.txt",
         }
+        if skill is not None:
+            manifest.update(skill=str(skill), validator=str(validator), skill_tree=tree_of_skill)
         (run / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
         made.append(run)
     return made
@@ -135,6 +207,10 @@ def main(argv: list[str] | None = None) -> int:
     parser.add_argument("--arm", choices=("baseline", "with-skill"), required=True)
     parser.add_argument("--session-context", required=True)
     args = parser.parse_args(argv)
+    if args.arm == "with-skill" and not skill_is_committed():
+        parser.error(
+            f"commit {SKILL_PATH} and pyproject.toml first: a run uses the committed skill"
+        )
     for run in prepare(
         args.runs.resolve(),
         args.scenario,
diff --git a/tests/eval/scenario_doc.py b/tests/eval/scenario_doc.py
index 03d549f..1e7fddb 100644
--- a/tests/eval/scenario_doc.py
+++ b/tests/eval/scenario_doc.py
@@ -40,6 +40,11 @@ def preamble(text: str) -> list[str]:
     return _quote(_section(text, "### Arm preamble"))


+def treatment(text: str) -> list[str]:
+    """The lines a with-skill arm's prompt adds after the preamble."""
+    return _quote(_section(text, "### Treatment lines"))
+
+
 def scoring(text: str) -> str:
     return _section(text, "## Scoring (every scenario)").strip()

@@ -53,9 +58,24 @@ def scenario(text: str, number: int) -> Scenario:
     return Scenario(number, "\n".join(_quote(prompt)), criteria.strip())


-def dispatch_prompt(text: str, number: int, workdir: Path, upstream: Path | None) -> str:
+def dispatch_prompt(
+    text: str,
+    number: int,
+    workdir: Path,
+    upstream: Path | None,
+    skill: Path | None = None,
+    validator: Path | None = None,
+) -> str:
     item = scenario(text, number)
     lines = [line for line in preamble(text) if item.has_upstream or "UPSTREAM" not in line]
+    if skill is not None:
+        if validator is None:
+            raise ValueError("a with-skill prompt needs the installed validator's path")
+        rendered = [
+            line.replace("SKILLDIR", str(skill)).replace("VALIDATOR", str(validator))
+            for line in treatment(text)
+        ]
+        lines += rendered
     prompt = "\n".join(lines) + "\n\n" + item.prompt
     prompt = prompt.replace("WORKDIR", str(workdir))
     if upstream is not None:
diff --git a/tests/scenarios.md b/tests/scenarios.md
index 084baff..dc89a4d 100644
--- a/tests/scenarios.md
+++ b/tests/scenarios.md
@@ -55,6 +55,13 @@ Every step below is a script under `tests/eval/`; run them from this repository'
 `prepare.py` drops the line naming `UPSTREAM` for scenarios whose prompt does not mention it.
 The two lines about temporary files and `XDG_CONFIG_HOME` were added on 2026-09-28, after the first plan-2b batches, because arms wrote scratch files into the dispatching session's scratch directory (which Claude Code names to every subagent) and one wrote the real `~/.config/git/config`; runs made before them are kept under `tests/runs/superseded-preamble-1/`.

+### Treatment lines
+
+A with-skill arm's prompt is the baseline prompt with these lines added after the preamble; `prepare.py --arm with-skill` copies the committed skill to `RUNS/sN-rK/skill/plugin-marketplaces/` (SKILLDIR) and installs its validator into `RUNS/sN-rK/validator/` (VALIDATOR is its `bin/check-marketplace`).
+
+> A skill for this task is at `SKILLDIR`: read `SKILLDIR/SKILL.md` before you start, and follow it; you may read anything under `SKILLDIR`, but do not change it.
+> The skill's validator is already installed as `VALIDATOR`; run that instead of the `uv run` command the skill gives.
+
 ## Scoring (every scenario)

 - Each criterion is pass or fail with one line of evidence pointing at the diff, the objective-check output, or the final report.
PLAN2C_EOF
~~~~

- [ ] **Step 4: Run the tests to see them pass**

Run: `uv run pytest -q tests/test_eval_scenarios.py tests/test_eval_prepare.py tests/test_eval_isolation.py`
Expected: all pass, including the seven `test_baseline_prompts_are_what_the_baselines_received` cases and the plan-2a calibration table unchanged.

- [ ] **Step 5: Exercise the CLI**

~~~~bash
X=$(mktemp -d -t plan2c-prep)
uv run python tests/eval/prepare.py "$X/runs" s6 --reps 1 --arm with-skill --session-context "dry run"
tail -4 "$X/runs/s6-r1/prompt.txt"; "$X/runs/s6-r1/validator/bin/check-marketplace" "$X/runs/s6-r1/repo" --no-claude | head -3
~~~~

Expected: the prompt's last lines are the two treatment lines, then the scenario 6 prompt; the validator prints `Check levels:`.
The skill is committed by Task 3, so `prepare.py` does not refuse.

- [ ] **Step 6: Commit**

~~~~bash
uv run ruff format . && uv run ruff check --fix . && uv run pytest -q
git add tests/eval tests/scenarios.md tests/test_eval_scenarios.py tests/test_eval_prepare.py tests/test_eval_isolation.py
prek run --all-files
git commit -q -m "feat(eval): add with-skill arms that copy the committed skill and install its validator" -m "🤖 Generated with Claude Code"
~~~~

### Task 6: Trigger-case runner

Each trigger prompt lists this skill's frontmatter description beside seven installed skills nearest in scope, copied verbatim, in an order fixed per repetition, and asks which skill, if any, to load; a fresh subagent answers without tools.

**Files:**
- Create: `tests/eval/trigger.py`, `tests/fixtures/trigger/distractors.json`
- Modify: `tests/trigger_cases.md`
- Test: `tests/test_eval_trigger.py`

**Interfaces:**
- Consumes: `transcript.find(tasks, prompt)`, `transcript.load(path)` (plan 2b).
- Produces: `trigger.cases(text) -> list[Case]` (`p1`–`p6`, `n1`–`n5`), `trigger.catalog(rep)`, `trigger.render(case, entries)`, `trigger.prepare(out, reps)`, `trigger.verdict(reply) -> str`, `trigger.record(out, tasks, dest)`.

- [ ] **Step 1: Write the failing test**

~~~~bash
mkdir -p 'tests'
cat > 'tests/test_eval_trigger.py' <<'PLAN2C_EOF'
import json

import pytest
from trigger import CASES, SKILL_NAME, cases, catalog, description, prepare, record, render, verdict


def test_the_cases_come_from_the_trigger_file():
    found = cases(CASES.read_text(encoding="utf-8"))
    assert [c.id for c in found] == [f"p{n}" for n in range(1, 7)] + [f"n{n}" for n in range(1, 6)]
    assert all(c.expected == SKILL_NAME for c in found if c.id.startswith("p"))
    assert all(c.expected == "none" for c in found if c.id.startswith("n"))
    assert found[0].prompt == "Set up a plugin marketplace for our team's Claude Code plugins."


def test_the_catalog_offers_every_skill_once_in_a_per_repetition_order():
    first, second = catalog(1), catalog(2)
    names = [name for name, _ in first]
    assert sorted(names) == sorted(name for name, _ in second)
    assert names.count(SKILL_NAME) == 1 and len(names) == len(set(names)) == 8
    assert names != [name for name, _ in second]
    assert catalog(1) == first  # deterministic
    assert dict(first)[SKILL_NAME] == description()


def test_prepare_writes_one_prompt_per_case_and_repetition(tmp_path):
    runs = prepare(tmp_path, reps=3)
    assert len(runs) == 33
    one = tmp_path / "p1-r1"
    prompt = (one / "prompt.txt").read_text()
    assert prompt == render(cases(CASES.read_text(encoding="utf-8"))[0], catalog(1))
    assert "> Set up a plugin marketplace" in prompt and "Do not use any tools." in prompt
    assert json.loads((one / "case.json").read_text())["expected"] == SKILL_NAME
    with pytest.raises(FileExistsError):
        prepare(tmp_path, reps=1)


@pytest.mark.parametrize(
    ("reply", "chosen"),
    [
        ("plugin-marketplaces\nIt is about catalogs.", "plugin-marketplaces"),
        ("`plugin-marketplaces` — it fits.", "plugin-marketplaces"),
        ("**none**\nNo skill fits.", "none"),
        ("None.", "none"),
        ("plugin-dev:plugin-structure\nScaffolding.", "plugin-dev:plugin-structure"),
        ("\n\nfastmcp", "fastmcp"),
    ],
)
def test_verdict_reads_the_first_line(reply, chosen):
    assert verdict(reply) == chosen


def _transcript(path, prompt, reply):
    records = [
        {
            "type": "user",
            "timestamp": "2026-09-29T10:00:00Z",
            "cwd": "/s",
            "message": {"role": "user", "content": prompt},
        },
        {
            "type": "assistant",
            "timestamp": "2026-09-29T10:00:03Z",
            "message": {
                "id": "m",
                "model": "claude-opus-5-5",
                "content": [{"type": "text", "text": reply}],
            },
        },
    ]
    path.write_text("".join(json.dumps(r) + "\n" for r in records), encoding="utf-8")


def test_record_scores_every_reply(tmp_path):
    out, tasks = tmp_path / "out", tmp_path / "tasks"
    tasks.mkdir()
    for i, run in enumerate(prepare(out, reps=1)):
        wrong = run.name == "n1-r1" or run.name == "p2-r1"
        reply = (
            ("fastmcp\nNo." if run.name.startswith("p") else "plugin-marketplaces\nYes.")
            if wrong
            else (
                "plugin-marketplaces\nFits." if run.name.startswith("p") else "none\nNothing fits."
            )
        )
        _transcript(tasks / f"a{i}.output", (run / "prompt.txt").read_text(), reply)
    doc = record(out, tasks, tmp_path / "trigger.md").read_text()
    assert "Positive: 5 of 6 passed." in doc and "Negative: 4 of 5 passed." in doc
    assert "| p2 | 1 | plugin-marketplaces | fastmcp | FAIL |" in doc
    assert "| n1 | 1 | none | plugin-marketplaces | FAIL |" in doc
    assert "claude-opus-5-5" in doc
PLAN2C_EOF
~~~~

Run: `uv run pytest -q tests/test_eval_trigger.py`
Expected: a collection error, `No module named 'trigger'`.

- [ ] **Step 2: Implement**

~~~~bash
mkdir -p 'tests/fixtures/trigger'
cat > 'tests/fixtures/trigger/distractors.json' <<'PLAN2C_EOF'
{
  "$comment": "Skill descriptions offered beside plugin-marketplaces in trigger runs, copied verbatim on 2026-09-28 from the skills installed in the dispatching Claude Code session (claude 2.1.284); chosen as the installed skills nearest in scope.",
  "skills": [
    {
      "name": "plugin-dev:plugin-structure",
      "description": "This skill should be used when the user asks to \"create a plugin\", \"scaffold a plugin\", \"understand plugin structure\", \"organize plugin components\", \"set up plugin.json\", \"use ${CLAUDE_PLUGIN_ROOT}\", \"add commands/agents/skills/hooks\", \"configure auto-discovery\", or needs guidance on plugin directory layout, manifest configuration, component organization, file naming conventions, or Claude Code plugin architecture best practices."
    },
    {
      "name": "plugin-dev:skill-development",
      "description": "This skill should be used when the user wants to \"create a skill\", \"add a skill to plugin\", \"write a new skill\", \"improve skill description\", \"organize skill content\", or needs guidance on skill structure, progressive disclosure, or skill development best practices for Claude Code plugins."
    },
    {
      "name": "plugin-dev:hook-development",
      "description": "This skill should be used when the user asks to \"create a hook\", \"add a PreToolUse/PostToolUse/Stop hook\", \"validate tool use\", \"implement prompt-based hooks\", \"use ${CLAUDE_PLUGIN_ROOT}\", \"set up event-driven automation\", \"block dangerous commands\", or mentions hook events (PreToolUse, PostToolUse, Stop, SubagentStop, SessionStart, SessionEnd, UserPromptSubmit, PreCompact, Notification). Provides comprehensive guidance for creating and implementing Claude Code plugin hooks with focus on advanced prompt-based hooks API."
    },
    {
      "name": "plugin-dev:mcp-integration",
      "description": "This skill should be used when the user asks to \"add MCP server\", \"integrate MCP\", \"configure MCP in plugin\", \"use .mcp.json\", \"set up Model Context Protocol\", \"connect external service\", mentions \"${CLAUDE_PLUGIN_ROOT} with MCP\", or discusses MCP server types (SSE, stdio, HTTP, WebSocket). Provides comprehensive guidance for integrating Model Context Protocol servers into Claude Code plugins for external tool and service integration."
    },
    {
      "name": "mcp-server-dev:build-mcp-server",
      "description": "This skill should be used when the user asks to \"build an MCP server\", \"create an MCP\", \"make an MCP integration\", \"wrap an API for Claude\", \"expose tools to Claude\", \"make an MCP app\", or discusses building something with the Model Context Protocol. It is the entry point for MCP server development — it interrogates the user about their use case, determines the right deployment model (remote HTTP, MCPB, local stdio), picks a tool-design pattern, and hands off to specialized skills."
    },
    {
      "name": "skill-creator:skill-creator",
      "description": "Create new skills, modify and improve existing skills, and measure skill performance. Use when users want to create a skill from scratch, edit, or optimize an existing skill, run evals to test a skill, benchmark skill performance with variance analysis, or optimize a skill's description for better triggering accuracy."
    },
    {
      "name": "fastmcp",
      "description": "Use when working with FastMCP to build MCP servers, tools, resources, or prompts in Python. Triggers on: FastMCP imports or questions, building or debugging MCP servers with FastMCP, FastMCP tools/resources/prompts/context, FastMCP app UI components, MCP server deployment with FastMCP, FastMCP authentication or transports, FastMCP migrations or upgrades, Model Context Protocol servers built with FastMCP."
    }
  ]
}
PLAN2C_EOF
~~~~

~~~~bash
mkdir -p 'tests/eval'
cat > 'tests/eval/trigger.py' <<'PLAN2C_EOF'
"""Trigger-case runs: from a list of skill descriptions, does a fresh agent pick this skill?

Usage:
  uv run python tests/eval/trigger.py prepare OUT [--reps 3]
  uv run python tests/eval/trigger.py record OUT TASKS tests/runs/DATE-trigger.md

`prepare` writes OUT/<case>-r<k>/prompt.txt for every case in tests/trigger_cases.md; each
prompt lists this skill's frontmatter description beside the distractors in
tests/fixtures/trigger/distractors.json, in an order fixed per repetition. Dispatch each
prompt, exactly, to a fresh subagent. `record` finds each reply by its prompt and writes the
results table.
"""

from __future__ import annotations

import argparse
import datetime
import json
import random
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml
from scenario_doc import ROOT
from transcript import find, load

CASES = ROOT / "tests" / "trigger_cases.md"
DISTRACTORS = ROOT / "tests" / "fixtures" / "trigger" / "distractors.json"
SKILL = ROOT / "skills" / "plugin-marketplaces" / "SKILL.md"
SKILL_NAME = "plugin-marketplaces"
ROW = re.compile(r'^\| "(.+)" \| .+ \|$')


@dataclass(frozen=True)
class Case:
    id: str
    prompt: str
    expected: str  # SKILL_NAME, or "none" for a case that must not load it


def cases(text: str) -> list[Case]:
    found: list[Case] = []
    for heading, prefix, expected in (
        ("## Positive cases", "p", SKILL_NAME),
        ("## Negative cases", "n", "none"),
    ):
        start = text.index(heading)
        end = text.find("\n## ", start + 1)
        block = text[start : end if end != -1 else len(text)]
        prompts = [m.group(1) for m in map(ROW.match, block.splitlines()) if m]
        found += [Case(f"{prefix}{i}", p, expected) for i, p in enumerate(prompts, start=1)]
    return found


def description() -> str:
    front = SKILL.read_text(encoding="utf-8").split("---\n")[1]
    return " ".join(yaml.safe_load(front)["description"].split())


def catalog(rep: int) -> list[tuple[str, str]]:
    skills = json.loads(DISTRACTORS.read_text(encoding="utf-8"))["skills"]
    entries = [(s["name"], s["description"]) for s in skills] + [(SKILL_NAME, description())]
    random.Random(rep).shuffle(entries)
    return entries


def render(case: Case, entries: list[tuple[str, str]]) -> str:
    listing = "\n".join(f"- `{name}`: {text}" for name, text in entries)
    return (
        f"Available skills:\n\n{listing}\n\n"
        f"A user sends this request:\n\n> {case.prompt}\n\n"
        "Which one skill from the list above, if any, should be loaded before answering it? "
        "Do not use any tools. "
        "Reply with the skill's name, or `none`, alone on the first line, then one sentence "
        "explaining the choice."
    )


def prepare(out: Path, reps: int = 3) -> list[Path]:
    made = []
    for case in cases(CASES.read_text(encoding="utf-8")):
        for rep in range(1, reps + 1):
            run = out / f"{case.id}-r{rep}"
            run.mkdir(parents=True)  # never reuse a run directory
            (run / "prompt.txt").write_text(render(case, catalog(rep)), encoding="utf-8")
            (run / "case.json").write_text(
                json.dumps(
                    {"id": case.id, "rep": rep, "prompt": case.prompt, "expected": case.expected}
                )
                + "\n",
                encoding="utf-8",
            )
            made.append(run)
    return made


def verdict(reply: str) -> str:
    first = next((line for line in reply.splitlines() if line.strip()), "")
    word = re.split(r"\s+[—–-]\s+|\s", first.strip())[0]
    return word.strip("`*_.,:;\"'").lower()


def passed(expected: str, chosen: str) -> bool:
    return chosen == SKILL_NAME if expected == SKILL_NAME else chosen != SKILL_NAME


def record(out: Path, tasks: Path, dest: Path) -> Path:
    rows = [
        "| Case | Rep | Expected | Chosen | Result | Reply |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    totals = {"p": [0, 0], "n": [0, 0]}
    models: set[str] = set()
    for run in sorted(out.glob("*-r*"), key=lambda p: (p.name[0] != "p", p.name)):
        case = json.loads((run / "case.json").read_text(encoding="utf-8"))
        t = load(find(tasks, (run / "prompt.txt").read_text(encoding="utf-8")))
        models.update(t.models)
        chosen = verdict(t.report)
        ok = passed(case["expected"], chosen)
        totals[case["id"][0]][0] += ok
        totals[case["id"][0]][1] += 1
        reply = " ".join(t.report.split()).replace("|", "\\|")
        rows.append(
            f"| {case['id']} | {case['rep']} | {case['expected']} | {chosen} | {'pass' if ok else 'FAIL'} | {reply} |"
        )
    doc = f"""# Trigger runs

Date: {datetime.date.today().isoformat()}.
Cases: `tests/trigger_cases.md`; distractors: `tests/fixtures/trigger/distractors.json`; description: `skills/plugin-marketplaces/SKILL.md` frontmatter at this commit.
Each prompt was dispatched, exactly as `tests/eval/trigger.py prepare` wrote it, to a fresh subagent (model: {", ".join(sorted(models))}).
A positive case passes when the reply chooses `{SKILL_NAME}`; a negative case passes when it does not.

Positive: {totals["p"][0]} of {totals["p"][1]} passed.
Negative: {totals["n"][0]} of {totals["n"][1]} passed.

{chr(10).join(rows)}
"""
    dest.write_text(doc, encoding="utf-8")
    return dest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Trigger-case runs.")
    sub = parser.add_subparsers(dest="command", required=True)
    prep = sub.add_parser("prepare")
    prep.add_argument("out", type=Path)
    prep.add_argument("--reps", type=int, default=3)
    rec = sub.add_parser("record")
    rec.add_argument("out", type=Path)
    rec.add_argument("tasks", type=Path)
    rec.add_argument("dest", type=Path)
    args = parser.parse_args(argv)
    if args.command == "prepare":
        for run in prepare(args.out.resolve(), args.reps):
            print(run)
    else:
        print(record(args.out.resolve(), args.tasks.resolve(), args.dest))
    return 0


if __name__ == "__main__":
    sys.exit(main())
PLAN2C_EOF
~~~~

~~~~bash
git apply <<'PLAN2C_EOF'
diff --git a/tests/trigger_cases.md b/tests/trigger_cases.md
index 726c33b..16dd2c6 100644
--- a/tests/trigger_cases.md
+++ b/tests/trigger_cases.md
@@ -1,7 +1,9 @@
 # Trigger Cases for plugin-marketplaces

-Prompts that must, and must not, load the skill, checked against SKILL.md's frontmatter `description` once plan 2b writes it.
-Run each prompt against the skill catalog without naming the skill; store the result in `tests/runs/YYYY-MM-DD-trigger.md`.
+Prompts that must, and must not, load the skill, checked against SKILL.md's frontmatter `description`.
+`uv run python tests/eval/trigger.py prepare OUT` writes one prompt per case and repetition, listing the description beside the distractors in `tests/fixtures/trigger/distractors.json` without saying which skill is under test; dispatch each prompt, exactly, to a fresh subagent, then `uv run python tests/eval/trigger.py record OUT TASKS tests/runs/YYYY-MM-DD-trigger.md` scores the replies.
+A positive case passes when the reply chooses `plugin-marketplaces`, and a negative case passes when it does not.
+The table rows are parsed by `tests/eval/trigger.py`: keep each prompt in double quotes in the first column.

 ## Positive cases (must trigger)

PLAN2C_EOF
~~~~

- [ ] **Step 3: Run the test to see it pass, and commit**

~~~~bash
uv run pytest -q tests/test_eval_trigger.py
uv run ruff format . && uv run ruff check --fix . && uv run pytest -q
git add tests/eval/trigger.py tests/fixtures/trigger/distractors.json tests/trigger_cases.md tests/test_eval_trigger.py
prek run --all-files
git commit -q -m "feat(eval): add a trigger-case runner with pinned distractor descriptions" -m "🤖 Generated with Claude Code"
~~~~

Expected: `10 passed`, then the whole suite passes.

### Task 7: Adopt the owner's rulings

Do not start until the owner has answered D1 to D4; record each answer, with its date, in the ledger.

**Files:**
- Modify: `tests/scenarios.md` (How to run, step 5)

- [ ] **Step 1: Add the adopted rulings to step 5**

For each of D1 and D2 the owner approved, add one line after the paragraph that begins "Adopted 2026-09-28, before any treatment run, after no s4 baseline arm set it", using the date from the ledger:

~~~~text
Adopted <ledger date>, before any treatment run (D2): a with-skill arm may read and `cd` into SKILLDIR and run VALIDATOR; writing under SKILLDIR or the validator's directory is still a write violation.
Adopted <ledger date>, before any treatment run (D1): when the arm has not set `TMPDIR`, the throwaway Claude Code configuration directory that VALIDATOR creates and removes under the system temporary directory is the validator's own, not a write violation.
~~~~

If the owner rejects D1, the scorer's adjudicator discards any arm whose validator ran without `TMPDIR` inside WORKDIR; if the owner rejects D2, revert the checker's `skill` allowance with a test first.

- [ ] **Step 2: Check and commit**

~~~~bash
uv run python tools/check_sentence_per_line.py tests/scenarios.md && uv run pytest -q tests/test_eval_scenarios.py
git add tests/scenarios.md
git commit -q -m "docs(eval): adopt the with-skill isolation rulings before any treatment run" -m "🤖 Generated with Claude Code"
~~~~

Expected: the baseline-prompt tests still pass, because step 5 is not part of any prompt.

### Task 8: With-skill runs

Follow `tests/scenarios.md`, How to run, exactly as plan 2b's Task 9 did, with `--arm with-skill`; every step is a script, and nothing is retyped.

**Files:**
- Create: `tests/runs/<date>-sN-rK-with-skill.md` (one per run, via `assemble.py`)
- Modify: `handoff/plan-2c-ledger.md`

- [ ] **Step 1: Prepare the batches**

`RUNS` is a fresh directory outside this repository whose name does not say which arm it holds; the session context names the plugins and skills present in the dispatching session, as in plan 2b.

~~~~bash
RUNS=$(mktemp -d -t runs); echo "RUNS=$RUNS" >> handoff/plan-2c-ledger.md
CTX="dispatched from a Claude Code session (claude $(claude --version | cut -d' ' -f1)) with installed plugins $(ls ~/.claude/plugins/cache | paste -sd, -); the plugin-marketplaces skill reaches arms only through the run's skill copy"
for s in s1 s2 s3 s5 s6 s7; do uv run python tests/eval/prepare.py "$RUNS" $s --reps 3 --arm with-skill --session-context "$CTX"; done
uv run python tests/eval/prepare.py "$RUNS" s4 --reps 5 --arm with-skill --session-context "$CTX"
~~~~

`claude --version` here reads only the version (exempt); read `$CTX` before running and add the user skills directory's contents (`ls ~/.claude/skills`) the way plan 2b's manifests list them.

- [ ] **Step 2: Run each batch**

For each batch of up to five runs: snapshot the homes (step 2), dispatch each arm with the exact content of its `prompt.txt` and nothing else (step 3), snapshot again and compare, collect (step 4), adjudicate every tool call (step 5), scan secrets (step 6), dispatch the scorer (step 7), and record (step 8).
Replace a discarded run with a new repetition (`--first-rep`), except in s4, whose discards are its outcome: record them, and do not replace them.

- [ ] **Step 3: Record the batch results in the ledger**

One line per run: id, status, score, tool calls, wall time, and any ruling made, gated on `assemble.py`'s exit status.

### Task 9: Trigger runs

- [ ] **Step 1: Prepare and dispatch**

~~~~bash
TRIG=$(mktemp -d -t trig); echo "TRIG=$TRIG" >> handoff/plan-2c-ledger.md
uv run python tests/eval/trigger.py prepare "$TRIG/out" --reps 3
~~~~

Dispatch each of the 33 prompts, exactly, to a fresh subagent with no other text; the prompt tells it not to use tools.

- [ ] **Step 2: Record**

~~~~bash
uv run python tests/eval/trigger.py record "$TRIG/out" "$TASKS" tests/runs/$(date +%F)-trigger.md
~~~~

`TASKS` is the session's task directory, as in plan 2b.
Expected: a table of 33 rows and the positive and negative totals.

### Task 10: One refinement round, if the runs call for it

The baseline summary's Outcomes rule decides what counts: in s1, s3, and s7 (saturated baselines) any failed criterion is a regression; in s2, s5, and s6 the target criteria are s2 criteria 4 and 5, s5 criterion 6, and s6 criterion 8; in s4 the outcome is the isolation rate.

- [ ] **Step 1: Decide**

A refinement round is owed when a scenario regresses in two or more of its runs, when a target criterion still fails in two or more runs, when s4's isolation rate is below 3 of 5, or when any trigger case fails in two or more of its three repetitions.
Write the decision and the evidence for it in the ledger; if none holds, skip to Task 11.

- [ ] **Step 2: Fix, then re-run only what the fix touches**

Change SKILL.md or a reference, test-first where a test applies, and commit; then re-run the affected scenarios, three repetitions each (five for s4), or all 33 trigger prompts after a description change, with new repetition numbers.
One round only: if the re-run still meets a condition in Step 1, stop and report to the owner.

### Task 11: Summary, replay check, review, and PR

- [ ] **Step 1: Write the with-skill summary**

~~~~bash
uv run python tests/eval/summarize.py tests/runs/*-s?-r[0-9]*-with-skill*.md
~~~~

Write `tests/runs/<date>-with-skill-summary.md` in the shape of `tests/runs/2026-09-28-baseline-summary-2b.md`: the generated tables; per scenario, the comparison the Outcomes section prescribes (criteria for s2, s5, s6; cost for s1, s3, s7; isolation rate for s4, with any score difference descriptive only); the trigger totals; each run's `skill_tree`; every ruling; and what remains for plans 3 and 4.

- [ ] **Step 2: Check the plan replays**

In a fresh clone of `main` at `446ce07`, apply every file-writing block of Tasks 2 to 6 in order, then compare the tree with the branch's Task 6 commit:

~~~~bash
git -c diff.external= diff --no-ext-diff --stat <task-6-commit> -- . ':!handoff'
~~~~

Expected: no differences.

- [ ] **Step 3: Final review**

Dispatch one fresh reviewer on the most capable model with the branch diff, the spec, the baseline summary, and this plan; apply what it finds test-first, recording each finding and its resolution in the ledger.

- [ ] **Step 4: Push and open the PR**

Push `feat/plan-2c` and open a PR whose body summarizes the probes, the skill, the dogfood check, the with-skill and trigger results, and the rulings, ending with the session's attribution line; then run the Copilot review loop as in plan 2b (the owner requests each round; re-query the reviews directly whatever a poll reports).
