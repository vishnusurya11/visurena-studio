# Trailer debate verdicts

Critic's round on `trailer-music-structure.md` (M) and
`trailer-iconic-lines-and-moments.md` (D), 2026-09-03. Nothing rendered, no
credit spent. Verdict key: **ACCEPT** (evidence on this repo's own data, or a
citation checked) / **ACCEPT-WITH-TEST** (named file, function, failing
assertion) / **REJECT** (reason, and what would change it).

## 0. Corrections to my own audit, made while checking the papers

- `analysis/iconicity.json` does **not exist for any book** (checked all 30).
  My audit said "hand-written for two books". The dialogue paper is right: the
  6.0-weighted term has always been zero, so selection has only ever run on
  camera emphasis, verbatim density, names and caps.
- The "~105 BPM, violin absent" note I quoted is not in any SKILL file; the
  tracker reads the chosen seed at 85.7 against 84 asked. Withdrawn.
- Scarlet has nine `cue-*.flac`, eight with caption files, all eight captions
  byte-identical (one md5). The music paper's "eight seeds of one caption" is
  confirmed on disk.
- I reproduced the `line_value` inversion on the repo's own function:
  "This is Sparta!" -8.4, "What is the Matrix?" -7.4, "Why so serious?" -7.4,
  "I'll be back." -3.4, "In space no one can hear you scream." -0.4, versus the
  Ferrier errand at 2.3. The paper's numbers differ by tenths (emotion arg);
  the direction is real.

## 1. Music-structure paper — verdicts

