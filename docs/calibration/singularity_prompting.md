# Prompting the Singularity fine-tune in ref2va

Scope: one shot per take, 4–8 s, 768×768, 24 fps, 1–3 reference images, no first frame.
Model `WarmBloodAban/Minimax-h3_Singularity` (ref2va pruned int8) + 8-step Ref2V turbo LoRA ×2.
Research only — nothing rendered for this document.

This is the **delta** on top of `docs/calibration/h3_ref_guide.md` (the official full-reference
guide, verbatim) and `docs/calibration/ref2v_prompt_spec.md` (our per-sentence builder spec).
Everything in those two still holds; the fine-tune did not replace the format.

---

## 1. Verified, with sources

**V1 — The fine-tune's prompt distribution is "official guide + action, expression, camera."**
The author, answering a complaint about prompt misreading: *"for prompts, I stick strictly to the
official prompt guidelines—I just add extra stuff like action, expression, and camera movement
descriptions."* → https://huggingface.co/WarmBloodAban/Minimax-h3_Singularity/discussions/18
The most actionable fact here: the six official fields stay, and the three things this checkpoint
was *trained to answer* are action, facial expression and camera.

**V2 — The desaturation is deliberate.** Same author, same thread: *"the model lowers video
saturation to avoid oversaturation."* Do not prompt the colour back; grade it in the edit.

**V3 — This checkpoint is ref-path only.** Author: *"Right now my model is only optimized for the
ref path, not fl2va, so it won't work properly with an fl2va hybrid loader setup."*
→ https://huggingface.co/WarmBloodAban/Minimax-h3_Singularity/discussions/17 — our standing
no-last-frame-pin rule, confirmed from the model side.

**V4 — The author ships his own prompt spec inside the model repo.** 357 lines,
`MiniMax_H3_Singularity_Prompt_Writing_Specification_Enhanced_EN.md`.
→ https://huggingface.co/WarmBloodAban/Minimax-h3_Singularity/raw/main/MiniMax_H3_Singularity_Prompt_Writing_Specification_Enhanced_EN.md
It self-labels as *"corpus-derived writing patterns… practical prompt-engineering guidance rather
than undocumented official MiniMax implementation rules."* Its load-bearing rules:
- §1 `Action chain ≈ initial state → trigger → primary action → displacement/momentum → contact or reaction → final state`
- §1 `Camera chain ≈ camera position → movement direction → speed → amplitude → subject followed → focus/depth-of-field result`
- §8 *"Avoid isolated verbs such as 'walks,' 'attacks,' 'turns,' or 'explodes'"* — expand into the chain.
- §8/§16 distant characters must be told to keep moving: *"their steps remain continuous even
  though their small scale makes the movement visually subtle."*
- §11 *"Words such as 'cinematic,' 'epic,' 'high quality,' and 'dynamic' … should never replace
  observable visual instructions."* Also: *"Motion blur only when justified by rapid motion."*
- §13 emotion → observable micro-acting: eyes, face, breathing, posture, hands, attention.
- §16 failure mode: *"Packing too many simultaneous actions into one shot."*

**V5 — Vendor claims (README, unverified by us).** HDR clarity and motion-blur elimination in fast
action; *"Distant Face Restoration: Drastically reduces facial distortion, blurriness, and
collapsing in medium-to-long shots"*; de-oiled skin; enhanced dynamic motion; VFX; *"Captures
subtle facial expressions and emotional nuances more vividly"*; stronger response to
pan/tilt/zoom/tracking; *"100% preserves MiniMax-H3's original prompt adherence."*
→ https://huggingface.co/WarmBloodAban/Minimax-h3_Singularity

