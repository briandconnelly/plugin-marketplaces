import hashlib
from pathlib import Path

RESEARCH = Path(__file__).resolve().parent.parent / "docs" / "research"


def recorded() -> dict[str, str]:
    lines = (RESEARCH / "SHA256SUMS").read_text(encoding="utf-8").splitlines()
    return {name: digest for digest, name in (line.split(maxsplit=1) for line in lines)}


def test_every_dated_report_is_in_the_checksum_index():
    dated = {p.name for p in RESEARCH.glob("20[0-9][0-9]-*.md")}
    assert dated, "no dated reports found; the glob is broken"
    assert set(recorded()) == dated


def test_every_recorded_digest_matches():
    for name, digest in recorded().items():
        assert hashlib.sha256((RESEARCH / name).read_bytes()).hexdigest() == digest, name
