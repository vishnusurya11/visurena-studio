#!/usr/bin/env python
"""G4 THE TAKE GATE: one verdict, one score, per rendered r2v take attempt.

`picture_dq` and a second `strip` used to live here and were called by nothing.
`picture_dq` could not have run if they had been: it referenced `sq`, which this
module never imported, so any call was a NameError.  Dead code that cannot run
is worse than dead code that can -- it reads as a working gate.  Its one useful
sentence, the FOREIGN_MARGIN calibration, already lives in `studio/cut_landing.py`.

    uv run python scripts/episode/take_dq.py <codex_id> <episode> <take...> [--attempts]

Every attempt on disk is measured the same way and the ladder returns ONE
number.  HARD: no segment sits frozen more than 1.0 s at its start
(studio.motion_gate), every internal cut lands on its pin and no frame is
another take's cell or a location plate (studio.cut_landing), a drawn END cell
is actually reached, the take stays on its OWN board mid-take -- off-board
share, last frame vs its last pinned cell, no unprompted hard cut
(studio.take_coherence; ep09 scored 28/28 at 100 with 62 % of its frames
off-board) -- and a dialogue take's lips sit within a frame of the wav AND say
the line (WER).  ADVISORY: the frozen share, the churn after pan removal, the
camera numbers, the identity gate while the face model is absent
(studio.identity_gate).  The per-take line prints the coherence rows like the
others: `coherence off-board 0.62 HARD | last-vs-cell 0.08 HARD | cut 32.7 HARD
| churn 10.7 adv`.

With `--attempts` every `T<NN>*.mp4` on disk is judged, the best by
(passed, score) is kept as `T<NN>.mp4` and the file it displaces becomes the
next `T<NN>_failN.mp4` -- which retires the hand-renaming that left
`T18.dq.json` describing a file that no longer existed.  Writes
`shots_r2v/T<NN>.dq.json` and a strip `work_r2v/dq/take_T<NN>.png`.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from PIL import Image, ImageDraw

from studio import av_sync, cut_landing as cl, episode_home, episode_seq_board as sq, frame_match as fm, motion_gate, take_verdict as tv
from studio.trailer_assemble import clip_seconds

SAMPLES = 8
LAG_TOLERANCE = 0.042
WER_CEILING = 0.20
CELLS = 6
SCALE_PER_SECOND = 0.15
"""Engine designer, 2026-09-10: the ±10 % wobble over ~2 s after a snap is
0.10/s; a snap was 0.6-1.8/s; i2v drift is 0.013/s.  Measured at 4 fps in a
1 s window, outside ±0.25 s of a declared cut.

DRIFT AND SNAP ARE THE TWO REGIMES OF A CAMERA HOLDING STILL, and 0.15 is the
line between them.  It was never a question about a camera that MOVES, and every
shot from episode 6 on has one -- so `camera_ok` below is a stillness meter, not
a quality signal.  Measured over all 25 of episode 7's first-pass records:
TRUE on 2 takes (mean 92.95), FALSE on 23 (mean 94.48), and FALSE on all
nineteen that score 100.00.  The two it calls good are the two least-moving
takes in the episode and one of them is a hard failure.

So `camera_ok` stays unread, on purpose.  That is not unfinished wiring, and
`tests/test_camera_ok_is_a_stillness_meter.py` holds the measurement and fails
if the picture ever changes."""
SCENE_EVENT = 0.15


def frame_at(video: Path, at: float, out: Path) -> Image.Image:
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{at:.3f}", "-i", str(video), "-frames:v", "1",
                    str(out)], check=True)
    return fm.load(out)


def expected_cell(t: float, seconds: float, cells: int = CELLS) -> int:
    return min(int(round(t / seconds * (cells - 1))), cells - 1)


def segment_order(anchors: list) -> list[str]:
    """The take's segments (start cells) in time order; an END pin belongs to its start cell."""
    starts = sorted(((f, n) for n, f in anchors if not n.endswith("E.png")), key=lambda x: x[0])
    out = []
    for _, n in starts:
        if n not in out:
            out.append(n)
    return out


def segment_of(anchors: list, k: int, order: list[str]) -> int:
    name = anchors[k][0].replace("E.png", ".png")
    return order.index(name) if name in order else 0


