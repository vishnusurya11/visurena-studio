# Jekyll anime chain test (2026-10-13)

**Question:** does the real episode chain hold a gothic anime look from start to finish? The chain has three stages:
1. NoobAI character sheet and place master.
2. Qwen-Image 2.1 storyboard panel, drawn by `grids.py`.
3. MiniMax-H3 ref2va take, rendered on the `takes_r2v` BASE graph.

Two styles were tested, each on two shots:
- Style 1 is Bloodlust (VHD), the owner's pick.
- Style 2 is Hellsing (HEL), the fallback.

Everything ran on the local GPU at $0. Nothing was written to `library/` (the test only read the ep01 voice `l25.wav`), and nothing was uploaded.

**Sheet:** `chain_sheet.jpg`. Each row is one style and shot: sheet(s) | place master | Qwen panel | H3 frames at 0/25/50/75/100 %.
**Takes:**
- Full quality (CRF 10, 768², 124 frames = 5.17 s, 4.2–4.9 MB): `VHD/take_a.mp4`, `VHD/take_b.mp4`, `HEL/take_a.mp4`, `HEL/take_b.mp4`.
- Previews (CRF 23, about 0.6 MB): `*/take_*_preview.mp4`.
- All four in one grid, with the l25 audio: `preview_2x2.mp4` (1.4 MB).

## Verdict

| | Panel (Qwen) | Take (H3) | Holds? |
|---|---|---|---|
| **1 Bloodlust** | Stays anime: black ink outlines, flat cel shading, the blue-violet fog palette of the place master. It is cleaner and more "TV anime" than the LoRA's painted texture. | Line art and cel shading hold on every frame of both takes, with no photoreal or 3D drift. Faces are stable. Utterson's mouth moves to the line; Jekyll stays still. Hyde walks over the girl and exits right as directed. | **Yes** |
| **2 Hellsing** | Stays anime: angular ink line, red/black palette. | Same: the cel look holds through 100 %. In the fireside take Utterson speaks in profile and the faces are stable. In the trampling at 75 % the girl merges into Hyde's legs, and his hat gains a small badge. | **Yes**, with more identity faults |

**The look survives the chain.** Qwen copied the style of the staged anime place picture, through the existing drawn-look branch (`book_look.DRAWN_GRID`). H3 kept what the panel gave it. Neither stage pulled toward photoreal or 3D.

**Where it degrades is the refs stage.** NoobAI sheets need rerolls and per-style fixes, listed below. The style also flattens a little at Qwen: Bloodlust's painted texture becomes clean cel.

**Step 4 was not run.** The NoobAI img2img or ControlNet panel was conditional on Qwen drifting, and Qwen did not drift. If the owner wants the panel to carry more of the LoRA's texture:
- A NoobAI img2img pass over the Qwen panel (denoise about 0.45–0.55, same LoRA) would cost about 20 s a panel, from times.jsonl's 15–20 s per 1024² NoobAI image.
- No SDXL ControlNet is installed. Only `Qwen-Image-InstantX-ControlNet-Union` is in `ComfyUI/models/controlnet`, so a lineart/canny ControlNet would need a download, about 2.5 GB.

## Recipe and cost

- **Refs:** `chain.py refs`.
  - Recipe: NoobAI-XL 1.1, `image_sdxl_t2i_2lora_hires_visurena` (not edited), hires denoise 0.55.
  - Prompt: the gothic probe's style leads and fixes (`../2026-10-13_jekyll_gothic_anime/render.py`), plus:
    - a one-figure front sheet on a grey gradient;
    - a weighted negative for text and green;
    - the fixes for each person (below).
  - Size: sheets 832×1216, places 1024², both then ×1.5 hires.
  - Speed: **15–20 s each.**
- **Panel:** `chain.py panel`.
  - The real builder, `grids.compose("v2", ...)`, with `grids.look_for(book)` and `grids.negative_for(book)`. The temp book is `STYLE/book/refs/look.json`, with look `anime_gothic`, a `lead` and a `take`.
  - Slots: the sheets, then the place last. 1×1 grid, seed per style and shot.
  - Graph: `grids.graph_for` (Qwen-Image 2.1 edit-multi, 25 steps).
  - Speed: **16–32 s each.** The first one took 175 s, including the model load.
  - The prompt sent and the negative are in `*/panel_*.txt`.
