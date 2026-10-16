"""The grid prompt lint (studio/grid_lint): deterministic, $0.  Each rule is a
class the Jekyll ep01 audit found in a drawn grid prompt (02_prompts.md, P14-P16
and the grid classes G1-G5); each test quotes the faulty text it found."""
from __future__ import annotations

from studio import grid_lint as gl

CLEAN = ("WIDE: the man in <image1> and the man in <image2> walk away along the pavement and a "
         "ragged tramp strikes a match on the panels of the blistered door. In it: the man in <image1>; "
         "the man in <image2>.\n\nThe man in <image1> wears: black bowler hat; long black overcoat.")


def test_a_clean_prompt_has_no_fault():
    assert gl.faults(CLEAN) == []


def test_p14_picture_for_the_doors_panels():
    for bad in ("a match on the picture of the blistered door", "the blistered door picture fill the background",
                "a blistered brown picture, its paint peeling", "its picture streaked black"):
        assert any(f.startswith("P14") for f in gl.faults(bad)), bad


def test_p15_a_raw_row_after_in_it():
    bad = ("In it: the man in <image1>, a mr. richard enfield (receding brown hair; clean-shaven; light-brown "
           "top hat. he is presented as a gentleman who walks regularly with utterson and maintains chambers).")
    assert any(f.startswith("P15") for f in gl.faults(bad))


def test_p15_an_unstaged_line_naming_another_person():
    bad = "In it: the man in <image1>; a man with brown hair who walks with utterson."
    assert any(f.startswith("P15") for f in gl.faults(bad, names=["utterson", "jekyll"]))


def test_p15_an_unstaged_line_too_long():
    bad = "In it: a man " + " ".join(["word"] * 32) + "."
    assert any(f.startswith("P15") for f in gl.faults(bad))


def test_p16_a_girl_is_never_the_person():
    bad = "In it: the person in <image1>."
    assert any(f.startswith("P16") for f in gl.faults(bad, nouns={1: "girl"}))
    assert not any(f.startswith("P16") for f in gl.faults("In it: the girl in <image1>.", nouns={1: "girl"}))


def test_case_garble():
    assert any(f.startswith("CASE") for f in gl.faults("tHE FOCUS OF THE PICTURE IS the door"))


def test_cure_glued_as_a_noun_phrase():
    assert any(f.startswith("CURE") for f in gl.faults("The shot opens on only the named people stand"))
    assert gl.faults("Only the named people stand in the picture.") == []


def test_physique_in_a_wears_list():
    bad = "The man in <image1> wears: fashionable dark frock coat; compact; upright; heavy jaw."
    assert any(f.startswith("WEARS") for f in gl.faults(bad))


def test_a_parenthetical_after_a_slot():
    bad = "Medium close of the man in <image1> (light-brown top hat) on the pavement"
    assert any(f.startswith("SLOT") for f in gl.faults(bad))


def test_named_in_finds_a_name_or_a_dossier_phrase():
    assert gl.named_in("a man who walks with Utterson", ["utterson"]) == "Utterson"
    assert gl.named_in("a man associated with the house", []) == "associated with"
    assert gl.named_in("a man with brown hair", ["utterson"]) == ""
