# Jekyll ep07 retro: evidence (lead, 2026-11-10)

Episode: library/20260827135504_the-strange-case-of-dr-jekyll-and-mr-hyde/episodes/ep07/
Shipped 2026-11-10 10:41 PST: https://youtu.be/ZSbWJVFDeGE. Master c032c727, 146.4 s.
Wall: launched 2026-10-30 17:17 PDT; finished 2026-11-10. Machine clock 7.08 h, over the 6 h budget.
Drive ran 20 times. The brain was retired 6 times (brain_retired_01..06).

## Sources
- `drive.jsonl`: one run/start/end row per drive.
- `drive_runNN.log`, `drive_launchNN.log`: per-run output.
- `autopilot/events.jsonl` and `autopilot/parked.jsonl`, at book level.
- `attempts.json`: per-wall rounds and seconds.
- `manifest.json`: timing by stage.
- `review/director_signoff.md`: the gate terminals.
- `review/eye_c032c727.json`: the owner's watch notes.
- `learnings.jsonl`
- `plan.json.bak_2026-11-03_shot07`: a hand edit of shot 07.

## Refusals by run

| Runs | Step | Refusal |
|---|---|---|
| 02–08, 16 | 10 assemble | **G-DEAD**: failed takes T06/T08/T10/T12/T17/T19/T22/T11. The brain said all of them carried "2 figures read as gabriel_john_utterson … the shot casts one". This is the Utterson/Enfield look-alike clone check. Fixes landed mid-episode: 35b7e603 (coats tell two people apart), 1029749f, 348c7390 (Enfield sheet redrawn brown, later bearded). |
| 10, 13, 14, 15, 17 | 11 | **G-PEOPLE** ship-block at shot_07 after the master ladder. The owner's eye notes say it was "a one-frame read (0.5 s) of Jekyll's hair as white; the panel and the take's first frame read black on seeds 19/23/29". It was a false refusal, held for 5 runs. |
| 09 | 07 grids | Refused. Engine down: EngineLost while QwenImage21 was loading with dynamic VRAM; the engine restarted mid-job. |
| 11 | 01/03 | A plan.json hand edit of shot 07's motion used "slowly", which the Episode contract forbids. The crash came at load, after the edit was saved. |
| 12 | 06 | takes_r2v prompts refused, after the same hand edit. |
| 19 | 13 publish | `RefreshError invalid_grant`: the YouTube token had expired. It was **parked as `clock_loop`**, not `youtube_token_expired`, and sat 6 days (11-04 → 11-10). "youtube_token_told" was logged at every launch from 11-04 03:51 on, yet the owner never acted. |

Autopilot parks named `clock_loop` fired at 7 launches on 11-04: 06:25, 07:03, 07:35, 08:42, 09:08, 09:35 and 17:25. Each was hand-retried about 20 min later.

Code moved during the run about 8 times (`code_moved_during_run`, `code_dirty_during_run`) as sessions committed fixes mid-episode.

## Shipped flaws (judge terminals ended keep_best; the auto-override shipped them)
- T00, T19, T21: gait "shuffle: 4.0 steps/s … HARD: the feet slide", 6 rolls each.
- T05: warp fail, S 2.98 Se 4.61, "HARD: the face is redrawn frame to frame".
- T21: content fail, lettering in the picture, and 12 figures where 11 are allowed.
- PLAN battery: REFUSED → keep_best (G-RISE: a second bird's-eye at shot 21).
- EYE_PANELS keep_best:
  - doubles at shot_00/05/18 (shot_05: 2 figures read as Enfield);
  - framing misses at 05/09/11/20;
  - orphan limbs at 20/21;
  - the place mirror at 02.

## Time by stage, minutes (manifest)
take_dq 179.6 · take_content 48.2 · grids 45.3 · takes 26.6 · plan 23.7 · panel_eye 21.9 · master_eye 16.4 · panel_content 12.9 · take_eye 11.0 · lines 9.7 · bed 7.6
attempts.json: wall.09 12 rounds / 15766 s (4.4 h); takes.first 7537 s; wall.07.order 7 rounds / 2693 s; wall.08 6 rounds / 2558 s.

Note: the 2026-11-09 efficiency debate built Tier A fixes #1 (DQ frame-3 skip) and #3 (re-judge with the model kept loaded) in the anime POC folder (docs/audit/2026-10-31_anime_model_poc/). That folder is not the production take DQ. Check whether production has them.
