from helpers import local_ids, read, write

CLAUDE = ".claude-plugin/marketplace.json"
CODEX = ".agents/plugins/marketplace.json"


def test_dotted_marketplace_name_fails_codex(market):
    data = read(market, CODEX)
    data["name"] = "demo.market"
    write(market, CODEX, data)
    assert local_ids(market) == ["local.marketplace-name"]


def test_duplicate_entry(market):
    data = read(market, CLAUDE)
    data["plugins"].append(dict(data["plugins"][1]))
    write(market, CLAUDE, data)
    assert local_ids(market) == ["local.duplicate-entry"]


def test_entry_name_with_space(market):
    for catalog in (CLAUDE, CODEX):
        data = read(market, catalog)
        data["plugins"][1]["name"] = "be ta"
        write(market, catalog, data)
    assert local_ids(market) == ["local.entry-name-pattern", "local.entry-name-pattern"]


def test_manifest_name_mismatch(market):
    write(
        market,
        "plugins/alpha/.claude-plugin/plugin.json",
        {
            "name": "alpha-renamed",
            "version": "1.2.0",
            "description": "Alpha",
            "author": {"name": "T"},
        },
    )
    assert local_ids(market) == ["local.name-mismatch", "local.name-mismatch"]


def claude_only_with_plugin_root(root, source="alpha"):
    (root / CODEX).unlink()
    write(root, "marketplace-policy.json", {"readers": ["claude-code"]})
    data = read(root, CLAUDE)
    data["metadata"] = {"pluginRoot": "./plugins"}
    data["plugins"][0]["source"] = source
    write(root, CLAUDE, data)


def test_plugin_root_bare_name_still_reaches_manifest_checks(market):
    claude_only_with_plugin_root(market)
    manifest = read(market, "plugins/alpha/.claude-plugin/plugin.json")
    manifest["name"] = "alpha-renamed"
    write(market, "plugins/alpha/.claude-plugin/plugin.json", manifest)
    assert local_ids(market) == ["local.name-mismatch"]
