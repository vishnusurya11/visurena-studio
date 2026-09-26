"""Cutting the picture to the measured music, and mixing it.

Straight cuts only.  Over-reliance on dissolves and fades is the most-named
amateur tell, and the semantic rule is that dips to black create separation
while cuts create connection -- so a dissolve has to MEAN something, and here
nothing means it.

Where a shot's footage comes from matters as much as its length: a beat used
three times must show three different moments of its take, or the repetition
reads as a stutter instead of a motif.
"""
from __future__ import annotations

import math

import json
import os
import re
import subprocess
from pathlib import Path
from typing import NamedTuple

def _ffmpeg(command: list[str], what: str) -> None:
    """Run ffmpeg and, on failure, say WHY.

    capture_output swallows stderr, so a failed encode surfaced only as a bare
    CalledProcessError with the command echoed back -- unactionable.  ffmpeg
    always explains itself; the explanation just has to be let through.
    """
    result = subprocess.run(command, capture_output=True, text=True, errors="replace")
    if result.returncode != 0:
        raise RuntimeError(f"{what} failed: " + result.stderr.strip()[-800:])


TARGET_LUFS = -14.0
"""Integrated loudness for online delivery."""

TARGET_TP = -2.0
"""True-peak ceiling.  EBU R128 asks for -1.0; -2.0 leaves room for the
intersample peaks the AAC encoder introduces after this measurement."""

LIMITING_DB = 2.0
"""How much peak limiting the master may do to bring the average up.

Was 5.5.  Five and a half decibels of gain reduction is not a safety net, it
IS the sound -- it is what flattens a trailer into a wall, and run 10's master
came out at crest 12.6 dB with its loudest moment at 53% of the runtime.  The
allowance is back to 2.0 and the average is found EARLIER instead: the bed is
peak-limited to -1 dBTP before the sum (F), which is where the headroom the
old allowance was buying actually comes from.

Bounded, and verified after the fact rather than trusted: the QC gate measures
the finished file's true peak, so overreach here fails loudly."""

TP_LINEAR = 0.80
"""A final sample-peak safety net at about -1.9 dBFS.

Note `level=disabled` wherever alimiter is used.  Its auto-level is ON by
default: it limits and then re-levels the result back up, so LOWERING the
limit made the mix LOUDER -- peaks went -0.55 -> +0.53 -> +0.95 dBTP across
three attempts while I kept tightening a limiter that was undoing itself."""

BED_TP = -1.0
"""True-peak ceiling on the bed BEFORE anything is summed into it (F).

Run 10 handed the mix a bed at +0.4 dBTP and a cue at +0.2, then asked the
master limiter to find 5.5 dB of average out of what was left.  Headroom is
made at the source or it is not made at all."""

LINE_TP = -3.0
"""True-peak ceiling on a levelled line (B).

A line is the one element that gets GAIN applied to it, so it is the one
element that can clip -- and run 10's did: 3,096 samples at full scale."""

LIMITER_MARGIN = 0.5
"""alimiter is a SAMPLE-peak limiter and every ceiling here is a TRUE-peak
one.  Intersample peaks run about half a decibel over sample peaks on
band-limited material, so the limiter is asked for that much less than the
ceiling that has to survive the measurement."""


def db_to_linear(db: float) -> float:
    """A decibel level as the linear amplitude ffmpeg's limiters take."""
    return round(10.0 ** (db / 20.0), 4)


def limiter(ceiling_db: float) -> str:
    """An `alimiter` holding a true-peak ceiling, with its auto-level off."""
    return f"alimiter=limit={db_to_linear(ceiling_db - LIMITER_MARGIN)}:level=disabled"

HANDLE = 0.25
"""Six frames of slack past the shot.

`segment_start` snaps its seek UP onto the frame grid and needs the shot to
still fit inside the take; a take cut exactly to length loses that fight by
up to one frame.  Part of the take tax the frame budget prices."""

HEAD_TRIM = 2.6
"""Seconds discarded from the head of every take.

Measured on the first bound clip: H3's reference-to-video path OPENS on the
reference image itself and animates it -- for roughly 2.1s the shot is the
character standing on the plain grey sheet backdrop -- before moving into the
scene.  That is the binding working, not failing; the reference is being held
hard.  But it is unusable footage, and cutting a trailer shot from it would
put a photographer's backdrop on screen.
"""


def segment_start(usage: int, of_uses: int, need: float, available: float,
                  head: float = HEAD_TRIM) -> float:
    """Where in a take to start this use of it.

    Uses are spread evenly across whatever room the take has after the head
    trim and the shot length are taken out, so a beat seen three times shows
    three genuinely different moments rather than three clamped to one frame.
    """
    room = max(available - head - need, 0.0)
    if room <= 0:
        return _on_frame(min(head, max(available - need, 0.0)), available, need)
    if of_uses <= 1:
        return _on_frame(head + room / 2, available, need)
    share = min(usage, of_uses - 1) / (of_uses - 1)
    return _on_frame(head + share * room, available, need)


