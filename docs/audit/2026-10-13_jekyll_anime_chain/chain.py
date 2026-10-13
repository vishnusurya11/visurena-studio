"""Does the episode chain hold a gothic anime look end to end?  Jekyll, styles 1 (VHD, Bloodlust) and 2 (HEL, Hellsing).

    uv run python docs/audit/2026-10-13_jekyll_anime_chain/chain.py refs  STYLE [name ...] [--salt S]
    uv run python docs/audit/2026-10-13_jekyll_anime_chain/chain.py panel STYLE a|b [--salt S]
    uv run python docs/audit/2026-10-13_jekyll_anime_chain/chain.py take  STYLE a|b
    uv run python docs/audit/2026-10-13_jekyll_anime_chain/chain.py frames STYLE a|b

Chain, as the episode runs it:  refs (sheets + place masters, NoobAI in the style)
-> Qwen-Image 2.1 panel from the REAL grids.py builder (grids.compose v2 + look_for/negative_for
   reading a temp look.json under STYLE/book/refs/, never library/)
-> MiniMax-H3 ref2va take on takes_r2v.BASE (CRF 10), staged the way takes_r2v stages a take
   that has a panel: the cast sheets, then the panel LAST, nothing pinned (ep27's card form).
Shots: a = ch1, Hyde strides over the fallen girl at a foggy gaslit corner (silent, narration lane);
       b = ch3, Jekyll and Utterson by the fire, Utterson speaks ep01 l25.wav, locked camera.
Everything is written beside this file; times.jsonl records seconds per render.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import subprocess
import sys
import time
import zlib
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "episode"))

from studio import book_look, comfy, h3_anchors, house_style, take_refs  # noqa: E402
from studio.storyboard_grid import cut_clause  # noqa: E402

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("gothic", ROOT / "docs/audit/2026-10-13_jekyll_gothic_anime/render.py")
G = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(G)

STYLE_NAMES = {"VHD": "1. Bloodlust gothic", "HEL": "2. Hellsing ink-red"}

# ---------------------------------------------------------------- refs (NoobAI)
SHEET = ("full body, standing, front view, facing viewer, looking at viewer, arms at sides, "
         "(simple background:1.2), dark grey gradient background, character reference")
SHEET_NEG = "(text:1.3), caption, blood, gore, injury, cape, coattails, scenery, street, building, multiple views, holding, coat over shoulder, chibi, cartoon, "
NO_GREEN = "(green theme:1.3), (green light:1.3), green background, green tint, acid green, "
UTTERSON = ("mr utterson, lawyer, (40 years old:1.3), (mature male:1.5), (middle-aged man:1.3), (wrinkles:0.9), hollow cheeks, long gaunt rugged face, "
            "(dour:1.2), unsmiling, serious, tired eyes, (nasolabial folds:1.1), lean, tall, bony, narrow-chested, (clean-shaven:1.2), "
            "(lank light brown hair streaked with grey:1.4), (dusty sandy hair:1.2), receding hairline, collar-length hair, "
            "black frock coat, dark waistcoat, white shirt, black cravat, (dark lawyer's dress:1.1)")
UTTERSON_NEG = ("(young:1.3), teenager, bishounen, pretty, spiked hair, (grey hair:1.2), (blonde hair:1.4), yellow hair, bright hair, smile, grin, fangs, "
                "beard, mustache, facial hair, old man, fat, black hair, white hair, hat, bowler hat, top hat, glasses, ")
JEKYLL_NEG = ("young, beard, mustache, facial hair, sideburns, thin, skinny, long hair, hat, top hat, evil, sneer, grin, "
              "fangs, red eyes, red hair, glasses, eyewear, ")
HYDE_SIDE = ", (black mutton chops:1.3), (long black sideburns:1.2), (young adult man:1.2), pale face, slender adult proportions"
HYDE_NEG = "huge hat, oversized hat, cavalier hat, old, middle-aged, glasses, (whiskers:1.4), cat whiskers, child, kid, round face, "
REFS = {
    "hyde": ("1boy, solo, " + G._HYDE + HYDE_SIDE + ", " + SHEET, G._HYDE_NEG + HYDE_NEG + SHEET_NEG, (832, 1216), True),
    "jekyll": ("1boy, solo, (mature male:1.4), (50 years old:1.3), " + G._JEKYLL + ", (no hat:1.2), " + SHEET, JEKYLL_NEG + SHEET_NEG, (832, 1216), False),
    "utterson": ("1boy, solo, " + UTTERSON + ", (no hat:1.2), " + SHEET, UTTERSON_NEG + SHEET_NEG, (832, 1216), False),
    "corner": ("(no humans:1.3), scenery, victorian london street corner, 3 a.m., (dark night:1.3), (thick fog:1.4), foggy, mist, "
               "a cast-iron gas lamp burning at the corner kerb on the right, two streets meeting at a right angle, "
               "terraced brick houses, shuttered shop windows, dark doorways, black iron railings, wet cobblestones, "
               "deserted, wide shot, eye level",
               "1boy, 1girl, people, person, character, silhouette, purple sky, pink sky, sunset, clouds, church, courtyard, (text:1.3), sign, ", (1024, 1024), False),
    "study": ("no humans, scenery, indoors, victorian study, night, fireplace, fire, firelight, two armchairs, "
              "small table, wine glass, bookshelf, wooden wall, warm light, deep shadow, wide shot",
              "1boy, 1girl, people, silhouette, (text:1.3), ", (1024, 1024), False),
}


def refs_prompt(style: str, name: str) -> tuple[str, str]:
    """NoobAI words for one refs picture: the gothic probe's style lead, its per-style fixes, no green."""
    lead, _, neg_extra = G.STYLES[style]
    body, neg, _, is_hyde = REFS[name]
    person = name in ("hyde", "jekyll", "utterson")
    fix_pos, fix_neg = G.HYDE_FIX.get(style, ("", "")) if is_hyde else ("", "")
    all_pos, all_neg = G.STYLE_ALL.get(style, ("", "")) if person else ("", "")
    return (G.QUALITY + lead + all_pos + fix_pos + body,
            G.NEG + neg + fix_neg + all_neg + neg_extra + NO_GREEN)


