#!/usr/bin/env python3

import numpy as np


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


def relative_error(measured: np.ndarray, theory: np.ndarray, eps: float = 1e-30) -> np.ndarray:
    return np.abs(measured - theory) / np.maximum(np.abs(theory), eps)


def max_relative_error(measured: np.ndarray, theory: np.ndarray, eps: float = 1e-30) -> float:
    return float(np.max(relative_error(measured, theory, eps=eps)))
