"""G-PEOPLE (owner 2026-10-28: "they are hard checks .. things like that can't be ignored").

A duplicated or extra person was a fault every judge saw and every terminal shipped: the master
eye read ep05 shot 18 "3 figure(s) for 1 declared" and the master ladder's terminal signed it
flagged; a take kept at keep_best with a twin read shipped flagged through G-DEAD. On the masters
of Jekyll ep03-05 and WotW ep19-20 these reads were real (two identical constables, ep04 s6/s7;
Jekyll and Utterson as twins, ep03 s19; strangers in fog) -- 10 reads, 9 plainly right.

Now: the master's terminal REFUSES while a people fault stands, and G-DEAD counts a take with a
people fault as failed (cut out of the master when its neighbours cover it, else refused)."""
from __future__ import annotations

import pytest

from studio import master_ladder, people_faults
from studio.judges.verdict import Fault, Verdict

EXTRA = "3 figure(s) for 1 declared (1 cast + 0 extras), 0 of them copies of another"


def master(*faults: Fault) -> Verdict:
    return Verdict(judge="master_eye", version="1", passed=False, faults=list(faults), confidence=1.0, reads=30)


def test_an_extra_figure_and_a_twin_are_wrong_people():
    assert people_faults.wrong_line(EXTRA)
    assert people_faults.wrong_line("twin: man in a bowler x2 (2 figures, 1 distinct)")
    assert not people_faults.wrong_line("text or lettering in the picture")
    assert not people_faults.wrong_line("1 figure(s) for 2 named: someone the shot casts is missing")


def test_a_take_eye_twin_clone_or_extra_figure_is_wrong():
    assert people_faults.wrong({"kind": "twin", "where": "T06", "note": "twin: x"})
    assert people_faults.wrong({"kind": "clones", "where": "T06", "note": "two faces read as one man"})
    assert people_faults.wrong({"kind": "content", "where": "T06", "note": EXTRA})
    assert not people_faults.wrong({"kind": "warp", "where": "T06", "note": ""})


def test_the_takes_with_wrong_people_are_named():
    faults = [{"kind": "twin", "where": "T06"}, {"kind": "warp", "where": "T11"}, {"kind": "content", "where": "T22",
                                                                                 "note": EXTRA}]
    assert people_faults.takes(faults) == {6, 22}


def test_the_master_terminal_refuses_a_people_fault():
    v = master(Fault(kind="content", where="shot_18", evidence={"at": 81.9, "faults": [EXTRA]}))
    with pytest.raises(SystemExit, match="G-PEOPLE.*shot_18"):
        master_ladder.flag(v)


def test_the_master_terminal_still_ships_any_other_fault_flagged():
    v = master(Fault(kind="content", where="shot_22", evidence={"at": 100.5, "faults": ["text or lettering in the picture"]}))
    assert master_ladder.flag(v) is v


def test_g_dead_counts_a_kept_take_with_wrong_people_as_failed():
    from studio import dead_footage
    kept = {6: [{"kind": "twin", "where": "T06", "evidence": {"settled": "keep_best"}}],
            11: [{"kind": "look", "where": "T11", "evidence": {"settled": "keep_best"}}]}
    assert dead_footage.admitted(kept) == {11: kept[11]}


def _cut(tmp_path, monkeypatch, faults, failing=4):
    import json
    from scripts.episode import assemble
    from tests.test_a_still_terminal_does_not_hide_the_other_kept_takes import sign
    monkeypatch.setattr(assemble, "clip_seconds", lambda p: 6.3)
    sign(tmp_path, faults, names=("T03", "T04", "T05"))
    for i in (3, 4, 5):
        rec = {"passed": i != failing, "gates": [{"name": "warp", "hard": True, "ok": False}] if i == failing else []}
        (tmp_path / f"T{i:02d}.dq.json").write_text(json.dumps(rec), encoding="utf-8")
    placed = {"shots": [{"index": i, "seconds": 3.0} for i in (3, 4, 5)], "lines": [{"shot": 5, "kind": "narration"}]}
    return assemble.dead_plan(placed, {3: "a", 4: "b", 5: "c"}, {}, tmp_path, {})


def test_a_kept_twin_take_is_cut_not_shipped_flagged(tmp_path, monkeypatch):
    from tests.test_a_still_terminal_does_not_hide_the_other_kept_takes import fault
    plan = _cut(tmp_path, monkeypatch, [fault("T04", "keep_best", kind="twin")])
    assert plan["cut"] == [4] and plan["flagged"] == []


def test_a_passing_take_the_eye_saw_doubled_is_cut_too(tmp_path, monkeypatch):
    from tests.test_a_still_terminal_does_not_hide_the_other_kept_takes import fault
    plan = _cut(tmp_path, monkeypatch, [fault("T03", "keep_best", kind="twin")], failing=None)
    assert 3 in plan["cut"] and plan["flagged"] == []
