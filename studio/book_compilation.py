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


CARD_MAX_FRAMES = 240
"""No title card runs past 10 s; a cut further back than this is the picture's."""


def card_start(*, cuts: list[int], black_from: int) -> int:
    """The card begins at the last hard cut before the black tail -- MEASURED,
    because an older Short carries an older card than title/epNN.mp4 (Scarlet
    ep01: a 90-frame card where today's is 107)."""
    before = [c for c in cuts if black_from - CARD_MAX_FRAMES <= c < black_from]
    if not before:
        raise ValueError(f"no cut in the {CARD_MAX_FRAMES} frames before the black at {black_from}")
    return max(before)


def frame_at(seconds: float, *, fps: int) -> int:
    """A measured time as the index of the frame that starts there."""
    return round(seconds * fps)


def pieces(*, main: int, card: int) -> dict[str, tuple[int, int]]:
    """The two videos of a chapter as frame ranges [start, end) of its Short."""
    return {"title": (main, main + card), "main": (0, main)}


def cut_argv(src: Path, frames: tuple[int, int], out: Path, *, fps: int, side: int) -> list[str]:
    """ffmpeg cutting [start, end) frames out, the sound by the same seconds;
    one encode for every piece so the book joins by stream copy."""
    a, b = frames
    return ["ffmpeg", "-y", "-v", "error", "-i", str(src),
            "-vf", f"trim=start_frame={a}:end_frame={b},setpts=PTS-STARTPTS,"
                   f"scale={side}:{side}:force_original_aspect_ratio=decrease,pad={side}:{side}:-1:-1,setsar=1",
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


def footer(*, author: str, book: str) -> str:
    """The source, the adaptation note and the AI disclosure, for THIS book."""
    return (f"Source: {author}, {book}, in the public domain. This is an adapted, abridged "
            "screenplay of the novel, not its complete text.\n"
            "— The Keeper's Lantern —\n"
            "AI DISCLOSURE: the picture and the voices in this video are generated. The words "
            f"are {author}'s story, adapted; the performances are synthetic.")


def intro(*, book: str, episodes: int) -> str:
    """What the video is, in the book's own name; no other book's plot."""
    return (f"{book}, told from beginning to end as one film: our screen adaptation of the novel, "
            f"in {episodes} episodes, each one chapter of the book. "
            "Use the chapters above to jump to any episode.")
