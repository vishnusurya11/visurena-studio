# Trailer blueprint — the checklist an agent follows without thinking

The brick of automation: **a blueprint an agent follows blindly is a program
whose only free variables are typed fields.** The model fills a schema; a
gate with a fixed number decides; a failed gate takes the next rung of a
ladder that changes the FORM and keeps the FUNCTION; the last rung is a
fallback that always exists. Nothing asks a human. Everything is logged.

## Run it

```
uv run python trailer.py <codex_id>      # one book — the unattended form
uv run python trailer.py                 # every ready book, until the first one fails
```
That is the whole interface. An agent asked to "make the trailer" runs the
command, reports `library/<book>/trailer/main/qc.json` and `learnings.jsonl`,
and stops.

**`<codex_id>` is NOT the folder name.** It is the 14-digit `codex.id`, and
`paths.book_dir` globs `library/{codex_id}_*` — so the book at
`library/20260822113400_a-study-in-scarlet/` is run as `20260822113400`.
Pasting the folder name every other line of this file uses raises
`expected exactly 1 library folder for <id>, found 0` before the run opens.
That is the first thing a fresh agent gets wrong.

**The bare batch form runs nothing today.** `ready()` is
`codex_ready_for_stage(conn, 'trailer', '10', 'screenplay', '05')`; MEASURED
2026-09-06 against `db/visurena_studio.db`: of 30 codex rows exactly one
carries a `screenplay`/`05`/`completed` event (Scarlet) and it also carries
`trailer`/`10`/`completed`, so the query returns `[]`. It is also not isolated
per book — `main` loops `process(conn, codex_id)` with no `try` and `process`
re-raises after marking the stage failed (`trailer.py:87-108`), so the first
crash ends the batch and every later book is never attempted, indistinguishable
in the db from "not ready". The unattended form is one `codex_id` per
invocation, driven from outside. MEASURED in `events` 2026-09-07: **32 trailer
runs exist and every one is the same book** (`20260822113400`); no second book
has ever been run past step 01. Everything below is a contract verified on a
corpus of one.

### What must exist before the command is run

The blind path is blind only about what it can CREATE. FIVE things it can only
READ, and it makes none of them — and **the one-book form checks none but
ffmpeg**: `books = argv or ready(conn)` (`trailer.py:105`), so a `codex_id` on
the command line skips the readiness query `db.py:238-243` calls "part of the
query, not a caller's courtesy check".

