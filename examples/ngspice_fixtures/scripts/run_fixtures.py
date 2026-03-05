#!/usr/bin/env python3
"""Run deterministic ngspice fixtures and collect RAW/log artifacts.

Output layout:
  outputs/raw/<case>/netlist.spice
  outputs/raw/<case>/sim.raw
  outputs/raw/<case>/sim.log
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

CASES = {
    "tran_square": "tran_square.spice",
    "tran_multitone": "tran_multitone.spice",
    "ac_onepole": "ac_onepole.spice",
}


def run_case(case: str, src_netlist: Path, out_root: Path) -> None:
    case_dir = out_root / case
    case_dir.mkdir(parents=True, exist_ok=True)

    netlist_out = case_dir / "netlist.spice"
    raw_out = case_dir / "sim.raw"
    log_out = case_dir / "sim.log"

    shutil.copyfile(src_netlist, netlist_out)

    cmd = [
        "ngspice",
        "-b",
        "-a",  # force ASCII RAW so normalize_raw.py can parse fixture outputs
        "-o",
        str(log_out),
        "-r",
        str(raw_out),
        str(netlist_out),
    ]

    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        err = proc.stderr.strip() or proc.stdout.strip() or f"ngspice failed for {case}"
        raise RuntimeError(err)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run ngspice fixture netlists")
    parser.add_argument(
        "--cases",
        nargs="+",
        choices=sorted(CASES.keys()),
        default=list(CASES.keys()),
        help="Subset of fixture cases to run",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    netlists_dir = repo_root / "netlists"
    out_root = repo_root / "outputs" / "raw"
    out_root.mkdir(parents=True, exist_ok=True)

    for case in args.cases:
        netlist_name = CASES[case]
        src_netlist = netlists_dir / netlist_name
        if not src_netlist.exists():
            raise FileNotFoundError(f"Missing netlist for {case}: {src_netlist}")

        print(f"[run_fixtures] running {case}")
        run_case(case, src_netlist, out_root)

    print("[run_fixtures] done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
