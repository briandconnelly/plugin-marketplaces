import pytest
from scenario_doc import DOC, dispatch_prompt, preamble, scenario, scoring

TEXT = DOC.read_text(encoding="utf-8")


@pytest.mark.parametrize("number", range(1, 8))
def test_every_scenario_parses_with_numbered_criteria(number):
    item = scenario(TEXT, number)
    assert item.prompt and "\n> " not in item.prompt
    assert item.criteria.startswith("**Success criteria:**\n\n1. ")
    assert item.has_upstream == (number in (1, 5))


def test_the_preamble_names_no_tool():
    lines = preamble(TEXT)
    assert lines[0].startswith("You are working in `WORKDIR`")
    assert not any(tool in " ".join(lines) for tool in ("claude", "codex", "copilot", "CODEX_HOME"))
    assert any("Do not send a prompt to any AI model" in line for line in lines)


def test_the_upstream_line_appears_only_when_the_task_mentions_it(tmp_path):
    with_mirror = dispatch_prompt(TEXT, 5, tmp_path / "repo", tmp_path / "weather-mcp")
    without = dispatch_prompt(TEXT, 2, tmp_path / "repo", None)
    assert f"You may also read `{tmp_path / 'weather-mcp'}`" in with_mirror
    assert "UPSTREAM" not in with_mirror and "You may also read" not in without
    with pytest.raises(ValueError):
        dispatch_prompt(TEXT, 1, tmp_path / "repo", None)


def test_scoring_explains_conditional_criteria():
    # scenario 5 passes a reasoned hold through an "either … or" criterion
    assert "either" in scenario(TEXT, 5).criteria.lower()
    assert 'A criterion of the form "either … or …" passes when either branch holds.' in scoring(
        TEXT
    )
