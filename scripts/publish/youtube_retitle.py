#!/usr/bin/env python
"""Re-title every published episode of a book to the series format.

    uv run python scripts/publish/youtube_retitle.py <codex_id> --dry-run
    uv run python scripts/publish/youtube_retitle.py <codex_id> --approved=publish

OWNER, 2026-09-14: "update all youtube title so far to SH : A Study in Scarlet
Ep 01/14 something like that ... book name and episode list should come first in
title".

The first five went up as `"<chapter>" -- A Study in Scarlet Ep.N`, which puts
the one thing a viewer cannot use -- the chapter title -- in the 40-70 characters
a search result actually shows, and leaves the series and the position to be
truncated away.  `youtube_publish.series_title` now builds the string, so this
script's only job is to carry that shape back over what is already live.

A RETITLE IS A WRITE TO A PUBLIC OBJECT, so it is gated like the upload: the
title comes from the ledger's own record of which episode each video is, and
`--approved=publish` is required before a single call goes out.  `--dry-run`
prints every before/after and touches no network.

WHY THE LIVE SNIPPET IS READ BACK FIRST.  `videos.update` with `part=snippet`
REPLACES the snippet; it does not merge.  Sending `{"title": ...}` alone returns
200 and leaves the video with no description, no tags and no category.  So each
video's current snippet is fetched, one field is changed, and that is what is
sent -- never a body built from `youtube.json`, which records what the upload
INTENDED and has drifted from what is live at least once already.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio import approval, episode_home, youtube, youtube_publish as yp

SENT = ("title", "description", "tags", "categoryId", "defaultLanguage",
        "defaultAudioLanguage")
"""The writable snippet fields.  Everything else YouTube returns -- channelTitle,
publishedAt, thumbnails, localized -- is read-only and echoing it back is at
best ignored."""


def restitled(snippet: dict, title: str) -> dict | None:
    """The snippet to send: the live one with the title replaced.  None if it
    already says that, so a re-run is free and writes nothing."""
    if "categoryId" not in snippet:
        raise ValueError("the live snippet has no categoryId; a part=snippet update "
                         "without one is refused as invalidCategoryId")
    if snippet.get("title") == title:
        return None
    out = {k: v for k, v in snippet.items() if k in SENT}
    out["title"] = title
    return out


def chapter_of(title: str) -> str:
    """The chapter name out of an old-format title: it is the quoted part."""
    if '"' in title:
        return title.split('"')[1]
    return title.split("—")[0].strip()


def episodes(book: Path) -> list[dict]:
    """The latest ledger row per episode -- one video each, newest cut wins."""
    path = yp.ledger_path(book)
    rows: dict[int, dict] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            rows[row["episode"]] = row
    return [rows[n] for n in sorted(rows)]


def fetch(api, video_id: str) -> dict:
    got = api.videos().list(part="snippet", id=video_id).execute()
    if not got.get("items"):
        raise SystemExit(f"{video_id} is not visible to this token")
    return got["items"][0]["snippet"]


def push(api, video_id: str, snippet: dict) -> dict:
    return api.videos().update(part="snippet",
                               body={"id": video_id, "snippet": snippet}).execute()


def series_of(book) -> tuple[str, str, int]:
    """(series, display title, episodes in the series), from the book's own
    source/book.json. No default: the defaults were the other book's -- "Sherlock
    Holmes" and 14 -- and would have retitled WotW's published videos with them."""
    said = json.loads((Path(book) / "source" / "book.json").read_text(encoding="utf-8"))
    if missing := [k for k in ("series", "display_title", "episodes") if not said.get(k)]:
        raise SystemExit(f"source/book.json does not say its {', '.join(missing)}; "
                         f"a title will not be guessed")
    return said["series"], said["display_title"], int(said["episodes"])


def main(argv: list[str]) -> None:
    args = [a for a in argv[1:] if not a.startswith("--")]
    book_id = args[0]
    dry = "--dry-run" in argv

    book = episode_home.book_dir(book_id)
    series, name, total = series_of(book)
    rows = episodes(book)
    print(f"book      {name}")
    print(f"episodes  {len(rows)} published, series of {total}\n")

    api = None
    if not dry:
        from googleapiclient.discovery import build
        api = build("youtube", "v3", credentials=youtube.credentials(), cache_discovery=False)
        approval.require("publish", f"re-titling {len(rows)} public videos on the channel",
                         0.0, approval.approved_for("publish", argv))

    for row in rows:
        want = yp.series_title(name, row["episode"], total, chapter_of(row["title"]), series=series)
        print(f"ep{row['episode']:02d}  {row['video_id']}")
        print(f"  was  {row['title']}")
        print(f"  now  {want}   ({len(want)} chars)")
        home = episode_home.home(book, row["episode"])
        meta_path = home / "youtube.json"
        if meta_path.exists():
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            meta["title"] = want
            if not dry:
                meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n",
                                     encoding="utf-8")
        if dry:
            continue
        send = restitled(fetch(api, row["video_id"]), want)
        if send is None:
            print("  (already says that; nothing sent)")
            continue
        push(api, row["video_id"], send)
        yp.record(book, {"key": f"{row['key']}#retitle", "episode": row["episode"],
                         "video_id": row["video_id"], "retitled_from": row["title"],
                         "title": want, "at": _now()})
        print("  updated.")

    if dry:
        print("\n--dry-run: nothing was sent and no youtube.json was written.")


def _now() -> str:
    import datetime as dt
    return dt.datetime.now().isoformat(timespec="seconds")


if __name__ == "__main__":
    main(sys.argv)
