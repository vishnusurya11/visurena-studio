"""Sub-shots: cuts inside a shot's audio window, no change to the audio."""
import pytest

from studio import episode_timeline as tl
from studio.episode_spec import Episode, Line, Setup, Shot, SubShot


WORDS = "one two three four five six seven eight nine ten eleven twelve"


def plan(cuts):
    """A valid 30-shot episode; shot 1 carries two narration lines and the cuts under test."""
    shots, lines = [], []
    for i in range(30):
        section = "hook" if i == 0 else "turn" if i == 18 else "button" if i == 29 else "setup"
        faces = ["stamford"] if i in (0, 29) else (["john_watson"] if i == 2 else [])
        size = "medium_close" if faces else "medium"
        shots.append(Shot(index=i, section=section, setup="c", size=size, faces=faces, frame=f"F{i}.",
                          motion="Static", beat_s=1.0 if i == 28 else 0.0, cuts=cuts if i == 1 else []))
    lines.append(Line(index=0, kind="dialogue", speaker="stamford", text=WORDS, shot=0))
    lines.append(Line(index=1, kind="narration", speaker="john_watson", text=WORDS, shot=1))
    lines.append(Line(index=2, kind="narration", speaker="john_watson", text=WORDS, shot=1))
    for i in range(2, 29):
        lines.append(Line(index=i + 1, kind="narration", speaker="john_watson", text=WORDS, shot=i))
    lines.append(Line(index=30, kind="dialogue", speaker="stamford", text=WORDS, shot=29))
    return Episode(number=1, title="t", protagonist="john_watson", setups={"c": Setup(described="corridor")},
                   shots=shots, lines=lines)


def test_sub_shots_ascend_and_keep_the_minimum_length():
    good = [SubShot(at_s=3.0, size="insert", frame="Hand.", motion="Static"),
            SubShot(at_s=6.0, size="medium", faces=["john_watson"], frame="Watson.", motion="Static")]
    assert plan(good).shot(1).cuts[1].at_s == 6.0
    with pytest.raises(ValueError):
        plan([SubShot(at_s=7.0, size="insert", frame="Hand.", motion="Static")])  # last sub-shot < 2.5 s of 9.0
    with pytest.raises(ValueError):
        plan([SubShot(at_s=3.5, size="insert", frame="Hand.", motion="Static"),
              SubShot(at_s=5.0, size="medium", frame="Watson.", motion="Static")])  # 1.5 s gap
    with pytest.raises(ValueError):
        plan([SubShot(at_s=1.0, size="insert", frame="Hand.", motion="Static")])  # first too early


def test_a_dialogue_shot_takes_no_cuts():
    ep = plan([])
    shots = [s.model_dump() for s in ep.shots]
    shots[0]["cuts"] = [SubShot(at_s=3.0, size="close", frame="X.", motion="Static").model_dump()]
    with pytest.raises(ValueError):
        Episode(**{**ep.model_dump(), "shots": shots})


def test_shot_seconds_and_the_timeline_are_unchanged_by_cuts_except_the_cuts_key():
    cuts = [SubShot(at_s=3.0, size="insert", frame="Hand.", motion="Static"),
            SubShot(at_s=6.0, size="medium", faces=["john_watson"], frame="Watson.", motion="Static")]
    a, b = plan([]), plan(cuts)
    assert a.shot_seconds(a.shot(1)) == b.shot_seconds(b.shot(1))
    measured = {l.index: 4.0 for l in a.lines}
    pa, pb = tl.place(a, measured), tl.place(b, measured)
    assert pa["duration_s"] == pb["duration_s"]
    assert pa["shots"][1]["t_start"] == pb["shots"][1]["t_start"]
    s1 = pb["shots"][1]
    assert s1["cuts"] == [round(s1["t_start"] + 3.0, 3), round(s1["t_start"] + 6.0, 3)]
    assert pa["shots"][1]["cuts"] == []


def test_a_last_sub_shot_that_would_be_too_short_is_reported():
    cuts = [SubShot(at_s=3.0, size="insert", frame="Hand.", motion="Static"),
            SubShot(at_s=6.0, size="medium", frame="Watson.", motion="Static")]
    ep = plan(cuts)
    placed = tl.place(ep, {l.index: 3.0 for l in ep.lines})  # shot 1 = 0.25+3+0.35+3+0.25 = 6.85 s < 6.0 + 2.5
    assert tl.short_subshots(placed) == [1]
