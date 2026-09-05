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

LIMITING_DB = 5.5
"""How much peak limiting the master may do to bring the average up.

Taking the strictly peak-safe gain left Jekyll at -16.2 LUFS, because a cue
with a braam in it has a high crest factor and the peak constraint binds long
before the loudness target.  Raised from 2.0 to 3.5 when the tone-matched cue
arrived at LRA 14.2 against the old 7.0: a wider range is the improvement, and
it costs exactly this much more limiting to reach the same average.  Allowing the limiter to do real gain reduction is
what mastering IS; the alternative is a correct-but-quiet master.

Bounded, and verified after the fact rather than trusted: the QC gate measures
the finished file's true peak, so overreach here fails loudly."""

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


def extract(video: Path, start: float, seconds: float, output: Path,
            width: int, height: int, fps: int, grade: str = "") -> Path:
    """Cut one shot out of a take, conformed to the trailer's single format.

    Every shot is forced to the same size, rate and pixel format here.  The
    first cut mixed aspect ratios, and a concat demuxer will happily join
    mismatched streams into something that plays wrong.
    """
    output.parent.mkdir(parents=True, exist_ok=True)
    _ffmpeg(
        ["ffmpeg", "-y", "-v", "error", "-ss", frames_arg(start, fps), "-i", str(video),
         "-t", frames_arg(seconds, fps), "-an",
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
         *bound,
         "-map", "0:v", "-map", "[out]", "-c:v", "copy", "-c:a", "aac", "-b:a", "256k",
         "-ar", "48000", "-shortest", str(output)],
        "mixing the trailer")
    return output


DUCK_SPLIT = "acrossover=split=250 4000"
"""The bed in three bands.  Only the middle one ducks: the low band is the
pulse the cut was made to, the high band is the air; the line lives at
250-4000 Hz and that is the room it needs (08-assemble)."""
DUCK = "sidechaincompress=threshold=0.03:ratio=6:attack=160:release=1000:level_sc=1"
"""Keyed by the line, not by a plan: a line that runs long ducks long."""


def _key_chain(index: int, at: float) -> str:
    """One line as a compressor key: conformed to the bed, delayed to its
    window, then PADDED -- sidechaincompress ends its output when the key
    ends, so an unpadded key cuts the bed off at the end of the line."""
    ms = int(round(at * 1000))
    return (f"[{index + 1}:a]aresample=48000,aformat=channel_layouts=stereo,"
            f"adelay={ms}:all=1,apad[key{index}]")


def duck_graph(starts: list[float]) -> str:
    """Input 0 is the bed, inputs 1..n the lines; one compressor per line,
    chained through the mid band, so each window ducks on its own key."""
    parts = [f"[0:a]aresample=48000,aformat=channel_layouts=stereo,{DUCK_SPLIT}[lo][mid0][hi]"]
    for index, at in enumerate(starts):
        parts.append(_key_chain(index, at))
        parts.append(f"[mid{index}][key{index}]{DUCK}[mid{index + 1}]")
    parts.append(f"[lo][mid{len(starts)}][hi]amix=inputs=3:normalize=0:duration=first[out]")
    return ";".join(parts)


def duck_bed(bed: Path, keys: list[tuple[float, Path]], output: Path) -> Path:
    """The bed with its mid band ducked under every spoken line.

    With nothing spoken the bed is returned as it is: a card gives the
    compressor no key, and a pass through the graph would not be a no-op.
    """
    if not keys:
        return bed
    inputs = ["-i", str(bed)]
    for _, path in keys:
        inputs += ["-i", str(path)]
    _ffmpeg(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex",
             duck_graph([at for at, _ in keys]), "-map", "[out]",
             "-t", f"{clip_seconds(bed):.3f}", "-c:a", "pcm_s16le", str(output)],
            "ducking the bed under the lines")
    return output


