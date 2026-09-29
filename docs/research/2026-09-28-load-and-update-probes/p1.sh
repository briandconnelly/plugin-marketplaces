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