1. **`library/<book>/trailer/music/tone.json`, authored, Tone v2** — the 18
   required fields and their rules are `subskills/03-music` §10.
   `music_tone.load_tone` is the FIRST line of step 03's `run()` and raises on
   a book that has none: "absent is an error, not a default". No gate, no
   rung, no fallback — the run ends ~75 min in (shares 01+02+03) with no
   master. MEASURED 2026-09-06: of 30 books, **1 has a tone.json that loads**
   (Jekyll's is v1; `from_json` refuses it by the 14 fields it lacks).
2. **The local ComfyUI answering at `comfy.HOST`, AND six workflow files it
   does not serve.** `comfy.WORKFLOWS` and `COMFY_ROOT` — the second is where
   `stage_image` copies every reference PNG — are ABSOLUTE paths into the
   sibling comfy_studio tree and the portable engine, frozen at
   `studio/comfy.py:18-19` with no env var and no override: another machine
   reproduces both directories or edits those two lines. `load_workflow` globs
   `*/<name>.json` under the root and opens `<name>.manifest.json` beside it
   (`comfy.py:23-31`); the chain names SIX — `image_krea2_turbo_t2i` (02),
   `image_qwen3vl_caption` (the identity gate of 02 AND 07),
   `audio_minimax_music_3` (03), `audio_qwen3tts_design` and
   `audio_qwen3tts_clone` (05), `video_minimax_h3_r2v_turbo` (07). A missing
   file raises `FileNotFoundError`; a node class or checkpoint the engine lacks
   comes back as an HTTP 400 that `submit` re-raises as a `RuntimeError` and
   `down()` deliberately does NOT retry (`comfy.py:78, 94-107`) — an exception,
   so no rung catches it. `comfy._open` retries a DOWN engine for
   `RESTART_SECONDS` (600 s) then raises; the first render is step 02, so an
   engine that is not up costs ten minutes and step 01's spent LLM call. **One
   GET to `/queue` proves none of this.**
3. **ffmpeg on PATH** — the only one `trailer.py:preflight` checks (`TOOLS`),
   added after run 11 spent step 01's call and died in step 03 without it.
4. **`screenplay/feature/screenplay.json`, finished** — step 01's `run()`
   opens that exact path unguarded (`step_01_story.py:153`), and step 04's
   `scenes_of` and step 06's `inputs` open it again. MEASURED 2026-09-06:
   27 of the 30 books have one; `dracula`, `pride-and-prejudice` and
   `dubliners` die in step 01 with a bare `FileNotFoundError` seconds after
   `preflight` returned. Check the FILE, never the db: `ready()` reads
   EVENTS, and 27 books have the file against **1** with a
   `screenplay`/`05`/`completed` event, so the readiness query is not a proxy
   for it in either direction.
5. **`OPENAI_API_KEY`, in the environment or `.env`, `api.openai.com`
   reachable.** Every tier in `models.yaml` is `provider: openai`. Step 01's
   `attempt` is a bare `llm.structured` (`step_01_story.py:135`), and
   `_NativeStructuredCaller.__init__` reads the key through `llm._api_key`
   (`llm.py:131`) and raises; `structured` builds that caller OUTSIDE both
   retry loops (`:213`), so the raise is not retried. Without the key the run
   dies in step 01 seconds in, `story.json` never written and step 01's own
   `fallback` never reached (see "a ladder catches VERDICTS, not EXCEPTIONS").
   Not in `preflight`, and the only precondition that costs money.

**The rule `preflight` encodes and stops four items short of: anything the run
can only READ is checked before the run opens.** Until 1, 2, 4 and 5 stand
beside `TOOLS`, check them by hand: the screenplay parses and carries `scenes`,
the tone file loads as `Tone`, one GET to `comfy.HOST/queue` answers AND
`comfy.load_workflow` returns for all six ids, the key is set. The test that finds the NEXT one — for each `in:` row below, name the
earlier step whose `out:` cell writes that literal path; a row with no answer is
a precondition — finds only FILE preconditions. **2, 3 and 5 are a service, a
binary and a secret, and no `in:` cell names them.** The test that finds THOSE:
every external thing a step's `run()` touches without a guard — a bare `open`,
a host constant, `shutil.which`, an env var — is a precondition until
`preflight` asks for it. An unlisted precondition is where a fresh agent guesses.

## The control law

- **Ceiling 6 h wall-clock per book — CONSULTED, not enforced.** Unused share
  rolls forward, overruns are charged forward, and `Budget.remaining` may
  return a NEGATIVE number: step 02 logged −272.4, −287.5, −302.5 and −141.1 s
  and the run carried on. Nothing refuses to open a step — but the NEXT step
  pays. The first three of those rows are run `…20260904230747`, whose step 02
  ran 49.9 min against a 40-min share; thirteen minutes later step 03 of that
  same run fell to `onset_grid` at `remaining` 725.7 s against a 1081.9 s rung,
  and then step 07 dropped ZERO beats and the run finished at 232.0 min. **An
  overrun is paid by the step immediately after it, not by the picture** — so
  the place to look after a slow step is the next step's ladder, not the cut.
  The clock is read in
  two places only: `Climb.ask` when a ladder considers a RETRY (`attempts > 0`
  — the first try of every rung is unpriced BY DESIGN and by test,
  `test_the_first_try_still_runs_with_no_budget_for_a_retry`), and steps
  03/06/07's sizing.
- **`slack` is a 15-minute HOLE in the ceiling, not a buffer.** A share is
  spendable only by a step that calls `budget.start()` with its own name:
  `allowance` is `shares[step] * ceiling + carry`, and `carry` is the PREVIOUS
  step's balance, never a pool (`run_budget.py:37-47`). `RunContext.open_step`
  is the only caller and always passes a registry id 01–10, so `start("slack")`
  never runs; the string exists in `TRAILER_SHARES` and in
  `test_trailer_shares_sum_to_one_including_slack`, and nowhere else in
  `studio/`, `scripts/`, `tests/` or `trailer.py`. **Steps 01–10 can allocate
  at most 345 of the 360 minutes**, and the late step this table promises a
  rescue is rescued by nothing. MEASURED on Scarlet's 344 learnings: 30 climbs
  ended on `gate="budget"` (07: 21, 02: 5, 03: 4), and reconstructed against
  each run's start in `events` — `remaining` is `min(allowance − in_step,
  ceiling − elapsed)` — **30 of 30 were refused by the step's SHARE, none by
  the 6 h ceiling**, with 46 min to 5.4 h of wall clock still unspent. Run
  `…20260905063430` dropped **seven beats** at `remaining` 594 s against a
  660 s rung with 55 min left on the ceiling; step 03 threw a whole metre grid
  away for `onset_grid` at 961.594 against **961.752** — short **0.16 s** —
  five hours inside it. The arithmetic closes: 07's allowance was 12,600 s plus
  the 4,932 s steps 01–06 left behind, against 16,942 s in step, which is the
  594 within 4 s. **The ceiling has never refused anything; shares have
  refused 30 times, and 15 minutes sat unclaimable through every one.** Either
  delete the key and rescale the ten shares over 360, or make `allowance` add
  the unclaimed pool; until then size every step against **345**.
- **No blocking wait may outlive its step's share.** NOT ENFORCED — every
  wait's deadline is a module constant, not `budget.remaining(step)`:
  `comfy.QUEUE_SECONDS` 7200 s queuing plus `describe.TIMEOUT` 600 s is 130
  min inside ONE call, 3.25× step 02's whole 40-min share. Measured twice: run
  18, 11 h in step 02 (BUILD row 65), then again with that fix in place — six
  `02/identity/accepted_on_timeout` rows 130.1 min apart, 14:43 → 01:34 on
  2026-09-06, ~7 h in one 40-min step with no other step's row between. **A
  clock consulted BESIDE a blocking call instead of passed INTO it is not a
  budget**, and no ladder pricing repairs it. First thing to fix.
- **Every retry is an adapt, not a repeat.** The ladder changes the form
  (seed → alternate shot / next line / re-authored caption) and keeps the
  function (this beat, a hook, this register). Same seed twice is a bug.
- **The terminal rung is always reachable and never asks.** Voice → card;
  vocal → instrumental; lines → music-only; metre → onset grid; character →
  unbound; beat → dropped. A run cannot end without a master file unless a step
  crashes, and a crash is a bug to fix, not a gate.
  **A ladder catches VERDICTS, not EXCEPTIONS.** `climb` calls
  `attempt(*wanted)` with no `try` (`ladder.py:118`) and `settle` runs only
  after `gate(result)` has returned, so an attempt that RAISES skips both the
  rung and its learning: it leaves `climb`, leaves the step's `run()`, and
  `run_step` marks the step failed and re-raises (`trailer.py:77-82`). Every
  fallback listed above answers a bad ANSWER; none answers NO answer.
  MEASURED in `events`: **11 `failed` step rows across SIX steps** — 02 ×3,
  06 ×2, 07 ×2, 08 ×2, 03, 09. Steps 02, 07 and 09 each have a ladder, a gate
  and a fallback and each still ended a run with no master: 02 on a 600 s
  `StillRunning` and on `WinError 10061` (the engine down — precondition 2),
  09 on its own `REFUSED: delivered picture drifts 0.130s`. **A gate does not
  protect its step from raising**, and the
  word for the steps that kill runs is not "deterministic". The repair this
  repo has found converts the non-return into a VALUE at the call site —
  `describe.patiently` returns `unseen` instead of raising (BUILD row 65) —
  because a rung is reachable only from something that came back. Wrapping
  `attempt` in a `try` is no fix on its own: an exception carries no
  `measured`, so the only rung it could take is the terminal one.
  **That closure holds only PAST the preconditions above**: a missing or v1
  `tone.json` is not a gate with a rung, it is step 03's first line, and it
  ends the run with no master on 29 of the 30 books in the library today.
- **A crash is resumed by re-running the same command; the ceiling restarts
  with it.** Expensive artifacts are self-identifying, so a re-run pays only
  for what changed (step 07: `is_complete(dest) and is_current(dest, recipe)`;
  step 03: `cue_is_current`). **Never delete `trailer/main/` to start clean** —
  run 19's step 07 round measured 12,707 s of render, 3.5 h, all reusable.
  Two asymmetries. (a) `Budget` is built in `RunContext.__init__` from
  `time.monotonic()` and nothing persists elapsed time, so **the 6 h is per
  INVOCATION, not per book**: a book restarted three times has had eighteen
  hours, and a wrapper that retries must count restarts. (b) Step 02 reuses a
  sheet by PATH — `build_refs.generate` returns `dest` before rendering and
  never reads `prompt`, and `fresh` is False on the first try of the first
  rung — so editing a character's description and re-running returns identical
  pixels with no error. Delete the PNG, or nothing changes.
- **A floor is the list that BLOCKS; a miss that ships is a flag.** The floor
  is `QCReport.floor_pass` and nothing else — eight conditions: integrated
  −15.5..−12.5 LUFS, true peak ≤ −1.0 dBTP, `unbound_shots` 0, `reused_shots`
  0, `stale_shots` 0, every line clean (TP ≤ −3.0, no flat samples), a hard
  out, and no `CUE_FLOORS` miss (`section_changes_cut` 1.0,
  `cuts_inside_sustain` 0, `long_shots_on_sustains` 1.0, `lines_in_troughs`
  1.0). **`title_on_downbeat` is NOT in it** — `floor_pass` never reads it,
  `_grid_flags` does. And the floor does not block: after two free recuts step
  09's `ship_flagged` writes `shipped_flagged: true` and step 10 delivers
  anyway (`step_10_deliver.py` records `floor_pass` in the manifest and
  branches on nothing). MEASURED on the shipped Scarlet cut: `manifest.json`
  carries **`floor_pass: false`** — `cue_cut.cuts_inside_sustain` 3 against 0,
  `long_shots_on_sustains` 0.667 against 1.0 — with `shipped_flagged: true`,
  and it went out. The floor was MISSED and the file shipped; that is the whole
  claim, on the delivered file. **It bounds DAMAGE, not quality.**
- **The owner's "all I hear is music … no dialogues" is NOT
  `line_over_bed_lu`.** That target PASSED on the cut he rejected — 16.11,
  14.71, 8.52, 7.32 LU against a 5.0 floor, and `_line_flags` only fires BELOW
  it, so it was never in `flags`. His sentence is carried by three others, all
  flagged, none in the floor, all shipped: `music_only_fraction` 0.765 (target
  0.45), `longest_music_only_s` 21.0 (15.0), `speech_occupancy` 0.115
  (`speech_target` 0.30). Raising the lines over the bed moves no number that
  is failing; what is wrong is how much of the picture has no voice on it —
  `lines = min(slate, measured_slots)`, cap 4, against 27 cuts — **and on half
  the runs that ever delivered it is ALL of it.** Step 04's terminal rung
  `music_only` deletes the LAYER instead of changing its form, and the floor
  cannot see that: `unbound_shots`, `reused_shots` and `stale_shots` are floor
  conditions, the COUNT OF SPOKEN LINES is not, and `lines_are_clean` is
  `all(tp <= …) and all(flat == 0.0)` over the per-line lists
  (`trailer_stage_spec.py:325-328`) — vacuously TRUE at zero lines, so a master
  with no voice on it is a floor PASS. The path is silent end to end: step 05
  writes `voice.json` as `[]` and no learning at all
  (`step_05_voice.py:134-137`), and `assemble.spoken_lines` returns `[]`.
  MEASURED on Scarlet's 344 learnings: step 04's `slate` gate was climbed TEN
  times and EIGHT ended `music_only` — "no hook fits the first slot" ×4, "a
  hook with no threat or stakes after it" ×4 — and in **two of the four runs
  that ran the whole chain to `10 completed`** (`…20260904230747`,
  `…20260905063430`) step 05 opened and completed in **0.123 s and 0.041 s**,
  which is only the "nothing spoken; voice.json is empty" branch, with step 10
  delivering after it. `drop_story_rules` exists only from 2026-09-06 and both
  climbs that took it ended `music_only` anyway. **A rung must change the FORM
  and keep the FUNCTION; the rung step 04 is owed is the best lines the slate
  HAS, unlabelled.** Everything outside the floor is a number in `qc.json` and
  a name in `flags` (`QC_TARGETS`, 15 keys), and a flag cannot stop anything
  shipping.
- **Every rung taken writes a learning:** `{ts, step, substep, gate, measured,
  threshold, action, attempt, seconds, terminal, note, frames}` →
  `learnings.jsonl` + a WARNING line in the step's JSONL log; the step's
  `completed` event carries "N rung(s) taken" in its detail (the events
  vocabulary is fixed: started/completed/failed/skipped). `frames` is the
  sizing law's abscissa — one row per FRESH take on a `gate="cycle"` row; run
  19 wrote the first 22, and they move only `Cycle.a` (The sizing law). The
  retrospect reads this file, never memory.

## Time shares (minutes of the 360)

| step | share | what eats it |
|---|---|---|
| 01 story | 5 | one agent call |
| 02 refs | 40 | image renders, identity gate |
| 03 music | 30 | 4–8 seeds at ~2 min + tracking |
| 04 lines | 10 | Wikiquote + one labelling call |
| 05 voice | 15 | ≤ 4 speakers × ≤ 12 lines at ~10 s |
| 06 plan | 5 | code |
| 07 clips | 210 | takes, at `Cycle` seconds each — see The sizing law |
| 08 assemble | 10 | ffmpeg |
| 09 qc | 15 | track + scene-detect + ≤ 2 re-cuts |
| 10 deliver | 5 | Telegram |
| slack | 15 | **nobody's — no step ever claims it; see the control law** |

## The sizing law — frames are the currency, the clock is the till

Nothing here chooses a length by taste. `studio/frame_budget.py` is the one
conversion and every duration is downstream of it: **remaining seconds →
affordable frames → picture seconds → bars of cue.** A take renders its shot
plus `TAKE_TAX` (`HEAD_TRIM` 2.6 s + `HANDLE` 0.25 s) snapped UP onto H3's
ladder (f ≡ 5 mod 17, `MAX_FRAMES` 362, so `LONGEST_SHOT` is 12.2 s) and costs
`Cycle.a + Cycle.b × frames` seconds. Step 03 reads `budget.allowance("07")`,
subtracts one reader session, keeps `RETRY_RESERVE` (0.15) back for rerolls,
and asks the generator for exactly the bars that buys (`cue_seconds_for` →
`bars_for`) — **so a run that overruns step 02 gets a SHORTER cue, not a later
one.** Step 06 conforms the plan to the same number (`fit_to_frames`: a
shorter cue is an EDIT of the verified one, never a second render); step 07
prices every rung on the same `Cycle` (`ladder_for` → `retry_cost`).

**Every constant in that law is marked FLAG in the module** (`b = 2.49`
s/frame is one point on a curve the AICU figures call superlinear; `a = 0.0`
was never measured; `RETRY_RESERVE` and `CORPUS_MIX` are guesses).
`Cycle.from_rows` was meant to replace them from `gate="cycle"` learnings
carrying `frames`. **It can never replace `b`.** Run 19 wrote the first 22
such rows (2026-09-07T05:39:48, one per fresh take): the typed curve priced
each at exactly `2.49 × frames` and every one came in over — 12,706.9 s
measured against 10,179.1 s priced, **+25%** — and the miss GROWS with
length, the superlinearity `B_TYPED`'s own docstring predicts. Because the
truth is CONVEX and `Cycle` is AFFINE, least squares over those 22 points
returns **a = −80.1, b = 3.54** (−149.3 / 3.83 without B00, the round's first
take and a model load); `from_rows` discards any fit with `a < 0` and falls to
`typed_slope`, which keeps **`b = B_TYPED` by construction** and only reads an
offset off the medians (175 f / 514.75 s → **a = 79.0**).

**A cost model fitted with the wrong curvature cannot learn from its own rows;
it can only move its intercept.** The refit is exact at the medians and wrong
at both ends: 107 frames priced 345.4 s against 296.0 measured (**17% HIGH**),
362 frames priced 980.4 against 1319.3 (**35% LOW**). Not a scale factor to
divide out — a TILT that charges the long takes to the short ones. Where to
look when a cut ends abruptly: `can_afford` is `remaining >= cost`, so the
beat that fails it first is the most expensive one left, and the tilt
underprices exactly those — coverage dies at the sustains, not evenly across
the trailer. `b` is unreachable until `Cycle` carries a superlinear term or
refits `b` per frame band; that fix is a line of maths, not another run.
Changing a shot length, adding a motif or adding a step changes the cue's
length; say by how much.

## The ten steps — input → output → gate → ladder → fallback

Each row is the whole contract. Schemas live in `studio/trailer_spec.py`.
**Every `in:`/`out:` cell is a literal path written exactly as the code opens
it** — relative to `trailer/main/` unless it names the book dir — so the
precondition test above is a string match between the two columns and not a
memory. A cell marked *(optional)* has a reader that guards its absence.

**01 story** — in: `screenplay/feature/screenplay.json` (precondition 4).
out: `story.json`
(`StorySpec`: lead, figure, turn, resolution, restricted_scenes, narrator,
register, thesis). gate: lead in ≥ 25% of candidate scenes; register ∈ enum;
thesis ≤ 7 syllables, no proper noun, present tense. ladder: agent call ×3
with the violation quoted back. fallback: register `procedural`, thesis
`null` (vocal path off), narrator by first-person pronoun ratio.

**02 refs** — in: `story.json`, `analysis/characters/<char>.json` (unguarded
`load_json`; 30/30 books have it), cast cards (the book's own verbatim portrait
sentences first - `refs/portraits.json`, written on demand by
`portrait.portraits_for` from `source/chapters/`, blank Portraits if that is
absent - then `refs/canon.json`, the KNOWN LOOK, written by `canon.canons_for`
from `source/book.json`, absent metadata meaning no known look for anyone -
then the dossier, then the pool; a slot the book states outranks the
rotation). out: `refs/<char>.png`, `refs/refs.json` (a TRAIT CARD per character: age, hair colour/length, facial
hair, headgear, complexion, build, read by the local VLM `describe.py`;
plus `closest`/`differs` against the cast bound so far). gate: the sheet
differs from every bound character in ≥ `DISTINCT_AT` (3) seen traits -
the `refuse_collision` rule applied to pixels. A card seeing < 4 traits is
accepted `unverifiable`. The VLM is asked to DESCRIBE in a closed
vocabulary, never yes/no. A render is judged for FIDELITY first: a card
whose reading disobeys the BOOK'S words on a channel-reliable trait (hair
colour/length, facial hair, headgear - `distinguish.RELIABLE`; complexion,
build and age are dead on this channel, run 4: 7/7 sheets read fair/average)
fails `faithful`, not the collision gate. Only the slots the book filled
(`card["asserted"]`, plus a woman's beardlessness) are owed; a slot the
rotation invented to separate the cast is the render's to decide, and once
bound the card's text is rewritten to what was drawn (`distinguish.adopt`)
so take prompts agree with the sheet (run 7: Holmes unbound over invented
sandy hair under a bowler). The book fills a slot when it NAMES the object
and an attribute of it (`cast_card.OBJECT`/`BARE`: "a brown bowler" yes,
"as brown as a nut" no, "a hat" no kind), and its words are reserved for
the whole cast before any slot is invented. ladder: the first render, then
`distinguish` ×3 - a collision rewrites exactly the traits that matched, to
phrases no other character holds, and drops the book's sentence when it
asserted the moved trait; a disobedient render goes again AS WRITTEN on a
new seed. fallback: character `unbound` → every setup needing it is
excluded at 06.

**03 music** — in: `story.json` (register, thesis), `tone.json`. out:
`music/cue-<seed>.flac`, `music/metre.json` (`Metre` per seed: beats,
downbeats, bpm, bar, bars_in_mode, events, slots, fitness),
`music/cutmap-<seed>.json`, and **`music/plan.json` — the `CuePlan` whose
spans ARE the shot list**; steps 06 and 08 raise `FileNotFoundError` without
it. Its LENGTH is not a choice: `bars_of` asks for the bars the frame budget
affords (The sizing law).
gate: best fitness ≥ floor AND slots ≥ 1 AND bars_in_mode ≥ 0.65. ladder:
4 seeds → 4 more → re-author caption same register (swap pulse carrier) ×2.
fallback: best-of-all, `grid: onsets`, flagged `rubato`. Vocal path only if
thesis present AND register ∈ {elegy, gothic, romance, coming-of-age,
tragedy} AND stem gaps ≥ 2; else instrumental, no retry.

**04 lines** — in: pools (screenplay, character quotes, source quoted
speech, narration), `analysis/iconicity.json` *(optional — `load_iconicity`
returns `{}` and selection falls back to the text signals)*. out: `lines.json`
(`LineSlate`: ordered lines with speaker, function, kept, words, plus `pool`,
the labelled lines it did not use, so step 05 can swap;
`step_04_lines.py:376-383`). gate:
≥ 1 hook AND ≥ 1 threat-or-stakes; no line names the figure's identity.
ladder: label the next 10 ranked lines ×2 → `drop_story_rules` ×1 — the third
labelling is gated on the CONTRACT alone, because a slate that cannot satisfy
enough voices, an early hook and an open last word should lose those rules
before it ships silence. fallback: empty slate → music-only, flagged — TAKEN on 8 of 10 measured climbs,
and it deletes the layer rather than changing its form (control law); a master
with zero lines is a floor PASS. Wikiquote offline → last cached revid → `iconicity: thin`.
fit: each line is chosen for the slot it occupies, never `atempo`d; on the
rubato path a line may overrun its trough by one ducker release
(`DUCK_OVERRUN` 1.0 s) for at most `MAX_DUCKS` (2) lines — the bed ducks
under it for as long as it runs (08). On the metre grid the return downbeat
is never crossed.

**05 voice** — in: `lines.json`, `analysis/characters/<speaker>.json` (book
dir) *(optional — `load_card` returns `None` and that speaker takes the card
fallback, `step_05_voice.py:45-49`)*. out: `voice.json` (per slate
line: measured seconds, similarity — the file steps 06 and 08 open BY NAME),
`voice/refs/<speaker>.wav` (one designed reference per speaker),
`voice/lines/<NN>-<try>.wav`. gate: similarity ≥ 0.75. ladder: seed ×3 → next line with the same function. fallback: card.
Unattributed line → card without trying.

**06 plan** — in: `music/metre.json`, `music/plan.json`, `story.json`,
`lines.json`, `voice.json`, `refs/refs.json`,
`screenplay/feature/screenplay.json` (`step_06_plan.py:258-276, 396`).
out: `plan.json` (`TrailerPlan`: cut list in beats, setups
bound to refs, lines in slots). Setups = one per span, the spans folded to
what the frames afford (`fit_to_frames`; see The sizing law) — frames, not
takes. **A take plays ONCE.** `setups_for` returns the beats in TRAILER order
(world, then problem, then threat) and `trailer_order.one_each` plays them in
exactly that order; `TrailerPlan._one_take_per_shot` raises "B## plays twice:
one take, one shot" and the QC floor requires `reused_shots == 0`. So
`count != len(beats)` is a planning bug, not a spacing problem: the cue's
spans are fitted to the takes upstream, never the takes spread over the spans.
gate: no unbound setup;
lead ≥ 25% of beats. ladder: unbound → alternate setup in the same beat →
location-only shot. fallback: drop the unbound beats, refill the spans.

**07 clips** — in: `plan.json`, `refs/refs.json` (book dir) and the sheets it
names (`step_07_clips.py:470-471`). out: `clips/<setup>.mp4`,
`clips.json` (trait card per take, `similarity`, `differs`, `known`,
seconds). A take runs `max(CLIP_SECONDS, longest shot of the beat +
HEAD_TRIM)` (`build_clips.take_seconds`): the hold outruns MAX_SHOT by
design, and a take that cannot hold it starts the cut inside the reference
leak (run 6). gate: three frames after the head leak, laid side by side in ONE
contact sheet (the VQA node reads only image[0] of a batch) and described by
the VLM into one card, differ from the reference card in < `DISTINCT_AT` (3)
traits; a card seeing < 4 traits is accepted `unverifiable` and flagged.
ladder: seed ×1 → whole-take close-up ×1 (a seed moves the reading about
half a trait: B12 read 4.0 then 3.5 in run 6), each rung priced at
`retry_cost(frames, cycle)` = `cycle.cost_seconds(frames) + SESSION_SECONDS`
so a retry may cost this beat but never a later beat's first render
(`ladder_for`); terminal:
the BEST take capped at 0.6 s. A beat is dropped only when no take exists:
`can_afford(STEP_ID, retry_cost)` false before its first render, or the render
failed. Every take is kept under `clips/takes/`.

**08 assemble** — in: `plan.json`, `clips.json`, `clips/<setup>.mp4`,
`music/plan.json`, the cue at `plan["music"]["rel_path"]` (book dir),
`voice.json` *(optional — `spoken_lines` returns `[]` and the master ships with
no voice on it)*. out: `TRAILER-*.mp4`. gate: none — an
exception is a bug. Not "here only": `run_step` catches at EVERY step, marks it
failed and re-raises; 08 is merely the step with no gate that could have
returned a verdict first (it has 2 of the 11 `failed` rows all the same).

**09 qc** — in: the master, `plan.json`, `metre.json`. out: `qc.json` (every
`QC_TARGETS` measurement, `flags`, `floor_pass`). gate: `QCReport.floor_pass`
(the eight conditions above); targets are `QC_TARGETS` in
`studio/trailer_stage_spec.py` — the one list, never copied here. Whole-trailer
`cuts_on_beat ≥ 0.80` is RETIRED: it is the single target that FORCED a music
video (76% of run 10's cuts on the beat, whole-bar lengths, and a viewer
starts counting within four shots), and `cuts_on_beat_act1` and
`on_cap_fraction` went with the walk that graded them (BUILD rows 54, 55).
Only `cuts_on_beat_act3` survives — a locked third act is what an act break
sounds like. Re-adding the whole-trailer target re-forces the music video.
ladder: re-cut ×2, free. fallback: `ship_flagged` — misses under `flags`,
`shipped_flagged: true`, and step 10 delivers it.

**10 deliver** — in: master, `qc.json`, `learnings.jsonl`. out:
`manifest.json`, Telegram message with the file and the flags. The file
sent is the master when it is ≤ 50 MiB (the Bot API cap) and otherwise a
CRF-20 copy at `work/telegram.mp4` (`deliverable`; run 6b's master was 45 KB
over and died with a bare TLS EOF ×3). ladder: send ×3. fallback: file
stays in the library; manifest records `undelivered`.

## What the model is allowed to decide

FIVE kinds of `llm.structured(tier, prompt, Schema)` call, each with a
`FakeModel` in tests: (1) register + thesis + narrator, step 01; (2) the
book's own portrait sentences, `studio/portrait.py`, once PER CHARACTER in
step 02; (3) the music caption from `tone.json`, step 03; (4) line function
labels, step 04; (5) **the look the world already knows a character by**,
`studio/canon.py`, tier `canon` — the only tier at `reasoning_effort: high` —
asked `ASKS = 3` times PER CHARACTER inside step 02 (`step_02_refs.py:66`) and
settled by majority reading (`agree`). **Steps 05–10 contain no
`llm.structured` call at all** — voice instructs and shot prompts are templates
filled from typed fields and the screenplay's authored shots. Every call is
gated by code and retried with the violation quoted. Nothing else is judgment.

**(5) is the highest-judgment call in the chain** — the model recalls a face
from OUTSIDE the book — and it fills the trait card, so it decides Brick 1.
It has two properties nothing else here has. `_one` swallows EVERY exception
and returns an empty `Canon()`, writing no learning (`canon.py:106-111`); and
`canons_for` caches that empty answer to `refs/canon.json` and never re-asks,
`if char_id not in kept` being the only freshness test (`:125-138`). **One
unreachable API during step 02 therefore makes every face in that book an
invention — permanently, silently, and invisibly to the retrospect**, which is
the defect run 7 produced (the book silent on Holmes, the rotation giving him
a bowler and forty years, the identity gate passing because the card WAS the
invention). To re-ask, delete `refs/canon.json`; nothing else will. Test for it
without a render: `known: false` on a character the world plainly knows —
Scarlet's file holds 7 characters, 5 `known`.

**These calls are the run's only money.** MEASURED in `usage` 2026-09-06: 83
calls billed to stage `trailer`, **$0.0242** (01: 33, 03: 19, 04: 31). Step 02
shows zero, and tier `canon` has no row in the whole 12,478-row table, only
because Scarlet's two ref caches were already written. A NEW book pays one
portrait call plus three high-effort canon asks per character (`models.yaml`:
~$0.02 a character) — see precondition 5.

## What the retrospect reads

`learnings.jsonl` across every book, grouped by `(step, gate)`. **The file is
CUMULATIVE per book and `Learning` carries no run id** — Scarlet's file held
344 rows on 2026-09-06, spanning 09-04 to 09-07 over roughly ten runs, and
grows while a run is live — so `by_gate` counts every run as one and
`Cycle.from_rows` prices this run off every earlier run's
takes. Read a date range, not a file, until a `run` field exists.
**The manifest has the same defect and it is the DELIVERED one.**
`step_10_deliver.manifest` embeds the whole file (`:96`) and counts it:
Scarlet's `manifest.json` carries all 344 rows, 09-04 → 09-07, and
`rungs_by_step` sums to 344 with `02: 168` — presented as one run's — and
`caption_for` sends those numbers to Telegram. One file, two time bases:
`qc` and `flags` are THIS run, `learnings` and `rungs_by_step` are every run of
this book, so the counts can only grow and "did the fix reduce the rerolls?"
cannot be asked of them. The run id exists (`ctx.tracker.run_id`) and is simply
not written onto the row. A gate
that fails on most books is mis-set or the step upstream is wrong; a rung
that is always taken should become the first rung. That is how the skill
improves: numbers from runs, edited by a person or an agent, tested before
merge. The run itself never edits the skill.
