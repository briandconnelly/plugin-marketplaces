from helpers import local_ids, read, remote, write

CLAUDE = ".claude-plugin/marketplace.json"
CODEX = ".agents/plugins/marketplace.json"
POLICY = "marketplace-policy.json"


def set_entry(root, catalog, index, **changes):
    data = read(root, catalog)
    data["plugins"][index].update(changes)
    write(root, catalog, data)


def test_manifest_versions_disagree(market):
    write(
        market,
        "plugins/alpha/plugin.json",
        {
            "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
            "name": "alpha",
            "version": "1.3.0",
            "description": "Alpha",
        },
    )
    assert local_ids(market) == ["local.version-mismatch", "local.version-mismatch"]


def test_entry_version_disagrees_with_manifest(market):
    set_entry(market, CLAUDE, 0, version="9.9.9")
    assert local_ids(market) == ["local.version-mismatch"]


def test_local_plugin_without_any_version_warns(market):
    for rel in ("plugins/alpha/.claude-plugin/plugin.json", "plugins/alpha/plugin.json"):
        data = read(market, rel)
        del data["version"]
        write(market, rel, data)
    assert local_ids(market) == ["local.version-missing", "local.version-missing"]


def test_membership_difference(market):
    data = read(market, CODEX)
    data["plugins"] = data["plugins"][:1]
    write(market, CODEX, data)
    assert local_ids(market) == ["local.parity-membership"]


def test_membership_exception_suppresses(market):
    data = read(market, CODEX)
    data["plugins"] = data["plugins"][:1]
    write(market, CODEX, data)
    write(
        market,
        POLICY,
        {
            "readers": ["claude-code", "codex"],
            "exceptions": [
                {"plugin": "beta", "kind": "membership", "reason": "Claude-only for now"}
            ],
        },
    )
    assert local_ids(market) == []


def test_version_difference_between_catalogs(market):
    set_entry(market, CODEX, 1, version="0.9.0")
    assert local_ids(market) == ["local.parity-version"]


def test_source_pin_difference_between_catalogs(market):
    set_entry(market, CODEX, 1, source=remote(sha="b" * 40))
    assert local_ids(market) == ["local.parity-source"]


def test_unused_exception_warns(market):
    write(
        market,
        POLICY,
        {
            "readers": ["claude-code", "codex"],
            "exceptions": [{"plugin": "alpha", "kind": "version", "reason": "stale"}],
        },
    )
    assert local_ids(market) == ["policy.unused-exception"]


def test_single_catalog_has_no_parity_findings(market):
    (market / CODEX).unlink()
    write(market, POLICY, {"readers": ["claude-code"]})
    assert local_ids(market) == []


def test_one_manifest_missing_its_version(market):
    data = read(market, "plugins/alpha/plugin.json")
    del data["version"]
    write(market, "plugins/alpha/plugin.json", data)
    assert local_ids(market) == ["local.version-field-missing", "local.version-field-missing"]


def test_same_version_from_different_npm_packages_differs_in_source(market):
    set_entry(market, CLAUDE, 1, source={"source": "npm", "package": "@a/beta", "version": "1.0.0"})
    set_entry(market, CODEX, 1, source={"source": "npm", "package": "@b/beta", "version": "1.0.0"})
    assert local_ids(market) == ["local.parity-source"]


def test_github_and_url_forms_of_one_repository_are_the_same_source(market):
    github = {"source": "github", "repo": "Example/Beta", "ref": "v1.0.0", "sha": "a" * 40}
    set_entry(market, CLAUDE, 1, source=github)
    assert local_ids(market) == []


def test_version_declared_in_one_catalog_only_is_a_difference(market):
    # A local plugin with no manifest version: one catalog declares one, the other none.
    for rel in ("plugins/alpha/.claude-plugin/plugin.json", "plugins/alpha/plugin.json"):
        data = read(market, rel)
        del data["version"]
        write(market, rel, data)
    set_entry(market, CLAUDE, 0, version="1.2.0")
    assert local_ids(market) == [
        "local.parity-version",
        "local.version-field-missing",
        "local.version-field-missing",
        "local.version-missing",
    ]


def test_remote_entry_without_version_is_unknown_not_different(market):
    # The remote plugin's own manifest supplies its version once fetched, so an omitted
    # entry version is unknown offline; the remote level checks it against the manifest.
    data = read(market, CODEX)
    del data["plugins"][1]["version"]
    write(market, CODEX, data)
    assert local_ids(market) == []
