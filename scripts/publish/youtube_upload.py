#!/usr/bin/env python
"""Upload one finished episode to the channel.  PRIVATE, gated, once.

    uv run python scripts/publish/youtube_upload.py <codex_id> <episode> --dry-run
    uv run python scripts/publish/youtube_upload.py <codex_id> <episode> \\
        --watched=<sha8> --approved=publish

`--dry-run` costs nothing and touches no network: it prints the exact request
body, the file, and every gate's verdict.  Read that before the real run.

THE GATE SCALES WITH IRREVERSIBILITY, so this step AUTOMATES.

A PRIVATE upload publishes nothing -- invisible, deletable, reversible in one
click -- so it is carried by the machine gates alone and the episode chain can
end here with nobody watching:

    QC passed - no take failed DQ - nothing already uploaded for this cut

Anything a stranger can see adds the human gates on top: `--watched=<sha8>` of
the file somebody actually watched, and `--audited` once Google has granted the
compliance audit.  Until that audit, `videos.insert` from an unverified project
is forced private whatever you send -- the call still returns 200 with a video
id -- so `public` before then would only record a falsehood.

`--watched` IS A CLAIM, AND THE EYE REVIEW IS ITS EVIDENCE (2026-09-16).  Episode
9 passed 28/28 takes at 100.0 and looked worse than 4-7; the flag was satisfied
by an agent that had looked at six frames.  So the flag is accepted only when
`episodes/epNN/review/eye_<sha8>.json` (`scripts/episode/eye_review.py`) exists
for THIS cut with every rubric field answered, and no `n` without a
`waived_because` -- and the waivers are recorded in the ledger beside the video.

That split is deliberate.  Demanding a human for every network call would make
the pipeline un-automatable, and an un-automatable safety gate is one somebody
eventually comments out.

The metadata is READ FROM DISK (`episodes/epNN/youtube.json`), never generated
here.  The AI-disclosure declaration in it is the owner's statement to the
platform, so this script refuses to run without it.
"""
from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.episode import eye_review
from studio import judged
from studio import approval, episode_home, youtube, youtube_publish as yp


def eye_stops(home: Path, watched: str, digest: str) -> tuple[list[str], dict]:
    """Why `--watched` is not accepted, and what the ledger records when it is.

    No flag, no claim, nothing to check: a private upload never needed a human.
    With the flag, the rubric file for that sha must exist, describe THIS cut,
    answer every field, and carry a reason beside every `n`."""
    if not watched:
        return [], {}
    stops, rubric = eye_review.verdict(home, watched, digest)
    if stops:
        return stops, {}
    return [], yp.eye_record(rubric.get("sha8"), rubric.get("reviewed_by", ""),
                             waived=eye_review.waivers(rubric), flags=eye_review.flags(rubric))


def metadata(home: Path) -> dict:
    path = home / "youtube.json"
    if not path.exists():
        raise SystemExit(f"{path} is missing: write the title, description, tags and the "
                         f"synthetic-media declaration before publishing.")
    got = json.loads(path.read_text(encoding="utf-8"))
    if "synthetic" not in got:
        raise SystemExit(f"{path} must state \"synthetic\": true|false -- the AI disclosure is a "
                         f"declaration to YouTube and is never generated.")
    return got


def failed_takes(home: Path, engine: str = "r2v") -> list[str]:
    """Which takes the DQ refused, read from their own reports, for THIS engine."""
    out = []
    # THE TAKES ROOM.  This globbed `shots_r2v/`, a room retired in the layout
    # change, so the glob returned nothing and `dq_failed` was ALWAYS empty --
    # the DQ gate on the one irreversible step in the pipeline could not fire,
    # and `yp.waived` recorded `dq_failed: []` in the override ledger as well,
    # so the audit trail said the same false thing.
    folder = episode_home.takes_under(home, engine)
    for report in sorted(folder.glob("T*.dq.json")):
        if not json.loads(report.read_text(encoding="utf-8")).get("passed"):
            out.append(report.stem.split(".")[0])
    # AND EVERY TAKE NOBODY JUDGED: counting only the reports that exist let a
    # take rendered and never measured reach the one irreversible step
    # (audit 2026-09-22, item 6).
    # WHAT IS IN THE PICTURE counts too: ep08 went public with a newspaper
    # printed "NEWSPAPER BOY" and four identical shopmen, at 100/100 on the
    # take gate, because no content verdict reached this refusal.
    for report in sorted(folder.glob("T*.content.json")):
        said = json.loads(report.read_text(encoding="utf-8"))
        if not said.get("passed"):
            out.append(f"{report.stem.split('.')[0]} (content: {'; '.join(said.get('faults', []))[:80]})")
    out += [f"{name} (never judged)" for name in judged.unjudged_takes(folder, kinds=("dq", "content"))]
    return out


