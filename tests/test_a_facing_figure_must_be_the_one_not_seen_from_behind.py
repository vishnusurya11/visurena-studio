"""G-WHO's third rule: in a shot whose plan sees a cast member only from behind, every figure FACING the camera
must fit one of the others (Jekyll ep06 panels 24/25, run 33, 2026-10-30).

Over the lawyer's shoulder toward the butler, the drawer put the lawyer's bowler and coat on the facing man.  The
reader called both men grey: facing in a bowler, the back one bare-headed -- which fits 'Poole from behind,
Utterson facing' once fair and grey are confusable, so no double and no stranger fired.  The plan says who has
his back turned (studio/back_view, grids.back_turned); the reader now says which figure faces the camera."""
from types import SimpleNamespace

from scripts.episode import panel_content_check as pcc
from studio import figure_who as fw
from studio import panel_content as pc

STAGED = {"poole": {"hair_colour": "fair", "facial_hair": "none", "coat": "dark", "hat": "none"},
          "gabriel_john_utterson": {"hair_colour": "grey", "facial_hair": "none", "coat": "dark", "hat": "hat"}}
BACK = frozenset({"gabriel_john_utterson"})
PANEL_24 = [{"headwear": "bowler", "hair": "grey", "facial_hair": "none", "coat": "black", "back_to_camera": "no"},
            {"headwear": "none", "hair": "grey", "facial_hair": "none", "coat": "black", "back_to_camera": "yes"}]


def test_the_facing_man_in_the_lawyers_hat_fails():
    bad = fw.fault(PANEL_24, STAGED, BACK)
    assert bad and bad.startswith("who: a figure facing the camera fits none of poole")


def test_the_butler_facing_bareheaded_passes():
    good = [{**PANEL_24[0], "headwear": "none", "hair": "blond"}, PANEL_24[1]]
    assert fw.fault(good, STAGED, BACK) is None


def test_a_figure_with_its_back_turned_is_not_judged_by_it():
    assert fw.turned([PANEL_24[1]], STAGED, BACK) is None


def test_no_one_seen_from_behind_turns_it_off():
    assert fw.turned(PANEL_24, STAGED, frozenset()) is None


def test_a_read_without_the_facing_key_is_not_judged_by_it():
    old = [{k: v for k, v in f.items() if k != "back_to_camera"} for f in PANEL_24]
    assert fw.turned(old, STAGED, BACK) is None


def test_the_ask_asks_which_way_each_figure_faces():
    assert "back_to_camera" in fw.ASK and fw.ASK_VERSION == "3"


def test_the_panel_check_hands_the_back_turned_cast_to_the_rule(monkeypatch, tmp_path):
    monkeypatch.setattr(pcc, "read_who", lambda path, seed=19: PANEL_24)
    monkeypatch.setattr(pc, "twin_applies", lambda planned, size, people: True)
    shot = SimpleNamespace(index=24, faces=["gabriel_john_utterson", "poole"], size="medium_close")
    faults = pcc.who_check(shot, SimpleNamespace(people=2), tmp_path / "shot_24.png", STAGED, BACK)
    assert faults and "facing the camera" in faults[0]
