from helpers import local_ids, read, remote, write

CLAUDE = ".claude-plugin/marketplace.json"
CODEX = ".agents/plugins/marketplace.json"


def set_both(root, index, **changes):
    for catalog in (CLAUDE, CODEX):
        data = read(root, catalog)
        data["plugins"][index].update(changes)
        write(root, catalog, data)


def test_git_source_without_sha(market):
    source = remote()
    del source["sha"]
    set_both(market, 1, source=source)
    assert local_ids(market) == ["local.pin-missing", "local.pin-missing"]


def test_short_sha(market):
    set_both(market, 1, source=remote(sha="abc1234"))
    assert local_ids(market) == ["local.pin-malformed", "local.pin-malformed"]


def test_npm_range_is_not_a_pin(market):
    set_both(market, 1, source={"source": "npm", "package": "@x/beta", "version": "^1.0.0"})
    assert local_ids(market) == ["local.pin-missing", "local.pin-missing"]


def test_npm_exact_version_passes(market):
    set_both(market, 1, source={"source": "npm", "package": "@x/beta", "version": "1.0.0"})
    assert local_ids(market) == []


def test_archive_without_sha256(market):
    (market / CODEX).unlink()
    write(market, "marketplace-policy.json", {"readers": ["claude-code"]})
    data = read(market, CLAUDE)
    data["plugins"][1]["source"] = {"source": "archive", "url": "https://example.com/b.zip"}
    write(market, CLAUDE, data)
    assert local_ids(market) == ["local.pin-missing"]


def test_command_source_is_unpinnable(market):
    (market / CODEX).unlink()
    write(market, "marketplace-policy.json", {"readers": ["claude-code"]})
    data = read(market, CLAUDE)
    data["plugins"][1]["source"] = {"source": "command", "command": "echo /tmp/x"}
    write(market, CLAUDE, data)
    assert local_ids(market) == ["local.pin-unpinnable"]


def test_entry_hooks_as_path(market):
    data = read(market, CLAUDE)
    data["plugins"][0]["hooks"] = "./hooks/hooks.json"
    write(market, CLAUDE, data)
    assert local_ids(market) == ["local.entry-hooks-path"]


def test_entry_hooks_inline_object_passes(market):
    data = read(market, CLAUDE)
    data["plugins"][0]["hooks"] = {"SessionStart": []}
    write(market, CLAUDE, data)
    assert local_ids(market) == []


def test_portable_plugin_with_only_dot_mcp(market):
    write(
        market, "plugins/alpha/.mcp.json", {"mcpServers": {"x": {"command": "uvx", "args": ["x"]}}}
    )
    assert local_ids(market) == ["local.portable-mcp-missing"]


def claude_only(root):
    (root / CODEX).unlink()


def unpinned_release(root, channels):
    claude_only(root)
    write(root, "marketplace-policy.json", {"readers": ["claude-code"], "channels": channels})
    data = read(root, CLAUDE)
    data["plugins"][1]["source"] = {"source": "github", "repo": "example/beta", "ref": "release"}
    write(root, CLAUDE, data)


def test_declared_channel_is_info_not_error(market):
    unpinned_release(market, [{"plugin": "beta", "ref": "release", "reason": "release branch"}])
    assert local_ids(market) == ["local.pin-channel"]


def test_channel_for_another_ref_does_not_excuse(market):
    unpinned_release(market, [{"plugin": "beta", "ref": "main", "reason": "main branch"}])
    assert local_ids(market) == ["local.pin-missing", "policy.unused-channel"]


def test_unused_channel_warns(market):
    write(
        market,
        "marketplace-policy.json",
        {
            "readers": ["claude-code", "codex"],
            "channels": [{"plugin": "beta", "ref": "release", "reason": "stale"}],
        },
    )
    assert local_ids(market) == ["policy.unused-channel"]


def test_pip_source_has_no_verified_pin_rule(market):
    claude_only(market)
    write(market, "marketplace-policy.json", {"readers": ["claude-code"]})
    data = read(market, CLAUDE)
    data["plugins"][1]["source"] = {"source": "pip", "package": "beta", "version": "1.0.0"}
    write(market, CLAUDE, data)
    assert local_ids(market) == ["local.pin-unverified", "local.source-type"]