def _on_frame(start: float, available: float, need: float, fps: int = 24) -> float:
    """Snap a seek onto the frame grid, DOWNWARD, and keep it inside the take.

    `round(start, 3)` looked like tidying and cost a frame on every single
    shot -- 23 of 24 in the first assembly, 0.958s of drift, enough for the
    gate to refuse the build.  `-ss 7.917` lands between frames: ffmpeg begins
    at the next whole frame, at 7.9583, but `-t` still measures from 7.917, so
    the 0.041s of fraction is subtracted from the end.  One frame, every time.

    Snapping UP, because the two bounds round in opposite directions.  The head
    is a FLOOR -- HEAD_TRIM exists to skip the reference leak, and 2.6s floored
    to a frame is 2.5833s, back inside the leak it was written to avoid.  The
    tail is a CEILING, so when snapping up would walk off the end of the take we
    fall back to the last whole frame that still fits.
    """
    import math

    latest = max(available - need, 0.0)
    snapped = math.ceil(min(start, latest) * fps) / fps
    if snapped > latest:
        snapped = math.floor(latest * fps) / fps
    return max(0.0, snapped)


def clip_seconds(video: Path) -> float:
    """Duration of a rendered clip, read from ffmpeg."""
    result = subprocess.run(["ffmpeg", "-i", str(video), "-f", "null", "-"],
                            capture_output=True, text=True, errors="replace")
    for line in reversed(result.stderr.splitlines()):
        if "time=" in line:
            stamp = line.split("time=")[1].split()[0]
            hours, minutes, seconds = stamp.split(":")
            return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
    return 0.0


def frames_arg(seconds: float, fps: int = 24) -> str:
    """The `-t` value that renders exactly the frames this duration names.

    MEASURED against ffmpeg, not assumed: `-t` keeps every frame whose
    timestamp falls BELOW t, so the rendered count is `ceil(t * fps)` -- `-t
    2.208` gives 53 frames and `-t 2.2292` gives 54.  A duration therefore
    rounds the picture UP, never down, and an unquantised plan asks for a
    fractional frame that the file then rounds to something the plan does not
    know about.  Thirty-three such roundings drifted the shipped cut by 1.28s.

    N frames means landing in ((N-1)/fps, N/fps] -- an interval open at the
    bottom and CLOSED at the top, so the decimal has to be truncated rather
    than rounded.  One frame at 24 fps is 0.0417s and `.4f` rounds it up to
    0.0417, one ten-thousandth past the top of its own interval, which renders
    two frames.  Truncating spends 1e-4 of the 4.17e-2 available below.
    """
    frames = round(seconds * fps)
    if frames <= 0:
        return "0"
    return f"{math.floor(frames / fps * 10_000) / 10_000:.4f}"


def output_bound(seconds: float | None) -> list[str]:
    """How the mix's own output is made to end.

    MEASURED on episode 1, 2026-09-12: `-t` and `-shortest` together cost four
    frames of picture.  The cut went into the mix at 3601 frames and came out
    at 3597, and the concat that follows then HELD the last picture frame for
    the 0.17 s of sound that had nowhere to sit -- a pause before the title
    card that nobody cut, and the one the owner saw.  `-t` alone renders every
    frame the duration names, so `-shortest` is left to the unbounded case it
    was written for: the bed is `apad`ed to an infinite stream, and with no
    duration to render to nothing else ends the file.
    """
    return ["-t", frames_arg(seconds)] if seconds else ["-shortest"]


def extract_filter(width: int, height: int, fps: int, grade: str = "", pre: str = "") -> str:
    """`pre` runs on the source before it is conformed (the episode's gutter
    guard crops there, so the crop is scaled back up to the full frame)."""
    return (f"{pre + ',' if pre else ''}scale={width}:{height}:force_original_aspect_ratio=increase,"
            f"crop={width}:{height},fps={fps},{grade + ',' if grade else ''}format=yuv420p")


def extract(video: Path, start: float, seconds: float, output: Path,
            width: int, height: int, fps: int, grade: str = "", pre: str = "") -> Path:
    """Cut one shot out of a take, conformed to the trailer's single format.

    Every shot is forced to the same size, rate and pixel format here.  The
    first cut mixed aspect ratios, and a concat demuxer will happily join
    mismatched streams into something that plays wrong.
    """
    output.parent.mkdir(parents=True, exist_ok=True)
    _ffmpeg(
        ["ffmpeg", "-y", "-v", "error", "-ss", frames_arg(start, fps), "-i", str(video),
         "-t", frames_arg(seconds, fps), "-an",
         "-vf", extract_filter(width, height, fps, grade, pre),
         "-c:v", "libx264", "-preset", "fast", "-crf", "17", str(output)],
        f"extracting {output.name}")
    return output


