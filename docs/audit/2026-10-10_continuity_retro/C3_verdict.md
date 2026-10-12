# C3 verdict: the cycle-3 (final) skeptic on C3_T and C3_R

2026-10-11. Read-only, CPU only. Nothing was rendered, no code or workflow was edited, and nothing was committed. This file is the only thing written.

**The bar (CYCLES.md):** build only at 95 %, which means measured on the artefact, in at least 2 independent cases, and surviving this review. Anything weaker is a hypothesis or a bench arm.

**Owner order (2026-10-11):** "don't ask me any more, design it the best way and implement it". There are **no owner-ruling items** in this verdict. Every call is made here and recorded in §4 with its reason, so the owner can veto it later. Spend approval still applies, and every item below is $0.

**Inputs:**
- `C3_T_p90_tail.md`, `C3_R_judges_leftovers.md`, `C2_verdict.md`, `CYCLE_2.md`, `CYCLES.md`, `.claude/skills/episode/LESSONS.md`
- the scratch folder `D:\temp\claude\d--Projects-KingdomOfViSuReNa-alpha-visurena-studio\53388bed-712c-4d9b-972d-6c2de9a9f94e\scratchpad\c3\`

---

## 0. What I re-checked myself

| Claim | My check | Result |
|---|---|---|
| T0: a killed step leaves no clock row | `studio/episode_clock.py:67` `timed` stamps in `finally`. A Windows `Stop-Process` (TerminateProcess) runs no `finally`. | **CONFIRMED.** |
| T0: 398 unlogged min; honest P50 5.88 / P90 7.55 h, 4/9 over | Recomputed from `projection_c3.json` (c2 + unlogged per episode): sorted 215.8, 235.2, 261.6, 347.3, **352.6**, 364.9, 388.3, 400.1, 665.7 min. P90 by linear interpolation is 400.1 + 0.2 × 265.6 = **453 min**. | **CONFIRMED** to the minute: 5.88 / 7.55 h, 4/9 over 360 min. |
| T4b: retry resets the clock | `scripts/episode/autopilot.py:818` `run_budget.reset_clock(...)`; `run_budget.spent_before` skips rows that ended before the stamp | **CONFIRMED.** In the ep21 events I see `parked over_budget` (10-07 07:35Z) and then `retry` (10-08 04:46Z), which gave the episode a fresh 5 h. |
| T4c: plan rungs cost 0 s | `studio/plan_ladder.py:114` `Rung(IMPROVE, 0.0, …), Rung(MODEL_TIER, 0.0)` | **CONFIRMED.** |
| T2: the drive is killed by people, never by the autopilot on code_moved | `run_loop` returns on `code_moved` and kills nothing. `set_paused` only writes `series.json` and does not stop a live drive. The one autopilot kill path is `rescue_engine` (an engine hang). ep21's events alternate `stale_lock` and `retry` minutes apart. | **CONFIRMED.** No boundary stop exists anywhere (grep for a stop flag in `step_runner`, `take_ladder`, `judged_gate`: none). |
| T3: the best draft lives only in memory | `Desk.best` and `Desk.drafts` (`plan_ladder.py:190-340`) reach disk only in `terminal()` / `best_refused()` | **CONFIRMED.** **Refinement:** `drafts` (the battery-passed drafts with their critic verdicts) is in memory too, so a killed critic climb loses them as well. The checkpoint must hold both. |
| T §3.1: the budget almost never binds in-run | I counted `gate:"budget"` learnings rows, ep19-27 | **CONFIRMED and sharper: 1 budget terminal in 9 episodes** (ep19), and 0 headroom overdraws. The in-run budget is not what puts an episode over 6 h; relaunch waste is. |
| **NEW (not in T): a partly rendered round 0 parks at a spent clock** | `scripts/episode/step_09_shoot.py:203-215`: `round_zero` is "no kept take yet". With some takes on disk and the clock spent, the step raises `REFUSED: the takes want … s`. | **CONFIRMED by code.** An honest, never-reset clock would hit this after any kill mid-round-0. Design call (c) must fix it, or it parks the episode forever. |
| **NEW: the plan battery mixes builder refusals with taste lines** | `scripts/episode/plan_check.py:255-372`. TAKE BUILDER, G-TAKELINT dry build, TAKE LENGTH, ONE PER TAKE and CAST BOUND are refusals a **downstream script repeats**. G-LIGHT, G-ARTICLE, G-CROWD, QUOTE, G-PHANTOM and the rest are judgement. | **CONFIRMED by code.** "Ship the best plan at the ceiling" crashes at step 06/09 when the best plan carries a builder line. (c) needs the split. |
| T6: QC runs Whisper before its cheap rows | `scripts/episode/qc.py:326-367`: `heard_on_master` is built inside the first dict, before `edit_report`/`presence` | **CONFIRMED.** **Trap:** `verdict()` reads `all(row["passed"] for row in report["lines"])`, which is True on an empty list. A fail-fast report must mark lines **unmeasured** so it can never read as heard. |
| R3/R5: the VL reader is seeded; the cache freezes any parseable answer | `ComfyUI_Qwen3-VL-Instruct/nodes.py:109` `torch.manual_seed(seed)`; `:223` `generate(temperature=…)` with no `do_sample`; `studio/comfy.py:450-462` `cached_text` | **CONFIRMED.** |
| R §3.3a: negated hair counts as authored, 117/281 | Re-ran `R_hairparse.py` (`uv run python -I`) | **117 CONFIRMED, one correction.** It is **not** true that "every one yields `''`": about 13 of the 117 carry a real colour from another clause (grey ×4, dark ×2, red ×2, bald, brown, fair). The fix must work **per clause**: a negated clause names no layer, and the other clauses still do. |
| R §3.3b: the adjacent colour | Same run: 21 disagreements. The real faults are Gregg (bald → red), Mary Lennox ("red in her cheeks") and the Scarlet sandy rows. Mrs Elphinstone, Ogilvy and the landlord ("brown flecked/threaded with grey", "auburn greying") must stay grey. | **CONFIRMED**, with the grey-modifier rule. Gregg is in no shipped `looks.json`: WotW has none under `library/`, so the tables are derived. **Also found:** `HAIR`'s `fair` row has no word boundary (`tow` matches "towards", `fair` matches "affair"). |
| R §3.1: the G-FRAME 0.22 MCU floor flags the owner's good episodes | `R_gframe_owner.json`: ep05 MCU flag 2/7, ep07 5/6 | **CONFIRMED.** |
| R §2.2: neutral-tile call sites | `refs_pack.py:20 T2I`, `sheet_ladder.py:89 row.get("workflow") or T2I`, `book_title.py:79` literal; comfy_studio is on `poc/2k-video-pipeline` | **CONFIRMED.** `git status` shows no uncommitted edits to either `book_title` file. |

**A process fault of mine, logged honestly:** a `find /d/ /c/ -maxdepth 6` that I ran to locate the VQA node is exactly the drive sweep `hdd_guard` (3291abb) forbids. It ran for less than 60 s and I stopped it (TaskStop). The node path is `studio/comfy.py:21 COMFY_ROOT`. Skill line in §5.

---

## 1. BUILD list, in commit order (CPU, test-first, $0; no test touches the GPU or a paid API)

- **[arch]** commits update `architecture/index.html`, `architecture/README.md` and a decision file `architecture/decisions/2026-10-11_cycle3_honest_clock.md` in the same commit. They also add a `docs/DECISIONS.md` line naming §4 as the ruling.
- Commit explicit paths only. Never stash, checkout or reset. A commit restarts the autopilot loop (memory: autopilot), so **pause the series before commit 1 and resume after the last**.

| # | Commit | Conf. | Acceptance test (written first, must fail first) |
|---|---|---|---|
| 1 | **T1: the plan climb checkpoints its best draft and state every rung.**<br>`Desk.remember()` writes `plan.climb.json` atomically: `best` (doc, n, faults), `drafts` (doc + verdict), merged `refusals`, rung index, `escalated`, plan sha8, code sha8.<br>On the next run, `Desk` restores **the drafts, never the verdicts**. Each restored draft is re-judged under today's battery (≈ 15 s) before it competes, because the code may have moved (LESSONS A75, memory *a cure is judged by every gate*).<br>A signature or a deferral retires the file. | 95 % (4 cut climbs restarted worse: ep17 1→38, ep22 35→46, ep26 5→6, ep13 0→22; 111/329 rung verdicts had a worse draft on disk) | (a) A FakeModel climb killed after rung 2 (raise inside the writer) resumes from the **best** draft and its merged refusals, not the last draft.<br>(b) A clean climb writes byte-identical `plan.json` and `plan.verdict.json` with and without the checkpoint.<br>(c) A checkpoint whose code sha differs re-judges the draft, and a draft that now passes is not left refused.<br>(d) A signed plan leaves no `plan.climb.json`.<br>(e) Replay: on `rungs.json`, the 4 cut climbs' restart counts become their best-so-far (CPU, recorded in the commit message). |
| 2 | **T2: QC fail-fast.**<br>`qc.main` measures the cheap rows first: loudness, true peak, length/Short, title card, `edit_report`, the cuts, `episode_sound.presence`, the gap, speech-over-gap.<br>If a hard one fails, it writes the report with `"lines": null, "lines_measured": false` and exits FAIL **without** Whisper.<br>`verdict()` treats unmeasured lines as **not passed**.<br>A pass still runs every row. **Precondition:** the builder times each cheap row on the ep27 master. A row over 30 s moves after Whisper, and the move is recorded. | Issue 95 %; saving 85 % (10/14 QC-fail runs were cheap rows, by commit text) | (a) A FakeTranscriber that counts calls is called **0** times when the edit gate fails and once per line on a pass.<br>(b) `verdict({... "lines": None ...})` is False.<br>(c) A passing master's report is byte-identical to today's apart from key order: `lines_measured: true` is added, and a test pins the key set.<br>(d) `step_11` reuse still keys on sha8 + `measures_sha8`, and a FAIL fast-report is reused only on identical bytes and code. |
| 3 | **[arch] The honest clock: the process, not the step.**<br>`episode_run` opens a run row in a new `clock.jsonl` (run_id, pid, started) and a daemon thread beats `last_beat` every 60 s (atomic rewrite of `clock.open.json`). A clean exit closes the row.<br>The next run closes any orphan row as `killed`, ended at its last beat.<br>`run_budget.spent_before` = **the union of run spans** (closed rows, plus orphans to their last beat), from the first launch.<br>`timing.jsonl` stays as it is for the per-stage report. | 95 % (398 machine-min invisible, 23 kills, 6 episodes) | (a) A FakeClock run "killed" (the thread stopped, no exit) counts to its last beat (±60 s).<br>(b) Overlapping or nested spans are counted once: two runs with overlapping spans give the union.<br>(c) Replay on the WotW ep19-27 records (drive.jsonl starts plus DB events as the beat stand-in): spent equals T's machine minutes ±2 %.<br>(d) The command-center progress view reads the new figure (its tests updated, not deleted). |
| 4 | **Retry stamps an attempt; it never resets the ceiling.**<br>`autopilot.retry` keeps `retire_brain` and writes `clock_reset.json` as `{"attempt_at": …}` for the audit. `spent_before` ignores it.<br>The ladders' own round counters (A55-A57) are untouched. | 95 % by code (67 retries, 4 over_budget parks each retried into a fresh 5 h) | (a) After `retry`, `spent_before` equals the value before it.<br>(b) The brain folder still moves aside.<br>(c) The audit stamp is written.<br>(d) The existing test asserting the reset is **rewritten to the new rule**, never deleted, and the commit names it. |
| 5 | **[arch] At the ceiling: take the best, flag it and continue; never park on the clock.** Five changes:<br>(i) **Firsts are never refused, only repeats.** `step_09.affordable` treats every take **missing on disk** as round 0 (`share_missing > 0` → render the missing takes, no retakes). The same rule applies to any step whose outputs are absent: grids, panels, lines, assemble.<br>(ii) `studio/autopilot.derive` drops the `clock_spent` park. A dead drive with a spent clock relaunches into terminal mode.<br>(iii) `episode_drive` no longer stops on `over_budget`. It resumes, and every ladder is already terminal through `affordable`.<br>(iv) **The plan battery at a spent clock:** `plan_check` tags each refusal `BUILDER` (a downstream script repeats it: TAKE BUILDER, G-TAKELINT, TAKE LENGTH, ONE PER TAKE, CAST BOUND, CONTRACT) or `JUDGED`. The builder must cite each BUILDER line's downstream refusal. The plan terminal then follows the tag. A best draft with only JUDGED lines signs `keep_best` and is flagged. One with a BUILDER line climbs the ladder once more over the clock (≤ 3 rungs); if it still carries one, it **stops** (a SAFETY refusal).<br>(v) **The SAFETY set** is the only thing that stops a spent-clock episode. It is a closed list in `gate_policy.SAFETY`, so each entry can be vetoed:<br>• a master over the Short length or with no title card<br>• a line not heard<br>• an unjudged take, or stale takes (edit provenance)<br>• LUFS/true peak still out of band after `master_loudness`<br>• a plan BUILDER line<br>• money walls, publish auth, GPU lost<br>Everything else at the ceiling (taste gates, sound cues, gaps, cut misses) ships flagged on the audit sheet. | 95 % on the mechanism (code; the round-0 hole is code). The policy is §4 D3. | (a) Spent clock, 10 of 24 takes on disk: step 09 renders the 14 missing takes and **no** retake. Today it raises.<br>(b) `derive` with a spent clock and no proc returns a relaunch, not PARKED.<br>(c) A FakeModel plan at a spent clock: JUDGED-only lines sign keep_best flagged; a BUILDER line climbs at most 3 rungs, then raises a SAFETY refusal.<br>(d) A QC fail on a sound cue at a spent clock signs the master flagged; one on a line not heard stops.<br>(e) A relaunch loop guard: a third consecutive spent-clock run that ends anything other than completed or SAFETY parks with reason `clock_loop` (a backstop, not a policy). |
| 6 | **Plan rungs priced; shares re-priced on the measure.** `ladder()` gets `Rung(IMPROVE, 240)` and `Rung(MODEL_TIER, 90)`, the measured medians. `EPISODE_SHARES` takes T §3.3's table (02 = 70, 07 = 22, 08 = 22, 09 = 105, 11 = 20, ladders 20, judges 6 …, summing to 300). The ceiling stays **5 h**. | 95 % that the old shares are fiction (`stage_p90.json`). Behaviour-neutral below the ceiling, because headroom pays (1 budget terminal in 9 episodes). | (a) The shares sum to 1.0.<br>(b) A FakeClock plan ladder below the ceiling runs every rung as today (same rung names, same writes).<br>(c) At a spent clock the plan ladder goes terminal (commit 5's rule).<br>(d) A replay of the ep19-27 learnings shows today's 1 budget terminal and no new one below 5 h. |
| 7 | **[arch] T1b: stop at a boundary.** `autopilot pause --at-boundary` writes `stop_at_boundary` in the episode home. The boundaries that read it are:<br>• `step_runner.run_steps` between steps<br>• `judged_gate.climbed` between rungs<br>• `take_ladder` between rounds<br>• `takes_r2v` and `grids.py` between units (a take or a grid is idempotent on disk)<br>The run then exits `paused_at_boundary` with every clock row closed. The autopilot reads it as PAUSED, not crashed. The longest wait is one unit (≈ 4 min take, ≈ 5 min grid, ≈ 4-10 min plan rung). | 90 %, raised to build by the measure: 22/23 kills were session pause→fix→retry, 527 waste-min, the top cause | (a) A flag set during step N: step N finishes, N+1 never starts, and the exit is `paused_at_boundary`.<br>(b) Inside a FakeRenderer takes loop, the flag stops after the current take; the resume renders only the missing takes.<br>(c) The flag is consumed on resume.<br>(d) `derive` maps the exit to PAUSED, never to a crash count. |
| 8 | **Look table (a): a negated clause names no layer.** `layer_of` returns `''` for a clause whose layer word sits inside `no\|not\|never\|without\|gives no\|does not (give\|describe\|specify)` within the same clause. | 95 % (117/281 dossiers, 29 books) | (a) Watson, Lestrade, Utterson and Van Helsing give no hair layer and reach the commit-6 row fallback.<br>(b) The ≈ 13 rows with a real colour in another clause keep it.<br>(c) The WotW look tables are byte-identical.<br>(d) Jekyll and Hyde are still refused. |
| 9 | **Look table (b): the colour next to "hair".** Take the colour adjective adjacent to `hair\|haired` (the reader's `SEEN_HAIR` shape). Keep grey when a grey/white modifier sits in the same hair clause ("greying", "flecked/threaded with grey"). Add `sandy` → `fair`. Put `\b` on `fair`, `tow`, `blond`, `dark` and `brown`. Fall back to first-of when no colour is adjacent. | 95 % (Gregg, Lennox, 2 Scarlet sandy rows) | (a) Gregg reads red; Lennox reads `''` (no hair colour; cheeks are not hair); "grey eyes under sandy hair" reads fair.<br>(b) Elphinstone, Ogilvy and the landlord stay grey.<br>(c) "towards" does not read fair.<br>(d) The WotW tables are byte-identical **except Gregg**, which no shipped file holds.<br>(e) No file under `library/` changes (git status assertion). |
| 10 | **G-FRAME floors, still advisory: MCU 0.15, close 0.25.** | 95 % that 0.22 is wrong (7/13 owner-good MCU flagged); 70 % on the new line, which is why it stays advisory | (a) On the owner-judged set, 0.15 flags 1/13 good and 3/6 bad MCU panels.<br>(b) The ep12-27 replay flags 14/84 MCU and 2/23 close.<br>(c) The verdict, ladder and terminal are unchanged on the fixture. |
| 11 | **Skill lines and retirements** (§5): J1's correction of carry #9, the retired list, and GATES for the clock, SAFETY and the boundary stop. **Eye job (CPU, ≈ 10 min), to close H5 harder:** full-resolution crops of the 6 plain-wall narrator frames (ep20 T20, ep22 T03, ep27 T24, ep18 T13, ep21 T16, ep24 T16). Any translucent face reopens H5; 0/6 closes it. | 100 % on the text | The suite is no redder than the 4 pre-existing reds. |
| post-bench P1 | **Neutral tile in production (new draws only).** One new file, `comfy_studio\workflows\image\image_krea2_cinematic_2x_neutraltile_visurena.json`, plus its manifest, carrying the **winning arm** of bench block 2 (or arm (a) if none passes).<br>`refs_pack.T2I` names it.<br>`sheet_ladder.job_from_row` maps the old `image_krea2_cinematic_2x` to `T2I` for a **new** draw; the row's recorded name stays as history.<br>**`book_title.py` is not touched** (§4 D7). | 100 % mechanics, owner-ruled | (a) `comfy.load_workflow(refs_pack.T2I)` resolves, so a comfy_studio checkout without the file fails loudly.<br>(b) The graph diff against `_presave_neutraltile` differs only in nodes 13/14 (one save).<br>(c) Every existing pack row and fixture keeps its literal name.<br>(d) `test_the_book_main_title` is untouched and green. |
| post-bench P2 | **Confirm-before-refuse** for `panel_content`, `take_content` and LOOK-STATE HARD faults. **Built only if block 1 passes its rule.** Two more cached reads at seeds +100/+200, run only when the first read raises a HARD count, boolean or head-marker fault. Refuse on 2 of 3. A pass stays one read. | from the bench | (a) A FakeReader with a 1-of-3 fault passes and a 2-of-3 fault refuses.<br>(b) A pass costs exactly one read.<br>(c) **Owner-fixture replay** (ep05/ep07 good, ep08/ep09 bad, CPU over the cached reads plus the bench reads): **no** bad-episode refusal vanishes. |
| post-bench P3 | **`bowler` joins the brimmed family**, only if block 3 reads ≥ 2 real bowler looks as `other_hat`/`felt_hat` on ≥ 2 of 3 seeds each | from the bench | commit-4's (C2) re-judge stays green, and a boater still refuses |

**Not built (and why):**
- **T #4 "drive refuses a resume on a moved SHA unless `--fix-lands`".** Under zero human input the autopilot would pass the flag every time, so it is a refusal nobody can read. The lever is commit 7 (no in-flight loss) plus commits 3-5, which make a mid-episode fix spend the episode's own clock (§4 D4).
- **A downstream reserve on headroom** (rungs spend only what the remaining firsts don't need). The budget bound once in 9 episodes, so the hypothesis has no measure. It is open (§6).
- **J4** (take_content count needs 2 frames), **J5** (pit≠cliff, scenery lettering≠caption), **J6** (repetition loops): §6.
- **H2 battery-side cure router, patch-mode improve, model_tier-first:** each changes the drafts. They need the 48-climb CPU replay first (§6).

---

## 2. ONE GPU bench, ≤ 60 min

**Preconditions:**
- Commits 1-11 have landed, and the series is paused (the autopilot is idle).
- ComfyUI is up with an empty queue. **Never relaunch it**; if it is down, stop and tell the owner.
- No output goes under `library/`. Renders go to `scratchpad\c3b\`, evidence to `docs\audit\2026-10-10_continuity_retro\bench_evidence\c3\`.
- New workflows are new files only.
- Each block is independent. A stopped block is logged and never retried. **Hard stop at 60 min.**

| Block | What | Work | min | Pass / stop rule |
|---|---|---|---|---|
| 0 | Engine and queue check. Determinism probe: re-read **one** cached panel (ep14 s22) at seed 11 through `run_text`, uncached | 1 read | 2 | It must equal the cached text byte for byte. If it does not, **stop block 1**: the "deterministic per input" premise (R3) is false and block 1 has no control. |
| 1 | **J2: is it the seed or the pixels?** 12 shipped panels: 6 with 2+ people, 3 night, 3 with signage, and **at least 4 that were refused on a count or text field at shipping** (from `R_refused_panels.jpg`). Read each at seeds 111, 211 and 311 (seed 11 is the cache). Then a new workflow, `image_qwen3vl_caption_beam2_visurena.json` (AILab node, `num_beams 2`, `repetition_penalty 1.0`), reads the same 12 twice. | 36 + 24 reads | 22 | **Seed flip rate** = per-field disagreement with seed 11 (people, lookalikes, hour, text, landform, posture). P2 is **built only if** HARD-field flips ≥ 5 % of field-reads **and** they occur on ≥ 2 panels. Below that, it is a measured "no": the instability is the pixel term, and confirming on the same pixels buys nothing. Beam-2 is **data only**: self-agreement, seconds per read, and agreement with seed 11. It is not adopted this cycle, because it changes every answer and would need every gate replayed. **Stop the beam arm if the clock passes 30 min.** |
| 2 | **Streak arms (R §2.3).** A new tile-only workflow, `image_krea2_upscale2x_neutraltile_visurena.json` (LoadImage → USDU with the bench's nodes), run on the 4 `c2b\looks\*_1x.png`. Arms: (a) today's neutral (the control); (b) denoise 0.15; (c) the tile words minus "brush stroke colour texture" and "high contrast"; (d) (c) plus the look's own wardrobe nouns. | 16 Krea2 tiles | 9 | **Pass** = 0 ghost faces by eye **and** a streak index ≤ 1.2× today's subject-prompt tile **and** trouser Laplacian ≥ 90 % **and** head facenet vs 1x ≥ arm (a). Arm (d) must also show 0 faces in the cloth. **First passing arm in the order (c), (b), (d) wins**: the fewest words and the least change. None passing → P1 ships arm (a), as the owner already saw and ruled. |
| 3 | **H7 bowler.** CPU first: grep Scarlet `refs.json`/cards for bowler/billycock rows with a picture on disk. Read each picture's LOOK-STATE at seeds 11/111/211. | ≤ 6 reads | 2 | Fewer than 2 pictures on disk → **retire H7 until a book has one** (no render to make one). |
| 4 | **The clock in the wild (the commit-3/5/7 smoke).** No render. Launch `episode.py` for a **scratch copy** of the ep27 home under `scratchpad\c3b\clockhome\`, using a book-neutral fixture with every step's outputs already present. Set `--at-boundary` after step 05 and kill the process with `Stop-Process` once during step 06. | 0 GPU | 5 | The killed span is counted to its last beat ±60 s. The boundary exit is `paused_at_boundary`. The resume renders nothing that exists. If any of these fails, the clock commits are reverted **before** the final replay. |
| — | Model loads (Qwen-VL cold ≈ 3 min, Krea2 ≈ 2 min), slack | | ≈ 15 | |
| | **Total** | | **≈ 55** | |

**Not in this bench:** J4 and J5 (rule changes; CPU replay first), a merged LoRA (retired), 992 and P-WORDS (ruled no), and the Jekyll probe (skipped by ruling).

---

## 3. The FINAL replay measurement (after the build and the bench)

The aim is one honest before-and-after on the fixed replay set, under the full pipeline as it stands after cycles 1-3. **Before** = the shipped files. **After** = today's code and workflows. Two parts.

### 3A. CPU: the clock replay of ep19-27 (≈ 20 min CPU)
Re-run `ledger.py` and `projection_c3.py` under the new rules:
- the run-span union clock;
- no reset;
- T1 (each cut plan climb loses at most the rung in flight);
- T2 (0.7 × the cheap-row QC failure minutes);
- T1b (the session kills become boundary stops: in-flight loss ≤ one unit);
- the ceiling rule (rungs after the honest 5 h mark become terminals; missing firsts still render).

**Report per episode:**
- machine minutes;
- the step at which the clock crossed 5 h;
- **the quality price**: how many ladder rungs (learnings rows with a timestamp) ran after that mark and would now be terminals, with which gate;
- the P50/P90 and the count over 6 h.

**My projection, to be checked by this replay** (from `projection_c3.json`, my arithmetic):

| Scenario | P50 | P90 | over 6 h |
|---|---|---|---|
| Honest baseline (C2 as built + unlogged) | 5.88 h | 7.55 h | 4/9 |
| + T1 + T2 + T1b (code only) | ≈ 5.3 h | ≈ 6.7 h | 2/9 (ep20, ep21) |
| + the no-reset ceiling, terminals at 5 h, firsts always | ≈ 5.3 h | **≈ 5.9-6.2 h** | 0-1/9 |
| Relaunch-free floor (T's measure) | 4.24 h | 4.85 h | 0/9 |

**The price of the third row:** ep20 and ep21 cross 5 h and finish on terminals, so they ship flagged instead of rescued. 3A counts those rungs. **If 3A shows any episode where a firsts-only floor after the crossing exceeds 60 min**, i.e. the crossing came before round 0, the P90 claim is restated with that case named. The guarantee is "rungs stop at 5 h", not "the episode ends by 6 h", because round 0 always renders.

### 3B. GPU: the picture replay (≤ 120 min, a separate session after the bench, the series paused)
Every item is scored on the same columns as cycles 1-2: facenet vs sheet, G-TAIL, invented speech, seams, ghost faces by eye, streak index, G-FRAME face_h, `panel_content` HARD faults (single-read, plus confirm-before-refuse if P2 was built), G-SETUP room match, lip lag on dialogue. Each item first states **whether it is expected to be bit-identical** (unchanged inputs: determinism is proved) or **changed** (and by which commit).

| Set | Items | Expected change |
|---|---|---|
| WotW narrator | ep25 `fulham_road` and ep27 `study_table` regrids. The narrator look pictures are drawn **new** under P1's tile, then the grid at the shipped seed, then the regrid bar (face-visible). | changed (P1). Must keep beard 3/3, 0 ghosts, regrid bar PASS. |
| WotW house | ep26 villa, ep27 study reverse, the ep11 study, the dining room: G-SETUP and seams under no-strips | identical, unless a look redraw feeds them |
| WotW phase-0 | S2-S6 and D1-D2 takes: narration on CK8, dialogue on BASE | identical to the cycle-1/2 renders (a control) |
| Scarlet | ep14 s22/s24, ep05, ep03, ep07: Holmes and Watson faces, 221B, one dialogue take (lip lag), one exterior | identical pictures. The gates re-judged under cycle 1-3 code (headwear family, G-FRAME, look-table head fallback in scratch) |
| **Gate regression** | the owner-judged fixtures, ep05/ep07 good and ep08/ep09 bad, through **every** gate | good stays passing; **no bad refusal vanishes** |

**Done** = the 3B table with before and after per row, the 3A table, and `CYCLE_3.md` with the deliverable path first. Then the architecture page is **republished to claude.ai** (CYCLES log: owed at the end of cycle 3).

---

## 4. Decisions made on the owner's behalf (each with its reason; veto any line)

| # | Decision | Reason |
|---|---|---|
| D1 | **The clock is the process (a 60 s run heartbeat, a union of run spans), not per-step open rows.** | Per-step open rows still miss the time between steps and the judges, and nested rows double-count. A run span catches all of it and a kill loses at most 60 s. The per-stage report keeps `timing.jsonl`. GPU-lock waits count as this episode's time, because one episode runs at a time. |
| D2 | **`retry` never resets the clock.** The ceiling is one per episode, from the first launch to public. | 67 retries made the 6 h unmeasurable. The reason for the reset (ep19: "code faults spent the ceiling before the takes were judged") disappears under D3: a spent clock no longer stops an episode; it only removes rescue rungs. |
| D3 | **At the 5 h ceiling: missing firsts always render; every ladder takes its best and signs it flagged; the episode never parks on the clock. Only the closed SAFETY list stops it.** The SAFETY list: Short length or no title card, a line not heard, unjudged or stale takes, loudness out of band after the leveller, a plan BUILDER line, money, publish auth, GPU lost. Sound cues, gaps, cut misses and every taste gate ship flagged. | This is the owner's order, refined. "Take the best" cannot apply to a plan line a downstream builder will refuse anyway: it would crash at step 06/09 and relaunch-loop. Parking needs a human, and the owner ruled zero human input. The cost is fewer rescues on over-clock episodes, and it is counted in 3A. |
| D4 | **Resume on moved code: allowed, but only from a boundary.** No refusal on a moved SHA. | Fixes must land in an unattended series. The loss was the **in-flight** minutes (killed mid-step), which commit 7 removes. The redo a real fix forces is correct work, and it is now charged to the episode's own clock, so it is visible and bounded by D3. |
| D5 | **The ceiling stays 5 h (internal), not 6.** | The hour between them pays for the always-render firsts and the terminal pass after the crossing (measured in 3A). Raising it to 6 h would put every crossing episode over 6 h. |
| D6 | **Confirm-before-refuse: bench first (block 1), not built blind.** | The 12.7 % flip mixes pixels and seed (R4). If the seed term is near 0, two extra reads on the same pixels cost +5-12 min per episode and change nothing. If it is ≥ 5 %, P2 is cheap and halves false refusals. The bench decides; the owner fixtures guard against false passes. |
| D7 | **The neutral tile: refs_pack.T2I and sheet_ladder's reseed map switch. `book_title` does NOT switch.** | A title plate carries drawn lettering, and a subject-free tile at 0.2 denoise on lettering is unmeasured. No new book is being started, so no plate is drawn before the next book. The peer session's file stays untouched. Revisit at the next book's title bake with a 2-plate A/B (≈ 2 min). |
| D8 | **The streak mitigation is benched before the switch, so the switch lands once.** | No episode draws new looks until the next book. Waiting costs 0 min, and it avoids two successive production picture changes. |
| D9 | **G-FRAME advisory floors: MCU 0.15, close 0.25. It never goes hard on this evidence.** | 0.22 flags 7/13 owner-good MCU panels. The owner's bad episodes were bad for other reasons, so the gate cannot be validated as a wall. |
| D10 | **Plan rungs are priced (240/90 s) and the shares re-priced; the plan never parks on the clock.** | It makes the plan stage visible to the one clock. Below the ceiling it changes nothing (headroom pays; 1 budget terminal in 9 episodes). At the ceiling, D3 applies. |
| D11 | **Retired:** H1 (narrow fault-set memory), H5/H6 (ghosts in takes / a ghost gate), H8 for WotW (G-LINEAGE stays advisory), the merged LoRA, and T #4's moved-SHA refusal. | H1: ep22 61→44→4 and ep21 50→13 progressed after ≥ 3 stalls. H5: 0/20 takes, plus commit 11's 6-frame full-resolution close. H8: no WotW cast-wide set exists. The merged LoRA saves ≤ 3 min at P90 against a 21 GB re-bake. T #4: §1. |
| D12 | **Content-rule calibration (pits read "cliff", signage reads "text") is not changed this cycle.** | The 21 panels are by eye on true reads. A looser rule risks false passes, and it needs an owner-fixture replay first (§6). |

---

## 5. Skill lines (each lands with its commit)

**LESSONS.md:**
- **The clock you budget against is not the clock you spend (commit 3).** 398 of 3,499 machine-min over ep19-27 sat in killed steps the step clock never logged. Time the process with a heartbeat, not the step on exit.
- **A reset clock is no clock (commit 4).** 67 retries each opened a fresh 5 h. A ceiling binds only if nothing can zero it.
- **The clock refuses repeats, never firsts (commit 5).** A spent clock with half the takes on disk refused the other half, and the episode could never finish. Missing work always renders; only rungs stop.
- **Stop at a boundary, never mid-step (commit 7).** 22 of 23 killed runs were sessions landing a fix (527 waste-min). `autopilot pause --at-boundary`, wait one unit, then commit.
- **The best draft goes to disk every rung (commit 1).** A killed climb restarted from the last draft 111 times out of 329 rung verdicts when a better one existed. Restore the draft, re-judge it, never trust an old verdict.
- **A cheap fail before an expensive one (commit 2).** 10/14 QC failures were loudness, cue and edit rows that take seconds. Whisper only runs on a master that can still pass. An unmeasured line is not a heard line.
- **A dossier says what it doesn't say (commit 8).** 117/281 physicals list "hair" inside a negation. Negation scopes the clause.
- **Same pixels, same size (J1, corrects CYCLE_2 carry #9).** The S6 "no-op crop" was a 1024→768 resample, and the reader tiles those differently. On truly identical pixels it agreed 2/2 and is deterministic by code. The real instability is a single sample on near-identical frames (6-16 % on count fields), frozen by the cache.
- **Never sweep a drive to find a file (skeptic's own slip, 2026-10-11).** The ComfyUI root is `studio/comfy.py COMFY_ROOT`; read the constant.

**GATES.md:**
- **Clock:** one ceiling per episode (5 h, a run-span union, no reset). Past it, rungs are terminal and flagged; missing firsts render; only the SAFETY list stops.
- **SAFETY (closed list):** Short length or title card, line unheard, unjudged or stale takes, loudness after the leveller, plan BUILDER lines, money, publish auth, GPU lost.
- **Plan battery lines** are tagged BUILDER or JUDGED. At a spent clock, JUDGED lines sign keep_best flagged.
- **G-FRAME (advisory):** MCU < 0.15, close < 0.25.
- **The reader** (`panel_content`/`take_content`/LOOK-STATE): one seeded, cached read. A cached refusal is never re-read; only a redraw escapes it. (Plus the P2 line if built.)

**SKILL.md:**
- "Landing a fix during an episode: `autopilot pause --at-boundary`, wait for `paused_at_boundary`, commit, `resume`. Never kill a drive."
- "A spent clock ships the episode flagged. Read the audit sheet; never `retry` to buy hours."

---

## 6. What stays open after the three cycles

1. **The P90 is bounded by policy, not by speed.** Code removes about 0.85 h of the honest P90 (7.55 → ≈ 6.7 h). The rest is held by the ceiling rule, and its price is rescue rungs on about 2/9 episodes (3A counts them). A faster P90 still needs the plan battery climbs to shrink: H2 (battery-side cure replay, CPU, ≈ 0 GPU), patch-mode improve and model_tier-first, each replayed on the 48 real climbs first.
2. **The redo after code moved (357 min over ep19-27)** is real work when a fix changes inputs. Only fixing on the replay set before the series runs reduces it. That is a discipline, now visible on the clock.
3. **The downstream reserve:** rungs that stop early enough to leave the remaining firsts their time. No measure exists yet (1 binding in 9 episodes). Revisit if 3A shows a pre-round-0 crossing.
4. **Reader reliability beyond the seed:** J4 (count on ≥ 2 frames or the last), J5 (rule calibration on the 21 panels against the owner fixtures), J6 (1.3 % repetition loops, a full 1,024-token decode each), and beam-2 adoption (it changes every answer).
5. **Look:** stubble wording; the Jekyll/Hyde base sheets (still refused, the probe skipped); H4 (a track-aware `look_id_at`); H7 if no bowler is on disk; the APPEARANCE regex precision.
6. **Framing:** a tight size is still drawn about a size wide (MCU median 0.207). Words bought +0.04 with costume drift; a bigger canvas drew wider. There is no cure at 95 %. H3, H9 and H11 (Qwen-Image-2.1-Turbo) need their own eye sheet.
7. **Audio:** room tone (needs a `speech_end` that ignores the bed), the Scarlet dq lag blindness, CK for dialogue (a measured no until an arm passes the sounding-tail pair).
8. **Carried shipped faults, never overwritten:** ep10/T21, ep26/T25, the Hope and Brigham Young redraws (Scarlet), and the narrator base sheet ghost (staged ep18-27; no ghost seen in takes).
9. **Housekeeping:** the 4 pre-existing reds (`test_llm` ×2, `test_canon`, `test_episode_tail`); 1,798 `tick_error` events in the WotW autopilot log are unexamined; the architecture page must be republished to claude.ai.
10. **The `book_title` plate tile** (D7), at the next book.

**Publishable (flag):**
- **"The clock you budget against is not the clock you spend":** unlogged killed-step time, reset clocks, and "refuse repeats, never firsts" as the rule that makes a ceiling enforceable in a resumable agent pipeline. Pairs with C2's "the answer already existed".
- **"Deterministic but not stable":** the seeded VLM judge plus a sticky cache, with the block-1 seed-vs-pixel split as its measurement.
- **"Dossiers that say what they don't say":** 42 % of LLM-written character dossiers across 29 public-domain books.
