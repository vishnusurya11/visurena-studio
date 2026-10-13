# Jekyll: gothic anime looks, Hyde only (2026-10-13)

Probe only. Nothing here is wired into the book. The owner asked to see more gothic and dark anime looks for
*The Strange Case of Dr Jekyll and Mr Hyde*, quickly. Everything ran on the local GPU at $0, with no uploads and nothing written to `library/`.

**Sheet:** `styles_sheet.jpg` has 15 styles with Hyde in each. `styles_sheet_partial.jpg` is the same sheet.

## Recipe (all styles)

- **Base:** `NoobAI-XL-v1.1.safetensors`, an Illustrious-family SDXL model that knows Danbooru copyright and artist tags.
- **Workflow:** `comfy_studio/workflows/image/image_sdxl_t2i_2lora_hires_visurena.json`. It already existed and was not edited.
  - Clip skip 2, euler_a, 28 steps, cfg 6, 1024².
  - 1.5x latent hires pass, 20 steps, at **denoise 0.55**. The default of 0.45 left blocky pixelation in hair (see BER/HEL `hyde_v1.png`).
- **Seed:** 3343000820 for every style, which is crc32("jekyll_gothic/hyde"). The one exception is Hellsing, which uses salt `b` (seed 3416890328). Its seed-1 hat came out top-hat-like.
- **Prompt:** `render.py` builds it as quality tags + the style lead + the shared Hyde body.
  - The Hyde body asks for: a young man, short and slight, pale, sneering, short messy black hair, black mutton chops, no moustache, `(black wide-brimmed hat:1.3), soft black felt hat, low flat crown, floppy brim`, an ill-fitting black coat, and a foggy gaslit Victorian street at night.
  - The negative bans: signage, lettering, road markings, skyscrapers, and the top hat, bowler, peaked cap, military cap, witch or conical hat, cowboy hat, long hair, blood and gore.
- **Speed:** **15–20 s per image** on the shared 4090 (from `times.jsonl`). Every recipe is far under the 3-minute ceiling.
- **Reproduce:** `uv run python docs/audit/2026-10-13_jekyll_gothic_anime/render.py STYLE hyde [--salt b]`, then `sheet_hyde.py OUT.jpg STYLE[=file] ...`

## Per style

