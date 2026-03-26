#!/usr/bin/env python3
"""Compact HDF5 query tool for normalized waveform artifacts.

Subcommands
-----------
- list-signals
- summary
- head --signal <name> --n <k>
- range --signal <name> --x0 <val> --x1 <val>

Default output is JSON. Use ``--format text`` for plain text output.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from typing import Any

import numpy as np

try:
    import h5py
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "h5py is required for tools/h5_query.py. Install with: pip install h5py"
    ) from exc


class QueryError(RuntimeError):
    """Raised for actionable query failures."""


@dataclass
class SignalTable:
    indep: np.ndarray
    signals: dict[str, np.ndarray]


def _decode_name(value: Any) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, np.bytes_):
        return bytes(value).decode("utf-8", errors="replace")
    return str(value)


def _as_1d(dataset: Any) -> np.ndarray:
    arr = np.asarray(dataset)
    if arr.ndim == 0:
        arr = arr.reshape(1)
    if arr.ndim != 1:
        raise QueryError(f"Expected 1D dataset but found shape={arr.shape}")
    return arr


def _load_indep(h5: h5py.File) -> np.ndarray:
    if "indep_var" not in h5:
        raise QueryError("Missing required dataset: indep_var")
    indep = _as_1d(h5["indep_var"][...])
    return indep


def _load_signals_from_group(h5: h5py.File, n_points: int) -> dict[str, np.ndarray]:
    if "signals" not in h5 or not isinstance(h5["signals"], h5py.Group):
        return {}

    out: dict[str, np.ndarray] = {}
    sig_group = h5["signals"]
    for name in sig_group.keys():
        values = _as_1d(sig_group[name][...])
        if values.shape[0] != n_points:
            raise QueryError(
                f"Signal '{name}' length={values.shape[0]} does not match indep_var length={n_points}"
            )
        out[name] = values
    return out


def _load_signals_from_vectors(h5: h5py.File, n_points: int) -> dict[str, np.ndarray]:
    if "vectors" not in h5 or "vector_names" not in h5:
        return {}

    names = [_decode_name(v) for v in np.asarray(h5["vector_names"][...]).ravel()]
    if not names:
        return {}

    vectors = np.asarray(h5["vectors"][...])
    if vectors.ndim != 2:
        raise QueryError(f"Expected 2D dataset 'vectors' but found shape={vectors.shape}")

    if vectors.shape[0] == len(names) and vectors.shape[1] == n_points:
        matrix = vectors
    elif vectors.shape[1] == len(names) and vectors.shape[0] == n_points:
        matrix = vectors.T
    else:
        raise QueryError(
            "Could not align 'vectors' with 'vector_names' and 'indep_var'. "
            f"vectors={vectors.shape}, names={len(names)}, indep_len={n_points}"
        )

    # Remove indep vector if present in names.
    indep_name = _decode_name(h5["indep_var"].attrs.get("name", ""))
    out: dict[str, np.ndarray] = {}
    for idx, name in enumerate(names):
        if name == indep_name:
            continue
        out[name] = np.asarray(matrix[idx])
    return out


def load_signal_table(path: str) -> SignalTable:
    with h5py.File(path, "r") as h5:
        indep = _load_indep(h5)
        signals = _load_signals_from_group(h5, indep.shape[0])
        if not signals:
            signals = _load_signals_from_vectors(h5, indep.shape[0])

    if not signals:
        raise QueryError(
            "No queryable signals found. Expected either a 'signals' group or {'vectors','vector_names'} datasets."
        )

    return SignalTable(indep=indep, signals=signals)


def _json_default(obj: Any) -> Any:
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, (np.floating, np.integer)):
        return obj.item()
    if isinstance(obj, np.bool_):
        return bool(obj)
    return str(obj)


def _emit(payload: dict[str, Any], out_format: str) -> None:
    if out_format == "json":
        print(json.dumps(payload, default=_json_default, separators=(",", ":")))
        return

    # text
    command = payload.get("command", "")
    if command == "list-signals":
        for name in payload.get("signals", []):
            print(name)
    elif command == "summary":
        print(f"points: {payload.get('points')}")
        print(f"x_min: {payload.get('x_min')}")
        print(f"x_max: {payload.get('x_max')}")
        print(f"signal_count: {payload.get('signal_count')}")
        preview = payload.get("signals_preview", [])
        if preview:
            print("signals_preview: " + ", ".join(preview))
    elif command in {"head", "range"}:
        print(f"signal: {payload.get('signal')}")
        print(f"count: {payload.get('count')}")
        for x, y in payload.get("points", []):
            print(f"{x}\t{y}")
    else:
        print(payload)


def cmd_list_signals(path: str) -> dict[str, Any]:
    table = load_signal_table(path)
    return {
        "command": "list-signals",
        "file": path,
        "count": len(table.signals),
        "signals": sorted(table.signals.keys()),
    }


def cmd_summary(path: str) -> dict[str, Any]:
    table = load_signal_table(path)
    x = table.indep
    names = sorted(table.signals.keys())
    return {
        "command": "summary",
        "file": path,
        "points": int(x.shape[0]),
        "x_min": float(np.min(x)),
        "x_max": float(np.max(x)),
        "signal_count": len(names),
        "signals_preview": names[:10],
    }


def _must_get_signal(table: SignalTable, signal: str) -> np.ndarray:
    if signal not in table.signals:
        available = sorted(table.signals.keys())
        preview = ", ".join(available[:20])
        suffix = " ..." if len(available) > 20 else ""
        raise QueryError(f"Signal '{signal}' not found. Available: {preview}{suffix}")
    return table.signals[signal]


def cmd_head(path: str, signal: str, n: int) -> dict[str, Any]:
    if n <= 0:
        raise QueryError("--n must be a positive integer")

    table = load_signal_table(path)
    y = _must_get_signal(table, signal)
    x = table.indep
    n_take = min(n, x.shape[0])

    points = [[x[i], y[i]] for i in range(n_take)]
    return {
        "command": "head",
        "file": path,
        "signal": signal,
        "count": len(points),
        "points": points,
    }


def cmd_range(path: str, signal: str, x0: float, x1: float) -> dict[str, Any]:
    if x1 < x0:
        raise QueryError("Invalid range: require x1 >= x0")

    table = load_signal_table(path)
    y = _must_get_signal(table, signal)
    x = table.indep

    mask = (x >= x0) & (x <= x1)
    idx = np.nonzero(mask)[0]
    if idx.size == 0:
        raise QueryError(
            f"No points in requested range [{x0}, {x1}]. Data domain is [{float(np.min(x))}, {float(np.max(x))}]"
        )

    points = [[x[i], y[i]] for i in idx]
    return {
        "command": "range",
        "file": path,
        "signal": signal,
        "x0": x0,
        "x1": x1,
        "count": len(points),
        "points": points,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Query normalized HDF5 waveform artifacts")
    parser.add_argument("file", help="Path to normalized HDF5 file")
    parser.add_argument("--format", choices=["json", "text"], default="json", help="Output format")

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list-signals", help="List available signal names")
    subparsers.add_parser("summary", help="Show compact file summary")

    p_head = subparsers.add_parser("head", help="Show first N points for a signal")
    p_head.add_argument("--signal", required=True, help="Signal name")
    p_head.add_argument("--n", type=int, default=10, help="Number of rows to return")

    p_range = subparsers.add_parser("range", help="Show points in x-range for a signal")
    p_range.add_argument("--signal", required=True, help="Signal name")
    p_range.add_argument("--x0", required=True, type=float, help="Range start (inclusive)")
    p_range.add_argument("--x1", required=True, type=float, help="Range end (inclusive)")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "list-signals":
            payload = cmd_list_signals(args.file)
        elif args.command == "summary":
            payload = cmd_summary(args.file)
        elif args.command == "head":
            payload = cmd_head(args.file, args.signal, args.n)
        elif args.command == "range":
            payload = cmd_range(args.file, args.signal, args.x0, args.x1)
        else:  # pragma: no cover
            raise QueryError(f"Unsupported command: {args.command}")

        _emit(payload, args.format)
        return 0
    except (OSError, QueryError, KeyError, ValueError) as exc:
        _emit({"error": str(exc), "file": args.file, "command": args.command}, args.format)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
