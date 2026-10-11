#!/usr/bin/env python
"""The whole book as one regular video (owner, 2026-10-10).

    uv run python scripts/publish/book_compilation.py <codex_id> --dry-run
    uv run python scripts/publish/book_compilation.py <codex_id> --upload [--replaces=<old video id>]

Every published episode's Short -- the exact bytes the channel carries, matched
by the ledger's sha8 -- is cut into its two videos, the title card and the main
video (`compilation/chapters/epNN_title.mp4`, `epNN_main.mp4`), and the book is
joined TITLE FIRST, then main, chapter after chapter (owner 2026-10-11), by
stream copy (every piece is one encode), into
`library/<book>/compilation/whole_book_iterN.mp4`.  The description OPENS with
YouTube chapter timestamps, one per episode from 0:00.  `--upload` sends it as a
regular public video and records it in the book's upload ledger.  Refuses while
any chapter of the book is unpublished.
"""
from __future__ import annotations

import contextlib
import datetime as dt
import json
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio import book_compilation as bc  # noqa: E402
from studio import episode_home, youtube, youtube_publish as yp  # noqa: E402
from studio.trailer_assemble import clip_seconds  # noqa: E402

FPS, SIDE = 24, 1536
def episode_meta(book: Path, n: int) -> dict:
    return episode_home.read_json(episode_home.home(book, n) / "youtube.json")


def chapters_in_book(book: Path) -> int:
    """The book's chapter count, read off episode 1's title ('Ep 01/27')."""
    m = re.search(r"Ep \d+/(\d+)", episode_meta(book, 1)["title"])
    if not m:
        raise SystemExit("episode 1's title names no chapter count ('Ep NN/TT')")
    return int(m.group(1))


GPU_DECODE = ["-hwaccel", "cuda"]
"""The measuring passes decode on the GPU (6.8 s a Short); in software every
check sat on the CPU with the GPU idle (owner, 2026-10-11)."""


def count_argv(video: Path) -> list[str]:
    """The frame count read off the packets, nothing decoded (215 ms, against ~15 s
    decoding a 1536 Short) -- packets, not the container's duration, which lies."""
    return ["ffmpeg", "-v", "quiet", "-stats", "-i", str(video), "-map", "0:v", "-c", "copy", "-f", "null", "-"]


def frames(video: Path) -> int:
    """The picture's frame count."""
    seen = subprocess.run(count_argv(video), capture_output=True, text=True, errors="replace")
    return int(seen.stderr.rsplit("frame=", 1)[1].split()[0])


def scene_scores(master: Path) -> dict[int, float]:
    """Every frame's scene-change score, keyed by frame (read at low size)."""
    seen = subprocess.run(["ffmpeg", "-hide_banner", *GPU_DECODE, "-i", str(master), "-an", "-vf",
                           "scale=192:-2,select='gte(scene,0)',metadata=print:key=lavfi.scene_score",
                           "-f", "null", "-"], capture_output=True, text=True, errors="replace")
    pairs = re.findall(r"pts_time:([0-9.]+)[^\n]*\n[^\n]*scene_score=([0-9.]+)", seen.stderr)
    return {bc.frame_at(float(t), fps=FPS): float(v) for t, v in pairs}


def black_tail(master: Path) -> float:
    """Where the Short's closing black begins, in seconds."""
    seen = subprocess.run(["ffmpeg", "-hide_banner", *GPU_DECODE, "-i", str(master), "-an", "-vf",
                           "scale=192:-2,blackdetect=d=0.05:pix_th=0.10", "-f", "null", "-"],
                          capture_output=True, text=True, errors="replace")
    starts = re.findall(r"black_start:([0-9.]+)", seen.stderr)
    if not starts:
        raise SystemExit(f"REFUSED: {master.name} has no closing black to find its card by")
    return float(starts[-1])


def card_of(book: Path, n: int) -> Path:
    """The chapter's title card file: its own, else the book's."""
    card = book / "title" / f"ep{n:02d}.mp4"
    return card if card.exists() else book / "title" / "title.mp4"


