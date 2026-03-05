#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.analyzers.ac_metrics import extract_ac_metrics
from src.analyzers.cycle_extract import extract_cycles
from src.analyzers.edge_events import extract_edge_events
from src.analyzers.fft_topk import fft_topk

CASE_ANALYZERS = {
    "square": ("edge_events", "cycle_extract"),
    "multitone": ("fft_topk",),
    "ac_onepole": ("ac_metrics",),
}


class CaseLoadError(RuntimeError):
    pass


def _decode_name(x: Any) -> str:
    if isinstance(x, bytes):
        return x.decode("utf-8", errors="ignore")
    return str(x)


def _normalize_name(name: str) -> str:
    return name.strip().lower().replace(" ", "")


def _read_h5(path: Path) -> dict[str, Any]:
    try:
        import h5py  # type: ignore
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("h5py is required for tools/run_analyzers.py") from exc

    signals: dict[str, np.ndarray] = {}
    attrs: dict[str, Any] = {}

    with h5py.File(path, "r") as h5:
        attrs = {k: _decode_name(v) for k, v in h5.attrs.items()}

        if "signals" in h5:
            obj = h5["signals"]
            if hasattr(obj, "items"):
                for k, v in obj.items():
                    signals[_decode_name(k)] = np.asarray(v)
            else:
                mat = np.asarray(obj)
                names = []
                if "vector_names" in h5:
                    names = [_decode_name(n) for n in np.asarray(h5["vector_names"]).tolist()]
                if names:
                    for i, name in enumerate(names):
                        if mat.ndim == 2:
                            axis = mat[i] if mat.shape[0] == len(names) else mat[:, i]
                            signals[name] = np.asarray(axis)

        if "vectors" in h5 and "vector_names" in h5:
            vec = np.asarray(h5["vectors"])
            names = [_decode_name(n) for n in np.asarray(h5["vector_names"]).tolist()]
            if vec.ndim == 2 and names:
                for i, name in enumerate(names):
                    if name not in signals:
                        axis = vec[i] if vec.shape[0] == len(names) else vec[:, i]
                        signals[name] = np.asarray(axis)

        indep_obj = h5.get("indep_var")
        indep = None
        if indep_obj is not None:
            indep_arr = np.asarray(indep_obj)
            if indep_arr.ndim == 0 and indep_arr.dtype.kind in {"S", "U", "O"}:
                indep = _decode_name(indep_arr.item())
            elif indep_arr.ndim == 1 and np.issubdtype(indep_arr.dtype, np.number):
                indep = indep_arr
            else:
                try:
                    indep = _decode_name(indep_arr.item())
                except Exception:
                    indep = None

    return {"signals": signals, "attrs": attrs, "indep": indep}


def _pick_signal(signals: dict[str, np.ndarray], candidates: list[str], *, exclude: set[str] | None = None) -> np.ndarray | None:
    exclude = exclude or set()
    canon = { _normalize_name(k): k for k in signals.keys() }

    for cand in candidates:
        key = canon.get(_normalize_name(cand))
        if key and key not in exclude:
            arr = np.asarray(signals[key]).squeeze()
            if arr.ndim == 1:
                return arr

    for k, arr in signals.items():
        if k in exclude:
            continue
        arr = np.asarray(arr).squeeze()
        if arr.ndim == 1 and np.issubdtype(arr.dtype, np.number):
            return arr
    return None


def _infer_case_type(path: Path, attrs: dict[str, Any]) -> str | None:
    for k in ("case_type", "fixture", "case"):
        if k in attrs:
            val = str(attrs[k]).lower()
            for ct in CASE_ANALYZERS:
                if ct in val:
                    return ct

    stem = path.stem.lower()
    for ct in CASE_ANALYZERS:
        if ct in stem:
            return ct
    return None


def _extract_transient_xy(data: dict[str, Any]) -> tuple[np.ndarray, np.ndarray]:
    signals = data["signals"]
    indep = data["indep"]

    t = None
    if isinstance(indep, np.ndarray):
        t = indep
    elif isinstance(indep, str) and indep in signals:
        t = np.asarray(signals[indep]).squeeze()

    if t is None:
        t = _pick_signal(signals, ["t", "time", "tran_time", "seconds"])

    if t is None:
        raise CaseLoadError("Could not resolve transient independent variable (time)")

    y = _pick_signal(
        signals,
        ["v(out)", "out", "vout", "y", "signal", "vin", "v(in)"],
        exclude={k for k, v in signals.items() if np.array_equal(np.asarray(v).squeeze(), t)},
    )
    if y is None:
        raise CaseLoadError("Could not resolve transient dependent waveform")

    return np.asarray(t, dtype=float), np.asarray(y, dtype=float)


