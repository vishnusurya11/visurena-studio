"""The book's main title: the pure half (owner 2026-10-11; decision
architecture/decisions/2026-10-11_book_main_title_and_thumbnail.md).

7 s at 24 fps inside the book's square, in a 2.39 scope band: a cold open of
five segments cut from the book's own Shorts, black on the sting's hit, "THE
KEEPER'S LANTERN PRESENTS", then a text-free key-art plate with the title set
by code.  NO MODEL DRAWS A LETTER: the chapter cards' lettering failed again
and again (WHE THE WORLDS, sideways plates, quote marks, ep17 six seeds out of
six), and the OCR there reads the still, never the frames that ship.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from pydantic import BaseModel, Field

SCOPE = 2.39
FPS = 24
TIMELINE = {"cold_end": 60, "black_end": 70, "presents_end": 91, "total": 168}
"""Frames: cold open 0-2.50 s, black to 2.92, presents to 3.80, the hero to 7.00."""
COLD_FRAMES = (17, 14, 12, 10, 7)
"""The cold open's five cuts, each shorter than the last (60 frames in all)."""
HERO_TIER = "reasoning"


class KeyArt(BaseModel):
    """What the writer is asked for.  The title is in the schema only so a
    writer that returns one is visibly overruled (`spec` never reads it)."""
    title: str = ""
    hero: str = Field(description="the text-free key-art picture: the book's one big image")
    thumb: str = Field(description="the same image, subject on the right third, dark empty space on the left")
    sting: str = Field(description="ACE-Step tags for a 7 s instrumental main-title sting")


class BookTitleSpec(BaseModel):
    title: str
    author: str
    hero: str
    thumb: str
    sting: str


def band_box(side: int) -> tuple[int, int, int, int]:
    """(x, y, w, h) of the scope band centred in a `side` square, h even."""
    h = 2 * round(side / SCOPE / 2)
    return 0, (side - h) // 2, side, h


PHOTOREAL = "a photoreal live-action film still, shot on 35 mm film, natural light and real textures"


def look_words(look: str) -> str:
    """The book's own look in words: its declared look, else photoreal live action."""
    return look.strip() or PHOTOREAL


def writer_prompt(name: str, author: str, synopsis: str, *, look: str) -> str:
    """The key art is asked for in the BOOK'S look: 'painted' drew Scarlet --
    a photoreal series -- in WotW's brushwork (owner, 2026-10-11)."""
    return (f"Main title for a screen adaptation of {name} by {author}.\n{synopsis}\n\n"
            f"The series looks like this, and every picture must too: {look_words(look)}.\n"
            "hero: ONE key-art picture in that look, the book's most famous image, wide, cinematic, "
            "with NO text, letters, signs or writing anywhere. thumb: the same moment in that look, "
            "showing at most ONE person, the subject on the right third and dark empty space on the "
            "left. sting: tags for a short instrumental orchestral sting with one big hit, no vocals.")


SHAPES = {"wide": ((1280, 544), "21:9 (Ultrawide)"), "thumb": ((1280, 720), "16:9 (Widescreen)"),
          "square": ((1024, 1024), "1:1 (Square)")}


def plate_request(look: str, *, wide: bool = False, shape: str = "") -> dict:
    """Which local renderer draws the plate, and how: a photoreal book on Krea2
    without the art-style LoRA, a stylised one on the house look (Krea2 + LoRA)."""
    size, aspect = SHAPES[shape or ("wide" if wide else "thumb")]
    if look.strip():
        from studio.refs_pack import STYLE_LEAD
        return {"workflow": "image_krea2_cinematic_2x", "lead": STYLE_LEAD,
                "values": {"width": size[0], "height": size[1]}}
    return {"workflow": "image_krea2_turbo_t2i", "lead": f"{PHOTOREAL[0].upper()}{PHOTOREAL[1:]}, of ",
            "values": {"aspect_ratio": aspect, "megapixels": 2, "enable_lora": False, "refine_prompt": False}}


def look_of(book: Path) -> str:
    """The series' declared look (episode 1's plan); empty is photoreal live action."""
    from studio import episode_home
    path = Path(episode_home.home(book, 1)) / "plan.json"
    return (episode_home.read_json(path).get("look") or "") if path.exists() else ""


def lead_for(book: Path, look: str) -> str:
    """The words a plate opens with: the house look, or a photoreal book's own refs words."""
    from studio import episode_home
    ask = plate_request(look)
    refs = Path(book) / "refs" / "refs.json"
    return photoreal_lead(episode_home.read_json(refs)) if not look.strip() and refs.exists() else ask["lead"]


