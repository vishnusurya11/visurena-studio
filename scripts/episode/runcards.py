#!/usr/bin/env python
"""One page per episode with EVERY input of every shot, so the owner can run
any step by hand: the storyboard sheet each panel was cut from (with the
gutters found on it and the cell boxes drawn), the references that sheet
was drawn from, the panel H3 starts from, the line wavs with the voice they
were cloned from, the H3 settings and the full prompt, and the take.

    uv run python scripts/episode/runcards.py <codex_id> <episode>

Writes `episodes/epNN/runcards.html` beside the files it links (relative
links only: the page moves with the folder).
"""
from __future__ import annotations

import html
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio import episode_board as board, episode_home, episode_take_prompt as take_prompt
from studio.episode_spec import Episode

CELL_COLOURS = ("#ff3b3b", "#ffb000", "#3bff7a", "#3bd7ff", "#c07bff", "#ff6ad5", "#f0ff3b",
                "#ffffff", "#8cff00")


def esc(text) -> str:
    return html.escape(str(text))


def rel(book: Path, path: Path) -> str:
    """A link from `episodes/epNN/` to any file under the book."""
    return Path("../..", path.resolve().relative_to(book.resolve())).as_posix()


# ---- the storyboard sheets ---------------------------------------------------

def sheet_refs(sheet: Path) -> list[Path]:
    """The reference images the sheet was drawn from, from its prompt file."""
    text = sheet.with_suffix(".prompt.txt").read_text(encoding="utf-8")
    if "references, in order:" not in text:
        return []
    names = [line.strip() for line in text.split("references, in order:")[1].splitlines() if line.strip()]
    book = sheet.resolve().parents[3]  # refs are written by name: char-* live in refs/characters, the rest beside the sheet
    return [Path(n) if Path(n).is_absolute() else
            (book / "refs" / "characters" / n if n.startswith("char-") else sheet.parent / n) for n in names]


def sheet_prompt(sheet: Path) -> str:
    text = sheet.with_suffix(".prompt.txt").read_text(encoding="utf-8")
    return text.split("references, in order:")[0].strip()


