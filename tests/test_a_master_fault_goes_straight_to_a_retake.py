"""The master's ladder under judged_gate.clear: a fault on a measured field
takes one retake of the shot the evidence names (followed by its recut), and
the terminal signs the rubric flagged with an audit row.  A story-only fault
has no rung: it is flagged straight away, at no cost.

2026-09-27 (speed plan #7): the two free `recut` rungs are gone.  Step 11 runs
only on a master newer than every cut input, so a recut re-made the same bytes
(ep12 master_iter5 == iter7 by md5) and spent ~9 min of qc a rung while the
one rung that can move a fault, retake_shot, was starved of budget."""
from __future__ import annotations

import json

import pytest

from studio import audit_rows, judged_gate, master_ladder as ml
from studio.gate_policy import Policy
from studio.judges import master_eye as me
from studio.judges.verdict import Fault, Verdict
from studio.run_budget import EPISODE_SHARES, Budget

AUTO = Policy(state="auto", judge="master_eye@1", decision="2026-09-24-automate-the-taste-gates", terminal="flag")


class Ctx:
    def __init__(self, tmp_path):
        self.stage, self.unit = "episode", "ep01"
        self.book_dir = tmp_path / "book"
        self.home = self.book_dir / "episodes" / "ep01"
        self.budget = Budget(18000, EPISODE_SHARES, clock=lambda: 0.0)
        self.learned = []

    def learn(self, learning):
        self.learned.append(learning)


def off_board() -> Verdict:
    return Verdict(judge="master_eye", version="1", passed=False, confidence=1.0, reads=30,
                   faults=[Fault(kind="board", where="master",
                                 evidence={"off": {3: 0.1, 5: 0.2}, "share": 0.5, "wall": {"cell": 0.5}}),
                           Fault(kind="faces", where="master", evidence={"under": [3], "wall": 0.25})])


def story_only() -> Verdict:
    return Verdict(judge="master_eye", version="1", passed=False, confidence=1.0, reads=30,
                   faults=[Fault(kind="story", where="master", evidence={"matched": []})])


def climb(tmp_path, verdict: Verdict):
    ctx, taken = Ctx(tmp_path), []
    ladder = ml.rungs(verdict, recut=lambda: taken.append("recut"), retake=lambda shot, v: taken.append(("retake", shot)))
    signed = judged_gate.clear(ctx, "MASTER", judge=ml.once(verdict, lambda: verdict),
                               sign=lambda v: me.write_rubric(ctx.home, "abc12345", v),
                               ladder=ladder, terminal=ml.flag, policy=AUTO)
    return ctx, taken, json.loads(signed.read_text(encoding="utf-8"))


def test_one_retake_of_the_named_shot_then_flag(tmp_path):
    ctx, taken, doc = climb(tmp_path, off_board())
    assert taken == [("retake", 3), "recut"]
    assert doc["terminal"] == "flag" and doc["rubric"]["board"]["answer"] == "n"
    assert doc["rubric"]["board"]["flagged_by"] == "judge:master_eye@1"
    actions = [(l.action, l.terminal) for l in ctx.learned]
    assert actions == [("retake_shot", False), ("flag", True)]
    rows = audit_rows.load(ctx.book_dir)
    assert len(rows) == 1 and rows[0].gate == "MASTER" and rows[0].terminal == "flag"
    assert rows[0].artefact == "episodes/ep01/review/eye_abc12345.json" and rows[0].sha8 == "abc12345"


def test_a_story_fault_takes_no_rung_and_is_flagged_at_no_cost(tmp_path):
    ctx, taken, doc = climb(tmp_path, story_only())
    assert taken == [] and doc["terminal"] == "flag" and doc["rubric"]["story"]["answer"] == "n"
    assert [(l.action, l.terminal) for l in ctx.learned] == [("flag", True)]
    assert not ml.recuttable(story_only()) and ml.recuttable(off_board())


def test_the_worst_shot_is_the_one_the_measures_name_most():
    assert ml.worst_shot(off_board()) == 3
    assert ml.worst_shot(story_only()) is None


def test_once_serves_the_first_read_then_fresh_ones():
    served = []
    judge = ml.once(story_only(), lambda: served.append(1) or off_board())
    assert judge().faults[0].kind == "story" and served == []
    assert judge().faults[0].kind == "board" and served == [1]


# -- a rung is judged by whether its inputs changed (ep01 2026-10-18: a refused retake, a recut of
# the same bytes and a second 8-minute eye read, all for nothing) ---------------------------------

def climb_with(tmp_path, verdict: Verdict, retake_result):
    ctx, taken, judged = Ctx(tmp_path), [], []
    moved = ml.Round()
    ladder = ml.rungs(verdict, recut=lambda: taken.append("recut"),
                      retake=lambda shot, v: taken.append(("retake", shot)) or retake_result, moved=moved)

    def again():
        judged.append(1)
        return verdict
    signed = judged_gate.clear(ctx, "MASTER", judge=ml.once(verdict, again, moved), ladder=ladder,
                               sign=lambda v: me.write_rubric(ctx.home, "abc12345", v), terminal=ml.flag,
                               policy=AUTO)
    return taken, judged, signed


