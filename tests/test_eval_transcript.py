import json

import pytest
from transcript import find, find_containing, load


def record(kind, content, *, ts, msg_id=None, model="claude-opus-5-5"):
    rec = {"type": kind, "timestamp": ts, "cwd": "/start"}
    if kind == "user":
        rec["message"] = {"role": "user", "content": content}
    else:
        rec["message"] = {"id": msg_id, "model": model, "content": content}
    return rec


def write(path, records):
    path.write_text("".join(json.dumps(r) + "\n" for r in records), encoding="utf-8")
    return path


@pytest.fixture
def arm(tmp_path):
    bash = {"type": "tool_use", "id": "t1", "name": "Bash", "input": {"command": "cd /w && ls"}}
    result = {
        "type": "tool_result",
        "tool_use_id": "t1",
        "content": [{"type": "text", "text": "a b"}],
    }
    handback = {"type": "tool_use", "name": "SubagentHandback", "input": {"message": "Done."}}
    return write(
        tmp_path / "a1.output",
        [
            record("user", "You are working in `/w`.", ts="2026-09-29T10:00:00.000Z"),
            record("assistant", [bash], ts="2026-09-29T10:00:05.000Z", msg_id="m1"),
            record("user", [result], ts="2026-09-29T10:00:30.000Z"),
            record("assistant", [handback], ts="2026-09-29T10:01:10.500Z", msg_id="m2"),
        ],
    )


def test_load_reads_prompt_calls_report_and_cost(arm):
    t = load(arm)
    assert t.prompt == "You are working in `/w`."
    assert t.calls == [{"tool": "Bash", "input": {"command": "cd /w && ls"}}]
    assert t.results == [{"call": 0, "is_error": False, "output": "a b"}]
    assert t.report == "Done."
    assert t.models == ["claude-opus-5-5"]
    assert t.start_cwd == "/start"
    assert t.metrics() == {"tool_calls": 1, "wall_seconds": 70.5}


def test_report_falls_back_to_the_last_text(tmp_path):
    text = {"type": "text", "text": "Final answer."}
    path = write(
        tmp_path / "a2.output",
        [
            record("user", [{"type": "text", "text": "Score this."}], ts="2026-09-29T10:00:00Z"),
            record("assistant", [text], ts="2026-09-29T10:00:01Z", msg_id="m1"),
        ],
    )
    t = load(path)
    assert (t.prompt, t.report) == ("Score this.", "Final answer.")


def test_find_matches_the_exact_prompt_only(arm, tmp_path):
    write(
        tmp_path / "b.output",
        [record("user", "You are working in `/w`. Extra.", ts="2026-09-29T10:00:00Z")],
    )
    assert find(tmp_path, "You are working in `/w`.") == arm
    assert find(tmp_path, "You are working in `/w`.\n") == arm  # a file's trailing newline
    assert find_containing(tmp_path, "Extra.") == tmp_path / "b.output"
    with pytest.raises(LookupError):
        find(tmp_path, "nothing like this")
    with pytest.raises(LookupError):
        find_containing(tmp_path, "You are working")


def test_find_skips_files_that_are_not_transcripts(arm, tmp_path):
    # the task directory also holds background shell output, which is not JSONL
    (tmp_path / "b3ra2fmaq.output").write_text("a1.output 301774 {partial\n", encoding="utf-8")
    (tmp_path / "empty.output").write_text("", encoding="utf-8")
    assert find(tmp_path, "You are working in `/w`.") == arm
    assert find_containing(tmp_path, "/w") == arm
