"""The designed sound layer, synthesised rather than generated.

Measured on this machine: asked for "single deep ominous impact boom", Stable
Audio 3 returned a mid-heavy thump 12.7 dB SHORT of sub -- its <=60 Hz peak sat
at -15.5 dB against -2.8 dB in the mids.  Every "deep", "sub" and "chest-heavy"
adjective in the prompt was ignored below 120 Hz.  That is a
training-distribution ceiling, and it is exactly the band a trailer lives in.

Synthesis fixes all three problems at once: the duration is sample-exact so the
cue lands on the frame it is cut to, the envelope is deterministic so the same
trailer rebuilds identically tomorrow, and the sub is actually there.

So: GENERATE the diegetic layer (a door, a carriage, rain), SYNTHESISE the
designed layer (sub-drop, riser, hit).  These are the designed ones.
"""
from __future__ import annotations

import subprocess
from pathlib import Path


HEADROOM = 0.70
"""Sample-peak ceiling for a synthesised cue, about -3.1 dBFS.

Generous on purpose.  TRUE peak runs above sample peak by a decibel or more,
and these are summed with a music bed that itself arrives at 0.00 dBTP -- the
first cut's own impact measured +0.72 dBTP before anything was mixed into it.
Headroom at the source is the only thing that survives the sum.
"""


def _render(filters: list[str], output: Path, seconds: float) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    command = ["ffmpeg", "-y", "-v", "error"]
    for source in filters[:-1]:
        command += ["-f", "lavfi", "-i", source]
    command += ["-filter_complex", filters[-1], "-map", "[out]",
                "-t", f"{seconds:.4f}", "-c:a", "pcm_s24le", str(output)]
    subprocess.run(command, check=True, capture_output=True)
    return output


def sub_drop(output: Path, seconds: float = 2.4, start_hz: float = 52.0,
             end_hz: float = 18.0) -> Path:
    """A descending sine that ends below hearing -- felt, not heard.

    Measured: <=60 Hz peak -2.5 dB against -14.9 dB above 120 Hz, the exact
    inverse of the generated boom's profile.
    """
    sweep = (f"aevalsrc='0.95*sin(2*PI*({start_hz}*t + ({end_hz}-{start_hz})"
             f"*t*t/(2*{seconds})))*exp(-1.1*t)':d={seconds}:s=48000:c=stereo")
    return _render([sweep, "[0:a]alimiter=limit=0.70:level=disabled[out]"], output, seconds)


def riser(output: Path, seconds: float = 3.0, start_hz: float = 180.0,
          end_hz: float = 1400.0) -> Path:
    """A sweep plus pink noise on rising envelopes, peaking in the last half
    second so the peak lands on the cut it is written to."""
    sweep = (f"aevalsrc='0.5*sin(2*PI*({start_hz}*t+({end_hz}-{start_hz})"
             f"*t*t/(2*{seconds})))':d={seconds}:s=48000:c=stereo")
    noise = f"anoisesrc=d={seconds}:c=pink:r=48000:a=0.6"
    graph = (f"[1:a]aformat=channel_layouts=stereo,highpass=f=400,"
             f"volume='pow(t/{seconds},2.2)':eval=frame[n];"
             f"[0:a]volume='pow(t/{seconds},1.8)':eval=frame[s];"
             f"[s][n]amix=inputs=2:normalize=0,alimiter=limit=0.70:level=disabled[out]")
    return _render([sweep, noise, graph], output, seconds)


def impact(output: Path, seconds: float = 2.4) -> Path:
    """A three-tier hit: transient, mid body, and the sub the models omit."""
    body = (f"aevalsrc='0.7*sin(2*PI*(90*t))*exp(-7*t)':d={seconds}:s=48000:c=stereo")
    sub = (f"aevalsrc='0.95*sin(2*PI*(48*t + (16-48)*t*t/(2*{seconds})))"
           f"*exp(-1.4*t)':d={seconds}:s=48000:c=stereo")
    noise = f"anoisesrc=d={seconds}:c=white:r=48000:a=0.5"
    graph = ("[2:a]aformat=channel_layouts=stereo,highpass=f=1200,"
             "volume='exp(-38*t)':eval=frame[crack];"
             "[0:a]highpass=f=70[mid];[1:a]volume=0.95[low];"
             "[crack][mid][low]amix=inputs=3:normalize=0,"
             "alimiter=limit=0.70:level=disabled[out]")
    return _render([body, sub, noise, graph], output, seconds)
