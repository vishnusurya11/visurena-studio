"""A row never carries two heads (retro 2026-10-10, A §5 cause 4).

The narrator's dossier body says "dark brown hair ... shaven cheeks and chin";
his ch22 look says "ash-grey ... sixteen days of grey-brown beard".  Joined,
the row asked for both, and every gate that read it allowed both.  The look's
head layers replace the body's, and the defining layer is written first."""
from __future__ import annotations

from studio import look_table as lt

BODY = ("Man of 34, 5 ft 10 in, slender and narrow-shouldered with long limbs. Long oval face, high "
        "forehead, long straight nose, straight dark brows, grey eyes. Fair English skin lightly tanned "
        "on face and hands. Dark brown hair cut short at back and sides, parted on the left and combed "
        "smooth. Neat close-trimmed dark brown moustache; shaven cheeks and chin.")
RAGGED = ("Cream-and-blue striped flannel shirt torn at the shoulder and stiff with black-brown earth, "
          "charcoal trousers caked with dried clay to the thigh, cracked black boots, battered brown felt "
          "hat. Hair turned ash-grey throughout and grown shaggy over the ears; sixteen days of grey-brown "
          "beard; face gaunt, cheekbones sharp.")
SUIT = ("Mid-grey herringbone tweed lounge suit: single-breasted jacket, matching waistcoat with a silver "
        "watch chain, narrow trousers. White shirt with starched turn-down collar, dark green knitted tie. "
        "Brown leather lace-up boots. Straw boater with a black band.")


def test_the_body_alone_keeps_no_hair_beard_or_hat():
    body = lt.body_of(BODY)
    assert "hair" not in body and "moustache" not in body and "shaven" not in body
    assert body.startswith("Man of 34") and "grey eyes" in body and "dark brows" in body


def test_a_ragged_row_never_says_dark_hair_or_shaven():
    text = lt.row_text(BODY, RAGGED)
    assert "Dark brown hair" not in text and "shaven" not in text and "moustache" not in text
    assert "ash-grey" in text and "grey-brown beard" in text


def test_the_looks_head_is_written_first():
    text = lt.row_text(BODY, RAGGED)
    assert text.startswith("Hair turned ash-grey")
    assert text.index("beard") < text.index("Man of 34") < text.index("Wearing:")


def test_a_look_that_states_no_head_keeps_the_bodys_head_and_bytes():
    text = lt.row_text("A man.", "A tweed suit.")
    assert text == "A man. Wearing: A tweed suit."
    assert lt.row_text("Tall man, grey eyes.", "a green cloak") == "Tall man, grey eyes. Wearing: a green cloak"


def test_a_clothes_only_look_keeps_the_bodys_hair_and_moustache():
    text = lt.row_text(BODY, SUIT)
    assert "Dark brown hair" in text and "moustache" in text and "Straw boater" in text


def test_the_markers_name_one_head():
    assert lt.markers_of(BODY, RAGGED) == {"headwear": "felt_hat", "hair_colour": "grey",
                                          "facial_hair": "beard", "top": "shirt", "dirt": "muddy"}
    assert lt.markers_of(BODY, SUIT) == {"headwear": "boater", "hair_colour": "dark",
                                        "facial_hair": "moustache", "top": "suit_jacket", "dirt": ""}


def test_bareheaded_is_a_stated_absence_of_a_hat():
    assert lt.markers_of("A man.", "Bareheaded, dark hair tousled over the brow.")["headwear"] == "none"


def test_a_clean_shaven_body_reads_none():
    assert lt.markers_of("A lean clean-shaven man of thirty-five.", "")["facial_hair"] == "none"


def test_no_text_states_no_marker():
    assert lt.markers_of("", "") == {"headwear": "", "hair_colour": "", "facial_hair": "", "top": "", "dirt": ""}
