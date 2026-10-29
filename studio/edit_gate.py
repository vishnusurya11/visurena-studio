"""G5.1-5.6 -- edit integrity: the master IS the takes, frame for frame, at the
frames the plan names, with nothing held, nothing dropped, and no take on disk
that is no longer the one the cut used.

Every function here is pure except the two ffmpeg readers.  Measured on ep01
master_iter11 against shots_r2v (2026-09-11): two crf-17 encodes of one frame
differ by 0.16-0.59 (mean |grey| at 128x224, 0-255); neighbouring frames of the
slowest take differ by 1.4-9.7; frames of different shots by 32-63.  So
SAME_FRAME sits an order of magnitude above encoder noise and an order below
any other picture.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import numpy as np

FPS = 24
GREY_W, GREY_H = 128, 224
SAME_FRAME = 4.0
"""CALIBRATION (above): encoder noise 0.16-0.59, another picture 32-63."""
SEGMENT_MEAN = 1.0
"""CALIBRATION: a segment that IS its take measured 0.16-0.59 mean; one frame off
lifts the mean to 1.6-9.7."""
SEGMENT_MEAN_RTX = 2.0
"""The cap on a master RTX VSR upscaled (owner 2026-10-14).  MEASURED on Jekyll
ep01, the same cut both ways: Lanczos 2x segments 0.35-0.55, RTX 4x 0.97-1.48
(per frame at most 1.56; off by one 1.50-5.20, and offset 0 the best shift on all
23).  The sharpening is the upscale's job, not a wrong frame; the offset, a frame
of another picture (SAME_FRAME) and a held run still fail as before."""


SEGMENT_MEAN_AV3 = 2.5
"""The cap on an av3 master (hqdn3d temporal denoise + x4 upscale).  MEASURED on
Jekyll ep01 (28 segments, offset 0 on all, cuts 27/27 exact): 1.47-2.10, three
over RTX's 2.0 (T01 2.06, T11 2.102, T12 2.017).  A wrong picture reads 32-63."""
SEGMENT_MEAN_CUT = 1.95
"""The cap on the judged cut at 768 (no upscale; the face paste baked in, CRF 8; Jekyll ep03 retro #2),
set from the measured RATIO of a cut's segment means to its own av3 master's, not one cut's max.
MEASURED 2026-10-27 by qc.edit_report (tests/fixtures/cut_segment_means.json): ep03's av3 master
1.486-2.083 (median 1.838), the same cut at 768 0.500-1.362 (median 1.002); per segment the cut reads
0.270-0.778 of its master (median 0.556).  SEGMENT_MEAN_AV3 2.5 x 0.778 = 1.95.  ep04's live cut
0.777-1.668 (median 1.105) sits under it; 1.6, fitted on ep03's max alone, refused ep04's T02 at 1.668.
Not the old 1.0: that was fitted on single-encode masters (a segment that IS its take 0.16-0.59); the
cut is the take re-encoded three times with the paste in.  A wrong picture reads 32-63 and a wrong
frame is caught by the offset, not the mean."""
HOLD_FRAMES_DENOISED = 6
"""A run of repeats an edit hold needs on a denoised master: the temporal denoise
smooths slow motion into 3-frame near-repeats the take does not have (ep01 T13,
T15, T19, T23: every run exactly 3); a freeze edit is a quarter second or more."""


def segment_cap(upscale: str) -> float:
    """The segment mean cap for the upscale that made the master ('' = unrecorded)."""
    if upscale == "av3":
        return SEGMENT_MEAN_AV3
    if upscale == "cut":
        return SEGMENT_MEAN_CUT
    return SEGMENT_MEAN_RTX if upscale.startswith("rtx") else SEGMENT_MEAN


def hold_least(upscale: str) -> int:
    """The shortest run of added repeats that is a hold, for the master's upscale."""
    return HOLD_FRAMES_DENOISED if upscale == "av3" else HOLD_FRAMES


