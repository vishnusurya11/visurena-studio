#!/usr/bin/env python
"""Draw the storyboard with gpt-image and cut every panel into a shot's first frame.

    uv run python scripts/episode/storyboard.py <codex_id> <episode>           # sheets + panels
    uv run python scripts/episode/storyboard.py <codex_id> <episode> --review  # contact sheet
    uv run python scripts/episode/storyboard.py <codex_id> <episode> --panel=19  # redraw ONE panel (PAID)

Per setup: the shots in cut order, spread evenly over 3x3 sheets; each sheet
is drawn from the plate, the setup's character sheets and the previous sheet
of the same scene; each panel is cropped and conformed to 768x1344 as
`frames/SNN.png`.  Spare cells are drawn as alternate angles so no cell is
black; they are not cropped out.  The prompt is written beside a sheet ONLY
when the sheet is drawn, so the record is the prompt that made it.  PAID
step (owner's go, 2026-09-10).  A sheet is reused only while the prompt that
made it is unchanged: `cached()` compares `asked(prompt, images)` against the
`<sheet>.prompt.txt` written beside it.  A path is not a cache key -- it names
WHERE the answer was put, never WHAT was asked -- and keying on it meant a
corrected prompt redrew nothing while every cell came back byte-identical.
"""
from __future__ import annotations

import base64
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio.episode_home import episode_arg
from studio import book_root
from studio import episode_board as board
from studio import episode_seq_board as sq
from studio import approval, canvas, episode_home, image_spend as spend
from studio.episode_spec import Episode
from studio.llm import _load_dotenv
from studio.trailer_refs import contract_description

W, H = canvas.size("9:16")
"""Rebound from the plan by `adopt()`: the plan declares the aspect."""
PEEK = 0.3


def adopt(aspect: str) -> tuple[int, int]:
    """Point `conform` at the plan's canvas.  One call, at the top of a run:
    a cell cropped to the wrong shape is silent until the master is cut."""
    global W, H
    W, H = canvas.size(aspect)
    return W, H


def strip_white_edges(image):
    """Cut the leaked sheet paper off every edge, as `episode_gutter.band` finds it.

    THIS OWNED ITS OWN IDEA OF PAPER -- WHITE=170, mean only, no flatness, no
    drop, a 6 % cap -- and it was the third such idea in the pipeline.  The
    other two were recalibrated for Part Two's pale skies on 2026-09-16 and
    this one was missed, so it went on trimming picture off any first frame
    whose edge is sky or sand: first frames that lost 30 px or more on an edge,
    ep04-07 0 / 0 / 0 / 1, ep08 11 of 30, ep09 10 of 30, every one to the cap,
    then re-squared by centre crop (-7 % on both axes, upscale 1.21-1.28x
    instead of 1.13x).  Q00_0 lost its snow peaks.

    Paper is bright AND flat AND has picture under it, and the guard already
    knows all three; one fact about paper, one function."""
    import numpy as np

    from studio import episode_gutter as gutter

    grey = np.asarray(image.convert("L"), dtype=float)
    return image.crop(gutter.box([grey]))


def conform(src: Path, dst: Path, box=None) -> Path:
    from PIL import Image

    image = Image.open(src).convert("RGB")
    if box:
        image = strip_white_edges(image.crop(box))
    scale = max(W / image.width, H / image.height)
    resized = image.resize((round(image.width * scale), round(image.height * scale)), Image.LANCZOS)
    left, top = (resized.width - W) // 2, (resized.height - H) // 2
    resized.crop((left, top, left + W, top + H)).save(dst)
    return dst


def physicals(book: Path) -> dict[str, str]:
    return {r["entity_id"]: contract_description(r.get("physical", ""))
            for r in episode_home.read_json(book / "refs" / "refs.json")["refs"]
            if r.get("kind") == "character"}


def book_of(path: Path) -> Path:
    """The book folder this drawing belongs to, FOUND and never counted to.

    This was `parents[3]` -- a hard-coded depth, correct for exactly one layout.
    The hour the sheets moved into `boards/sheets/` it silently sent $0.91 of
    real spend to `episodes/spend.jsonl` instead of the book's own ledger, with
    nothing raised and nothing printed."""
    return book_root.of(path)


