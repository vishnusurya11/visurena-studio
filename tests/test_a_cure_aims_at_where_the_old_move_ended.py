"""A move-type cure aims at where the old move ENDED, whole (Jekyll ep01 HEL v2, 2026-10-14).

The batched round re-headed three frozen takes with garbled camera clauses, and two of
them froze again (H3 obeys the camera verb and its aim; a broken aim is no move):
  "pans from the lawyer across to the door's lock, travelling a quarter ..."
      -> "The camera tracks beside the lawyer across to the door's"
  "tilts up from the gold coins to the folded cheque, travelling a hand's breadth ..."
      -> "The camera tracks beside the gold coins to the folded"
  "pushes in a hand's breadth toward Mr. Enfield's face, across the whole shot"
      -> "The camera tracks beside Mr. Enfield's face,"
The aim took the FIRST preposition's whole tail, cut it at six words (mid-phrase), and
stripped its comma before the travel tail went.  A from-to move aims at its destination.
"""
from __future__ import annotations

from studio.take_ladder import aim_of


def test_a_from_to_move_aims_at_its_destination():
    got = aim_of("The camera pans from the lawyer across to the door's lock, travelling a quarter of the "
                 "frame, across the whole shot; Mr. Enfield lifts his cane")
    assert got == "the door's lock"


def test_the_destination_is_never_cut_mid_phrase():
    got = aim_of("The camera tilts up from the gold coins to the folded cheque, travelling a hand's breadth, "
                 "across the whole shot; the knuckly hand pushes the gold")
    assert got == "the folded cheque"


def test_no_comma_is_left_behind_the_aim():
    got = aim_of("The camera pushes in a hand's breadth toward Mr. Enfield's face, across the whole shot; "
                 "Mr. Enfield lowers his eyes")
    assert got == "Mr. Enfield's face"


def test_a_plain_aim_is_unchanged():
    assert aim_of("The camera pushes in toward the little man's pale face, travelling a forearm, across the "
                  "whole shot; he speaks") == "the little man's pale face"


def test_an_aim_cut_on_a_possessive_is_read_again_from_at_rest():
    """The plan already carries the garbled head ("tracks beside the lawyer across to the door's"):
    an aim that ends on a possessive names nothing and is read from at_rest instead."""
    got = aim_of("The camera tracks beside the lawyer across to the door's; Mr. Enfield lifts his cane",
                 "THE FOCUS OF THE PICTURE IS Mr. Enfield at the CENTRE, his head a quarter of the frame's height")
    assert got == "Mr. Enfield at the CENTRE"


def test_a_frozen_follow_gets_a_push_never_a_lock():
    """A frozen take whose cure already made it follow froze again (T18, T19): its next move
    is a push -- a lock is the one move a frozen cel take cannot be cured by."""
    from studio.take_ladder import substitute_id
    assert substitute_id("frozen-whole", "The camera tracks beside Mr. Enfield's face; he nods") == "push_slow"
    assert substitute_id("frozen-whole", "The camera holds a locked-off frame; he nods") == "push_slow"


def test_a_take_still_frozen_gets_its_second_move_type(tmp_path):
    """Owner ruling 2026-10-14: a drawn look is judged by the house stillness rule, and G-DEAD
    refuses a master holding a failed take.  A frozen take whose first move-type cure froze
    again is given its second, DIFFERENT move type (the skill's cure: change the move TYPE)
    while it has attempts left -- the identical-signature breaker still holds every other kind."""
    from studio import take_ladder as tl
    from studio.judges.verdict import Fault, Verdict
    room = tmp_path / "takes" / "r2v"
    (room / "attempts").mkdir(parents=True)
    v = Verdict(judge="take_eye", version="1", passed=False, confidence=1.0, reads=1,
                faults=[Fault(kind="frozen-whole", where="T18"), Fault(kind="held", where="T06")])
    tl.count_round(room, "batch: move_type", tl.signatures(v))
    again = tl.route(v, room, try_i=2)
    assert again == {"move_type": {18: [v.faults[0]]}}


def test_the_terminal_never_holds_a_panel_g_dead_will_refuse(tmp_path, monkeypatch):
    """T10 (6.75 s) and T16 (3.9 s) were settled as stills; G-DEAD refuses any still held past
    2.5 s, so the master could never be built.  A still is chosen only when G-DEAD would ship it;
    a longer narration take keeps its best render, flagged high."""
    from types import SimpleNamespace
    from studio import dead_footage, take_ladder as tl
    from studio.judges.verdict import Fault
    monkeypatch.setattr(tl, "shot_kind", lambda plan, i: "narration")
    monkeypatch.setattr(tl, "still_for", lambda home, i, fs: tmp_path / "shot.png")
    monkeypatch.setattr(tl, "load_stills", lambda home: {})
    monkeypatch.setattr(tl, "write_still", lambda *a, **k: None)
    faults = [Fault(kind="content", where="T10")]
    monkeypatch.setattr(tl, "placed_seconds", lambda home, i: 6.75)
    assert tl.settle_take(tmp_path, SimpleNamespace(), 10, faults, [9, 10, 11], 2) == "high"
    monkeypatch.setattr(tl, "placed_seconds", lambda home, i: dead_footage.STILL_LIMIT_S)
    assert tl.settle_take(tmp_path, SimpleNamespace(), 10, faults, [9, 10, 11], 2) == "still"


def test_a_still_g_dead_would_refuse_is_retired_from_the_cut(tmp_path):
    """stills.json written before the rule (ep01 v2 T10 6.75 s, T16 3.9 s) must not reach the cut:
    the cut holds the take instead, and its flag rides on."""
    import json
    from studio import take_ladder as tl
    home = tmp_path / "ep01"
    room = home / "takes" / "r2v"
    room.mkdir(parents=True)
    (room / "stills.json").write_text(json.dumps({"10": {"panel": "p.png", "seconds": 6.75, "decided": 1e10},
                                                  "12": {"panel": "q.png", "seconds": 2.0, "decided": 1e10}}),
                                      encoding="utf-8")
    assert list(tl.live_stills(home)) == [12]


def test_assemble_reads_the_same_live_stills(tmp_path):
    """assemble kept its own reader of stills.json and cut T10 (6.75 s) as a still after the
    ladder retired it: G-DEAD refused the master again (ep01 v2, 00:00Z)."""
    import json
    from scripts.episode import assemble
    room = tmp_path / "takes"
    room.mkdir()
    (room / "stills.json").write_text(json.dumps({"10": {"panel": "p.png", "seconds": 6.75, "decided": 1e10},
                                                  "12": {"panel": "q.png", "seconds": 2.0, "decided": 1e10}}),
                                      encoding="utf-8")
    assert list(assemble.stills_of(room, tmp_path)) == [12]
