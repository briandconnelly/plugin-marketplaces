import os

import pytest
from helpers import local_ids, read, remote, write

CLAUDE = ".claude-plugin/marketplace.json"
CODEX = ".agents/plugins/marketplace.json"


def set_entry(root, catalog, index, **changes):
    data = read(root, catalog)
    data["plugins"][index].update(changes)
    write(root, catalog, data)


def test_clean_market_has_no_local_findings(market):
    assert local_ids(market) == []


def test_declared_reader_without_catalog(market):
    (market / CLAUDE).unlink()
    assert local_ids(market) == ["local.reader-no-catalog"]


def test_unread_catalog_warns(market):
    write(market, "marketplace-policy.json", {"readers": ["codex"]})
    assert local_ids(market) == ["local.unread-catalog"]


def test_github_source_in_catalog_codex_reads(market):
    (market / CODEX).unlink()
    set_entry(
        market, CLAUDE, 1, source={"source": "github", "repo": "example/beta", "sha": "a" * 40}
    )
    assert local_ids(market) == ["local.source-type"]


def test_local_object_in_catalog_claude_reads(market):
    set_entry(market, CLAUDE, 0, source={"source": "local", "path": "./plugins/alpha"})
    assert local_ids(market) == ["local.source-type"]


def test_bare_path(market):
    set_entry(market, CLAUDE, 0, source="plugins/alpha")
    assert local_ids(market) == ["local.path-prefix"]


def test_traversal(market):
    set_entry(market, CLAUDE, 0, source="./plugins/../plugins/alpha")
    assert local_ids(market) == ["local.path-traversal"]


def test_symlink_escape(market, tmp_path_factory):
    outside = tmp_path_factory.mktemp("outside")
    os.symlink(outside, market / "plugins" / "escape")
    set_entry(market, CLAUDE, 0, source="./plugins/escape")
    assert "local.path-escape" in local_ids(market)


def test_missing_directory(market):
    set_entry(market, CLAUDE, 0, source="./plugins/nope")
    assert "local.path-missing" in local_ids(market)


def test_source_pointing_at_file(market):
    write(market, "plugins/file.txt", "x")
    set_entry(market, CLAUDE, 0, source="./plugins/file.txt")
    assert "local.path-missing" in local_ids(market)


def test_symlink_loop_is_reported(market):
    os.symlink(market / "plugins" / "loop", market / "plugins" / "loop")
    set_entry(market, CLAUDE, 0, source="./plugins/loop")
    assert "local.path-missing" in local_ids(market)


def test_remote_sources_skip_path_checks(market):
    set_entry(market, CLAUDE, 1, source=remote())
    assert local_ids(market) == []


def test_local_object_without_string_path(market):
    set_entry(market, CODEX, 0, source={"source": "local", "path": 7})
    assert local_ids(market) == ["local.path-invalid"]


def claude_only_with_plugin_root(root, source="alpha"):
    (root / CODEX).unlink()
    write(root, "marketplace-policy.json", {"readers": ["claude-code"]})
    data = read(root, CLAUDE)
    data["metadata"] = {"pluginRoot": "./plugins"}
    data["plugins"][0]["source"] = source
    write(root, CLAUDE, data)


def test_plugin_root_bare_name_is_clean_for_claude(market):
    claude_only_with_plugin_root(market)
    assert local_ids(market) == []


def test_plugin_root_does_not_help_codex(market):
    claude_only_with_plugin_root(market)
    write(market, "marketplace-policy.json", {"readers": ["claude-code", "codex"]})
    ids = local_ids(market)
    assert ids.count("local.path-prefix") == 1
    assert "local.path-missing" not in ids


def test_codex_exempts_cursor_catalog_from_dot_slash(market):
    (market / CLAUDE).unlink()
    (market / CODEX).unlink()
    write(market, "marketplace-policy.json", {"readers": ["codex"]})
    write(
        market,
        ".cursor-plugin/marketplace.json",
        {
            "name": "demo",
            "owner": {"name": "T"},
            "plugins": [{"name": "alpha", "source": "plugins/alpha"}],
        },
    )
    assert local_ids(market) == []


def test_git_subdir_rejected_for_copilot(market):
    write(market, "marketplace-policy.json", {"readers": ["claude-code", "codex", "copilot-cli"]})
    set_entry(
        market,
        CLAUDE,
        1,
        source={
            "source": "git-subdir",
            "url": "https://github.com/o/r.git",
            "path": "p",
            "sha": "a" * 40,
        },
    )
    assert "local.source-type" in local_ids(market)


@pytest.mark.parametrize(
    "source",
    [
        {"source": "github", "sha": "a" * 40},
        {"source": "url", "sha": "a" * 40},
        {"source": "git-subdir", "url": "https://github.com/o/r.git", "sha": "a" * 40},
        {"source": "npm", "version": "1.0.0"},
    ],
)
def test_source_without_its_locator_is_invalid(market, source):
    (market / CODEX).unlink()
    write(market, "marketplace-policy.json", {"readers": ["claude-code"]})
    set_entry(market, CLAUDE, 1, source=source)
    assert "local.source-invalid" in local_ids(market)
