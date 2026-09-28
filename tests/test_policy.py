from helpers import write
from mpcheck.policy import load_policy
from mpcheck.readers import load_readers

READERS = load_readers()
CLAUDE = ".claude-plugin/marketplace.json"
CODEX = ".agents/plugins/marketplace.json"
READING: dict[str, str | None] = {"claude-code": CLAUDE, "codex": None}


def ids(findings):
    return sorted(f.check for f in findings)


def test_missing_policy_infers_readers_and_warns(tmp_path):
    policy, findings = load_policy(tmp_path, None, READERS, READING)
    assert policy.readers == ("claude-code",)
    assert policy.declared is False
    assert ids(findings) == ["policy.inferred"]


def test_inference_ignores_a_fallback_catalog(tmp_path):
    reading: dict[str, str | None] = {"claude-code": CLAUDE, "codex": CLAUDE}
    policy, findings = load_policy(tmp_path, None, READERS, reading)
    assert policy.readers == ("claude-code",)
    assert "codex would also read a catalog here" in findings[0].message


def test_inference_uses_native_catalogs(tmp_path):
    reading: dict[str, str | None] = {"claude-code": CLAUDE, "codex": CODEX}
    policy, _ = load_policy(tmp_path, None, READERS, reading)
    assert policy.readers == ("claude-code", "codex")


def test_valid_policy(tmp_path):
    write(
        tmp_path,
        "marketplace-policy.json",
        {
            "readers": ["claude-code", "codex"],
            "exceptions": [{"plugin": "x", "kind": "membership", "reason": "Claude only"}],
            "channels": [{"plugin": "y", "ref": "release", "reason": "release branch"}],
        },
    )
    policy, findings = load_policy(tmp_path, None, READERS, READING)
    assert findings == []
    assert policy.readers == ("claude-code", "codex")
    assert policy.excepts("x", "membership")
    assert not policy.excepts("x", "version")
    assert policy.channel("y", "release") is not None
    assert policy.channel("y", "main") is None


def test_unknown_reader(tmp_path):
    write(tmp_path, "marketplace-policy.json", {"readers": ["claude-code", "cursor"]})
    policy, findings = load_policy(tmp_path, None, READERS, READING)
    assert ids(findings) == ["policy.unknown-reader"]
    assert policy.readers == ("claude-code",)


def test_exception_without_reason(tmp_path):
    exceptions = [
        {"plugin": "x", "kind": "membership", "reason": "  "},
        {"plugin": "y", "kind": "bogus", "reason": "r"},
    ]
    write(tmp_path, "marketplace-policy.json", {"readers": ["codex"], "exceptions": exceptions})
    policy, findings = load_policy(tmp_path, None, READERS, READING)
    assert ids(findings) == ["policy.invalid-exception", "policy.invalid-exception"]
    assert policy.exceptions == ()


def test_non_string_kind_is_invalid_not_a_crash(tmp_path):
    exception = {"plugin": "x", "kind": [], "reason": "r"}
    write(tmp_path, "marketplace-policy.json", {"readers": ["codex"], "exceptions": [exception]})
    _, findings = load_policy(tmp_path, None, READERS, READING)
    assert ids(findings) == ["policy.invalid-exception"]


def test_channel_without_reason(tmp_path):
    channels = [{"plugin": "y", "ref": "release"}, {"plugin": "y", "ref": 3, "reason": "r"}]
    write(tmp_path, "marketplace-policy.json", {"readers": ["codex"], "channels": channels})
    policy, findings = load_policy(tmp_path, None, READERS, READING)
    assert ids(findings) == ["policy.invalid-channel", "policy.invalid-channel"]
    assert policy.channels == ()


def test_invalid_policy_shapes(tmp_path):
    write(tmp_path, "marketplace-policy.json", {"readers": [], "exceptions": {}, "channels": 1})
    _, findings = load_policy(tmp_path, None, READERS, READING)
    assert ids(findings) == ["policy.invalid", "policy.invalid", "policy.invalid"]


def test_explicit_policy_path(tmp_path):
    custom = write(tmp_path, "config/policy.json", {"readers": ["codex"]})
    policy, findings = load_policy(tmp_path, custom, READERS, READING)
    assert findings == []
    assert policy.readers == ("codex",)