def expected_anchor(anchors: list, at: float) -> int:
    """Index of the latest anchor (start or END pin) at or before `at` seconds."""
    return max(range(len(anchors)), key=lambda i: (anchors[i][1] <= round(at * 24) + 1e-6, anchors[i][1]))


def own_family(anchors: list) -> set[str]:
    """The pictures that belong to this take, by the one rule in
    `cut_landing.own_family`: its anchor cells and each of their END pictures."""
    return cl.own_family({name for name, _ in anchors})



def camera_dq(video: Path, seconds: float, cuts: list[float]) -> dict:
    """Scale change per second and scene events, away from declared cuts."""
    import subprocess as sp

    import numpy as np

    from studio import cell_scale

    raw = sp.run(["ffmpeg", "-v", "error", "-i", str(video), "-t", f"{seconds:.3f}", "-vf", "fps=4,scale=192:336",
                  "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True).stdout
    frames = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 336, 192)
    imgs = [Image.fromarray(f) for f in frames]
    scales = [cell_scale.scale_between(imgs[0], im) for im in imgs]
    worst, events = 0.0, []
    for i in range(1, len(imgs)):
        at = i / 4
        if any(abs(at - c) <= 0.25 for c in cuts):
            continue
        step = abs(scales[i] - scales[i - 1]) * 4          # per second, from a quarter-second step
        worst = max(worst, step)
        sim = fm.similarity(imgs[i - 1], imgs[i])
        if 1 - sim > SCENE_EVENT:
            events.append(round(at, 2))
    return {"scale_curve": [round(s, 2) for s in scales[::4]], "max_scale_per_s": round(worst, 3),
            "scene_events": events, "camera_ok": worst < SCALE_PER_SECOND and not events}


def lag_verdict(lag: float | None, dialogue: bool) -> dict:
    """A narration take's audio is silence by design (owner 2026-09-11 06:00), so
    its envelope lag is noise: only a dialogue take is gated on lag.

    `mux_lag_s`, not `lag_s`: the number is the take's own soundtrack against
    the wav that drove it -- the MUX, which cannot fail (ep10: all seven takes
    at +0.000/-0.010) -- and not the mouth against the words."""
    if not dialogue:
        return {"mux_lag_s": 0.0, "lag_ok": True, "lag_measured": False}
    return {"mux_lag_s": round(lag, 3), "lag_ok": abs(lag) <= LAG_TOLERANCE, "lag_measured": True}


def audio_dq(video: Path, composite: Path, dialogue: bool, work: Path, index: int) -> dict:
    out = lag_verdict(av_sync.take_lag(video, composite) if dialogue else None, dialogue)
    if dialogue:
        from studio import voice_qc

        track = work / f"take_T{index:02d}_track.wav"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(video), "-ac", "1", "-ar", "24000",
                        str(track)], check=True)
        out["heard"] = voice_qc.any_transcriber()(track)
    return out



def segment_kinds(episode, anchors: list) -> dict[str, str]:
    """Cell -> what its segment is (dialogue / track / insert / hold), from the plan.
    A cell whose shot is not in the plan is a hold: the gate never guesses harder."""
    kinds = {}
    for name, _ in anchors:
        try:
            kinds[name] = motion_gate.kind_of(episode.shot(motion_gate.shot_of(name)), episode.lines)
        except (StopIteration, KeyError, ValueError, IndexError):
            kinds[name] = "hold"
    return kinds


def planned_motion(episode, rec: dict) -> str:
    """The plan's motion for the take's first shot: the zoom row's reach word."""
    first = (rec.get("shots") or [rec.get("index")])[0]
    try:
        return episode.shot(first).motion
    except (StopIteration, KeyError, ValueError, IndexError):
        return ""


def planned_motions(episode, rec: dict) -> list[str]:
    """The plan's motion for EVERY shot of the take, one per anchor segment: the
    zoom row judges each segment against its own shot, and an exit clause
    belongs to the segment that planned it."""
    return [planned_motion(episode, {"index": i}) for i in (rec.get("shots") or [rec.get("index")])]


def planned_size(episode, rec: dict) -> str:
    """The plan's size for the take's first shot: the churn row's wall (a wide
    is walled at take_coherence.NONRIGID_WIDE, hard)."""
    first = (rec.get("shots") or [rec.get("index")])[0]
    try:
        return str(episode.shot(first).size)
    except (StopIteration, KeyError, ValueError, IndexError):
        return ""


