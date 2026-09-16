#!/usr/bin/env python
"""ONE PAGE holding everything that went into an episode and everything that came out.

    uv run python scripts/episode/dossier.py <codex_id> <episode>

Written because the owner asked to see episode 8 whole: "give me the html file
with all inputs and prompts and outputs".  Reviewing a 164-second film by
reading nine JSON files and opening 46 PNGs in a viewer is not reviewing it, and
every fault this pipeline has shipped was visible in an artefact somebody could
have looked at.

The page is written INTO the episode folder so every `src` is a short relative
path: nothing is copied, nothing is embedded, and the pictures and the video are
the real ones off disk at full resolution.  Open it in a browser from there.

What it shows, in the order the pipeline makes it:

    the plan          title, question, palette, aspect, the shape
    the lines         every line, its speaker, its measured seconds, its wav
    the setups        the authored prose and the drawn plate
    the sheets        the FULL prompt sent to gpt-image, and the sheet it drew
    the shots         the authored prose, the cells cut for it, the take card's
                      whole prompt, the rendered take, and its DQ verdict
    the bed           the tone spans and the tone files
    the cut           the master, and the QC verdict

Free.  Reads only; writes one .html.
"""
from __future__ import annotations

import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from studio import episode_home

CSS = """
:root{--ink:#1a1a1a;--dim:#6b6b6b;--line:#dcd8d0;--paper:#faf8f5;--warn:#a8321e;--ok:#2f6b3a}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);
     font:15px/1.55 "Iowan Old Style",Georgia,serif;padding:0 0 6rem}
header{background:#22201d;color:#f2efe9;padding:2rem 1.5rem 1.6rem}
header h1{margin:0 0 .3rem;font-size:1.7rem;letter-spacing:.01em}
header .sub{color:#b9b2a6;font-size:.95rem}
.num{display:flex;flex-wrap:wrap;gap:.4rem 1.6rem;margin-top:1rem;font-size:.9rem;color:#d8d2c6}
.num b{color:#fff;font-weight:600}
main{max-width:1180px;margin:0 auto;padding:0 1.2rem}
h2{margin:2.6rem 0 .2rem;font-size:1.25rem;border-bottom:2px solid var(--ink);padding-bottom:.3rem}
h2 small{font-weight:400;color:var(--dim);font-size:.8rem;margin-left:.5rem}
h3{margin:1.8rem 0 .5rem;font-size:1.02rem}
.card{border:1px solid var(--line);background:#fff;border-radius:3px;padding:1rem 1.1rem;margin:.9rem 0}
.row{display:flex;gap:1.1rem;flex-wrap:wrap}
.row>.pic{flex:0 0 300px}
.row>.txt{flex:1 1 380px;min-width:280px}
img,video{max-width:100%;display:block;border:1px solid var(--line);background:#eee}
.cells{display:flex;gap:.5rem;flex-wrap:wrap;margin:.5rem 0}
.cells figure{margin:0;width:150px}
.cells figcaption{font:11px ui-monospace,Menlo,Consolas,monospace;color:var(--dim);padding-top:.2rem}
dl{margin:.4rem 0}
dt{font:11px ui-monospace,Menlo,Consolas,monospace;color:var(--dim);
   text-transform:uppercase;letter-spacing:.06em;margin-top:.55rem}
dd{margin:.1rem 0 0}
pre{white-space:pre-wrap;word-break:break-word;background:#f4f1eb;border:1px solid var(--line);
    border-radius:3px;padding:.7rem .8rem;font:12px/1.5 ui-monospace,Menlo,Consolas,monospace;
    margin:.4rem 0;max-height:26rem;overflow:auto}
details>summary{cursor:pointer;font:12px ui-monospace,Menlo,Consolas,monospace;color:#3a5a8c;
                padding:.25rem 0;user-select:none}
table{border-collapse:collapse;width:100%;font-size:.88rem;margin:.5rem 0}
th,td{border-bottom:1px solid var(--line);padding:.32rem .5rem;text-align:left;vertical-align:top}
th{font:11px ui-monospace,Menlo,Consolas,monospace;text-transform:uppercase;
   letter-spacing:.06em;color:var(--dim)}
td.n{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.tag{display:inline-block;font:11px ui-monospace,Menlo,Consolas,monospace;
     border:1px solid var(--line);border-radius:2px;padding:.05rem .4rem;margin-right:.3rem;color:var(--dim)}
.bad{color:var(--warn);font-weight:600}
.good{color:var(--ok)}
.said{font-style:italic}
@media (max-width:640px){.row>.pic{flex:1 1 100%}.cells figure{width:calc(50% - .25rem)}}
"""