DUP = 0.6
"""CALIBRATION: |f[k+1]-f[k]| below this and the frame is a repeat -- the encoder
reproduces an identical frame to within 0.59."""
HOLD_FRAMES = 3
"""CALIBRATION: singletons are threshold noise (0.623 against 0.609); a run of
three or more repeats the master has and the take does not is an edit hold."""
PTS_TOL = 0.001
PTS = re.compile(r"pts_time:\s*([0-9.]+)")


def grey_frames(video: Path, w: int = GREY_W, h: int = GREY_H) -> np.ndarray:
    """Every decoded frame, timestamps passed through (no dup, no drop), small and grey."""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(video), "-an", "-fps_mode", "passthrough",
                          "-vf", f"scale={w}:{h}", "-f", "rawvideo", "-pix_fmt", "gray", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.uint8).reshape(-1, h, w)


def frame_times(video: Path) -> list[float]:
    """The presentation time of every frame, from showinfo."""
    result = subprocess.run(["ffmpeg", "-i", str(video), "-an", "-fps_mode", "passthrough",
                             "-vf", "showinfo", "-f", "null", "-"],
                            capture_output=True, text=True, errors="replace")
    return [float(m) for m in PTS.findall(result.stderr)]


def frame_diff(a: np.ndarray, b: np.ndarray) -> float:
    """Mean absolute grey difference between two frames."""
    return float(np.abs(a.astype(np.int16) - b.astype(np.int16)).mean())


def repeats(frames: np.ndarray, dup: float = DUP) -> set[int]:
    """Indices k where frame k+1 repeats frame k."""
    return {k for k in range(len(frames) - 1) if frame_diff(frames[k], frames[k + 1]) < dup}


def in_cut(records: list[dict], placed: dict) -> list[dict]:
    """The take records whose shots the timeline places; a take of an omitted
    shot stays on disk and out of the cut's measures (ep13, 2026-09-27)."""
    here = {s["index"] for s in placed["shots"]}
    return [r for r in records if all(i in here for i in (r.get("shots") or [r["index"]]))]


def run_of(r: dict) -> list[int]:
    return r.get("shots") or [r["index"]]


def dead_factors(placed: dict, records: list[dict], plan: dict) -> dict[int, float]:
    """shot -> the factor G-DEAD gave its take-run (new seconds / placed seconds)."""
    by = {s["index"]: s["seconds"] for s in placed["shots"]}
    out = {}
    for r in records:
        new, old = (plan.get("seconds") or {}).get(r["index"]), sum(by[i] for i in run_of(r))
        out.update({i: new / old for i in run_of(r)} if new and old else {})
    return out


def dead_view(placed: dict, records: list[dict], plan: dict | None) -> tuple[dict, list[dict]]:
    """The timeline and takes the master was CUT from: work/dead_cuts.json (G-DEAD) removed
    shots and gave their neighbours new seconds, so rows, boundaries and starts follow it."""
    if not plan or not (plan.get("cut") or plan.get("seconds")):
        return placed, records
    gone = {i for r in records if r["index"] in plan.get("cut", []) for i in run_of(r)}
    factor, shots, t = dead_factors(placed, records, plan), [], 0.0
    for s in (s for s in placed["shots"] if s["index"] not in gone):
        seconds = round(s["seconds"] * factor.get(s["index"], 1.0), 6)
        shots.append({**s, "seconds": seconds, "t_start": round(t, 6)})
        t += seconds
    return {**placed, "shots": shots}, [r for r in records if r["index"] not in plan.get("cut", [])]


def segment_plan(placed: dict, records: list[dict], fps: int = FPS) -> list[dict]:
    """One row per take-run in cut order: master start frame and frames placed."""
    by = {s["index"]: s for s in placed["shots"]}
    rows = []
    for r in sorted(records, key=lambda r: r["index"]):
        shots = r.get("shots") or [r["index"]]
        rows.append({"take": r["index"], "shots": shots, "rel_path": r["rel_path"],
                     "start": int(round(by[shots[0]]["t_start"] * fps)),
                     "n": int(round(sum(by[i]["seconds"] for i in shots) * fps))})
    return rows


