#!/usr/bin/env python3

import argparse
import json
from pathlib import Path

import h5py
import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def read_signal(h5_path: Path, key: str) -> np.ndarray:
    with h5py.File(h5_path, "r") as f:
        return np.array(f["signals"][key])


def main() -> int:
    parser = argparse.ArgumentParser(description="Plot OTA5T DC bench results from HDF5 files.")
    parser.add_argument("run_dir", help="Run directory containing normalized HDF5 outputs")
    args = parser.parse_args()

    run_dir = Path(args.run_dir).resolve()
    iv_h5 = run_dir / "tb_dc_iv_transfer.spice.raw.h5"
    unity_h5 = run_dir / "tb_dc_unity_rr_sweep.spice.raw.h5"

    if not iv_h5.exists() or not unity_h5.exists():
        missing = [str(p) for p in [iv_h5, unity_h5] if not p.exists()]
        raise FileNotFoundError(f"Missing required file(s): {', '.join(missing)}")

    vinp = read_signal(iv_h5, "V(INP)")
    vinn = read_signal(iv_h5, "V(INN)")
    iload = read_signal(iv_h5, "I(V_VSRC_LOAD)")
    vdiff = vinp - vinn
    iout = -iload
    gm = np.gradient(iout, vdiff)

    vin = read_signal(unity_h5, "V(INP)")
    vout = read_signal(unity_h5, "V(OUT_FB)")
    err = vout - vin

    metrics = {
        "iv_iout_uA_min": float(np.min(iout) * 1e6),
        "iv_iout_uA_max": float(np.max(iout) * 1e6),
        "iv_iout_at_vdiff0_uA": float(np.interp(0.0, vdiff, iout) * 1e6),
        "iv_gm_at_vdiff0_uS": float(np.interp(0.0, vdiff, gm) * 1e6),
        "unity_vout_at_vin0_V": float(vout[0]),
        "unity_vout_at_vinmax_V": float(vout[-1]),
        "unity_max_abs_error_mV": float(np.max(np.abs(err)) * 1e3),
    }

    idx = np.where(np.signbit(iout[:-1]) != np.signbit(iout[1:]))[0]
    if len(idx) > 0:
        i = int(idx[0])
        x0, x1 = vdiff[i], vdiff[i + 1]
        y0, y1 = iout[i], iout[i + 1]
        metrics["iv_zero_cross_vdiff_mV"] = float((x0 - y0 * (x1 - x0) / (y1 - y0)) * 1e3)

    (run_dir / "metrics_ota5t_dc.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    plt.figure(figsize=(6, 4))
    plt.plot(vdiff, iout * 1e6, lw=2)
    plt.axvline(0, color="k", ls="--", lw=1)
    plt.axhline(0, color="k", ls="--", lw=1)
    plt.xlabel("Vdiff = Vinp - Vinn (V)")
    plt.ylabel("Output current into load (uA)")
    plt.title("OTA5T Differential I-V (Vout fixed at 1.65 V)")
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(run_dir / "plot_iv_transfer.png", dpi=180)
    plt.close()

    plt.figure(figsize=(6, 4))
    plt.plot(vdiff, gm * 1e6, lw=2)
    plt.axvline(0, color="k", ls="--", lw=1)
    plt.xlabel("Vdiff = Vinp - Vinn (V)")
    plt.ylabel("dIout/dVdiff (uS)")
    plt.title("OTA5T Large-Signal Transconductance")
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(run_dir / "plot_gm_vs_vdiff.png", dpi=180)
    plt.close()

    plt.figure(figsize=(6, 4))
    plt.plot(vin, vout, lw=2, label="Vout")
    plt.plot(vin, vin, "k--", lw=1.2, label="Ideal Vout=Vin")
    plt.xlabel("Vin (V)")
    plt.ylabel("Vout (V)")
    plt.title("OTA5T Unity-Gain DC Rail-to-Rail Sweep")
    plt.legend(frameon=False)
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(run_dir / "plot_unity_transfer.png", dpi=180)
    plt.close()

    plt.figure(figsize=(6, 4))
    plt.plot(vin, err * 1e3, lw=2)
    plt.axhline(0, color="k", ls="--", lw=1)
    plt.xlabel("Vin (V)")
    plt.ylabel("Vout - Vin (mV)")
    plt.title("Unity-Gain Tracking Error vs Input")
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(run_dir / "plot_unity_error.png", dpi=180)
    plt.close()

    print(f"wrote plots and metrics in {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
