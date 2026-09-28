# Research archive

Research reports gathered on 2026-09-27 while designing the skill (see [the design spec](../superpowers/specs/2026-09-27-plugin-marketplaces-design.md)).
Each report is the verbatim final output of a Claude Code research subagent, extracted programmatically from its transcript; `SHA256SUMS` records the extracted content.
They are archived evidence, so they are exempt from this repo's one-sentence-per-line rule and must not be reformatted or edited.

| File | Scope | Instruments |
| --- | --- | --- |
| [2026-09-27-claude-code.md](2026-09-27-claude-code.md) | Claude Code catalog and plugin formats | live docs, `claude plugin validate` probes on claude 2.1.283 |
| [2026-09-27-codex.md](2026-09-27-codex.md) | Codex catalog and both plugin formats | live docs, `openai/codex@659b35f` source, probes on codex-cli 0.157.1 |
| [2026-09-27-agent-plugins.md](2026-09-27-agent-plugins.md) | Agent Plugins 1.0 spec, governance, client claims | spec repo `agentplugins/agent-plugins-spec@ff8ab5e`, site, schemas |
| [2026-09-27-other-harnesses.md](2026-09-27-other-harnesses.md) | Catalog formats in other agent tools | live docs and source via `gh api` |

These reports are inputs, not references: the skill's references re-verify every fact they use and carry their own provenance.

## Known corrections

- `2026-09-27-other-harnesses.md`, closing recommendation: it says a portable catalog should use "relative or `github` sources"; Codex skips `github` sources (`2026-09-27-codex.md` §1, confirmed by probe), so the widest-reaching remote source type is `url`.
- `2026-09-27-other-harnesses.md`: Cursor, OpenHands, OpenClaw, and Factory Droid are excluded from the skill under the coverage rule (a tool is covered only if a runnable probe can check it), so their rows are not maintained.
- `2026-09-27-claude-code.md`, "Scratchpad hazard": a note about sibling research agents sharing a scratch directory during the session; it has no bearing on the facts reported.
- Codex's review of the design spec added facts not in these reports: Copilot CLI's `plugin marketplace browse <name> --json` and `COPILOT_HOME`/`COPILOT_CACHE_HOME` (verified by `--help` on copilot 1.0.88), and Claude's statement that some git hosts cannot fetch a commit by SHA (verified against the Claude marketplace reference).
