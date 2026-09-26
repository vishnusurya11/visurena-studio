"""studio.stillness -- whole-frame stillness from optical flow, split into
camera and subject motion.  Synthetic numpy frames only; the two read tests
build a 1-2 s clip with ffmpeg's own test source, no real take is read."""
from __future__ import annotations

import subprocess

import numpy as np
import pytest

from studio import stillness as st


def texture(h: int = 128, w: int = 128, seed: int = 0) -> np.ndarray:
    """Smooth grey noise Farneback can track."""
    import cv2

    rng = np.random.default_rng(seed)
    noise = rng.integers(0, 255, (h, w)).astype(np.float32)
    return cv2.GaussianBlur(noise, (0, 0), 2.0).clip(0, 255).astype(np.uint8)


def still_frames(n: int = 6) -> np.ndarray:
    return np.stack([texture()] * n)


def panned_frames(n: int = 6, px: int = 2) -> np.ndarray:
    base = texture(160, 160)
    return np.stack([base[16:144, 16 + k * px:144 + k * px] for k in range(n)])


def acting_frames(n: int = 6) -> np.ndarray:
    """A still background with one 40 px patch sliding 3 px a frame."""
    bg, patch = texture(seed=1), texture(40, 40, seed=2)
    out = []
    for k in range(n):
        f = bg.copy()
        f[44:84, 20 + 3 * k:60 + 3 * k] = patch
        out.append(f)
    return np.stack(out)


# ---- sizes -------------------------------------------------------------------

def test_a_square_take_reads_at_256_square():
    assert st.fit_size(768, 768) == (256, 256)


def test_a_wide_frame_keeps_its_aspect():
    assert st.fit_size(1920, 1080) == (256, 144)


def test_a_portrait_frame_keeps_its_aspect_with_even_sides():
    w, h = st.fit_size(768, 1344)
    assert h == 256 and w % 2 == 0 and abs(w / h - 768 / 1344) < 0.02


# ---- flow --------------------------------------------------------------------

def test_identical_frames_have_no_flow():
    assert st.flow_mags(still_frames()).max() < 0.05


def test_a_two_pixel_pan_reads_two_pixels_a_step():
    mags = st.flow_mags(panned_frames(px=2))
    assert len(mags) == 5 and np.allclose(mags, 2.0, atol=0.4)


def test_one_frame_has_no_steps():
    assert len(st.flow_mags(still_frames(1))) == 0


def test_a_pan_is_camera_motion_not_subject_motion():
    parts = st.global_and_residual(panned_frames(px=2))
    assert parts["camera"].mean() > 1.5 and parts["residual"].mean() < 0.4


def test_an_actor_on_a_locked_camera_is_subject_motion():
    parts = st.global_and_residual(acting_frames())
    assert parts["residual"].mean() > parts["camera"].mean()


def test_the_camera_fit_recovers_a_zoom():
    ys, xs = np.mgrid[0:64, 0:64].astype(np.float32)
    flow = np.stack([(xs - 32) * 0.05, (ys - 32) * 0.05], axis=-1)
    cam, res = st.split_step(flow)
    assert cam > 0.5 and res < 0.05


# ---- step kinds and shares ---------------------------------------------------

def test_a_step_under_static_is_static_whatever_its_split():
    kinds = st.step_kinds(np.array([0.05]), np.array([0.04]), np.array([0.01]), static=0.15)
    assert list(kinds) == ["static"]


def test_a_moving_step_goes_to_the_larger_of_camera_and_subject():
    kinds = st.step_kinds(np.array([1.0, 1.0]), np.array([0.9, 0.2]), np.array([0.1, 0.8]), static=0.15)
    assert list(kinds) == ["camera", "subject"]


def test_the_longest_static_run_is_in_seconds():
    mask = np.array([1, 1, 0, 1, 1, 1, 1, 0], bool)
    assert st.longest_run_s(mask, fps=4) == 1.0


def test_no_steps_have_no_run():
    assert st.longest_run_s(np.zeros(0, bool), fps=24) == 0.0


def test_the_summary_shares_add_to_one():
    parts = {"total": np.array([0.0, 1.0, 1.0, 0.0]), "camera": np.array([0.0, 0.9, 0.1, 0.0]),
             "residual": np.array([0.0, 0.1, 0.9, 0.0])}
    s = st.summarize(parts, fps=24)
    assert (s["static_share"], s["camera_share"], s["subject_share"]) == (0.5, 0.25, 0.25)
    assert s["steps"] == 4 and s["mean_flow"] == 0.5


