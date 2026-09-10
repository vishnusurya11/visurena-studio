# Episode 04 — the SIMPLIFY critic: the smallest pipeline that still ships an episode

Written 2026-09-10 against the working tree (nothing in the episode pipeline is
committed yet: every file below is `??` in `git status`). Brief: the owner says
"too many artifacts, too complicated". This is the case for the cut. Every
verdict says whether the thing exists because of a MEASURED failure (keep) or
because a research doc or a vendor guide said so (cut until measured).

Legend: **M** = measured on this box, on this pipeline (the skill files record
it with a date). **R** = a research-doc rule (grade A-C, never run here).
**S** = speculative: no measurement, no failure it answers.

## 0. The count

| what | files | lines / size |
|---|---|---|
| `.claude/skills/episode/SKILL.md` + 7 subskills | 8 | 363 lines |
| `.claude/agents/episode-*.md` | 5 | 127 lines |
| `scripts/episode/*.py` | 7 | 987 LOC |
| `studio/episode_*.py` | 5 | 659 LOC |
| `tests/test_episode_*.py` | 9 | 492 LOC, 54 tests (all pass, 0.46 s) |
| research docs `episode-01..03` | 3 | 94 KB |
| **pipeline total** | **37 files** | **2,628 lines of skill/agent/code/test** |
| `library/.../episodes/ep01/` today | 77 files | 61.0 MB |
| ep01 at planned completion (17 shots, 13 lines) | ~160 files | ~130 MB |

What ep01 has delivered so far: **no `master.mp4`, no `qc.json`, no take on
disk.** `episode.log` shows T00 rendered three times (312 / 342 / 327 s) and
deleted three times; the skill says a fourth prompt "is the current round".
`shots/` holds 17 prompt files and no video. The pipeline has never run
end-to-end; every stage after 4b is unexercised on an episode.

## 1. Inventory and verdict

### 1.1 Stages

| # | stage | script | what it buys | evidence | verdict |
|---|---|---|---|---|---|
| 1 | compress | (writer agent) -> `plan.json` | the episode's shape; the only LLM-judgement step | R (01 s1-2) | **KEEP** — this is the brick |
| 2 | carriers | (writer agent) -> same `plan.json` | no line on a readable mouth | R (03 s0) | **MERGE into 1** — one plan, one validator, one agent; two subskills for one file is method prose, not a stage |
| 3 | plates + sheets | `frames.py plates` | one empty 9:16 plate per setup; `char-<who>.png` for the storyboard's references | M — a plate with a figure carried it into every panel | **MERGE into 4a** — the plate is an input to the sheet, made one line earlier |
| 4a | storyboard | `storyboard.py` | one coherent picture per setup; all 16 panels matched, first try | M (2026-09-10) | **KEEP** — the one measured success and the one paid step |
| 4b | takes | `shots.py` | i2v per panel | M (T00 opens on its panel, HEAD 0) | **KEEP, strip** — FLF, CHAIN, run cards go |
| 4c | review page | `storyboard.py --review` | panel-vs-take html for a human | S — never produced; the measured T00 reads were hand-made stills in `work/` | **KILL** — replace with one contact strip png written by the takes stage |
| 5 | lines | `say_lines.py` | cloned lines + Whisper listen gate | M (trailer: Brigham Young hallucination); 13/13 passed here | **KEEP** as is |
| 6 | assemble | `assemble.py` | cut, bed, mix, captions, chip | trailer's mixer, measured there; unexercised here | **KEEP, merge with 7** |
| 7 | qc | `qc.py` | length, LUFS, TP, cuts seen, lines heard on the master | M for "heard on master" (trailer 08); cut detection S | **MERGE into 6** — qc is the last function of assemble; a failing gate is the script's exit code |

Seven stages -> four scripts + a runner: `lines`, `board`, `takes`, `cut`.

### 1.2 Skill and agent files