def title_card(title: str, output: Path, seconds: float, width: int, height: int,
               fps: int, font: str | None = None) -> Path:
    """The title, held on black.

    Text goes through a FILE, never inline: ffmpeg's drawtext silently drops
    apostrophes from an inline `text=` argument, and it does it without an
    error, on the one frame the audience is guaranteed to read.
    """
    output.parent.mkdir(parents=True, exist_ok=True)
    text_file = output.with_suffix(".txt")
    text_file.write_text(title.upper(), encoding="utf-8")
    escaped = str(text_file).replace("\\", "/").replace(":", r"\:")
    draw = (f"drawtext=textfile='{escaped}':fontcolor=white:fontsize={height // 14}:"
            f"x=(w-text_w)/2:y=(h-text_h)/2:line_spacing=12")
    if font:
        draw += f":fontfile='{font}'"
    _ffmpeg(
        ["ffmpeg", "-y", "-v", "error", "-f", "lavfi",
         "-i", f"color=c=black:s={width}x{height}:r={fps}:d={seconds + 0.5:.3f}",
         "-vf", f"{draw},format=yuv420p", "-c:v", "libx264", "-preset", "fast",
         "-crf", "16", "-t", frames_arg(seconds), str(output)],
        "rendering the title card")
    return output


def listing_lines(segments: list[Path], listing: Path) -> list[str]:
    """The concat demuxer resolves a relative entry against the LIST FILE's
    directory, not the cwd -- so every entry is written relative to it.  A
    repo-relative segment written verbatim doubled its own path (run 6)."""
    base = listing.resolve().parent
    return [f"file '{Path(os.path.relpath(p.resolve(), base)).as_posix()}'"
            for p in segments]


def concat(segments: list[Path], output: Path) -> Path:
    """Join the shots with hard cuts and no re-encode."""
    listing = output.with_suffix(".txt")
    listing.write_text("\n".join(listing_lines(segments, listing)), encoding="utf-8")
    _ffmpeg(
        ["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
         "-i", str(listing), "-c", "copy", str(output)],
        "concatenating the shots")
    return output


def _measure_loudness(command: list[str]) -> dict:
    """Run a loudnorm analysis pass and return its JSON report."""
    result = subprocess.run(command, capture_output=True, text=True, errors="replace")
    tail = result.stderr[result.stderr.rfind("{"):result.stderr.rfind("}") + 1]
    try:
        return json.loads(tail)
    except ValueError:
        return {}


def mix(picture: Path, bed: Path, cues: list[tuple[float, Path]], output: Path,
        seconds: float | None = None) -> Path:
    """Lay the bed and the designed hits under the cut, and land the loudness.

    Two-pass loudnorm is deliberate: single-pass runs in DYNAMIC mode, which
    reshapes the programme's dynamics instead of applying one gain -- and the
    dynamics are the thing the cue was chosen for.  The limiter sits at 0.891
    (-1.0 dBTP) because the previous trailer measured -0.03 dBTP, about a dB
    over the EBU R128 ceiling.
    """
    inputs = ["-i", str(picture), "-i", str(bed)]
    for _, path in cues:
        inputs += ["-i", str(path)]
    parts = ["[1:a]aresample=48000,apad[bedpad]"]
    mixed = ["[bedpad]"]
    for index, (when, _) in enumerate(cues):
        label = f"cue{index}"
        parts.append(f"[{index + 2}:a]aresample=48000,"
                     f"adelay={int(when * 1000)}|{int(when * 1000)}[{label}]")
        mixed.append(f"[{label}]")
    # `apad` makes the bed an INFINITE stream and amix defaults to
    # duration=longest, so the mix never ends -- and `-shortest` does not
    # reliably terminate a filter-graph output.  The first run of this hung at
    # exactly 25,690,160 bytes and stayed there.  An explicit `-t` bounds it.
    # Measure, compute one exact gain, apply it.  Chaining normalisers does
    # not work here: ffmpeg's loudnorm only enters LINEAR mode when
    # measured_LRA <= target_LRA, and a trailer cue's range is far wider than
    # the default 7 LU -- so it silently falls back to DYNAMIC, re-gains, and
    # a two-pass attempt came out LOUDER than the single pass (+0.53 dBTP
    # against -0.55).  alimiter cannot rescue it either, being sample-peak
    # while the ceiling that matters is true-peak.
    #
    # One deterministic gain, bounded by whichever limit binds first, is both
    # simpler and actually correct.
    base = f"{''.join(mixed)}amix=inputs={len(mixed)}:normalize=0:duration=first"
    bound = ["-t", frames_arg(seconds)] if seconds else []
    # The analysis must run the WHOLE graph, not just its last link.  Passing
    # `base` alone referenced [bedpad] and [cue0] without the entries that
    # define them, so ffmpeg errored on undefined labels, the JSON parse
    # returned {}, and the gain silently defaulted to 0.0 -- leaving every mix
    # unnormalised while the failure looked like a tuning problem.
    analysis = _measure_loudness(
        ["ffmpeg", "-v", "info", *inputs, "-filter_complex",
         ";".join(parts + [f"{base},loudnorm=I={TARGET_LUFS}:TP={TARGET_TP}"
                           f":print_format=json[out]"]),
         *bound, "-map", "[out]", "-f", "null", "-"])
    if "input_i" not in analysis or "input_tp" not in analysis:
        raise RuntimeError(
            "loudness analysis produced no measurement; refusing to guess a "
            f"gain. ffmpeg reported: {sorted(analysis) or 'nothing'}")
    to_target = TARGET_LUFS - float(analysis["input_i"])
    to_ceiling = TARGET_TP - float(analysis["input_tp"])
    gain = min(to_target, to_ceiling + LIMITING_DB)
    parts.append(f"{base},volume={gain:.2f}dB,alimiter=limit={TP_LINEAR}:level=disabled[out]")
    _ffmpeg(
        ["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", ";".join(parts),
         "-map", "0:v", "-map", "[out]", "-c:v", "copy", "-c:a", "aac", "-b:a", "256k",
         "-ar", "48000", *output_bound(seconds), str(output)],
        "mixing the trailer")
    return output