def draw_ref(style: str, name: str, salt: str) -> Path:
    prompt, negative = refs_prompt(style, name)
    (w, h), seed = REFS[name][2], zlib.crc32(f"jekyll_chain/{style}/{name}{salt}".encode())
    values = {"prompt": prompt, "negative_prompt": negative, "width": w, "height": h, "seed": seed,
              "hires_seed": seed, "hires_denoise": 0.55, "ckpt_name": G.BASES["noob"],
              "filename_prefix": f"jekyll_chain/{style}_{name}"}
    for i, (lora, weight) in enumerate(G.STYLES[style][1], start=1):
        values.update({f"lora{i}": lora, f"lora{i}_model": weight, f"lora{i}_clip": weight})
    began = time.time()
    out = comfy.run(G.WORKFLOW, values)
    dest = HERE / style / f"{name}{'_s' + salt if salt else ''}.png"
    dest.parent.mkdir(exist_ok=True)
    shutil.copy2(out[0], dest)
    log({"step": "refs", "style": style, "name": name, "seed": seed, "seconds": round(time.time() - began, 1),
         "file": rel(dest), "workflow": G.WORKFLOW, "loras": G.STYLES[style][1], "prompt": prompt, "negative": negative})
    return dest


# ---------------------------------------------------------------- the book's temp look
LOOKS = {
    "VHD": {"look": "anime_gothic",
            "lead": ("Hand-drawn 2D gothic anime in the style of Vampire Hunter D: Bloodlust (2000, Madhouse, "
                     "Yoshiaki Kawajiri): a cel animation frame with fine thin black ink outlines, flat cel shading "
                     "with hard-edged shadows, elegant long faces, painted gothic backgrounds, cold moonlight, a "
                     "blue-black and violet palette."),
            "take": "Hand-drawn 2D gothic anime, Bloodlust cel animation"},
    "HEL": {"look": "anime_gothic",
            "lead": ("Hand-drawn 2D gothic anime in the style of Hellsing Ultimate (2006, Kouta Hirano): a cel "
                     "animation frame with sharp angular black ink linework, jagged black ink shadows, flat cel "
                     "shading, a red and black palette with crimson shadows, a dark gothic atmosphere."),
            "take": "Hand-drawn 2D gothic anime, Hellsing Ultimate cel animation"},
}
"""What a book would file in refs/look.json for this look (book_look.DRAWN_GRID reads `lead`,
plan_look reads `take`).  No `atmosphere`: the grid says it 'in every frame', fireside included."""


