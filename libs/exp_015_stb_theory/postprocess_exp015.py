#!/usr/bin/env python3

import argparse
import sys
from pathlib import Path

import numpy as np


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from analysis.tools.xyce.io_helpers import load_frequency, load_signal, require_files
from analysis.tools.xyce.metrics_helpers import combine_tian, max_relative_error, unity_cross_hz
from analysis.tools.xyce.plot_helpers import save_bar_comparison, save_bode_magnitude_overlay, save_phase_overlay
from analysis.tools.xyce.report_helpers import write_json, write_markdown_lines


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate exp_015 summary plots and a quick Markdown report.")
    parser.add_argument("run_dir", help="Run directory containing exp_015 DC/AC outputs")
    parser.add_argument("--gm", type=float, required=True)
    parser.add_argument("--go", type=float, required=True)
    parser.add_argument("--gi", type=float, required=True)
    parser.add_argument("--cout", type=float, required=True)
    parser.add_argument("--cin", type=float, required=True)
    parser.add_argument("--ro", type=float, required=True)
    parser.add_argument("--ri", type=float, required=True)
    args = parser.parse_args()

    run_dir = Path(args.run_dir).resolve()

    dc_series_h5 = run_dir / "tb_dc_middlebrook_series.spice.raw.h5"
    dc_shunt_h5 = run_dir / "tb_dc_middlebrook_shunt.spice.raw.h5"
    ac_series_h5 = run_dir / "tb_ac_middlebrook_series.spice.raw.h5"
    ac_shunt_h5 = run_dir / "tb_ac_middlebrook_shunt.spice.raw.h5"
    require_files([dc_series_h5, dc_shunt_h5, ac_series_h5, ac_shunt_h5])

    gm = float(args.gm)
    go = float(args.go)
    gi = float(args.gi)
    cout = float(args.cout)
    cin = float(args.cin)

    # DC extraction
    vr_dc = float(np.real(load_signal(dc_series_h5, "V(OUT_SIDE)")[-1]))
    vf_dc = float(np.real(load_signal(dc_series_h5, "V(INN_SIDE)")[-1]))
    tv_dc_meas = -vr_dc / vf_dc
    tv_dc_theory = (gm + gi) / go

    iout_dc = float(np.real(load_signal(dc_shunt_h5, "I(V_VS_OUT)")[-1]))
    iin_dc = float(np.real(load_signal(dc_shunt_h5, "I(V_VS_IN)")[-1]))
    ti_dc_meas = iout_dc / iin_dc
    ti_dc_theory = (go + gm) / gi

    t_dc_meas = float(np.real(combine_tian(np.array([tv_dc_meas]), np.array([ti_dc_meas]))[0]))
    t_dc_theory = gm / (go + gi)

    # AC extraction
    f = load_frequency(ac_series_h5)
    vr_ac = load_signal(ac_series_h5, "V(OUT_SIDE)")
    vf_ac = load_signal(ac_series_h5, "V(INN_SIDE)")
    tv_ac_meas = -vr_ac / vf_ac

    iout_ac = load_signal(ac_shunt_h5, "I(V_VS_OUT)")
    iin_ac = load_signal(ac_shunt_h5, "I(V_VS_IN)")
    ti_ac_meas = iout_ac / iin_ac

    t_ac_meas = combine_tian(tv_ac_meas, ti_ac_meas)

    s = 1j * 2.0 * np.pi * f
    go_s = go + s * cout
    gi_s = gi + s * cin
    tv_ac_theory = (gm + gi_s) / go_s
    ti_ac_theory = (go_s + gm) / gi_s
    t_ac_theory = gm / (go_s + gi_s)

    max_err_tv = max_relative_error(tv_ac_meas, tv_ac_theory)
    max_err_ti = max_relative_error(ti_ac_meas, ti_ac_theory)
    max_err_t = max_relative_error(t_ac_meas, t_ac_theory)

    ugb_meas = unity_cross_hz(f, t_ac_meas)
    ugb_theory = unity_cross_hz(f, t_ac_theory)

    save_bode_magnitude_overlay(
        f,
        [
            (tv_ac_meas, "|Tv| measured", "-", 2.0),
            (tv_ac_theory, "|Tv| theory", "--", 1.6),
            (ti_ac_meas, "|Ti| measured", "-", 2.0),
            (ti_ac_theory, "|Ti| theory", "--", 1.6),
            (t_ac_meas, "|T| measured", "-", 2.4),
            (t_ac_theory, "|T| theory", "--", 2.0),
        ],
        out_path=run_dir / "plot_exp015_ac_magnitudes.png",
        title="EXP-015 AC Two-Pass vs Theory",
        legend_ncol=2,
    )

    save_phase_overlay(
        f,
        [
            (t_ac_meas, "phase(T) measured", "-", 2.2),
            (t_ac_theory, "phase(T) theory", "--", 1.8),
        ],
        out_path=run_dir / "plot_exp015_t_phase.png",
        title="EXP-015 Loop Gain Phase",
    )

    save_bar_comparison(
        labels=["Tv", "Ti", "T"],
        measured=[tv_dc_meas, ti_dc_meas, t_dc_meas],
        theory=[tv_dc_theory, ti_dc_theory, t_dc_theory],
        out_path=run_dir / "plot_exp015_dc_summary.png",
        title="EXP-015 DC Two-Pass Check",
    )

    summary = {
        "parameters": {
            "gm_S": gm,
            "go_S": go,
            "gi_S": gi,
            "cout_F": cout,
            "cin_F": cin,
            "ro_ohm": float(args.ro),
            "ri_ohm": float(args.ri),
        },
        "dc": {
            "Tv_measured": tv_dc_meas,
            "Tv_theory": tv_dc_theory,
            "Ti_measured": ti_dc_meas,
            "Ti_theory": ti_dc_theory,
            "T_measured": t_dc_meas,
            "T_theory": t_dc_theory,
        },
        "ac": {
            "ugb_T_measured_Hz": ugb_meas,
            "ugb_T_theory_Hz": ugb_theory,
            "max_rel_err_Tv": max_err_tv,
            "max_rel_err_Ti": max_err_ti,
            "max_rel_err_T": max_err_t,
        },
        "plots": {
            "ac_magnitudes": "plot_exp015_ac_magnitudes.png",
            "t_phase": "plot_exp015_t_phase.png",
            "dc_summary": "plot_exp015_dc_summary.png",
        },
    }
    summary_path = run_dir / "summary_exp015.json"
    write_json(summary_path, summary)

    report_lines = [
        "# EXP-015 Reproduction Summary",
        "",
        f"- run_dir: `{run_dir}`",
        f"- gm/go/gi: `{gm}` / `{go}` / `{gi}` S",
        f"- cin/cout: `{cin}` / `{cout}` F",
        "",
        "## DC",
        f"- Tv measured/theory: `{tv_dc_meas:.12g}` / `{tv_dc_theory:.12g}`",
        f"- Ti measured/theory: `{ti_dc_meas:.12g}` / `{ti_dc_theory:.12g}`",
        f"- T measured/theory: `{t_dc_meas:.12g}` / `{t_dc_theory:.12g}`",
        "",
        "## AC",
        f"- UGB(T) measured/theory [Hz]: `{ugb_meas}` / `{ugb_theory}`",
        f"- max rel err Tv/Ti/T: `{max_err_tv:.3e}` / `{max_err_ti:.3e}` / `{max_err_t:.3e}`",
        "",
        "## Plots",
        "- `plot_exp015_ac_magnitudes.png`",
        "- `plot_exp015_t_phase.png`",
        "- `plot_exp015_dc_summary.png`",
    ]
    write_markdown_lines(run_dir / "summary_exp015.md", report_lines)

    print(f"wrote {summary_path}")
    print(f"wrote {run_dir / 'summary_exp015.md'}")
    print(f"wrote plots under {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
