"""Jekyll gothic-anime styles: named gothic anime looks on an Illustrious (SDXL) base, same 3 subjects, fixed seeds.

uv run python docs/audit/2026-10-13_jekyll_gothic_anime/render.py STYLE [subject ...] [--salt S]
Writes <STYLE>/<subject>.png beside this file; appends each render's seconds to times.jsonl.
Seed = crc32("jekyll_gothic/<subject><salt>"), identical across styles. Bodies follow analysis/heads.json.
"""
from __future__ import annotations

import argparse
import json
import shutil
import time
import zlib
from pathlib import Path

from studio import comfy

HERE = Path(__file__).resolve().parent
WORKFLOW = "image_sdxl_t2i_2lora_hires_visurena"
BASES = {"noob": "NoobAI-XL-v1.1.safetensors", "wai": "waiIllustriousSDXL_v170.safetensors"}
QUALITY = "masterpiece, best quality, amazing quality, very aesthetic, absurdres, "
NEG = ("nsfw, nude, lowres, worst quality, bad quality, bad anatomy, bad hands, extra fingers, text, watermark, "
       "signature, artist name, logo, letters, speech bubble, sign, signage, road markings, modern, car, chibi, "
       "skyscraper, modern city, city lights, "
       "moe, cute, kawaii, big eyes, sparkling eyes, pastel colors, bright colors, 3d, photo, multiple views, ")
KAWAJIRI = "gothic_anime\\kawajiri_city_trilogy_xl_v1r64.safetensors"
KOJIMA = "gothic_anime\\ayami_kojima_castlevania_pony.safetensors"
MONONOKE = "gothic_anime\\mononoke_anime_style_illustrious.safetensors"
# name -> (style lead tags, LoRA list [(file, strength)], extra negative)
STYLES = {
    "VHD": ("vampire hunter d: bloodlust, 2000s (style), madhouse, yoshiaki kawajiri, anime screencap, "
            "elegant gothic character design, long elegant face, fine thin linework, painted gothic background, "
            "cold moonlight, blue-black and violet palette, ", [(KAWAJIRI, 0.45)], ""),
    "KAW": ("wicked city (1987 ova), yoshiaki kawajiri, 1980s (style), retro artstyle, ova screencap, "
            "hard angular faces, heavy black shadows, high contrast chiaroscuro, red and black palette, "
            "airbrushed night background, ", [(KAWAJIRI, 0.9)], ""),
    "HEL": ("hellsing ultimate ova, hirano kouta (style), anime screencap, sharp angular linework, "
            "jagged black ink shadows, insane grin, red and black palette, blood-red highlights, "
            "dark gothic atmosphere, ", [], ""),
    "BER": ("kenpuu denki berserk (1997 anime), berserk, miura kentarou, 1990s (style), retro artstyle, "
            "anime screencap, flat cel shading, heavy outlines, muted earthy palette, grim dark fantasy, ", [], ""),
    "KUR": ("kuroshitsuji, toboso yana (style), black butler anime screencap, victorian london, elegant thin "
            "linework, gothic victorian fashion, dark bluish palette, ornate gaslit background, ", [], ""),
    "CAS": ("kojima ayami, castlevania, official art, concept art, traditional media, painterly gothic "
            "illustration, baroque, sepia and crimson oil-paint shading, fine hatching, ", [(KOJIMA, 0.8)], ""),
    "MON": ("mononoke (anime), ayakashi japanese classic horror, ukiyo-e, washi paper texture, flat color, "
            "woodblock print, bold decorative outlines, psychedelic gothic patterns, limited palette, victorian english clothes, ", [(MONONOKE, 0.6)], "kimono, japanese clothes, straw hat, kasa, conical hat, bald, old man, "),
    "AMA": ("amano yoshitaka (style), vampire hunter d novel illustration, watercolor, ink wash, ethereal "
            "flowing lines, pale washed colors, decadent gothic art nouveau, traditional media, ", [], ""),
    "MOR": ("yuukoku no moriarty, miyoshi hikaru (style), production i.g, anime screencap, victorian england, "
            "refined slender bishounen character design, clean thin linework, soft cel shading, muted teal and "
            "amber palette, elegant gaslit london, ", [], ""),
    "GAN": ("gankutsuou, gonzo, mahiro maeda, (patterned clothing:1.5), (patterned hair:1.3), (gold and indigo floral damask pattern filling the coat and hat:1.4), flat static textile texture, klimt (style), stained glass, collage, ornate, decadent baroque, jewel tones, ", [], ""),
    "DN": ("death note, (obata takeshi:1.3), official art, manga illustration, realistic proportions, sharp detailed linework, fine crosshatching, gaunt angular face, dramatic chiaroscuro, desaturated green-grey palette, cold gothic, ", [], "cartoon, flat color, "),
    "ITO": ("itou junji (style), horror (theme), manga, monochrome, greyscale, dense ink hatching, cross-hatching, "
            "screentone, fine pen lines, uncanny, unsettling stare, black and white ink illustration, ", [],
            "color, colorful, red, "),
    "PAN": ("pandora hearts, mochizuki jun (style), xebec, gothic victorian fashion, ornate lace and ribbons, "
            "anime screencap, delicate linework, dark fairytale, crimson and black palette, clock motif, ", [], ""),
    "DGM": ("d.gray-man, hoshino katsura (style), gothic, black and white and red, sharp elegant linework, "
            "dark victorian fantasy, dramatic shadows, ", [], ""),
    "TRI": ("trigun stampede, orange (studio), 3d cel-shaded anime, toon shading, crisp rim light, bold "
            "outlines, cinematic lighting, ", [], ""),
}
SUBJECTS = {
    "hyde": ("1boy, solo, mr edward hyde, sinister young man, short, small slight build, narrow shoulders, pale skin, "
             "cold sneer, smirk, evil smile, thin lips, face visible, (short messy black hair:1.2), (facial hair:1.2), (long black "
             "sideburns:1.3), (bushy black mutton chops on both cheeks:1.2), no mustache, (black wide-brimmed hat:1.3), soft black felt hat, low flat crown, floppy brim, "
             "ill-fitting black coat, hunched, gnarled hands, cowboy shot, looking at viewer, standing, victorian london street, night, "
             "thick fog, gas lamp, wet cobblestones",
             "top hat, bowler hat, mustache, tall, muscular, cape, d (vampire hunter d), shadowed face, peaked cap, military hat, cap, fedora hatband, long hair, blood, gore, weapon, holding, witch hat, pointy hat, conical hat, cowboy hat, "),
    "jekyll": ("1boy, solo, dr henry jekyll, mature male, 50 years old, tall, large heavy-set build, handsome, "
               "broad smooth face, clean-shaven, thick iron-grey hair, grey hair, brushed back hair, black silk top "
               "hat, black frock coat, waistcoat, respectable victorian gentleman, calm, composed, full body, "
               "cowboy shot, looking at viewer, standing, victorian london street, night, fog, gas lamp, cobblestones",
               "young, beard, mustache, facial hair, thin, "),
    "ch1": ("1boy, 1girl, mr edward hyde, sinister young man, small, pale, sneer, black hair, black mutton chops, "
            "(black wide-brimmed hat:1.2), soft felt hat, floppy brim, black coat, standing over a fallen little girl, "
            "child, 9 years old, grey pinafore, knitted bonnet, blonde braids, sitting on ground, looking up, "
            "frightened, his shadow falls over her, lit from below by a gas lamp, deserted street corner, "
            "3 a.m., black winter night, thick fog, shuttered shops, wet cobblestones, menace, wide shot",
            "top hat, mustache, crowd, multiple boys, "),
}