| # | Claim | Verdict | Test / reason |
|---|---|---|---|
| M1 | Brick: cut on the grid the music keeps; break it only where the music breaks it | ACCEPT-WITH-TEST | `tests/test_trailer_edit.py::test_plan_cuts_lands_every_L0_event` — every structural event within `duration` is a cut, on a `FakeMetre`. Closure is honest: rubato is declared a fallback. |
| M2 | 35/44 "on onset" is 12/44 on beat, 4/44 on downbeat; chance 12 % / 4 % | ACCEPT-WITH-TEST | Numbers are not reproducible from the repo: no script, no `beat-this` in `pyproject`. Commit `scripts/trailer/metre_report.py` and its output `trailer/music/metre.json`; `tests/test_metre.py::test_on_beat_fraction_of_shipped_plan_matches_report` reads both and asserts 12/44. |
| M3 | Bars-in-mode 0.31–0.97 across seeds; chosen 331107 = 0.51 | ACCEPT-WITH-TEST | Every "tracked BPM" in the table is 3000/n for integer n (187.5, 166.7, 150, 125, 100, 93.7, 85.7, 83.3): a modal 20 ms inter-beat count, not a tempo estimate, and 187.5/150 are the octave doubles of 93.7/75. `tests/test_metre.py::test_tracker_agrees_with_hand_taps_on_331107` — 16 bars tapped by a human, stored as fixture; downbeat F1 >= 0.8 or the 0.51 is the tracker's. |
| M4 | 26/36 impacts on a beat, 16/36 on a downbeat, 3/3 title moments on a downbeat | ACCEPT-WITH-TEST | Same report script; `test_title_moments_sit_on_tracked_downbeats` asserts 3/3 within 60 ms. n=3 is stated honestly. |
| M5 | Timbral segmentation fails; envelope events snapped to downbeats find sections | ACCEPT (negative) / REJECT (positive) | The negative result stands. The positive is two coincidences (111.5/117.3 vs 111.0/116.2/117.35). Would change: a section list a human marks on 5 cues, >= 4/5 boundaries recovered. |
| M6 | beat-this 1.1.0 MIT, 6–11 s CPU, GTZAN F1 89.1/78.3; allin1 and madmom rejected | ACCEPT | Licence reasoning checked (madmom models CC BY-NC-SA; NATTEN API break). F1 figures are the paper's own on human music; see M3 for ours. |
| M7 | `metre()` -> `Metre(beats, downbeats, bpm, bars_in_mode, ibi_cv)`; `phrases()` re-anchored at events | ACCEPT-WITH-TEST | `tests/test_metre.py::test_click_track_recovers_beats_and_downbeats` — synthetic 4/4 at 84 BPM, accent on 1, F1 = 1.0 within 20 ms; `test_phrases_reanchor_at_structural_event`. |
| M8a | Fitness gains metric / tempo / title / lift terms | ACCEPT-WITH-TEST | `tests/test_beatmap.py::test_fitness_ranks_metric_seed_above_rubato_seed` on `FakeMetre(0.97)` vs `(0.51)`. Thresholds 0.85 / 0.65 / 0.10 / 0.25 are feel; label them so. |
| M8b | Refuse any seed with `bars_in_mode < 0.5` | REJECT | Until M3's hand-tap test passes, the tracker is the arbiter of taste and would have refused the seed a human chose. Would change: hand-tap F1 >= 0.8 on a drumless cue. |
| M9 | Author the hit at section 8/9 (78–89 %), then measure | ACCEPT-WITH-TEST | Sections are not honoured to the second (duration is a second seed). `test_post_chorus_downbeat_lands_in_hit_band` — across the 8 seeds, >= 6 have the return downbeat in 0.75–0.92. |
| M10 | Add "strict 4/4 ... pulse carried by struck objects" to the caption; "that is the difference between 0.51 and 0.97" | REJECT the causal claim | The shipped caption already says "the pulse is a walking double bass and a pocket watch, struck objects only", and under that caption seeds ranged 0.31–0.97. Would change: the caption A/B the paper itself proposes (8 vs 8 seeds, median bars_in_mode up >= 0.15). |
| M11 | Vocal sheet; refrain <= 7 syllables from 2.86 s bar x 2.4 syl/s | ACCEPT-WITH-TEST | The 2.4 figure was measured on parenthetical notes, not sung words (paper admits). `test_refrain_first_syllable_on_downbeat` — one vocal render, demucs stem, onset within 60 ms of a tracked downbeat. |
| M12a | Vocal only if a thesis line <= 7 syllables, not an event, exists | ACCEPT-WITH-TEST | No function produces it. `tests/test_trailer_story.py::test_thesis_line_is_present_tense_and_names_nothing` on a FakeModel; coverage across 30 books reported. |
| M12b | Genre table: gothic/romance -> vocal; detective/procedural -> instrumental | REJECT | A genre table asserted from four examples; the paper's own Jekyll is "either". No `01-story` register tag of this kind exists. Would change: the rule stated as a measurable property (spoken-line count needed, M12c) with the genre table deleted. |
| M12c | <= 2 spoken lines on the vocal path; vocals and dialogue alternate (Lieu) | ACCEPT (alternation) / REJECT (the constant 2) | See contradiction C1. |
| M13 | Cut hierarchy L0–L4 and the `plan_cuts` beat walk | ACCEPT-WITH-TEST | `test_plan_cuts_no_shot_exceeds_cap_and_none_below_min_shot`: half-beat at 84 BPM is 0.357 s < `MIN_SHOT` 0.4; the hold set {4,8,12} beats is 2.9–8.6 s > cap 4.0. The walk as written fails both. Also `nearest(..., tolerance=beat/2)` on an L0 event up to one bar away returns nothing: specify. |
| M14 | `MAX_SHOT = max(4.0, 1.25 * bar)`; the five consecutive 4.0 s shots are the cap filling an onset hole | ACCEPT-WITH-TEST | `test_on_cap_fraction_below_ten_percent_on_synthetic_grid` — 84 BPM click grid, build section, <= 10 % of shots at the cap (shipped: 10/45). |
| M15 | Gate targets >= 80 % on beat, >= 30 % downbeat, 100 % L0, never 100 % | ACCEPT (report) / REJECT (thresholds) | Report in the manifest and in `qc.py` measured on the **delivered file** (scene-cut detection + the file's own audio), not on `plan.json`. Thresholds are numbers to beat, as the paper says. |
| M16 | Dependency group `music`, CPU torch index, pinned versions | ACCEPT-WITH-TEST | `uv sync --group music` in CI; `tests/test_metre.py` imports `beat_this`. |
| M17 | "The hit is a downbeat with silence in front of it; two independent measurements say so" | ACCEPT-WITH-TEST | n=3; same test as M4. |
| M18–M21 | Section grammar (plateau/turn/fill/rise/hit), music-stop overuse, library act shape, instrumental default, lyrics = thesis not plot | ACCEPT | Citations are practitioner sources I recognise; they supply vocabulary, not numbers. No rule derives from M19 (our cues are one-caption 2.3 min pieces, not four acts). |
| M22 | Line starts one beat after the drop, ends one beat before the return; dialogue begins on beat 2 or 3 | ACCEPT-WITH-TEST | Feel, stated cleanly. `test_line_slot_inside_stopdown_leaves_one_beat_each_side` on `FakeMetre`; the audibility test in §7 decides if it matters. |

Music: **ACCEPT 6 · ACCEPT-WITH-TEST 13 · REJECT 5** (M5+, M8b, M10, M12b, M12c-constant).

## 2. Iconic-lines paper — verdicts

| # | Claim | Verdict | Test / reason |
|---|---|---|---|
| D1 | Brick: a trailer line needs no scene and takes a side; culture's keeping outranks text | ACCEPT-WITH-TEST | It is an oracle interface, not a brick (§6). The "needs no scene" half has the test the paper omits: `tests/test_line_value.py::test_top_lines_are_understood_without_the_book` — ten top lines, a FakeModel judge contract now, a human panel once. |
| D2 | Wikiquote 19 quotes, 4 survive into the screenplay at ranks 39/51/104/158; "scarlet thread" only in `source/chapters/ch_04` | ACCEPT | Checked: the phrase is in `ch_04.json` and absent from `screenplay.json`. |
| D3 | `analysis/characters/*.quotes` exists, `studio/quotes.py` cleans it, nothing in the trailer reads it | ACCEPT | Checked on disk. |
| D4 | No book has `iconicity.json`; the 6.0 term is always zero | ACCEPT | Checked; my audit was wrong. |
| D5 | 38-line corpus: median 4.5 words, 97 % present tense, 18 % questions; `line_value` median -1.5, 26/38 negative | ACCEPT-WITH-TEST | Inversion reproduced (§0). 19 lines are from memory and WatchMojo is a popularity list biased to punch. `tests/fixtures/trailer_lines.json` with a source per line; the 19 verified lines only drive `test_corpus_median_words_under_seven`. |
| D6 | Cornell "You had me at hello": rarer words on commoner syntax; generality; ~60 % pairwise | ACCEPT | Paper known to me (ACL 2012); features stated correctly. Held-out use: `test_line_value_beats_chance_on_cornell_pairs` >= 0.55 pairwise on the public pairs file. |
| D7 | Wikiquote API works; editors bold the famous clause; Goodreads API dead; Kindle closed | ACCEPT (API, Goodreads, Kindle) / ACCEPT-WITH-TEST (bold) | Bold checked on one page. `test_bold_clause_present_on_three_book_pages` against recorded fixtures. |
| D8 | Lieu template; money shot withheld; accents must relate | ACCEPT | Vocabulary. |
| D9a | Qwen3-TTS node signatures; clone path has no `instruct`; 24 kHz | ACCEPT | Read from the installed pack. |
| D9b | Design once -> SaveVoice -> clone every line; same instruct drifts timbre | ACCEPT-WITH-TEST | Third-party drift claim. `tests/test_voice.py::test_same_instruct_five_seeds_spreads_wider_than_clone_five_seeds` (`@pytest.mark.local`, resemblyzer cosine spread). |
| D9c | Duration words in instruct have no effect; accents drift; celebrities blocked | ACCEPT-WITH-TEST | Only the duration claim matters here: `test_instruct_duration_word_changes_nothing` (local). |
| D10 | Mix recipe (HPF, presence, small room, spectral duck) "agrees with the existing 12–15 dB duck rule" | REJECT the framing / ACCEPT-WITH-TEST the duck | No duck exists in `assemble.py`; the paper cites an asserted SKILL rule as existing. `tests/test_trailer_assemble.py::test_line_sits_six_lu_over_bed_in_its_window` on synthetic bed + tone. |
| D11 | Netflix 20 cps as the card's lower gate; the 0.55 x words + 0.5 rule holds a 12-word card 7.1 s | ACCEPT | Arithmetic checks. `test_card_hold_never_below_reading_floor` is a one-liner; add it. |
| R1 | Three pools: screenplay, character quotes, source quoted speech | ACCEPT-WITH-TEST | Source quotes have no speaker field; "attributed to its speaker" is a new problem the paper waves at. `test_source_pool_lines_carry_a_speaker_or_are_cards`. |
| R2 | Fetch Wikiquote once per book into `iconicity.json`, fuzzy match >= 85, "flying blind" when absent | ACCEPT-WITH-TEST | Cache keyed on the page **revid**, not the title (a cache keyed on a name is a lie). Network only in the build step; tests use a recorded fixture. `test_iconicity_cache_invalidates_on_new_revid`; `test_wikiquote_coverage_across_thirty_books` reports how many books have >= 5 quotes — this is the "any novel" number. |
| R3 | Delete `<5 -> -3.0` and `? -> -4.0`; length band; question bonus when answerable | ACCEPT-WITH-TEST | The function's own docstring says the *previous* version over-scored shortness and put "No data yet." on top. Two tests: `test_sparta_outscores_ferrier_errand` and `test_no_data_yet_does_not_top_the_book`. |
| R4 | Generality and per-book IDF distinctiveness | ACCEPT-WITH-TEST | The Cornell held-out test (D6). |
| R5 | Title echo +3.0, keep only if >= 40 % of 30 titles appear verbatim | ACCEPT-WITH-TEST | The paper names its own test; run it before the weight lands. |
| R6 | Function label via Strands FakeModel; slate needs >= 1 hook and >= 1 threat/stakes | ACCEPT-WITH-TEST | Contract test only (schema, retry). The refusal rule is a gate on model judgment; say so. |
| R7 | No book line may outscore every line of the 38-line corpus | REJECT | A scorer graded on the corpus it was tuned against is derived from its own target, and a per-book IDF scale cannot be compared to "I'll be back". Would change: replace with within-book ranking — Wikiquote-kept lines in the top quartile — plus the Cornell held-out. |
| R8 | Reversal +3.0 from `state_changes`, first sight +2.5, reaction-to-unseen +2.0, identity-naming line forbidden | ACCEPT-WITH-TEST | `state_changes` exists (92 in Scarlet scenes). `test_reversal_scene_outranks_errand_scene`; `test_line_naming_the_figure_is_refused` — needs a detector the paper does not define. |
| R9 | Source-pool line placed on the speaker's highest-value beat in its chapter | ACCEPT-WITH-TEST | Same attribution problem as R1. |
| R10 | <= 4 spoken lines; over-black and risk >= 2 become cards; never both | ACCEPT | Consistent with 05-dialogue; see C1. |
| ALG | `order_lines`: hook -> answer (shares content word) -> threat -> title -> button; refuse without hook | ACCEPT-WITH-TEST | `test_order_lines_refuses_without_a_hook`; `test_answer_shares_a_content_word_with_hook`. Placement into troughs assumes >= 3 troughs; Scarlet 331107 has one. |
| V1–V7 | Voice recipe: instruct template, neutral 8–12 s reference, one seed per character, calm/peak references, resemblyzer >= 0.75, `atempo` 0.85–1.0, post chain at -20 LUFS-S | ACCEPT-WITH-TEST | All unrendered (paper admits). `test_line_seconds_within_15pct_of_speech_seconds` (local, ten lines) — the paper never mentions `speech_seconds`, the number placement runs on; `test_similarity_gate_rerolls_then_cards`; `test_threshold_separates_two_designed_voices` (20 lines). |
| V8 | Retire the Attenborough-clone workflow for this use | ACCEPT | A real person's voice on a commercial trailer. |
| V9 | Omniscient narrator -> "author's voice"; prefer the card | ACCEPT (as fallback) | A choice, not a claim. |
| PKG | resemblyzer 0.1.4, rapidfuzz 3.14.6 | ACCEPT-WITH-TEST | resemblyzer is 2019-era; `uv sync` against the torch pin is the test. |

Dialogue: **ACCEPT 12 · ACCEPT-WITH-TEST 17 · REJECT 2** (D10 framing, R7).

## 3. Attack list — pre-empted or landed

- **Pre-empted** (the paper answered before I asked): 4 (section detector — measured negative), 6 (lyric onset — demucs proposed), 9 (rebuild from delivered cue), 10 (instrumental constant — vocal sheet), 13 (clone path — design then clone), 14 (voice identity gate — proposed), 19 (exclamation risk -> card), 23 (Jekyll avoided).
- **Landed**: 1 (tracker on drumless: paper admits, no fix), 2 (BPM table is 3000/n — resolution and octave artefacts), 3 (no post-scheme cap fraction), 5 (half-beat < MIN_SHOT; hold > cap), 7 (crossfade vs hard cut unaddressed), 11 (zero lines rendered), 12 (`speech_seconds` unmentioned), 15 ("three derivations" still unnamed), 16 (Wikiquote coverage across 30 books unmeasured), 17 (`REPLY` regex kept, untested off-Victorian), 20 (duck cited as existing), 21 (narration excluded from the pools), 22 (context-free reader test absent), 24 (tags without counts).
- **Half**: 8 (tolerance = beat/2, but on-beat measured at +-1 frame with a 20 ms tracker), 18 (line bound to speaker's shot; order of troughs vs order of hook/answer/threat not reconciled).

## 4. Top five objections each author must answer

**Music**
1. The tempo column is a frame-count artefact (3000/n) with octave errors; hand-tap 16 bars of 331107 and 442208 and report tracker F1 before any refusal rule.
2. The metre sentence you propose is already in the shipped caption; your 0.51-vs-0.97 is seed variance under it. Run the A/B or drop the causal sentence.
3. Your walk violates your own constants: half-beat 0.357 s < `MIN_SHOT` 0.4; hold 12 beats = 8.6 s > cap. State the exemptions.
4. Nothing in the paper measures a delivered file. Move `cuts_on_beat` into `qc.py` on the master's own audio and picture, or the gate is the plan grading itself.
5. Troughs are not in fitness. The dialogue paper needs 3–4 slots; 331107 offers one. A cue selected for metre and title but not for slots cannot carry the lines.

**Dialogue**
1. `speech_seconds` (0.22 x vowels + 0.45) decides where every line sits and the paper never tests it. Ten rendered lines, residual reported.
2. R7 is train-equals-test. Replace with within-book Wikiquote-in-top-quartile plus the Cornell pairs.
3. Wikiquote coverage across the 30 analysed books is the "any novel" number; report it. For the book nobody kept, the paper's own words are "text features are a floor, not a finder" — say what ships then.
4. The duck you "agree with" does not exist; the pools exclude narration, so a first-person novel's best sentences never enter. Two build items, not citations.
5. Attribution: a quoted sentence in `source/chapters/` has no speaker. Name the function, or R1/R9 are cards only.

## 5. Contradictions between the papers

- **C1 Line count.** Music: <= 2 spoken lines on the vocal path. Dialogue: <= 4, hook + answer + threat + button. Neither number is measured. Rule that resolves it: **lines = min(slate, measured slots)**, where a slot is a stopdown or `[Instrumental]` gap in the *delivered* cue (vocal stem via demucs on the vocal path). Music wins on mechanism (slots are measured); dialogue wins on cap (4). Vocal path is on only if slots >= 2 (hook + threat).
- **C2 Line timing.** Music: a line occupies whole beats, starts on beat 2–3, never crosses L0. 05-dialogue and the paper's R9: a line may span one cut, placed by `assign_lines(max_span=2)`. Music wins wherever `bars_in_mode >= 0.65`; the span rule survives only in the rubato fallback, and the manifest says which applied.
- **C3 Duration control.** 05-dialogue: IndexTTS-2 for duration. Dialogue paper: Qwen3 clone + `atempo` 0.85–1.0. Music: whole-beat slots. `atempo` 0.85 buys 15 %; a 2.5 s line cannot enter a 2-beat 1.43 s slot. Rule: **choose the line for the slot** (words <= slot_seconds x measured syl/s), never compress a line into it. Both papers lose; the slot wins.
- **C4 Who owns the register tag.** Music's vocal rule reads a "register from `01-story`" (gothic / romance / procedural) that does not exist; dialogue's R6 labels lines, not books. Nobody owns the book-level tag; until someone does, M12b is void (already rejected).
- **C5 The title event.** Music: title on the hit downbeat, or the second Chorus's first syllable. Dialogue: 13/38 corpus lines are pre-title, and `order_lines` puts the threat before the title. Compatible only if the pre-title slot exists: the stopdown before the hit must hold threat + 2 beats. Fitness must score that slot (music §5 objection 5).
- **C6 Constant pulse vs holes.** Music asks the caption for "a clear pulse on every downbeat even in the quiet sections"; dialogue needs stopdowns for lines and the shipped caption's stopdowns were killed once already by shared padding (9 -> 1). A pulse that never stops removes the slots. Resolve in the caption: the pulse stops *inside* `[Bridge]` and `[Solo]` by name.

## 6. Revised brick

Two layers, one interface, and the closure claim is honest about which layer
has a brick.

- **Timing brick (music paper, amended).** Base case: one shot, bound to one
  identity, from one measured event to the next on the grid the delivered cue
  keeps. Recursive rule: the next cut is the highest-level grid point within
  half a beat of the arc's nominal, in beats not seconds; a phrase resets at
  every structural event; a slot (stopdown / instrumental gap) is a shot of
  its own. Closure: any cut of any length is the fold of that rule over the
  event list; where `bars_in_mode` is low the grid degrades to onsets and the
  manifest says so. This regenerates the arc, the cap, the register gate and
  the title rule; it is a brick.
- **Meaning oracle (dialogue paper, renamed).** "What a culture kept" is not
  generated by any rule in the repo; it is fetched (Wikiquote, revid-keyed)
  or judged (a model with a contract test). Its *interface* is the brick:
  every candidate line or moment arrives as `(text, speaker, kept: bool,
  function)`; the text features are the floor for the unkept book and are
  graded on a held-out corpus, never on themselves.
- **Coupling rule.** A line is a shot: it is bound to its speaker's picture,
  occupies whole beats in a measured slot, and is chosen for the slot it
  fits. Lines = min(slate, slots). The trailer is the fold of the timing rule
  over events plus slots, the slots filled from the oracle's ranked list in
  hook -> answer -> threat -> title -> button order.

## 7. Build order, smallest first

1. `studio/trailer_dialogue.py::line_value` — drop the two inverted terms, add the length band. Tests: `test_sparta_outscores_ferrier_errand`, `test_no_data_yet_does_not_top_the_book`. (One hour; unblocks everything in D.)
2. `tests/fixtures/trailer_lines.json` + Cornell pairs; `test_line_value_beats_chance_on_cornell_pairs`.
3. `studio/iconicity.py::fetch_wikiquote(title, author) -> list[Quote]`, `cache_key = revid`; recorded fixture; `test_four_of_nineteen_match_screenplay`, `test_cache_invalidates_on_new_revid`. Then `scripts/analysis/iconicity_coverage.py` over 30 books — the "any novel" number.
4. `studio/trailer_story.py::line_pools(book)` — three pools plus narration for first-person books; `test_scarlet_thread_line_is_in_pool`; `test_source_line_without_speaker_becomes_card`.
5. `pyproject` group `music`; `studio/beatmap.py::metre()`; `test_click_track_recovers_beats_and_downbeats`; `test_rubato_reports_low_bars_in_mode`.
6. `scripts/trailer/metre_report.py` -> `trailer/music/metre.json`; hand-tap fixture for 331107; `test_tracker_agrees_with_hand_taps`. Only after this may M8b's refusal exist.
7. `beatmap.trailer_fitness` gains metric, tempo, title and **slot-count** terms; `test_fitness_ranks_metric_seed_above_rubato_seed`; `test_fitness_prefers_cue_with_two_slots`.
8. `studio/trailer_edit.py::plan_cuts(metre, events, ...)` — the beat walk with the `MIN_SHOT` and hold exemptions stated; `test_lands_every_L0_event`; `test_on_cap_fraction_below_ten_percent`; `test_no_shot_below_min_shot`.
9. `scripts/trailer/qc.py` — `cuts_on_beat / downbeat / L0` measured on the delivered master (scene detect + its own audio); `plan_unbound` rebuilt from `screenplay.json`; `dynamic_range` = P95 - P5.
10. `studio/voice.py::design_reference`, `clone_line`; two comfy workflows; `test_line_seconds_within_15pct_of_speech_seconds` (local); `test_similarity_gate_rerolls_then_cards`.
11. `scripts/trailer/assemble.py` — line layer, duck, per-line loudness; `test_line_sits_six_lu_over_bed_in_its_window`.
12. `studio/trailer_dialogue.py::order_lines` with `lines = min(slate, slots)`; `test_refuses_without_hook`; `test_line_chosen_for_slot_not_compressed`.
13. Vocal path last: caption `Vocal Details`, demucs stem, `test_refrain_first_syllable_on_downbeat`. It depends on 5–12 and on a thesis line the story stage does not yet produce.
