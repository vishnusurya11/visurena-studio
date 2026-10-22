"""A book's playlist and the "— Watch in order —" links, as text and ledger reads.

The growth apply of 2026-10-21 made one public playlist per book, the episodes in
order, and appended a block to every episode's description:

    — Watch in order —
    Previous: Ep 01 — "Story of the Door" https://youtu.be/<id>
    Next: Ep 03 — "Dr. Jekyll Was Quite at Ease" https://youtu.be/<id>
    All episodes in order: https://www.youtube.com/playlist?list=<id>
    The whole book in one video: https://youtu.be/<id>

Step 13 keeps that true for each new episode (scripts/publish/youtube_playlist.py
makes the calls).  Nothing here touches the network: it builds the text and reads
what the book's own records say.  The ledger rows written here carry neither
`episode` nor `video_id`, so no reader of uploads.jsonl takes one for an upload.
"""
from __future__ import annotations

import datetime as dt
import json
import re
from pathlib import Path

from studio import youtube_publish as yp

MARK = "— Watch in order —"
ALL = "All episodes in order: "
PLAYLIST_ID = re.compile(r"playlist\?list=([\w-]+)")
PLAYLIST_TITLE_MAX = 150


def playlist_url(pid: str) -> str:
    return f"https://www.youtube.com/playlist?list={pid}"


def id_in(text: str) -> str | None:
    """The first playlist id a text links, else None."""
    hit = PLAYLIST_ID.search(text or "")
    return hit.group(1) if hit else None


def rows(book: Path) -> list[dict]:
    path = yp.ledger_path(book)
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def record(book: Path, row: dict) -> None:
    """One upkeep row in the book's ledger, stamped in local (Seattle) time."""
    yp.record(book, {**row, "at": dt.datetime.now().astimezone().isoformat(timespec="seconds")})


def recorded_id(book: Path) -> str | None:
    """The playlist id the book's records hold: step 13's own row first, else the
    book video's youtube.json, which the apply rewrote with the playlist link."""
    found = [r["playlist_id"] for r in rows(book) if r.get("event") == "playlist" and r.get("playlist_id")]
    if found:
        return found[-1]
    meta = Path(book) / "compilation" / "youtube.json"
    if not meta.exists():
        return None
    return id_in(json.loads(meta.read_text(encoding="utf-8")).get("description", ""))


def done(book: Path, event: str, video: str) -> bool:
    """Whether an upkeep act was already recorded for this video."""
    return any(r.get("event") == event and r.get("video") == video for r in rows(book))


def public_episodes(book: Path) -> dict[int, str]:
    """{episode: video id} for every chapter whose newest privacy flip says public."""
    newest: dict[str, dict] = {}
    for r in rows(book):
        if r.get("event") == "privacy" and isinstance(r.get("episode"), int) and r.get("video_id"):
            newest[r["video_id"]] = r
    return {r["episode"]: vid for vid, r in newest.items() if r.get("privacy") == "public"}


def compilation_id(book: Path) -> str | None:
    """The book video, when one is public and was not retired private after."""
    said: dict[str, str] = {}
    for r in rows(book):
        if r.get("episode") == "compilation" and r.get("video_id") and r.get("privacy"):
            said[r["video_id"]] = r["privacy"]
    live = [vid for vid, privacy in said.items() if privacy == "public"]
    return live[-1] if live else None


def episode_line(word: str, n: int, chapter: str, vid: str) -> str:
    return f'{word}: Ep {n:02d} — "{chapter}" https://youtu.be/{vid}'


def own_block(*, previous: str | None, playlist_id: str, whole: str | None) -> str:
    """The block a new episode's description ends with (it has no Next yet)."""
    lines = ["", "", MARK] + ([previous] if previous else []) + [ALL + playlist_url(playlist_id)]
    return "\n".join(lines + ([f"The whole book in one video: https://youtu.be/{whole}"] if whole else []))


def with_own_block(text: str, block: str) -> str:
    """The description with the block after it; one that has a block is left alone."""
    return text if MARK in text else text.rstrip() + block


def with_next(text: str, line: str) -> str:
    """The Next line inside the block, before its playlist line; a block is made
    when there is none, and a description already holding the line is unchanged."""
    if line.rsplit(" ", 1)[-1] in text:
        return text
    if MARK not in text:
        return f"{text.rstrip()}\n\n{MARK}\n{line}"
    head, block = text.split(MARK, 1)
    if f"\n{ALL}" in block:
        return head + MARK + block.replace(f"\n{ALL}", f"\n{line}\n{ALL}", 1)
    return head + MARK + block.rstrip() + "\n" + line


def position(items: list[str], order: dict[str, int], n: int) -> int:
    """Where episode n goes: before the first item of a later episode."""
    for k, vid in enumerate(items):
        if order.get(vid, 0) > n:
            return k
    return len(items)


def playlist_title(lead: str, author: str) -> str:
    """`Dr Jekyll and Mr Hyde — Robert Louis Stevenson | Episodes in Order`: the
    apply's title, with no count a book in progress would make untrue."""
    return yp.elided(f"{lead} — {author} | Episodes in Order", PLAYLIST_TITLE_MAX)


def playlist_description(book: str, author: str) -> str:
    """What the playlist is, the adaptation note and the disclosure; no promise."""
    return (f"{book} by {author}, one chapter per episode, in order from the first page to the last: "
            "our adapted, abridged screenplay of the public-domain novel.\n"
            "— The Keeper's Lantern —\n"
            "AI DISCLOSURE: the picture and the voices are generated. "
            f"The words are {author}'s story, adapted; the performances are synthetic.")