def spec(book: dict, *, synopsis: str, ask, look: str = "") -> BookTitleSpec:
    """The words from the book's own data; only the pictures and sound are written."""
    name = book.get("display_title") or book["title"]
    try:
        art = ask(HERO_TIER, writer_prompt(name, book["author"], synopsis, look=look), KeyArt)
    except Exception as why:                       # the writer is down: never wait on it
        print(f"  spec: the writer failed ({str(why)[:100]}); the book's own logline", flush=True)
        art = fallback_art(name, synopsis)
    return BookTitleSpec(title=name, author=book["author"], hero=art.hero, thumb=art.thumb, sting=art.sting)


def fit_lines(text: str, font_path: Path, *, max_w: int, start_px: int, min_px: int,
              tracking: float = 0.0) -> tuple[list[str], int]:
    """The title in capitals on one line, else two, at the largest size that
    fits -- at its WIDEST letter spacing (`tracking` em), so it never runs off."""
    from PIL import ImageFont
    words = text.upper().split()
    splits = [[" ".join(words)]] + [[" ".join(words[:k]), " ".join(words[k:])] for k in range(1, len(words))]
    for px in range(start_px, min_px - 1, -4):
        font = ImageFont.truetype(str(font_path), px)
        wide = lambda line: font.getlength(line) + tracking * px * (len(line) - 1)
        fits = [s for s in splits if all(wide(line) <= max_w for line in s)]
        if fits:
            return min(fits, key=lambda s: (len(s), max(font.getlength(x) for x in s))), px
    raise ValueError(f"{text!r} does not fit {max_w}px even at {min_px}px")


def glyphs_missing(text: str, font_path: Path) -> list[str]:
    """Characters of `text` the font has no glyph for."""
    from fontTools.ttLib import TTFont
    cmap = TTFont(str(font_path)).getBestCmap()
    return sorted({c for c in text if not c.isspace() and ord(c) not in cmap})


TRACK_FROM, TRACK_TO = 0.4, 0.12


def tracking_em(progress: float) -> float:
    """Letter spacing in em: wide closing to set, easing out."""
    p = min(max(progress, 0.0), 1.0)
    return TRACK_FROM - (TRACK_FROM - TRACK_TO) * (1 - (1 - p) ** 3)


def _part(c: dict, episodes: int, n: int) -> int:
    return (c["episode"] - 1) * n // episodes


def shortlist(cands: list[dict], *, episodes: int, n: int, k: int) -> list[dict]:
    """The `k` sharpest candidates of each n-th of the book: the few a reader scores."""
    out = []
    for part in range(n):
        mine = [c for c in cands if _part(c, episodes, n) == part]
        out += sorted(mine, key=lambda c: (-c["sharp"], c["episode"], c["start_s"]))[:k]
    return out


def pick_segments(cands: list[dict], *, episodes: int, n: int, clean) -> list[dict]:
    """One segment per n-th of the book: the most cinematic (`drama`, read by
    the VLM), then the sharpest, that `clean` passes.  The sharpest alone
    picked a garden gate, a sawmill and a railway (WotW, 2026-10-11)."""
    picks = []
    for part in range(n):
        mine = [c for c in cands if _part(c, episodes, n) == part]
        for c in sorted(mine, key=lambda c: (-c.get("drama", 0), -c["sharp"], c["episode"], c["start_s"])):
            if clean(c):
                picks.append(c)
                break
    return picks


def segment_window(shot: dict, *, frames: int, fps: int) -> tuple[float, float]:
    """`frames` from the middle of the shot, in seconds."""
    mid, half = (shot["start_s"] + shot["end_s"]) / 2, frames / fps / 2
    return mid - half, mid + half


