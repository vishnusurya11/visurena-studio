"""How long a cue is allowed to run, and why that is the only knob here.

`max_duration` is a CAP, not a target and not a seed.  The node's own tooltip
says "Maximum duration in seconds; the model can end the song earlier", the AR
loop stops on `<|audio_end|>` or at the frame cap, and seven delivered cues
under a 150 s cap ended of their own accord at 101.9, 118.8, 128.5, 132.4,
132.4, 137.8 and 146.8 s.  The old docstring here called it "a seed, not a
ceiling" and pinned 150; four of five measured cues then ran 128-150 s against
a sheet documented as "about a hundred seconds", and the cut had to stretch to
meet them.

So it is pinned at the trailer's real need instead.  The staircase in
`music_tone.STAIRCASE` is 38 bars plus a tail: at 92-100 BPM that is 101-104 s
with the title hit at 95% of the runtime, which is exactly where
`beatmap.title_moment` looks for it.

The section count is what actually decides length, and the old "~11.1 s per
section" figure was measured while every section carried sung prose -- the
per-section time was the time to SING the note.  With a `(instrumental)` sheet
that number has to be re-measured, so nothing here depends on it any more.
"""
from __future__ import annotations

PINNED_DURATION = 108
"""The cap, pinned once and left alone.

38 bars plus a five-second tail lands at 101-104 s across 84-120 BPM; 108
gives the model a few seconds of headroom to finish its own decay and cuts a
runaway off before the trailer has to stretch to it.  Iteration happens on
seed, never on this number: waveform correlation between the same caption
rendered at 30, 60 and 150 s was -0.03, so changing it re-rolls the whole
composition.
"""