def overlay(sheet: Path, boxes: list[tuple[int, int, int, int]], out: Path) -> Path:
    """The sheet with its found cells drawn on it: the proof of the crop."""
    from PIL import Image, ImageDraw

    image = Image.open(sheet).convert("RGB")
    draw = ImageDraw.Draw(image)
    for k, (l, t, r, b) in enumerate(boxes):
        draw.rectangle((l, t, r - 1, b - 1), outline=CELL_COLOURS[k % len(CELL_COLOURS)], width=6)
    image.resize((image.width // 2, image.height // 2)).save(out)
    return out


def cells_of(sheet: Path) -> list[tuple[int, int, int, int]]:
    import numpy as np
    from PIL import Image

    return board.cell_boxes(np.asarray(Image.open(sheet).convert("L"), dtype=float))


def locate(episode: Episode, frames: Path | None = None) -> dict[int, tuple[str, int]]:
    """shot index -> (sheet stem, cell index) for every shot cut from a sequence
    sheet, read from `seq_<setup>.dq.json` (a STRICT redraw outranks its first draw)."""
    out = {}
    for name in episode.setups:
        report = frames / f"seq_{name}.dq.json" if frames else None
        if not report or not report.exists():
            continue
        for sheet in episode_home.read_json(report)["sheets"]:
            for i, cell in enumerate(sheet["cells"]):
                if cell.endswith("_0.png"):
                    out[int(cell[1:3])] = (sheet["sheet"][:-4], i)
    return out


def thumbs(book: Path, paths: list[Path], label: str) -> str:
    items = "".join(f'<figure><a href="{rel(book, p)}"><img src="{rel(book, p)}"></a>'
                    f"<figcaption>{esc(p.name)}</figcaption></figure>" for p in paths)
    return f"<h4>{esc(label)}</h4><div class=thumbs>{items}</div>"


def sheet_section(book: Path, frames: Path, stem: str, shots: list[int]) -> str:
    sheet = frames / f"{stem}.png"
    boxes = cells_of(sheet)
    shown = overlay(sheet, boxes, frames / f"{stem}.cells.png")
    cells = "".join(f"<li>cell {k + 1}: shot {s:02d}, crop box {boxes[k]}</li>"
                    for k, s in enumerate(shots))
    return (f'<section id="{stem}"><h2>Sheet {esc(stem)} · gpt-image {esc(board.MODEL)} · '
            f"{board.CANVAS[0]}x{board.CANVAS[1]} · high</h2>"
            f'<div class=row><figure><a href="{rel(book, sheet)}"><img src="{rel(book, shown)}"></a>'
            f"<figcaption>cells as found on the sheet (gutter = row/col mean &gt; {board.GUTTER_WHITE:.0f}, "
            f"std &lt; {board.GUTTER_FLAT:.0f})</figcaption></figure><div class=meta>"
            f"<ul>{cells}</ul>{thumbs(book, sheet_refs(sheet), 'reference images, in the order attached')}"
            f"<details><summary>sheet prompt</summary><pre>{esc(sheet_prompt(sheet))}</pre></details>"
            f"</div></div></section>")


# ---- the cast voices ---------------------------------------------------------

def voice_card(book: Path, who: str) -> str:
    """The designed reference voice every line of `who` is cloned from."""
    folder = book / "cast" / who / "voice"
    meta = episode_home.read_json(folder / "voice.json") if (folder / "voice.json").exists() else {}
    profile = meta.get("instruction", {}).get("voice_profile", "")
    face = book / "refs" / "characters" / f"char-{who}.png"
    wav = folder / "design.wav"
    return (f'<section id="voice-{who}"><h2>Voice · {esc(who)}</h2><div class=row>'
            f'<figure><a href="{rel(book, face)}"><img src="{rel(book, face)}"></a>'
            f"<figcaption>{esc(face.name)}</figcaption></figure><div class=meta>"
            f'<p><b>reference clip:</b> <a href="{rel(book, wav)}">{esc(rel(book, wav))}</a> '
            f"(register {meta.get('register_hz', '?')} Hz)</p>"
            f'<audio controls preload="none" src="{rel(book, wav)}"></audio>'
            f"<p><b>designed passage:</b> {esc(meta.get('passage', ''))}</p>"
            f"<p><b>voice profile:</b> {esc(profile)}</p>"
            f"<details><summary>full voice sheet</summary><pre>{esc(meta.get('sheet', ''))}</pre></details>"
            f"</div></div></section>")


# ---- the shots ---------------------------------------------------------------

def voice_of(book: Path, speaker: str) -> Path:
    return book / "cast" / speaker / "voice" / "design.wav"


def wav_cell(book: Path, m: dict) -> str:
    if not m.get("rel_path"):
        return "not rendered"
    wav = book / m["rel_path"]
    return (f'<a href="{rel(book, wav)}">{esc(wav.name)}</a> {m.get("seconds", "?")} s'
            f'<br><audio controls preload="none" src="{rel(book, wav)}"></audio>')


def line_rows(book: Path, lines: list, measured: dict[int, dict]) -> str:
    rows = []
    for line in lines:
        m = measured.get(line.index, {})
        rows.append(
            f"<tr><td>{line.index:02d}</td><td>{esc(line.kind)}</td><td>{esc(line.speaker)}</td>"
            f"<td>{esc(line.text)}</td><td>{wav_cell(book, m)}</td>"
            f'<td><a href="{rel(book, voice_of(book, line.speaker))}">{esc(line.speaker)}/design.wav</a></td>'
            f"<td>{m.get('seed', '')}</td><td>{m.get('error_rate', '')}</td><td>{m.get('similarity', '')}</td></tr>")
    head = ("<tr><th>#</th><th>kind</th><th>speaker</th><th>text</th><th>wav (IndexTTS2)</th>"
            "<th>cloned from</th><th>seed</th><th>WER</th><th>voice sim</th></tr>")
    return f"<table class=lines>{head}{''.join(rows)}</table>" if rows else "<p>no line on this shot</p>"


def ref_row(book: Path, frames: Path, record: dict) -> str:
    """<Picture N> slots of an r2v take, as thumbnails in slot order."""
    if not record.get("refs"):
        return ""
    paths = []
    for name in record["refs"]:
        paths.append(frames / name if (frames / name).exists() else book / "refs" / "characters" / name)
    return f"<tr><th>references</th><td>{thumbs(book, paths, 'Picture 1..4, in slot order')}</td></tr>"


MANIFEST = Path(__file__).resolve().parents[3] / "comfy_studio" / "workflows" / "video"


def engine_values(name: str, graph: dict | None) -> dict:
    """The values the take ran with: read from its saved graph when there is one,
    else from the workflow file, through the manifest's inject map (node, field)."""
    manifest = MANIFEST / f"{name}.manifest.json"
    if not manifest.exists():
        return {}
    m = episode_home.read_json(manifest)
    graph = graph or (episode_home.read_json(MANIFEST / f"{name}.json") if (MANIFEST / f"{name}.json").exists() else {})
    out = {}
    for key, slot in m.get("inject", {}).items():
        if key not in ("lora_name", "lora_strength", "steps", "sampler", "scheduler", "shift_video", "shift_audio", "cfg", "ref_image_size"):
            continue  # the settings that decide the picture; prompt, seed, sizes and audio are on the card already
        node = graph.get(str(slot.get("node")), {})
        value = node.get("inputs", {}).get(slot.get("field"))
        if value is not None:
            out[key] = value
    out["models"] = ", ".join(m.get("models", [])) if isinstance(m.get("models"), list) else str(m.get("models", ""))
    return out


def engine_settings(workflow: str, take: Path | None = None) -> str:
    """LoRA, steps, sampler and sigma shift as the take ran (saved graph beside it), else the workflow file today."""
    name = workflow.split(" ")[0]
    graph_file = take.with_suffix(".graph.json") if take else None
    graph = episode_home.read_json(graph_file) if graph_file and graph_file.exists() else None
    values = engine_values(name, graph)
    if not values:
        return esc(workflow)
    source = "as run (saved graph)" if graph else "the workflow file as it is now (the take's own graph was not saved)"
    rows = "".join(f"<tr><th>{esc(k)}</th><td>{esc(v)}</td></tr>" for k, v in values.items())
    return f"{esc(name)} · <small>{source}</small><table>{rows}</table>"


def anchor_row(book: Path, frames: Path, record: dict) -> str:
    """Every pinned cell as a picture with its frame and role (start / END cell / start again)."""
    anchors = record.get("anchors") or []
    if not anchors:
        return ""
    starts = {}
    items = []
    for name, frame in sorted(anchors, key=lambda a: a[1]):
        role = "END cell" if name.endswith("E.png") else ("start cell again (end pin)" if name in starts else "start")
        starts.setdefault(name, frame)
        items.append(f'<figure><a href="{rel(book, frames / name)}"><img src="{rel(book, frames / name)}"></a>'
                     f"<figcaption>{esc(name)}<br>frame {frame} ({frame / 24:.2f} s)<br>{role}</figcaption></figure>")
    return f"<tr><th>pinned cells</th><td><div class=thumbs>{''.join(items)}</div></td></tr>"


def dq_row(book: Path, record: dict) -> str:
    """The take's DQ verdict, its strip, its motion scan and every attempt on disk."""
    take = book / record["rel_path"]
    dq = take.with_suffix(".dq.json")
    cells = []
    if dq.exists():
        r = episode_home.read_json(dq)
        a = r.get("audio", {})
        verdict = (f"{'PASS' if r.get('passed') else 'FAIL'} · foreign {r.get('foreign')} · off-beat {r.get('off_beat')} "
                   f"(advisory) · lag {a.get('lag_s', 0):+.3f} s{' (silent take, lag ungated)' if not a.get('lag_measured', True) else ''}"
                   f" · heard: {esc(a.get('heard', ''))[:80]}")
        strip = Path(r.get("strip", ""))
        if strip.exists():
            verdict += (f'<br><a href="{rel(book, strip)}"><img src="{rel(book, strip)}" style="width:100%;max-width:900px">'
                        f"</a><br><small>top: sampled frames with the closest own cell and its score; bottom: the cell expected at that time</small>")
        cells.append(f"<tr><th>DQ</th><td>{verdict}</td></tr>")
    motion = take.parent.parent.parent / "work" / "motion.json"
    if motion.exists():
        m = episode_home.read_json(motion).get(take.stem)
        if m:
            bars = "".join(f'<span style="display:inline-block;width:6px;height:{min(40, 3 * e):.0f}px;background:{"#f66" if e < 1.5 else "#6c6"};margin-right:1px;vertical-align:bottom"></span>'
                           for e in m["energy_per_quarter_s"])
            cells.append(f"<tr><th>motion</th><td>frozen {m['frozen_s']} s of {m['seconds']} s · spans {m['frozen_spans']} · "
                         f"mean energy {m['mean_energy']}<br>{bars}<br><small>one bar per 0.25 s; red = below the freeze floor</small></td></tr>")
    attempts = sorted(take.parent.glob(f"{take.stem}_*.mp4"))
    if attempts:
        cells.append("<tr><th>other attempts</th><td>" + " · ".join(f'<a href="{rel(book, p)}">{esc(p.name)}</a>' for p in attempts) + "</td></tr>")
    return "".join(cells)


def take_block(book: Path, record: dict | None, planned: str = "", frames: Path | None = None) -> str:
    if not record:
        return (f"<p class=todo>take not rendered yet</p><details open><summary>H3 prompt it will "
                f"run with (from the plan)</summary><pre>{esc(planned)}</pre></details>")
    take = book / record["rel_path"]
    audio = record.get("audio")
    if isinstance(audio, list):
        audio = ", ".join(f'<a href="lines/{n}">{n}</a> at {at} s' for n, at in audio)
    elif audio and not str(audio).startswith("silence"):
        audio = f'<a href="lines/{audio}">{audio}</a> at frame {record.get("audio_frame_idx", 6)}'
    else:
        audio = f"{audio or 'none'} (silent take)"
    run = (f"<tr><th>take run</th><td>shots {record['shots']} · anchors {esc(record.get('anchors'))}</td></tr>"
           if record.get("shots") else "")
    return (f"<table><tr><th>workflow</th><td>{engine_settings(record['workflow'], take)}</td></tr>{run}"
            f"{ref_row(book, frames, record) if frames else ''}"
            f"{anchor_row(book, frames, record) if frames else ''}"
            f"{dq_row(book, record) if record.get('rel_path') else ''}"
            f"<tr><th>mode</th><td>{esc(record['mode'])}</td></tr>"
            f"<tr><th>start image</th><td>{esc(record.get('start_image') or 'anchored cells: ' + ', '.join(n for n, _ in record.get('anchors', [])))} · {record['width']}x{record['height']}</td></tr>"
            f"<tr><th>audio guide</th><td>{audio}</td></tr>"
            f"<tr><th>frames</th><td>{record['frames']} @ {record['fps']} fps = {record['seconds']} s "
            f"(placed {record['placed_seconds']} s)</td></tr>"
            f"<tr><th>steps / seed</th><td>{record['steps']} / {record['seed']}</td></tr>"
            f"<tr><th>render</th><td>{record.get('render_s', '—')} s</td></tr>"
            f'<tr><th>take</th><td><a href="{rel(book, take)}">{esc(take.name)}</a></td></tr></table>'
            f"<details open><summary>H3 prompt</summary><pre>{esc(record['prompt'])}</pre></details>"
            f'<video src="{rel(book, take)}" controls muted preload="none"></video>')


def final_clip(book: Path, home: Path, master: Path, shot_placed: dict, out_dir: Path) -> tuple[Path, Path] | None:
    """The shot's own seconds cut from the master (picture + mix) and a 5-frame strip, cached by master mtime."""
    import subprocess
    from PIL import Image

    if not master.exists():
        return None
    out_dir.mkdir(parents=True, exist_ok=True)
    clip = out_dir / f"S{shot_placed['index']:02d}_final.mp4"
    strip = out_dir / f"S{shot_placed['index']:02d}_final.png"
    t0, t1 = shot_placed["t_start"], shot_placed["t_end"]
    if not clip.exists() or clip.stat().st_mtime < master.stat().st_mtime:
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{t0:.3f}", "-to", f"{t1:.3f}", "-i", str(master),
                        "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-c:a", "aac", "-movflags", "+faststart", str(clip)], check=True)
        tiles = []
        for k in range(5):
            at = t0 + (t1 - t0) * (k / 4 if k < 4 else 0.999)
            png = out_dir / f"_f{k}.png"
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{at:.3f}", "-i", str(master), "-frames:v", "1", "-vf", "scale=192:-1", str(png)], check=True)
            tiles.append(Image.open(png).convert("RGB"))
        sheet = Image.new("RGB", (sum(t.width for t in tiles) + 4 * 4, tiles[0].height), "black")
        x = 0
        for t in tiles:
            sheet.paste(t, (x, 0)); x += t.width + 4
        sheet.save(strip)
    return clip, strip