def line_text(episode, rec: dict) -> str:
    """The dialogue the take is supposed to say, for the word-error rate (G4.6)."""
    if rec.get("lane") != "dialogue":
        return ""
    shots = rec.get("shots") or [rec.get("index")]
    return " ".join(line.text for line in episode.lines if line.kind == "dialogue" and line.shot in shots)




def current_placed(placed: dict, rec: dict) -> float:
    """The take's placed seconds from the CURRENT timeline (the sum over its
    run of shots), not the render record: a line shortened after the render
    moves the shot's end, and the DQ judges the window the edit will use."""
    by = {s["index"]: float(s["seconds"]) for s in placed.get("shots", [])}
    run = rec.get("shots") or [rec.get("index")]
    if all(i in by for i in run):
        return round(sum(by[i] for i in run), 6)
    return float(rec.get("placed_seconds", 0.0))


def fitting(verdicts: dict, placed: float, seconds_of) -> dict:
    """The attempts long enough to fill the shot (a frame of slack); every
    attempt when none is -- ep11 T15's 5.16 s file scored 100 and beat the
    8.25 s re-render that could fill its shot."""
    long = {p: v for p, v in verdicts.items() if seconds_of(p) + 0.05 >= placed}
    return long or verdicts


def settle(take_dir: Path, index: int, verdicts: dict) -> Path:
    """Keep the best attempt by (passed, score) as `T<NN>.mp4`; the file it displaces
    becomes the next `T<NN>_failN.mp4`.  Returns the winner's path before the rename."""
    kept = take_dir / f"T{index:02d}.mp4"
    best = max(verdicts, key=lambda p: tv.rank_key(verdicts[p]))
    if best != kept:
        if kept.exists():
            kept.rename(episode_home.next_fail(take_dir, index))
        best.rename(kept)
    return best


def live_rows(gates: list) -> tuple[int, int]:
    """(rows that CAN fire, rows printed).  A row with no value -- not measured,
    n/a for the lane -- cannot fire, and "30/30 pass" must say how many rows
    it speaks for: over ep05-10 foreign, cut-landing and lip-sync fired 0 times
    on 172 renders and identity never measured (analyst H, change 6)."""
    return sum(g.value is not None for g in gates), len(gates)


def row(index: int, v, kept: str = "", attempts: int = 0) -> str:
    """The one line the run prints per take."""
    live, total = live_rows(v.gates)
    head = f"T{index:02d} {'PASS' if v.passed else 'FAIL'} {v.score:g}/100 ({live} of {total} rows live)"
    gates = " | ".join(f"{g.name} {g.note or g.value}" + ("" if g.ok else (" HARD" if g.hard else " adv"))
                       for g in v.gates)
    return head + (f" | {gates}" if gates else "") + (f" | kept {kept} of {attempts}" if kept else "")


def same_render(a: dict, b: dict) -> bool:
    """One render judged twice: the same file and, when both know it, the same bytes."""
    return a.get("file") == b.get("file") and (a.get("bytes") is None or b.get("bytes") is None
                                               or a.get("bytes") == b.get("bytes"))


def superseded(prior: dict | None, now: list[dict]) -> list[dict]:
    """The prior record's attempts that are not among the renders judged now,
    each marked so.  A re-judged render keeps ONE entry -- the new verdict."""
    return [a | {"superseded": True} for a in (prior or {}).get("attempts", [])
            if not any(same_render(a, n) for n in now)]


def prior_record(take_dir: Path, index: int) -> dict | None:
    """The T<NN>.dq.json about to be overwritten, if any."""
    path = take_dir / f"T{index:02d}.dq.json"
    return episode_home.read_json(path) if path.exists() else None


def record(best, attempts: list, prior: dict | None = None) -> dict:
    """The T<NN>.dq.json record: the kept verdict, every attempt -- the prior
    record's superseded renders first -- and the budget flag over all of them.
    `foreign` and `off_beat` stay scalars so the run cards keep rendering.

    MEASURED ep10 (analyst H): six of the seven retaken takes held
    `attempts == [self]`; the renders the reviewer graded survived only in
    scratch logs, and the next calibration was a log dig."""
    now = [tv.to_json(v) for v in attempts]
    every = superseded(prior, now) + now
    out = tv.to_json(best) | {"attempts": every, "budget_spent": len(every) > tv.RETAKE_BUDGET and not best.passed}
    out["foreign_samples"] = out.pop("foreign", [])
    out["foreign"] = sum(bool(f.get("foreign")) for f in out["foreign_samples"])
    out["off_beat"] = sum(1 for s in out["segments"] if not s["landed"])
    return out


