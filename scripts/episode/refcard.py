#!/usr/bin/env python
"""The INPUTS page: every picture and every prompt that goes IN, before the GPU.

    uv run python scripts/episode/refcard.py <codex_id> <episode>

`runcards.py` answers "what came out and what went wrong". It can only show a
take's staged references AFTER the render, because it reads them from the
post-render record -- which is too late to check them. This page reads
`shots_r2v/prompts.json` and the sheet prompts on disk, so it answers "what goes
in" while the answer can still change something.

Two halves, and they are the two paid/slow stages in order:

  STORYBOARDS   per setup: the sheet as drawn, the full gpt-image prompt it was
                drawn from, and every cell cut out of it
  REF2V TAKES   per take: the staged reference pictures IN THEIR `<Picture N>`
                ORDER, the pins with their frames and seconds, the H3 settings,
                and the full MiniMax prompt

Relative links only, so the page moves with the folder.
"""
from __future__ import annotations

import html
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio import episode_home

CSS = """
*{box-sizing:border-box}
body{margin:0;background:#14140f;color:#e8e3d8;font:15px/1.6 Constantia,Georgia,serif}
header{padding:28px 32px 18px;border-bottom:1px solid #3a3630;background:#0f0f0b}
h1{margin:0 0 6px;font-size:26px;color:#c9a227;letter-spacing:.01em}
h2{margin:0 0 4px;font-size:19px;color:#e8e3d8}
.sub{color:#8c8578;font-size:14px}
nav{position:sticky;top:0;z-index:9;display:flex;flex-wrap:wrap;gap:2px;padding:8px 32px;
    background:#0f0f0bf2;border-bottom:1px solid #3a3630;backdrop-filter:blur(4px)}
nav a{color:#9a8f7d;text-decoration:none;font-size:12px;padding:3px 8px;border-radius:3px}
nav a:hover{background:#2a2620;color:#e8e3d8}
section{padding:26px 32px;border-bottom:1px solid #262620}
.row{display:flex;gap:22px;align-items:flex-start;flex-wrap:wrap}
.sheet img{max-width:540px;width:100%;border:1px solid #3a3630;border-radius:3px}
.cells{display:grid;grid-template-columns:repeat(auto-fill,minmax(132px,1fr));gap:10px;margin-top:14px}
.cell{background:#1c1c16;border:1px solid #2e2a24;border-radius:3px;padding:6px}
.cell img{width:100%;display:block;border-radius:2px}
.cell .n{font:11px ui-monospace,Consolas,monospace;color:#9a8f7d;margin-top:5px;word-break:break-all}
.pic{background:#1c1c16;border:1px solid #2e2a24;border-radius:3px;padding:6px;width:150px}
.pic img{width:100%;display:block;border-radius:2px}
.pic .n{font:11px ui-monospace,Consolas,monospace;color:#c9a227;margin-top:5px}
.pic .f{font:10px ui-monospace,Consolas,monospace;color:#8c8578;word-break:break-all}
pre{white-space:pre-wrap;background:#100f0b;border:1px solid #2e2a24;border-radius:3px;
    padding:14px 16px;font:12.5px/1.62 ui-monospace,Consolas,monospace;color:#cfc8b8;
    max-height:460px;overflow:auto;margin:10px 0 0}
table{border-collapse:collapse;font-size:13px;margin-top:6px}
td,th{border:1px solid #2e2a24;padding:4px 10px;text-align:left}
th{color:#9a8f7d;font-weight:normal;background:#1a1a14}
.tag{display:inline-block;background:#2a2620;color:#c9a227;border-radius:3px;
     padding:2px 8px;font-size:12px;margin-right:6px}
.miss{color:#e0794f}
h3{margin:20px 0 2px;font-size:15px;color:#9a8f7d;font-weight:normal;
   text-transform:uppercase;letter-spacing:.09em}
"""


def esc(text) -> str:
    return html.escape(str(text))


def sheet_used(frames: Path, setup: str, k: int = 0) -> Path | None:
    """The sheet the cells were actually cut from.

    A sheet that failed its gate is drawn a SECOND time with a strict prefix, and
    both files stay on disk. The cells come from the last attempt, so `_strict`
    wins wherever it exists."""
    strict = Path(frames) / f"seq_{setup}_{k}_strict.png"
    plain = Path(frames) / f"seq_{setup}_{k}.png"
    if strict.exists():
        return strict
    return plain if plain.exists() else None


def numbered(refs: list[str]) -> list[tuple[int, str]]:
    """`<Picture N>` IS the position in the staged list (spec 1.1)."""
    return list(enumerate(refs, start=1))


def href(name: str) -> str:
    """Where a staged reference lives, relative to the episode folder."""
    return f"../../refs/characters/{name}" if name.startswith("char-") else f"frames/{name}"


def anchor_rows(anchors: list, fps: int = 24) -> list[tuple[str, int, float]]:
    """Each pinned cell with the frame it is pinned at and that frame's second."""
    return [(name, int(frame), round(int(frame) / fps, 3)) for name, frame in anchors]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


# ---- the two halves ---------------------------------------------------------

