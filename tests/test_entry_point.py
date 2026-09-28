import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


@pytest.mark.skipif(shutil.which("uvx") is None, reason="uvx not installed")
def test_installed_console_script_validates_a_marketplace(market, tmp_path):
    dist = tmp_path / "dist"
    subprocess.run(
        ["uv", "build", "--wheel", "--out-dir", str(dist), str(ROOT)],
        check=True,
        capture_output=True,
        text=True,
        timeout=300,
    )
    wheel = next(dist.glob("*.whl"))
    proc = subprocess.run(
        ["uvx", "--from", str(wheel), "check-marketplace", str(market), "--no-claude"],
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
        cwd=tmp_path,
    )
    assert proc.returncode == 0, proc.stderr
    assert "No findings." in proc.stdout
