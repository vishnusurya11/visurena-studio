"""SFX onset placer (owner go 2026-10-17, "sound effects placed on the measured moment").

The plan says WHAT a shot sounds like and roughly WHEN (`Sound.at`); the take
says exactly when.  `studio.sfx_onset` measures the take -- the walker's stride
width for footsteps, the residual motion around the people for a single event --
and lays the Stable Audio 3 cue so its own first onset lands on that frame;
footsteps go one by one, a slice of the render per measured heel strike.
Validated on Jekyll ep01 T03/T06/T09 against the hand-marked onsets of the
2026-10-16 battery (sfx_metrics.json).  No test opens a video or ComfyUI."""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from studio import sfx_onset as so
from studio.sfx_cues import Cue

RATE = 48000


# ------------------------------------------------------------- what to look for

@pytest.mark.parametrize("sound,kind", [
    ("hard boot heels striking frosted flagstones", "steps"),
    ("footsteps on stone pavement", "steps"),
    ("a man's boots striding briskly on cobbles", "steps"),
    ("an iron key turning in an old lock, one click", "motion"),
    ("a heavy wooden door creaking open", "motion"),
    ("a heavy leather boot stamps down hard, a dull thud", "motion"),
    ("a young girl screaming", ""),
    ("a man shouting halloa", ""),
    ("distant church bells tolling", ""),
])
def test_the_sound_says_what_the_picture_must_show(sound, kind):
    assert so.kind_of(sound) == kind


# ------------------------------------------------------------- the walker

def walking_boxes(n: int = 60) -> list[list[list[float]]]:
    """A big man fixed at the left edge (feet cut off) and a small walker crossing
    to the right whose stride width peaks every 16 frames, from frame 8."""
    out = []
    for k in range(n):
        width = 40 + 12 * math.cos(2 * math.pi * (k - 8) / 16)
        x = 100 + 2 * k
        out.append([[0, 160, 100, 384, 0.94], [x, 140, x + width, 258, 0.9]])
    return out


def test_tracks_link_a_box_to_the_same_person_frame_to_frame():
    tracks = so.tracks(walking_boxes())
    assert sorted(len(t) for t in tracks) == [60, 60]


def test_the_walker_is_the_one_who_crosses_the_ground_not_the_biggest():
    boxes = walking_boxes()
    walker = so.walker(so.tracks(boxes), pan=np.zeros(len(boxes)))
    assert walker[0][0] == 100


def test_strikes_are_the_stride_width_peaks():
    boxes = walking_boxes()
    walker = so.walker(so.tracks(boxes), pan=np.zeros(len(boxes)))
    got = so.strike_times(so.widths(walker, len(boxes)), fps=24)
    assert got == pytest.approx([8 / 24, 24 / 24, 40 / 24, 56 / 24], abs=0.02)


def test_peaks_refine_between_frames():
    x = np.cos(2 * np.pi * (np.arange(40) - 10.5) / 20)
    assert so.peaks(x, gap=5)[0] == pytest.approx(10.5, abs=0.1)


def test_a_duplicate_frame_does_not_split_one_motion_into_two():
    """H3 repeats a frame every second or third: the flow between the twins is
    ~0, a dip that is no event."""
    raw = np.array([0.2, 0.2, 1.0, 0.1, 1.2, 0.1, 1.4, 0.1, 1.2, 0.1, 1.0, 0.1, 0.2, 0.2])
    env = so.envelope(raw)
    assert len(so.peaks(env, gap=4, prominence=0.05)) == 1


# ------------------------------------------------------------- which event a cue takes

def test_a_single_event_takes_the_strongest_motion_peak_near_its_planned_time():
    peaks = [(0.42, 0.6), (1.09, 0.75), (2.09, 0.91), (2.58, 0.82), (4.26, 1.09)]
    assert so.strongest_near(peaks, at=2.0) == 2.09


def test_no_peak_near_the_plan_is_no_event():
    assert so.strongest_near([(0.4, 1.0), (4.2, 1.0)], at=2.0) is None


def test_footsteps_take_every_strike_inside_the_cue_span():
    assert so.strikes_in([0.06, 0.72, 1.42, 2.14, 2.88, 3.6], start=0.3, seconds=2.5) == [0.72, 1.42, 2.14]


