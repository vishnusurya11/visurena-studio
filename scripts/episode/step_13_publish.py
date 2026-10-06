#!/usr/bin/env python
"""Step 13 -- publish: metadata, the measured sign-off, upload, the public
flip, the /shorts/ poll -- and the public Short URL as the LAST line printed.

    uv run python scripts/episode/step_13_publish.py <codex_id> <n>

The last mile was hand work: youtube.json and the director's sign-off typed,
youtube_upload/youtube_privacy driven from a shell, drive.py ending at a
manifest instead of a URL.  Everything needed was already measured on disk,
so this step only assembles and sends:

  G-STANDING   library/<book>/publish/standing.json is the owner's one-time
               standing hand; absent, the unit PARKS (the one standing hand kept
               by decision 2026-10-01; F3 writes it at book setup) and nothing
               uploads.  RENDER_HOLD still stops everything first (GPU=True
               puts this step behind the runner's brake too).
  G-META       metadata.ensure() is called IN-PROCESS so llm.spend_context /
               guard_spend (the $3 wall) cover its one paid call -- never via
               ctx.run_script: a subprocess has an empty spend context and
               would walk past the wall.
  G-PUBLIC     the UNCHANGED chain in youtube_upload/youtube_privacy decides;
               --watched=<sha8> is satisfied by the judge-filled eye rubric
               review/eye_<sha8>.json under decision
               2026-10-01-no-human-input-at-publish.
  G-SHORTS     advisory terminal: GET youtube.com/shorts/<id> until the final
               URL still says /shorts/ at 200 (cap 600 s); the honest outcome
               is recorded in uploads.jsonl either way, never a stop -- the
               video is already public.

Idempotent per cut: an uploaded sha8 is never re-sent (yp.uploaded); a recut
is a new sha8 and a new upload by design.
"""
from __future__ import annotations

import datetime as dt
import json
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.publish import metadata, signoff, youtube_privacy, youtube_upload  # noqa: E402
from studio import standing_approval, step_cli  # noqa: E402
from studio import youtube_publish as yp  # noqa: E402
from studio.learnings import Learning, record  # noqa: E402

STEP_ID = "13"
NAME = "publish"
GPU = True
"""Going public is the one irreversible act in the chain, so the runner's
RENDER_HOLD brake covers this step the way it covers a render."""
WHY = standing_approval.DECISION
POLL_EVERY_S, POLL_CAP_S = 30.0, 600.0


# ---- the ledger, read ------------------------------------------------------------

def rows(book: Path) -> list[dict]:
    path = yp.ledger_path(book)
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()]


def _newest(book: Path, video_id: str, event: str, **want) -> dict | None:
    found = None
    for row in rows(book):
        if (row.get("event") == event and row.get("video_id") == video_id
                and all(row.get(k) == v for k, v in want.items())):
            found = row
    return found


def public_row(book: Path, video_id: str) -> dict | None:
    """The ledger row where YouTube RETURNED public -- never what was asked."""
    return _newest(book, video_id, "privacy", privacy="public")


def poll_row(book: Path, video_id: str) -> dict | None:
    return _newest(book, video_id, "shorts_poll")


# ---- the argv the unchanged gate chain receives -----------------------------------

def upload_argv(book_id: str, number: int, sha8: str) -> list[str]:
    """--watched=<sha8>: the judge-filled eye rubric IS the watch (G-PUBLIC)."""
    return ["youtube_upload.py", book_id, str(number), f"--watched={sha8}",
            "--approved=publish"]


def privacy_argv(book_id: str, number: int) -> list[str]:
    return ["youtube_privacy.py", book_id, str(number), "public",
            "--approved=publish", f"--why={WHY}"]


# ---- the acts, each once per cut ---------------------------------------------------

def upload(ctx, sha8: str, send) -> str:
    """The private upload, once per cut; the ledger row is the receipt."""
    key = yp.upload_key(ctx.book_dir.name, ctx.number, sha8)
    if not yp.uploaded(ctx.book_dir, key):
        youtube_upload.main(upload_argv(ctx.book_id, ctx.number, sha8), send=send)
    row = yp.uploaded(ctx.book_dir, key)
    if not row or not row.get("video_id"):
        raise SystemExit(f"the upload left no ledger row for {key}")
    return row["video_id"]


