"""The face paste replaces the face and nothing else (owner 2026-10-19: "the face fix and eye fix is
warping the video around" the head in ep01 master_iter2).

The audit (docs/audit/2026-10-19_face_warp/audit_our_paste.md) measured why: 9 of 11 tracks were pasted
through a full square feather, so the H3 redraw's hat, hair, collar and background replaced the take's;
its lines sat 1-4 px off and wandered (ring MAD 6-13 against a 0.4 control).  The rule now: outside a
face-core ellipse (0.55 x 0.65 face heights round the tracked face, feathered inside its outline) every
pixel is the take's, for a soft small face and a big one alike; in the feather band the take's low
frequencies replace the redraw's (no tone step), its lines stay the redraw's.  A global similarity
registration and a Lab tone match were replayed and refused (the replay table in
docs/calibration/face_refine.md): the resample blurred the drawn eyes, the per-frame tone shift
flickered.  The gate checks the paste: nothing outside the mask moves, the ring round the face does not
warp.  Pure numpy and OpenCV on synthetic frames; the ep01 replay lives in docs/audit."""
from __future__ import annotations

import json

import numpy as np
import pytest

from studio import face_gate as fg
from studio import face_paste as fp
from studio import face_refine as fr
from studio import face_track as ft
from studio import master_av3 as av

SIDE = 160
FACE = 64.0


def noise(side=SIDE, seed=0, lo=60, hi=160):
    return np.random.default_rng(seed).integers(lo, hi, (side, side, 3)).astype(np.uint8)


# ---- fix 1: the face core -------------------------------------------------------------------------

def test_the_core_is_whole_at_the_face_and_nothing_at_its_outline():
    m = fp.core_mask(SIDE, FACE)[..., 0]
    cx, cy = SIDE / 2, fp.FACE_Y * SIDE
    assert m[int(cy), int(cx)] == pytest.approx(1.0)
    assert m[int(cy), int(cx + fp.CORE_RADII[0] * FACE) + 1] == 0.0
    assert m[int(cy - fp.CORE_RADII[1] * FACE) - 1, int(cx)] == 0.0


def test_the_hat_crown_the_hair_top_and_the_collar_stay_the_takes():
    m = fp.core_mask(SIDE, FACE)[..., 0]
    cx, cy = int(SIDE / 2), int(fp.FACE_Y * SIDE)
    assert m[cy - int(0.7 * FACE), cx] == 0.0          # above the brow: hat brim, hair top
    assert m[cy + int(0.7 * FACE), cx] == 0.0          # below the chin: collar, tie
    assert m[cy, cx + int(0.6 * FACE)] == 0.0          # beside the cheek: ear, hair, background


def test_the_feather_lies_inside_the_outline_and_has_no_step():
    m = fp.core_mask(SIDE, FACE)[..., 0]
    assert np.abs(np.diff(m, axis=0)).max() < 0.12 and np.abs(np.diff(m, axis=1)).max() < 0.12
    assert 0.0 < m.mean() < 0.25


def test_a_soft_small_face_gets_the_same_rule_scaled():
    big = fp.paste_mask(192, 72.0)[..., 0]
    small = fp.paste_mask(96, 36.0)[..., 0]
    assert np.abs(big[::2, ::2] - small).max() < 0.1


