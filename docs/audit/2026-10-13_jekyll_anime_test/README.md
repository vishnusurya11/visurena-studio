# Jekyll and Hyde: anime gothic probe (2026-10-13), stopped

**Owner: did not like.** The owner rejected these anime recipes after the first Hyde probes. The test was
stopped part-way: no further stills, no H3 take, no compare sheet. A new research-led test replaces this one.
Nothing in `library/` was touched, nothing was uploaded, $0 (local ComfyUI).

## What exists

- Hyde, full figure, one still per recipe, seed `crc32("jekyll_look/2_hyde")` = 1570898721 (style A's seed):
  - `Q21/2_hyde.png`: Qwen-Image 2.1 (`image_qwen_image_2_1_t2i`), words only, 1328², 25 steps.
  - `DG/2_hyde.png`: Qwen-Image v1 fp8 + `qwen/QWEN_DarkGhibli_000001500` 1.0 + Lightning 8-step,
    on the new workflow `comfy_studio/workflows/image/image_qwen_image_2_1_t2i_stylelora_visurena.json` (new file, no edits).
  - `NU/2_hyde.png`: the same workflow with `qwen/naoki_urasawa_qwen_v1`.
  - `hyde_3recipes_preview.jpg`: the three side by side, as the owner saw them.
- `render.py` (lead, tail, recipes), `subjects.json` (six subjects from `analysis/heads.json`, never rendered beyond Hyde),
  `take.py` and `make_sheet.py` (written, never run), `times.jsonl`.
- The MysticAnime probe was queued and then deleted from the queue before it ran. The Krea2 words-only arm (`K2`) never ran.

## Inventory (what can draw anime locally)

- Bases: Qwen-Image 2.1 (int8/bf16), Qwen-Image v1 and 2512 (fp8), Krea2 turbo, Flux-2 Klein 9B, and one Illustrious SDXL checkpoint.
  **No Flux.1-dev base is installed**, so the Flux anime LoRAs on disk (RetroAnimeFluxV1 and others) cannot run.
- Qwen-Image v1 style LoRAs: DarkGhibli, Ghibli_qwen, naoki_urasawa, MysticAnime, arcanev2, kiki. These do not load on 2.1 (a different architecture).

## Time (cold, sharing the queue with another session's cast render)

Q21 267 s, DG 411 s, NU 828 s. Each figure includes a model load from the HDD and waiting behind other jobs. Warm speed was not measured.

## Faults read by eye

- **Q21**: the strongest of the three. It is seinen, not chibi, and reads as sinister, with side-whiskers and a low hat.
  But it is very dark and close to a Krea2 frame drawn with ink lines.
- **DG and NU**: almost the same frame. The LoRA barely moved Qwen-Image v1 at this seed. Both give Hyde a
  **top hat and a handlebar moustache instead of side-whiskers**, both draw **gibberish lettering on shop signs**,
  and both draw **modern yellow road lines**. Both are brighter, flat Ghibli-like drawings.

## If anime gothic returns

Switching would mean redrawing every cast sheet and place master. The grid and take style already follow `refs/look.json`
(e7d7b59), so these two need no code change.
