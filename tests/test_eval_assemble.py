from pathlib import Path

from assemble import redact, secret_lines

SESSION_ID = "0cb38abb-81e7-44aa-9a78-e2678b385bc4"


def test_redact_hides_the_session_and_the_encoded_project_path(tmp_path):
    session = tmp_path / "-Users-someone-projects-skills" / SESSION_ID
    run = session / "scratchpad" / "eval-b" / "s2-r1"
    doc = "\n".join(
        [
            f"cd {run}/repo",
            f"cat {run.parent}/batch.json {run.parent.parent}/docs/x.md",
            f"cat {session}/tasks/b1.output",
            f"grep x {Path.home()}/.claude/projects/-Users-someone-projects-skills/{SESSION_ID}/tool-results/t.txt",
        ]
    )
    out = redact(doc, run)
    assert "$RUN/repo" in out and "$RUNS/batch.json" in out and "$SCRATCH/docs" in out
    assert "$SESSION/tasks/b1.output" in out
    assert "~/.claude/projects/$PROJECT/$SESSION_ID/tool-results" in out
    assert "-Users-" not in out and SESSION_ID not in out


def test_credentials_are_found_but_placeholders_are_not():
    assert secret_lines("echo ghp_" + "a1B2" * 9)
    assert secret_lines("Authorization: Bearer " + "x9Y8" * 8)
    assert secret_lines("key sk-" + "Ab3" * 10)
    assert secret_lines("-----BEGIN OPENSSH PRIVATE KEY-----")
    assert not secret_lines(
        "REVIEW_API_KEY=secret123 COPILOT_GITHUB_TOKEN=dummy-not-a-token sk-from-shell"
    )
