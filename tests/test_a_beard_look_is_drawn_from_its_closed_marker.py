"""The beard words a look is drawn with come from its CLOSED marker (C1_verdict #5).

MEASURED on the model's own sheets (C1_L §1a, `wotw_beards.png`): Krea2 +
Cinematic draws a beard only from a plain "full ... beard" noun -- 2/2
(captain "Full iron-grey beard trimmed square", Ogilvy "Full close-cut auburn
beard") -- and drops duration, stubble and qualified wording 0/7, including
ep25 ragged_greyed "Sixteen days of grey-brown beard" on all three draws.
So when `markers.facial_hair == beard` the drawn layer says
"a full short <colour> beard covering the jaw, chin and upper lip" and the
duration is kept only as an adjective. A `stubble` marker is NOT touched (owner:
stubble vs short beard is not ruled) and a look with no beard is byte-identical.
"""
from __future__ import annotations

from scripts.refs import looks
from studio.continuity_spec import CharacterLooks, Layers, Look, Markers

CANON = "a full short grey-brown beard covering the jaw, chin and upper lip"
RAGGED = Look(layers=Layers(headwear="battered brown felt hat.",
                            hair="Hair turned ash-grey throughout and grown shaggy over the ears.",
                            face="sixteen days of grey-brown beard; face gaunt, cheekbones sharp.",
                            top="Cream-and-blue striped flannel shirt torn at the shoulder."),
              markers=Markers(headwear="felt_hat", hair_colour="grey", facial_hair="beard", top="shirt"),
              face_change=True)
BASE = Look(layers=Layers(hair="Dark brown hair cut short.", face="Neat close-trimmed dark brown moustache."),
            markers=Markers(hair_colour="brown", facial_hair="moustache"), made_by="base")


def card(**more) -> CharacterLooks:
    return CharacterLooks(base="day_suit", body="Man of 34, slender.", looks={"day_suit": BASE, **more})


def test_the_ragged_greyed_prompt_carries_the_drawable_beard():
    said = looks.fresh_prompt(card(ragged_greyed=RAGGED), "ragged_greyed", "")
    assert CANON in said.lower()
    assert "sixteen days" in said.lower()                   # kept, as an adjective
    assert "face gaunt, cheekbones sharp" in said


def test_the_edit_route_says_the_same_beard():
    assert CANON in looks.edit_prompt(RAGGED).lower()


def test_a_look_without_a_beard_marker_is_byte_identical():
    plain = card(day_suit_hat=BASE.model_copy(update={"made_by": "fresh"}))
    before = "Dark brown hair cut short. Neat close-trimmed dark brown moustache."
    assert looks.layers_first(BASE) == before
    assert looks.fresh_prompt(plain, "day_suit_hat", "").startswith(before)


def test_a_stubble_look_is_byte_identical():
    stubble = RAGGED.model_copy(update={"layers": RAGGED.layers.model_copy(update={"face": "three days of dark stubble."}),
                                        "markers": RAGGED.markers.model_copy(update={"facial_hair": "stubble"})})
    assert "Three days of dark stubble." in looks.layers_first(stubble)
    assert "full short" not in looks.layers_first(stubble)


def test_a_plain_full_beard_wording_is_left_as_it_is():
    full = RAGGED.model_copy(update={"layers": RAGGED.layers.model_copy(update={"face": "Full iron-grey beard trimmed square."})})
    assert "Full iron-grey beard trimmed square" in looks.layers_first(full)


def test_a_styled_beard_keeps_the_books_words():
    """Lord Garrick's chin beard has a SHAVEN upper lip: the canonical sentence would
    contradict the book, so only the duration wording the model drops is rewritten."""
    chin = RAGGED.model_copy(update={"layers": RAGGED.layers.model_copy(
        update={"face": "Short square-cut white chin beard along the jaw with a shaven upper lip."})})
    assert looks.drawn_face(chin) == chin.layers.face
