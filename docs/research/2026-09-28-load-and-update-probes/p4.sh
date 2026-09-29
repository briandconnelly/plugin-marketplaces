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
