"""ep27 (2026-10-09 17:00Z): after the voice, the battery refused shots 3 and 21
with 'stamp 00:06 outside 00:00-00:05' and 'the line crosses a cut' -- shots
with no cuts.  The dry take build got shot seconds from the VOICE (5.58 s, the
line recorded at 5.08 s) and placed the line by the RATE (past 6 s): two rulers
in one card.  The dry build projects what the renderer builds at plan time, so
its shots are projected at the rate, like its lines and like TAKE LENGTH."""
from __future__ import annotations

import sys
from types import SimpleNamespace

sys.path.insert(0, "scripts/episode")
import plan_check  # noqa: E402

from studio import plan_gates  # noqa: E402

LINE = "one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen"


def test_the_dry_projection_ignores_the_voice():
    ep = SimpleNamespace(shots=[SimpleNamespace(index=0, beat_s=0.0, coda_s=0.0, setup="room", cuts=[])],
                         lines=[SimpleNamespace(shot=0, text=LINE)])
    token = plan_gates.VOICE.set({LINE: 2.0})
    try:
        at_rate = plan_check.projected(ep, 2.5, voice=False)[0]["seconds"]
        by_voice = plan_check.projected(ep, 2.5)[0]["seconds"]
    finally:
        plan_gates.VOICE.reset(token)
    assert abs(at_rate - (0.5 + 15 / 2.5)) < 1e-6
    assert abs(by_voice - (0.5 + 2.0)) < 1e-6