# ------------------------------------------------------------- the cue's own onset

def clicks(path: Path, at: list[float], seconds: float = 2.0) -> Path:
    y = np.random.default_rng(0).normal(0, 1e-4, int(seconds * RATE)).astype(np.float32)
    for t in at:
        i = int(t * RATE)
        y[i:i + 2400] += (0.5 * np.exp(-np.arange(2400) / 400.0)).astype(np.float32)
    sf.write(str(path), y, RATE)
    return path


def test_the_first_onset_of_a_render_is_where_its_sound_starts(tmp_path):
    y, rate = sf.read(str(clicks(tmp_path / "c.wav", [0.30])), dtype="float32")
    assert so.first_onset(y, rate) == pytest.approx(0.30, abs=0.01)


def test_a_footsteps_render_splits_into_its_steps(tmp_path):
    y, rate = sf.read(str(clicks(tmp_path / "c.wav", [0.10, 0.62, 1.15])), dtype="float32")
    assert so.onsets(y, rate) == pytest.approx([0.10, 0.62, 1.15], abs=0.01)


def test_each_step_slice_starts_on_its_onset(tmp_path):
    src = clicks(tmp_path / "steps.wav", [0.10, 0.62, 1.15])
    got = so.step_slices(src, tmp_path / "slices")
    assert len(got) == 3
    first, rate = sf.read(str(got[1]), dtype="float32")
    assert so.first_onset(first, rate) == pytest.approx(so.PRE_ROLL, abs=0.006)


# ------------------------------------------------------------- the clock

def test_take_seconds_map_onto_the_master_through_the_run_start_and_head():
    assert so.master_time(event=2.09, run_start=31.0, head=0.25) == pytest.approx(32.84)


def test_a_shot_inside_a_run_starts_after_the_earlier_shots_of_its_take():
    rows = {4: {"t_start": 10.0, "seconds": 3.0}, 5: {"t_start": 13.0, "seconds": 2.0}}
    assert so.shot_in_take(5, run=[4, 5], rows=rows, head=0.5) == pytest.approx(3.5)


def test_a_motion_cue_is_shifted_so_its_onset_hits_the_event():
    assert so.cue_start(event_master=12.0, onset=0.18) == pytest.approx(11.82)


# ------------------------------------------------------------- the episode path

def test_placing_a_motion_cue_uses_the_measurement(tmp_path):
    wav = clicks(tmp_path / "shot06_x.wav", [0.20], seconds=3.0)
    cue = Cue(shot=6, sound="a heavy leather boot stamps down hard", at=2.0, seconds=3.0)
    rows = {6: {"index": 6, "t_start": 30.0, "seconds": 10.0}}
    curves = {"fps": 24, "strikes": [], "motion": [[0.42, 0.6], [2.09, 0.91], [2.58, 0.82]]}
    placed, row = so.place_cue(cue, wav, rows, take={"run": [6], "head": 0.0, "curves": curves}, work=tmp_path)
    assert row["kind"] == "motion" and row["event_take_s"] == 2.09
    assert placed == [(pytest.approx(30.0 + 2.09 - 0.20, abs=0.01), wav)]


def test_footsteps_are_laid_one_slice_per_strike(tmp_path):
    wav = clicks(tmp_path / "shot04_x.wav", [0.10, 0.62, 1.15], seconds=3.0)
    cue = Cue(shot=4, sound="hard boot heels striking frosted flagstones", at=0.3, seconds=3.0)
    rows = {4: {"index": 4, "t_start": 20.0, "seconds": 6.0}}
    curves = {"fps": 24, "strikes": [0.06, 0.72, 1.42, 2.14, 2.88, 3.6], "motion": []}
    placed, row = so.place_cue(cue, wav, rows, take={"run": [4], "head": 0.0, "curves": curves}, work=tmp_path)
    assert row["kind"] == "steps" and row["events_take_s"] == [0.72, 1.42, 2.14, 2.88]
    assert [round(t + so.PRE_ROLL, 2) for t, _ in placed] == [20.72, 21.42, 22.14, 22.88]


