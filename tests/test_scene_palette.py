"""Within one scene the weather and palette hold (Jekyll ep01 iter4: pavement_day T11 overcast,
T12 a sunny blue sky; sunday_street blue and teal against a soot-and-oxblood palette)."""
import numpy as np

from studio import scene_palette as sp


def grey(h=64):
    return np.full((h, h, 3), 128, dtype=np.uint8)


def blue_sky(h=64):
    a = grey(h)
    a[: h // 3] = (90, 150, 230)
    return a


def test_stats_read_a_blue_sky_and_a_grey_one():
    assert sp.stats(blue_sky())["sky_blue"] > 60
    assert abs(sp.stats(grey())["sky_blue"]) < 1


def test_an_outlier_take_in_a_scene_is_named():
    stats = {11: sp.stats(grey()), 12: sp.stats(blue_sky()), 18: sp.stats(grey()), 19: sp.stats(grey())}
    got = sp.outliers(stats, {11: "pavement_day", 12: "pavement_day", 18: "pavement_day", 19: "pavement_day"})
    assert [t for t, _ in got] == [12]


def test_a_scene_of_one_take_has_no_outlier():
    assert sp.outliers({3: sp.stats(blue_sky())}, {3: "night"}) == []


def test_scene_map_reads_each_shots_setup():
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "episode"))
    import scene_palette as cli
    assert cli.scene_map({"shots": [{"index": 0, "setup": "door_day"}, {"index": 1, "setup": "door_day"}]}) == \
        {0: "door_day", 1: "door_day"}
