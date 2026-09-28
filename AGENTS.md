# Agent instructions

- Markdown uses one sentence per line, so diffs stay reviewable.
- Dated reports under `docs/research/` are archived evidence: never edit or reformat them; add a new dated file instead (`README.md` and `SHA256SUMS` there are indexes and may be updated).
- Commit messages follow conventional commits.
- A normative rule has exactly one home: the Rules section of `skills/plugin-marketplaces/SKILL.md`; every other file cites the rule id and does not restate it.
- The skill covers a tool only if a runnable probe can check its behaviour; a tool without one is excluded, not described as unverified.
- Tool behaviour facts live in `skills/plugin-marketplaces/scripts/mpcheck/data/readers.json` and the reference files, each with provenance; change a fact only after re-verifying it against its source.
- Use `uv` for all Python work; run `uv run pytest` and `prek run --all-files` before committing.
- Never run the validator or a probe against a real tool configuration; probes use throwaway config directories.