def best_offset(master: np.ndarray, take: np.ndarray, start: int, n: int, span: int = 3) -> tuple[int, float]:
    """The take shift (frames) that best explains master[start:start+n], and its mean diff."""
    best = (0, float("inf"))
    for off in range(-span, span + 1):
        pairs = [(start + i, i + off) for i in range(n) if 0 <= i + off < len(take) and start + i < len(master)]
        if pairs:
            mean = float(np.mean([frame_diff(master[a], take[b]) for a, b in pairs]))
            if mean < best[1]:
                best = (off, mean)
    return best


def held_runs(master_dups: set[int], take_dups: set[int], least: int = HOLD_FRAMES) -> list[list[int]]:
    """Runs of frames the master repeats where the take does not."""
    runs: list[list[int]] = []
    for k in sorted(master_dups - take_dups):
        if runs and k == runs[-1][-1] + 1:
            runs[-1].append(k)
        else:
            runs.append([k])
    return [r for r in runs if len(r) >= least]


CLEAR = 0.85
"""A segment is clearly its take when its offset-0 mean sits under this share of both one-frame
shifts.  Jekyll ep05 repair: T11 read 2.40 against 3.18/3.20, T14 1.96 against 2.47/2.57 (ratios
0.75, 0.79), every frame under SAME_FRAME, over SEGMENT_MEAN_CUT 1.95 -- re-encode noise on a bright,
detailed picture (grey mean 104), not a wrong frame."""
CLEAR_OVER = 1.3
"""How far over its cap a clear segment may sit: T11 sat 1.23x SEGMENT_MEAN_CUT.  Past it a segment
that beats both shifts is a regrade of the take (a uniform +3 on every frame), still refused."""


def clear(row: dict, cap: float) -> bool:
    """The offset-0 mean clearly beats both one-frame shifts and sits near the cap (none measured: not clear)."""
    shifts = row.get("shifts") or []
    return len(shifts) == 2 and row["mean"] < CLEAR * min(shifts) and row["mean"] <= CLEAR_OVER * cap


def shift_mean(master: np.ndarray, take: np.ndarray, start: int, n: int, off: int) -> float:
    """master[start:start+n] against the take shifted by `off` frames, inner frames only."""
    pairs = [(start + i, i + off) for i in range(n) if 0 <= i + off < len(take) and start + i < len(master)]
    return float(np.mean([frame_diff(master[a], take[b]) for a, b in pairs])) if pairs else float("inf")


def segment_ok(row: dict, cap: float, least: int = HOLD_FRAMES) -> bool:
    """The verdict on a measured segment row: offset 0, close, no other picture, no hold."""
    holds = [h for h in row["held"] if len(h) >= least]
    close = row["mean"] <= cap or row["flat"] or clear(row, cap)
    return row["offset"] == 0 and close and not row["frames_off"] and not holds


def segment_match(master: np.ndarray, take: np.ndarray, start: int, n: int,
                  cap: float = SEGMENT_MEAN, hold: int = HOLD_FRAMES) -> dict:
    """Is master[start:start+n] take[0:n]?  Offset, mean, the frames that are another
    picture, and the holds the edit added."""
    per = [frame_diff(master[start + i], take[i]) if start + i < len(master) and i < len(take) else 255.0
           for i in range(n)]
    offset, _ = best_offset(master, take, start, n)
    row = {"offset": offset, "mean": round(float(np.mean(per)), 3),
           "frames_off": [i for i, d in enumerate(per) if d > SAME_FRAME],
           "held": held_runs(repeats(master[start:start + n + 1]), repeats(take[:n + 1]), hold),
           "flat": level_shift(per),
           "shifts": [round(shift_mean(master, take, start, n, k), 3) for k in (-1, 1)]}
    row["ok"] = segment_ok(row, cap, hold)
    return row


