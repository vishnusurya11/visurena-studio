---
name: episode
description: "Turn one book chapter into a 2-3 minute square (1:1) episode at $0, entirely local: first-person narration and a few spoken lines laid over pictures cut to the measured voice. Chain: plan (gated) -> per-episode place pictures + one sheet per character -> Qwen3-TTS lines -> timeline -> Qwen-Image storyboard grids cut into panels (two panel gates) -> MiniMax-H3 ref2va takes (take gate + content gate) -> assemble with bed and title card -> QC -> publish public. Use when writing, building, fixing, resuming or reviewing an episode under library/<book>/episodes/."
---

# Episode

**Where to run.** Every command below runs from the repo root,
`D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio`, on `master`. There is
one checkout. Never create a worktree, a per-book branch or a second copy of
the repo; the owner's rule (2026-09-24) is that everything lives in this one
folder, and everything book-specific lives under its `library/<book>/`.

One chapter is one episode: 2-3 minutes, 1:1, $0, every step local. The owner's
word outranks anything in this file; when he corrects the work, the correction
goes here and into memory.

**Read these before you work:**
- `LESSONS.md` beside this file: every rule below, with the measurement that made it.
- `GATES.md` beside this file: every gate, what it measures, whether it is hard, and how to run it.
- `docs/calibration/*.md` in the repo: the measured detail behind the gates.
- `SCARLET_ARCHIVE.md`: the previous skill, for the other book's route and dated history only.

**Deliverable first.** Every message that produces or changes an output begins
with the full absolute path of the finished file, on its own line. Keep every
master as `cut/master_iterN.mp4`, and never overwrite the only copy.

---

## RULE ONE — gate the plan before anything is made

Nothing is rendered until the plan passes both batteries. Each battery needs
inputs, so the order is fixed:

