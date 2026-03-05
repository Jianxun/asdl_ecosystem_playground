#!/usr/bin/env python3
"""Normalize ngspice ASCII RAW files into a stable HDF5 schema.

Schema (root):
- vectors:      (n_points, n_vars) float64/complex128
- vector_names: (n_vars,) utf-8 strings
- vector_kinds: (n_vars,) utf-8 strings
- indep_var:    (n_points,) same dtype as vectors column
- signals/:     one dataset per dependent vector (flat v1)

CLI example:
    python tools/normalize_raw.py --input outputs/raw/tran_square/tran_square.raw \
        --output outputs/hdf5/tran_square.h5 --case-id tran_square
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import h5py
import numpy as np


@dataclass
class RawData:
    header: dict[str, str]
    names: list[str]
    kinds: list[str]
    values: np.ndarray  # shape=(n_points, n_vars)


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _parse_scalar(token: str) -> complex | float:
    tok = token.strip()
    if "," in tok:
        a, b = tok.split(",", 1)
        return complex(float(a), float(b))
    return float(tok)


def _safe_dataset_name(name: str, idx: int) -> str:
    safe = re.sub(r"[^a-zA-Z0-9_.-]+", "_", name).strip("_")
    if not safe:
        safe = f"sig_{idx}"
    return f"{idx:03d}_{safe}"


def parse_ngspice_ascii_raw(raw_path: str | Path) -> RawData:
    path = Path(raw_path)
    raw_bytes = path.read_bytes()
    text = raw_bytes.decode("utf-8", errors="replace")
    lines = text.splitlines()

    header: dict[str, str] = {}
    n_vars = None
    n_points = None
    i = 0

    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("Variables:"):
            i += 1
            break
        if ":" in line:
            k, v = line.split(":", 1)
            header[k.strip()] = v.strip()
            if k.strip().lower() == "no. variables":
                n_vars = int(v.strip())
            elif k.strip().lower() == "no. points":
                n_points = int(v.strip())
        i += 1

    if n_vars is None or n_points is None:
        raise ValueError("RAW header missing No. Variables / No. Points")

    names: list[str] = []
    kinds: list[str] = []
    for _ in range(n_vars):
        if i >= len(lines):
            raise ValueError("Unexpected EOF while reading Variables section")
        row = lines[i].strip()
        i += 1
        if not row:
            continue
        parts = row.split()
        if len(parts) < 3:
            raise ValueError(f"Bad variable row: {row!r}")
        names.append(parts[1])
        kinds.append(parts[2])

    has_complex_flag = "complex" in header.get("Flags", "").lower()

    # ASCII RAW path
    j = i
    while j < len(lines) and not lines[j].strip().startswith("Values:"):
        j += 1
    if j < len(lines):
        j += 1
        flat_vals: list[complex | float] = []
        for line in lines[j:]:
            s = line.strip()
            if not s:
                continue
            parts = s.split()
            if len(parts) >= 2 and re.fullmatch(r"[+-]?\d+", parts[0]):
                token = parts[1]
            else:
                token = parts[-1]
            flat_vals.append(_parse_scalar(token))

        expected = n_points * n_vars
        if len(flat_vals) != expected:
            raise ValueError(
                f"Parsed {len(flat_vals)} values, expected {expected} (= {n_points}x{n_vars}); RAW format mismatch"
            )

        has_complex = any(isinstance(v, complex) and v.imag != 0 for v in flat_vals)
        dtype = np.complex128 if has_complex else np.float64
        arr = np.asarray(flat_vals, dtype=dtype).reshape(n_points, n_vars)
        return RawData(header=header, names=names, kinds=kinds, values=arr)

    # Binary RAW path
    marker = b"Binary:\n"
    idx = raw_bytes.find(marker)
    if idx < 0:
        marker = b"Binary:\r\n"
        idx = raw_bytes.find(marker)
    if idx < 0:
        raise ValueError("RAW file missing both Values and Binary sections")

    blob = raw_bytes[idx + len(marker) :]
    if len(blob) % 8 != 0:
        # tolerate a trailing newline/padding byte if present
        blob = blob[: len(blob) - (len(blob) % 8)]
    vals = np.frombuffer(blob, dtype="<f8")

    expected_real = n_points * n_vars
    expected_complex = expected_real * 2

    if has_complex_flag:
        if vals.size != expected_complex:
            raise ValueError(f"Binary complex RAW size mismatch: got {vals.size}, expected {expected_complex}")
        arr = vals.reshape(n_points, n_vars, 2)
        out = arr[..., 0] + 1j * arr[..., 1]
    else:
        if vals.size != expected_real:
            raise ValueError(f"Binary real RAW size mismatch: got {vals.size}, expected {expected_real}")
        out = vals.reshape(n_points, n_vars)

    return RawData(header=header, names=names, kinds=kinds, values=out)


def normalize_raw_to_hdf5(
    raw_path: str | Path,
    hdf5_path: str | Path,
    *,
    case_id: str | None = None,
    simulator: str = "ngspice",
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    raw_path = Path(raw_path)
    hdf5_path = Path(hdf5_path)
    hdf5_path.parent.mkdir(parents=True, exist_ok=True)

    parsed = parse_ngspice_ascii_raw(raw_path)

    if parsed.values.ndim != 2 or parsed.values.shape[1] != len(parsed.names):
        raise ValueError("Shape consistency check failed for vectors")

    indep_idx = 0
    for idx, (nm, kd) in enumerate(zip(parsed.names, parsed.kinds)):
        if nm.lower() in {"time", "frequency"} or kd.lower() in {"time", "frequency"}:
            indep_idx = idx
            break

    indep_var = parsed.values[:, indep_idx]
    if indep_var.size == 0:
        raise ValueError("Independent variable is empty")

    with h5py.File(hdf5_path, "w") as h5:
        str_dt = h5py.string_dtype("utf-8")

        h5.create_dataset("vectors", data=parsed.values)
        h5.create_dataset("vector_names", data=np.asarray(parsed.names, dtype=object), dtype=str_dt)
        h5.create_dataset("vector_kinds", data=np.asarray(parsed.kinds, dtype=object), dtype=str_dt)
        h5.create_dataset("indep_var", data=indep_var)

        sig_grp = h5.create_group("signals")
        for idx, (name, kind) in enumerate(zip(parsed.names, parsed.kinds)):
            if idx == indep_idx:
                continue
            ds = sig_grp.create_dataset(_safe_dataset_name(name, idx), data=parsed.values[:, idx])
            ds.attrs["name"] = name
            ds.attrs["kind"] = kind
            ds.attrs["source_index"] = idx

        h5.attrs["schema_version"] = "S-102.v1"
        h5.attrs["created_utc"] = datetime.now(timezone.utc).isoformat()
        h5.attrs["source_file"] = str(raw_path)
        h5.attrs["source_sha256"] = _sha256_file(raw_path)
        h5.attrs["simulator"] = simulator
        if case_id:
            h5.attrs["case_id"] = case_id
        h5.attrs["n_points"] = int(parsed.values.shape[0])
        h5.attrs["n_vars"] = int(parsed.values.shape[1])
        h5.attrs["indep_var_index"] = indep_idx
        h5.attrs["indep_var_name"] = parsed.names[indep_idx]
        h5.attrs["quality_status"] = "ok"
        h5.attrs["integrity_checks"] = json.dumps(
            {
                "shape_consistent": True,
                "indep_var_present": True,
            }
        )

        for k, v in (metadata or {}).items():
            try:
                h5.attrs[f"meta_{k}"] = v
            except TypeError:
                h5.attrs[f"meta_{k}"] = json.dumps(v)

    return {
        "raw_path": str(raw_path),
        "hdf5_path": str(hdf5_path),
        "n_points": int(parsed.values.shape[0]),
        "n_vars": int(parsed.values.shape[1]),
        "indep_var": parsed.names[indep_idx],
    }


def _parse_meta_items(items: list[str]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for item in items:
        if "=" not in item:
            raise ValueError(f"Bad --meta item {item!r}; expected key=value")
        k, v = item.split("=", 1)
        out[k] = v
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Normalize ngspice ASCII RAW to HDF5")
    ap.add_argument("--input", "-i", required=True, help="Input ngspice RAW file")
    ap.add_argument("--output", "-o", required=True, help="Output HDF5 path")
    ap.add_argument("--case-id", default=None, help="Optional case identifier")
    ap.add_argument("--simulator", default="ngspice", help="Simulator label metadata")
    ap.add_argument("--meta", action="append", default=[], help="Additional metadata key=value (repeatable)")

    args = ap.parse_args(argv)
    meta = _parse_meta_items(args.meta)
    info = normalize_raw_to_hdf5(
        args.input,
        args.output,
        case_id=args.case_id,
        simulator=args.simulator,
        metadata=meta,
    )
    print(json.dumps(info, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
