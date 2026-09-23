---
name: episode
description: "Turn one book chapter into a 2-3 minute square (1:1) episode at $0, entirely local: first-person narration and a few spoken lines laid over pictures cut to the measured voice. Chain: plan (gated) -> per-episode place pictures + one sheet per character -> Qwen3-TTS lines -> timeline -> Qwen-Image storyboard grids cut into panels (two panel gates) -> MiniMax-H3 ref2va takes (take gate + content gate) -> assemble with bed and title card -> QC -> publish public. Use when writing, building, fixing, resuming or reviewing an episode under library/<book>/episodes/."
---

# Episode

**Where to run.** Every command below runs from the worktree
`D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio_wotw` (branch
`wotw-refs-poc`), which holds the code this skill names. `master` is behind
it. The library is shared between the two by a symlink.

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

Nothing is rendered, voiced or drawn until the plan passes both batteries:

```
uv run python scripts/episode/plans/<book>_epNN_<slug>.py        # writes plan.json
uv run python scripts/episode/plan_check.py <book> <n>            # must end "VERDICT: clean"
uv run python scripts/episode/takes_r2v.py <book> <n> --from-refs --prompts   # must refuse nothing
```

`--prompts` builds every take prompt and runs the take lint over it for $0,
with no GPU. ep06 paid for three picture stages by skipping it. ep09 skipped
it too: seven take prompts were over length and four carried a banned prop,
and nobody knew until the takes stage (2026-09-22).

`plan_check` exits 1 whenever it refuses anything. **An exit of 1 is a stop.**
It used to fail every WotW plan for another book's reasons, and people read
past it; that is fixed, so a refusal now means something.

---

## The chain

`<book>` is the codex id (e.g. `20260827135508_the-war-of-the-worlds`), `<n>`
the episode number. Every command refuses when the episode number is missing,
and none of them defaults to 1.

| # | step | command | its gate |
|---|---|---|---|
| 1 | Plan | write `scripts/episode/plans/<book>_epNN_<slug>.py`, run it | RULE ONE above |
| 2 | Bind this chapter's cast | `uv run python scripts/refs/cast_rows.py <book> <n> <who[=Display:gender]> ...` | stamps `refs.json` with the chapter; the take, grid and content steps refuse rows stamped for another chapter |
| 3 | Sheets | `uv run python scripts/refs/build_pack.py <book> --kind characters --only <who> ...` | look at every sheet beside its row; words must match the picture (LESSONS: cast) |
| 4 | Places at this episode's hour | `uv run python scripts/refs/places.py <book> <n> [--draw]` | every setup's `location`+`view` resolves to a drawn picture (guard test); look at each one |
| 5 | Voices (new speakers only) | `uv run python scripts/cast/cast_voices.py <codex> --only <who>` | pairwise similarity under the wall; at most 4 voices an episode |
| 6 | Lines | `uv run python scripts/episode/say_lines.py <book> <n>` | every line heard as written (listen gate) |
| 7 | Timeline | `uv run python scripts/episode/respot.py <book> <n>` then `uv run python scripts/episode/timeline.py <book> <n>` | fingerprinted to the plan AND the measured voice; every reader refuses a stale one |
| 8 | Grids | `uv run python scripts/episode/grids.py <book> <n> <setup> <cols> <rows> [tag] [--shots=..]` | filed under `storyboard/grids/` with a manifest, the plan's hash and the prompt version (v2 default; `--prompt=v1` reproduces old grids, see docs/calibration/grid_prompt_ab.md) |
| 9 | Panels | `uv run python scripts/episode/panels.py <book> <n>` | every shot from exactly one grid, drawn from THIS plan |
| 10 | Panel gates | `uv run python scripts/episode/panel_check.py <book> <n>` and `uv run python scripts/episode/panel_content_check.py <book> <n>` | both must exit 0; `takes_r2v` refuses without both verdicts |
| 11 | Takes | `uv run python scripts/episode/takes_r2v.py <book> <n> --from-refs --approved=render` | the take lint; a take is current only to its words AND its pictures |
| 12 | Take gates | `uv run python scripts/episode/take_dq.py <book> <n>` and `uv run python scripts/episode/take_content_check.py <book> <n>` | QC and the upload refuse an unjudged take |
| 13 | Title card | `uv run python scripts/episode/series_title.py <book> <n>` | |
| 14 | Cut | `uv run python scripts/episode/assemble.py <book> <n> --engine=r2v` | kept as `cut/master_iterN.mp4` |
| 15 | QC | `uv run python scripts/episode/qc.py <book> <n> --engine=r2v` | must say PASS; a silent gap names the shot it is made of |
| 16 | Publish | write `episodes/epNN/youtube.json`; `uv run python scripts/publish/youtube_upload.py <book> <n> --engine=r2v --approved`; then `uv run python scripts/publish/youtube_privacy.py <book> <n> public --approved` | the upload refuses failed or unjudged takes; the title is the book's own series |

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
- Name people with `cast_refs.tag(BOOK, who, "the narrator", [fragments])`.
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

The owner's rule is a 2x2 minimum; a setup of 2, 3 or 5 shots needs his word
before a 1x1 or 2x1 is drawn.

**Panels.** `panels.py` cuts each shot from its grid and sheds the gutter it
measures. It writes `storyboard/h3/shot_NN.png` at 768 for the take.

---

## Takes

MiniMax-H3 ref2va runs the Singularity fine-tune with the turbo LoRA x2
(1.0/0.7). **H3 obeys direction, not amount.** It follows the cell and the
camera verb; amounts, angles and negations are ignored.

**Camera.**
- Point every move at something the cell already holds.
- Use at least 8 moves an episode, drawn from `docs/calibration/camera_catalog.md`.

**When a take fails, match the cure to the cause:**

| symptom | cure |
|---|---|
| a moving take froze | re-roll the seed |
| a still take froze | change the move TYPE, not its amount |
| a take froze after its OWN length changed | put the length back; a fresh seed is not the cure (ep08 T16: 51%, then 75%, then 10% frozen once restored) |
| lip-sync lags | shorten the take |
| a hard cut appears early | the take opened on another staged picture |

Retakes run in one batched round: `--retake=a,b --why="..."`. The failed take
is kept as `T<NN>_failN.mp4`.

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
| a panel gate failure | redraw that grid (`--shots=`, `--seed-bump=`); never patch the panel |
| a take that is "current" but wrong | its pictures changed; currency now sees that |
| QC's silent gap | the silent shot inside it (docs/calibration/silent_gaps.md) |

## Infrastructure

- **Never pass a backslash escape through a Bash heredoc or nested quotes.**
  Write the patch as a file with the file tool. This broke a regex three times
  and a patch script twice on 2026-09-22.
- **Never pipe a test run into `tail` and then `&&` a commit.** The pipe
  swallows pytest's exit code. Run `pytest; echo EXIT=$?`.
- **A take POST is not idempotent.** Ask the queue before re-posting.
- **The library is a symlink from the worktree to the main repo's library.**
  A path under it resolves to the main repo.