| # | Style (folder) | Reference | LoRA (strength) | Style lead tags (abridged) | s/img | Faults seen | Verdict |
|---|---|---|---|---|---|---|---|
| 1 | Bloodlust gothic (VHD) | Vampire Hunter D: Bloodlust (2000, Madhouse, Kawajiri, Amano designs) | Kawajiri City Trilogy XL 0.45 | vampire hunter d: bloodlust, madhouse, kawajiri, fine thin linework, blue-black/violet | 20 | Long hair is back (the LoRA pulls toward D). The hat is D's tall wide-brim, not a low wideawake. The salt-b reroll was feminine with a white hat. | Strong mood; Hyde reads as D |
| 2 | Hellsing ink-red (HEL) | Hellsing Ultimate (2006–12) | none | hellsing ultimate ova, hirano kouta, jagged ink shadows, insane grin, red/black | 20 | Long hair. Brown suit, not a black coat. Seed 1 gave a gory hand (v1) or a top-hat crown (v2). | Best "monster grin"; the hat is close (soft slouch) |
| 3 | Berserk '97 retro cel (BER) | Kenpuu Denki Berserk (1997, OLM) | none (the Berserk IL LoRA download needs a civitai login) | kenpuu denki berserk, miura, 1990s, flat cel, muted earthy | 15 | Eyepatch (Guts bleed). Long hair. The hat is a good crumpled felt slouch. | Retro cel texture is there; the costume bleeds in |
| 4 | Black Butler Victorian (KUR) | Kuroshitsuji (2008, A-1) | none | kuroshitsuji, toboso yana, elegant thin linework, ornate gaslit | 15 | Too handsome and dapper for Hyde. Gloves. | Clean, usable house look; not menacing |
| 5 | Moriarty Victorian (MOR) | Moriarty the Patriot (2020, Production I.G) | none | yuukoku no moriarty, miyoshi hikaru, soft cel, teal/amber | 15 | Bright, warm, not gothic. Smile rather than sneer. | Hat, hair and whiskers are the most on-model; the least dark |
| 6 | Mononoke washi (MON) | Mononoke (2007, Toei, dir. Kenji Nakamura) | **Mononoke (Anime) Style IL** 0.6 | mononoke, ukiyo-e, washi paper texture, flat colour, woodblock | 20 | Hyde looks middle-aged. The street turned into a wooden corridor. At 0.9 the LoRA gave a kasa straw hat and a kimono (`hyde_v2_lora09.png`). | The most distinct look; flat paper palette, needs a younger face |
| 7 | Kojima baroque (CAS) | Castlevania (Netflix) / Ayami Kojima art | Ayami Kojima Castlevania (Pony) 0.8 | kojima ayami, castlevania, painterly gothic, sepia + crimson, hatching | 20 | Long hair and a jabot, so he reads as a vampire lord. The hat is a wide flat brim. | Beautiful sepia ink-paint; too elegant for Hyde |
| 8 | Kawajiri OVA noir (KAW) | Wicked City (1987) / Ninja Scroll (1993) | Kawajiri City Trilogy XL 0.9 | wicked city ova, 1980s, hard angular faces, airbrushed night | 20 | The background is a neon-like blur. The coat is a high-collared tunic. | Authentic 80s OVA cel; good short hair and whiskers |
| 9 | Gankutsuou textile (GAN) | Gankutsuou (2004, Gonzo, Mahiro Maeda) | none | gankutsuou, (patterned clothing:1.5), gold/indigo damask filling the coat | 20 | The pattern is lumpy 3D embroidery, not the show's flat static texture. The hat brim is furry. There is a faint signature-like scrawl at right. Seed-1 tags alone gave only a patterned cravat (v1). | Partial; the real technique (a static pattern behind a transparent cel) would need a texture-composite pass |
| 10 | Death Note Obata (DN) | Death Note (2006, Madhouse, Takeshi Obata) | none | death note, (obata takeshi:1.3), crosshatching, green-grey | 15 | Very dark, and the face is lost in the hat shadow. v1 gave a goatee and a cartoon face. | Mood is right; Obata detail is not there |
| 11 | Junji Ito ink horror (ITO) | Junji Ito manga / Uzumaki (2024) | none | itou junji, horror, monochrome, ink hatching, screentone | 15 | Goatee. The face is mild, not uncanny. | The hat is the closest to a wideawake; a clean B/W ink look |
| 12 | Pandora Hearts gothic (PAN) | Pandora Hearts (2009, Xebec, Jun Mochizuki) | none | pandora hearts, mochizuki jun, lace and ribbons, crimson/black | 15 | Very long hair. Pretty-boy face. Gaucho flat-crown hat. | Gothic-lolita Victorian; wrong body for Hyde |
| 13 | Amano watercolour (AMA) | Yoshitaka Amano's VHD illustrations | none | amano yoshitaka, watercolor, ink wash, art nouveau | 15 | Oversized cavalier brim. It reads as a soft digital paint, not Amano's line. | Atmospheric; not Amano |
| 14 | D.Gray-man gothic (DGM) | D.Gray-man (2006, TMS, Katsura Hoshino) | none | d.gray-man, hoshino katsura, black/white/red | 15 | Long hair. A dome hat with a red underbrim. Weak show identity. | A dark silhouette; generic |
| 15 | Trigun Stampede 3D cel (TRI) | Trigun Stampede (2023, Orange) | none | trigun stampede, 3d cel-shaded, toon shading, rim light | 15 | Not the 3D toon look at all. A sketchy 2D paint instead. | Hat (soft, round, low) and short hair are on-model; the style missed |

Files: `<STYLE>/hyde.png` is the shown image, and Hellsing's is `HEL/hyde_sb.png`. The other files are earlier passes, kept for the record:
- `hyde_v1.png`: pass 1 at hires denoise 0.45 for VHD–MON, with long-hair-permitting text.
- `hyde_prev*.png`: the previous agent's renders. VHD's has the peaked cap.
- `hyde_sb.png`: the salt-b rerolls.

