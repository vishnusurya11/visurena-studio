"""The face refine's seam is read where the paste's mask falls, so a bad seam fails at every face size
(face-blur round 2, fix round, 2026-10-19).

The round-2 seam was the mean of mask x |refined - take| over EVERY pixel outside the head.  A small
face's soft mask is near 0 over most of its floored 96 px window, so the mean was diluted toward 0:
a crop 60 levels off its take read 2.5 at a 13 px face and 6.3 at 20 px, a +80 halo right outside
the head 2.6 and 6.5 -- all under the wall (the skeptic's probe).  The seam is now the level change
weighted by the mask's slope |grad m| outside the head: the change where the paste passes from the
crop to the take.  It scales with the face (the soft ring is in head radii) and reads a uniform change
D as D at any size.  Through the hard feather it is round 1's feather-band seam again (the bench's 15
rows: within -1.3 / +0.8 of the logged value), so the wall returns to round 1's 18.  Since the face-warp
fix (2026-10-19) the paste is the face core alone; these rulers stay the seam's (studio/face_gate.seam_mask).
Pure numpy: synthetic crops."""
from __future__ import annotations

import numpy as np
import pytest

from studio import face_gate as fg
from studio import face_paste as fp
from studio import face_refine as fr

SIDE = 96


def take_like(n=9, side=SIDE, seed=0):
    rng = np.random.default_rng(seed)
    base = rng.integers(60, 160, (side, side, 3)).astype(np.uint8)
    return [base.copy() for _ in range(n)]


def shifted(frames, d):
    return [np.clip(f.astype(int) + d, 0, 255).astype(np.uint8) for f in frames]


def halo(frames, face, d, out=1.3):
    """`d` levels added in a ring from the head's edge to `out` head radii."""
    r = fg.head_radius(SIDE, face)
    ring = ((r > 1.0) & (r <= out))[..., None]
    return [np.clip(f.astype(int) + d * ring, 0, 255).astype(np.uint8) for f in frames]


@pytest.mark.parametrize("face", [13.0, 20.0, 30.0, 36.0])
def test_a_crop_sixty_levels_off_fails_the_soft_paste_at_any_face_size(face):
    src = take_like()
    seam, _, _ = fg.seam_and_flicker(src, shifted(src, 60), face=face / SIDE, soft=True)
    assert seam == pytest.approx(60.0, abs=3.0) and seam > fr.SEAM_MAX


@pytest.mark.parametrize("face", [13.0, 20.0, 30.0])
def test_a_halo_right_outside_the_head_fails_the_soft_paste(face):
    src = take_like()
    seam, _, _ = fg.seam_and_flicker(src, halo(src, face, 80), face=face / SIDE, soft=True)
    assert seam > fr.SEAM_MAX


def test_the_hard_feather_reads_a_level_change_as_itself():
    src = take_like()
    seam, _, _ = fg.seam_and_flicker(src, shifted(src, 60), face=36 / SIDE, soft=False)
    assert seam == pytest.approx(60.0, abs=3.0)


def test_a_change_inside_the_head_is_no_seam():
    src = take_like()
    inside = fg.head_mask(SIDE, 20.0)[..., None]
    ref = [np.clip(f.astype(int) + 80 * inside, 0, 255).astype(np.uint8) for f in src]
    seam, _, _ = fg.seam_and_flicker(src, ref, face=20 / SIDE, soft=True)
    assert seam < 1.0


def test_through_the_feather_the_seam_is_the_old_feather_band_difference():
    """Round 1's wall (18) was set on the feather band's mean difference (face_paste.ring_diff)."""
    rng = np.random.default_rng(1)
    src = take_like()
    ref = [np.clip(f.astype(int) + rng.integers(-25, 26, f.shape), 0, 255).astype(np.uint8) for f in src]
    seam, _, _ = fg.seam_and_flicker(src, ref, face=40 / SIDE, soft=False)
    old = np.mean([fp.ring_diff(s, r, max(4, round(SIDE * fp.FEATHER_SHARE))) for s, r in zip(src, ref)])
    assert seam == pytest.approx(old, rel=0.1)


def test_the_seam_weights_are_the_masks_slope_outside_the_head():
    mask, head = fg.seam_mask(SIDE, 20.0), fg.head_mask(SIDE, 20.0)
    w = fg.edge_weight(mask, head)
    assert w.shape == (SIDE, SIDE) and w[head].sum() == 0 and w.sum() > 0


def test_a_flat_mask_has_no_edge_to_read():
    src = take_like(1)
    assert fg.edge_change(src[0], shifted(src, 60)[0], np.zeros((SIDE, SIDE))) == 0.0
