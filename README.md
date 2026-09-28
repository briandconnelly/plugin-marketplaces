# plugin-marketplaces

An agent skill for creating, auditing, maintaining, and releasing user-hosted plugin marketplaces for Claude Code, Codex, and tools that read the same catalog formats.

A user-hosted plugin marketplace is a catalog file that its maintainer writes and hosts, typically in a git repository; it is distinct from a vendor-hosted registry.

Status: under construction; see `docs/superpowers/specs/` for the design.

## Development

```bash
uv sync
uv run pytest
prek run --all-files
```
