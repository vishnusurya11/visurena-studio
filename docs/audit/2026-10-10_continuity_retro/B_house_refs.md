# B: House references, War of the Worlds (retro 2026-10-10)

Investigator B. This was a read-only pass: no code was changed, nothing was rendered and nothing was spent.
Book: `library/20260827135508_the-war-of-the-worlds` (written `<book>` below).
Evidence folder: `docs/audit/2026-10-10_continuity_retro/B_evidence/`
(contact sheets, the grid-input matcher script, and its full output `house_grids_matched.tsv`).

## Verdict in one paragraph

The owner suspected the house reference image was never passed. For the storyboard grids that suspicion is wrong.
For the H3 takes it is right, but only from ep07 onward.

I recovered the inputs of all **90 of 90** house grids from ep10 to ep27 by inverting
their manifest `inputs` hash (method below). Every grid staged its setup's location picture, or the
room panel cut from a grid that had staged it. None staged an empty slot or `example.png`.

The H3 takes changed. In ep01-03 every house take staged the location picture itself, with no storyboard step.
From ep07 onward a take stages only the Qwen panel plus face sheets. **H3 never sees `refs/locations/` again.**
The panel is also only a reference image, not a frame guide.

So the problem is not a missing file. It is that **the house is no longer one picture.**
- The owner's 2026-09-18 rule was "ONE picture per location: its establishing wide … no derived or edited views".
- That rule was quietly replaced on 2026-09-22 by `scripts/refs/places.py`. Since then, every episode-chosen `view` is drawn **fresh, text-to-image, from that episode's words**.
- The 2026-09-28 ruling said that "per-episode views are drawn FROM [the pinned picture]". That was never built.
- The result:
  - one dining room exists as 3 unrelated rooms under 2 location ids;
  - the study exists as 6+ rooms;
  - the garden exists under 3 location ids;
  - the wrecked or deserted states are carried only in words, which the picture overrides.

## 1. Every house setup, what was meant to be staged, and what was staged

Sources:
- `plan.json` `setups[*].location/view`;
- grid inputs recovered by hash (`B_evidence/house_grids_matched.tsv`);
- take inputs read from `takes/r2v/TNN.graph.json` LoadImage nodes, with staged names resolved by md5[:8] (`studio/comfy.py:53 staged_name`).

`refs/refs.json` holds **no location rows at all**: 26 character rows only.
Locations live only in `refs/locations/<id>/<view>.png` and `analysis/locations/<id>.json`. No "pinned" field exists anywhere.

