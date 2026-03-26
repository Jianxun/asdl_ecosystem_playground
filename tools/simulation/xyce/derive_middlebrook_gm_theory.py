#!/usr/bin/env python3

import argparse
import csv
import json
from pathlib import Path

import numpy as np


def unity_cross_hz(freq_hz: np.ndarray, response: np.ndarray) -> float | None:
    mag = np.abs(response)
    idx = np.where((mag[:-1] >= 1.0) & (mag[1:] < 1.0))[0]
    if len(idx) == 0:
        return None
    i = int(idx[0])
    f1 = np.log10(freq_hz[i])
    f2 = np.log10(freq_hz[i + 1])
    m1 = np.log10(max(mag[i], 1e-300))
    m2 = np.log10(max(mag[i + 1], 1e-300))
    if abs(m2 - m1) < 1e-15:
        return float(freq_hz[i])
    return float(10 ** (f1 + (0.0 - m1) * (f2 - f1) / (m2 - m1)))


def combine_tian(tv: np.ndarray, ti: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 / (1.0 + tv) + 1.0 / (1.0 + ti)) - 1.0


def main() -> int:
    parser = argparse.ArgumentParser(description="Derive closed-form Middlebrook/Tian theory for ideal gm-ro-cin follower.")
    parser.add_argument("run_dir", help="Output run directory for theory artifacts")
    parser.add_argument("--gm", type=float, default=1e-3, help="Transconductance (S)")
    parser.add_argument("--ro", type=float, default=100e3, help="Output resistance (ohm)")
    parser.add_argument("--cin", type=float, default=1e-12, help="Input-side capacitance to ground (F)")
    parser.add_argument("--cload", type=float, default=1e-12, help="Output load capacitance to ground (F)")
    parser.add_argument("--f-start", type=float, default=1.0, help="Start frequency (Hz)")
    parser.add_argument("--f-stop", type=float, default=1e11, help="Stop frequency (Hz)")
    parser.add_argument("--num-points", type=int, default=4000, help="Number of log-spaced points")
    args = parser.parse_args()

    run_dir = Path(args.run_dir).resolve()
    run_dir.mkdir(parents=True, exist_ok=True)

    gm = float(args.gm)
    ro = float(args.ro)
    cin = float(args.cin)
    cload = float(args.cload)
    go = 1.0 / ro

    f = np.logspace(np.log10(args.f_start), np.log10(args.f_stop), int(args.num_points))
    s = 1j * 2.0 * np.pi * f

    y_out = go + s * cload
    y_in = s * cin
    den_closed = gm + go + s * (cin + cload)

    h_closed = gm / den_closed
    t_true = gm / (go + s * (cin + cload))

    tv = (gm + y_in) / y_out
    tv_legacy = tv - 1.0
    ti = (gm + y_out) / y_in

    t_combined = combine_tian(tv, ti)
    t_combined_legacy = combine_tian(tv_legacy, ti)

    f_target = gm / (2.0 * np.pi * (cin + cload))
    f_target_ro = (gm + go) / (2.0 * np.pi * (cin + cload))

    metrics = {
        "model": "ideal gm-ro-cin unity follower (input capacitor to ground)",
        "parameters": {
            "gm_S": gm,
            "ro_ohm": ro,
            "go_S": go,
            "cin_F": cin,
            "cload_F": cload,
        },
        "equations": {
            "closed_loop_transfer": "H(s)=gm/(gm+go+s*(cin+cload))",
            "loop_gain_true": "T_true(s)=gm/(go+s*(cin+cload))",
            "tv_canonical": "Tv(s)=-(Vr/Vf)=(gm+s*cin)/(go+s*cload)",
            "tv_legacy": "Tv_legacy(s)=-(Vr/Vf)-1",
            "ti_canonical": "Ti(s)=-(Ir/If)=(gm+go+s*cload)/(s*cin)",
            "combine": "1/(1+T)=1/(1+Tv)+1/(1+Ti)",
        },
        "unity_crossings_hz": {
            "T_true": unity_cross_hz(f, t_true),
            "Tv_canonical": unity_cross_hz(f, tv),
            "Tv_legacy": unity_cross_hz(f, tv_legacy),
            "Ti_canonical": unity_cross_hz(f, ti),
            "T_combined_from_canonical": unity_cross_hz(f, t_combined),
            "T_combined_from_legacy_tv": unity_cross_hz(f, t_combined_legacy),
        },
        "references_hz": {
            "gm_over_2pi_csum": f_target,
            "(gm+go)_over_2pi_csum": f_target_ro,
        },
        "identity_checks": {
            "max_abs_error_combined_vs_true": float(np.max(np.abs(t_combined - t_true))),
            "max_abs_error_legacy_combined_vs_true": float(np.max(np.abs(t_combined_legacy - t_true))),
        },
    }

    metrics_path = run_dir / "metrics_middlebrook_theory.json"
    metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    csv_path = run_dir / "curves_middlebrook_theory.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f_csv:
        writer = csv.writer(f_csv)
        writer.writerow(
            [
                "freq_hz",
                "mag_H_closed",
                "mag_T_true",
                "mag_Tv_canonical",
                "mag_Tv_legacy",
                "mag_Ti_canonical",
                "mag_T_combined_canonical",
                "mag_T_combined_legacy",
            ]
        )
        for i in range(len(f)):
            writer.writerow(
                [
                    float(f[i]),
                    float(np.abs(h_closed[i])),
                    float(np.abs(t_true[i])),
                    float(np.abs(tv[i])),
                    float(np.abs(tv_legacy[i])),
                    float(np.abs(ti[i])),
                    float(np.abs(t_combined[i])),
                    float(np.abs(t_combined_legacy[i])),
                ]
            )

    print(f"wrote theory metrics: {metrics_path}")
    print(f"wrote theory curves: {csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
