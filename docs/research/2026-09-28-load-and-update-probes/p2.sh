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
