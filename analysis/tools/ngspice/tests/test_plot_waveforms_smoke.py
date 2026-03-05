from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_plot_waveforms_smoke(tmp_path: Path) -> None:
    out_png = tmp_path / "tran_square_smoke.png"

    cmd = [
        sys.executable,
        "tools/plot_waveforms.py",
        "--input",
        "outputs/hdf5/tran_square.h5",
        "--signals",
        "001_v_in",
        "002_v_out",
        "--mode",
        "transient",
        "--output",
        str(out_png),
    ]
    proc = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert out_png.exists()
    assert out_png.stat().st_size > 0
