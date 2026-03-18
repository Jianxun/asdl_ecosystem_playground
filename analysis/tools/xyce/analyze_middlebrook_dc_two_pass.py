#!/usr/bin/env python3

import argparse
import json
from pathlib import Path

import h5py
import numpy as np


def load_signal(path: Path, key: str) -> np.ndarray:
    with h5py.File(path, "r") as f:
        if key.startswith("signals/"):
            return np.array(f[key])
        return np.array(f[f"signals/{key}"])


def scalar(x: np.ndarray) -> float:
    if x.size == 0:
        raise ValueError("empty signal array")
    return float(np.real(np.ravel(x)[-1]))


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze resistive two-pass Middlebrook/Tian DC runs.")
    parser.add_argument("run_dir", help="Run directory containing series/shunt .raw.h5 outputs")
    parser.add_argument("--gm", type=float, required=True, help="Gm in siemens")
    parser.add_argument("--go", type=float, required=True, help="Go in siemens")
    parser.add_argument("--gi", type=float, required=True, help="Gi in siemens")
    args = parser.parse_args()

    run_dir = Path(args.run_dir).resolve()
    series_h5 = run_dir / "tb_dc_middlebrook_series.spice.raw.h5"
    shunt_h5 = run_dir / "tb_dc_middlebrook_shunt.spice.raw.h5"

    if not series_h5.exists() or not shunt_h5.exists():
        missing = [str(p) for p in [series_h5, shunt_h5] if not p.exists()]
        raise FileNotFoundError(f"Missing required file(s): {', '.join(missing)}")

    vr = scalar(load_signal(series_h5, "V(OUT_SIDE)"))
    vf = scalar(load_signal(series_h5, "V(INN_SIDE)"))
    tv_meas = -vr / vf

    i_out = scalar(load_signal(shunt_h5, "I(V_VS_OUT)"))
    i_in = scalar(load_signal(shunt_h5, "I(V_VS_IN)"))
    ti_meas = i_out / i_in

    t_combined_meas = 1.0 / (1.0 / (1.0 + tv_meas) + 1.0 / (1.0 + ti_meas)) - 1.0

    gm = float(args.gm)
    go = float(args.go)
    gi = float(args.gi)

    tv_theory = (gm + gi) / go
    ti_theory = (go + gm) / gi
    t_theory = gm / (go + gi)

    t_combined_theory = 1.0 / (1.0 / (1.0 + tv_theory) + 1.0 / (1.0 + ti_theory)) - 1.0

    metrics = {
        "parameters": {"gm_S": gm, "go_S": go, "gi_S": gi},
        "series": {
            "Vr_V": vr,
            "Vf_V": vf,
            "Tv_measured": tv_meas,
            "Tv_theory": tv_theory,
            "Tv_error_pct": 100.0 * (tv_meas - tv_theory) / tv_theory,
        },
        "shunt": {
            "Iout_A": i_out,
            "Iin_A": i_in,
            "Ti_measured": ti_meas,
            "Ti_theory": ti_theory,
            "Ti_error_pct": 100.0 * (ti_meas - ti_theory) / ti_theory,
        },
        "combined": {
            "T_combined_measured": t_combined_meas,
            "T_combined_theory_from_Tv_Ti": t_combined_theory,
            "T_theory_direct": t_theory,
            "T_error_pct_vs_direct": 100.0 * (t_combined_meas - t_theory) / t_theory,
        },
    }

    out_path = run_dir / "metrics_middlebrook_dc_two_pass.json"
    out_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
