# OpenAI's plugin pages after the 2026-09-29 rewrite

Date: 2026-09-29.
This is a hand-written record of the re-verification issue #6 asked for.
The first weekly run of `upstream-drift` (run 36603371947) reported the pin `openai-plugins-build` changed: https://developers.openai.com/plugins/build/plugins.md dropped its lists of root manifest fields, `extensions.com.openai` fields, and `interface` fields, and now points to https://developers.openai.com/plugins/deploy/submission.md for "manifest examples, supported fields, requirements, and import behavior".

## Pages read

- `openai-plugins-build`: https://developers.openai.com/plugins/build/plugins.md, sha256 `cc5b62094f9c8fcd910c6ae72fa58c63a13191abdc29fb45b19500e241f71460` (27,906 characters).
  The only change since the pinned copy is the removed block (lines 654 to 685 of the pinned text) and the pointer that replaces it; the diff is in the run's `upstream.md` report.
- `openai-plugin-submission`: https://developers.openai.com/plugins/deploy/submission.md, sha256 `b89bbdeecec9faf9e7023b4828937a9c0df572b5fc4b1249e471a216b3d7c3b6` (50,740 characters), identical on two consecutive fetches.

## Lines re-verified

Every line `uv run python tests/check_upstream.py lines openai-plugins-build` lists was re-read on 2026-09-28 against the whole pinned page; only the lines whose support was in the removed block need a new source.

| Line | Verdict | Where the support is now |
| --- | --- | --- |
| `codex.md:37` (portable packages take skills from `skills/` and MCP servers from `mcp.json`, and nothing in the manifest can move them) | confirmed | submission page, Manifest fields: "Portable packages always discover skills in `skills/` and MCP servers in `mcp.json`. A skills or `mcpServers` declaration in the inline extension or compatibility overlay can’t replace, disable, or add to those components." |
| `codex.md:38` (`extensions["com.openai"]`, when present, replaces `.codex-plugin/plugin.json` as the overlay rather than merging with it) | confirmed | submission page: "If that object is present, OpenAI ignores settings in `.codex-plugin/plugin.json`; the two files are not merged." |
| `codex.md:40` (display metadata in an `interface` object: `displayName`, `shortDescription`, `longDescription`, `developerName`, `category`, `capabilities`, `websiteURL`, `defaultPrompt`, `brandColor`, `logo`, "and others", in `.codex-plugin/plugin.json` or under `extensions["com.openai"]`) | confirmed | submission page, Listing metadata: "Put the following fields in `extensions.com.openai.interface` for Agent Plugins or interface for the Codex format", listing every field the line names plus `supportURL`, `privacyPolicyURL`, `termsOfServiceURL`, `brandColorDark`, `composerIcon`, `composerIconDark`, `logoDark`, and `screenshots` |
| `codex.md:37` (hooks come from `hooks/hooks.json` unless `extensions["com.openai"].hooks` names another file) | confirmed | still on the build page: "Codex discovers `hooks/hooks.json` by default when the selected OpenAI extension or compatibility manifest doesn't define `hooks`" |

No fact changed; `codex.md`'s E3 row now names the submission page beside the build page, and a new pin `openai-plugin-submission` affects it.