| ep | setup | location / view (plan) | picture drawn (pack.jsonl) | staged in grid | staged in H3 take |
|---|---|---|---|---|---|
| 01 | study | narrators_study / (none → wide_establishing) | 09-18 T2I | no grid (refs-only) | `wide_establishing_13c8eea6` = study wide **direct** |
| 01 | porch | narrators_home / (none → wide_establishing) | 09-18 T2I | no grid | `wide_establishing_7972962f` = villa wide **direct** (T19-22) |
| 02 | study, home | same two | same | no grid | same two pictures, direct (T00-01, T20-22) |
| 03 | home | narrators_home / wide_establishing | same | no grid | same villa picture, direct (T11) |
| 07 | arch, gate | maybury_hill / (none) | — | ep07 grids have no `inputs` manifest: **unverified** | panel only (`shot_NN_*.png`) |
| 07 | door, table | narrators_home / (none) | — | **unverified**. The frames match `narrators_home/wide_dining_room` (drawn 09-21), not the villa wide the plan resolves to today. *Guess:* the plan was migrated after rendering. | panel only |
| 09 | garden | narrators_garden / wide_morning | 09-22 T2I | (ep09 manifests predate `inputs`) | panel only |
| 09 | lawn | maybury_hill / wide_lawn_burning | T2I | — | panel only |
| 10 | hall | narrators_home / interior_hall_staircase | 09-23 T2I | interior_hall_staircase + narrator sheet | panel only |
| 11 | study | narrators_study / interior_window_fire_night | 09-24 T2I (**sash** window, different desk) | that picture | panel only |
| 11 | valley, dawn | narrators_study / window_view_valley_fire_night, window_view_ashes_dawn | 09-24 T2I | those | panel only |
| 11 | garden | narrators_garden / wide_lawn_palings_night | 09-24 T2I | that | panel only |
| 11 | dining | **narrators_home** / dining_room_unlit_night | 09-24 T2I (dark damask, round table) | that | panel only |
| 12 | hill | maybury_hill / wide_road_dawn_deserted | T2I | that | panel only |
| 18-23 | Mortlake kitchen / scullery / pantry / pit | mortlake_* / various | 09-18 T2I, then scullery views **redrawn 10-05 → 10-08** | every anchor grid = setup view; siblings = room (ep anchors) | panel only |
| 22 | sheen_ruins | **sheen** / wide_establishing | 10-08 T2I | that | panel only |
| 23 | pit_summit | **mortlake_pit** / wide_summit_sheen | 10-07 T2I (a second, different "Sheen from the mound") | that | panel only |
| 26 | villa_front | narrators_home / wide_establishing | 09-18 (the **ep01 picture: intact**) | `wide_establishing_7972962f`, the same bytes as ep01 | panel only |
| 26 | dining_room | **narrators_dining_room** / medium_french_window | **10-09 T2I, new** | that, then the room | panel only |
| 27 | study_essay | narrators_study / wide_establishing | 09-18 (the ep01 picture) | `wide_establishing_13c8eea6`, the same bytes as ep01 | panel only |
| 27 | study_table | narrators_study / medium_writing_table | 09-18 T2I | that | panel only |
| 27 | study_window | narrators_study / window_view_panorama | 09-18 T2I | that | panel only |
| 27 | study_reverse | narrators_study / reverse | **10-09 T2I, new** (fireplace and bookcases) | that | panel only |

Where a setup was split over several grids, all of them followed the 09-28 chain:
- the anchor grid staged the place picture;
- every sibling grid staged `storyboard/anchors/<setup>.png`;
- a sibling also staged the place picture only when it held a wide.

The matcher found no sibling missing its room. The full table is in `B_evidence/house_grids_matched.tsv`.

### Method: how the staged bytes were recovered
`grids.py:139 inputs_sha` hashes `sha256(json.dumps([prompt_text, sorted(sha256(bytes) of each staged picture)]))[:16]`
and writes it into each grid's manifest. The prompt text is saved beside each grid as `.txt`.

`B_evidence/match_grid_inputs.py` brute-forces combinations of 1-3 pictures. The candidate pool is:
- every current location view, sheet, front crop, prop sheet and episode anchor;
- every older content-addressed copy of those files in `ComfyUI/input`.

All 90 matched exactly. This is proof, not inference.

## 2. What the frames show, early versus late

Contact sheets (10 % and 80 % of each take):
- `B_evidence/early_house.png`
- `B_evidence/mid_house.png`
- `B_evidence/late_house.png`
- `B_evidence/mortlake.png`
- location pictures: `B_evidence/home_views.png`, `study_views.png`, `garden_views.png`, `mortlake_views.png`

**ep01-03 (good):** one villa and one study.
- The porch takes (ep01 T19-22, ep02 T20-22, ep03 T11) all show the same red-brick villa: canted bay, tiled lean-to porch, white sash windows, brick wall with an iron gate.
- The study takes (ep01 T03/T18, ep02 T00/T01) all show the same room: French windows with an iron rail, cream curtains, green-shaded lamp, globe.
- H3 was given the Krea picture itself, the same bytes every time.

**ep07 / ep11 (middle):** the dining room is already two rooms.
- ep07: papered beige walls, white tablecloth, oil lamp, engraving.
- ep11: dark damask walls, a round pedestal table, decanters.
- ep11's study is a different room from ep01's: a **sash** window instead of French windows, a different desk and chair (`interior_window_fire_night`).

**ep26 / ep27 (late):**
- ep26 T15 (villa wide) is consistent with ep01. The pin held because the setup used `wide_establishing`.
  - But the house is **intact**. The prose asks for a forced door hanging ajar, dusty open sashes, smashed privet and red-weed fronds.
  - The panel follows the picture: door shut, garden neat, no weed.
