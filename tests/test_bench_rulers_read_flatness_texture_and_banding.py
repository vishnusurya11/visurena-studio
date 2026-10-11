"""Phase-0 bench rulers (2026-10-10): each reads one thing the owner complained of --
flat fills, missing painted texture, banded dark gradients -- and a ruler votes only
after it separates the owner's good takes from his bad ones (AUC on content-matched sets)."""
import numpy as np

from scripts.bench import rulers


def flat() -> np.ndarray:
    return np.full((256, 256), 120.0)


def textured(seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return 120.0 + 30.0 * rng.standard_normal((256, 256))


def test_a_flat_frame_is_all_flat_blocks_and_no_texture():
    assert rulers.flat_share(flat()) == 1.0
    assert rulers.texture(flat()) < 0.01


def test_a_textured_frame_has_no_flat_blocks_and_high_texture():
    assert rulers.flat_share(textured()) == 0.0
    assert rulers.texture(textured()) > 5.0


def test_a_posterised_dark_gradient_combs_more_than_a_smooth_one():
    ramp = np.tile(np.linspace(5, 55, 256), (256, 1))
    banded = np.floor(ramp / 6) * 6
    assert rulers.banding(banded) > rulers.banding(ramp)


def test_masked_pixels_are_left_out_of_the_texture():
    img = flat()
    img[:128] = textured()[:128]
    mask = np.zeros(img.shape, bool)
    mask[:128] = True
    assert rulers.texture(img, exclude=mask) < 0.01


def test_auc_is_one_when_every_good_take_outranks_every_bad_one():
    assert rulers.auc([3, 4, 5], [0, 1, 2]) == 1.0
    assert rulers.auc([0, 1], [2, 3]) == 0.0
    assert rulers.auc([1, 2], [1, 2]) == 0.5
