#!/usr/bin/env python
"""The episode's title card: one still from gpt-image, animated 4 s by H3.

`--local` draws the still on the owner's own model instead (free, no API):
the fallback for a day the paid API has no credits (ep13, 2026-09-17).

    uv run python scripts/episode/title.py <codex_id> <episode>

The series name is the main title ("SHERLOCK HOLMES"), the book the subtitle,
"EPISODE N" the tag (owner, 2026-09-10), so the card is made once PER
EPISODE under `library/<book>/title/epNN.png|mp4` and appended after the
last frame.  PAID (one gpt-image call per episode); the still and the take
are cached and never redrawn.
"""
from __future__ import annotations

import base64
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio.episode_home import episode_arg
from studio import approval, canvas, episode_home, image_spend as spend
from studio.comfy import run, stage_image
from studio.h3 import frames_for
from studio.llm import _load_dotenv

W, H = canvas.size("9:16")
ASPECT = "9:16"
"""Both rebound from the plan in `main`; the plan declares the aspect."""
SECONDS = 4.0
MODEL = "gpt-image-2.5-sunburst"
WORKFLOW = "video_minimax_h3_i2v_turbo"
SEED = 91000
SERIES = "Sherlock Holmes"


def still_prompt(series: str, title: str, number: int, palette: str,
                 shape: str = "vertical 9:16") -> str:
    """Holmes's own sentence made a picture: the scarlet thread running through
    the colourless skein.  The book's title, in one object, with no blood in it."""
    return (f'A cinematic title card poster, {shape}, photoreal 35 mm film still, 1881. '
            f'THE PICTURE: a loose skein of undyed wool, pale grey and colourless, lies coiled on '
            f'the dark leather top of a Victorian writing desk and fills the lower half of the '
            f'frame, lit cold and low from a tall window behind it. Running through the whole '
            f'length of that grey skein is ONE fine SCARLET THREAD, and its loose end is drawn up '
            f'and out of the coil toward the lens, lying bright across the leather; the scarlet '
            f'thread carries the only saturated colour in the picture. Beside the skein, in soft '
            f'focus, a magnifying glass on its side, a folded newspaper, an inkwell with a steel '
            f'pen, and a brass oil lamp with a low flame. Far behind the desk, out of focus and '
            f'small, the tall lean dark silhouette of a man in a long coat stands at the window '
            f'with the grey London fog pressing against the glass and rooftops beyond. The scarlet '
            f'thread and the lamp flame hold all the colour here; every other surface is cold '
            f'grey, soot-black, bone-white and worn leather brown. TYPOGRAPHY, the whole block '
            f'centred inside the middle of the frame, clear of the top and bottom eighths, and '
            f'with a wide clear margin inside the LEFT and RIGHT edges so that every letter stands '
            f'complete: the words "{series.upper()}" on one line, set large in an elegant Victorian '
            f'serif with fine hairlines, letterpress-crisp, pale ivory; directly beneath and half '
            f'that size, in the same serif, the words "{title.upper()}", with the word SCARLET in '
            f'the same deep scarlet as the thread; directly beneath that, at the same size as the '
            f'subtitle and widely letter-spaced, "EPISODE {number}". {palette} Fine grain, deep '
            f'shadow, a single cold key light from the window and the warm point of the lamp. The '
            f'thread, the skein and the lettering are the only sharp things. Clean plain frame '
            f'edges, lettering in these three lines only.')


