"""Sub-shots: a cut inside a shot's audio window, no change to the audio.

A SHOT NOW HOLDS AT MOST ONE SUB-SHOT, and not by a rule that says so.  Three
constants decide it between them:

    MIN_SUB          = 2.5 s   a segment shorter than this is not a shot
    Line word wall   = 18      so one line projects at most 6.00 s of speech
    episode_takes.BUDGET = 8.0 a shot longer than this is a take nobody renders

Two sub-shots need three segments, 7.5 s of picture before handles, and no legal
shot reaches it: one line gives 6.50 s with its handles, two lines give 12.53 s
and are refused as over budget.  So the reachable shape is one cut, which is
exactly `episode_takes.SEGMENT_CAP = 2` -- two segments, one cut.

That agreement is new.  This file used to build a 9.2 s shot carrying two
narration lines and two sub-shots, a three-segment take the packer would have
refused and the spec accepted.  Episode 3 rendered two of those: they passed 0
of 2 at a mean of 23.5 and were the worst takes in the episode.
"""
import pytest

from studio import episode_timeline as tl
from studio.episode_spec import Episode, Line, Setup, Shot, SubShot

WORDS = "one two three four five six seven eight nine ten eleven twelve"
LONG = WORDS + " thirteen fourteen fifteen sixteen seventeen eighteen"   # 18, the wall


def plan(cuts):
    """A valid 30-shot episode; shot 1 carries ONE long narration line (6.50 s
    with its handles, inside the take budget) and the cuts under test."""
    shots, lines = [], []
    for i in range(30):
        section = "hook" if i == 0 else "turn" if i == 18 else "button" if i == 29 else "setup"
        faces = ["stamford"] if i in (0, 29) else (["john_watson"] if i == 2 else [])
        size = "medium_close" if faces else "medium"
        shots.append(Shot(index=i, section=section, setup="c", size=size, faces=faces, frame=f"F{i}.",
                          motion="Static", beat_s=1.0 if i == 28 else 0.0, cuts=cuts if i == 1 else []))
    lines.append(Line(index=0, kind="dialogue", speaker="stamford", text=WORDS, shot=0))
    lines.append(Line(index=1, kind="narration", speaker="john_watson", text=LONG, shot=1))
    for i in range(2, 29):
        lines.append(Line(index=i, kind="narration", speaker="john_watson", text=WORDS, shot=i))
    lines.append(Line(index=29, kind="dialogue", speaker="stamford", text=WORDS, shot=29))
    return Episode(number=1, title="t", protagonist="john_watson", setups={"c": Setup(described="corridor")},
                   shots=shots, lines=lines)


def cut(at_s: float, size: str = "insert", **kw) -> SubShot:
    return SubShot(at_s=at_s, size=size, frame="Hand.", motion="Static", **kw)


def test_one_sub_shot_inside_the_budget_is_the_reachable_shape():
    assert plan([cut(3.0)]).shot(1).cuts[0].at_s == 3.0


def test_a_last_sub_shot_under_the_minimum_is_refused():
    """Shot 1 projects 6.50 s; a cut at 4.5 leaves 2.0, under MIN_SUB."""
    with pytest.raises(ValueError, match="shorter than"):
        plan([cut(4.5)])


def test_a_first_sub_shot_too_early_is_refused():
    with pytest.raises(ValueError):
        plan([cut(1.0)])


def test_two_sub_shots_no_longer_fit_in_a_take():
    """Three segments need 7.5 s of picture and no legal shot reaches it.  The
    shot is inside the budget, so the refusal comes from MIN_SUB, not length."""
    with pytest.raises(ValueError, match="shorter than"):
        plan([cut(3.0), cut(5.5, "medium", faces=["john_watson"])])


def test_two_lines_and_two_sub_shots_is_a_take_nobody_can_render():
    """The old fixture's own shape: 9.2 s, two lines, two cuts.

    It VALIDATES -- the cuts at 3.0 and 6.0 each leave more than MIN_SUB of a
    9.2 s shot -- and that is the point.  Nothing in the contract refuses it;
    `long_shots` reports it and the steps that spend refuse on that, so a plan
    already on disk still loads (`test_a_shot_fits_in_a_take.py`)."""
    data = plan([]).model_dump()
    data["lines"].insert(2, Line(index=2, kind="narration", speaker="john_watson",
                                 text=WORDS, shot=1).model_dump())
    for k, line in enumerate(data["lines"]):
        line["index"] = k
    data["shots"][1]["cuts"] = [cut(3.0).model_dump(), cut(6.0, "medium").model_dump()]
    ep = Episode(**data)
    assert [i for i, _ in ep.long_shots()] == [1]

    from scripts.episode.takes_r2v import refuse_long_shots
    with pytest.raises(SystemExit, match="longer than a take"):
        refuse_long_shots(ep)


def test_a_dialogue_shot_takes_no_cuts():
    ep = plan([])
    shots = [s.model_dump() for s in ep.shots]
    shots[0]["cuts"] = [cut(3.0, "close").model_dump()]
    with pytest.raises(ValueError):
        Episode(**{**ep.model_dump(), "shots": shots})


def test_shot_seconds_and_the_timeline_are_unchanged_by_cuts_except_the_cuts_key():
    a, b = plan([]), plan([cut(3.0)])
    assert a.shot_seconds(a.shot(1)) == b.shot_seconds(b.shot(1))
    measured = {l.index: 4.0 for l in a.lines}
    pa, pb = tl.place(a, measured), tl.place(b, measured)
    assert pa["duration_s"] == pb["duration_s"]
    assert pa["shots"][1]["t_start"] == pb["shots"][1]["t_start"]
    s1 = pb["shots"][1]
    assert s1["cuts"] == [round(s1["t_start"] + 3.0, 3)]
    assert pa["shots"][1]["cuts"] == []


def test_a_last_sub_shot_that_would_be_too_short_is_reported():
    """The PROJECTION passed and the MEASURE did not: the line came back at 3.0 s,
    so shot 1 runs 3.50 s and the cut at 3.0 leaves 0.50."""
    ep = plan([cut(3.0)])
    placed = tl.place(ep, {l.index: 3.0 for l in ep.lines})
    assert tl.short_subshots(placed) == [1]
