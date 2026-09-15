r"""A mark that belongs to one character may not be attributed to another.

THE FAULT, found by audit over every rendered take of episodes 1-5 (2026-09-14).
The faces are not confused: Holmes is clean-shaven in bottle-green velvet in
every take, Watson carries the waxed moustache and the tweed in every take, and
no take swaps their sides or their wardrobe. `<Subject N>` tagging is correct
everywhere, and so is every dialogue attribution.

What IS confused is the PROPS, and it is the kind you notice on a phone:

    ep04 T02 -- an insert of nothing but a hand, and that hand carries BOTH
    men's identity marks at once: Holmes's small white sticking plaster wound
    round a finger, gripping the silver ball knob of a black walking stick,
    which refs.json gives to WATSON alone. Holmes owns no stick anywhere in
    the bible.

    ep04 T00 -- both men hold the same stick in one cab two-shot, so at that
    scale they read as the same man twice.

It is authored in `plan.json` (`ep04/plan.json:98`, `:100`, `:121`), drawn into
the paid storyboard cell `boards/cells/Q02_0.png`, and then rendered. Nothing
downstream can catch it, because no stage compares a shot's prose against who
owns what. `Shot._no_banned_props` is the only prop gate and it knows a global
banned list and nothing about ownership.

AND I MADE IT AGAIN THE SAME DAY, writing episode 6: Gregson as "a heavy
fair-haired man in a dark grey overcoat over a fawn waistcoat" with "fat hands"
and "a broad pink face", 24 times, against a bible that says tall, long-limbed,
pale, flaxen, dark green hunting jacket. That is the strongest argument for the
gate there is -- the person who had just finished reading the audit wrote the
fault into the next plan.

NEAREST-PRECEDING-NAME IS THE WHOLE DIFFICULTY. The passing fixture below names
Holmes too; a naive "does this text contain Holmes and a stick" refuses a
correct shot. The mark is attributed to the last character named before it.

Free: string work on `plan.json`, before the $0.20 sheet.
"""
import pytest

from studio.episode_spec import crossed_mark

OWNERS = {"black walking stick": "john_watson",
          "silver ball knob": "john_watson",
          "waxed moustache": "john_watson",
          "sticking plaster": "sherlock_holmes",
          "bottle-green velvet": "sherlock_holmes",
          "hunting jacket": "tobias_gregson"}

NAMES = {"holmes": "sherlock_holmes", "watson": "john_watson", "gregson": "tobias_gregson"}


# ---- the real faults, verbatim from the plans on disk ----------------------

def test_holmes_may_not_hold_watsons_stick():
    """ep04/plan.json:118, the take that rendered both marks on one hand."""
    said = ("Insert on Holmes's raised hand between the two men, two fingers standing up "
            "off the head of the black walking stick, the open window beyond.")
    assert crossed_mark(said, OWNERS, NAMES) == ("sherlock_holmes", "black walking stick",
                                                 "john_watson")


def test_the_same_fault_with_the_knob_named():
    said = "Close on Holmes's hand on the silver ball knob, the plaster on his forefinger."
    got = crossed_mark(said, OWNERS, NAMES)
    assert got and got[0] == "sherlock_holmes" and got[2] == "john_watson"


def test_gregson_may_not_wear_holmess_velvet():
    said = "Medium close of Gregson in the bottle-green velvet jacket, his chin up."
    assert crossed_mark(said, OWNERS, NAMES)[0] == "tobias_gregson"


# ---- and the correct shots it must not refuse ------------------------------

def test_two_men_named_means_the_lint_stands_down():
    """ep03/plan.json, a correct shot. "Holmes" appears in this sentence too --
    inside a subordinate clause about the FLOOR -- and the stick is Watson's.
    Nearest-preceding-name calls it Holmes and refuses a correct shot; first-name
    calls it Watson and gets episode 6's breakfast two-hander wrong the other
    way. So two names means NOT MEASURED, and `unmeasured_marks` says so."""
    said = ("Medium on Watson down on one knee on the dusty boards where Holmes has knelt, "
            "bare-headed, sunburnt, the thin waxed moustache on his lip, his right hand on "
            "the silver ball knob of the black walking stick")
    assert crossed_mark(said, OWNERS, NAMES) is None


def test_holmes_wears_his_own_velvet():
    said = "Close on Holmes at the mantelpiece, the bottle-green velvet at his shoulder."
    assert crossed_mark(said, OWNERS, NAMES) is None


def test_gregson_wears_his_own_hunting_jacket():
    said = ("Medium close of Gregson, a tall long-limbed man, the dark green hunting jacket "
            "open over a black silk scarf.")
    assert crossed_mark(said, OWNERS, NAMES) is None


def test_a_mark_with_no_name_at_all_is_nobodys():
    """An insert naming no one has no candidate wearer. A KNOWN LIMIT, stated.
    The insert that actually shipped the fault names Holmes, so it is caught."""
    said = "Insert on a bare hand on the silver ball knob of the black walking stick."
    assert crossed_mark(said, OWNERS, NAMES) is None