def split(book: Path, n: int, master: Path) -> tuple[Path, Path]:
    """The chapter's two videos -- title, main -- cut out of its Short
    (owner 2026-10-11); the card MEASURED in the Short (the cut where its own
    length puts it before the closing black), each piece's frames checked."""
    folder = book / "compilation" / "chapters"
    folder.mkdir(parents=True, exist_ok=True)
    black = bc.frame_at(black_tail(master), fps=FPS)
    start = bc.card_start(scores=scene_scores(master), black_from=black, card_frames=frames(card_of(book, n)))
    out = {}
    for name, (a, b) in bc.pieces(main=start, card=black - start).items():
        out[name] = folder / f"ep{n:02d}_{name}.mp4"
        if not (out[name].exists() and frames(out[name]) == b - a):
            subprocess.run(bc.cut_argv(master, (a, b), out[name], fps=FPS, side=SIDE), check=True)
        if (got := frames(out[name])) != b - a:
            raise SystemExit(f"REFUSED: ep{n:02d} {name} is {got} frames, wanted {b - a}")
    return out["title"], out["main"]


def parts_of(book: Path) -> list[tuple[int, str, list[Path], float]]:
    """(episode, chapter title, [title, main], seconds) for every chapter --
    the title FIRST (owner 2026-10-11); refuses a gap."""
    total, pub = chapters_in_book(book), dict(bc.published(book))
    if missing := [n for n in range(1, total + 1) if n not in pub]:
        raise SystemExit(f"REFUSED: chapters {missing} are not published yet; the book is {total} chapters")
    out = []
    for n in range(1, total + 1):
        master = bc.uploaded_master(episode_home.home(book, n) / "cut", pub[n])
        if master is None:
            raise SystemExit(f"REFUSED: ep{n:02d}'s uploaded master ({pub[n]}) is not on disk")
        pair = split(book, n, master)
        out.append((n, bc.chapter_of(episode_meta(book, n)["title"]), list(pair),
                    sum(frames(p) for p in pair) / FPS))
        print(f"  ep{n:02d}/{total}: title {frames(pair[0])}f + main {frames(pair[1])}f", flush=True)
    return out


def next_iter(folder: Path) -> Path:
    k = 1
    while (folder / f"whole_book_iter{k}.mp4").exists():
        k += 1
    return folder / f"whole_book_iter{k}.mp4"


def running_order(main_title: Path, parts: list) -> list[Path]:
    """The book's main title, then every chapter title first (owner 2026-10-11)."""
    return [main_title] + bc.title_first([tuple(p[2]) for p in parts])


def join(order: list[Path], want: float, folder: Path) -> Path:
    """The pieces joined by stream copy, checked against the sum of their lengths."""
    folder.mkdir(parents=True, exist_ok=True)
    listing = folder / "concat.txt"
    listing.write_text(bc.concat_list(order), encoding="utf-8")
    out = next_iter(folder)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(listing),
                    "-c", "copy", "-movflags", "+faststart", str(out)], check=True)
    if abs((got := clip_seconds(out)) - want) > 2.0:
        raise SystemExit(f"REFUSED: the join is {got:.1f} s against the parts' {want:.1f} s")
    return out


def set_thumbnail(api, video_id: str, jpg: Path) -> str:
    """'set', or 'refused: <why>' -- an unverified channel answers 403 and the
    video ships anyway; the refusal is recorded, never raised."""
    from googleapiclient.http import MediaFileUpload
    try:
        api.thumbnails().set(videoId=video_id, media_body=MediaFileUpload(str(jpg), mimetype="image/jpeg")).execute()
        return "set"
    except Exception as why:
        return f"refused: {why}"


def metadata(book: Path, parts: list, lead_s: float = 0.0) -> dict:
    """Title, description (chapters first) and tags, from the book's own
    source/book.json -- the code names no book."""
    first, source = episode_meta(book, 1), episode_home.read_json(book / "source" / "book.json")
    series = first["title"].split(" — Ep")[0]
    name = source.get("display_title") or source["title"]
    lines = bc.chapter_lines([(n, t, s) for n, t, _, s in parts], lead_s=lead_s)
    text = bc.description(lines, intro=bc.intro(book=name, episodes=len(parts)),
                          footer=bc.footer(author=source["author"], book=name))
    return {"title": bc.title(series, len(parts)), "description": text,
            "tags": first.get("tags", []), "synthetic": True, "chapters": lines}


