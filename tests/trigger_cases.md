# Trigger Cases for plugin-marketplaces

Prompts that must, and must not, load the skill, checked against SKILL.md's frontmatter `description` once plan 2b writes it.
Run each prompt against the skill catalog without naming the skill; store the result in `tests/runs/YYYY-MM-DD-trigger.md`.

## Positive cases (must trigger)

| Prompt | Reason |
| --- | --- |
| "Set up a plugin marketplace for our team's Claude Code plugins." | Creating a user-hosted marketplace is the core scope. |
| "Our Codex users can't see half the plugins in our marketplace.json — why?" | Diagnosing a catalog that one reader skips is the core scope. |
| "Bump weather-mcp to v1.4.0 in our plugin marketplace." | Releasing a plugin version through a catalog entry is the core scope. |
| "Make this Claude Code plugin installable from Codex and Copilot CLI too." | Packaging a plugin for several tools is in scope. |
| "Review our .claude-plugin/marketplace.json and .agents/plugins/marketplace.json before we publish." | Auditing catalog files is in scope. |
| "Should I use a root plugin.json from agent-plugins.org or .codex-plugin/plugin.json?" | Choosing a plugin manifest format is in scope. |

## Negative cases (must not trigger)

| Prompt | Reason |
| --- | --- |
| "Write a PreToolUse hook that blocks rm -rf." | Writing a hook is component authoring, which the skill defers to other skills. |
| "Build an MCP server for our ticketing API." | Writing an MCP server is out of scope. |
| "Install the superpowers plugin for me." | Installing a plugin for personal use is out of scope. |
| "Publish our VS Code extension to the Visual Studio Marketplace." | A vendor-hosted extension marketplace is not a user-hosted plugin marketplace. |
| "List our package on npm." | A package registry is not a plugin marketplace. |
