# C1-L: looks, the Scarlet replay set, and the Jekyll/Hyde probe

Cycle 1, researcher L. 2026-10-11. CPU and reading only: no GPU, no code edits, nothing under `library/` was written.

Evidence (contact sheets, logs and the scripts that rebuild them) is in the session scratchpad:

`D:\temp\claude\d--Projects-KingdomOfViSuReNa-alpha-visurena-studio\53388bed-712c-4d9b-972d-6c2de9a9f94e\scratchpad\c1\`

| File | What it shows |
|---|---|
| `wotw_beards.png` | Face crops of six WotW base sheets whose prompts name facial hair |
| `ghost_thighs.png` | 2x crop of the ragged_greyed thighs, with the two ghost faces |
| `base_face.png` | The narrator's base sheet face (day_suit) |
| `scarlet_221b_plates.png` | 12 plates of the 221B sitting-room, ep02 to ep14 |
| `scarlet_ferrier_parlour_plates.png` | 5 plates of the Ferrier parlour, ep09 to ep11 |
| `scarlet_lauriston_plates.png` | Lauriston Gardens, exterior and front room, ep03, ep04, ep13 and ep14 |
| `scarlet_holmes_sheets.png`, `scarlet_watson_sheets.png` | Every Holmes and Watson sheet version that was staged |
| `scarlet_utah_sheets.png` | The Ferrier and Jefferson Hope sheet versions |
| `scarlet_holmes_low_takes.png` | Frames of the lowest-scoring identity takes |
| `hw_identity.json`, `hw_identity.log` | facenet scores for every single-face Holmes or Watson take |
| `scarlet_inv.json` | All 353 shipped Scarlet takes: setup, faces, lane and staged images |
| `jh_sheets.png` | The current Jekyll, Hyde and Utterson sheets |

Scripts in the same folder: `prompts.py`, `ghost.py`, `ghost2.py`, `faces_sheet.py`, `contact.py`, `scarlet_inv.py`, `hw_identity.py`, `sheet_cos.py`.

---

## Issue 1a: the ep25 `ragged_greyed` look was drawn without a beard. Confidence 95 %.

### What was sent
The prompt was rebuilt on CPU by `prompts.py`, which runs the real `looks.fresh_prompt` and `refs_pack.styled`.

The look has `face_change=True`, so it takes `route = fresh`. That route is a Krea2 text-to-image draw:
- workflow `image_krea2_cinematic_2x`: krea2 turbo fp8, Cinematic_Artstyle LoRA at 1.0, 8 steps, cfg 1.0, er_sde, then a 2x USDU pass at denoise 0.2;
- seed 4165438081, the base sheet's own seed, then +1 and +2 on the redraws.

The prompt, after the style lead:

> `... Cinematic film still of Hair turned ash-grey throughout and grown shaggy over the ears. Sixteen days of grey-brown beard; face gaunt, cheekbones sharp. Battered brown felt hat. ... Man of 34, ... Character reference sheet ...`

On the redraw the faulted layer moves to the front ("Sixteen days of grey-brown beard; ..." first). It made no difference.

### What came back
- **Seed 0**: the crop `replay/ep25_fulham_road*/looks/unnamed_first_person_narrator/ragged_greyed.png` (md5 29c775a3 in both runs) and the run-1 sheet. Clean-shaven: not even the base sheet's moustache. Grey hair, hat and shirt are all right.
- **Seed +2**: the run-2 `ragged_greyed_sheet.png`. Clean-shaven again, in all five views and the face close-up.
- LOOK-STATE read `facial_hair none` against `beard` on all three draws (run-2 `report.json`), so the climb ended `keep_best`.

### Root cause: the wording, measured on the model's own base sheets
Krea2 with the Cinematic LoRA draws facial hair only when the prompt names it as a plain full-beard noun. It drops duration wording, stubble wording and qualified wording. From `wotw_beards.png`:

| Sheet | Prompt words | Drawn? |
|---|---|---|
| captain | "Full iron-grey beard trimmed square" | **beard drawn** |
| ogilvy | "Full close-cut auburn beard shot with grey" | **beard drawn** |
| lord_garrick | "Short square-cut white chin beard along the jaw with a shaven upper lip" | none |
| narrators_brother | "three days of dark stubble" | none |
| unnamed_gardener | "Short white stubble over jaw and chin" | none |
| artilleryman | "black stubble" | none (his "full black moustache" was drawn) |
| ragged_greyed | "Sixteen days of grey-brown beard" | none, 3 of 3 draws |

That is 2 of 2 "Full ... beard" wordings drawn, against 0 of 7 duration, stubble or qualified wordings. The angular art style renders a face as flat facets, so stubble, a fine texture, has nowhere to go. "Sixteen days of" reads as stubble.

**The beard was encoded, then misplaced.** The ghost face on the right thigh of the seed-0 picture has grey hair and a grey beard (`ghost_thighs.png`). The concept reached the image but was bound to the wrong region: attribute leakage, as in Rassin et al. 2022 and arXiv 2404.13766.

A contributing cause in the prompt's form: it opens "Cinematic film still of **Hair** turned ash-grey ...", and the person noun ("Man of 34") only arrives after every look layer. The attributes have no subject to bind to. This part is a hypothesis: it is plausible, but it has not been isolated.

### A second, independent gap: the grid words
The setup's shot tags in the ep25 plan omit the beard on 4 of 12 tags. For example, fulham_road's "(face gaunt, grey eyes, battered brown felt hat)" appears 3 times. A bearded look picture would have been staged beside words that do not ask for a beard.

### Proposed fix (test-first; the GPU bench is one look, about 6 draws)
1. **Words come from the closed marker.** When `markers.facial_hair == beard`, the drawn layer text gets the canonical, drawable phrase `a full short <colour> beard covering the jaw, chin and upper lip`. The duration or stubble wording is kept only as an adjective. When the marker is `stubble`, either draw it as "a short <colour> beard shadow" or record the style limit, so that LOOK-STATE does not demand what the style cannot render. This is one pure function plus a test, in `look_timeline.with_head` or `looks.layers_first`.
2. **Subject noun first.** `fresh_prompt` should read `"A man of 34 with <hair>, <beard>, wearing <hat> ..."`. The hair and face layers then attach to a person, not float free.
3. **Bench B-3 for a face change: the edit route against the fresh route.** Krea2 identity edit (the existing `image_krea2_identity_edit`) of `sheet_front.png` with the canonical beard sentence, against fresh with the canonical sentence. 3 seeds each.
   - Score: LOOK-STATE, eye on the face crop, and a ghost-face count (Issue 1b).
   - The online guidance agrees, though it is weak: an identity-preserving edit should name the beard's style and coverage explicitly ("full beard covering jaw, chin and upper lip; match colour to hair; keep face unchanged"). Qwen-Image-Edit-2511 advertises identity preservation for exactly this kind of edit.
   - No composites, and no masked paste of a head: a masked face inpaint of the beard region of the SAME picture is still one hop. It is not a paste, but the owner should rule on it before it is built.
4. **G-LOOK-WORDS on tags.** It becomes hard on the defining marker: a one-face shot tag for a person whose look carries `facial_hair=beard` must contain the beard phrase.

---

## Issue 1b: ghost faces in the clothing texture. The artefact is confirmed; the cause is a 60 % hypothesis.

**Measured.** The seed-0 ragged_greyed crop has 2 painted faces in the dark, clay-caked trousers. They sit at about y 0.62 to 0.72, at x about 0.30 and x about 0.68. The right one is bearded and grey-haired.
- The seed +2 sheet shows none to the eye.
- `epilogue_home.png` (light herringbone) has none.

So the artefact appears in 1 of 3 saved look pictures, on the darkest, lowest-texture regions that carry a "dirt" instruction.

**The detector we have cannot see them (measured, `ghost.py` / `ghost2.py`).** YuNet (`studio/models/yunet.onnx`) at the house score of 0.5 finds exactly 1 face on the crop: the real one. Tiled, at 0.5 to 2x scale, with CLAHE, at a 0.2 threshold:
- it finds only the right ghost (score 0.26 to 0.38) and never the left;
- it fires false positives on shirt buttons and the pocket at 0.42 to 0.58;
- on `epilogue_home` it fires false positives on the boots (0.21 to 0.42).

The scores do not separate ghosts from noise. A CPU face-count gate built on YuNet would be both blind and noisy.

**Cause: two candidates, not yet separated.**
- (a) The Cinematic/angular LoRA hallucinates a face in a large dark area that carries a texture instruction, the same misbinding as Issue 1a.
- (b) The USDU 2x pass, denoise 0.2 on 1024 tiles. Every tile receives the full prompt ("face close-up", "Long oval face ..."), and a tile holding only trouser fabric is pulled toward drawing the prompt's subject.

Practitioners blame (b) in tiled upscalers ("face words in the tile prompt make faces in non-face tiles"). The usual cures are a neutral or empty tile prompt, a lower denoise, or ControlNet-tile. That attribution comes from forum consensus and my own reasoning, not from a source that shows it.

**Experiment to separate them (GPU, about 2 minutes).**
- Re-render seed 4165438081 with the same prompt through a NEW workflow file, `image_krea2_cinematic_2x_presave.json`, which adds a SaveImage on the 1x VAEDecode. The existing file is not edited.
- If the 1x picture already has the faces, the cause is (a). If not, it is (b), and the fix is an empty or neutral USDU prompt in a new `_neutraltile` workflow.

**Proposed check (works for both causes).** Before a look picture is staged, ask the VLM to list faces, and judge in code, as already done for G-CROWD and drawn-twice:
- ask: "List every face or face-like pattern visible, including faces in clothing, texture, shadow or background, with where it is";
- refuse if the count is more than 1 on a one-figure look crop;
- run it on a CLAHE-boosted body crop below the real face as well.

Calibrate it on the seed-0 crop (must refuse) and on `epilogue_home.png` plus seed +2 (must pass) before arming it.

---

## Issue 2: the Scarlet replay set. Same continuity faults as WotW? Yes for PLACES and a secondary character; no for Holmes and Watson.

Inventory: 15 episode folders (ep01 to ep14 plus ep01_short), 353 shipped r2v takes (278 narration, 75 dialogue), `scarlet_inv.json`. Scarlet runs the older pipeline:
- `char-<id>[_indoor|_outdoor].png` sheets, content-addressed in ComfyUI input from ep04;
- per-episode plates `boards/plates/plate_<setup>.png`, drawn by T2I from the setup's `described` words (`scripts/episode/frames.py: plate`);
- no `refs/looks.json`;
- no `loc-*` anchor was staged in any take.

### 2.1 Holmes and Watson faces: no drift. Confidence 85 %.
- **Identity was never measured on any Scarlet take.** All 353 of 353 `takes/r2v/T*.dq.json` read `identity: not measured`. The facenet group was not installed at render time. **This is a fact (100 %).**
- **Measured now on CPU** (`hw_identity.py`, the identity_gate walls: readable at h ≥ 0.15, frontal at yaw ≤ 0.35, 5 samples per take, facenet VGGFace2 against the base busts):
  - Holmes: per-episode median 0.58 to 0.68 from ep01 to ep13, and 0.489 in ep14.
  - Watson: 0.57 to 0.79.
  - Cross-person maximum: 0.21 to 0.56, with one 0.775 outlier, ep03 T22.
- **Sheet lineage holds:** Holmes bust against indoor 0.813; Watson bust against indoor versions 0.84 to 0.94.
- **The low takes are pose or occlusion, not a new man** (eye check, `scarlet_holmes_low_takes.png`): ep14 T12 has a magnifier over the eye (0.29); ep14 T22 has the head thrown back (0.19); ep03 T21 is crawling (0.26).
- **Open for the eye:** ep03 T22, a Holmes-only dialogue take where some sampled face scores Watson at 0.775. It may be a second person entering.

### 2.2 Places: the same drift as WotW's house. Confidence 95 %, 4 places.
Each plate is a fresh T2I draw from words. The room holds when the words were copied verbatim and drifts when they were rewritten. Text similarity against the first episode's `described` (difflib) predicts it:

| Place | Episodes | Text similarity | What the eye sees |
|---|---|---|---|
| 221B sitting-room | ep02 to ep07 | 0.39 to 0.58 | One room: fireplace at left, two sash windows in the far wall, door and sofa at right, red Turkey carpet |
| 221B sitting-room | **ep14 `sitting_room_evening`** | **0.15** | A different room: curtained windows, a warm palette, another mantel and door |
| Ferrier parlour | ep09, ep10 ×2, ep11 ×2 | 0.27 to 0.32 | Five rooms: stone hearth at left, then a whitewashed chimney at the back, then a cast-iron stove; the window moves from far wall to left wall |
| Lauriston Gardens exterior | ep03 `garden_path` against ep14 `garden_path_morning` | n/a | Different house fronts, garden layouts and gates |
| No. 3 Lauriston Gardens front room | ep03 `front_room` against ep13 `brixton_front_room` / ep14 `lauriston_front_room` | n/a | ep03 drew an open-fronted cutaway room seen from the garden; ep13 and ep14 drew a yellow, peeling closed room |

### 2.3 A secondary character's identity break, which WotW also had. Confidence 90 %.
Jefferson Hope in 1881 is staged on two different men:
- **ep07 T23** (the arrest at 221B) uses `char-jefferson_hope_indoor_8826eb07.png`, a long full beard and long hair;
- **ep13 and ep14** use `..._indoor_dd298c29.png` and `..._cabman_outdoor_0c68eeba.png`.

facenet on the head-region faces (h 0.11 to 0.17, frontal):
- 8826eb07 against each of Hope's other three sheets: **0.41 / 0.44 / 0.44**. All are below STRANGER (0.45).
- The other three among themselves: 0.77 to 0.89.

John Ferrier, 1847 (ep08, `7e1cc905`) against 1860 (ep10/ep11): 0.57 to 0.59. That is below MATCH, and the hair goes from chestnut curls to short grey. It is an intended 13-year age-up done as a redraw, not one hop.

Scarlet's flashback (Part 2) and its 20-year jump are carried by separate cast rows (`lucy_ferrier_child`, `jefferson_hope_cabman`). That works for Lucy. It is not a look timeline.

### 2.4 The lip-lag measure cannot rank Scarlet dialogue
All 80 dialogue dq rows read lag +0.000 or −0.010 s. A statistic that never moves cannot pick "one dialogue take with lip lag". This is a hypothesis: that number aligns audio, not mouth motion. `studio/measure/mouth.py` should be the reader for the replay.

### The Scarlet replay set (fixed for cycles 1 to 3)

| Slot | Take or grid | Why |
|---|---|---|
| **S-221B + faces + dialogue (drifted)** | ep14 `sitting_room_evening` grid (`ep14/boards/sheets/seq_sitting_room_evening_0.prompt.txt`, `boards/plates/plate_sitting_room_evening.png`). Takes **T03** (wide, room), **T04** (Holmes MC dialogue), **T05** (Watson MC dialogue), **T17** (Watson close dialogue; shipped failing coherence-off-board 0.64, last-vs-cell 0.29, churn 7.25), **T22** (Holmes MC dialogue, identity 0.19 on pose) | One grid covers the room drift (text similarity 0.15), the lowest Holmes episode (0.489) and two dialogue takes |
| **S-221B control (held)** | ep05 `hearth_night`: **T09** (Watson medium), **T11** (Holmes full, plate staged), **T12** (Holmes MC) | The consistent-era room; checks that a pinned anchor does not regress a room that already held |
| **S-exterior (recurring)** | ep03 `garden_path`: **T07** (wide, plate staged), **T08** (Holmes medium), **T10** (Watson MC). Against ep14 `garden_path_morning`: **T09** (wide) | A recurring exterior that drifted |
| **S-identity (secondary)** | ep07 **T23** `landing_arrest` (Holmes + Hope on 8826eb07) against ep13 **T19** `brixton_front_room` (Hope close dialogue on dd298c29) | A same-story-time identity break of 0.41 to 0.44 |
| optional | ep10 `farm_parlour` **T08** / **T14** (Ferrier close) against ep11 `farm_parlour_day` | Ferrier parlour drift (5 rooms) |

**Caveat for the replay tooling.** `look_replay.py` targets the look-table path. Scarlet has no `refs/looks.json` and stages `char-*_indoor` sheets, so its replay runs the legacy path.
- The comparison for places is the anchor pinned against the shipped plate.
- The comparison for faces is the ComfyUI-input sheet named in each `T*.graph.json` against the replay.
- ep01 to ep03 staged unhashed names (`char-sherlock_holmes_indoor.png`) that may have been overwritten since. Treat those episodes' staged pictures as unknown.

---

## Issue 3: the Jekyll/Hyde probe (`20260827135504`, not started)

### What `looks_table.py` would produce today (measured on CPU)
- `looks_from_dossier`: **None** for both. They have no `wardrobe` or `wardrobe_by_chapter`, so the LLM writer path would run.
- **Their heads are empty:** `layer_text(physical, hair|face|headwear)` returns `''` for both. The dossier `physical` has no hair, beard, age or hat. Every marker would be blank, so **LOOK-STATE would pass anything** (a vacuous judge).
- **`APPEARANCE` regex rows** (what the writer reads):
  - Jekyll: 4 rows, which are noise ("burned the envelope", "fleshly vestment", "retains Hyde's clothes", "transforms in Regent's Park").
  - It **misses** every real appearance change: ch3 "grew pale to the very lips ... a blackness about his eyes", ch5 "looking deathly sick", ch9 "he seemed to swell ... features melt", ch10 "lost in stature". The words pale, sick, black, stature, shrunk and swell are not in the regex.
  - Hyde: 9 rows, mostly violence and possession.
- **Story time is not narrative order.** ch10 (Jekyll's confession) narrates the first transformation and the years before ch1. A chapter-keyed `Span` gives every ch10 shot the latest look. Scarlet Part 2 has the same structural gap.
- **The current refs are unusable for a probe** (`jh_sheets.png`). Jekyll, Hyde and Utterson are three near-identical men in black frock coats with faces about 5 % of frame height. Hyde is neither "small" nor "ill-kempt". This breaks the unique-character-looks rule.

### Does Jekyll to Hyde fit "one hop from base"? No. Hyde fits as his own base.
- The look contract keeps the body invariant (`CharacterLooks.body`) and lets only headwear, hair, face, top and dirt move. Hyde changes stature, age, face and hands: "smaller, slighter and younger than Henry Jekyll" (ch10); "pale and dwarfish" (ch2); the hand "lean, corded, knuckly, of a dusky pallor and thickly shaded with a swart growth of hair" (ch10).
- He is already a separate entity (`edward_hyde`), and he must keep his own base sheet.
- What *does* fit one hop is **Hyde's own look in Jekyll's clothes**: "enormously too large for him in every measurement -- the trousers hanging on his legs and rolled up ..., the waist of the coat below his haunches" (ch9), and "my clothes hung formlessly on my shrunken limbs" (ch10). That is a garment edit of Hyde's base.

### The look table it should have (quotes verified in `source/chapters/ch_0N.json`)
```
henry_jekyll  base doctor_well   head: "a large, well-made, smooth-faced man of fifty" (ch3) -> clean-shaven, hair/age authored once
              look deathly_sick  ch5 ("looking deathly sick"), ch6 sc2-ch7; face layer: pale to the lips, blackness about the eyes
                                 (markers cannot express pallor -> face_change=False today; identity + VLM-list judge it)
