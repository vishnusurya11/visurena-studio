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


def title(series: str, chapters: int) -> str:
    """`<series> — Full Adaptation, All <n> Episodes`, inside YouTube's wall.
    An ADAPTATION, never 'the complete book': the episodes are our abridged
    screenplay of the novel, not its full text (owner, 2026-10-11)."""
    return yp.elided(f"{series} — Full Adaptation, All {chapters} Episodes", yp.TITLE_MAX)
