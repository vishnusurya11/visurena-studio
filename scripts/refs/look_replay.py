#!/usr/bin/env python
"""The continuity slice's ACCEPTANCE replay (verdict S §6). GPU, local, $0 -- run
only in an owner-approved GPU window; it writes nothing a shipped episode reads.

    uv run python scripts/refs/look_replay.py <book_id> <episode> <setup> <cols> <rows> [--shots=1,2]

For one shipped grid: draw each staged person's chapter LOOK one hop from the
base sheet (LOOK-STATE judged, the capped ladder), redraw the grid with the
look pictures staged and the look's words, cut it into panels, and have the
local VLM list each panel's hair colour and facial hair -- the same ask for
the SHIPPED panels of those shots.  Everything lands under
library/<book>/bench/continuity_2026-10-10/ep<NN>_<setup>/; nothing under
refs/ or episodes/ is written, and the book gets no refs/looks.json.

Pass: the person shows the look's hair colour AND facial hair in >= 80 % of
the replayed panels he is in (WotW ep25/ep27 narrator: 0-1 of ~24 shipped).
Look at the contact sheet as well (`contact.png`): a list is not an eye.
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio import cast_refs, episode_home, look_timeline, look_table as lt  # noqa: E402
from studio.episode_home import episode_arg  # noqa: E402

BENCH = Path("bench") / "continuity_2026-10-10"
PASS_SHARE = 0.8


def bench_dir(book: Path, number: int, setup: str) -> Path:
    return Path(book) / BENCH / f"ep{number:02d}_{setup}"


def panel_boxes(width: int, height: int, cols: int, rows: int) -> list[tuple[int, int, int, int]]:
    """Equal cells, row by row, the order a grid's manifest lists its shots."""
    w, h = width // cols, height // rows
    return [(c * w, r * h, (c + 1) * w, (r + 1) * h) for r in range(rows) for c in range(cols)]


def shows_look(seen: dict, want) -> bool:
    """Does one panel's read show the look's hair colour family and facial hair?"""
    hair = not want.hair_colour or lt.family("hair_colour", seen.get("hair_colour", "")) == \
        lt.family("hair_colour", want.hair_colour)
    face = not want.facial_hair or seen.get("facial_hair", "") == want.facial_hair
    return hair and face


def tally(reads: list[dict], want) -> dict:
    """{'shown': n, 'of': m, 'share': n/m, 'passed': share >= PASS_SHARE}."""
    shown = sum(shows_look(r, want) for r in reads)
    share = shown / len(reads) if reads else 0.0
    return {"shown": shown, "of": len(reads), "share": round(share, 2), "passed": share >= PASS_SHARE}


def staged_looks(book: Path, table, ep, shots) -> dict[str, str]:
    """The chapter look of every person the grid's shots cast who is on the table."""
    who = list(dict.fromkeys(f for s in shots for f in (s.faces or [])))
    return {w: table.characters[w].look_id_at(ep.number) for w in who if w in table.characters}


def redirect(book: Path, home: Path, table, looks: dict[str, str]) -> None:
    """Point the look machinery at the bench (pictures) and the replay's table
    (words), so the real prompt builder stages the looks without touching refs/."""
    from scripts.refs import looks as looks_step
    from studio import continuity, pack_refs
    looks_step.look_path = lambda b, who, look: home / "looks" / who / f"{look}.png"
    pack_refs.look_sheet = lambda b, who, look: home / "looks" / who / f"{look}.png" \
        if look and look != table.characters[who].base else pack_refs.character_sheet(b, who)
    continuity.look_for = lambda setup, who, row: looks.get(who, (row or {}).get("look", ""))
    continuity.words_for = lambda b, who, look, row: look_timeline.look_words(table.characters[who], look) \
        if who in table.characters and look else (row or {}).get("physical", "")


def draw_looks(book: Path, home: Path, table, looks: dict[str, str]) -> dict:
    """Each non-base look drawn one hop from the base and judged; its verdict."""
    from scripts.refs import looks as looks_step
    out = {}
    for who, look in looks.items():
        card = table.characters[who]
        if look == card.base:
            continue
        (home / "looks" / who).mkdir(parents=True, exist_ok=True)
        seed, verdict = looks_step.climb(book, who, look, card, looks_step.comfy_draws(book),
                                         looks_step.vlm_judge(book))
        out[f"{who}/{look}"] = {"seed": seed, **verdict.model_dump(mode="json")}
    return out


def render_grid(book: Path, home: Path, ep, setup: str, shots, cols: int, rows: int) -> Path:
    from scripts.episode import grids
    from studio.comfy import submit, wait
    text, slots = grids.prompt_for(book, ep, setup, shots, cols, rows)
    seed = 40500 + sum(s.index for s in shots)
    made = wait(submit(grids.graph_for(text, slots, cols, rows, seed, f"bench_look_{setup}")), timeout=3600)
    (home / "prompt.txt").write_text(text, encoding="utf-8")
    return Path(shutil.copyfile(made[0], home / "grid.png"))


def read_panels(paths: list[Path]) -> list[dict]:
    from studio import look_back
    from studio.judges import look_state
    out = []
    for path in paths:
        try:
            out.append(look_state.parse(look_back.vlm_reader(path, look_state.ASK)))
        except Exception as why:        # an unread panel counts as not showing the look
            out.append({"unread": str(why)[:80]})
    return out


def cut(grid: Path, cols: int, rows: int, home: Path) -> list[Path]:
    from PIL import Image
    im = Image.open(grid)
    out = []
    for k, box in enumerate(panel_boxes(im.width, im.height, cols, rows)):
        out.append(home / f"panel_{k}.png")
        im.crop(box).save(out[-1])
    return out


def main(book_id: str, number: int, setup: str, cols: int, rows: int, only: list[int] | None) -> int:
    from scripts.episode import grids
    from scripts.refs.continuity_replay import table_of
    book = episode_home.book_dir(book_id)
    ep = episode_home.load_plan(book, number)
    shots = grids.grid_shots(ep, setup, cols, rows, only)
    table, home = table_of(book), bench_dir(book, number, setup)
    home.mkdir(parents=True, exist_ok=True)
    looks = staged_looks(book, table, ep, shots)
    redirect(book, home, table, looks)
    verdicts = draw_looks(book, home, table, looks)
    panels = cut(render_grid(book, home, ep, setup, shots, cols, rows), cols, rows, home)
    shipped = [episode_home.home(book, number) / "storyboard" / "h3" / f"shot_{s.index:02d}.png" for s in shots]
    now, then = read_panels(panels), read_panels([p for p in shipped if p.exists()])
    then = iter(then)
    then = [next(then) if p.exists() else {"unread": "no shipped panel"} for p in shipped]
    report = {"looks": looks, "look_verdicts": verdicts}
    for who, look in looks.items():
        mine = [i for i, s in enumerate(shots) if who in (s.faces or [])]
        want = table.characters[who].looks[look].markers
        report[who] = {"replayed": tally([now[i] for i in mine], want),
                       "shipped": tally([then[i] for i in mine], want)}
    (home / "report.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    print(json.dumps(report, indent=1))
    print(f"report: {home / 'report.json'}")
    return 0 if all(v["replayed"]["passed"] for k, v in report.items() if k in looks) else 1


if __name__ == "__main__":
    plain = [a for a in sys.argv[1:] if not a.startswith("--")]
    only = [int(v) for a in sys.argv if a.startswith("--shots=") for v in a.split("=", 1)[1].split(",") if v]
    raise SystemExit(main(plain[0], episode_arg(sys.argv), plain[2], int(plain[3]), int(plain[4]), only or None))
