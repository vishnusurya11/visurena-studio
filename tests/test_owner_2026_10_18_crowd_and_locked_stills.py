"""Two owner rulings on Jekyll Kawajiri ep01 (owner 2026-10-18 approved).

1. A setup's crowd enters a take only on a shot that declares extras > 0.  The night door's
   "five townsfolk ... pressing in a ring" was pasted into T00 (Hyde alone at 3 a.m.), T10,
   T11 and T12, every one extras=0, and the video model invented people walking in.
2. On a grammar plan a LOCKED shot is the grammar's own: frozen-whole is advisory on it when
   it speaks with a moving mouth (the lip-sync row present and passing) or carries an
   actor / ambient verb; the FROZEN cure never swaps a locked grammar shot to a push (G-PUSH);
   G-DEAD does not call such a take dead.
"""
from __future__ import annotations

from types import SimpleNamespace

from studio import dead_footage, episode_ref_official as ro, stillness, take_ladder
from studio.take_verdict import Gate, grammar_still

CROWD = "five townsfolk in shawls and nightcaps shouting and pressing in a ring by the kerb"


def seg(size="medium", extras=0, crowd=""):
    return {"size": size, "extras": extras, "crowd": crowd, "setup": SimpleNamespace(crowd=CROWD)}


def test_a_setup_crowd_stays_out_of_a_shot_with_no_extras():
    assert ro.crowd_of(seg(extras=0)) == ""


def test_a_shot_that_declares_extras_gets_the_setup_crowd():
    assert "townsfolk" in ro.crowd_of(seg(extras=5))


def test_a_shots_own_crowd_always_rides():
    assert "walkers" in ro.crowd_of(seg(extras=0, crowd="three walkers far off"))


def test_the_cell_carries_the_shots_extras():
    framed = SimpleNamespace(frame="", motion="", faces=[], size="wide", crowd="", end="", camera="",
                             at_rest="", changed="", still=False, extras=3)
    assert ro.cell(framed)["extras"] == 3


LOCKED_TALK = ("The camera holds a locked-off frame across the whole shot; the man about town's "
               "heavy jaw tightens; he jabs his cane back toward the west")


def frozen_row():
    return Gate(name="frozen-whole", value=0.85, ok=False, hard=True, note="85% static, run 2.71s HARD", penalty=51.0)


def test_a_locked_speaking_grammar_shot_is_advisory():
    rec = {"grammar": True, "lane": "dialogue", "motions": [LOCKED_TALK]}
    rows = grammar_still([frozen_row(), Gate("lip-sync", 0.0, True, True)], rec)
    row = next(g for g in rows if g.name == "frozen-whole")
    assert row.hard is False and "ADVISORY" in row.note


def test_a_speaking_shot_with_no_lip_sync_read_stays_hard():
    rec = {"grammar": True, "lane": "dialogue", "motions": [LOCKED_TALK]}
    row = next(g for g in grammar_still([frozen_row()], rec) if g.name == "frozen-whole")
    assert row.hard is True


def test_a_locked_narration_shot_with_an_actor_verb_is_advisory():
    rec = {"grammar": True, "lane": "narration", "motions": [LOCKED_TALK]}
    row = next(g for g in grammar_still([frozen_row()], rec) if g.name == "frozen-whole")
    assert row.hard is False


def test_a_push_or_a_legacy_plan_stays_hard():
    push = "The camera pushes in toward his face across the whole shot; he frowns"
    for rec in ({"grammar": True, "lane": "narration", "motions": [push]},
                {"grammar": False, "lane": "narration", "motions": [LOCKED_TALK]}):
        row = next(g for g in grammar_still([frozen_row()], rec) if g.name == "frozen-whole")
        assert row.hard is True


def test_the_frozen_cure_never_pushes_a_locked_grammar_shot():
    doc = {"grammar": "anime_tv", "lines": [], "shots": [{"index": 10, "motion": LOCKED_TALK, "at_rest": ""}]}
    from studio.judges.verdict import Fault
    out = take_ladder.move_type(doc, 10, [Fault(kind="frozen-whole", where="T10")])
    assert out["shots"][0]["motion"] == LOCKED_TALK


def test_g_dead_does_not_call_an_advisory_still_dead():
    record = {"passed": True, "gates": [{"name": "frozen-whole", "value": 0.85, "ok": True, "hard": False}]}
    state = dead_footage.state_of(4, {}, record)
    assert not dead_footage.is_dead(state, 5.9)
    assert not dead_footage.faults([(3, 5.9), (4, 5.9)], {3: state, 4: state})


def test_locked_and_acted_read_the_plan_words():
    assert stillness.locked(LOCKED_TALK) and stillness.acted(LOCKED_TALK)
    assert not stillness.locked("The camera pushes in toward his face across the whole shot; he frowns")
