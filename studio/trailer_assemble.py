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

import json
import subprocess
from pathlib import Path

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

TARGET_TP = -1.5
"""True-peak ceiling.  EBU R128 asks for -1.0; -1.5 leaves room for the
intersample peaks the AAC encoder introduces after this measurement."""

TP_LINEAR = 0.80
"""A final sample-peak safety net at about -1.9 dBFS.

Note `level=disabled` wherever alimiter is used.  Its auto-level is ON by
default: it limits and then re-levels the result back up, so LOWERING the
limit made the mix LOUDER -- peaks went -0.55 -> +0.53 -> +0.95 dBTP across
three attempts while I kept tightening a limiter that was undoing itself."""

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
        return min(head, max(available - need, 0.0))
    if of_uses <= 1:
        return round(head + room / 2, 3)
    return round(head + min(usage, of_uses - 1) / (of_uses - 1) * room, 3)


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


def extract(video: Path, start: float, seconds: float, output: Path,
            width: int, height: int, fps: int, grade: str = "") -> Path:
    """Cut one shot out of a take, conformed to the trailer's single format.

    Every shot is forced to the same size, rate and pixel format here.  The
    first cut mixed aspect ratios, and a concat demuxer will happily join
    mismatched streams into something that plays wrong.
    """
    output.parent.mkdir(parents=True, exist_ok=True)
    _ffmpeg(
        ["ffmpeg", "-y", "-v", "error", "-ss", f"{start:.3f}", "-i", str(video),
         "-t", f"{seconds:.3f}", "-an",
         "-vf", (f"scale={width}:{height}:force_original_aspect_ratio=increase,"
                 f"crop={width}:{height},fps={fps},{grade + ',' if grade else ''}"
                 f"format=yuv420p"),
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
         "-i", f"color=c=black:s={width}x{height}:r={fps}:d={seconds:.3f}",
         "-vf", f"{draw},format=yuv420p", "-c:v", "libx264", "-preset", "fast",
         "-crf", "16", "-t", f"{seconds:.3f}", str(output)],
        "rendering the title card")
    return output


def concat(segments: list[Path], output: Path) -> Path:
    """Join the shots with hard cuts and no re-encode."""
    listing = output.with_suffix(".txt")
    listing.write_text(
        "\n".join(f"file '{p.as_posix()}'" for p in segments), encoding="utf-8")
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
    bound = ["-t", f"{seconds:.3f}"] if seconds else []
    analysis = _measure_loudness(
        ["ffmpeg", "-v", "info", *inputs, "-filter_complex",
         f"{base},loudnorm=I={TARGET_LUFS}:TP={TARGET_TP}:print_format=json[out]",
         *bound, "-map", "[out]", "-f", "null", "-"])
    gain = 0.0
    if "input_i" in analysis and "input_tp" in analysis:
        try:
            to_target = TARGET_LUFS - float(analysis["input_i"])
            to_ceiling = TARGET_TP - float(analysis["input_tp"])
            gain = min(to_target, to_ceiling)
        except ValueError:
            gain = 0.0
    parts.append(f"{base},volume={gain:.2f}dB,alimiter=limit={TP_LINEAR}:level=disabled[out]")
    _ffmpeg(
        ["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", ";".join(parts),
         *bound,
         "-map", "0:v", "-map", "[out]", "-c:v", "copy", "-c:a", "aac", "-b:a", "256k",
         "-ar", "48000", "-shortest", str(output)],
        "mixing the trailer")
    return output


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


TITLE_FONT = "Bookman Old Style"
TITLE_FONT_FILE = Path("C:/Windows/Fonts/BOOKOS.TTF")
"""libass substitutes a missing font WITHOUT WARNING -- the same silent
failure as PIL's default bitmap face, on the one frame the audience reads.
So the file is asserted to exist before the card is rendered."""


def ass_title(title: str, seconds: float, width: int, height: int,
              tracking: int = 22, fade_ms: int = 700) -> str:
    """An ASS subtitle file body for the title card.

    Letter-spacing is the whole point: tracking is what separates a title that
    was designed from one that was typed, and drawtext cannot do it at all.
    """
    if not TITLE_FONT_FILE.exists():
        raise RuntimeError(f"title font missing: {TITLE_FONT_FILE}; libass would "
                           "silently substitute another face")
    end = f"{int(seconds // 3600)}:{int(seconds // 60) % 60:02d}:{seconds % 60:05.2f}"
    return (
        "[Script Info]\nScriptType: v4.00+\n"
        f"PlayResX: {width}\nPlayResY: {height}\nWrapStyle: 2\n\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour,"
        " Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle,"
        " BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        f"Style: Card,{TITLE_FONT},{height // 13},&H00FFFFFF,&H00000000,&H00000000,"
        f"0,0,0,0,100,100,{tracking},0,1,0,0,5,60,60,60,1\n\n"
        "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR,"
        " MarginV, Effect, Text\n"
        f"Dialogue: 0,0:00:00.00,{end},Card,,0,0,0,,"
        f"{{\fad({fade_ms},{fade_ms})}}{title.upper()}\n")


def title_card_ass(title: str, output: Path, seconds: float, width: int,
                   height: int, fps: int) -> Path:
    """The title, tracked and faded, held on black."""
    output.parent.mkdir(parents=True, exist_ok=True)
    script = output.with_suffix(".ass")
    script.write_text(ass_title(title, seconds, width, height), encoding="utf-8")
    escaped = str(script).replace("\\", "/").replace(":", r"\:")
    _ffmpeg(
        ["ffmpeg", "-y", "-v", "error", "-f", "lavfi",
         "-i", f"color=c=black:s={width}x{height}:r={fps}:d={seconds:.3f}",
         "-vf", f"ass='{escaped}',format=yuv420p", "-c:v", "libx264",
         "-preset", "fast", "-crf", "16", "-t", f"{seconds:.3f}", str(output)],
        "rendering the tracked title card")
    return output