edward_hyde   base hyde_own      ch1-4: "pale and dwarfish"; small, younger; corded hairy hands; ill-kempt clothes
              look in_jekylls_clothes  ch9 sc6, ch10 sc7-8: top layer = Jekyll's frock coat and trousers enormously too large (route: edit)
```

### The one-shot probe (proposed, about 30 min GPU, owner-gated; the book stays unstarted)
- **Scene:** ch9 sc6, Lanyon's consulting room. "he seemed to swell -- his face became suddenly black and the features seemed to melt and alter -- and the next moment ... there stood Henry Jekyll!"
- **Owner rulings needed first:** the book's look (style is the owner's), and new Jekyll and Hyde base sheets (bust plus full figure, distinct silhouettes).
- **Refs:**
  1. Draw new base sheets for jekyll and hyde.
  2. Draw one look, `edward_hyde/in_jekylls_clothes`, by the edit route from Hyde's `sheet_front`. Judge it with LOOK-STATE plus the face-list check from Issue 1b.
  3. Gate: Jekyll and Hyde sheets must score below 0.45 on facenet against each other.
- **Grid:** 1x2. P1 is Hyde in Jekyll's clothes at the table, glass in hand. P2 is Jekyll, pale and half-fainting, at the same spot. One anchor holds the room.
- **Take:** one H3 ref2va take. First frame P1; refs are the Hyde look and the Jekyll base; the motion says "he swells, his face blackens and the features melt and alter until he is the man in <image2>".
- **Measures:**
  - facenet against both sheets on every sampled frame;
  - pass: the first 20 % reads Hyde ≥ 0.60, the last 20 % reads Jekyll ≥ 0.60, the crossover is monotone, there are 0 clone pairs, and only one figure appears (VLM list).
- **Prediction (a hypothesis to test, not assumed):** H3 keeps the first frame's identity, because ref2v pins only the first frame (memory: no last-frame pin), so the take stays Hyde.
- **Fallback:** a cut pair (P1 take to an insert of the hands to P2 take), which the plan contract would need to express as `transforms: {from: edward_hyde, to: henry_jekyll}`. Without it, the identity gate refuses a mid-take change of face as STRANGER or uncast.

### Fixes the probe implies (code, test-first)
1. Add `pale|sick|black|swell|stature|shrunk|dwarf|younger|older|age` to `look_timeline.APPEARANCE`. Test: Jekyll ch3 sc1 and ch5 sc1 rows are kept.
2. Refuse to write a look table for a bound character whose head layers are all empty. The dossier must author a head first. A blank-marker LOOK-STATE is a judge that reads nothing (the same lesson as the "unread" verdict).
3. Add an optional `StoryTime.order` (or a flashback flag) so a confession or flashback chapter can name the story time of its scene.

---

## Confidence summary

| # | Claim | Confidence | Basis |
|---|---|---|---|
| 1a | The beard is dropped because of its wording ("N days of / stubble / qualified") under Krea2 + Cinematic LoRA | 95 % | 0 of 7 such wordings drawn against 2 of 2 "Full ... beard"; 3 of 3 ragged draws |
| 1a' | Subject-noun-last prompt form contributes | 55 % | One bearded ghost face; not isolated |
| 1a'' | Grid tags omit the beard on 4 of 12 ep25 tags | 100 % | grep of `episodes/ep25/plan.json` |
| 1b | Ghost faces exist and YuNet cannot gate them | 95 % | 2 faces on 1 picture; YuNet measured blind or noisy |
| 1b' | Cause is LoRA dark-area hallucination vs USDU tile prompt | 60 % | 2-minute presave A/B decides it |
| 2.1 | Holmes and Watson do not drift across Scarlet | 85 % | facenet on 59 takes plus eye; identity never measured at ship (100 %) |
| 2.2 | Scarlet has WotW-class place drift | 95 % | 4 places, plates by eye, text similarity predicts it |
| 2.3 | Jefferson Hope is two men in 1881 | 90 % | facenet 0.41 to 0.44 on 3 pairs |
| 3 | Jekyll to Hyde is not one hop; Hyde-in-Jekyll's-clothes is | 95 % | Contract fields; quoted text |
| 3' | A single H3 take cannot transform identity | hypothesis | The probe decides |

Sources:
- [Object-Attribute Binding in T2I (arXiv 2404.13766)](https://arxiv.org/html/2404.13766v1)
- [Magnet: concept bleeding (arXiv 2409.19967)](https://arxiv.org/html/2409.19967v1)
- [Ultimate SD Upscale (A1111 extension)](https://github.com/Coyote-A/ultimate-upscale-for-automatic1111)
- [Qwen-Image-Edit-2511 (Replicate)](https://replicate.com/qwen/qwen-image-edit-2511)
- [Pruna image-editing prompting guide](https://docs.pruna.ai/en/docs/docs_pruna_endpoints/image_editing/quickstart.html)
- [Dreamina beard prompt patterns](https://dreamina.capcut.com/ai-image/ai-beard-online)