- **ep26 T17 (insert on the forced lock) opens on a different house.** It shows a gabled bracketed porch, a paved road and a terraced façade, then pushes in (`B_evidence/t17_strip.png`).
  - The panel (`storyboard/h3/shot_17.png`, md5 `7e7ba0e5`) is a door close-up. It was staged and ignored.
  - Its content gate passed anyway (`ep26/takes/r2v/T17.content.json: passed true`).
- **ep26 dining (T18-T26) is a third dining room:** crimson damask, French windows onto a meadow, a square table. None of it matches ep07 or ep11.
- **ep27:**
  - The study wide (T00, T10) matches ep01: same picture.
  - The reverse (T22) is a new, unrelated room drawn on 10-09: fireplace, wall of bookcases, side door.
  - T24 shows a white-glass lamp where the study has a green one.
  - Every view of the study is a separately invented room. The cut jumps between them, which is the observatory fault the owner ruled out on 2026-09-18.

**Mortlake (ep18-22):**
- The scullery is broadly consistent across ep19-21: window, pump, plank doors. Its views were redrawn 10-05 to 10-08, during the run.
- ep18's kitchen takes drift: T15 opens on legs and then a green-lit room.
- The Sheen view from the mound exists as two unrelated pictures: `sheen/wide_establishing` for ep22 and `mortlake_pit/wide_summit_sheen` for ep23.

## 3. Root causes, ranked

### R1 (certain): every new view of a recurring place is a fresh text-to-image draw from that episode's words
`scripts/refs/places.py:88-97` together with `:105-106`:
```python
def draw_missing(book, setups, draw, look=""):
    for name, loc, view, state in status(book, setups):
        if state == "missing" and picture(book, loc, view) not in made:
            draw(styled(setups[name].described, look), target)          # words only
...
job = Job("locations", target.parent.name, target.stem, T2I, prompt, 1536, 1024)  # T2I = image_krea2_cinematic_2x
```
- No existing picture of the place is ever an input.
- This contradicts `studio/refs_pack.py:21-26`: *"ONE picture per location … Views drawn each from words came out as different rooms … OWNER 2026-09-18 … no derived or edited views."*
- It also contradicts `docs/DECISIONS.md:171-173` (2026-09-28): *"a recurring place is PINNED … per-episode views are drawn from it"*.
- The "drawn from it" half was never built. The `places.py` history (`9169d5b` 2026-09-22, `481a3c9`, `f6c80e8`) shows no edit path.
- Step 03 is still described as "drawn from its own described words" (`.claude/skills/episode/SKILL.md:169`).
- **This is what changed after ep03.** ep01-07 setups have `view` empty, so they resolve to the one wide. From ep09 the writer names views, and each named view is a new room.
- Count of pictures for the narrator's house: 5 under `narrators_home`, 11 under `narrators_study`, 1 under `narrators_dining_room`, 2 under `narrators_garden`, and 9 under `maybury_hill`. Three of the `maybury_hill` pictures (`wide_lawn_evening`, `wide_lawn_burning`, `wide_night`) are the same villa's lawn or road.

### R2 (certain): the H3 take stopped receiving the place picture; the storyboard panel is its only carrier, and it is not a hard pin
- `scripts/episode/takes_r2v.py:337-339` (`refs_from_cards`): `if panel: return refs`, so the place picture is dropped whenever a panel exists.
- ep01-03 had no panels, so the Krea picture went straight into `ref_images`.
- From ep07 on, the take graph has `ref_images.ref_image_N = shot_NN_<md5>.png`. The only `MiniMaxH3AddGuide` is the audio at frame 0 (for example `ep26/takes/r2v/T17.graph.json` nodes 8/18/20).
- The "first frame" exists only as prompt words (`<Picture 1> ([Shot 1] first frame): fully_preserved`).
- On a tight shot, the prompt's `summary:` line comes from `setup.described`. In T17 it reads "One 8.71-second take … in a detached two-storey red-brick villa on a sloping suburban road …". That line invites H3 to open wide and invent the house. The panel alone does not stop it.

