#!/usr/bin/env python3
"""Analyze two-pass (AC1/AC2) Middlebrook observables for GM validation benches.

Formulas used here follow current bench wiring/sign conventions:

- AC1 simulation return ratio (existing scratchpad expression):
  T_ac1 = -V(OUT_SIDE) / V(INN_SIDE) - 1

- AC1 pure series quantity (for reference):
  T_series = -Vtest / V(INN_SIDE)
  where Vtest = V(OUT_SIDE) - V(INN_SIDE)

- AC2 current return ratio (per KCL):
  I_dut = -( I(V_VSENSE) + I(V_VSHORT) )
  R_current = I(V_VSHORT) / I_dut

- Combined equation (user-provided form):
  1/(1+T) = 1/(1+Tv) + 1/(1+Ti)
  -> T = 1 / ( 1/(1+Tv) + 1/(1+Ti) ) - 1

Where this script reports two Ti conventions:
- Ti_user = I(V_VSHORT)/I_dut
- Ti_inverse = I_dut/I(V_VSHORT) = 1/Ti_user

This script reports these curves and extracted |.|=1 crossing frequencies.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import h5py
import numpy as np


def _load_dataset(path: Path, key: str) -> np.ndarray:
    with h5py.File(path, "r") as handle:
        return np.array(handle[key])


def _extract_ugb(freq: np.ndarray, response: np.ndarray) -> float | None:
    mag = np.abs(response)
    idx = np.where((mag[:-1] >= 1.0) & (mag[1:] < 1.0))[0]
    if idx.size == 0:
        return None

    i = int(idx[0])
    f1 = float(freq[i])
    f2 = float(freq[i + 1])
    m1 = float(mag[i])
    m2 = float(mag[i + 1])
    if m1 <= 0 or m2 <= 0 or f1 <= 0 or f2 <= 0:
        return f1

    x1 = np.log10(f1)
    x2 = np.log10(f2)
    y1 = np.log10(m1)
    y2 = np.log10(m2)
    if y1 == y2:
        return f1

    x = x1 + (0.0 - y1) * (x2 - x1) / (y2 - y1)
    return float(10.0**x)


def _complex_pair(value: complex) -> dict[str, float]:
    return {"real": float(np.real(value)), "imag": float(np.imag(value))}


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze AC1/AC2 Middlebrook observables")
    parser.add_argument("run_dir", type=Path, help="Run directory containing AC1/AC2 .raw.h5 files")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output JSON path (default: <run_dir>/metrics_middlebrook_two_pass.json)",
    )
    parser.add_argument("--gm", type=float, default=None, help="Optional GM for theory checks")
    parser.add_argument("--cin", type=float, default=None, help="Optional CIN for theory checks")
    parser.add_argument("--cload", type=float, default=None, help="Optional CLOAD for theory checks")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    run_dir = args.run_dir.resolve()

    ac1 = run_dir / "tb_ac_unity_gm_middlebrook_ac1.spice.raw.h5"
    ac2 = run_dir / "tb_ac_unity_gm_middlebrook_ac2.spice.raw.h5"
    output = args.output or (run_dir / "metrics_middlebrook_two_pass.json")

    try:
        if not ac1.exists() or not ac2.exists():
            missing = [str(p) for p in [ac1, ac2] if not p.exists()]
            raise FileNotFoundError("Missing required file(s): " + ", ".join(missing))

        freq = _load_dataset(ac1, "indep_var/FREQUENCY")
        vout_ac1 = _load_dataset(ac1, "signals/V(OUT_SIDE)")
        vinn_ac1 = _load_dataset(ac1, "signals/V(INN_SIDE)")
        vtest = vout_ac1 - vinn_ac1
        t_ac1 = -vout_ac1 / vinn_ac1 - 1.0
        t_series = -vtest / vinn_ac1

        i_vsense = _load_dataset(ac2, "signals/I(V_VSENSE)")
        i_vshort = _load_dataset(ac2, "signals/I(V_VSHORT)")
        i_dut = -(i_vsense + i_vshort)
        i_dut_safe = np.where(np.abs(i_dut) > 1e-30, i_dut, 1e-30 + 0j)
        r_current = i_vshort / i_dut_safe
        r_current_safe = np.where(np.abs(r_current) > 1e-30, r_current, 1e-30 + 0j)
        ti_inverse = 1.0 / r_current_safe

        t_combined_user = 1.0 / (1.0 / (1.0 + t_ac1) + 1.0 / (1.0 + r_current)) - 1.0
        t_combined_inverse = 1.0 / (1.0 / (1.0 + t_ac1) + 1.0 / (1.0 + ti_inverse)) - 1.0

        theory = {}
        if args.gm is not None and args.cload is not None:
            theory["ugb_cload_only_Hz"] = float(args.gm / (2.0 * np.pi * args.cload))
        if args.gm is not None and args.cload is not None and args.cin is not None:
            theory["ugb_cin_plus_cload_Hz"] = float(args.gm / (2.0 * np.pi * (args.cin + args.cload)))

        metrics = {
            "formula_ac1": "T_ac1 = -V(OUT_SIDE)/V(INN_SIDE) - 1",
            "formula_series": "T_series = -(V(OUT_SIDE)-V(INN_SIDE))/V(INN_SIDE)",
            "formula_kcl": "I_dut = -(I(V_VSENSE)+I(V_VSHORT))",
            "formula_current": "Ti_user = I(V_VSHORT)/I_dut",
            "formula_combined": "T = 1/(1/(1+Tv)+1/(1+Ti)) - 1",
            "f_start_Hz": float(freq[0]),
            "f_stop_Hz": float(freq[-1]),
            "ugb_ac1_Hz": _extract_ugb(freq, t_ac1),
            "ugb_series_Hz": _extract_ugb(freq, t_series),
            "ugb_combined_ti_user_Hz": _extract_ugb(freq, t_combined_user),
            "ugb_combined_ti_inverse_Hz": _extract_ugb(freq, t_combined_inverse),
            "r_current_1Hz": _complex_pair(r_current[0]),
            "r_current_1e8Hz": _complex_pair(r_current[int(np.argmin(np.abs(freq - 1.0e8)))]),
            "ti_inverse_1Hz": _complex_pair(ti_inverse[0]),
            "ti_inverse_1e8Hz": _complex_pair(ti_inverse[int(np.argmin(np.abs(freq - 1.0e8)))]),
            "i_dut_1Hz": _complex_pair(i_dut[0]),
            "i_dut_1e8Hz": _complex_pair(i_dut[int(np.argmin(np.abs(freq - 1.0e8)))]),
            "t_ac1_1Hz": _complex_pair(t_ac1[0]),
            "t_series_1Hz": _complex_pair(t_series[0]),
            "t_combined_ti_user_1Hz": _complex_pair(t_combined_user[0]),
            "t_combined_ti_inverse_1Hz": _complex_pair(t_combined_inverse[0]),
            "theory": theory,
            "note": "Both Ti conventions are reported because sign/orientation conventions can invert Ti.",
        }

        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"wrote middlebrook two-pass metrics to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
