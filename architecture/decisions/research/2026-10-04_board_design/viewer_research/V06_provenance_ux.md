# V06 — Provenance UX: "why does this picture look like this?"

The INFO panel that sits beside a panel picture or a take in the in-page viewer. Grounded in the real
files of ep12 (finished) and ep17 (running), read-only, 2026-10-04.

## 1. What the outside world does

| Tool | What sits beside the output | Lesson for us |
|---|---|---|
| ComfyUI | Two JSON chunks in the PNG: `prompt` (the API graph that actually ran: node ids, class types, model names, seed, prompt text) and `workflow` (the canvas layout). Drag the file back and the graph rebuilds. [numonic](https://www.numonic.ai/blog/comfyui-png-metadata-chunks-workflow-parameters), [civitai article](https://civitai.com/articles/26592/the-workflow-in-a-png-trick-in-comfyui) | Separate *what was asked* from *what ran*. Our `T??.graph.json` is exactly the ComfyUI `prompt` chunk: it is the truth for model, LoRA, seed. |
| Civitai image page | "Generation data" block: prompt, negative, resources used (model + LoRA with weights), sampler, steps, CFG, seed, size, one "Copy all" button. [civitai metadata](https://civitai.com/articles/6590/metadata-leveraging-metadata-to-reclaim-your-prompts-and-other-generation-data), [@civitai/generation-metadata](https://www.npmjs.com/package/@civitai/generation-metadata) | Resources are a list of named chips with weights; params are a compact key/value grid; one copy action for the whole recipe. |
| Midjourney web | Right of the image: prompt text, parameters, reference images used; "More options" copies prompt, Job ID, seed. [docs](https://docs.midjourney.com/hc/en-us/articles/33390732264589-Creating-on-Web) | Reference images shown as thumbnails *in the recipe*, not as a filename. |
| Leonardo | Detail view: prompt, model, seed, then actions (Remix, Upscale, Use as reference). [leonardo](https://leonardo.ai/news/how-to-use-leonardo-ai) | Prompt first, params second, actions last. |
| Runway | Assets: an "Info / Details" panel per generation with prompt and seed. [runway seed](https://runway.com/resources/what-is-an-ai-image-seed) | The "i" key/icon is the standard affordance. |
| W&B media panels | Step slider over logged media; compare mode puts 2-4 media from different steps side by side. [media panels](https://docs.wandb.ai/models/app/features/panels/media) | Attempts are a *slider over the same slot*, not a separate page. |
| Langfuse trace | Tree/timeline of observations; each has input, output, metadata, scores; scores and comments sit on the node they judge. [new trace view](https://langfuse.com/changelog/2025-03-19-new-trace-view) | Judge verdicts belong on the node they judged (this shot), not only on the episode. |
| C2PA Verify | Manifest: issuer, date, tool, actions, and *ingredients* checked recursively. [contentcredentials](https://spec.c2pa.org/specifications/specifications/2.4/specs/ContentCredentials.html) | Provenance is a chain of ingredients: plan row -> prompt -> graph -> take. Show the chain, each link openable. |

None of these tools does the one thing our studio needs most: **show which words of the prompt came
from the plan, and which plan words never reached the prompt.** That is the original part of this panel
(and a publishable idea: "prompt lineage highlighting" for templated generation pipelines).

## 2. The brick

A take is `graph(prompt(plan_row, refs), seed)` judged by `gates`. Every visible field has exactly one
source file and one key. The panel is therefore a **join on one key per shot**, rendered in a fixed
order, each field carrying a small source chip that opens the raw JSON at that key. If a field has no
source, the panel says "not recorded", never a blank. Everything below regenerates from that rule.

## 3. Field -> file -> key (verified on disk)

Paths relative to `episodes/<ep>/`. Join keys: take `T10` <-> `prompts.json[i].shots` (ep12: take i = shot i,
24 takes; a take may list several shots) <-> `plan.json.shots[n]` <-> fault `where` = `"T10"` or `"shot_10"`.

**Take (video)**

| Section | Field | Source | Notes from the real files |
|---|---|---|---|
| Header | take, shots, section, setup, lane, seconds | `takes/r2v/prompts.json[i]` (`index, shots, section, setup, lane, seconds, placed_seconds`) | ep12 T05: friction / woods / narration / 8.71 s (placed 8.458) |
| Prompt | full prose | `prompts.json[i].prompt` | 5 labelled blocks: `subject_definitions`, `summary`, `retention_analysis`, `detailed_description`, `overall_soundscape` (+ `non_diegetic_music`). Show `detailed_description` open, the rest collapsed. |
| Prompt | did the graph run this prompt? | `T??.graph.json` node class `MiniMaxH3ReferenceToVideo` `.inputs.prompt` | Equal for ep12 T10 (verified). If unequal, red chip "prompt edited after plan". |
| Inputs | reference pictures | `prompts.json[i].refs` + graph `LoadImage.inputs.image` | ep12 refs = `storyboard/h3/shot_NN.png`; ep17 refs = `refs/characters/martians/sheet.png`, `refs/locations/paddle_steamer/wide_establishing.png`. Graph names the staged copy (`shot_10_99888bad.png`). Show thumbnails via `/thumb/.../160/<ref>`. |
| Inputs | audio | `prompts.json[i].audio` + graph `LoadAudio` | `silence` -> `silence_10_9edf7e50.wav`; dialogue takes -> `voice_NN.wav`. |
| Model | UNET, LoRA(s), text encoder, VAEs | graph `UNETLoader.unet_name`, every `LoraLoaderModelOnly` (`lora_name`, `strength_model`), `CLIPLoader`, `VAELoader` x2 | ep12: `Minimax-h3_Singularity_ref2va_Pruned_v1.3_int8`, turbo 8-step LoRA at 1.0 **and** 0.7 (node `lora_second`), `qwen3vl_32b_minimax_h3_nvfp4_awq`. `prompts.json.model` only says "MiniMax-H3 ref2va + Ref2V 8-step LoRA": use the graph. |
| Params | seed | graph `RandomNoise.noise_seed`, planned `prompts.json[i].seed` | ep12: planned 930NN; ran 93101 (T00), 93103 (T02), 93111 (T10), 93112 (T11), 93118 (T17). Show "93111 (planned 93010, +101 reseed)". |
| Params | steps, scheduler, sampler, shift, size, frames, fps | graph `BasicScheduler` (8, beta), `KSamplerSelect` (euler), `MiniMaxH3SigmaShift` (12 / 3.0), `prompts.json` width/height/frames/fps | 768x768, 24 fps, 209 frames. |
| Plan | size, frame, motion, camera, at_rest, path, why, faces, extras | `plan.json.shots[n]` | One row per shot listed in `prompts.json[i].shots`. |
| Verdict | gate table | `takes/r2v/T??.dq.json.gates[]` (`name, value, ok, hard, note, penalty`), `.score`, `.passed`, `.strip` | Show only gates with `penalty>0`, `!ok`, or `hard`; "N clean gates" folds the rest. `note` text verbatim ("not measured (no cell)", "1.00x hand"). |
| Verdict | content read | `T??.content.json` (`passed, faults, people, lookalikes, hour, text`) | ep12 T10: 5 people, day, no text. |
| Verdict | judge faults on THIS take | latest `takes/r2v/eye_*.json` by `signed_at`, `faults[]` where `where == "T10"` | Fault = `kind`, `severity`, `note`, `evidence` (e.g. lag "-9f (-0.375s) corr 0.61", penalty 30, repeated). |
| Verdict | plan-judge faults on its shots | `plan.verdict.json.faults[]` where `where == "shot_05"` | ep12 shot 5: invented "count 'three hussars' ... not in the chapter", match 0.49 vs wall 0.85. |
| Verdict | master-judge faults on its shots | `review/eye_*.json.rubric.*.evidence` (`under`, `closes[].shot`) | ep12 shot 6: face h 0.102 under wall 0.12. |
| Fate | is this take in the master? | `takes/r2v/stills.json` | ep12 T19 is **not** in the cut: `{"19": {"panel": "storyboard/shot_19.png", "why": "still: cut, cut-vote, jump"}}`. The panel must lead with this. |
| Attempts | failed renders | `takes/r2v/attempts/T10_fail1..3.mp4` | 11 fails in ep12. No sidecar recipe, no reason file. |
| Attempts | reasons | `learnings.jsonl` rows `gate=EYE_TAKES` whose `note` contains `at T10` | "rotation at T10: 7.6deg turned, no roll planned" -> action `seed`, then `move_type`. |
| Raw | files | `prompts.json`, `T??.graph.json`, `T??.dq.json`, `T??.content.json`, `eye_*.json`, `plan.json`, `work/dq/take_T10.png` strip | Each opens in the same viewer's JSON mode at the key. |

**Panel (storyboard picture `storyboard/shot_NN.png`)**

| Field | Source |
|---|---|
| grid it was cut from + cell position | `storyboard/layout.json` (setup, cols, rows, shots[]; position = index in shots) -> `grids/ep12_grid_<setup>_<CxR>[_tag].json` |
| prompt prose | `grids/<name>.txt`, the paragraph `PANEL k (row r left/right), SIZE:`; the grid preamble collapsed |
| seed, template version, hashes | grid `.json`: `seed` 40501, `prompt` "v2", `plan`, `drawn_from`, `inputs` (16-hex hashes; show 8, full on hover) |
| model | **not recorded** in the grid JSON (no graph saved for grids) -> say so |
| panel gates | `panel_dq.json[shot]` (faces, cast_faces, planned, sharp, ink, tiled, flags) |
| content read | `panel_content.json[shot]` (subjects[], hour, landform, people, text) |
| judge faults | `storyboard/eye_*.json.faults[]` where `where=="shot_NN"` (ep12: 531 faults, 137 KB, mostly "landmark at shot_NN": group by kind with a count) |
| superseded drawings | `storyboard/superseded/r1..r3/` + `hand_layout/` = the panel's attempts |

## 4. The panel

**Placement.** Desktop >= 1100 px: a 360 px column on the right of the viewer stage, the media keeps its
aspect in the remainder. 700-1100 px: 320 px overlay drawer over the stage's right edge. Phone >= 400 px:
bottom sheet, 45 % height, drag to 90 %. Toggle with the `i` key and an "Info" button (aria-pressed).
The panel stays open while the viewer navigates (arrow keys), and re-renders for the new item; this is
the W&B "slider over the same slot" lesson and the main time-saver when walking T00..T23.

**Order (top to bottom), each a `<section>` with an `<h3>`; sections 1-3 open, the rest closed:**

1. **Fate line** (one line, coloured): `In the master · 8.71 s at 0:36.5` or `Not in the master: replaced
   by still storyboard/shot_19.png (cut, cut-vote, jump)` or `Running · try 2` (ep17). The answer to "is
   this what the audience sees" comes before everything.
2. **Verdict on this shot.** Score chip (`dq.score` 100 / passed). Then fault cards, newest judge first:
   `[take_eye] lag · high · -9f (-0.375s) corr 0.61 · penalty 30 · repeated`. One card per fault, the
   `note` verbatim in body text, `evidence` as a 2-col mini table, a "plan" fault card says which plan
   field it accuses. Then the folded gate table ("17 clean gates"). Empty state: "No judge named a fault
   on T05 (take_eye@1, 48 reads, signed 2026-09-26 00:12)". Never a green tick alone.
3. **Prompt.** `detailed_description` as prose, 14 px, line-height 1.55. Spans that came from the plan
   are highlighted by field, each with its own underline style so colour is not the only cue:
   `frame` (solid), `camera` (dotted), `at_rest` (dashed), `motion` (double). Hover/focus a span: the
   tooltip names `plan.shots[5].motion`. Below it, a **"Plan words that did not reach the prompt"** list.
   Real example, ep12 shot 5: the motion clause *"travelling a hand's breadth"* and the camera clause
   *"the riders read dark blue and the road reads pale"* are absent from the prompt; frame and at_rest
   arrive 27/27 and 51/51 tokens. This is exactly the "amounts are ignored" lesson made visible per shot.
   The other prompt blocks sit below in a closed `<details>` each.
4. **Inputs.** Ref thumbnails (64 px, 160-thumb source) with role labels from `subject_definitions`
   (`<Picture 1>` = storyboard frame / `<Subject 1>` = the Martian sheet) and the audio file. Click opens
   the ref in the same viewer (push onto a back-stack; Backspace/"Back to T05" returns).
5. **Model and params.** Civitai-style: model chips (UNET, LoRA x strength, encoder) then a 2-col
   key/value grid: seed (with planned/ran delta), steps 8, scheduler beta, sampler euler, shift 12/3.0,
   768x768, 209 f @ 24 fps, 8.71 s. One **Copy recipe** button (plain-text block, Civitai "Copy all").
6. **Plan shot.** size, path, faces/extras, then frame / motion / camera / at_rest / why as labelled prose,
   the same underline style as their spans in section 3 (the two sections cross-highlight on hover).
7. **Attempts.** A row of tiles `try 1 · try 2 · try 3 · final` (W&B step slider). Tile = 160 thumb of the
   fail mp4's poster + one-line reason from `learnings.jsonl`. Selecting a tile swaps the stage media
   (still one `<video>`); the current one is outlined. Honest labels: fails carry "recipe not recorded".
8. **Raw files.** A list of the source files with sizes; each opens the viewer's JSON mode scrolled to the
   key (`prompts.json` -> `[10]`, `eye_21227f91.json` -> `faults[0]`). Plus "Open at :8700/lib" as a
   plain link for the original file. Every source chip in sections 2-6 is a shortcut into this.

**Component specs.** Section headers 12 px caps, 0.06em tracking, muted ink; body 14 px; mono 12.5 px for
seeds/hashes/filenames. Source chip: 11 px mono pill, `aria-label="open plan.json at shots[5].motion"`.
Fault card severity: `high` amber left border 3 px, `normal` neutral; never red unless the take is not in
the master. Highlight fills at 14 % alpha on Studio black and 18 % on Graphite, tokens
`--prov-frame/-camera/-at-rest/-motion` defined on `:root` and redefined for light.

**States.** loading (skeleton lines per section while the JSONs fetch) · running unit (ep17: no graph,
no dq yet; sections 2/5/7 read "not rendered yet", prompt and plan still show: ep17 `takes/r2v/` holds
only `prompts.json`) · missing source ("not recorded", with the file that would hold it) · stale (see 5) ·
error (fetch failed: file path + retry).

**Accessibility.** The panel is a `<aside role="complementary" aria-label="About T05">` inside the
viewer's dialog, so the viewer's focus trap includes it. `i` toggles; `Esc` closes the panel first, the
viewer second. Tab order: fate -> faults -> prompt spans (each span focusable only in "trace mode",
toggled with `t`, so normal Tab does not walk 40 spans) -> buttons. Fault cards are `<article>` with the
kind as heading; highlights use `<mark data-field="motion">` plus a visually hidden "from plan motion:".

## 5. Data honesty: what the files get wrong (the panel must not repeat it)

- **Stale mode prose.** ep12 `prompts.json[i].mode` says "no storyboard cell, nothing pinned" while
  `refs` is the storyboard panel `storyboard/h3/shot_05.png`. Do not show `mode`; show the refs that ran.
- **dq.attempt is always 0**, even for takes re-rendered with seed +101. Derive "try n" from the seed
  delta and the attempts folder, not from `dq.attempt`.
- **Several eye files per folder** (`eye_20cc84ad` pass, `eye_21227f91` flagged). The latest `signed_at`
  is the verdict; the older ones are attempt history and belong in section 7, labelled superseded.
- **Fails have no recipe.** `attempts/T10_fail1..3.mp4` have no graph/dq/reason sidecar and their mtimes
  are the original render times, so fail N cannot be joined deterministically to a `learnings.jsonl` row
  (which carries no take field; the take is only inside `note` text: "rotation at T10: ..."). Show the
  reasons as "the ladder said, in order" and the files as "renders, in order"; do not pair them. Pipeline
  fix to propose separately: write `T10_fail1.graph.json` + `T10_fail1.why.json` when a take is retired.
- **Grid model not recorded.** Grid JSON has seed and template version, no model/graph.
- **Logs name no episode.** `logs/<codex>/episode/*.log` lines carry `ts, step_id, msg` but no unit; link
  a log by the time window of the attempt, labelled "log around this time".
- **Fault text is repetitive.** `storyboard/eye_c7e3eb93.json` repeats "landmark at shot_00" 28 times:
  group by `kind`+`where` with a count, keep each distinct `note`.

## 6. Building it (mockups now, board later)

- One vendored script `assets/prov.js` (~6 KB): `loadUnitIndex(ep)` fetches `prompts.json`, `plan.json`,
  the latest eye per folder, `plan.verdict.json`, `stills.json`, `learnings.jsonl`, `layout.json`, once
  per unit open, and builds `byTake[T]` / `byShot[n]`; per-item files (`T??.graph.json`, `.dq.json`,
  `.content.json`, grid `.txt`) are fetched lazily when that item is shown. Largest: 137 KB panel eye.
- Highlighting: token LCS (plan field tokens ~50 x prompt tokens ~400 = 20 k cells, < 2 ms) per field,
  in the browser; the board later precomputes it server-side into a `provenance.json` cache (no video
  decode involved). Match on `\w+|punct`, lower-cased; a run of >= 3 matched tokens becomes a span.
- Mockup data: capture T05 (clean, plan highlights + dropped words), T10 (3 fails, reseed), T16 (lag +
  face-at-end), T19 (still, not in master), shot_05 panel (invented-count plan fault), ep17 T14 (running,
  sheet refs) as the six fixtures; they cover every state above.

## Top 8 recommendations

1. Build the panel as a **join on one key per shot** with a source chip on every field; "not recorded"
   instead of blanks. Same component for takes and panels.
2. **Lead with the fate line** (in the master / replaced by a still / running), then the verdict on this
   shot, then the prompt. ep12 T19 proves the order matters.
3. **Highlight plan-derived spans by field and list the plan words that did not reach the prompt**;
   ship it, it is the studio's original contribution (and a publishable "prompt lineage" pattern/tool).
4. Take model, LoRA strengths and seed from **`T??.graph.json`, never `prompts.json`**; show planned vs ran
   seed with the delta.
5. Fault cards show the judge's `note` **verbatim** with severity and evidence, filtered to `where` = this
   take or shot, from the latest-signed eye file plus `plan.verdict.json` and the master rubric.
6. Attempts as a **W&B-style tile strip in the same viewer**, honest that fails carry no recipe; propose
   the pipeline write a graph+why sidecar when it retires a take.
7. Panel follows viewer navigation (`i` toggles, arrows keep it open), right column >= 1100 px, drawer
   below, bottom sheet on phones; Esc closes panel before viewer; focus stays in the dialog trap.
8. Raw JSON opens **in the same viewer at the key**, plus one "Copy recipe" text block; do not show the
   stale `mode` prose or `dq.attempt`.

## 2 disagreements I expect

1. **"Show the whole prompt, not just `detailed_description`."** The other blocks (retention analysis,
   soundscape) are mostly constant boilerplate across 24 takes; showing them open buries the 2-3
   sentences that differ. I hold: open the shot-specific block, keep the rest one click away and
   diff-able against the previous take.
2. **"Pair each fail mp4 with its ladder reason."** It looks tidy, but the files give no deterministic
   join (mtimes are render times, learnings rows name the take only in free text). A guessed pairing
   would make the panel lie on exactly the shots the owner opens it for. I hold: two honest ordered
   lists now, a real join once the pipeline writes sidecars.
