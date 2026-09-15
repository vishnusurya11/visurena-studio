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
is actually reached, and a dialogue take's lips sit within a frame of the wav
AND say the line (WER).  ADVISORY: the frozen share, the camera numbers, the
identity gate while the face model is absent (studio.identity_gate).

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
    its envelope lag is noise: only a dialogue take is gated on lag."""
    if not dialogue:
        return {"lag_s": 0.0, "lag_ok": True, "lag_measured": False}
    return {"lag_s": round(lag, 3), "lag_ok": abs(lag) <= LAG_TOLERANCE, "lag_measured": True}


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


def line_text(episode, rec: dict) -> str:
    """The dialogue the take is supposed to say, for the word-error rate (G4.6)."""
    if rec.get("lane") != "dialogue":
        return ""
    shots = rec.get("shots") or [rec.get("index")]
    return " ".join(line.text for line in episode.lines if line.kind == "dialogue" and line.shot in shots)




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


def row(index: int, v, kept: str = "", attempts: int = 0) -> str:
    """The one line the run prints per take."""
    head = f"T{index:02d} {'PASS' if v.passed else 'FAIL'} {v.score:g}/100"
    gates = " | ".join(f"{g.name} {g.note or g.value}" + ("" if g.ok else (" HARD" if g.hard else " adv"))
                       for g in v.gates)
    return head + (f" | {gates}" if gates else "") + (f" | kept {kept} of {attempts}" if kept else "")


def record(best, attempts: list) -> dict:
    """The T<NN>.dq.json record: the kept verdict, every attempt, and the budget flag.
    `foreign` and `off_beat` stay scalars so the run cards keep rendering."""
    out = tv.to_json(best) | {"attempts": [tv.to_json(v) for v in attempts],
                              "budget_spent": len(attempts) > tv.RETAKE_BUDGET and not best.passed}
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
        files = episode_home.attempts_of(take_dir, index) if attempts else [book / rec["rel_path"]]
        judged = {f: measure_attempt(f, rec, index, cells, work, take_dir, kinds, line, k)
                  for k, f in enumerate(files)}
        verdicts = {f: v for f, (v, _) in judged.items()}
        best = settle(take_dir, index, verdicts) if attempts else files[0]
        v, audio = judged[best]
        kept = take_dir / f"T{index:02d}.mp4" if attempts else best
        report = record(v, list(verdicts.values()))
        report["audio"], report["camera"] = audio, camera_dq(kept, v.seconds, [f / 24 for _, f in rec.get("anchors", [])][1:])
        report["strip"] = str(tv.strip(v, kept, cells, work / f"take_T{index:02d}.png"))
        episode_home.write_json(take_dir / f"T{index:02d}.dq.json", report)
        print(row(index, v, best.name if attempts else "", len(files)), flush=True)


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]), [int(a) for a in sys.argv[3:] if a.isdigit()],
         attempts="--attempts" in sys.argv)
