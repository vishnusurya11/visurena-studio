"""G-ZOOM -- how far did the push actually travel?

Episode 10: the ref2v model turns "a hand's breadth" into a dolly that ends
one or two sizes tighter (T05's first render ended on nostrils) and every
existing gate passed it, because none of them measures scale.  Everything here
is synthetic: a textured picture progressively centre-cropped and resized is a
push of KNOWN ratio, written as PNG frames on tmp_path.  No ffmpeg, no GPU, no
repo asset, nothing paid.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from studio import take_zoom as tz

SIZE = 256


def picture(seed: int, size: int = SIZE) -> np.ndarray:
    """A grey picture with STRUCTURE: hard-edged rectangles and discs plus grain,
    so that every window of it has something to match on."""
    rng = np.random.default_rng(seed)
    y, x = np.mgrid[0:size, 0:size]
    img = np.full((size, size), rng.uniform(40, 200))
    for _ in range(60):
        cx, cy = rng.uniform(0, size, 2)
        w, h, tone = rng.uniform(size / 20, size / 4), rng.uniform(size / 20, size / 4), rng.uniform(0, 255)
        if rng.uniform() < 0.5:
            img[(np.abs(x - cx) < w / 2) & (np.abs(y - cy) < h / 2)] = tone
        else:
            img[((x - cx) ** 2 + (y - cy) ** 2) < (w / 2) ** 2] = tone
    return np.clip(img + rng.normal(0, 3, img.shape), 0, 255).astype(np.uint8)


def dolly(pic: np.ndarray, n: int, zoom: float) -> np.ndarray:
    """n frames whose apparent scale goes 1 -> zoom (>1 tighter, <1 wider).
    A pull-back starts from a centre crop so the last frame is the full picture."""
    im, s = Image.fromarray(pic), pic.shape[0]
    out = []
    for k in range(n):
        z = 1 + (zoom - 1) * k / max(n - 1, 1)
        z = z if zoom >= 1 else z / zoom            # pull-back: z runs 1/zoom -> 1
        c = int(round(s / z))
        o = (s - c) // 2
        out.append(np.asarray(im.crop((o, o, o + c, o + c)).resize((s, s), Image.BILINEAR)))
    return np.stack(out)


def hold(pic: np.ndarray, n: int, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return np.clip(pic[None].astype(np.int16) + rng.integers(-2, 3, (n, *pic.shape)), 0, 255).astype(np.uint8)


def walker(frames: np.ndarray, seed: int = 3) -> np.ndarray:
    """A textured 'person' a fifth of the frame wide crossing left to right,
    independent of the camera, so that RANSAC has something to discard."""
    n, h, w = frames.shape
    rng = np.random.default_rng(seed)
    body = rng.integers(0, 255, (h // 3, w // 5)).astype(np.uint8)
    out = frames.copy()
    for k in range(n):
        x0 = int((w - w // 5) * k / max(n - 1, 1))
        out[k, h // 3:h // 3 + h // 3, x0:x0 + w // 5] = body
    return out


def grower(back: np.ndarray, n: int, zoom: float, seed: int = 5) -> np.ndarray:
    """A still room with a textured 'person' filling half the frame at the centre
    and growing by `zoom` over the clip -- the model walking him at the lens."""
    h, w = back.shape
    rng = np.random.default_rng(seed)
    body = Image.fromarray(rng.integers(0, 255, (h // 2, w // 2)).astype(np.uint8))
    out = np.repeat(back[None], n, axis=0)
    for k in range(n):
        size = int(round(h / 2 * (1 + (zoom - 1) * k / max(n - 1, 1))))
        y0, x0 = (h - size) // 2, (w - size) // 2
        out[k, y0:y0 + size, x0:x0 + size] = np.asarray(body.resize((size, size), Image.BILINEAR))
    return out


def write_frames(frames: np.ndarray, folder: Path) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    for k, f in enumerate(frames):
        Image.fromarray(f).save(folder / f"f{k:04d}.png")
    return folder


# ---- the ratio -----------------------------------------------------------------

def test_a_push_recovers_its_ratio_within_15_percent(tmp_path):
    clip = write_frames(dolly(picture(1), 24, 1.8), tmp_path / "push")
    z = tz.zoom(clip, samples=6)
    assert z["measured"] is True
    assert abs(z["ratio"] - 1.8) / 1.8 < 0.15
    assert z["monotonic"] is True and len(z["per_step"]) == 5
    assert all(s > 1 for s in z["per_step"])


def test_a_pull_back_recovers_its_ratio_within_15_percent(tmp_path):
    clip = write_frames(dolly(picture(2), 24, 1 / 1.8), tmp_path / "pull")
    z = tz.zoom(clip, samples=6)
    assert z["measured"] is True
    assert abs(z["ratio"] - 1 / 1.8) / (1 / 1.8) < 0.15
    assert z["monotonic"] is True and all(s < 1 for s in z["per_step"])


def test_a_static_clip_reads_one(tmp_path):
    clip = write_frames(hold(picture(3), 24), tmp_path / "hold")
    z = tz.zoom(clip, samples=6)
    assert z["measured"] is True
    assert abs(z["ratio"] - 1.0) < 0.05
    assert z["monotonic"] is True


def test_a_walking_person_does_not_move_the_ratio(tmp_path):
    clip = write_frames(walker(dolly(picture(4), 24, 1.5)), tmp_path / "walk")
    z = tz.zoom(clip, samples=6)
    assert z["measured"] is True
    assert abs(z["ratio"] - 1.5) / 1.5 < 0.15


def test_the_ratio_is_read_from_the_head_of_the_clip_only(tmp_path):
    """A two-shot take: the first shot pushes 1.5x, then a hard cut to a held
    picture.  With end_frame at the cut the second shot is not read."""
    first = dolly(picture(5), 20, 1.5)
    clip = write_frames(np.concatenate([first, hold(picture(6), 20)]), tmp_path / "two")
    z = tz.zoom(clip, samples=6, end_frame=20)
    assert abs(z["ratio"] - 1.5) / 1.5 < 0.15


def test_a_textureless_clip_is_not_measured(tmp_path):
    flat = np.full((12, SIZE, SIZE), 128, np.uint8)
    z = tz.zoom(write_frames(flat, tmp_path / "flat"), samples=4)
    assert z["measured"] is False and z["ratio"] == 1.0


def test_zoom_accepts_a_frame_array_directly():
    z = tz.zoom_frames(dolly(picture(7), 12, 1.4), samples=4)
    assert abs(z["ratio"] - 1.4) / 1.4 < 0.15


def test_the_camera_read_comes_from_the_whole_frame():
    """A pure zoom: subject and camera agree.  A walker through the centre
    changes neither, because RANSAC discards him from both fields."""
    z = tz.zoom_frames(walker(dolly(picture(10), 12, 1.5)), samples=4)
    assert abs(z["camera"] - 1.5) / 1.5 < 0.15 and abs(z["ratio"] - 1.5) / 1.5 < 0.15
    assert len(z["camera_steps"]) == len(z["per_step"]) == 3


def test_a_person_growing_in_a_still_room_reads_on_the_subject_not_the_camera():
    """Episode 10 T12 / T25 / T33: the room zooms little, the man grows a size.
    The judged ratio is the man's; the whole-frame read, with the room's
    windows voting, sits well under it."""
    z = tz.zoom_frames(grower(picture(11), 24, 1.6), samples=6)
    assert z["measured"] is True
    assert abs(z["ratio"] - 1.6) / 1.6 < 0.15
    assert z["camera"] < z["ratio"] - 0.15


# ---- the step ------------------------------------------------------------------

def test_step_scale_reads_one_zoom_step():
    a, b = dolly(picture(8), 2, 1.12)
    s, inliers = tz.step_scale(a, b)
    assert abs(s - 1.12) < 0.03 and inliers >= tz.MIN_INLIERS


def test_a_pure_pan_is_scale_one():
    big = picture(9, SIZE + 32)
    s, inliers = tz.step_scale(big[:SIZE, :SIZE], big[:SIZE, 12:12 + SIZE])
    assert abs(s - 1.0) < 0.02 and inliers >= tz.MIN_INLIERS


def test_monotonic_ignores_still_steps_and_catches_a_reversal():
    assert tz.is_monotonic([1.1, 1.05, 1.0, 1.08]) is True
    assert tz.is_monotonic([0.95, 0.9, 0.97]) is True
    assert tz.is_monotonic([1.1, 0.9]) is False
    assert tz.is_monotonic([]) is True


# ---- the verdict ---------------------------------------------------------------

HAND = "The camera pushes in on the face across the whole shot, travelling a hand's breadth; he lifts his chin."
FINGER = "The camera pushes in on the hand across the whole shot, travelling a finger's breadth."
FOREARM = "The camera pushes in on Brigham Young across the whole shot, travelling a forearm; he lays one hand flat."
STRIDE = "The camera pushes in on the two men across the whole shot, travelling one long stride."
PULL = "The camera pulls back from Brigham Young's face across the whole shot, travelling a hand's breadth."


def test_planned_reach_is_read_from_the_motion_words():
    assert tz.planned_reach(HAND) == "hand"
    assert tz.planned_reach(FINGER) == "finger"
    assert tz.planned_reach(FOREARM) == "forearm"
    assert tz.planned_reach(STRIDE) == "stride"
    assert tz.planned_direction(PULL) == -1 and tz.planned_direction(HAND) == 1


@pytest.mark.parametrize("planned", [HAND, FINGER])
def test_a_hand_or_finger_push_is_hard_at_the_wall(planned):
    assert tz.judge(tz.OVER_PUSH - 0.05, planned)["hard"] == []
    v = tz.judge(tz.OVER_PUSH + 0.05, planned)
    assert v["ok"] is False and len(v["hard"]) == 1 and tz.planned_reach(planned) in v["hard"][0]


@pytest.mark.parametrize("planned", [FOREARM, STRIDE])
def test_a_forearm_or_stride_push_has_the_higher_wall(planned):
    assert tz.judge(tz.OVER_PUSH + 0.05, planned)["hard"] == []
    assert tz.judge(tz.OVER_PUSH_LONG - 0.05, planned)["hard"] == []
    assert tz.judge(tz.OVER_PUSH_LONG + 0.05, planned)["ok"] is False


def test_the_walls_are_ordered():
    assert 1.0 < tz.ADVISORY_PUSH < tz.OVER_PUSH < tz.OVER_PUSH_LONG <= tz.OVER_PUSH_ANY


UNREAD = "The camera pushes in on the lamp across the whole shot; the flame rises."


def test_any_plan_is_hard_over_the_top_wall():
    assert tz.planned_reach(UNREAD) is None
    assert tz.judge(tz.OVER_PUSH_ANY - 0.05, UNREAD)["hard"] == []
    v = tz.judge(tz.OVER_PUSH_ANY + 0.05, UNREAD)
    assert v["ok"] is False and v["hard"]


def test_a_pull_back_is_judged_on_its_own_reach():
    assert tz.judge(1 / (tz.OVER_PUSH - 0.05), PULL)["hard"] == []
    assert tz.judge(1 / (tz.OVER_PUSH + 0.05), PULL)["ok"] is False


def test_the_wrong_direction_is_advisory():
    v = tz.judge(1.3, PULL)
    assert v["hard"] == [] and v["advisory"]


def test_the_wrong_direction_over_the_wall_is_still_hard():
    """T05's first render: planned as a pull-back today, it pushed 1.93x to
    the nostrils.  Over the wall the wrong way is not an advisory."""
    v = tz.judge(1.93, PULL)
    assert v["ok"] is False and v["hard"] and v["advisory"]


def test_the_verdict_carries_its_inputs():
    v = tz.judge(1.2, HAND)
    assert v["ok"] is True and v["ratio"] == 1.2 and v["planned"] == "hand"


def test_an_unmeasured_take_is_advisory_not_hard():
    v = tz.judge(1.0, HAND, measured=False)
    assert v["ok"] is True and v["hard"] == [] and v["advisory"]
