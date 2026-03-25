#!/usr/bin/env python3
"""Inspect available signal names in Xyce HDF5 artifacts.

This helper is intended for fast, reusable signal discovery during analysis.
It accepts one or more `.raw.h5` files and/or run directories, and writes a
machine-readable JSON manifest of independent-variable and signal datasets.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def _collect_h5_files(inputs: list[Path]) -> list[Path]:
    files: list[Path] = []
    missing: list[str] = []

    for item in inputs:
        if not item.exists():
            missing.append(str(item))
            continue

        if item.is_dir():
            matches = sorted(p for p in item.glob("*.raw.h5") if p.is_file())
            if not matches:
                raise FileNotFoundError(f"No '*.raw.h5' files found in directory: {item}")
            files.extend(matches)
        elif item.is_file():
            files.append(item)
        else:
            raise ValueError(f"Unsupported input path type: {item}")

    if missing:
        raise FileNotFoundError("Missing input path(s): " + ", ".join(missing))

    deduped = sorted({p.resolve() for p in files})
    if not deduped:
        raise FileNotFoundError("No input files resolved")
    return deduped


def _walk_dataset_names(group, prefix: str = "") -> list[str]:
    names: list[str] = []
    for key in sorted(group.keys()):
        obj = group[key]
        path = f"{prefix}/{key}" if prefix else key
        if hasattr(obj, "shape"):
            names.append(path)
        else:
            names.extend(_walk_dataset_names(obj, path))
    return names


def _inspect_one(path: Path, include_re: re.Pattern[str] | None) -> dict:
    try:
        import h5py
    except ImportError as exc:
        raise RuntimeError("This script requires 'h5py'.") from exc

    with h5py.File(path, "r") as handle:
        if "indep_var" not in handle or "signals" not in handle:
            raise ValueError(f"Not a normalized Xyce HDF5 structure: {path}")

        indep_names = _walk_dataset_names(handle["indep_var"])
        signal_names_all = _walk_dataset_names(handle["signals"])

        if include_re is None:
            signal_names = signal_names_all
        else:
            signal_names = [name for name in signal_names_all if include_re.search(name)]

        return {
            "file": str(path),
            "indep_var_names": indep_names,
            "signal_count_total": len(signal_names_all),
            "signal_count_selected": len(signal_names),
            "signals": signal_names,
        }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect available signal datasets in Xyce .raw.h5 files")
    parser.add_argument(
        "inputs",
        nargs="+",
        type=Path,
        help="Input .raw.h5 file(s) and/or run directory path(s)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        required=True,
        help="Output JSON path",
    )
    parser.add_argument(
        "--include",
        type=str,
        default=None,
        help="Optional regex filter applied to signal dataset names",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)

    try:
        include_re = re.compile(args.include) if args.include else None
        files = _collect_h5_files(args.inputs)
        inspections = [_inspect_one(path, include_re) for path in files]

        payload = {
            "tool": "inspect_xyce_signals",
            "inputs": [str(p) for p in args.inputs],
            "include_regex": args.include,
            "files": inspections,
        }

        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"wrote signal manifest for {len(inspections)} file(s) to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