def take_prompt(series: str, title: str, number: int) -> str:
    """One continuous action for four seconds: the thread draws out of the skein."""
    return ("For the target video, at 0.00 seconds into the target video, <Picture 1> (from "
            "[Shot 1]) is fully referenced.\n\n"
            "integrated_multimodal_description: [Shot 1] Photoreal cinematic title card, a cold "
            "study, grey daylight. Begin exactly from <Picture 1>. The camera holds one steady "
            "position for the whole shot. From 00:00 to 00:04 the single scarlet thread draws "
            "steadily out of the grey skein toward the lens in one continuous pull, its loose end "
            "travelling across the leather and the coil turning over once as it gives up the "
            "thread; the low lamp flame wavers; the fog behind the window drifts steadily from the "
            "left of frame to the right; the tall dark silhouette at the window keeps its place. "
            "The lettering "
            f'"{series.upper()}", "{title.upper()}" and "EPISODE {number}" stays exactly as drawn, '
            "still, sharp and legible, for every frame.\n\n"
            "overall_soundscape: A quiet room, a clock ticking somewhere, the small hiss of a lamp, "
            "muffled street sound far beyond the window.\n\n"
            "non_diegetic_music: N/A")


def previous_still(book: Path, number: int) -> Path | None:
    """The nearest earlier episode's title still, if the book has one.

    A series card is the same picture every week with one line changed, so the
    later card is an EDIT of the earlier one rather than a fresh generation:
    generated afresh it is a different skein, a different desk and a different
    lamp, and the run stops looking like one series.  The canvas may still
    differ -- episode 1 is 9:16 and episode 2 is 1:1 -- which is exactly why the
    earlier still is a reference and not a copy."""
    for earlier in range(number - 1, 0, -1):
        was = book / "title" / f"ep{earlier:02d}.png"
        if was.exists():
            return was
    return None


def draw(prompt: str, out: Path, approved: bool = False, size: str = "1024x1536",
         like: Path | None = None) -> Path:
    if out.exists():
        return out
    approval.require("title", f"one {MODEL} still for {out.stem}", 0.20, approved)
    _load_dotenv()
    from openai import OpenAI
    from PIL import Image

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    if like and like.exists():
        with open(like, "rb") as handle:
            result = client.images.edit(model=MODEL, image=[handle], prompt=prompt,
                                        size=size, quality="high", n=1)
    else:
        result = client.images.generate(model=MODEL, prompt=prompt, size=size, quality="high", n=1)
    out.parent.mkdir(parents=True, exist_ok=True)
    raw = out.with_name(out.stem + "_raw.png")
    raw.write_bytes(base64.b64decode(result.data[0].b64_json))
    spend.record(out.resolve().parents[1], MODEL, size, "high", 1, f"title still {out.stem}")
    image = Image.open(raw).convert("RGB")
    scale = max(W / image.width, H / image.height)
    resized = image.resize((round(image.width * scale), round(image.height * scale)), Image.LANCZOS)
    left, top = (resized.width - W) // 2, (resized.height - H) // 2
    resized.crop((left, top, left + W, top + H)).save(out)
    return out


LOCAL_WORKFLOW = "image_krea2_turbo_t2i"
LOCAL_SEED = 4400
"""MEASURED ep13 (2026-09-17): seeds 4100-4500 all set the three lines legibly;
4400 keeps the lamp warm and the word SCARLET red."""


def local_prompt(said: str) -> str:
    """The card's prompt with the red asked for twice: the local drawer draws the
    lettering well and drops the scarlet thread unless it is named as the only red."""
    return (said + " THE ONE THREAD RUNNING THROUGH THE GREY SKEIN IS BRIGHT PILLAR-BOX RED, vivid "
            "and saturated, and it trails off the desk toward the lens; it is the only red in the "
            "picture. In the subtitle line the single word SCARLET is lettered in that same bright "
            "red while the words A STUDY IN stay pale ivory.")


def render_local(prompt: str, prefix: str, seed: int) -> Path:
    """The one ComfyUI call. Injected in tests so no test touches the GPU."""
    written = run(LOCAL_WORKFLOW, {"prompt": prompt, "aspect_ratio": canvas.comfy_ratio(ASPECT),
                                   "megapixels": 1.0, "seed": seed, "steps": 8,
                                   "filename_prefix": f"ep_title_local_{seed}"})
    if not written:
        raise RuntimeError(f"{prefix} produced no image")
    return written[0]