def book_of(style: str) -> Path:
    """A throwaway book folder holding only refs/look.json -- library/ is never touched."""
    book = HERE / style / "book"
    (book / "refs").mkdir(parents=True, exist_ok=True)
    said = dict(LOOKS[style], decision="2026-10-13 chain test only, not a ruling", by="test")
    (book / "refs" / "look.json").write_text(json.dumps(said, indent=1), encoding="utf-8")
    return book


# ---------------------------------------------------------------- the rows (refs.json words, faults fixed)
PHYS = {
    "hyde": ("Coarse, unkempt black hair; thick bushy black mutton-chop side-whiskers down both cheeks to the jaw; "
             "pale, dwarfish, thin upper lip curled in a cold sneer, displeasing smile; soft black felt wideawake hat, "
             "low flat crown, wide floppy brim. A small, slight, sinister young man of about twenty-five, short and "
             "narrow-shouldered. Wearing: ill-fitting black coat, dark trousers, lean corded knuckly hands"),
    "jekyll": ("Thick iron-grey hair, silver-grey at the temples and sides, brushed back from a high forehead; full, "
               "broad, smooth, clean-shaven face. A large, broad, heavy-set, handsome man of fifty. Wearing: black "
               "frock coat, dark waistcoat, white shirt, cravat"),
    "utterson": ("Lank, dusty sandy-grey hair falling to his collar, thin at the crown; clean-shaven, long, gaunt, "
                 "rugged, unsmiling face. A lean, long, bony, dry man of about forty, narrow-chested. Wearing: black "
                 "frock coat, dark waistcoat, white shirt, black cravat"),
    "child": ("Fair hair in two plaits; small knitted woollen bonnet. A small girl of about nine. Wearing: plain "
              "grey pinafore dress, black boots"),
}
CAST = {"hyde": ("EDWARD HYDE", "Mr Hyde"), "jekyll": ("HENRY JEKYLL", "Dr Jekyll"),
        "utterson": ("GABRIEL JOHN UTTERSON", "Mr Utterson"), "child": ("CHILD", "the child")}

SHOTS = {
    "a": {"size": "full", "place": "corner", "who": ["hyde", "child"], "sheets": ["hyde"],
          "frame": ("Mr Hyde strides straight over the child, who has fallen on the wet cobbles at the corner; his "
                    "boot comes down beyond her and he walks on without a pause, his cold sneer turned down at her "
                    "as she looks up, frightened."),
          "at_rest": ("The corner gas lamp stands at the RIGHT third; Mr Hyde is at the LEFT of centre, the child "
                      "lies at the CENTRE bottom, his long shadow across her."),
          "described": ("A street corner in a sleeping London quarter at three in the morning: terraced brick houses "
                        "with shuttered windows and black iron railings, a cast-iron gas lamp burning at the corner "
                        "kerb, frosted wet cobbles, thick fog"),
          "light": "gaslight from the right, deep black"},
    "b": {"size": "medium", "place": "study", "who": ["jekyll", "utterson"], "sheets": ["jekyll", "utterson"],
          "frame": ("Dr Jekyll and Mr Utterson sit facing each other in two armchairs by the fire, both bareheaded, "
                    "a glass of wine on the small table between them; Mr Utterson leans forward and speaks, "
                    "Dr Jekyll listens with a pale, uneasy face."),
          "at_rest": ("The fireplace is at the LEFT edge; Dr Jekyll sits at the LEFT third, Mr Utterson at the "
                      "RIGHT third, both seen from the knees up."),
          "described": ("A warm Victorian study at night: a stone fireplace with a coal fire, two leather armchairs, "
                        "bookshelves and dark wood panelling; the light is the firelight from the left"),
          "light": "firelight from the left, deep black"},
}


