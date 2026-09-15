# MOTION-GATE — a DQ gate for "static image, then video"

Owner's finding (2026-09-11 15:15): "some takes start with a static image and then after some time video ... static shots ... we need to fix that."
Everything below is measured on every take on disk (iteration 4 `shots_r2v`, 3 `shots_r2v_v5`, 2 `shots_r2v_v4`; 63 files incl. retakes and fails), free tools only (ffmpeg, numpy).
Prototype, tests, calibration data and the integration diff: `D:\temp\claude\d--Projects-KingdomOfViSuReNa-alpha-visurena-studio\8a764c01-76e4-437c-b43b-8b6a5e4a5481\scratchpad\review8\motion_gate\`

## DIAGNOSIS

**1. The END pin of an unchanged cell turns the whole segment into a still.**
Per storyboard segment (one per start pin in `shots.json` anchors), seconds frozen at the segment START and at its END, block-max metric (defined below), placed seconds only:

| iteration | segments | frozen > 1 s at START | frozen > 1 s at END | mean start-still | mean end-still | mean frozen share |
|---|---|---|---|---|---|---|
| 4 `shots_r2v` (start + END pins) | 37 | **8** | **8** | 0.86 s | 0.82 s | **0.34** |
| 3 `shots_r2v_v5` (start pins only) | 34 | 2 | 1 | 0.16 s | 0.04 s | 0.07 |
| 2 `shots_r2v_v4` (start pins only) | 43 | 1 | 0 | 0.09 s | 0.00 s | 0.04 |

The eight iteration-4 offenders are exactly the hold segments whose END pin is the start cell again: T17 `Q17_0` (4.75 of 5.0 s still), T17 `Q17_2` (5.75/5.75), T12 `Q12_1` (5.0/5.0), T13 `Q13_0` (3.0/3.0), T11 `Q11_1` (2.75/2.75), T11 `Q11_0` (2.5/2.75), T10 `Q10_0` (3.0/3.25), T01 `Q01_1` (1.5/4.0). Start-still == end-still == segment length: the model shows the pinned cell from cut to cut. Without END pins the same kind of hold freezes at its start in 3 of 77 segments (v5 T02 `Q02_0` 1.25 s, v5 T16 `Q16_2` 1.5 s, v4 T08 `Q08_1` 1.25 s), so the prompt-side "Static shot" freeze exists but is the minor cause (~4 % of segments vs 22 %).
Files: `library\20260822113400_a-study-in-scarlet\episodes\ep01\shots_r2v\T17.mp4` (timeline: bmax 0.3-0.7 for 0-4.9 s, a 1.5 s move at 5.5-7.0 s after the cut, 0.1-0.4 for 8.9-15 s), `T12.mp4`, `T13.mp4`, `T11.mp4`, `T10.mp4`, `T01.mp4`; numbers in `motion_gate\run_all.txt`, `motion_gate\tails.py` output, per-step data in `motion_gate\calib.json`.

**2. The old scan (`motion_scan.py`: 96x168 grey, 8 fps, frame-wide mean |diff| < 1.5) mis-measures faces.** During heard dialogue (RMS > -45 dBFS) it called **68 of 270** quarter-second bins frozen (T00 10/13, T18_fail1 9/14, v4 T18 11/33); the block-max metric calls **0 of 270** (`motion_gate\lips.py`). A mouth is one ~96x96 px region of a 768x1344 frame: its motion averages to ~0.5 frame-wide, under the old threshold. So the old 55 % / 25 % frozen shares were inflated by lips and breathing; the true shares are 0.31 (iteration 4) and 0.05 (iteration 3). The direction of the finding stands, the size was wrong.

**3. What a frozen frame is.** A pinned still is NOT pixel-identical (full-res max pixel diff 10-60 from codec ringing, p99.9 <= 5); "identical frames" is the wrong test. Block-max at 192x336 / 24 fps separates the population cleanly (13 813 steps): pinned still 0.2-0.7, slow drift that the eye reads as a still 0.8-1.1 (T12 seg 1, T01 seg 1: the two men's outlines shift ~1 px over a second), living hold at rest 1.8-3.0 (v4 T16 ink in water, iteration-4 T16 head sway), speech 3-15, walk 9-16, the cab crossing 40-55. Frame pairs one second apart with the diff x8: `motion_gate\eyeball.png`. No film grain is rendered (the prompt asks for it; the pixels do not carry it), so nothing masks a freeze.

**4. Ranked by what a viewer notices:** (i) a still after a cut that lasts > 1 s (8 segments, 6 takes in iteration 4; the viewer reads "slideshow"); (ii) a still before a cut (same 8 segments; less visible, the cut hides it); (iii) a tracking shot that stops (T20 `Q21_0`: "Tracking beside at walking pace", 77 % frozen, passes the start gate, caught by the advisory); (iv) an insert that lies dead (T10 `Q10_0` sheet and stick: 3.0 s still, 92 % frozen).

## THE CHECK

`studio/motion_gate.py` — prototype at `motion_gate\motion_gate.py`, 13 tests green in `motion_gate\test_motion_gate.py` (synthetic frames pin the arithmetic; four tests run on the real takes and are skipped when the library is absent). ~1.5 s per take.

**Metric.** ffmpeg decodes the placed seconds to grey 192x336 at 24 fps. Per frame step: `block_max` = the largest mean |diff| over 24x24 blocks (a block is a mouth's size at full res). Bins of 0.25 s (mean of 6 steps). A bin is **still** when its mean block-max < `STILL = 1.2` (the gap between drift 0.8-1.1 and a living hold 1.8+).

**Per segment** (`segments(anchors, frames)`: every start pin opens a segment; `Q??_?E.png` or a start cell pinned again is an END pin and opens nothing; the cut step itself is excluded):
- `leading_still_s` — the first still run that begins within `GRACE_S = 0.5` s of the segment's first frame (a pinned cell settles with one 1.3-2.0 twitch bin before the still: T17 seg 0 reads 1.4 then 0.3-0.7 for 4.75 s). This is the owner's "static image, then video".
- `still_share` — still bins / bins.
- `kind` from the plan (`kind_of(shot, lines)`): `dialogue` if a dialogue line plays on the shot, `track` if `motion` starts "Tracking", `insert` if `size == "insert"`, else `hold`.

**Thresholds** (calibrated; per-kind distributions over 136 segments):

| kind | n | segment mean energy min / median / max | frozen share median / max | HARD: leading still | ADVISORY: share ceiling |
|---|---|---|---|---|---|
| dialogue | 18 | 6.0 / 12.4 / 26.4 | 0.00 / 0.17 | <= 1.0 s | 0.20 |
| hold | 82 | 0.2 / 7.3 / 47.1 | 0.02 / 1.00 | <= 1.0 s | 0.35 |
| insert | 12 | 3.4 / 11.5 / 21.1 | 0.00 / 0.92 | <= 1.0 s | 0.50 |
| track | 24 | 1.2 / 21.2 / 42.9 | 0.00 / 0.77 | <= 1.0 s | 0.10 |

The hard gate is one number for every kind (`START_LIMIT_S = 1.0`): a viewer notices a still after a cut regardless of what the shot is. The share ceilings are advisory and per kind: a healthy dialogue/track/insert segment measures 0.00, a healthy hold up to ~0.3 (iteration-4 T16, a breathing close-up, 0.21).

**Signatures**
```python
def motion_dq(video: Path, anchors: list, seconds: float, kinds: dict[str, str] | None = None) -> dict
def segments(anchors: list, total_frames: int) -> list[tuple[str, int, int]]
def kind_of(shot, lines: list) -> str
def leading_still_s(bins: list[float], still=1.2, bin_s=0.25, grace_s=0.5) -> float
def still_share(bins: list[float], still=1.2) -> float
def attempt_score(report: dict) -> tuple      # (0 pass / 1 fail, worst_leading_still_s, still_share, foreign, |lag|)
def best_attempt(reports: dict[str, dict]) -> str
```
**Verdict shape** (goes into `T??.dq.json` as `report["motion"]`):
```json
{"segments": [{"cell": "Q17_0.png", "kind": "hold", "start_s": 0.0, "end_s": 5.04, "seconds": 5.0,
               "leading_still_s": 4.75, "still_share": 0.95, "mean_energy": 0.6, "start_ok": false, "share_ok": false}, ...],
 "worst_leading_still_s": 5.75, "still_share": 0.763, "frozen_spans": [[0.25, 5.0], [7.5, 8.75], [9.0, 14.75]],
 "motion_ok": false, "share_ok": false, "bins": [1.4, 0.7, 0.6, ...]}
