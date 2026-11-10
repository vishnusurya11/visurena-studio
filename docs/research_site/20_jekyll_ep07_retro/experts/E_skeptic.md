# E. Skeptic over A-D (Jekyll ep07 retro, Opus, 2026-11-10)

Read-only, CPU only. `E` = library/20260827135504_the-strange-case-of-dr-jekyll-and-mr-hyde/episodes/ep07.
Each fix was checked four ways: is the cite right; would it ship a known true fault (ep05 doubles, ep03 look-alikes,
ep04 twin constables, ep06 envelope lettering); does it duplicate another fix; is it one small function with a $0 test.

## 0. Measurements I ran (CPU, scratchpad scripts, nothing in the repo touched)
- **Gait alias, re-measured.** I ran `gait.measure`'s own per-frame code at stride 2 (12 fps, today) and at stride 1
  (24 fps, MIN_RUN 48). The top in-band peaks, as frequency (prominence):

  | take | 12 fps today | 24 fps, top peak in 0.7-12 Hz | 24 fps verdict |
  |---|---|---|---|
  | ep07 T19 | shuffle 4.00 Hz (4.54) | **7.95 Hz (9.0)** | unmeasured: no step rhythm (1.63) |
  | ep07 T00 | shuffle 3.92 (3.82), travel 0.005 h/s | **8.04 (7.73)** | unmeasured (2.31) |
  | ep07 T21 | shuffle 4.04 (3.17) | **8.04 (7.98)** | unmeasured (1.29) |
  | WotW ep03 T07 (owner-liked) | walk 3.10 | 1.73 (4.4), in band | walk, 1.73 steps/s, 0.121 h a step |
  | WotW ep06 T23 (shipped non-fire) | walk 4.04, 0.048 | **11.94 (13.8)**, then 4.02 (2.68) | **SHUFFLE 4.02, 0.034**: a new false fire |

  The alias is real: an 8 Hz render pulse sampled at 12 fps folds to |12-8| = 4 Hz, inside BAND (gait.py:39, 45, 88-98,
  184-189). **But C's fix, 24 fps with the same walls, is refuted.** It does not read T19 as a walk, as C predicted:
  it reads T19 as unmeasured. It also turns a shipped WotW walk into a new HARD shuffle (a 2-frame pulse at 12 Hz).
  And `travel` is not the same at both strides (T19 0.162 -> 0.049 h/s; WotW T07 0.162 -> 0.209), so the 0.045
  step wall cannot be carried across. The gate's only owner-labelled positive, Jekyll HEL ep01 T03 (3.94 Hz, 10-14), sits in the same 4 Hz
  cluster. Its bytes are gone: ep01/takes/r2v/T03.mp4 is the 10-18 remake, and no attempts copy exists. So the positive cannot be
  replayed.
- **Thread scaling (for D fix 2).** `gait.measure` on T19 takes 25.1 s at 2 OpenCV threads and 8.6 s at 8 threads
  (2.9x, two runs each). Only the gait measure was timed. Warp, mouth and the embedder were not.
- **Ledger shape.** In `E/drive.jsonl` the `error` field is only the class (`RuntimeError`, lines 6-52). It never
  holds the refusal text, and no row has `inputs_sha8`. The refusal text with its shots (`G-DEAD T10`,
  `stands at shot_07`) is only in `drive_runNN.log` (run07:128-130, run10:423).
- **Who relaunched runs 12-19.** Every run 12-19 ended with `clock_spent: True` (drive.jsonl lines 37-56). Each was
  parked `clock_loop` at its own end time, and each relaunch was an owner hand-retry.

## 1. Verdicts

