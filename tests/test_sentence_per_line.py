from check_sentence_per_line import main, violations


def test_single_sentences_pass():
    assert violations("One sentence.\nAnother sentence here.\n") == []


def test_two_sentences_on_one_line_fail():
    assert violations("Intro line.\nFirst one. Second one.\n") == [2]


def test_sentences_ending_in_code_or_capitals_fail():
    assert violations("Run `uv sync`. Then run the tests.\n") == [1]
    assert violations("Report it as SKIPPED. Never as passed.\n") == [1]


def test_abbreviations_are_not_sentence_breaks():
    assert violations("Use a source, e.g. Codex reads it.\nCompare A vs. B here.\n") == []


def test_list_markers_and_numbered_headings_are_not_sentences():
    assert violations("## 1. Purpose\n1. Core model: a catalog.\n  2. Second item here.\n") == []


def test_code_spans_fences_and_tables_are_ignored():
    text = "Run `a. B` now.\n```\nx = 1. Y = 2.\n```\n| a. B | c. D |\n"
    assert violations(text) == []


def test_main_reports_and_fails(tmp_path, capsys):
    bad = tmp_path / "bad.md"
    bad.write_text("One. Two.\n", encoding="utf-8")
    assert main([str(bad)]) == 1
    assert "bad.md:1" in capsys.readouterr().out