DUCK_DEPTH_DB = 10.0
"""The least the bed loses under a line, full band (B: duck >= 10 LU).

Run 10 ducked 250-4000 Hz only -- `acrossover` split the bed in three and
compressed the middle -- so the pulse and the air kept hitting straight
through the one spoken line, and the deepest the bed ever got was 6.2 LU.
A band-split duck is what you do when the bed is the point.  Here the LINE is
the point."""

DUCK_ATTACK = 0.02
"""Seconds for the duck to reach full depth.  Run 10 used 160 ms, so the
first third of "You have been..." played over a -9 LUFS bed."""

DUCK_RELEASE = 0.8
"""Seconds for the bed to come back.  Inside the 600-900 ms norm: shorter
pumps, longer eats the next line's room."""

DUCK_PREDELAY = 0.15
"""Seconds the duck opens BEFORE the line does.

This is the lookahead, and it is free: the windows are known before a single
sample is rendered, so the envelope can simply start early instead of a
compressor guessing at it from a key it has not heard yet."""

BED_UNDER_LINE = -24.0
"""Momentary LUFS the bed may reach under a line (B), including the first
200 ms.  With the line at -16 that is the 8 LU of separation the norm asks
for; the depth per line is whatever gets THIS bed down to it.

A CEILING, so the depth is sized against the loudest moment of the window
and not its average.  Measured on run 10's bed: the mean momentary under its
one line is -14.8 LUFS and the peak is -9.1, because the line was placed on a
bar the cue puts a hit on.  A duck sized to the mean leaves that hit 5.7 LU
above where the rule says the bed has to be, and the rule reads as met."""

DUCK_DEPTH_MAX = 18.0
"""The most the bed will duck for one line.

Past about this the bed is not ducked, it is gone, and the hole is a worse
artefact than the bed.  A line that would need more than this was placed on
a hit -- which is a PLACEMENT fault, and QC's `bed_under_line_lu` names it
instead of the mix hiding it under a gate."""

LINE_TARGET_LUFS = -16.0
"""Integrated loudness a line is levelled to (B: -20..-15).

An absolute target, not a gap: run 9 set the line against the bed BEFORE the
duck and run 10 measured the result at -8.2 LUFS -- the loudest point of the
whole trailer was a piece of dialogue. The gap is made by the duck, which
knows exactly how deep it has to go, not by shouting."""

LINE_OVER_BED = 8.0
"""LU a line rides over the DUCKED bed in its window (B: 8-12).

Derived, not tuned: LINE_TARGET_LUFS - BED_UNDER_LINE.  Run 10's QC read
9.92 here and passed -- measured after the line had already clipped, against
a bed ducked in one band only."""

HARD_OUT_GATE = 0.02
"""Seconds the bed takes to stop.  Twenty milliseconds is a STOP -- below the
~50 ms where the ear starts hearing a fade.  Run 10 faded out over 3 s, which
is the cue ending, not the trailer stopping."""

GAIN_LIMIT = 20.0


def _ramp(t: float, start: float, end: float, attack: float, release: float) -> float:
    """0 before `start`, 1 across the hold, back to 0 `release` after `end`."""
    return max(0.0, min(1.0, (t - start) / attack, (end + release - t) / release))


def duck_db(t: float, windows: list[tuple[float, float, float]],
            attack: float | None = None, release: float | None = None,
            predelay: float | None = None) -> float:
    attack = DUCK_ATTACK if attack is None else attack
    release = DUCK_RELEASE if release is None else release
    predelay = DUCK_PREDELAY if predelay is None else predelay
    """The gain reduction the bed carries at `t`, in dB, over every window.

    `windows` are (line start, line end, depth); the deepest one wins, so
    two lines close together do not stack into a hole.
    """
    return -max((depth * _ramp(t, at - predelay, end, attack, release)
                 for at, end, depth in windows), default=0.0)


def _ramp_expr(start: float, end: float, attack: float, release: float) -> str:
    """`_ramp` as an ffmpeg expression.  Commas are escaped because a comma
    inside a filter argument otherwise ends the filter."""
    return (rf"max(0\,min(1\,min((t-{start:.4f})/{attack:.4f}\,"
            rf"({end + release:.4f}-t)/{release:.4f})))")


def duck_expr(windows: list[tuple[float, float, float]], attack: float | None = None,
              release: float | None = None, predelay: float | None = None) -> str:
    attack = DUCK_ATTACK if attack is None else attack
    release = DUCK_RELEASE if release is None else release
    predelay = DUCK_PREDELAY if predelay is None else predelay
    """The duck as one `volume` expression: a product of per-line envelopes.

    An expression, not `sidechaincompress`, because every number the rule
    asks for -- depth, attack, lookahead, release -- is then EXACTLY what was
    asked for.  A compressor's depth is a consequence of a threshold, a ratio
    and how loud the key happened to be, and run 10's key was quiet.
    """
    return "*".join(
        f"(1-{1 - db_to_linear(-depth):.6f}*{_ramp_expr(at - predelay, end, attack, release)})"
        for at, end, depth in windows) or "1"


