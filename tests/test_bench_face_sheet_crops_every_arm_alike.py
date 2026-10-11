"""R2_verdict §2.4: the owner's face-crop sheet.  For each readable face box at
8/50/92 % of the CONTROL take, the same box (as a share of the frame, so a 992
arm crops the same face as a 768 control) is cut from every arm and shown at
one display size, arms side by side.  The owner's deliverable, not a gate."""
import numpy as np

from scripts.bench import contact


def frame(size: int, shade: int) -> np.ndarray:
    return np.full((size, size, 3), shade, np.uint8)


def fake_read(video, shares):
    size = 992 if "992" in str(video) else 768
    return [frame(size, 40 * (k + 1)) for k, _ in enumerate(shares)]


def detect(rgb):
    h = rgb.shape[0]
    return [{"box": [0.4 * h, 0.2 * h, 0.5 * h, 0.32 * h], "score": 0.99},
            {"box": [0, 0, 10, 10], "score": 0.99}]          # too small to read: dropped


def test_a_box_is_kept_as_a_share_of_the_frame_and_squared():
    boxes = contact.face_boxes(frame(768, 0), detect)
    assert len(boxes) == 1
    x1, y1, x2, y2 = boxes[0]
    assert 0 <= x1 < x2 <= 1 and 0 <= y1 < y2 <= 1
    assert abs((x2 - x1) - (y2 - y1)) < 1e-6


def test_the_same_share_crops_the_same_face_at_any_canvas():
    box = (0.25, 0.25, 0.75, 0.75)
    assert contact.crop(frame(768, 9), box).shape[:2] == (384, 384)
    assert contact.crop(frame(992, 9), box).shape[:2] == (496, 496)


def test_the_sheet_has_a_row_per_arm_and_a_column_per_face():
    rows = [("A3", "a3.mp4"), ("A3+992", "a3_992.mp4")]
    img = contact.face_sheet(rows, detect, read=fake_read)
    assert img.size == (contact.LABEL_W + contact.FACE * 3, contact.FACE * 2)


def test_a_control_with_no_readable_face_gives_no_sheet():
    assert contact.face_sheet([("A3", "a.mp4")], lambda rgb: [], read=fake_read) is None
