#!/usr/bin/env python
"""The whole book as one regular video (owner, 2026-10-10).

    uv run python scripts/publish/book_compilation.py <codex_id> --dry-run
    uv run python scripts/publish/book_compilation.py <codex_id> --upload

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

import datetime as dt
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio import book_compilation as bc  # noqa: E402
from studio import edit_gate, episode_home, youtube, youtube_publish as yp  # noqa: E402
from studio.trailer_assemble import clip_seconds  # noqa: E402

FPS = 24
FOOTER = ("Source: H. G. Wells, The War of the Worlds (1898), in the public domain. This is an\n"
          "adapted, abridged screenplay of the novel, not its complete text.\n"
          "— The Keeper's Lantern —\n"
          "AI DISCLOSURE: the picture and the voices in this video are generated. The words\n"
          "are Wells's story, adapted; the performances are synthetic.")


def episode_meta(book: Path, n: int) -> dict:
    return episode_home.read_json(episode_home.home(book, n) / "youtube.json")


def chapters_in_book(book: Path) -> int:
    """The book's chapter count, read off episode 1's title ('Ep 01/27')."""
    m = re.search(r"Ep \d+/(\d+)", episode_meta(book, 1)["title"])
    if not m:
        raise SystemExit("episode 1's title names no chapter count ('Ep NN/TT')")
    return int(m.group(1))


def frames(video: Path) -> int:
    """The picture's frame count, decoded (the container's duration lies)."""
    seen = subprocess.run(["ffmpeg", "-v", "quiet", "-stats", "-i", str(video), "-map", "0:v",
                           "-f", "null", "-"], capture_output=True, text=True, errors="replace")
    return int(seen.stderr.rsplit("frame=", 1)[1].split()[0])


def card_of(book: Path, n: int) -> Path:
    card = book / "title" / f"ep{n:02d}.mp4"
    return card if card.exists() else book / "title" / "title.mp4"


def split(book: Path, n: int, master: Path) -> tuple[Path, Path]:
    """The chapter's two videos -- title, main -- cut out of its Short
    (owner 2026-10-11); each piece's frames checked against its range."""
    folder = book / "compilation" / "chapters"
    folder.mkdir(parents=True, exist_ok=True)
    card = frames(card_of(book, n))
    main = bc.main_frames(master_frames=frames(master), card_frames=card, chip_frames=edit_gate.END_CHIP_FRAMES)
    out = {}
    for name, (a, b) in bc.pieces(main=main, card=card).items():
        out[name] = folder / f"ep{n:02d}_{name}.mp4"
        if not (out[name].exists() and frames(out[name]) == b - a):
            subprocess.run(bc.cut_argv(master, (a, b), out[name], fps=FPS), check=True)
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
    return out


def next_iter(folder: Path) -> Path:
    k = 1
    while (folder / f"whole_book_iter{k}.mp4").exists():
        k += 1
    return folder / f"whole_book_iter{k}.mp4"


def join(parts: list, folder: Path) -> Path:
    """The parts joined by stream copy, checked against the sum of their lengths."""
    folder.mkdir(parents=True, exist_ok=True)
    listing = folder / "concat.txt"
    listing.write_text(bc.concat_list(bc.title_first([tuple(p[2]) for p in parts])), encoding="utf-8")
    out = next_iter(folder)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(listing),
                    "-c", "copy", "-movflags", "+faststart", str(out)], check=True)
    want, got = sum(p[3] for p in parts), clip_seconds(out)
    if abs(got - want) > 2.0:
        raise SystemExit(f"REFUSED: the join is {got:.1f} s against the parts' {want:.1f} s")
    return out


def metadata(book: Path, parts: list) -> dict:
    first = episode_meta(book, 1)
    series = first["title"].split(" — Ep")[0]
    lines = bc.chapter_lines([(n, t, s) for n, t, _, s in parts])
    book = series.split(": ", 1)[-1]
    intro = (f"{book}, told from beginning to end as one film: our screen adaptation of the novel, "
             f"in {len(parts)} episodes, each one chapter of the book. The Martian cylinders fall on "
             f"Surrey, the fighting-machines march on London, and one man survives to tell it. "
             f"Use the chapters above to jump to any episode.")
    return {"title": bc.title(series, len(parts)),
            "description": bc.description(lines, intro=intro, footer=FOOTER),
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


def retitle(api, video_id: str, meta: dict) -> dict:
    """The live video's title and description replaced; every other snippet field
    carried over (videos.update REPLACES the part -- a missing categoryId fails)."""
    from scripts.publish import youtube_retitle
    snippet = dict(youtube_retitle.fetch(api, video_id), title=meta["title"], description=meta["description"])
    return youtube_retitle.push(api, video_id, snippet)


def main(argv: list[str]) -> None:
    book = episode_home.book_dir(argv[1])
    parts = parts_of(book)
    meta = metadata(book, parts)
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
    out = join(parts, folder)
    episode_home.write_json(folder / "youtube.json", meta | {"file": episode_home.relative(book, out),
                                                              "sha8": yp.sha8(out)})
    print(out.resolve())
    print(f"{len(parts)} chapters, {clip_seconds(out) / 60:.1f} min\n\n{meta['title']}\n\n{meta['description']}")
    if "--upload" in argv:
        print(f"\nhttps://youtu.be/{upload(book, out, meta)}")


if __name__ == "__main__":
    main(sys.argv)