def gate_expr(at: float, ramp: float = HARD_OUT_GATE) -> str:
    """A fall to nothing at `at`, over `ramp` seconds: a stop, not a fade."""
    return rf"max(0\,min(1\,({at:.4f}-t)/{ramp:.4f}))"


def bed_expr(windows: list[tuple[float, float, float]], hard_out: float | None = None) -> str:
    """The whole bed envelope: ducked under every line, stopped at the hard out."""
    parts = [duck_expr(windows)] + ([gate_expr(hard_out)] if hard_out is not None else [])
    return "*".join(part for part in parts if part != "1") or "1"


def bed_gain(t: float, windows: list[tuple[float, float, float]],
             hard_out: float | None = None) -> float:
    """`bed_expr` evaluated in Python: the linear gain the bed carries at `t`."""
    gate = 1.0 if hard_out is None else max(0.0, min(1.0, (hard_out - t) / HARD_OUT_GATE))
    return db_to_linear(duck_db(t, windows)) * gate


def shape_bed(bed: Path, windows: list[tuple[float, float, float]],
              hard_out: float | None, output: Path) -> Path:
    """The bed as the master will hear it: full-band duck under every line, a
    hard out at the last cut, and peak-safe before anything is summed into it.

    With nothing to duck and nothing to stop, the bed is returned as it is: a
    pass through the graph would not be a no-op.
    """
    if not windows and hard_out is None:
        return bed
    _ffmpeg(["ffmpeg", "-y", "-v", "error", "-i", str(bed), "-af",
             (f"aresample=48000,aformat=channel_layouts=stereo,"
              f"volume=volume='{bed_expr(windows, hard_out)}':eval=frame,{limiter(BED_TP)}"),
             "-t", f"{clip_seconds(bed):.3f}", "-c:a", "pcm_s16le", str(output)],
            "shaping the bed under the lines")
    return output


READING = re.compile(r"t:\s*([\d.]+)\s+TARGET.*?M:\s*(-?[\d.]+|-inf)\s+S:\s*(-?[\d.]+|-inf)")


def loudness_readings(path: Path) -> list[tuple[float, float, float]]:
    """(t, momentary, short-term) every 100 ms from ebur128.

    Both windows, from one pass: momentary is 400 ms and answers "is the bed
    out of the way of this line"; short-term is 3 s and is the only one that
    answers "where is the loudest part of the trailer".  Reading only M is
    how run 10's QC could report a level and know nothing of its shape.
    """
    result = subprocess.run(["ffmpeg", "-v", "info", "-nostats", "-i", str(path),
                             "-af", "ebur128", "-f", "null", "-"],
                            capture_output=True, text=True, errors="replace")
    return [(float(t), float(m), float(st)) for t, m, st in READING.findall(result.stderr)]


def momentary(path: Path) -> list[tuple[float, float]]:
    """(t, M) every 100 ms: the momentary loudness QC reads."""
    return [(t, m) for t, m, _ in loudness_readings(path)]


def short_term(path: Path) -> list[tuple[float, float]]:
    """(t, S) every 100 ms.  S is undefined until its 3 s window fills, so
    ebur128 reports about -120 there and the caller drops the head."""
    return [(t, st) for t, _, st in loudness_readings(path)]


def window_loudness(readings: list[tuple[float, float]], start: float, end: float) -> float:
    """Mean momentary loudness over [start, end); refuses to average nothing."""
    inside = [m for t, m in readings if start <= t < end]
    if not inside:
        raise ValueError(f"no loudness readings in {start:.2f}-{end:.2f}s")
    return sum(inside) / len(inside)


def window_peak(readings: list[tuple[float, float]], start: float, end: float,
                default: float = float("-inf")) -> float:
    """The LOUDEST reading in a window.

    A mean says the bed was mostly out of the way of a line; only the peak
    says whether it ever was not.
    """
    return max((m for t, m in readings if start <= t < end), default=default)


def line_windows(plan: dict, lines: list, book: Path) -> list[tuple[float, Path]]:
    """Where each spoken line starts, from the plan.

    `plan["lines"] = [{"index", "at"}]` names a window per voice line; a plan
    without it (the shipped format) carries the text on the shot it plays
    over, so the shot's start is the window.  A line the plan placed nowhere
    was dropped by the plan and is not laid.  Cards have no file to lay.
    """
    by_index = {int(l["index"]): float(l["at"]) for l in plan.get("lines", [])}
    by_text = {s["line"]: float(s["start"]) for s in plan.get("shots", []) if s.get("line")}
    keys = []
    for line in lines:
        if line.card or not line.rel_path:
            continue
        at = by_index.get(line.index, by_text.get(line.text))
        if at is not None:
            keys.append((at, Path(book) / line.rel_path))
    return keys