def _extract_ac_arrays(data: dict[str, Any]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    signals = data["signals"]
    indep = data["indep"]

    f = None
    if isinstance(indep, np.ndarray):
        f = indep
    elif isinstance(indep, str) and indep in signals:
        f = np.asarray(signals[indep]).squeeze()

    if f is None:
        f = _pick_signal(signals, ["f_hz", "freq", "frequency", "f"])

    if f is None:
        raise CaseLoadError("Could not resolve AC independent variable (frequency)")

    gain = _pick_signal(signals, ["gain_db", "mag_db", "db(v(out))", "vdb(out)", "gain"])
    phase = _pick_signal(signals, ["phase_deg", "phase", "ph(out)", "vp(out)"])

    if gain is None or phase is None:
        resp = _pick_signal(signals, ["v(out)", "out", "response", "resp"])
        if resp is not None and np.iscomplexobj(resp):
            if gain is None:
                gain = 20.0 * np.log10(np.maximum(np.abs(resp), 1e-15))
            if phase is None:
                phase = np.rad2deg(np.angle(resp))

    if gain is None:
        raise CaseLoadError("Could not resolve AC gain_db vector")
    if phase is None:
        raise CaseLoadError("Could not resolve AC phase_deg vector")

    return np.asarray(f, dtype=float), np.asarray(gain, dtype=float), np.asarray(phase, dtype=float)


def _run_case(path: Path, out_dir: Path, forced_case_type: str | None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "case": path.stem,
        "input_hdf5": str(path),
        "status": "ok",
        "analyzers": {},
        "quality": {"status": "ok", "reasons": []},
    }

    try:
        data = _read_h5(path)
        case_type = forced_case_type or _infer_case_type(path, data["attrs"])
        if case_type not in CASE_ANALYZERS:
            raise CaseLoadError(
                f"Could not determine case_type for '{path.name}'. "
                f"Use --case-type one of {sorted(CASE_ANALYZERS)}"
            )
        payload["case_type"] = case_type

        if case_type in {"square", "multitone"}:
            t, y = _extract_transient_xy(data)
            payload["inputs_summary"] = {
                "n_samples": int(len(t)),
                "x_span": [float(t[0]), float(t[-1])],
            }

            if case_type == "square":
                for analyzer_name in CASE_ANALYZERS[case_type]:
                    try:
                        if analyzer_name == "edge_events":
                            payload["analyzers"][analyzer_name] = extract_edge_events(t=t, y=y)
                        elif analyzer_name == "cycle_extract":
                            payload["analyzers"][analyzer_name] = extract_cycles(t=t, y=y)
                    except Exception as exc:
                        payload["analyzers"][analyzer_name] = {
                            "quality": {"status": "bad", "reasons": [str(exc)]},
                            "error": str(exc),
                        }
                        payload["quality"]["status"] = "warn"
                        payload["quality"]["reasons"].append(f"{analyzer_name}_failed")

            elif case_type == "multitone":
                try:
                    payload["analyzers"]["fft_topk"] = fft_topk(t=t, y=y)
                except Exception as exc:
                    payload["analyzers"]["fft_topk"] = {
                        "quality": {"status": "bad", "reasons": [str(exc)]},
                        "error": str(exc),
                    }
                    payload["quality"]["status"] = "warn"
                    payload["quality"]["reasons"].append("fft_topk_failed")

        elif case_type == "ac_onepole":
            f_hz, gain_db, phase_deg = _extract_ac_arrays(data)
            payload["inputs_summary"] = {
                "n_points": int(len(f_hz)),
                "f_span_hz": [float(f_hz[0]), float(f_hz[-1])],
            }
            try:
                payload["analyzers"]["ac_metrics"] = extract_ac_metrics(
                    f_hz=f_hz, gain_db=gain_db, phase_deg=phase_deg
                )
            except Exception as exc:
                payload["analyzers"]["ac_metrics"] = {
                    "quality": {"status": "bad", "reasons": [str(exc)]},
                    "error": str(exc),
                }
                payload["quality"]["status"] = "warn"
                payload["quality"]["reasons"].append("ac_metrics_failed")

    except Exception as exc:
        payload["status"] = "error"
        payload["quality"] = {"status": "bad", "reasons": [str(exc)]}
        payload["error"] = str(exc)

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{path.stem}.json"
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def _collect_inputs(input_path: Path, pattern: str) -> list[Path]:
    if input_path.is_file():
        return [input_path]
    if not input_path.exists():
        return []

    files = sorted(input_path.glob(pattern))
    return [p for p in files if p.is_file()]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run prototype analyzers over normalized HDF5 cases and emit JSON outputs."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("outputs/normalized"),
        help="Input HDF5 file or directory (default: outputs/normalized)",
    )
    parser.add_argument(
        "--pattern",
        default="*.h5",
        help="Glob pattern when --input is a directory (default: *.h5)",
    )
    parser.add_argument(
        "--case-type",
        choices=sorted(CASE_ANALYZERS),
        default=None,
        help="Optional override case type for all selected inputs",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs/analysis"),
        help="Output directory for per-case JSON (default: outputs/analysis)",
    )
    args = parser.parse_args()

    paths = _collect_inputs(args.input, args.pattern)
    if not paths:
        print(f"No input files found at {args.input} (pattern={args.pattern})")
        return 1

    statuses = []
    for path in paths:
        payload = _run_case(path=path, out_dir=args.output_dir, forced_case_type=args.case_type)
        statuses.append(payload.get("status", "error"))
        print(f"[{payload.get('status', 'error')}] {path.name} -> {args.output_dir / (path.stem + '.json')}")

    return 0 if any(s == "ok" for s in statuses) else 2


if __name__ == "__main__":
    raise SystemExit(main())
