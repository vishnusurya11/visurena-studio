# A. Loops, autopilot and publish-blocker faults (ep07 retro, expert A)

Read-only. Paths are repo-relative. B = `library/20260827135504_the-strange-case-of-dr-jekyll-and-mr-hyde`,
E = `B/episodes/ep07`. Times are UTC as logged. Hours are measured from the logs unless marked.

## Ranking (hours saved per episode)
| # | Fix | Saves |
|---|-----|-------|
| 1 | F2 finished-but-unpublished reaches the owner (repeating nudge + delivery proof) | up to 145 h wall (11-04 17:25 to 11-10 18:28), owner-visible |
| 2 | F1 clock_loop must not outrank a named park; a retry must break its window | the same 145 h (it hid the token cause) + ~1.7 h of 5 hand-retry gaps + 7.4 h idle (09:35 to 16:57) |
| 3 | F3 a cure order must change the fault signature, else park as gate-class | about 4-6 h machine (G-DEAD runs 2-8; wall.09 = 4.4 h) |
| 4 | F4 plan contract at preflight + plan-hash check | about 0.5-1 h wall (runs 11-12, a 27 min gap, a brain call); blocks a destructive `redo 02` |
| 5 | F5 code moves | 0 h (noise); one brake worth keeping |

## F1. Seven `clock_loop` parks, run 19 included

Evidence
- Parks at 06:25 07:03 07:35 08:42 09:08 09:35 17:25 on 11-04: `B/autopilot/events.jsonl` lines 1694, 1699, 1704, 1709, 1714, 1719, 1729.
- Every `end` row from 11-04 05:28 on is `code 1, clock_spent true` (`E/drive.jsonl` lines 31-56). Run 19's log says `charged 7.50 h` (`E/drive_launch19.log`, last line), over the 5 h ceiling (`studio/run_budget.py:23`).
- Run 19 tail: `RefreshError invalid_grant` (`E/drive_run19.log`, last line); run row `error=google.auth.exceptions.RefreshError step=13` (`E/drive.jsonl:55`).

Root cause (symptom, mechanism, rule)
1. Symptom: a token death parked as `clock_loop`; the owner was never told it was the token.
2. Mechanism: `derive()` tests `clock_loop(s)` at `studio/autopilot.py:464`, BEFORE `_ended()` at line 468. `_ended` is the only caller of `classify()` (line 422), and the token row is in `classify`'s TABLE (`studio/autopilot.py:248-249`). A true clock_loop returns PARKED, so the table never runs. The table is right alone: `tests/test_an_expired_youtube_token_parks_with_the_mint_command.py:17-19` tests `classify`, never `derive` on a spent clock.
3. What clock_loop measures (`studio/autopilot.py:437-443`): the last 3 `end` rows are non-zero AND `clock_spent`, with the current clock over the ceiling. It counts stops, not faults: it never asks whether the three stops were the same. Its docstring (line 433) calls it "a backstop against a relaunch loop".
4. Why it fired after ONE run each time: `retry()` removes the parked row and stamps `clock_reset.json`, but "the ceiling is NOT reset" (`scripts/episode/autopilot.py:1536-1548`; `tests/test_a_retry_starts_the_episodes_clock_over.py:1-12`). The 3-row window is history a retry never clears, so the first stop after each hand retry re-completes it. The third spent stop was run 11 (05:56); every failure after that parks at once. This is the 7-park sequence.
5. Was clock_loop the correct reason? Partly. Runs 13, 14, 15, 17 really repeated one signature (step 11 RuntimeError, G-PEOPLE; `E/drive.jsonl` 39-51), so a loop brake was fair there. It was wrong for run 12 (contract crash) and run 19 (a one-time fault with a known owner action).
Rule: a repeat-brake keys on fault signature (step + error class) since the last owner action, and a named park outranks it.

Fix (functions)
- `studio/autopilot.py:clock_loop`: count only `end` rows after the last `retry` (new Signals field, read from events or `clock_reset.json.attempt_at`), and require the same `(step, error)` in the matching `run` rows.
- `studio/autopilot.py:derive`: call `classify` first; if its kind is `park` (token, over_budget, safety, escalated) return that reason before `clock_loop`.
- Reason text names the signature: `clock_loop: step 11 RuntimeError x3`.

