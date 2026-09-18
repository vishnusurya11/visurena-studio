# A Study in Scarlet — the whole production, in one file

**Status: COMPLETE. Fourteen chapters, fourteen episodes, all published.**
Finished 2026-09-18. This file is the context handoff: what was built, how it
works, what was learned, and what is still broken.

Book id: `20260822113400_a-study-in-scarlet`
Everything below lives under
`D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\library\20260822113400_a-study-in-scarlet\`
except the code, which is in the repo, and `docs/`, which is tracked.

> `library/` is **gitignored**. The renders, plans, audio, sheets and ledgers
> exist only on that disk. The code, the docs and this file are in git.

---

## 1. What it is

A YouTube serial on the channel **The Keeper's Lantern**. One whole chapter per
episode, in order, first page to last. Each episode is 2–3 minutes, 1:1 square,
rendered at 768×768 and uploaded at 2×. The pictures and the voices are
generated; the words are Doyle's, adapted. Every episode carries an AI
disclosure and is flagged synthetic to YouTube.

### The fourteen

| # | chapter | video | length | note |
|---|---|---|---|---|
| 1 | A Mr. Sherlock Holmes | `-K2ucdt_mCg` | | |
| 2 | The Science of Deduction | `P8i7niWhEWo` | | 0 words lifted from Doyle |
| 3 | The Lauriston Garden Mystery | `Pkr4HudmQPo` | 167 s | shipped against a **stale QC report** — the reason the sha8 gate exists |
| 4 | What John Rance Had to Tell | `WN2ktyq8tr0` | 143 s | 24/24 takes, mean 96.8 |
| 5 | Our Advertisement Brings a Visitor | `g-U-P0ZOoq8` | 162 s | 25/25; first episode where provenance actually measured |
| 6 | Tobias Gregson Shows What He Can Do | `AIX83NAcTGc` | 164 s | 26/26 at 100.00. First with a camera move in every shot head; frozen-share 0.0 against 67.2 in ep05 |
| 7 | Light in the Darkness | `xksX2qouWEo` | 135 s | 25/25; first whose END panels are drawn from where the camera finished |
| 8 | On the Great Alkali Plain | `V5sFXhGemRk` | 164 s | **Part Two begins**: no London, no Holmes, no Watson. 28/28 |
| 9 | The Flower of Utah | `Me9h8oQwx6E` | 151 s | 28/28 at 100.0, the best DQ in the series — **and one of the worst episodes**. See §5 |
| 10 | John Ferrier Talks with the Prophet | `nftf6bbjQMs` | 176 s | 30/30 after 9 retakes; 5.0 h of stages |
| 11 | A Flight for Life | `ZC7AWsoTrlo` | 164 s | 25/25 |
| 12 | The Avenging Angels | `s7_uJ-VSDHk` | 170 s | 24/28; four takes accepted on sight with a recorded override |
| 13 | A Continuation of the Reminiscences… | `OoTLbV3KurU` | 170 s | 28/28 after one retake. Title card drawn **locally** — the image API ran out of credit mid-episode |
| 14 | The Conclusion | `FSVrTMyOxxs` | 163 s | 16/24 after two retake rounds. See §6 |

Chapters 8–12 are the Utah flashback: different cast, different continent, no
Holmes or Watson. That cast and location work is as large as an episode of its
own.

### What it cost

**332 paid images, ~$41.02 estimated**, all on `gpt-image-2.5-sunburst`.

| count | size | cost |
|---|---|---|
| 169 | 2048×2048 | $21.97 |
| 65 | 2048×3072 | $12.80 |
| 43 | 1024×1536 | $3.44 |
| 53 | 1024×1024 | $2.65 |
| 2 | 1536×1024 | $0.16 |

Per episode ran $0.73–$1.77. Every image is logged to `spend.jsonl` with its
purpose; the `usd_estimate` field is the number, calibrated against the OpenAI
usage page on 2026-09-10. **Video rendering costs nothing** — it is local GPU
(ComfyUI, MiniMax-H3), and it is the slow part, roughly 4 minutes a take.

---

## 2. The pipeline

Run through one dispatcher, which enforces one GPU stage at a time:

```
uv run python scripts/episode/run.py <book_id> <n> <stage> -- [flags]
```

| stage | script | what it does | cost |
|---|---|---|---|
| `lines` | `say_lines.py` | **AUDIO FIRST** — every line rendered on IndexTTS2 and measured | free, GPU |
| `respot` | `respot.py` | scales sub-shot cuts to the measured lines | free |
| `timeline` | `timeline.py` | `placed.json`: shot times derived FROM the audio | free |
| `frames` | `frames.py` | one empty plate per setup | free, GPU |
| `sheets` | `seq_boards.py` | one storyboard sequence per setup | **PAID**, ~$0.13/sheet |
| `takes` | `takes_r2v.py` | every take on H3 ref2va from the board's cells | free, GPU, ~4 min each |
| `take_dq` | `take_dq.py` | 16 measured rows per take | free |
| `assemble` | `assemble.py` | cut, music bed, title card → `master_r2v.mp4` | free |
| `qc` | `qc.py` | measures the delivered file, stamps its sha8 | free |
| `title` | `title.py` | the episode's title card | **PAID**, ~$0.05 |
| `eye_review` | `eye_review.py` | 30-frame contact sheet + a rubric a person fills | free |
| `publish` | `scripts/publish/youtube_upload.py` | the gate ladder, then upload | free |

### The non-negotiables

- **AUDIO FIRST.** The plan carries no seconds. Every line is rendered and
  measured, and each shot's length is derived from the lines it carries.
  `shot.seconds = 0.25 + Σ(line seconds) + 0.70×(lines−1) + 0.25 + beat + coda`,
  snapped up to a whole frame at 24 fps. Nothing is scheduled afterwards.
- **THE PANEL IS FRAME ZERO.** The storyboard cell is the instant before the
  motion, and the render begins on it.
- **NO END CELL EVER REACHES A TAKE.** A take gets its first frame and nothing
  else; the arrival is said in WORDS. A last-frame pin makes the model race to
  the end picture and hold, which is the freezing, or glide, which dissolves the
  background. `docs/calibration/end_frames.md`. The check is on the artefact:
  a take prompt must contain zero occurrences of `last frame of [Shot` and stage
  zero `*E.png` references.
- **NARRATION IS NEVER IN THE TAKE.** Only dialogue wavs go into a render — an
  anchored narration made the on-screen face mouth it. Narration is laid on the
  master.
- **One GPU, one stage at a time.** Two concurrent H3 runs clobbered a work dir.

### The YouTube title

Built by `studio/youtube_publish.series_title`, never typed by hand:

```
Sherlock Holmes: A Study in Scarlet — Ep 04/14 — "What John Rance Had to Tell"
```

The serial and position come first because a search result shows 40–70
characters and the first five episodes led with the chapter title, which is the
one thing that cannot tell a viewer what this is. `04/14` not `Ep.4` because
someone deciding whether to start a serial wants to know how long it is.

---

## 3. The assets

**Cast:** 32 identity busts, each with indoor/outdoor wardrobe cards, under
`refs/characters/`. Holmes, Watson, Lestrade, Gregson, Drebber, Stangerson,
Jefferson Hope (plus a separate cabman card), the Ferriers, Lucy as child and
woman, Brigham Young, the Charpentiers, Wiggins, and the walk-ons.

**Voices:** 30 under `cast/`, including group voices (fugitives, Mormons, two
detectives). IndexTTS2 from `cast/<who>/voice/design.wav`. Gate: Whisper WER
≤ 0.20 **and** ECAPA ≥ 0.70.

**Locations:** 13 under `refs/locations/` — 221b, the Criterion, Lauriston
Gardens, Audley Court, Scotland Yard, Halliday's, St Bartholomew's, the Utah
plates. **See the warning in §7.**

**Wardrobe contract**, one state, in every frame text: Watson bare sunburnt
hands to the wrist, black stick with a silver knob; Holmes bare-headed, green
velvet jacket, plaster on the right forefinger. `physical` is invariant;
`wardrobe[state]` carries the hat, chosen by the setup's own state.

---

## 4. What was learned about the model

These are measured, not folklore. Each cost at least one episode.

- **H3 obeys the cell and the camera VERB. It ignores amounts, angles,
  absences and kept-clauses.** "Travelling a hand's breadth" is not read. A
  stated head fraction is honoured at a median 0.95 at or above a quarter of
  frame height, and 0.00–0.45 below it.
- **A move's DIRECTION is obeyed and its DISTANCE is not, so the direction must
  point somewhere the cell already covers.** When a move overruns past
  everything the cell contains, the model *invents* what it arrives at, and what
  it invents contradicts the other takes in the setup. (§6.)
- **A push is the only move that changes a shot's SIZE, and size is what the cut
  is built from.** Treat a push on a wide as a plan smell.
- **Negations are unreadable.** A negated noun is still that noun — a "no
  signage" clause drew a shopfront reading CRISTERION. Every string is
  affirmative.
- **Stillness words freeze the segment.** A block with two or more measured
  0.77 frozen share against 0.47.
- **Between two panels: ONE simple camera move plus ONE small local action.** A
  ref2va segment is given two pictures and asked to get between them. If they
  differ by a *reposition*, there is no path and the model dissolves one into
  the other — that is the morphing. If they differ by *scale* or a shifted frame
  edge, the path is a camera move, which it is good at.
- **A frozen start is cured only by a fresh seed.** 4 of 51 moving shots in
  ep06–07 froze regardless of wording. `docs/calibration/frozen_starts.md`.
- **Put the cut in the EDIT, not in the take.** A sub-shot is a cut the model
  places from a stamp rounded to a whole second, so ±12 frames. Measured over
  ep03's 15 internal pins, 7 could not land inside the tolerance even with
  perfect obedience. Episode 4 onward: one line per shot, no internal cuts.

---

## 5. What was learned about the gates — read this before trusting a score

**Episode 9 passed 28 of 28 takes at 100.0, the best DQ in the series, and is
one of the worst episodes.** 62% of its frames were off their storyboard cell,
its 5th-percentile luma was 16.5 against 4–7 for episodes 5–7, and its first
dialogue arrived at 87.6 seconds. Every gate was built for one fault and found
its own fault absent. `docs/analysis/ep08_ep09_why_worse.md`.

That produced two standing rules:

1. **A passing gate proves only the absence of the fault it was built for.** The
   owner-judged episodes are the calibration set, not the scores.
2. **`eye_review` is a STAGE with an ARTEFACT** — a 30-frame contact sheet and
   five questions, each one of episode 9's faults, answered `y`/`n` by name. The
   publish ladder refuses `--watched=<sha8>` without it, and refuses a rubric
   that reviewed different bytes.

**A gate accusing correct work is usually a threshold calibrated on an earlier
episode.** Two live examples:

- The **off-board** row is a cosine to the static cell and cannot forgive a
  large honest move. Its own calibration notes say so. Episode 6, which the
  owner judged fine, is the worst episode ever measured on it (10 HARD of 26).
- The **look floor** is calibrated on night interiors, so a daylit interior
  fails it for having no true black.

**Corollary, learned the hard way:** green tests are not evidence that a prompt
fix reached the artefact. Measure the artefact.

---

## 6. Episode 14, in detail (the most recent work)

Two things about it are worth carrying forward.

### The references-only experiment, and why it was abandoned

With the image API out of credit, the owner asked what a take looks like if the
character cards and location pictures go **straight into the ref2v slots** with
no storyboard at all, everything else said in words. Implemented behind
`--from-refs`, and one 24-take reel was rendered.

Results: identity bound well and the corpse read as the right man. But:

- A take handed only a face **invented the room** — four takes put Holmes and
  Watson in a Gothic panelled hall with a carved stone chimneypiece.
- A take handed a room picture **opened at that room's framing** and pushed in,
  so inserts and wides landed but mediums started far too wide.
- Five of sixteen DQ rows report "not measured" with no cell, so the episode
  could not be judged.

The owner stopped it on a different fault entirely: **the room looked wrong**,
and he was right — see §7. The experiment is preserved on branch
`refs-experiment-2026-09-17`; master was reset to the commit before it.

### The camera-direction finding

Shots 7 and 8 are inserts on the ground — cart ruts, bootprints in clay — both
written "the camera tilts up … travelling a finger's breadth". Both travelled
until they were looking at the skyline, where their cell holds nothing, and both
invented a **tidy occupied terrace with a clipped lawn**. Shot 9, cut from the
same sheet, correctly shows a **boarded-up empty house**. The sheet was right;
the takes left it.

- Panning shot 7 along the kerb fixed it, because everything sideways of the
  ruts is more roadway.
- The same pan did **not** fix shot 8, whose lens sits at a stooping man's eye
  and therefore looks *along* the path — sideways travel still swept to the
  house. Pointing it **straight down at the clay** fixed it, because then no
  direction leads anywhere else.

This is the same failure as the references-only Gothic hall, reached from the
other side: not "no reference" but "travelled past the reference". **No DQ row
caught it.** Comparing three takes of one setup by eye did.

Also fixed: shot 0's push turned an 8-second wide into a close on the dead face,
which is shot 1's framing, so the two cut on the same picture — now a pan.
Shot 21 froze for 1.75 s — the lift was the last of four clauses, and now leads.
And shot 1 still carried "a strand of black hair stirs on the stone", animating
a corpse; now only the dawn light crosses his face. A dead man has exactly one
honest mover, and `crosses` satisfies the body-scale lint without touching him.

---

## 7. Open faults — the work that is left

Ordered by how much they matter.

**1. THE SERIES HAS NO SINGLE BAKER STREET.** This is the one the owner stopped
a render over. `refs/locations/loc-221b_baker_street.png` and episode 14's own
`plate_sitting_room_evening.png` are two completely different rooms — the book
picture has a chemistry bench, a violin and two windows flanking the fireplace;
the plate has none of them and a different wall layout. 221b appears in only
three of fourteen episodes (3, 5, 14) and was never pinned to one reference.
Episode 3's only Baker Street shot is too tight to establish the room, so the
series cannot even be checked against itself. **Every recurring location needs
one picture that every episode stages, and nothing enforces it.** Until 2026-09-18
`picture_path` had no `loc-` branch at all, so a book location resolved into the
episode's cells folder and crashed.

**2. `identity` and `wardrobe` DQ rows are stubs.** `identity_gate.observe`
raises `NotImplementedError` and facenet-pytorch is not installed. Every take in
the series reports "identity not measured". Nothing has ever verified that the
face on screen is the right person.

**3. No gate reads text.** A re-roll produced a visiting card reading "Number 3
Lauriston Gardens." instead of "Enoch J. Drebber", and DQ **promoted it over the
correct take** because it scored higher. Any lettered prop needs an OCR check or
best-of-N will actively choose the misspelt one.

**4. Every DQ gate reads one 48×84 grey thumbnail**, 146:1 against the frame. A
defect smaller than ~1/150 of the frame — lettering, a face, a sixth finger, the
wrong hat — is invisible by construction.

**5. No prop reference has ever reached a take.** `reference_list` never calls
`props_in`; episode 3's takes used 1–5 of 9 available slots.

**6. Three of six episode-3 plates are the wrong place.** `plate_corner_wall` is
a street exterior for a setup described as "the darkest corner of the front
room", because `described` opens with the exterior paragraph and `geometry`
never reaches the plate prompt.

**7. `geo_gate` is dead code** — zero callers outside its own test.

**8. Unresolved from the episode-14 audit:** illegible newspaper text in
inserts; boot prints that read modern; light-direction instructions disobeyed.

---

## 8. Operating notes

- **Spend is pre-authorised** by the standing goal. Sheets $0.13–0.20, panels
  $0.08, title cards $0.05, an episode about $1.00–1.30. Log it, report the
  number. Ask first only for something outside scope, an order of magnitude past
  the norm, or a paid service never used before.
- **Publishing may run unattended ONLY when QC passes on the exact file.** QC
  stamps the sha8 it measured and the ladder refuses a report about different
  bytes. Episode 3 went out against a stale report; that is why.
- `--override="<reason>"` waives the two *quality* gates (qc.passed and the DQ
  roll-up) and nothing else. The reason is recorded in `uploads.jsonl` beside
  the video id. Episodes 12 and 14 used it.
- **A single-take retake round is refused** unless you pass `--last`, to stop
  death by a thousand retakes. Batch retakes into one round.
- **Kill runs by CommandLine match, not by killing `uv.exe`** — the Python
  children keep rendering. Check `/queue` on ComfyUI at 127.0.0.1:8188 before
  and after.
- **Never write source through a Bash heredoc.** A backslash escape reaches disk
  mangled — `\b` became byte 0x08 in two committed files. Use the Write/Edit
  tools. `tests/test_no_backspace_byte_in_source.py` guards it now.
- **This box has no `ffprobe`.** ffmpeg reports duration instead; `script_qc.py`
  already falls back.
- **OpenRouter serves `openai/gpt-image-2.5-sunburst`** through
  `/v1/images/generations` — it does **not** appear in the `/models` listing, and
  there is **no** `/images/edits` endpoint, so reference images cannot be passed
  that way. Useful only if the OpenAI account is dry and you can work without
  references. Chat-completions image models there cap at 1024×1024, which halves
  every storyboard cell.

---

## 9. Where to look

| what | where |
|---|---|
| the standing goal and open faults | `docs/SERIES_GOAL.md` |
| the progress ledger | `library/…/SERIES_PROGRESS.json` |
| every paid image | `library/…/spend.jsonl` |
| every upload, with waivers | `library/…/uploads.jsonl` |
| per-episode state and decisions | `library/…/episodes/epNN/story.md` |
| why a threshold is what it is | `docs/calibration/` |
| why an episode went wrong | `docs/analysis/epNN_issues.md` |
| the H3 reference-prompt spec | `docs/calibration/h3_ref_guide.md` |
| the pipeline's own rules | `.claude/skills/episode/SKILL.md` |

**Start with `docs/SERIES_GOAL.md`.** It is the watchdog file, it now records
that the series is discharged, and its last section carries everything learned
from the final episode.
