"""Five-iterations build B4.3 (2026-10-20): eight of Jekyll ep01's frozen-whole
rows carried `hard=false` (the owner's 2026-10-18 grammar-locked exemption)
while their note still read "HARD: the whole frame stands still (locked on the
grammar, advisory)".  The delivery list and the brain read the note, so an
advisory printed as a wall.  The demoted row now says ADVISORY and never HARD,
and its numbers stay.  No video is read."""
from __future__ import annotations

from studio import stillness
from studio.take_verdict import Gate, grammar_still

LOCKED_TALK = ("The camera holds a locked-off frame across the whole shot; the man about town "
               "leans in and jabs a finger at the small man's chest")   # ep01 shot 10's motion, cut


def row():
    m = {"static_share": 0.94, "longest_static_run_s": 6.1, "still": True, "exempt": False}
    return Gate(**stillness.gate_args(m))


def test_the_hard_row_says_hard():
    assert "HARD" in row().note and row().hard is True


def test_the_demoted_row_says_advisory_and_never_hard():
    rec = {"grammar": True, "lane": "narration", "motions": [LOCKED_TALK]}
    got = next(g for g in grammar_still([row()], rec) if g.name == stillness.KIND)
    assert got.hard is False
    assert "HARD" not in got.note and "ADVISORY (locked on the grammar)" in got.note
    assert got.note.startswith("94% static, run 6.1s")
