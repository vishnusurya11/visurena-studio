"""The anime-TV framing grammar (owner 2026-10-17), as plan gates.

Measured in part 2 of the model tests (docs/audit/2026-10-16_model_tests/
framing/results.json, Jekyll ep01 reframes on the shipped graphs and seeds):

- D3 a two-person reaction as a LOCKED MEDIUM two-shot: face 4.9 -> 11.3 % of
  frame, face sharpness 555 -> 1671, identity 0.20 -> 0.53 (from full + track);
- D5 the payoff line on a LOCKED CLOSE: face 35 -> 40 %, sharpness 3586 -> 4487;
- D2 the violent beat as a faceless low INSERT: no clones, no freeze -- but the
  voice held it 10.1 s where the grammar wants 1-3 s;
- D4 an over-the-shoulder CLOSE is not taken as frame 0 (19.8 dB, 2/2 seeds):
  OTS stays medium_close;
- D1/D6/D7 a silhouette, a Dutch angle and (D5) an eye close-up asked in WORDS
  failed every time: the staged place wins.  Unsupported until a panel route.

Faces: at least 55 % of the shots at close/medium_close.  Wides: at most 2,
4 s each (the opener 5 s).  Mediums 7 s at most.  At most 2 pushes, and no
amount words ("a hand's breadth": H3 governed 0 of 16).  $0."""
from __future__ import annotations

from types import SimpleNamespace

from studio import framing_grammar as fg

LOCKED = "The camera holds a locked-off frame across the whole shot; he turns his head; his hand lifts"
PUSH = "The camera pushes in toward his face, travelling a hand's breadth, across the whole shot; he turns; he lifts"
PAN = "The camera pans across to the door across the whole shot; he turns; his hand lifts"


def _shot(i, size="medium_close", faces=("lead",), motion=LOCKED, section="setup", frame="", camera=""):
    return SimpleNamespace(index=i, size=size, faces=list(faces), motion=motion, section=section,
                           frame=frame or f"{size} of the lead", camera=camera, at_rest="", end="",
                           cuts=[], beat_s=0.0, coda_s=0.0)


def _ep(shots, lines=()):
    return SimpleNamespace(shots=list(shots), lines=list(lines), omit=[],
                           cut_shots=lambda: list(shots))


def _line(i, shot, kind="narration"):
    return SimpleNamespace(index=i, shot=shot, kind=kind, speaker="lead", text="one two three")


def test_a_face_shot_is_close_or_medium_close_with_a_face():
    assert fg.face_shot(_shot(0, "close"))
    assert not fg.face_shot(_shot(0, "medium"))
    assert not fg.face_shot(_shot(0, "close", faces=()))


def test_under_55_percent_face_shots_is_refused():
    shots = [_shot(i, "close" if i < 5 else "medium") for i in range(10)]
    assert [f.split(":")[0] for f in fg.face_faults(_ep(shots))] == ["G-FACES plan"]
    shots = [_shot(i, "close" if i < 6 else "medium") for i in range(10)]
    assert fg.face_faults(_ep(shots)) == []


def test_three_wides_or_a_long_wide_is_refused():
    shots = [_shot(0, "wide"), _shot(1), _shot(2, "wide"), _shot(3, "wide")]
    secs = {0: 5.0, 1: 4.0, 2: 4.0, 3: 4.5}
    got = fg.wide_faults(_ep(shots), secs)
    assert any("G-WIDE plan" in f for f in got)                 # three wides
    assert any(f.startswith("G-WIDE shot 3") for f in got)      # 4.5 s past 4.0
    assert not any(f.startswith("G-WIDE shot 0") for f in got)  # the opener may hold 5 s


def test_a_medium_past_seven_seconds_is_refused():
    shots = [_shot(0, "medium"), _shot(1, "medium")]
    got = fg.medium_faults(_ep(shots), {0: 7.0, 1: 7.4})
    assert [f.split(":")[0] for f in got] == ["G-MEDIUM shot 1"]


