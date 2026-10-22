"""Reader 2 for the mouth exam: face_yolov8m's speaker box (the face refine's detector and
tracker), the lower face's frame-to-frame motion less the upper face's (a pan or a head move
moves both; a mouth moves only the lower), against the line's PHRASES (voiced runs, short gaps
closed, flickers dropped), scored per phrase.  Developed on the five other ep01 dialogue takes
(T03 T04 T11 T20 T23) only, never on an exam render (exam/PREREG_exam.md).  These tests use
synthetic crops and series; nothing decodes video or opens a model.
"""
import numpy as np
import pytest

from studio.measure import mouth_motion as mm


def line_with(runs, n=60, loud=0.05, quiet=0.001) -> np.ndarray:
    x = np.full(n, quiet)
    for a, b in runs:
        x[a:b] = loud
    return x


def test_phrases_close_short_gaps_and_drop_flickers():
    line = line_with([(5, 15), (16, 25), (40, 41), (45, 55)])
    assert mm.phrases(line) == [(5, 25), (45, 55)]


def test_the_gate_is_one_on_the_phrases():
    g = mm.gate(line_with([(5, 15)]), 20)
    assert g.tolist() == [0.0] * 5 + [1.0] * 10 + [0.0] * 5


def test_motion_is_the_mean_change_from_the_last_frame():
    stack = np.zeros((3, 4, 4))
    stack[1] += 2.0
    assert mm.motion(stack).tolist() == [2.0, 2.0, 2.0]


def frames_of(mouth_on, pan) -> np.ndarray:
    """64x64 face crops: a soft texture panned `pan[t]` px, the mouth rows dark when `mouth_on[t]`."""
    y, x = np.mgrid[0:64, 0:200]
    tex = 128 + 60 * np.sin(x / 9.0) + 40 * np.sin(y / 7.0)
    out = []
    for on, p in zip(mouth_on, pan):
        f = tex[:, p:p + 64].copy()
        if on:
            f[40:50, 24:40] = 0.0
        out.append(f)
    return np.array(out)


def test_a_pan_moves_both_halves_and_cancels():
    on = np.zeros(40)
    on[10:20] = 1
    m = mm.face_motion(frames_of(on, np.arange(40) * 2))
    assert abs(np.median(m)) < 1.0 and m[10] > 10 and m[20] > 10


def test_the_speaker_is_the_biggest_longest_face():
    dets = {t: [{"box": [10, 10, 30, 30], "score": 0.9}, {"box": [200, 100, 320, 220], "score": 0.9}]
            for t in range(0, 30, 3)}
    boxes, seen = mm.speaker(dets, 30)
    assert boxes.shape == (30, 4) and seen.all() and boxes[15, 2] - boxes[15, 0] > 100


def test_no_face_reads_nothing():
    boxes, seen = mm.speaker({0: [], 3: []}, 6)
    assert boxes is None and not seen.any()


@pytest.mark.parametrize("k", [-8, 0, 5, 16])
def test_a_mouth_moving_k_frames_after_the_phrases_reads_k(k):
    line = line_with([(10, 40), (60, 90)], n=124)
    m = np.roll(mm.gate(line, 124), k) + np.random.default_rng(1).normal(0, 0.2, 124)
    lag, score, measured = mm.fit(m, line, 20)
    assert abs(lag - k) <= 1 and score > 0.5 and measured is True


def test_a_still_mouth_is_not_measured():
    line = line_with([(10, 40), (60, 90)], n=124)
    assert mm.fit(np.random.default_rng(2).normal(0, 1, 124), line, 20)[2] is False
    assert mm.fit(np.full(124, np.nan), line, 20)[2] is False


def test_onsets_read_per_phrase_and_silence_motion_is_a_share():
    line = line_with([(10, 40), (60, 90)], n=124)
    m = np.roll(mm.gate(line, 124), 4)
    assert mm.onset_errors(m, line, 20) == [4, 4]
    assert mm.silence_motion(m, line, 4) == 0.0
    assert mm.silence_motion(np.ones(124), line, 0) == 1.0
