"""The mix, made from the page: the bed STOPS where the trailer speaks.

THE COMPLAINT THIS EXISTS TO ANSWER: "all I hear is music too loud... no
dialogues", on a cut that had four spoken lines in it.  The old path ducked
the bed by `DUCK_DEPTH_DB` 10, capped at 18.  Ten decibels down is still a
full orchestra sitting on top of a cloned voice, and a cloned voice is quieter
and less present than a recorded one to begin with.

The trade's own move is not a duck.  A trailer editor cutting comedy stops the
music on the downbeat so the reaction line lands -- the score is OUT, the line
is alone, the score returns.  The page already writes those moments ("the
watch stops dead under the line"), and `script_cue.spoken_windows` knows where
every one of them is, so the bed can leave the line the whole room.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from studio.trailer_assemble import (LIMITER_MARGIN, TARGET_LUFS, TARGET_TP, _ffmpeg,
                                     db_to_linear, limiter)

STOP_DB = 40.0
"""How far the bed goes down where a line plays.  Not a duck: 40 dB is out.
The bed is still THERE -- its tail and its room keep the cut from sounding
like a hole -- but nothing of it competes with the voice."""

STOP_ATTACK = 0.12
"""Seconds for the bed to clear.  Fast enough to be out before the first
syllable, slow enough that the drop is not itself an event."""

STOP_RELEASE = 0.45
"""Seconds for the bed to come back after the line, musical rather than
mechanical."""

LEAD_IN = 0.10
"""The bed starts clearing this long before the line opens its mouth."""


def ramp_expr(start: float, end: float) -> str:
    """1 inside the window, 0 outside, ramped at both ends -- as an ffmpeg
    expression.  Commas are escaped: a bare comma inside a filter argument
    ends the filter."""
    opened, closed = start - LEAD_IN, end
    return (rf"max(0\,min(1\,min((t-{opened:.3f})/{STOP_ATTACK:.3f}\,"
            rf"({closed + STOP_RELEASE:.3f}-t)/{STOP_RELEASE:.3f})))")


def bed_expr(windows: list[tuple[float, float]], stop_db: float = STOP_DB) -> str:
    """The bed's gain over the whole trailer: full, except where it speaks."""
    if not windows:
        return "1"
    deepest = "max(" + "\\,".join(ramp_expr(a, b) for a, b in windows) + ")" \
        if len(windows) > 1 else ramp_expr(*windows[0])
    floor = db_to_linear(-stop_db)
    return f"(1-(1-{floor:.6f})*{deepest})"


def line_inputs(lines: list[tuple[float, Path]]) -> list[str]:
    return [arg for _, path in lines for arg in ("-i", str(path))]


def line_filters(lines: list[tuple[float, Path]]) -> list[str]:
    """Each spoken line laid at the second the page put it."""
    return [f"[{i}:a]aresample=48000,adelay={int(at * 1000)}|{int(at * 1000)},"
            f"volume={db_to_linear(-1.0):.4f}[v{i}]"
            for i, (at, _) in enumerate(lines, start=2)]


def premix(bed: Path, lines: list[tuple[float, Path]], windows: list[tuple[float, float]],
           out: Path, seconds: float) -> Path:
    """Bed plus lines, with the bed out of the way where the lines are."""
    chains = [f"[1:a]aresample=48000,apad,volume='{bed_expr(windows)}':eval=frame[bed]"]
    chains += line_filters(lines)
    voices = "".join(f"[v{i}]" for i in range(2, 2 + len(lines)))
    chains.append(f"[bed]{voices}amix=inputs={1 + len(lines)}:normalize=0:"
                  f"dropout_transition=0[mixed]")
    _ffmpeg(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
             "-i", str(bed), *line_inputs(lines),
             "-filter_complex", ";".join(chains), "-map", "[mixed]",
             "-t", f"{seconds:.3f}", "-c:a", "pcm_s16le", str(out)],
            f"premixing {out.name}")
    return out


def measured(audio: Path) -> dict:
    """Integrated loudness and true peak of a finished premix."""
    proc = subprocess.run(
        ["ffmpeg", "-v", "info", "-i", str(audio), "-af",
         "loudnorm=print_format=json", "-f", "null", "-"],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    body = proc.stderr[proc.stderr.rfind("{"):proc.stderr.rfind("}") + 1]
    found = json.loads(body)
    return {"lufs": float(found["input_i"]), "peak": float(found["input_tp"])}


def gain_for(reading: dict) -> float:
    """The one gain that lands the programme in the delivery band, never
    pushing its true peak past the ceiling the limiter then guards."""
    return min(TARGET_LUFS - reading["lufs"], TARGET_TP - reading["peak"])


def master(picture: Path, audio: Path, gain_db: float, out: Path) -> Path:
    """Picture and mix together, levelled and peak-guarded."""
    _ffmpeg(["ffmpeg", "-y", "-v", "error", "-i", str(picture), "-i", str(audio),
             "-af", f"volume={db_to_linear(gain_db):.5f},{limiter(TARGET_TP)}",
             "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-shortest", str(out)],
            f"mastering {out.name}")
    return out


def mix(picture: Path, bed: Path, lines: list[tuple[float, Path]],
        windows: list[tuple[float, float]], work: Path, out: Path,
        seconds: float) -> Path:
    """The finished trailer: the page's picture, its cue, and its voices."""
    Path(work).mkdir(parents=True, exist_ok=True)
    mixed = premix(bed, lines, windows, Path(work) / "premix.wav", seconds)
    return master(picture, mixed, gain_for(measured(mixed)), Path(out))
