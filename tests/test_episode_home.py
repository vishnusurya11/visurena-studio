"""An episode's files live under the book, and artifacts name them relatively."""
import json

import pytest

from studio import episode_home


def test_home_is_under_the_books_episodes_folder(tmp_path):
    assert episode_home.home(tmp_path, 3) == tmp_path / "episodes" / "ep03"


def test_paths_are_recorded_relative_to_the_book(tmp_path):
    line = tmp_path / "episodes" / "ep01" / "lines" / "l00.wav"
    assert episode_home.relative(tmp_path, line) == "episodes/ep01/lines/l00.wav"


def test_a_plan_is_validated_on_load(tmp_path):
    episode_home.write_json(episode_home.plan_path(tmp_path, 1), {"book": "b"})
    with pytest.raises(Exception):
        episode_home.load_plan(tmp_path, 1)


def test_write_json_makes_the_folder(tmp_path):
    out = episode_home.write_json(tmp_path / "a" / "b.json", {"x": 1})
    assert json.loads(out.read_text()) == {"x": 1}
