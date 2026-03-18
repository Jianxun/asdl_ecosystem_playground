#!/usr/bin/env python3

from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def save_bode_magnitude_overlay(
    freq_hz: np.ndarray,
    traces: list[tuple[np.ndarray, str, str, float]],
    out_path: Path,
    title: str,
    ylabel: str = "Magnitude (dB)",
    hline_db: float | None = 0.0,
    legend_ncol: int = 1,
) -> None:
    plt.figure(figsize=(8.0, 5.2))
    for arr, label, style, lw in traces:
        plt.semilogx(freq_hz, 20 * np.log10(np.maximum(np.abs(arr), 1e-30)), style, lw=lw, label=label)
    if hline_db is not None:
        plt.axhline(hline_db, color="k", ls=":", lw=1)
    plt.xlabel("Frequency (Hz)")
    plt.ylabel(ylabel)
    plt.title(title)
    plt.grid(alpha=0.25, which="both")
    plt.legend(frameon=False, ncol=legend_ncol)
    plt.tight_layout()
    plt.savefig(out_path, dpi=180)
    plt.close()


def save_phase_overlay(
    freq_hz: np.ndarray,
    traces: list[tuple[np.ndarray, str, str, float]],
    out_path: Path,
    title: str,
) -> None:
    plt.figure(figsize=(8.0, 4.6))
    for arr, label, style, lw in traces:
        plt.semilogx(freq_hz, np.unwrap(np.angle(arr)) * 180.0 / np.pi, style, lw=lw, label=label)
    plt.xlabel("Frequency (Hz)")
    plt.ylabel("Phase (deg)")
    plt.title(title)
    plt.grid(alpha=0.25, which="both")
    plt.legend(frameon=False)
    plt.tight_layout()
    plt.savefig(out_path, dpi=180)
    plt.close()


def save_bar_comparison(
    labels: list[str],
    measured: list[float],
    theory: list[float],
    out_path: Path,
    title: str,
    ylabel: str = "Value",
) -> None:
    x = np.arange(len(labels))
    w = 0.35
    plt.figure(figsize=(6.4, 4.2))
    plt.bar(x - w / 2, measured, width=w, label="Measured")
    plt.bar(x + w / 2, theory, width=w, label="Theory")
    plt.xticks(x, labels)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.grid(axis="y", alpha=0.25)
    plt.legend(frameon=False)
    plt.tight_layout()
    plt.savefig(out_path, dpi=180)
    plt.close()