| # | proposal | verdict | reason (path:line) | risk of shipping a true fault |
|---|---|---|---|---|
| A-F1a | `derive`: a stop that the table parks by name outranks `clock_loop` | **ACCEPT** | `clock_loop` (autopilot.py:464) runs before `_ended` (:468), which is the only caller of `classify` (:422). The token row is at :248-249. Cites are correct. | none: a park stays a park; only its name changes |
| A-F1b | `clock_loop` counts stops only since the last retry, and only of one (step, error) signature | **REJECT** | It loosens the only brake on a spent clock. Under D3 nothing else parks there (GATES.md:648-652), and ep19's 67 retries are why a retry stopped opening a fresh window (tests/test_a_retry_starts_the_episodes_clock_over.py:1-12). A's own replay says runs 12-17 would "reach `_ended` and then the brain", which means more spent-clock runs. The signature is also too coarse: `error` is only `RuntimeError` (drive.jsonl), and runs 15/16/17 (steps 11/10/11) would have broken the window | low for faults, high for time: more brain turns and relaunches on a spent clock |
| A-F1c | the `clock_loop` reason names the cause | **MODIFY** | Print the last stop's classified reason: `clock_loop: refused: <last line>` | none |
| A-F2 | a finished but unpublished master nudges the owner every 6 h; `notify` returns a bool | **MODIFY** | Verified at scripts/episode/autopilot.py:800-811 (told before send), drive.py:74-83 (no return code), and park's `parked_already` at :925-926. Excluded: **HELD_PUBLISH**. The owner holds publish on purpose (no upload unless asked; autopilot.py:403-411), so nudging a held episode every 6 h is spam about a choice he made | none |
| A-F3 | a cure order that leaves the same fault signature twice parks `cure_no_change` | **MODIFY** | The no-op is real: run07 STEP 09, all 26 takes "cached (bytes unchanged)", then G-DEAD T10/T17 again. The cite `triage_action` 1065-1070 is wrong; it is at **1058-1063**. The signature has to come from the log tail's refusal lines, because the ledger has none. `redo` carrying `take_ids` is deferred: it touches work_orders + step_runner and is more than one function | none: a park never ships |
| A-F4 | preflight: plan contract check, plus plan sha vs its verdict | **MODIFY** | Contract check accepted (episode_home.py:75-77; drive.py:186-190 has no plan check). **The sha8 check as written refuses legitimate ladder cures**: `gait_edit`, `move_type` and `plan_cure` rewrite plan.json (take_ladder.py:502-525), and `plan.cures.jsonl` records them. Use `plan_provenance.chain(...) is None` (step_02_plan.py:126), and only as a "will re-plan at step 02" line, never a refusal. The TABLE row parking a contract `ValidationError` is accepted | none |
| A-F5 | code moves: print the warning once per sha | **REJECT** | Noise by A's own finding. Gold plating | none |
| B | `ship_block.master_blocks`: a per-frame master fault blocks only on 2+ frames or when the take eye names the shot | **MODIFY** | Mechanism verified: master_eye.py:46 (30 frames), :597-606 (one fault per frame), master_ladder.py:145-154 (any one blocks). Three holes. (1) The function drops a lone frame instead of taking a second look. A one-frame shot is the normal case at a 5 s cadence, and re-reading the same frame with the same seed is not a second look; that is why runs 10-17 refused identically. (2) It gates **every** `blocks()` line. Scaffold words and long leaks would lose their one-sighting block, and the ep06 envelope ("THE FOCUS OF THE PICTURE", ~4 s on screen) is exactly a one-sighting fault. (3) `take_named` is empty in practice: a take whose eye names a people fault is refused at G-DEAD (dead_footage.py:89) before the master, and T07.content.json passed. The test also uses `HAIR_LINE`, which master reads never emit; only take_content.py:144 writes it | **as written: ep05 s18 "strangers in the fog" was a master content row** (owner_vs_gates.md row 10), very likely one frame, and it would ship flagged. As modified: blocked if the fault persists into a second frame |
| B-msg | the REFUSED message prints the fault line, frame time and count | **ACCEPT** | master_ladder.py:150-153 prints only `where`. Five runs and one brain retirement went on a line nobody could read | none |
| B-r2 | lift CONFIRM to `take_content.drifted` and to the panel `who:` read | **REJECT** | No false hair-line or panel-who block is in evidence (brick 3: no population). A panel is one still image; it has no "second frame". ep05 T07's grey Jekyll is the true fault the take hair line exists for | high: thins the guard that caught ep05 T07 |
| B-r3 | sheet-time distinguishability of co-cast sheets via the who-reader | **MODIFY -> (b)** | Not built and not measured. It tightens, which is the safe direction, but it needs a VL replay to show it does not refuse every two-man book | none (it tightens) |
| C-F1 | gait at 24 fps, or reject the alias by the take_dq pulse row | **MODIFY** | 24 fps is refuted above: it adds a false fire and travel changes with stride. Keying on the pulse row misses T21, whose pulse row reads `ok, r 0.76` (T21.dq.json). Use **confirm-on-fire** instead: a 12 fps shuffle stands only if the 24 fps leg spectrum has its in-band peak within 0.3 Hz with prominence >= 2.5; otherwise `unmeasured: alias` with both numbers printed (brick 7) | nil for shipping: gait is a flag, never on the ship-block list (ship_block.py:7). What changes is the retake rolls (ep07: 6 each on T00/T19/T21). Real foot-sliding at a true 3-4.5 Hz still fires, because it is in band at 24 fps |
| C-F2a | `gait_verb` is idempotent | **ACCEPT** | gait.py:79 appends `; the walker goes VERB.` again when no pace phrase is left (T00's prompt carried it after "halt") | none |
| C-F2b | gait with the verb already present -> `move_type` | **REJECT** | It cures a mis-measured fault (brick 7); moot after C-F1 | none |
| C-F3 | travel < 0.02 h/s is no walker; un-exempt locked shots from `move_type` | **REJECT** | Part 1 is subsumed by C-F1: T00 reads unmeasured at 24 fps. Part 2 overturns an owner ruling ("a locked grammar shot is never pushed", take_ladder.py:507-508, G-PUSH 2026-10-18; brick 9) | none |
| C-F4 | warp: a second fail -> `plan_warp` (drop the head turn, shorten, widen) | **MODIFY -> (b)** | Supported by brick 11 (a fault that repeats on a fresh seed belongs to the plan) and CURE_RATES warp_se seed 0/4 (take_ladder.py:92-97). There is no measured rate for a plan cure, and it is not one function. It needs the GPU proof, and its plan edit must go through `plan_provenance.record` | none: warp is a flag |
| C-F5 | the crowd ceiling follows the plan, never the panel | **REJECT** (replay first) | The panel base was itself a fix (take_content.py:117-120, retro 2026-10-19: a setup crowd stood the count down on 14 takes). A declared-only base fires on every crowded place with `extras` unset (brick 3). The real hole is the panel gate passing 10 for 6; replay that rule on CPU before building | none (tightens) |
| C-F6 | lettering on a clean panel -> one seed | **MODIFY** | take_ladder.py:159-160 converts only `{content, clones}`. Lettering has no measured seed rate, so the seed is allowed only with a `("lettering","seed")` CURE_RATES row recording the outcome. The writer rule (shop fronts invite signs) is the real cure | none: it adds one roll and never changes shipping |
| D-1a | `derive`: the same refusal on the same inputs parks (`same_refusal`) | **REJECT, merge into A-F3** | Its premise, that under the ceiling a same-reason refusal relaunches without limit, is false: REFUSED goes to `_brain`, capped at BRAIN_ATTEMPTS 3 (autopilot.py:35, 338-349). On ep07 it saves **0 min**, because every run 12-19 was already parked by `clock_loop` and relaunched by hand. `inputs_sha8` and the refusal text are not in drive rows | none |
| D-1b | `ship_block.blocks`: the hair line needs 2 frames | **REJECT, duplicate of B** | Wrong data shape (`fault["lines"]`; `lines_of` reads `note` + `evidence.faults`, ship_block.py:30-32). The hair line never comes from the master. `blocks()` is shared with G-DEAD (dead_footage.py:89, assemble.py:737), so this would loosen the take-level guard for ep05 T07 | high (ep05 T07) |
| D-2 | take_dq's thread cap only on the `--cpu-only` lane | **ACCEPT** | take_dq.py:387 caps on every pass. Gait scales 2.9x at 8 threads (measured above). It pays back on every episode | none |
| D-3 | take_eye cached on input bytes | **MODIFY** | The key must carry the judge-code hash and gate version, as `take_dq.cache_key` does (:736-739). Without them a moved judge re-signs with stale reads (brick 4: "judge_code_moved") | none if keyed so |
| D-4 | skip the third who-frame when two agree | **MODIFY** | Skip only after CONFIRM faults are already in. If the frames are clean, the last read can still return `unread: who`, which is a kept fault (take_content_check.py:121-123, 154-163), so skipping it would pass a take that fails today | as written: an unread take passes |
| D-5 | cache the bed | **REJECT for now** | Its 5.6 min sits inside B's loop and is gone once B lands. Revisit with the full input-dict key | none |

## 2. Final specs (each is a failing test first, $0, no GPU)

**S1 `studio/ship_block.py::master_blocks(faults, reads_per_shot: dict[str,int]) -> list[str]`** (with B-msg).
- A fault that `blocks()` and is **not** a per-frame people line stands alone, as today: scaffold, leak, clones/twin
  kinds, no `evidence.at`.
- A per-frame people line (`people_faults.wrong`, kind `content`, `evidence.at` set) blocks its shot when it shows on
  >= `CONFIRM_FRAMES = 2` distinct `at` values, or when the shot was read on fewer than 3 frames (no second look
  ran, so it fails closed).
- `master_ladder.flag` calls it, and its SystemExit prints `shot_NN: <line> at <t>s (<k> of <n> frames)` per shot.
- Companion `studio/judges/master_eye.py::lone_people_shots(faults) -> list[int]`: shots with exactly one
  people-line frame. `measures` (master_eye.py:549-556) reads once as today, judges the provisional reads, then
  sends those shots through the existing `with_extra(times, placed, shots)` (:161-167) and reads only the new
  times. That is one extra batch of 3 VL reads per lone shot, in the same pass with the model kept.
- Tests in `tests/test_master_people_block_needs_a_second_frame.py`, built from real `Fault` objects:
  1. `who: 1 figure read as 'gabriel_john_utterson'` at 0.5 s, with shot_07 read on 4 frames -> `[]`, and `flag(v) is v`.
  2. The same line at 0.5 s and 2.0 s -> `["shot_07"]`.
  3. One people frame, with the shot read on only 1 frame -> `["shot_07"]` (fail closed).
  4. One frame of `scaffold: the prompt's words drawn in the picture (focus, picture)` -> blocks (ep06 envelope).
  5. `Fault(kind="clones", ...)` with no `at` -> blocks.
  6. ep05 s18 shape: `3 figure(s) for 1 declared` on 2 of 4 frames -> blocks.
  7. `lone_people_shots` returns [7] for test 1's faults and [] for test 2's.
  8. The REFUSED text contains `at 0.5s` and `(2 of 4 frames)`.

**S2 `studio/autopilot.py::named_park(s) -> Derived | None`**, called in `derive` just before `clock_loop`. It returns
`classify`'s park when its kind is `park`, else None. In the same change the clock_loop reason becomes
`clock_loop: <classify reason>`.
- Tests: three spent stops plus a `RefreshError invalid_grant` tail -> PARKED, reason starts `youtube_token_expired`.
- Three spent stops plus a `REFUSED: G-PEOPLE ... shot_07` tail -> PARKED, reason starts `clock_loop: refused:`.
- `tests/test_an_expired_youtube_token_parks_with_the_mint_command.py` stays green.

**S3 `studio/autopilot.py::nudge_due(s, events, now, every_s=6*3600) -> bool`** and `scripts/episode/drive.py::notify -> bool`.
- `nudge_due` is True when the state is PARKED, the last run row's `step == "13"` (the chain reached publish),
  `s.standing` is true, the episode is not published, and no `owner_nudge` event for N is younger than `every_s`.
- The tick sends `epNN FINISHED, NOT PUBLISHED: <parked reason> | <command>` and logs `owner_nudge {sent: bool, n}`.
- `token_watch` logs `sent` from `notify`'s return code.
- Tests: parked at step 13 with standing -> due at 0 h and 6 h, not at 3 h; HELD_PUBLISH -> never due; published ->
  never; a notify that returns False is logged `sent: false` and is due on the next tick.

**S4 `scripts/episode/autopilot.py::cure_changed_nothing(events, order, sig) -> bool`** plus
`studio/autopilot.py::refusal_sig(tail) -> str`.
- `refusal_sig` is the sorted set of `G-[A-Z]+ T\d\d` and `stands at shot_\d\d` matches in the tail, else the last line.
- `triage_action` stores `sig` on each `brain_cure`. When the same order already ran and the following stop left the
  same `sig`, it parks `cure_no_change: <order> <sig>` and does not place the order.
- Tests: two `redo 09` cures with `G-DEAD T10,T17` both times -> park. Same order, sig changed -> placed.
  `refusal_sig(run07 tail)` == `G-DEAD T10|G-DEAD T17`.

**S5 `scripts/episode/drive.py::plan_lines(book, n) -> list[str]`**, appended to `preflight`.
- `load_plan` fails -> `refuse now: plan.json fails the Episode contract: <first error line>`.
- `plan_provenance.chain(dir, verdict_sha8, now_sha8) is None` -> `will re-plan at step 02: plan.json changed
  outside a recorded cure since its verdict`.
- TABLE row `ValidationError[\s\S]*Episode` -> `("park", "plan_contract: {line}", None)`, placed before `Traceback`.
- Tests: motion `"drifts slowly"` -> a refuse-now line; a plan changed only through `plan_provenance.record` -> no
  line; a hand-changed plan -> the re-plan line; `classify` of a ValidationError tail -> park.

**S6 `scripts/episode/take_dq.py::judge_threads(cpu_only, env) -> int`**: `lane_threads(env)` when `cpu_only`, else
`max(lane_threads(env), (os.cpu_count() or 4) // 2)`. `Judges.get` calls it.
- Tests: cpu_only -> 2; serial on a 32-core count (monkeypatched) -> 16; `VISURENA_LANE_THREADS=4` with cpu_only -> 4.

**S7 `studio/gait.py::alias(rows24) -> dict | None`**, called by `measure` only when the 12 fps `judge` says shuffle.
- It re-reads at stride 1 with MIN_RUN 48 and FPS 24, **passed as arguments; no module global is mutated**.
- If the 24 fps in-band peak is not within 0.3 Hz of the 12 fps freq with prominence >= PROMINENCE, it returns
  `{"state": "unmeasured: alias", "freq_12": f12, "peak_24": f24}`.
- `cadence` and `judge` gain an `fps` argument (default FPS).
- Tests on synthetic rows: an 8 Hz art series at 24 fps whose stride-2 read is 4 Hz -> `unmeasured: alias`.
  A 3.9 Hz art series with travel 0.10 h/s -> shuffle stands. A 1.8 Hz walk -> never re-read.
- Before wiring it, run the CPU replay in section 3(a).

**S8 `gait.gait_verb` idempotent.** Test: `gait_verb(m + "; the walker goes " + VERB + ".") == that string`.

**S9 `studio/judges/take_eye.py::cache_key(takes, judge_sha8, version)`** (D-3). Test: a fake reader is called 0
times on the second pass with the same bytes, and N times after `judge_sha8` changes.

**S10 `take_content_check.who_faults_for`** stops reading once `CONFIRM` who-lines are in (D-4). Test: fake reader,
faults on frames 0 and 1 -> 2 calls. Frames 0 and 1 clean -> 3 calls, so an `unread` on frame 2 is still caught.

**S11 `take_ladder.cure_of`**: with `panel_clean`, `lettering` joins `{content, clones}` (one seed). Add
`("lettering","seed"): (0, 0)` to CURE_RATES, so the outcome gets recorded. Test as in C-F6, plus: a second
lettering fault marked `repeated` -> `""`.

## 3. Build order (value per hour first)

(a) Build now, CPU tests only:
1. **S6 thread cap**: ~0.5 h. It saves 27-41 min on every episode (D), and gait is measured at 2.9x.
2. **S2 named park + clock_loop reason**: ~0.5 h. It would have named the token cause on 11-04 instead of 6 days of `clock_loop`.
3. **S1 master_blocks + lone-shot re-read + message**: ~2 h. It removes the run 10-17 loop (84 min of drive clock, 5
   runs). The message part alone is free and lands first.
4. **S3 owner nudge + notify bool**: ~1.5 h.
5. **S5 plan preflight**: ~1 h.
6. **S4 cure signature memory**: ~1.5 h.
7. **S8 gait_verb idempotent**: ~0.25 h.
8. **S7 gait alias confirm**: ~1.5 h. First a CPU replay (yolo on CPU, no GPU): the 20 measurable takes in
   docs/audit/2026-10-14_jekyll_ep01_hel/gait_replay.jsonl plus ep07 T00/T19/T21. Accept only if no 12 fps walk
   verdict changes (confirm runs on shuffles only), ep07's three become `unmeasured: alias`, and the tally is
   written into the GATES row. The skeptic's 5-take run above is the first evidence.
9. **S10, S9, S11**: about 1 h each, about 1-4 min a run each.
10. **C-F5 replay (no build)**: count the panel_content.json people against declared + 1 over Jekyll ep01-07.
   Write the tally before any crowd rule changes.

(b) Needs a GPU proof after the PCIe fix (memory project_gpu_lost_needs_reboot):
- **S1 proof.** Re-run the master eye only (no render) with S1 wired, on: (i) ep07's shipped master and its pre-ship
  cut (the shot_07 refusal) -> flag, not refuse; (ii) ep05's deleted master `a2d09fc0`, if its bytes are on disk ->
  must still refuse at shot_18 (strangers) and at s03/s15 (Jekyll as Utterson); (iii) ep04 master `403e67cf` shot_18
  -> must still refuse. Any of (ii)/(iii) that flags instead of refusing rejects S1. Run the master eye through its
  only caller, scripts/episode/step_11_qc.py (judge only, no recut, no retake). There is no standalone CLI, so the
  lead writes a 10-line runner that calls `master_eye.measures` + `verdict_of` on each master and then
  `ship_block.master_blocks`.
- **C-F4 warp plan cure.** Retake T05 once with the head turn removed:
  `takes_r2v.py --retake=5 --why="plan_warp"`, then `take_dq.py 5`. Pass: S <= 2.5 and Se < 3. A fail keeps warp at the terminal.
- **B-r3 sheet distinguishability.** It must refuse ep03's collapsing pair (`two characters collapse` 0.808), the
  pre-redraw ep07 Enfield/Utterson and ep05 Jekyll/Utterson, and pass 5 WotW/Scarlet co-cast pairs that drew no owner
  complaint.
- **C-F6 / writer rule.** T21 retaken with "blank fascias, no signs" -> `text: false`. One draw records the rate row.

## 4. Skill text changes (exact wording)

LESSONS.md, new brick 17 after 16:
> 17. **A block stands on a second look, and a second look is another frame.** A per-frame people read refuses
>     only when a different frame of the same shot agrees; the same frame re-read on the same seed is the same
>     misread (ep07 shot_07: one 0.5 s master frame of Jekyll's hair refused five runs, 84 min). Scaffold words,
>     a long leak and a measured clone stand on one sighting. Every refusal prints its line, time and frame count.
>     -> Jekyll ep07 retro.

LESSONS.md, new brick 18:
> 18. **A rhythm sampled under twice its rate is another rhythm.** gait read at 12 fps folds the H3 8 Hz render
>     pulse to "4.0 steps/s" (ep07 T00/T19/T21 at 24 fps: 8.0 Hz, no step in band); a shuffle stands only when the
>     native-rate read agrees. A gate whose only positive's bytes are gone is advisory until a new label exists.
>     -> Jekyll ep07 retro.

LESSONS.md brick 8, append:
> A notification is a send, not a read: a finished master that is not public is a state, nudged until a person acts
> (ep07 waited 6 days behind a `clock_loop` park that hid an expired token).

LESSONS.md brick 2, append:
> A cure order that left the same refusal line is spent; the same order is not placed twice (ep07: `redo 09` x3,
> every take cached).

GATES.md:652, replace the last sentence with:
> A third spent-clock stop in a row parks `clock_loop: <the last stop's classified reason>`; a stop the table parks
> by name (token, SAFETY, over budget, plan contract) parks by that name first. A retry never opens a new window.

GATES.md:302 (G-GAIT), replace "HARD. Replay over 91 walker takes ..." up to "a first calibration." with:
> HARD only when the 24 fps read confirms the 12 fps cadence (within 0.3 Hz, prominence >= 2.5); otherwise
> `unmeasured: alias` (Jekyll ep07 2026-11-10: T00/T19/T21's "4.0 steps/s" was the 8 Hz render pulse folded at 12
> fps; the 10-14 positive ep01 T03 3.94 sat in the same cluster and its bytes are gone). Advisory in practice until an
> owner-labelled shuffle replays at both rates.

GATES.md, master-eye / G-PEOPLE terminal row (append to the G-DEAD row's master sentence or the master ladder row):
> At the master a per-frame people line blocks only on 2+ frames of its shot; a shot with one such frame gets 3
> extra reads in the same pass; under 3 frames read it fails closed. The REFUSED line prints line, time, k of n.

## 5. Conflicts resolved
- A-F1b vs D-1a vs A-F3 are three brakes on one loop. Only S4 survives: a signature from the refusal lines, keyed to
  the cure order. The clock window stays as it is.
- B master_blocks vs D-1b: B, modified (S1). D-1b would loosen the take-level G-DEAD guard.
- A-F4's sha check vs the ladder's plan cures (C-F2/C-F4, take_ladder.py:514-525): this is settled by
  `plan_provenance.chain`, never by a raw sha.
- C-F1 vs C-F2b/C-F3: S7 makes both moot.
- D's projection: D's fix 1 is credited 70 min, but all of it comes from S1, not from `same_refusal`. S1 + S6 + S9 +
  S10 project ~5.3-5.4 h on ep07, the same total as D's with the credit moved.

## 6. Not verified
- What the shot_07 master line said. It is not on disk; `who:` is inferred, because the master emits no hair line.
- Whether ep05/ep04 master bytes still exist for the S1 proof.
- How warp, mouth and the embedder scale with threads (only gait was timed).
- Publishable: the gait alias (stride-2 flow cadence vs 3-frame VAE render pulses in video diffusion) plus the 5-take
  table is a short note or benchmark on measuring motion in generated video. Flagged for the paper list.