def final_block(book: Path, home: Path, shot_placed: dict | None) -> str:
    """What the viewer sees for this shot: its seconds of the latest master."""
    if not shot_placed:
        return ""
    master = home / "master_r2v.mp4"
    made = final_clip(book, home, master, shot_placed, home / "takes" / "work" / "final")
    if not made:
        return ""
    clip, strip = made
    return (f"<h4>final output of this shot (from the latest master, {shot_placed['t_start']:.2f}-{shot_placed['t_end']:.2f} s)</h4>"
            f'<a href="{rel(book, strip)}"><img src="{rel(book, strip)}" style="width:100%;max-width:980px"></a>'
            f'<div class=row2><video src="{rel(book, clip)}" controls preload="none"></video>'
            f'<a href="{rel(book, clip)}">open the final clip in the side viewer</a></div>')


def shot_card(book: Path, episode: Episode, shot, where: tuple[str, int] | None,
              record: dict | None, measured: dict[int, dict], r2v: dict | None = None,
              r2v_planned: str = "", with_i2v: bool = True, placed_shot: dict | None = None) -> str:
    panel = episode_home.boards_dir(book, episode.number) / f"S{shot.index:02d}.png"
    if where:
        stem, cell = where
        origin = (f'cut from <a href="#{stem}">{stem}.png</a>, cell {cell + 1}'
                  + (f" (redrawn alone: panel_S{shot.index:02d}_take{shot.take}.png)"
                     if (panel.parent / f"panel_S{shot.index:02d}_take{shot.take}.png").exists() else ""))
    else:
        origin = "no sheet"
    return (f'<section id="shot{shot.index:02d}"><h2>Shot {shot.index:02d} · {esc(shot.section)} · '
            f"{esc(shot.setup)} · {esc(shot.size)} · take {shot.take}</h2>"
            f'<div class=row><figure><a href="frames/{panel.name}"><img src="frames/{panel.name}"></a>'
            f"<figcaption>{panel.name} (H3 start frame) · {origin}</figcaption></figure><div class=meta>"
            f"<h4>plan</h4><p><b>frame:</b> {esc(shot.frame)}</p><p><b>motion:</b> {esc(shot.motion)}</p>"
            f"<p><b>faces:</b> {esc(', '.join(shot.faces) or '—')} · <b>beat</b> {shot.beat_s} s · "
            f"<b>coda</b> {shot.coda_s} s</p>"
            f"<h4>lines on this shot (audio first)</h4>{line_rows(book, episode.lines_of(shot.index), measured)}"
            + (f"<h4>i2v take (Start Frame)</h4>{take_block(book, record, take_prompt.build(episode, shot))}" if with_i2v else "")
            + final_block(book, episode_home.home(book, episode.number), placed_shot)
            + f"<h4>r2v take: references, pinned cells, workflow as run, audio, prompt, DQ, motion, attempts</h4>"
            f"{take_block(book, r2v, r2v_planned, episode_home.boards_dir(book, episode.number))}"
            f"</div></div></section>")


