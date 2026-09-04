# Trailer critic audit

Adversarial read of the trailer skill as it exists on 2026-09-03: nine SKILL.md
files, the studio modules they describe, the five build scripts, the Scarlet
and Jekyll artefacts, and the last sixty commits. Nothing was rendered and no
credit was spent. The standard is the creed: a claim is MEASURED if a number
was read off a file, DERIVED if it follows arithmetically from a measured or
external fact, ASSERTED if it is stated and nothing in the repo tests it.

Two facts frame everything below:

- The pipeline has been verified on **two books**, both Victorian, both Doyle
  or Stevenson, both dialogue-rich, both with a built-in narrator swap.
- **Jekyll's shipped artefacts are stale.** `plan.json` has 14 beats / 34
  shots with shots of 11.08 s and 8.38 s (over the current `MAX_SHOT` 4.0),
  a palindromic order whose `shortest_return` is 1 (would fail the current
  gate), and `cues.json` in the old schema with no caption. Every "verified
  on Jekyll" number in the skills predates the current code. n is really 1.

## 1. Claim ledger

Tag key: **M** measured, **D** derived, **A** asserted. Where a rule carries a
measured symptom and an asserted cure, both tags appear and the rule counts as
A (a symptom is not a rule).

### SKILL.md (root)
- Seed 777777 identity drift; audio-ref 0.886 -> 0.088 — **M**
- Title miss 75.21 s vs 80.5 s; glob-order 4.0 vs 9.7 LU — **M**
- Redfern arc 1.50 -> 1.33 -> 0.54 -> 3.0 s from 50 Hollywood trailers — **D** (external corpus; never validated against this pipeline's output or any literary trailer)
- Register table: literary = one cue, no VO, stretch 2.5x — **A**
- `LITERARY_STRETCH` 2.5, `MAX_SHOT` 4.0, `MIN_SHOT` 0.4 — **A** (no sweep, no A/B)
- Motif rule (a returning image reads as a return) — **A**
- Stable Audio 12.7 dB short of sub; sub_drop -2.2 dB — **M**
- "Two-pass loudnorm, -14 / -1.0 dBTP" — **A**, and **contradicted by code**: `TARGET_TP = -2.0`, one measured gain, no loudnorm second pass
- Duck 12-15 dB under lines — **A**, not implemented anywhere
- H3: frames%17==5, 1344x768, 24 fps, adapt_canvas fixed point — **M**
- Reference leak 2.1 s / `HEAD_TRIM` 2.6 — **M** (leak), **A** (margin)
- "Location binding weaker than character" — **A** (no number)
- CRISTERION lettering; populated plates — **M** (observed once), **A** (rule)
- Lead not cast[0]; beat index; story-wide ranking — **M**
- Action line must feature the bound character — **D**, and the shipped Scarlet plan violates it (B01/B02 bind Holmes while the action names Watson/Stamford)
- Two-shot render free: 631 s vs 690 s — **M** at n=1 each (inside the 650-781 s run-to-run spread the same file reports)
- H3 audio -39.8 LUFS discarded; alimiter level=disabled; apad infinite — **M**
- loudnorm LRA linear-mode rule — **A** (docs paraphrase)
- STEPS 8: "final Euler step from sigma 0.72" — **D**; "two published sources call four a draft" — **A** (uncited)

### 01-story
- Element unit 241 / 630 candidates — **M**
- LEAD / FIGURE / TURN land on Part II and the Full Statement — **M** on n=2 (and TURN is only *printed* by build_plan; nothing downstream reads it)
- Lexical spoiler 0 vs 39/50 — **M**; tail-15 %-plus-last-meeting rule — **A**
- "Show <= 0.6 s, no dialogue" — **A**, unenforced
- Lead >= 25 % gate; `max(3, n//4)` — **A**
- Register gate — **D** from the plan's own rank (see section 3)
- Beat index; capitalised tokens 13/268 — **M**; "capitals are the beats" — **A**
- Concreteness length-controlled lift 1.10x over ~900 illustrator-labelled paragraphs — **M** (the one externally validated ranking claim in the repo)
- Rarity ranker RACHE 165 -> 14 — **M**; "rarity is not iconicity" — honest
- `setup_value` weights 3.0 / 2.5 / 2.0 / 1.5 / -1.5 / +6.0 iconicity — **A**; `iconicity.json` is hand-written per book and its weight dominates the sum

### 02-refs
- Sampling missed Henry Jekyll — **M**
- SFace collision 0.540 / 0.464 vs same-person line 0.363; 0.540 -> 0.104 after cards — **M**
- ArcFace 0.291 passed a cast readers called identical — **M**
- Bust framing 59x83 px -> ~250 px — **M**
- "A model draws objects, not adjectives" — **A** as mechanism (one fix, one measurement, no ablation)
- Subject-1 / Subject-2 bind positionally — **A**
- Three-gentlemen limit — **M** (honest)
- is_photographable / is_scene_safe filters — **D**
- Unmarked adult = 35-50 — **A**

### 03-music
- 11.1 s per section — **M** (fit)
- Duration is a second seed, corr -0.03 — **M**
- Caption prose 4.0 vs 9.7 LU — **M**
- Negation -> humming — **A** (anecdote, n unstated)
- Fitness crowding "8-40 onsets" — **A**, **contradicts code** (`trailer_fitness` uses 15-120)
- Render 2-3 seeds — **A**
- 2.4 syllables/s fill — **A** ("documented", unlinked)
- Non-executable tags produced the 78.5-139.75 s spread — **M**
- Shared padding killed stopdowns 9 -> 1 — **M**
- Asked 84 BPM solo violin, got ~105 BPM and no violin — **M** (tone.json is not obeyed; the skill records this and keeps the tone.json path anyway)
- P95-P5 dynamic range; floor -52.5..-53.9 dBFS — **M** / **D**
- GRID_DB 6 -> 4: 20 -> 59 onsets per 100 s — **M**; 4 dB itself — **A**
- `title_moment` window 0.6-0.95, within 3 dB of P95, stopdown within 6 s — **A**
- `late_density` 0.80-0.95 window — **A**; the motivating 7.42 s shot — **M**

### 04-shots
- 683 s mean, 650-781 s per take — **M**
- <= 1.4 shots per setup — **A**
- 3.0x / 3.8x shipped reuse — **M**
- Head-size framing table; 3 moves per register; `BOUND_FLOOR` medium — **A**
- 7.0 s take = 175 frames, 4.69 s usable — **D**
- LoRA no speed gain — **M** (one run)
- OpenVDN not applicable — **A**

### 05-dialogue
- Trough budget Sherlock 1 / Jekyll 4-5 — **D** from beatmap (the Jekyll figure from the stale cue)
- "4-6 lines, 40-60 words, 10-14 s, <= 13 %; three derivations agree" — **A**; no derivation is named
- Duck <= 2 lines — **A**
- Reply / unbound / pronoun penalties — **A** (regex over an English idiom list)
- Dedupe 673 -> 370, 650 -> 257 — **M**
- IndexTTS-2 over Qwen3-TTS for duration control — **A** (no local run)
- Qwen3-TTS discards instruct on the clone path — **A** (docs)
- Compress 0.85-1.0x; one seed per character; over-black line = card; ship 3 lines and A/B — **A**
- `speech_seconds = 0.22 x vowel groups + 0.45` — **A** (no fit against any rendered speech)
- Question -4 — **A**
- "Synthesis risk and quotability are correlated axes" — **A** (plausible, unmeasured)
- A line may span one cut — **A**

### 06-style
- Luma 11.9-48.4 across plates — **M**
- Krea2 / Qwen-Image lineage; style LoRA — **A**
- Stylised reference through H3 — honestly UNTESTED

### 07-cards
- `\fad` form feed; test with the same bug — **M**
- Jekyll card 1323 / 1344 px clipped — **M**
- MarginL compensates the trailing letter-space — **M**
- Bookman; 5 % cap height; 0.20 em; `&H00DAE6ED`; 0-2 quotation cards; hold 0.55 x words + 0.5 s floor 1.4; cut in on hit; `TITLE_SAFE` 0.90 — **A** (eight rules, zero measurements)

### 08-assemble
- Order of operations — **D**
- Ratio table 0.75-0.85 build / <0.70 stutter / 0.90-1.10 plateau / >1.50 reset — **A**, labelled Reasoned, not implemented
- Phrase unit, hold >= 3x median, accent <= 0.5x, adjacency — **A**, not implemented
- Grade floor 32 (corpus median 28, P5 3.2) — **M** corpus, **A** floor
- Black-as-layer table (only one black exists in the cut) — **A**
- SFX budget 3-5; five-layer impact (tick / tail / pre-swell absent from sfx.py) — **A**
- BT.1359 45 / 125 ms — **A** (standard cited, never measured on a delivered file)
- ffmpeg `-t` is ceil(t x fps), verified at 7 frame counts; `-ss` rounding — **M**
- Drift gate 2 frames — **A** threshold, **M** drift
- `TARGET_LUFS` -14 / `TARGET_TP` -2.0 / `LIMITING_DB` 5.5 — **A** convention, **M** consequence
- QC -16.0..-12.5 — **A**
- QC `db.max - db.min >= 20` — **D** from the metric beatmap's own docstring rejects

### Counts
118 rules and numbers tagged. **MEASURED 43. DERIVED 11. ASSERTED 64.**
Of the 64 asserted, 27 are the numeric constants the cut actually runs on
(`MAX_SHOT`, `LITERARY_STRETCH`, `GRID_DB`, `title_moment` window, card hold,
grade floor, loudness targets, dialogue budget). Of the 43 measured, 31 are
measurements of a *bug* rather than of a *rule*: they prove something was
wrong, not that the replacement is right. Three rules contradict the code they
describe (-1.0 vs -2.0 dBTP, two-pass vs one gain, 8-40 vs 15-120 onsets).

## 2. Generality audit

"Works for any novel" is claimed in the root skill. Rule by rule, for the seven
book shapes the caller named:

| Rule | Horror | Romance | Comedy | Epic fantasy | 1st-person | No dialogue | Translation |
|---|---|---|---|---|---|---|---|
| Redfern arc (Hollywood action trailers) | ok | wrong shape (no hit) | wrong (gag rhythm) | ok | ok | ok | ok |
| Literary register: one cue, no VO, 2.5x stretch | too slow | plausible | wrong | too slow | plausible | plausible | plausible |
| LEAD by presence | ok | fails: two leads | ok | fails: ensemble | trivially the narrator | ok | ok |
| FIGURE = most story outside lead's view | ok | wrong: co-lead | wrong | ensemble noise | fails: nothing is outside the narrator's view | ok | ok |
| TURN = longest lead-absent run | ok | none exists | none | many | **undefined** (never absent) | ok | ok |
| RESOLUTION = tail 15 % + last meeting | ok | ok | ok | ok | ok | no meeting | ok |
| Iconicity.json hand-written | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| `REPLY` regex ("no, sir", "quite so") | Victorian only | Victorian only | Victorian only | fails | ok | **no input** | fails |
| `speech_seconds` vowel-group formula | English | English | English | invented names | English | n/a | **fails** |
| Costume pools / age bands | Victorian | Victorian | Victorian | fails | Victorian | Victorian | Victorian |
| Cast cards, SFace identity | ok | ok | ok | non-human fails | narrator has no face | ok | ok |
| Caption "instrumental", tone.json | ok | ok | ok | ok | ok | ok | ok |
| Title moment 0.6-0.95 of cue | ok | ok | ok | ok | ok | ok | ok |
| Quotation cards 0-2 | ok | ok | ok | ok | ok | **the only voice** | attribution |

Rules that are Sherlock/Jekyll-shaped by construction:

1. **TURN = first scene of the longest lead-absent run.** Scarlet has Part II
   (Utah), Jekyll has the Full Statement: two books with a built-in narrator
   swap. Pride and Prejudice has no lead-absent run; Frankenstein has three
   nested ones; a first-person novel has zero by definition.
2. **FIGURE = whoever owns the most story outside the lead's view.** Written
   to return Hope and Hyde instead of Watson and Utterson. In a romance the
   answer is the love interest, who is *inside* the lead's view.
3. **`REPLY` / `UNBOUND` regexes** carry "no, sir", "quite so", "indeed",
   "my dear fellow". That is the idiom of one register of English prose.
4. **Costume vocabulary** (custodian helmet, frock coat, consulting detective
   vs constable) is a Victorian table.
5. **`iconicity.json`** exists for the two books someone hand-wrote it for.
   With weight 6.0 it decides selection; for any other book the term is 0 and
   selection degrades to camera emphasis plus rarity, which the repo's own
   commit says "is not iconicity".
6. **"One cue, no VO" literary register** was chosen because Scarlet and
   Jekyll are moody. It is a house style, not a property of literature.
7. **Trough budget "Sherlock 1 line, Jekyll 4-5"** is the number of stopdowns
   two MiniMax seeds happened to produce.

Nothing in the skill is tested on a book with more than one narrator, a
female lead, an ensemble, a comic register, or a text not in English.

## 3. Test audit

### Gates that cannot fail on the property they name
- `qc.plan_unbound` — reads `char_refs` from the plan and asks whether the
  plan's beats use them. Expectation and object are the same file.
- **Register gate** (`build_plan`) — arc position is `i / (n-1)` over the
  value-ranked element list, so quiet / build / hit / aftermath is a function
  of rank, not of where the shot lands in the timeline; with >= 4 elements
  every register is present by construction. The cut order is random scatter,
  so the register a shot was selected under is unrelated to when it plays.
- `qc` dynamic-range check uses `db.max - db.min >= 20`, the metric
  `beatmap.trailer_fitness` was rewritten to abandon because it reduces to
  `peak + 53`.
- Lead-presence gate counts beats in the *plan*; nothing checks the lead is
  visible in a delivered frame (SFace exists and is never run on a clip).
- "Cuts on onsets 45/45" is measured on `plan.json` cut points, never on the
  delivered file. `assemble` measures drift of the title only.

### Steps with a test that can fail on what matters
`cut_points` on a synthetic grid; `MAX_SHOT`; card hold; grade clamps;
`alimiter level=disabled`; `LIMITING_DB`; `frames_arg` against ffmpeg;
`shortest_return` / `longest_repeat` against the real shipped order;
`card_fits` on a decoded frame; `refuse_collision`; clip-cache fingerprint;
form-feed absence in ASS. These are good tests. Every one of them was written
*after* the corresponding file shipped broken.

### Steps with no test, or a test only on arrays
- `beatmap.envelope / onsets / structural_impacts / stopdowns / title_moment`
  — tested only via `late_density` and `trailer_fitness` on hand arrays. No
  test feeds a synthetic signal with hits at known times and asks whether the
  hits come back.
- `qc.py`, `assemble.py`, `build_plan.py`, `build_music.py`, `build_clips.py`
  — untested end to end.
- `trailer_dialogue.line_value / synthesis_risk / speech_seconds` — placement
  invariants only; nothing tests the number against speech.
- Any TTS — no TTS code exists.
- `music_tone.caption` — "vocals excluded by silence" tests a string.

### Missing tests, by name
- `test_onsets_recover_a_synthetic_click_track_at_known_times` — 20 clicks at
  random gaps >= 0.35 s over pink noise; assert every click is within one
  window (0.05 s) of a returned onset and no more than 2 spurious.
- `test_title_moment_is_the_planted_stopdown_then_impact` — plant one
  12 dB, 0.4 s hole at 0.8 of length followed by a P95 hit; assert it is
  returned, and assert `None` when the hit precedes the hole.
- `test_every_delivered_cut_lands_within_one_frame_of_a_measured_onset` —
  scene-cut detection on the master (`ffmpeg select='gt(scene,0.4)'`),
  onsets on the master's own audio track; assert >= 90 % within 1 frame.
- `test_title_card_first_frame_precedes_the_cue_impact_in_the_file` — decode,
  find the first frame whose ink bbox matches the card, compare to
  `structural_impacts` of the file's audio, not the plan.
- `test_no_more_than_ten_percent_of_shots_sit_on_the_cap` — Scarlet shipped
  10/45 at exactly 4.0 s. A grid with one onset per 1.7 s should not be
  capped a quarter of the time in the build section.
- `test_register_follows_timeline_position_not_selection_rank`.
- `test_lead_is_recognised_in_a_delivered_frame_of_the_first_third` —
  SFace on the clip's mid frame against the cast card, > 0.363.
- `test_every_placed_line_is_audible_above_the_bed_in_the_master` — after
  TTS exists: short-term LUFS of the line band vs bed in the same window,
  >= 6 LU.
- `test_speech_seconds_within_15_percent_of_rendered_duration` — on ten
  rendered lines.
- `test_plan_unbound_fails_when_a_scene_character_has_no_reference` — build
  the expectation from `screenplay.json`, not from `plan.json`.
- `test_qc_dynamic_range_uses_p95_minus_p5`.
- `test_jekyll_artifacts_are_current_with_the_code_that_claims_them` —
  every shot <= `MAX_SHOT`, `shortest_return` >= 3, cues carry a caption.

## 4. Gap list against the owner's three requirements

**"Song-level cuts / music beat cuts"**
- There is no beat, downbeat, tempo, bar, or section detector anywhere.
  `beatmap.py` is an RMS envelope at 50 ms with a 4 dB rise threshold. An
  "onset" here is any loudness step, not a beat.
- The cut grid is therefore dominated by the arc and the cap: 10 of 45
  Scarlet shots are exactly 4.0 s. The music is consulted only to nudge a
  nominal.
- `SNAP_TOLERANCE` exists and is unused. `STOPDOWN_DB` exists and is unused.
- No vocal path: `music_tone.caption` hardcodes "This piece is instrumental".
  A song with a chorus, a lyric hook, a vocal entry — none is representable.
- The tone the caption asks for is not what arrives (84 BPM violin -> ~105
  BPM no violin), and nothing measures BPM on the delivered cue.
- `late_density` and `title_moment` are the only structural facts read from
  the music; both are amplitude statistics.

**"Powerful iconic dialogues and moments"**
- Lines are selected and placed in `plan.json` and then **nothing renders or
  mixes them**. `assemble.py` mixes bed + sub_drop + impact. Four Scarlet
  lines exist on paper only. No TTS code, no voice, no duck.
- "Iconic" is `iconicity.json`, a hand-made file, weight 6.0. The repo's own
  commit says rarity "is not iconicity" and "needs a judge that has read the
  culture". That judge does not exist.
- `line_value` is a regex over English idiom. Zero validation that a
  high-scoring line is one a reader would recognise.
- "Moments" have no data path either: `structural_impacts` are audio
  events; screenplay capitalised tokens are counted, but the plan does not
  place a named moment on a named impact.
- Story order is discarded: `best_scatter` randomises. TURN is printed and
  dropped. A trailer that cannot say "then" cannot deliver a moment.

**"Works for any novel"**
- Verified on two books, one of which is stale. See section 2.
- Every ranking constant is asserted. No held-out book, no human rating.

## 5. Brick hypothesis

Candidate brick, stated so it can fail:

- **Base case**: one shot bound to one identity on one measured audio event
  (`cut_in`, `cut_out` on the file's own onset grid; SFace > 0.363 against
  the card; loudness measured on the file).
- **Recursive rule**: the next shot is chosen by *lack* — it supplies what
  the running cut has not yet shown (a face, a place, a claim) and lands on
  the next event the music offers at the arc's current density.
- **Closure claim**: any trailer of any length is the fold of that rule over
  the music's event list; the title card is the shot chosen when the music
  offers a stopdown and the cut has already shown lead, figure and place.

Against the five-test battery it regenerates results not stated in it (the
arc becomes a density schedule rather than a table; the register gate becomes
"has the cut shown X yet"; the literary stretch becomes a property of how
many events the cue offers). It fails one test: **closure**. The rule
generates a *cut*, not a *trailer*, because it has no term for meaning — it
cannot tell a moment from an event, or an iconic line from a short one. The
repo's own history says this: rarity is not iconicity; the honest ranker is a
judge that has read the culture.

So the honest finding is: **there is a brick for the timing layer** (event
list x lack-driven selection, and the pipeline is most of the way to it) and
**no brick for the meaning layer**. Iconicity, spoiler, "moment" are not
generated by any rule in the repo; they are read off a hand-made file or a
lexical proxy. Any paper that claims a brick for book -> trailer must show a
rule that produces `iconicity.json` from the text, or admit that layer is an
oracle (human or LLM judge, cached per book) and build the brick around the
oracle's *interface*, not its content.

## 6. Attack list

Objections the two papers must answer with a number, a test name, or a
withdrawal. Each is falsifiable.

**Music-structure paper**
1. A downbeat tracker is trained on human music. Cite its F-measure on
   MiniMax Music 3 output, on these five cues, or the claim is a story.
2. The delivered Scarlet cue plays ~105 BPM against 84 requested with no
   violin. Any "cut on the bar" scheme inherits a tempo the caption did not
   choose. Show BPM measured on the file, not on tone.json.
3. 35/44 cuts on grid with 10/45 shots at the 4.0 cap: the cap, not the
   music, sets a quarter of the shot lengths. Show the on-cap fraction after
   your scheme, or it is the arc with a new label.
4. `structural_impacts(count=4, min_gap=4.0)` returns four loudest windows.
   A "section boundary" from that is a loudness percentile. Show a section
   detector that agrees with a human on >= 4 of 5 cues.
5. Cutting on the beat at 84 BPM gives a 0.714 s quarter; `MIN_SHOT` is
   0.4 and the trough is 0.54 s. Show the arithmetic that reconciles a
   metric grid with the Redfern arc without one overriding the other.
6. A vocal song path needs a lyric-onset detector and a phrase boundary.
   Neither exists. Name the code path that finds a chorus entry.
7. Cross-fade over a downbeat vs hard cut on it: which, and measured how?
   BT.1359 is cited nowhere in a test.
8. `SNAP_TOLERANCE` 0.30 is dead. Any tolerance in the paper must be
   measured against the RMS onset's timing error, which is +-25 ms at
   `WINDOW` 0.05 plus the frame quantisation.
9. Duration is a second seed (corr -0.03). A cue with a chorus at 0.62 on
   one seed has it at 0.71 on the next. Show the cut is rebuilt from the
   delivered cue, never from the caption's intent.
10. "Instrumental only" is a constant in `music_tone.caption`. A vocal path
    that keeps it is a paragraph, not a path.

**Iconic-lines paper**
11. Zero lines have ever been rendered. Every duration, duck, compress and
    seed claim is asserted until a `.wav` exists. Name the first test that
    plays one.
12. `speech_seconds = 0.22 x vowel groups + 0.45` has never met a rendered
    line. Report the residual on ten Qwen3-TTS outputs before placing any
    line by that number.
13. The skill says Qwen3-TTS discards instruct on the clone path and picks
    IndexTTS-2. A paper that names Qwen3-TTS must either refute that or show
    the design-voice path controls duration without cloning.
14. A designed voice per character has no identity gate. SFace exists for
    faces; name the speaker-embedding check, threshold and same-person line
    for voices, or two characters will be one voice as two leads were one man.
15. "Four to six lines, 40-60 words, three derivations agree" names no
    derivation. Give the three or drop the sentence.
16. `iconicity.json` is hand-written. A "generic" skill cannot ship a file
    someone writes per book. Name the function that produces it from the
    text, its agreement with a human on one held-out book, and its cache key.
17. `REPLY` matches "no, sir" and "quite so". Show the regex on a modern
    novel, a translation and a first-person text, with false-positive rate.
18. The cut order is random scatter; a line placed on shots 0-1 speaks into a
    picture chosen at random. Show what a line's *picture* is, and how the
    placement survives `best_scatter`.
19. Shot 0 of Scarlet opens on a line with an exclamation risk ("I've found
    it! I've found it."). Placement ignores `synthesis_risk` at the head of
    the cut. Where is the test?
20. Ducking 12-15 dB is described and does not exist. Any mix claim needs a
    measured line-over-bed LU in the master.
21. First-person novels put the most quotable prose in narration, not
    dialogue (`action_elements` still filters kind == "action"; narration
    is neither). Name the path that makes a narrated sentence speakable.
22. Every trailer line has to survive the loss of its context. A test that
    hands the line alone to a reader who has not read the book and asks
    what it means is the only measurement of "stands alone". Propose it or
    stop claiming it.

**Both papers**
23. Jekyll is stale. Any number quoted from Jekyll artefacts must be rebuilt
    on current code before it is evidence.
24. Both papers must state which of their rules is MEASURED on a delivered
    file, which is DERIVED from a stated fact, and which is ASSERTED — and
    give the count.
