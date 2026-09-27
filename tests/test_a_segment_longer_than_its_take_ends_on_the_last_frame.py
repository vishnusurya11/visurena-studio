"""A segment the cut held past its take's last frame is checked against that
last frame, not an index past the end.

ep13 master_iter2 (2026-09-27): QC died on `index 146 is out of bounds for
axis 0 with size 146` -- a segment of 147 frames from a 146-frame take (the cut
holds the last frame), and edit_integrity crashed instead of measuring.
"""
import numpy as np

from studio import edit_gate


def test_the_last_frame_of_a_segment_is_clamped_to_the_take():
    frames = np.arange(146 * 4).reshape(146, 2, 2)
    assert (edit_gate.last_used(frames, 147) == frames[-1]).all()
    assert (edit_gate.last_used(frames, 100) == frames[99]).all()
