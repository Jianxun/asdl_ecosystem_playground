# P-004 Deterministic Validation First

## Intent

Before validating complex extraction methods on real circuits, validate on a deterministic reference with known closed-form behavior.

## Why

- Separates method errors from circuit-model complexity.
- Provides a reliable baseline for numerical accuracy checks.

## Rules

- Build a minimal synthetic fixture first (for example ideal `gm`, `ro`, known capacitors).
- Compare extracted metrics against theory (for example DC gain, pole, UGB).
- Require agreement within a predefined tolerance before applying method to larger designs.

## Recommended Tolerance

- Start with <= 2% relative error for gain-bandwidth and pole checks.
- Tighten as fixture complexity is reduced.