def panel_prompt(style: str, shot: str) -> tuple[str, str, dict]:
    """(prompt, negative, {LoadImage node: picture}) through grids.py's own builder and look."""
    import grids
    book, s = book_of(style), SHOTS[shot]
    cast, slots = [], {}
    for who in s["who"]:
        name, display = CAST[who]
        ref = None
        if who in s["sheets"]:
            ref = len(slots) + 1
            slots[str(100 + ref)] = HERE / style / f"{who}.png"
        cast.append({"ref": ref, "name": name, "entity": who, "display": display,
                     "wear": PHYS[who], "against": ""})
    place_slot = len(slots) + 1
    slots[str(100 + place_slot)] = HERE / style / f"{s['place']}.png"
    blocks = [{"size": grids.SAID[s["size"]], "body": f"{s['frame']} {s['at_rest']}",
               "cut": cut_clause(s["size"], peopled=True), "who": [CAST[w][0] for w in s["who"]], "extras": 0}]
    text = grids.compose("v2", blocks, 1, 1, ([place_slot], s["described"]), cast, place_slot, [],
                         room=None, geometry="", light=s["light"], **grids.look_for(book))
    return text, grids.negative_for(book), slots


def draw_panel(style: str, shot: str, salt: str) -> Path:
    import grids
    text, negative, slots = panel_prompt(style, shot)
    seed = 40500 + zlib.crc32(f"{style}{shot}{salt}".encode()) % 1000
    name = f"jekyll_chain_{style}_panel_{shot}"
    began = time.time()
    made = comfy.wait(comfy.submit(grids.graph_for(text, slots, 1, 1, seed, name, negative)), timeout=3600)
    dest = HERE / style / f"panel_{shot}{'_s' + salt if salt else ''}.png"
    shutil.copy2(made[0], dest)
    dest.with_suffix(".txt").write_text(f"{text}\n\n--- negative ---\n{negative}\n", encoding="utf-8")
    log({"step": "panel", "style": style, "shot": shot, "seed": seed, "seconds": round(time.time() - began, 1),
         "file": rel(dest), "workflow": "image_qwen_image_2_1_edit_multi",
         "slots": {k: rel(v) for k, v in slots.items()}})
    return dest


# ---------------------------------------------------------------- the take (H3 BASE)
FRAMES, SIDE, FPS = 124, 768, 24
VOICE = ROOT / "library/20260827135504_the-strange-case-of-dr-jekyll-and-mr-hyde/episodes/ep01/audio/lines/l25.wav"
LINE = "I know the other name already. Your tale has gone home."


def style_line(style: str, light: str) -> str:
    """The take's first detailed_description line, as the run would declare it for this book."""
    book = book_of(style)
    house_style.adopt("London, 1886", light)
    house_style.adopt_look(book_look.plan_look(book, ""))
    house_style.adopt_atmosphere(book_look.atmosphere(book))
    return house_style.live(None)