# ---- the engines table --------------------------------------------------------

def engine_cell(book: Path, record: dict | None) -> str:
    if not record:
        return "<td class=todo>—</td>"
    take = book / record["rel_path"]
    return (f'<td><video src="{rel(book, take)}" controls muted preload="none"></video>'
            f"<br>{record['frames']} f · {record.get('render_s', '?')} s render · seed {record['seed']}</td>")


def engines_table(book: Path, episode: Episode, i2v: dict[int, dict], r2v: dict[int, dict]) -> str:
    """The same shot on both engines, side by side, every shot."""
    rows = "".join(
        f'<tr><td><a href="#shot{s.index:02d}">S{s.index:02d}</a><br>{esc(s.section)}<br>{esc(s.setup)}</td>'
        f'<td><img src="frames/S{s.index:02d}.png" style="width:120px"></td>'
        f"{engine_cell(book, i2v.get(s.index))}{engine_cell(book, r2v.get(s.index))}</tr>"
        for s in episode.shots)
    done = sum(1 for s in episode.shots if s.index in r2v)
    return (f'<section id="engines"><h2>Engines · i2v (Start Frame) vs r2v (references + anchors) · '
            f"r2v rendered {done}/{len(episode.shots)}</h2>"
            f"<table class=engines><tr><th>shot</th><th>panel</th><th>i2v take</th><th>r2v take</th></tr>{rows}"
            f"</table></section>")



# ---- the r2v take card, redesigned --------------------------------------------

def name_of(who: str) -> str:
    return who.replace("_", " ").title()


def slot_map(record: dict) -> list[dict]:
    """What each <Picture N> and <Subject N> of the prompt is: the refs in slot
    order are the cast sheets of the faces shown, then the plate, then the strip
    (mirrors studio.episode_ref_official.subjects)."""
    faces = record.get("faces") or []
    refs = record.get("refs") or []
    out = []
    for k, name in enumerate(refs, start=1):
        if k <= len(faces):
            role, subject = f"cast sheet of {name_of(faces[k - 1])}", f"<Subject {k}>"
        elif k == len(faces) + 1:
            role, subject = "location plate (defines the room)", f"<Subject {k}>"
        else:
            role, subject = "storyboard strip: the take's own cells in time order (+ END frames)", "storyboard reference, no subject"
        out.append({"picture": f"<Picture {k}>", "file": name, "role": role, "subject": subject})
    return out