### R3 (certain): one room, two location ids, chosen by the writer from the analysis rows
- The analysis has a separate row `analysis/locations/narrators_dining_room.json` (first_appearance 7).
- ep07 and ep11 put the dining room under `narrators_home`. ep26's writer used `narrators_dining_room`, which had no picture, so step 03 drew a new one.
- `studio/plan_brief.py:198-206 places()` gives the writer the analysis rows and their **planned** `design.views` ids.
  - It does not say which views are actually drawn.
  - It does not say which `location/view` earlier episodes staged for the same place.
- So nothing steers the writer back to an existing picture. The garden has the same problem across `narrators_garden` and `maybury_hill`, and the Sheen view across `sheen` and `mortlake_pit`.

### R4 (certain): state over time lives in words, and the pinned picture overrides it
- ep26 `villa_front` correctly reused the ep01 picture. That picture is the intact, sunny, neat house from 09-18.
- The prose's damage (forced door, dust, smashed privet, red weed) is outranked by the staged pixels, which is the grid's own rule that a place is held by pixels.
- Nothing models `state` for a location. `analysis/locations/*.json` has `state_changes`, but no step draws a state variant **from** the anchor.
- R1's cure (a state edit of the pinned picture) is also R4's cure.

### R5 (likely): one place split into several setups, each with its own room chain
- `studio/grid_room.py` chains only within one setup.
- ep27 split the study into `study_essay`, `study_table`, `study_window` and `study_reverse`. Each setup anchors on its own unrelated T2I picture, so the chain cannot hold the room across them.

### R6 (minor): the gates never caught it
- The take content gate passed ep26 T17.
- `panel_place` is still advisory: the 2026-09-28 tracker lists its calibration as open.
- No gate compares a place across episodes.

### Not the cause (checked)
- An empty or doll slot: every staged slot resolves to a real picture.
- The wrong file being staged: every staged file is the plan's own `location/view`.
- A redrawn anchor overwriting ep01's pictures: `narrators_home/wide_establishing` and `narrators_study/wide_establishing` are byte-identical to ep01's staged copies (`7972962f`, `13c8eea6`).

## 4. State over time, for the record

| place | book state | pictures that exist | gap |
|---|---|---|---|
| Narrator's villa, exterior | ep01-03 intact; ep09-11 under fire or storm; ep26 abandoned, door forced | one intact wide, plus a porch medium (night), plus lawn and road views under `maybury_hill` | no abandoned variant; ep26 shows the intact house |
| Study | ep01-02 night, lamp; ep11 dark, valley on fire; ep27 epilogue | 6 different rooms (French windows versus a sash window, different desks) | ep11 contradicts ep01 and ep27 |
| Dining room | ep07 supper; ep11 dark; ep26 dusty, decayed mutton | 3 unrelated rooms | three dining rooms |
| Mortlake house | ep18 intact, then hit by the cylinder; ep19-21 buried; ep22 red weed, empty | each state its own T2I picture (`wide_empty`; kitchen red weed in words only) | partly held, because scullery views were drawn close together in time |

## 5. What would fix it (for the fix owner; not done here)
1. In `places.py`, a missing view of a location that already has `wide_establishing` should be drawn **from** that picture with an image-edit model (Qwen-Image edit or similar) at the setup's hour and state, not with Krea T2I. This builds the "drawn from it" ruling of 2026-09-28.
2. The plan brief should list each place's drawn views and the `location/view` earlier episodes staged. A plan gate should refuse a new location id whose name or aliases match an existing drawn place (`narrators_dining_room` versus `narrators_home`).
3. A take whose first shot is tight should not carry the setup's whole `described` as its `summary`. Measure first whether the panel should become an `AddGuide` image at frame 0 (note the memory "no last-frame pin": a first-frame guide is a different thing; this needs a trial).
4. A cross-episode place gate: compare the opening panel of a recurring place with that place's anchor picture.

This work generalizes beyond the repo and could be published: "a place is a picture; derived views are edits of it, never new draws". That is the brick for location continuity in any multi-episode generative pipeline. A small benchmark is possible: the same location over N episodes, scored for cross-render agreement.