def take_prompt(style: str, shot: str) -> str:
    book, s = book_of(style), SHOTS[shot]
    sheets = s["sheets"]
    defs = [f"<Subject {k}> is {CAST[w][1]} in <Picture {k}>: {PHYS[w]}. <Picture {k}> defines this man alone; "
            f"each shot keeps the framing its own words describe." for k, w in enumerate(sheets, start=1)]
    panel = len(sheets) + 1
    keep = [f"<Subject {k}> (the man in [Shot 1]): partially_preserved - the face, hair, build and clothes of "
            f"<Picture {k}> carry into every shot that shows him; <Picture {k}> serves as a definition of the man "
            f"and each shot keeps the framing its own words describe." for k in range(1, len(sheets) + 1)]
    if shot == "a":
        audio_def = "<Audio 1> is the take's complete audio track and runs silent for its whole length."
        summary = ("[reference generation + audio reuse] One 5.17-second take of 1 shot at a street corner in a "
                   "sleeping London quarter at three in the morning. [Shot 1] runs from 00:00 to 00:05. The take "
                   "carries <Subject 1> through [Shot 1]. <Audio 1> is the complete audio track.")
        body = ("[Shot 1] From 00:00 to 00:05. The shot opens on a full shot of the little man (thick bushy black "
                "mutton-chop side-whiskers, soft black felt wideawake hat) striding at a hard walk over the child "
                "(fair plaits, knitted bonnet, grey pinafore) who lies fallen on the wet cobbles under the corner "
                "gas lamp. The camera is on the corner pavement at waist height, five yards off, a 35mm lens; "
                "yellow gaslight from the corner lamp on the RIGHT throws his long black shadow across her. At the "
                "first frame THE FOCUS OF THE PICTURE IS the little man at the LEFT of centre, his figure from the "
                "hat to the boots half the frame's height, the child at the CENTRE bottom looking up at him. Fog "
                "drifts between the shuttered houses behind them. The camera keeps a locked-off frame across the "
                "whole shot as the little man brings his boot down beyond her and walks on toward the RIGHT, from "
                "00:00 to 00:03. At 00:03 the child lifts one arm over her face and draws her knees in, and the "
                "little man keeps walking to the last frame of the shot. <Subject 1>'s mouth is closed from 00:00 "
                "to 00:05 while he sneers down at her.")
        sound = "Open air under the action; boots on wet cobbles, cloth, a child's breath."
    else:
        audio_def = ("<Audio 1> is the take's complete audio track: the one line spoken on camera at 00:00, over "
                     "silence for the rest of its length.")
        summary = ("[reference generation + audio reuse] One 5.17-second take of 1 shot in a warm Victorian study "
                   "at night. [Shot 1] runs from 00:00 to 00:05. The take carries <Subject 1> and <Subject 2> "
                   "through [Shot 1]. <Audio 1> carries that spoken line and is the complete audio track.")
        body = ("[Shot 1] From 00:00 to 00:05. The shot opens on a medium shot of <Subject 1> (thick iron-grey "
                "hair, broad clean-shaven face) and <Subject 2> (lank dusty sandy-grey hair, long gaunt unsmiling "
                "face) seated in two leather armchairs facing each other by the fire. The camera is across the "
                "hearthrug at seated head height, three yards from them, a 40mm lens; firelight from the LEFT lights "
                "both faces and throws the room behind them into deep shadow. At the first frame THE FOCUS OF THE "
                "PICTURE IS <Subject 2>'s face at the RIGHT third, <Subject 1> at the LEFT third, the fire at the "
                "LEFT edge. The camera keeps a locked-off frame across the whole shot as <Subject 2> leans forward "
                "in his chair. <Subject 2> (S1), on screen, gaunt, with a dry English voice at an even pace, says: "
                f"<d>[English] {LINE}</d> His mouth shapes every syllable as the line is heard and closes on the "
                "last word. <Subject 1> listens, his mouth closed, and lowers his eyes to the fire from 00:03 to "
                "the last frame of the shot.")
        sound = "Indoor air under the action; the fire crackling, cloth and the creak of leather."
    return "\n".join([
        "subject_definitions:", *defs, audio_def,
        take_refs.panel_definition(panel, book_look.panel_look(book)), "",
        "summary:", summary, "",
        "retention_analysis:", *keep,
        "<Audio 1>: fully_copy - <Audio 1> is reused 1:1 as the take's complete final audio track.",
        take_refs.panel_relation(panel, 1, pin=True), "",
        "detailed_description:", style_line(style, s["light"]), body, "",
        f"overall_soundscape: {sound}", "", "non_diegetic_music: N/A"])


