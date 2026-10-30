"""G-WHO's second rule: a figure that fits NO staged cast member (Jekyll ep06 panels 24/25, 2026-10-29).

Redrawn on the emptied doorstep room, panels 24 and 25 put the lawyer's bowler and double-breasted coat on the
man facing camera, with black hair: not Poole (bare-headed, fair) and not Utterson (grey).  G-WHO looks only
for two figures resolving to one member, found none, and both panels passed.  A figure that clashes with every
member -- each member's look stating every NEEDED key, so none is a sink -- is a stranger in the shot."""
from studio import figure_who as fw

STAGED = {"poole": {"hair_colour": "fair", "facial_hair": "none", "coat": "dark", "hat": "none"},
          "gabriel_john_utterson": {"hair_colour": "grey", "facial_hair": "none", "coat": "dark", "hat": "hat"}}
PANEL_24 = [{"headwear": "top_hat", "hair": "black", "facial_hair": "none", "coat": "black"},
            {"headwear": "none", "hair": "grey", "facial_hair": "none", "coat": "black"}]


def test_the_ep06_panel_24_read_is_a_stranger_fault():
    bad = fw.fault(PANEL_24, STAGED)
    assert bad and bad.startswith("who: a figure fits no cast member")


def test_the_two_men_as_staged_pass():
    both = [{"headwear": "none", "hair": "blond", "facial_hair": "none", "coat": "black"},
            {"headwear": "bowler", "hair": "grey", "facial_hair": "none", "coat": "black"}]
    assert fw.fault(both, STAGED) is None


def test_a_figure_fitting_one_member_is_no_stranger():
    assert fw.stranger([{"headwear": "none", "hair": "grey", "facial_hair": "none", "coat": "black"}], STAGED) is None


def test_a_member_with_a_key_unsaid_could_be_anyone():
    vague = {**STAGED, "poole": {"hair_colour": "fair", "facial_hair": "none", "coat": "", "hat": "none"}}
    assert fw.stranger(PANEL_24, vague) is None


def test_a_double_is_still_named_first():
    twice = [{"headwear": "bowler", "hair": "grey", "facial_hair": "none", "coat": "black"}] * 2
    assert fw.fault(twice, STAGED).startswith("who: 2 figures read as 'gabriel_john_utterson'")
