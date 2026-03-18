# Theory Note: Two-Pass Return Ratio for a Generic Grounded Two-Node System

## Purpose

Capture a transferable derivation for two-pass (series/shunt) return-ratio extraction using generic grounded admittances, independent of any specific DUT implementation.

## Generic model

- Node `Vr`: output-side node.
- Node `Vf`: feedback/input-side node.
- Output shunt admittance to ground: `Go`.
- Input shunt admittance to ground: `Gi`.
- Controlled current injected at output node: `Igm = Gm * Vf`.

All quantities may be complex and frequency-dependent.

## AC1: series voltage injection (`Vt` between `Vr` and `Vf`)

Define source branch current `It` positive from `Vr -> Vf`, and source voltage:

- `Vt = Vr - Vf`

KCL:

- At `Vr`: `Go*Vr + Gm*Vf + It = 0`
- At `Vf`: `Gi*Vf - It = 0` => `It = Gi*Vf`

Substitute:

- `Go*Vr + (Gm + Gi)*Vf = 0`
- `Vr/Vf = -(Gm + Gi)/Go`

Hence canonical voltage return ratio:

- `Tv = -(Vr/Vf) = (Gm + Gi)/Go`

And node voltages vs injected source:

- `Vf = -(Go/(Go + Gm + Gi)) * Vt`
- `Vr = ((Gm + Gi)/(Go + Gm + Gi)) * Vt`

## AC2: shunt current injection (`Iinj` into shorted node)

Short the break so `Vr = Vf = Vx`.

Define branch currents leaving the shorted node:

- Output-side current: `Iout = (Go + Gm) * Vx`
- Input-side current: `Iin = Gi * Vx`

KCL:

- `Iinj = Iout + Iin = (Go + Gm + Gi) * Vx`

Current partition:

- `Iout = ((Go + Gm)/(Go + Gm + Gi)) * Iinj`
- `Iin = (Gi/(Go + Gm + Gi)) * Iinj`

Current ratio:

- `Iout/Iin = (Go + Gm)/Gi`

Choose current-sense orientation so canonical current return ratio is:

- `Ti = -(Ir/If) = (Go + Gm)/Gi`

## Reconstructed loop gain (Tian combine)

Use:

- `1/(1+T) = 1/(1+Tv) + 1/(1+Ti)`

with:

- `Tv = (Gm + Gi)/Go`
- `Ti = (Go + Gm)/Gi`

Then:

- `1/(1+Tv) = Go/(Go + Gm + Gi)`
- `1/(1+Ti) = Gi/(Go + Gm + Gi)`
- `1/(1+T) = (Go + Gi)/(Go + Gm + Gi)`
- `T = Gm/(Go + Gi)`

So AC1 and AC2 recover a self-consistent loop-gain expression.

## Sanity limits (single-parameter)

Holding the other two finite:

- `Gm -> 0`: `Tv -> Gi/Go`, active path vanishes.
- `Gi -> 0`: `Tv -> Gm/Go`, feedback-node shunt loading vanishes.
- `Go -> 0`: `Vf -> 0`, `Vr -> Vt`, and `Tv -> infinity` when `Gm + Gi != 0`.

Degenerate simultaneous denominator collapse leads to ill-defined ratio forms (`0/0`-type limits).

## Mapping to capacitor-based special cases

Use substitutions such as:

- `Go = go + s*Cout`
- `Gi = s*Cin`

to recover frequency-dependent forms used in RC loop-gain fixtures.