def momentary(path: Path) -> list[tuple[float, float]]:
    """(t, M) every 100 ms from ebur128: the momentary loudness QC reads."""
    result = subprocess.run(["ffmpeg", "-v", "info", "-nostats", "-i", str(path),
                             "-af", "ebur128", "-f", "null", "-"],
                            capture_output=True, text=True, errors="replace")
    readings = []
    for line in result.stderr.splitlines():
        hit = re.search(r"t:\s*([\d.]+)\s+TARGET.*?M:\s*(-?[\d.]+|-inf)", line)
        if hit:
            readings.append((float(hit.group(1)), float(hit.group(2))))
    return readings


def window_loudness(readings: list[tuple[float, float]], start: float, end: float) -> float:
    """Mean momentary loudness over [start, end); refuses to average nothing."""
    inside = [m for t, m in readings if start <= t < end]
    if not inside:
        raise ValueError(f"no loudness readings in {start:.2f}-{end:.2f}s")
    return sum(inside) / len(inside)


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


LINE_OVER_BED = 8.0
"""LU a line rides over the bed in its window, set BEFORE the duck against
the bed as rendered: QC targets 5 and the duck only widens the gap.  Run 9's
master was heard as 'music too loud': the bed was normalised to -14 LUFS and
nothing set a line against it -- a take at its own level was whatever the
voice model gave, and a quiet one was no key to the compressor either."""
GAIN_LIMIT = 20.0


def integrated(path: Path) -> float:
    """Integrated loudness of one file, LUFS, from ebur128 via loudnorm."""
    report = _measure_loudness(["ffmpeg", "-v", "info", "-i", str(path), "-af",
                                "loudnorm=print_format=json", "-f", "null", "-"])
    return float(report["input_i"])


def bed_level(readings: list[tuple[float, float]], start: float, end: float) -> float:
    """The bed's momentary loudness over a window, silence left out: a
    stop-down reads -inf and is not a level to sit over."""
    return window_loudness([(t, m) for t, m in readings if m > -70.0], start, end)


def line_gain(bed_lu: float, line_lu: float) -> float:
    """The dB that lands a line LINE_OVER_BED above its window, bounded."""
    return round(max(-GAIN_LIMIT, min(GAIN_LIMIT, bed_lu + LINE_OVER_BED - line_lu)), 2)


def level_line(line: Path, gain_db: float, output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    _ffmpeg(["ffmpeg", "-y", "-v", "error", "-i", str(line), "-af", f"volume={gain_db:.2f}dB",
             "-c:a", "pcm_s16le", str(output)], "levelling a line")
    return output


def level_lines(bed: Path, lines: list[tuple[float, Path]], out_dir: Path) -> list[tuple[float, Path]]:
    """Each line at the gain that sits it over its own window of the bed."""
    readings = momentary(bed)
    out = []
    for index, (at, path) in enumerate(lines):
        window = bed_level(readings, at, at + clip_seconds(path))
        gain = line_gain(window, integrated(path))
        out.append((at, level_line(path, gain, out_dir / f"line-{index}.level.wav")))
    return out


def write_level_sheet(out_dir: Path, levelled: list[tuple[float, Path]]) -> Path:
    """lines.level.json: where each levelled line was laid, for QC."""
    sheet = out_dir / "lines.level.json"
    sheet.write_text(json.dumps([{"at": at, "rel_path": path.name} for at, path in levelled],
                                indent=2), encoding="utf-8")
    return sheet


def mix_with_lines(picture: Path, bed: Path, cues: list[tuple[float, Path]],
                   lines: list[tuple[float, Path]], output: Path,
                   seconds: float | None = None) -> Path:
    """`mix` with the line layer: each line is levelled to its window, the
    bed ducks under it, and the line rides as one more cue.  The ducked bed
    and the levelled lines are kept beside the master so QC can measure
    line-over-bed without un-mixing anything."""
    if not lines:
        return mix(picture, bed, cues, output, seconds)
    levelled = level_lines(bed, lines, Path(output).parent)
    write_level_sheet(Path(output).parent, levelled)
    ducked = duck_bed(bed, levelled, Path(output).with_name(f"{Path(output).stem}.bed-ducked.wav"))
    return mix(picture, ducked, cues + levelled, output, seconds)


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
