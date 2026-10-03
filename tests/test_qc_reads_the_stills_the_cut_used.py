"""ep16 (2026-10-02): QC failed the edit on shots 16 and 19 as 'stills' whose
first frame was not the panel -- because the CUT had used the takes.  assemble
drops a still whose take was rendered again after the still was decided
(ep12 T19); QC read stills.json raw.  One rule, in one place: live_stills."""
from __future__ import annotations

import json
import os
import time

from studio.take_ladder import live_stills, stills_path


def test_a_take_rendered_after_its_still_retires_the_still(tmp_path):
    home = tmp_path
    room = home / "takes" / "r2v"
    room.mkdir(parents=True)
    now = time.time()
    (room / "T16.mp4").write_bytes(b"old")
    (room / "T19.mp4").write_bytes(b"new")
    os.utime(room / "T16.mp4", (now - 100, now - 100))     # rendered BEFORE the decision
    os.utime(room / "T19.mp4", (now + 100, now + 100))     # rendered AFTER the decision
    p = stills_path(home)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"16": {"panel": "a.png", "decided": now},
                             "19": {"panel": "b.png", "decided": now}}), encoding="utf-8")
    assert set(live_stills(home)) == {16}