In `times.jsonl`, the "file" field of a pass-1 row names `hyde.png`, which was later renamed `hyde_v1.png`.

## Findings

- **The hat is solved by words for most looks.** Three things fixed it: weighting `black wide-brimmed hat`, adding `soft felt, low flat crown, floppy brim`, and negating cap, top hat, witch hat and cowboy hat. No style showed a peaked or military cap after that. The truest wideawakes are ITO, TRI, BER and MOR. VHD, AMA and DGM overshoot to a cavalier brim.
- **Show tags carry the costume as well as the style.** Berserk added an eyepatch, VHD, Hellsing, Pandora Hearts and D.Gray-man added long hair, and Mononoke added a kimono. `long hair` in the negative does not beat a show tag.
- **The LoRA styles are the most distinct:** Mononoke, Kojima and Kawajiri. The tags-only looks converge on one NoobAI anime house look (KUR, MOR, DGM, TRI and AMA are close cousins).
- **Downloaded:** `C:\comfy_models\loras\gothic_anime\mononoke_anime_style_illustrious.safetensors` (218 MB).
  - Source: "Mononoke (Anime) Style Lora (Illustrious / Pony)" v1.0 Illustrious, https://civitai.com/api/download/models/1934538, mirror page https://civarchive.com/models/1049962. Trigger `mononoke`.
  - Licence: the creator's terms say "Do not sell or commercialize this LoRA", with no formal licence stated. It is fine for this private probe; check with the creator before any commercial episode.