```
uv run python scripts/refs/cast_rows.py <book> <n> <who[=Display:gender]> ...  # FIRST: takes, grids and content checks read this one bound row
uv run python scripts/episode/step_02_plan.py <book> <n>          # the writer agent -> plan.json through plan_check + improve loop, then the PLAN signature
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
parking on every owner gate with a call-sheet line:

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
| 03 | places | `uv run python scripts/episode/step_03_places.py <book> <n>` | Each setup's location+view at THIS unit's hour, drawn from its own described words on the local image model. |
| 04 | record | `uv run python scripts/episode/step_04_record.py <book> <n>` | Every line in its character's voice, MEASURED and LISTENED to. |
| 05 | timeline | `uv run python scripts/episode/step_05_timeline.py <book> <n>` | AUDIO FIRST - the animatic. |
| 06 | prompts | `uv run python scripts/episode/step_06_prompts.py <book> <n>` | Every take prompt built and linted for $0 with no GPU, BEFORE any grid: length per block, style line, banned props, no last frame, no fragments. |
| 07 | board | `uv run python scripts/episode/step_07_board.py <book> <n>` | Storyboard grids on the local image model from the plan's prose, up to three references - cast sheets first, the setup's place last. |
| 08 | panels | `uv run python scripts/episode/step_08_panels.py <book> <n>` | One panel per shot, two machine gates, then `judge:panel_eye`. |
| 09 | shoot | `uv run python scripts/episode/step_09_shoot.py <book> <n>` | The slow step. |
| 10 | edit | `uv run python scripts/episode/step_10_edit.py <book> <n>` | Title card, measured bed, cut, mix. |
| 11 | qc | `uv run python scripts/episode/step_11_qc.py <book> <n>` | Measure the DELIVERED master, never the intention. |
| 12 | deliver | `uv run python scripts/episode/step_12_deliver.py <book> <n>` | manifest.json beside the master (every gate verdict, every rung, timing totals), the deliverable's full path printed first, notify() through the platform. |
<!-- /registry:episode -->

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

| # | step | command | its gate |
|---|---|---|---|
| 1 | Bind this chapter's cast | `uv run python scripts/refs/cast_rows.py <book> <n> <who[=Display:gender]> ...` | stamps `refs.json` with the chapter; must precede the plan; the take, grid and content steps all read this one row |
| 2 | Plan | a new unit's plan is written by the `episode_writer` agent (step 02) into `library/<book>/episodes/epNN/plan.json`; an existing hand-authored `library/<book>/episodes/epNN/plan.py` regenerates it when run | RULE ONE above |
| 3 | Sheets and prop sheets | `uv run python scripts/refs/build_pack.py <book> --kind characters --only <a> --only <b>` (repeat the flag; `--kind props` for a key prop) | look at every sheet beside its row; words must match the picture (LESSONS: cast) |
| 4 | Places at this episode's hour | `uv run python scripts/refs/places.py <book> <n> [--draw] [--new=<loc>="Its name"]` | every setup's `location`+`view` resolves to a drawn picture (guard test); look at each one |
| 5 | Voices (new speakers only) | `uv run python scripts/cast/cast_voices.py <codex> --only <a>,<b> [--recast]` | pairwise similarity under the wall; at most 4 voices an episode |
| 6 | Lines | `uv run python scripts/episode/say_lines.py <book> <n> [--redo=i,j]` | every line heard as written (listen gate) |
| 7 | Timeline | `uv run python scripts/episode/respot.py <book> <n>` then `uv run python scripts/episode/timeline.py <book> <n>` | fingerprinted to the plan AND the measured voice; every reader refuses a stale one |
| 8 | Grids | `uv run python scripts/episode/grids.py <book> <n> <setup> <cols> <rows> [tag] [--shots=..]` | shot count = cols x rows; the manifest records `inputs` (the exact prompt and every staged picture's bytes) and the prompt version (v2 default) |
| 9 | Panels | `uv run python scripts/episode/panels.py <book> <n>` | a grid is stale when its prompt or a staged picture would now differ (a rebound row, a redrawn sheet or place, a builder fix); every shot from exactly one grid; a panel is cropped square and written only if its pixels changed, so re-running is safe |
| 10 | Panel gates + EYE | `uv run python scripts/episode/panel_check.py <book> <n>` and `uv run python scripts/episode/panel_content_check.py <book> <n>`, then a contact sheet of all panels, looked at | both must exit 0; `takes_r2v` refuses without both verdicts. Both gates have passed one man with two hats, a white gutter and an insert that was the place reference copied back |
| 11 | Takes | `uv run python scripts/episode/takes_r2v.py <book> <n> --from-refs --approved=render` | the take lint; a take is current only to its words AND its pictures |
| 12 | Take gates + EYE | `uv run python scripts/episode/take_dq.py <book> <n> [idx...] [--attempts]` and `uv run python scripts/episode/take_content_check.py <book> <n>`, then a 5-frame strip of every take, looked at | QC and the upload refuse an unjudged take. `held` fails a person pinned while the set slides; `jump` fails a switch of picture |
| 13 | Title card | `uv run python scripts/episode/series_title.py <book> <n>` | QC fails a master without one |
| 14 | Cut | `uv run python scripts/episode/assemble.py <book> <n> --engine=r2v` | kept as `cut/master_iterN.mp4` |
| 15 | QC | `uv run python scripts/episode/qc.py <book> <n> --engine=r2v` | must say PASS; a silent gap names the shot it is made of |
| 16 | Publish | write `episodes/epNN/youtube.json`; `youtube_upload.py <book> <n> --engine=r2v --dry-run`, then `--approved`; then `uv run python scripts/publish/youtube_privacy.py <book> <n> public --approved` | the upload refuses failed or unjudged takes; the flip to public re-checks QC (about the uploaded sha8) and every take, as they stand then |

Step 16 inserts the video private, because an unverified API project forces
that on `videos.insert`, and then flips it public. **When the owner says
upload, it goes public.** He corrected the work for making it private once.

---

## Writing the plan

The plan is the contract (`studio/episode_spec.py`). The plan `.py` is the
source, and `plan.json` is always what running it produces. **Never patch
`plan.json` directly.** ep01, ep03 and ep04 were patched that way; their plan
scripts would revert what shipped, and a strict guard names them.

**The story.** One chapter, one brick: a QUESTION, a TURN (the lead's choice,
50-75% of the way in), an ANSWER, and a BUTTON (the last line, never the
lead's). The turn is people acting on each other, so name both of them in one
motion clause.

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
- `faces` are the people whose faces must read.
- A setup's `crowd` declares a crowd.
- Every other unnamed person is counted in the shot's `extras`.
- No gate guesses people from the prose any more, so the plan must say.

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
- dialogue outside 5-20% of the words.

`plan_check` refuses each of these.

---

## Pictures

**Sheets.** One sheet per character, one wide per place per episode, and one
sheet per key prop. Closer sizes and states come from the take's camera and
words, never from edited pictures.

**Look at every picture you draw** before anything is built on it. Put the
defining state or detail FIRST in its prompt. A detail buried mid-sentence is
dropped:
- the lawn was drawn with no fire;
- Snippy was drawn clean-shaven when every text gave him a moustache.

When the words and the picture disagree and the book is silent, make the words
match the picture.

**Grids.** Qwen-Image-2.1 edit-multi takes 1-3 references:
- cast sheets first, the identity slots;
- the setup's own place picture last, the scene and style slot;
- only the cast of the shots a grid OWNS, since a borrowed cast draws line-ups;
- an unused LoadImage slot feeds the encoder ComfyUI's example doll, so
  `stage_only` removes it.

The 2x2 minimum is an OPEN owner decision (audit Tier 0, D3). ep09 drew
1x1, 2x1 and 3x1 grids because its setups hold 5, 3 and 2 shots; the owner
has not ruled. Say which layout you use in the report.

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

MiniMax-H3 ref2va runs the Singularity fine-tune with the turbo LoRA x2
(1.0/0.7). **H3 obeys direction, not amount.** It follows the cell and the
camera verb; amounts, angles and negations are ignored.

**Camera.**
- Point every move at something the cell already holds (G-AIM).
- Never truck sideways across a person anchored to the set (G-ANCHOR). A
  walker the camera tracks WITH is fine: say "with him" / "keeping him".
- The take prompt carries the camera's direction only; the builder drops the
  travel amount. The plan keeps amounts because G-MOVE measures them.
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
| lip-sync lags | shorten the take |
| a hard cut appears early | the take opened on another staged picture, or on the place its prompt names three times |
| the same fault on a fresh seed | the PLAN: re-aim the move at what the cell holds (ep09 shots 14, 15, 18 repeated on new seeds) |
| a person pinned while the set slides | the plan: push in or crane instead of the truck (G-ANCHOR) |

Retakes run in ONE batched round, after the take gates AND `judge:take_eye`:
`takes_r2v.py <book> <n> --from-refs --approved=render --retake=a,b --why="<gate row or finding>"`.
`--why` is required; a round of one take is refused unless `--last` declares
it the last round for this master. The failed take is kept as
`attempts/T<NN>_failN.mp4`. Judge with `take_dq.py <book> <n> a b --attempts`
so the better attempt is kept. After `panels.py` rewrites a panel, re-run both
panel gates: the takes refuse a verdict older than its panel.

**Never pin a last frame.** ref2v gives a take its first frame only.

---

## Cut and QC

**Audio first, always.** The picture is cut to the measured voice. Every line
sits at its shot's start plus the handle, and `episode_timeline.misaligned()`
refuses anything else.

**Silent gaps.** QC walls the longest silence at 6.0 s and names the shot the
gap is made of. If a silent shot lies inside the gap, give it a line or move
the silence to a short shot with lines on both sides. Trim a coda last, and
never a moving shot's coda.

---

## Resuming

1. Read `episodes/epNN/story.md` and say back where the episode is.
2. Check the GPU and ComfyUI's queue before starting a run.
3. If a job ignores `/interrupt`, restart ComfyUI; see memory
   `project_comfy_restart`.

Stop a run by killing its process tree by command line, never `uv.exe` alone
(memory `project_kill_run_tree`).

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