| file | lines | what it buys | verdict |
|---|---|---|---|
| `skills/episode/SKILL.md` | 102 | commands, the brick, the measured table, constants, open items | **KEEP, shrink to ~80** — absorb 03-07 as one table row each |
| `subskills/01-compress` | 40 | the writer's procedure (button first, hook, tags, budget, shape) | **KEEP** — the only prose an LLM needs that the code cannot check |
| `subskills/02-carriers` | 38 | carrier table, forbidden list, J/L timing | **MERGE into 01** — half of it is the validator's error messages restated |
| `subskills/03-frames` | 26 | describes `frames.py`; half is the dead compositor lane | **KILL** — the docstring already says it |
| `subskills/04-shots` | 95 | the measurements (sheet size, FLF morph, prompt length) | **KEEP the measurement table only** (~25 lines) in SKILL.md; the prose describing the prompt builder describes code that should not exist |
| `subskills/05-voice` | 19 | describes `say_lines.py` | **KILL** — docstring |
| `subskills/06-assemble` | 25 | describes `assemble.py` + unbuilt phone rules | **KILL** — docstring; the unbuilt list goes to open items |
| `subskills/07-qc` | 18 | the gate table + unbuilt list | **KILL** — the table is `qc.json`'s keys |
| `agents/episode-showrunner` | 26 | order + gates | **KEEP as the one agent** |
| `agents/episode-writer` | 27 | "read 01 and 02, write plan.json, validate" | **MERGE into showrunner** — one agent writes the plan, runs the script, looks at the sheets, reads qc.json |
| `agents/episode-art` | 26 | "look at every sheet" checklist | **MERGE** — the checklist (4 questions) survives as 4 lines in SKILL.md |
| `agents/episode-cinematographer` | 28 | "read T00 before the round" | **MERGE** — one line |
| `agents/episode-editor` | 20 | "read qc.json, fix the mix not the line" | **MERGE** — one line |

Five agents that each say "read SKILL.md, then run one script" are five ways to
lose the context between stages. An unattended run is ONE agent that owns the
whole `epNN/` folder.

### 1.3 Scripts

| file | LOC | on the blind path | verdict |
|---|---|---|---|
| `episode.py` | 40 | runner (`STEPS` tuple, `file:function` loader) | **KEEP** — becomes 4 steps |
| `frames.py` | 319 | ~70 LOC (`conform`, `plate`, `sheet_for`, `physical_of`, `plates`, `STAMFORD`); ~250 LOC is the compositor lane (`place`, `place_group`, `master`, `start_frame`, `masters`, `main`, `scene_kept`, `WARDROBE`, `BLOCKING`, `KEEP`, `GROUP_WHERE`, `SCENE_KEPT`, `PLACE_TRIES`, `EDIT_ONE/TWO`) | **KILL 250 LOC** — off the path for a MEASURED reason (wardrobe swap, 2026-09-10). The skill already records the failure; the code does not need to stay to remember it. git remembers. |
| `storyboard.py` | 166 | `draw`, `sheets`, `grids` (~90); `conform` duplicated from frames.py; review page (~60) | **MERGE** with the 70 live LOC of frames.py into `board.py` (~130 LOC); kill review |
| `shots.py` | 148 | `render`, `main`, `panels` (~70); FLF/CHAIN/`workflow_for`/`end_image` (~25); `run_card`/`prompts` (~30) | **KEEP ~80 LOC** as `takes.py`; kill FLF (measured morph), kill run cards (below) |
| `say_lines.py` | 97 | all of it | **KEEP** unchanged |
| `assemble.py` | 117 | all of it | **KEEP**, absorb qc |
| `qc.py` | 100 | all of it | **MERGE into assemble** as `cut.py` (~180 LOC) |

### 1.4 Studio modules

| file | LOC | what it buys | verdict |
|---|---|---|---|
| `episode_spec.py` | 249 | the contract; 12 validators | **KEEP ~190** — drop `looks`, `continues`, `carrier`, `Shot.cast`, `Setup.sound/reaction/location_id`, `Line.tags/element`, `next_hook/series_cue/button_type/chapter/book`; drop 2 validators (s3) |
| `episode_home.py` | 74 | paths + json io; docstring still lists `masters` and `frames.json` | **KEEP ~50** — fix the docstring, drop `frames_dir`/`shots_dir` in favour of `home()/name` |
| `episode_board.py` | 99 | sheet prompt, chunking, `panel_box`, ALTERNATES | **KEEP ~65** — kill `ALTERNATES`/`alternates()` (S) |
| `episode_take_prompt.py` | 135 | the "official H3 structure" prompt, 12 functions | **KILL** — the measurement it cites says the SHORT prompt won (s5); `beats()` computes second ranges it then throws away; `preserve()` injects `plan.looks` that disagrees with the panel (s6) |
| `episode_captions.py` | 102 | phrase captions in the safe box, name chip | **KEEP** — pure, tested, and the one rule with grade-A evidence (69 % sound-off) |

