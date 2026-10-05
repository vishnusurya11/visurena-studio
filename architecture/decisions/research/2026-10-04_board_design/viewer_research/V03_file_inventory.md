# V03 — File inventory and provenance map (ep12 finished, ep17 running)

Read-only walk on 2026-10-04 of
`D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\library\20260827135508_the-war-of-the-worlds\episodes\ep12`,
`...\ep17`, `...\refs\`, and `D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\logs\20260827135508\episode\`.
Writers were read in `scripts/episode/{grids,panels,takes_r2v,assemble,qc,sign_eye,eye_review,panel_check,panel_content_check,drive,run}.py`.
Every `rel_path` in the JSON is **book-relative** (`episodes/ep12/...`, `refs/...`), so it goes straight onto
`/lib/20260827135508/<rel>` and `/thumb/20260827135508/{160|320}/<rel>`. ep12 = 2.9 GB, ep17 = 121 MB.

## 1. Inventory: what the viewer can open

### Pictures
| kind | path pattern (unit-relative) | ep12 | ep17 | size each | writer |
|---|---|---|---|---|---|
| panel (for people) | `storyboard/shot_NN.png` 1024² | 24 | 22 | 1.5–1.6 MB | panels.py |
| panel (staged into H3) | `storyboard/h3/shot_NN.png` 768² | 24 | 22 | 0.8–0.95 MB | panels.py |
| storyboard contact sheet | `storyboard/contact.png` | 1 | 1 | 2.4–2.8 MB | step_08 (panel_contact) |
| grid (live) | `storyboard/grids/epNN_grid_<setup>_<C>x<R>[_tag].png` | 12 | 10 | 1.9–7.8 MB | grids.py |
| grid (superseded) | ep12 `storyboard/superseded/{hand_layout,r1,r2,r3}/`; ep17 `storyboard/grids/{old_martian_humanoid,iter1_machines}/` | 19 | 4 | 5–7.8 MB | hand moves (no writer) |
| setup anchor plate | `storyboard/anchors/<setup>.png` | 0 | 2 | 1.4 MB | step_03 places |
| take DQ strip | `takes/work/dq/take_TNN.png` | 24 | 0 | ~0.4 MB | take_strip / take_dq |
| take content frames | `takes/work/content/TNN_{0,1,2}.png` | 72 | 0 | ~0.9 MB | take_content_check |
| assemble guard frames | `takes/work/guard_TNN_{0,1,2}.png` | 72 | 0 | ~0.9 MB | assemble.py:512 |
| master review frames | `review/work/eye/fNN.png`, `review/work/<sha8>/fNN.png` (every 5 s) | 30+30 | 0 | ~3 MB | eye_review / master judge |
| master contact | `review/contact_<sha8>.png` | 1 | 0 | 3.1 MB | eye_review |
| episode strip | `reports/strip_T00_T23.png` | 1 | 0 | **13.2 MB** | take_strip |
| cast sheet (book) | `refs/characters/<entity>/sheet.png` (+`sheet_front.png`, `sheet_v1.png`, `.superseded/`) | 47 sheets, 335 MB total | | ~6 MB | cast_cards / refs stage |
| place picture (book) | `refs/locations/<location>/<view>.png` | 152, 955 MB total | | 3–7.6 MB | places / refs stage |
| prop sheet (book) | `refs/props/<prop>/sheet.png` | — | | ~6 MB | prop_refs |

### Videos
| kind | path | ep12 | ep17 | size | note |
|---|---|---|---|---|---|
| kept take | `takes/r2v/TNN.mp4` (NN = first shot of the take) | 24 | 0 | 0.55–2.9 MB | takes_r2v.py |
| failed attempt | `takes/r2v/attempts/TNN_failK.mp4` | 11 (T00,T02,T10×3,T11,T16×2,T17,T19×2) | 0 | ~1.6 MB | `episode_home.next_fail` on `--retake` |
| head trim | `takes/work/dq/TNN_head.mp4` | 1 (T19) | 0 | 3.8 MB | take_dq |
| master segment | `takes/work/segNN.mp4` | 24 | 0 | ~6 MB | assemble.py |
| picture/mixed/title/black | `takes/work/{picture,mixed,title_conformed,black}.mp4` | 4 | 0 | up to ~60 MB | assemble.py |
| **masters** | `cut/master_iter1..7.mp4` + `cut/master_r2v.mp4` | 8 | 0 | **~257–261 MB each, 1.98 GB** | assemble.py:915 copies master_r2v → master_iterN |

### Audio (viewer: play inline, low priority)
`audio/lines/lNN.wav` (23 / 21, ~0.2 MB), `audio/bed*.wav` (8–27 MB), `takes/r2v/{silence,voice}_NN.wav` (25),
`takes/work/*.wav` (49, 110 MB: line levels, qc lines, bed-ducked mix, room tone).

### Prompt files — every file that holds the words that made a picture or a take
| what it made | file | shape | key that names the output |
|---|---|---|---|
| a **grid** (and its panels) | `storyboard/grids/<name>.txt` | plain text: header + `PANEL k (row r column c), SIZE: …` blocks + cast/place `<imageN>` paragraphs (3–6 KB) | file stem = grid name; block `PANEL k` = slot `k-1` |
| grid manifest | `storyboard/grids/<name>.json` | `{name, episode, setup, cols, rows, shots[], seed, plan, drawn_from, inputs, prompt:"v2", room}` (~300 B) | `shots[slot]` = plan shot index |
| grid layout (the order the board draws) | `storyboard/layout.json` | `[{setup, cols, rows, shots[], tag?}]` | grid name = `ep{NN}_grid_{setup}_{cols}x{rows}[_{tag}]` (grids.py:71) |
| **take prompt cards** (planned) | `takes/r2v/prompts.json` | list of 24 / 22 cards `{index, shots[], setup, lane, refs[], faces[], anchors[], audio, width, height, fps, frames, seconds, steps, seed, prompt}` (88 / 111 KB) | `index` → `TNN.mp4` |
| take run record (as rendered) | `takes/r2v/shots.json` | same card + `{tries, retake_why, measured_seconds, render_s, waited_s, rel_path}` (91 KB) | `rel_path` |
| **exact graph sent to ComfyUI** | `takes/r2v/TNN.graph.json` | ComfyUI API graph (7–9 KB): node `8` MiniMaxH3ReferenceToVideo `.inputs.prompt`, node `12` `noise_seed`, `LoadImage` nodes with staged names `shot_05_6fb049a9.png`, node `19` LoadAudio | file stem |
| cast sheet / place / prop picture | `refs/pack.jsonl` (book, 221 rows, 168 KB, append-only) | `{path, workflow, prompt, seed, seconds, [source|rung|note]}` | `path` (book-relative); 15 paths have >1 row — the LAST row is the current picture |
| cast identity text | `refs/refs.json` (38 KB) | `refs[] {ref_id, entity_id, name, physical, wardrobe{indoor,outdoor}, rel_path, display, gender}` | `entity_id`, `rel_path` |
| the plan's own prose (source of all of the above) | `plan.json` (43 / 60 KB) | `setups{<setup>:{described, cast[], location, view, props[], geometry…}}`, `shots[] {index, setup, size, faces[], frame, motion, camera, at_rest, end, why, cuts[], take?}`, `lines[] {index, kind, speaker, text, shot}` | `shots[].index` |

### Verdicts, QC, run records
| file | ep12 | ep17 | size | link key |
|---|---|---|---|---|
| `plan.verdict.json` (judge:plan@1) | 2.2 KB | 4.1 KB | small | `faults[].where = "shot_NN"`, `plan_sha8` |
| `storyboard/eye_<sha8>.json` panel eye (judge:panel_eye@1) | **138 KB, 531 faults** | absent (not judged yet) | lazy | `files[]` = panel names; `faults[].where = "shot_NN"` |
| `storyboard/panel_dq.json`, `panel_content.json` | 5 / 9 KB | 4.5 / 8.5 KB | small | list, `[i].shot` |
| `takes/r2v/eye_<sha8>.json` take eye (judge:take_eye@1) | 2 files (one `pass`, one `flagged`/`still`) | absent | <2 KB | `files[]` = `TNN.mp4`; `faults[].where = "TNN"`, `evidence.still` |
| `takes/r2v/TNN.dq.json` | 24, **20–81 KB each** | — | lazy | `take`, `attempts[].file` (`TNN_failK.mp4`, `TNN_head.mp4`), `strip`, `measures.board.last_cell` |
| `takes/r2v/TNN.content.json` | 24, 111 B | — | small | file stem |
| `takes/r2v/stills.json` | `{19:{panel, seconds, why}}` | — | small | shot → panel held instead of a take |
| `review/eye_<sha8>.json` master eye | 5.5 KB | — | small | `master`, `contact`, `rubric.*.evidence` (per-shot rows `shot`), `faults[].where = "master"` |
| `qc_r2v.json` | 18 KB | — | small | `master`, `sha8`, `edit.segments[] {take, shots[], rel_path, start, n}`, `edit.cut_manifest` |
| `placed.json` (timeline) | 9.7 KB | 9 KB | small | `shots[] {index, t_start, t_end}`, `lines[] {index, shot, at}` |
| `manifest.json`, `youtube.json`, `heads.json`, `moves.json` | yes | — | tiny | unit level; `moves.json` = shot → camera move |
| `review/speaker_check.json`, `audio/lines/lines.json` | yes | yes | small | per speaker / `lines[].rel_path` |
| `learnings.jsonl` | 19 rows, 28 KB | 19 rows, 42 KB | lazy (long `note`) | `{ts, step, gate, measured, threshold, action, attempt, terminal, note}` — **no shot/take field** |
| `timing.jsonl` | 96 rows, 14 KB | 24 rows | small | `{stage, started, ended, seconds, ok, note}`; `note` carries grid args |
| `drive.jsonl`, `drive_runNN.log` | — | 1 + 4 | tiny | `{ts, event, sha, n, outcome}` |
| `plan.deferred.json`, `plan.json.bak_*` | — | 69 / 62 / 59 KB | lazy | prior plan versions |
| `ep12_dossier.html` | 171 KB | — | open in iframe/new tab only | dossier.py |
| `logs/20260827135508/episode/*.log` | 136 files, 1.2 MB total, max 47 KB | | lazy | JSONL `{ts, level, codex_id, stage, step_id, msg}` — **no unit field**; the unit is only inside `msg` (`episode/ep17`) — 6 files mention ep12, 1 mentions ep17 |

Also in ep12 root: `plan.py` (40 KB), `grids.sh`, `__pycache__` — session leftovers; the viewer should not list them.

## 2. Provenance graph (the edges and their keys)

```
plan.json shots[i] ──(layout.json row whose shots[] contains i; name rule grids.py:71)──► grid <name>.json/.png/.txt
grid <name>.json shots[slot]==i ──► slot ──► .txt block "PANEL slot+1 (row r column c)"   (panels.py: owner_of)
grid .png + slot ──(panels.py cut)──► storyboard/shot_ii.png  &  storyboard/h3/shot_ii.png
grid .txt <image1..n> ──(grids.py slot order: cast sheets, then place plate)──► refs/characters/<faces>/sheet.png, refs/locations/<setup.location>/<setup.view>.png ──► refs/pack.jsonl row (path)
plan.verdict.json / storyboard/eye_*.json faults[].where == "shot_ii" ; panel_dq/panel_content [i].shot == i
prompts.json card where i ∈ shots[] ──► card.index = k (first shot) ──► takes/r2v/Tkk.mp4
   card.refs[] may name "episodes/epNN/storyboard/h3/shot_ii.png"  (the panel → take edge)
takes/r2v/Tkk.graph.json (exact prompt+seed+staged images) ; shots.json row rel_path ; Tkk.dq.json / Tkk.content.json
takes/r2v/eye_*.json faults[].where == "Tkk" ; Tkk.dq.json attempts[].file ──► attempts/Tkk_failN.mp4
qc_r2v.json edit.segments[] (take==k) ──► start frame, n frames in cut/master_r2v.mp4 (24 fps) ; takes/work/segkk.mp4
placed.json shots[i].t_start/t_end = the same span in seconds
stills.json {i: panel} ──► the master holds the PANEL, not the take, for shot i
```

### Worked example A — ep12 shot 05 (finished)
1. **Plan shot**: `plan.json shots[5]` — `setup:"woods"`, `size:"medium"`, `faces:[]`, `frame:"Medium through the pine stems … three hussars …"`; line `lines[5]` "Through the trees, three hussars were riding toward Woking. We hailed them."
2. **Grid**: `layout.json` row `{setup:"woods", cols:3, rows:1, shots:[3,4,5]}` → `storyboard/grids/ep12_grid_woods_3x1.{png,json,txt}` (png 6.0 MB). Manifest `shots:[3,4,5]`, `seed:40512`, `plan:"c7aa61c68469da5b"`, `drawn_from:"d73fbcd03c4e8232"`, `inputs:"c44e53e24f294aa2"`.
3. **Prompt entry**: slot = `shots.index(5)` = 2 → `.txt` block `PANEL 3 (row 1 column 3), MEDIUM: Medium through the pine stems …`; the closing paragraphs bind `<image1>` = narrator sheet, `<image2>` = `refs/locations/pine_woods_maybury/wide_clearing_morning.png` (plan `setups.woods.location/view`), whose prompt is the `refs/pack.jsonl` row with that `path` (seed 1992634231).
4. **Panel**: `storyboard/shot_05.png` (1.6 MB) and `storyboard/h3/shot_05.png` (0.95 MB).
5. **Verdicts on the panel**: `storyboard/eye_c7e3eb93.json` — 20 faults with `where:"shot_05"` (1 `framing` advisory "framing 'wide': the shot asks for 'medium'", 19 `landmark` e.g. "barn drawn where the place names none"); terminal `keep_best`. `panel_dq.json[5]` passed (faces 3, cast_faces 0), `panel_content.json[5]` passed (subjects horse, tree, path, soldier). `plan.verdict.json`: no `shot_05` fault.
6. **Take**: `prompts.json` card `index:5, shots:[5]`, `refs:["episodes/ep12/storyboard/h3/shot_05.png"]`, `seed:93005`, 209 frames / 8.71 s, `audio:"silence"` → `takes/r2v/T05.mp4` (2.0 MB). `shots.json` row equals the card (`prompt` identical) + `measured_seconds 8.7`, `render_s 335.1`. `T05.graph.json` node 8 prompt == card prompt; node 18 `LoadImage image:"shot_05_6fb049a9.png"`; node 12 `noise_seed:93005`; node 19 `silence_05_a1612368.wav`.
7. **Take verdicts**: `T05.dq.json` PASS 100/100, `strip:"episodes/ep12/takes/work/dq/take_T05.png"`, `measures.board.last_cell:"shot_05.png"`; `T05.content.json` passed (people 3); take eyes: no `T05` fault in either `eye_20cc84ad` (pass) or `eye_21227f91` (flagged T16/T19). No attempts for T05.
8. **Master**: `qc_r2v.json edit.segments[5]` `{take:5, start:877, n:203}` → frames 877–1079 = 36.54–45.0 s of `cut/master_r2v.mp4`; `placed.json shots[5]` `t_start 36.541667, t_end 45.0`; cut at frame 877 `exact:true`; work copy `takes/work/seg05.mp4`. `moves.json["5"] = "pan_to"`.

### Worked example B — ep17 shot 13 (running; no take, no master yet)
1. **Plan shot**: `plan.json shots[13]` — `setup:"steamer_forward"`, `size:"medium"`, `faces:["captain"]`, `take:1`, `sounds[]`, `source[]` (chapter quotes); line 13 "As the decks fill, guns speak southward and three ironclads appear."
2. **Grid by the rule**: `layout.json` row `{setup:"steamer_forward", cols:3, rows:1, shots:[13,14,15], tag:"a"}` → `storyboard/grids/ep17_grid_steamer_forward_3x1_a.*`, slot 0 → `PANEL 1 (row 1 column 1), MEDIUM: Medium view over the forward deck …`.
3. **Trap — the live grid did not make the live panel.** `timing.jsonl` shows `grids "steamer_forward 3 1 a"` 19:21–19:22 and `panels` 19:24; `storyboard/shot_13.png` is stamped 19:24, but the live `ep17_grid_steamer_forward_3x1_a.png` is stamped **19:38** with `plan:"bebba4c4…"` (redrawn outside the runner, no timing row). The draw that the panel was cut from is `storyboard/grids/old_martian_humanoid/ep17_grid_steamer_forward_3x1_a.png` (`plan:"eb6be6e8…"` = `plan.verdict.json plan_sha8 "eb6be6e8"`). Also the live folder now holds `…_1x1_b.json` (shot 14) and `…_2x1_d.json` (16,17), which overlap `3x1_a`/`3x1_b`, so the next `panels.py` run will refuse ("shots drawn by two grids"). The board must say "panel older than its grid", not show the new grid as the panel's source.
4. **Cast & place inputs**: `captain` → `refs/characters/captain/sheet.png` (+ `refs.json` row `char-captain`, `pack.jsonl` seed 3700914650); place → `setups.steamer_forward {location:"paddle_steamer", view:"wide_establishing"}` → `refs/locations/paddle_steamer/wide_establishing.png`; setup anchor `storyboard/anchors/steamer_forward.png`.
5. **Verdicts**: `plan.verdict.json` (APPROVE, flagged, keep_best) has no `shot_13` fault (nearest: `shot_15` story); `panel_dq.json[13]` passed (faces 11, cast_faces 1); `panel_content.json[13]` passed (people 30). No `storyboard/eye_*.json` yet.
6. **Take card**: `prompts.json` card `index:13, shots:[13]`, `seed:105932`, 192 f / 8.0 s, `refs:["refs/characters/captain/sheet.png","refs/locations/paddle_steamer/wide_establishing.png"]` — **no panel ref** (written 19:11, before the panels existed) and older than `plan.json` (20:28): the card is stale. `T13.mp4`, graph, dq, eye: not yet. `drive_run0{2..4}.log`: run refused in `takes_r2v.py`.

## 3. Missing links (no key; the board must derive or say "unknown")
1. **Panel → grid draw**: panels carry no record of which grid file/bytes they were cut from (panels.py prints `shot NN <- name slot k` to stdout only). Name+layout is the rule, but redrawn and superseded grids break it (ep17 shot 13). A per-panel `{grid, slot, grid_sha}` sidecar is absent.
2. **Grid `<imageN>` → file**: the `.txt` names `<image1>`, `<image2>`; the manifest stores only an `inputs` hash and (ep17) `room`. Which sheet/plate filled which slot is recomputed from `plan.setups` + cast order, never recorded. Same for the take graph: `LoadImage` holds staged names `shot_05_6fb049a9.png` (stem + hash), not the library path; map via `card.refs[]` order.
3. **Failed attempts have no prompt/graph**: `TNN.graph.json` is overwritten each retake; `attempts/TNN_failK.mp4` links only through `TNN.dq.json attempts[].file` and `shots.json retake_why`.
4. **prompts.json vs shots.json drift**: two lists of the same cards; seed differs on T00 (prompts 93000, shots 93101 after retake). The graph is the truth of what ran; prompts.json is what *would* run now.
5. **master_iterN ↔ QC/eye**: `qc_r2v.json`, `review/eye_faf11c8f.json`, `manifest.json` describe `master_r2v.mp4` only. Iter files carry no sidecar; iter7 = same byte size as master_r2v (259,457,105) — equality by size/hash only. Iter1–6 have no verdicts.
6. **Verdict file → time**: several `eye_<sha8>.json` coexist; the current one is the one whose `files[]` bytes match disk (`eye_verdict.passed`), not the newest name. The board must compare `signed_at` or recompute sha.
7. **learnings.jsonl and logs** have no shot/take/unit field; shot refs live in free text (`note` "landmark at shot_00 …", `msg` "episode/ep17"). Logs are per run timestamp, not per unit.
8. **Superseded folders are not uniform**: ep12 `storyboard/superseded/<round>/`, ep17 `storyboard/grids/<reason>/`; panels.py ignores subfolders (non-recursive glob).
9. `takes/work/final.txt` holds **absolute** paths (breaks the "no absolute path" invariant; display as text only).
10. Shots held as stills (`stills.json`, ep12 shot 19) have a `T19.mp4` and attempts that never reach the master.

## 4. Lazy-loading list
- Never preload: `cut/*.mp4` (260 MB each; `preload="none"`, range requests), `takes/work/{picture,mixed}.mp4`, `audio/bed*.wav`.
- Thumb-first (`/thumb/…/320/`), original on demand: grids (up to 7.8 MB), `reports/strip_T00_T23.png` (13.2 MB), contact sheets (2.4–3.3 MB), all `refs/` sheets/places (3–7.6 MB).
- JSON to fetch on open, render collapsed, virtualise long arrays: `storyboard/eye_c7e3eb93.json` (138 KB, 531 faults — group by `where`, then `kind`), `TNN.dq.json` (to 81 KB; hide `energy_q`, `zoom.*steps`), `prompts.json`/`shots.json` (88–111 KB — show one card by `index`), `plan.json`/`plan.deferred.json` (43–69 KB), `refs/pack.jsonl` (168 KB — filter by `path`), `learnings.jsonl` (42 KB, long notes), `ep12_dossier.html` (171 KB). Logs ≤ 47 KB each but 136 files: list by name, load one.

## Top 8 recommendations
1. Key the viewer on **(unit, shot index)** and resolve every neighbour from the edges in §2; the "lineage strip" for a panel is: plan shot → grid (slot) → grid prompt block → refs → take card → take → verdicts → master span.
2. Open a grid prompt at its **`PANEL slot+1` block**, scrolled and highlighted, not the whole `.txt`.
3. For a take, show the **`TNN.graph.json` prompt and seed as "as run"**, `prompts.json` as "would run now", and flag when they differ (ep17 T13 stale; ep12 T00 seed).
4. Seek the master with `qc_r2v.json edit.segments[take==k].start/24` (fallback `placed.json t_start`); show "held as still" from `stills.json`.
5. Verdict chips per picture: filter `faults[].where == "shot_NN"` / `"TNN"`; collapse ep12's 531 panel faults to counts by `kind`.
6. Mark provenance confidence: when a panel is older than its grid (mtime) or two live grids claim a shot, show "source uncertain" and list the superseded draw (ep17 shot 13).
7. Attempts carousel from `TNN.dq.json attempts[].file` (resolve `_failK` in `attempts/`, `_head` in `takes/work/dq/`), with score/passed; say "no prompt kept" for failed attempts.
8. Propose (for the real board, not the mockup) one writer change each in panels.py (`storyboard/panels.json` `{shot: {grid, slot, grid_sha8}}`) and grids.py (`slots: {image1: rel_path, …}` in the manifest) — closes missing links 1 and 2 at near-zero cost.

## 2 disagreements I expect
1. **"Show the live grid as the panel's source"** (simple, by name) vs. my "derive and flag uncertainty": the simple rule is wrong today on ep17 shot 13–18, and a viewer that lies about provenance is worse than one that says "uncertain".
2. **Which prompt is "the prompt"**: designers will want one prompt per take; I argue for two tabs (as run = graph.json, would run = prompts.json) because they already differ, and the difference is the review signal.
