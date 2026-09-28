from check_skill_frontmatter import _extract_frontmatter

BLOCK = "---\nname: demo\ndescription: |\n  first line\n  ---\n  still description\n---\nbody\n"


def test_indented_marker_inside_a_block_scalar_does_not_close():
    yaml_text, _ = _extract_frontmatter(BLOCK)
    assert yaml_text is not None and "still description" in yaml_text


def test_indented_opening_marker_is_not_frontmatter():
    assert _extract_frontmatter("  ---\nname: demo\n---\n") == (None, 0)


def test_trailing_whitespace_on_a_marker_is_allowed():
    yaml_text, _ = _extract_frontmatter("--- \nname: demo\n---\t\nbody\n")
    assert yaml_text == "name: demo"