def integrated(path: Path) -> float:
    """Integrated loudness of one file, LUFS, from ebur128 via loudnorm."""
    return float(_loudnorm(path)["input_i"])


def true_peak(path: Path) -> float:
    """True peak of one file, dBTP, from the same analysis pass."""
    return float(_loudnorm(path)["input_tp"])


def _loudnorm(path: Path) -> dict:
    """loudnorm's analysis of one whole file."""
    return _measure_loudness(["ffmpeg", "-v", "info", "-i", str(path), "-af",
                              "loudnorm=print_format=json", "-f", "null", "-"])


def astats_of(path: Path) -> dict[str, float]:
    """The overall time-domain statistics of one file, by the name astats prints."""
    result = subprocess.run(["ffmpeg", "-v", "info", "-nostats", "-i", str(path), "-af",
                             "astats=measure_perchannel=none", "-f", "null", "-"],
                            capture_output=True, text=True, errors="replace")
    stats: dict[str, float] = {}
    for line in result.stderr.splitlines():
        key, _, value = line.partition("] ")[2].rpartition(":")
        try:
            stats[key.strip()] = float(value)
        except ValueError:
            continue
    return stats


def line_shape(path: Path) -> tuple[float, float, float]:
    """(true peak dBTP, flat factor, crest dB) of one levelled line.

    Flat factor counts runs of identical consecutive samples -- what clipping
    leaves behind, and what run 10's only line measured 24.2 of.  Crest is
    peak over RMS: speech runs 12-18 dB, a square wave runs single digits.
    """
    stats = astats_of(path)
    return (true_peak(path), stats["Flat factor"],
            round(stats["Peak level dB"] - stats["RMS level dB"], 2))


def bed_level(readings: list[tuple[float, float]], start: float, end: float) -> float:
    """The bed's momentary loudness over a window, silence left out: a
    stop-down reads -inf and is not a level to sit over."""
    return window_loudness([(t, m) for t, m in readings if m > -70.0], start, end)


def line_gain(line_lu: float, target: float = LINE_TARGET_LUFS) -> float:
    """The dB that lands a line at its absolute target, bounded.

    Against a TARGET, not against the bed.  Setting it against the bed is what
    put a -8.2 LUFS line into run 10: the window it was placed in happened to
    be the loudest moment of the cue's first half, so the rule said shout.
    """
    return round(max(-GAIN_LIMIT, min(GAIN_LIMIT, target - line_lu)), 2)


def bed_peak(readings: list[tuple[float, float]], start: float, end: float) -> float:
    """The LOUDEST the bed gets in a window, silence left out.

    What the duck is sized against.  The mean says the bed was mostly quiet
    there; the rule a line needs is a ceiling.
    """
    return window_peak([(t, m) for t, m in readings if m > -70.0], start, end,
                       default=BED_UNDER_LINE)


def duck_depth(bed_lu: float, floor: float = BED_UNDER_LINE,
               minimum: float | None = None,
               maximum: float = DUCK_DEPTH_MAX) -> float:
    minimum = DUCK_DEPTH_DB if minimum is None else minimum
    """How deep THIS bed has to duck to reach the floor a line needs under it."""
    return round(min(maximum, max(minimum, bed_lu - floor)), 2)


class Levelled(NamedTuple):
    """One line as the mix laid it, and what the bed must do under it."""

    at: float
    seconds: float
    path: Path
    depth: float
    bed_peak_lufs: float


def level_line(line: Path, gain_db: float, output: Path,
               ceiling_db: float = LINE_TP) -> Path:
    """Level a line THROUGH a limiter -- never plain `volume=` into pcm.

    Run 10 applied +11.8 dB with `volume=` alone and wrote the result to
    pcm_s16le with no ceiling anywhere in the chain: 3,096 samples pinned at
    full scale, flat factor 24.2, crest 8.2 dB.  The one line the trailer had
    was a square wave, and QC measured its level after it had already clipped.
    """
    output.parent.mkdir(parents=True, exist_ok=True)
    _ffmpeg(["ffmpeg", "-y", "-v", "error", "-i", str(line), "-af",
             f"volume={gain_db:.2f}dB,{limiter(ceiling_db)}",
             "-c:a", "pcm_s16le", str(output)], "levelling a line")
    return output


def level_lines(bed: Path, lines: list[tuple[float, Path]], out_dir: Path,
                offsets: list[float] | None = None) -> list[Levelled]:
    """Each line at LINE_TARGET_LUFS plus its delivery's offset (a shout above,
    a whisper under -- root cause 2026-09-26, D11), and the depth its window ducks."""
    readings = momentary(bed)
    offsets = offsets or [0.0] * len(lines)
    out = []
    for index, (at, path) in enumerate(lines):
        seconds = clip_seconds(path)
        peak = bed_peak(readings, at, at + seconds)
        levelled = level_line(path, line_gain(integrated(path), LINE_TARGET_LUFS + offsets[index]),
                              out_dir / f"line-{index}.level.wav")
        out.append(Levelled(at, seconds, levelled, duck_depth(peak), peak))
    return out