def audio_map(book: Path, record: dict) -> str:
    audio = record.get("audio")
    if isinstance(audio, list) and audio:
        return "<b>&lt;Audio 1&gt;</b> = " + " + ".join(f'<a href="lines/{esc(n)}">{esc(n)}</a> at {at} s' for n, at in audio) + \
            " (the dialogue wavs laid at their offsets, silence elsewhere, anchored at frame 0)"
    return "<b>&lt;Audio 1&gt;</b> = silence (a narration take: the narration is laid on the master, never in the take)"


def tag_prompt(text: str, slots: list[dict]) -> str:
    """The prompt with every <Subject N>, <Picture N>, <Audio 1> tag coloured and titled with what it is."""
    import re
    titles = {}
    for s in slots:
        titles[s["picture"]] = f"{s['file']} — {s['role']}"
        if s["subject"].startswith("<Subject"):
            titles[s["subject"]] = f"{s['role']} ({s['file']})"
    titles["<Audio 1>"] = "the take's audio track (see Inputs)"
    def rep(m):
        kind_word, number = m.group(1), m.group(2)
        tag = f"<{kind_word} {number}>"
        kind = {"Subject": "sub", "Picture": "pic", "Audio": "aud"}[kind_word]
        return f'<span class="tag {kind}" title="{esc(titles.get(tag, kind_word))}">&lt;{kind_word} {number}&gt;</span>'
    return re.sub(r"&lt;(Subject|Picture|Audio) (\d+)&gt;", rep, text)


def inputs_table(book: Path, frames: Path, record: dict, take: Path) -> str:
    slots = slot_map(record)
    rows = []
    for s in slots:
        path = frames / s["file"] if (frames / s["file"]).exists() else book / "refs" / "characters" / s["file"]
        rows.append(f'<tr><th>{esc(s["picture"])}</th><td><a href="{rel(book, path)}"><img class=thumb src="{rel(book, path)}"></a></td>'
                    f'<td><b>{esc(s["subject"])}</b><br>{esc(s["role"])}<br><small>{esc(s["file"])}</small></td></tr>')
    seen, items = set(), []
    for n, f in sorted(record.get("anchors") or [], key=lambda a: a[1]):
        role = "END cell" if n.endswith("E.png") else ("start of its segment" if n not in seen else "SAME cell pinned again (the freeze: removed for the final render)")
        seen.add(n)
        items.append(f'<figure><a href="{rel(book, frames / n)}"><img src="{rel(book, frames / n)}"></a>'
                     f"<figcaption>{esc(n)}<br>frame {f} ({f / 24:.2f} s)<br>{role}</figcaption></figure>")
    pins = "".join(items)
    return (f"<table class=inputs>{''.join(rows)}"
            f"<tr><th>audio</th><td colspan=2>{audio_map(book, record)}</td></tr>"
            f"<tr><th>pinned cells</th><td colspan=2><div class=thumbs>{pins}</div>"
            f"<small>the pins this take ran with. The final policy is one pin per cell at its start; a repeated or END pin is what froze the holds.</small></td></tr>"
            f"<tr><th>engine</th><td colspan=2>{engine_settings(record['workflow'], take)}</td></tr>"
            f"<tr><th>frames</th><td colspan=2>{record['frames']} @ {record['fps']} fps = {record['seconds']} s (placed {record['placed_seconds']} s) · "
            f"seed {record['seed']} · render {record.get('render_s', '—')} s</td></tr></table>")


def outputs_block(book: Path, home: Path, record: dict, placed_shot: dict | None) -> str:
    take = book / record["rel_path"]
    parts = [final_block(book, home, placed_shot)]
    parts.append(f'<h4>raw take {esc(take.name)} (before the cut, with its own audio)</h4>'
                 f'<div class=row2><video src="{rel(book, take)}" controls muted preload="none"></video>'
                 f'<a href="{rel(book, take)}">open in the side viewer</a></div>')
    parts.append(f"<table>{dq_row(book, record)}</table>")
    return "".join(parts)


def r2v_card(book: Path, episode: Episode, shot, where, record: dict | None, measured: dict, placed_shot: dict | None,
             planned: str = "") -> str:
    home, frames = episode_home.home(book, episode.number), episode_home.boards_dir(book, episode.number)
    cell = frames / f"Q{shot.index:02d}_0.png"
    origin = f'cut from <a href="#{where[0]}">{where[0]}.png</a>, cell {where[1] + 1}' if where else "no sheet"
    head = (f'<section id="shot{shot.index:02d}" class=card><h2>Shot {shot.index:02d} · {esc(shot.section)} · '
            f"{esc(shot.setup)} · {esc(shot.size)}</h2>")
    plan = (f"<div class=col><h3>Plan</h3>"
            f'<figure><a href="{rel(book, cell)}"><img src="{rel(book, cell)}"></a><figcaption>{esc(cell.name)} · frame zero · {origin}</figcaption></figure>'
            f"<p><b>frame:</b> {esc(shot.frame)}</p><p><b>motion:</b> {esc(shot.motion)}</p>"
            + "".join(f"<p><b>sub-shot at {c.at_s} s:</b> {esc(c.frame)} <i>{esc(c.motion)}</i></p>" for c in shot.cuts)
            + f"<p><b>faces:</b> {esc(', '.join(shot.faces) or '—')} · <b>beat</b> {shot.beat_s} s · <b>coda</b> {shot.coda_s} s</p>"
            f"<h3>Lines (audio first)</h3>{line_rows(book, episode.lines_of(shot.index), measured)}</div>")
    if not record:
        body = (f"<div class=col><h3>Take</h3><p class=todo>not rendered yet</p>"
                f"<details><summary>prompt it will run with</summary><pre>{esc(planned)}</pre></details></div>")
        return head + f"<div class=cols>{plan}{body}</div></section>"
    take = book / record["rel_path"]
    slots = slot_map(record)
    body = (f"<div class=col><h3>Inputs</h3>{inputs_table(book, frames, record, take)}"
            f"<h3>Prompt</h3><details open><summary>the exact text sent to the model (hover a tag to see what it is)</summary>"
            f"<pre>{tag_prompt(esc(record['prompt']), slots)}</pre></details></div>"
            f"<div class=col><h3>Outputs</h3>{outputs_block(book, home, record, placed_shot)}</div>")
    return head + f"<div class=cols3>{plan}{body}</div></section>"



