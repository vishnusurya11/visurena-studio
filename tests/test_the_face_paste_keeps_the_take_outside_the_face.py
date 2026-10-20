"""The face paste replaces the face and nothing else (owner 2026-10-19: "the face fix and eye fix is
warping the video around" the head in ep01 master_iter2).

The audit (docs/audit/2026-10-19_face_warp/audit_our_paste.md) measured why: 9 of 11 tracks were pasted
through a full square feather, so the H3 redraw's hat, hair, collar and background replaced the take's;
its lines sat 1-4 px off and wandered (ring MAD 6-13 against a 0.4 control).  The rule now: outside the
face core (brow to chin, cheek to cheek: a superellipse 0.35 face heights across each way, 0.34 up and
down, square-shouldered above the face so the eyes are drawn whole; its 0.08 face-height feather inside
the outline) every pixel is the take's, for a soft small face and a big one alike; in the feather the
take's low frequencies replace the redraw's (no tone step), its lines stay the redraw's.  Round 1 of the
fix (722050e) used an ellipse 1.1 x 1.3 face heights across: the skeptic drew it over the frames and it
took in the brim, the hair, the ears and the jaw.  A Lab tone match was replayed and refused (it flickered).
The gate reads the paste the Paster makes (one function, face_paste.paste_patch): nothing outside the
mask moves, the feather band and the ring just outside it do not warp, and a redraw that turned the
face (ep01 T08: H3 turned the child's head; MTCNN's eye line) is refused.  The redraw is put back on the
take's head frame by frame (H3's redraws jitter 2-3 px at 384), so the face does not swim in a still
head.  A decision made before these walls is regated on CPU before the cut pastes it.  Pure numpy and
OpenCV on synthetic frames, detectors faked; the ep01 replay lives in docs/audit."""
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


def at(m, dx, dy):
    """The mask at (dx, dy) face heights from the face's centre."""
    return float(m[int(fp.FACE_Y * SIDE + dy * FACE), int(SIDE / 2 + dx * FACE)])


# ---- fix 1: the face core -------------------------------------------------------------------------

def test_the_core_is_whole_at_the_face_and_nothing_at_its_outline():
    m = fp.core_mask(SIDE, FACE)[..., 0]
    x, up, down = fp.CORE_HALF
    assert at(m, 0, 0) == pytest.approx(1.0)
    assert at(m, x + 0.02, 0) == 0.0 and at(m, -x - 0.02, 0) == 0.0
    assert at(m, 0, -up - 0.02) == 0.0 and at(m, 0, down + 0.02) == 0.0


def test_the_brim_the_hair_the_ears_and_the_jaw_stay_the_takes():
    """The skeptic's overlay of round 1 (r = 1 at 0.55 x 0.65 face heights) crossed the hat band, the
    brim's lower edge, the hair at both sides, the ears, the jaw and the collar's top."""
    m = fp.core_mask(SIDE, FACE)[..., 0]
    assert at(m, 0, -0.36) == 0.0                                   # the brim's lower edge, the hair top
    assert at(m, 0.37, -0.2) == 0.0 and at(m, -0.37, -0.2) == 0.0   # the hair and the ears beside the eyes
    assert at(m, 0.37, 0.05) == 0.0                                 # beside the cheek
    assert at(m, 0.27, 0.27) == 0.0 and at(m, -0.27, 0.27) == 0.0   # the jaw's corners
    assert at(m, 0, 0.36) == 0.0                                    # below the chin: the collar


def test_the_eyes_are_drawn_whole():
    """face_yolov8m puts the eyes in rows 0.27-0.35 of the face box (studio/face_eye), -0.23 to -0.15
    face heights from its centre; out to the outer corners they are the redraw's, not a blend."""
    m = fp.core_mask(SIDE, FACE)[..., 0]
    assert min(at(m, dx, dy) for dx in (-0.22, -0.1, 0.1, 0.22) for dy in (-0.23, -0.15)) > 0.95


def test_the_feather_lies_inside_the_outline_and_has_no_hard_step():
    m = fp.core_mask(SIDE, FACE)[..., 0]
    assert np.abs(np.diff(m, axis=0)).max() < 0.4 and np.abs(np.diff(m, axis=1)).max() < 0.4
    assert 0.0 < m.mean() < 0.12


def test_a_soft_small_face_gets_the_same_rule_scaled():
    big = fp.paste_mask(192, 72.0)[..., 0]
    small = fp.paste_mask(96, 36.0)[..., 0]
    assert np.abs(big[::2, ::2] - small).max() < 0.35
    assert abs(float(big.mean()) - float(small.mean())) < 0.01


