from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import h5py
import numpy as np

from tools.normalize_raw import normalize_raw_to_hdf5


SAMPLE_RAW = """Title: synthetic tran
Date: Wed Mar 04 00:00:00 2026
Plotname: Transient Analysis
Flags: real
No. Variables: 3
No. Points: 4
Variables:
	0	time	time
	1	v(in)	voltage
	2	v(out)	voltage
Values:
	0	0.0
	1	0.0
	2	0.0
	1	1e-9
	1	1.0
	2	0.5
	2	2e-9
	1	0.0
	2	1.0
	3	3e-9
	1	1.0
	2	1.5
"""


def _write_sample_raw(tmp_path: Path) -> Path:
    raw = tmp_path / "sample.raw"
    raw.write_text(SAMPLE_RAW, encoding="utf-8")
    return raw


def test_normalize_raw_library_smoke(tmp_path: Path):
    raw = _write_sample_raw(tmp_path)
    out = tmp_path / "sample.h5"

    info = normalize_raw_to_hdf5(raw, out, case_id="sample_case")

    assert out.exists()
    assert info["n_points"] == 4
    assert info["n_vars"] == 3
    assert info["indep_var"] == "time"

    with h5py.File(out, "r") as h5:
        assert h5["vectors"].shape == (4, 3)
        assert list(h5["vector_names"].asstr()[:]) == ["time", "v(in)", "v(out)"]
        assert "vector_kinds" in h5
        assert "indep_var" in h5
        assert "signals" in h5
        assert len(h5["signals"].keys()) == 2
        np.testing.assert_allclose(h5["indep_var"][:], [0.0, 1e-9, 2e-9, 3e-9])
        assert h5.attrs["quality_status"] == "ok"


def test_normalize_raw_cli_smoke(tmp_path: Path):
    raw = _write_sample_raw(tmp_path)
    out = tmp_path / "cli.h5"

    proc = subprocess.run(
        [
            sys.executable,
            "tools/normalize_raw.py",
            "--input",
            str(raw),
            "--output",
            str(out),
            "--case-id",
            "cli_case",
            "--meta",
            "corner=tt",
        ],
        cwd=Path(__file__).resolve().parents[1],
        check=True,
        capture_output=True,
        text=True,
    )

    assert out.exists()
    assert "cli.h5" in proc.stdout

    with h5py.File(out, "r") as h5:
        assert h5.attrs["case_id"] == "cli_case"
        assert h5.attrs["meta_corner"] == "tt"


def test_convert_all_existing_fixture_raw_files(tmp_path: Path):
    repo = Path(__file__).resolve().parents[1]
    raw_files = sorted(repo.glob("outputs/raw/**/*.raw"))

    # If no fixtures exist yet, we still validate conversion path using synthetic RAW.
    if not raw_files:
        raw_files = [_write_sample_raw(tmp_path)]

    for i, raw in enumerate(raw_files):
        h5_out = tmp_path / f"fixture_{i}.h5"
        normalize_raw_to_hdf5(raw, h5_out, case_id=raw.stem)
        with h5py.File(h5_out, "r") as h5:
            assert h5["vectors"].shape[0] > 0
            assert h5["vectors"].shape[1] >= 2
            assert h5["indep_var"].shape[0] == h5["vectors"].shape[0]
