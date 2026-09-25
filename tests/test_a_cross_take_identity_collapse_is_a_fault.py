"""The cross-take identity pass: every character within DRIFT of his own
median over every frame he is in, and no two characters' medians within DRIFT
of each other.  Injected vectors; facenet is never loaded."""
from __future__ import annotations

import numpy as np

from studio import identity_gate
from studio.judges import master_eye as me


def vec(angle: float) -> np.ndarray:
    return np.array([np.cos(angle), np.sin(angle), 0.0, 0.0])


def reads(faces_by_shot: dict[int, list[dict]]) -> dict[int, list[me.Read]]:
    return {shot: [me.Read(at=float(shot), shot=shot, faces=faces)] for shot, faces in faces_by_shot.items()}


def test_two_characters_apart_and_each_steady_pass():
    grouped = reads({1: [{"h": 0.3, "vec": vec(0.0)}], 2: [{"h": 0.3, "vec": vec(0.05)}],
                     3: [{"h": 0.3, "vec": vec(1.5)}], 4: [{"h": 0.3, "vec": vec(1.55)}]})
    shots = {1: {"faces": ["a"]}, 2: {"faces": ["a"]}, 3: {"faces": ["b"]}, 4: {"faces": ["b"]}}
    assert me.identity(grouped, shots) == []


def test_two_characters_whose_medians_meet_collapse():
    grouped = reads({1: [{"h": 0.3, "vec": vec(0.0)}], 2: [{"h": 0.3, "vec": vec(0.1)}],
                     3: [{"h": 0.3, "vec": vec(0.05)}]})
    faults = me.identity(grouped, {1: {"faces": ["a"]}, 2: {"faces": ["a"]}, 3: {"faces": ["b"]}})
    assert [f.where for f in faults] == ["a+b"] and faults[0].kind == "identity"
    assert faults[0].evidence["cosine"] >= identity_gate.DRIFT and faults[0].evidence["wall"] == identity_gate.DRIFT


def test_a_character_who_drifts_from_his_own_median_is_a_fault():
    """Two of five reads far from the median: a drift.  One hard-lit frame alone
    is not (the next test): an accepted episode read one of six at 0.658."""
    grouped = reads({1: [{"h": 0.3, "vec": vec(0.0)}], 2: [{"h": 0.3, "vec": vec(0.0)}],
                     3: [{"h": 0.3, "vec": vec(0.0)}], 4: [{"h": 0.3, "vec": vec(1.4)}],
                     5: [{"h": 0.3, "vec": vec(1.4)}]})
    who = {i: {"faces": ["a"]} for i in range(1, 6)}
    faults = me.identity(grouped, who)
    assert len(faults) == 1 and faults[0].where == "a" and faults[0].evidence["min_cosine"] < identity_gate.DRIFT
    assert faults[0].evidence["reads"] == 5 and faults[0].evidence["below"] == 2


def test_one_read_off_the_median_is_not_a_drift():
    grouped = reads({1: [{"h": 0.3, "vec": vec(0.0)}], 2: [{"h": 0.3, "vec": vec(0.0)}],
                     3: [{"h": 0.3, "vec": vec(1.2)}]})
    faults = me.identity(grouped, {1: {"faces": ["a"]}, 2: {"faces": ["a"]}, 3: {"faces": ["a"]}})
    assert faults == []


def test_a_face_in_a_two_person_shot_is_counted_only_when_the_reader_names_him():
    grouped = reads({1: [{"h": 0.3, "vec": vec(0.0)}], 2: [{"h": 0.3, "vec": vec(1.2)}],
                     3: [{"h": 0.3, "vec": vec(0.0), "who": "a"}]})
    shots = {1: {"faces": ["a"]}, 2: {"faces": ["a", "b"]}, 3: {"faces": ["a", "b"]}}
    assert me.identity(grouped, shots) == []
