"""Cutting the page: each beat taken out of its own take, in written order.

The old cut read its spans off the MUSIC and stamped beats onto them.  This one
cuts the PAGE: every beat plays for the seconds it was written for, out of the
middle of the take rendered for it, and a beat that holds a card is drawn
rather than filmed.

WHERE THE SECONDS COME FROM.  A take renders longer than its beat plays --
`HEAD_TRIM` of reference leak at the front, a seek handle at the back -- so the
cut starts at HEAD_TRIM and never reaches the tail.  MEASURED across 32 of our
own takes: detail drifts -5.1% from first quarter to last (median -1.9%), so
there is no reason to favour the head beyond skipping the leak; what does
happen is that 6 takes in 32 collapse outright, which is a per-take fault for
the gate to catch, not a reason to shorten every beat.
"""
from __future__ import annotations

from pathlib import Path

from studio.trailer_assemble import HEAD_TRIM, concat, extract, title_card
from studio.trailer_script import TrailerScript

FPS = 24
VERTICAL_W, VERTICAL_H = 768, 1344


def take_for(beat, clips_dir: Path) -> Path:
    """The take rendered for this beat."""
    return Path(clips_dir) / f"{beat.id}.mp4"


def missing(page: TrailerScript, clips_dir: Path) -> list[str]:
    """Beats with no take on disk -- a card needs none."""
    return [b.id for b in page.beats
            if b.see and not take_for(b, clips_dir).exists()]


SAFE_TOP, SAFE_BOTTOM = 0.14, 0.35
"""The share of a 9:16 frame the platform's own interface covers.  Text sits
between them or the viewer never reads it."""


def over_text(card: str, out: Path, height: int) -> str:
    """A drawtext filter that lays a card's words over the picture.

    Through a FILE, never inline: ffmpeg's drawtext silently drops apostrophes
    from an inline `text=` argument, on the one frame the audience is
    guaranteed to read (`trailer_assemble.title_card` learned this first).
    The line sits inside the vertical safe band, clear of the platform's UI."""
    path = out.with_suffix(".card.txt")
    path.write_text(card.upper(), encoding="utf-8")
    escaped = str(path).replace("\\", "/").replace(":", r"\:")
    return (f"drawtext=textfile='{escaped}':fontcolor=white:fontsize={height // 22}:"
            f"borderw=2:bordercolor=black@0.6:x=(w-text_w)/2:"
            f"y=h*{1 - SAFE_BOTTOM:.2f}-text_h")


def segment(beat, clips_dir: Path, work: Path, width: int, height: int,
            fps: int = FPS) -> Path:
    """One beat as a finished piece of picture: cut from its take, or drawn.

    A beat that has BOTH a picture and a card is the picture, captioned -- the
    page names the book inside the first seven seconds, over the opening image.
    Drawn as a card instead, the first real cut threw that image away and
    opened on black, which is the one thing every source says never to do."""
    out = Path(work) / f"{beat.id}.mp4"
    if beat.card and not beat.see:
        return title_card(beat.card, out, beat.seconds, width, height, fps)
    grade = over_text(beat.card, out, height) if beat.card else ""
    return extract(take_for(beat, clips_dir), HEAD_TRIM, beat.seconds, out,
                   width, height, fps, grade=grade)


def cut(page: TrailerScript, clips_dir: Path, work: Path, dest: Path,
        width: int = VERTICAL_W, height: int = VERTICAL_H, fps: int = FPS) -> Path:
    """The whole picture, beat by beat, in the order the page wrote them."""
    absent = missing(page, clips_dir)
    if absent:
        raise FileNotFoundError(f"no take rendered for {', '.join(absent)}")
    Path(work).mkdir(parents=True, exist_ok=True)
    pieces = [segment(b, clips_dir, work, width, height, fps) for b in page.beats]
    return concat(pieces, Path(dest))
