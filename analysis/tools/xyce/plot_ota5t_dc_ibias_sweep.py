#!/usr/bin/env python3

import argparse
import json
from pathlib import Path

import h5py
import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def load_iv(h5_path: Path):
    with h5py.File(h5_path, "r") as f:
        vinp = np.array(f["signals"]["V(INP)"])
        vinn = np.array(f["signals"]["V(INN)"])
        iload = np.array(f["signals"]["I(V_VSRC_LOAD)"])
    return vinp - vinn, -iload


def plateau_current(iout: np.ndarray, frac: float = 0.1) -> tuple[float, float]:
    n = len(iout)
    k = max(1, int(round(n * frac)))
    neg = float(np.mean(iout[:k]))
    pos = float(np.mean(iout[-k:]))
    return neg, pos


def main() -> int:
    parser = argparse.ArgumentParser(description="Plot OTA5T differential I-V versus bias current.")
    parser.add_argument("run_dir", help="Run directory containing *_ibias_*.raw.h5 outputs")
    args = parser.parse_args()

    run_dir = Path(args.run_dir).resolve()
    benches = [
        ("50uA", run_dir / "tb_dc_iv_transfer_ibias_050u.spice.raw.h5", 50e-6),
        ("100uA", run_dir / "tb_dc_iv_transfer.spice.raw.h5", 100e-6),
        ("200uA", run_dir / "tb_dc_iv_transfer_ibias_200u.spice.raw.h5", 200e-6),
    ]

    for _, p, _ in benches:
        if not p.exists():
            raise FileNotFoundError(f"Missing required file: {p}")

    summary = []

    plt.figure(figsize=(6.4, 4.2))
    for label, h5_path, ibias in benches:
        vdiff, iout = load_iv(h5_path)
        ineg, ipos = plateau_current(iout, frac=0.1)
        summary.append(
            {
                "label": label,
                "ibias_A": ibias,
                "iout_neg_plateau_uA": ineg * 1e6,
                "iout_pos_plateau_uA": ipos * 1e6,
                "iout_span_uA": (np.max(iout) - np.min(iout)) * 1e6,
            }
        )
        plt.plot(vdiff, iout * 1e6, lw=2, label=label)

    plt.axvline(0, color="k", ls="--", lw=1)
    plt.axhline(0, color="k", ls="--", lw=1)
    plt.xlabel("Vdiff = Vinp - Vinn (V)")
    plt.ylabel("Output current into load (uA)")
    plt.title("OTA5T Differential I-V vs Bias Current")
    plt.legend(frameon=False)
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(run_dir / "plot_iv_transfer_ibias_sweep.png", dpi=180)
    plt.close()

    (run_dir / "metrics_ota5t_dc_ibias_sweep.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"wrote plot and metrics in {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