def test_text_with_no_mark_at_all_is_clean():
    assert crossed_mark("Wide of the empty room, the grate cold.", OWNERS, NAMES) is None


def test_empty_text_is_clean():
    assert crossed_mark("", OWNERS, NAMES) is None


# ---- the owners come from refs.json, not from a constant -------------------

def test_the_marks_are_read_off_the_bible():
    from studio.episode_spec import marks_of

    refs = [{"kind": "character", "entity_id": "john_watson",
             "marks": ["black walking stick", "waxed moustache"]},
            {"kind": "character", "entity_id": "sherlock_holmes",
             "marks": ["sticking plaster"]},
            {"kind": "location", "entity_id": "sitting_room"}]
    assert marks_of(refs) == {"black walking stick": "john_watson",
                              "waxed moustache": "john_watson",
                              "sticking plaster": "sherlock_holmes"}


def test_a_row_with_no_marks_contributes_none():
    from studio.episode_spec import marks_of

    assert marks_of([{"kind": "character", "entity_id": "x"}]) == {}


def test_two_characters_may_not_claim_one_mark():
    """A mark owned by two people is not a mark; say so rather than pick one."""
    from studio.episode_spec import marks_of

    refs = [{"kind": "character", "entity_id": "a", "marks": ["a black stick"]},
            {"kind": "character", "entity_id": "b", "marks": ["a black stick"]}]
    with pytest.raises(ValueError, match="a black stick"):
        marks_of(refs)


# ---- an unmeasured segment is reported, never treated as a pass ------------

def test_a_two_hander_carrying_marks_is_reported_unmeasured():
    from studio.episode_spec import unmeasured_marks

    said = ("Medium of the table: Holmes bare-headed in the bottle-green velvet jacket in "
            "the far chair, Watson bare-headed, his thin waxed moustache dark on his face.")
    assert set(unmeasured_marks(said, OWNERS, NAMES)) == {"sherlock_holmes", "john_watson"}


def test_a_two_hander_with_no_marks_needs_no_report():
    said = "Wide of Holmes and Watson at the table, the grate cold beyond them."
    assert unmeasured("Wide of Holmes and Watson at the table.") == []
    assert unmeasured(said) == []


def unmeasured(text: str) -> list[str]:
    from studio.episode_spec import unmeasured_marks
    return unmeasured_marks(text, OWNERS, NAMES)


def test_a_single_named_man_is_measured_not_reported():
    assert unmeasured("Close on Holmes, the bottle-green velvet at his shoulder.") == []


# ---- who the names actually point at ---------------------------------------

ROWS = [{"kind": "character", "entity_id": "madame_charpentier", "name": "Madame Charpentier"},
        {"kind": "character", "entity_id": "alice_charpentier", "name": "Alice Charpentier"},
        {"kind": "character", "entity_id": "arthur_charpentier", "name": "Arthur Charpentier"},
        {"kind": "character", "entity_id": "madame_sawyer", "name": "Mrs Sawyer",
         "aka": ["the old woman"]},
        {"kind": "location", "entity_id": "sitting_room", "name": "The Sitting Room"}]


def test_a_shared_surname_identifies_nobody():
    """Three Charpentiers answer to `charpentier`, so the last row written won
    the key and episode 6's mother was reported as her son wearing her dress."""
    from studio.episode_spec import name_map

    assert "charpentier" not in name_map(ROWS)


def test_a_first_name_that_is_unique_still_works():
    from studio.episode_spec import name_map

    got = name_map(ROWS)
    assert got["alice"] == "alice_charpentier" and got["arthur"] == "arthur_charpentier"


def test_a_full_name_always_works():
    from studio.episode_spec import name_map

    assert name_map(ROWS)["madame charpentier"] == "madame_charpentier"


def test_a_descriptive_alias_is_a_name():
    """ep05 shot 20 calls her "the old woman going small and bent in her brown
    shawl" and names Holmes in the same sentence. Without the alias the shawl is
    attributed to Holmes, which is a false refusal of a correct shot."""
    from studio.episode_spec import name_map

    assert name_map(ROWS)["the old woman"] == "madame_sawyer"


def test_locations_are_not_people():
    from studio.episode_spec import name_map

    assert "sitting room" not in name_map(ROWS)


def test_the_alias_settles_the_ep05_shot():
    from studio.episode_spec import name_map

    said = ("Wide of Baker Street: the old woman going small and bent in her brown shawl "
            "along the far pavement, and Holmes in his heavy ulster following at the LEFT.")
    owners = {"brown shawl": "madame_sawyer", "bottle-green velvet": "sherlock_holmes"}
    names = dict(name_map(ROWS), holmes="sherlock_holmes")
    assert crossed_mark(said, owners, names) is None
