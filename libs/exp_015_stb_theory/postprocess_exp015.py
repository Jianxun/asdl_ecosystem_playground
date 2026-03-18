#!/usr/bin/env python3

import argparse
import json
from pathlib import Path

import h5py
import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt


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


def combine_tian(tv: np.ndarray, ti: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 / (1.0 + tv) + 1.0 / (1.0 + ti)) - 1.0


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
    required = [dc_series_h5, dc_shunt_h5, ac_series_h5, ac_shunt_h5]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        raise FileNotFoundError(f"Missing required file(s): {', '.join(missing)}")

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
    f = load_freq(ac_series_h5)
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

    eps = 1e-30
    max_err_tv = float(np.max(np.abs(tv_ac_meas - tv_ac_theory) / np.maximum(np.abs(tv_ac_theory), eps)))
    max_err_ti = float(np.max(np.abs(ti_ac_meas - ti_ac_theory) / np.maximum(np.abs(ti_ac_theory), eps)))
    max_err_t = float(np.max(np.abs(t_ac_meas - t_ac_theory) / np.maximum(np.abs(t_ac_theory), eps)))

    ugb_meas = unity_cross_hz(f, t_ac_meas)
    ugb_theory = unity_cross_hz(f, t_ac_theory)

    # Plot 1: AC magnitude comparisons
    plt.figure(figsize=(8.0, 5.2))
    plt.semilogx(f, 20 * np.log10(np.maximum(np.abs(tv_ac_meas), 1e-30)), lw=2, label="|Tv| measured")
    plt.semilogx(f, 20 * np.log10(np.maximum(np.abs(tv_ac_theory), 1e-30)), "--", lw=1.6, label="|Tv| theory")
    plt.semilogx(f, 20 * np.log10(np.maximum(np.abs(ti_ac_meas), 1e-30)), lw=2, label="|Ti| measured")
    plt.semilogx(f, 20 * np.log10(np.maximum(np.abs(ti_ac_theory), 1e-30)), "--", lw=1.6, label="|Ti| theory")
    plt.semilogx(f, 20 * np.log10(np.maximum(np.abs(t_ac_meas), 1e-30)), lw=2.4, label="|T| measured")
    plt.semilogx(f, 20 * np.log10(np.maximum(np.abs(t_ac_theory), 1e-30)), "--", lw=2.0, label="|T| theory")
    plt.axhline(0.0, color="k", ls=":", lw=1)
    plt.xlabel("Frequency (Hz)")
    plt.ylabel("Magnitude (dB)")
    plt.title("EXP-015 AC Two-Pass vs Theory")
    plt.grid(alpha=0.25, which="both")
    plt.legend(frameon=False, ncol=2)
    plt.tight_layout()
    plt.savefig(run_dir / "plot_exp015_ac_magnitudes.png", dpi=180)
    plt.close()

    # Plot 2: loop-gain phase
    plt.figure(figsize=(8.0, 4.6))
    plt.semilogx(f, np.unwrap(np.angle(t_ac_meas)) * 180.0 / np.pi, lw=2.2, label="phase(T) measured")
    plt.semilogx(f, np.unwrap(np.angle(t_ac_theory)) * 180.0 / np.pi, "--", lw=1.8, label="phase(T) theory")
    plt.xlabel("Frequency (Hz)")
    plt.ylabel("Phase (deg)")
    plt.title("EXP-015 Loop Gain Phase")
    plt.grid(alpha=0.25, which="both")
    plt.legend(frameon=False)
    plt.tight_layout()
    plt.savefig(run_dir / "plot_exp015_t_phase.png", dpi=180)
    plt.close()

    # Plot 3: DC bar comparison
    labels = ["Tv", "Ti", "T"]
    measured = [tv_dc_meas, ti_dc_meas, t_dc_meas]
    theory = [tv_dc_theory, ti_dc_theory, t_dc_theory]
    x = np.arange(len(labels))
    w = 0.35
    plt.figure(figsize=(6.4, 4.2))
    plt.bar(x - w / 2, measured, width=w, label="Measured")
    plt.bar(x + w / 2, theory, width=w, label="Theory")
    plt.xticks(x, labels)
    plt.ylabel("Value")
    plt.title("EXP-015 DC Two-Pass Check")
    plt.grid(axis="y", alpha=0.25)
    plt.legend(frameon=False)
    plt.tight_layout()
    plt.savefig(run_dir / "plot_exp015_dc_summary.png", dpi=180)
    plt.close()

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
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

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
    (run_dir / "summary_exp015.md").write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    print(f"wrote {summary_path}")
    print(f"wrote {run_dir / 'summary_exp015.md'}")
    print(f"wrote plots under {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