LEVEL_SHIFT = 2.0
"""The most a uniform level shift may lift the mean.  ep14 T26 (2026-09-29): a dark
insert (grey mean 23) measured 1.00-1.05 on EVERY frame, mean 1.011 over the 1.0
cap -- one grey level of the encoder's range handling, not a wrong frame."""
FLAT = 0.1
"""Per-frame spread (p90 - p10) of a level shift; a slipped frame is uneven (T26: 0.05)."""


def level_shift(per: list[float]) -> bool:
    """Every frame off by the same small amount: the picture is the take's."""
    if not per:
        return False
    return (float(np.mean(per)) <= LEVEL_SHIFT
            and float(np.percentile(per, 90) - np.percentile(per, 10)) <= FLAT)


def cut_exact(master: np.ndarray, at: int, prev_last: np.ndarray, first: np.ndarray) -> bool:
    """The frame before the cut is the previous take's last placed frame, the frame
    at it is the next take's first."""
    return frame_diff(master[at - 1], prev_last) <= SAME_FRAME and frame_diff(master[at], first) <= SAME_FRAME


def timestamp_holes(times: list[float], fps: int = FPS, tol: float = PTS_TOL) -> list[tuple[int, float]]:
    """(frame, gap) wherever the picture does not advance by one frame: a late first
    frame, or a hole a player fills by holding the frame before it."""
    holes = [(0, round(times[0], 4))] if times and abs(times[0]) > tol else []
    holes += [(k, round(times[k + 1] - times[k], 4)) for k in range(len(times) - 1)
              if abs(times[k + 1] - times[k] - 1 / fps) > tol]
    return holes


END_CHIP_FRAMES = 6
"""The silent black chip after the title card, in frames: 0.25 s at 24 fps.

THE CONTRACT LIVES HERE, and `assemble.END_CHIP_SECONDS` derives from it, because
holding it twice is what broke every episode's QC.  The chip was shortened from
2.0 s to 0.25 s on 2026-09-11 ("2 s of silent black before a loop is dead time")
and this gate kept demanding 48.  Measured on every episode ever cut -- ep01,
ep02 and ep03 -- expected minus master is 42 = 48 - 6, exactly, three times.

`tail["ok"]` was therefore False forever, so `edit_integrity.ok` was False, so
`qc.passed` was False on every episode, so `--override` became the normal way to
publish.  A gate that can never pass is a gate nobody reads."""


FADE_MAX_FRAMES = 30
"""A fade is short: 0.5 s up and 0.8 s down at 24 fps is 12 + 20 frames."""


def faded(shown, source) -> bool:
    """Is `shown` the same picture as `source`, only darker?"""
    return float(shown.mean()) < float(source.mean()) * 0.98


def fades_ok(indices: list[int], card_n: int) -> bool:
    """Faded frames sit only at the card's head and tail, and are few."""
    if not indices:
        return True
    head = [i for i in indices if i < FADE_MAX_FRAMES]
    tail = [i for i in indices if i >= card_n - FADE_MAX_FRAMES]
    return len(head) + len(tail) == len(indices) and len(indices) < card_n // 2


