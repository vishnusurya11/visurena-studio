# THE FINAL ref2v TAKE-PROMPT SPEC

Proposal only. Nothing in the repo was edited, nothing rendered, nothing spent.
Subject: every sentence `studio\episode_ref_official.py` emits.

**Sources compared line by line**

- MiniMax official, fetched this session:
  `https://huggingface.co/MiniMaxAI/MiniMax-H3/raw/main/docs/VIDEO_PROMPT_WRITING_GUIDE_ref_en.md`
  (verbatim spot-checks on the word count, the §5.1 bullets, the `<Picture N>` rules, the task-type
  table and the retention Picture entry all match the local copy) and the base guide
  `VIDEO_PROMPT_WRITING_GUIDE_base_en.md`.
  Local copies used for line references:
  `D:\temp\claude\d--Projects-KingdomOfViSuReNa-alpha-visurena-studio\8a764c01-76e4-437c-b43b-8b6a5e4a5481\scratchpad\ref-en.txt`
  `D:\temp\claude\d--Projects-KingdomOfViSuReNa-alpha-visurena-studio\8a764c01-76e4-437c-b43b-8b6a5e4a5481\scratchpad\base-en.txt`
- Ours, as it stands **today in the working tree** (integer ranges landed):
  `D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\studio\episode_ref_official.py`
  `D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\scripts\episode\takes_r2v.py`
- Live output of the current builder for all 19 takes, generated for this report:
  `D:\temp\claude\d--Projects-KingdomOfViSuReNa-alpha-visurena-studio\8a764c01-76e4-437c-b43b-8b6a5e4a5481\scratchpad\review9\all_prompts.txt`
  (script `...\review9\emit.py`; example bodies `...\review9\ddA.txt`, `...\review9\ddB.txt`)

---

## 0. Two facts to read before the template

**0.1 The current builder cannot emit this episode at all.** `build()` ends with the negation guard,
and on `library\20260822113400_a-study-in-scarlet\episodes\ep01\plan.json` it raises:

```
ValueError: the prompt carries negation MiniMax cannot read: ['no', 'nobody', 'not']
```

Every "ours" prompt quoted below was produced with that guard monkey-patched off. The negations are
in the source text, not in the builder — measured across the plan and the book refs:

| where | field | negations |
|---|---|---|
| `plan.json` setups | `criterion.described` | no, nobody, not |
| | `bench.described` | no |
| `refs\refs.json` | `john_watson.physical` | no ("no gloves") |
| `plan.json` shots | 1, 1.1, 4, 5, 5.1, 6, 10, 11, 13.1, 14, 14.1, 16, 17.1, 17.2, 19, 19.1, 22 | not, no, never, nobody, nothing, barely |

18 shot/cut texts, 2 setups, 1 character sheet. **Nothing else in this spec can ship until those are
rewritten positively.** Narration line text never enters a prompt (only `kind == "dialogue"` reaches
`<d>`), so the five narration lines carrying "not / never / nobody" are safe and must be left alone.

**0.2 How descriptive ours is now, measured.** Over all 19 takes / 40 shot blocks in
`all_prompts.txt`: **4574 words total, 241 words per take, 114 words per `[Shot k]` block**
(min 75, max 149). The guide (ref-en §5.2): *"For generation tasks, `detailed_description` is
normally 350-500 English words. ... A single shot does not automatically justify a shorter
description; distribute detail across multiple shots according to their information load."* Exactly
one of our 19 takes (T18/T19 at 408) is inside that band. The template below lands 2-shot takes at
~400 words and 3-shot takes at ~640, i.e. **150-240 words per shot block** — see §4 L14 for the gate
and §5.17 for the deliberate overshoot on 3-shot takes.

---

## 1. THE TEMPLATE — every sentence the builder emits

Six sections in this order, exactly as ref-en §1. Marking: **OFFICIAL** = the guide's own form or
example sentence; **OURS** = a deviation, with its reason and evidence.

### 1.1 `subject_definitions`

