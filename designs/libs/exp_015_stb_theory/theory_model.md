# EXP-015 Theory Model: Generic `Gm-Go-Gi` Follower

This experiment reframes the loop analysis in a generic single-ended, ground-referenced form.

## Circuit abstraction

- Output node: `Vr`
- Feedback/input node: `Vf`
- Output shunt admittance to ground: `Go`
- Input shunt admittance to ground: `Gi`
- Transconductor current injected at output node: `Igm = Gm * Vf`
- Series test source inserted between output and feedback nodes: `Vt = Vr - Vf`

Sign conventions in this note:

- Positive branch current is taken from node to ground for shunt admittances.
- Series source branch current `It` is defined positive from `Vr -> Vf`.

## AC1 (series voltage injection): solve for `Vr` and `Vf`

KCL at output node `Vr`:

- `Go*Vr + Gm*Vf + It = 0`

KCL at feedback node `Vf`:

- `Gi*Vf - It = 0`
- therefore `It = Gi*Vf`

Substitute into output-node KCL:

- `Go*Vr + (Gm + Gi)*Vf = 0`
- so `Vr/Vf = -(Gm + Gi)/Go`

Apply the series source constraint:

- `Vt = Vr - Vf`

Solve for node voltages in terms of injected source:

- `Vf = -(Go/(Go + Gm + Gi)) * Vt`
- `Vr = ((Gm + Gi)/(Go + Gm + Gi)) * Vt`

Useful derived ratio:

- `-(Vr/Vf) = (Gm + Gi)/Go`

## Sanity checks (single-parameter limits)

Using:

- `Vf = -(Go/(Go + Gm + Gi)) * Vt`
- `Vr = ((Gm + Gi)/(Go + Gm + Gi)) * Vt`
- `-(Vr/Vf) = (Gm + Gi)/Go`

while holding the other two admittances finite:

- `Gm -> 0`
  - `Vf -> -(Go/(Go+Gi)) * Vt`
  - `Vr -> (Gi/(Go+Gi)) * Vt`
  - `-(Vr/Vf) -> Gi/Go`
  - interpretation: active path vanishes and the split is set by passive shunt loading.

- `Gi -> 0`
  - `Vf -> -(Go/(Go+Gm)) * Vt`
  - `Vr -> (Gm/(Go+Gm)) * Vt`
  - `-(Vr/Vf) -> Gm/Go`
  - interpretation: no feedback-node shunt current; ratio is set by transconductor versus output shunt admittance.

- `Go -> 0`
  - `Vf -> 0`
  - `Vr -> Vt`
  - `-(Vr/Vf) -> infinity` when `Gm + Gi != 0`
  - interpretation: output node loses its shunt path, so nearly all injected series voltage appears at `Vr`.

Degenerate note:

- If denominator terms collapse simultaneously (for example `Go -> 0` and `Gm + Gi -> 0`), the ratio form becomes ill-defined (`0/0`-type floating limit).

## AC2 (shunt current injection): current return ratio

For the current-pass derivation, short the broken port so:

- `Vr = Vf = Vx`

Inject a shunt AC current `Iinj` into the shorted node and define branch currents leaving the node into each side:

- Output-side branch current: `Iout = (Go + Gm) * Vx`
- Input-side branch current: `Iin = Gi * Vx`

KCL at the shorted node:

- `Iinj = Iout + Iin = (Go + Gm + Gi) * Vx`
- therefore `Vx = Iinj / (Go + Gm + Gi)`

Current partition:

- `Iout = ((Go + Gm)/(Go + Gm + Gi)) * Iinj`
- `Iin = (Gi/(Go + Gm + Gi)) * Iinj`

Current return ratio magnitude from branch split:

- `Iout/Iin = (Go + Gm)/Gi`

To keep Tian/Middlebrook convention `Ti = -(Ir/If)` while getting a positive canonical expression, choose branch-sense orientations so `Ir/If = -(Go+Gm)/Gi`. Then:

- `Ti = (Go + Gm)/Gi`

## AC1+AC2 consistency check (generic)

From AC1:

- `Tv = -(Vr/Vf) = (Gm + Gi)/Go`

From AC2:

- `Ti = (Go + Gm)/Gi`

Use Tian combine:

- `1/(1+T) = 1/(1+Tv) + 1/(1+Ti)`

which gives:

- `1/(1+Tv) = Go/(Go + Gm + Gi)`
- `1/(1+Ti) = Gi/(Go + Gm + Gi)`
- `1/(1+T) = (Go + Gi)/(Go + Gm + Gi)`
- `T = Gm/(Go + Gi)`

So the reconstructed loop gain from generic AC1/AC2 equations is self-consistent.

## Mapping back to the capacitor case

The prior `gm-ro-cin-cload` setup is a direct special case:

- `Gm -> gm`
- `Go -> go + s*Cload` where `go = 1/ro`
- `Gi -> s*Cin`

Then:

- `-(Vr/Vf) = (gm + s*Cin)/(go + s*Cload)`

which is the canonical voltage-return quantity used in the two-pass reconstruction.