```
`passed = foreign == 0 and lag_ok and motion["motion_ok"]`; `advisory["frozen_share"]`, `advisory["frozen_share_ok"]`.

**Tests** (`motion_gate\test_motion_gate.py`): identical frames -> 0 energy; one flickering 24x24 block registers > 100 in block-max while the frame-wide mean stays < 3 (the lips case); leading still counts bins until the first that moves; a 0.5 s settle twitch does not hide a still start; share and spans; quarter-second bins drop a sliver; segments come from start pins only (iteration-4 anchors with END pins); kind of a segment; verdict gates the start and advises the share; best attempt prefers a pass, then the shorter freeze; REAL: iteration-4 T17 fails at segments 0 and 2 and passes segment 1; T00 (speaking), v4 T16 (breathing hold), T09 (walk), T03 (cab, share 0.00) pass; T00 has 0.00 frozen share while the line is heard.

**Result of the gate on disk** (`motion_gate\run_all.txt`): iteration 4 FAIL 6/18 — T01 (1.5 s), T10 (3.0), T11 (2.75), T12 (5.0), T13 (3.0), T17 (5.75); iteration 3 FAIL 2/18 — T02 (1.25), T16 (1.5); iteration 2 FAIL 1/19 — T08 (1.25). Advisory-only catches: T20 `Q21_0` (track, 77 % still), T02 `Q02_0` (hold, 69 %), T07 `Q07_0` (hold, 88 %).

## THE FIX

**Files to add** (copy as-is):
- `studio/motion_gate.py` <- `motion_gate\motion_gate.py`
- `tests/test_motion_gate.py` <- `motion_gate\test_motion_gate_repo.py` (same tests, imports `studio.motion_gate`)

**`scripts/episode/take_dq.py`** — the exact diff, `git apply --check` clean against the working tree; the patched file was run end to end in a sandbox on copies of the real takes (`motion_gate\drive_patched.py`): T17 -> `FAIL ... frozen-start 5.75s share 0.76`; `--attempts` on T01 -> `kept T01_retake1.mp4 of 2`, files afterwards `T01.mp4`, `T01_fail1.mp4`, strip re-run on the kept file. File: `motion_gate\take_dq.diff`.

```diff
--- a/scripts/episode/take_dq.py
+++ b/scripts/episode/take_dq.py
@@ -9,8 +9,13 @@
 take better than its own (no foreign composition).  Audio: the take's own
 track against the anchored composite must sit within one frame (0.042 s)
 of zero lag; for a dialogue take the words are heard (Whisper) with WER