def render_take(style: str, shot: str) -> Path:
    import takes_r2v as tr
    s = SHOTS[shot]
    refs = [HERE / style / f"{w}.png" for w in s["sheets"]]
    refs = take_refs.with_panel(refs, HERE / style / f"panel_{shot}.png", speaking=shot == "b")
    prompt = take_prompt(style, shot)
    seed = 81000 + zlib.crc32(f"{style}{shot}".encode()) % 1000
    template, inject = comfy.load_workflow(tr.BASE)
    values = {"prompt": prompt, "width": SIDE, "height": SIDE, "frames": FRAMES, "steps": 8, "seed": seed,
              "ref_image_size": tr.REF_IMAGE_SIZE, "filename_prefix": f"jekyll_chain_{style}_take_{shot}",
              "ref_image_1": comfy.stage_image(refs[0]), "ref_image_2": comfy.stage_image(refs[1])}
    graph = comfy.apply_inject(template, inject, values)
    base = next(k for k, n in graph.items() if n["class_type"] == "MiniMaxH3ReferenceToVideo")
    for k, path in enumerate(refs[2:], start=2):
        node = h3_anchors.next_id(graph)
        graph[node] = {"class_type": "LoadImage", "inputs": {"image": comfy.stage_image(path), "upload": "image"},
                       "_meta": {"title": f"ref_image_{k + 1}"}}
        graph[base]["inputs"][f"ref_images.ref_image_{k}"] = [node, 0]
    seconds = round(FRAMES / FPS, 3)
    lines = [(VOICE, 0.25)] if shot == "b" else []
    wav = tr.composite(lines, seconds, HERE / style / f"audio_{shot}.wav")
    graph = h3_anchors.anchored(graph, [], (comfy.stage_image(wav), 0))
    (HERE / style / f"take_{shot}.prompt.txt").write_text(prompt, encoding="utf-8")
    (HERE / style / f"take_{shot}.graph.json").write_text(json.dumps(graph, indent=1), encoding="utf-8")
    began = time.time()
    made = comfy.wait(comfy.submit(graph), timeout=7200)
    dest = HERE / style / f"take_{shot}.mp4"
    shutil.copy2(made[0], dest)
    log({"step": "take", "style": style, "shot": shot, "seed": seed, "seconds": round(time.time() - began, 1),
         "file": rel(dest), "workflow": tr.BASE, "refs": [rel(p) for p in refs], "frames": FRAMES, "size": SIDE})
    return dest


def frames(style: str, shot: str) -> list[Path]:
    """Frames at 0, 25, 50, 75 and 100 % of the take."""
    out = []
    for pct in (0, 25, 50, 75, 100):
        n = min(FRAMES - 1, round((FRAMES - 1) * pct / 100))
        dest = HERE / style / f"take_{shot}_f{pct:03d}.png"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(HERE / style / f"take_{shot}.mp4"), "-vf",
                        f"select=eq(n\\,{n})", "-frames:v", "1", str(dest)], check=True)
        out.append(dest)
    return out


def rel(p: Path) -> str:
    return Path(p).resolve().relative_to(ROOT).as_posix()


def log(row: dict) -> None:
    with open(HERE / "times.jsonl", "a", encoding="utf-8") as fh:
        fh.write(json.dumps(row) + "\n")
    print({k: row[k] for k in row if k in ("step", "style", "name", "shot", "seconds", "file")}, flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["refs", "panel", "take", "frames", "prompt"])
    ap.add_argument("style", choices=sorted(LOOKS))
    ap.add_argument("names", nargs="*")
    ap.add_argument("--salt", default="")
    args = ap.parse_args()
    if args.step == "refs":
        for name in args.names or list(REFS):
            draw_ref(args.style, name, args.salt)
    for shot in args.names if args.step != "refs" else []:
        if args.step == "panel":
            draw_panel(args.style, shot, args.salt)
        elif args.step == "take":
            render_take(args.style, shot)
        elif args.step == "frames":
            frames(args.style, shot)
        else:
            print(panel_prompt(args.style, shot)[0], "\n=====\n", take_prompt(args.style, shot))


if __name__ == "__main__":
    main()
