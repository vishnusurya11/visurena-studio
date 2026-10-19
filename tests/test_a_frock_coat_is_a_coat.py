"""A frock is a dress only without "coat": a frock coat is a coat.

Jekyll Kawajiri ep01 (2026-10-18): Enfield's look 'frock_coat_topper' read as top=dress, so a judge
asked for a dress on a man in a frock coat."""
from studio import look_table as lt


def test_a_frock_coat_is_a_coat():
    assert lt.first_of(lt.TOP, "a black frock coat") == "coat"
    assert lt.first_of(lt.TOP, "Frock-coat") != "dress"


def test_a_frock_alone_is_still_a_dress():
    assert lt.first_of(lt.TOP, "a grey frock") == "dress"
    assert lt.first_of(lt.TOP, "a gown") == "dress"


def test_the_markers_of_a_frock_coat_look_say_coat():
    assert lt.markers_of("A tall man.", "Wearing: a black frock coat, a silk top hat.")["top"] == "coat"
