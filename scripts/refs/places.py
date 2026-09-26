#!/usr/bin/env python
"""Each setup's place picture, at this episode's hour, from the plan. Local, $0.

    uv run python scripts/refs/places.py <book_id> <episode>                 # report
    uv run python scripts/refs/places.py <book_id> <episode> --draw          # draw what is missing
    uv run python scripts/refs/places.py <book_id> <episode> --new=<loc>="Its name" ...

For every setup with a `location`, the picture its `view` names must exist
under refs/locations/<location>/. `--draw` draws each missing one with Krea2
from the setup's own `described` words and logs it to refs/pack.jsonl.
The hour comes from the picture, never from the words, so a place at a new
hour is a new picture.

Promoted from three ep09 session scripts (audit 2026-09-22). The typed lists
of what to draw are gone -- the plan's setups ARE the list -- and so is the
step that rewrote the book's location rows to point at ep09's pictures. That
moved every earlier episode's Horsell Common into daylight. A setup's `view`
is the choice; an existing row is never touched. A place new to the book gets
a row only with the name given on the command line, because that name is
what the take's style line says.

**Look at every picture this draws before building on it.** Put the defining
state first in `described`: the lawn's fire sat about 55 words in and was not
drawn.
"""
from __future__ import annotations

import json
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio import episode_home
from studio.episode_home import episode_arg

ANCHOR = "wide_establishing"


def picture(book: Path, location: str, view: str) -> Path:
    return Path(book) / "refs" / "locations" / location / f"{view or ANCHOR}.png"


def status(book: Path, setups: dict) -> list[tuple[str, str, str, str]]:
    """(setup, location, view, "have" | "missing") for every setup with a place."""
    out = []
    for name, s in setups.items():
        if getattr(s, "location", ""):
            view = s.view or ANCHOR
            out.append((name, s.location, view, "have" if picture(book, s.location, view).exists() else "missing"))
    return out


def ensure_rows(book: Path, setups: dict, names: dict[str, str], number: int) -> list[str]:
    """Write a row for a place new to the book -- only with its given name --
    and NEVER touch a row that exists. Returns the rows written."""
    folder = Path(book) / "analysis" / "locations"
    wrote = []
    for s in setups.values():
        loc = getattr(s, "location", "")
        if not loc or (folder / f"{loc}.json").exists() or loc in wrote:
            continue
        if loc not in names:
            raise SystemExit(f"{loc} has no row in analysis/locations; give it a name: --new={loc}=\"...\"")
        row = {"id": loc, "name": names[loc], "aliases": [], "region": "other", "scenes": [],
               "visitors": [], "state_changes": [], "first_appearance": number,
               "profile": {"summary": s.described,
                           "design": {"views": [{"id": s.view or ANCHOR, "prompt": s.described}]}}}
        (folder / f"{loc}.json").write_text(json.dumps(row, indent=1, ensure_ascii=False), encoding="utf-8")
        wrote.append(loc)
    return wrote


LOOK = ("Rendered in exactly the same look as the characters that will stand in it: {look}, "
        "broad simplified 3D shapes, flat high-chroma colour, clean edges -- a frame from a stylised "
        "3D animated film, not a painting and not a photograph.")
"""Root cause 2026-09-26 (D13): with no style words the house model drew places
painterly while it drew the cast as stylised 3D figures, and the storyboard takes
its style from the place picture -- people pasted onto paintings from ep09 on."""


def styled(described: str, look: str) -> str:
    """The setup's words, then the book's look when it declares one."""
    return f"{described} {LOOK.format(look=look.strip().rstrip('.'))}" if look.strip() else described


def draw_missing(book: Path, setups: dict, draw, look: str = "") -> list[Path]:
    """Draw every missing view with `draw(prompt, target)`, from its setup's words
    in the book's look."""
    made = []
    for name, loc, view, state in status(book, setups):
        if state == "missing" and picture(book, loc, view) not in made:
            target = picture(book, loc, view)
            draw(styled(setups[name].described, look), target)
            made.append(target)
    return made


def krea(book: Path):
    """The house drawer: Krea2 + the Cinematic_Artstyle LoRA, logged to pack.jsonl."""
    from studio.comfy import run
    from studio.refs_pack import T2I, Job, values_for

    def draw(prompt: str, target: Path) -> None:
        job = Job("locations", target.parent.name, target.stem, T2I, prompt, 1536, 1024)
        began = time.time()
        out = run(job.workflow, values_for(job))[0]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(out, target)
        with (Path(book) / "refs" / "pack.jsonl").open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"path": episode_home.relative(book, target), "workflow": job.workflow,
                                 "prompt": prompt, "seed": values_for(job)["seed"],
                                 "seconds": round(time.time() - began, 1)}, ensure_ascii=False) + "\n")
        print(f"  drew {episode_home.relative(book, target)}", flush=True)
    return draw


def main(book_id: str, number: int, drawing: bool, names: dict[str, str]) -> int:
    book = episode_home.book_dir(book_id)
    plan = episode_home.load_plan(book, number)
    setups = plan.setups
    for loc in ensure_rows(book, setups, names, number):
        print(f"  new row: {loc}")
    if drawing:
        draw_missing(book, setups, krea(book), look=plan.look)
    rows = status(book, setups)
    for name, loc, view, state in rows:
        print(f"  {state:8} {name:10} {loc}/{view}.png")
    return 1 if any(r[3] == "missing" for r in rows) else 0


if __name__ == "__main__":
    new = dict(a.split("=", 1)[1].split("=", 1) for a in sys.argv if a.startswith("--new="))
    names = {k: v.strip('"') for k, v in new.items()}
    raise SystemExit(main(sys.argv[1], episode_arg(sys.argv), "--draw" in sys.argv, names))
