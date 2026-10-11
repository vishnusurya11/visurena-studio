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


def chapter_lines(parts: list[tuple[int, str, float]], lead_s: float = 0.0) -> list[str]:
    """`0:00 Ep 1 — Title` per part, each starting where the last one ended.
    The book's main title (`lead_s`) folds into Ep 1: a 7 s chapter of its own
    is under YouTube's 10 s floor, and one short chapter drops them all."""
    out, at = [], 0.0
    for number, title, seconds in parts:
        out.append(f"{stamp(at)} Ep {number} — {title}")
        at += seconds + (lead_s if not out[:-1] else 0.0)
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


CUT_FLOOR = 0.1
"""A scene change under this is motion, not a cut."""


NEAR = 6
"""Frames either side of where the card's own length puts its start (the black is
measured from inside the card's fade-out, ~2 frames early)."""


def card_start(*, scores: dict[int, float], black_from: int, card_frames: int) -> int:
    """The card begins at the change nearest where its length puts it (black -
    card_frames); with no change there -- an older card than title/epNN.mp4
    (Scarlet ep01: 90 frames, today's 107) -- at the BIGGEST change before the
    black.  The biggest alone took a hard cut inside the picture on WotW ep06/10/20
    and Scarlet ep12; no fixed threshold holds (WotW ep01's dark cut scored 0.24)."""
    window = {f: v for f, v in scores.items() if black_from - CARD_MAX_FRAMES <= f < black_from and v >= CUT_FLOOR}
    if not window:
        raise ValueError(f"no cut in the {CARD_MAX_FRAMES} frames before the black at {black_from}")
    expect = black_from - card_frames
    near = {f: v for f, v in window.items() if abs(f - expect) <= NEAR}
    return max(near or window, key=(near or window).get)


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
            "-color_primaries", "bt709", "-color_trc", "iec61966-2-1", "-colorspace", "bt709",
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


# ---- the door: nothing uploads that a check can catch (retro, 2026-10-11) ----------

CARD_SLACK = 3
"""Frames a title piece may run over its card: the black is measured ~2 frames
inside the card's fade-out."""


def door_faults(*, title_frames: dict[int, int], card_frames: dict[int, int], order_ok: bool,
                title_verdict: dict) -> list[str]:
    """What stops the book video at the upload door.  A title piece LONGER than its
    card holds chapter picture (Scarlet ep12: 175 for 107); a shorter one is an
    older card (Scarlet ep01: 90), not a fault."""
    faults = [] if order_ok else ["the running order is not main title, then title + main per chapter"]
    if title_verdict.get("refused"):
        faults.append(f"G-BOOKTITLE refused: {title_verdict['refused']}")
    for n in sorted(title_frames):
        if title_frames[n] > card_frames.get(n, title_frames[n]) + CARD_SLACK:
            faults.append(f"ep{n:02d}: title piece is {title_frames[n]} frames for a {card_frames[n]}-frame card")
    return faults


def title_first_order(order: list[Path]) -> bool:
    """The concat list reads main title, then epNN_title, epNN_main, chapter after chapter."""
    names = [Path(p).name for p in order]
    if not names or names[0] != "main_title.mp4" or len(names) % 2 == 0:
        return False
    pairs = list(zip(names[1::2], names[2::2]))
    return all(t.endswith("_title.mp4") and m.endswith("_main.mp4") and t[:4] == m[:4] for t, m in pairs)


def lock_holder(lock: Path, *, alive) -> int | None:
    """The live process holding a book's compilation lock, or None (none, or stale).
    A 'detached' job survived its shell and raced the upload run (2026-10-11)."""
    try:
        pid = int(Path(lock).read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return None
    return pid if alive(pid) else None


LAYOUT = "master_layout.json"
"""cut/<this>: {sha8: {main, card, chip}} written by assemble for every master it builds."""


def recorded_split(layout: dict, sha8: str) -> tuple[int, int] | None:
    """(main frames, card frames) assemble recorded for these exact bytes, else None
    (an older Short: the card is measured)."""
    row = layout.get(sha8)
    return (int(row["main"]), int(row["card"])) if row else None
