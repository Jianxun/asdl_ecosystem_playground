#!/usr/bin/env python3
"""Extract Middlebrook voltage/current return ratios from AC1/AC2 runs.

Definitions implemented (as requested):

  Tv = -(Vr / Vf)
  Ti = -(Ir / If)
  1 + T = Tv + Ti

with the default signal mapping for exp_014 benches:

  Vr = V(OUT_SIDE)          (AC1)
  Vf = V(INN_SIDE)          (AC1)
  Ir = I(V_VSHORT)          (AC2)
  If = I_dut                (AC2), from KCL:
       I_dut = -( I(V_VSENSE) + I(V_VSHORT) )

All ratios are complex-valued AC quantities.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import h5py
import numpy as np


def _load(path: Path, key: str) -> np.ndarray:
    with h5py.File(path, "r") as handle:
        return np.array(handle[key])


def _safe_div(num: np.ndarray, den: np.ndarray, eps: float = 1e-30) -> np.ndarray:
    den_safe = np.where(np.abs(den) > eps, den, eps + 0j)
    return num / den_safe


def _complex_obj(x: complex) -> dict[str, float]:
    return {"real": float(np.real(x)), "imag": float(np.imag(x))}


def _extract_crossing(freq: np.ndarray, y: np.ndarray, target: float = 1.0) -> float | None:
    mag = np.abs(y)
    idx = np.where((mag[:-1] >= target) & (mag[1:] < target))[0]
    if idx.size == 0:
        return None

    i = int(idx[0])
    f1, f2 = float(freq[i]), float(freq[i + 1])
    m1, m2 = float(mag[i]), float(mag[i + 1])
    if f1 <= 0 or f2 <= 0 or m1 <= 0 or m2 <= 0:
        return f1

    x1, x2 = np.log10(f1), np.log10(f2)
    y1, y2 = np.log10(m1), np.log10(m2)
    if y1 == y2:
        return f1

    x = x1 + (np.log10(target) - y1) * (x2 - x1) / (y2 - y1)
    return float(10.0**x)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract Tv, Ti, and T from AC1/AC2 HDF5 outputs")
    parser.add_argument("run_dir", type=Path, help="Run directory containing AC1/AC2 .raw.h5 files")
    parser.add_argument(
        "--ac1",
        type=str,
        default="tb_ac_unity_gm_middlebrook_ac1.spice.raw.h5",
        help="AC1 HDF5 filename under run_dir",
    )
    parser.add_argument(
        "--ac2",
        type=str,
        default="tb_ac_unity_gm_middlebrook_ac2.spice.raw.h5",
        help="AC2 HDF5 filename under run_dir",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output JSON path (default: <run_dir>/metrics_middlebrook_tv_ti.json)",
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=None,
        help="Optional output CSV path for per-frequency complex curves",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    run_dir = args.run_dir.resolve()
    ac1 = run_dir / args.ac1
    ac2 = run_dir / args.ac2
    out_json = args.output or (run_dir / "metrics_middlebrook_tv_ti.json")

    try:
        if not ac1.exists() or not ac2.exists():
            missing = [str(p) for p in [ac1, ac2] if not p.exists()]
            raise FileNotFoundError("Missing required file(s): " + ", ".join(missing))

        freq = _load(ac1, "indep_var/FREQUENCY")
        vr = _load(ac1, "signals/V(OUT_SIDE)")
        vf = _load(ac1, "signals/V(INN_SIDE)")

        i_vsense = _load(ac2, "signals/I(V_VSENSE)")
        ir = _load(ac2, "signals/I(V_VSHORT)")
        i_dut = -(i_vsense + ir)
        i_fwd = i_dut

        tv = -_safe_div(vr, vf)
        ti = -_safe_div(ir, i_fwd)
        one_plus_t = tv + ti
        t = one_plus_t - 1.0

        i_1e8 = int(np.argmin(np.abs(freq - 1.0e8)))
        metrics = {
            "formula_tv": "Tv = -(Vr/Vf)",
            "formula_ti": "Ti = -(Ir/If)",
            "formula_overall": "1+T = Tv + Ti",
            "signal_map": {
                "Vr": "V(OUT_SIDE) from AC1",
                "Vf": "V(INN_SIDE) from AC1",
                "Ir": "I(V_VSHORT) from AC2",
                "If": "I_dut from AC2, where I_dut = -(I(V_VSENSE)+I(V_VSHORT))",
            },
            "f_start_Hz": float(freq[0]),
            "f_stop_Hz": float(freq[-1]),
            "unity_crossings": {
                "Tv": _extract_crossing(freq, tv, 1.0),
                "Ti": _extract_crossing(freq, ti, 1.0),
                "T": _extract_crossing(freq, t, 1.0),
                "1_plus_T": _extract_crossing(freq, one_plus_t, 1.0),
            },
            "samples": {
                "Tv_1Hz": _complex_obj(tv[0]),
                "Tv_1e8Hz": _complex_obj(tv[i_1e8]),
                "Ti_1Hz": _complex_obj(ti[0]),
                "Ti_1e8Hz": _complex_obj(ti[i_1e8]),
                "T_1Hz": _complex_obj(t[0]),
                "T_1e8Hz": _complex_obj(t[i_1e8]),
                "I_dut_1Hz": _complex_obj(i_dut[0]),
                "I_dut_1e8Hz": _complex_obj(i_dut[i_1e8]),
            },
        }

        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

        if args.csv is not None:
            args.csv.parent.mkdir(parents=True, exist_ok=True)
            with args.csv.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.writer(handle)
                writer.writerow(
                    [
                        "freq_Hz",
                        "Tv_real",
                        "Tv_imag",
                        "Ti_real",
                        "Ti_imag",
                        "T_real",
                        "T_imag",
                        "I_dut_real",
                        "I_dut_imag",
                    ]
                )
                for i, f_hz in enumerate(freq):
                    writer.writerow(
                        [
                            float(f_hz),
                            float(np.real(tv[i])),
                            float(np.imag(tv[i])),
                            float(np.real(ti[i])),
                            float(np.imag(ti[i])),
                            float(np.real(t[i])),
                            float(np.imag(t[i])),
                            float(np.real(i_dut[i])),
                            float(np.imag(i_dut[i])),
                        ]
                    )
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    msg = f"wrote Tv/Ti metrics to {out_json}"
    if args.csv is not None:
        msg += f" and curves to {args.csv}"
    print(msg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
