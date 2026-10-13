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
       "signature, artist name, logo, letters, speech bubble, sign, signage, road markings, hazard stripes, yellow lines, modern, car, chibi, "
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
            "jagged black ink shadows, red and black palette, crimson shadows, "
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
    "TRI": ("orange (studio), trigun stampede (style), (3d cel-shaded anime:1.1), cgi anime, toon shading, crisp rim light, bold "
            "outlines, cinematic lighting, ", [], "sketch, painterly, "),
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
# Examples pass (owner shortlist 2026-10-13: HEL, VHD, MON, AMA, TRI): six pictures per style from heads.json.
_HYDE = ("mr edward hyde, sinister young man, 25 years old, young face, small slight build, short, narrow shoulders, "
         "pale skin, cold sneer, thin lips, (short cropped messy black hair:1.3), (bushy black mutton chops:1.2), "
         "(long black sideburns:1.2), no mustache, (soft black felt wideawake hat:1.3), low flat crown, wide floppy brim, "
         "ill-fitting black coat")
_JEKYLL = ("dr henry jekyll, mature male, 50 years old, tall, large heavy-set build, broad shoulders, handsome, kindly "
           "face, gentle smile, broad smooth face, (clean-shaven:1.2), thick iron-grey hair, brushed back grey hair, "
           "black frock coat, waistcoat, white shirt, cravat")
_UTTERSON = ("mr utterson, lawyer, 40 years old, lean, tall and long, bony, narrow-chested, long gaunt rugged face, dour, "
             "unsmiling, serious, (clean-shaven:1.2), lank sandy-blond hair to the collar, dusty fair hair, black overcoat")
_HYDE_NEG = ("(long hair:1.4), medium hair, ponytail, old man, middle-aged, wrinkles, top hat, bowler hat, cap, peaked cap, "
             "military hat, witch hat, pointy hat, cowboy hat, conical hat, mustache, beard, tall, muscular, cape, "
             "d (vampire hunter d), ")
