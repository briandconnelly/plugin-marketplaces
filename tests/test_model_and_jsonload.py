import json

import pytest
from mpcheck.jsonload import DuplicateKeyError, load_json
from mpcheck.model import Finding, Severity


def test_group_and_level():
    assert Finding("schema.portable.mcp", Severity.ERROR, "f", "m").group == "schema.portable"
    assert Finding("schema.portable.mcp", Severity.ERROR, "f", "m").level == "schema"
    assert Finding("local.path-escape", Severity.ERROR, "f", "m").group == "local"


def test_to_dict_is_json_serialisable():
    data = Finding("local.x", Severity.WARNING, "f", "m", rule="R3").to_dict()
    assert json.loads(json.dumps(data))["severity"] == "warning"
    assert data["group"] == "local"


def test_load_json_rejects_duplicate_keys(tmp_path):
    path = tmp_path / "a.json"
    path.write_text('{"name": "a", "name": "b"}', encoding="utf-8")
    with pytest.raises(DuplicateKeyError, match="'name'"):
        load_json(path)


def test_load_json_detects_nested_duplicates(tmp_path):
    path = tmp_path / "a.json"
    path.write_text('{"plugins": [{"source": 1, "source": 2}]}', encoding="utf-8")
    with pytest.raises(DuplicateKeyError):
        load_json(path)


def test_load_json_reads_valid_json(tmp_path):
    path = tmp_path / "a.json"
    path.write_text('{"a": [1, {"b": 2}]}', encoding="utf-8")
    assert load_json(path) == {"a": [1, {"b": 2}]}
