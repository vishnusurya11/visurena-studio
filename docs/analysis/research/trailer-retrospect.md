# Trailer blind path — retrospect

One entry per unattended run. Each names what the run measured, what broke,
what changed in code (with its test), and what is still open. A retrospect
item is closed only by a test that fails on the old behaviour.

## Run 6 — A Study in Scarlet, 2026-09-04 17:20–22:29 UTC

**Outcome:** no master from the run itself — step 08 crashed. Run 6b
(23:00 UTC, the same 14 takes with B09 re-rendered long enough for the
hold) delivered: 136.33 s, drift +0.003 s, 64 cuts, 45% on beat (onset
grid; baseline 12/35 = 34%), 0% on downbeat, 53% on L0, −14.0 LUFS,
−1.8 dBTP, floor pass, flags `cuts_on_beat, cuts_on_downbeat, cuts_on_L0,
title_on_downbeat`. Sent to Telegram by hand as a 39 MB copy (defect 4).

**What the run did**

| step | rungs | result |
|---|---|---|
| 01 story | 1 (thesis 8 syllables → agent_call) | passed |
| 02 refs | 10 identity rungs; Hope and Holmes UNBOUND | cards were rotation-invented (fixed before this run finished: book-first portraits, `9887c67`) |
| 03 music | 4 → terminal `onset_grid` | fitness 9.2 with 2 slots on seed 1002; the gate `metre AND slots` has never been jointly satisfiable |
| 04 lines | 2 → `music_only` | no hook fits the first slot (fixed before this run finished: `DUCK_OVERRUN`) |
| 06 plan | 2 (19 unbound → 7 unbound → pass) | 22 setups, 58 shots, 0 line windows |
| 07 clips | B12: identity 4.0 → reroll, 3.5 → reroll, bound on take 3; B14–B21 dropped on budget | 14 takes, all bound to the Holmes sheet, similarity ≥ 0.75 |
| 08 assemble | — | **crash**: ffmpeg concat could not open `work/library/.../work/s000.mp4` |

**Defects found, all reproduced by a test**

1. `trailer_assemble.concat` wrote segment paths verbatim into the concat
   list; ffmpeg resolves a relative entry against the LIST FILE's directory,
   so a repo-relative `book_dir` (what the blind path passes) doubled the
   path. Three shipped trailers came from absolute dirs and never hit it.
   Fix: `listing_lines` writes every entry relative to the listing
   (`test_entries_are_relative_to_the_listing_not_the_cwd`).
2. Every take rendered at `CLIP_SECONDS = 7.0` (175 frames, 7.29 s). The
   plan's final hold asked 7.667 s of B09; the hold is exempt from
   `MAX_SHOT` by design. `extract` ran off the end (7.25 s delivered),
   `segment_start` fell back to 0.0 — inside the 2.6 s reference leak — and
   the drift gate refused the picture at 0.423 s. `need_seconds` existed in
   step 07 for exactly this and was never called, and used the 1.0 s
   identity-frame leak instead of the 2.6 s cut trim. Fix:
   `build_clips.take_seconds` = max(`CLIP_SECONDS`, longest shot +
   `HEAD_TRIM`), wired into `take_values` so the recipe changes only for the
   beats that need it (`test_a_take_holds_its_longest_shot_past_the_head_trim`).
   Cost: the hold beat renders 260 frames (~16 min) instead of 175.
3. All 31 learnings carried `seconds: 0.0`. `climb` never timed an attempt,
   so the budget rung's `cost_seconds` (a 660 s guess) had nothing to
   calibrate against. Fix: every rung learning records the attempt's cost
   from the budget clock (`test_every_learning_carries_what_its_attempt_cost`).