_MANY = "multiple boys, 3boys, crowd, clone, twins, duplicate, "
SUBJECTS.update({
    "ex_hyde": ("1boy, solo, " + _HYDE + ", hunched, gnarled hands, cowboy shot, looking at viewer, standing, "
                "victorian london street, night, thick fog, gas lamp, wet cobblestones",
                _HYDE_NEG + "shadowed face, blood, gore, weapon, holding, "),
    "ex_jekyll": ("1boy, solo, " + _JEKYLL + ", (black silk top hat:1.2), respectable victorian gentleman, calm, "
                  "cowboy shot, looking at viewer, standing, victorian london street, evening, fog, gas lamp, cobblestones",
                  "young, beard, mustache, facial hair, sideburns, thin, skinny, long hair, bowler hat, wide-brimmed hat, "
                  "evil, sneer, grin, fangs, red eyes, red hair, "),
    "ex_utterson": ("1boy, solo, " + _UTTERSON + ", (black bowler hat:1.3), round hard crown, short curled brim, "
                    "cowboy shot, looking at viewer, standing, victorian london street, day, grey fog, cobblestones",
                    "top hat, wide-brimmed hat, smile, grin, fangs, red hair, beard, mustache, facial hair, old man, grey hair, fat, black hair, "),
    "ex_trample": ("1boy, 1girl, " + _HYDE + ", striding over a fallen (little girl:1.3), walking past, his foot over her, "
                   "female child, 9 years old, small girl lying on the ground, grey pinafore dress, black boots, blonde braids, "
                   "knitted bonnet, frightened, crying, his long shadow falls over her, lit from below by a gas lamp, "
                   "deserted street corner, 3 a.m., black winter night, thick fog, shuttered shops, wet cobblestones, "
                   "menace, full body, wide shot",
                   _HYDE_NEG + _MANY + "2girls, male child, boy lying, blood, gore, injury, weapon, gun, cane, skull, nsfw, "),
    "ex_door": ("outdoors, foggy london by-street, daytime, 2boys, two victorian gentlemen in overcoats walking along "
                "the pavement, from side, full body, wide shot, beside them a (closed old door:1.2) set in a "
                "(tall blank windowless grimy wall:1.3), blistered peeling discoloured paint on the door, sinister, neglected, "
                "the lean man with sandy hair wears a (black bowler hat:1.2), the broad man with brown hair wears a "
                "light-brown top hat, grey fog, cobblestones, muted light",
                _MANY + "open door, doorway, indoors, interior, hallway, corridor, room, 1girl, woman, female, dress, "
                "window, windows, barred window, sign, shop sign, (text:1.3), number, (blood:1.3), night, "),
    "ex_study": ("2boys, two victorian gentlemen sitting in armchairs by a fireplace, talking, warm victorian study, "
                 "firelight, bookshelves, wood panelling, glasses of wine, warm amber light, interior, "
                 "left: " + _JEKYLL + ", right: " + _UTTERSON + ", no hats, wide shot",
                 _MANY + "1girl, woman, hat, top hat, bowler hat, beard, mustache, grin, evil smile, fangs, red hair, window, (text:1.3), "),
})
# style -> (positive appended to Hyde subjects, negative appended to Hyde subjects); README faults
HYDE_FIX = {
    "VHD": ("(black wide-brimmed hat:1.4), ", "long cape, tall hat, beanie, knit hat, (cap:1.2), hood, ornament on hat, "),  # "(very short hair:1.3)" here gave pure noise with the Kawajiri LoRA
    "HEL": ("insane grin, (very short hair:1.3), black clothes, ", "brown suit, brown coat, red coat, alucard (hellsing), (cross:1.3), priest, cassock, clergy, alexander anderson, "),
    # Amano overshoots the brim; Hyde's AMA pick was rendered with "(modest soft felt hat:1.2), " (times.jsonl), which put
    # caps, helmets and a woman into the trampling, so the trampling uses this line
    "AMA": ("(male focus:1.2), (black wide-brimmed felt hat:1.2), ", "(huge hat:1.3), oversized hat, cavalier hat, (witch hat:1.4), beanie, helmet, cap, 1woman, "),
    "TRI": ("(male focus:1.3), young adult man, (black wide-brimmed hat:1.4), ", "child, kid, (beanie:1.3), knit hat, female, woman, skirt, "),
    "MON": ("young adult man, (black wide-brimmed hat:1.4), (victorian street:1.3), ", "old, elderly, (middle-aged:1.3), wrinkles, wooden corridor, child, kid, (beanie:1.3), knit hat, pom pom, kasa, "),  # (young man:1.4) made him a child
}
# style -> (positive, negative) for every subject: VHD pulls men toward long-haired, feminine D/Leila looks
STYLE_ALL = {"TRI": ("", "topless, shirtless, bare chest, (text:1.6), (subtitled:1.5), caption, subtitles, english text, title, logo, solo, "),  # TRI printed captions
             "MON": ("(washi paper texture:1.2), muted earthy colours, ", ""),
             "VHD": ("(male focus:1.3), masculine, ", "1girl, female, woman, androgynous, (long hair:1.3), off shoulder, bare shoulders, topless, shirtless, sleeveless, bare chest, nipples, ")}
# style -> tags removed from the shared negative (TRI asks for 3D toon shading, which NEG bans)
NEG_DROP = {"TRI": ("3d, ",)}


def build(style: str, name: str) -> tuple[str, str]:
    """The positive and negative prompt for one style x subject, with the style's Hyde fixes."""
    lead, _, neg_extra = STYLES[style]
    body, neg_subject = SUBJECTS[name]
    neg = NEG
    for tag in NEG_DROP.get(style, ()):
        neg = neg.replace(tag, "")
    fix_pos, fix_neg = HYDE_FIX.get(style, ("", "")) if name in ("ex_hyde", "ex_trample") else ("", "")
    all_pos, all_neg = STYLE_ALL.get(style, ("", ""))
    return QUALITY + lead + all_pos + fix_pos + body, neg + neg_subject + fix_neg + all_neg + neg_extra


def render(style: str, name: str, salt: str, base: str) -> None:
    _, loras, _ = STYLES[style]
    prompt, negative = build(style, name)
    seed = zlib.crc32(f"jekyll_gothic/{name}{salt}".encode())
    values = {"prompt": prompt, "negative_prompt": negative,
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
    for name in args.subjects or [s for s in SUBJECTS if s.startswith("ex_")]:
        render(args.style, name, args.salt, args.base)


if __name__ == "__main__":
    main()
