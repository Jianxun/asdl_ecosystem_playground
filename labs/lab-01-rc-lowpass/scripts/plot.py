#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def _load_csv(path: Path) -> np.ndarray:
    data = np.genfromtxt(path, delimiter=",", names=True)
    if data.shape == ():
        data = np.array([data])
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate RC low-pass lab figures")
    parser.add_argument("--data", required=True, type=Path, help="Derived data directory")
    parser.add_argument("--out", required=True, type=Path, help="Figure output directory")
    args = parser.parse_args()

    data_dir = args.data.resolve()
    out_dir = args.out.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    ac = _load_csv(data_dir / "ac_response.csv")
    tr = _load_csv(data_dir / "transient_response.csv")
    metrics = json.loads((data_dir / "metrics.json").read_text(encoding="utf-8"))

    f_hz = ac["freq_hz"]
    gain_db = ac["gain_db"]
    fc_theory = float(metrics["theory"]["cutoff_hz"])
    fc_sim = float(metrics["simulation"]["cutoff_hz"])

    plt.figure(figsize=(7.0, 4.2))
    plt.semilogx(f_hz, gain_db, lw=2.0, color="#0b4f6c", label="|Vout/Vin| (sim)")
    plt.axhline(-3.0103, color="#8c8c8c", ls="--", lw=1.0, label="-3 dB reference")
    plt.axvline(fc_theory, color="#f4a259", ls=":", lw=1.5, label=f"Theory fc={fc_theory:.2f} Hz")
    plt.axvline(fc_sim, color="#d7263d", ls="-.", lw=1.5, label=f"Sim fc={fc_sim:.2f} Hz")
    plt.xlabel("Frequency (Hz)")
    plt.ylabel("Magnitude (dB)")
    plt.title("RC Low-Pass AC Magnitude Response")
    plt.grid(True, which="both", alpha=0.25)
    plt.legend(frameon=False, fontsize=8)
    plt.tight_layout()
    plt.savefig(out_dir / "fig1_ac_response.png", dpi=180)
    plt.close()

    t_s = tr["time_s"]
    vin_v = tr["vin_v"]
    vout_v = tr["vout_v"]
    t_step = float(metrics["simulation"]["t_step_s"])
    t_tau = float(metrics["simulation"]["t_tau_s"])

    plt.figure(figsize=(7.0, 4.2))
    plt.plot(t_s * 1e6, vin_v, lw=1.8, color="#d7263d", label="Vin step")
    plt.plot(t_s * 1e6, vout_v, lw=2.0, color="#0b4f6c", label="Vout")
    plt.axvline(t_step * 1e6, color="#444444", ls=":", lw=1.2, label="Step reaches 99%")
    plt.axvline(t_tau * 1e6, color="#f4a259", ls="--", lw=1.2, label="Vout at 63.2% point")
    plt.xlabel("Time (us)")
    plt.ylabel("Voltage (V)")
    plt.title("RC Step Response and Extracted Time Constant")
    plt.grid(True, alpha=0.25)
    plt.legend(frameon=False, fontsize=8)
    plt.tight_layout()
    plt.savefig(out_dir / "fig2_transient_step.png", dpi=180)
    plt.close()

    print(f"wrote figures to {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