def tail_check(master: np.ndarray, picture_frames: int, card: np.ndarray | None,
               black: int = END_CHIP_FRAMES) -> dict:
    """After the picture: the card frame for frame, then `black` black frames, nothing else."""
    card_n = len(card) if card is not None else 0
    out = {"expected_frames": picture_frames + card_n + black, "master_frames": len(master)}
    if card is not None:
        got = master[picture_frames:picture_frames + card_n]
        off = [i for i in range(min(len(got), card_n)) if frame_diff(got[i], card[i]) > SAME_FRAME]
        # THE CARD IS FADED UP AND DOWN (assemble.conform_card, owner 2026-09-19:
        # "it ended abruptly").  A faded frame is darker than the card's own, so
        # frame-for-frame equality only holds in the middle.  The fade frames are
        # checked as fades instead: dimmer than their source, and monotonic.
        out["card_frames_off"] = [i for i in off if not faded(got[i], card[i])]
        out["card_fade_frames"] = [i for i in off if faded(got[i], card[i])]
        out["card_fades_ok"] = fades_ok(out["card_fade_frames"], card_n)
    dark = 0
    for f in master[::-1]:
        if f.max() >= 8:
            break
        dark += 1
    out["black_frames"] = dark
    # The card's fade-out ENDS on black, so the run of dark frames at the end is
    # the chip plus the last frames of the fade.  Those extra frames are the
    # fade's own, never missing picture: the frame count above already fixes the
    # total, so a longer dark run can only come from inside the card.
    extra = dark - black
    out["ok"] = (out["master_frames"] == out["expected_frames"]
                 and 0 <= extra <= (FADE_MAX_FRAMES if card is not None else 0)
                 and not out.get("card_frames_off") and out.get("card_fades_ok", True))
    return out


def cut_manifest(plan: list[dict], book: Path) -> dict:
    """What the cut used: per take file, its relative path, frames placed and size on
    disk.  `assemble.py` writes this as `work/cut.json` AT CUT TIME (G5.6)."""
    out = {}
    for row in plan:
        path = Path(book) / row["rel_path"]
        out[Path(row["rel_path"]).name] = {"rel_path": row["rel_path"], "frames": row["n"],
                                           "bytes": path.stat().st_size if path.exists() else 0}
    return out


def stale_takes(manifest: dict, book: Path) -> list[str]:
    """Take files that are no longer the ones the cut used: a different size, or gone."""
    out = []
    for name, row in manifest.items():
        path = Path(book) / row["rel_path"]
        if not path.exists() or path.stat().st_size != row.get("bytes"):
            out.append(name)
    return sorted(out)


def provenance(plan: list[dict], book: Path, manifest: dict | None) -> dict:
    """G5.6 -- only measurable against a manifest recorded when the cut was made; a
    manifest read off the same files it is compared to can never be stale."""
    if not manifest:
        return {"measured": False, "stale_takes": []}
    return {"measured": True, "stale_takes": stale_takes(manifest, book)}


def heads_in(home: Path) -> dict[int, float]:
    """Seconds the cut skipped at the head of a take, from `<episode>/heads.json`
    (ep12 T13: an invented jump at frame 15).  The ONE reader: assemble cuts from
    it and this gate compares from it, so the two can never disagree."""
    import json

    path = Path(home) / "heads.json"
    if not path.exists():
        return {}
    heads = {int(k): float(v) for k, v in json.loads(path.read_text(encoding="utf-8")).items()}
    # A DIALOGUE SHOT IS NEVER HEADED (its wav is anchored in the take's first
    # frames): dropped HERE, in the one reader, so the cut and this gate agree
    # (ep24 2026-10-09: the cut dropped T02's head and the gate still expected it)
    plan = Path(home) / "plan.json"
    if plan.exists():
        lines = json.loads(plan.read_text(encoding="utf-8")).get("lines") or []
        spoken = {l["shot"] for l in lines if l.get("kind") == "dialogue"}
        heads = {i: h for i, h in heads.items() if i not in spoken}
    return heads


def headed(frames: np.ndarray, head_s: float, fps: int = FPS) -> np.ndarray:
    """The take's frames from the one the cut started on."""
    return frames[int(round(head_s * fps)):]


def last_used(frames: np.ndarray, n: int) -> np.ndarray:
    """The segment's last frame: the take's own last one when the cut held past
    it (ep13: 147 frames asked of a 146-frame take crashed QC)."""
    return frames[min(n, len(frames)) - 1]