def upload(book: Path, out: Path, meta: dict) -> str:
    """Sent as a regular public video; recorded; flipped public if it landed private."""
    from scripts.publish import youtube_privacy, youtube_upload
    digest = yp.sha8(out)
    key = f"{book.name}/compilation/{digest}"
    if done := yp.uploaded(book, key):
        raise SystemExit(f"REFUSED: this compilation is already uploaded as {done.get('video_id')}")
    body = yp.spec(meta["title"], meta["description"], meta["tags"], synthetic=meta["synthetic"], privacy="public")
    got = youtube_upload.send(out, body, youtube.credentials())
    vid, privacy = got.get("id"), got.get("status", {}).get("privacyStatus")
    yp.record(book, {"key": key, "episode": "compilation", "video_id": vid, "privacy": privacy,
                     "title": meta["title"], "sha8": digest, "at": dt.datetime.now(dt.timezone.utc).isoformat()})
    if privacy != "public":
        api = youtube_privacy._build_api()
        youtube_privacy.set_privacy(api, vid, youtube_privacy.live_status(api, vid), "public")
        yp.record(book, {"key": f"{key}#public", "episode": "compilation", "video_id": vid,
                         "privacy": "public", "why": "owner 2026-10-10: the whole book as one video"})
    return vid


def finish(book: Path, vid: str, thumb: Path, replaces: str) -> None:
    """The thumbnail set, and the video this one replaces made private (never
    deleted: private is undone with one call); both recorded."""
    from scripts.publish import youtube_privacy
    api = youtube_privacy._build_api()
    said = set_thumbnail(api, vid, thumb)
    yp.record(book, {"key": f"{book.name}/compilation/{vid}#thumbnail", "episode": "compilation",
                     "video_id": vid, "thumbnail": said, "file": episode_home.relative(book, thumb)})
    print(f"thumbnail: {said}")
    if replaces:
        youtube_privacy.set_privacy(api, replaces, youtube_privacy.live_status(api, replaces), "private")
        yp.record(book, {"key": f"{book.name}/compilation/{replaces}#private", "episode": "compilation",
                         "video_id": replaces, "privacy": "private", "replaced_by": vid,
                         "why": "owner 2026-10-11: the book video re-made with the main title, title first"})
        print(f"retired https://youtu.be/{replaces} (private)")


def retitle(api, video_id: str, meta: dict) -> dict:
    """The live video's title and description replaced; every other snippet field
    carried over (videos.update REPLACES the part -- a missing categoryId fails)."""
    from scripts.publish import youtube_retitle
    snippet = dict(youtube_retitle.fetch(api, video_id), title=meta["title"], description=meta["description"])
    return youtube_retitle.push(api, video_id, snippet)


def pid_alive(pid: int) -> bool:
    """Whether a Windows process is still running."""
    import ctypes
    k32 = ctypes.windll.kernel32
    handle = k32.OpenProcess(0x1000, False, pid)            # PROCESS_QUERY_LIMITED_INFORMATION
    if not handle:
        return False
    code = ctypes.c_ulong()
    k32.GetExitCodeProcess(handle, ctypes.byref(code))
    k32.CloseHandle(handle)
    return code.value == 259                                # STILL_ACTIVE


@contextlib.contextmanager
def book_lock(book: Path):
    """One compilation per book at a time: a 'detached' run survived its shell and
    raced the upload run on the same pieces (2026-10-11)."""
    lock = book / "compilation" / ".lock"
    lock.parent.mkdir(parents=True, exist_ok=True)
    if holder := bc.lock_holder(lock, alive=pid_alive):
        raise SystemExit(f"REFUSED: process {holder} is already compiling {book.name}")
    lock.write_text(str(os.getpid()), encoding="utf-8")
    try:
        yield
    finally:
        lock.unlink(missing_ok=True)


