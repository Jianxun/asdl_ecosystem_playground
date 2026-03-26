#!/usr/bin/env python3
"""Plot normalized HDF5 waveforms and save PNG figures.

Examples
--------
python tools/plot_waveforms.py \
  --input outputs/hdf5/tran_square.h5 \
  --signals 001_v_in 002_v_out \
  --mode transient \
  --output outputs/plots/tran_square_overlay.png

python tools/plot_waveforms.py \
  --input outputs/hdf5/ac_onepole.h5 \
  --signals 002_v_out \
  --mode ac \
  --output outputs/plots/ac_onepole_bode.png
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import numpy as np

try:
    import h5py
except ImportError as exc:  # pragma: no cover
    raise SystemExit("h5py is required. Install with: pip install h5py") from exc

try:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except ImportError as exc:  # pragma: no cover
    raise SystemExit("matplotlib is required. Install with: pip install matplotlib") from exc


class PlotError(RuntimeError):
    """Raised for actionable plotting failures."""


@dataclass
class SignalTable:
    indep: np.ndarray
    indep_name: str
    signals: dict[str, np.ndarray]
    aliases: dict[str, str]


def _decode_name(value: object) -> str:
    if isinstance(value, (bytes, np.bytes_)):
        return bytes(value).decode("utf-8", errors="replace")
    return str(value)


def _as_1d(arr: np.ndarray) -> np.ndarray:
    out = np.asarray(arr)
    if out.ndim == 0:
        out = out.reshape(1)
    if out.ndim != 1:
        raise PlotError(f"Expected 1D dataset, got shape={out.shape}")
    return out


def load_signal_table(path: str | Path) -> SignalTable:
    with h5py.File(path, "r") as h5:
        if "indep_var" not in h5:
            raise PlotError("Missing required dataset: indep_var")
        indep = _as_1d(h5["indep_var"][...])
        indep_name = _decode_name(h5.attrs.get("indep_var_name", "indep_var"))

        if "signals" not in h5 or not isinstance(h5["signals"], h5py.Group):
            raise PlotError("Missing required group: signals")

        signals: dict[str, np.ndarray] = {}
        aliases: dict[str, str] = {}
        for key in h5["signals"].keys():
            ds = h5["signals"][key]
            values = _as_1d(ds[...])
            if values.shape[0] != indep.shape[0]:
                raise PlotError(
                    f"Signal '{key}' length={values.shape[0]} does not match indep_var length={indep.shape[0]}"
                )
            signals[key] = values
            aliases[key] = key

            raw_name = _decode_name(ds.attrs.get("name", "")).strip()
            if raw_name and raw_name not in aliases:
                aliases[raw_name] = key

    return SignalTable(indep=indep, indep_name=indep_name, signals=signals, aliases=aliases)


def _resolve_signals(table: SignalTable, requested: list[str]) -> list[tuple[str, np.ndarray]]:
    resolved: list[tuple[str, np.ndarray]] = []
    for name in requested:
        key = table.aliases.get(name)
        if key is None:
            available = sorted(table.signals.keys())
            raise PlotError(
                f"Signal '{name}' not found. Available dataset keys: {', '.join(available[:20])}"
            )
        resolved.append((name, table.signals[key]))
    return resolved


def _prepare_x(indep: np.ndarray, indep_name: str, mode: str) -> tuple[np.ndarray, str, bool]:
    x = indep
    semilog = mode == "ac"
    label = indep_name

    if np.iscomplexobj(x):
        x = np.abs(x)
        label = f"|{indep_name}|"

    x = np.asarray(x, dtype=float)
    if mode == "ac":
        semilog = np.all(x > 0)
        if indep_name.lower() in {"frequency", "freq"}:
            label = "Frequency (Hz)"
    elif indep_name.lower() == "time":
        label = "Time (s)"

    return x, label, semilog


def plot_transient(ax: plt.Axes, x: np.ndarray, series: list[tuple[str, np.ndarray]]) -> None:
    for name, y in series:
        if np.iscomplexobj(y):
            y = np.real(y)
        ax.plot(x, np.asarray(y, dtype=float), label=name, linewidth=1.4)
    ax.set_ylabel("Amplitude")


def plot_ac(
    fig: plt.Figure,
    x: np.ndarray,
    series: list[tuple[str, np.ndarray]],
    semilog: bool,
) -> tuple[plt.Axes, plt.Axes]:
    ax_mag = fig.add_subplot(2, 1, 1)
    ax_phase = fig.add_subplot(2, 1, 2, sharex=ax_mag)

    for name, y in series:
        yc = np.asarray(y, dtype=np.complex128)
        mag_db = 20.0 * np.log10(np.maximum(np.abs(yc), 1e-30))
        phase_deg = np.unwrap(np.angle(yc)) * 180.0 / np.pi
        if semilog:
            ax_mag.semilogx(x, mag_db, label=name, linewidth=1.4)
            ax_phase.semilogx(x, phase_deg, label=name, linewidth=1.4)
        else:
            ax_mag.plot(x, mag_db, label=name, linewidth=1.4)
            ax_phase.plot(x, phase_deg, label=name, linewidth=1.4)

    ax_mag.set_ylabel("Magnitude (dB)")
    ax_phase.set_ylabel("Phase (deg)")
    return ax_mag, ax_phase


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Plot normalized HDF5 waveforms to PNG")
    parser.add_argument("--input", "-i", required=True, help="Input normalized HDF5 file")
    parser.add_argument("--signals", "-s", nargs="+", required=True, help="Signal names to plot")
    parser.add_argument("--output", "-o", required=True, help="Output PNG path")
    parser.add_argument("--mode", choices=["transient", "ac", "auto"], default="auto")
    parser.add_argument("--title", default=None, help="Optional figure title")
    parser.add_argument("--style", default="seaborn-v0_8-whitegrid", help="Matplotlib style name")
    parser.add_argument("--dpi", type=int, default=140, help="Output image DPI")
    parser.add_argument("--figsize", nargs=2, type=float, default=[10.0, 4.0], metavar=("W", "H"))
    return parser


def _infer_mode(indep_name: str, indep: np.ndarray) -> str:
    if indep_name.lower() in {"frequency", "freq"}:
        return "ac"
    if np.iscomplexobj(indep):
        return "ac"
    return "transient"


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        table = load_signal_table(args.input)
        selected = _resolve_signals(table, args.signals)
        mode = args.mode if args.mode != "auto" else _infer_mode(table.indep_name, table.indep)

        plt.style.use(args.style)
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if mode == "ac":
            fig = plt.figure(figsize=(args.figsize[0], max(args.figsize[1], 5.0)))
        else:
            fig, ax = plt.subplots(figsize=(args.figsize[0], args.figsize[1]))

        x, x_label, semilog = _prepare_x(table.indep, table.indep_name, mode)

        if mode == "ac":
            ax_mag, ax_phase = plot_ac(fig, x, selected, semilog=semilog)
            ax_phase.set_xlabel(x_label)
            ax_mag.grid(True, which="both", alpha=0.25)
            ax_phase.grid(True, which="both", alpha=0.25)
            ax_mag.legend(loc="best")
        else:
            plot_transient(ax, x, selected)
            ax.set_xlabel(x_label)
            ax.grid(True, alpha=0.25)
            ax.legend(loc="best")

        if args.title:
            fig.suptitle(args.title)

        fig.tight_layout()
        fig.savefig(output_path, dpi=args.dpi)
        plt.close(fig)
        print(output_path)
        return 0
    except (OSError, ValueError, PlotError) as exc:
        print(f"error: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
