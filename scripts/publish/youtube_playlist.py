"""A new episode joins its book's playlist and the "— Watch in order —" links.

Called by step 13 AFTER YouTube returned the episode public, behind the same
standing hand (publish/standing.json) that let it upload; never run on its own.

    playlist   the id the book's records hold (step 13's ledger row, else the book
               video's youtube.json, both written where the 2026-10-21 apply left
               it), else the previous episode's own live block, else the channel's
               playlist titled with the book's name; made public ONLY when the
               book has none anywhere.
    item       the episode inserted at its episode-order position, once.
    own block  Previous / All episodes in order / The whole book, appended once.
    next line  the previous episode's block gains "Next: Ep NN — ...", once.

Every description write reads the live snippet first and sends back only the
writable fields (videos.update REPLACES the part; youtube_retitle.SENT).  Each act
is recorded in uploads.jsonl and skipped when recorded, and each also checks the
live text, so a re-run never writes a block or a line twice.
"""
from __future__ import annotations

from pathlib import Path

from scripts.publish import youtube_retitle
from studio import book_compilation as bc
from studio import book_playlist as bp
from studio import episode_home
from studio import youtube_publish as yp

IN_ORDER = "Episodes in Order"


def described(live: dict, text: str) -> dict:
    """The live snippet's writable fields with the description replaced; refused past
    YouTube's wall or without a categoryId (the update would be rejected)."""
    if "categoryId" not in live:
        raise SystemExit("the live snippet has no categoryId; a part=snippet update is refused")
    if len(text) > yp.DESCRIPTION_MAX:
        raise SystemExit(f"the description would be {len(text)} characters, over YouTube's {yp.DESCRIPTION_MAX}")
    return {**{k: v for k, v in live.items() if k in youtube_retitle.SENT}, "description": text}


def set_description(api, vid: str, live: dict, text: str) -> None:
    """Send the new description, unless the live one already says it."""
    if text != live.get("description"):
        youtube_retitle.push(api, vid, described(live, text))


def book_names(book: Path) -> tuple[str, str]:
    """(the book's display name, its author), from source/book.json."""
    said = episode_home.read_json(Path(book) / "source" / "book.json")
    return said.get("display_title") or said["title"], said["author"]


def on_channel(api, lead: str) -> str | None:
    """The channel's playlist whose title names this book and says it is in order."""
    token = None
    while True:
        got = api.playlists().list(part="snippet", mine=True, maxResults=50, pageToken=token).execute()
        for p in got.get("items", []):
            if lead in p["snippet"]["title"] and IN_ORDER in p["snippet"]["title"]:
                return p["id"]
        if not (token := got.get("nextPageToken")):
            return None


def made(api, book: Path, lead: str) -> str:
    """A public playlist for a book that has none anywhere."""
    name, author = book_names(book)
    body = {"snippet": {"title": bp.playlist_title(lead, author),
                        "description": bp.playlist_description(name, author)},
            "status": {"privacyStatus": "public"}}
    return api.playlists().insert(part="snippet,status", body=body).execute()["id"]


def found(api, book: Path, lead: str, prev_text: str) -> tuple[str, str]:
    """(playlist id, where it came from), made only when every place is empty."""
    for how, look in (("recorded", lambda: bp.recorded_id(book)),
                      ("previous episode", lambda: bp.id_in(prev_text)),
                      ("channel", lambda: on_channel(api, lead))):
        if pid := look():
            return pid, how
    return made(api, book, lead), "made"


def playlist_id(api, book: Path, lead: str, prev_text: str) -> tuple[str, str]:
    """The book's playlist id, recorded in the ledger the first time it is known."""
    pid, how = found(api, book, lead, prev_text)
    if not any(r.get("event") == "playlist" and r.get("playlist_id") == pid for r in bp.rows(book)):
        bp.record(book, {"event": "playlist", "playlist_id": pid, "how": how})
    return pid, how


def items(api, pid: str) -> list[str]:
    """The playlist's video ids, in its order."""
    out, token = [], None
    while True:
        got = api.playlistItems().list(part="contentDetails", playlistId=pid, maxResults=50,
                                       pageToken=token).execute()
        out += [i["contentDetails"]["videoId"] for i in got.get("items", [])]
        if not (token := got.get("nextPageToken")):
            return out


def join(api, book: Path, pid: str, n: int, vid: str, *, fresh: bool) -> None:
    """The episode inserted at its episode-order place, once.  A playlist made
    seconds ago is empty and not yet readable (404 seen live 2026-10-21 19:30)."""
    if bp.done(book, "playlist_item", vid):
        return
    have = [] if fresh else items(api, pid)
    if vid not in have:
        order = {v: k for k, v in bp.public_episodes(book).items()}
        body = {"snippet": {"playlistId": pid, "position": bp.position(have, order, n),
                            "resourceId": {"kind": "youtube#video", "videoId": vid}}}
        api.playlistItems().insert(part="snippet", body=body).execute()
    bp.record(book, {"event": "playlist_item", "video": vid, "playlist_id": pid})


def own_links(api, book: Path, vid: str, live: dict, pid: str, previous: str | None) -> None:
    """The new episode's own block, once."""
    if bp.done(book, "watch_block", vid):
        return
    block = bp.own_block(previous=previous, playlist_id=pid, whole=bp.compilation_id(book))
    set_description(api, vid, live, bp.with_own_block(live["description"], block))
    bp.record(book, {"event": "watch_block", "video": vid, "playlist_id": pid})


def next_link(api, book: Path, prev_id: str, prev: dict, line: str, vid: str) -> None:
    """The previous episode's Next line, once."""
    if bp.done(book, "next_line", prev_id):
        return
    set_description(api, prev_id, prev, bp.with_next(prev["description"], line))
    bp.record(book, {"event": "next_line", "video": prev_id, "next": vid})


def upkeep(api, book: Path, n: int, vid: str) -> str | None:
    """All four acts for episode n's public video; the playlist id it joined."""
    if bp.done(book, "in_order", vid):
        return None
    own = youtube_retitle.fetch(api, vid)
    prev_id = bp.public_episodes(book).get(n - 1)
    prev = youtube_retitle.fetch(api, prev_id) if prev_id else None
    lead = bc.search_lead(own["title"].split(" — Ep")[0], book_names(book)[1])
    pid, how = playlist_id(api, book, lead, prev["description"] if prev else "")
    join(api, book, pid, n, vid, fresh=how == "made")
    back = bp.episode_line("Previous", n - 1, bc.chapter_of(prev["title"]), prev_id) if prev else None
    own_links(api, book, vid, own, pid, back)
    if prev:
        next_link(api, book, prev_id, prev, bp.episode_line("Next", n, bc.chapter_of(own["title"]), vid), vid)
    bp.record(book, {"event": "in_order", "video": vid, "playlist_id": pid})
    return pid