def test_a_refused_retake_takes_no_recut(tmp_path):
    taken, judged, _ = climb_with(tmp_path, off_board(), False)
    assert taken == [("retake", 3)] and judged == [], "no recut, no second master eye"


def test_a_silent_return_inside_retake_takes_no_recut(tmp_path):
    class Unchanged:
        changed, reason = False, "no new bytes"
    taken, judged, _ = climb_with(tmp_path, off_board(), Unchanged())
    assert taken == [("retake", 3)] and judged == []


def test_a_retake_that_changed_a_take_recuts_and_reads_again(tmp_path):
    taken, judged, _ = climb_with(tmp_path, off_board(), True)
    assert taken == [("retake", 3), "recut"] and judged == [1]


def test_a_legacy_retake_that_returns_nothing_keeps_its_recut(tmp_path):
    taken, judged, _ = climb_with(tmp_path, off_board(), None)
    assert taken == [("retake", 3), "recut"] and judged == [1]


def test_a_shadow_fault_has_no_shot_and_no_rung(tmp_path):
    shadow = Verdict(judge="master_eye", version="1", passed=False, confidence=1.0, reads=30,
                     faults=[Fault(kind="shadow", where="master", evidence={"share": 0.4})])
    assert not ml.recuttable(shadow) and ml.worst_shot(shadow) is None
    taken, judged, _ = climb_with(tmp_path, shadow, True)
    assert taken == [] and judged == []


def test_the_cap_line_names_why_no_recut_ran(tmp_path, capsys):
    climb_with(tmp_path, off_board(), False)
    assert "CAP master: retake of T03 changed no take, no recut" in capsys.readouterr().out


def test_a_retake_is_priced_from_the_measured_seconds_with_a_floor(tmp_path):
    from studio import step_attempts
    assert ml.retake_seconds(tmp_path) == 9 * 60.0
    step_attempts.spend(tmp_path, "retakes", 300.0)
    assert ml.retake_seconds(tmp_path) == 9 * 60.0
    step_attempts.spend(tmp_path, "retakes", 1500.0)
    assert ml.retake_seconds(tmp_path) == 900.0


def shot_room(tmp_path):
    room = tmp_path / "takes" / "r2v"
    room.mkdir(parents=True)
    (room / "T03.mp4").write_bytes(b"old take")
    (room / "shots.json").write_text("[1]", encoding="utf-8")
    return room


def test_the_fingerprint_moves_with_the_take_its_head_or_its_still_not_its_record(tmp_path):
    """Jekyll ep03 T04 (2026-10-27): a render rewrites shots.json even when keep_best keeps the old draw;
    the record is not what the cut reads (tests/test_a_master_retake_must_change_an_input.py)."""
    room = shot_room(tmp_path)
    before = ml.fingerprint(tmp_path, 3)
    (room / "shots.json").write_text("[2]", encoding="utf-8")
    assert ml.fingerprint(tmp_path, 3) == before
    (room / "T03.mp4").write_bytes(b"new take")
    assert ml.fingerprint(tmp_path, 3) != before
    after = ml.fingerprint(tmp_path, 3)
    (tmp_path / "heads.json").write_text('{"3": 0.2}', encoding="utf-8")
    assert ml.fingerprint(tmp_path, 3) != after


def through(tmp_path, monkeypatch, act, spent=False):
    """retake_through_take_ladder with the take ladder replaced by `act`."""
    from scripts.episode import step_09_shoot
    from studio import gate_policy, step_attempts, take_ladder
    monkeypatch.setattr(take_ladder, "refuse_spent", lambda ctx, n: spent)
    monkeypatch.setattr(take_ladder, "retake", lambda ctx, idx, why, flag, trims=None: act())
    monkeypatch.setattr(ml, "cured_plan", lambda home, shot, faults: ({}, "retake_shot: board -> move_type"))
    monkeypatch.setattr(ml.episode_home, "write_plan", lambda path, doc: path)
    monkeypatch.setattr(step_09_shoot, "approved", lambda p: "--ok")
    monkeypatch.setattr(gate_policy, "of", lambda stage, gate: None)
    ctx = Ctx(tmp_path)
    ctx.home = tmp_path
    return ml.retake_through_take_ladder(ctx, 3, off_board()), step_attempts.count(tmp_path, "retakes")


def test_a_retake_that_rewrote_the_take_is_changed_and_booked_once(tmp_path, monkeypatch):
    room = shot_room(tmp_path)
    changed, booked = through(tmp_path, monkeypatch, lambda: (room / "T03.mp4").write_bytes(b"new"))
    assert changed is True and booked == 1


def test_a_retake_that_left_the_bytes_is_unchanged_and_not_booked(tmp_path, monkeypatch):
    shot_room(tmp_path)
    changed, booked = through(tmp_path, monkeypatch, lambda: None)
    assert changed is False and booked == 0


def test_a_spent_episode_refuses_the_retake_without_a_recut(tmp_path, monkeypatch):
    shot_room(tmp_path)
    changed, booked = through(tmp_path, monkeypatch, lambda: pytest.fail("rendered"), spent=True)
    assert changed is False and booked == 0