Failing tests (shape)
```python
def test_a_token_death_on_a_spent_clock_parks_as_token_expired():
    rows = [start, spent_end(1)] * 3
    got = ap.derive(_signals(drive_rows=rows, clock_spent_s=CEIL + 1, log_tail=REFRESH_ERROR_TAIL), 7)
    assert got.reason.startswith("youtube_token_expired") and "youtube_auth.py" in got.reason

def test_a_retry_breaks_the_clock_loop_window():
    s = _signals(drive_rows=[start, spent_end(1)] * 3, retries_since_last_stop=1, clock_spent_s=CEIL + 1)
    assert not ap.clock_loop(s)

def test_clock_loop_needs_one_repeated_signature():
    rows = [run("refused", "RuntimeError", "11"), end(), run("failed", "ValidationError", "01"), end(),
            run("failed", "RefreshError", "13"), end()]
    assert not ap.clock_loop(_signals(drive_rows=rows, clock_spent_s=CEIL + 1))
```
Expected effect (replay on `E/drive.jsonl`): run 19's window is runs 16, 17, 19 with three different signatures, so no loop; `classify` gives `youtube_token_expired: run ... youtube_auth.py (owner consent), then retry`, parked at 17:25 with the command. Runs 12-17 would park only after 3 same-signature stops since the last retry, so hand retries 1-2 reach `_ended` and then the brain or `retry_exhausted`. Unproven: that the owner would have stopped retrying G-PEOPLE sooner (that real loop is F3's signature rule).

## F2. `youtube_token_told` at every launch; finished episode unseen for 6 days

Evidence
- Told at each launch 11-04 03:51 to 17:23 (`events.jsonl` 1672, 1680, 1686, 1692, ... 1727). Last told 17:23:23, 91 s before the failure at 17:24:54.
- Parked 17:25:26 (line 1729). Then only: code_moved 11-05 02:55, `supervisor_died_at` 11-09 23:26 (heartbeat age 10295 s), code_moved 11-10 08:04, owner `retry` 11-10 18:28 (lines 1730-1735). Six days with no row that says "master finished, waiting on you".
- The master was done at run 19 (failure at step 13). The drive's own line: `wall 113.11 h | dead 105.61 h` (`E/drive_launch19.log`, last line): dead time dominates, not charged time.

Root cause
1. What "told" sends: `token_watch` (`scripts/episode/autopilot.py:800-811`) appends the event FIRST, then `deps.notify`, which is `scripts/episode/drive.py:74-83`: `notify_bench.py text` through `subprocess.run(..., check=False)`. A non-zero exit, a Telegram outage or a muted chat is invisible. The event proves a send was attempted, nothing more.
2. To whom: Telegram only. The text is the paste-link instruction (`scripts/publish/youtube_auth.py:87-96`; `TOKEN_WARN_DAYS = 5.0` at line 35).
3. Why it failed: it fires at LAUNCH, once per drive (`told_this_drive`, lines 792-797), so it is 20 copies of launch chatter with no state in them. The one message that mattered, the PARKED line (`scripts/episode/autopilot.py:934`), carried `clock_loop` (F1), not the token. After that nothing re-notifies: `park()` returns `parked_already` forever (lines 925-926) and `derive` pins PARKED while a parked row exists (`studio/autopilot.py:454-455`). No code watches "finished master + no public row + age".
4. `drive.py:196-206 token_lines` only prints "will park at step 13"; it neither re-probes before step 12 nor refuses.
Rule: a notification is evidence of a send, not of a person acting. An unpublished finished master is a STATE and needs a state-driven repeating alarm, not an edge-triggered event.

Fix
- New pure `studio/autopilot.py:finished_unpublished(s)` (master on disk, no public upload row, state PARKED or HELD) and `owner_nudge_due(rows, now, every_s)`.
- `scripts/episode/autopilot.py:park` and `hold`: for a finished episode the message starts `ep07 FINISHED, NOT PUBLISHED: <reason> | <exact command>` and repeats every 6 h until a public row exists or the owner runs `retry` (event `owner_nudge` with a count). Channel: Telegram (the one the owner reads) plus a `needs_owner` field in `status.json` and a board banner, so launch chatter cannot bury it.
- `drive.py:notify` returns a bool; `token_watch` and the nudge log `sent: true/false` and retry a false send next tick.
- Right after the master is signed, re-probe the token (`youtube_auth.refresh_fails`) and, on failure, park at once with `youtube_token_expired` and the finished-unpublished text, so the long wait starts with the correct message.
```python
def test_a_parked_finished_episode_is_nudged_every_six_hours(tmp_path):
    book = parked_with_master(tmp_path, reason="youtube_token_expired")
    for hrs in (0, 3, 6, 12):
        tick(book, now=T0 + hrs * 3600, notify=spy)
    assert [m for m in spy.msgs if "FINISHED, NOT PUBLISHED" in m] == [m0, m6, m12]

def test_a_failed_send_is_not_logged_as_told(tmp_path):
    token_watch(book, 7, "launch", deps_with(notify=lambda t: False))
    assert last_event(book)["sent"] is False

def test_a_published_episode_is_never_nudged(tmp_path): ...
```
Expected effect: replayed on ep07, nudges at 17:25, 23:25, 05:25 ... about 4 per day to 11-10, the first the same evening the owner was at the keyboard (pause/resume at 17:13 and 17:23). Unproven: that any Telegram message was read (no delivery receipt exists; the Telegram MCP in this session is down, but `notify_bench.py` is a separate path).