def storyboard_section(frames: Path, setup: str, cells: list[str]) -> str:
    sheet = sheet_used(frames, setup)
    prompt = read(frames / f"{sheet.stem}.prompt.txt") if sheet else ""
    pic = (f'<div class="sheet"><img src="frames/{esc(sheet.name)}" alt="{esc(setup)}"></div>'
           if sheet else '<p class="miss">no sheet on disk</p>')
    grid = "".join(f'<div class="cell"><img src="frames/{esc(n)}"><div class="n">{esc(n)}</div></div>'
                   for n in cells)
    body = (f'<pre>{esc(prompt)}</pre>' if prompt
            else '<p class="miss">no prompt.txt beside this sheet</p>')
    return (f'<section id="sb-{esc(setup)}"><h2>{esc(setup)}</h2>'
            f'<p class="sub">{len(cells)} cells cut from '
            f'{esc(sheet.name) if sheet else "(none)"}</p>'
            f'<div class="row">{pic}<div style="flex:1;min-width:320px">'
            f'<h3>gpt-image sheet prompt</h3>{body}</div></div>'
            f'<h3>cells</h3><div class="cells">{grid}</div></section>')


def take_section(card: dict) -> str:
    refs = "".join(
        f'<div class="pic"><img src="{esc(href(n))}" alt="{esc(n)}">'
        f'<div class="n">&lt;Picture {k}&gt;</div><div class="f">{esc(n)}</div></div>'
        for k, n in numbered(card["refs"]))
    pins = "".join(f"<tr><td>{esc(n)}</td><td>{f}</td><td>{s:.3f}s</td></tr>"
                   for n, f, s in anchor_rows(card["anchors"], card.get("fps", 24)))
    audio = card["audio"]
    audio_txt = "silence" if audio == "silence" else ", ".join(f"{n} @ {a}s" for n, a in audio)
    facts = (f"<tr><th>shots</th><td>{esc(card['shots'])}</td>"
             f"<th>setup</th><td>{esc(card['setup'])}</td>"
             f"<th>lane</th><td>{esc(card['lane'])}</td></tr>"
             f"<tr><th>frames</th><td>{card['frames']} @ {card.get('fps',24)}fps "
             f"= {card['seconds']}s</td>"
             f"<th>canvas</th><td>{card['width']}x{card['height']}</td>"
             f"<th>steps</th><td>{card['steps']}</td></tr>"
             f"<tr><th>seed</th><td>{card['seed']}</td>"
             f"<th>ref size</th><td>{esc(card['ref_image_size'])}</td>"
             f"<th>audio</th><td>{esc(audio_txt)}</td></tr>"
             f"<tr><th>model</th><td colspan=5>{esc(card['model'])}</td></tr>")
    return (f'<section id="t{card["index"]:02d}"><h2>T{card["index"]:02d} '
            f'<span class="tag">{len(card["refs"])} references</span>'
            f'<span class="tag">{len(card["anchors"])} pins</span></h2>'
            f'<table>{facts}</table>'
            f'<h3>staged references, in &lt;Picture N&gt; order</h3>'
            f'<div class="row">{refs}</div>'
            f'<h3>pins</h3><table><tr><th>cell</th><th>frame</th><th>time</th></tr>{pins}</table>'
            f'<h3>MiniMax-H3 ref2v prompt</h3><pre>{esc(card["prompt"])}</pre></section>')


def build(book: Path, number: int) -> Path:
    home, frames = episode_home.home(book, number), episode_home.frames_dir(book, number)
    episode = episode_home.load_plan(book, number)
    cards = json.loads((home / "shots_r2v" / "prompts.json").read_text(encoding="utf-8"))
    cards = cards["takes"] if isinstance(cards, dict) else cards

    by_setup: dict[str, list[str]] = {}
    for p in sorted(frames.glob("Q*.png")):
        if ".before" in p.name or ".cells" in p.name:
            continue
        shot = int(p.stem[1:3])
        by_setup.setdefault(episode.shot(shot).setup, []).append(p.name)

    head = (f'<header><h1>{esc(episode.title)} — episode {number}: the inputs</h1>'
            f'<p class="sub">{len(episode.shots)} shots &middot; {len(cards)} takes &middot; '
            f'{sum(c["frames"] for c in cards)} frames &middot; aspect {esc(episode.aspect)} '
            f'&middot; {esc(episode.question)}</p></header>')
    nav = ("<nav>" + "".join(f'<a href="#sb-{esc(s)}">{esc(s)}</a>' for s in by_setup)
           + "".join(f'<a href="#t{c["index"]:02d}">T{c["index"]:02d}</a>' for c in cards) + "</nav>")
    body = "".join(storyboard_section(frames, s, cells) for s, cells in by_setup.items())
    body += "".join(take_section(c) for c in cards)
    out = home / "refcard.html"
    out.write_text(f"<!doctype html><meta charset=utf-8><title>{esc(episode.title)} ep{number} inputs"
                   f"</title><style>{CSS}</style>{head}{nav}{body}", encoding="utf-8")
    return out


def main(book_id: str, number: int) -> None:
    out = build(episode_home.book_dir(book_id), number)
    print(f"inputs page -> {out}")


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 1)