def test_a_cue_the_picture_cannot_place_keeps_its_planned_time(tmp_path):
    wav = clicks(tmp_path / "shot06_y.wav", [0.20], seconds=3.0)
    cue = Cue(shot=6, sound="a young girl screaming", at=2.0, seconds=3.0)
    rows = {6: {"index": 6, "t_start": 30.0, "seconds": 10.0}}
    placed, row = so.place_cue(cue, wav, rows, take={"run": [6], "head": 0.0, "curves": {"motion": [[2.1, 1.0]]}},
                               work=tmp_path)
    assert placed == [(32.0, wav)] and row["fallback"]


def test_a_shot_with_no_measured_take_keeps_its_planned_time(tmp_path):
    wav = clicks(tmp_path / "shot06_z.wav", [0.20], seconds=3.0)
    cue = Cue(shot=6, sound="a heavy door creaking open", at=2.0, seconds=3.0)
    rows = {6: {"index": 6, "t_start": 30.0, "seconds": 10.0}}
    placed, row = so.place_cue(cue, wav, rows, take=None, work=tmp_path)
    assert placed == [(32.0, wav)] and "no measured take" in row["fallback"]


def test_the_placements_are_written_for_qc(tmp_path):
    rows = [{"shot": 6, "sound": "a door", "starts": [11.82], "kind": "motion"}]
    so.write_report(tmp_path, rows)
    assert so.measured_starts(tmp_path) == {"6|a door": 11.82}
    assert json.loads((tmp_path / so.REPORT).read_text(encoding="utf-8"))["cues"] == rows


# ------------------------------------------------------------- measuring a take (synthetic frames)

def square_frames(n: int = 48, size: int = 96) -> list[np.ndarray]:
    """A grey field; a white block that rests, jumps right fast at frames 20-24, rests."""
    out = []
    for k in range(n):
        f = np.full((size, size, 3), 60, np.uint8)
        f[::8, :, :] = 90                                   # texture for the flow to read
        x = 20 + int(np.clip(k - 20, 0, 4)) * 8
        f[30:70, x:x + 20] = 230
        out.append(f)
    return out


def fake_detect(frame: np.ndarray) -> list:
    ys, xs = np.nonzero(frame[..., 0] > 200)
    return [((float(xs.min()), float(ys.min()), float(xs.max()), float(ys.max())), 0.9)] if len(xs) else []


def test_curves_find_the_one_burst_of_motion():
    got = so.curves_of(square_frames(), fake_detect)
    assert got["frames"] == 48
    assert [t for t, _ in got["motion"]] == pytest.approx([22 / 24], abs=2 / 24)


def test_a_measurement_is_cached_by_the_takes_bytes(tmp_path, monkeypatch):
    video = tmp_path / "T06.mp4"
    video.write_bytes(b"take one")
    calls = []
    monkeypatch.setattr(so, "read_frames", lambda v: calls.append(v) or square_frames())
    first = so.measured(video, tmp_path / "measured", detect=fake_detect)
    again = so.measured(video, tmp_path / "measured", detect=fake_detect)
    assert first == again and len(calls) == 1
    video.write_bytes(b"take two")
    so.measured(video, tmp_path / "measured", detect=fake_detect)
    assert len(calls) == 2


# ------------------------------------------------------------- the episode wiring

def episode_home(tmp_path: Path, heads: dict | None = None) -> Path:
    home = tmp_path / "ep01"
    (home / "takes" / "r2v").mkdir(parents=True)
    (home / "takes" / "work").mkdir(parents=True)
    (home / "takes" / "r2v" / "shots.json").write_text(json.dumps(
        [{"index": 4, "shots": [4, 5]}, {"index": 6, "shots": [6]}]), encoding="utf-8")
    for i in (4, 6):
        (home / "takes" / "r2v" / f"T{i:02d}.mp4").write_bytes(b"x")
    layout = [{"index": 4, "seconds": 5.0, "head": 0.5, "slow": 1.0, "still": False},
              {"index": 6, "seconds": 10.0, "head": 0.0, "slow": 1.0, "still": False}]
    (home / "takes" / "work" / "layout.json").write_text(json.dumps(layout), encoding="utf-8")
    return home


def test_the_take_of_a_shot_is_the_run_that_holds_it(tmp_path):
    home = episode_home(tmp_path)
    got = so.takes_for(home, [5, 6], measure=lambda video: {"strikes": [], "motion": [], "video": video.name})
    assert got[5]["run"] == [4, 5] and got[5]["head"] == 0.5 and got[5]["curves"]["video"] == "T04.mp4"
    assert got[6]["run"] == [6] and got[6]["head"] == 0.0


