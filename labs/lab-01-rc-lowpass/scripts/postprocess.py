#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np


R_OHM = 1_000.0
C_F = 1e-9
TAU_THEORY_S = R_OHM * C_F
FC_THEORY_HZ = 1.0 / (2.0 * np.pi * TAU_THEORY_S)


def _read_csv(path: Path) -> tuple[list[str], np.ndarray]:
    with path.open("r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
    data = np.genfromtxt(path, delimiter=",", skip_header=1)
    if data.ndim == 1:
        data = data.reshape(1, -1)
    return header, data


def _col(header: list[str], table: np.ndarray, key: str) -> np.ndarray:
    idx = header.index(key)
    return table[:, idx]


def _interp_x_at_y(x: np.ndarray, y: np.ndarray, y_target: float) -> float:
    sign = np.sign(y - y_target)
    crossings = np.where(np.diff(sign) != 0)[0]
    if crossings.size == 0:
        i = int(np.argmin(np.abs(y - y_target)))
        return float(x[i])
    i0 = int(crossings[0])
    x0, x1 = x[i0], x[i0 + 1]
    y0, y1 = y[i0], y[i0 + 1]
    if np.isclose(y1, y0):
        return float(x0)
    return float(x0 + (y_target - y0) * (x1 - x0) / (y1 - y0))


def main() -> int:
    parser = argparse.ArgumentParser(description="Post-process RC low-pass lab outputs")
    parser.add_argument("--run", required=True, type=Path, help="Run folder path")
    parser.add_argument("--out", required=True, type=Path, help="Output data folder")
    args = parser.parse_args()

    run_dir = args.run.resolve()
    out_dir = args.out.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    ac_path = run_dir / "tb.spice.FD.csv"
    tran_path = run_dir / "tb_tran.spice.csv"
    if not ac_path.exists() or not tran_path.exists():
        missing = [str(p) for p in [ac_path, tran_path] if not p.exists()]
        raise FileNotFoundError(f"Missing required simulation outputs: {', '.join(missing)}")

    ac_header, ac_table = _read_csv(ac_path)
    f_hz = _col(ac_header, ac_table, "FREQ")
    vin_ac = _col(ac_header, ac_table, "Re(V(VIN))") + 1j * _col(ac_header, ac_table, "Im(V(VIN))")
    vout_ac = _col(ac_header, ac_table, "Re(V(VOUT))") + 1j * _col(ac_header, ac_table, "Im(V(VOUT))")
    gain_mag = np.abs(vout_ac / vin_ac)
    gain_db = 20.0 * np.log10(np.maximum(gain_mag, 1e-30))

    cutoff_target = 1.0 / np.sqrt(2.0)
    fc_sim_hz = _interp_x_at_y(f_hz, gain_mag, cutoff_target)

    tran_header, tran_table = _read_csv(tran_path)
    t_s = _col(tran_header, tran_table, "TIME")
    vin_t = _col(tran_header, tran_table, "V(VIN)")
    vout_t = _col(tran_header, tran_table, "V(VOUT)")

    vin_initial = float(vin_t[0])
    vin_final = float(np.mean(vin_t[-5:]))
    vin_delta = vin_final - vin_initial
    if np.isclose(vin_delta, 0.0):
        raise ValueError("Transient input did not step; cannot extract time constant")

    step_threshold = vin_initial + 0.99 * vin_delta
    step_index = int(np.argmax(vin_t >= step_threshold))
    t_step_s = float(t_s[step_index])

    vout_at_step = float(np.interp(t_step_s, t_s, vout_t))
    vout_final = float(np.mean(vout_t[-5:]))
    tau_target_v = vout_at_step + (1.0 - np.exp(-1.0)) * (vout_final - vout_at_step)
    t_tau_s = _interp_x_at_y(t_s[t_s >= t_step_s], vout_t[t_s >= t_step_s], tau_target_v)
    tau_sim_s = t_tau_s - t_step_s

    fc_error_pct = (fc_sim_hz - FC_THEORY_HZ) / FC_THEORY_HZ * 100.0
    tau_error_pct = (tau_sim_s - TAU_THEORY_S) / TAU_THEORY_S * 100.0

    metrics = {
        "theory": {
            "R_ohm": R_OHM,
            "C_f": C_F,
            "cutoff_hz": FC_THEORY_HZ,
            "tau_s": TAU_THEORY_S,
        },
        "simulation": {
            "cutoff_hz": fc_sim_hz,
            "t_step_s": t_step_s,
            "t_tau_s": t_tau_s,
            "tau_s": tau_sim_s,
        },
        "error_pct": {
            "cutoff": fc_error_pct,
            "tau": tau_error_pct,
        },
        "acceptance": {
            "cutoff_within_5pct": abs(fc_error_pct) <= 5.0,
            "tau_within_10pct": abs(tau_error_pct) <= 10.0,
        },
    }

    np.savetxt(
        out_dir / "ac_response.csv",
        np.column_stack([f_hz, gain_mag, gain_db]),
        delimiter=",",
        header="freq_hz,gain_mag,gain_db",
        comments="",
    )
    np.savetxt(
        out_dir / "transient_response.csv",
        np.column_stack([t_s, vin_t, vout_t]),
        delimiter=",",
        header="time_s,vin_v,vout_v",
        comments="",
    )

    with (out_dir / "metrics.json").open("w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    with (out_dir / "theory_vs_sim.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "theory", "simulation", "error_pct", "tolerance", "pass"])
        writer.writerow(
            [
                "cutoff_hz",
                f"{FC_THEORY_HZ:.6g}",
                f"{fc_sim_hz:.6g}",
                f"{fc_error_pct:.4f}",
                "+-5%",
                str(abs(fc_error_pct) <= 5.0),
            ]
        )
        writer.writerow(
            [
                "tau_s",
                f"{TAU_THEORY_S:.6g}",
                f"{tau_sim_s:.6g}",
                f"{tau_error_pct:.4f}",
                "+-10%",
                str(abs(tau_error_pct) <= 10.0),
            ]
        )

    print(f"wrote derived data to {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