def send(path: Path, body: dict, creds) -> dict:
    """The one call that publishes.  Injected in tests; never reached by them."""
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    api = build("youtube", "v3", credentials=creds, cache_discovery=False)
    media = MediaFileUpload(str(path), chunksize=8 << 20, resumable=True, mimetype="video/mp4")
    call = api.videos().insert(part="snippet,status", body=body, media_body=media)
    got = None
    while got is None:
        status, got = call.next_chunk()
        if status:
            print(f"    {int(status.progress() * 100):3d}%", flush=True)
    return got


def main(argv: list[str], send=send) -> None:
    args = [a for a in argv[1:] if not a.startswith("--")]
    book_id, number = args[0], int(args[1])
    dry = "--dry-run" in argv
    watched = next((a.split("=", 1)[1] for a in argv if a.startswith("--watched=")), "")
    # --override="<reason>" waives the two QUALITY gates (qc.passed, the DQ roll-up)
    # and NOTHING else: not `already uploaded`, not --watched, not --audited. The
    # reason is recorded beside the upload in the ledger.
    override = next((a.split("=", 1)[1] for a in argv if a.startswith("--override=")), "")

    book = episode_home.book_dir(book_id)
    home = episode_home.home(book, number)
    engine = next((a.split("=", 1)[1] for a in argv if a.startswith("--engine=")), "")
    engine, master, qc_path = yp.deliverable(home, engine)

    meta = metadata(home)
    digest = yp.sha8(master)
    key = yp.upload_key(book.name, number, digest)
    qc = json.loads(qc_path.read_text(encoding="utf-8")) if qc_path.exists() else {}

    privacy = next((a.split("=", 1)[1] for a in argv if a.startswith("--privacy=")),
                   meta.get("privacy", "private"))
    body = yp.spec(meta["title"], meta["description"], meta.get("tags", []),
                   synthetic=meta["synthetic"], privacy=privacy)
    dq_failed = failed_takes(home, engine)
    stops = yp.refusals(qc, dq_failed, privacy=body["status"]["privacyStatus"],
                        watched=watched, digest=digest, already=yp.uploaded(book, key),
                        audited="--audited" in argv, override=override)
    waived = yp.waived(qc, dq_failed, override=override)
    seen, eye = eye_stops(home, watched, digest)
    stops += seen

    print(f"file      {master}")
    print(f"size      {master.stat().st_size / 1e6:.1f} MB   sha8 {digest}")
    print(f"engine    {engine}")
    print(f"qc        {qc_path.name} passed={qc.get('passed')}")
    print(f"title     {body['snippet']['title']}")
    print(f"privacy   {body['status']['privacyStatus']}   "
          f"synthetic={body['status']['containsSyntheticMedia']}")
    print(f"tags      {len(body['snippet']['tags'])}")
    print(f"\ndescription ({len(body['snippet']['description'])} chars):\n"
          f"{body['snippet']['description']}\n")

    if waived:
        print(f"OVERRIDE  {waived['reason']}")
        print(f"  waived qc.passed={waived['qc_passed']} and "
              f"{len(waived['dq_failed'])} failed take(s): {', '.join(waived['dq_failed']) or 'none'}")
        print("  recorded in the ledger beside this upload.")
    if eye:
        print(f"EYE       reviewed by {eye['reviewed_by'] or '(unsigned)'}; "
              f"waived: {', '.join(f'{k}: {v}' for k, v in eye['waived'].items()) or 'nothing'}")

    if stops:
        print("REFUSED:")
        for stop in stops:
            print(f"  - {stop}")
        raise SystemExit(1)
    print("all gates pass.")

    if dry:
        print("\n--dry-run: nothing was uploaded.")
        return

    approval.require("publish", f"uploading ep{number:02d} to YouTube as "
                                f"{body['status']['privacyStatus']}", 0.0,
                     approval.approved_for("publish", argv))
    got = send(master, body, youtube.credentials())
    video_id = got.get("id")
    yp.record(book, {"key": key, "episode": number, "video_id": video_id, "waived": waived,
                     "eye": eye, "privacy": got.get("status", {}).get("privacyStatus"),
                     "title": body["snippet"]["title"], "sha8": digest,
                     "at": dt.datetime.now().isoformat(timespec="seconds")})
    print(f"\nuploaded: https://youtu.be/{video_id}")
    print(f"  privacy as returned by YouTube: {got.get('status', {}).get('privacyStatus')}")
    if got.get("status", {}).get("privacyStatus") != body["status"]["privacyStatus"]:
        print("  NOTE: YouTube changed the privacy -- that is the unverified-project lock.")


if __name__ == "__main__":
    main(sys.argv)
