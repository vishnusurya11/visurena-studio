"""Assemble pastes each kept refined crop into the master AFTER the 4x upscale, at
master scale (studio/face_paste.py).  F2: pasted into the 768 take, the new detail
was averaged away again; pasted into the 3072 master it read as a face.  The
geometry follows the cut exactly -- the take's head trim, a G-DEAD slow-down, the
gutter guard's crop -- and a take with nothing kept is the unrefined path, byte for
byte.  CPU only: a nearest-neighbour stand-in for RTX VSR, synthetic frames."""
from __future__ import annotations

import json

import numpy as np
import pytest

from studio import face_paste as fp


def test_a_window_scales_by_the_upscale_factor_with_no_guard():
    assert fp.to_master((100, 200, 96), None, 768, 768, 4) == (400, 800, 384)


def test_the_gutter_guards_crop_moves_and_grows_the_window():
    # crop=744:744:12:12 is scaled back up to 768 (x 768/744), then the master's 4x
    X, Y, S = fp.to_master((112, 212, 96), (744, 744, 12, 12), 768, 768, 4)
    s = 768 / 744
    assert (X, Y, S) == (round(100 * s * 4), round(200 * s * 4), round(96 * s * 4))


def test_a_guard_is_read_off_its_ffmpeg_filter():
    assert fp.parse_guard("crop=744:740:12:16") == (744, 740, 12, 16)
    assert fp.parse_guard("") is None and fp.parse_guard(None) is None


def test_a_take_frame_follows_the_head_trim_and_the_slow_down():
    assert fp.take_frame(0, head=6, slow=1.0) == 6
    assert fp.take_frame(10, head=0, slow=1.5) == 6


def test_a_track_fades_in_and_out_at_its_life():
    assert fp.fade(10, (10, 100)) == pytest.approx(1 / fp.FADE)
    assert fp.fade(50, (10, 100)) == 1.0
    assert fp.fade(101, (10, 100)) == 0.0


def test_the_feather_is_solid_inside_and_zero_at_the_edge():
    m = fp.feather(64, 6)
    assert m.shape == (64, 64, 1) and m[32, 32, 0] > 0.99 and m[0, 0, 0] < 0.05


def test_a_blend_lands_in_its_window_and_nowhere_else():
    frame = np.zeros((40, 40, 3), np.uint8)
    fp.blend(frame, np.full((10, 10, 3), 200, np.uint8), 5, 5, np.ones((10, 10, 1), np.float32), 1.0)
    assert frame[10, 10, 0] == 200 and frame[2, 2, 0] == 0 and frame[20, 20, 0] == 0


def test_a_window_hanging_off_the_frame_is_clipped_not_refused():
    frame = np.zeros((40, 40, 3), np.uint8)
    fp.blend(frame, np.full((10, 10, 3), 90, np.uint8), 35, -5, np.ones((10, 10, 1), np.float32), 1.0)
    assert frame[0, 39, 0] == 90 and frame[6, 39, 0] == 0


def test_the_seam_is_the_level_difference_in_the_band():
    src = np.zeros((32, 32, 3), np.uint8)
    ref = src.copy()
    ref[8:24, 8:24] = 200                                  # a new face inside, the band untouched
    assert fp.ring_diff(src, ref, 4) == 0.0
    ref[:2] = 60
    assert fp.ring_diff(src, ref, 4) > 0.0


def test_flicker_is_the_face_regions_change_frame_to_frame():
    still = [np.zeros((32, 32, 3), np.uint8)] * 3
    blink = [np.zeros((32, 32, 3), np.uint8), np.full((32, 32, 3), 30, np.uint8)] * 2
    assert fp.region_flicker(still) == 0.0 and fp.region_flicker(blink) == pytest.approx(30.0)


# ---- the paster over the upscale --------------------------------------------------------

def nearest(f):
    return f.repeat(4, axis=0).repeat(4, axis=1)


class Reader:
    """The refined crop: every frame one level, its index."""

    def frame(self, k):
        return np.full((64, 64, 3), 100 + k, np.uint8)


