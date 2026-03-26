#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def run_cmd(command: list[str]) -> None:
    print("[cmd]", " ".join(command))
    subprocess.run(command, check=True)


def materialize_tb(
    tb_source: Path,
    tb_output: Path,
    *,
    top_module: str,
    gm: float,
    ro: float,
    ri: float,
    cout: float,
    cin: float,
    ac_points: int,
    ac_start: float,
    ac_stop: float,
    vtest_ac: float,
    itest_ac: float,
) -> None:
    text = tb_source.read_text(encoding="utf-8")

    replacements = {
        "top: tb_series": f"top: {top_module}",
        "GM: 1e-3": f"GM: {gm}",
        "RO: 5k": f"RO: {ro}",
        "RI: 10k": f"RI: {ri}",
        "COUT: 1p": f"COUT: {cout}",
        "CIN: 1p": f"CIN: {cin}",
        "AC_POINTS: 200": f"AC_POINTS: {ac_points}",
        "AC_START: 1": f"AC_START: {ac_start}",
        "AC_STOP: 1e11": f"AC_STOP: {ac_stop}",
        "VTEST_AC: 1": f"VTEST_AC: {vtest_ac}",
        "VTEST_AC: 0": f"VTEST_AC: {vtest_ac}",
        "ITEST_AC: 0": f"ITEST_AC: {itest_ac}",
        "ITEST_AC: 1": f"ITEST_AC: {itest_ac}",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    tb_output.write_text(text, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="EXP-016: run AC two-pass from one ASDL source")
    parser.add_argument("--run-id", default=None, help="Run id (default: current UTC timestamp)")
    parser.add_argument("--gm", type=float, default=1e-3)
    parser.add_argument("--ro", type=float, default=5e3)
    parser.add_argument("--ri", type=float, default=1e4)
    parser.add_argument("--cout", type=float, default=1e-12)
    parser.add_argument("--cin", type=float, default=1e-12)
    parser.add_argument("--ac-points", type=int, default=200)
    parser.add_argument("--ac-start", type=float, default=1.0)
    parser.add_argument("--ac-stop", type=float, default=1e11)
    parser.add_argument("--series-vtest-ac", type=float, default=1.0)
    parser.add_argument("--series-itest-ac", type=float, default=0.0)
    parser.add_argument("--shunt-vtest-ac", type=float, default=0.0)
    parser.add_argument("--shunt-itest-ac", type=float, default=1.0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[2]
    run_id = args.run_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = repo_root / "runs" / "exp_016_stb_reusable" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    tb_source = repo_root / "libs" / "exp_016_stb_reusable" / "tb_ac_middlebrook_two_pass.asdl"

    series_asdl = run_dir / "tb_ac_middlebrook_series.materialized.asdl"
    materialize_tb(
        tb_source,
        series_asdl,
        top_module="tb_series",
        gm=args.gm,
        ro=args.ro,
        ri=args.ri,
        cout=args.cout,
        cin=args.cin,
        ac_points=args.ac_points,
        ac_start=args.ac_start,
        ac_stop=args.ac_stop,
        vtest_ac=args.series_vtest_ac,
        itest_ac=args.series_itest_ac,
    )

    shunt_asdl = run_dir / "tb_ac_middlebrook_shunt.materialized.asdl"
    materialize_tb(
        tb_source,
        shunt_asdl,
        top_module="tb_shunt",
        gm=args.gm,
        ro=args.ro,
        ri=args.ri,
        cout=args.cout,
        cin=args.cin,
        ac_points=args.ac_points,
        ac_start=args.ac_start,
        ac_stop=args.ac_stop,
        vtest_ac=args.shunt_vtest_ac,
        itest_ac=args.shunt_itest_ac,
    )

    series_spice = run_dir / "tb_ac_middlebrook_series.spice"
    shunt_spice = run_dir / "tb_ac_middlebrook_shunt.spice"

    exp_lib = repo_root / "libs" / "exp_016_stb_reusable"
    run_cmd(
        [
            "asdlc",
            "netlist",
            str(series_asdl),
            "--backend",
            "sim.xyce",
            "--lib",
            str(exp_lib),
            "-o",
            str(series_spice),
        ]
    )
    run_cmd(
        [
            "asdlc",
            "netlist",
            str(shunt_asdl),
            "--backend",
            "sim.xyce",
            "--lib",
            str(exp_lib),
            "-o",
            str(shunt_spice),
        ]
    )

    run_cmd(["xyce", str(series_spice)])
    run_cmd(["xyce", str(shunt_spice)])

    raw_to_h5 = repo_root / "analysis" / "tools" / "xyce" / "raw_to_h5.py"
    run_cmd([str(repo_root / "venv" / "bin" / "python"), str(raw_to_h5), str(series_spice) + ".raw"])
    run_cmd([str(repo_root / "venv" / "bin" / "python"), str(raw_to_h5), str(shunt_spice) + ".raw"])

    analyze = repo_root / "analysis" / "tools" / "xyce" / "analyze_middlebrook_ac_two_pass.py"
    run_cmd(
        [
            str(repo_root / "venv" / "bin" / "python"),
            str(analyze),
            str(run_dir),
            "--gm",
            str(args.gm),
            "--go",
            str(1.0 / args.ro),
            "--gi",
            str(1.0 / args.ri),
            "--cout",
            str(args.cout),
            "--cin",
            str(args.cin),
        ]
    )

    summary = {
        "run_id": run_id,
        "run_dir": str(run_dir),
        "tb_source": str(tb_source),
        "materialized_tb": {
            "series": str(series_asdl),
            "shunt": str(shunt_asdl),
        },
        "spice": {
            "series": str(series_spice),
            "shunt": str(shunt_spice),
        },
        "source_params": {
            "series": {"vtest_ac": args.series_vtest_ac, "itest_ac": args.series_itest_ac},
            "shunt": {"vtest_ac": args.shunt_vtest_ac, "itest_ac": args.shunt_itest_ac},
        },
        "dut_params": {
            "gm_S": args.gm,
            "ro_ohm": args.ro,
            "ri_ohm": args.ri,
            "go_S": 1.0 / args.ro,
            "gi_S": 1.0 / args.ri,
            "cout_F": args.cout,
            "cin_F": args.cin,
        },
    }
    summary_path = run_dir / "summary_exp016_run.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"wrote {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