-<= 0.20.  Writes `shots_r2v/T<NN>.dq.json` and a strip
-`work_r2v/dq/take_T<NN>.png`.
+<= 0.20.  Motion: no storyboard segment may sit frozen longer than 1.0 s at
+its start (owner 2026-09-11: "a static image and then after some time video");
+the frozen share per segment is advisory.  Writes `shots_r2v/T<NN>.dq.json`
+and a strip `work_r2v/dq/take_T<NN>.png`.  With `--attempts`, every
+`T<NN>_fail*/retake*.mp4` on disk is judged too and the best attempt
+(hard gates, then start-freeze, frozen share, foreign, drift) is kept as
+`T<NN>.mp4`, the displaced file renamed `T<NN>_failN.mp4`.
 """
 from __future__ import annotations
 
@@ -23,7 +28,7 @@
 
 from PIL import Image, ImageDraw
 
-from studio import av_sync, episode_home, frame_match as fm
+from studio import av_sync, episode_home, frame_match as fm, motion_gate
 from studio.trailer_assemble import clip_seconds
 
 SAMPLES = 8
@@ -156,36 +161,88 @@
     return out
 
 
-def main(book_id: str, number: int, indices: list[int]) -> None:
+def segment_kinds(episode, anchors: list) -> dict[str, str]:
+    """Cell -> what its segment is (dialogue / track / insert / hold), from the plan."""
+    kinds = {}
+    for name, _ in anchors:
+        try:
+            kinds[name] = motion_gate.kind_of(episode.shot(motion_gate.shot_of(name)), episode.lines)
+        except StopIteration:
+            kinds[name] = "hold"
+    return kinds
+
+
+def dq_one(video: Path, rec: dict, index: int, frames_dir: Path, work: Path, take_dir: Path,
+           kinds: dict[str, str]) -> dict:
+    seconds = min(clip_seconds(video), rec["placed_seconds"])
+    report = picture_dq(video, index, frames_dir, work, seconds, rec.get("anchors"))
+    cuts = [f / 24 for _, f in rec.get("anchors", [])][1:]
+    report["camera"] = camera_dq(video, seconds, cuts)
+    composite = take_dir / (f"voice_{index:02d}.wav" if rec["audio"] != "silence" else f"silence_{index:02d}.wav")
+    report["audio"] = audio_dq(video, composite, rec["lane"] == "dialogue", work, index)
+    report["motion"] = motion_gate.motion_dq(video, rec.get("anchors"), seconds, kinds)
+    # HARD gates: no foreign composition, audio on the wav, no segment frozen > 1.0 s at its start
+    # (owner 2026-09-11 15:15: "a static image and then after some time video"; MEASURED on iterations
+    # 2-4: a pinned still reads block-max 0.2-0.7, a living hold at rest 1.8-3.0, speech 3-15).
+    # ADVISORY (recorded, judged by eye): off-beat, the camera numbers -- MEASURED 2026-09-10 23:30
+    # on i2v/v2/v3: the crude scale estimator scores a moving textured insert at 0.8-1.8/s with dozens
+    # of "events" on every engine, and "closest cell" is noise on a close-up whose six cells are
+    # near-identical -- and the frozen share against its ceiling per segment kind.
+    report["passed"] = report["foreign"] == 0 and report["audio"]["lag_ok"] and report["motion"]["motion_ok"]
+    report["advisory"] = {"off_beat": report["off_beat"], "camera": report["camera"]["camera_ok"],
+                          "frozen_share": report["motion"]["still_share"],
+                          "frozen_share_ok": report["motion"]["share_ok"]}
+    report["strip"] = str(strip(work, index, report["frames"], frames_dir, rec.get("anchors")))
+    return report
+
+
+def attempts_of(take_dir: Path, index: int) -> list[Path]:
+    """The kept file first, then every `T<NN>_*.mp4` (fail, retake) on disk."""
+    kept = take_dir / f"T{index:02d}.mp4"
+    others = sorted(take_dir.glob(f"T{index:02d}_*.mp4"))
+    return ([kept] if kept.exists() else []) + others
+
+
+def settle(take_dir: Path, index: int, reports: dict[Path, dict]) -> Path:
+    """Keep the best attempt as `T<NN>.mp4`; a displaced kept file becomes the next `T<NN>_failN.mp4`.
+    Returns the path the best attempt had before the rename (its key in `reports`)."""
+    kept = take_dir / f"T{index:02d}.mp4"
+    best = Path(motion_gate.best_attempt({str(p): r for p, r in reports.items()}))
+    if best != kept:
+        used = [int(p.stem.rsplit("_fail", 1)[1]) for p in take_dir.glob(f"T{index:02d}_fail*.mp4")
+                if p.stem.rsplit("_fail", 1)[1].isdigit()]
+        if kept.exists():
+            kept.rename(take_dir / f"T{index:02d}_fail{max(used, default=0) + 1}.mp4")
+        best.rename(kept)
+    return best
+
+
+def main(book_id: str, number: int, indices: list[int], attempts: bool = False) -> None:
     book = episode_home.book_dir(book_id)
     home = episode_home.home(book, number)
+    episode = episode_home.load_plan(book, number)
     frames_dir, take_dir = episode_home.frames_dir(book, number), episode_home.takes_dir(book, number, "r2v")
     work = home / "work_r2v" / "dq"
     work.mkdir(parents=True, exist_ok=True)
     records = {r["index"]: r for r in episode_home.read_json(take_dir / "shots.json")}
     for index in indices:
         rec = records[index]
-        video = book / rec["rel_path"]
-        seconds = min(clip_seconds(video), rec["placed_seconds"])
-        report = picture_dq(video, index, frames_dir, work, seconds, rec.get("anchors"))
-        t0 = rec.get("t_start") or 0.0
-        cuts = [f / 24 for _, f in rec.get("anchors", [])][1:]
-        report["camera"] = camera_dq(video, seconds, cuts)
-        composite = take_dir / (f"voice_{index:02d}.wav" if rec["audio"] != "silence" else f"silence_{index:02d}.wav")
-        report["audio"] = audio_dq(video, composite, rec["lane"] == "dialogue", work, index)
-        # HARD gates: no foreign composition, audio on the wav.  ADVISORY (recorded, judged by eye):
-        # off-beat and the camera numbers -- MEASURED 2026-09-10 23:30 on i2v/v2/v3: the crude scale
-        # estimator scores a moving textured insert at 0.8-1.8/s with dozens of "events" on every
-        # engine, and "closest cell" is noise on a close-up whose six cells are near-identical.
-        report["passed"] = report["foreign"] == 0 and report["audio"]["lag_ok"]
-        report["advisory"] = {"off_beat": report["off_beat"], "camera": report["camera"]["camera_ok"]}
-        report["strip"] = str(strip(work, index, report["frames"], frames_dir, rec.get("anchors")))
+        kinds = segment_kinds(episode, rec.get("anchors", []))
+        files = attempts_of(take_dir, index) if attempts else [book / rec["rel_path"]]
+        reports = {f: dq_one(f, rec, index, frames_dir, work, take_dir, kinds) for f in files}
+        best = settle(take_dir, index, reports) if attempts else files[0]
+        report = reports[best]
+        if attempts and best != files[-1]:                 # the strip and work frames must be the kept file's
+            report = dq_one(take_dir / f"T{index:02d}.mp4", rec, index, frames_dir, work, take_dir, kinds)
+        report["attempts"] = {f.name: motion_gate.attempt_score(r) for f, r in reports.items()}
         episode_home.write_json(take_dir / f"T{index:02d}.dq.json", report)
         print(f"T{index:02d}: {'PASS' if report['passed'] else 'FAIL'} off_beat {report['off_beat']} "
               f"foreign {report['foreign']} scale/s {report['camera']['max_scale_per_s']:.2f} "
               f"events {report['camera']['scene_events']} lag {report['audio']['lag_s']:+.3f}s "
+              f"frozen-start {report['motion']['worst_leading_still_s']:.2f}s share {report['motion']['still_share']:.2f} "
+              f"{'kept ' + best.name + ' of ' + str(len(files)) + ' ' if attempts else ''}"
               f"{report['audio'].get('heard', '')[:60]}", flush=True)
 
 
 if __name__ == "__main__":
-    main(sys.argv[1], int(sys.argv[2]), [int(a) for a in sys.argv[3:]])
+    main(sys.argv[1], int(sys.argv[2]), [int(a) for a in sys.argv[3:] if a.isdigit()], attempts="--attempts" in sys.argv)
```

**Retake policy (automatic).** After `takes_r2v.py --retake=N` (which leaves `T<NN>_failK.mp4` beside the new `T<NN>.mp4`), run `take_dq.py <codex_id> <n> N --attempts`. Every attempt gets the full DQ; `attempt_score` orders them `(hard gates failed?, worst leading still s, frozen share, foreign frames, |lag|)`, lower wins, a tie keeps the current file; the winner becomes `T<NN>.mp4`, the displaced file `T<NN>_fail{next}.mp4`; `T<NN>.dq.json` records `attempts: {name: score}`. On disk today: T01 -> keep `T01_retake1` (0.5 s freeze, share 0.22 vs 1.5 s, 0.37; both carry a foreign frame, so both still fail and the take needs a third seed); T17 -> keep `T17_fail1` (4.75 s vs 5.75 s, share 0.56 vs 0.76; both fail: this take cannot be fixed by a seed, its END pins must go). Note the order puts the freeze before foreign frames among failing attempts, as the brief asked; swap the tuple's 2nd and 4th elements if a foreign composition should outrank a freeze.

**Loop wiring** (`.claude/skills/episode/SKILL.md` section 5, one sentence to replace "A failing take is retaken once ... keep the better one by eye"): "A failing take is retaken once with a fresh seed; `take_dq.py ... --attempts` then judges every attempt on disk and keeps the best by (hard gates, start-freeze, frozen share, foreign, drift) as `T??.mp4` automatically." `iterationN.sh`: add `--attempts` to the DQ call after each `--retake`.

**Upstream (for the pins member, not applied here):** the diagnosis says the END pin of an unchanged cell is the cause of 8 of the 11 failing segments across three iterations. In `scripts/episode/takes_r2v.py::end_cells`, emit no END pin when the end cell would be the start cell again (a hold); keep END pins only where a `Q??_?E.png` exists. With that change the gate above is the regression test: iteration 3 (no END pins) fails 2/18 on motion, iteration 4 fails 6/18.

## Files
```
D:\temp\claude\d--Projects-KingdomOfViSuReNa-alpha-visurena-studio\8a764c01-76e4-437c-b43b-8b6a5e4a5481\scratchpad\review8\motion_gate.md              this report
D:\temp\claude\d--Projects-KingdomOfViSuReNa-alpha-visurena-studio\8a764c01-76e4-437c-b43b-8b6a5e4a5481\scratchpad\review8\motion_gate\motion_gate.py             -> studio/motion_gate.py
D:\temp\claude\d--Projects-KingdomOfViSuReNa-alpha-visurena-studio\8a764c01-76e4-437c-b43b-8b6a5e4a5481\scratchpad\review8\motion_gate\test_motion_gate.py        13 tests (scratchpad import)
D:\temp\claude\d--Projects-KingdomOfViSuReNa-alpha-visurena-studio\8a764c01-76e4-437c-b43b-8b6a5e4a5481\scratchpad\review8\motion_gate\test_motion_gate_repo.py   -> tests/test_motion_gate.py
D:\temp\claude\d--Projects-KingdomOfViSuReNa-alpha-visurena-studio\8a764c01-76e4-437c-b43b-8b6a5e4a5481\scratchpad\review8\motion_gate\take_dq.diff               the integration diff (git apply --check clean)
D:\temp\claude\d--Projects-KingdomOfViSuReNa-alpha-visurena-studio\8a764c01-76e4-437c-b43b-8b6a5e4a5481\scratchpad\review8\motion_gate\take_dq_patched.py         the patched file, run in the sandbox
D:\temp\claude\d--Projects-KingdomOfViSuReNa-alpha-visurena-studio\8a764c01-76e4-437c-b43b-8b6a5e4a5481\scratchpad\review8\motion_gate\run_all.txt                the gate on all 63 takes, per-kind table, retake ranking
D:\temp\claude\d--Projects-KingdomOfViSuReNa-alpha-visurena-studio\8a764c01-76e4-437c-b43b-8b6a5e4a5481\scratchpad\review8\motion_gate\gate_results.json          verdicts per take
D:\temp\claude\d--Projects-KingdomOfViSuReNa-alpha-visurena-studio\8a764c01-76e4-437c-b43b-8b6a5e4a5481\scratchpad\review8\motion_gate\calib.json                 per-step energies (global, block-max, moving share) for every take
D:\temp\claude\d--Projects-KingdomOfViSuReNa-alpha-visurena-studio\8a764c01-76e4-437c-b43b-8b6a5e4a5481\scratchpad\review8\motion_gate\eyeball.png                frame pairs 1 s apart with diff x8 (still / drift / breathing / speech)
D:\temp\claude\d--Projects-KingdomOfViSuReNa-alpha-visurena-studio\8a764c01-76e4-437c-b43b-8b6a5e4a5481\scratchpad\review8\motion_gate\{calibrate,analyze,timeline,identical,lips,tails,eyeball,run_all,make_patch,drive_patched}.py   the measurements
```
