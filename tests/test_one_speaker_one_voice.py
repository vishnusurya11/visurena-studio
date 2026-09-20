"""A speaker's own lines must sound like each other, not just like the design clip."""
from studio.speaker_spread import SAME_SPEAKER_FLOOR, spread, worst_pair


def test_lines_that_agree_pass():
    sims = {("l05", "l24"): 0.92, ("l05", "l09"): 0.88, ("l09", "l24"): 0.90}
    assert spread(sims)["ok"]
    assert spread(sims)["worst"] == 0.88


def test_a_published_episodes_worst_pair_still_passes():
    assert spread({("l01", "l19"): 0.72})["ok"]


def test_two_men_under_one_name_fail():
    """ep05: the neighbour's l05 and l24 each passed against the design clip and
    measured 0.58 against EACH OTHER -- two different men in one part."""
    sims = {("l05", "l24"): 0.58, ("l05", "l09"): 0.91}
    out = spread(sims)
    assert not out["ok"] and out["worst"] == 0.58
    assert worst_pair(sims) == ("l05", "l24")


def test_one_line_is_always_consistent_with_itself():
    assert spread({})["ok"] and spread({})["worst"] is None


def test_the_floor_passes_every_episode_already_published():
    """ep01 0.76, ep02 0.76, ep03 0.72 were watched, approved and published;
    the one real split measured 0.58. The floor has to clear the first three."""
    assert SAME_SPEAKER_FLOOR < 0.72
    assert SAME_SPEAKER_FLOOR > 0.58
