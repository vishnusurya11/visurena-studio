#!/usr/bin/env python
"""The take prompts, for the owner to validate BEFORE any GPU time.

    uv run python scripts/episode/takecards.py <codex_id> <episode>

One card per take: the references in slot order with what each one IS, every
pinned cell with its frame and time, the audio the take is given, the engine
values it will run on, the lint's verdict, and the whole prompt in its own
sections.  Re-run after the render and the same page carries the take beside
the words that made it.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import importlib.util as _iu

from studio import episode_home, episode_ref_official as ro

SECTIONS = ("subject_definitions:", "summary:", "retention_analysis:", "detailed_description:",
            "overall_soundscape:", "non_diegetic_music:")


def _sibling(name: str):
    spec = _iu.spec_from_file_location(name, Path(__file__).with_name(f"{name}.py"))
    module = _iu.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


rc = _sibling("runcards")
takes = _sibling("takes_r2v")


def sections_of(prompt: str) -> list[tuple[str, str]]:
    """The prompt split at its own section headings, in order."""
    marks = [(prompt.index(s), s) for s in SECTIONS if s in prompt]
    marks.sort()
    out = []
    for k, (at, name) in enumerate(marks):
        end = marks[k + 1][0] if k + 1 < len(marks) else len(prompt)
        out.append((name.rstrip(":"), prompt[at + len(name):end].strip()))
    return out


def slots(record: dict) -> list[dict]:
    """What each <Picture N> is, in the order the builder stages them: a cast sheet
    for every face the take shows, then the location plate, then ONE picture per
    pinned cell (the first frame of its shot), then the take's own strip."""
    faces, refs, out = record.get("faces") or [], record.get("refs") or [], []
    shot_of = {name: k for k, (name, _) in enumerate(sorted(record.get("anchors") or [], key=lambda a: a[1]), start=1)}
    for k, name in enumerate(refs, start=1):
        if k <= len(faces):
            role, subject = f"cast sheet of {faces[k - 1].replace('_', ' ').title()}", f"<Subject {k}>"
        elif name.startswith("plate_"):
            role, subject = "the location plate, which defines the room", f"<Subject {k}>"
        elif name.startswith("ref_take_"):
            role, subject = "the take's own storyboard strip, its cells side by side in time order", "storyboard reference"
        else:
            j = shot_of.get(name)
            role = f"the first frame of [Shot {j}]" if j else "a pinned storyboard cell"
            subject = "keyframe"
        out.append({"picture": f"<Picture {k}>", "file": name, "role": role, "subject": subject})
    return out


def inputs_table(book: Path, frames: Path, record: dict) -> str:
    rows = []
    for s in slots(record):
        path = frames / s["file"] if (frames / s["file"]).exists() else book / "refs" / "characters" / s["file"]
        rows.append(f'<tr><th>{rc.esc(s["picture"])}</th>'
                    f'<td><a href="{rc.rel(book, path)}"><img class=thumb src="{rc.rel(book, path)}"></a></td>'
                    f'<td><b>{rc.esc(s["subject"])}</b><br>{rc.esc(s["role"])}<br><small>{rc.esc(s["file"])}</small></td></tr>')
    audio = record.get("audio")
    if isinstance(audio, list) and audio:
        said = "<b>&lt;Audio 1&gt;</b> = " + " + ".join(f'<a href="lines/{rc.esc(n)}">{rc.esc(n)}</a> at {at} s' for n, at in audio)
    else:
        said = "<b>&lt;Audio 1&gt;</b> = silence; this take carries no voice, and the narration is laid on the master"
    pins = "".join(f'<figure><a href="{rc.rel(book, frames / n)}"><img src="{rc.rel(book, frames / n)}"></a>'
                   f"<figcaption>{rc.esc(n)}<br>frame {f} ({f / 24:.2f} s)</figcaption></figure>"
                   for n, f in sorted(record.get("anchors") or [], key=lambda a: a[1]))
    return (f"<table class=inputs>{''.join(rows)}"
            f"<tr><th>audio</th><td colspan=2>{said}</td></tr>"
            f"<tr><th>pinned cells</th><td colspan=2><div class=thumbs>{pins}</div>"
            f"<small>each cell pinned once at its own first frame; the next pin closes the segment</small></td></tr>"
            f"<tr><th>engine</th><td colspan=2>{rc.engine_settings(record['workflow'], None)}</td></tr>"
            f"<tr><th>length</th><td colspan=2>{record['frames']} frames @ {record['fps']} fps = "
            f"{record['seconds']} s (placed {record['placed_seconds']} s) · seed {record['seed']} · "
            f"{record['steps']} steps</td></tr></table>")


