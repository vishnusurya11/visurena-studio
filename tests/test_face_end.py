"""G-FACE-END -- did the push carry the face out of the frame?

Episode 10: T05's second render ended on nostrils, T16 and T28 on a crown cut
by the top edge, and every row passed them (zoom measures scale, not whether
the face is whole).  The row reads ONE frame -- the last frame of the first
segment -- with OpenCV's YuNet (studio/models/yunet.onnx, 232 KB, CPU) and asks
two things of the largest face: how tall it is against the frame, and whether
its box touches an edge.

Everything here is synthetic: a shaded face sprite drawn with PIL, pasted into
frames on tmp_path.  No repo video, no GPU, nothing paid.  The model is a file
in the repo and runs in a few milliseconds on a 256-px frame.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from PIL import Image, ImageDraw, ImageFilter

from studio import face_end as fe

SIZE = 256


def sprite(size: int) -> Image.Image:
    """A face-like sprite YuNet reads: hair cap, shaded skin oval, brows, eyes
    with pupils, a nose with nostrils, a mouth.  Black around it."""
    s = size
    im = Image.new("RGB", (s, s), (0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((s * 0.12, 0, s * 0.88, s * 0.55), fill=(60, 40, 25))
    d.ellipse((s * 0.18, s * 0.08, s * 0.82, s * 0.97), fill=(224, 182, 150))
    for x0 in (0.10, 0.78):
        d.ellipse((s * x0, s * 0.42, s * (x0 + 0.12), s * 0.62), fill=(214, 172, 140))
    shade = Image.new("L", (s, s), 0)
    ImageDraw.Draw(shade).ellipse((s * 0.18, s * 0.08, s * 0.82, s * 0.97), fill=90)
    shade = shade.filter(ImageFilter.GaussianBlur(s * 0.08))
    im = Image.composite(im, Image.new("RGB", (s, s), (120, 80, 60)),
                         shade.point(lambda v: max(0, 255 - int(v * 1.6))))
    d = ImageDraw.Draw(im)
    for cx in (0.37, 0.63):
        d.arc((s * (cx - 0.11), s * 0.30, s * (cx + 0.11), s * 0.42), 200, 340, fill=(50, 35, 25), width=max(2, s // 60))
        d.ellipse((s * (cx - 0.075), s * 0.40, s * (cx + 0.075), s * 0.47), fill=(245, 245, 245))
        d.ellipse((s * (cx - 0.035), s * 0.405, s * (cx + 0.035), s * 0.465), fill=(70, 50, 40))
        d.ellipse((s * (cx - 0.015), s * 0.42, s * (cx + 0.015), s * 0.45), fill=(10, 10, 10))
    d.line((s * 0.5, s * 0.47, s * 0.47, s * 0.62), fill=(190, 140, 115), width=max(2, s // 80))
    d.ellipse((s * 0.44, s * 0.60, s * 0.56, s * 0.66), fill=(200, 150, 125))
    d.ellipse((s * 0.455, s * 0.625, s * 0.485, s * 0.65), fill=(120, 80, 70))
    d.ellipse((s * 0.515, s * 0.625, s * 0.545, s * 0.65), fill=(120, 80, 70))
    d.ellipse((s * 0.36, s * 0.72, s * 0.64, s * 0.80), fill=(160, 70, 70))
    return im.filter(ImageFilter.GaussianBlur(max(0.5, s / 400)))


def frame_with_face(frac: float, top: bool = False, size: int = SIZE) -> np.ndarray:
    """A dark frame with the sprite at `frac` of the frame height; `top` pushes
    it up so the hair and the brow leave through the top edge (YuNet's box is
    the face from the brow down, so the hair alone leaving is not a clip).
    A `frac` over 1 is a face larger than the frame -- the ep10 faults read
    0.74-0.85 of the frame AND clipped, and only a face that size does both."""
    fs = int(size * frac)
    frame = Image.new("RGB", (size, size), (30, 30, 30))
    y = -int(fs * 0.3) if top else (size - fs) // 2
    frame.paste(sprite(fs), ((size - fs) // 2, y))
    return np.asarray(frame)


def write_frames(frames: list[np.ndarray], folder: Path) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    for k, f in enumerate(frames):
        Image.fromarray(f).save(folder / f"f{k:04d}.png")
    return folder


# ---- the measure -----------------------------------------------------------------

class TestTheFaceRead:
    def test_a_face_at_half_the_frame_reads_about_half_and_whole(self):
        got = fe.largest_face(frame_with_face(0.5))
        assert got is not None
        assert 0.30 <= got["h"] <= 0.50 and not got["clipped"]

    def test_a_face_pushed_through_the_top_edge_reads_clipped(self):
        got = fe.largest_face(frame_with_face(0.8, top=True))
        assert got is not None and got["clipped"] and "top" in got["edges"]

    def test_a_bigger_face_reads_taller(self):
        small, big = fe.largest_face(frame_with_face(0.4)), fe.largest_face(frame_with_face(0.8))
        assert big["h"] > small["h"] + 0.2

    def test_an_empty_frame_has_no_face(self):
        assert fe.largest_face(np.full((SIZE, SIZE, 3), 30, np.uint8)) is None

    def test_the_largest_of_two_faces_is_read(self):
        frame = Image.fromarray(frame_with_face(0.6))
        frame.paste(sprite(48), (4, 200))
        got = fe.largest_face(np.asarray(frame))
        assert got["h"] > 0.35


class TestWhichFrame:
    def test_a_one_segment_take_reads_its_last_frame(self):
        assert fe.end_index([["Q05_0.png", 0]]) is None      # None = the last frame

    def test_a_two_segment_take_reads_the_frame_before_the_pin(self):
        assert fe.end_index([["Q03_0.png", 0], ["Q04_0.png", 85]]) == 84

    def test_no_anchors_is_the_last_frame(self):
        assert fe.end_index([]) is None

    def test_a_frames_folder_serves_the_named_frame_and_the_last(self, tmp_path):
        folder = write_frames([frame_with_face(0.3), frame_with_face(0.5), frame_with_face(0.8)], tmp_path / "f")
        assert fe.largest_face(fe.frame_at(folder, 1))["h"] < fe.largest_face(fe.frame_at(folder, None))["h"]


# ---- the verdict: pure arithmetic over one face read ----------------------------------

def gate(face, size="close", faces=("brigham_young",)):
    return fe.verdict(face, size, len(faces))


class TestTheWall:
    """CALIBRATION (docs/calibration/face_end.md, YuNet on the end frame of the
    first segment of every ep10 render): faults T05_fail2 0.85 clipped,
    T05_fail1 0.85, T16 0.81 clipped, T25 0.77, T28 0.74 clipped; KEEPs <= 0.73
    -- except T14 at 0.83 clipped, the one accepted false alarm -- and T22 at
    0.68 clipped, a close drawn without headroom, which the clip trigger's
    size floor keeps."""

    def test_the_walls_are_the_calibrated_numbers(self):
        assert (fe.FACE_END_HARD, fe.CLIPPED_HARD) == (0.75, 0.70)

    @pytest.mark.parametrize("h, clipped", [(0.85, True), (0.85, False), (0.81, True), (0.77, False), (0.74, True)])
    def test_the_five_ep10_faults_are_hard(self, h, clipped):
        g = gate({"h": h, "clipped": clipped, "edges": ["top"] if clipped else []})
        assert g.name == "face-at-end" and g.hard and not g.ok and g.penalty > 0

    @pytest.mark.parametrize("h", [0.73, 0.69, 0.68, 0.63, 0.59, 0.51, 0.40])
    def test_the_keeps_pass(self, h):
        g = gate({"h": h, "clipped": False, "edges": []})
        assert g.ok and not g.hard and g.penalty == 0

    def test_t14_is_the_accepted_false_alarm(self):
        """0.83 clipped on a KEEP: the wall fails it, and the calibration says so."""
        assert not gate({"h": 0.83, "clipped": True, "edges": ["top"]}).ok

    def test_a_small_face_on_the_edge_is_composition_not_a_clip(self):
        """T22: Lucy's close at 0.68 with the hair line on the top edge, a KEEP."""
        assert gate({"h": 0.68, "clipped": True, "edges": ["top"]}).ok

    def test_a_large_face_on_the_edge_is_leaving(self):
        """T28: 0.74, the profile going out frame-left as he turns to the window."""
        assert gate({"h": 0.74, "clipped": True, "edges": ["left"]}).hard

    def test_clipped_is_named_with_its_edge(self):
        assert "clipped top" in gate({"h": 0.80, "clipped": True, "edges": ["top"]}).note

    @pytest.mark.parametrize("size", ["medium", "wide", "insert", "full", "extreme_close"])
    def test_only_a_close_or_medium_close_can_fail(self, size):
        """T24 is an insert whose hand read as a 0.80 face: no planned face, no wall."""
        g = gate({"h": 0.86, "clipped": True, "edges": ["top"]}, size=size)
        assert g.ok and not g.hard

    def test_a_close_with_no_planned_face_cannot_fail(self):
        assert gate({"h": 0.86, "clipped": True, "edges": ["top"]}, faces=()).ok

    def test_a_planned_face_that_is_not_found_is_advisory(self):
        """T29_fail1's class: the back of a head where the plan staged a face."""
        g = gate(None)
        assert not g.ok and not g.hard and "no face" in g.note and g.penalty > 0

    def test_no_face_where_none_was_planned_is_quiet(self):
        g = gate(None, size="wide", faces=())
        assert g.ok and g.value is None