**V6 — Official camera vocabulary is a closed token list** (MiniMax base guide §4.3):
`Zoom In/Out` (focal length, body still) · `Push In/Pull Out` (body moves) · `Pan Left/Right` ·
`Truck Left/Right` · `Tilt Up/Down` · `Pedestal Up/Down` · `Arc Shot` · `Tracking Shot` ·
`Static Shot` · `Shake Slightly/Strongly` · `POV` · `Roll Clockwise/Counterclockwise`.
Amplitude: `with small amplitude` / `with large amplitude`. Speed: `at slow speed` / `at fast
speed`. *"medium amplitude and normal speed are usually omitted."*
→ https://huggingface.co/MiniMaxAI/MiniMax-H3/raw/main/docs/VIDEO_PROMPT_WRITING_GUIDE_base_en.md
The Singularity spec §9/§20 adds `orbit, swoop, dive, whip-pan, barrel roll` — a superset with no
token guarantee. **Prefer the official token; append a Singularity verb only as a gloss.**

**V7 — Group speech has an official compound form.** Base guide §4.4: *"When multiple
already-numbered speakers speak or sing together, use a compound ID such as `(S1,S2)`."*
Also: *"characters who never vocalize receive no speaker ID."* Same URL as V6.

**V8 — Hard limits and knobs** (ComfyUI official docs). From
https://docs.comfy.org/tutorials/video/minimax/minimax-h3-native : *"Up to 9 reference images,
3 reference videos … and 3 standalone reference audio clips"*; *"`match` scales references down to
the generation resolution for speed; `max` keeps up to a 2048px short edge for stronger identity
fidelity at the cost of speed"*; *"Reference each input by tag in the exact order it was
connected"*; *"Assign each reference a job: State which reference drives which part of the shot
(identity, style, motion, camera, voice). Explicit assignments tend to work much better."*
From https://docs.comfy.org/tutorials/video/minimax/minimax-h3-prompt-guide : *"H3's native canvas
is a 768px short edge… resolutions are rounded to a multiple of 32"*; *"The duration input snaps
to the model's 17-frame-per-block (17k+5) grid at 24fps"* — so our 4–8 s window lands only on 90
(3.75 s), 107, 124, 141, 158, 175, **192 (8.00 s exactly)**; on-screen text goes in English double
quotes, one string at a time, and `<d>` is only for speech.

**V9 — Step count.** The official R2V template runs **20 steps** by default; *"raise the step count
(for example to 25) for better motion quality"*; the 4-step turbo LoRA gives *"slightly lower
audio and motion quality."* → docs.comfy.org native page. The Singularity README nevertheless
recommends the **4-step** LoRA. Our 8-step-stacked-twice sits between and matches neither.

**V10 — Length.** Official full-reference guide §5.2: *"For generation tasks,
`detailed_description` is normally 350-500 English words… A single shot does not automatically
justify a shorter description."* No documented hard token limit was found.

---

## 2. Community lore (secondary — count of independent reports given)

**C1 — Stacked turbo LoRAs wreck reference adherence. Contested, 2 reports, opposite signs.**
`g2t2`: *"You are using 2 Turbo LoRA. In my testing experience, Turbo LoRAs terribly damage the
referencing for me."* `EllipsesMark`, on the same 2-LoRA screenshot: *"I tried it… and it severely
improved the output."* → discussions/18. This lands directly on our stack (1.0 + 0.7). **Untested
by us. Experiment E1.**

**C2 — 4 steps is too few; 8–10 is the sweet spot. 1 report.** Esha Sharma reports 4-step output
was poor and improved at *"8–10 steps"*, and recommends testing on your own rig.
→ https://aistudynow.com/minimax-h3-comfyui-workflow-almost-3x-faster-ref2va-guide/
Consistent in direction with V9. Our 8 steps is inside her band.

**C3 — Low step counts are where this checkpoint breaks. 1 report.** The Civitai workflow author
warns the model's diffusion *"can be aggressive at low step counts."*
→ https://civitai.com/models/2917683/minimax-h3singularity-workflow

