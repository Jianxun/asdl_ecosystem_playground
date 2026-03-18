#!/usr/bin/env python3

import argparse
import json
from pathlib import Path

import h5py
import numpy as np


def resolve_signal_key(h5_path: Path, wanted: str) -> str:
    with h5py.File(h5_path, "r") as f:
        keys = list(f["signals"].keys())
    wanted_u = wanted.upper()
    for k in keys:
        if k.upper() == wanted_u:
            return k
    raise KeyError(f"Signal '{wanted}' not found in {h5_path}. Available: {keys}")


def load_signal(h5_path: Path, wanted: str) -> np.ndarray:
    key = resolve_signal_key(h5_path, wanted)
    with h5py.File(h5_path, "r") as f:
        return np.array(f[f"signals/{key}"])


def load_freq(h5_path: Path) -> np.ndarray:
    with h5py.File(h5_path, "r") as f:
        return np.array(f["indep_var/FREQUENCY"])


def unity_cross_hz(freq_hz: np.ndarray, response: np.ndarray) -> float | None:
    mag = np.abs(response)
    idx = np.where((mag[:-1] >= 1.0) & (mag[1:] < 1.0))[0]
    if len(idx) == 0:
        return None
    i = int(idx[0])
    lf1 = np.log10(freq_hz[i])
    lf2 = np.log10(freq_hz[i + 1])
    lm1 = np.log10(max(mag[i], 1e-300))
    lm2 = np.log10(max(mag[i + 1], 1e-300))
    if abs(lm2 - lm1) < 1e-15:
        return float(freq_hz[i])
    return float(10 ** (lf1 + (0.0 - lm1) * (lf2 - lf1) / (lm2 - lm1)))


def combine_tian(tv: np.ndarray, ti: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 / (1.0 + tv) + 1.0 / (1.0 + ti)) - 1.0


