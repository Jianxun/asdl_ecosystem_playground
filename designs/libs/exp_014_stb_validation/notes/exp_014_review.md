I think the core issue is **not Xyce** and not even mainly the algebra. It is that your two-pass benches are **not measuring the exact port quantities that the Middlebrook reconstruction assumes**.

The biggest clue is this:

* **AC1 gives ~ (gm/(2\pi C_{load}))**, not (gm/(2\pi(C_{in}+C_{load})))

That is actually a very revealing result. It says your AC1 pass is measuring the loop seen from the **output side only**. In other words, the series test source is effectively supplying the current for (C_{in}), so the amplifier loop only “feels” (C_{load}) in that pass. That part is expected.

For your ideal unity follower, the true closed-loop pole is:

[
H(s)=\frac{gm}{gm+\frac{1}{r_o}+s(C_{in}+C_{load})}
]

so the bandwidth target near

[
\frac{gm}{2\pi(C_{in}+C_{load})}
]

is correct.

## What AC1 is really telling you

With the loop broken by the **series voltage source**, the relation you are extracting is basically governed by:

[
T_v(s)\approx \frac{gm}{\frac{1}{r_o}+sC_{load}}
]

So the fact that its unity crossing lands near the **cload-only** value is not the bug. That is the expected behavior of the first pass.

The second pass is supposed to add back the effect of the input-side loading. That means the problem is almost certainly in **AC2 topology and/or current-ratio definition**.

## The likely issue

Your AC2 bench is very close, but I think it is still **not isolating the canonical “return current” and “driving-point current” cleanly enough**.

You currently infer:

[
I_{dut}=-(I(V_VSENSE)+I(V_VSHORT))
]

and then try

[
T_i = \frac{I(V_VSHORT)}{I_{dut}}
]

But the fact that only the reciprocal convention gives a sensible crossing is a strong sign that one of these is true:

1. **The current orientation is reversed relative to the theorem**, or
2. **The branch current through `vshort` is not the exact current quantity the formula expects**, because the shorted bench is not partitioning the two sides of the broken port cleanly enough.

I suspect it is **both**.

## Why your present AC2 is fragile

In the shunt pass, the loop is re-closed by `vshort`, and then you inject current through `itest` to ground via `vsense`.

That can work in principle, but it makes the extracted currents depend on how the solver reports the current through the short and the auxiliary source. In other words, you are reconstructing the needed port currents **indirectly**, and the sign/orientation becomes easy to get wrong.

For Middlebrook, you want the AC2 bench to give you a **clean partition of currents entering the two sides of the original cut**. Right now `vshort` is doing double duty as both “reclose the loop” and “one of the measured branches,” which muddies the interpretation.

## Why `Ti_inverse` looks better

This is another strong clue.

You reported:

* `Ti_user` → no unity crossing
* `Ti_inverse` → UGB ≈ (8.59\times 10^7) Hz

That means your analyzer’s “user” definition is almost certainly the **inverse of the canonical ratio** for your chosen current directions.

So the first concrete fix is:

* adopt the reciprocal that produces physically sensible behavior as the **normative Ti definition**
* then rewrite the bench comments and analyzer docs to match that convention exactly

In other words, don’t treat this as “one of two plausible conventions.” Pick one and freeze it.

## My diagnosis in one sentence

Your AC1 pass is behaving sensibly; the mismatch comes from **AC2 not measuring the exact two-port current ratio assumed by the Middlebrook reconstruction, plus a reversed current-ratio orientation**.

## A more rigorous way to structure AC2

I would change the AC2 bench so the shorted loop node is still present, but you place **explicit 0 V current-sense sources on each side of the original break**, so you can directly read:

* current contributed by the amplifier/output side
* current contributed by the feedback/input side
* injected test current

That is much cleaner than inferring DUT current from a KCL combination of `vsense` and `vshort`.

Conceptually:

* keep the loop closed for AC2
* inject the shunt current at the closed-loop node
* insert a **sense element on the output-side branch**
* insert a **sense element on the input-side branch**
* define Ti from those two directly measured branch currents

That removes the ambiguity of whether `I(V_VSHORT)` is really the “returned” current in the theorem.

## Another subtle possibility: the theorem is fine, but the mapping is not

I do **not** think your combined equation is the main problem:

[
\frac{1}{1+T}=\frac{1}{1+T_v}+\frac{1}{1+T_i}
]

That is the right kind of reconstruction. The problem is more likely that your extracted (T_i) is not actually the theorem’s (T_i).

So I would not abandon the combine formula yet. I would fix the port-current measurement first.

## Sanity checks I would add immediately

These are extremely useful for this fixture:

### 1. Closed-loop direct AC reference

Run the loop fully closed with no injection source and directly measure (V(out)/V(inp)).
That gives the gold-standard transfer function for this toy problem.

For this fixture it should match approximately:

[
\frac{gm}{gm+\frac{1}{r_o}+s(C_{in}+C_{load})}
]

If that direct closed-loop AC run lands at the expected (79.6) MHz-ish UGB, your theoretical target is confirmed.

### 2. Low-frequency limit checks

At low frequency:

* (C_{in}) current should vanish
* the AC2 correction should therefore behave in a very specific asymptotic way

If your chosen (T_i) stays finite and ordinary at low frequency, that is suspicious. For this fixture, the current-side correction is fundamentally tied to the input capacitor, so it should reflect that.

### 3. Branch-current conservation check

In AC2, verify numerically over frequency that:

[
I_{inj} = I_{out_branch} + I_{in_branch}
]

with the exact sign convention spelled out.
If that does not hold cleanly, the bench is not measuring the right currents.

## Why the remaining 8% error is not the main story

The +7.96% error with `Ti_inverse` is probably not the true mystery. Once you are in the right ballpark, the residual error can come from:

* branch-current definition mismatch
* sign/orientation inconsistency
* using unity-crossing of reconstructed return ratio versus direct closed-loop bandwidth
* interpolation details around the crossing

But the real structural problem is that your current pass is still underdefined.

## My recommendation

I would do this next:

1. **Freeze the exact theoretical target** with a direct closed-loop AC run.
2. **Redesign AC2** so the two sides of the former cut each have their own explicit current-sense element.
3. **Define one canonical Ti orientation** and delete the alternative.
4. Add an analyzer self-check:

   * low-frequency asymptote
   * KCL balance at the injection node
   * whether the chosen Ti is the reciprocal of the discarded one

## Bottom line

Your agent did not “fail” in a random way. It actually found something meaningful:

* **AC1 is correctly seeing only (C_{load})**.
* The correction from (C_{in}) is supposed to come from AC2.
* Your AC2 bench and Ti definition are still **port-quantity ambiguous**.
* The fact that the reciprocal convention works better is the smoking gun that the **current ratio is flipped relative to the reconstruction formula**.

So I would focus on **reformulating AC2 around explicit branch-current sensing across the original cut**, not on changing simulators or abandoning the Middlebrook method.

If you want, I can help you derive a **fully explicit symbolic two-pass formulation for this exact gm-ro-cin fixture**, so you have a gold-standard expression for (T_v), (T_i), and the reconstructed (T) before touching the bench again.
