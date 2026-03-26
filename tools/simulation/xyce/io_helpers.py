#!/usr/bin/env python3

from pathlib import Path

import h5py
import numpy as np


def require_files(paths: list[Path]) -> None:
    missing = [str(p) for p in paths if not p.exists()]
    if missing:
        raise FileNotFoundError(f"Missing required file(s): {', '.join(missing)}")


def resolve_signal_key(h5_path: Path, wanted: str) -> str:
    with h5py.File(h5_path, "r") as f:
        keys = list(f["signals"].keys())
    wanted_u = wanted.upper()
    for key in keys:
        if key.upper() == wanted_u:
            return key
    raise KeyError(f"Signal '{wanted}' not found in {h5_path}. Available: {keys}")


def load_signal(h5_path: Path, wanted: str) -> np.ndarray:
    key = resolve_signal_key(h5_path, wanted)
    with h5py.File(h5_path, "r") as f:
        return np.array(f[f"signals/{key}"])


def load_frequency(h5_path: Path) -> np.ndarray:
    with h5py.File(h5_path, "r") as f:
        return np.array(f["indep_var/FREQUENCY"])


def scalar_real_last(x: np.ndarray) -> float:
    if x.size == 0:
        raise ValueError("empty signal array")
    return float(np.real(np.ravel(x)[-1]))


def complex_at_frequency(freq_hz: np.ndarray, arr: np.ndarray, target_hz: float) -> complex:
    i = int(np.argmin(np.abs(freq_hz - target_hz)))
    return complex(arr[i])
