# plugin-marketplaces

An agent skill for creating, auditing, maintaining, and releasing user-hosted plugin marketplaces for Claude Code, Codex, and tools that read the same catalog formats.

A user-hosted plugin marketplace is a catalog file that its maintainer writes and hosts, typically in a git repository; it is distinct from a vendor-hosted registry.

Status: the skill and its offline validator are written and being evaluated; see `docs/superpowers/specs/` for the design and `tests/runs/` for the evaluation records.

## Install

This repository is its own marketplace, with one plugin, `plugin-marketplaces`.

```bash
# Claude Code
claude plugin marketplace add briandconnelly/plugin-marketplaces
claude plugin install plugin-marketplaces@plugin-marketplaces

# Codex
codex plugin marketplace add briandconnelly/plugin-marketplaces
codex plugin add plugin-marketplaces@plugin-marketplaces

# GitHub Copilot CLI
copilot plugin marketplace add briandconnelly/plugin-marketplaces
copilot plugin install plugin-marketplaces@plugin-marketplaces
```

The validator also runs on its own, for example in another repository's CI:

```bash
uvx --from git+https://github.com/briandconnelly/plugin-marketplaces check-marketplace .
```

## Development

```bash
uv sync
uv run pytest
prek run --all-files
```