def test_a_slowed_or_still_take_is_not_measured(tmp_path):
    home = episode_home(tmp_path)
    layout = json.loads((home / "takes/work/layout.json").read_text(encoding="utf-8"))
    layout[1]["slow"] = 1.4
    (home / "takes/work/layout.json").write_text(json.dumps(layout), encoding="utf-8")
    assert 6 not in so.takes_for(home, [6], measure=lambda video: {"motion": []})


def test_no_takes_at_all_is_no_measurement(tmp_path):
    assert so.takes_for(tmp_path / "nowhere", [6], measure=lambda video: {}) == {}


def test_place_all_lays_every_cue_and_writes_the_report(tmp_path):
    home = episode_home(tmp_path)
    folder = home / "audio" / "sfx"
    folder.mkdir(parents=True)
    a = clicks(folder / "shot06_a.wav", [0.20], seconds=3.0)
    b = clicks(folder / "shot06_b.wav", [0.20], seconds=3.0)
    rendered = [(Cue(shot=6, sound="a heavy door creaking open", at=2.0, seconds=3.0), a),
                (Cue(shot=6, sound="a young girl screaming", at=2.0, seconds=3.0), b)]
    shots = [{"index": 6, "t_start": 30.0, "seconds": 10.0}]
    got = so.place_all(rendered, shots, home, folder,
                       measure=lambda video: {"strikes": [], "motion": [[2.09, 0.9]]})
    assert got == [(pytest.approx(31.89, abs=0.01), a), (32.0, b)]
    assert so.measured_starts(folder)["6|a heavy door creaking open"] == pytest.approx(31.89, abs=0.01)


# ------------------------------------------------------------- the episode sound layer uses it

def test_the_episode_layer_lays_its_effects_through_the_placer(tmp_path, monkeypatch):
    from types import SimpleNamespace as NS
    from studio import episode_sound as es
    from studio.episode_spec import Sound
    ep = NS(number=1, where="", setups={"s": NS(ambience="")},
            shots=[NS(index=6, setup="s", sounds=[Sound(sound="a heavy door creaking open", at=2.0)])])
    placed = {"shots": [{"index": 6, "t_start": 30.0, "seconds": 10.0}]}
    monkeypatch.setattr(es.sfx_cues, "render_all", lambda cues, folder, seed, run=None, where="":
                        [(c, tmp_path / "door.wav") for c in cues])
    calls = []
    monkeypatch.setattr(es.sfx_onset, "place_all", lambda rendered, shots, home, folder:
                        calls.append((len(rendered), home)) or [(31.89, tmp_path / "door.wav")])
    assert es.layer(tmp_path, ep, placed) == [(31.89, tmp_path / "door.wav")]
    assert calls == [(1, tmp_path)]


def test_qc_listens_where_the_cue_was_laid_not_where_it_was_planned(tmp_path, monkeypatch):
    from types import SimpleNamespace as NS
    from studio import episode_sound as es
    from studio.episode_spec import Sound
    home = tmp_path / "ep01"
    so.write_report(home / "audio" / "sfx", [{"shot": 2, "sound": "a door slams", "starts": [11.82]}])
    ep = NS(number=1, where="", setups={}, shots=[NS(index=2, setup="s", sounds=[Sound(sound="a door slams", at=0.5)])])
    placed = {"shots": [{"index": 2, "t_start": 10.0, "seconds": 4.0}]}
    heard = []
    monkeypatch.setattr(es.sfx_cues, "event_db", lambda master, start, seconds, **_: heard.append(start) or 9.0)
    rows = es.presence(home / "cut" / "m.mp4", ep, placed)
    assert heard == [11.82] and rows[0]["at"] == 11.82


def test_a_sound_never_starts_before_the_episode():
    """Jekyll ep06 shot 0 (2026-10-29): the door's event 0.021 s into the first take, less the file's own
    0.04 s lead-in, laid the cue at -0.019 s; ffmpeg's adelay refused it (-22) and step 10 could not mix."""
    from studio import sfx_onset
    assert sfx_onset.cue_start(0.021, 0.04) == 0.0
    assert sfx_onset.cue_start(5.0, 0.04) == 4.96