4. Run 6b's master (14 takes, 52,473,989 bytes) was 45 KB over the Telegram
   Bot API's 50 MiB cap; three sends died with `EOF occurred in violation
   of protocol` and step 10 went `undelivered`. A CRF-20 copy (39 MB) went
   through first time. Fix: `deliverable` sends the master when it fits and
   a shrunk copy otherwise; the manifest names the file sent
   (`test_a_master_over_the_bot_limit_sends_a_shrunk_copy`).
5. Learnings written by step 07 in this run have an empty `substep`: the
   process loaded the code before `fe87828` landed. Not a new defect;
   noted so the run-6 rows are not read as a regression.

**Measured, still open**

- Identity reroll is the wrong rung for a small distance. B12 read 4.0
  then 3.5 against `DISTINCT_AT` 3 on two seeds: the seed moved it half a
  trait. Two rerolls cost 33 min — three beats' worth — before the third
  seed bound. CLOSED 2026-09-04: the ladder now climbs to `alternate_setup`
  (a framing the reader can see the face in) after ONE reroll
  (`test_a_face_that_never_binds_ships_its_best_take_short`). Admitting a
  take within one notch when the beat has no line stays open until run 7
  measures how often the close-up binds.
- Step 03's gate has never passed. Measured over the 16 Scarlet seeds:
  every metre-grid seed scores `title_term` 0.3 and `slot_term` 0.4 (the
  struck-pulse captions produce no pre-title trough and no slot); the one
  seed with both (1002, fitness 9.2) reads `bars_in_mode` 0.43. The fix is
  upstream — a caption/section sheet the generator obeys, or a tracker that
  reports beat regularity beside downbeat regularity — not a lower floor.
  MEASURED 2026-09-05, all 16 seeds re-tracked on CPU: (1) the troughs are
  not what breaks the metre — bars-in-mode outside the stopdowns/slots is
  within 0.02 of the whole-cue figure on every seed; (2) four seeds held a
  steady BEAT for 40–58 s (beats-in-mode 0.89–0.96) and were graded rubato
  because the downbeat tracker alternated two- and four-beat bars
  ({2: 29, 4: 31}) — `Grid.of` now re-votes the downbeats every modal bar
  along the beat when the beat is steady (`beatmap.rebar`, `TestRebar`):
  metre seeds 6 → 9 of 16, the shipped seed unchanged; (3) the generator
  DOES obey the Outro — seven seeds put a stop before a late hit — but the
  caption asked for "one beat of silence" and `title_term` grades a bar
  (2001: 1.5 s against 3.0 s), and one seed landed the hit at 99%, past the
  95% the title moment accepts; the sheet and caption now ask for two full
  bars of silence, the impact, and an eight-second decay
  (`test_the_closing_section_asks_for_what_the_gate_grades`); (4) three of
  the five metric seeds read 175–201 BPM against 84 asked because the
  caption said "the pulse doubles" — it now holds the tempo and doubles the
  subdivision. (5) FIXED 2026-09-05: the fitness floor of 6 is carried by
  dynamic range, so the rubato seed with a title moment (1002, 9.2) outranked
  every metric seed (best 2.4) and `best_of` SHIPPED it -- the delivered
  run-7 trailer cut on the onset grid with 0% of cuts on a downbeat.
  `best_of` now ranks on what the gate grades before fitness: a metric grid,
  then a slot, then fitness (`test_best_of_ranks_on_what_the_gate_grades_
  before_fitness`). Still open: whether the floor itself should weigh the
  metric term more -- measure on run 7c's seeds under the new caption.
- The identity gate among men has five live traits (figure, complexion,
  build are shared on every "shares" list). Run 7 measures the unbound
  count under book-first cards before any threshold moves.
- Budget: step 06 caps setups at what 07's share affords with ONE take in
  reserve (262 min → 22 setups). B12's two rerolls spent three takes, so
  the reserve covered one and eight beats went unrendered — not because
  of the reroll alone: step 07's share was measured from the run's start
  and steps 02–06 had already used 48 min of it. Fixed the same night:
  `ladder_for` prices every retry rung at `660 × (beats_left + 1)`, so a
  retry that would cost a later beat's first render goes terminal instead
  (best take, capped) and the beat is kept
  (`test_a_retry_never_spends_a_later_beats_first_render`).
- `describe.TIMEOUT` includes ComfyUI queue wait, so a VLM read behind a
  render times out for the render's reason. CLOSED 2026-09-05:
  `comfy.wait_record` polls `/queue` and starts the clock when the job
  leaves `queue_pending` (`QUEUE_SECONDS` caps the wait in line).
- Holmes's hair and facial hair are still invented when the book is
  silent; the card should say "unspecified" and let the render decide, so
  the fidelity gate does not enforce an invention. CLOSED 2026-09-04, the
  hard way: run 7's first launch spent 20 min refusing four Holmes sheets
  for `hair_colour` (dark hair under a bowler; the card said "receding
  sandy hair") and unbound the lead. The invention stays on the card (the
  cast must still be told apart in the prompt) but only `asserted` slots
  are owed, and the bound card's text follows the render
  (`test_an_invented_slot_the_render_reinterprets_binds_and_the_card_follows`).
  Measured on the way: a sheet render + read costs 286 s, not the 90 s the
  rung was priced at (step 02's `RENDER_SECONDS`/`DESCRIBE_SECONDS`; now
  180 + 110, `TestRungPrice`; the old run's budget went to -300 s three
  times while it believed 90). And
  rebuilding the five Scarlet cards offline found the generator of the
  over-assertion: `book_match` matched adjectives ("brown as a nut" -> a
  brown bowler hat; "long rifle" -> long black hair; "tall" -> a tall beaver
  hat on two men; "felt long-forgotten" -> a felt hat), each then owed by
  the render. It now needs the object named plus one attribute
  (`TestBookNamesTheObject`); stated values are reserved cast-wide before
  invention; a woman's age reads "in her"; women get bonnets, not top hats.
  After the fix the five cards share nothing in Tier One and only
  clean-shaven between Hope and Lucy.
- One sheet per beat. `build_plan.beat_of` casts ONE principal, `h3_prompt`
  declares <Subject 1> = that person and <Subject 2> = the place, and step 07
  measures one face. The delivered run-6b trailer shows the cost: all 14
  takes referenced the Holmes sheet, and the Watson who appears in B05/B09/
  B11/B13 is prompt-only -- a different clean-shaven man each time. H3's
  workflow takes two reference slots, so a two-person beat could bind
  Holmes + Watson and carry the place by prompt (locations were measured
  as `attribute_transfer` anyway). Needs the GPU: render B05 with
  (a) Holmes + place and (b) Holmes + Watson over three seeds and read BOTH
  faces -- `describe_frames` returns one card, so the read must name which
  person it describes ("the man in the bowler" / "the man with the
  moustache"). Do not build the two-subject path before that A/B says H3
  keeps two faces apart rather than blending them.
  BUILT 2026-09-05 (unmeasured): `scripts/trailer/two_subject_ab.py` renders
  a beat both ways over the same seeds and reads each expected face by its
  own sheet's cue (`describe.prompt_for(whom=...)`).  `take_values` now turns
  two bound cast members into <Subject 1> and <Subject 2> (`h3_prompt.build
  (second=...)`); the blind path is unchanged because `beat_of` still casts
  one principal.  Run after run 7: `uv run python -m scripts.trailer.
  two_subject_ab 20260822113400 --beat B05 --second john_watson --seeds 3`.
- CLOSED 2026-09-05: `identity.py` and `identity_gate.py` retired with their
  tests and the `qc` group's OpenCV/onnxruntime pins; only `frame_times` /
  `frame_at` were still used (step 07) and now live in `studio/frames.py`.
  FP8 Qwen3-VL and moving it to NVMe are user-side.

## Run 7 — A Study in Scarlet, 2026-09-05, stopped at step 07

Stopped by hand once the character sheets were looked at: the Holmes sheet
was a man of forty with a walrus moustache under a brown bowler; run 6's
had been white hair worn long. The owner's question — "did you do any DQ?"
— has a plain answer: no. The identity gate compared each render to its
own card, and the card was the thing that was wrong. A gate that checks a
render against an invention passes the invention.

**What generated it.** `cast_card` is built on "a model draws OBJECTS;
invent only where the book is silent", and the book is silent about
Holmes's face because in 1887 nobody needed telling. The rotation filled
the empty slots — hair, facial hair, headgear, age — from the pool, and
each run's rotation landed on a different man. The portrait prompt
forbids canon on purpose ("never infer from period or reputation"), which
is right for a book's own words and wrong as the whole of the authority.
Silence in the text is not licence when the audience knows the face.

**What changed** (each with its test, `tests/test_canon.py`,
`tests/test_cast_card.py`, `tests/test_step_02_refs.py`,
`tests/test_distinguish.py`):

- `studio/canon.py`: a known-look rung between the book's words and
  invention. Asked in the card's closed vocabulary, at the time of this
  book, with `known=false` permitted; cached in `refs/canon.json`. Its
  slots are `asserted`, so the render OWES them — a bearded Holmes is
  refused, not shipped. Authority order now: book's own words > known
  look > role costume > rotation.
- Agreement, not an answer: `ASKS = 3`, each slot kept by majority
  READING, `known` by majority; a slot the asks disagree on is empty.
  Measured first at luna `reasoning_effort: none`: Watson came back a
  short pointed beard / nothing / a thin waxed moustache (guessing), and on
  a second round the three asks AGREED on a pointed beard, receding sandy
  hair and forty-five — confidently wrong. At `high`: late twenties, a
  moustache, sun-darkened, three of three. Recall of a face needs the
  thinking, so models.yaml has a `canon` tier (luna, `reasoning_effort:
  high`; same priced model, ~5k output tokens an ask, ≈$0.02 a character,
  ≈$0.13 a book, once). Not a frontier model: none has a confirmed rate
  in models.yaml and nothing is priced from memory.
- `cast_card.IDENTITY = ("facial_hair", "hair")`: on a known face these
  are never invented, only `neutral` — clean-shaven, and the plainest hair
  of the band nobody else has (BANDED hair reordered plainest-first; long
  black hair on Watson is not nothing added). Not asserted: a proven
  collision may still move them.
- `cast_card.alike`: what is taken is what the reader would call the same.
  A thin waxed moustache and a heavy walrus moustache are two phrases and
  one reading ("moustache"); handing the second to the next character was
  handing out a collision the sheet gate then had to catch on the GPU.
- `distinguish` never moves an asserted slot ("two people the book makes
  alike stay alike"); `movable` lists what a rung may still move, and when
  nothing is movable the sheet binds `accepted_as_written` with a learning
  — the book made them alike, and a faithful sheet beats an unbound lead.
- FACIAL_HAIR pool reordered least-added first, so `_move` off clean-shaven
  reaches a moustache before a full dark beard.

**Measured after the fix** (Scarlet cards, canon tier): Holmes — late
twenties, dark hair swept back, clean-shaven, pale, tall and lean,
deerstalker; Watson — late twenties, moustache, brown as a nut (book),
thin as a lath (book), sturdy neutral hair; Lestrade, Gregson — known only
for build/complexion, the book's words carry the rest; Ferrier, Lucy —
unknown, invented as before.

**Still open.**
- Jefferson Hope's card mixes two eras: the book's "tall, savage-looking
  young fellow" (Utah, ~1860) sets his age to early twenties, while the
  canon's long untrimmed beard and lined sunburnt face are the London
  cabman of 1881. The portrait step should prefer the sentences of the
  era the trailer's beats use; a character with two looks needs two cards
  or a timeline, not one blend.
- The known look is asked of the model that also wrote the analysis. A
  frontier `judge` tier is the owner's stated preference and needs an
  owner-confirmed rate before it exists.
- No sheet is yet compared to anything but its card. The card is now
  worth obeying; a second, independent read ("is this Sherlock Holmes?")
  against the canon text would close the loop the owner asked about.

## Run 8 — A Study in Scarlet, 2026-09-05, step 02 only

The fixed cards rendered; the FINAL sheets did not match them. Lestrade's
sheet: about seventy, white hair worn long, a full dark beard, top hat.
Watson's: fifty, grey hair. Holmes, Hope, Lucy: as carded.

**Not a stale read.** The Qwen trait reads were re-checked against the
final PNGs and are accurate. The sheets were wrong because the ladder
made them so.

**Generator.** Two rules, each right on its own, compounding:
1. `distinguish._move` walks the pool to the NEXT phrase that reads
   differently, with no notion of how far it has moved the person. Lestrade
   read as Watson on hair colour and length, facial hair and build; the
   rung took him from "thinning red hair" to "white hair worn long", from
   clean-shaven past two moustaches to "a full dark beard", and (on the
   next try, age now matched) from thirty-five to seventy.
2. The gate rewards drift. Watson's first render drew dark hair on "fair
   hair parted in the middle" and read as Holmes; the reroll drew GREY,
   which read as three traits from Holmes, and bound. The `adopt` step
   then rewrote his card to "close-cropped grey hair" so the clip prompts
   would agree with the sheet: the pipeline rationalised the drift
   instead of refusing it. Run 6's white-haired Holmes was the same
   mechanism one character earlier.

**Fixed (test-first).**
- `distinguish.movable` and `distinguish` move only RELIABLE traits (hair
  colour, hair length, facial hair, headgear) on unasserted slots. Age,
  complexion and build are read off a sheet but not expressed by it
  (run 4: age followed the hair colour, build read 'average' 7/7); moving
  them changes the person and not the reading. Build no longer moves.
- On a known face (`canon.known`) the IDENTITY slots — facial hair and
  hair — are listed as `neutral` on the card, a third category beside
  asserted and free. No rung moves them. A known face that reads like
  another known face binds `accepted_as_written`, as two people the book
  makes alike do.

**Second pass (same day).** The first fix ASSERTED the neutral slots, and
the rerun refused three good Watsons in a row: `disobeyed hair_colour`,
brown drawn on "fair hair parted in the middle". The sheet at the third
refusal was a correct Watson — about thirty, brown hair, moustache, brown
bowler. Nobody had said fair; `neutral()` had, as the plainest hair
nobody else had taken. A neutral phrase is a placeholder, and owing a
placeholder as a fact refuses the man for the placeholder's sake.

The rule that fits both failures: a neutral slot is owed as NOTHING
ADDED. `distinguish.ADDED` names what a render adds to a young face —
grey, white, bald, long, any facial hair on clean-shaven — and
`disobeyed` refuses a neutral slot only for those; brown on fair is
adopted (`adopt` still rewrites unasserted slots to what was drawn, so
the clip prompts say brown). Lestrade's seventy-white-bearded and
Watson's grey are still refused; Watson's brown is bound. The card
carries `neutral` next to `asserted` so `movable` excludes both.

**Also measured.** Step 02's 40-minute share is thin: 7 sheets at 290 s
first-try is 34 min, one reroll is 5 min. Ferrier and Gregson went
unbound on budget in run 8 after each one reroll. Not changed yet —
the fixes above remove the rerolls the ladder was causing itself.

## Run 9 — A Study in Scarlet, 2026-09-05, delivered and rejected

**Outcome:** a master was delivered (132 s, 78 cuts, 87% on beat, 31% on
downbeat, −14.3 LUFS, −1.19 dBTP, 0 unbound shots, floor pass, one flag)
and the owner's read of it was the whole review: *"all I hear is music too
loud, not at all matching tone, it is just some random music, no
dialogues."* Every number above was true and none of them measured what
was heard. Four causes, each fixed test-first, none needing a render to
reproduce.

**What the run did**

| step | rungs | result |
|---|---|---|
| 02 refs | reroll/distinguish chains; five `accepted_as_written` pairs | 7 sheets |
| 03 music | `first_seeds` (fitness 1.0, metre, 0 slots) → `four_more_seeds` (4.4, metre, 4 slots) → `reauthor_caption` ×2 → terminal `onset_grid` | seed 2003: 177.8 BPM in three against 84 asked, 132.1 s, four troughs of 1.25–2.4 s |
| 04 lines | `relabel_next_10` ×2 ("no hook fits the first slot") → terminal `music_only` | no line, fourth run running |
| 06 plan | 21 unbound → 6 unbound → plates | 25 beats: 19 Holmes, 6 empty plates (every Utah beat); scenes 4, 8, 21 carry 18 of 25 |
| 07 clips | 7× `drop_beat` on budget | 18 takes |
| 08–10 | — | master, QC, Telegram |

**Cause 1 — no dialogue.** `fits` refused every hook at the trough's edge:
the longest trough held five beats at 177.8 BPM, 1.7 s under the fit rule,
and the shortest hook ran 2.5 s. The refusal quoted to the labeller was
"no hook fits the first slot", which names nothing a label can change, so
the labeller relabelled the same lines and the ladder ended `music_only`.
Fixed: a line lives in a window, FOUND (a trough) or MADE (a phrase of the
grid the mix ducks under it); roles aim at an even share of the span and
take the nearest window that holds them; a refusal says "the shortest hook
takes 3.3 s, the longest window holds 1.7 s; label shorter lines as hook";
the sheets the labeller applied are kept at `work/labels-N.json`. Run 9's
own pool on run 9's own cue now places two lines
(`test_the_run_9_slate_is_not_music_only`). Commit `6d8ecb7`.

**Cause 2 — random music.** Step 03 asked for 84 BPM and shipped 177.8:
nothing compared the measured tempo to the asked one. `best_of` ranked
metre, slots, fitness — and 2003 was the only seed with slots. Fixed: the
gate is a metric grid within one tempo mark (15%) of the asked BPM;
`best_of` ranks in the gate's order; `FITNESS_FLOOR` and the slot criterion
are gone; `reauthor` keeps register AND tempo; the terminal rung ships the
best seed and warns OFF TONE. Replayed on the 16 real seeds: 3004 at 100.9
BPM is picked over 2003, no seed is within 15% of 84, and the ladder
reauthors. Commit `f62c673`.

**Cause 3 — too loud.** The bed was normalised to −14 LUFS and no line was
set against it; a take rode at the voice model's level, and a quiet one did
not even key the duck. Fixed: `level_lines` sets each take 8 LU over the
bed under its own window before the duck, bounded ±20 dB; the levelled
takes are the sidechain's keys. Verified on real ffmpeg with takes 30 dB
under and 18 dB over the bed. Commit `f0f4745`.

**Cause 4 — one man in one room.** `unbound` refused a beat if ANY face in
the scene's cast lacked a sheet, and `alternates` drew only from scenes
where everyone was sheeted. Every Utah scene holds `group_mormons` or an
unnamed hunter, so Hope's close-ups were refused, plated, and shipped as
empty desert while his sheet went unused; the plan was 19 Holmes beats
and 6 plates. Fixed: a setup carries `subjects`, the people its own prose
names from the scene cast (`subjects_of`); `beat_of`, `unbound` and
`alternates` bind on the frame. Same 18 setups offline: 15 refused under
the old rule, 6 under the new, all six substituted with sheeted spares,
Utah bound on Hope and Ferrier, lead share 61%.

**What the QC did not measure.** `line_over_bed_lu` has a target (5 LU)
and had never been filled: `report()` left it empty. Fixed: the mix
writes `lines.level.json` beside the master and `qc.line_over_bed` reads
each levelled take against the ducked bed under its window; a master with
no lines measures nothing rather than passing. Tempo against the asked BPM
was not a QC field either; it is now the step 03 gate.

**Open.** An independent "is this Sherlock?" read on the sheets;
`same_look` across gender; step 02's 40-minute share (Ferrier and Gregson
went to `accepted_as_written`); a bare shared surname credits every sharer
(`addressing Ferrier` binds Lucy too — harmless while both are sheeted);
two-subject binding stays an A/B; no run has yet cut through all four
fixes.

## Run 10 — A Study in Scarlet, 2026-09-05 12:18–17:35 UTC, delivered

The first run through all four run-9 fixes (dialogue windows, tempo gate,
line levelling, subject binding). Launched once as a tracked background
process; step 10 delivered the master, `qc.json` and the caption to
Telegram itself. Nothing was spent but GPU wall-clock: three LLM calls on
`gpt-5.6-luna` (step 01 story 425/33 tokens, step 03 reauthor 338/68, step
04 label 744/219) — $0.0007 by the ledger; MiniMax Music 3, MiniMax-H3 and
Qwen3-TTS on the local ComfyUI.

| step | what happened | rungs |
|---|---|---|
| 02 | five `accepted_as_written` pairs (Watson~Holmes, Lestrade~Holmes, Ferrier~Hope, Lucy~Lestrade, Gregson~Lestrade), all under the 3.0 threshold | — |
| 03 | 115 BPM against 84 asked on the first two batches; `reauthor` held the register and the tempo; seed 3002 at 92.5 BPM (band 1) shipped, not `best_seed` | first_seeds → four_more_seeds → reauthor |
| 04 | three lines placed in windows; not `music_only` for the first time since run 7 | one relabel |
| 06 | 8 unbound, lead 43% → 0 unbound, lead ≥ 25%; Utah bound on Hope and Ferrier; 25 setups, 51 shots | select_setups |
| 07 | 19 takes in ~4 h 56 min (12:36 → 17:32); B19–B24 dropped with 52 s of the 660 s budget left | drop_beat ×6 |
| 08–10 | mixed, graded, titled, QC'd, delivered with 4 flags | — |

**Heard vs measured.** I cannot listen; the numbers are the ear. The one
spoken line rides 9.92 LU over the ducked bed under its window (target 5,
so audible — the run-9 complaint "music too loud" cannot recur on that
line). Integrated −14.16 LUFS, true peak −1.43. Whether 92.5 BPM at the
reauthored caption reads as the register asked is the owner's call.

**Cause 5 — one of three spoken.** Two of the three placed lines had no
speaker and shipped as text cards. `role_candidates` ranked two speakerless
source quotes over Watson's spoken line because `shares_content_word`
related them to "You HAVE been in Afghanistan" on the auxiliary alone.
Fixed: a spoken line outranks a card at every role after the hook, and
`FUNCTION_WORDS` are not content. Replayed on run 10's own labels: hook
Holmes and answer Watson both spoken; the threat is still a card because
the 24-row sheet holds no spoken threat at all.

**Cause 6 — QC graded the wrong grid.** The delivered `qc.json` read 75% on
beat, 27% on downbeat. The walk cuts on every L0 event and the tracker puts
hits and stopdowns between beats; 8 of the 13 "off" cuts sat on one, and
the intro shot and the tail card had no pulse under them. Fixed: `on_music`
and `graded`. Re-measured on the same master: 52 cuts, 0.90 on the music,
0.43 on a downbeat or L0, `cuts_on_L0` 0.53, on-cap 0.02, floor pass.

**Open.**
- Spoken threat supply: the source pool's attribution (tag + sibling rules,
  neither firing → card) is conservative by design and leaves most Holmes
  lines speakerless. A labeller-guessed speaker was considered and rejected
  — a guess from memory puts the wrong voice on a line. The honest fix is
  more attribution rules in the pool, tested against the book.
- `cuts_on_L0` 0.53: the stutter stopdowns at 11.5–13.9 s are 0.5 s apart
  and `MIN_SHOT` cannot take them all; either the target admits a cluster
  or the walk treats a stutter as one event.
- `title_on_downbeat`: the card lands at the cue's end (102.08 s ≈ 101.95),
  where no downbeat falls; the walk should place the title on the last
  downbeat, not the last sample.
- Step 07 at ~5 h for 19 takes, 6 dropped, is the whole budget. The
  banner read "−199 min left" at step 08: it was printed before the step
  opened, so 07's five hours were charged against 08's ten minutes. The
  gates inside the steps read the right clock; only the banner lied. Fixed
  in `run_step` (`test_the_banner_reads_the_budget_of_the_step_it_opens`).
- Carried: independent "is this Sherlock?" read; cross-gender `same_look`;
  step 02's 40-minute share; the Ferrier era blend; a frontier judge tier
  needs an owner-confirmed rate; LoRA and two-subject A/Bs; bare shared
  surname over-credit.

### Run 10 — the no-reuse rule

The owner watched the delivered master and gave one instruction: *"Don't even
use a single shot .. create similar shots for rule of three or whatever
artistic reason .. but don't reuse man I hate it doesn't look good at all."*

Measured on what shipped: **51 shots from 25 takes** — every take played
twice, B00 three times — and **24% of the picture came from clips left over
from earlier plans**, files still sitting in `clips/` under the right beat
names from a plan that no longer existed. Neither was a bug in one function.
Both were the pipeline working as designed: `shots_for` called `best_scatter`,
whose whole purpose is to spread FEWER beats over MORE cuts, and the
assembler globbed `clips/*.mp4` without ever asking whether a file was the
take this run rendered.

**The brick.** The render is the only fixed thing; everything else bends to
it. A take costs ~16 min on this GPU and no argument changes that, so it is
the base case, and every other number is derived from it: takes = what step
07's share affords → the story authors exactly that many distinct setups →
the walk is shortened until its cut count fits the takes → one shot per take
→ the assembler cuts only fresh clips of THIS plan → QC proves it. Run 10
ran that recursion backwards — 44 cuts first, then whatever the budget could
render — and the arithmetic had to close somewhere, so it closed on reuse.

The chain, each link refusing rather than filling:

- `trailer_order.one_each` replaces `best_scatter` in `shots_for`: beats in
  story order, one shot each, `ValueError` on any mismatch. A count that does
  not match is a plan that was never fitted to its takes, not a spacing
  problem to be scattered.
- `TrailerPlan._one_take_per_shot` makes a repeated beat unrepresentable. The
  plan cannot be written that way, whatever writes it.
- `RENDER_SECONDS` is now **16 min, measured** (19 takes, 12:36 → 17:32 =
  15.76 min each). The old 660 s was the 243-frame arithmetic, and the plan
  it sized asked for 25 setups of which the budget rung dropped six — the
  last six, which are the climax.
- `affordable_takes` → `fit_points` → `agree`: the walk gives up seconds,
  half a bar at a time, until its cuts fit the takes, and hands back any
  beats it could not use. On the test metre (120 BPM, title hit at 88 s) 12
  affordable takes fit a **25.0 s** trailer of 12 shots. That is the honest
  length of this pipeline today: the trailer is short because the render is
  slow, and the only way to a 60 s cut is a faster cycle, not a second look
  at a picture.
- `music_of(metre, ends)`: the title lands on the cue's hit only when the
  picture reaches it. A 25 s cut with a card timed to a hit at 88 s would
  hold a static title for a minute. Line windows past the end are dropped
  the same way (`inside`).
- `clip_cache.fresh`: a clip counts only when step 07's record and the file's
  own sidecar agree. `promote` now copies the recipe sidecar with the bytes,
  so a promoted clip is identifiable; before this it was anonymous, which is
  exactly why last plan's B04 could pass for this one's.
- `assemble.takes_for` computes every shot's clip BEFORE `luma_stats` and
  refuses if any is missing. The stale clips had also been poisoning the
  grade calibration — the hero look was matched against pictures that were
  not in the trailer.
- `step_08.usable` + `step_06.refit`: a beat whose take never rendered, came
  back capped shorter than its shot, or is stale, leaves the plan and the
  walk is re-cut around what remains. `neighbouring_take` and `resolver_for`
  are gone. A trailer that lost a take is a shorter trailer.
- QC's floor gains `reused_shots` and `stale_shots`, both of which must be 0.
  The rule is now measured on the delivered master, not only enforced
  upstream — which is the standard every other gate here is held to.

`best_scatter`, `scatter`, `interleave`, `allocate`, `is_cyclic`,
`shortest_return`, `longest_repeat` and `refuse_repetitive` are now dead with
respect to the pipeline: nothing but their own tests calls them. They are the
measuring apparatus of a problem that no longer exists, kept until someone
decides whether the song and episode paths still want them.

**Open.** The trailer's length is now the render cycle's hostage: 16 min a
take, ~12 takes in step 07's share, ~25 s of picture. Every second of trailer
costs about half a take. The next real gain is not in the cut — it is fewer
frames, fewer steps, or a second GPU.

### Run 10 — phase B: the trailer is a shape, not an average

The owner's second and third instructions on the same master: *"The song is
really bad … lyrics are bland … don't use negative prompts .. not in images
or videos or music .. strict rule"*, then *"Make all the changes .. use sub
agents"*. Four critiques (editor, sound, story, pipeline) and five music
reports were written against the run-10 master; every finding below is
measured on that file, and every fix is in the build table as rows 29–42.

**What the master measured.** 105 s; music with nothing over it 92 %; one
spoken line (2.1 %), clipped (peak 0 dBFS, flat factor 24.2, crest 2.6 dB)
and laid over the wrong face; loudest moment at 53 % of runtime, the last
wave equal to the chorus, no lift; two declared cards not rendered; the
killer's face at 8.75 s and the arrest at 17 s; 10 cuts at exactly two beats
each in 83–94 s; the pipeline had asked for `[Verse][Chorus]` and
"instruments STRUCK on every beat" and ranked the steadiest grid first. It
was a music video because every stage ordered one.

**The brick, again.** A trailer is three movements and a made ending, and
everything measurable follows from the position in the picture: the story
(M1 25 % / M2 45 % / M3 30 %), the cut (bars per shot 1.40 → 0.80 → 0.44,
off the grid in acts 1–2, on it in act 3), the sound (peak in the last
fifth, pulse gone under lines, a hard out, 2.2 s of room tone, the hit on
the card), and the lines (hook ≤ 12 s, threat, button last; 5–12 per 100 s;
every one on its speaker's face). QC now grades the SHAPE — where the peak
is, how much of the picture speaks, per-act on-beat fractions, line true
peak — not integrated loudness and one whole-trailer `cuts_on_beat`, which
run 9's fixes had each satisfied while making the trailer worse.

**Two consequences worth stating plainly.**

- `title_on_downbeat` is now usually false and that is correct: the card is
  struck 2.2 s after a hard out on a chosen downbeat, a made shape, not a
  found one. The measurements that matter are `hard_out`,
  `pre_title_silence_s` and `title_hit_lu`.
- `MAX_LINES` was 4, under the story spine's own floor of 5 per 100 s, so
  no long cut could ever satisfy R1; it is now derived (12 per 100 s over
  the 108 s pinned cue = 13) and `roles_for` fills the extra windows with
  more middle (answer / threat alternating), never a fifth role. On a 25 s
  cut this changes nothing: `wanted_speech(25)` is 3.

**Negatives.** `studio/affirm.py` lints every prompt string under `studio`
and `scripts` for negation; the six trailer workflows in comfy_studio
(`video_minimax_h3_r2v_turbo`, `image_krea2_turbo_t2i`,
`image_qwen3vl_caption`, `audio_minimax_music_3`, `audio_qwen3tts_design`,
`audio_qwen3tts_clone`) already feed `ConditioningZeroOut` and carry no
negative text; only the unused LTX workflows do. Fixtures under `tests/`
are data (movie lines) and are not scanned.

**What run 11 must measure — none of these numbers is measured yet.**

| expectation | where it comes from | what to read |
|---|---|---|
| ~7.45 min/take with H3 resident through a round (28 takes in the share) | pipeline critique: 8.3 of 15.76 min per take was model swap | gate=`cycle` learnings; `render_seconds(rows)` |
| ~5.34 min/take with frames per shot (39 takes) | 124 frames average vs 175 | the same rows, second round onward |
| reader session <= 240 s + 20 s/sheet | one Qwen3-VL session per round | gate=`read` learnings |
| identity still holds at 124 frames with the head leak out of the sample | `frames_of` samples past `HEAD_TRIM` | step 07 bind verdicts, reroll count |
| one 4-step insert vs its 8-step twin | `FAST_INSERTS` is off | a single paired take, by eye and by the reader |
| `speech_occupancy` >= `speech_target` on a 25 s cut (3 lines) | story spine + `MAX_LINES` | `qc.json` |

Until the first round writes a `cycle` learning, step 06 sizes the plan at
the typed 16 min: **12 takes, ~25 s of picture**. The trailer gets longer
only as the measured cycle gets shorter — the same recursion as the no-reuse
rule, now with the cycle as the base case it was always supposed to be.
