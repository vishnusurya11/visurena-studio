---
name: episode
description: "Turn one book chapter into a square (1:1) YouTube SHORT episode (delivered master <= 180 s, picture <= 174 s) at $0, entirely local: the book's narrator, a few spoken lines and the characters' own tales laid over pictures cut to the measured voice. Chain: plan (gated) -> per-episode looks (one hop from each base sheet) + place pictures (masters, states one edit of them) -> Qwen3-TTS lines -> timeline -> Qwen-Image storyboard grids cut into panels (two panel gates) -> MiniMax-H3 ref2va takes (take gate + content gate) -> assemble with bed and the pre-baked title card -> QC -> publish public. Use when writing, building, fixing, resuming or reviewing an episode under library/<book>/episodes/."
---

# Episode

**Where to run.** Every command below runs from the repo root,
`D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio`, on `master`. There is
one checkout. Never create a worktree, a per-book branch or a second copy of
the repo; the owner's rule (2026-09-24) is that everything lives in this one
folder, and everything book-specific lives under its `library/<book>/`.

One chapter is one episode, and it is a YouTube SHORT: 1:1 square and at most 3:00 DELIVERED (picture <= 174 s; assemble appends the ~4.5 s title card and the chip after it), $0, every step local. Both are the owner's hard requirements (2026-09-30): ep14 delivered 182.6 s and YouTube filed it as a regular video. The book's title cards are ALL baked before its first episode
(`uv run python scripts/episode/titles_batch.py <book>`; drive.py bakes
stragglers automatically, outside the episode's clock) -- an episode never
renders a card mid-run (owner design, 2026-09-30). The owner's
word outranks anything in this file; when he corrects the work, the correction
goes here and into memory.

**Read by the question you have (D17, 2026-10-19):**
- What runs next, what caps it, what stops it: "The chain" below (the generated algorithm) and
  GATES.md "Step caps" (the generated cap and clock tables).
- What may I do to a live run: "Operating a live run" below.
- Why a rule exists: `LESSONS.md` beside this file, an index of bricks (8 KB); open
  `LESSONS_ARCHIVE.md` only at the anchor the index names.
- What a gate measures, whether it is hard, its outcome at the cap: `GATES.md`.
- The measured detail behind a gate: `docs/calibration/*.md`. The other book's route:
  `SCARLET_ARCHIVE.md`.

**Deliverable first.** Every message that produces or changes an output begins
with the full absolute path of the finished file, on its own line. Keep every
master as `cut/master_iterN.mp4`, and never overwrite the only copy.

---

## THE RUN, ON ONE PAGE (ten-agent debate, 2026-09-27; docs/audit/2026-09-27_ep13_ten_agent_plan.md)

ep13 took 43 hours and 12 masters for about 5 hours of real work: code debugged on a
live episode, re-reads of unchanged pictures, retries on faults no retry cures, runs
nobody watched, and hand edits to pipeline state. Sherlock ep04-14 took 1 master each.
The rules below are what closes that gap. **The owner's standing order: no input from
him in production.** The chapter number and its cast are the only inputs.

**The series runs itself (decision 2026-10-06, `architecture/decisions/2026-10-06_autopilot_and_brain.md`).**
The scheduled task `visurena-autopilot` runs `scripts/episode/autopilot.py run --book <codex>`
at logon and every 5 minutes. Every 30 s it reads the disk, names ONE state (IDLE, RUNNING,
PUBLISHED, NEEDS_BRAIN, BRAIN_RUNNING, WAIT_TREE, PARKED, PAUSED, COMPLETE), takes ONE
action, and writes `library/<book>/autopilot/status.json` + `events.jsonl`. It launches
`drive.py` for the next chapter, retries what retries, cures through work orders, restarts a
hung ComfyUI, asks the brain (read-only triage, a JSON verdict) when a stop is not in its
table, and PARKS with a reason — a row in `parked.jsonl` and one Telegram — never a wait on
a person. Two consecutive parks pause the series. A commit on master makes the loop exit
and the scheduler restarts it on the new code; a dirty tree is WAIT_TREE.

**Your job is WATCH + REPORT, never a hand.** You do not launch `drive.py`. You do not run a
step script. You do not edit anything under `library/`. You read:

    uv run python scripts/episode/autopilot.py status --book <codex>
    library/<book>/autopilot/{status.json,events.jsonl,parked.jsonl}
    library/<book>/episodes/epNN/{drive.jsonl,drive_runNN.log,brain/attempt_NN.json}

and when a parked row names a CODE fault, you fix it the way the fixer does: the failing
test first, the fix, the suite, one commit by explicit path, then
`autopilot.py retry N --book <codex>` (and `resume` if the series paused). The owner's
optional acts are `pause`, `resume`, `retry N`, `park N --why`.

| step | stops on (HARD) | what the autopilot does |
|---|---|---|
| 02 plan | the battery; tier-1 rows after the climbs (3 writer rounds each, 2 climbs an episode) | a relaunch re-signs a stale flagged signature over the rows it carries (one critic read, no writer round); else relaunch, brain triage, PARK |
| 05 timeline | the MEASURED speech gap over 6.0 s | one bounded auto-trim; rendered → PARK |
| 07-08 board, panels | panel gates; EYE_PANELS climbs only on redraw-curable faults | the ladder; `redo 08` when takes wait on panels |
| 09 shoot | HARD take rows; EYE_TAKES climbs on hard faults | the batched ladder; a hung engine is killed and restarted, twice at most |
| 11 qc | any QC row, incl. the sound band | `redo 10` / `redo 09` by the row's kind, else PARK |
| 13 publish | the publish lock; the $0.10 reserve keeps the metadata call alive | upload, public flip, `uploads.jsonl` row → PUBLISHED, one Telegram with the URL |
| money | `$3.00` media wall (`guard_spend`) | `OverBudget` is a ladder terminal; a signed plan relaunches once past step 02, an unsigned one PARKs |

**The non-negotiables.**
1. **$0**, and no test spends.
2. **One writer per file.** Before the first rendered take, `plan.py` or the writer agent
   writes `plan.json`. After it, only the ladders do. Never hand-edit `plan.json`,
   `heads.json`, `stills.json`, graphs or take files, and never `touch` a timestamp.
   A plan.json the ladders edited carries `PATCHED_BY_HAND = True` in its plan.py.
3. **One launcher:** the autopilot (`scripts/episode/autopilot.py`, the scheduled task);
   `drive.py` is its child, never yours. No guard-stops, no scratch drivers, no bare step
   scripts mid-run. What the runner cannot do is a finding and a fix, then `retry N`.
4. **No code changes on a live episode.** Fix, test, commit (the loop restarts itself on
   the new code), then `autopilot.py retry N` once; a paused series needs `resume`.
   **Landing a fix during an episode (C3_verdict #7, 2026-10-11):** `autopilot.py pause
   --at-boundary --book <codex>`, wait for `paused_at_boundary` in the drive log (one unit:
   a take ~4 min, a grid ~5 min, a plan rung 4-10 min), commit, `resume`. Never kill a
   drive: 22 of 23 kills over ep19-27 were this, 527 waste-minutes. The full protocol is
   "Operating a live run" below.
   **A spent clock ships the episode flagged** (C3_verdict #5): read the audit sheet; never
   `retry` to buy hours -- a retry no longer resets the clock.
5. **A terminal is not a pass.** A judge-signed terminal on an `auto` gate auto-clears the lock
   and ships flagged (2026-10-01); a hand-waived or unsigned terminal never does. Never write
   `review/waiver.json` yourself.
6. **Watch and listen before anything leaves the machine**; the lock needs the sign-off.
7. **Audio first.** Picture cut to the measured voice. Effects duck under every line
   (6 dB), ambience 3 dB, every cue trimmed 3 dB (`studio/episode_sound`). Every effect
   lands on its MEASURED moment (`studio/sfx_onset`, 2026-10-17): footsteps one slice per
   heel strike, a single event on the take's motion peak near its planned time; a voice,
   crowd or weather keeps the planned time. Read `audio/sfx/onsets.json` for why each cue sits where it does.
8. **Shots follow the chapter** across scenes (G-ORDER). A flash-forward is omitted
   (`omit` in the plan), never slipped in to pass a gate.
9. **Deliverable first**; every `master_iterN.mp4` kept.
10. **When the owner says upload, it goes public.**

---

## RULE ONE — gate the plan before anything is made

Nothing is rendered until the plan passes both batteries. Each battery needs
inputs, so the order is fixed:

```
# ONCE PER BOOK, before ep01: refs/narrator.json (studio/book_narrator.py). A third-person
# book takes the dedicated `narrator` voice row (never a cast member); a first-person book
# declares its "I". Step 02 STOPS without one -- a gate never picks the narrator.
uv run python scripts/refs/cast_rows.py <book> <n> <who[=Display:gender]> ...  # FIRST: takes, grids and content checks read this one bound row
uv run python scripts/episode/step_02_plan.py <book> <n>          # the writer agent -> plan.json through plan_check; 3 rounds a climb, 2 climbs, then the PLAN signature
uv run python scripts/episode/downstream_replay.py <book> <n>     # ADVISORY after sign, $0: step 05 packed(), the hold cure, the dry take lint; a RULER row = fix the ruler
uv run python library/<book>/episodes/epNN/plan.py                 # OR a hand-authored plan beside its plan.json, only through episode_home.write_plan
uv run python scripts/episode/plan_check.py <book> <n>             # "VERDICT: clean"; CAST BOUND needs every sheet on disk
#   then sheets, places, lines, respot, timeline (steps 3-7)
uv run python scripts/episode/takes_r2v.py <book> <n> --from-refs --prompts   # needs placed.json, lines.json and every view; BEFORE any grid
```

Tag with `chapter=N` so the plan checks its fragments against its own
chapter's dossier row whatever is bound (without it, `tag()` reads refs.json).
A hand-authored plan lives under the library as `episodes/epNN/plan.py`; the
regenerate guard globs the library, and a plan whose plan.json was patched in
place declares `PATCHED_BY_HAND = True` in its own file.

`--prompts` builds every take prompt and runs the take lint over it for $0,
with no GPU. ep06 paid for three picture stages by skipping it. ep09 skipped
it too: seven take prompts were over length and four carried a banned prop,
and nobody knew until the takes stage (2026-09-22).

**The CELL GATES in `plan_check` read each shot against what its panel will
hold (2026-09-23), and each cost ep09 renders before it existed:**
- **G-ANCHOR:** no sideways truck on a medium-or-closer person who leans on,
  sits on, or stands at the set. H3 keeps the person and slides the scenery
  through them. The owner's "he walked with the fence ... ai slop" (ep09 T02).
  Push in, crane, or hold.
- **G-AIM:** every noun a move starts on or aims at must be in `at_rest`. A
  move toward what is not drawn invents it (ep09 shots 14, 15, 18: three
  retake rounds).
- **G-HAT:** a hat worn and held in one picture draws two hats. Tag the
  person without it and say "bareheaded".
- **G-PLACE:** a landmark the setup's words and picture lack is dropped or
  invented (ep09 shot 18's bridge on the lawn).
- **G-LAID:** a close on one person lying down says "above him looking down"
  or "on the ground level with his face". "Low over him" drew the landlord
  upright, and H3 turned the world round his face to lay him down (ep10 T18,
  passed by every gate).

`plan_check` exits 1 whenever it refuses anything. **An exit of 1 is a stop.**
It used to fail every WotW plan for another book's reasons, and people read
past it; that is fixed, so a refusal now means something.

---

## The chain

`<book>` is the codex id (the `library/<book>` folder name), `<n>` the episode
number. Every command refuses when the episode number is missing, and none of
them defaults to 1.

**The runner is the leader; this skill is the desk over it.** One command runs
the whole chain over one unit, skipping every step whose output exists and
stopping only on a hard refusal. The autopilot drives it through
`scripts/episode/drive.py` (above, never by hand); `episode.py` is what the driver runs:

    uv run python episode.py <book> <n>        # one episode
    uv run python episode.py <book>            # every episodes/epNN with a plan.json

Each step is also a command of its own, from the registry (`stages.yaml`,
stage `episode`); the table below is generated by
`scripts/episode/commands.py --write` and a test keeps it equal to the registry.
The references sheets and voices live in their own department: `uv run python refs.py <book>`.

<!-- registry:episode -->
| step | name | alone | what it does |
|---|---|---|---|
| 01 | bind | `uv run python scripts/episode/step_01_bind.py <book> <n>` | This unit's cast. |
| 02 | plan | `uv run python scripts/episode/step_02_plan.py <book> <n>` | The contract, gated before anything is voiced or drawn. |
| 03 | places | `uv run python scripts/episode/step_03_places.py <book> <n>` | This unit's character looks and place pictures (decision 2026-10-10): a look and a place state are ONE derivation of their base (the sheet, the place's master) on refs/looks.json and refs/places.json; a recurring place's view is its master or derived from it, never a fresh room from words. |
| 04 | record | `uv run python scripts/episode/step_04_record.py <book> <n>` | Every line in its character's voice, MEASURED and LISTENED to. |
| 05 | timeline | `uv run python scripts/episode/step_05_timeline.py <book> <n>` | AUDIO FIRST - the animatic. |
| 06 | prompts | `uv run python scripts/episode/step_06_prompts.py <book> <n>` | Every take prompt built and linted for $0 with no GPU, BEFORE any grid: length per block, style line, banned props, no last frame, no fragments. |
| 07 | board | `uv run python scripts/episode/step_07_board.py <book> <n>` | Storyboard grids on the local image model from the plan's prose, up to three references - cast sheets first, the setup's place last. |
| 08 | panels | `uv run python scripts/episode/step_08_panels.py <book> <n>` | One panel per shot, two machine gates, then `judge:panel_eye`. |
| 09 | shoot | `uv run python scripts/episode/step_09_shoot.py <book> <n>` | The slow step. |
| 10 | edit | `uv run python scripts/episode/step_10_edit.py <book> <n>` | Title card, measured bed, cut, mix, the master upscaled once: hqdn3d per shot + realesr-animevideov3 4x (`av3`, 2026-10-18). |
| 11 | qc | `uv run python scripts/episode/step_11_qc.py <book> <n>` | Measure the DELIVERED master, never the intention. |
| 12 | deliver | `uv run python scripts/episode/step_12_deliver.py <book> <n>` | manifest.json beside the master (every gate verdict, every rung, timing totals), the deliverable's full path printed first, notify() through the platform. |
| 13 | publish | `uv run python scripts/episode/step_13_publish.py <book> <n>` | The last mile, unattended (decision 2026-10-05, under the standing hand of 2026-10-01): youtube.json from one guarded structured call, the director's sign-off rendered from measures only, the gated upload, the public flip, the /shorts/ poll -- the public Short URL is the last line printed. |
<!-- /registry:episode -->

**The algorithm** (generated from `stages.yaml` steps and `caps:` by the same command; a test
holds it equal; the caps' meanings are GATES.md "Step caps"):

<!-- registry:algorithm -->
```
RUN(book, n): the autopilot launches drive.py; you read the disk, never call a step
  clock    = the union of the episode's run spans, never reset (GATES clock table)
  counters = attempts.json, per episode: a relaunch, a resume or a retry never resets one
  FOR each step in order, skipping a step whose outputs are current:
    log 'STEP <id> start'; run its ladder; a round is a change of bytes
    pass -> next | cap -> 'CAP <phase>: ...', keep best, sign flagged, next
    ruler fault -> park; fix the gate test-first; retry N | SAFETY -> park by its name
01 bind      caps: bind 1/pass, 2 min
02 plan      caps: plan 3/climb x2, 30 min, gate PLAN
03 places    caps: places 3/draw, 15 min
04 record    caps: lines 1/episode, 10 min; voice 2/episode, 30 min
05 timeline  caps: timeline 1/pass, 2 min
06 prompts   caps: prompts 1/pass, 2 min
07 board     caps: grids 1/grid, 30 min
08 panels    caps: panel_checks 1/round, 30 min; regrid 2/episode, 20 min, gate EYE_PANELS
09 shoot     caps: takes 1/pass, 120 min; take_dq 1/round, 30 min; take_content 1/round, 20 min; take_eye 1/round, 10 min; strip 1/round, 2 min; retakes 2/episode, 45 min, gate EYE_TAKES; face_refine 1/take, 15 min
10 edit      caps: assemble 1/pass, 15 min; upscale 1/pass, 15 min
11 qc        caps: qc 1/episode, 30 min; master_eye 1/episode, 30 min, gate MASTER
12 deliver   caps: deliver 1/pass, 2 min
13 publish   caps: publish 1/pass, 10 min
```
<!-- /registry:algorithm -->

No step parks on a person (decision `2026-09-24-automate-the-taste-gates`).
Each taste gate is signed by a judge named in `gates.yaml`: LOOK by `judge:look`
(`refs/verdict.json`), PLAN by `judge:plan` (`episodes/epNN/plan.verdict.json`),
the EYE on panels and takes by `judge:panel_eye` / `judge:take_eye`
(`eye_<sha8>.json`), MASTER by `judge:master_eye` (`review/eye_<sha8>.json`). A
judge signs `pass` or `flagged`, never a fault, never a waiver; a terminal rung
writes an audit row. The owner reads `library/<book>/audit/<unit>.html` when he
likes; a finding goes through `scripts/audit/note.py` into the casebook, and the
bench (`scripts/calibration/bench.py`) is what changes a judge. The `sign_*.py`
scripts remain for a person who chooses to write a verdict; they are not a step.
See GATES.md "Judges".

### The tools each step wraps

The first column is the registry step the tool belongs to.

| step | tool | command | its gate |
|---|---|---|---|
| 01 | Bind this chapter's cast | `uv run python scripts/refs/cast_rows.py <book> <n> <who[=Display:gender]> ...` | stamps `refs.json` with the chapter; must precede the plan; the take, grid and content steps all read this one row |
| 02 | Plan | a new unit's plan is written by the `episode_writer` agent (step 02) into `library/<book>/episodes/epNN/plan.json`; an existing hand-authored `library/<book>/episodes/epNN/plan.py` regenerates it when run | RULE ONE above |
| 03 | Sheets and prop sheets | `uv run python scripts/refs/build_pack.py <book> --kind characters --only <a> --only <b>` (repeat the flag; `--kind props` for a key prop) | look at every sheet beside its row; words must match the picture (LESSONS: cast) |
| 03 | Looks (step 03_04) | once per book `uv run python scripts/refs/looks_table.py <book>` (refs/looks.json); per episode `uv run python scripts/refs/looks.py <book> <n> [--draw]` | LOOK-STATE (`judge:look_state`): hat, hair colour, facial hair HARD on every new look picture; G-LOOK in the plan battery; the step-06 lint refuses a person whose picture and words name two looks |
| 03 | Places at this episode's hour | `uv run python scripts/refs/places.py <book> <n> [--draw] [--new=<loc>="Its name"]` | every setup's `location`+`view` resolves to a drawn picture (guard test); a first picture is the location's master (refs/places.json); a `place_state` is ONE 2511 edit of it (03_05); G-PLACE in the plan battery; look at each one |
| 04 | Voices (new speakers only) | `uv run python scripts/cast/cast_voices.py <codex> --only <a>,<b> [--recast]` | pairwise similarity under the wall; at most 4 voices an episode |
| 04 | Lines | `uv run python scripts/episode/say_lines.py <book> <n> [--redo=i,j]` | every line heard as written (listen gate) |
| 05 | Timeline | `uv run python scripts/episode/respot.py <book> <n>` then `uv run python scripts/episode/timeline.py <book> <n>` | fingerprinted to the plan AND the measured voice; every reader refuses a stale one |
| 07 | Grids | `uv run python scripts/episode/grids.py <book> <n> <setup> <cols> <rows> [tag] [--shots=..]` | shot count = cols x rows; the manifest records `inputs` (the exact prompt and every staged picture's bytes) and the prompt version (v2 default) |
| 08 | Panels | `uv run python scripts/episode/panels.py <book> <n>` | a grid is stale when its prompt or a staged picture would now differ (a rebound row, a redrawn sheet or place, a builder fix); every shot from exactly one grid; a panel is cropped square and written only if its pixels changed, so re-running is safe |
| 08 | Panel gates + EYE | `uv run python scripts/episode/panel_check.py <book> <n>` and `uv run python scripts/episode/panel_content_check.py <book> <n>`, then a contact sheet of all panels, looked at | both must exit 0; `takes_r2v` refuses without both verdicts. Both gates have passed one man with two hats, a white gutter and an insert that was the place reference copied back |
| 09 | Takes | `uv run python scripts/episode/takes_r2v.py <book> <n> --from-refs --approved=render` | the take lint; a take is current only to its words AND its pictures |
| 09 | Take gates + EYE | `uv run python scripts/episode/take_dq.py <book> <n> [idx...] [--attempts]` and `uv run python scripts/episode/take_content_check.py <book> <n>`, then a 5-frame strip of every take, looked at | QC and the upload refuse an unjudged take. `held` fails a person pinned while the set slides; `jump` fails a switch of picture |
| 10 | Title card | `uv run python scripts/episode/series_title.py <book> <n>` | QC fails a master without one |
| 10 | Cut | `uv run python scripts/episode/assemble.py <book> <n> --engine=r2v` | kept as `cut/master_iterN.mp4` |
| 11 | QC | `uv run python scripts/episode/qc.py <book> <n> --engine=r2v` | must say PASS; a silent gap names the shot it is made of |
| 13 | Publish (only when the owner asks; no `publish/standing.json` = step 13 parks, 2026-10-12) | write `episodes/epNN/youtube.json`; `youtube_upload.py <book> <n> --engine=r2v --dry-run`, then `--approved`; then `uv run python scripts/publish/youtube_privacy.py <book> <n> public --approved` | the upload refuses failed or unjudged takes; the flip to public re-checks QC (about the uploaded sha8) and every take, as they stand then |

The publish row inserts the video private, because an unverified API project forces
that on `videos.insert`, and then flips it public. **When the owner says
upload, it goes public.** He corrected the work for making it private once.

---

## Writing the plan

The plan is the contract (`studio/episode_spec.py`). Before the first rendered
take, the plan `.py` (or the writer agent) is the source of `plan.json`. From the
first rendered take on, only the ladders write it: re-running the plan `.py` then
erases their cures (ep13 finding 49), so its plan.py declares
`PATCHED_BY_HAND = True`. **Never patch `plan.json` by hand.** ep01, ep03 and ep04
were patched that way; a strict guard names them.

**The story.** One chapter, one brick: a QUESTION, a TURN (the lead's choice,
50-75% of the way in), an ANSWER, and a BUTTON (the last line, never the
lead's). The turn is people acting on each other, so name both of them in one
motion clause.

**The viewer (2026-10-13, Jekyll ep01).** A plan that obeys every instrument
and bores a person is refused:
- the first shot and line carry the chapter's threat, never a portrait of
  habits (G-HOOK; a `nonscene` row may be folded away);
- the chapter's key event is a SHOT of the act itself (G-SPIKE), and every
  shot carries a story action -- weather is not story (G-ACTION, at most 2
  empty weather shots);
- a character who tells a story in the chapter tells it himself: `kind:
  "tale"`, his voice, the book's words, over pictures of what he tells;
- at most 310 words and at least 15 s of beats and codas (G-PACE); over budget
  a line is cut, never a breath;
- a dialogue shot is held locked or over the shoulder, the actor carries the
  verb; at most one spoken line's camera travels (G-TALK);
- what the chapter withholds stays withheld.

**The anime-TV grammar (owner 2026-10-17, "Go ahead with changes").** Every new plan is
written under it: `grammar: anime_tv` is set by code from the brief's band, and the
battery's GRAMMAR row is HARD on it until something is drawn (decision
`architecture/decisions/2026-10-17_anime_tv_grammar.md`). The frame holds a face large
enough to read and a CUT changes the size: faces at close / medium close on 55 % of the
shots, few and short wides, mostly locked, a silent face after every exchange, a cold open,
one act_out, at most 28 shots, every shot its own take. Every wall with its number and its
replay is the GATES.md grammar table (one home, so the two cannot drift).
A face that MATTERS (a line by someone in the shot, or a reaction) is planned medium or closer:
a wide draws it about 28 px and a full 67 on the 768 take, under the 96 px an eye needs, so the
plan ladder steps such a wide or full one size closer for free and lists every faced shot still
under the floor as a face-refine candidate (G-FACE-FLOOR, advisory; GATES.md).
A scratch re-plan is judged beside the live one: `plan_check.py <book> <n> --plan=plan_v3.json`.
The title card stays at the END of the Short (the G2 bumper was not adopted).

**The voice.** Every narration line is the book's narrator's
(`refs/narrator.json`, else the narrator the book's published episodes share).
The projection rate is the book's measured voice, else the studio's 2.45
words/s -- never 3.0.

**The cast.**
- Name people with `cast_refs.tag(BOOK, who, "the narrator", [fragments], chapter=N)`.
  Pass the plan's own chapter: refs.json holds ONE chapter, so without it an
  earlier plan cannot regenerate once the next chapter is bound. The tag is
  closed in parentheses, so the plan's next verb cannot run on.
  The fragments are verbatim words from the bound row, face first and then
  silhouette.
- It refuses any fragment the row does not say, so a plan can no longer
  contradict its cast.
- Never type a description, and never inline the whole row. The take prompt
  already defines every staged person in full.

**Who is in a shot.**
- `faces` are the people whose faces must read -- and on a wide or full shot,
  every cast member the picture holds, however small (owner 2026-10-14).
- A setup's `crowd` declares a crowd.
- Every other unnamed person is counted in the shot's `extras`.
- No gate guesses people from the prose any more, so the plan must say.

**Nobody appears from nowhere (G-PRESENT, owner 2026-10-14, Jekyll ep01 HEL).**
A scene is a run of consecutive shots on one setup. Whoever is in the picture
anywhere in a scene is in its FIRST shot's picture (in `faces`, or named in its
frame/at_rest -- an over-the-shoulder holds the shoulder's owner), unless a
shot marks his arrival in `enters` and its motion shows it ("runs in down the
cross street"). `exits` marks a leaving the same way. Open a peopled scene on a
picture that shows its people: never an empty-set wide, a single, or an insert
when a second person is about to be seen. A later wide that leaves a present
person out is advised (G-PRESENT-WIDE). Grids and takes stage the sheet of
everyone a picture holds, at every size; over the ceiling the closest readable
faces win (`scene_cast.pick`), the rest are drawn from their wardrobe words.

**Places.**
- A setup names its `location` and the `view` it uses: the picture of that
  place drawn at THIS episode's hour. The hour comes from the picture, never
  from the words.
- One picture per place per episode, chosen by the setup. A shot never picks
  its own view.
- Never rewrite the book's location rows to point at your picture; that moved
  every earlier episode's Horsell Common into ep09's daylight.

**Cells.**
- A setup's `geometry` lays out its establishing WIDE.
- Every tighter shot (medium, medium close, close, insert) carries its own
  cells: where ITS subject sits and one or two things behind it (G-SCALE,
  hard).
- Write cells from the drawn picture, after it exists, never before.

**Words the models cannot read:**
- negations ("no", "nothing", "without");
- "slow" (name an amount);
- dialect spellings ("cook yer" defeated the listen gate twice);
- more than 18 words a line;
- more than 4 voices;
- dialogue outside the chapter's band (5-20 %, the ceiling up to the chapter's speech + 8
  points and never past 35 %; a `tale` or an `inner` line is outside it);
- more than 310 words, or under 15 s of beats and codas.

`plan_check` refuses each of these.

---

## Pictures

**The book's look and atmosphere (2026-10-13).** `refs/look.json` declares the look (`photoreal`, or a drawn look such as `anime_gothic` with its own `lead` and optional `take` words) and an `atmosphere` ("fog, damp haze"): the grid line, the grid negative, the panel's name in the take prompt and the H3 style line all read it. The house (no look.json) is unchanged byte for byte. The atmosphere fills the air OUTDOORS only (2026-10-13): a setup that is not `outdoors` and whose `described` names a room (study, parlour, cabinet, fireplace, room, hall ...; `book_look.under_sky`) gets the grid line and the H3 line without it.

**Sheets and looks.** One sheet per character LOOK on the book's look table,
`refs/looks.json` (owner 2026-10-10: reverses 09-18 for story-time looks): the
base sheet, and every later look ONE hop from it -- an identity edit for
clothes, a fresh draw from the base prompt and seed for a face change -- never
an edit of an edit, never a composite. One master per place side
(`refs/places.json`); a state of a place is ONE edit of its master; a view of a
recurring place is its master or derived from it, never a fresh room from
words. One sheet per key prop. Closer sizes come from the take's camera.
**The closed marker writes the drawn facial-hair phrase** (`looks.drawn_face`,
2026-10-11): under a `beard` marker a duration beard ("sixteen days of grey-brown
beard", drawn 0/3) is drawn as "a full short grey-brown beard covering the jaw, chin
and upper lip, sixteen days grown"; a styled beard and `stubble` keep the book's words.
**A row with no dossier, or a silent dossier head, takes its head from the bound row's
`physical`** (C2_verdict #6, `look_timeline.body_layer`): hair and face only, never the
hat (a row's physical carries one chapter's costume); a row with no dossier is one look
per refs.json card (`looks_from_cards`).

**Every refs picture is drawn in the BOOK's look** (2026-10-12): `library/<book>/refs/look.json`
declares it once by the owner's ruling (`studio/book_look.py`); the base sheet, a fresh look,
a place master and the title plates read it. A photoreal book draws on Krea2 turbo with no
LoRA, led by its declared words; no declaration is the house look. A DRAWN look (2026-10-13,
anime) files its own drawer under `refs` in look.json -- `workflow`
(`image_sdxl_t2i_2lora_hires_visurena`), `ckpt`, `loras`, a tag `lead`, a `negative`, `frames`
per kind (characters / locations) and `entities` (a person's own tags and negative, keyed by id;
a place's by `<location>/<view>`): a person's base sheet is ONE front figure at 832x1216 (NoobAI
turnarounds came back as 8 copies), drawn from his tags, else from the look table's words with the
sheet form cut; `sheet_front` takes a portrait sheet whole; a place is 1216x832 with no plan LOOK
sentence. A drawn look with no `refs` keeps the house drawer. Tags, not prose, for NoobAI: "side-whiskers"
drew cat whiskers, `mutton chops` did not. A character with no
`design.sheet_prompt` gets its base sheet from the look table (`build_pack.table_job`). A
dossier sentence dated to a chapter ("By chapter 6, ... balder") is a state, never the base
head (`head_author.dated`). Describe a place by its LAYOUT, never its absences: "no window"
drew windows on Jekyll's door, "a flat blank plaster upper storey filling the frame" did not.

**Look at every picture you draw** before anything is built on it. Put the
defining state or detail FIRST in its prompt. A detail buried mid-sentence is
dropped:
- the lawn was drawn with no fire;
- Snippy was drawn clean-shaven when every text gave him a moustache.

When the words and the picture disagree and the book is silent, make the words
match the picture. A look on `refs/looks.json` means the book is NOT silent:
change the picture (stage the look), never the words.

**Grids.** Qwen-Image-2.1 edit-multi takes 1-3 references:
- cast sheets first, the identity slots;
- the setup's own place picture, the scene slot; on a chained grid the ROOM
  last (the style slot): the setup's first-drawn panel, `storyboard/anchors/<setup>.png`,
  named "this exact room, already drawn" — the plate stays beside it only when
  the grid holds a wide or a full;
- only the cast of the shots a grid OWNS, since a borrowed cast draws line-ups;
- an unused LoadImage slot feeds the encoder ComfyUI's example doll, so
  `stage_only` removes it.

**One room per setup (2026-09-28, owner: "fix all that").** A place is held by
pixels, not words: within one render the room holds, between renders of one
setup the drawer re-dresses it (ep14: two biology classrooms, a mirrored
Waterloo, an attic that became a street). So the grid holding the setup's
widest shot is its ANCHOR and is drawn first; its widest cell is cut to the
room; every sibling grid stages the room; the `inputs` hash covers the staged
bytes, so a redrawn anchor re-cuts the room; the re-cut is compared to the old
room first (`grid_room.recut_room`, 2026-10-19): a matching place keeps the old
room bytes and the siblings stay valid, a moved place stales them and the ladder
redraws them on it. Under a declared atmosphere every figure is drawn solid,
the haze behind it (`book_look.ATMOSPHERE_GRID`; ep01 shot 2 faded into fog). The prompt says the location "is identical in every panel and never
changes" again, carries the setup's `geometry` and `landmark`, and a tight grid
gets the place's first clause plus `Setup.light`. `panel_place` reads every
loose panel against the room and names its mirror — advisory until calibrated
(`docs/calibration/panel_place.md`). G-SETUP holds a setup to 50 s of picture.
panel_dq records face_h against the planned size (G-FRAME, advisory, 2026-10-11): a
tight size is drawn a size wide (MCU median 0.208 against ~0.30 asked).

The layout is ruled by `grid_layout` (by setup and shot size): **a grid is 1 or 4
cells, never 2 or 3** -- a strip canvas comes back as Qwen's own grid count, seamed
(2026-10-11). A close is bound by
the items above the chest only (9cb4609: six ep13 closes drew whole seated figures
when bound to trousers and socks).

**Lay a grid out by shot size**: wides with wides, faces with faces. A mixed
2x2 drew a medium close as a full figure; head counts are a lottery across
cells, and a 1x1 holds its count where a 2x2 does not (ep09 shot 18: 8-14
riders in every 2x2 seed, the declared count in every 1x1).

**Declare `extras` from the book's own count, never a guess.** ep09's "a bevy
of hussars ... two of them dismounted" was declared 6; the take drew six
riders and the two on foot, and the content gate held it to the guess.

**A person with a hat in his hand is "bareheaded"** in that panel's words;
that word is what drops headwear from the binding (G-HAT refuses the clash).
In a CAST ROW or tag never write "Bareheaded"/"Bare head": the drawer reads it
as a bald scalp (ep10 narrator and landlord). Write "Hatless, <his hair>".

**Panels.** `panels.py` cuts each shot from its grid, sheds the gutter it
measures (at the edge up to 48 px, or a thin run within 120 px when the model
drew the panel narrower than its cell), crops square, and writes
`storyboard/h3/shot_NN.png` at 768 for the take. To redraw a grid, move the
old grid's png/json/txt to `storyboard/superseded/` first: a shot in two
grids is refused, and `--seed-bump` without a tag writes over the only copy.

**Look at a contact sheet of every panel before any take.** On ep09 both
gates passed a white gutter, two hats on one man, and an insert that was the
place picture handed back.

---

## Takes

**The take model follows the planned size (2026-10-18, main session on measured evidence).**
A take whose every segment is close / medium_close / medium / insert renders on Wuli 8-step HQ
int8 + Spark-H3 attention (`takes_r2v.WULI_BASE`: sharper faces, the owner's V4 pick); a take
with any wide or full segment, or a card with no sizes, renders on the Singularity fine-tune
with the turbo LoRA x2 (1.0/0.7) and Spark attention (`SPARK_BASE`): Wuli's line work boils on a
small face (G-WARP S 4.13 / Se 7.22 on the Kawajiri W wide, against 2.65 / 3.12 on Spark).
The run queues each model's takes together (`by_model`), so each loads once. Rollback:
`ROLLBACK_BASE` (the CK 8-step) for every take. `TAKE_WIDE_DETAIL=1` (OFF; face-blur fix #4,
2026-10-19) sends wide/full takes to `WIDE_DETAIL_BASE`: Spark at 15 steps, second LoRA 0.4,
about +3 min an episode on ep01's four wides; it stays off until bench arm A3 (T01, T06) shows
eye sharpness up and flicker not. **H3 obeys direction, not amount.** It follows the cell and the
camera verb; amounts, angles and negations are ignored.

**Camera.**
- Point every move at something the cell already holds (G-AIM).
- Never truck sideways across a person anchored to the set (G-ANCHOR). A
  walker the camera tracks WITH is fine: say "with him" / "keeping him".
- The take prompt carries the camera's direction only; the builder drops the
  travel amount. A legacy plan kept amounts for G-MOVE; a grammar plan writes none
  (G-PUSH refuses one; the repair round strips it for $0).
- Use at least 8 moves an episode, drawn from `docs/calibration/camera_catalog.md`.

**Look at a 5-frame strip of every take before the cut.** Watch for a person
or prop sliding against the set, a picture that changes into another, and a
first second that is not the panel. The gates passed ep09 T02 at 92.6 before
`held` existed.

**When a take fails, match the cure to the cause:**

| symptom | cure |
|---|---|
| a moving take froze | re-roll the seed |
| a still take froze | change the move TYPE, not its amount |
| a take froze after its OWN length changed | put the length back; a fresh seed is not the cure (ep08 T16: 51%, then 75%, then 10% frozen once restored) |
| lip-sync lags (HARD mux lag) | the edit lays the line where the take's soundtrack put it (`studio/line_laid`); an advisory lag or rotation is points off, never a rung (ep13: five lag rounds, 157 min, none cured) |
| a hard cut appears early | the take opened on another staged picture, or on the place its prompt names three times |
| the same fault on a fresh seed | the PLAN: re-aim the move at what the cell holds (ep09 shots 14, 15, 18 repeated on new seeds) |
| a person pinned while the set slides | the plan: push in or crane instead of the truck (G-ANCHOR) |

**The GPU never waits on a check (owner, 2026-10-14).** Step 09 runs the renders and the CPU
checks side by side (`studio/take_overlap.py`): never run `take_dq` by hand while a render is
running unless it is `--cpu-only` (a ComfyUI job between renders evicts the video weights), and
never wait for the checks before queueing a render. A take the dq rows alone condemn (frozen,
held, camera-move, gait) is retaken in the round that the first renders' tail runs into.
`scripts/episode/take_schedule_replay.py <book> <n>` projects any episode's step 09 both ways.

Retakes run in ONE batched round per ladder rung (the early round is round 1, the eye's is round 2):
`takes_r2v.py <book> <n> --from-refs --approved=render --retake=a,b --why="<gate row or finding>"`.
`--why` is required; a round of one take is refused unless `--last` declares
it the last round for this master. The failed take is kept as
`attempts/T<NN>_failN.mp4`. Judge with `take_dq.py <book> <n> a b --attempts`
so the better attempt is kept. After `panels.py` rewrites a panel, re-run both
panel gates: the takes refuse a verdict older than its panel.

**Every dialogue take passes the TAIL gate** (G-TAIL, 2026-10-11, `take_dq` row `tail`):
a mouth that keeps speaking into the guide's silent tail -- a tail louder than -45 dB
with words after the line, or an open, working mouth -- fails. The cure is a SHORTER TAKE:
the shot's beat and coda halved (`take_ladder.shorten`, measured against the length the
take was built for, `built_for`), then one reseed, then keep_best flagged. The line itself
is never cut: the voice is the ruler. Jekyll ep01 v2 T14 failed WER 0.56 + tail on four
same-length reseeds and passed both (WER 0.11, tail -48 dB) on its first shorter take
(coda 1.5 -> 0.75 s).

**Soft faces are refined (09_07, owner 2026-10-17: "I like face improvements a lot in wide shots, go ahead";
widened 2026-10-19: "why our fix skipped those shots? fix that").** Every take with a planned face (never an insert)
whose dq lets it ship (no hard row outside warp/gait/pulse/frozen-whole/lip-sync/lag, no warp seed retake owed) is
tracked: `face_yolov8m.pt` every 3rd frame in a worker under the embedded python (`studio/face_detect.py`, GPU when
idle, CPU while rendering, MTCNN if the worker fails), tracks cut at hard cuts, the crop centre median-smoothed over 21
frames and its size over 51 (ComfyUI-H3-FaceRefine's ideas, ported). Each track whose smallest face (running median) is
under 120 px is matched to the take's staged cast (facenet + the Lab colour of head and hat + the plan's
"at the LEFT/CENTRE/RIGHT"), and its crop re-rendered through H3 with ONLY that person's sheet at a denoise that follows
the face: 0.45 at 60 px, +0.05 per halving, inside 0.40-0.55 (`fr.denoise_for`; F2's workflow, never edited). The plan
size is not read, nor face-at-end. The gate keeps a crop only when identity to the sheet does not drop, there is no seam
or new flicker, and the face count holds; else the unrefined take. Decisions per take: `takes/r2v/refine.json`
(`refined`, `unrefined`, `none_found`, `all_readable`, `no_cast`, `cut`; a `no_faces` row of the old 60 px wall is
owed a new look, its jobless round refunded). Step 09 queues the refine on the
GPU lane right behind the renders (a REFINE job: after renders and retakes, before the GPU checks) and refines what
the ladder left owed once at the end. ~110 s per face per take (ep01: 11 takes, 1,512 s priced); the FIRST thing cut
for time, never a check. A take whose every planned face the warp gate tracked >= 80 % of it at >= 120 px AT ITS
SMALLEST (each track's `min_px`, never its median: a push-in reads big there) is declined before tracking; a record
with medians only goes to the tracker. Priced per face not already readable (`fr.soft_faces`); `none_found` / `all_readable` spend no round. Assemble pastes the kept crops at CUT scale on the
decoded frames, before the denoise and the one upscale (owner 2026-10-18, 24caaeb); after the upscale only audio is
muxed. On `av3` (the default) the pass runs in the portable python's worker (`studio/master_av3.py`),
which rebuilds the paste from its spans: the same geometry, the same frame loop. By hand: `uv run python scripts/episode/face_refine.py <book> <n> [take ...]`.
The render is the SaveVideo node's output, by node id (`fr.saved_node`), never the job's first output: on ComfyUI
v0.41.2 the LoadVideo echoes its input crop first, and a refined crop equal to its source is refused (2026-10-18).

**G-WARP is HARD on S only (2026-10-19, retro D1-D2, for owner veto).** `take_dq` scores every take that stages a
face for frame-to-frame face redraw (`studio/warp_gate.py`, CPU lane). FAIL is S > 2.5: one seed retake, then F2 for a
face tracked under 60 px, else the take ships kept-best and flagged. An Se-only score is the advisory `eye` (all 8 ep01
hard fails were Se-only; seeds cured 0 of 4). A WARN goes to F2 only for a small face (face_w < 0.10) or S_held > 1.5.
The wall has no owner labels: `scripts/episode/warp_labels.py` takes person-signed labels only and re-arms hard Se at
>= 80 % precision. A `warp_gate.py` edit re-measures every take: land it between episodes.

**A round is a change of bytes (2026-10-19).** A retake rung that renders, trims or cuts a head spends a round; one that
does none of them prints `NO ROUND` and ends the climb. An unaffordable batch is trimmed to the takes the budget affords,
worst first. A gait shuffle is cured by the plan's verb (`gait_verb`), never a seed; a cure under 20 % over 4+ tries is
dropped for its class (`take_ladder.CURE_RATES`).

**Never pin a last frame.** ref2v gives a take its first frame only.

**A kept take is current to its inputs (G-TAKE-INPUTS, 2026-10-15).** After `take_dq --attempts`,
step 09 prints each kept take's staged sheet and panel names and STOPS on any name that is not the
current card's (a `superseded/` hash, a redrawn panel); the ranker never keeps an attempt made from
older pictures over a current one, and assemble and QC refuse a master holding one. After a sheet,
place or panel redraw, every take that stages it is re-rendered. A master report quotes QC's
"inputs: all N takes current".

**The prompt is linted before the GPU (2026-10-15).** `takes_r2v.py --prompts` and every render run
the PROMPT LINT (GATES.md); a refusal is a builder or plan fix, never a re-roll. A plan epithet ("the
lawyer") binds to its staged `<Subject k>`; a person is described once, in `subject_definitions`.
Over-the-shoulder: a camera "behind his RIGHT side" puts his shoulder at the LEFT edge. A hand insert
names no hat or coat.

---

## Before anything leaves the machine (2026-09-26)

Episode 12 was published because the runner finished and QC was green. Every
taste gate had ended in a terminal, the plan stopped at paragraph 57 of 69, the
mix had no sound effects and the shouts were flat. Nobody watched it. So, for
every episode, before `youtube_upload.py`:

1. Read `learnings.jsonl`: any gate whose last row is a terminal is OPEN. A
   judge-signed terminal ships flagged and the owner reads it in
   `audit/<unit>.html` when he likes; nothing waits on him. Fix what a code fault
   left open; never write `review/waiver.json` yourself.
2. Watch the master FULL SIZE and LISTEN to it, start to end. Read every take
   strip. Check the plan's last span against the chapter's last paragraph.
3. Write `review/director_signoff.md` (Watched / Take strips / Coverage / Flags)
   naming the cut's sha8. The lock refuses without it.
4. A run the owner calls a test stays local or private until he says public.

## When the book is done: the book video (owner, 2026-10-11)

When the last chapter is public, run
`uv run python scripts/publish/book_compilation.py <codex> --upload [--replaces=<old id>]`. It:
1. cuts every shipped Short into its two videos, title and main, by MEASURING the card (the last cut before the
   closing black), conformed to the book's square, into `compilation/chapters/`;
2. makes the book's main title once (`scripts/episode/book_title.py`, under `title/book/`): 7 s in a 2.39 band, a
   cold open from the book's own faceless wides, black on the sting's hit, PRESENTS, Krea2 key art on H3, the
   title SET BY CODE in Bebas Neue. No model ever draws a letter in it. G-BOOKTITLE refuses on frames, LUFS,
   contrast and stream equality, and flags on the read-back;
3. joins main title + (title, main) per chapter by stream copy, stamps shifted by the title (never a 7 s chapter:
   YouTube drops all chapters if one is under 10 s);
4. uploads it public, sets the 16:9 thumbnail (a 403 is recorded, never fatal), and makes `--replaces` private.
Look at `title/book/main_title.mp4` and `thumbnail.jpg` before the upload. The run
holds `compilation/.lock`, prints a line per chapter, renders the title's GPU half while
the CPU cuts, and stops at THE DOOR (`compilation/door.json` + `door_sheet.png`) on a
title piece longer than its card, a wrong order or a refused G-BOOKTITLE. Every picture
follows the BOOK's look (photoreal = Krea2, no LoRA, its own refs words).

## Cut and QC

**G-DEAD (2026-10-13; owner option A 2026-10-18).** Step 10 never builds a master with a still held past 2.5 s, a frozen take, a failed take the ladder never settled, or two such shots in a row. It first cuts what it can for free (the dead shot out, live non-dialogue neighbours slowed <= 1.5x to cover it; `takes/work/dead_cuts.json`). A take the ladder settled keep_best or high at the cap (`fault.evidence.settled`) is ADMITTED, ships flagged, and is listed with its seconds in the master in `takes/work/flagged_takes.json` (the audit sheet and the sign-off show it); frozen rows stay dead. A dialogue take is never cut or slowed.

**Audio first, always.** The picture is cut to the measured voice. Every line
sits at its shot's start plus the handle, and `episode_timeline.misaligned()`
refuses anything else.

**Silent gaps.** QC walls the longest silence at 6.0 s and names the shot the
gap is made of. If a silent shot lies inside the gap, give it a line or move
the silence to a short shot with lines on both sides. Trim a coda last, and
never a moving shot's coda.

---

## Step caps (owner, 2026-10-18; table in GATES.md "Step caps")

- Every step logs `STEP <id> start` with a Seattle timestamp when it begins (a killed step
  leaves no timing row otherwise).
- At its cap a step logs `CAP <phase>: r/N rounds, mm:ss, kept best (k advisories)` and moves
  on with its best attempt. Never loop, never defer-and-re-author past the table, never park
  on style. The plan gets two climbs per episode; tier-1-only faults park once.
- Counters are per episode in `attempts.json` and a step's seconds survive a relaunch; a
  killed step is charged from its 60 s heartbeat. A round is a change of bytes.
- The 6 h episode clock is the outer wall; the caps only stop a runaway step. GATES.md holds
  the generated cap and clock tables.

## Resuming

1. Read `episodes/epNN/drive.jsonl` and the last `drive_runNN.log` (one log per launch), and
   say back where the episode is.
2. Resume through the autopilot only: `autopilot.py retry N --book <codex>` for a parked
   episode, `autopilot.py resume --book <codex>` for a paused series. Never launch drive.py.
3. The autopilot restarts a dead ComfyUI after 2 missed ticks; if a job ignores `/interrupt`,
   see memory `project_comfy_restart`. Never kill a drive (memory `project_kill_run_tree`
   is for a run already lost).

## Operating a live run (2026-10-19, Jekyll Kawajiri ep01 retro)

You watch and report; these are the only acts on a live run.

| you want | do | never |
|---|---|---|
| land a fix | the failing test, `autopilot.py pause --at-boundary --book <codex>`, wait for `paused_at_boundary` in the drive log, apply the patch file, run the touched tests NOW (the drive is paused), commit by explicit path, `autopilot.py resume`; a commit restarts the loop on the new code | edit a file a running drive will load (every subprocess it starts loads it); run pytest or a plan_check beside a Qwen edit; kill a drive |
| a plan row is wrong | `plan_repair` (records the cure in `plan.cures.jsonl`); an owner order is a recorded plan edit named `owner_order_<shots>`, judged first as a scratch plan by `plan_check.py <book> <n> --plan=<scratch>.json`; the next entry re-signs over carried rows, no writer round | patch `plan.json` unrecorded; touch a timestamp |
| a gate accuses correct work | read the MEASURE against the WALL; a wall calibrated on another form is a ruler fault: fix the ruler test-first (cheque/check, packs at 8 s, the 240-word floor), then `retry N` | re-roll a render; raise a wall without its replay |
| the owner changes an order mid-run | state the pictures it stales ("inputs: 2 of 28 takes stale"), redraw by the registry route only | a tagged one-off redraw the next step 07 supersedes |

- Dirty means runtime code: edits to tests/, docs/, architecture/, library/, logs/, `*.md`
  and `.claude/skills/` never hold a launch; a runtime edit during a run is logged
  (`code_dirty_during_run`), never paused for. A park at an older HEAD or on a dirty tree is
  never the brain's; a `brain:` park clears itself when runtime code lands (2 per episode).
- After a prompt-builder change, before any re-render: a no-write take-build replay (rebuild
  the dry prompts, diff against `takes/r2v/shots.json`, list the changed takes).
- On a plan park read `plan.cures.jsonl` and the learnings `draft` row first; after a panel
  rewind read the `panel_eye` row in timing.jsonl (`reads=N cache_hits=M unread=K`).
- After each run read `library/.device/gpu_util.jsonl` (`gpu_ledger.minutes_per_step`:
  busy / claimed / idle) and `scripts/audit/doc_sync.py` (fix commits with no doc line).
- **The report line:** the master's full path first, then QC's
  "inputs: all N takes current", every `CAP` line of the run, the flagged takes with their
  seconds, then the time left in Seattle time.

## After every run: improve this skill (owner, 2026-10-08)

Each episode ends with its lessons written here before the next one starts:
the measurement in LESSONS_ARCHIVE.md with its brick in the LESSONS.md index,
the rule in this file, a new gate number in GATES.md, all in the commit that
fixed the fault (or a `Docs: none (<reason>)` trailer; `scripts/audit/doc_sync.py`
lists the commits that did neither). An owner ruling that retires a sentence
adds it to `tests/fixtures/ep01_replay/P16/retired_phrases.json` in its own
commit. The Jekyll Kawajiri ep01 retro (13 failures, five bricks) is in the
archive. Rules learned on ep19-21:

- **One ruler.** A judge and the cure for its fault measure the same number the
  same way (`plan_gates.line_seconds`: the voice where a line is recorded). A
  fault no cure can move is a ruler mismatch until both numbers are printed.
- **A table keyed by a contract value covers every value** the contract can
  sign, tested against the Literal (`episode_spec.Size` and the grid's words).
- **A HARD take row is believed only after its strip is seen.** The letterbox,
  last-vs-panel and posture rows have each refused correct dark or quiet takes.
- **After the signature, plan.json changes only through a recorded cure.**
- **A verdict cache keys on the bytes AND the code that measured them.**
- **Where a fault was born decides its cure:** a take content fault on a panel
  that passed content gets one seed retake; on a panel that carries it, the
  board owns it. Count the stills a terminal chose before anything publishes.
- **A step is done when its check PASSED (or its one cure ran), never when
  its report exists.** The record step re-says a split voice's lines itself.
- **A timeline belongs to the plan it was built from**; read it through
  `episode_home.load_placed`, never by existence.

## When a failure sends you back

| you see | go back to |
|---|---|
| a plan gate or take-lint refusal | the plan `.py` (never `plan.json`) |
| a person in the wrong clothes, or the wrong person | `cast_rows.py` for this chapter; the plan's `tag`s |
| a picture missing its subject, or drawing the place instead | G-SCALE cells; the subject first in the prompt |
| a panel gate failure, or a fault `judge:panel_eye` lists | redraw that grid (`--shots=` plus a tag, or `--seed-bump=`) after moving the old one to `storyboard/superseded/`; never patch the panel |
| a person's count or clothes wrong in the grid | `extras` from the book; the chapter row (`cast_rows.py`); the grid goes stale by itself |
| a take that is "current" but wrong | its pictures changed; currency now sees that |
| QC's silent gap | the silent shot inside it (docs/calibration/silent_gaps.md) |

## Infrastructure

- **Never pass a backslash escape through a Bash heredoc or nested quotes.**
  Write the patch as a file with the file tool. This broke a regex three times
  and a patch script twice on 2026-09-22.
- **Never pipe a test run into `tail` and then `&&` a commit.** The pipe
  swallows pytest's exit code. Run `pytest; echo EXIT=$?`.
- **A take POST is not idempotent.** Ask the queue before re-posting.
