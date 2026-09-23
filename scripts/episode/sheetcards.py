#!/usr/bin/env python
"""The storyboard sheets, for the owner to validate BEFORE anything is drawn.

    uv run python scripts/episode/sheetcards.py <codex_id> <episode>

One card per setup: the grid, the reference images the drawer is given, the
gate verdict, every panel's own text, and the whole prompt exactly as it is
sent.  Re-run after the draw and the same page carries the drawn sheet and
its cut cells beside each panel, so the words and the picture sit together.
Owner, 2026-09-11: "give them in html so i will validate, once i say, create
images and then add the images to html".
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import importlib.util as _iu

from studio.episode_home import episode_arg
from studio import episode_home, episode_seq_board as sq
from studio.episode_spec import Episode

def _sibling(name: str):
    spec = _iu.spec_from_file_location(name, Path(__file__).with_name(f"{name}.py"))
    module = _iu.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


rc = _sibling("runcards")
boards = _sibling("seq_boards")  # the drawer's own `physicals`, so the page shows what it will send

BLOCKS = ("SHEET", "DIFFERENT PICTURES", "ORDER", "REFERENCES", "LOCATION", "GEOMETRY",
          "WARDROBE", "BACKGROUND LIFE", "PANELS", "STYLE", "CONSTRAINTS")
COST = {(3, 1): 0.08, (3, 2): 0.13, (3, 3): 0.20}


def blocks_of(prompt: str) -> list[tuple[str, str]]:
    """The prompt split into its labelled blocks, in order, for reading."""
    out, name, body = [], "PROMPT", []
    for line in prompt.splitlines():
        if line.strip() in BLOCKS:
            if body:
                out.append((name, "\n".join(body).strip()))
            name, body = line.strip(), []
        else:
            body.append(line)
    out.append((name, "\n".join(body).strip()))
    return [(n, b) for n, b in out if b]


def references(book: Path, frames: Path, setup_name: str, setup) -> list[Path]:
    """The pictures the drawer is handed, in the order the prompt names them."""
    out = [frames / f"plate_{setup_name}.png"]
    out += [sq.cast_sheet(book, who, setup_name, setup.state) for who in setup.cast]
    return [p for p in out if p.exists()]


def panel_rows(book: Path, frames: Path, panels: list[dict]) -> str:
    """Every panel: its cell when drawn, its key, and the four texts that made it."""
    rows = []
    for k, seg in enumerate(panels, start=1):
        name = sq.named(seg)
        cell = frames / name
        shot = f"S{seg['shot']:02d}" + (f".{seg['sub']}" if seg["sub"] else "") + ("E" if seg.get("end") else "")
        picture = (f'<a href="{rc.rel(book, cell)}"><img src="{rc.rel(book, cell)}" style="width:150px"></a>'
                   if cell.exists() else '<span class=todo>not drawn yet</span>')
        texts = "".join(f"<p><b>{f}:</b> {rc.esc(seg[f])}</p>" for f in ("frame", "motion", "camera", "at_rest", "end", "changed")
                        if seg.get(f))
        rows.append(f"<tr><th>panel {k}<br>{rc.esc(shot)}<br><small>{rc.esc(name)}</small></th>"
                    f"<td>{picture}</td><td>{texts}</td></tr>")
    return f"<table class=panels>{''.join(rows)}</table>"


def verdict_of(frames: Path, setup_name: str) -> str:
    """The pre-spend gate's reading of this sheet, when it has run.

    HARD findings refuse the draw; WATCH findings are recorded and judged by eye,
    because they measure a heuristic (a noun that may be a prop, a wardrobe word
    that may be implied) rather than a fault the drawing cannot come back from.
    """
    path = frames / "sheet_dq.json"
    if not path.exists():
        return "<p class=todo>the sheet gate has not run yet</p>"
    report = episode_home.read_json(path)
    setup = next((s for s in report.get("setups", []) if s.get("setup") == setup_name), None)
    if not setup:
        return "<p class=todo>no verdict for this setup</p>"
    out = []
    for sheet in setup.get("sheets", []):
        v = sheet.get("verdict", {})
        head = "PASS" if v.get("passed") else "FAIL"
        counts = " · ".join(f"{k} {n}" for k, n in (v.get("checks") or {}).items())
        rows = "".join(f"<tr><td>{rc.esc(f.get('check', ''))}</td><td>{rc.esc(f.get('panel', ''))}</td>"
                       f"<td>{rc.esc(f.get('detail') or f.get('text', ''))[:300]}</td></tr>"
                       for f in sheet.get("findings", []))
        out.append(f"<p><b>{head}</b> · {v.get('hard', 0)} hard · {v.get('watch', 0)} to watch"
                   + (f" · {rc.esc(counts)}" if counts else "") + "</p>"
                   + (f"<table class=lines><tr><th>check</th><th>panel</th><th>what</th></tr>{rows}</table>" if rows else ""))
    return "".join(out)


def sheet_card(book: Path, frames: Path, name: str, setup, panels: list[dict], route: list[int],
               grid: tuple, prompt: str) -> str:
    cols, rows, canvas = grid
    drawn = frames / f"seq_{name}_0.png"
    picture = (f'<a href="{rc.rel(book, drawn)}"><img src="{rc.rel(book, drawn)}" style="width:100%"></a>'
               if drawn.exists() else '<p class=todo>sheet not drawn yet</p>')
    refs = rc.thumbs(book, references(book, frames, name, setup), "reference images, in the order the prompt names them")
    body = "".join(f"<details{' open' if n in ('DIFFERENT PICTURES', 'GEOMETRY', 'WARDROBE') else ''}>"
                   f"<summary>{rc.esc(n)}</summary><pre>{rc.esc(b)}</pre></details>" for n, b in blocks_of(prompt))
    return (f'<section id="{name}" class=card><h2>{rc.esc(name)} · {cols}x{rows} · {len(panels)} panels · '
            f"{canvas[0]}x{canvas[1]} · ${COST[(cols, rows)]:.2f}</h2>"
            f"<div class=cols3><div class=col><h3>The sheet</h3>{picture}"
            f"<h3>What the drawer is given</h3>{refs}"
            f"<h3>Gate</h3>{verdict_of(frames, name)}"
            f"<p><small>panels on the route: {route or 'none'} · {len(prompt.split())} words</small></p></div>"
            f"<div class=col><h3>Panels</h3>{panel_rows(book, frames, panels)}</div>"
            f"<div class=col><h3>The prompt, exactly as sent</h3>{body}</div></div></section>")


def main(book_id: str, number: int) -> None:
    book = episode_home.book_dir(book_id)
    episode: Episode = episode_home.load_plan(book, number)
    frames = episode_home.boards_dir(book, number)
    cards, total = [], 0.0
    for name, setup in episode.setups.items():
        for panels, route, grid in sq.sheets(sq.segments(episode.shots, name), aspect=episode.aspect):
            prompt = sq.prompt(panels, setup, boards.physicals(book), previous=False, first=True,
                               geography=route, aspect=episode.aspect)
            cards.append(sheet_card(book, frames, name, setup, panels, route, grid, prompt))
            total += COST[(grid[0], grid[1])]
    head = (f'<section id="top"><h2>{len(cards)} sheets to draw · ${total:.2f}</h2>'
            f"<p>Every panel, its words and the picture they will make. Click any image to open it beside the page. "
            f"Nothing is drawn until you say so.</p></section>")
    nav = '<a href="#top">total</a>' + "".join(f'<a href="#{n}">{n}</a>' for n in episode.setups)
    out = episode_home.home(book, number) / "sheets.html"
    out.write_text(rc.page(f"{episode.title} — EP {number} storyboard sheets to validate", nav, [head] + cards),
                   encoding="utf-8")
    print(f"{len(cards)} sheet cards, ${total:.2f} -> {out}")


if __name__ == "__main__":
    main(sys.argv[1], episode_arg(sys.argv))