def workflow_section(book: Path, records: dict) -> str:
    """Every input the H3 workflow is given, what it is called in the prompt, and where it comes from."""
    any_record = next(iter(records.values()), None)
    if not any_record:
        return ""
    name = any_record["workflow"].split(" ")[0]
    manifest = MANIFEST / f"{name}.manifest.json"
    m = episode_home.read_json(manifest) if manifest.exists() else {}
    models = "".join(f"<li>{esc(x)}</li>" for x in (m.get("models") or []))
    rows = [
        ("models", "the engine itself", f"<ul>{models}</ul>"),
        ("prompt", "the text, in MiniMax's ref2va grammar",
         "subject_definitions (who and where, each tied to a &lt;Picture N&gt;), summary, retention_analysis "
         "(how faithfully each reference is kept), detailed_description (the shots, timed), overall_soundscape, non_diegetic_music"),
        ("ref_image_1 … ref_image_N", "the reference pictures, in slot order",
         "<span class='tag pic'>&lt;Picture 1..k&gt;</span> = the cast sheet of each face the take SHOWS, one per face, each declared as "
         "<span class='tag sub'>&lt;Subject k&gt;</span>; then <span class='tag pic'>&lt;Picture k+1&gt;</span> = the location plate, declared as the location "
         "<span class='tag sub'>&lt;Subject k+1&gt;</span>; then <span class='tag pic'>&lt;Picture k+2&gt;</span> = the storyboard strip of this take's own cells "
         "in time order. The model keeps identity, wardrobe and room from these."),
        ("guide images (MiniMaxH3AddGuide)", "the pinned storyboard cells",
         "one cell per segment at its first frame: the take starts on it and cuts to the next one at its frame. A pin is a soft "
         "conditioning row at that time, not a hard frame replacement."),
        ("guide audio (MiniMaxH3AddGuide)", "<span class='tag aud'>&lt;Audio 1&gt;</span>",
         "one wav anchored at frame 0: the dialogue lines of this take laid at their offsets with silence between them, so the lips "
         "are driven by the same recording the master plays. A narration take gets pure silence; narration is laid on the master."),
        ("width, height, frames, fps", "the canvas", "768 x 1344 at 24 fps; frames = the shot's placed seconds plus a handle"),
        ("steps, sampler, scheduler, seed", "the sampling", "8 steps, euler, beta; the seed is derived from the episode and shot"),
        ("lora_name, lora_strength", "the turbo LoRA", "the dedicated Ref2V 8-step 768p LoRA at 1.0 (an FL2VA-lineage LoRA on ref2va pumps the camera)"),
        ("shift_video, shift_audio", "MiniMaxH3SigmaShift", "12 / 3, the Ref2V LoRA's own release values"),
        ("ref_image_size", "how references are scaled", "match"),
        ("output", "what comes back", "one mp4 with its own audio track; the cut uses the picture and the master's own mix"),
    ]
    body = "".join(f"<tr><th>{esc(a)}</th><td>{esc(b)}</td><td>{d}</td></tr>" for a, b, d in rows)
    return (f'<section id="workflow"><h2>What the workflow receives, and what every label means</h2>'
            f"<p>Workflow <b>{esc(name)}</b>. Every take card below shows these same inputs with the actual files.</p>"
            f"<table class=lines><tr><th>input</th><th>what it is</th><th>detail</th></tr>{body}</table></section>")


LEGEND = ('<section id="legend"><h2>How to read a take card</h2><p>Each shot card has three columns. '
          '<b>Plan</b>: the storyboard cell that is frame zero, the frame and motion text, and the lines with their wavs. '
          '<b>Inputs</b>: what the model received, in slot order: every <span class="tag pic">&lt;Picture N&gt;</span> with its file and what it is, '
          'the <span class="tag sub">&lt;Subject N&gt;</span> it defines, <span class="tag aud">&lt;Audio 1&gt;</span>, the pinned cells with their frames, '
          'the engine values as run, and the prompt with every tag coloured (hover a tag). '
          '<b>Outputs</b>: the shot as it is in the latest master, the raw take, the DQ verdict with its strip, the motion bars '
          '(red = below the freeze floor) and every other attempt. Click any picture or clip: it opens in the side viewer.</p></section>')

# ---- the page ----------------------------------------------------------------

