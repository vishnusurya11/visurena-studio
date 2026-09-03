---
name: trailer-assemble
description: The cut, the grade, the mix, and the gates - including three ffmpeg traps that cost hours.
---

# Assemble

`studio/trailer_assemble.py`, `scripts/trailer/assemble.py`, `scripts/trailer/qc.py`.

## The cut

Shot lengths follow the arc measured across 50 released trailers: opens ~1.50s,
RISES to 1.33s for a breath around a third in, falls to a 0.54s trough at
85-90%, then DECELERATES into a ~3.0s hold. Loudness peaks in the same 80-90%
band. Stretch 2.5x for the literary register.

The arc is a **diagnostic prior, not a target** — no ASL makes a trailer better.
What IS a defect is uniformity, and it is a generated pipeline's default because
clips come back at one fixed size. `assemble` refuses a cut whose shots are all
the same length.

Straight cuts. "Dips to black create separation, cuts create connection."

## The grade

The prompt buys intent, not exposure — a verbatim grade string in every prompt
still gave clips spanning **11.9 to 48.4** luma. Match to one hero clip: the
median of the set, floored at **32**, matching spread as well as mean because
correcting brightness alone leaves flat clips flat.

The floor is 32 and not something brighter because the measured corpus median
is **28/255** with a 5th percentile of 3.2 — trailers ARE dark. A floor of 58
washes out exactly the gloom the material wants.

## Three ffmpeg traps

**`alimiter` re-levels by default.** Auto-level is ON: it limits, then pushes
the result back up. Tightening the limit made the mix LOUDER — peaks went
−0.55 → +0.53 → +0.95 dBTP across three attempts. Always
`alimiter=limit=N:level=disabled`. Peaks rising as the limit falls means the
model is wrong, not the setting: measure the SOURCES. The MiniMax bed arrives
at **0.00 dBTP** already clipping, and a synthesised impact measured **+0.72**
before anything was mixed with it.

**The mix never terminates.** `apad` makes the bed infinite, `amix` defaults to
`duration=longest`, and `-shortest` does not reliably bound a filter-graph
output. It ran 45 minutes at a fixed byte count and I misread it once as slow
and once as dead. Bound it with an explicit `-t`; the same mix then finishes in
2 seconds. **A process that neither finishes nor errors is the hardest failure
to read.**

**The analysis must run the WHOLE graph.** Passing only the last link
referenced `[bedpad]` and `[cue0]` without the entries defining them, so ffmpeg
errored, the JSON parse returned `{}`, and the gain defaulted to 0.0 through a
silent `except`. Every mix was unnormalised. A missing measurement RAISES.

Do not chain normalisers: `loudnorm` only enters linear mode when
`measured_LRA <= target_LRA`, and a trailer cue is far wider than the default
7 LU, so it falls back to dynamic and re-gains. Measure once, compute one gain,
apply it, keep a disabled-auto-level limiter as a net.

## Gates (`qc.py`)

shot lengths vary · every shot reference-bound · true peak ≤ −1.0 dBTP ·
integrated near −14 LUFS · longest ≥2x shortest · dynamic range ≥20 dB ·
≥12 shots · the title card fits the frame.

Assembly degrades rather than refusing: a missing beat falls back to a
neighbouring take, deterministically, above a 60% floor. One failed render at
4am should cost variety, not the whole trailer.

## Sound design is synthesised, not generated

Stable Audio 3 measured **12.7 dB short of sub** — its ≤60 Hz peak at −15.5 dB
against −2.8 in the mids, with every "deep" and "chest-heavy" adjective ignored
below 120 Hz. `studio/sfx.py` synthesises sub-drop, riser and impact in ffmpeg:
sample-exact duration, deterministic envelope, and the sub actually present
(−2.2 dB below 60 Hz against −14.7 above 120). Generate the DIEGETIC layer;
synthesise the DESIGNED layer.