def measure_attempt(video: Path, rec: dict, index: int, cells: Path, work: Path, take_dir: Path,
                    kinds: dict, line: str, attempt: int):
    """One attempt: its audio, then the one verdict every gate feeds.

    `cells` is the CELLS room, `boards/cells/`, not `boards/`: `tv.measure`
    resolves every anchor name against it."""
    seconds = min(clip_seconds(video), rec["placed_seconds"])
    composite = take_dir / (f"voice_{index:02d}.wav" if rec["audio"] != "silence" else f"silence_{index:02d}.wav")
    audio = audio_dq(video, composite, rec["lane"] == "dialogue", work, index)
    v = tv.measure(video, rec, cells, seconds, attempt, audio, line, kinds)
    return v, audio


def wanted(records: dict, indices: list[int]) -> list[int]:
    """Which takes to measure: the ones asked for, or every one that exists.

    MEASURED on episode 7: 26 shots became 25 takes because `episode_takes.
    groups` packed two shots into one, so take 5 is not on disk.  Called with
    `seq 0 25` -- the shot count -- the run died at `records[index]` after 5 of
    25 reports, and the five it had written were the only evidence of how far
    it got.  The caller cannot know the packing; `shots.json` already does."""
    if not indices:
        return sorted(records)
    missing = sorted(set(indices) - set(records))
    if missing:
        have = f"{min(records)}-{max(records)}" if records else "none"
        raise SystemExit(f"no take rendered for {missing}; takes on disk: {have}")
    return sorted(set(indices))


def daylit(episode, rec: dict) -> bool:
    """Is this take's setup an exterior lit by the sky (the look floor is advisory there)?"""
    from studio import take_look

    setup = episode.setups.get(rec.get("setup", ""))
    return bool(setup) and take_look.is_daylight(setup.described, setup.outdoors)


def main(book_id: str, number: int, indices: list[int], attempts: bool = False) -> None:
    book = episode_home.book_dir(book_id)
    home = episode_home.home(book, number)
    episode = episode_home.load_plan(book, number)
    boards, take_dir = episode_home.boards_dir(book, number), episode_home.takes_dir(book, number, "r2v")
    cells = sq.cells_in(boards)
    work = episode_home.work_dir(book, number, "r2v") / "dq"
    work.mkdir(parents=True, exist_ok=True)
    records = {r["index"]: r for r in episode_home.read_json(take_dir / "shots.json")}
    for index in wanted(records, indices):
        rec = records[index]
        kinds, line = segment_kinds(episode, rec.get("anchors", [])), line_text(episode, rec)
        rec["motion"], rec["motions"] = planned_motion(episode, rec), planned_motions(episode, rec)
        rec["size"] = planned_size(episode, rec)
        rec["placed_seconds"] = current_placed(episode_home.read_json(home / "placed.json"), rec)
        rec["daylight"] = daylit(episode, rec)
        files = episode_home.attempts_of(take_dir, index) if attempts else [book / rec["rel_path"]]
        judged = {f: measure_attempt(f, rec, index, cells, work, take_dir, kinds, line, k)
                  for k, f in enumerate(files)}
        verdicts = {f: v for f, (v, _) in judged.items()}
        best = (settle(take_dir, index, fitting(verdicts, rec["placed_seconds"], clip_seconds))
                if attempts else files[0])
        v, audio = judged[best]
        kept = take_dir / f"T{index:02d}.mp4" if attempts else best
        report = record(v, list(verdicts.values()), prior_record(take_dir, index))
        report["audio"], report["camera"] = audio, camera_dq(kept, v.seconds, [f / 24 for _, f in rec.get("anchors", [])][1:])
        report["strip"] = str(tv.strip(v, kept, cells, work / f"take_T{index:02d}.png"))
        episode_home.write_json(take_dir / f"T{index:02d}.dq.json", report)
        print(row(index, v, best.name if attempts else "", len(files)), flush=True)


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]), [int(a) for a in sys.argv[3:] if a.isdigit()],
         attempts="--attempts" in sys.argv)