def render(style: str, name: str, salt: str, base: str) -> None:
    lead, loras, neg_extra = STYLES[style]
    body, neg_subject = SUBJECTS[name]
    seed = zlib.crc32(f"jekyll_gothic/{name}{salt}".encode())
    values = {"prompt": QUALITY + lead + body, "negative_prompt": NEG + neg_subject + neg_extra,
              "seed": seed, "hires_seed": seed, "hires_denoise": 0.55, "ckpt_name": BASES[base], "filename_prefix": f"jekyll_gothic/{style}_{name}"}
    for i, (lora, weight) in enumerate(loras, start=1):
        values.update({f"lora{i}": lora, f"lora{i}_model": weight, f"lora{i}_clip": weight})
    start = time.time()
    out = comfy.run(WORKFLOW, values)
    seconds = round(time.time() - start, 1)
    dest = HERE / (style if base == "noob" else f"{style}_{base}") / f"{name}{'_s' + salt if salt else ''}.png"
    dest.parent.mkdir(exist_ok=True)
    shutil.copy2(out[0], dest)
    row = {"style": style, "base": BASES[base], "workflow": WORKFLOW, "subject": name, "seed": seed, "seconds": seconds,
           "file": f"{style}/{dest.name}", "loras": loras, "hires_denoise": values["hires_denoise"], "prompt": values["prompt"],
           "negative": values["negative_prompt"]}
    with open(HERE / "times.jsonl", "a", encoding="utf-8") as fh:
        fh.write(json.dumps(row) + "\n")
    print(style, name, seed, seconds, flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("style", choices=sorted(STYLES))
    ap.add_argument("subjects", nargs="*")
    ap.add_argument("--salt", default="")
    ap.add_argument("--base", choices=sorted(BASES), default="noob")
    args = ap.parse_args()
    for name in args.subjects or list(SUBJECTS):
        render(args.style, name, args.salt, args.base)


if __name__ == "__main__":
    main()