## F3. Cure orders that cured nothing; brain retired 6 times

Evidence (`E/brain_retired_NN/attempt_*.json`; `B/autopilot/events.jsonl` 1626-1689; `E/drive.jsonl`)
| set | verdict, order | outcome |
|---|---|---|
| 01 a1 | cure, redo 08 | the cited signature (`2 figures read as utterson/enfield`) fell run by run: 17, 10, 6, 4, 0 lines in drive_run02..06.log; panels redo plus mid-run fixes did cut the panel-level doubles |
| 01 a2, 02 a1 | cure, redo 06 | prompt re-author; no signature change logged |
| 03 a1-a3 | cure, redo 09 x3 | no-op: `E/drive_run07.log:34-46` STEP 09 took 14 s, every take `cached (bytes unchanged)`, then G-DEAD T10/T17 refused again; runs 6, 7, 8 each took about 2 min (`drive.jsonl` 18-24) |
| 04 | park (clamped: step '' not a step) | right on cause (EngineLost), but a park is not a cure; the engine restart was the cure |
| 05 | cure, redo 06 for G-PEOPLE shot_07 | wrong class: the lead's eye notes say a one-frame hair misread by the judge; runs 13-17 refused five more times |
| 06 | cure, redo 02 for `slowly` | right location; destructive cure over a hand-edited plan (F4) |

Root cause
1. A `redo 09` order names a STEP. Step 09's cache keeps unchanged takes (`cached (bytes unchanged)`), so the order can re-judge but cannot re-draw T10/T17. The brain wrote "retake T10 & T17 only" (`brain_retired_03/attempt_01.json` finding_row); the order schema `{kind: redo, step_id}` cannot say it. Three identical orders in 5 minutes, no memory that the last one changed nothing.
2. `triage_action` places the order and logs `brain_cure` (`scripts/episode/autopilot.py:1065-1070`) without comparing fault signatures. The cap `stops(drive_rows) > CURE_CAP` (`studio/autopilot.py:399-401`, cap 2) counts stops, not whether the same gate and shots recurred. The packet the brain gets (`studio/autopilot.py:316-325`) holds no list of orders already taken and their result.
3. The brain cannot measure a gate. Set 01 a2 declared "G-DEAD's refusal is correct, not a false gate" from log prose alone. When the fault lives in a judge or look-alike sheet (fixed by 35b7e603, 348c7390, 1029749f and the Enfield sheet), no redo can cure it and the brain cannot commit (`commit: null` in all six).
Judgement: the diagnosis of WHERE the fault first showed (panels, shot text) was plausible; the cure was wrong whenever the class was judge, sheet or engine. Right: the EngineLost park and the `slowly` location. Wrong: G-DEAD x3 (no-op) and G-PEOPLE.
What would have stopped the repeat: a signature memory. Signature = (refusing gate, sorted failing shots, step). An order is a cure only if the signature changes after it runs; the same signature twice means no repeat of that order, and the episode parks as `gate_class: <gate>` with evidence for the fixer rung (`.claude/skills/fix-parked`) or the owner.

