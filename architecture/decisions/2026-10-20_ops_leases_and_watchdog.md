# 2026-10-20 -- Ops after the ep01 deadline retro: a pause is a lease, silence is alerted, a hold is not a park, code holds still under a live drive

Status: **BUILT 2026-10-20 (package E of the deadline retro).** The owner vetoed none of V1-V11, so the
retro's defaults hold: V4 (code is held still during a live run) and V7 (pause leases) are on.
The debate: `docs/audit/2026-10-20_deadline_retro/` (`RETRO.md` sections 3, 5 and 6; `ops_reliability.md` and
`ops_reliability_skeptic.md`; this folder is outside git). Items built: 7, 8 and 12 of RETRO.md section 3.

## Why

ep01 took 30.85 h of wall for 7.85 h of machine time. Four ops faults sat inside that:

| Fault | Evidence |
|---|---|
| The supervisor was dead for 4.68 h and nothing said so | events.jsonl 2026-10-19T12:39:32Z `supervisor_died_at`, heartbeat_age_s 16,840. The cause is in the Windows System log: Windows Update restarted the PC at 00:59 and 01:03 PDT (User32 1074, "Service pack (Planned)" and "Upgrade (Planned)"; active hours are 06:00-00:00). The task `visurena-autopilot` has an Interactive logon and an AtLogOn trigger, so it could not run until the owner logged on at 05:40. |
| A retro pause had no end | `pause` at 2026-10-19T06:10:15Z (23:10 PDT), never looked at again until the next work |
| A deliberate hold was recorded as a failure | ep01 parked twice on "escalated: G-STANDING" (10-19 21:33 PDT and 10-20 04:51Z); in a series two holds in a row trip the two-parks brake |
| Code moved under live runs | 9 shas over the 13 first-delivery runs; 62 `code_moved` and 35 `successor` rows in ep01's window; 6 of 13 runs ended refused |
| The YouTube token blocked an upload-ready master | "Token has been expired or revoked": the consent screen is in Testing (7-day tokens) and `.env` was last written 10-07 (12.9 days at this commit) |

## What changed in the org (architecture)

- **Autopilot state (studio/autopilot.py):** a new state `HELD_PUBLISH`. The hand-back table reads
  `OWNER G-STANDING |` as kind `held`, ahead of the general `OWNER` park row. The episode gets no parked
  row, so it never feeds the two-parks brake. The CLI writes one `held_publish` row and one message naming
  `publish/standing.json`. The series moves past a held episode. When only holds are left it sits on the
  lowest one, never on COMPLETE. A signed standing file lifts every hold, and the held master runs step 13
  again (`standing_signed`). A `retry N` lifts N's hold.
- **Pause leases (series.json `pause`):** `{by, why, since, expires, sha}`. `pause --by --why --hours`.
  A retro pause, or the autopilot's own, expires at 2 h. An owner pause never expires unless he gives hours.
  When a lease expires the autopilot writes one `pause_expired` row and sends one message. It resumes a pause
  only when the autopilot set it itself (the two-parks brake), only after the lease has run out, and only
  after a commit has landed since. An owner pause or a retro pause is never lifted by code. A pause set
  before leases existed (today's Jekyll series.json) is left alone.
- **Supervisor watchdog (a second scheduled task):** `visurena-autopilot-watchdog` runs every 5 min and at
  logon. `install` registers it with the same logon that worked for the supervisor, and `uninstall` removes
  both tasks. `autopilot.py watchdog` reads the age of `heartbeat.json`. After 10 min of silence it writes one
  `supervisor_silent` row and sends one Telegram message per silence. The message goes through the existing
  `drive.notify` path, which the tests fake.
- **Code held still under a live drive:** `launch` records the sha it launched on, in `gpu.lock` and in the
  launch row. When HEAD moves while a drive is alive, the loop keeps its code and writes one
  `code_moved_during_run` row per commit. It spawns no successor and hands over after the drive ends.
  `may-commit` exits 3 while a drive runs on staged runtime code and names
  `pause --at-boundary --by <you> --why ...`. A relaunch on moved code writes the checks whose judge code
  changed (`invalidated_checks`: judges, measures, gates, dq and content checks, qc, gates.yaml) at the top
  of its `drive_launchNN.log`, plus one `judge_code_moved` row. It does not refuse; fixes may still land.
- **YouTube token (scripts/publish/youtube_auth.py):** a stored token now carries `YOUTUBE_REFRESH_TOKEN_AT`.
  Without the stamp, the age falls back to the mtime of `.env`, which the token is at least as old as. At
  launch and at render start (step 09 opens), once each per drive, a token 5 days old, or one whose refresh
  fails, sends the consent paste link. The link reuses a verifier already pending, so an owner in the middle
  of a paste keeps a working link.

## What did not change

- The owner's pause and his RENDER_HOLD stay his. No code lifts them.
- No branch and no patch queue (one checkout on master). A commit is held, not refused, and only while a
  drive is alive.
- The OAuth fix that lasts is the owner's click: publish the consent screen to Production (V1). Until a
  post-switch token has lived 8 days, the age check is the fallback, not the fix.
- The existing ep01 parked row ("escalated: G-STANDING") stays until a `retry 1`. This commit wrote nothing
  under `library/`.

## Open (for the owner's machine, not code)

- **The 4.68 h gap will recur on the next Windows Update restart.** Both tasks need a logon. Durable fixes
  need elevation, which this shell does not have (S4U was refused with 0x80070005 on 2026-10-06). One fix is
  to register the tasks with S4U or a stored password plus `-AtStartup`, from an elevated shell. The other
  is to stop update restarts while a series is live (Settings > Windows Update > pause updates, or an
  active-hours window that covers the night). V8's default is to check read-only first, then change. The
  read-only check is in this file.
- The watchdog task is registered by the next `autopilot.py install`. It is not registered by this commit.

## Tests

`tests/test_a_silent_supervisor_is_alerted_once.py`, `tests/test_a_pause_is_a_lease.py`,
`tests/test_the_standing_hold_is_held_publish.py` (fixture: the last lines of ep01's `drive_launch18.log`),
`tests/test_code_is_held_still_under_a_live_drive.py`, `tests/test_an_old_youtube_token_sends_the_paste_link.py`.
No test reaches Google, Telegram, the GPU or Task Scheduler.
