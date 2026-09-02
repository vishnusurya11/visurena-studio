# What in tonight's work is generalizable

Flagged per the standing goal, not built — each is a standalone package or
short paper, and none is specific to this repo.

## 1. `cue-beatmap` — conform picture to music that was generated, not composed

**The problem it solves.** A generated cue does not put its hit where the
prompt asked. Our own evidence: the previous trailer's title card sat **5.29s**
before its cue's +37 LU impact, so the braam landed inside the button shot;
and the current pipeline would have missed by 0.85s until it was caught. Both
came from conforming picture to the *section plan* instead of the *audio*.

**What it is.** Decode the audio, read the envelope, emit a JSON event map —
onset grid, structural impacts, stopdowns, and the title moment (a late hit
with silence in front of it) — plus editor markers and a `--conform` mode
reporting the offset needed to land a picture event on a music event.

**Why it doesn't exist yet.** Beat-tracking libraries find tempo. This finds
the four or five moments an *editor* cares about, and it is the missing piece
for every "AI generates the music, then AI cuts to it" pipeline now being
built. `studio/beatmap.py` is the working core, ~120 lines, ffmpeg + numpy.

## 2. A trailer-SFX synthesis toolkit, and the measurement behind it

**The citable finding:** *the leading open sound-effects model does not
generate sub-bass, measured.* Asked for a "deep ominous impact boom", Stable
Audio 3 returned a thump with its ≤60 Hz peak at −15.5 dB against −2.8 dB in
the mids — **12.7 dB short**, with every "deep" and "chest-heavy" adjective
ignored below 120 Hz. That is a training-distribution ceiling, and it is
exactly the band a trailer lives in.

**The artifact:** deterministic ffmpeg generators for the designed layer
(sub-drop, riser, three-tier impact) with band-energy assertions in the tests.
Measured here: `sub_drop` at −2.2 dB below 60 Hz against −14.7 dB above 120 Hz
— the exact inverse of the generated boom. Sample-exact duration and a
deterministic envelope are the other two things generation cannot give you.

## 3. "The Shape of a Trailer" — the measured editing and loudness arcs

Redfern published the dataset (CC-BY, 50 horror trailers); as far as the
research could find, **nobody has published the arc**. Shot length opens ~1.50s,
*rises* to 1.33s for a breath around a third in, falls to a 0.54s trough at
85–90%, then *decelerates* into a ~3.0s final hold. Loudness peaks in the same
80–90% band and collapses in the last tenth. The two arcs coinciding is the
result, and it yields a concrete, testable prescription — plus a validator
that scores an EDL or a finished video against it.

Note the correction that has to travel with it: Lieu is explicit that no
average shot length makes a trailer better or worse, so **the arc is a
diagnostic prior, not a target**. What it does license is the negative claim:
uniform shot length is a defect, and it is a generated pipeline's default.

## 4. A smaller one: identity binding as a contract

The bug this whole stage exists to fix generalizes to every reference-driven
generation pipeline: *a check whose expectation is derived from the thing it
is checking cannot fail*, and *an agent's output is INPUT, not a guarantee*.
`ShotSpec.unbound_cast()` asks what the JOB will carry, never what the prompt
says. Twelve good reference sheets existed for eight months and nothing ever
passed one to a keyframe.