def span(start=2, frames=4, head=0, slow=1.0, guard=None, life=(0, 10)):
    track = fp.Track(windows=[(4, 4, 8)] * 12, life=life, start=0, crop="refine/T00_p0.mp4")
    return fp.Span(index=0, start=start, frames=frames, head=head, slow=slow, guard=guard, tracks=(track,))


def test_the_paster_upscales_then_pastes_only_inside_its_segment():
    paster = fp.Paster(nearest, [span()], 16, 16, 4, open_crop=lambda p: Reader())
    out = [paster(np.zeros((16, 16, 3), np.uint8)) for _ in range(8)]
    assert out[0].shape == (64, 64, 3)
    centre = [int(o[32, 32, 0]) for o in out]
    assert centre[:2] == [0, 0] and centre[6:] == [0, 0]
    assert all(v > 0 for v in centre[2:6])


def test_the_pasted_crop_frame_is_the_take_frame_the_cut_shows():
    paster = fp.Paster(nearest, [span(head=3)], 16, 16, 4, open_crop=lambda p: Reader())
    out = [paster(np.zeros((16, 16, 3), np.uint8)) for _ in range(3)]
    assert int(out[2][32, 32, 0]) == pytest.approx(103, abs=2)   # cut frame 0 is take frame 3


def test_nothing_kept_is_the_upscale_untouched():
    paster = fp.Paster(nearest, [], 16, 16, 4, open_crop=lambda p: Reader())
    frame = np.random.default_rng(1).integers(0, 255, (16, 16, 3), dtype=np.uint8)
    assert np.array_equal(paster(frame), nearest(frame))


# ---- the spans from what the cut recorded -------------------------------------------------

def write(room, sha="abcd1234", kept=True):
    (room / "refine").mkdir(parents=True)
    (room / "refine" / "T03_p0.json").write_text(json.dumps(
        {"windows": [[10, 10, 96]] * 50, "life": [4, 40], "start": 0}))
    doc = {"T03": {"take_sha8": sha, "people": [
        {"who": "a", "crop": "refine/T03_p0.mp4", "track": "refine/T03_p0.json", "kept": kept}]}}
    (room / "refine.json").write_text(json.dumps(doc))


def layout():
    return [{"index": 0, "seconds": 2.0, "head": 0.0, "slow": 1.0, "still": False},
            {"index": 3, "seconds": 1.5, "head": 0.25, "slow": 1.0, "still": False}]


def test_a_kept_crop_becomes_a_span_where_its_take_sits_in_the_cut(tmp_path):
    write(tmp_path)
    spans = fp.spans_from(layout(), {0: 48, 3: 36}, {3: "crop=744:744:12:12"},
                          tmp_path, sha_of=lambda i: "abcd1234", fps=24)
    assert [(s.index, s.start, s.frames, s.head, s.guard) for s in spans] == [(3, 48, 36, 6, (744, 744, 12, 12))]
    assert spans[0].tracks[0].life == (4, 40) and spans[0].tracks[0].crop.endswith("T03_p0.mp4")


def test_a_refine_of_other_bytes_is_never_pasted(tmp_path):
    write(tmp_path, sha="00000000")
    assert fp.spans_from(layout(), {0: 48, 3: 36}, {}, tmp_path, sha_of=lambda i: "abcd1234", fps=24) == []


def test_a_crop_the_gate_refused_is_never_pasted(tmp_path):
    write(tmp_path, kept=False)
    assert fp.spans_from(layout(), {0: 48, 3: 36}, {}, tmp_path, sha_of=lambda i: "abcd1234", fps=24) == []


def test_no_refine_file_is_the_unrefined_path(tmp_path):
    assert fp.spans_from(layout(), {0: 48, 3: 36}, {}, tmp_path, sha_of=lambda i: "x", fps=24) == []


def test_a_still_plays_no_take_and_gets_no_paste(tmp_path):
    write(tmp_path)
    rows = layout()
    rows[1]["still"] = True
    assert fp.spans_from(rows, {0: 48, 3: 36}, {}, tmp_path, sha_of=lambda i: "abcd1234", fps=24) == []