STYLE = ("body{font:14px system-ui;background:#111;color:#ddd;margin:20px;max-width:1500px}"
         "section{background:#1b1b1b;padding:14px;border-radius:8px;margin-bottom:18px}"
         ".row{display:grid;grid-template-columns:320px 1fr;gap:18px}figure{margin:0}"
         "figure img{width:100%}figcaption{font-size:12px;color:#9ab;margin-top:4px}"
         "table{border-collapse:collapse;margin:4px 0}th{text-align:left;padding:2px 10px 2px 0;color:#9ab;vertical-align:top}"
         "td{padding:2px 10px 2px 0;vertical-align:top}table.lines td,table.lines th{border-bottom:1px solid #333;font-size:13px}"
         "pre{white-space:pre-wrap;background:#0d0d0d;padding:10px;border-radius:6px;font-size:12px}"
         "a{color:#8cf}h4{margin:12px 0 4px;color:#9ab}.thumbs{display:flex;gap:8px;flex-wrap:wrap}"
         ".thumbs figure{width:110px}audio{width:320px;display:block;margin:4px 0}.todo{color:#fb8}video{width:320px;margin-top:8px}"
         "table.engines td{border-bottom:1px solid #333;padding:6px 10px 6px 0}table.engines video{width:200px}"
         "nav a{margin-right:10px}details summary{cursor:pointer;color:#9ab}.row2{display:flex;gap:12px;align-items:center;flex-wrap:wrap}"
         ".cols3{display:grid;grid-template-columns:minmax(260px,1fr) minmax(360px,1.4fr) minmax(360px,1.4fr);gap:20px}"
         ".cols{display:grid;grid-template-columns:1fr 2fr;gap:20px}.col h3{margin:8px 0 6px;color:#cde;font-size:15px;border-bottom:1px solid #333}"
         "table.inputs th{width:84px}table.inputs td{padding:4px 8px 4px 0}img.thumb{width:96px;height:auto;display:block}"
         ".tag{padding:0 4px;border-radius:3px;cursor:help}.tag.pic{background:#1e3a5f;color:#9cf}.tag.sub{background:#3a2a1e;color:#fc9}.tag.aud{background:#1e3a2a;color:#9f9}"
         "section.card{max-width:none}body{max-width:none}h1{font-size:20px}")


def deliverables_section(book: Path, home: Path) -> str:
    """Every kept master with its size and time, newest first, and the QC of the current one."""
    masters = sorted(home.glob("master_iter*.mp4"), key=lambda p: int(p.stem.split("iter")[1]), reverse=True)
    rows = "".join(f'<tr><td><a href="{rel(book, p)}">{esc(p.name)}</a></td><td>{p.stat().st_size / 1e6:.1f} MB</td>'
                   f"<td>{__import__('datetime').datetime.fromtimestamp(p.stat().st_mtime):%Y-%m-%d %H:%M}</td></tr>" for p in masters)
    qc = home / "qc_r2v.json"
    q = episode_home.read_json(qc) if qc.exists() else {}
    qline = (f"latest QC: {q.get('seconds', 0):.1f} s · {q.get('lufs', 0):.1f} LUFS · TP {q.get('true_peak', 0):.1f} dBTP · "
             f"lines heard {sum(1 for l in q.get('lines', []) if l.get('passed'))}/{len(q.get('lines', []))} · "
             f"{'PASS' if q.get('passed') else 'FAIL'}") if q else ""
    return (f'<section id="deliverables"><h2>Deliverables</h2><p>{esc(qline)}</p>'
            f"<table class=lines><tr><th>master</th><th>size</th><th>made</th></tr>{rows}</table></section>")


def findings_section(home: Path) -> str:
    """The owner's feedback and the DQ findings, each with its evidence and the planned fix."""
    path = home / "findings.json"
    if not path.exists():
        return ""
    items = episode_home.read_json(path)
    rows = "".join(f"<tr><td>{esc(i.get('stage', ''))}</td><td>{esc(i['source'])}</td><td>{esc(i['finding'])}</td><td>{esc(i.get('evidence', ''))}</td>"
                   f"<td>{esc(i.get('fix', ''))}</td><td><b>{esc(i.get('status', ''))}</b></td></tr>" for i in items)
    return (f'<section id="findings"><h2>Every issue found, by stage: script, storyboards, prompts, workflow, takes, editing, audio, title (iteration 4 → final)</h2>'
            f"<table class=lines><tr><th>stage</th><th>source</th><th>finding</th><th>evidence</th><th>fix</th><th>status</th></tr>{rows}</table></section>")


def stages_section(home: Path) -> str:
    """Stage times of the latest iteration from iterations.log."""
    log = home / "iterations.log"
    if not log.exists():
        return ""
    lines = [l for l in log.read_text(encoding="utf-8").splitlines() if l.startswith("== ")]
    starts = [k for k, l in enumerate(lines) if "start" in l]
    latest = lines[starts[-1]:] if starts else lines[-12:]
    return (f'<section id="stages"><h2>Stage times (latest iteration)</h2><pre>' + esc("\n".join(latest)) + "</pre></section>")


VIEWER = (
    "<aside id=viewer><div id=vhead><span id=vname></span><button onclick=\"closeViewer()\">close</button></div><div id=vbody></div></aside>"
    "<script>"
    "function closeViewer(){document.getElementById('viewer').style.display='none';document.body.classList.remove('with-viewer');}"
    "function showIn(href,name){var b=document.getElementById('vbody');b.innerHTML='';"
    r"var el=/\.(mp4|webm)$/i.test(href)?document.createElement('video'):document.createElement('img');"
    "if(el.tagName==='VIDEO'){el.controls=true;el.autoplay=true;}el.src=href;b.appendChild(el);"
    "document.getElementById('vname').textContent=name;document.getElementById('viewer').style.display='block';"
    "document.body.classList.add('with-viewer');}"
    "document.addEventListener('click',function(e){var a=e.target.closest('a');if(!a)return;var h=a.getAttribute('href')||'';"
    r"if(/\.(png|jpg|jpeg|webp|mp4|webm)$/i.test(h)){e.preventDefault();showIn(h,h.split('/').pop());}});"
    "</script>")