def flip_public(ctx, video_id: str, build_api) -> dict | None:
    """The public flip through the UNCHANGED policy chain, once per video."""
    if not public_row(ctx.book_dir, video_id):
        youtube_privacy.main(privacy_argv(ctx.book_id, ctx.number), build_api=build_api)
    return public_row(ctx.book_dir, video_id)


def urllib_get(url: str) -> tuple[int, str]:
    """GET following redirects: (status, FINAL url) -- a Short that lands on
    /watch answered 200 somewhere that is not /shorts/."""
    with urllib.request.urlopen(url, timeout=30) as got:
        return got.status, got.geturl()


def poll_shorts(video_id: str, http=urllib_get, every: float = POLL_EVERY_S,
                cap: float = POLL_CAP_S, sleep=time.sleep) -> dict:
    """G-SHORTS, ADVISORY TERMINAL: pass when the final URL still holds
    /shorts/ at 200; a timeout returns the honest answer, never a stop."""
    url = f"https://www.youtube.com/shorts/{video_id}"
    waited = 0.0
    while True:
        try:
            status, final = http(url)
        except OSError as why:
            status, final = 0, f"({why})"
        if status == 200 and "/shorts/" in str(final):
            return {"status": status, "final_url": str(final), "passed": True}
        if waited >= cap:
            return {"status": status, "final_url": str(final), "passed": False}
        sleep(every)
        waited += every


def record_poll(ctx, video_id: str, got: dict) -> None:
    """The poll's outcome beside the upload; a non-Short answer is a recorded
    flag -- the video is already public, so this records truth, never stops."""
    yp.record(ctx.book_dir, {"event": "shorts_poll", "video_id": video_id,
                             "status": got["status"], "final_url": got["final_url"],
                             "at": dt.datetime.now().isoformat(timespec="seconds")})
    if not got["passed"]:
        record(Path(ctx.home) / "learnings.jsonl",
               Learning(step=STEP_ID, gate="G-SHORTS", action="flag", terminal=True,
                        note=f"not serving as a Short: {got['status']} {got['final_url']}"[:160]))
        print(f"G-SHORTS: not serving as a Short yet ({got['status']} {got['final_url']}); "
              f"recorded, not a stop -- the video is public")


# ---- the step ---------------------------------------------------------------------

def done(ctx) -> bool:
    """A public row and a poll row exist for THIS cut's own upload."""
    try:
        _engine, master, _qc = yp.deliverable(ctx.home, "")
    except SystemExit:
        return False
    key = yp.upload_key(ctx.book_dir.name, ctx.number, yp.sha8(master))
    row = yp.uploaded(ctx.book_dir, key)
    if not row or not row.get("video_id"):
        return False
    return bool(public_row(ctx.book_dir, row["video_id"])
                and poll_row(ctx.book_dir, row["video_id"]))


def run(ctx, send=youtube_upload.send, build_api=None, http=urllib_get,
        sleep=time.sleep) -> None:
    """The whole last mile; the public Short URL is the LAST line printed."""
    engine, master, _qc = yp.deliverable(ctx.home, "")
    sha8 = yp.sha8(master)
    if not standing_approval.ok(ctx.book_dir):
        raise standing_approval.escalation(ctx.book_dir)
    metadata.ensure(ctx.home, ctx.book_dir, ctx.number)  # IN-PROCESS: the $3 wall applies
    signoff.write(ctx.home, sha8, engine)
    print(f"--watched={sha8}: the master eye's measured rubric review/eye_{sha8}.json "
          f"is the watch (judge:master_eye, decision {WHY})")
    video_id = upload(ctx, sha8, send)
    if not flip_public(ctx, video_id, build_api):
        print(f"NOT-PUBLIC: YouTube did not return public for {video_id}; the ledger "
              f"records what happened, and nothing more is claimed")
        raise SystemExit(f"https://youtu.be/{video_id} is NOT public; fix the channel, re-run")
    if not poll_row(ctx.book_dir, video_id):
        record_poll(ctx, video_id, poll_shorts(video_id, http=http, sleep=sleep))
    print(f"https://www.youtube.com/shorts/{video_id}")


if __name__ == "__main__":
    raise SystemExit(step_cli.main(sys.modules[__name__], sys.argv))