STILL_FIRST = 8.0
"""The panel against the master's first still frame: the push starts at zoom 1.0,
so the pictures are the same through one scale and one encode (SAME_FRAME is 4.0
for take-vs-take; the PNG-vs-x264 path is allowed twice that)."""


def panel_grey(panel: Path) -> "np.ndarray":
    from PIL import Image
    return np.asarray(Image.open(panel).convert("L").resize((GREY_W, GREY_H), Image.LANCZOS), dtype=np.float64)


def still_match(master: "np.ndarray", start: int, n: int, panel) -> dict:
    """A still segment IS its panel pushed: the first frame is the panel, and no
    frame inside is another picture (the push moves slowly).  ep14 (2026-09-30):
    the gate compared held segments against take files assemble never used."""
    panel = panel if isinstance(panel, np.ndarray) else panel_grey(panel)
    first = frame_diff(master[start], panel) if start < len(master) else 255.0
    steps = [frame_diff(master[start + i], master[start + i + 1])
             for i in range(n - 1) if start + i + 1 < len(master)]
    inside = max(steps) if steps else 0.0
    return {"still": True, "offset": 0, "mean": round(first, 3), "frames_off": [], "held": [],
            "inside_max": round(inside, 3), "ok": first <= STILL_FIRST and inside <= STILL_STEP}


STILL_STEP = 2 * SAME_FRAME
"""A pushed still's frame-to-frame step: twice SAME_FRAME, like STILL_FIRST.
MEASURED: 25 stills ep14-26 read 1.02-3.75; ep26 T06, a detailed panel, rose
smoothly to 4.17-4.57 at the end of its push; another picture reads 32-63."""


def cut_beside_still(master: "np.ndarray", at: int) -> bool:
    """A cut next to a still: the master itself changes picture at the frame."""
    if not 0 < at < len(master):
        return False
    return frame_diff(master[at - 1], master[at]) > SAME_FRAME


def edit_integrity(master_path: Path, placed: dict, records: list[dict], book: Path,
                   card: Path | None, manifest: dict | None = None,
                   heads: dict[int, float] | None = None,
                   stills: dict[int, Path] | None = None, upscale: str = "") -> dict:
    """The whole gate: every segment, every cut, every timestamp, the tail, provenance.
    `upscale` is the master's recorded upscale; it sets the segment cap."""
    master = grey_frames(master_path)
    plan = segment_plan(placed, records)
    heads, stills = heads or {}, stills or {}
    takes = {row["take"]: headed(grey_frames(book / row["rel_path"]), heads.get(row["take"], 0.0))
             for row in plan if row["take"] not in stills}
    segments = [{**row, **(still_match(master, row["start"], row["n"], stills[row["take"]])
                           if row["take"] in stills else
                           segment_match(master, takes[row["take"]], row["start"], row["n"],
                                         cap=segment_cap(upscale), hold=hold_least(upscale)))} for row in plan]
    cuts = [{"at": nxt["start"],
             "exact": (cut_beside_still(master, nxt["start"])
                       if prev["take"] in stills or nxt["take"] in stills else
                       cut_exact(master, nxt["start"], last_used(takes[prev["take"]], prev["n"]), takes[nxt["take"]][0]))}
            for prev, nxt in zip(plan, plan[1:])]
    holes = timestamp_holes(frame_times(master_path))
    tail = tail_check(master, int(round(placed["duration_s"] * FPS)), grey_frames(card) if card else None)
    prov = provenance(plan, book, manifest)
    return {"segments": segments, "cuts": cuts, "timestamp_holes": holes, "tail": tail,
            "cut_manifest": cut_manifest(plan, book), "provenance": prov,
            "stale_takes": prov["stale_takes"],
            "ok": all(s["ok"] for s in segments) and all(c["exact"] for c in cuts) and not holes
            and tail["ok"] and not prov["stale_takes"]}
