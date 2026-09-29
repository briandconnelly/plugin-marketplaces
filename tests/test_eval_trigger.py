import json

import pytest
from trigger import (
    CASES,
    SKILL_NAME,
    cases,
    catalog,
    description,
    offered,
    passed,
    prepare,
    record,
    render,
    verdict,
)


def test_the_cases_come_from_the_trigger_file():
    found = cases(CASES.read_text(encoding="utf-8"))
    assert [c.id for c in found] == [f"p{n}" for n in range(1, 7)] + [f"n{n}" for n in range(1, 6)]
    assert all(c.expected == SKILL_NAME for c in found if c.id.startswith("p"))
    assert all(c.expected == "none" for c in found if c.id.startswith("n"))
    assert found[0].prompt == "Set up a plugin marketplace for our team's Claude Code plugins."


def test_the_catalog_offers_every_skill_once_in_a_per_repetition_order():
    first, second = catalog(1), catalog(2)
    names = [name for name, _ in first]
    assert sorted(names) == sorted(name for name, _ in second)
    assert names.count(SKILL_NAME) == 1 and len(names) == len(set(names)) == 8
    assert names != [name for name, _ in second]
    assert catalog(1) == first  # deterministic
    assert dict(first)[SKILL_NAME] == description()


def test_prepare_writes_one_prompt_per_case_and_repetition(tmp_path):
    runs = prepare(tmp_path, reps=3)
    assert len(runs) == 33
    one = tmp_path / "p1-r1"
    prompt = (one / "prompt.txt").read_text()
    assert prompt == render(cases(CASES.read_text(encoding="utf-8"))[0], catalog(1))
    assert "> Set up a plugin marketplace" in prompt and "Do not use any tools." in prompt
    assert json.loads((one / "case.json").read_text())["expected"] == SKILL_NAME
    with pytest.raises(FileExistsError):
        prepare(tmp_path, reps=1)


@pytest.mark.parametrize(
    ("reply", "chosen"),
    [
        ("plugin-marketplaces\nIt is about catalogs.", "plugin-marketplaces"),
        ("`plugin-marketplaces` — it fits.", "plugin-marketplaces"),
        ("**none**\nNo skill fits.", "none"),
        ("None.", "none"),
        ("plugin-dev:plugin-structure\nScaffolding.", "plugin-dev:plugin-structure"),
        ("\n\nfastmcp", "fastmcp"),
    ],
)
def test_verdict_reads_the_first_line(reply, chosen):
    assert verdict(reply) == chosen


def _transcript(path, prompt, reply):
    records = [
        {
            "type": "user",
            "timestamp": "2026-09-29T10:00:00Z",
            "cwd": "/s",
            "message": {"role": "user", "content": prompt},
        },
        {
            "type": "assistant",
            "timestamp": "2026-09-29T10:00:03Z",
            "message": {
                "id": "m",
                "model": "claude-opus-5-5",
                "content": [{"type": "text", "text": reply}],
            },
        },
    ]
    path.write_text("".join(json.dumps(r) + "\n" for r in records), encoding="utf-8")


def test_record_scores_every_reply(tmp_path):
    out, tasks = tmp_path / "out", tmp_path / "tasks"
    tasks.mkdir()
    for i, run in enumerate(prepare(out, reps=1)):
        wrong = run.name == "n1-r1" or run.name == "p2-r1"
        reply = (
            ("fastmcp\nNo." if run.name.startswith("p") else "plugin-marketplaces\nYes.")
            if wrong
            else (
                "plugin-marketplaces\nFits." if run.name.startswith("p") else "none\nNothing fits."
            )
        )
        _transcript(tasks / f"a{i}.output", (run / "prompt.txt").read_text(), reply)
    doc = record(out, tasks, tmp_path / "trigger.md").read_text()
    assert "Positive: 5 of 6 passed." in doc and "Negative: 4 of 5 passed." in doc
    assert "| p2 | 1 | plugin-marketplaces | fastmcp | FAIL |" in doc
    assert "| n1 | 1 | none | plugin-marketplaces | FAIL |" in doc
    assert "claude-opus-5-5" in doc


def test_a_negative_case_passes_only_on_none_or_an_offered_skill():
    names = offered(render(cases(CASES.read_text(encoding="utf-8"))[6], catalog(1)))
    assert SKILL_NAME in names and "fastmcp" in names and len(names) == 8
    assert passed("none", "none", names)
    assert passed("none", "fastmcp", names)
    assert not passed("none", "", names)  # an empty reply is not an answer
    assert not passed("none", "made-up-skill", names)
    assert not passed("none", SKILL_NAME, names)
    assert passed(SKILL_NAME, SKILL_NAME, names)
