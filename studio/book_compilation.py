"""The whole book as one regular video (owner, 2026-10-10).

Every PUBLISHED episode, in chapter order, joined into one file and uploaded as
a normal video -- not a Short -- whose description OPENS with YouTube chapter
timestamps (one per episode, the first at 0:00, each at least 10 s long), so
the player shows the book's chapters.  The parts are the exact masters the
channel carries, matched by the sha8 the upload ledger recorded; a later
re-cut of an episode never slips into the compilation.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from studio import youtube_publish as yp

QUOTED = re.compile(r'"([^"]+)"\s*$')


def stamp(seconds: float) -> str:
    """YouTube's chapter timestamp: M:SS under an hour, H:MM:SS after."""
    s = int(seconds)
    h, m, sec = s // 3600, (s % 3600) // 60, s % 60
    return f"{h}:{m:02d}:{sec:02d}" if h else f"{m}:{sec:02d}"


def chapter_lines(parts: list[tuple[int, str, float]]) -> list[str]:
    """`0:00 Ep 1 — Title` per part, each starting where the last one ended."""
    out, at = [], 0.0
    for number, title, seconds in parts:
        out.append(f"{stamp(at)} Ep {number} — {title}")
        at += seconds
    return out


def description(lines: list[str], *, intro: str, footer: str) -> str:
    """The chapters FIRST (the owner's ask), then the intro and the footer."""
    return "\n".join(lines) + "\n\n" + intro.strip() + "\n\n" + footer.strip()


def chapter_of(title: str) -> str:
    """The chapter name an episode's title quotes, else the title itself."""
    m = QUOTED.search(title or "")
    return m.group(1) if m else (title or "")


def uploaded_master(cut: Path, sha8: str) -> Path | None:
    """The file in an episode's cut/ whose bytes the channel carries."""
    for path in sorted(Path(cut).glob("master*.mp4")):
        if yp.sha8(path) == sha8:
            return path
    return None


def published(book: Path) -> list[tuple[int, str]]:
    """(episode, sha8) for every episode with a PUBLIC video, in chapter order:
    the public flip names the video, the upload row of that video names the bytes."""
    rows = [json.loads(l) for l in (Path(book) / "uploads.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    public = {r["video_id"] for r in rows if r.get("privacy") == "public" and r.get("video_id")}
    out = {}
    for r in rows:
        if r.get("video_id") in public and r.get("sha8") and isinstance(r.get("episode"), int):
            out[int(r["episode"])] = r["sha8"]
    return sorted(out.items())


def concat_list(paths: list[Path]) -> str:
    """ffmpeg's concat-demuxer list: one `file '<path>'` per part, in order,
    a single quote in a path written as '\\'' (the demuxer's own escape)."""
    lines = []
    for path in paths:
        text = Path(path).resolve().as_posix().replace("'", "'\\''")
        lines.append(f"file '{text}'")
    return "\n".join(lines) + "\n"


def main_frames(*, master_frames: int, card_frames: int, chip_frames: int) -> int:
    """The Short is main + title card + black chip: the main video is what
    is left before the card (owner 2026-10-11: two videos per chapter)."""
    main = master_frames - card_frames - chip_frames
    if main <= 0:
        raise ValueError(f"a {master_frames}-frame Short cannot hold a {card_frames}-frame card")
    return main


def pieces(*, main: int, card: int) -> dict[str, tuple[int, int]]:
    """The two videos of a chapter as frame ranges [start, end) of its Short."""
    return {"title": (main, main + card), "main": (0, main)}


def cut_argv(src: Path, frames: tuple[int, int], out: Path, *, fps: int) -> list[str]:
    """ffmpeg cutting [start, end) frames out, the sound by the same seconds;
    one encode for every piece so the book joins by stream copy."""
    a, b = frames
    return ["ffmpeg", "-y", "-v", "error", "-i", str(src),
            "-vf", f"trim=start_frame={a}:end_frame={b},setpts=PTS-STARTPTS",
            "-af", f"atrim=start={a / fps:.6f}:end={b / fps:.6f},asetpts=PTS-STARTPTS",
            "-c:v", "libx264", "-preset", "fast", "-crf", "16", "-pix_fmt", "yuv420p",
            "-r", str(fps), "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-ac", "2", str(out)]


def title_first(chapters: list[tuple[Path, Path]]) -> list[Path]:
    """The book's running order: each chapter's title, then its main video."""
    return [p for title_video, main_video in chapters for p in (title_video, main_video)]


def title(series: str, chapters: int) -> str:
    """`<series> — Full Adaptation, All <n> Episodes`, inside YouTube's wall.
    An ADAPTATION, never 'the complete book': the episodes are our abridged
    screenplay of the novel, not its full text (owner, 2026-10-11)."""
    return yp.elided(f"{series} — Full Adaptation, All {chapters} Episodes", yp.TITLE_MAX)
