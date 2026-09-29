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