def draw_local(prompt: str, out: Path, seed: int = LOCAL_SEED, render=render_local) -> Path:
    """The still from the LOCAL model, conformed to the episode's canvas.

    FREE, and no approval: it spends the owner's own GPU, like every other
    ComfyUI stage. The paid `draw` stays the default; this is what ships the
    episode when the API has no credits (ep13). The card is legible and on
    style; the scarlet thread is the one thing the local drawer will not draw."""
    if out.exists():
        return out
    from PIL import Image

    out.parent.mkdir(parents=True, exist_ok=True)
    raw = out.with_name(out.stem + "_raw.png")
    raw.write_bytes(Path(render(local_prompt(prompt), out.stem, seed)).read_bytes())
    image = Image.open(raw).convert("RGB")
    scale = max(W / image.width, H / image.height)
    resized = image.resize((round(image.width * scale), round(image.height * scale)), Image.LANCZOS)
    left, top = (resized.width - W) // 2, (resized.height - H) // 2
    resized.crop((left, top, left + W, top + H)).save(out)
    return out


def animate(still: Path, prompt: str, out: Path, seed: int, approved: bool = False) -> Path:
    if out.exists():
        return out
    approval.require("render", f"the title card's {SECONDS:.0f} s animation on ComfyUI", 0.0, approved)
    made = run(WORKFLOW, {"prompt": prompt, "width": W, "height": H,
                          "frames": frames_for(SECONDS + 0.25), "steps": 8, "seed": seed,
                          "start_image": stage_image(still), "filename_prefix": "ep_title"},
               timeout=1800)
    video = next(p for p in made if p.suffix in (".mp4", ".webm"))
    out.write_bytes(video.read_bytes())
    return out


def card_path(book: Path, number: int) -> Path:
    return book / "title" / f"ep{number:02d}.mp4"


def main(book_id: str, number: int, approved: bool = False, rendering: bool = False,
         local: bool = False) -> None:
    """The still and the animation are two spends: one is money, one is the
    owner's own GPU and queue.  Each is approved for itself, so an approval
    typed for the picture never starts a ComfyUI job."""
    book = episode_home.book_dir(book_id)
    global W, H, ASPECT
    ASPECT = episode_home.load_plan(book, number).aspect
    W, H = canvas.size(ASPECT)
    refs = episode_home.read_json(book / "refs" / "refs.json")
    play = episode_home.read_json(book / "screenplay" / "feature" / "screenplay.json")
    series, title = play.get("series", SERIES), play["title"]
    folder = book / "title"
    shape = canvas.words(ASPECT)
    like = previous_still(book, number)
    said = still_prompt(series, title, number, refs["palette"], shape)
    if like:
        said = (f"THE SAME TITLE CARD AS THE ATTACHED PICTURE, reproduced on a {shape} canvas: the same "
                f"skein of grey wool, the same single scarlet thread drawn out of it toward the lens, "
                f"the same dark leather desk, the same magnifying glass, folded newspaper, inkwell and "
                f"brass lamp, the same cold window light and the same tall dark silhouette at the "
                f"window. Keep the lettering in the same Victorian serif at the same three sizes, and "
                f"recompose it for the {shape} frame. THE ONLY CHANGE: the bottom line now reads "
                f'"EPISODE {number}". {said}')
    card = folder / f"ep{number:02d}.png"
    still = (draw_local(said, card) if local
             else draw(said, card, approved, canvas.still_size(ASPECT), like))
    prompt = take_prompt(series, title, number)
    (folder / f"ep{number:02d}.prompt.txt").write_text(
        still_prompt(series, title, number, refs["palette"]) + "\n\n" + prompt, encoding="utf-8")
    take = animate(still, prompt, card_path(book, number), SEED + number, rendering)
    print(f"title card -> {take}", flush=True)


def _cli(argv: list[str]) -> None:
    args = [a for a in argv[1:] if not a.startswith("--")]
    main(args[0], episode_arg(argv),
         approval.approved_for("title", argv), approval.approved_for("render", argv),
         "--local" in argv)


if __name__ == "__main__":
    _cli(sys.argv)