def sting_hit(sound: np.ndarray, rate: int) -> float:
    """The strongest rise in loudness, in seconds: where the sting hits."""
    hop = max(1, rate // 50)
    mono = sound if sound.ndim == 1 else sound.mean(axis=1)
    usable = len(mono) // hop * hop
    rms = np.sqrt((mono[:usable].reshape(-1, hop) ** 2).mean(axis=1))
    return float(np.argmax(np.diff(rms)) + 1) * hop / rate


def riser(rate: int, at_s: float, total_s: float):
    """Filtered noise and a low drone swelling into `at_s`, silent after it."""
    t = np.arange(int(total_s * rate)) / rate
    swell = np.clip(t / at_s, 0, 1) ** 3 * (t < at_s)
    noise = np.convolve(np.random.default_rng(7).standard_normal(t.size), np.ones(8) / 8, mode="same")
    return (noise * 0.18 + np.sin(2 * np.pi * 55 * t) * 0.25) * swell


def align_sting(sound: np.ndarray, rate: int, *, hit_s: float, at_s: float, total_s: float) -> np.ndarray:
    """The sting laid so its hit lands at `at_s`, a riser under whatever comes
    before it, `total_s` long, stereo.  ACE-Step's stings open ON the hit
    (0.68 s, WotW): shifting alone left the cold open silent."""
    stereo = sound if sound.ndim == 2 else np.stack([sound, sound], axis=1)
    out = np.zeros((int(total_s * rate), 2))
    shift = int(round((at_s - hit_s) * rate))
    src = stereo[max(0, -shift):]
    dst = max(0, shift)
    n = min(len(src), len(out) - dst)
    out[dst:dst + n] = src[:n]
    lead = riser(rate, at_s, total_s)
    peak = max(np.abs(out).max(), 1e-9)
    return out + lead[:, None] * peak * 0.6


def contrast_ratio(fg: float, bg: float) -> float:
    """WCAG contrast of two relative luminances."""
    hi, lo = max(fg, bg), min(fg, bg)
    return (hi + 0.05) / (lo + 0.05)


COLD_SIZES = ("wide", "insert")
MIN_SHOT_S = 1.5


def candidates(episode: int, plan: dict, placed: dict) -> list[dict]:
    """Faceless wides and inserts the cut placed, long enough to cut from:
    no face means no identity to drift, and the place reads at a glance."""
    shots = {s["index"]: s for s in plan.get("shots") or []}
    omitted = set(plan.get("omit") or [])
    out = []
    for row in placed.get("shots") or []:
        shot = shots.get(row["index"], {})
        if row["index"] in omitted or shot.get("size") not in COLD_SIZES or shot.get("faces"):
            continue
        if row["t_end"] - row["t_start"] >= MIN_SHOT_S:
            out.append({"episode": episode, "shot": row["index"], "start_s": row["t_start"], "end_s": row["t_end"]})
    return out


PRESENTS = "THE KEEPER'S LANTERN PRESENTS"
SCRIM = 110
"""The dark band behind the title; 170 buried the key art (WotW, contrast 14:1)."""
WHITE = (236, 240, 245)
"""Cold white: the chapter cards are warm ivory serif."""


def _ramp(n: int, a: int, b: int) -> float:
    return min(max((n - a) / max(b - a, 1), 0.0), 1.0)


def _tracked(draw, xy_centre: tuple[int, int], text: str, font, em: float, alpha: int) -> int:
    """Draw `text` centred on xy with `em` letter spacing; returns its width."""
    gap = em * font.size
    widths = [font.getlength(c) for c in text]
    total = sum(widths) + gap * (len(text) - 1)
    x, y = xy_centre[0] - total / 2, xy_centre[1]
    for c, w in zip(text, widths):
        draw.text((x, y), c, font=font, fill=WHITE + (alpha,), anchor="lm")
        x += w + gap
    return int(total)


def _scrim(img, alpha: int) -> None:
    """A dark band across the middle third, darkest at the centre line."""
    from PIL import Image
    w, h = img.size
    column = Image.linear_gradient("L").resize((1, h // 2))
    ramp = Image.new("L", (1, h))
    ramp.paste(column, (0, 0))
    ramp.paste(column.transpose(Image.FLIP_TOP_BOTTOM), (0, h // 2))
    shade = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    shade.putalpha(ramp.resize((w, h)).point(lambda v: v * alpha // 255))
    img.alpha_composite(shade)


def overlay_frame(spec: BookTitleSpec, n: int, *, width: int, height: int, font: Path):
    """The type over frame `n` of the band: nothing over the cold open, the
    presents line over the black, the title tracking in over the hero."""
    from PIL import Image, ImageDraw, ImageFont
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    t = TIMELINE
    if t["black_end"] <= n < t["presents_end"]:
        fade = min(_ramp(n, t["black_end"], t["black_end"] + 6), 1 - _ramp(n, t["presents_end"] - 6, t["presents_end"]))
        small = ImageFont.truetype(str(font), max(12, height // 16))
        _tracked(ImageDraw.Draw(img), (width // 2, height // 2), PRESENTS, small, 0.35, int(255 * fade))
    elif n >= t["presents_end"]:
        _hero_type(img, spec, n, font)
    return img


def _hero_type(img, spec: BookTitleSpec, n: int, font: Path) -> None:
    from PIL import ImageDraw, ImageFont
    w, h = img.size
    t = TIMELINE
    _scrim(img, int(SCRIM * _ramp(n, t["presents_end"], t["presents_end"] + 12)))
    lines, px = hero_layout(spec.title, font, width=w, height=h)
    big, draw = ImageFont.truetype(str(font), px), ImageDraw.Draw(img)
    em = tracking_em(_ramp(n, t["presents_end"], t["presents_end"] + 60))
    alpha = int(255 * _ramp(n, t["presents_end"], t["presents_end"] + 24))
    top = h // 2 - (len(lines) - 1) * px // 2 - px // 6
    for k, line in enumerate(lines):
        _tracked(draw, (w // 2, top + k * px), line, big, em, alpha)
    by = int(255 * _ramp(n, t["presents_end"] + 30, t["presents_end"] + 48))
    y = top + (len(lines) - 1) * px + int(px * 0.62)
    draw.line([(w * 0.40, y), (w * 0.60, y)], fill=WHITE + (by,), width=max(1, h // 300))
    small = ImageFont.truetype(str(font), max(10, px // 4))
    _tracked(draw, (w // 2, y + px // 4), spec.author.upper(), small, 0.3, by)


def thumbnail(plate, spec: BookTitleSpec, *, episodes: int, font: Path):
    """1280x720: the plate, a dark wash on the left, the title set on it."""
    from PIL import Image, ImageDraw, ImageFont
    w, h = 1280, 720
    scale = max(w / plate.width, h / plate.height)
    pic = plate.convert("RGB").resize((round(plate.width * scale), round(plate.height * scale)))
    pic = pic.crop(((pic.width - w) // 2, (pic.height - h) // 2, (pic.width - w) // 2 + w, (pic.height - h) // 2 + h))
    wash = Image.linear_gradient("L").rotate(90, expand=True).resize((w, h)).point(lambda v: min(255, v * 230 // 180))
    pic.paste(Image.new("RGB", (w, h), (0, 0, 0)), (0, 0), wash.transpose(Image.FLIP_LEFT_RIGHT).point(lambda v: max(0, v - 25)))
    draw = ImageDraw.Draw(pic)
    lines, px = fit_lines(spec.title, font, max_w=560, start_px=170, min_px=40)
    y = h // 2 - len(lines) * px // 2 - 30
    for k, line in enumerate(lines):
        draw.text((60, y + k * px), line, font=ImageFont.truetype(str(font), px), fill=(255, 255, 255))
    small = ImageFont.truetype(str(font), 44)
    draw.text((62, y + len(lines) * px + 16), f"FULL ADAPTATION · {episodes} EPISODES", font=small, fill=(235, 196, 120))
    draw.text((62, y + len(lines) * px + 70), spec.author.upper(), font=small, fill=(200, 205, 212))
    return pic


def stream_signature(ffmpeg_info: str) -> tuple[str, ...]:
    """The stream lines of `ffmpeg -i`, without bitrates, durations or ids:
    what must be equal for the concat demuxer to join by stream copy."""
    import re
    out = []
    for line in ffmpeg_info.splitlines():
        if "Stream #" in line and (": Video:" in line or ": Audio:" in line):
            line = re.sub(r"Stream #\S+ ", "", line.strip())
            line = line.replace(" [SAR 1:1 DAR 1:1]", "")                  # square pixels, tagged or not
            out.append(re.sub(r",? ?\d+ kb/s|\(default\)", "", line).strip())
    return tuple(out)


READ_ASK = ("Transcribe every word of lettering, signage or writing visible in this image, exactly "
            "as spelled. If there is none, answer exactly: NONE")
NOTHING = ("NONE", "NO LETTERING", "NO TEXT", "THERE IS NO")


def has_lettering(said: str) -> bool:
    """Whether the reader found any writing (a plate or a cold-open frame
    with lettering is refused: only code sets type in the main title)."""
    from studio.series_title import transcription
    text = " ".join(transcription(said).upper().split())
    if not any(ch.isalnum() for ch in text):
        return False
    return not any(text.startswith(n) for n in NOTHING)


DRAMA_ASK = ("Score this frame from 0 to 10 as the opening shot of a movie trailer: spectacle, danger, "
             "fire, machines, crowds in flight and striking light score high; empty rooms, fences, gates, "
             "roads and plain landscapes score low. Answer with the number only.")


def drama_score(said: str) -> int:
    """The reader's first number, 0-10; nothing readable is 0."""
    import re
    found = re.search(r"\d+", said or "")
    return min(int(found.group()), 10) if found else 0


def hero_layout(title: str, font: Path, *, width: int, height: int) -> tuple[list[str], int]:
    """The title's lines and size over the hero: what is drawn and what the judge reads."""
    return fit_lines(title, font, max_w=int(width * 0.9), start_px=int(height * 0.30), min_px=12, tracking=TRACK_FROM)


def square_source(ffmpeg_info: str) -> bool:
    """Whether the video's picture is square (a portrait Short pads into the band)."""
    import re
    found = re.search(r"Video:.*?, (\d{2,5})x(\d{2,5})", ffmpeg_info)
    return bool(found) and found.group(1) == found.group(2)


PEOPLE_ASK = ("Describe each person in this image on its own line, naming what they actually wear, in the form "
              "HAT; CLOTHES; HAIR -- for example: top hat; grey frock coat; white hair. Use 'no hat' when "
              "bare-headed. If there are no people, answer NONE.")
"""A worked example: given only 'hat; coat; hair' the reader echoed the template
for every person, and every plate read as doubled."""


def doubled(said: str) -> bool:
    """Two people listed with the same hat and clothes: one character copied
    (Scarlet's thumbnail, 2026-10-11: Watson drawn as a second Holmes)."""
    from studio.series_title import transcription
    rows = [";".join(p.strip(" \t[]\"',") for p in line.lower().split(";")[:2])   # JSON debris off
            for line in transcription(said or "").splitlines() if ";" in line]
    return len(rows) != len(set(rows))


def banner_thumbnail(plate, spec: BookTitleSpec, *, episodes: int, font: Path):
    """1280x720: the whole wide plate on top, the title in a dark band under it --
    for when no thumbnail plate passes and the hero plate (already vetted) must serve."""
    from PIL import Image, ImageDraw, ImageFont
    w, h = 1280, 720
    pic = Image.new("RGB", (w, h), (8, 9, 12))
    top = plate.convert("RGB").resize((w, round(plate.height * w / plate.width)))
    pic.paste(top, (0, 0))
    band = top.height
    fade = Image.linear_gradient("L").resize((w, 60))
    pic.paste(Image.new("RGB", (w, 60), (8, 9, 12)), (0, band - 60), fade)
    draw = ImageDraw.Draw(pic)
    lines, px = fit_lines(spec.title, font, max_w=1180, start_px=min(110, h - band - 40), min_px=30)
    draw.text((w // 2, band + 8), lines[0] if len(lines) == 1 else " ".join(lines), font=ImageFont.truetype(str(font), px),
              fill=(255, 255, 255), anchor="ma")
    small = ImageFont.truetype(str(font), 30)
    draw.text((w // 2, h - 12), f"FULL ADAPTATION · {episodes} EPISODES  ·  {spec.author.upper()}", font=small,
              fill=(235, 196, 120), anchor="md")
    return pic


def photoreal_lead(refs: dict) -> str:
    """A photoreal book's own picture lead: its location sheets' opening words up
    to and including its palette -- what the series was drawn with -- else the
    generic line."""
    palette = (refs.get("palette") or "").strip()
    for row in refs.get("refs") or []:
        prompt = row.get("prompt") or ""
        if row.get("kind") == "location" and palette and palette in prompt:
            return prompt[:prompt.index(palette) + len(palette)].strip() + " "
    return f"{PHOTOREAL[0].upper()}{PHOTOREAL[1:]}, of "


def fallback_art(name: str, synopsis: str) -> KeyArt:
    """The key art from the book's own logline when the writer cannot be reached
    (the Claude SDK hung at start-up on every call, 2026-10-11)."""
    moment = synopsis.strip().rstrip(".") or name
    return KeyArt(hero=f"the defining image of {name}: {moment}. Wide, cinematic, dramatic light, no text.",
                  thumb=f"one person only, the main character of {name}, on the right third of the frame; "
                        f"{moment}; the left two-thirds dark and empty. No text.",
                  sting="instrumental orchestral main-title sting, no vocals, low strings swelling into "
                        "one deep timpani and brass hit, reverberant decay")
