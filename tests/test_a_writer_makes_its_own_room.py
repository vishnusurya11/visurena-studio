"""A writer makes its own room.

`episode_home.master_path` returns `<home>/cut/master_<engine>.mp4` and nothing
created `cut/`.  Episodes 1 to 3 have one only because `migrate_layout.py` made
it while moving their masters in; a NEW episode never gets one, so the first
assemble reaches ffmpeg and dies on

    Error opening output ...\ep04\cut\master_r2v.mp4: No such file or directory

after the cut, the mix and the bed -- four minutes of GPU and a refused bed's
worth of retries -- had already been paid for.  The room is free and the work in
front of it is not, so it is made before the work starts, not at the moment of
writing.

`reports_dir` has the same shape: `runcards.py` writes `report_final.html` into
a folder only the migration ever created.
"""
from pathlib import Path

from studio import episode_home


def test_the_cut_room_is_made_for_a_fresh_episode(tmp_path):
    episode_home.make_rooms(tmp_path, 4)
    assert episode_home.cut_dir(tmp_path, 4).is_dir()


def test_the_reports_room_is_made_too(tmp_path):
    episode_home.make_rooms(tmp_path, 4)
    assert episode_home.reports_dir(tmp_path, 4).is_dir()


def test_it_is_safe_to_call_twice(tmp_path):
    episode_home.make_rooms(tmp_path, 4)
    episode_home.make_rooms(tmp_path, 4)
    assert episode_home.cut_dir(tmp_path, 4).is_dir()


def test_it_does_not_touch_another_episode(tmp_path):
    episode_home.make_rooms(tmp_path, 4)
    assert not episode_home.cut_dir(tmp_path, 5).exists()


def test_assemble_makes_its_rooms_before_it_spends(tmp_path):
    """Before the cut, the mix and the bed -- not at the moment of writing."""
    import inspect

    from scripts.episode import assemble
    src = inspect.getsource(assemble.main)
    assert "make_rooms" in src
    assert src.index("make_rooms") < src.index("quiet_bed")
