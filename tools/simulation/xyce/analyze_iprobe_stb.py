#!/usr/bin/env python3

import argparse
import json
from pathlib import Path

import h5py
import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def load_dataset(path: Path, key: str) -> np.ndarray:
    with h5py.File(path, "r") as f:
        return np.array(f[key])


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze STB iprobe series/shunt AC runs.")
    parser.add_argument("run_dir", help="Run directory containing tb_ac_stb_series/shunt *.raw.h5")
    args = parser.parse_args()

    run_dir = Path(args.run_dir).resolve()
    series_h5 = run_dir / "tb_ac_stb_series.spice.raw.h5"
    shunt_h5 = run_dir / "tb_ac_stb_shunt.spice.raw.h5"

    if not series_h5.exists() or not shunt_h5.exists():
        missing = [str(p) for p in [series_h5, shunt_h5] if not p.exists()]
        raise FileNotFoundError(f"Missing required file(s): {', '.join(missing)}")

    f = load_dataset(series_h5, "indep_var/FREQUENCY")

    vout_s = load_dataset(series_h5, "signals/V(OUT_FB)")
    vinn_s = load_dataset(series_h5, "signals/V(INN_FB)")
    ivser_s = load_dataset(series_h5, "signals/XPROBE/I(V_VSER)")
    vport_s = vout_s - vinn_s
    z_series = vport_s / ivser_s

    vout_h = load_dataset(shunt_h5, "signals/V(OUT_FB)")
    vinn_h = load_dataset(shunt_h5, "signals/V(INN_FB)")
    ivser_h = load_dataset(shunt_h5, "signals/XPROBE/I(V_VSER)")
    ivsense_h = load_dataset(shunt_h5, "signals/XPROBE/I(V_VSENSE)")
    vport_h = vout_h - vinn_h
    z_shunt = vport_h / ivsense_h

    metrics = {
        "note": "This script captures observables from the two STB runs. Final loop-gain reconstruction equation can be applied in a follow-up step.",
        "f_start_Hz": float(f[0]),
        "f_stop_Hz": float(f[-1]),
        "z_series_1Hz_ohm": {
            "real": float(np.real(z_series[0])),
            "imag": float(np.imag(z_series[0])),
        },
        "z_shunt_1Hz_ohm": {"real": float(np.real(z_shunt[0])), "imag": float(np.imag(z_shunt[0]))},
        "ivsense_mag_1Hz_A": float(np.abs(ivsense_h[0])),
        "ivser_shunt_mag_1Hz_A": float(np.abs(ivser_h[0])),
        "series_run": {
            "available": ["V(OUT_FB)", "V(INN_FB)", "XPROBE/I(V_VSER)"],
            "definition": "vport_s = V(OUT_FB)-V(INN_FB), iser_s = I(V_VSER)",
        },
        "shunt_run": {
            "available": ["V(OUT_FB)", "V(INN_FB)", "XPROBE/I(V_VSER)", "XPROBE/I(V_VSENSE)"],
            "definition": "vport_h = V(OUT_FB)-V(INN_FB), ishort_h = I(V_VSER), iinj_h = I(V_VSENSE)",
        },
    }

    (run_dir / "metrics_stb_iprobe.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    plt.figure(figsize=(6.5, 4.2))
    plt.semilogx(f, 20 * np.log10(np.maximum(np.abs(z_series), 1e-30)), lw=2, label="|Z_series|")
    plt.semilogx(f, 20 * np.log10(np.maximum(np.abs(z_shunt), 1e-30)), lw=2, label="|Z_shunt|")
    plt.xlabel("Frequency (Hz)")
    plt.ylabel("Magnitude (dB-ohm)")
    plt.title("IPROBE Port Impedances")
    plt.grid(alpha=0.3, which="both")
    plt.legend(frameon=False)
    plt.tight_layout()
    plt.savefig(run_dir / "plot_stb_iprobe_impedances.png", dpi=180)
    plt.close()

    plt.figure(figsize=(6.5, 4.2))
    plt.semilogx(f, 20 * np.log10(np.maximum(np.abs(ivser_s), 1e-30)), lw=2, label="|I(VSER)| series run")
    plt.semilogx(f, 20 * np.log10(np.maximum(np.abs(ivsense_h), 1e-30)), lw=2, label="|I(VSENSE)| shunt run")
    plt.semilogx(f, 20 * np.log10(np.maximum(np.abs(ivser_h), 1e-30)), lw=2, label="|I(VSER)| shunt run")
    plt.xlabel("Frequency (Hz)")
    plt.ylabel("Magnitude (dB-A)")
    plt.title("IPROBE Injection/Return Currents")
    plt.grid(alpha=0.3, which="both")
    plt.legend(frameon=False)
    plt.tight_layout()
    plt.savefig(run_dir / "plot_stb_iprobe_currents.png", dpi=180)
    plt.close()

    print(f"wrote stb analysis artifacts in {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
