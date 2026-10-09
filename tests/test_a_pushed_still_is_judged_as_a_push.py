"""ep26 (2026-10-09 14:20Z): QC failed the master on T06, a still -- its panel
held under the slow push -- because one frame-to-frame step read 4.57 against
SAME_FRAME 4.0, the take-vs-take limit.  The steps rose smoothly to ~4.1 at the
end of the push (median 1.68): a detailed panel moving under the zoom, not
another picture (32-63).  25 stills across ep14-26 read 1.02-3.75 and none was
another picture.  A still's inside steps get the still's own limit, STILL_FIRST's
'twice SAME_FRAME' -- an order below another picture."""
from __future__ import annotations

import numpy as np

from studio import edit_gate


def pushed(n: int = 12, last_step: float = 4.5) -> np.ndarray:
    """Frames whose consecutive mean differences grow to `last_step`."""
    base = np.full((edit_gate.GREY_H, edit_gate.GREY_W), 100.0)
    frames = [base.copy()]
    for i in range(1, n):
        frames.append(frames[-1] + last_step * i / (n - 1))
    return np.stack(frames)


def test_a_detailed_push_passes():
    master = pushed()
    row = edit_gate.still_match(master, 0, len(master), master[0])
    assert row["ok"] and row["inside_max"] > edit_gate.SAME_FRAME


def test_another_picture_inside_a_still_still_fails():
    master = pushed(last_step=1.0)
    master[6:] += 40.0
    assert not edit_gate.still_match(master, 0, len(master), master[0])["ok"]