# ---- the row, end to end on a frames folder --------------------------------------------

class TestTheRow:
    def record(self, size="close", faces=("brigham_young",), anchors=None):
        return {"shots": [5], "anchors": anchors or [["Q05_0.png", 0]], "size": size, "faces": list(faces)}

    def test_a_push_that_ends_on_a_clipped_face_is_hard(self, tmp_path):
        clip = write_frames([frame_with_face(0.4), frame_with_face(0.6), frame_with_face(1.3, top=True)], tmp_path / "a")
        g = fe.row(clip, self.record())
        assert g.name == "face-at-end" and g.hard and not g.ok

    def test_a_push_that_keeps_the_face_whole_passes(self, tmp_path):
        clip = write_frames([frame_with_face(0.3), frame_with_face(0.4), frame_with_face(0.5)], tmp_path / "b")
        assert fe.row(clip, self.record()).ok

    def test_a_two_segment_take_is_judged_before_its_pin(self, tmp_path):
        frames = [frame_with_face(0.4), frame_with_face(0.5), frame_with_face(1.3, top=True)]
        clip = write_frames(frames, tmp_path / "c")
        assert fe.row(clip, self.record(anchors=[["Q18_0.png", 0], ["Q19_0.png", 2]])).ok

    def test_no_model_is_not_measured(self, tmp_path, monkeypatch):
        monkeypatch.setattr(fe, "detector", lambda size: None)
        clip = write_frames([frame_with_face(1.3, top=True)], tmp_path / "d")
        g = fe.row(clip, self.record())
        assert g.value is None and g.ok and not g.hard and g.note == "not measured"

    def test_the_model_file_is_in_the_repo(self):
        assert fe.MODEL.exists() and fe.MODEL.stat().st_size > 200_000
