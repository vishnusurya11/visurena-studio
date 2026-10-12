# C2-J: looks and judges (cycle 2, researcher J)

2026-10-11. Read-only. Work was done online and on CPU (facenet/MTCNN on CPU), with no GPU, no ComfyUI calls and no code edits. Nothing under `library/` was written.

**Bar (CYCLES.md):** 95 % means measured on the artefact in ≥ 2 independent cases. Anything weaker is a hypothesis.

**Scratch folder** (scripts, JSON, contact sheets): `D:\temp\claude\d--Projects-KingdomOfViSuReNa-alpha-visurena-studio\53388bed-712c-4d9b-972d-6c2de9a9f94e\scratchpad\c2\`

| File | What it is |
|---|---|
| `j_heads.py` → `j_heads.json` | Census of head markers: every WotW, Scarlet and Jekyll bound row, its dossier head, its refs.json head, and its look markers |
| `j_lineage.py` → `j_lineage.json` | Full-sheet facenet over every staged Scarlet/WotW sheet. The WotW attribution is unreliable (see §5) |
| `j_headcos.py` → `j_headcos.json` | Head-crop facenet over the Scarlet sheet lineages (the calibrated instrument) |
| `lineage_scarlet.jpg` | Hope ×4, Brigham Young ×3 and Ferrier ×3 sheets, side by side |
| `j_facevis.py` → `j_facevis.json` | MTCNN on the ep25/ep27 regrid panels |
| `j_ghost.py` → `j_ghost.json` | MTCNN ghost pre-filter. It is shown **unusable** (§3) |
| `ghost_eye\g00-g10.jpg` | Eye scan: clothing crops of 33 WotW base sheets |
| `narrator_sheet_ghost.jpg` | **The second ghost case:** the narrator's base sheet and its staged front crop |
| `pit_base_vs_2x.jpg` | An MTCNN false positive on heather |
| `captain_sheet.jpg` | The sheet layout, for reference |

---

## 1. LOOK-STATE refuses the felt hat. Confidence 95 %: two faults, both measured

### 1a. Reader side: the VLM calls a felt hat `other_hat`, and the code has no headwear family
- `studio/judges/look_state.py:69` compares with `lt.family(key, ·)`.
- `studio/look_table.py:177` `family()` groups **hair colour only**. For headwear the comparison is exact string equality over the closed list `none, boater, felt_hat, bowler, top_hat, cap, bonnet, helmet, hood, bandage, other_hat` (`studio/continuity_spec.py:22`).
- **Measured:** the same battered brown felt hat (ep25 `ragged_greyed`) was read **8 times**:

| Source | Reads | `other_hat` | `felt_hat` |
|---|---|---|---|
| `bench_evidence\c1\looks_judge.json` (fresh_s0/s1/s2, ghost_2x) | 4 | 4 | 0 |
| `bench_evidence\c1\regrid_ep25_report.json` "reads" (panels 0, 1, 2, 4) | 4 | 3 | 1 (the tiny far figure, panel 4) |
| **Total** | **8** | **7** | **1** |

- The regrid "shown" tally (`scripts/refs/look_replay.py:61 shows_look`) ignores headwear, so the miss only bites in LOOK-STATE.
- **Other headwear-comparing sites** use the same exact compare:
  - `studio/panel_content.py:262`, G-LOOK-PANEL (advisory);
  - `scripts/refs/continuity_replay.py` (hair only).

### 1b. Writer side: `look_table.HEADWEAR` mis-maps the book's hat words
`first_of` takes the first pattern that matches. Replaying it over all 61 WotW looks (`j_heads.json`) gives **8/61 looks (13 %) whose closed marker is wrong**:

| Look | Book words | Marker today | Why | Should be |
|---|---|---|---|---|
| stent `pit_frock_coat`, `deputation_frock_coat` | "Black silk top hat" | `other_hat` | `top-?hat` needs a hyphen or no space, and "silk hat" ≠ "silk top hat" | `top_hat` |
| unnamed_cabmen `summer_rank`, `box_coat_london` | "billycock hat" | `other_hat` | a billycock *is* a bowler; the word is not in the table | `bowler` |
| unnamed_milkman `morning_round` | "Brown felt pork-pie hat" | `other_hat` | "felt hat" needs the two words adjacent | `felt_hat` |
| narrators_wife `mourning_reunion` | "Black straw hat with … crape veil" | `boater` | `straw hat` → boater | `other_hat` |
| mrs_elphinstone `white_summer`, `white_grimed` | "Wide white straw hat …" | `boater` | same | `other_hat` |

Scarlet's refs.json card words show the same class of fault:
- Lestrade's outdoor "a tall black hat" → `other_hat` (the VLM will say `top_hat`);
- Hope's outdoor card names a hat the regex misses → blank.

### How often it misfires
The VLM confuses three markers: `felt_hat`, `other_hat` and `bowler`.

| Book | Exposure | Expected misfire |
|---|---|---|
| WotW | **14/61 looks (23 %)** carry one of these three markers: felt_hat 6, other_hat 6, bowler 2. Another **3 looks** carry a wrong `boater`. | On the one hat with repeat reads, 7/8 reads disagreed with the marker (88 %). Expect about **12 of the 17 hat looks refused on a correct picture** under today's exact compare. This includes both narrator felt-hat looks (`flannel_buried`, `ragged_greyed`). |
| Scarlet | 9/26 rows change hat by card (indoor bare-headed, outdoor hat). The hats are bowler ×2, felt ×2, other ×4 and boater ×2. | The same exposure once a Scarlet table exists. |

Only the felt hat has been read more than once, so the misfire rate for *other* hats (top hat, billycock) is a **hypothesis** until VLM reads exist.

### Fix (CPU, test-first, no GPU)
1. **A headwear family in `look_table.family`.** `HEADWEAR_FAMILY = {felt_hat, other_hat, bowler → "brimmed"}`; every other marker is its own family. `boater`, `top_hat`, `cap`, `bonnet`, `helmet`, `hood` and `none` stay distinct, so the real shipped fault (shipped ep25 panels read `boater` on a felt-hat look, `regrid_ep25_report.json` "shipped_reads") is still caught. One function serves LOOK-STATE and G-LOOK-PANEL.
2. **Writer table corrections** in `look_table.HEADWEAR`:
   - `top_hat`: `top[- ]?hat|silk hat|stovepipe`
   - `bowler`: `bowler|derby|billycock`
   - `felt_hat`: `felt\b[\w\s-]{0,20}\bhat|pork-?pie|slouch hat|wide-?awake`
   - `boater`: `boater` only (a "straw hat" falls to `other_hat`)
   - The order stays most-specific first.
3. **Acceptance replay (CPU):**
   - Re-judging `looks_judge.json`, fresh_s0/s1/s2 **pass** (dirt stays an advisory).
   - ghost_2x **still fails** on `beard` against `stubble`, which is correct: that draw used the old beardless prompt.
   - The `regrid_ep25` shipped reads still fail on `boater`.
   - Re-deriving the 61 WotW looks changes **exactly the 8 rows** in the table above and nothing else.

Do **not** widen `other_hat` into a wildcard over all hats. A boater-for-felt fault is the very drift LOOK-STATE exists to catch.

---

## 2. The regrid bar counted back views. Confidence 95 %: measured on 2 replays, plan and detector agree 7/7

**Rule proposed: the face-visible denominator** (`look_replay.tally`, and any production panel tally that copies it):
- **Denominator:** panels whose shot casts the person **and** whose plan does not ask for a hidden face:
  - `frame` matches `\b(from behind|seen from behind|back to (the )?camera|walking away|over (his|her) shoulder)\b`, **or**
  - `size ∈ {wide, extreme_wide, establishing}`.
- A panel inside the denominator where the reader sees no face **counts as a miss**. A model that turns everyone round must not pass.
- Denominator = 0 → **unmeasurable**, never a pass (a terminal is not a pass).
- Bar unchanged: ≥ 80 % of the denominator.

**Check on the replays** (`j_facevis.json`; MTCNN, p ≥ 0.86, frontal yaw ≤ 0.14 on every hit):

| Replay | Planned face panels | MTCNN face | Plan-exempt panels | MTCNN face | Old score | **New score** |
|---|---|---|---|---|---|---|
| ep25 `fulham_road`, C1 regrid with the beard look (`scratchpad\c1b\regrid_ep25\panel_0*.png`) | shot 0 (medium), shot 1 (MC) | 2/2 (h .19, .35) | shot 2 "Medium **from behind**", shot 4 "**Wide** … small" | 0/2 | 2/4 FAIL | **2/2 PASS** |
| ep25 round 0, the beardless look (`replay\ep25_fulham_road\panel_*.png`) | shot 0 | 1/1 | shots 2, 4 | 0/2 | 0/4 FAIL | **0/1 FAIL** (it still catches the real fault) |
| ep27 `study_table` (`replay\ep27_study_table\panel_*.png`, and `_run1`) | shots 3, 12, 13 (MC / close) | 3/3 and 3/3 | shot 2 is an insert, not cast | 0 | 3/3 | **3/3 PASS** |

- The plan rule and the detector agree on all 7 cast panels: 5 included panels with a face, 2 exempt panels without one.
- Prefer the **plan rule** to the detector: it is deterministic and free.
- MTCNN fails on stylized texture (see §3), so keep it as a logged cross-check, not the gate.

---

## 3. Ghost faces from the 2x USDU pass. Confidence 95 % for the issue (2 cases). The cure is a bench item

### Mechanism, read from the workflow
In `D:\Projects\KingdomOfViSuReNa\alpha\comfy_studio\workflows\image\image_krea2_cinematic_2x.json`:
- Node 12 `UltimateSDUpscale` takes `positive: ['5',0]`, the **full subject prompt**.
- Its settings: denoise 0.2, 8 steps, simple, 1024² tiles. A 3072×2048 output is 6 tiles.
- So a tile that holds only trousers or backdrop is still told "a gaunt man with a grey beard …", and it paints a face.
- The upscale seed is hard-coded at 0 and not injected; the noise is the same on every draw.

### Prevalence: an eye scan of 33 WotW base sheets (lower 60 %, clothing and backdrop, `ghost_eye\g00-g10.jpg`) plus the cycle-1 looks
| Case | What | Where |
|---|---|---|
| 1 (known) | ragged_greyed ghost_2x: two faces on the thighs. The 1x decode of the same seed has none | `bench_evidence\c1\ghost_ab_legs.jpg` |
| **2 (new)** | **The narrator's base sheet** `library/20260827135508_the-war-of-the-worlds/refs/characters/unnamed_first_person_narrator/sheet.png` has a **large translucent moustached face painted into the grey backdrop** between the front and ¾ figures. **The staged front crop `sheet_front.png` (md5 `28241af7`), staged in ep18-ep27 (10 episodes), carries its right half behind the figure.** | `narrator_sheet_ghost.jpg` |
| clean | 32/33 other sheets, plus fresh_s0/s1/s2 by eye. `fresh_s0` may have a faint eye at the knee, which C1 already noted | — |

**Rate: 1/33 base sheets (3 %), plus 1 of 4 recent look draws.**
- The narrator case is the one that matters: it is the most-staged sheet in the book.
- It is a *backdrop* ghost, not a texture ghost. That is the same mechanism in the other tile type: a backdrop-only tile with a portrait prompt.
- Its 1x was never saved, so the USDU attribution for case 2 is **by mechanism (90 %), not by A/B**.
- It is a hypothesis that this ghost reached the shipped takes. Checking needs an eye pass over ep18-27 takes for a face in the backdrop.

**Automatic detection is not available on CPU.** MTCNN (`j_ghost.json`):
- **misses both real ghosts**: ghost_2x is found only through the bust inset, and the narrator backdrop ghost is not found;
- **fires 7-9 times on heather** in `_looktest/cinema_lora__horsell_pit_wide_2x.png`, which are not faces by eye (`pit_base_vs_2x.jpg`).

So any ghost gate must be a VLM list on the 2x image, or a 1x-vs-2x difference check. That is cycle-3 work, not now.

### The standard fix (online)
- USDU applies **one prompt to every tile**. Replicate's guide says that although tiles are upscaled separately, the prompt applies to the whole image.
- Community templates advise **stripping a many-tile pass to a subject-less or material-only prompt**.
- Denoise should stay low (0.15-0.3). A **tile ControlNet** curbs hallucination but can lose likeness.
- Larger tiles help; seam-fix "chessboard" or "band" addresses seams, not ghosts.
- There is no Krea2/Qwen-Image tile ControlNet in the house set, so the prompt is the lever.

### Proposal: one new file, never an edit
**`image_krea2_cinematic_2x_neutraltile_visurena.json`** (with manifest), copied from `image_krea2_cinematic_2x_presave.json` so the 1x is kept for A/B. The single change:
- a second `CLIPTextEncode` (node 14) holding **only the house style words, no subject**: *"A 3d, clean ultra hd … heavily angular 3d art style with brush stroke colour texture."*;
- it feeds `UltimateSDUpscale.positive`, and its `ConditioningZeroOut` feeds `negative`;
- denoise stays at 0.2 and tiles stay at 1024, so it is a one-variable A/B.

**Bench (GPU, about 6 min):**
- ghost seed 4165438081 with the old ragged_greyed prompt: today's file against `_neutraltile`;
- 2 more look seeds;
- the narrator day_suit base prompt at its stored seed, if `refs.json` keeps it.

**Pass:**
- 0 faces outside heads by eye on all draws;
- texture sharpness (Laplacian variance on the trouser crop) ≥ 90 % of today's;
- face sheet identity against the 1x ≥ today's.

**If it fails, a second arm:** add tiles at 1536 (4 tiles). Do not add a tile ControlNet: no Krea2-compatible one exists in the house.

**Owner-visible note:** re-drawing the narrator base sheet is a look change, so it is **his ruling** (CYCLES.md). Until then, every new grid stages a ghost-bearing reference.

---

## 4. Scarlet's empty heads. Confidence 100 %, measured. The cure is code, not a wall

C1's "9/15" understates the problem. Three measured facts (`j_heads.json` and the runs below):
1. **The writer path crashes on every real dossier before the head check runs.** `studio/look_timeline.py:46` `dossier_text` does `min(card['appearances'])`, but `appearances` is an **int** (a count) in **every** dossier of Scarlet, WotW and Jekyll. Running it on `jefferson_hope.json` raises `TypeError: 'int' object is not iterable`.
   - The test fixture `tests/test_the_look_timeline_comes_from_state_changes.py:17` hand-writes `"appearances": [1, 2, 3]`. That is fixture drift against the contract (CLAUDE.md: fixtures derive from the contract). The real field is `first_chapter`.
   - WotW never hit this because it takes the `wardrobe_by_chapter` path.
2. **11 of Scarlet's 26 bound rows have no dossier at all** (`analysis/characters/<id>.json` is missing): wiggins, madame_charpentier, alice_charpentier, lucy_ferrier_child, joseph_stangerson_young, enoch_drebber_young, unnamed_sentinel, cowper, drebber_wife, jefferson_hope_cabman and police_inspector. `looks_table.card_of` raises `FileNotFoundError`.
3. **9 of the 15 rows that have a dossier name no head** (Holmes, the sergeant, Lucy, Stamford, Rance, Sawyer, Arthur Charpentier, Brigham Young and Drebber), **but 26/26 Scarlet refs.json rows do name a head in `physical`.** Holmes's row, for example, reads "dark hair swept back …, clean-shaven". The bound sheet was drawn from exactly those words.

### Cure (`scripts/refs/looks_table.py` + `studio/look_timeline.py`, test-first)
- (a) `dossier_text` reads `card['first_chapter']`, and the fixture is rebuilt from a real dossier's keys.
- (b) **The head comes from the bound row when the dossier is silent.** `with_head` and `markers_from` take `fallback=row['physical']` and use it per layer only where the dossier's physical has none. The bound sheet and the judge then read the same words.
- (c) **A row with no dossier, or a legacy book with cards**, is built from refs.json:
  - each `wardrobe` card (indoor/outdoor) becomes a look via the existing `dossier_look(row.physical, wardrobe[card], base)`, with the base on the first card;
  - this matters because **9/26 Scarlet rows change hat by card** (Watson's bowler outdoors, Ferrier's felt hat, Rance's helmet, …), so a single "base" look would make LOOK-STATE refuse every outdoor card.

**Replay (CPU):**
- Scarlet: **0/26 refused**.
- WotW: 0/26 refused and its tables are byte-identical (they never touch the fallback).
- **Jekyll and Hyde are still refused.** Their refs.json physical is empty too, so the wall stays exactly where C1 put it, and the cure there is the pending owner look ruling.

It is never a wall that blocks Scarlet.

---

## 5. The C1 hypotheses

### 5a. Cast drift: a cast row's staged sheets are different men. Confidence 95 %, ≥ 2 cases, measured

**Instrument** (`j_headcos.py`): MTCNN on the head region (top 35 % of a full-body sheet, upscaled), keeping faces with p > 0.95, then the VGGFace2 cosine. Calibrated on the same run:
- same-man versions: Holmes 0.82, Watson 0.84-0.95, Lucy 0.89, Drebber in/out 0.88, Hope dd298/102857/0c68 0.80-0.89, Brigham in/out 0.96;
- **cross-person median 0.19, p95 0.45, max 0.68.**

The full-sheet version (`j_lineage.json`) is **unreliable**: Hope 8826eb07 has a "face" box 0.70 of the frame tall, which is a false detection.

| Row | Pair | cos | Story time | Verdict |
|---|---|---|---|---|
| **jefferson_hope** | `char-jefferson_hope_indoor_8826eb07` (ep07) vs dd298c29 / 102857b4 / cabman 0c68eeba (ep09-14) | **0.453 / 0.457 / 0.460** | 1881 vs 1881 (ep07 against ep13-14) | **Different man**: at the cross-person p95. This reproduces C1_L's 0.41-0.44. By eye (`lineage_scarlet.jpg`): long hair and a long full beard against short hair and a short beard |
| **brigham_young** (new) | `char-brigham_young_c9192677` (ep08) vs indoor 2669f3d2 / outdoor c1d82748 (ep10) | **0.235 / 0.158** | 1847 vs about 1860 | **Different man**: near the cross-person *median*. By eye: a lean, dark-haired, clean-shaven 35-year-old against a heavy, grey, jowled man. A 13-year age-up does not explain a build change. Same entity id, with no `_young` row |
| john_ferrier | 7e1cc905 (ep08) vs indoor/outdoor (ep09-12) | 0.558 / 0.575 | 1847 vs 1860 | Intended age-up, done as a redraw (curly chestnut hair and a fur cap against short grey hair). Borderline; logged |
| *control:* drebber / stangerson young vs old (separate `_young` rows) | | 0.60-0.63 / 0.58 | | A separate row redrawn from a shared description holds about 0.6. A same-row redraw (Brigham) does not |

**Fix: G-LINEAGE, CPU, a refs step.**
- On every new sheet version of a cast row, run this head-crop facenet against all earlier staged versions of the same row.
- A pair < 0.60 (MATCH) on a row with no `_young` / age-up marker **refuses the new version**, and the cure is to redraw it one hop from the previous version.
- An age-up row (story-time gap ≥ 10 years, read from the timeline track) is an **advisory**.
- **Replay acceptance:** fails exactly Hope 8826eb07 and Brigham c9192677; passes Holmes, Watson, Lucy, Drebber and Lestrade; flags Ferrier as an advisory.

**WotW is not scored.** Its staged names are `sheet_<md5>` with no character stem. Attributing them through one-face takes put the same file under 2-3 characters (`j_lineage.json`, e.g. `sheet_5d3153e0` under both the narrator and ogilvy), so those numbers are void. A correct attribution needs `staged_name()` over every historic sheet file, and only the current versions are on disk. Hypothesis.

### 5b. Flashback story time: the look timeline keys on reading order. Mechanism confidence 90 % (code + 3 ledgers); a live mis-pick is a hypothesis because no Scarlet table has been written

- `CharacterLooks.look_id_at(chapter, scene)` (`studio/continuity_spec.py`) walks spans sorted by **reading order**.
- A span with `until=None` runs until the next span starts.
- `analysis/timeline.json` already holds the tracks: **Scarlet `flashback: [8-13]`, `main: [1-7, 14]`; Jekyll `flashback: [10]`; WotW `main` only.** **Nothing in `studio/` reads them** (grep).

**Measured ledgers** (`appearance_rows` over the real Scarlet dossiers):

| Row | First appearance row | What reading order then does |
|---|---|---|
| Jefferson Hope | ch7 "cut and bloodied" (1881) | **Nothing changes his look in ch9-11** (Utah, 1860), so an injury look opened at ch7 runs into the young hunter. His beard row is filed at **ch13** ("grows his beard as a disguise", told in the confession), but he already wore it in ch7 |
| Joseph Stangerson | ch7 "found with a fatal stab wound" (1881) | The corpse look runs open into ch8/11/12, where he is alive in Utah |
| Enoch Drebber | a ch6 row (1881, dead) | Precedes his living ch11-12 Utah rows |

The `APPEARANCE` regex also lets "Ferrier rejects the **suit**ors" into two ledgers (`suit\w*`). That is a precision case for C1 hypothesis 8.

**Fix (code, test-first, book-neutral):**
- `Span` and `look_id_at` take the **track**, read from `analysis/timeline.json`.
- `look_id_at(chapter)` considers only spans on the chapter's track, and an open span never crosses into another track.
- A track with no span of its own starts from the base look.
- Injury and death looks get `until` = their own chapter unless the ledger repeats them.
- **Test fixture:** Scarlet's real `timeline.json` tracks, plus Hope/Stangerson-shaped ledgers. ch9 must not pick the ch7 look.
- WotW's single track leaves every table byte-identical.

**Caveat:** Scarlet ch13 mixes the 1881 frame (Hope's statement at the station) with the 1860s confession, so chapter granularity is not enough there. It needs a scene-level track from `timeline.json` `scenes`. That is logged and not designed here.

---

## Summary table

| # | Issue | Confidence | Fix | Cost |
|---|---|---|---|---|
| 1 | LOOK-STATE hat: no headwear family (7/8 reads say `other_hat` for a felt hat); writer table mis-maps 8/61 WotW looks (top hat, billycock, pork-pie, wide straw hats) | 95 % | `HEADWEAR_FAMILY` brimmed = {felt_hat, other_hat, bowler}; regex fixes | CPU, 1 commit |
| 2 | The regrid bar counts back and far views | 95 % (ep25 2/2, ep27 3/3; round 0 still 0/1) | A face-visible denominator from the plan (`from behind`, wide sizes); an empty denominator is unmeasurable | CPU, 1 commit |
| 3 | Ghost faces from the USDU full prompt per tile | 95 % issue (2 cases: the ragged_greyed thighs, and **the narrator base sheet backdrop, staged ep18-27**). 1/33 base sheets by eye | New `image_krea2_cinematic_2x_neutraltile_visurena.json` (style-only tile prompt); 6-min GPU A/B; narrator sheet redraw = owner ruling | GPU bench |
| 4 | Scarlet look table impossible: `appearances` int crash (all dossiers), 11/26 rows have no dossier, 9/15 dossiers have no head | 100 % | `first_chapter`; head fallback from refs.json physical (26/26 have one); cards become looks (9/26 change hat by card) | CPU, 1 commit |
| 5a | Cast drift across sheet versions | 95 % (Hope 0.45-0.46; **Brigham Young 0.16-0.24, new**) | G-LINEAGE head-crop facenet < 0.60 refuses a new version | CPU, 1 commit |
| 5b | Flashback: looks keyed on reading order | 90 % mechanism; a live mis-pick is a hypothesis | Track-aware `look_id_at` from `analysis/timeline.json` | CPU, 1 commit |

**Publishable (flag):**
- "One prompt per tile paints faces": a 1x/2x same-seed A/B plus a backdrop case, and MTCNN's failure on stylized ghosts.
- The head-crop facenet lineage check, with its calibration (same-man 0.80-0.96 against cross-person p95 0.45).

Both fit the planned public storyboard/ref bench.

**Sources:**
- [Replicate: SD Ultimate Upscale guide](https://frontend.replicate.com/guides/upscaling-images/sd-ultimate-upscale)
- [Replicate: ControlNet tile guide](https://internal.replicate.com/guides/upscaling-images/controlnet-tile)
- [comfy.icu: UltimateSDUpscale node](https://comfy.icu/node/UltimateSDUpscaleNoUpscale)
- [ComfyUI: different prompts for each tile in SD Upscale](https://tap-app-api.adeq.arkansas.gov/post/comfyui-different-prompts-for-each)
- [r/StableDiffusion: tile ControlNet strength and denoise](https://reddit.fabiomanganiello.com/r/StableDiffusion/comments/135jffn/extreme_8x_upscale_of_a_640x480_gif_using_sd)
- [RunComfy: Flux upscaler, TTP tile and face restore](https://www.runcomfy.com/comfyui-workflows/flux-upscaler-ttp-tile-face-restoration-4k-upscaling)