def test_an_insert_is_an_impact_of_one_to_three_seconds():
    shots = [_shot(0, "insert", faces=()), _shot(1, "insert", faces=()), _shot(2, "insert", faces=())]
    got = fg.insert_faults(_ep(shots), {0: 2.5, 1: 3.6, 2: 0.6})
    assert [f.split(":")[0] for f in got] == ["G-INSERT shot 1", "G-INSERT shot 2"]


def test_a_third_push_is_refused_and_an_amount_word_on_any_head():
    shots = [_shot(i, motion=PUSH.replace(", travelling a hand's breadth", "")) for i in range(3)]
    assert [f.split(":")[0] for f in fg.push_faults(_ep(shots))] == ["G-PUSH shot 2"]
    assert [f.split(":")[0] for f in fg.amount_faults(_ep([_shot(0, motion=PUSH)]))] == ["G-PUSH shot 0"]
    assert fg.amount_faults(_ep([_shot(0, motion=LOCKED)])) == []


def test_the_camera_is_mostly_locked():
    shots = [_shot(i, motion=LOCKED if i < 4 else PAN) for i in range(10)]
    assert [f.split(":")[0] for f in fg.locked_faults(_ep(shots))] == ["G-LOCKED plan"]
    shots = [_shot(i, motion=LOCKED if i < 5 else PAN) for i in range(10)]
    assert fg.locked_faults(_ep(shots)) == []


def test_an_over_the_shoulder_close_is_refused_and_a_medium_close_is_not():
    ots = "Over the lawyer's shoulder toward Mr. Enfield's face"
    assert fg.ots_faults(_ep([_shot(0, "close", frame=ots)]))
    assert fg.ots_faults(_ep([_shot(0, "medium_close", frame=ots)])) == []
    assert fg.ots_faults(_ep([_shot(0, "close", frame="Close on the lawyer")])) == []


def test_a_two_person_reaction_is_a_locked_medium_two_shot():
    good = _shot(0, "medium", faces=("a", "b"), section="reaction")
    full = _shot(1, "full", faces=("a", "b"), section="reaction")
    moving = _shot(2, "medium", faces=("a", "b"), section="reaction", motion=PAN)
    alone = _shot(3, "full", faces=("a",), section="reaction")
    got = fg.two_shot_faults(_ep([good, full, moving, alone]))
    assert [f.split(":")[0] for f in got] == ["G-TWO shot 1", "G-TWO shot 2"]


def test_the_payoff_line_is_a_locked_close():
    shots = [_shot(0, "close", section="payoff"), _shot(1, "medium_close", section="payoff"),
             _shot(2, "close", section="payoff", motion=PUSH), _shot(3, "medium", section="payoff")]
    lines = [_line(k, k, "dialogue") for k in range(3)] + [_line(3, 3, "narration")]
    got = fg.payoff_faults(_ep(shots, lines))
    assert [f.split(":")[0] for f in got] == ["G-PAYOFF shot 1", "G-PAYOFF shot 2"]


def test_a_silhouette_a_dutch_angle_or_an_eye_close_up_in_words_is_unsupported():
    assert fg.unsupported_faults(_ep([_shot(0, frame="Wide of two men in silhouette against the lamp")]))
    assert fg.unsupported_faults(_ep([_shot(0, camera="the camera canted at a slant")]))
    assert fg.unsupported_faults(_ep([_shot(0, "extreme_close", frame="Extreme close on his eyes")]))
    assert fg.unsupported_faults(_ep([_shot(0, frame="Close on the lawyer under the lamp")])) == []


def test_the_grammar_numbers_are_one_table():
    band = fg.band()
    assert band["face_share"] == 0.55 and band["max_wides"] == 2 and band["max_pushes"] == 2
    assert band["wide_seconds"] == 4.0 and band["opener_wide_seconds"] == 5.0 and band["medium_seconds"] == 7.0
    assert band["insert_seconds"] == [1.0, 3.0] and "silhouette" in band["unsupported"]
