"""Run prepare → collect → assemble → summarize on a scripted arm, with no model and no CLI."""

import json

from assemble import assemble
from collect import collect
from prepare import git, prepare
from records import failed_criteria, load, manifest, score
from summarize import summarize
from test_run_records import check_record
from transcript import load as load_transcript


def write_transcript(path, prompt, calls, report):
    records = [
        {
            "type": "user",
            "timestamp": "2026-09-29T10:00:00Z",
            "cwd": "/start",
            "message": {"role": "user", "content": prompt},
        }
    ]
    for n, call in enumerate(calls):
        part = {"type": "tool_use", "name": call[0], "input": call[1]}
        records.append(
            {
                "type": "assistant",
                "timestamp": f"2026-09-29T10:00:{10 + n}Z",
                "message": {"id": f"m{n}", "model": "claude-opus-5-5", "content": [part]},
            }
        )
    handback = {"type": "tool_use", "name": "SubagentHandback", "input": {"message": report}}
    records.append(
        {
            "type": "assistant",
            "timestamp": "2026-09-29T10:01:00Z",
            "message": {"id": "end", "model": "claude-opus-5-5", "content": [handback]},
        }
    )
    path.write_text("".join(json.dumps(r) + "\n" for r in records), encoding="utf-8")


def test_a_scripted_run_becomes_a_valid_record(tmp_path):
    runs, tasks, out = tmp_path / "runs", tmp_path / "tasks", tmp_path / "out"
    tasks.mkdir()
    out.mkdir()
    (run,) = prepare(
        runs,
        "s2",
        1,
        "baseline",
        "test session",
        tools={"claude": "x", "codex": "x", "copilot": "x"},
    )
    work = run / "repo"
    write_transcript(
        tasks / "arm.output",
        (run / "prompt.txt").read_text(),
        [
            ("Bash", {"command": f"cd {work} && echo '# notes' >> README.md"}),
            ("Bash", {"command": f"cd {work} && touch ../stray.txt"}),
        ],
        "Added nothing useful. I ran no checks.",
    )
    # the transcript is scripted, so apply its effects by hand; the arm commits its change,
    # so the diff must be taken against the fixture, not against HEAD
    with (work / "README.md").open("a") as readme:
        readme.write("# notes\n")
    git(work, "commit", "-q", "-am", "arm commit")
    (work / ".tool-homes").mkdir()  # excluded tool state must not reach the objective checks
    (work / ".tool-homes" / "state").write_text("x")
    (work / ".tool-homes" / "home").symlink_to(tmp_path)  # a link out of the run directory
    summary = collect(
        run, tasks, objective=lambda path: {"exported": sorted(p.name for p in path.iterdir())}
    )
    assert summary["tool_calls"] == 2 and summary["isolation_flags"] == 2
    art = run / "artefacts"
    assert "+# notes" in (art / "diff.patch").read_text()
    assert (
        "README.md | 1 +" in (art / "refs.txt").read_text()
    )  # every branch, diffed against the fixture
    assert json.loads((art / "objective.json").read_text()) == {
        "exported": [".agents", ".claude-plugin", "README.md", "plugins"]
    }
    flag_lines = (art / "isolation-flags.txt").read_text().splitlines()
    assert flag_lines[0].startswith("#1 outside-write:")
    assert flag_lines[1].startswith("after the run symlink-outside:")
    assert load_transcript(tasks / "arm.output").report in (art / "report.md").read_text()
    assert (art / "tool-results.jsonl").read_text() == ""  # the scripted arm got no results

    table = "| Criterion | Result | Evidence |\n|---|---|---|\n| 1 | pass | x |\n| 2 | fail | y |\nTotal: 1 of 2 passed."
    write_transcript(
        tasks / "scorer.output",
        f"Read the file {run / 'score-prompt.txt'} and follow it.",
        [],
        table,
    )
    record = assemble(run, tasks, out, "Adjudication: #1 is a real write outside WORKDIR (test).")
    assert record.name.endswith("-s2-r1-baseline.md")
    text = load(record)
    assert str(tmp_path) not in text and "$RUN/repo" in text  # RUNS' parent becomes $SCRATCH
    assert manifest(text)["metrics"] == {"tool_calls": 2, "wall_seconds": 60.0}
    assert (score(text), failed_criteria(text)) == ((1, 2), [2])
    assert "## Repository refs" in text and "README.md | 1 +" in text  # per-ref evidence is kept
    check_record(record)
    assert "| s2-r1 | 1/2 | 2 | 2 | 60.0 | scored |" in summarize([record])


def test_objective_checks_are_skipped_when_a_committed_link_escapes(tmp_path):
    # Copilot review of PR #3: the real CLIs must never follow a link out of the export
    runs, tasks = tmp_path / "runs", tmp_path / "tasks"
    tasks.mkdir()
    (run,) = prepare(
        runs, "s2", 1, "baseline", "t", tools={"claude": "x", "codex": "x", "copilot": "x"}
    )
    (tmp_path / "real-home").mkdir()
    (run / "repo" / "plugins" / "escape").symlink_to(tmp_path / "real-home")
    write_transcript(tasks / "arm.output", (run / "prompt.txt").read_text(), [], "Done.")

    def never(path):
        raise AssertionError("objective checks ran on an export with an escaping link")

    collect(run, tasks, objective=never)
    result = json.loads((run / "artefacts" / "objective.json").read_text())
    assert result["skipped"].startswith("symlink escapes the export: plugins/escape")
