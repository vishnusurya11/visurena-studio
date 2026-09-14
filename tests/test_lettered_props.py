"""A prop MAY carry words -- when a picture of those words is attached.

The board's standing law is "Every surface in every panel stays wordless", and
it was written for a good reason: our own board drew CRISTERION on a shop sign
from a "no signage" clause, and episode 3 shipped both "Number 3 Lauriston
Gardens." and "Vinisitien of 3 Lauriston Gardens" from ONE seed and ONE blank
card.  gpt-image INVENTS lettering.

But the law overshoots what the measurement says.  What is a coin-flip is
GENERATION.  PROPAGATION from an attached picture came back near-lossless, 6 of
6, including a word at 14 % of frame width, defocused, under a moving camera.

So the real law is not "no words".  It is NO INVENTED WORDS -- and a word with a
reference picture is not invented, it is copied.  `wordless_law` states the
carve-out affirmatively (a negated noun is still that noun; that is what drew
CRISTERION), naming the exact letters and the picture they come from, and keeps
the blanket law wherever no lettered prop is on the sheet.

The plan's own prose is what has to stop hiding the words: episode 3 wrote "a
yellowed TO LET card ... the card's face blank and foxed" and "the name standing
in plain type ... its face unmarked" -- a card asked for and then asked to be
empty.
"""
import pytest

from studio.episode_seq_board import CONSTRAINTS, references_block, props_block, wordless_law
from studio.episode_spec import Setup
from studio.prop_refs import Prop, lettered, props_in, refs_row

CARD = refs_row(Prop(
    id="visiting_card", name="Drebber's visiting card",
    aliases=["visiting card", "printed visiting card", "calling card"],
    overall="held between one finger and thumb it covers half a man's palm",
    cross_section="it is as thin as a fingernail and stands stiff on its own",
    detail="three lines of fine black copperplate script run across its face",
    material="stiff ivory bristol board with square corners, foxed and yellowed",
    words="Enoch J. Drebber / Cleveland / Ohio", held_by="sherlock_holmes"))
RACHE = refs_row(Prop(
    id="rache_wall", name="the word written on the plaster",
    aliases=["blood-red word", "blood-red letters", "word scrawled across the plaster"],
    overall="the five letters run as wide as two spread hands on the wall",
    cross_section="each stroke is as thick as a man's fingertip",
    detail="the strokes are smeared and run down in thin dried drips",
    material="drying blood on bare ochre plaster", words="RACHE"))
STICK = refs_row(Prop(
    id="walking_stick", name="Watson's walking stick", aliases=["the black stick"],
    overall="stands hip high on a six-foot man", cross_section="its shaft is as thick as one finger",
    detail="a polished silver ball knob the size of a plum caps it",
    material="black lacquered hardwood", held_by="john_watson"))

ROOM = Setup(name="front_room", described="A bare front room with a tall curtainless window.",
             cast=[], props=[], state="day")


# ---- the field ------------------------------------------------------------

def test_a_prop_carries_no_words_by_default():
    """Nineteen props are already bound in the book and none of them is lettered;
    the field has to be absent-by-default or every one of them re-validates."""
    assert STICK["words"] == "" and lettered([STICK]) == []


def test_the_words_are_kept_verbatim_and_are_not_flattened_to_lower_case():
    assert RACHE["words"] == "RACHE"


def test_a_lettered_prop_is_picked_out_of_a_mixed_list_in_row_order():
    assert [r["entity_id"] for r in lettered([STICK, CARD, RACHE])] == ["visiting_card", "rache_wall"]


def test_the_words_reach_the_contract_sentence_so_the_size_block_carries_them_too():
    """`physical` is the one sentence repeated on every sheet AND every take. If
    the words live anywhere else they reach the sheet and not the take."""
    assert "RACHE" in RACHE["physical"]


def test_a_negation_inside_the_words_is_still_refused():
    """The affirmative rule is what keeps CRISTERION off the board; carrying
    letters through is not a licence to smuggle a "no ..." clause in."""
    with pytest.raises(ValueError, match="absence"):
        Prop(id="x", name="a notice", overall="as wide as a man's hand",
             cross_section="as thin as a fingernail", detail="black block capitals",
             words="NO ENTRY, no border")


# ---- the law --------------------------------------------------------------

def test_with_no_lettered_prop_the_law_is_the_standing_one_word_for_word():
    """The blanket law stays exactly as it is on the other 19 props and every
    sheet of every other episode. This change buys a carve-out, not a rewrite."""
    assert wordless_law([]) == CONSTRAINTS
    assert wordless_law([STICK]) == CONSTRAINTS


def test_the_carve_out_names_the_exact_letters():
    law = wordless_law([CARD, RACHE])
    assert "RACHE" in law and "Enoch J. Drebber / Cleveland / Ohio" in law


def test_the_carve_out_stays_affirmative_because_a_negated_noun_is_still_that_noun():
    """CRISTERION came off "no signage, no lettering". The exception may not be
    written as "no text EXCEPT ..." -- it says what IS on the surface."""
    from studio.affirm import negations
    assert not negations(wordless_law([CARD, RACHE]))


def test_every_other_surface_is_still_wordless_when_one_prop_is_lettered():
    assert "wordless" in wordless_law([CARD])


def test_the_carve_out_sends_the_model_to_the_picture_rather_than_to_its_own_spelling():
    """The whole reason this is safe is that the letters are COPIED. If the law
    does not say copy, the model spells it again and RAHE comes back."""
    assert "cop" in wordless_law([CARD]).lower()


# ---- the reference list ---------------------------------------------------

def test_the_indexed_reference_line_states_the_words_that_picture_carries():
    """A prop that held its size in episode 2 was the one both INDEXED and
    MEASURED in one sentence. Letters need the same: picture, index, words."""
    said = references_block(ROOM, {}, [CARD])
    assert "Enoch J. Drebber / Cleveland / Ohio" in said and "Image 2" in said


def test_an_unlettered_prop_reference_line_is_unchanged():
    assert "reads against the fingers" in references_block(ROOM, {}, [STICK])


# ---- and it all hangs off the prose, as the props already do ---------------

def test_the_plan_prose_finds_the_card_by_its_alias():
    said = ("A printed visiting card is held up in one bare hand at the CENTRE of frame, "
            "the thumb flat on its face.")
    assert [r["entity_id"] for r in props_in(said, [STICK, CARD, RACHE])] == ["visiting_card"]


def test_the_prose_that_calls_rache_only_the_word_still_finds_it():
    """Shot 19 never spells it -- "one word scrawled across it in blood-red
    letters" -- which is exactly why the alias list carries "the word"."""
    said = "One word stands scrawled across the plaster in blood-red letters, thick where the finger bore down."
    assert [r["entity_id"] for r in props_in(said, [STICK, CARD, RACHE])] == ["rache_wall"]


def test_the_size_block_carries_the_letters_into_the_sheet_prompt():
    assert "RACHE" in props_block([RACHE])