def pick_at(freq_hz: np.ndarray, arr: np.ndarray, target_hz: float) -> complex:
    i = int(np.argmin(np.abs(freq_hz - target_hz)))
    return complex(arr[i])


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze AC two-pass Middlebrook/Tian runs for generic Gm-Go-Gi RC fixture.")
    parser.add_argument("run_dir", help="Run directory containing series/shunt .raw.h5 outputs")
    parser.add_argument("--gm", type=float, required=True, help="Gm in siemens")
    parser.add_argument("--go", type=float, required=True, help="Go (conductance) in siemens")
    parser.add_argument("--gi", type=float, required=True, help="Gi (conductance) in siemens")
    parser.add_argument("--cout", type=float, default=0.0, help="Cout in farads")
    parser.add_argument("--cin", type=float, default=0.0, help="Cin in farads")
    args = parser.parse_args()

    run_dir = Path(args.run_dir).resolve()
    series_h5 = run_dir / "tb_ac_middlebrook_series.spice.raw.h5"
    shunt_h5 = run_dir / "tb_ac_middlebrook_shunt.spice.raw.h5"

    if not series_h5.exists() or not shunt_h5.exists():
        missing = [str(p) for p in [series_h5, shunt_h5] if not p.exists()]
        raise FileNotFoundError(f"Missing required file(s): {', '.join(missing)}")

    f = load_freq(series_h5)

    vr = load_signal(series_h5, "V(OUT_SIDE)")
    vf = load_signal(series_h5, "V(INN_SIDE)")
    tv_meas = -vr / vf

    i_out = load_signal(shunt_h5, "I(V_VS_OUT)")
    i_in = load_signal(shunt_h5, "I(V_VS_IN)")
    ti_meas = i_out / i_in

    t_meas = combine_tian(tv_meas, ti_meas)

    gm = float(args.gm)
    go = float(args.go)
    gi = float(args.gi)
    cout = float(args.cout)
    cin = float(args.cin)

    s = 1j * 2.0 * np.pi * f
    go_s = go + s * cout
    gi_s = gi + s * cin

    tv_theory = (gm + gi_s) / go_s
    ti_theory = (go_s + gm) / gi_s
    t_theory = gm / (go_s + gi_s)
    t_theory_combined = combine_tian(tv_theory, ti_theory)

    eps = 1e-30
    tv_rel_err = np.abs(tv_meas - tv_theory) / np.maximum(np.abs(tv_theory), eps)
    ti_rel_err = np.abs(ti_meas - ti_theory) / np.maximum(np.abs(ti_theory), eps)
    t_rel_err = np.abs(t_meas - t_theory) / np.maximum(np.abs(t_theory), eps)

    metrics = {
        "parameters": {
            "gm_S": gm,
            "go_S": go,
            "gi_S": gi,
            "cout_F": cout,
            "cin_F": cin,
        },
        "equations": {
            "Tv": "-(Vr/Vf)",
            "Ti": "I(V_VS_OUT)/I(V_VS_IN)",
            "combine": "1/(1+T)=1/(1+Tv)+1/(1+Ti)",
            "tv_theory": "(Gm+Gi(s))/Go(s)",
            "ti_theory": "(Go(s)+Gm)/Gi(s)",
            "t_theory": "Gm/(Go(s)+Gi(s))",
        },
        "unity_crossings_hz": {
            "Tv_measured": unity_cross_hz(f, tv_meas),
            "Ti_measured": unity_cross_hz(f, ti_meas),
            "T_measured": unity_cross_hz(f, t_meas),
            "T_theory": unity_cross_hz(f, t_theory),
        },
        "error_summary": {
            "max_rel_err_Tv": float(np.max(tv_rel_err)),
            "max_rel_err_Ti": float(np.max(ti_rel_err)),
            "max_rel_err_T": float(np.max(t_rel_err)),
            "max_abs_err_T_theory_identity": float(np.max(np.abs(t_theory_combined - t_theory))),
        },
        "samples": {
            "f_1Hz": {
                "Tv_measured": {"real": float(np.real(pick_at(f, tv_meas, 1.0))), "imag": float(np.imag(pick_at(f, tv_meas, 1.0)))},
                "Tv_theory": {"real": float(np.real(pick_at(f, tv_theory, 1.0))), "imag": float(np.imag(pick_at(f, tv_theory, 1.0)))},
                "Ti_measured": {"real": float(np.real(pick_at(f, ti_meas, 1.0))), "imag": float(np.imag(pick_at(f, ti_meas, 1.0)))},
                "Ti_theory": {"real": float(np.real(pick_at(f, ti_theory, 1.0))), "imag": float(np.imag(pick_at(f, ti_theory, 1.0)))},
                "T_measured": {"real": float(np.real(pick_at(f, t_meas, 1.0))), "imag": float(np.imag(pick_at(f, t_meas, 1.0)))},
                "T_theory": {"real": float(np.real(pick_at(f, t_theory, 1.0))), "imag": float(np.imag(pick_at(f, t_theory, 1.0)))},
            },
            "f_1e8Hz": {
                "Tv_measured": {"real": float(np.real(pick_at(f, tv_meas, 1e8))), "imag": float(np.imag(pick_at(f, tv_meas, 1e8)))},
                "Tv_theory": {"real": float(np.real(pick_at(f, tv_theory, 1e8))), "imag": float(np.imag(pick_at(f, tv_theory, 1e8)))},
                "Ti_measured": {"real": float(np.real(pick_at(f, ti_meas, 1e8))), "imag": float(np.imag(pick_at(f, ti_meas, 1e8)))},
                "Ti_theory": {"real": float(np.real(pick_at(f, ti_theory, 1e8))), "imag": float(np.imag(pick_at(f, ti_theory, 1e8)))},
                "T_measured": {"real": float(np.real(pick_at(f, t_meas, 1e8))), "imag": float(np.imag(pick_at(f, t_meas, 1e8)))},
                "T_theory": {"real": float(np.real(pick_at(f, t_theory, 1e8))), "imag": float(np.imag(pick_at(f, t_theory, 1e8)))},
            },
        },
    }

    out_path = run_dir / "metrics_middlebrook_ac_two_pass.json"
    out_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
