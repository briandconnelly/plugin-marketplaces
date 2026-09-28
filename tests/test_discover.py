from helpers import AP_SCHEMA, write
from mpcheck.discover import discover
from mpcheck.readers import load_readers

READERS = load_readers()
CLAUDE = ".claude-plugin/marketplace.json"


def ids(findings):
    return sorted(f.check for f in findings)


def catalog(**extra):
    return {"name": "demo", "owner": {"name": "T"}, "plugins": [], **extra}


def test_no_catalog_is_an_error(tmp_path):
    repo, findings = discover(tmp_path, READERS)
    assert ids(findings) == ["schema.parse.no-catalog"]
    assert repo.catalogs == {}


def test_codex_prefers_native_catalog(tmp_path):
    write(tmp_path, ".claude-plugin/marketplace.json", catalog())
    repo, _ = discover(tmp_path, READERS)
    assert repo.reader_catalog["codex"] == ".claude-plugin/marketplace.json"
    write(tmp_path, ".agents/plugins/marketplace.json", catalog())
    repo, _ = discover(tmp_path, READERS)
    assert repo.reader_catalog["codex"] == ".agents/plugins/marketplace.json"
    assert repo.reader_catalog["claude-code"] == ".claude-plugin/marketplace.json"


def test_duplicate_key_is_reported(tmp_path):
    write(tmp_path, ".claude-plugin/marketplace.json", '{"name": "a", "name": "b", "plugins": []}')
    _, findings = discover(tmp_path, READERS)
    assert ids(findings) == ["schema.parse.duplicate-key"]


def test_bom_is_reported(tmp_path):
    path = tmp_path / ".claude-plugin" / "marketplace.json"
    path.parent.mkdir(parents=True)
    path.write_bytes(b"\xef\xbb\xbf" + b'{"name": "a", "plugins": []}')
    _, findings = discover(tmp_path, READERS)
    assert ids(findings) == ["schema.parse.invalid-json"]
    assert findings[0].file == ".claude-plugin/marketplace.json"


def test_catalog_shape_errors(tmp_path):
    write(tmp_path, ".claude-plugin/marketplace.json", catalog(plugins={}))
    write(
        tmp_path,
        ".agents/plugins/marketplace.json",
        catalog(
            plugins=[
                {"name": "ok", "source": "./x"},
                {"source": "./y"},
                {"name": "no-source"},
                "not-an-object",
            ]
        ),
    )
    repo, findings = discover(tmp_path, READERS)
    assert ids(findings) == ["schema.parse.catalog-shape"] + ["schema.parse.entry-shape"] * 3
    assert [i for i, _ in repo.catalogs[".agents/plugins/marketplace.json"].entries] == [0]
    assert {f.pointer for f in findings if f.check.endswith("entry-shape")} == {
        "/plugins/1",
        "/plugins/2",
        "/plugins/3",
    }


def test_local_plugin_manifests_are_indexed(tmp_path):
    write(
        tmp_path,
        ".claude-plugin/marketplace.json",
        catalog(plugins=[{"name": "a", "source": "./p/a"}]),
    )
    write(tmp_path, "p/a/.claude-plugin/plugin.json", {"name": "a"})
    write(tmp_path, "p/a/plugin.json", {"$schema": AP_SCHEMA, "name": "a"})
    repo, findings = discover(tmp_path, READERS)
    assert findings == []
    plugin = repo.plugin_for({"name": "a", "source": "./p/a"}, repo.catalogs[CLAUDE])
    assert plugin is not None
    assert set(plugin.manifests) == {".claude-plugin/plugin.json", "plugin.json"}


def test_root_plugin_json_without_portable_schema(tmp_path):
    write(
        tmp_path,
        ".claude-plugin/marketplace.json",
        catalog(plugins=[{"name": "a", "source": "./p/a"}]),
    )
    write(tmp_path, "p/a/plugin.json", {"name": "a"})
    repo, findings = discover(tmp_path, READERS)
    assert ids(findings) == ["local.portable-schema-missing"]
    plugin = repo.plugin_for({"source": "./p/a"}, repo.catalogs[CLAUDE])
    assert plugin is not None
    assert "plugin.json" not in plugin.manifests


def test_symlinked_root_plugin_json(tmp_path):
    write(
        tmp_path,
        ".claude-plugin/marketplace.json",
        catalog(plugins=[{"name": "a", "source": "./p/a"}]),
    )
    real = write(tmp_path, "elsewhere.json", {"$schema": AP_SCHEMA, "name": "a"})
    (tmp_path / "p/a").mkdir(parents=True)
    (tmp_path / "p/a/plugin.json").symlink_to(real)
    _, findings = discover(tmp_path, READERS)
    assert ids(findings) == ["local.portable-symlink"]


def test_non_object_manifests_are_reported(tmp_path):
    write(
        tmp_path,
        ".claude-plugin/marketplace.json",
        catalog(plugins=[{"name": "a", "source": "./p/a"}]),
    )
    write(tmp_path, "p/a/.claude-plugin/plugin.json", [])
    write(tmp_path, "p/a/plugin.json", "7\n")
    _, findings = discover(tmp_path, READERS)
    assert ids(findings) == ["schema.parse.manifest-shape", "schema.parse.manifest-shape"]
