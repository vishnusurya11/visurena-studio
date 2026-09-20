"""A cast row may declare `gender: "creature"`, and the builder stops saying "man".

WotW ep04: the Martian is a bear-sized bulk that is wholly head, with no arms,
no legs and no torso, and the whole first reveal is that absence.  The take
prompt called it "this man" and "the man in [Shot 1]" -- a humanoid noun beside
a sheet of a limbless bulk, in the one take the episode is built on.
"""
from studio import episode_ref_official as ro


def teardown_function():
    ro.WOMEN.clear()
    ro.CREATURES.clear()
    ro.DISPLAY.clear()


def test_a_creature_is_a_creature_and_an_it():
    ro.CREATURES.add("martians")
    assert ro.noun("martians") == "creature"
    assert ro.possessive("martians") == "Its"
    assert ro.objective("martians") == "it"


def test_men_and_women_are_unchanged():
    ro.WOMEN.add("narrators_wife")
    assert ro.noun("narrators_wife") == "woman" and ro.possessive("narrators_wife") == "Her"
    assert ro.noun("ogilvy") == "man" and ro.objective("ogilvy") == "him"


def test_the_row_is_what_declares_it():
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "episode"))
    import takes_r2v

    takes_r2v.adopt_names([{"kind": "character", "entity_id": "martians", "gender": "creature"},
                           {"kind": "character", "entity_id": "ogilvy", "gender": "male"}])
    assert ro.CREATURES == {"martians"} and ro.WOMEN == set()
    takes_r2v.adopt_names([])
    assert ro.CREATURES == set()