def esc(text) -> str:
    return html.escape(str(text if text is not None else ""))


def rel(path: Path, home: Path) -> str:
    return path.relative_to(home).as_posix()


def read(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def field(name: str, value) -> str:
    """One authored field, shown only when the plan actually wrote it."""
    return f"<dt>{esc(name)}</dt><dd>{esc(value)}</dd>" if value else ""


def head(plan: dict, qc: dict | None, takes: list[dict], home: Path) -> str:
    scores = [t["score"] for t in takes]
    passed = sum(1 for t in takes if t.get("passed"))
    bits = [f"<b>{len(plan['shots'])}</b> shots", f"<b>{len(plan['lines'])}</b> lines",
            f"<b>{len(plan['setups'])}</b> setups"]
    if scores:
        bits += [f"takes <b>{passed}/{len(scores)}</b>",
                 f"mean DQ <b>{sum(scores) / len(scores):.2f}</b>",
                 f"worst <b>{min(scores):.1f}</b>"]
    if qc:
        bits += [f"<b>{qc.get('seconds')}</b>s", f"<b>{qc.get('lufs')}</b> LUFS",
                 f"<b>{qc.get('true_peak')}</b> dBTP",
                 ("QC <b class=good>PASS</b>" if qc.get("passed") else "QC <b class=bad>FAIL</b>"),
                 f"sha8 <b>{qc.get('sha8')}</b>"]
    return (f"<header><h1>{esc(plan.get('title'))}</h1>"
            f"<div class=sub>Episode {plan.get('number')} &middot; {esc(home.name)} &middot; "
            f"aspect {esc(plan.get('aspect'))}</div>"
            f"<div class=num>{' '.join(bits)}</div></header>")


def the_plan(plan: dict) -> str:
    out = ["<h2>The plan <small>what the episode was asked to be</small></h2>",
           "<div class=card><dl>",
           field("question", plan.get("question")),
           field("protagonist", plan.get("protagonist")),
           field("palette", plan.get("palette") or "(the book's own)"),
           "</dl></div>"]
    return "".join(out)


def the_lines(plan: dict, said: dict, home: Path) -> str:
    """Every line with its measured length and its wav."""
    heard = {}
    rows = said if isinstance(said, list) else (said or {}).get("lines", [])
    for row in rows:
        heard[row.get("index")] = row
    out = ["<h2>The lines <small>audio first: the picture is cut to these</small></h2>",
           "<table><tr><th>#</th><th>kind</th><th>speaker</th><th>shot</th>"
           "<th>secs</th><th>text</th><th>wav</th></tr>"]
    for line in plan["lines"]:
        met = heard.get(line["index"], {})
        wav = home / "audio" / "lines" / f"l{line['index']:02d}.wav"
        player = (f"<audio controls preload=none style='height:28px' "
                  f"src='{rel(wav, home)}'></audio>") if wav.exists() else ""
        secs = met.get("seconds")
        out.append(
            f"<tr><td class=n>{line['index']}</td><td>{esc(line['kind'])}</td>"
            f"<td>{esc(line['speaker'])}</td><td class=n>{line['shot']}</td>"
            f"<td class=n>{f'{secs:.2f}' if isinstance(secs, (int, float)) else ''}</td>"
            f"<td class=said>{esc(line['text'])}</td><td>{player}</td></tr>")
    out.append("</table>")
    return "".join(out)


def the_setups(plan: dict, home: Path) -> str:
    out = ["<h2>The setups <small>the authored place, and the plate drawn from it</small></h2>"]
    for name, setup in plan["setups"].items():
        plate = home / "boards" / "plates" / f"plate_{name}.png"
        pic = f"<img src='{rel(plate, home)}' alt='plate {esc(name)}'>" if plate.exists() else \
              "<p class=bad>no plate on disk</p>"
        out.append(
            f"<h3>{esc(name)}</h3><div class='card row'>"
            f"<div class=pic>{pic}</div><div class=txt><dl>"
            + field("described", setup.get("described"))
            + field("geometry", setup.get("geometry"))
            + field("cast", ", ".join(setup.get("cast") or []) or "(nobody)")
            + field("landmark", f"{setup.get('landmark')} — {setup.get('landmark_size')} "
                                f"({setup.get('landmark_at')})")
            + field("route", setup.get("route"))
            + field("crowd", setup.get("crowd"))
            + field("outdoors", setup.get("outdoors"))
            + "</dl></div></div>")
    return "".join(out)


def the_sheets(home: Path) -> str:
    """Every paid draw: the whole prompt, and the sheet it produced."""
    room = home / "boards" / "sheets"
    out = ["<h2>The storyboard sheets <small>the prompt sent to gpt-image, and what came "
           "back &mdash; this is the paid step</small></h2>"]
    for sheet in sorted(room.glob("seq_*.png")):
        prompt = sheet.with_suffix(".prompt.txt")
        said = prompt.read_text(encoding="utf-8") if prompt.exists() else "(no prompt recorded)"
        out.append(
            f"<h3>{esc(sheet.name)}</h3><div class=card>"
            f"<img src='{rel(sheet, home)}' alt='{esc(sheet.name)}'>"
            f"<details><summary>the prompt, in full ({len(said.split())} words)</summary>"
            f"<pre>{esc(said)}</pre></details></div>")
    return "".join(out)


def verdict(dq: dict | None) -> str:
    if not dq:
        return "<p class=dim>no DQ record</p>"
    mark = "good" if dq.get("passed") else "bad"
    rows = []
    for gate in dq.get("gates", []):
        how = "" if gate["ok"] else (" class=bad" if gate.get("hard") else "")
        rows.append(f"<tr><td>{esc(gate['name'])}</td><td{how}>{esc(gate['note'])}</td>"
                    f"<td class=n>{gate.get('penalty', 0) or ''}</td></tr>")
    return (f"<p><span class={mark}>{'PASS' if dq.get('passed') else 'FAIL'} "
            f"{dq.get('score')}/100</span></p>"
            f"<table><tr><th>gate</th><th>measured</th><th>penalty</th></tr>"
            + "".join(rows) + "</table>")


def the_shots(plan: dict, placed: dict, cards: list[dict], home: Path) -> str:
    """Each shot: its prose, its cells, its take card, its render, its verdict."""
    when = {s["index"]: s for s in (placed or {}).get("shots", [])}
    card_for, dq_for = {}, {}
    for card in cards:
        for shot in card.get("shots", []):
            card_for[shot] = card
    for path in sorted((home / "takes" / "r2v").glob("T*.dq.json")):
        got = read(path)
        if got:
            dq_for[got["take"]] = got
    out = ["<h2>The shots <small>authored prose &rarr; drawn cells &rarr; the take card's "
           "prompt &rarr; the render &rarr; the verdict</small></h2>"]
    for shot in plan["shots"]:
        k = shot["index"]
        at = when.get(k, {})
        card = card_for.get(k)
        cells = sorted((home / "boards" / "cells").glob(f"Q{k:02d}_*.png"))
        figs = "".join(
            f"<figure><img src='{rel(c, home)}' alt='{esc(c.name)}'>"
            f"<figcaption>{esc(c.name)}</figcaption></figure>" for c in cells)
        take = home / "takes" / "r2v" / f"T{card['index']:02d}.mp4" if card else None
        player = (f"<video controls preload=metadata src='{rel(take, home)}'></video>"
                  if take and take.exists() else "<p class=bad>no take on disk</p>")
        spoken = [l for l in plan["lines"] if l["shot"] == k]
        heading = (f"<h3>Shot {k} <span class=tag>{esc(shot['section'])}</span>"
                   f"<span class=tag>{esc(shot['setup'])}</span>"
                   f"<span class=tag>{esc(shot['size'])}</span>"
                   + (f"<span class=tag>{at['t_start']:.2f}&ndash;{at['t_end']:.2f}s</span>"
                      if at else "")
                   + (f"<span class=tag>take T{card['index']:02d}</span>" if card else "")
                   + "</h3>")
        out.append(
            heading + "<div class=card>"
            + (f"<div class=cells>{figs}</div>" if figs else "<p class=bad>no cells on disk</p>")
            + "<div class=row><div class=txt><dl>"
            + field("frame", shot.get("frame"))
            + field("motion", shot.get("motion"))
            + field("camera", shot.get("camera"))
            + field("at rest", shot.get("at_rest"))
            + field("turn", shot.get("turn"))
            + field("faces", ", ".join(shot.get("faces") or []))
            + field("beat / coda", f"{shot.get('beat_s', 0)}s / {shot.get('coda_s', 0)}s")
            + "".join(f"<dt>line {l['index']} ({l['kind']})</dt>"
                      f"<dd class=said>{esc(l['text'])}</dd>" for l in spoken)
            + "</dl></div><div class=pic>" + player
            + (verdict(dq_for.get(card["index"])) if card else "") + "</div></div>"
            + (f"<details><summary>the take card's prompt, in full "
               f"({len(card.get('prompt', '').split())} words) &mdash; refs: "
               f"{esc(', '.join(card.get('refs', [])))}</summary>"
               f"<pre>{esc(card.get('prompt', ''))}</pre></details>" if card else "")
            + "</div>")
    return "".join(out)


def the_bed(plan: dict, home: Path) -> str:
    out = ["<h2>The music bed <small>one tone per span, chosen against the scene</small></h2>",
           "<table><tr><th>from shot</th><th>tone</th><th>file</th></tr>"]
    for span in plan.get("beds", []):
        wav = home / "audio" / f"bed_{span['tone']}.wav"
        player = (f"<audio controls preload=none style='height:28px' "
                  f"src='{rel(wav, home)}'></audio>") if wav.exists() else "(not on disk)"
        out.append(f"<tr><td class=n>{span['from_shot']}</td><td>{esc(span['tone'])}</td>"
                   f"<td>{player}</td></tr>")
    out.append("</table>")
    whole = home / "audio" / "bed.wav"
    if whole.exists():
        out.append(f"<div class=card><dt>the composed bed</dt>"
                   f"<audio controls preload=none src='{rel(whole, home)}'></audio></div>")
    return "".join(out)


def the_cut(qc: dict | None, home: Path) -> str:
    master = home / "cut" / "master_r2v.mp4"
    out = ["<h2>The cut <small>what shipped</small></h2><div class=card>"]
    if master.exists():
        out.append(f"<video controls preload=metadata src='{rel(master, home)}'></video>")
    if qc:
        keep = ("seconds", "planned_seconds", "lufs", "true_peak", "lines", "speech_s",
                "longest_gap_s", "missing_cuts", "internal_cuts", "title_card", "sha8", "passed")
        out.append("<table><tr><th>measure</th><th>value</th></tr>" + "".join(
            f"<tr><td>{esc(k)}</td><td>{esc(qc.get(k))}</td></tr>" for k in keep if k in qc)
            + "</table>")
    out.append("</div>")
    return "".join(out)


def build(book_id: str, number: int) -> Path:
    book = episode_home.book_dir(book_id)
    home = episode_home.home(book, number)
    plan = read(home / "plan.json")
    if plan is None:
        raise SystemExit(f"no plan at {home / 'plan.json'}")
    placed = read(home / "placed.json") or {}
    qc = read(home / "qc_r2v.json")
    said = read(home / "audio" / "lines" / "lines.json") or []
    cards = read(home / "takes" / "r2v" / "prompts.json") or []
    cards = cards if isinstance(cards, list) else cards.get("cards", [])
    takes = [t for t in (read(p) for p in sorted((home / "takes" / "r2v").glob("T*.dq.json"))) if t]

    page = (f"<!doctype html><meta charset=utf-8>"
            f"<meta name=viewport content='width=device-width,initial-scale=1'>"
            f"<title>Episode {number} — {esc(plan.get('title'))} — dossier</title>"
            f"<style>{CSS}</style>"
            + head(plan, qc, takes, home)
            + "<main>"
            + the_plan(plan) + the_lines(plan, said, home) + the_setups(plan, home)
            + the_sheets(home) + the_shots(plan, placed, cards, home)
            + the_bed(plan, home) + the_cut(qc, home)
            + "</main>")
    out = home / f"ep{number:02d}_dossier.html"
    out.write_text(page, encoding="utf-8")
    return out


if __name__ == "__main__":
    print(build(sys.argv[1], int(sys.argv[2])))
