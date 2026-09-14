"""A shot longer than the take budget is a take nobody can render.

`MAX_LINES_PER_SHOT` caps a shot at two LINES, and two lines is not a length.
`episode_takes.groups` caps a RUN of shots at `BUDGET` seconds, but a single
shot over the budget still gets its own take -- the cap can split a run, never a
shot.  So a two-line shot walks straight past both.

MEASURED on episode 4's first plan, 2026-09-13: five of nineteen takes ran
9.4-12.25 s, and every one of them was a shot carrying two lines.  That band is
where takes die -- over episode 3's 24, 5.9-8.7 s passed 16 of 20 at a mean of
82.9, while the two at 12.25 s passed NONE at a mean of 3.75 and were the worst
two in the episode.

Nothing refused it.  It took reading the built take cards by hand to find, after
the plan had already been drawn twice.

The plan carries no seconds, but it carries WORDS, and `Episode.shot_seconds`
already projects a shot at the measured 3.0 words/s with its breaths, handles,
beat and coda.  Episode 4's rewritten plan projects a worst shot of 7.90 s and
measured 7.71 s, so the projection is close enough to refuse on.
"""
import pytest

from studio.episode_spec import Episode
from studio.episode_takes import BUDGET
from tests.test_episode_spec import NARR, episode


def test_the_budget_is_the_one_the_packer_uses():
    """One constant, not a second copy of the number."""
    import inspect

    from studio import episode_spec
    assert "episode_takes" in inspect.getsource(episode_spec)


def two_lines_on_one_shot() -> dict:
    """The episode-4 shape: one shot carrying both lines."""
    data = episode().model_dump()
    victim = data["lines"][2]["shot"]
    data["lines"][3] = dict(data["lines"][3], shot=victim)
    for k, line in enumerate(data["lines"]):
        line["index"] = k
    # the shot the second line left now carries nothing, so give it a beat
    data["shots"][victim + 1]["beat_s"] = 1.5
    return data


def test_a_shot_that_projects_past_the_budget_is_found():
    assert Episode(**two_lines_on_one_shot()).long_shots() == [(2, 11.87)]


def test_the_step_that_spends_refuses_it():
    """A QUERY on the plan, a REFUSAL at the step.  As a validator this refused
    episode 1's already-published plan (shot 17, 11.40 s) and broke every tool
    that merely READS an old plan, `story.py` included.  Reading a historical
    plan is not endorsing it."""
    from scripts.episode.takes_r2v import refuse_long_shots
    with pytest.raises(SystemExit, match="longer than a take"):
        refuse_long_shots(Episode(**two_lines_on_one_shot()))


def test_the_refusal_names_the_shot_and_its_seconds():
    from scripts.episode.takes_r2v import refuse_long_shots
    with pytest.raises(SystemExit) as e:
        refuse_long_shots(Episode(**two_lines_on_one_shot()))
    said = str(e.value)
    assert "shot 2 projects 11.87 s" in said and f"({BUDGET} s)" in said
    assert "Split each into two" in said


def test_an_old_plan_with_a_long_shot_still_loads():
    """Episode 1 ships one.  It must keep loading for every reader."""
    from studio import episode_home
    ep = episode_home.load_plan(episode_home.book_dir("20260822113400_a-study-in-scarlet"), 1)
    assert ep.long_shots() == [(17, 11.4)]


def test_one_line_a_shot_still_passes():
    """The shape episode 4 ships: every shot inside the budget."""
    ep = episode()
    assert max(ep.shot_seconds(s) for s in ep.shots) <= BUDGET


def test_a_hold_counts_against_the_budget_too():
    """It is not a rule about lines.  A beat and a coda are picture as well, and
    a shot already near the budget is pushed over by them."""
    data = episode().model_dump()
    # 18 words is the line wall, so one line can never overrun alone: 6.00 s of
    # speech + 0.50 of handles.  A full beat and a coda push it to 9.50.
    data["lines"][4]["text"] = " ".join(["word"] * 18)
    data["shots"][data["lines"][4]["shot"]].update(beat_s=1.5, coda_s=1.5)
    assert Episode(**data).long_shots()


def test_a_shot_exactly_at_the_budget_is_allowed():
    """18 words (6.00 s) + two handles (0.50) + a full beat (1.50) = 8.00."""
    data = episode().model_dump()
    data["lines"][4]["text"] = " ".join(["word"] * 18)
    data["shots"][data["lines"][4]["shot"]]["beat_s"] = 1.5
    ep = Episode(**data)
    assert ep.shot_seconds(ep.shots[data["lines"][4]["shot"]]) == BUDGET


def test_the_shipped_episode_four_plan_passes():
    from studio import episode_home
    ep = episode_home.load_plan(episode_home.book_dir("20260822113400_a-study-in-scarlet"), 4)
    assert max(ep.shot_seconds(s) for s in ep.shots) <= BUDGET