| # | Sentence emitted | Source |
|---|---|---|
| S1 | `<Subject k> is {Name} in <Picture k>: {physical}` — one line per cast sheet, `k = 1..n` in `faces` order | **OFFICIAL** ref-en §2.1 (`<Subject 1> is the young woman in <Picture 1>, with ...`); the sheet is cited inside the subject with no standalone `<Picture>` entry (§2: "cite the image source inside the corresponding `<Subject N>` definition") |
| S2 | `<Subject p> is the location in <Picture p>: {described}` where `p = n+1` | **OFFICIAL** ref-en §2.1 ("Scenes, backgrounds, or environments" are subjects) + §2 (cite the defining image inside the subject) |
| S3 | `<Picture p> defines this {room\|place} alone; each shot keeps the framing of its own first-frame picture.` | **OURS.** The plate leaked into T01 as a *shot* at 0.88-0.996 similarity (review7 headline). Stated positively — "no frame is framed like `<Picture p>`" is the negation the owner bans. |
| S4 | `<Picture a> is the first frame of [Shot k], {one clause naming what the cell shows}.` — **one line per pinned cell**, in first-pin order, `a = n+2 ...` | **OFFICIAL** ref-en §2.2, verbatim form: `<Picture 2> is the first frame of [Shot 1], showing a woman seated beside a café window.` |
| S5 | `<Picture b> is the last frame of [Shot k], {where the body has arrived}.` — only for segments whose END cell exists on disk **and differs from its own start cell** | **OFFICIAL** ref-en §2.2 / §5.3 (`the shot ends on <Picture 3>`). END cells are never pinned (brief, decided); this sentence is the only place they act. |
| S6 | `<Picture s> is a storyboard reference for [Shot 1], [Shot 2] and [Shot 3], giving their order and the way one shot follows another; each shot's own first frame is <Picture a>, <Picture a'> and <Picture a''>.` | **OFFICIAL** ref-en §2.2 (`<Picture 3> is a storyboard reference for [Shot 1] and [Shot 2], defining their viewpoint, subject placement, and shot order.`). The trailing clause is **OURS**: it stops the strip competing with the per-cell pictures for the "first frame" role. |
| S7 | dialogue take: `<Audio 1> is the take's complete audio track: the {N} line(s) spoken on camera at their own times, over silence for the rest of its length.` | **OFFICIAL** ref-en §2.4 (an `<Audio N>` definition states the audio's role) |
| S7' | narration take: `<Audio 1> is the take's complete audio track and runs silent for its whole length.` | **OURS**, honest: narration is laid on the master and `composite()` feeds `anullsrc`. Today's text ("the lines spoken on camera, and silence elsewhere") claims speech that is not in the file. |

Picture numbering **is** reference-slot order, and `graph_for()` stages them in list order, so the
refs list becomes exactly:
`cast sheets (<=2) -> plate -> pinned cells (first-pin order) -> END cells -> strip`.
`MiniMaxH3ReferenceToVideo.ref_images` is an Autogrow with `min=0, max=9`
(`nodes_minimax_h3.py:267-270`); worst case on this episode is take [7,8] at 7 pictures. Fits.

### 1.2 `summary`

```
[reference generation + keyframe completion + audio reuse] One {frames/fps:.2f}-second take of {n} shots in <Subject p>, {short location name}. [Shot 1] begins from <Picture a1> and runs from 00:00 to 00:03; [Shot 2] begins from <Picture a2> and runs from 00:03 to 00:08. {one sentence of what happens, naming the subjects}. <Audio 1> is the complete audio track.
```

| element | Source |
|---|---|
| the three task types joined with ` + ` | **OFFICIAL** ref-en §3: `keyframe completion` = "An image serves as the target video's first frame, keyframe, last frame ... or another concrete frame anchor" (our pins); `reference generation` = the sheets, plate and strip; `audio reuse` = "The same audio signal is reused in full or in part" (`fully_copy`). "When a task satisfies multiple relationships, combine the task types with ` + `". Ours says only `[reference generation]`. |
| `{frames/fps:.2f}` — the **rendered** length, never `placed_seconds` | **OFFICIAL** base-en §2.1 states the effective duration "formatted to exactly two decimal places". Ours prints the placed length: T01 says "6.79-second" for a 7.29 s latent; T20 says "11.83" for 12.25. |
| per-shot `begins from <Picture a>` + its range | **OFFICIAL** ref-en §3 ("uses the previously defined labels to describe the main subjects, shot flow"); the range is **OURS** (owner: always give the range). No new labels are introduced, per §3. |
| no `(Sx)` anywhere in `summary` | **OURS**, conservative: ref-en §5.4 forbids `(Sx)` only in `retention_analysis`, but says IDs are assigned "according to the order of actual vocal events", so the first `(Sx)` is introduced at the first vocal event in `detailed_description`. |

### 1.3 `retention_analysis`

| # | Sentence emitted | Source |
|---|---|---|
| R1 | `<Subject k> (appears in [Shot 1], [Shot 2]): fully_preserved - face, hair, build and clothes exactly as in <Picture k>.` | **OFFICIAL** ref-en §4.1 subject entry, verbatim shape |
| R2 | `<Subject p> (the location behind [Shot 1] and [Shot 2]): partially_preserved - {the materials, furniture and light that carry into the shots}; <Picture p> serves as a definition of the {room\|place} and each shot keeps the framing of its own first-frame picture.` | **OURS on two counts.** (a) `partially_preserved` instead of `fully_preserved`: ref-en §4.1 — "the referenced content is still used, but some defined characteristics are changed or only partially retained"; the plate's *wide empty composition* is not retained, its materials are. (b) `(the location behind ...)` instead of `(appears in ...)`: the owner's rule that the plate is a **definition**, not a thing that appears in a shot, and `appears in` is the phrasing that measurably invited the plate in as a cutaway. |
| R3 | `<Picture a> ([Shot k] first frame): fully_preserved - viewpoint, subject placement, wardrobe and light.` — one per pinned cell | **OFFICIAL** ref-en §4.1 Picture entry, verbatim: `<Picture 2> ([Shot 1] first frame): fully_preserved - ...` |
| R4 | `<Picture b> ([Shot k] last frame): fully_preserved - the same viewpoint with the action completed.` — only where S5 was emitted | **OFFICIAL**, same form |
| R5 | `<Picture s> (storyboard reference for [Shot 1], [Shot 2] and [Shot 3]): weak_reference - the order of the shots and the way each one is staged; every frame comes from the shot's own first-frame picture.` | **THE RIGHT MARKER, and it is official.** ref-en §4.1: `weak_reference` = "Only broad similarity in style, category, composition, or atmosphere is retained." A 2-to-7-panel composite downscaled into one slot cannot be a preserved frame. Ours today says `<Picture 3> ([Shot 1] first frame, [Shot 2] first frame): fully_preserved` — one image claimed as the first frame of every shot, which §2.2 splits into two different roles. |
| R6 | `<Audio 1>: fully_copy - <Audio 1> is reused 1:1 as the take's complete final audio track.` | **OFFICIAL** ref-en §4.2, verbatim example |
| R7 | no `(Sx)` in this section | **OFFICIAL** ref-en §5.4: "Do not write `(Sx)` in `retention_analysis`." |

### 1.4 `detailed_description`

**Line 0, before `[Shot 1]`** — `Photoreal cinematic live-action, 1881 London, 35 mm film grain, natural weight and pace.`
**OFFICIAL** ref-en §5.2: in full-reference mode the style opening is "Established in one or two
English sentences before `[Shot 1]`". Ours already complies.

**Per segment `k`, in this order:**

| # | Sentence emitted | Source |
|---|---|---|
| D1 | `[Shot k] From MM:SS to MM:SS.` — `k=1` starts at `00:00`; every range's end **is** the next range's start; the last range ends at `ceil(frames/fps)` | **OURS**, owner verbatim: "always start with 0 ... integer values of time ... always have a time range" and "timestamps should account for ALL the time of the video". The guide gives `[Shot 1]` no timestamp and later shots a bare onset (§5.1). Ceiling, not rounding: a 7.29 s take ends at `00:08` so no second of the latent is unnamed; the exact 7.29 is still stated once, in `summary`. |
| D2a | `k=1`: `The shot begins from <Picture a>: {frame text as a noun phrase, people replaced by their <Subject> tags}.` | **OFFICIAL** ref-en §5.3 phrase `the shot begins from <Picture 1>`. Deletes ours' `the shot shows Close on Watson ...` (ungrammatical: the frame text already opens with a shot size). |
| D2b | `k>1`: `At MM:SS the shot cuts to {frame text as a noun phrase}, beginning from <Picture a>.` | **OFFICIAL** base-en §4.2 (`the shot cuts to` is one of the five listed cut phrases) + ref-en §5.3. This is the owner's "give the range, and then say at what time what happens": the range in D1, the onset here. |
| D3 | static: `The camera holds a static shot as {action 1}, from MM:SS to MM:SS.` | **OFFICIAL** base-en §4.3, its own example sentence: *"The camera holds a static shot as the runner exits the frame."* Replaces ours' `Static shot; the camera position and lens remain still throughout` — an assertion of immobility over the whole shot, which §4.3 explicitly does not do ("written as a natural English action within the shot"). |
| D3' | moving: `The camera tracks beside them as {action 1}, from MM:SS to MM:SS.` / `The camera pushes in with small amplitude as {action 1}, ...` | **OFFICIAL** base-en §4.3 motion-type table + "Add amplitude and speed only when they are meaningful; medium amplitude and normal speed are usually omitted." Deletes ours' `slowly, with small amplitude, in one continuous motion in one direction`. |
| D4 | `At MM:SS {action j}.` — one per remaining action clause, integer stamps strictly increasing inside the segment | **OURS**, owner: "give the range, and then say at what time what happens if you wanna be specific". Also closes the untimed-tail finding (review7 #5). |
| D5 | `..., and the {noun} continues to the last frame of the shot.` — appended to the last action of every segment | **OURS**, measured: 6 of 8 dialogue segments froze at the second their line ended, and the untimed "Then ..." tails are where the holds sat (frozen_prompt §3; plan_vs_render §1.1). |
| D6 | public setup only: `Behind {them\|him} {life clause}, from MM:SS to MM:SS.` | **OURS**, owner verbatim: "i liked you added some background folks in public shots, that is having people regular work sells that thing". Needs a new `Setup.life: str = ""` field (§3.11). Public here = `criterion`, `cab`, `gateway`; empty for `corridor`, `lab`, `bench`. |
| D7 | narration segment with a person on camera: `<Subject k>'s mouth is closed from MM:SS to MM:SS while he {action}.` — the range **clipped to this segment**, one sentence per segment the line overlaps | **OURS.** The official voiceover form (base-en §4.4: `says in an off-screen voiceover` + "his lips remain completely closed") presumes the narration is *in the track*; ours is not (owner, 2026-09-11: only dialogue goes into a take's audio). "remain" is also a measured freeze word (>=2 stillness words -> 0.77 frozen vs 0.47). This also fixes the unclipped span: `voice_events()` still emits `span(t0, t0+duration)`, so T01 says `From 00:00 to 00:05` inside a shot that ends at `00:03`. |
| D7' | narration segment with **no** person (an insert): emit nothing about lips; instead `Only the hand, the stick and the counter top are in frame.` | **OURS**, review7 #1: "a hand insert has no corresponding character". Replaces the `hidden` heuristic's `The people are seen from behind, in profile or far off.` — that sentence is a composition, and it is the plate's composition. |
| D8 | first vocal event of a speaker: `<Subject k> (Sx), on screen, {a lean sunburnt man in his late twenties with a dry, clipped English baritone at an even pace}, says: <d>[English] {line text verbatim}</d>` | **OFFICIAL** ref-en §5.4 (`<Subject N> (Sx)` when the subject speaks; mark `off-screen` if off) + base-en §4.4 ("When a speaker first appears, provide enough information ... character type, age, gender, whether the person is on-screen, pitch, timbre, speaking rate, or accent" and "Place the speaker's identifying phrase, ID, action, and delivery outside `<d>`"). Ours has the tag and nothing else. Later events in the same take: `<Subject k> (Sx) says: <d>...</d>` with no re-description (ref-en §5.3). |
| D9 | `His mouth shapes every syllable as the line is heard and closes on the last word.` | **OURS**, kept: the lips are driven by the line's own wav, and the measured dialogue lag is 0.00 / 0.00 / 0.00 / 0.00 / -0.01 s across the five dialogue takes. |
| D10 | `At MM:SS, as the line ends, {action 2}, and the {noun} continues to the last frame of the shot.` | **OURS**, measured: T14 froze at 9.50 s (line end 9.50), T22 at 3.00 s (line end 2.92). A dialogue shot's follow-on beats are timed from the **line end**, never from the segment start. |
| D11 | any walk / climb / ride in the segment carries a pace: `at a normal walking pace`, `at a normal pace`, `at the horse's trot` | **OURS**, owner: the motion runs at normal speed, never "slow" alone on a person. base-en's speed vocabulary (`at slow speed` / `at fast speed`) is camera-only. |
| D12 | Watson walking or climbing anywhere in the segment: `limps along on his stick at a normal walking pace` / `limps on his stick ... the stick planting on every second step` | **OURS**, owner verbatim: Watson limps and walks slowly on his stick while Stamford walks at a normal pace, and the motion runs at normal speed. The word "slowly" never reaches the prompt; the limp carries the slowness. |
| D13 | every segment, including a one-second reference or establishing beat, contains at least one **body-scale** action | **OURS**, owner verbatim: "if we need a ref shot, like just show the other character, put it for a second and define an action, so it is not static" and "all MiniMax ref2v prompts should include some action". Eyes, brows, blinks, breath, jaw and fingers-alone do **not** satisfy it; a hand that lifts, reaches, plants or sets down does. |

### 1.5 `overall_soundscape`

```
overall_soundscape: {1-4 sentences of ambience and physical action sound}.
```

**OFFICIAL** base-en §4.6: 1-4 sentences in one paragraph, ambient + physical action + non-verbal
human sound; "Dialogue, singing, and diegetic music already belong in the multimodal description and
should not be repeated here." Ours today writes `Stamford's voice, close and dry; the room's own tone
underneath.` — a delivery note that belongs in `detailed_description` — and on narration takes it
says "the narration is off-screen" about audio that is not in the file.

### 1.6 `non_diegetic_music`

```
non_diegetic_music: N/A
```

**OFFICIAL** base-en §4.7 ("Use `N/A` when there is no non-diegetic music"). Unchanged.

---

## 2. TWO WORKED PROMPTS, EXACTLY AS THEY WOULD BE EMITTED

Real takes of `library\20260822113400_a-study-in-scarlet\episodes\ep01`, with the real measured
numbers (`placed.json`, `episode_takes.grid_frame`, `lines\lines.json`).

### 2.A Take T01 — NARRATION, 2 shots, Criterion (a public location)

Measured inputs: `frames 175` -> 7.2917 s, ceiling **00:08**. Segments: `[Shot 1]` at frame 0 = 00:00;
`[Shot 2]` at `grid_frame(round(3.16*24) = 76) = 77` = 3.208 s -> **00:03**. Narration line 1 runs
0.25 - 5.02 s and crosses the cut. Faces `[john_watson]`.
Refs, in slot order: `char-john_watson_criterion.png`, `plate_criterion.png`, `Q01_0.png`,
`Q01_1.png`, `ref_take_01.png` -> `<Picture 1..5>`.

**Plan `motion` it is built from** (rewritten to the §1.4 rules; the text on disk today fails the
lint on "hold", "slow" and "does not", and gives the shot no body-scale action):

```
shot 1   : static; Watson lifts the wine glass from the mahogany and drinks; he lowers the glass to the counter and turns the bowler over against his chest; he sets his hand back on the silver ball knob of the black stick and leans his weight onto it
shot 1.1 : static; the fingers loosen on the silver knob and close on it again; the hand reaches across the mahogany, lifts the wine glass, drinks out of frame and sets it down beside the knob; the thumb comes over the ball of the knob and the wrist turns the stick a quarter round on the tiles
```

**Emitted prompt:**

```text
subject_definitions:
<Subject 1> is John Watson in <Picture 1>: A man in his late twenties, as thin as a lath, as brown as a nut, dark hair swept back, a thin waxed moustache, wearing a fawn tweed overcoat and a white cravat pinned with a stud; a brown bowler hat, on his head outdoors and in his left hand indoors; both hands bare; a bare sunburnt right hand on the silver ball knob of a black walking stick.
<Subject 2> is the location in <Picture 2>: The Criterion Bar, Piccadilly, 1881, early evening: a long mahogany counter with a brass foot-rail under a great gilt-framed mirror, gasoliers burning yellow through tobacco haze, marble pillars, bottles ranked on glass shelves, a tiled floor; drinkers two deep at the near end by the doors, thinning to an empty stretch of counter at the far end under the mirror; the mirror behind the counter is silvered glass in a gilt frame and reflects the men's backs, the gasoliers and the bottle shelves of this same room; warm gaslight, with the dark street beyond the doors alone. <Picture 2> defines this room alone; each shot keeps the framing of its own first-frame picture.
<Picture 3> is the first frame of [Shot 1], a close shot of Watson turned from the counter near its crowded end with the brown bowler carried against his chest.
<Picture 4> is the first frame of [Shot 2], an insert at the brass foot-rail of Watson's bare sunburnt hand on the silver ball knob of his black stick.
<Picture 5> is a storyboard reference for [Shot 1] and [Shot 2], giving their order and the way one shot follows the other; each shot's own first frame is <Picture 3> and <Picture 4>.
<Audio 1> is the take's complete audio track and runs silent for its whole length.

summary:
[reference generation + keyframe completion + audio reuse] One 7.29-second take of 2 shots in <Subject 2>, the Criterion Bar. [Shot 1] begins from <Picture 3> and runs from 00:00 to 00:03; [Shot 2] begins from <Picture 4> and runs from 00:03 to 00:08. <Subject 1> drinks at the crowded end of the counter and the take closes on his hand on the silver knob of his stick, with the drinkers working behind him throughout. <Audio 1> is the complete audio track.

retention_analysis:
<Subject 1> (appears in [Shot 1], [Shot 2]): fully_preserved - face, hair, build and clothes exactly as in <Picture 1>.
<Subject 2> (the location behind [Shot 1] and [Shot 2]): partially_preserved - the mahogany counter, brass foot-rail, gilt mirror, gasoliers, bottle shelves and yellow haze carry into both shots behind the people and beneath the hand; <Picture 2> serves as a definition of the room and each shot keeps the framing of its own first-frame picture.
<Picture 3> ([Shot 1] first frame): fully_preserved - viewpoint, subject placement, wardrobe and light.
<Picture 4> ([Shot 2] first frame): fully_preserved - viewpoint, subject placement, wardrobe and light.
<Picture 5> (storyboard reference for [Shot 1] and [Shot 2]): weak_reference - the order of the two shots and the way each one is staged; every frame comes from the shot's own first-frame picture.
<Audio 1>: fully_copy - <Audio 1> is reused 1:1 as the take's complete final audio track.

detailed_description:
Photoreal cinematic live-action, 1881 London, 35 mm film grain, natural weight and pace.
[Shot 1] From 00:00 to 00:03. The shot begins from <Picture 3>: a close shot of <Subject 1> turned from the mahogany counter near its crowded end, bareheaded, dark hair swept back, his gaunt sunburnt face and thin moustache filling the frame, the brown bowler in the hand on the right of frame pressed against his chest, Stamford's black shoulder at the left edge, gaslight on him and the drinkers soft behind. The camera holds a static shot as <Subject 1> lifts the wine glass from the mahogany and drinks, from 00:00 to 00:01. At 00:01 he lowers the glass to the counter and turns the bowler over against his chest. At 00:02 he sets his bare sunburnt hand back on the silver ball knob of the black stick and leans his weight onto it, and the lean continues to the last frame of the shot. Behind him the drinkers two deep at the near end talk, lift their glasses and shift on their feet, and a barman reaches a bottle down from the glass shelf, from 00:00 to 00:03. <Subject 1>'s mouth is closed from 00:00 to 00:03 while he drinks and turns the bowler.
[Shot 2] From 00:03 to 00:08. At 00:03 the shot cuts to an insert at the brass foot-rail, the same place at the counter, beginning from <Picture 4>: <Subject 1>'s bare sunburnt hand on the silver ball knob of his black stick, the frayed tweed cuff above it, a wine glass beside it on the mahogany, the brass rail and the tiled floor below; only the hand, the stick and the counter top are in frame. The camera holds a static shot as the fingers loosen on the silver knob and close on it again, from 00:03 to 00:05. At 00:05 the hand reaches across the mahogany, lifts the wine glass, carries it up out of frame and brings it back down beside the knob. At 00:06 the thumb comes over the ball of the knob and the wrist turns the stick a quarter round on the tiles, and the turn continues to the last frame of the shot. Behind the hand a drinker's sleeve passes along the brass rail and a second pair of hands sets a glass down on the mahogany, from 00:03 to 00:08.

overall_soundscape: Yellow gaslight hisses in the gasoliers over the steady murmur of drinkers at the near end of the counter. Glasses are set down on mahogany, boots scuff the tiled floor, and bottles move on the glass shelves behind the bar throughout the take.

non_diegetic_music: N/A
```

`detailed_description` = **396 words** (Shot 1: 196, Shot 2: 187). Today's T01 is 218 words
(Shot 1: 130, Shot 2: 87).

### 2.B Take T20 — DIALOGUE, 3 segments, gateway (public location, tracking, the limp)

Measured inputs: `frames 294` -> 12.25 s, ceiling **00:13**. Segments: frame 0 = 00:00;
`grid_frame(115) = 115` = 4.792 s -> **00:05**; `grid_frame(188) = 188` = 7.833 s -> **00:08**.
Dialogue line 20 (`john_watson`) runs 0.25 - 3.83 s, so it ends at **00:04**. Narration line 21 runs
4.958 - 10.368 s, crossing the 00:08 cut, so it is clipped into two sentences.
Faces `[john_watson]`. Refs: `char-john_watson.png`, `plate_gateway.png`, `Q20_0.png`, `Q21_0.png`,
`Q21_1.png`, `ref_take_20.png` -> `<Picture 1..6>`.

**Plan `motion` it is built from:**

```
shot 20   : static; Watson puts the question to the man beside him; he lifts the black stick off the paving, plants it a pace forward, takes his weight on it and limps one step after Stamford at a normal walking pace
shot 21   : track beside them; Watson limps along on his stick at a normal walking pace while Stamford walks at a normal pace a step ahead of him, the iron railings and the hospital wall sliding past behind them; Stamford lifts one shoulder in a shrug and turns his head back to Watson; the corner of the hospital wall comes up ahead of them and both men walk on toward it
shot 21.1 : track ahead of him; Watson limps on his stick toward the camera at a normal walking pace, the stick planting on every second step and the railings sliding past behind him; he turns his head to Stamford beside him and back to the pavement ahead, and his brows draw together; he lengthens his stride to keep level with Stamford and the stick swings up and plants again
```

**Emitted prompt:**

```text
subject_definitions:
<Subject 1> is John Watson in <Picture 1>: A man in his late twenties, as thin as a lath, as brown as a nut, dark hair swept back, a thin waxed moustache, wearing a fawn tweed overcoat and a white cravat pinned with a stud; a brown bowler hat, on his head outdoors and in his left hand indoors; both hands bare; a bare sunburnt right hand on the silver ball knob of a black walking stick.
<Subject 2> is the location in <Picture 2>: The street front of Saint Bartholomew's Hospital, 1881, late afternoon: a stone gateway arch onto the wet cobbled street, iron gates open, worn stone steps beyond the arch up to a small side-door in soot-dark brick, a pavement with iron railings along the hospital wall running to a corner, gas lamps on iron posts unlit, fog thinning, rain just stopped. <Picture 2> defines this place alone; each shot keeps the framing of its own first-frame picture.
<Picture 3> is the first frame of [Shot 1], a medium close-up of Watson stopped on the wet pavement just outside the gateway arch with the question on his face.
<Picture 4> is the first frame of [Shot 2], a medium two-shot side on along the iron railings with Stamford nearer the camera in profile and Watson beyond him, both walking.
<Picture 5> is the first frame of [Shot 3], a close shot of Watson walking along the railings with his eyes on Stamford at the frame edge.
<Picture 6> is a storyboard reference for [Shot 1], [Shot 2] and [Shot 3], giving their order and the way one shot follows another; each shot's own first frame is <Picture 3>, <Picture 4> and <Picture 5>.
<Audio 1> is the take's complete audio track: the one line spoken on camera at 00:00, over silence for the rest of its length.

summary:
[reference generation + keyframe completion + audio reuse] One 12.25-second take of 3 shots in <Subject 2>, the street front of Saint Bartholomew's Hospital. [Shot 1] begins from <Picture 3> and runs from 00:00 to 00:05; [Shot 2] begins from <Picture 4> and runs from 00:05 to 00:08; [Shot 3] begins from <Picture 5> and runs from 00:08 to 00:13. <Subject 1> puts his question at the gateway and then walks the pavement beside Stamford toward the corner, with the street traffic and the hospital porters working behind them. <Audio 1> carries that one spoken line and is the complete audio track.

retention_analysis:
<Subject 1> (appears in [Shot 1], [Shot 2], [Shot 3]): fully_preserved - face, hair, build and clothes exactly as in <Picture 1>.
<Subject 2> (the location behind [Shot 1], [Shot 2] and [Shot 3]): partially_preserved - the gateway arch, the open iron gates, the wet cobbles, the iron railings, the soot-dark hospital wall and the grey late-afternoon light carry into all three shots behind the people; <Picture 2> serves as a definition of the place and each shot keeps the framing of its own first-frame picture.
<Picture 3> ([Shot 1] first frame): fully_preserved - viewpoint, subject placement, wardrobe and light.
<Picture 4> ([Shot 2] first frame): fully_preserved - viewpoint, subject placement, wardrobe and light.
<Picture 5> ([Shot 3] first frame): fully_preserved - viewpoint, subject placement, wardrobe and light.
<Picture 6> (storyboard reference for [Shot 1], [Shot 2] and [Shot 3]): weak_reference - the order of the three shots and the way each one is staged; every frame comes from the shot's own first-frame picture.
<Audio 1>: fully_copy - <Audio 1> is reused 1:1 as the take's complete final audio track.

detailed_description:
Photoreal cinematic live-action, 1881 London, 35 mm film grain, natural weight and pace.
[Shot 1] From 00:00 to 00:05. The shot begins from <Picture 3>: a medium close-up of <Subject 1> stopped on the wet pavement just outside the gateway arch, the brown bowler on his head, dark hair, thin moustache, turned to Stamford off frame at the left, the question on his face, the silver knob of the black stick under his bare sunburnt hand at the bottom of frame, iron railings and the soot-dark hospital wall behind him, grey late-afternoon light. The camera holds a static shot as <Subject 1> puts the question to the man beside him, from 00:00 to 00:04. <Subject 1> (S1), on screen, a lean sunburnt man in his late twenties with a dry, clipped English baritone at an even pace, says: <d>[English] How the deuce did he know I was in Afghanistan?</d> His mouth shapes every syllable as the line is heard and closes on the last word. At 00:04, as the line ends, he lifts the black stick off the paving, plants it a pace forward, takes his weight on it and limps one step after Stamford at a normal walking pace, and the step continues to the last frame of the shot. Behind him a hansom rolls past on the wet cobbles at the horse's trot and a porter carries a crate in through the open iron gates, from 00:00 to 00:05.
[Shot 2] From 00:05 to 00:08. At 00:05 the shot cuts to a medium two-shot side on along the railings, halfway to the corner, beginning from <Picture 4>: Stamford nearer the camera in strict profile, dark hair, a round clean-shaven face, a black frock coat and a half smile, with <Subject 1> beyond him in the brown bowler watching his face, the black stick's silver knob swinging in his bare sunburnt hand on the railings side. The camera tracks beside them as <Subject 1> limps along on his stick at a normal walking pace and Stamford walks at a normal pace a step ahead of him, the iron railings and the hospital wall sliding past behind them, from 00:05 to 00:08. At 00:06 Stamford lifts one shoulder in a shrug and turns his head back to <Subject 1>. At 00:07 the corner of the hospital wall comes up ahead of them and both men walk on toward it, and the walk continues to the last frame of the shot. On the pavement beyond them two clerks in dark coats walk the other way and a hansom is drawn up at the corner with its horse shifting in the shafts, from 00:05 to 00:08. <Subject 1>'s mouth is closed from 00:05 to 00:08 while he limps along the railings.
[Shot 3] From 00:08 to 00:13. At 00:08 the shot cuts to a close shot of <Subject 1> walking along the railings, beginning from <Picture 5>: the brown bowler on, the thin moustache, his eyes on Stamford beside him at the frame edge, the hospital wall and the railings sliding past behind him. The camera tracks ahead of him as <Subject 1> limps on his stick toward the camera at a normal walking pace, the stick planting on every second step and the railings sliding past behind him, from 00:08 to 00:10. At 00:10 he turns his head to Stamford beside him and back to the pavement ahead, and his brows draw together. At 00:11 he lengthens his stride to keep level with Stamford and the stick swings up and plants again, and the walk continues to the last frame of the shot. Behind him a porter with a crate on his shoulder passes the other way and a costermonger's barrow stands at the kerb, from 00:08 to 00:13. <Subject 1>'s mouth is closed from 00:08 to 00:10 while he walks.

overall_soundscape: Wet cobbles and standing water carry under boots and the ferrule of a walking stick, and the iron railings ring faintly as the men pass. A hansom's hooves and wheels cross the street behind them, under the low murmur and footfall of the pavement, throughout the take.

non_diegetic_music: N/A
```

`detailed_description` = **640 words** (Shot 1: 228, Shot 2: 218, Shot 3: 181). Today's T20 is 357
words (119 / 132 / 105), and today's Shot 2 names **no on-camera subject at all** — `faces` is empty
for shot 21, so the builder emits `The people are seen from behind, in profile or far off.` That is
exactly the condition review7 blames for the plate walking in: an environment subject declared
present, a shot with nobody named in it, and time to fill.

**One flag for the pins/refs owner, not for the prompt builder.** Stamford is the *nearer* figure in
Shot 2 and his face is described in the frame text, but `plan.json` shot 21 has `faces: []`, so no
Stamford sheet is staged and he cannot be a `<Subject>`. The template describes him in words. Either
add `stamford` to shot 21's `faces` (still inside `MAX_FACES = 2`) or accept a described-only
Stamford in that shot.

---

## 3. EXACT FUNCTION-LEVEL CHANGES TO `studio\episode_ref_official.py`

Full path: `D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\studio\episode_ref_official.py`
(207 lines today). Test-first, one thing per function, 10-20 lines each, per the project rules.

| # | function | change |
|---|---|---|
| 3.1 | `stamp(seconds)` | **keep as is** (whole seconds, `MM:SS`). It is the owner's rule and it is what `span()` and the beat stamps both use. |
| 3.2 | `span(start, end)` | **keep**, but every caller must now pass bounds already clipped to the segment. Put the invariant in the docstring: a span never leaves its segment. |
| 3.3 | **new** `take_end(frames, fps=24) -> int` | `math.ceil(frames / fps)`. The last segment's range ends here so no second of the latent is unnamed (owner: "account for ALL the time"). |
| 3.4 | **new** `beats(t0, t1, n) -> list[int]` | `n` strictly increasing integer seconds strictly inside `(t0, t1)`, evenly spread (`t0 + (t1-t0)*(k+1)/(n+1)`, rounded, then forced strictly increasing). If fewer integer seconds exist than clauses, the surplus clauses attach to the last stamp joined with `, then`. ~12 lines. |
| 3.5 | `subjects(...)` | **rewrite.** New signature `subjects(faces, physical, described, segs, ends) -> tuple[str, dict[int, int], int]` returning the text, `{segment index -> first-frame picture number}`, and the strip's picture number. Emits S1, S2, S3, one S4 per pinned cell, one S5 per differing END cell, then S6 and S7/S7'. The shot-list join (`"[Shot 1], [Shot 2] and [Shot 3]"`) moves into a helper `shot_list(ns)`. |
| 3.6 | `ends_sentence(ends)` | **delete.** Its job ("the panel after them shows how [Shot k] ends") is now S5 + R4, which name the picture instead of its position in a strip. |
| 3.7 | `retention(...)` | **rewrite** to R1-R7. The location line becomes `partially_preserved` and drops `appears in`; the strip line becomes `weak_reference`; one `fully_preserved` Picture line per pinned cell and per END cell. Delete the dead `if False else` expression on the `faces_per_segment` line while you are in there. |
| 3.8 | `voice_id(...)` | **keep** (dialogue only, vocal order). |
| 3.9 | **new** `speaker_intro(who, sid, physical, seen) -> str` | first appearance: `<Subject k> (Sx), on screen, {type, age, voice, pace}, says:`; afterwards `<Subject k> (Sx) says:`. `seen` is the set of speaker ids already introduced in this take. The voice descriptor comes from a new `voice` field on the character ref, falling back to a neutral one built from `physical`. |
| 3.10 | `voice_events(...)` | **rewrite.** New signature takes the segment bounds `(seg_t0, seg_t1)`. Narration: emit D7 with the range clipped to `[max(line_t0, seg_t0), min(line_end, seg_t1)]`, and **only** when the segment has a person on camera; otherwise emit nothing (D7' comes from `description()`). Dialogue: D8 + D9 + D10, with D10's stamp `= stamp(line_t0 + line_seconds)`. Delete `at the pace of a spoken line` entirely (it is in all 14 narration takes today). |
| 3.11 | **new** `life_sentence(setup) -> str` | returns D6 from a new `Setup.life: str = ""` field in `studio\episode_spec.py`. Empty -> no sentence. This is the one contract change the spec needs; everything else is builder-local. Values for this episode: `criterion` = `the drinkers two deep at the near end talk, lift their glasses and shift on their feet, and a barman reaches a bottle down from the glass shelf`; `cab` = `shopfronts and gas lamps slide past, a costermonger's barrow stands at the kerb and two passers-by walk the pavement at a normal walking pace`; `gateway` = `a hansom rolls past on the wet cobbles at the horse's trot and a porter carries a crate in through the open iron gates`; `corridor`, `lab`, `bench` = `""`. |
| 3.12 | **new** `limp_clause(text) -> str` | if the segment's action text names Watson with a walk or climb verb and does not already carry `limps`, inject `limping on his stick` after the verb. Raises instead of repairing if the plan already said `slow`. |
| 3.13 | `camera_sentence(motion, t0, t1, line_end=None)` | **rewrite** to D3 / D3' / D4 / D5. Static -> `The camera holds a static shot as {action 1}, from {span}.`; a `MOVES` head -> `The camera {head lower-cased} as {action 1}, from {span}.`, amplitude only when the plan wrote one. Remaining clauses become `At {beats(...)} {clause}.`, the last gaining D5's tail. When `line_end` is given, the beats spread over `[line_end, t1]`, not `[t0, t1]`. Deletes `slowly, with small amplitude, in one continuous motion in one direction` and `Static shot; the camera position and lens remain still throughout`. |
| 3.14 | `segments(...)` | **extend** each dict with `end` (this segment's end second = the next segment's `t`, or `take_end` for the last), `last` (bool) and `setup` (for `life_sentence`). The end computation moves out of `description()`. |
| 3.15 | `description(...)` | **rewrite** the head and the body order: D1, then D2a/D2b, then D3, D4, D5, then D6, then D7/D7'/D8-D10. Delete `the shot shows`; delete the `hidden` heuristic and its `The people are seen from behind, in profile or far off.`; name **every** person in the segment (a `<Subject>` tag when a sheet is staged, a described noun phrase otherwise) so no segment is subject-less. |
| 3.16 | `build(...)` | **rewrite** `summary` per §1.2: the three task types, `frames / fps` to two decimals, the per-shot `begins from <Picture a>` + range. `sound` becomes §1.5 (ambience only; no voice-delivery note, no "the narration is off-screen"). Keep the negation guard and add `check(text)` (§4) after it, raising on the first failing rule with the `[Shot k]` that failed. |
| 3.17 | `NEGATIONS` | **extend** to `no not never nobody nothing none neither nor without barely hardly n't don't doesn't isn't cannot can't`. Keep the `<...>` and `N/A` stripping, and **add**: strip everything between `<d>` and `</d>` before scanning — ref-en §5.4 requires dialogue verbatim, so a line that legitimately contains "not" must never block the build. |
| 3.18 | **new** `lint(text) -> list[str]` / `check(text)` | §4. `lint` returns `"L{n} [Shot k]: message"` strings; `check` raises `ValueError` on a non-empty list. Called from `build()`, so a bad prompt can never reach the GPU. |
| 3.19 | `scripts\episode\takes_r2v.py: card()` | **companion change** (different file, but the spec needs it): `refs = cast sheets + plate + unique pinned cells in first-pin order + END cells + strip`, and pass the segment -> picture map into `ro.build`. `reference_strip()` stays — it is what carries shot order in one image — but is now the **last** slot and the `weak_reference` one. `ref_images` allows 9; worst case here is 7. |
| 3.20 | `scripts\episode\takes_r2v.py: on_grid()` | **optional, cheap, cross-cutting:** snap a cut to the token start nearest the whole second instead of the next token start at or after it. T01's cut would move from frame 77 (3.208 s) to frame 73 (3.042 s), so the text's `00:03` would sit 42 ms from the pin instead of 208 ms. Belongs to the pins owner; listed here because it is what closes the last gap between the owner's integer stamps and the pins. |

Tests to write first (project rule: no implementation before its test), all free and offline:
`take_end`; `beats` (spread, collision, overflow); `span` clipping; `subjects` picture numbering
(cells -> END -> strip); `retention` markers (`partially_preserved` on the location,
`weak_reference` on the strip, no `(Sx)` anywhere); `speaker_intro` (first vs later);
`voice_events` clipping across a cut; `camera_sentence` static / moving / dialogue-tail;
`life_sentence` on a public vs a private setup; `limp_clause`; and every rule of `lint` (§4).

---

## 4. PROMPT LINT — what makes a prompt FAIL before it is sent

`lint(text) -> list[str]`, called by `build()` through `check(text)`. Scope: the whole emitted
prompt, with everything between `<d>` and `</d>` removed first (dialogue is verbatim by grammar) and
the label tags `<Subject N>`, `<Picture N>`, `<Audio N>` and `N/A` removed before word scanning.

| id | rule | fails when |
|---|---|---|
| **L1** | NEGATION | any of `no not never nobody nothing none neither nor without barely hardly n't don't doesn't isn't cannot can't` appears outside `<d>` |
| **L2** | STILLNESS | any of `still stays stay remain remains motionless frozen pause pauses waits unchanged unmoving` appears; `holds a static shot` is the single allowed use of `hold` |
| **L3** | SLOW | `slow`, `slowly` or `slow motion` appears anywhere (this episode names no slow camera move; the limp carries the slowness) |
| **L4** | NO ACTION | a `[Shot k]` block contains no body-scale verb (`walks limps climbs steps turns lifts raises lowers sets down picks up reaches pushes pulls opens crosses passes enters leaves travels drinks pours writes shrugs plants springs rolls sways drops takes off follows arrives carries swings`). Eyes, brows, blinks, swallow, breath, jaw and fingers-alone do not count |
| **L5** | COVERAGE | the `[Shot k] From A to B` ranges do not satisfy `A(1) == 00:00`; `B(k) == A(k+1)` for every k; `B(last) == ceil(frames/fps)`; `A(k) < B(k)` |
| **L6** | STAMP OUT OF RANGE | any `At MM:SS` or `from MM:SS to MM:SS` inside `[Shot k]` falls outside that shot's own range, or two `At` stamps in one block are not strictly increasing |
| **L7** | PIN DISAGREEMENT | `abs(grid_frame_seconds(k) - parsed_stamp(k)) > 0.5` for any k > 1 |
| **L8** | NO PACE | a walk / limp / climb / trot / ride verb in a block with no `at a normal walking pace`, `at a normal pace`, `at the horse's trot` or `at normal speed` in the same block |
| **L9** | NO LIMP | a block names Watson plus a walk or climb verb and contains no `limp` |
| **L10** | NO LIFE | a block whose setup has a non-empty `Setup.life` does not contain that setup's life clause |
| **L11** | PICTURES | any `<Picture N>` cited without a definition; `N > 9`; the number of picture definitions != the number of staged refs; a picture declared the first frame of more than one shot; the plate declared a first or last frame; the strip's retention marker is anything but `weak_reference`; the location subject's marker is anything but `partially_preserved`, or its retention line contains `appears in` |
| **L12** | SPEAKERS | `(Sx)` appears in `retention_analysis`; ids are not `S1..Sn` in vocal order; the first occurrence of an id carries no identity clause; a `<d>[English] ...</d>` body does not match its `Line.text` byte for byte |
| **L13** | TASK TYPE | `summary` does not begin with `[`; a relationship in use is unnamed (`keyframe completion` whenever anchors exist, `audio reuse` whenever an `<Audio N>` is `fully_copy`, `reference generation` whenever a sheet / plate / strip is staged); a type is repeated |
| **L14** | LENGTH | `detailed_description` under 350 words, or any `[Shot k]` block outside 150-240 words |
| **L15** | SUMMARY LENGTH | the seconds stated in `summary` differ from `frames / fps` by more than 0.01 |
| **L16** | DIALOGUE TAIL | a block holding a dialogue line has no `At MM:SS` at or after the second the line ends |
| **L17** | CROSS-CUT LINE | a **dialogue** line's span crosses a segment boundary and neither part carries `<scenetrans>` (ref-en §5.1 / base-en §4.4). No line in ep01 does; the rule exists so the first one that does cannot ship silently |
| **L18** | BANNED PROP | `glove` anywhere (already `BANNED_PROPS` in `episode_spec.py`; the lint repeats it at prompt level) |

### Test cases (every input string below is real, from disk)

| # | input | expect |
|---|---|---|
| T1 | `Static shot; the camera position and lens remain still throughout.` (present in all 40 blocks on disk today) | FAIL L2 |
| T2 | `nobody on screen speaks while John Watson's lips remain completely closed` (iteration-4 T01) | FAIL L1, L2 |
| T3 | `Lips stay closed ... a single slow breath` (T16.1, measured 98 % frozen) | FAIL L2, L3, L4 |
| T4 | `the finger stays over the water; the water stays clear` (T17, 97-100 % frozen in both iterations) | FAIL L2, L4 |
| T5 | `lie still ... does not change` (T10.1, 94 % frozen) | FAIL L1, L2, L4 |
| T6 | `The smile stays on him ... His head does not turn away and the framing does not change.` (T22, freezes at 3.00 s) | FAIL L1, L2, L4, L16 |
| T7 | `his eyes narrow slightly` alone | FAIL L4 (micro-motion only) |
| T8 | `Tracking beside at walking pace, slowly, with small amplitude, in one continuous motion in one direction.` (T20 shot 2 today) | FAIL L3; PASS L8 |
| T9 | today's T01 `[Shot 1] From 00:00 to 00:03 ... From 00:00 to 00:05 John Watson keeps the lips closed` | FAIL L6 (the voice range leaves a shot that ends at 00:03) |
| T10 | today's T20 blocks `00:00-00:05`, `00:05-00:08`, `00:08-00:12` with `frames 294` | FAIL L5 (`ceil(12.25) = 13`, not 12) |
| T11 | today's T01 `summary: ... One 6.79-second take` with `frames 175` | FAIL L15 (7.29) |
| T12 | today's T01 `[reference generation]` with 2 anchors and an `<Audio 1>: fully_copy` | FAIL L13 |
| T13 | today's `<Picture 3> ([Shot 1] first frame, [Shot 2] first frame): fully_preserved` for the strip | FAIL L11 (one picture as two shots' first frame, and the strip marked `fully_preserved`) |
| T14 | today's `<Subject 2> (appears in [Shot 1], [Shot 2]): fully_preserved - the room ...` | FAIL L11 (`appears in` plus the wrong marker on the location) |
| T15 | today's T20 `<Subject 1> (S1) says: <d>[English] How the deuce ...</d>` with no identity clause | FAIL L12 |
| T16 | today's T20 shot 2: Watson walking, no `limp`, in a `Tracking` block | FAIL L9 |
| T17 | today's T20 shots 2 and 3, gateway setup, no crowd sentence | FAIL L10 |
| T18 | today's whole-prompt word counts (mean 241, blocks 75-149) | FAIL L14 on 18 of 19 takes and on 40 of 40 blocks |
| T19 | `plan.json` `criterion.described` ("thinning to nobody ... not a window ... no street is visible") | FAIL L1 — this is the §0.1 blocker |
| T20 | §2.A's emitted prompt, whole | PASS every rule |
| T21 | §2.B's emitted prompt, whole | PASS every rule |
| T22 | §2.B with the dialogue replaced by a hypothetical `<d>[English] I do not know.</d>` | PASS L1 — proof that `<d>` is stripped before scanning |

Calibration on disk: every one of the 40 shot blocks in `all_prompts.txt` fails at least L2 and L14;
19 of 19 summaries fail L13 and L15; 19 of 19 retention sections fail L11.

The lint is the **pre-render** gate. It is necessary, not sufficient: it cannot predict a freeze
caused by a pin or by a panel drawn at the instant *after* the action. The post-render gate stays
`motion_scan` per segment (`frozen_share <= 0.20` per segment, mean energy `>= 2.0` per take).

---

## 5. WHERE THE OFFICIAL GUIDE CONTRADICTS US

### 5A. Ours is wrong against the guide — fix

| # | ours today | the guide |
|---|---|---|
| 5.1 | `Static shot; the camera position and lens remain still throughout.` in all 40 blocks | base-en §4.3: `Static Shot` is a motion **type**, and camera motion "should be written as a natural English action within the shot, rather than stacked as separate labels"; its own example is `The camera holds a static shot as the runner exits the frame.` Ours asserts immobility over the whole shot with no action bound to it. |
| 5.2 | `slowly, with small amplitude, in one continuous motion in one direction` on every named move | base-en §4.3: the speed vocabulary is `at slow speed` / `at fast speed`; "medium amplitude and normal speed are usually omitted"; "in one continuous motion in one direction" is not in the guide at all. And `slowly` on a tracking shot of two walking men is the slow-motion walk the owner reported. |
| 5.3 | one `<Picture 3>` (the strip) declared `([Shot 1] first frame, [Shot 2] first frame): fully_preserved` | ref-en §2.2 splits the roles: a **standalone** `<Picture N>` is a concrete frame; a **storyboard** picture "state[s] which shots it maps to and what planning information it provides". Ours makes one picture both and claims full preservation of a downscaled composite. |
| 5.4 | `<Subject p> (appears in ...): fully_preserved - the room, its furniture, walls, windows and light.` for the plate | ref-en §4.1: choose the marker "only within the reference role already defined". The plate's role is definition; its wide composition is not retained -> `partially_preserved`. Measured cost of getting this wrong: the plate rendered as a shot at 0.88-0.996 similarity in both T01 attempts. |
| 5.5 | `[reference generation]` alone | ref-en §3: "Choose task types according to the actual role each reference asset plays", combined with ` + `. We pin keyframes and copy an audio track and name neither. |
| 5.6 | `summary` states `placed_seconds` (T01 "6.79" against a 7.29 s latent; T20 "11.83" against 12.25) | base-en §2.1: the effective duration, two decimals. |
| 5.7 | `overall_soundscape: Stamford's voice, close and dry; ...` and `the narration is off-screen` | base-en §4.6: dialogue and singing "already belong in the multimodal description and should not be repeated here"; the section is ambience + physical + non-verbal only. |
| 5.8 | `<Subject 1> (S1) says:` with no identity | base-en §4.4: at first appearance give "character type, age, gender, whether the person is on-screen, pitch, timbre, speaking rate, or accent", outside `<d>`. |
| 5.9 | 241 words per take, 114 per shot block | ref-en §5.2: "normally 350-500 English words ... A single shot does not automatically justify a shorter description". This is also the owner's "the more descriptive you are the better the video will be" — the guide and the owner agree, and only we disagree. |
| 5.10 | `The people are seen from behind, in profile or far off.` (the `hidden` heuristic) | Not in the grammar in any form, and it describes the plate's composition. Delete. |
| 5.11 | `<scenetrans>` / `<cutoff>` never emitted | ref-en §5.1 and base-en §4.4 require `<scenetrans>` when one line crosses a cut. No ep01 line does, but the builder has no code path for it — hence L17. |
| 5.12 | `ends_sentence()`: "the panel after them shows how [Shot 1] ends" | A positional reference into an unlabelled strip. The grammar's form is `the shot ends on <Picture 3>` (§5.3) with a retention line `([Shot k] last frame)` (§4.1). |

### 5B. We deviate on purpose — the owner's rule, stated so it is a decision and not a drift

| # | deviation | guide says | why we do it anyway |
|---|---|---|---|
| 5.13 | `[Shot 1]` carries a time range | ref-en §5.1: "`[Shot 1]` marks the opening shot and has no timestamp" | Owner: "always have a time range ... always start with 0", and every second of the take must be covered. We keep the guide's onset form for `k > 1` (`At MM:SS the shot cuts to`) **in addition to** the range, which is literally the owner's "give the range, and then say at what time what happens". |
| 5.14 | whole-second stamps (`00:03`) | the format is `MM:SS.mmm` | Owner: "integer values of time". Measured cost on this episode: the worst text-vs-pin gap is T01, pin frame 77 = 3.208 s against a stated `00:03` — **0.208 s**. L7 caps it at 0.5 s; change 3.20 closes it to 0.042 s if the pins owner wants it gone. |
| 5.15 | narration is **not** written as `says in an off-screen voiceover` | base-en §4.4 gives that exact phrase for voiceover, followed by the lips statement | Our narration is not in `<Audio 1>` at all (owner, 2026-09-11: anchored narration made the on-screen face mouth the narrator's words). Saying a line is spoken when the wav is silence is a contradiction the model resolves by inventing a speaker. We keep the lips statement, positively and bound to an action (D7), and drop the voiceover claim. |
| 5.16 | `(the location behind [Shot 1] ...)` instead of `(appears in ...)` | ref-en §4.1's subject entry form is `(appears in [Shot 1], [Shot 3])` | The owner's rule that the plate is a definition, plus the measured leak. This is the only place we change a **format** string rather than its content; if it is ever suspected of costing anything, the fallback is `(appears in ...)` with `partially_preserved` kept. |
| 5.17 | a 3-shot take runs to ~640 words, over the 500 ceiling | "normally 350-500" | Owner: more descriptive rather than less; and the guide's own instruction is to "distribute detail across multiple shots according to their information load". The gate is therefore **per shot block** (150-240 words, L14), so a long take is long because it has more shots, never because one shot is padded. |
| 5.18 | every segment, including a one-second reference beat, must carry a body-scale action | the guide is silent | Owner verbatim, and it is the highest-value rule in this document: 51 % of iteration 4's segment time was frozen, and segments carrying two or more stillness words ran 0.77 frozen against 0.47. |

### 5C. One conflict inside our own contract

`episode_spec.MIN_SUB = 2.5` ("a sub-shot must last at least this long") against the owner's "if we
need a ref shot ... put it for a second". Not resolved here — this prompt spec only requires that a
beat of **any** length carries an action. If the owner wants literal one-second reference beats,
`MIN_SUB` is the thing to change, and it belongs to whoever owns the plan contract.