def duck_windows(levelled: list[Levelled]) -> list[tuple[float, float, float]]:
    """The (start, end, depth) triples the bed envelope is built from."""
    return [(line.at, line.at + line.seconds, line.depth) for line in levelled]


def write_level_sheet(out_dir: Path, levelled: list[Levelled],
                      hard_out: float | None = None) -> Path:
    """lines.level.json: what the mix DID, for QC to read back.

    Not just where each line was laid -- the depth the bed ducked under it,
    the level the bed had there, the floor those two imply, and the point the
    bed was stopped at.  QC cannot ask whether the duck was deep enough or
    whether the hard out landed unless the mix writes down what it chose.
    """
    sheet = out_dir / "lines.level.json"
    sheet.write_text(json.dumps({"hard_out": hard_out, "lines": [
        {"at": round(line.at, 3), "seconds": round(line.seconds, 3),
         "rel_path": line.path.name, "duck_db": round(-line.depth, 2),
         "bed_peak_lufs": round(line.bed_peak_lufs, 2),
         "bed_floor_lufs": round(line.bed_peak_lufs - line.depth, 2)} for line in levelled]},
        indent=2), encoding="utf-8")
    return sheet


def mix_with_lines(picture: Path, bed: Path, cues: list[tuple[float, Path]],
                   lines: list[tuple[float, Path]], output: Path,
                   seconds: float | None = None, hard_out: float | None = None,
                   offsets: list[float] | None = None) -> Path:
    """`mix` with the line layer and the shaped bed.

    Each line is levelled to an absolute target through a limiter, the bed
    ducks full-band under it and stops dead at `hard_out`, and the line rides
    as one more cue.  The shaped bed, the levelled lines and the sheet saying
    what was done are kept beside the master, so QC can measure the mix
    without un-mixing anything.
    """
    levelled = level_lines(bed, lines, Path(output).parent, offsets)
    write_level_sheet(Path(output).parent, levelled, hard_out)
    shaped = shape_bed(bed, duck_windows(levelled), hard_out,
                       Path(output).with_name(f"{Path(output).stem}.bed-ducked.wav"))
    return mix(picture, shaped, cues + [(line.at, line.path) for line in levelled],
               output, seconds)


def luma_stats(video: Path) -> tuple[float, float]:
    """(mean, standard deviation) of luma across a clip, 0-255.

    Measured across the 2026-08-25 clips, frame-average luma spanned
    42.9 to 96.6 out of 255 despite a verbatim `grade` string in every prompt.
    The prompt buys intent, not exposure -- so the look is matched in post,
    against one hero clip, which is the only method that actually works.
    """
    result = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(video), "-vf",
         "scale=160:90,format=gray", "-f", "rawvideo", "-"],
        capture_output=True)
    if not result.stdout:
        raise RuntimeError(f"could not read luma from {video}")
    import numpy as np
    pixels = np.frombuffer(result.stdout, dtype=np.uint8).astype(np.float32)
    return float(pixels.mean()), float(pixels.std())


def grade_to(mean: float, deviation: float, hero_mean: float,
             hero_deviation: float) -> str:
    """An ffmpeg filter matching one clip's exposure and contrast to the hero.

    Matching the SPREAD as well as the mean matters: correcting brightness
    alone leaves the flat clips flat, and flatness is what reads as cheap.
    Contrast is clamped because pushing a genuinely low-contrast clip hard
    just amplifies its noise.
    """
    contrast = max(0.75, min(1.35, hero_deviation / max(deviation, 1e-3)))
    brightness = (hero_mean - mean * contrast) / 255.0
    return (f"eq=contrast={contrast:.4f}:brightness={max(-0.3, min(0.3, brightness)):.4f}")


TITLE_COLOUR = "&H00DAE6ED"
"""Warm off-white, in ASS BGR order.  Pure white on pure black is the one
pair a default hands you, and it reads as exactly that."""

TITLE_FONT = "Bookman Old Style"
TITLE_FONT_FILE = Path("C:/Windows/Fonts/BOOKOS.TTF")
"""libass substitutes a missing font WITHOUT WARNING -- the same silent
failure as PIL's default bitmap face, on the one frame the audience reads.
So the file is asserted to exist before the card is rendered."""


def wrap_title(title: str, per_line: int = 22) -> list[str]:
    """Break a title into lines that will fit, keeping names intact.

    `WrapStyle: 2` disables libass wrapping, so a long title has no way to fail
    except by running off the frame -- and that is exactly what shipped: the
    Jekyll card read "GE CASE OF DR. JEKYLL AND", clipped off both edges, with
    the film's own title unreadable in the delivered file.
    """
    honorifics = {"DR", "DR.", "MR", "MR.", "MRS", "MRS.", "ST", "ST.", "MISS"}
    words = title.upper().split()
    lines: list[str] = []
    current: list[str] = []
    for index, word in enumerate(words):
        candidate = " ".join(current + [word])
        # Never end a line on an honorific -- "DR" / "JEKYLL" reads as a typo.
        dangling = word in honorifics and index + 1 < len(words)
        if current and len(candidate) > per_line and not dangling:
            lines.append(" ".join(current))
            current = [word]
        elif current and len(candidate) > per_line and dangling:
            lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        lines.append(" ".join(current))
    # Pull a trailing honorific down to the next line rather than stranding it.
    for i in range(len(lines) - 1):
        parts = lines[i].split()
        if parts and parts[-1] in honorifics:
            lines[i] = " ".join(parts[:-1])
            lines[i + 1] = parts[-1] + " " + lines[i + 1]
    return [l for l in lines if l]