### 1.5 Tests

| file | tests | verdict |
|---|---|---|
| `test_episode_spec.py` | 15 | **KEEP 13** — drop strangers + carrier-none |
| `test_episode_frames.py` | 8 | **KEEP 2** (`conform`) — 6 test the dead compositor (`BLOCKING`, `KEEP`, `scene_kept`, `place_prompt` x2, `master` group) |
| `test_episode_board.py` | 4 | **KEEP 3** — drop alternates |
| `test_episode_take_prompt.py` | 7 | **KILL 7, write 1** — "the take prompt is frame + motion + register and names no room and no look" |
| `test_episode_shots.py` | 7 | **KEEP 3** — drop FLF x2, run card, HEAD cross-test (HEAD is 0 and gone) |
| `test_episode_captions.py` | 5 | **KEEP** |
| `test_episode_say_lines.py` | 2 | **KEEP** |
| `test_episode_qc.py` | 2 | **KEEP** (moves with the code) |
| `test_episode_home.py` | 4 | **KEEP** |
| | 54 -> ~35 | |

### 1.6 Per-episode artifacts (ep01, 17 shots, 13 lines)

| artifact | today | at completion | what it buys | verdict |
|---|---|---|---|---|
| `plan.json` | 15.8 KB | 1 | the contract | **KEEP, shrink** (s4) |
| `frames/plate_<setup>.png` | 2 (2.4 MB) | 2 | sheet reference | **KEEP** |
| `frames/board_<setup>_<k>.png` | 3 (24.8 MB) | 3 | the paid, cached, coherent picture | **KEEP** — the cache IS the spend guard |
| `frames/board_*.prompt.txt` | 3 | 3 | record of the paid call | **MERGE into `board.json`** — and write it ONLY when the sheet is drawn; today `draw()` rewrites the txt on every cached rerun, so the record can drift from the sheet it claims to describe |
| `frames/SNN.png` | 17 (18.9 MB) | 17 | the take's first frame | **KEEP** |
| `frames/SNN_altK.png` | 10 (10.6 MB) | 10 | "what an editor asks for first" | **KILL** — no editor has asked; no take has failed for a reason an alternate fixes. The spare cells stay ON the sheet (the owner's "no black cell"); `panel_box` crops one by hand the day one is wanted |
| `frames/storyboard.json` | 1 | 1 | shot -> panel map + alternates | **KEEP as `board.json`** without `alternates`; add the prompt per sheet |
| `lines/lNN.wav` + `lines.json` | 14 (2.2 MB) | 14 | the voice, measured seconds, WER | **KEEP** |
| `shots/TNN.prompt.txt` | 17 | 17 | the prompt beside the take | **KILL** — it is already the `prompt` key of `shots.json` (written twice: once by `--prompts`, again at submission) |
| `shots/prompts.json` | 1 (45 KB) | 1 | "run on another H3 host" | **KILL** — S; nobody has a second host; `shots.json` carries the same keys after the round |
| `shots/TNN.mp4` + `shots.json` | 0 | 18 | the takes | **KEEP** |
| `storyboard.html` + `storyboard/SNN.png` | 0 | 18 | panel-vs-take for a human | **KILL** — one `takes/strip.png` contact sheet (panel above frame at 0.3 s) is what the agent needs and what was actually used (`work/t00_strip.png`) |
| `audio/bed.wav` | 0 | 1 | the ACE-Step bed | **KEEP** (made once) |
| `work/*` | 5 hand stills | ~50 (segs, mixed, captioned, ass, levelled lines, shaped bed, level sheet, qc windows) | ffmpeg intermediates | **KEEP but treat as scratch** — delete on a passing qc, keep on a failing one |
| `master.mp4`, `qc.json` | 0 | 2 | the deliverable and its measurement | **KEEP** |
| `*.log` x3 (two empty) | 3 | 3 | tee'd stdout | not the pipeline's |
| **total** | **77** | **~160** | | **~61 files, of which ~50 are the takes, lines and panels a viewer's episode is literally made of** |

## 2. What must survive, and why (the honest half)

These exist because something broke and was seen to break. Cutting them is
not simplifying, it is forgetting:

- **gpt-image storyboard as the input.** Two other approaches failed on this
  chapter on the same day (compositor swapped wardrobes; ref2v blended the room
  and leaked 2.6 s of sheet). One sheet, one setup, coherent by construction.
- **`conform` to 768x1344.** The i2v node stretches (`crop="disabled"`,
  `nodes_minimax_h3.py:145`). Not optional.
- **The Whisper listen gate on lines**, and **"heard on the master"** in QC.
  Both answer a trailer failure (a hallucinated line; a line lost in the sum).
- **All renders, then all listens** in `say_lines`, and **one model resident
  per stage** in the runner. 250-470 s per swap off the HDD, measured from
  ComfyUI's own log.
- **Sheets cached on disk, never redrawn.** The only guard on the only paid step.
- **CHAIN off** — but as a deletion, not a flag. A flag that is measured-wrong
  is a trap for the next agent.
- **`Line` <= 18 words, VO <= 60 %, one turn 50-70 %, button not the lead's,
  no line on a readable face, no onset on a cut.** Research-graded, not
  measured here, but they are the shape of the product and cost one file.
- **Captions in the safe box with a name chip for an off-screen speaker.**
  The one rule with grade-A evidence.

## 3. The minimal target

**Four scripts, one runner, one agent, one skill file, one spec.**

```
scripts/episode/episode.py      runner: lines -> board -> takes -> cut     (~35 LOC)
scripts/episode/lines.py        = say_lines.py, unchanged                   (~95)
scripts/episode/board.py        plate per setup, sheet per <=9 shots, crop  (~130)
scripts/episode/takes.py        i2v per panel, one round, strip.png         (~90)
scripts/episode/cut.py          cut, bed, mix, captions, chip, qc.json      (~190)
studio/episode_spec.py          contract + 10 validators                    (~190)
studio/episode_home.py          paths + json                                (~50)
studio/episode_board.py         sheet prompt, chunks, panel_box             (~65)
studio/episode_captions.py      unchanged                                   (~100)
.claude/skills/episode/SKILL.md commands, brick, writer's procedure,
                                measurement table, 4 look-at questions      (~150)
.claude/agents/episode.md       one agent                                   (~30)
tests/                          ~35 tests
```

~945 LOC + ~180 lines of prose, from 2,628. `lines` runs first because it is
cheap and fails fast on a missing `cast/<who>/voice/design.wav` — before the
paid sheet is drawn.

**Per-episode artifacts:** `plan.json`; `board/` (2 plates, 3 sheets, 17
panels, `board.json` with the prompt per sheet); `lines/` (13 wav,
`lines.json`); `takes/` (17 mp4, `takes.json` with the prompt per take,
`strip.png`); `bed.wav`; `master.mp4`; `qc.json`; `work/` scratch. **61 files.**

**Validators that stay in `episode_spec`** (the plan is the only input an LLM
writes, so this is the only place a bad plan is cheap):

| keep | why |
|---|---|
| 80 <= duration <= 120 | the product |
| shots tile the runtime exactly | `cut.py` depends on it |
| exactly one hook / turn / button; hook ends by 5 s; setup by 15 s; turn at 50-70 % | the brick |
| last line not the protagonist's, on the button shot, >= 2 s silence before it | the brick |
| VO <= 60 %; <= 3 speakers; <= 3 setups; every shot names a defined setup | cheap, shape |
| no 30 s without a line | cheap |
| speaker not in `faces` at a readable size (F1); onset >= 0.25 s from a cut (T1) | the carrier brick |
| line <= 18 words; shot >= 1 s | captions and the frame grid depend on them |

| drop | why |
|---|---|
| `shot.cast` subset of `setup.cast` (strangers) | `frame` text is what the image model reads; a stranger in the text is drawn regardless; `cast` goes with it |
| `carrier == "none"` refuses a line | guards the writer against a choice the writer made in the same file; `carrier` goes with it — F1 needs only `faces` + `size` |

Not added (present in research, absent from the validator, and it should stay
absent until an episode is watched): wide <= 2 s and <= 2 per episode (rule
16 — ep01 has a 10 s wide), first payoff by 0:35 (rule 8), button type
rotation (rule 5), series cue in the first 10 s (rule 21).

## 4. The plan.json I would accept

```json
{
  "number": 1,
  "title": "A Study in Scarlet",
  "protagonist": "john_watson",
  "duration_s": 90.0,
  "setups": {
    "corridor": {"described": "A long stone corridor inside St Bartholomew's ...",
                 "cast": ["john_watson", "stamford"]}
  },
  "shots": [
    {"index": 0, "role": "hook", "t_start": 0.0, "t_end": 5.0, "setup": "corridor",
     "size": "close", "faces": [],
     "frame": "Close on Watson's gloved hand clenched white on the silver head of his walking stick ...",
     "motion": "Handheld, tracking beside the hand; the stick plants and lifts once; Stamford's head turns back."}
  ],
  "lines": [
    {"index": 0, "speaker": "stamford", "at": 0.6, "text": "You mustn't blame me if you don't get on with him."}
  ]
}
```

Fields dropped and what each was for:

| field | was for | why drop |
|---|---|---|
| `book`, `chapter` | provenance | read by no code; the folder is the provenance |
| `button_type`, `series_cue`, `next_hook` | rules 5, 21, 6 | none is checked (rotation needs ep N-1; cue-in-10 s is unchecked; next_hook is read by nothing) — writer's notes, not contract |
| `looks` | repeated in every take prompt | **disagrees with `refs.json`** in ep01 (Watson: "full brown moustache, herringbone tweed, gloves, silver ball" vs the sheet's "thin waxed moustache, fawn tweed overcoat, white cravat"); the panel IS the look; naming a different one is the measured way to make the model show it |
| `Setup.location_id` | — | read by nothing |
| `Setup.sound` | `overall_soundscape` | `trailer_assemble.extract` runs `-an`: the take's audio is generated by H3 and thrown away before the mix. The field costs audio-DiT compute and delivers nothing |
| `Setup.reaction` | "environment responds" | S; and "the heavy door swings on its hinge" named inside a hand close-up is exactly the named-element-gets-shown failure measured on T00 |
| `Shot.section` (11 values) | shape validator | collapse to `role` in {hook, setup, turn, button, null}: the four the validator reads; the other seven are the writer's method words |
| `Shot.continues` | FLF | FLF is off by measurement |
| `Shot.carrier` (8 values), `Shot.cast` | validator | see s3 — `faces` + `size` carry F1; the frame text carries who is in the picture |
| `Line.tags`, `Line.element` | rule 11, provenance | tags are never checked; element is read by nothing |

25 field kinds -> 15. Two of the dropped ones (`looks`, `reaction`) were
actively working against the panel.

## 5. The shortest take prompt H3 needs

What was measured on T00 (same panel, same seed, 2026-09-10): the SHORT
prompt — "motion + frame + register" — held the hand close-up; the full
official structure with a room paragraph pulled wide; the third, with a person
described, widened to show him. The fourth (today's, 2,267 chars, in
`shots/T00.prompt.txt`) is unmeasured. The measured winner is the floor. My
prompt:

```
{shot.frame} {shot.motion} Photoreal 1881 London, 35 mm film grain.
The camera keeps the first frame's distance, height and lens; nothing outside it is revealed.
Nobody speaks; mouths stay closed. One continuous shot, no text.
```

~300 characters (from 2,267). Frame + motion are the plan's two strings; the
last two sentences are the two rules measured or forced (the LOCK, which
"no zoom past the described framing" did not achieve; mouths closed, because
the line is laid later). Everything else in today's prompt is one of:

- the `<Picture 1>` alignment line and the `[Shot 1]` / `integrated_multimodal_description` /
  `overall_soundscape` / `non_diegetic_music` scaffolding — the API's keyframe
  grammar; whether the local i2v ComfyUI node (start frame as a latent, not a
  `<Picture>` slot) reads any of it is **unmeasured**;
- the STYLE paragraph, the FRAMING sentence ("eyes on the upper third"), the
  "environment responds" clause, the "final second comes to rest" clause, the
  soundscape (thrown away by `-an`) — each a named element, each unmeasured,
  and the measured rule is *every element the prompt names, the model shows*;
- `plan.looks` for `faces` shots — measured harmful in kind (the Stamford
  case) and contradicting `refs.json` in fact.

If the fourth prompt is rendered and holds, fine: then measure it AGAINST the
300-character one on the same seed, and keep the shorter if both hold. Until
then `episode_take_prompt.py` (135 LOC, 7 tests) is a module built on top of
its own counter-evidence. One f-string in `takes.py` replaces it.

## 6. Delete until measured (S)

1. **`episode_take_prompt.py`** — s5. The official structure was adopted from
   vendor guides (RunDiffusion, DomoAI, fal) for the API, not from a run here.
2. **Alternates** — `ALTERNATES`, `alternates()`, 10 files, 10.6 MB per
   episode, the `alternates` record. "What an editor asks for first" — no
   editor has, on any episode.
3. **The review page** (`storyboard.py --review`, `storyboard.html`,
   `storyboard/` stills, `still()`, `card()`, `page()`). Never produced. The
   actual review of T00 was `work/t00_strip.png`, made by hand. Make that the
   artifact: one png.
4. **Run cards** (`run_card`, `prompts`, `prompts.json`, `TNN.prompt.txt`).
   "Run on another H3 host" — there is no other host. The prompt is in
   `shots.json` already; today it is written in three places.
5. **FLF / CHAIN / `continues` / `end_image` / `workflow_for`** — measured
   wrong (morph). Delete, do not flag.
6. **The compositor lane** (~250 LOC of `frames.py`, 6 tests, `--masters`,
   `--frames`) — measured wrong (wardrobe swap). Delete; the skill's table
   records why.
7. **`Setup.sound` / `overall_soundscape`** — the audio is discarded at
   `extract -an`. Either the mix keeps take audio (then measure whether H3's
   diegetic sound is worth keeping under a bed) or the field is dead. Today
   it is dead.
8. **`Setup.reaction`**, **`plan.looks`** — s4.
9. **`HEAD`** and its cross-module test — measured 0.0; a constant that is
   zero and an assertion that two zeros are equal.
10. **Five agent files** — the four department agents contain, between them,
    six sentences of judgement ("look at every sheet: same room, same person,
    same clothes, mouth closed, hook close-up"; "read T00 before the round";
    "a line not heard on the master is a mix problem"). Six sentences in
    SKILL.md, one agent.
11. **Subskills 03-07** — they describe scripts that describe themselves.
    Keep 01 (+02 folded in): that is the LLM's job description.
12. **Cut detection at `scene > 0.1`** — keep the gate but mark it unmeasured:
    a cut between two takes of the SAME setup (S00->S01, S03->S04, both
    `continues`) may score under 0.1 and be reported missing when it is
    there. Measure on the first master before trusting a FAIL from it.

Not deleted, but worth saying: three `.log` files (two empty) and five
hand-made stills in `work/` are the trail of a human debugging, not the
pipeline's; they are the kind of thing an unattended agent should never
leave in `epNN/`.

## 7. What the cut costs

- The "official H3 structure" is gone; if a future H3 build honours it, it is
  one f-string away.
- Alternates are gone; a failed take means a new seed, then a redrawn panel
  (the skill's rule already), never an alternate.
- The html page is gone; the agent reads `takes/strip.png`.
- `looks`, `sound`, `reaction` are gone from the plan; the panel and the
  bed carry what they were for.
- Provenance (`element`, `tags`, `next_hook`) leaves the contract; the writer
  can keep it in `plan.notes.md` beside the plan if it wants it, where no
  validator has to carry it.

Nothing that was measured to work is removed. Two things measured to hurt
(`looks` naming a different coat; `reaction` naming a door in a hand
close-up) are.
