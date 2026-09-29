from pathlib import Path

import pytest
from scenario_doc import DOC, dispatch_prompt, preamble, scenario, scoring, treatment

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


def test_the_preamble_confines_temporary_files_and_xdg_config():
    # plan-2b batch 1-5: arms wrote scratch files into the dispatching session's scratch
    # directory, and one wrote the real ~/.config/git/config through XDG_CONFIG_HOME
    text = " ".join(preamble(TEXT))
    assert "temporary file" in text and "`WORKDIR/.tool-homes/`" in text
    assert "XDG_CONFIG_HOME" in text


def _recorded_prompt(number):
    """The dispatch prompt of the first valid plan-2b baseline record for a scenario."""
    runs = Path(__file__).resolve().parent / "runs"
    path = sorted(runs.glob(f"2026-09-28-s{number}-r[0-9]*-baseline.md"))[0]
    text = path.read_text(encoding="utf-8")
    start = text.index("## Dispatch prompt\n\n```text\n") + len("## Dispatch prompt\n\n```text\n")
    return text[start : text.index("\n```\n", start)]


@pytest.mark.parametrize("number", range(1, 8))
def test_baseline_prompts_are_what_the_baselines_received(number):
    # a treatment arm is comparable only if the baseline text it extends is unchanged
    upstream = Path("$RUN/weather-mcp") if scenario(TEXT, number).has_upstream else None
    assert dispatch_prompt(TEXT, number, Path("$RUN/repo"), upstream) == _recorded_prompt(number)


def test_a_treatment_prompt_is_the_baseline_plus_the_skill_lines(tmp_path):
    work, up = tmp_path / "repo", tmp_path / "weather-mcp"
    skill, validator = (
        tmp_path / "skill" / "plugin-marketplaces",
        tmp_path / "validator" / "bin" / "check-marketplace",
    )
    base = dispatch_prompt(TEXT, 1, work, up)
    treated = dispatch_prompt(TEXT, 1, work, up, skill=skill, validator=validator)
    lines = treatment(TEXT)
    assert len(lines) == 2 and "SKILLDIR" in lines[0] and "VALIDATOR" in lines[1]
    rendered = [
        line.replace("SKILLDIR", str(skill)).replace("VALIDATOR", str(validator)) for line in lines
    ]
    assert treated == base.replace("\n\n", "\n" + "\n".join(rendered) + "\n\n", 1)
    assert "SKILLDIR" not in treated and "VALIDATOR" not in treated
    assert f"`{skill}/SKILL.md`" in treated
    with pytest.raises(ValueError):
        dispatch_prompt(TEXT, 1, work, up, skill=skill)
