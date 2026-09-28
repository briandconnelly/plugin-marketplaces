import os

from home_snapshot import compare, main, snapshot


def test_compare_reports_every_kind_of_change(tmp_path):
    home = tmp_path / "home"
    (home / "sub").mkdir(parents=True)
    (home / "keep").write_text("a")
    (home / "edit").write_text("a")
    (home / "sub" / "gone").write_text("a")
    os.symlink("/nowhere", home / "link")
    before = snapshot([home, tmp_path / "absent"])
    assert compare(before, snapshot([home, tmp_path / "absent"])) == []  # clean is a real result
    (home / "edit").write_text("b")
    (home / "sub" / "gone").unlink()
    (home / "new").write_text("a")
    (tmp_path / "absent").mkdir()
    after = snapshot([home, tmp_path / "absent"])
    assert compare(before, after) == [
        f"created {tmp_path / 'absent'}",
        f"changed {home}/edit",
        f"added {home}/new",
        f"removed {home}/sub/gone",
    ]
    files = before[str(home)]
    assert files is not None and files["link"] == "symlink: /nowhere"


def test_cli_exit_status_marks_a_change(tmp_path, capsys):
    home = tmp_path / "home"
    home.mkdir()
    a, b = tmp_path / "a.json", tmp_path / "b.json"
    assert main(["save", str(a), str(home)]) == 0
    assert main(["save", str(b), str(home)]) == 0
    assert main(["compare", str(a), str(b)]) == 0
    (home / "x").write_text("1")
    assert main(["save", str(b), str(home)]) == 0
    assert main(["compare", str(a), str(b)]) == 1
    assert f"added {home}/x" in capsys.readouterr().out
