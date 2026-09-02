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

import subprocess
from pathlib import Path

def segment_start(usage: int, of_uses: int, need: float, available: float) -> float:
    """Where in a take to start this use of it.

    Uses are spread evenly across whatever room the take has left after the
    shot length is taken out, so a beat seen three times shows three genuinely
    different moments rather than three clamped to the same frame.
    """
    room = max(available - need, 0.0)
    if room <= 0 or of_uses <= 1:
        return 0.0
    return round(min(usage, of_uses - 1) / (of_uses - 1) * room, 3)


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
            width: int, height: int, fps: int) -> Path:
    """Cut one shot out of a take, conformed to the trailer's single format.

    Every shot is forced to the same size, rate and pixel format here.  The
    first cut mixed aspect ratios, and a concat demuxer will happily join
    mismatched streams into something that plays wrong.
    """
    output.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-ss", f"{start:.3f}", "-i", str(video),
         "-t", f"{seconds:.3f}", "-an",
         "-vf", (f"scale={width}:{height}:force_original_aspect_ratio=increase,"
                 f"crop={width}:{height},fps={fps},format=yuv420p"),
         "-c:v", "libx264", "-preset", "medium", "-crf", "16", str(output)],
        check=True, capture_output=True)
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
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-f", "lavfi",
         "-i", f"color=c=black:s={width}x{height}:r={fps}:d={seconds:.3f}",
         "-vf", f"{draw},format=yuv420p", "-c:v", "libx264", "-preset", "medium",
         "-crf", "16", "-t", f"{seconds:.3f}", str(output)],
        check=True, capture_output=True)
    return output


def concat(segments: list[Path], output: Path) -> Path:
    """Join the shots with hard cuts and no re-encode."""
    listing = output.with_suffix(".txt")
    listing.write_text(
        "\n".join(f"file '{p.as_posix()}'" for p in segments), encoding="utf-8")
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
         "-i", str(listing), "-c", "copy", str(output)],
        check=True, capture_output=True)
    return output


def mix(picture: Path, bed: Path, cues: list[tuple[float, Path]], output: Path) -> Path:
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
    parts.append(f"{''.join(mixed)}amix=inputs={len(mixed)}:normalize=0,"
                 f"alimiter=limit=0.891,loudnorm=I=-14:TP=-1.0[out]")
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", ";".join(parts),
         "-map", "0:v", "-map", "[out]", "-c:v", "copy", "-c:a", "aac", "-b:a", "256k",
         "-ar", "48000", "-shortest", str(output)],
        check=True, capture_output=True)
    return output