def asked(prompt: str, images: list[Path]) -> str:
    """The whole question: the words, and the pictures they were said over.

    The references are half the instruction -- the same prompt over a different
    wardrobe card draws a different sheet -- and their ORDER is the other half,
    because `shift_indices` numbers the panels against it."""
    refs = "\n".join(p.name for p in images)
    return f"{prompt}\n\nreferences, in order:\n{refs}\n"


def remember(out: Path, prompt: str, images: list[Path]) -> Path:
    """Write the question beside the answer.  `draw` has always done this; now
    the cache reads it."""
    record = out.with_suffix(".prompt.txt")
    record.write_text(asked(prompt, images), encoding="utf-8")
    return record


def cached(out: Path, prompt: str, images: list[Path]) -> bool:
    """May this sheet be reused?

    IT USED TO BE `out.exists()`, which is not a cache key: a path names WHERE
    the answer was put, never WHAT was asked.  So `seq_boards --setup=
    landing_arrest` returned in seconds against a changed END-panel prompt, the
    sheet kept its two-hour-old timestamp, and every cell cut from it came back
    byte-identical -- indistinguishable, from outside, from a fix that was
    genuinely a no-op.  Both happened, in that order, to the same fix.

    A sheet drawn before the record existed is KEPT.  Six published episodes
    have sheets with no prompt file beside them, and re-spending on all of them
    to learn nothing is not a cache miss worth having."""
    if not out.exists():
        return False
    record = out.with_suffix(".prompt.txt")
    if not record.exists():
        return True
    return record.read_text(encoding="utf-8") == asked(prompt, images)


def draw(prompt: str, images: list[Path], out: Path, size: tuple[int, int] = board.CANVAS,
         approved: bool | None = None) -> Path:
    """One sheet from gpt-image, references attached in order.  Cached on its
    PROMPT -- see `cached`."""
    if cached(out, prompt, images):
        return out
    if approved is None:  # the caller did not decide, so the command line does
        approved = approval.approved_for("sheets", sys.argv)
    usd = {(2048, 3072): 0.20, (2048, 2048): 0.13, (1536, 1024): 0.08}.get(size, 0.20)
    approval.require("sheets", f"one {board.MODEL} sheet {out.stem} at {size[0]}x{size[1]}", usd, approved)
    _load_dotenv()
    from openai import OpenAI

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    handles = [open(p, "rb") for p in images]
    try:
        result = client.images.edit(model=board.MODEL, image=handles, prompt=prompt,
                                    size=f"{size[0]}x{size[1]}",
                                    quality="high", n=1)
    finally:
        for h in handles:
            h.close()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(base64.b64decode(result.data[0].b64_json))
    spend.record(book_of(out), board.MODEL, f"{size[0]}x{size[1]}", "high", 1, f"storyboard {out.stem}")
    remember(out, prompt, images)
    return out


def cells(sheet: Path) -> list[tuple[int, int, int, int]]:
    """The nine cell boxes as FOUND on the sheet (gutters detected), never thirds."""
    import numpy as np
    from PIL import Image

    return board.cell_boxes(np.asarray(Image.open(sheet).convert("L"), dtype=float))


def redrawn(boards: Path, shot) -> Path:
    return sq.panels_in(boards) / f"panel_S{shot.index:02d}_take{shot.take}.png"


def sheets(book: Path, episode: Episode, boards: Path) -> None:
    looks = physicals(book)
    for name, setup in episode.setups.items():
        refs = [sq.plates_in(boards) / f"plate_{name}.png"]
        refs += [book / "refs" / "characters" / f"char-{who}.png" for who in setup.cast]
        previous: Path | None = None
        for k, group in enumerate(board.chunks([s for s in episode.shots if s.setup == name])):
            text = board.prompt(group, setup.described, setup.cast, looks, previous is not None)
            sheet = draw(text, refs + ([previous] if previous else []),
                         boards / f"board_{name}_{k}.png")
            boxes = cells(sheet)
            for i, shot in enumerate(group):
                if redrawn(boards, shot).exists():
                    continue  # a panel redrawn alone outranks its sheet cell
                conform(sheet, boards / f"S{shot.index:02d}.png", boxes[i])
            print(f"  sheet {name} {k}: shots {[s.index for s in group]} -> {sheet}", flush=True)
            previous = sheet