def test_the_core_follows_the_tracked_face_not_the_window_centre():
    m = fp.core_mask(SIDE, FACE, centre=(50.0, 70.0))[..., 0]
    assert m[70, 50] == pytest.approx(1.0) and m[int(fp.FACE_Y * SIDE), SIDE // 2 + 20] == 0.0


def test_an_old_track_without_a_face_size_reads_the_margins_face():
    assert np.array_equal(fp.paste_mask(SIDE, None), fp.core_mask(SIDE, SIDE / ft.MARGIN))


def test_outside_the_mask_the_frame_is_the_take_byte_for_byte():
    frame = noise(400, 1)
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
    x = SIDE // 2 + int(0.3 * FACE)                            # in the feather band
    assert 0.0 < fp.core_mask(SIDE, FACE)[cy, x, 0] < 1.0
    assert locked[cy, x].mean() < locked[cy - 6, x].mean() - 60


def test_a_patch_equal_to_its_take_is_left_alone():
    take = noise()
    locked = fp.band_lock(take, take, fp.paste_mask(SIDE, FACE), FACE)
    assert np.abs(locked.astype(int) - take.astype(int)).max() <= 1


# ---- the redraw's head put back on the take's, frame by frame -----------------------------------------

def test_the_redraws_head_offset_is_read_on_the_ring_round_the_face():
    """H3's redraw jitters 2-3 px at 384 frame to frame (ep01 T18); the paste reads where its hat and hair
    sit against the take's on the ring just outside the face core, where both drew the same things."""
    take = lines(1)
    dx, dy = fp.head_shift(np.roll(take, 2, axis=1), take, FACE, None)
    assert (dx, dy) == pytest.approx((2.0, 0.0), abs=0.4)


def test_a_jittered_redraw_is_pasted_back_on_the_takes_face():
    take = lines(2)
    out = take.copy()
    fp.paste_patch(out, np.roll(take, 2, axis=1), 0, 0, FACE, None)
    core = fp.core_mask(SIDE, FACE)[..., 0] == 1.0
    plain = np.abs(np.roll(take, 2, axis=1).astype(int) - take.astype(int))[core].mean()
    assert np.abs(out.astype(int) - take.astype(int))[core].mean() < 0.3 * plain


def test_the_head_shift_is_held_to_a_few_hundredths_of_a_face():
    """A turned head (ep01 T08) is not a jitter: the shift never exceeds SHIFT_MAX face heights."""
    take = lines(3)
    dx, dy = fp.head_shift(np.roll(take, 12, axis=1), take, FACE, None)
    assert np.hypot(dx, dy) <= fp.SHIFT_MAX * FACE + 1e-6


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


def test_a_track_written_before_its_face_size_reads_it_off_its_refine_row(tmp_path):
    """ep01's track files hold no face_px; refine.json's row does.  Read as the margin's 1 / 2.4, T06's
    13.5 px Hyde (window 96) was pasted through a core three times his face, over hat and collar."""
    (tmp_path / "refine").mkdir()
    doc = {"windows": [[0, 0, 96]] * 2, "life": [0, 1], "start": 0}
    (tmp_path / "refine" / "T06_p1.json").write_text(json.dumps(doc))
    entry = {"people": [{"kept": True, "track": "refine/T06_p1.json", "crop": "refine/T06_p1.mp4", "face_px": 13.5}]}
    track, = fp.kept_tracks(entry, tmp_path)
    assert track.face == pytest.approx(13.5 / 96)


def test_the_av3_worker_gets_the_face_sizes_the_repo_built():
    track = fp.Track([(16, 8, 24)] * 2, (0, 1), 0, "c.mp4", face=0.4, faces=((0.5, 0.55, 0.4), (0.5, 0.55, 0.4)))
    spans = [fp.Span(0, 0, 2, 0, 1.0, None, (track,))]
    assert av.spans_back(json.loads(json.dumps(av.spans_json(spans)))) == spans


# ---- the paster -------------------------------------------------------------------------------------

class Fixed:
    def __init__(self, frame):
        self.f = frame

    def frame(self, k):
        return self.f


def test_the_paster_changes_only_the_face_core():
    track = fp.Track([(20, 20, 40)] * 4, (0, 3), 0, "c.mp4", face=0.4)
    span = fp.Span(0, 0, 4, 0, 1.0, None, (track,))
    paster = fp.Paster(lambda f: f, [span], 100, 100, 1, open_crop=lambda p: Fixed(np.full((64, 64, 3), 250, np.uint8)))
    take = noise(100, 5)
    for _ in range(3):
        out = paster(take.copy())
    moved = np.abs(out.astype(int) - take.astype(int)).max(axis=2) > 0
    ys, xs = np.nonzero(moved)
    x, up, down = fp.CORE_HALF
    assert moved.any() and xs.min() >= 20 + 20 - x * 16 - 1 and xs.max() <= 20 + 20 + x * 16 + 1
    assert ys.min() >= 20 + 22 - up * 16 - 1 and ys.max() <= 20 + 22 + down * 16 + 1


def test_the_gate_reads_the_paste_the_paster_makes():
    """Round 1's gate rebuilt its own paste and read a ring where that mask was 0: zero by construction."""
    take, redraw = noise(seed=3), noise(seed=4, lo=0, hi=255)
    track = fp.Track([(0, 0, SIDE)] * 10, (0, 9), 0, "c.mp4", face=FACE / SIDE)
    paster = fp.Paster(lambda f: f, [fp.Span(0, 0, 10, 0, 1.0, None, (track,))], SIDE, SIDE, 1,
                       open_crop=lambda p: Fixed(redraw))
    for _ in range(4):                                        # frames 0-2 fade in; frame 3 is whole
        pasted = paster(take.copy())
    assert np.array_equal(fg.pasted_of([take], [redraw], FACE / SIDE)[0][0], pasted)


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
    assert 0.3 * f_src < f_ref < 0.95 * f_src            # a still face core, the take's own pixels round it


def lines(k):
    """Grey detail Farneback can follow (blurred noise, stretched): a stand-in for ink lines."""
    import cv2
    g = cv2.GaussianBlur(noise(seed=k, lo=0, hi=255)[..., 0].astype(np.float32), (0, 0), 2)
    g = (g - g.min()) / (g.max() - g.min()) * 255
    return np.repeat(g.astype(np.uint8)[..., None], 3, axis=2)


def test_a_redraw_on_the_takes_lines_moves_nothing_outside_and_does_not_warp_the_band():
    rng = np.random.default_rng(7)
    src = [lines(k) for k in range(9)]
    ref = [np.clip(s.astype(int) + rng.integers(-6, 7, s.shape), 0, 255).astype(np.uint8) for s in src]
    outside, band = fg.paste_check(src, ref, FACE / SIDE)
    assert outside <= fr.OUTSIDE_MAX and band <= fr.BAND_WARP_MAX
    assert fg.core_flow(src, ref, FACE / SIDE) < 0.5


def test_redrawn_lines_off_the_takes_are_a_band_warp_the_gate_refuses():
    """The band is read where the production mask falls (inside the outline) and just outside it, so a
    redrawn face whose lines sit 3 px off the take's, on a head drawn where the take's is, reads there:
    it is not zero by construction."""
    src = [lines(k) for k in range(9)]
    face = fp.core_radius(SIDE, FACE)[..., None] < 1.1
    moved = [np.where(face, np.roll(s, 3, axis=1), s) for s in src]
    _, band = fg.paste_check(src, moved, FACE / SIDE)
    assert band > fr.BAND_WARP_MAX


def test_the_band_is_where_the_mask_falls_and_just_outside_it():
    band = fg.band_mask(SIDE, FACE / SIDE)
    m = fp.paste_mask(SIDE, FACE)[..., 0]
    assert band[(m > 0.05) & (m < 0.95)].all() and not band[m == 1.0].any()
    assert band.any() and not band[fp.core_radius(SIDE, FACE) > fg.BAND_OUT].any()


def test_the_core_flow_is_logged_on_the_paste_after_the_head_shift():
    src = [lines(k) for k in range(9)]
    assert fg.core_flow(src, src, FACE / SIDE) == pytest.approx(0.0, abs=0.05)
    assert fg.core_flow(src, [np.roll(s, 2, axis=1) for s in src], FACE / SIDE) < 0.5   # a jitter, put back


def eyes_at(angle):
    """A fake MTCNN face, inside a 768 window, whose eye line leans `angle` degrees."""
    a = np.radians(angle)
    marks = [[384 - 60 * np.cos(a), 384 - 60 * np.sin(a)], [384 + 60 * np.cos(a), 384 + 60 * np.sin(a)],
             [384, 420], [350, 460], [418, 460]]
    return [{"box": [284, 284, 484, 504], "landmarks": marks, "score": 0.99}]


def marked(frame, level):
    out = frame.copy()
    out[:8, :8] = level
    return out


def leaning(rgb):
    """The fake detector: a frame marked bright is the redraw, its face turned 8 degrees."""
    return eyes_at(8.0 if rgb[0, 0, 0] > 127 else 0.0)


def test_a_redraw_that_turned_the_face_is_refused():
    """ep01 T08: H3 turned the child's head inside her hood (MTCNN eye line 9.3 deg off the take's on the
    replay, 12 pairs; the faces kept by eye 0.9-2.84, the re-posed ones 5.55-9.34)."""
    take = [np.zeros((768, 768, 3), np.uint8)] * 6
    redraw = [np.full((768, 768, 3), 255, np.uint8)] * 6
    assert fg.face_turn(take, redraw, leaning) == pytest.approx(8.0, abs=0.01)
    assert fg.face_turn(take, take, leaning) == 0.0
    assert 2.84 < fr.TURN_MAX < 5.55


def test_a_face_no_detector_reads_has_no_turn():
    take = [np.zeros((768, 768, 3), np.uint8)] * 6
    assert fg.face_turn(take, take, lambda rgb: []) is None
    assert fg.face_turn(take[:2], take[:2], leaning) is None             # fewer pairs than TURN_PAIRS


def test_the_walls_refuse_a_paste_that_moves_the_take_warps_the_band_or_moves_the_face():
    from dataclasses import replace
    base = fr.Measures(id_src=None, id_ref=None, seam=5.0, flick_src=2.0, flick_ref=2.0, faces_src=1, faces_ref=1,
                       outside=0.0)
    assert fr.decide(base)[0]
    assert not fr.decide(replace(base, outside=None))[0]                  # unread is a refusal (2026-10-20)
    assert not fr.decide(replace(base, outside=fr.OUTSIDE_MAX + 1))[0]
    kept, why = fr.decide(replace(base, band_warp=fr.BAND_WARP_MAX + 0.5))
    assert not kept and "band" in why
    kept, why = fr.decide(replace(base, turn=fr.TURN_MAX + 1))
    assert not kept and "turned" in why
    assert fr.decide(replace(base, core_flow=9.0))[0]                     # logged, never a wall


# ---- a decision made under the old paste is re-gated before the cut pastes it ---------------------------

def stale_entry(room):
    (room / "refine").mkdir(parents=True, exist_ok=True)
    doc = {"windows": [[0, 0, SIDE]] * 9, "life": [0, 8], "start": 0, "face_px": FACE, "side": SIDE}
    (room / "refine" / "T08_p0.json").write_text(json.dumps(doc))
    measures = {"id_src": 0.2, "id_ref": 0.4, "seam": 12.0, "flick_src": 17.0, "flick_ref": 15.0,
                "faces_src": 1, "faces_ref": 1, "change": 17.0}
    row = {"who": "child", "crop": "refine/T08_p0.mp4", "track": "refine/T08_p0.json", "kept": True,
           "why": "kept", "measures": measures, "face_px": FACE}
    return {"status": "refined", "take_sha8": "abc", "people": [row]}


def test_a_row_decided_before_the_band_and_turn_walls_is_regated(tmp_path):
    from scripts.episode import face_refine as cli
    reads = {"T08.mp4": [marked(lines(k), 0) for k in range(9)], "T08_p0.mp4": [marked(lines(k), 255) for k in range(9)]}
    entry = cli.regate_entry(tmp_path, 8, stale_entry(tmp_path), read=lambda p: reads[p.name], detect=leaning)
    row, = entry["people"]
    assert not row["kept"] and "turned" in row["why"] and "band_warp" in row["measures"]
    assert row["measures"]["turn"] == pytest.approx(8.0, abs=0.01)
    assert entry["status"] == "unrefined" and row["regated"]


def test_a_regated_row_that_holds_stays_kept(tmp_path):
    from scripts.episode import face_refine as cli
    reads = {"T08.mp4": [marked(lines(k), 0) for k in range(9)], "T08_p0.mp4": [marked(lines(k), 0) for k in range(9)]}
    entry = cli.regate_entry(tmp_path, 8, stale_entry(tmp_path), read=lambda p: reads[p.name], detect=leaning)
    assert entry["people"][0]["kept"] and entry["status"] == "refined"


def test_a_row_the_new_gate_measured_or_with_no_measures_is_left_alone(tmp_path):
    from scripts.episode import face_refine as cli
    assert cli.regate_due(stale_entry(tmp_path))
    measured = stale_entry(tmp_path)
    measured["people"][0]["measures"].update(band_warp=0.4, outside=0.0)
    bare = {"status": "refined", "people": [{"kept": True, "crop": "c.mp4", "track": "t.json"}]}
    assert not cli.regate_due(measured) and not cli.regate_due(bare)


def test_the_cut_regates_the_room_before_it_pastes():
    import inspect
    from scripts.episode import assemble
    source = inspect.getsource(assemble.face_paste_wrap)
    assert source.index("regate") < source.index("spans_from")