def ass_title(title: str, seconds: float, width: int, height: int,
              tracking: int = 13, fade_ms: int = 500) -> str:
    r"""An ASS subtitle file body for the title card.

    EVERY override string here is a RAW string.  Most of the ASS vocabulary
    collides with Python escapes -- \fad and \fsp become form feed, \t becomes
    tab, \bord becomes backspace -- and libass discards an unrecognised block
    in silence.  The fade was written without an r prefix, so it never fired on
    a single trailer shipped, and the form feed even split the Dialogue line.

    Tracking is 0.20 em rather than the 0.37 em first used; all-caps display
    convention is about 0.1 em and film titles push to 0.2-0.3.  MarginL
    carries an extra `tracking` because libass counts the trailing letter-space
    of the final glyph in the line width, so a centred tracked line otherwise
    sits tracking/2 px left of true centre.
    """
    if not TITLE_FONT_FILE.exists():
        raise RuntimeError(f"title font missing: {TITLE_FONT_FILE}; libass would "
                           "silently substitute another face")
    end = f"{int(seconds // 3600)}:{int(seconds // 60) % 60:02d}:{seconds % 60:05.2f}"
    body = r"\N".join(wrap_title(title))
    fade = r"{\fad(" + f"{fade_ms},{int(fade_ms * 1.6)}" + r")}"
    header = (
        "[Script Info]\n"
        "ScriptType: v4.00+\n"
        f"PlayResX: {width}\n"
        f"PlayResY: {height}\n"
        "WrapStyle: 2\n\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour,"
        " Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle,"
        " BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        f"Style: Card,{TITLE_FONT},{height // 13},{TITLE_COLOUR},&H00000000,&H00000000,"
        f"0,0,0,0,100,100,{tracking},0,1,0,0,5,{60 + tracking},60,60,1\n\n"
        "[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV,"
        " Effect, Text\n")
    return header + f"Dialogue: 0,0:00:00.00,{end},Card,,0,0,0,,{fade}{body}\n"


def title_card_ass(title: str, output: Path, seconds: float, width: int,
                   height: int, fps: int) -> Path:
    """The title, tracked and faded, held on black."""
    output.parent.mkdir(parents=True, exist_ok=True)
    script = output.with_suffix(".ass")
    script.write_text(ass_title(title, seconds, width, height), encoding="utf-8")
    escaped = str(script).replace("\\", "/").replace(":", r"\:")
    _ffmpeg(
        ["ffmpeg", "-y", "-v", "error", "-f", "lavfi",
         "-i", f"color=c=black:s={width}x{height}:r={fps}:d={seconds + 0.5:.3f}",
         "-vf", f"ass='{escaped}',format=yuv420p", "-c:v", "libx264",
         "-preset", "fast", "-crf", "16", "-t", frames_arg(seconds), str(output)],
        "rendering the tracked title card")
    return output


TITLE_SAFE = 0.90
"""Fraction of frame width the title may occupy.

Nothing measured the card after rendering it, so the Jekyll title shipped
clipped off BOTH edges -- "GE CASE OF DR. JEKYLL AND" -- with the film's own
name unreadable in a delivered file.  A card that fits is a card that has been
measured."""


def ink_bounds(frame: Path, width: int, height: int,
               threshold: int = 40) -> tuple[int, int, int, int]:
    """(x0, x1, y0, y1) of the lit pixels in a rendered card."""
    import numpy as np
    result = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(frame), "-f", "rawvideo",
         "-pix_fmt", "gray", "-"], capture_output=True)
    if not result.stdout:
        raise RuntimeError(f"could not decode {frame}")
    pixels = np.frombuffer(result.stdout, dtype=np.uint8).reshape(height, width)
    lit = pixels > threshold
    if not lit.any():
        raise RuntimeError(f"{frame} has no visible text at all")
    cols, rows = np.where(lit.any(axis=0))[0], np.where(lit.any(axis=1))[0]
    return int(cols[0]), int(cols[-1]), int(rows[0]), int(rows[-1])


def card_fits(card: Path, width: int, height: int, at: float = 0.5) -> tuple[bool, str]:
    """Render a frame of the card and check the type is inside the frame."""
    frame = card.with_name(card.stem + "-probe.png")
    _ffmpeg(["ffmpeg", "-y", "-v", "error", "-ss", f"{at:.2f}", "-i", str(card),
             "-frames:v", "1", str(frame)], "sampling the title card")
    x0, x1, y0, y1 = ink_bounds(frame, width, height)
    ink = x1 - x0
    margin = min(x0, width - x1)
    note = (f"ink {ink}px of {width} ({ink / width:.0%}), "
            f"margin {margin}px, rows {y0}-{y1}")
    return (ink <= TITLE_SAFE * width and margin >= 8), note
