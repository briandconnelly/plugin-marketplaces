from mpcheck.readers import load_readers, source_path, source_type


def test_covered_readers_load():
    readers = load_readers()
    assert {"claude-code", "codex"} <= set(readers)
    codex = readers["codex"]
    assert codex.catalog_paths[0] == ".agents/plugins/marketplace.json"
    assert ".claude-plugin/marketplace.json" in codex.catalog_paths
    assert "github" not in codex.source_types
    assert "local-object" in codex.source_types
    assert "local-object" not in readers["claude-code"].source_types


def test_name_patterns():
    readers = load_readers()
    codex_market = readers["codex"].marketplace_name_re
    claude_market = readers["claude-code"].marketplace_name_re
    codex_entry = readers["codex"].entry_name_re
    assert codex_market and claude_market and codex_entry
    assert codex_market.fullmatch("my-market_1")
    assert not codex_market.fullmatch("my.market")
    assert not claude_market.fullmatch("has space")
    assert codex_entry.fullmatch("a.b-c")
    assert not codex_entry.fullmatch("a..b")


def test_source_type_classification():
    assert source_type("./plugins/a") == "path"
    assert source_type({"source": "local", "path": "./a"}) == "local-object"
    assert source_type({"source": "github", "repo": "o/r"}) == "github"
    assert source_type({"repo": "o/r"}) == "invalid"
    assert source_type(7) == "invalid"


def test_source_path():
    assert source_path("./a") == "./a"
    assert source_path({"source": "local", "path": "./b"}) == "./b"
    assert source_path({"source": "url", "url": "https://x"}) is None


def test_copilot_reader():
    copilot = load_readers()["copilot-cli"]
    assert copilot.catalog_paths[-1] == ".claude-plugin/marketplace.json"
    assert copilot.source_types == {"path", "github", "url"}


def test_copilot_honours_plugin_root():
    # docs/research/2026-09-27-copilot-pluginroot-probe.md
    assert load_readers()["copilot-cli"].honours_plugin_root is True