- **Not obtained:**
  - The Berserk (1997) IL LoRA (https://civarchive.com/models/755564): the civitai download returns 401 without a login.
  - The Junji Ito "Vintage Horror Comic" LoRA (https://civarchive.com/models/1327068): deleted from civitai.

## Next, if the owner picks a look

Pick 2–3 looks and render Jekyll and the ch1 scene in them (`render.py STYLE jekyll ch1`; `make_sheet.py` builds the 3-column sheet). Fixes for the top candidates:
- MON: a younger face, and `victorian street` weighted.
- HEL: a black coat.
- KAW: a cleaner background.
- GAN: a static-texture composite pass, which is how the show does it.

## References

- Vampire Hunter D: Bloodlust: https://en.wikipedia.org/wiki/Vampire_Hunter_D:_Bloodlust
- Hellsing Ultimate: https://en.wikipedia.org/wiki/Hellsing_Ultimate
- Berserk (1997): https://en.wikipedia.org/wiki/Berserk_(1997_TV_series)
- Black Butler: https://en.wikipedia.org/wiki/Black_Butler
- Moriarty the Patriot: https://en.wikipedia.org/wiki/Moriarty_the_Patriot
- Mononoke (2007):
  - https://en.wikipedia.org/wiki/Mononoke_(TV_series)
  - ukiyo-e and washi motifs: https://nippon.com/en/japan-topics/c030287
  - rough paper texture: https://towardchaos.substack.com/p/mononoke-when-art-overwhelms-the
- Castlevania (Netflix) / Ayami Kojima: https://en.wikipedia.org/wiki/Castlevania_(TV_series), https://en.wikipedia.org/wiki/Ayami_Kojima
- Wicked City / Ninja Scroll: https://en.wikipedia.org/wiki/Wicked_City_(1987_film), https://en.wikipedia.org/wiki/Ninja_Scroll
- Gankutsuou:
  - https://en.wikipedia.org/wiki/Gankutsuou:_The_Count_of_Monte_Cristo
  - static-pattern technique: https://unwinnable.com/2011/01/04/greatest-unknown-anime-part-5-gankutsuo/
  - https://tropedia.fandom.com/wiki/Unmoving_Plaid
- Death Note: https://en.wikipedia.org/wiki/Death_Note
- Junji Ito: https://en.wikipedia.org/wiki/Junji_Ito
- Pandora Hearts: https://en.wikipedia.org/wiki/Pandora_Hearts
- Yoshitaka Amano: https://en.wikipedia.org/wiki/Yoshitaka_Amano
- D.Gray-man: https://en.wikipedia.org/wiki/D.Gray-man
- Trigun Stampede: https://en.wikipedia.org/wiki/Trigun_Stampede

## Examples for the shortlist (2026-10-13, second pass)

The owner shortlisted styles 1, 2, 6, 13 and 15 and asked for examples. Each style got the same six pictures, built from `analysis/heads.json`, at the same seeds. A reroll's salt is in its file name (`_sb`, `_sc` and so on).
1. Hyde, fixed.
2. Jekyll.
3. Utterson.
4. ch1: Hyde strides over the fallen girl.
5. ch1: Utterson and Enfield pass the door.
6. ch3: Jekyll and Utterson by the fire.

Every image was looked at. A seed was rerolled for a wrong hat, duplicate or extra people, lettering or a signature, modern road markings, or another show's costume. `picks.json` names the kept file for each picture, `times.jsonl` holds each render's exact prompt, and `make_examples.py` builds the sheets.

- **Sheets:** `examples_2_hellsing.jpg`, `examples_1_bloodlust.jpg`, `examples_6_mononoke.jpg`, `examples_13_amano.jpg`, `examples_15_trigun_stampede.jpg`. Each is 2 × 3.
- **Overview:** `examples_overview.jpg` has the 5 styles as rows, showing Hyde, Jekyll and the ch1 trampling.
- **Reproduce:** `uv run python docs/audit/2026-10-13_jekyll_gothic_anime/render.py STYLE [ex_subject ...] [--salt b]`. With no subject it renders all six `ex_*`. Then run `make_examples.py STYLE` or `make_examples.py overview`.
- **Caveat:** `render.py` holds the final prompt lines. A few picks were rendered before a later fix to the same style, and their exact prompt is the row in `times.jsonl`. They are: MON Jekyll, Utterson and study (before the washi tag), AMA Hyde (with "modest soft felt hat"), and TRI Jekyll, Utterson and door (with the earlier lead).

| # | Style | Fixes that held | Rerolls / faults met | Verdict |
|---|---|---|---|---|
| 2 | Hellsing ink-red | Moved "insane grin" from the style lead to Hyde only, because every man was grinning. Dropped "blood-red highlights", which gave red hair. For Hyde: short hair, black clothes, and a negative on the priest cross. | Anderson's priest cross on Hyde. A witch hat and a gun in the trampling. A woman in the door scene. Japanese lettering in the study. | The menace reads best of the five, and Jekyll and Utterson stay human. It is dark and cel, with a red-black palette. |
| 1 | Bloodlust gothic | `male focus` for every subject, plus a negative on long hair, bare shoulders and topless. Hyde's hat is the weighted wide brim. | Without the fix, every man drifted to D or Leila: long blond hair, women. `(very short hair:1.3)` in the lead gave **pure noise**. `(low crown)` gave caps and beanies. A third man appeared in the door scene. | The most cinematic look, with the strongest lighting and colour. Hyde reads as a D-cousin, wide brim and long coat. |
| 6 | Mononoke washi | "young adult man" plus the weighted wide brim. | `(young man:1.4)` made Hyde a child in a beanie. A red seal signature appeared in the door scene (seed 1). The hat jumped onto the girl. A witch hat. | Most distinctive and least anime: pale kabuki faces on flat paper greys. The LoRA's washi patterns are faint, so it reads as quiet rather than ornate. |
| 13 | Amano watercolour | A negative on huge, cavalier and witch hats. For the trampling: `male focus` plus a wide-brimmed felt hat. | The trampling took 13 seeds. Faults met: witch hats, a helmet, a woman as Hyde, the girl wearing his hat, and two signatures. | Art-nouveau frames and an ink wash on the portraits, but the scenes fall back to generic digital paint. Amano's own line is still absent. |
| 15 | Trigun Stampede 3D cel | Removed `3d` from the shared negative for this style. Lead: `(3d cel-shaded anime:1.1), cgi anime`. Negative: text, subtitles, solo. `male focus` for Hyde. | It now renders as 3D toon. In exchange, "trigun stampede" printed fake captions in every study, and "solo" plus a strong text negative cleared them. Faults met: a shirtless Hyde, a female Utterson and a female Hyde. A modern tie and wristwatch also slip in. | The 3D cel look the owner named, which the first pass missed. It is the least gothic: bright, smooth and Western-CG. |
