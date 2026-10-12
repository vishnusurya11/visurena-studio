# D — How to keep a recurring location the same place across 27 episodes

Date: 2026-10-10. Researcher D, continuity retro. Scope: the narrator's house in The War of
the Worlds. Web research (cited inline, 2025-2026 sources preferred) plus a short look at
what is on disk, so the advice is aimed at the failure that actually happened.
Evidence sheets: `docs/audit/2026-10-10_continuity_retro/D_evidence/*.jpg`.

## 0. What the disk says (read this first; it changes the question)

**The hypothesis "the location ref was not passed in late episodes" is false for the house.**

- ep26 `villa_front` grid (`ep26/storyboard/grids/ep26_grid_villa_front_3x1.png`, embedded
  graph): exactly one LoadImage, `wide_establishing_7972962f.png` = the book's
  `refs/locations/narrators_home/wide_establishing.png` (drawn 2026-09-18). The panels and the
  H3 take T15 (staged: narrator sheet + `shot_15` panel) show the same villa: two bays, red
  tiled door canopy, beech trees on the left, gate piers (`D_evidence/house_compare.jpg`,
  `D_evidence/t15.jpg`). The front of the house held from ep01 to ep26.
- **The drift is in the book's own reference set.** The house is split across **4 location
  ids and 17 separately drawn pictures**, and every setup picks one of them:

| episode | setup -> location / view |
|---|---|
| ep01-03, ep07 | narrators_home (wide), narrators_study (wide) |
| ep09 | narrators_garden / wide_morning |
| ep10 | narrators_home / interior_hall_staircase |
| ep11 | narrators_study / interior_window_fire_night, window_view_valley_fire_night, window_view_ashes_dawn; narrators_home / dining_room_unlit_night; narrators_garden / wide_lawn_palings_night |
| ep26 | narrators_home / wide_establishing; **narrators_dining_room** / medium_french_window |
| ep27 | narrators_study / wide_establishing, medium_writing_table, window_view_panorama, **reverse (drawn 2026-10-09)** |

- Each view was drawn from words, so each is a different room. **Dining room:** three rooms.
  One has floral paper, a sash window and a clothed square table. One has dark damask and a
  round table. One has red damask and French windows (`D_evidence/dining.jpg`), and they sit
  under two location ids. **Study:** the wide has French windows onto a balcony. ep11's
  `interior_window_fire_night` has a sash window and a spindle chair. ep27's `reverse` has a
  door, a fireplace and a wall map that nothing else shows (`D_evidence/study_refs.jpg`).
  **Porch:** `medium_front_door_porch` has a slate gabled canopy, a fanlight and a bay. The
  wide has a small red tiled canopy (`D_evidence/house_compare.jpg`).
- This is the observatory fault of 2026-09-18 again: "each separately drawn view had become a
  different room". The owner answered it with ONE wide per location (memory
  `one-sheet-per-character`). The rule was never enforced on the refs folder. `places.py`
  kept adding views (`--new=`) and every episode's "picture at this hour" was a fresh draw.
  Within one episode, P1's anchor chain (2026-09-28) holds a setup to one render. **Nothing
  holds a place across episodes, across views, or across ids.** ep27's `study_reverse` is
  the newest instance of the fault.
- Book fact for the state model: the "ruined house at Sheen" (Book II ch.1-4) is a
  **different house** from the narrator's villa at Maybury. The villa's own states are: intact
  night/morning (ep01-03), the night watch at the study window with the valley burning (ep11,
  I.11 "At the Window"), and the return in II.9 "Wreckage" (ep26): front door forced, stair
  carpet ruffled and discoloured, study window open, his unfinished paper still on the table.
  Then the epilogue study (ep27). Sheen gets its own master. It must not be modelled as a
  state of the villa.

So the design question is: **how does a place keep ONE geometry across views, hours and
states without being redrawn from words each time?**

## 1. How productions do it: the data model to copy