**C4 — Prompt adherence is slightly worse than base H3. 1 report, partially conceded.**
`liuxingsyue`: the model *"slightly impairs the handling of prompt functions, leading to a certain
degree of misunderstanding of the prompt words."* The author answered the *colour* half of the
complaint (V2) and did not deny the prompt half. → discussions/18. This contradicts the README's
"100% preserves prompt adherence" claim; treat README V5 as marketing.

**C5 — "Separate refs per element beat one sheet." Not supported for our mode.** The official docs
say *assign each reference a job* (V8) — that is about naming roles **in the prompt**, not about
splitting a character across images. The only worked per-element example is a third-party
*still-image* node pack: *"Keep the identity, face, hair, clothing, camera, and environment from
`<Picture 1>`. Use the body pose and limb positions from `<Picture 2>`."*
→ https://github.com/astropuzzo/ComfyUI-MiniMax-H3-Image-Studio
**Counter-evidence, and it is primary:** the official full-reference guide §2.1 — *"One subject may
be defined by multiple reference assets, and one reference asset may provide multiple subjects."*
Both shapes are sanctioned; no source found claims a turnaround sheet is worse for ref2va video.
Our one-sheet-per-entity rule stands, and the 9-slot budget is not the constraint.

---

## 3. Untested here

Whether the second turbo LoRA at 0.7 costs identity (C1) · whether lighting/HDR/material words
move this checkpoint more than base H3 (V5 claims yes) · whether "distant face restoration" buys
us wider framing · whether an action chain beats a single verb on a 4–8 s **single-shot** take
(V4's examples are all multi-beat combat) · whether 250–350 words underperforms the official
350–500 band (V10) · whether `ref_image_size: max` recovers detail lost to pruning + int8.

---

## 4. The prompt spec for one 4–8 s ref2va take

Six fields, official order, unchanged: `subject_definitions`, `summary`, `retention_analysis`,
`detailed_description`, `overall_soundscape`, `non_diegetic_music`. (V1, V4 §2.)

**R1 — No standalone `<Picture N>`.** No first frame is staged, so every picture is cited *inside*
its subject, and the summary prefix is `[reference generation]` alone. *Official guide §2.2/§3;
Singularity §16 names "treating every reference image as an automatic first frame" a failure.*

**R2 — One subject line per staged reference, each given a job.** `<Subject 1> is X in <Picture 1>:
face, hair, build, clothes.` Then state once what each drives — identity from the sheets, place
and light from the wide, material from the prop sheet. *V8: "Explicit assignments tend to work
much better."*

**R3 — Every visible person gets its own noun phrase and a unique silhouette.** A group named once
renders as one figure cloned (in-house, measured). For a crowd, name 2–4 individuals by
hat/height/dress/position, then give the remainder as a *band* ("a ragged line of hats and
shoulders, faces turned down into the pit") — never as a countable repeated person. *In-house;
Singularity §8 fixes the same class of fault by naming background behaviour explicitly.*

**R4 — Every action is a chain, not a verb.** initial state → trigger → primary action →
displacement → reaction → final state. One chain per take. *V4 §8 and §16 "packing too many
simultaneous actions into one shot"; V1 — action is what this fine-tune was tuned to answer.*

**R5 — Camera in five elements, in official tokens.** shot size + motion token + direction +
amplitude/speed + the subject it keeps in frame. Point the move at something already in the
reference; never state a distance. *V6 token table; V4 §1; in-house — direction obeyed, distance
not, push-ins overrun 1.9–3.5×.*

**R6 — The camera clause ends on what it holds, not on an exit.** "…keeping the gate in the right
of frame," never "…as he leaves the shot." *In-house: a final exit clause makes the take reframe;
Singularity §7 ends on "keeping [subject] in [composition relationship]".*

**R7 — Positive only.** No "no", "not", "without", "nobody". *In-house, measured.*

**R8 — One expression clause per named face:** gaze, brow, jaw, breath — not "he looks worried".
*V1 (expression is one of the three things the author added); V4 §13; V5.*

**R9 — Light as source + direction + exposure + material response**, never "cinematic". Expect the
return lower in saturation than written (V2) — grade in the edit. *V4 §11; V2.*

**R10 — One physical-feedback clause** — dust, spill, cloth, hair, heat shimmer — tied to the
action's contact moment. *V4 §10/§20.*

**R11 — 250–350 words of `detailed_description` for a one-shot take.** Above our measured house
average (114 words/block), below the official multi-shot band, because §5.2 says a single shot does
not license a short description. Flagged as E4.

**R12 — Audio.** `overall_soundscape` = ambience + effects synced to visible events;
`non_diegetic_music: N/A` on narration episodes. Any staged `<Audio 1>` must carry `fully_copy` or
lip movement drifts. *V8 prompt-guide tip 6.*

**R13 — Never write "slow" against a person;** write the gait. The turbo LoRA already pulls that
way. *In-house handbook, measured.*

---

## 5. Worked rewrite — two shots from ep03

### 5.1 The pit

**Before**
> frame: "Medium inside the pit on the glaring afternoon: three workmen in collarless shirts and
> moleskin trousers digging at the foot of the crusted hull, and above them along the rim a dense
> crowd pressing forward"
> motion: "The camera tilts up from the workmen's spades in the sand to the crowd pressing along
> the rim; a boy slides a little way down the sand wall and scrambles back"

**After** (`detailed_description` body)
> A medium-wide shot from inside the pit holds the three workmen low in frame against the crusted
> hull. `<Subject 1>` is the tall digger in a collarless shirt with the sleeves rolled past the
> elbow; beside him a shorter man works bare-headed with his braces down; the third, in a flat
> cloth cap and moleskin trousers, kneels at the hull's foot clearing sand by hand. High afternoon
> sun comes almost straight down: short hard shadows, the sand bleached pale, the hull's crust
> reading dark and matte against it. The three begin at a steady digging rhythm, spades biting and
> lifting. The tall digger drives his spade in, braces his back foot, levers the load up and swings
> it clear; sand spills off the blade and drifts as a thin curtain across the light, and the loose
> face below the hull slumps a few inches. Along the rim above, a stout man in a bowler leans out
> over the edge with both hands on his knees, a woman in a straw hat shields her eyes beside him,
> and a bareheaded boy in shirtsleeves crouches at the lip; behind the three the rim is a ragged
> band of hats and shoulders, faces small and turned down into the pit, pressing steadily forward.
> The camera tilts up with large amplitude at slow speed from the spades to the rim, keeping the
> crouching boy in the upper centre of frame. As the tilt settles, the boy shifts his weight onto
> the sand wall, the lip gives, and he slides feet-first down the face; sand runs ahead of him in a
> sheet. He digs both hands in, checks himself, and scrambles back up on all fours to the rim,
> where the bowler-hatted man catches his arm. The shot ends with the boy kneeling at the lip,
> breathing hard, the crowd behind him unmoved and still pressing forward.

| Change | Rule |
|---|---|
| "three workmen" → three men, each with its own silhouette | R3 (clone) |
| "a dense crowd" → three named figures + the rest as a *band*, not repeated people | R3 |
| "digging" → brace / lever / swing clear / sand spills / face slumps | R4, R10 |
| "tilts up … to the crowd" → `Tilt Up` + `with large amplitude at slow speed` + what it keeps | R5 |
| clause now ends "keeping the crouching boy in the upper centre" | R6 |
| "slides a little way" (an amount) → slides to the point the sand gives, with a final state | R5, R4 |
| "glaring afternoon" → sun direction, shadow length, bleached sand, matte crust | R9 |
| Medium held at **medium-wide**, not tightened | in-house: inserts against a wide-only location go soft; V5's face claim is for *distant* faces, not close inserts |

### 5.2 The villa gate

**Before**
> frame: "Wide of the narrator's red-brick villa at eleven on a hot bright morning: the Narrator in
> the grey herringbone tweed suit and the straw boater walking up the gravel road toward the black
> iron gate"
> motion: "The camera pans from the tall beeches at the left across to the iron gate; the Narrator
> walks up the gravel to the gate and stops with his hand on it"

**After**
> A wide shot frames the red-brick villa behind its black iron gate, the gravel road running in
> from the left under a row of tall beeches. The eleven-o'clock sun stands high and slightly
> behind the house: shadows are short and hard, the gravel is bleached near-white, the brick holds
> its red in the glare, and the air above the road carries a faint heat shimmer. `<Subject 1>`, the
> Narrator in the grey herringbone tweed suit and the straw boater, walks in from the left at an
> even, unhurried pace, boots working audibly into the loose gravel, the boater's brim cutting a
> hard shadow across his eyes. The camera pans right with large amplitude at slow speed from the
> beeches across the frontage to the gate, keeping the Narrator in the lower left of frame as he
> travels with it. He lifts his chin as the gate comes up, his gaze fixed on the latch; his pace
> holds steady, then shortens over the last few strides. He reaches out, sets his right hand flat
> on the top rail of the gate, and stops; the gravel settles under his heel and a thin lift of dust
> drifts past his knee. He stands with his hand on the iron, shoulders dropping as his breath
> evens, looking through the bars at the house. The camera settles with the gate at the right of
> frame and the Narrator square inside it.

| Change | Rule |
|---|---|
| "pans from the beeches … to the gate" → `Pan Right` + amplitude + speed + the subject it holds | R5 |
| pan now bound to the walk ("as he travels with it") rather than listed beside it | R5, V4 §9 |
| clause ends "settles with the gate at the right of frame" | R6 |
| "walks … and stops" → even pace → shortens stride → hand flat on the rail → gravel settles, dust lifts | R4, R10 |
| pace written as "even, unhurried" — the word *slow* never touches him | R13 |
| "hot bright morning" → sun height/direction, shadow length, bleached gravel, heat shimmer | R9 |
| added gaze/chin/breath beats | R8 |
| single figure held **wide** and face called out — the claim we are testing | V5, E3 |

---

## 6. Cheap experiments to settle the unverified

| # | Renders | Measure |
|---|---|---|
| **E1** | Shot 5.2, 3 seeds each, at LoRA 1.0-only vs 1.0+0.7 | ArcFace/embedding similarity of the take's faces against the character sheet; per-frame blur; whether the pan completes. Settles C1 on our own stack. |
| **E2** | Shot 5.1, 3 seeds, steps 8 vs 12 vs 20, LoRA held fixed | Same identity + blur metrics plus wall-clock. Settles C2/C3/V9 against our 8-step default. |
| **E3** | Shot 5.2 wide, 3 seeds, Singularity vs the previous base checkpoint | Face-region sharpness and landmark stability on the one distant face. Tests V5's "distant face restoration" and tells us if we may frame wider. |
| **E4** | Shot 5.1 at ~114 words (house average), ~300 words (Rule 11), ~450 words (official band), 3 seeds each | Count the prompted beats that actually appear; count invented content. Settles V10/Rule 11. |
| **E5** | Shot 5.1 crowd clause written three ways: "a dense crowd" / 3 named + band / 6 named | Count distinct silhouettes at the rim; count exact-duplicate faces. Settles R3's threshold. |
| **E6** | Shot 5.2 at `ref_image_size: match` vs `max`, 3 seeds | Identity similarity and wardrobe-detail recall vs render time. Settles the last item in §3. |
| **E7** | Shot 5.1 with and without the Rule 9 lighting clause, 3 seeds | Mean saturation and luminance histogram of the output. Quantifies V2's desaturation and whether lighting words move it at all. |