PANEL_SIZE = (1024, 1536)


def sheet_of(episode: Episode, shot) -> int:
    """Which sheet of its setup the shot's panel was cut from."""
    groups = board.chunks([s for s in episode.shots if s.setup == shot.setup])
    return next(k for k, group in enumerate(groups) if shot in group)


def repanel(book_id: str, number: int, index: int) -> None:
    """Redraw ONE panel (PAID: one gpt-image call) from the plan's current
    `frame`, referenced to the plate, the cast and the sheet it came from.
    The old panel is kept beside it as `SNN.prev.png`; the take must be redone."""
    book = episode_home.book_dir(book_id)
    episode = episode_home.load_plan(book, number)
    boards = episode_home.boards_dir(book, number)
    shot, setup = episode.shot(index), episode.setups[episode.shot(index).setup]
    refs = [sq.plates_in(boards) / f"plate_{shot.setup}.png"]
    refs += [book / "refs" / "characters" / f"char-{who}.png" for who in setup.cast]
    refs.append(boards / f"board_{shot.setup}_{sheet_of(episode, shot)}.png")
    text = board.panel_prompt(shot, setup.described, setup.cast, physicals(book))
    drawn = draw(text, refs, sq.panels_in(boards) / f"panel_S{index:02d}_take{shot.take}.png", PANEL_SIZE)
    panel = boards / f"S{index:02d}.png"
    if panel.exists():
        panel.replace(panel.with_suffix(".prev.png"))
    conform(drawn, panel)
    print(f"  panel S{index:02d} redrawn -> {panel}", flush=True)


def grids(book_id: str, number: int) -> None:
    book = episode_home.book_dir(book_id)
    sheets(book, episode_home.load_plan(book, number), episode_home.boards_dir(book, number))


# ---- the review contact sheet, after the round -----------------------------

def still(take: Path, at: float, out: Path) -> Path:
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{at:.3f}", "-i", str(take),
                    "-frames:v", "1", "-vf", "scale=256:-2", str(out)], check=True)
    return out


def contact(rows: list[tuple[Path, ...]], out: Path) -> Path:
    """One row per shot: panel | take start | take end.  The END frame is where
    every drift of iterations 1-2 showed (a window appearing, a hand raised,
    a vessel gone red); the start frame alone passed them all."""
    from PIL import Image

    tiles = [tuple(Image.open(p).resize((256, 448)) for p in row) for row in rows]
    width = len(tiles[0]) if tiles else 3
    page = Image.new("RGB", (width * 268, len(tiles) * 452), "black")
    for i, row in enumerate(tiles):
        for j, tile in enumerate(row):
            page.paste(tile, (j * 268, i * 452))
    page.save(out)
    return out


def review(book_id: str, number: int) -> None:
    book = episode_home.book_dir(book_id)
    episode = episode_home.load_plan(book, number)
    home = episode_home.home(book, number)
    work = home / "work"
    work.mkdir(exist_ok=True)
    records = {r["index"]: r for r in
               episode_home.read_json(episode_home.takes_dir(book, number) / "shots.json")}
    rows = []
    for shot in episode.shots:
        if shot.index not in records:
            continue
        take = book / records[shot.index]["rel_path"]
        rows.append((sq.panels_in(home / "boards") / f"S{shot.index:02d}.png",
                     still(take, PEEK, work / f"take{shot.index:02d}.png"),
                     still(take, max(records[shot.index]["placed_seconds"] - 0.1, 0.0),
                           work / f"end{shot.index:02d}.png")))
    out = contact(rows, home / "review.png")
    print(f"{len(rows)} shots -> {out}", flush=True)


if __name__ == "__main__":
    panel = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--panel=")), "")
    number = episode_arg(sys.argv)
    if panel:
        repanel(sys.argv[1], number, int(panel))
    else:
        (review if "--review" in sys.argv else grids)(sys.argv[1], number)
