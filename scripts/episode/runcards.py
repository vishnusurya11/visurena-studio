#!/usr/bin/env python
"""One page per episode with every shot's INPUTS: the panel, the audio, the
settings and the full prompt -- so the owner can run any take by hand.

    uv run python scripts/episode/runcards.py <codex_id> <episode>

Writes `episodes/epNN/runcards.html` next to the panels it links.
"""
from __future__ import annotations

import html
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio import episode_home


def card(record: dict, line_text: str) -> str:
    audio = (f'<a href="lines/{record["audio"]}">{record["audio"]}</a>' if record.get("audio")
             else "none (silent take)")
    return (f'<section><h2>T{record["index"]:02d} · {record["section"]} · {record["lane"]}</h2>'
            f'<div class=row><figure><img src="frames/{record["start_image"]}">'
            f'<figcaption>{record["start_image"]} · 768x1344</figcaption></figure>'
            f'<div class=meta><table>'
            f'<tr><th>workflow</th><td>{record["workflow"]}</td></tr>'
            f'<tr><th>mode</th><td>{record["mode"]}</td></tr>'
            f'<tr><th>audio</th><td>{audio}</td></tr>'
            f'<tr><th>frames</th><td>{record["frames"]} @ 24 fps = {record["seconds"]} s '
            f'(placed {record["placed_seconds"]} s)</td></tr>'
            f'<tr><th>steps / seed</th><td>{record["steps"]} / {record["seed"]}</td></tr>'
            f'<tr><th>line</th><td>{html.escape(line_text) or "—"}</td></tr>'
            f'<tr><th>render</th><td>{record.get("render_s", "—")} s</td></tr></table>'
            f'<h3>prompt</h3><pre>{html.escape(record["prompt"])}</pre></div></div></section>')


def page(title: str, cards: list[str]) -> str:
    return ("<!doctype html><meta charset=utf-8><title>" + html.escape(title) + "</title>"
            "<style>body{font:14px system-ui;background:#111;color:#ddd;margin:20px;max-width:1400px}"
            "section{background:#1b1b1b;padding:14px;border-radius:8px;margin-bottom:18px}"
            ".row{display:grid;grid-template-columns:300px 1fr;gap:18px}figure{margin:0}img{width:100%}"
            "table{border-collapse:collapse}th{text-align:left;padding:2px 10px 2px 0;color:#9ab}"
            "pre{white-space:pre-wrap;background:#0d0d0d;padding:10px;border-radius:6px;font-size:12px}"
            "a{color:#8cf}</style>"
            f"<h1>{html.escape(title)}</h1>{''.join(cards)}")


def main(book_id: str, number: int) -> None:
    book = episode_home.book_dir(book_id)
    episode = episode_home.load_plan(book, number)
    home = episode_home.home(book, number)
    shots = {r["index"]: r for r in episode_home.read_json(home / "shots" / "shots.json")}
    cards = []
    for shot in episode.shots:
        record = shots.get(shot.index)
        if not record:
            continue
        spoken = " / ".join(f"{l.speaker}: {l.text}" for l in episode.lines_of(shot.index))
        cards.append(card(record, spoken))
    out = home / "runcards.html"
    out.write_text(page(f"{episode.title} — EP {number} run cards", cards), encoding="utf-8")
    print(f"{len(cards)} run cards -> {out}", flush=True)


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 1)