- **Take:** `chain.py take`.
  - Graph: `takes_r2v.BASE` (CRF 10, Singularity int8 + turbo LoRA 1.0/0.7, 8 steps), staged the way a panel take is staged today (ep27's card form):
    - the cast sheets, then the panel LAST, with nothing pinned by a guide;
    - the panel's relation is `take_refs.panel_pin` ("first frame: fully_preserved");
    - the audio comes from `takes_r2v.composite` (silence, or l25 at 0.25 s).
  - The style line comes from `house_style` after `adopt_look(book_look.plan_look(book))`. It reads: `Hand-drawn 2D gothic anime, Bloodlust cel animation, London, 1886, firelight from the left, deep black.` That is 14 words, under the 16-word wall, and there is no "35 mm film grain".
  - The prompt body was hand-written in the `episode_ref_official` grammar (there was no plan for `ro.build`). It is in `*/take_*.prompt.txt`, and the graph sent is in `*/take_*.graph.json`.
  - Speed: **101–107 s per 5.17 s take**.
- **Both takes rendered on BASE (the dialogue arm), as asked.** Production would put the silent shot a on the CK-attention narration arm (`NARRATION_BASE`).
- All seconds and prompts are in `times.jsonl`.

## Faults found (refs stage), with fixes now in `chain.py`

- **Utterson** (owner's fault list). The v1 renders are in `*/v1/`.
  - v1: young with grey spiky hair (VHD), or a long silver fringe and blood (HEL).
  - Fixed by weighting `mature male`, `40 years old` and `lank light brown hair streaked with grey`, and by negating `young`, `blonde`, `spiked hair`, `grey hair` and `glasses`.
  - VHD's pick (salt 2) is sandy-brown, dour and about 40, but drawn in a softer comedic face. HEL's (salt 1) is closer.
- **Green cast:** gone. The fix was a weighted `green theme / green light` negative on everything.
- **Hyde** (VHD v1):
  - The words "side-whiskers" drew **cat whiskers** and a chibi face. The `mutton chops` + `sideburns` tags with `young adult man` fixed it.
  - The HEL lead's `(very short hair:1.3)` gave a beanie, and one seed drew 8 copies (`character reference` → multiple views). The pick is HEL salt 1: wide black hat, black coat, faint whiskers.
- **Jekyll (HEL)** comes out **bearded** on every seed: the Hellsing look draws an older man as Walter. The `beard` negative did not beat it, and the beard carried through the panel and the take. It is still open; try `(beard:1.5)` or the VHD sheet.
- **Study place:**
  - Weighted tags (`(two leather armchairs:1.5)` ...) drove the Kawajiri LoRA into **pure noise** (VHD) and drew a robed silhouette (HEL). This is the same failure the gothic probe found with weights under that LoRA.
  - Plain unweighted tags gave usable rooms. None of them has the armchairs, so Qwen added them from the panel prose.
- **Corner:**
  - v1 was a violet-sky courtyard with no fog. Fixed with `(thick fog:1.4)` and by negating `purple sky` and `courtyard`.
  - The Bloodlust lead's `cold moonlight` competes with the gaslight.

## Pipeline changes needed to make anime the book's look

1. **Refs drawer → NoobAI.**
   - `book_look.t2i` and `sheet_ladder.redraw` know two looks, photoreal (Krea2) and the house (`refs_pack.T2I`, Krea2 + the Cinematic LoRA). A drawn look such as `anime_gothic` falls through to the **house** WotW painted look.
   - Add a third branch that reads `workflow`, `ckpt`, `loras`, `tags` and `negative` from refs/look.json, and draws on `image_sdxl_t2i_2lora_hires_visurena`.
   - NoobAI does not draw a four-pose turnaround reliably (8 copies on one seed). Draw the **one-figure front** that grids and takes stage (`sheet_front`) and skip the turnaround.
   - The per-style person fixes (the male-focus and long-hair negatives for VHD, the grin on Hyde only for HEL, the age weights) need a home in the look.json or the cast row.
2. **Grid style:** works as built.
   - `DRAWN_GRID` with the look's `lead` kept the anime look in all four panels, and `negative_for` adds "photographic".
   - Two cautions:
     - `ATMOSPHERE_GRID` says the fog is "in every frame", so it would put fog indoors at the fireside. Gate it on an outdoor setup, or leave `atmosphere` out of an anime look.json (this test left it out).
     - Keep light words (`cold moonlight`) out of the `lead`, because the setup's own light already rides in the panel.
3. **H3 style line:** works as built. `plan_look` → `house_style.adopt_look` gives a 14-word drawn line, and `book_look.panel_look` tells H3 the panel is "in the book's own anime gothic look". The look.json only needs a short `take` (≤ 7 words).
4. **Photoreal-only finishes to turn off for a drawn look:**
   - `book_title` (the plate is photoreal or house only), `book_look.t2i`, `sheet_ladder.redraw` and the place drawer (`scripts/refs/places.py`, through `book_look.t2i`).
   - `assemble.py` has no grade or grain pass (checked), so nothing needs turning off there.
   - The take DQ thresholds were calibrated on photoreal and WotW. A per-book recalibration on the first anime episode is expected (memory: "constants outlive their world").
5. **Book declaration:** the owner's ruling goes into `library/<jekyll>/refs/look.json`. It currently says `photoreal` (style A, 2026-10-12). It was not touched here.

## Files

- `chain.py` runs every step.
- `make_chain_sheet.py` builds the sheet.
- `takes_run.log` is the take run's output.
- In `VHD/` and `HEL/`:
  - `hyde`, `jekyll`, `utterson`, `corner`, `study` `.png` are the refs used. `*_sN.png` are the rerolls, and `v1/` is the first pass.
  - `panel_a|b.png` and `.txt` are the Qwen panels and their prompts.
  - `take_a|b.mp4`, `.prompt.txt`, `.graph.json` and `_fNNN.png` are the takes, their prompts, their graphs and the extracted frames.
  - `audio_a|b.wav` is the take audio.
  - `book/refs/look.json` is the temp look declaration.
