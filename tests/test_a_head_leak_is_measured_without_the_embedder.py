"""A head leak measured by the one picture switch in a take's first second.

The DINOv3 `image_embed` workflow is a placeholder, so the leak row read 'not
measured' and the take ladder's head-cut rung could never fire (ep12 T19 ended
keep_best and failed QC on a leak a head of 0.5 s cures). MEASURED on 290
takes (ep01-ep12): the brightness-normalised step between frames, largest in
the first 24, read 0.85-1.17 on the four known heads (ep06 T01 -- published,
never caught -- ep10 T07, T12, ep12 T19) and at most 0.62 on every other.
"""
import numpy as np

from studio import take_leak


def frames_of(picture_a, picture_b, switch_at, n=40):
    return [picture_a if i < switch_at else picture_b for i in range(n)]


def pattern(seed):
    rng = np.random.default_rng(seed)
    return (rng.random((64, 64, 3)) * 255).astype(np.uint8)


def test_a_switch_at_frame_twelve_is_a_twelve_frame_head():
    got = take_leak.step_leak(frames_of(pattern(1), pattern(2), 12))
    assert got["frames"] == 12 and got["covers"] and got["seconds"] == 0.5


def test_a_lightning_flash_is_not_a_switch():
    base = pattern(3)
    flash = np.clip(base.astype(int) + 90, 0, 255).astype(np.uint8)
    frames = [flash if i == 6 else base for i in range(40)]
    assert take_leak.step_leak(frames)["frames"] == 0


def test_a_steady_take_opens_on_its_panel():
    assert take_leak.step_leak([pattern(4)] * 40)["frames"] == 0


def test_a_switch_after_the_first_second_is_not_a_head():
    assert take_leak.step_leak(frames_of(pattern(5), pattern(6), 30))["frames"] == 0