def verdict(record: dict) -> str:
    """The lint the builder itself runs; a prompt only exists because it passed."""
    faults = ro.lint(record["prompt"])
    words = len(record["prompt"].split())
    body = "".join(f"<tr><td>{rc.esc(f)}</td></tr>" for f in faults)
    head = "PASS" if not faults else "FAIL"
    return (f"<p><b>{head}</b> · {len(faults)} fault(s) · {words} words</p>"
            + (f"<table class=lines>{body}</table>" if body else ""))


def take_card(book: Path, frames: Path, home: Path, episode, record: dict) -> str:
    shots = record.get("shots") or [record["index"]]
    made = home / "shots_r2v" / f"T{record['index']:02d}.mp4"
    video = (f'<div class=row2><video src="{rc.rel(book, made)}" controls muted preload="none"></video>'
             f'<a href="{rc.rel(book, made)}">open beside the page</a></div>'
             if made.exists() else '<p class=todo>take not rendered yet</p>')
    plan = "".join(f"<p><b>S{i:02d}</b> {rc.esc(episode.shot(i).frame)}<br><i>{rc.esc(episode.shot(i).motion)}</i></p>"
                   for i in shots)
    body = "".join(f"<details{' open' if n == 'detailed_description' else ''}><summary>{rc.esc(n)}</summary>"
                   f"<pre>{rc.esc(b)}</pre></details>" for n, b in sections_of(record["prompt"]))
    return (f'<section id="T{record["index"]:02d}" class=card><h2>Take {record["index"]:02d} · '
            f'{rc.esc(record["setup"])} · shots {shots} · {rc.esc(record["lane"])} · {record["seconds"]} s</h2>'
            f"<div class=cols3><div class=col><h3>Plan</h3>{plan}<h3>Lint</h3>{verdict(record)}"
            f"<h3>Rendered</h3>{video}</div>"
            f"<div class=col><h3>Inputs</h3>{inputs_table(book, frames, record)}</div>"
            f"<div class=col><h3>The prompt, exactly as sent</h3>{body}</div></div></section>")


def main(book_id: str, number: int) -> None:
    book = episode_home.book_dir(book_id)
    episode = episode_home.load_plan(book, number)
    home, frames = episode_home.home(book, number), episode_home.boards_dir(book, number)
    records = takes.cards(book, episode, number)
    faults = sum(len(ro.lint(r["prompt"])) for r in records)
    words = [len(r["prompt"].split()) for r in records]
    seconds = sum(r["seconds"] for r in records)
    head = (f'<section id="top"><h2>{len(records)} takes · {seconds:.1f} s of picture · '
            f"{faults} lint faults</h2><p>Prompts run from {min(words)} to {max(words)} words. "
            f"Every input the model is given, named. Click any picture or clip to open it beside the "
            f"page. Nothing renders until you say so.</p></section>")
    cards = [take_card(book, frames, home, episode, r) for r in records]
    nav = '<a href="#top">total</a>' + "".join(f'<a href="#T{r["index"]:02d}">T{r["index"]:02d}</a>' for r in records)
    out = home / "takes.html"
    out.write_text(rc.page(f"{episode.title} — EP {number} take prompts to validate", nav, [head] + cards),
                   encoding="utf-8")
    print(f"{len(records)} take cards, {faults} lint faults -> {out}")


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 1)
