"""A8: G-MUTE, no speech verb on a face that does not speak (craft ruling 2026-10-21, wave 1).

Jekyll ep01 shot 13 has Enfield "speaking" and shot 15 "answering" while the narrator speaks (lines 12
and 14 are narration); take audio carries dialogue only (takes_r2v.py:693-703), so H3 moved a mouth with
no voice (T13 "speaks ... mouth is closed").  A `tale` or `narration` line drives no lips, so neither
counts as speaking.  A face too small to read (full, wide, insert) is not asked: shot 8's girl "screams"
in a full shot is the take-prompt C13 class, not this one.  The row is a SHADOW: plan_check prints it,
it never counts, and plan_repair never reads an advisory row; its free cure ("listens") is registered
for the day it earns a wall.  Fixture: tests/fixtures/craft (Jekyll ep01 plan.json).  No spend."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

from scripts.episode import screenplay_replay as sr
from studio import plan_cures, screenplay_grammar as sg

CRAFT = Path(__file__).parent / "fixtures" / "craft"


def plan() -> dict:
    return json.loads((CRAFT / "episodes" / "ep01" / "plan.json").read_text(encoding="utf-8"))


def test_ep01_fires_on_shots_13_and_15_only():
    fires = sg.mute_faults(plan(), [])
    assert [f.split(":")[0] for f in fires] == ["G-MUTE shot 13", "G-MUTE shot 15"]
    assert "speaking" in fires[0] and "answering" in fires[1]


def test_a_tale_drives_no_lips_so_it_does_not_speak():
    doc = plan()
    doc["lines"][3]["kind"] = "tale"                  # Enfield's "Did you ever remark that door?" told, not said
    assert "G-MUTE shot 3" in [f.split(":")[0] for f in sg.mute_faults(doc, [])]


def test_the_cure_makes_the_face_listen_and_the_row_goes_quiet():
    cured = plan_cures.mute_listens(copy.deepcopy(plan()), [13, 15])
    assert "listening on the pavement" in cured["shots"][13]["frame"]
    assert "listens and taps his black walking cane" in cured["shots"][13]["motion"]
    assert cured["shots"][15]["frame"].endswith("listening, the court entry behind him.")
    assert sg.mute_faults(cured, []) == []
    assert cured["shots"][3] == plan()["shots"][3]            # a shot that speaks keeps its verb


def test_the_row_routes_to_the_cure_but_an_advisory_never_reaches_repair():
    assert plan_cures.cure_for("G-MUTE shot 13: a speech verb on a face with no dialogue line") == "mute_listens"
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "episode"))
    import plan_repair
    assert plan_repair.fault_rows("  advisory: G-MUTE shot 13: speaking") == []
    doc, uncured, names = plan_repair.apply(plan(), ["G-MUTE shot 13: speaking"], CRAFT, llm=False)
    assert names == ["mute_listens"] and "listening" in doc["shots"][13]["frame"]


def test_the_replay_reads_it_on_every_plan():
    row = sr.fires(plan(), [], sr.CHECKS["silent_speaker"])
    assert len(row) == 2


def test_plan_check_prints_it_as_advice():
    import inspect
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "episode"))
    import plan_check
    assert "mute_faults" in inspect.getsource(plan_check.shadow_rows)


def test_the_replay_silences_every_speaking_face_and_g_mute_hears_each():
    names = [m["name"] for m in sr.mutants(plan(), []) if m["expect"] == "silent_speaker"]
    assert len(names) == 8 and names[0] == "dialogue 3 told as a tale"
    out = sr.recall(plan(), [], {"silent_speaker": sr.CHECKS["silent_speaker"]})["silent_speaker"]
    assert out["k"] == out["n"] == 8