def test_the_core_follows_the_tracked_face_not_the_window_centre():
    m = fp.core_mask(SIDE, FACE, centre=(50.0, 70.0))[..., 0]
    assert m[70, 50] == pytest.approx(1.0) and m[int(fp.FACE_Y * SIDE), SIDE // 2 + 20] == 0.0


def test_an_old_track_without_a_face_size_reads_the_margins_face():
    assert np.array_equal(fp.paste_mask(SIDE, None), fp.core_mask(SIDE, SIDE / ft.MARGIN))


def test_outside_the_mask_the_frame_is_the_take_byte_for_byte():
    frame, before = noise(400, 1), None
    before = frame.copy()
    mask = fp.paste_mask(SIDE, FACE)
    fp.blend(frame, noise(SIDE, 2, 0, 255), 100, 120, mask, 1.0)
    outside = np.ones(frame.shape[:2], bool)
    outside[120:120 + SIDE, 100:100 + SIDE] = mask[..., 0] == 0
    assert np.array_equal(frame[outside], before[outside])


# ---- fix 2: the edge lock ---------------------------------------------------------------------------

def test_a_tone_step_is_taken_from_the_take_where_the_mask_falls():
    take = np.full((SIDE, SIDE, 3), 100, np.uint8)
    patch = np.full((SIDE, SIDE, 3), 140, np.uint8)
    mask = fp.paste_mask(SIDE, FACE)
    locked = fp.band_lock(patch, take, mask, FACE)
    r = fp.core_radius(SIDE, FACE)
    assert abs(float(locked[r < 0.2].mean()) - 140) < 2      # the face core keeps the redraw
    assert abs(float(locked[(r > 0.9) & (r < 1.0)].mean()) - 100) < 12   # the outline meets the take


def test_the_lock_keeps_the_redraws_lines_in_the_band():
    take = np.full((SIDE, SIDE, 3), 120, np.uint8)
    patch = take.copy()
    cy = int(fp.FACE_Y * SIDE)
    patch[cy - 1:cy + 2, :] = 20                               # an ink line across the face
    locked = fp.band_lock(patch, take, fp.paste_mask(SIDE, FACE), FACE)
    x = SIDE // 2 + int(0.45 * FACE)                           # in the feather band
    assert locked[cy, x].mean() < locked[cy - 6, x].mean() - 60


def test_a_patch_equal_to_its_take_is_left_alone():
    take = noise()
    locked = fp.band_lock(take, take, fp.paste_mask(SIDE, FACE), FACE)
    assert np.abs(locked.astype(int) - take.astype(int)).max() <= 1


# ---- fix 3: the float box the crop was cut by ------------------------------------------------------

def test_the_float_box_carries_the_guards_scale_unrounded():
    xf, yf, sf = fp.box_at((112, 212, 96), (744, 744, 12, 12), 768, 768, 1)
    s = 768 / 744
    assert (xf, yf, sf) == pytest.approx((100 * s, 200 * s, 96 * s))
    assert fp.to_master((112, 212, 96), (744, 744, 12, 12), 768, 768, 1) == (round(xf), round(yf), round(sf))


def test_the_face_centre_lands_where_the_float_box_puts_it():
    cx, cy, face = fp.face_in_patch((0.5, 0.55, 0.4), (100.4, 50.6, 103.2), (100, 51, 103))
    assert (cx, cy, face) == pytest.approx((0.4 + 51.6, -0.4 + 0.55 * 103.2, 0.4 * 103.2))


def test_a_track_reads_its_face_per_frame_and_falls_back_to_the_median():
    t = fp.Track([(0, 0, 96)] * 3, (0, 2), 0, "c.mp4", face=0.4, faces=((0.5, 0.55, 0.4), (0.3, 0.6, 0.35), None))
    assert fp.face_at(t, 1) == (0.3, 0.6, 0.35)
    assert fp.face_at(t, 2) == (0.5, fp.FACE_Y, 0.4)
    assert fp.face_at(fp.Track([(0, 0, 96)], (0, 0), 0, "c.mp4"), 0) == pytest.approx((0.5, fp.FACE_Y, 1 / ft.MARGIN))


def test_every_kept_track_carries_its_face_size_and_its_faces(tmp_path):
    (tmp_path / "refine").mkdir()
    doc = {"windows": [[0, 0, 200]] * 2, "life": [0, 1], "start": 0, "face_px": 80.0, "side": 200, "soft": False,
           "faces": [[0.5, 0.55, 0.4], [0.52, 0.55, 0.41]]}
    (tmp_path / "refine" / "T05_p0.json").write_text(json.dumps(doc))
    entry = {"people": [{"kept": True, "track": "refine/T05_p0.json", "crop": "refine/T05_p0.mp4"}]}
    track, = fp.kept_tracks(entry, tmp_path)
    assert track.face == pytest.approx(0.4) and track.faces[1] == pytest.approx((0.52, 0.55, 0.41))


def test_the_av3_worker_gets_the_face_sizes_the_repo_built():
    track = fp.Track([(16, 8, 24)] * 2, (0, 1), 0, "c.mp4", face=0.4, faces=((0.5, 0.55, 0.4), (0.5, 0.55, 0.4)))
    spans = [fp.Span(0, 0, 2, 0, 1.0, None, (track,))]
    assert av.spans_back(json.loads(json.dumps(av.spans_json(spans)))) == spans


# ---- the paster -------------------------------------------------------------------------------------

class Bright:
    def frame(self, k):
        return np.full((64, 64, 3), 250, np.uint8)


def test_the_paster_changes_only_the_face_core():
    track = fp.Track([(20, 20, 40)] * 4, (0, 3), 0, "c.mp4", face=0.4)
    span = fp.Span(0, 0, 4, 0, 1.0, None, (track,))
    paster = fp.Paster(lambda f: f, [span], 100, 100, 1, open_crop=lambda p: Bright())
    take = noise(100, 5)
    for _ in range(3):
        out = paster(take.copy())
    moved = np.abs(out.astype(int) - take.astype(int)).max(axis=2) > 0
    ys, xs = np.nonzero(moved)
    assert moved.any() and xs.min() >= 20 + 20 - 0.55 * 16 - 1 and xs.max() <= 20 + 20 + 0.55 * 16 + 1
    assert ys.min() >= 20 + 22 - 0.65 * 16 - 1 and ys.max() <= 20 + 22 + 0.65 * 16 + 1


# ---- the run records the face per frame --------------------------------------------------------------

def test_a_run_records_where_the_face_sits_in_each_window():
    from scripts.episode import face_refine as cli
    track = [(t, (300.0, 300.0, 360.0, 370.0)) for t in range(0, 60, 3)]
    run = cli.run_of(track, 60, 768, 768, [])
    fx, fy, fh = run.faces[10]
    x, y, s = run.windows[10]
    assert (x + fx * s, y + fy * s, fh * s) == pytest.approx((330.0, 335.0, 70.0), abs=1.5)


# ---- fix 4: the gate -----------------------------------------------------------------------------------

def test_the_old_seam_reading_stays_on_its_own_ruler():
    """The seam still reads how far the redraw strays from the take at the window's edge band (round 1's
    wall of 18 and its calibration hold), though that band is no longer pasted."""
    src = [noise() for _ in range(9)]
    seam, _, _ = fg.seam_and_flicker(src, [np.clip(s.astype(int) + 40, 0, 255).astype(np.uint8) for s in src],
                                     face=FACE / SIDE)
    assert seam == pytest.approx(40.0, abs=2.0)


def test_the_flicker_is_read_on_the_face_core_paste():
    src = [noise(seed=k) for k in range(6)]
    still = [np.full((SIDE, SIDE, 3), 100, np.uint8)] * 6
    _, f_src, f_ref = fg.seam_and_flicker(src, still, face=FACE / SIDE)
    assert 0.3 * f_src < f_ref < 0.9 * f_src             # a still face core, the take's own pixels round it


def test_a_face_only_paste_moves_nothing_outside_and_does_not_warp_the_ring():
    rng = np.random.default_rng(7)
    src = [noise(seed=k) for k in range(9)]
    ref = [np.clip(s.astype(int) + rng.integers(-30, 31, s.shape), 0, 255).astype(np.uint8) for s in src]
    outside, ring = fg.paste_check(src, ref, FACE / SIDE)
    assert outside <= fr.OUTSIDE_MAX and ring <= fr.RING_WARP_MAX


def test_a_redrawn_ring_is_a_warp_the_gate_refuses():
    import cv2
    src = [cv2.GaussianBlur(noise(seed=k, lo=0, hi=255), (0, 0), 2) for k in range(9)]
    moved = [np.roll(s, 3, axis=1) for s in src]                 # every line 3 px off, as H3's redraw
    ring = fg.ring_warp(src, moved, FACE / SIDE)
    assert ring > fr.RING_WARP_MAX


def test_the_walls_refuse_a_paste_that_moves_the_take_or_warps_the_ring():
    base = fr.Measures(id_src=None, id_ref=None, seam=5.0, flick_src=2.0, flick_ref=2.0, faces_src=1, faces_ref=1)
    assert fr.decide(base)[0]
    from dataclasses import replace
    assert not fr.decide(replace(base, outside=fr.OUTSIDE_MAX + 1))[0]
    kept, why = fr.decide(replace(base, ring_warp=fr.RING_WARP_MAX + 0.5))
    assert not kept and "ring" in why