Fix (functions)
- `studio/autopilot.py:packet`: add `orders_tried: [{order, sig_before, sig_after}]` read from events.
- `scripts/episode/autopilot.py:triage_action`: refuse an `(order, signature)` pair that already ran and left the same signature; park with `cure_no_change: <order> x2 <sig>`.
- `studio/work_orders.py` and `studio/step_runner.py`: let `redo` carry `take_ids` (clears those takes' cache), or make the step report `retook 0 of 2 named` and fail the order when it retook nothing.
```python
def test_the_same_cure_twice_with_the_same_signature_parks():
    events = [brain_cure(redo="09"), drive_end(sig="G-DEAD:T10,T17@10"),
              brain_cure(redo="09"), drive_end(sig="G-DEAD:T10,T17@10")]
    d = triage_action(book, codex, 7, "cure", {"order": {"kind": "redo", "step_id": "09"}}, deps_with(events))
    assert d["state"] == "PARKED" and d["reason"].startswith("cure_no_change")

def test_a_redo_of_09_that_retakes_nothing_is_a_failed_order(tmp_path): ...
```
Expected effect, replay on ep07: orders 03 a2 and a3 and runs 7-8 are cut and the episode parks at 12:41 on 10-31 with a gate-class tag, not 3 launches. Those no-op runs cost only about 7 min; the hours are upstream: `wall.09` 12 rounds = 4.4 h and `wall.07.order` 7 rounds = 0.75 h (`E/attempts.json`), which a gate-class park would route to the judge fix first. Unproven: how many of those 4.4 h were avoidable; the judge fix landing on 11-02 (1029749f) is what ended the clone read, not any order.

## F4. Hand edit of plan.json reached the drive (runs 11, 12)

Evidence: run 11 crashed at step 01 on `Episode.shots[7].motion` ('slowly', `E/drive_run11.log:60`); run 12 refused at step 06; brain set 06 ordered `redo 02`. `plan.json` differs from `E/plan.json.bak_2026-11-03_shot07` in shot 07's at_rest, changed and end text (not only motion), and `E/plan.verdict.json` still says `plan_sha8 21e108cb`, dated 10-30, signed before the edit.

Root cause
1. The contract is enforced at WRITE (`studio/episode_home.py:63-72 write_plan`) and at LOAD (`:75-77 load_plan`, "a plan that fails here never renders"), but a hand edit bypasses write, and the first load is inside step 01 (bind): after the launch, the lock and a run row. The launch gate `scripts/episode/drive.py:186-190 preflight` checks the chapter audit, standing approval and token age, not the plan.
2. `scripts/episode/handbook.py:41` documents `Episode(**json...)` printing VALID as a manual step; it was not run.
3. The verdict binds the plan by sha8 (`studio/plan_verdict.py:24`), but nothing compares it at launch, so a post-signature edit looks signed.
Rule: every consumer reads the plan through `load_plan`; the same call belongs at the one door every drive passes, before the first spend.

Fix: `scripts/episode/drive.py:preflight` gains `plan_lines(book, number)`. If plan.json exists, call `episode_home.load_plan` in try; failure gives `refuse now: plan.json fails the Episode contract: <first error line>` (exit 2 via `refuse_launch`, no charge). A sha8 mismatch with `plan.verdict.json` gives `will park at step 02: plan edited after its verdict`. `scripts/episode/autopilot.py:launch` runs the same checks before spawning, so a refused plan never becomes a brain turn. In `studio/autopilot.py:TABLE` add `ValidationError .* plan.json|Episode.shots` as `("park", "plan_contract: ...")` before the generic Traceback row, so the brain never orders `redo 02` over a hand edit.
```python
def test_preflight_refuses_a_plan_that_fails_the_contract(tmp_path):
    book = book_with_plan(tmp_path, motion="drifts slowly")
    assert any(l.startswith("refuse now: plan.json fails") for l in drive.preflight(book, 7))

def test_preflight_names_a_plan_edited_after_its_verdict(tmp_path): ...

def test_a_contract_value_error_parks_instead_of_asking_the_brain():
    assert autopilot.classify("pydantic_core._pydantic_core.ValidationError: Episode.shots", set())[0] == "park"
```
Expected effect, replay: run 11, run 12, the 27 min gap (05:57 to 06:24), one brain call and one possible plan rewrite are avoided; about 0.5-1 h wall, near-zero machine time. Unproven: whether the sha8 check false-refuses legitimate cure edits; check that `studio/plan_provenance.py` re-signs or records the new sha before wiring a refusal (the contract check alone is safe).

## F5. Code moved about 8 times

Evidence: 17 `code_moved`, 2 `code_moved_during_run` and 1 `code_dirty_during_run` rows in the window (`B/autopilot/events.jsonl` 1554-1733, dirty at 1615); `WARNING code moved mid-episode` appears in 19 launch logs (`E/drive_launch*.log`). The refusals by run (`E/drive.jsonl` run rows) are all gates (G-DEAD, G-PEOPLE), engine, contract or token. No `REFUSED to start: the working tree is dirty` appears in any ep07 log, and no `wait_tree` event is in the window.
Verdict: noise for refusals, with two real effects.
- `code_moved` hands the supervisor to a successor only after the drive ends (`scripts/episode/autopilot.py:1424-1457`), so no run was killed.
- Positive: `_brain` returns `head_moved`, a relaunch instead of a brain turn, on a new HEAD (`studio/autopilot.py:344-345`); the fixes 35b7e603 and 1029749f were picked up this way and ended the clone read.
The real loop was the opposite: runs 12-17 relaunched 6 times on the SAME sha (1029749f), because the owner's `retry` bypasses the "one relaunch per new HEAD" brake. That is fixed by F1's signature window, not by freezing code. Optional: print the per-launch WARNING once per sha.

## Not verified
- Telegram delivery of any told or PARKED message (no receipt exists; F2 adds one).
- That brain set 06's `redo 02` would have overwritten plan.json (inferred from its `why`); not run.
- The G-PEOPLE false refusal itself (lead's evidence; other experts own it).