def door_sheet(book: Path, parts: list) -> Path:
    """Every chapter's first title frame and last main frame, side by side: what a
    person checks the order by at a glance (compilation/door_sheet.png)."""
    folder = book / "compilation" / "door"
    folder.mkdir(parents=True, exist_ok=True)
    for k, (_, _, (title_piece, main_piece), _) in enumerate(parts, start=1):
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(title_piece), "-sseof", "-0.5", "-i", str(main_piece),
                        "-filter_complex", "[0:v]scale=160:160[a];[1:v]scale=160:160[b];[a][b]hstack",
                        "-frames:v", "1", "-update", "1", str(folder / f"{k:03d}.png")], check=True)
    out = book / "compilation" / "door_sheet.png"
    cols = 4
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-start_number", "1", "-i", str(folder / "%03d.png"),
                    "-vf", f"tile={cols}x{-(-len(parts) // cols)}:padding=4", "-frames:v", "1", str(out)], check=True)
    return out


def door(book: Path, order: list[Path], parts: list) -> dict:
    """The upload door: running order, each title piece against its card, the
    main title's verdict; refuses on any fault, writes compilation/door.json."""
    verdict_path = book / "title" / "book" / "verdict.json"
    faults = bc.door_faults(title_frames={p[0]: frames(p[2][0]) for p in parts},
                            card_frames={p[0]: frames(card_of(book, p[0])) for p in parts},
                            order_ok=bc.title_first_order(order),
                            title_verdict=episode_home.read_json(verdict_path) if verdict_path.exists() else {"refused": ["no verdict"]})
    record = {"faults": faults, "sheet": episode_home.relative(book, door_sheet(book, parts))}
    episode_home.write_json(book / "compilation" / "door.json", record)
    if faults:
        raise SystemExit(f"REFUSED at the door: {faults}")
    return record


def main(argv: list[str]) -> None:
    sys.stdout.reconfigure(line_buffering=True)              # the log is read while it runs
    book = episode_home.book_dir(argv[1])
    with book_lock(book):
        run(book, argv)


def run(book: Path, argv: list[str]) -> None:
    from concurrent.futures import ThreadPoolExecutor
    from scripts.episode import book_title
    with ThreadPoolExecutor(1) as gpu:                       # the GPU works while the CPU cuts
        early = gpu.submit(book_title.prepare, book, chapters_in_book(book))
        parts = parts_of(book)
        early.result()
    main_title, thumb = book_title.ensure(book, len(parts))
    lead = frames(main_title) / FPS
    meta = metadata(book, parts, lead_s=lead)
    if retitle_id := next((a.split("=", 1)[1] for a in argv if a.startswith("--retitle=")), ""):
        from scripts.publish import youtube_privacy
        retitle(youtube_privacy._build_api(), retitle_id, meta)
        episode_home.write_json(book / "compilation" / "youtube.json",
                                episode_home.read_json(book / "compilation" / "youtube.json") | meta)
        yp.record(book, {"key": f"{book.name}/compilation/{retitle_id}#retitle", "episode": "compilation",
                         "video_id": retitle_id, "title": meta["title"],
                         "why": "owner 2026-10-11: an adaptation, not the complete book"})
        print(f"retitled https://youtu.be/{retitle_id}\n\n{meta['title']}\n\n{meta['description']}")
        return
    folder = book / "compilation"
    order = running_order(main_title, parts)
    print(f"door: {door(book, order, parts)}", flush=True)
    out = join(order, lead + sum(p[3] for p in parts), folder)
    episode_home.write_json(folder / "youtube.json", meta | {"file": episode_home.relative(book, out),
                                                              "sha8": yp.sha8(out),
                                                              "thumbnail": episode_home.relative(book, thumb)})
    print(out.resolve())
    print(f"{len(parts)} chapters, {clip_seconds(out) / 60:.1f} min\n\n{meta['title']}\n\n{meta['description']}")
    if "--upload" in argv:
        vid = upload(book, out, meta)
        print(f"\nhttps://youtu.be/{vid}")
        finish(book, vid, thumb, next((a.split("=", 1)[1] for a in argv if a.startswith("--replaces=")), ""))


if __name__ == "__main__":
    main(sys.argv)