VIEWER_STYLE = ("#viewer{display:none;position:fixed;top:0;right:0;width:42vw;height:100vh;background:#000;border-left:1px solid #333;"
                "z-index:9;overflow:auto}#vhead{display:flex;justify-content:space-between;padding:6px 10px;color:#9ab;font-size:12px}"
                "#vbody img,#vbody video{width:100%;height:auto;max-height:92vh;object-fit:contain}"
                "body.with-viewer{padding-right:44vw}#vhead button{background:#222;color:#ddd;border:1px solid #444;border-radius:4px;cursor:pointer}")


def page(title: str, nav: str, sections: list[str]) -> str:
    """Every image or video link opens in the side viewer; the page never leaves."""
    return (f"<!doctype html><meta charset=utf-8><title>{esc(title)}</title><style>{STYLE}{VIEWER_STYLE}</style>"
            f"<h1>{esc(title)}</h1><nav>{nav}</nav>{''.join(sections)}{VIEWER}")


def main(book_id: str, number: int) -> None:
    book = episode_home.book_dir(book_id)
    episode = episode_home.load_plan(book, number)
    home, frames = episode_home.home(book, number), episode_home.boards_dir(book, number)
    # The i2v sheet is OPTIONAL. runcards was written when every episode rendered
    # both engines and compared them; r2v is the engine now, and an episode that
    # only ran r2v was left with no report at all -- which is the one artefact the
    # owner reads to see what went wrong.
    i2v_sheet = home / "shots" / "shots.json"
    records = ({r["index"]: r for r in episode_home.read_json(i2v_sheet)}
               if i2v_sheet.exists() else {})
    r2v_sheet = home / "shots_r2v" / "shots.json"
    r2v = {}
    for r in (episode_home.read_json(r2v_sheet) if r2v_sheet.exists() else []):
        for i in r.get("shots") or [r["index"]]:
            r2v[i] = r  # a take-run's record answers for every shot in the run
    r2v_cards = home / "shots_r2v" / "prompts.json"
    r2v_planned = {}
    for c in (episode_home.read_json(r2v_cards) if r2v_cards.exists() else []):
        for i in c.get("shots") or [c["index"]]:
            r2v_planned[i] = c["prompt"]
    measured = {r["index"]: r for r in episode_home.read_json(home / "lines" / "lines.json")}
    where = locate(episode, episode_home.boards_dir(book, number))
    by_sheet: dict[str, list[int]] = {}
    for index, (stem, _) in where.items():
        by_sheet.setdefault(stem, []).append(index)
    speakers = sorted({line.speaker for line in episode.lines})
    sections = [findings_section(home), stages_section(home)] + [voice_card(book, who) for who in speakers]
    sections += [engines_table(book, episode, records, r2v)]
    sections += [sheet_section(book, frames, stem, shots) for stem, shots in by_sheet.items()]
    sections += [shot_card(book, episode, shot, where.get(shot.index), records.get(shot.index), measured,
                           r2v.get(shot.index), r2v_planned.get(shot.index, ""))
                 for shot in episode.shots]
    nav = '<a href="#findings">findings</a><a href="#stages">stage times</a>' + "".join(f'<a href="#voice-{who}">voice: {who}</a>' for who in speakers)
    nav += '<a href="#engines">engines: i2v vs r2v</a>'
    nav += "".join(f'<a href="#{stem}">{stem}</a>' for stem in by_sheet)
    nav += "".join(f'<a href="#shot{s.index:02d}">S{s.index:02d}</a>' for s in episode.shots)
    out = home / "runcards.html"
    out.write_text(page(f"{episode.title} — EP {number} run cards: every input", nav, sections),
                   encoding="utf-8")
    # the final report: deliverables, every issue by stage, times, sheets, and the r2v takes only
    final = [deliverables_section(book, home), findings_section(home), stages_section(home), LEGEND,
             workflow_section(book, r2v)]
    final += [voice_card(book, who) for who in speakers]
    final += [sheet_section(book, frames, stem, shots) for stem, shots in by_sheet.items()]
    placed_file = home / "placed.json"
    placed_by = {s["index"]: s for s in episode_home.read_json(placed_file)["shots"]} if placed_file.exists() else {}
    final += [r2v_card(book, episode, shot, where.get(shot.index), r2v.get(shot.index), measured,
                       placed_by.get(shot.index), r2v_planned.get(shot.index, "")) for shot in episode.shots]
    fnav = ('<a href="#deliverables">deliverables</a><a href="#findings">issues</a><a href="#stages">stage times</a>'
            '<a href="#legend">how to read a card</a><a href="#workflow">workflow inputs</a>'
            + "".join(f'<a href="#voice-{who}">voice: {who}</a>' for who in speakers)
            + "".join(f'<a href="#{stem}">{stem}</a>' for stem in by_sheet)
            + "".join(f'<a href="#shot{s.index:02d}">S{s.index:02d}</a>' for s in episode.shots))
    (home / "report_final.html").write_text(
        page(f"{episode.title} — EP {number} final report: issues, inputs, prompts, workflow per take", fnav, final),
        encoding="utf-8")
    print(f"final report -> {home / 'report_final.html'}")
    print(f"{len(episode.shots)} shot cards, {len(by_sheet)} sheets -> {out}", flush=True)


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 1)
