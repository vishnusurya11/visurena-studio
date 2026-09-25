"""The timeline's path is named in one place, episode_home: a step that needs
only its timestamp (step 10's currency) asks for the path, never spells it."""
from studio import episode_home


def test_the_timeline_path_is_the_episode_homes_placed_json(tmp_path):
    assert episode_home.timeline_path(tmp_path, 12) == episode_home.home(tmp_path, 12) / "placed.json"