def test_an_empty_take_summarises_to_zero():
    empty = {"total": np.zeros(0), "camera": np.zeros(0), "residual": np.zeros(0)}
    assert st.summarize(empty, fps=24)["static_share"] == 0.0


# ---- the verdict -------------------------------------------------------------

def test_a_long_static_take_is_still():
    assert st.is_still({"static_share": st.WALL}, st.MIN_SECONDS)


def test_a_short_static_take_is_not_still():
    assert not st.is_still({"static_share": 1.0}, st.MIN_SECONDS - 0.5)


def test_a_moving_take_is_not_still():
    assert not st.is_still({"static_share": st.WALL - 0.01}, 10.0)


def test_a_planned_still_is_exempt():
    assert not st.is_still({"static_share": 1.0}, 10.0, exempt=True)


def test_the_advisory_sits_under_the_wall():
    assert st.ADVISORY < st.WALL
    assert st.is_advisory({"static_share": st.ADVISORY}, 10.0)
    assert not st.is_advisory({"static_share": st.ADVISORY}, 10.0, exempt=True)


def test_a_short_nearly_frozen_take_is_advisory():
    """ep12 T07: 4.2 s at 0.71 static, the owner's 'nearly' -- under MIN_SECONDS, still named."""
    assert st.is_advisory({"static_share": 0.71}, 4.21) and not st.is_still({"static_share": 0.71}, 4.21)


def test_the_fitted_constants_separate_the_labelled_takes():
    """Known-good max 0.60 (ep09 T13), owner-dead min 0.69 (ep12 T18)."""
    assert 0.60 < st.WALL <= 0.69 and st.STATIC == 0.15 and st.MIN_SECONDS == 5.0


def test_a_still_take_gives_a_frozen_fault_the_ladder_knows():
    m = {"static_share": 0.9, "longest_static_run_s": 6.0, "seconds": 8.0, "still": True, "exempt": False}
    f = st.fault(6, m)
    assert f["kind"] in {"frozen-at-start", "frozen-share", "frozen-whole"} and f["where"] == "T06"
    assert f["severity"] == "normal" and f["evidence"]["static_share"] == 0.9


def test_a_moving_take_gives_no_fault():
    assert st.fault(4, {"static_share": 0.1, "still": False}) is None


def test_the_gate_row_is_hard_and_fails_a_still_take():
    row = st.gate_args({"static_share": 0.9, "longest_static_run_s": 6.0, "seconds": 8.0, "still": True,
                        "advisory": True, "exempt": False})
    assert row["name"] == st.KIND and row["hard"] and not row["ok"] and row["penalty"] > 0


def test_the_gate_row_passes_a_moving_take():
    row = st.gate_args({"static_share": 0.1, "longest_static_run_s": 0.2, "seconds": 8.0, "still": False,
                        "advisory": False, "exempt": False})
    assert row["ok"] and row["penalty"] == 0.0


def test_the_gate_row_names_an_exempt_take():
    row = st.gate_args({"static_share": 1.0, "longest_static_run_s": 8.0, "seconds": 8.0, "still": False,
                        "advisory": False, "exempt": True})
    assert row["ok"] and "planned still" in row["note"]


# ---- reading a clip (ffmpeg test source, generated in tmp) --------------------

def clip(tmp_path, source: str, size: str, seconds: float) -> str:
    out = tmp_path / "c.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"{source}=size={size}:rate=24:d={seconds}",
                    "-pix_fmt", "yuv420p", str(out)], check=True)
    return str(out)


def test_read_frames_keeps_a_wide_clip_wide(tmp_path):
    frames = st.read_frames(clip(tmp_path, "testsrc", "320x180", 1), seconds=0.5)
    assert frames.dtype == np.uint8 and frames.shape[1:] == (144, 256) and len(frames) == 12


def test_a_flat_clip_measures_still(tmp_path):
    m = st.measure(clip(tmp_path, "color", "128x128", 6), seconds=6)
    assert m["static_share"] == 1.0 and m["still"] and m["seconds"] == 6.0


def test_the_same_flat_clip_is_not_still_when_planned(tmp_path):
    m = st.measure(clip(tmp_path, "color", "128x128", 6), seconds=6, exempt=True)
    assert not m["still"] and m["exempt"]


@pytest.mark.parametrize("seconds", [None, 0.5])
def test_read_frames_honours_the_seconds(tmp_path, seconds):
    frames = st.read_frames(clip(tmp_path, "testsrc", "128x128", 1), seconds=seconds)
    assert len(frames) == (24 if seconds is None else 12)