- **The set is built once, and every later appearance is a redress of the same build.** A
  set redress "is the redecoration of an existing movie set so that it can double for
  another set". The listed continuity risk is that "the set dresser may be unaware of
  changes created by the action" ([Wikipedia: Set redress](https://en.wikipedia.org/wiki/Set_redress)).
  Episodic TV keeps standing sets across a season, and the DP decides each time whether to
  match the earlier look ([ASC Shot Craft: Fresh perspectives](https://theasc.com/blog/shot-craft/fresh-perspectives)).
  When a standing set was lost (the U.N.C.L.E. tailor shop burned), later episodes reused
  **stock exterior shots** of it rather than build a new one ([manfromuncle.org](https://www.manfromuncle.org/kcretro7.htm)).
  In other words: one establishing exterior, reused for the whole run.
- **Continuity is recorded as photos of the set state, tied to scene numbers.** Continuity
  scripts carry Polaroids of "sets and set dressing, props, and actors' costumes"
  ([SLSA continuity script](https://collections.slsa.sa.gov.au/resource/PRG+1726/3/7)).
  Changes are "updated on an ongoing basis and … recorded on script breakdown"
  ([training.gov.au CUFCOS301A](https://training.gov.au/Training/Details/CUFCOS301A)).
  Progressive damage is tracked the way wardrobe uses **breakdown charts**: one item, numbered
  states (clean, dirty, torn), and each state mapped to scenes. Script supervisors do the same
  for injuries that progress across story time
  ([nofilmschool: scripty](https://nofilmschool.com/scripty-most-important)). No source
  described a "damaged-set ledger" by name. The structure below is the wardrobe breakdown
  chart applied to a set.
- **Data model to copy (set bible):**

```
Place (book-level, one per physical place; "narrators_villa")
  geometry      : fixed features + where they stand (walls, windows, doors, fireplace, stair)
  masters       : one plate per SIDE actually needed (front_ext, study_wide, study_reverse,
                  dining_wide, hall) -- each drawn ONCE, then frozen; every other side is
                  derived FROM an existing master, never from words
  states[]      : ordered, each tied to chapters: intact -> night_watch(fire) -> abandoned
                  (door forced, carpet ruffled) -> restored ; a state = a delta list on a master
  variants      : (master, state, hour) -> picture, derived from the master in ONE hop
Setup.location  -> Place + master ; Setup.state + hour -> variant (never a fresh draw)
```

`narrators_home`, `narrators_study`, `narrators_garden` and `narrators_dining_room` become
masters of one Place. Sibling ids are what let ep26 pick a third dining room.

## 2. AI techniques for a persistent location

**2a. Master plate plus per-state variants, by edit or by regeneration.**
- Regeneration from words gives a new room every time. That is the disk evidence above, and
  vendor guides say the same: "A cozy kitchen with morning light" makes the model "invent a
  slightly different kitchen each time"
  ([Higgsfield guide 2026](https://higgsfield.ai/blog/consistent-characters-locations)).
- Edit from the master. The closest fit is the **Qwen-Image 2.1 Consistency LoRA** (ausboss,
  updated 2026-09-28), which runs on the base model the studio already uses for grids. It
  addresses exactly this: plain 2.1 "re-composes the whole picture". With the LoRA, median
  worst-corner drift on restyles falls from **24.3 px to 1.6 px**, and the area changed
  outside the edit falls from 12.8 % to 7.5 %. Relighting and object removal are among its
  examples. It runs at 25 steps, CFG 1, strength 1.0, ~1 MP, with the latent kept at the
  input size. It is **untested with turbo LoRAs**, it **ignores edits that need movement**,
  and it carries the **Qwen Research License**, which needs checking for a monetised channel
  ([HF model card](https://huggingface.co/ausboss/Qwen-Image-2.1-Consistency-LoRA),
  [comfyui-wiki news 2026-10-01](https://comfyui-wiki.com/en/news/2026-10-01-qwen-image-2-1-consistency-lora)).
  A state such as "door forced, carpet ruffled, window open" is a small, local, non-moving
  edit, which is the case this LoRA is good at.
- **Star topology, never a chain.** Each variant is one hop from the master. Repeated edits
  decay. Banana100 found visible quality loss after ~5-10 consecutive edits, and that none of
  21 no-reference IQA metrics reliably flags the decay
  ([arXiv 2604.03400](https://arxiv.org/abs/2604.03400v1)). FreqEdit shows FLUX Kontext and
  Qwen-Image losing high frequencies across turns ([arXiv 2512.01755](https://alphaxiv.org/overview/2512.01755v1)).
  Agent Banana names "Prior-Induced Editing Drift", where unedited regions slide toward the
  model's preferred textures ([arXiv 2602.09084](https://arxiv.org/pdf/2602.09084)).
  So `abandoned` = edit(master), never edit(night_watch).
- **One change per pass** and a stated invariant list. This is the common Kontext advice:
  "keep the original composition", keep the subject "in the exact same position, scale, and
  pose", and split compound edits because they drift
  ([ComfyUI Kontext docs](https://docs.comfy.org/tutorials/partner-nodes/black-forest-labs/flux-1-kontext)).

**2b. Other sides of the same set (the reverse, the porch close).**
- **Multi-angle LoRAs.** fal's Qwen-Image-Edit-2511 Multiple-Angles LoRA covers 96 poses
  (8 azimuths × 4 elevations × 3 distances) and was trained on 3000+ pairs rendered from
  Gaussian splats, with the prompt form `<sks> back view eye-level shot wide shot`
  ([HF card](https://huggingface.co/fal/Qwen-Image-Edit-2511-Multiple-Angles-LoRA)). The
  older dx8152 2509 LoRA's author admitted "unstable consistency" and retrained it in
  Nov 2025 ([Replicate readme](https://replicate.com/qwen/qwen-edit-multiangle/readme)).
  The cards show products and subjects, not interiors. **A 180° turn on a room must invent the
  unseen wall anyway.** Its value is that the invention happens once, conditioned on the
  master's materials and light, and is then **frozen as a second master**. It is not
  re-invented per episode.
- **Panorama / 3D.** Qwen 360 Diffusion (rank-128 LoRA on Qwen-Image, equirectangular
  2048×1024) gives one 360° plate per interior. Every reverse and side angle then becomes a
  crop or reprojection of the same pixels ([HF README](https://huggingface.co/ProGamerGov/qwen-360-diffusion/blob/main/README.md)).
  The FLUX.2 Klein ERP-outpaint LoRA plus Panorama-Stickers can outpaint an EXISTING plate
  into a full ERP ([HF](https://huggingface.co/nomadoor/flux-2-klein-9B-360-erp-outpaint-lora)),
  which would keep the current study wide. HunyuanWorld 1.0-Lite fits in <17 GB. Voyager
  wants 60 GB, so it is out of reach for a 4090
  ([The Decoder](https://the-decoder.com/tencent-releases-hunyuan-world-model-1-0-lite-for-faster-resource-efficient-3d-scene-generation/),
  [comfyui-wiki Voyager](https://comfyui-wiki.com/en/news/2025-09-05-tencent-hunyuanworld-voyager-3d-video-generation)).
  The research direction agrees: Map2Video grounds every shot in one shared coordinate frame
  and avoids generated reference images because they are "themselves inconsistent"
  ([arXiv 2512.17883](https://arxiv.org/html/2512.17883v1)). This is the best long-term
  answer for interiors (study, dining room), but it is a new model plus a new projection
  step. It belongs in phase 2.

**2c. Passing the location into the multi-reference models, and slot competition.**
- **Grids (Qwen-Image 2.1 edit-multi, 1-3 slots):** slots are scarce. The studio already
  puts cast sheets first and the place last. The 2026-09-28 audit measured that the drawer
  follows prose over the plate and holds the room per RENDER.
- **H3 ref2va (≤9 pictures):** the takes stage the character sheet plus the shot's panel
  (`ep26 T15.graph.json`), so the place reaches H3 through the panel's pixels. That works if
  the panel is right. H3's own guide lets a `<Subject N>` be "Scenes, backgrounds, or
  environments" (`docs/calibration/h3_ref_guide.md`), so a place plate could be added as a
  subject. But it is the same place as the panel, and memories `no-composed-frame-zero` and
  `h3-freeze-and-hardcut` record that an extra staged picture of the place produces hard cuts
  ("opened on another staged picture"). **Recommendation: do not add a place slot to H3.
  Fix the place upstream, in the picture the panel is drawn from.**
- Evidence on competition: no controlled test of background-vs-character was found. Research
  shows that extra references raise copy-paste and dilute identity
  ([MAGREF arXiv 2505.23742](https://arxiv.org/pdf/2505.23742),
  [Identity-Motion dilemma](https://www.alphaxiv.org/overview/2603.21299)). Kling's guide
  says to state which reference supplies subject, environment and style
  ([Kling Element Library](https://kling.ai/quickstart/klingai-element-library-3-user-guide)).
  Practitioners add one reference at a time and measure the loss
  ([WaveSpeed](https://wavespeed.ai/blog/ai-guides/prepare-multi-reference-video-assets/)).
- **The most directly transferable system is CANVAS** (2026), a storyboarding agent. Its
  memory is ℳ = (characters, **locations**, frames), and ℳ_l stores "background anchor images
  associated with locations". Retrieval depends on the case. A continuing scene uses the
  previous frame. **A revisited location from a new viewpoint uses the stored location
  anchor.** A first appearance uses characters only. When an object transition changes the
  location's structure, the system extracts **a new anchor and overwrites ℳ_l**, which is
  their state change. Removing location grouping or background reuse cut background
  consistency by **50-57 %**. Reported gain: +21.6 % background continuity
  ([arXiv 2604.13452](https://arxiv.org/html/2604.13452)). That is the data model in §1,
  shown to work and ablated.

## 3. Prompting a place so it holds

- **Words pin what the picture leaves free. They never re-describe the room.** This is the
  2026-09-28 brick and the vendor advice
  ([Higgsfield](https://higgsfield.ai/blog/consistent-characters-locations)), and the
  observatory, the dining rooms and the study all confirm it.
- **Name the fixed features with their frame position, from the picture** (ep09-11 held with
  4-8 CAPS position tokens per shot). The fixed set should be what CANVAS's judge scores:
  "walls, doorways, windows, pillars, floors", with movable props and light excluded
  ([CANVAS](https://arxiv.org/html/2604.13452)). For the study, the list is: French windows
  CENTRE, green-shaded lamp on the writing-table LEFT, glass-fronted bookcase RIGHT, globe
  right of the table.
- **Grid role sentence:** state roles explicitly, using the Kling pattern ("Image 2 is this
  exact room …"; P1 already does this).
- **A changed state is written as a delta on the same room, never as a description of a
  room.** Use: same room as Image 1, same walls, windows and furniture in the same places;
  ONLY change: the front door stands forced open, the stair carpet ruffled and stained, dust
  on the table. Make one change per pass and list the invariants
  ([ComfyUI Kontext docs](https://docs.comfy.org/tutorials/partner-nodes/black-forest-labs/flux-1-kontext)).
  Put the defining state first (SKILL: "a detail buried mid-sentence is dropped").
- Time of day: use an hour/light phrase on a Consistency-LoRA edit of the master, never a
  redraw. dx8152's Relight LoRA exists for 2509, but it neutralises light rather than setting
  an hour ([HF](https://huggingface.co/dx8152/Qwen-Image-Edit-2509-Relight)).

## 4. Automated verification

- **Embeddings, calibrated per studio:** no source gives a universal threshold. DINOv2-VLAD
  (AnyLoc-style) loop closure found verified same-place pairs at median cosine **0.81-0.90**
  and different places from the same sequence at **0.5-0.7**. A 0.60 gate was useless
  ([arXiv 2607.01757](https://arxiv.org/pdf/2607.01757)). DreamSim (CLIP+DINO+OpenCLIP
  ensemble, human-aligned) is the alternative ([github ssnl/dreamsim](https://github.com/ssnl/dreamsim)).
  VBench's "background consistency" is CLIP ViT-L/14 cosine against the first and previous
  frames. It rewards blur and static output, so it is unusable as a wall
  ([VBench summary](https://www.emergentmind.com/topics/vbench),
  [Hi-Light CVPRW 2026 supp.](https://openaccess.thecvf.com/content/CVPR2026W/CVEU/supplemental/Liu_Hi-Light_A_Path_CVPRW_2026_supplemental.pdf)).
  The studio's own measurement agrees: hue, Lab and pHash separate nothing
  (`docs/calibration/panel_place.md`).
- **VLM structural judge, the one that matches what the owner sees:** CANVAS ContinuityEval.
  A VLM compares two frames on fixed architecture only and counts appear / disappear / layout
  violations, discounting what the camera move explains.
  GeomCons = 100·(1 − violations / max(N_A, N_B)), banded 90-100→5, 75-89→4, 55-74→3,
  30-54→2, <30→1. With Gemini-2.5-Flash as judge, **Fleiss κ = 0.74 vs humans**
  ([arXiv 2604.13452](https://arxiv.org/html/2604.13452)). TinyHistory uses a gate question
  ("is an environment visible?") and then three yes/no stability sub-questions (layout,
  lighting, details) ([arXiv 2512.23851](https://arxiv.org/pdf/2512.23851)). This is the
  "VLM furniture-per-wall rung" the 2026-09-28 audit left open. Build it list-then-judge-in-code,
  as `panel_content` does: the VL lists the fixed features per wall for the master once
  (cached), lists them per panel, and code counts the violations.
- **Thresholds to start (advisory, then calibrate on the owner-judged episodes per memory
  `gates-are-not-quality`):** variant vs master GeomCons ≥ 75 (band 4) to accept a derived
  variant. Panel vs master: flag < 55. DINOv2 global cosine as a cheap pre-screen, with the
  band set from this book's own same/different pairs (the 17 house pictures above are a ready
  negative set). Exempt a planned reverse, as `panel_place` already does.

## 5. Time on the 4090 (measured where we can; estimates marked)

| item | cost | source |
|---|---|---|
| a place draw today (places stage, per episode) | 60-370 s (ep24-27 timing.jsonl); ep27's lone `reverse` 127 s | measured |
| a grid draw (Qwen-Image 2.1, 1-4 cells) | 31-77 s | measured, ep25-26 |
| Consistency-LoRA edit of a master, 25 steps, ~1 MP | **~60-90 s est.** (same base model as grids, no turbo) | estimate; LoRA card gives no inference time |
| multi-angle / reverse master (one-time per Place side) | ~60-120 s + look | estimate |
| VL fixed-feature list, per picture (VL resident) | ~10-20 s est.; master's list cached | estimate |
| DINOv2 pre-screen | <1 s/pair | estimate |

Per episode under the recommendation: a recurring place has 0-2 derived variants
(state/hour), so **~2-5 min including the judge**. That replaces the 1-3 fresh draws it would
otherwise make (~2-6 min). **Net change ≈ 0 against the ~6.0 h median; a held place
saves its own redraws.** One-time book cost: consolidating the villa into one Place with 4
masters (front, study wide, study reverse, dining) is ≈ 10-15 min GPU plus an owner look.
Panorama/3D (phase 2) is a separate bench, ≈ half a day.

## 6. Recommendation

1. **One Place, few masters, frozen.** Book-level `Place` rows (§1 model) above `location`.
   The four `narrators_*` ids become one `narrators_villa`. Keep the masters that are
   mutually consistent: the front wide, the study wide, `medium_writing_table` (same lamp,
   desk and window). Retire the rest to `_rejected`: the 3 dining rooms but one, the sash-window
   fire night, the off-model `reverse`, and the porch close. A guard test refuses a second
   picture of a side that already has a master, and refuses `--new=` for a view of an existing
   Place unless it is derived (step 3). **This alone fixes most of what drifted.**
2. **Hour and state are edits of a master, one hop, never draws.** Use Qwen-Image 2.1 + the
   Consistency LoRA, a delta prompt with an invariant list, one change per pass, and seed
   fixed per (Place, master, state). States are declared in the Place row and mapped to
   chapters (villa: intact, night_watch_fire, abandoned [II.9], epilogue).
3. **A new side (a reverse) is derived once from a master** (multi-angle LoRA, or an outpaint
   of the master) and is judged and frozen as a master. It is never drawn from words.
4. **Judge every derived picture before anything is built on it:** ContinuityEval-style VLM
   fixed-feature violations vs the master (accept ≥ 75), a DINOv2 pre-screen, and the owner's
   look the first time a Place gets a new master.
5. **Do not add a place slot to H3.** The panel carries the place. Keep the grid plate/anchor
   chain from P1, but stage the Place's master or derived variant, never a per-episode redraw.
6. **Phase 2 (bench before adopting):** one 360° ERP plate per recurring interior (Qwen 360
   LoRA, or ERP outpaint of the existing wide). Every view becomes a reprojection of the same
   pixels.

**Owner ruling needed (docs/DECISIONS.md):** recommendation 2 relaxes the 2026-09-18 "do NOT
derive views with Qwen-Image-Edit" text. Note that the failure behind that rule was
separately DRAWN views, which is the same failure found here, and the text itself said "for
now". Ask: allow derived state/hour/side variants of a location master on Qwen-Image 2.1 +
Consistency LoRA, gated by the fixed-feature judge (yes/no), and confirm the LoRA's Qwen
Research License is acceptable for the channel. Without the ruling, steps 1, 4 and 5 still
apply, and states go to words in the take prompt as the 09-18 rule says.

**Publishable:** the Place/master/state ledger plus the fixed-feature VLM judge
(list-then-count, calibrated on a real 27-episode series with owner verdicts) is
generalisable beyond this repo. It could ship as a standalone "set bible" package or ComfyUI
node, and as a short benchmark note on cross-episode location drift.
