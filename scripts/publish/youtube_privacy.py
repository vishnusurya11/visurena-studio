#!/usr/bin/env python
"""Set the privacy of an episode that is already on the channel.

    uv run python scripts/publish/youtube_privacy.py <codex_id> <episode> public --dry-run
    uv run python scripts/publish/youtube_privacy.py <codex_id> <episode> public \\
        --approved=publish

THIS EXISTS BECAUSE THE UPLOAD IS THE WRONG PLACE TO CHANGE YOUR MIND. An
upload happens once and is recorded in the ledger; going from private to
public afterwards is a second, separate decision about who may see the file,
and `youtube_upload.py` says so itself: "publish later with videos.update".
There was no script for that, so a privacy change meant either re-uploading
(a second copy on the channel, which the `already` gate exists to stop) or
doing it by hand outside the ledger.

MAKING SOMETHING PUBLIC IS THE ONLY IRREVERSIBLE STEP IN THE CHAIN. Private is
invisible and deletable; public is seen by strangers and cannot be unseen. So
this asks for `--approved=publish` before a single call goes out, reads the
live status back afterwards and records what YouTube actually returned -- not
what we asked for. An unverified API project forces private on INSERT, and
this is the call that finds out whether it does the same on UPDATE.

The ledger keeps the change beside the upload it amends, so the record of who
could see this file, and from when, stays in one place.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from studio import approval, episode_home, youtube
from studio import youtube_publish as yp

ALLOWED = ("private", "unlisted", "public")


def row_for(book: Path, number: int) -> dict:
    """The newest ledger row for this episode -- the cut that is live."""
    found = None
    for line in yp.ledger_path(book).read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            if row.get("episode") == number and row.get("video_id"):
                found = row
    if not found:
        raise SystemExit(f"episode {number} has no upload in the ledger")
    return found


def public_gates(book: Path, number: int, row: dict, engine: str = "r2v") -> list[str]:
    """The machine gates on the cut the ledger says is on the channel."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from youtube_upload import failed_takes
    home = episode_home.home(book, number)
    engine, _master, qc_path = yp.deliverable(home, engine)
    qc = json.loads(qc_path.read_text(encoding="utf-8")) if qc_path.exists() else {}
    return yp.public_refusals(qc, failed_takes(home, engine), row)


def live_status(api, video_id: str) -> dict:
    got = api.videos().list(part="status", id=video_id).execute()
    if not got.get("items"):
        raise SystemExit(f"{video_id} is not visible to this token")
    return got["items"][0]["status"]


def set_privacy(api, video_id: str, status: dict, privacy: str) -> dict:
    """`videos.update` REPLACES the whole part, so the live status is carried
    over and only privacyStatus is changed -- otherwise the call would blank
    the made-for-kids and licence fields it never read."""
    body = dict(status)
    body["privacyStatus"] = privacy
    got = api.videos().update(part="status",
                              body={"id": video_id, "status": body}).execute()
    return got.get("status", {})


def record(book: Path, row: dict, was: str, asked: str, got: str, why: str) -> None:
    with yp.ledger_path(book).open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({
            "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "episode": row["episode"], "video_id": row["video_id"],
            "event": "privacy", "was": was, "asked": asked, "privacy": got,
            "sha8": row.get("sha8"), "why": why,
        }, ensure_ascii=False) + "\n")


def main(argv: list[str]) -> None:
    args = [a for a in argv[1:] if not a.startswith("--")]
    book_id, number, privacy = args[0], int(args[1]), args[2].lower()
    if privacy not in ALLOWED:
        raise SystemExit(f"privacy must be one of {ALLOWED}, not {privacy!r}")
    why = next((a.split("=", 1)[1] for a in argv if a.startswith("--why=")), "")
    dry = "--dry-run" in argv

    book = episode_home.book_dir(book_id)
    row = row_for(book, number)
    print(f"episode   {number}")
    print(f"video     https://youtu.be/{row['video_id']}")
    print(f"recorded  privacy {row.get('privacy')} at {row.get('at')}")
    print(f"asking    {privacy}")
    if why:
        print(f"why       {why}")
    if privacy == "public" and (stops := public_gates(book, number, row)):
        raise SystemExit("NOT MADE PUBLIC:\n  " + "\n  ".join(stops))
    if dry:
        print("\n--dry-run: nothing was changed.")
        return

    from googleapiclient.discovery import build
    api = build("youtube", "v3", credentials=youtube.credentials(), cache_discovery=False)
    was = live_status(api, row["video_id"]).get("privacyStatus")
    print(f"live      {was}")
    if was == privacy:
        print("already there; nothing sent.")
        return
    approval.require("publish",
                     f"setting episode {number} from {was} to {privacy} on the channel",
                     0.0, approval.approved_for("publish", argv))
    got = set_privacy(api, row["video_id"], live_status(api, row["video_id"]), privacy)
    back = got.get("privacyStatus")
    record(book, row, was, privacy, back, why)
    print(f"\nprivacy as returned by YouTube: {back}")
    if back != privacy:
        print(f"ASKED FOR {privacy} AND GOT {back}: the channel or the API project would not "
              f"allow it. The ledger records what happened, not what was asked.")


if __name__ == "__main__":
    main(sys.argv)
