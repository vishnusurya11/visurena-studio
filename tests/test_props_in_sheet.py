"""Props reach the sheet: the pictures get attached and the sizes get a block.

Binding a prop and drawing its reference does nothing on its own -- episode 2's
sheet prompt has no PROPS block at all (`grep -c '^PROPS'` returns 0 on all six)
and its reference list carries only the plate and the cast.  These two functions
are what makes the object references actually reach gpt-image.

Which props a setup shows is READ FROM ITS OWN PANEL PROSE, by name and alias,
rather than declared a second time: `Setup.props` was declared `[]` on all six
setups of episode 2 while the panels named nine objects between them, and a
field that can disagree with the prose is the fault `cast_agree` exists to catch.
"""
from studio.episode_seq_board import props_block
from studio.prop_refs import Prop, props_in, refs_row

STICK = refs_row(Prop(
    id="walking_stick", name="Watson's walking stick", aliases=["the black stick", "his stick"],
    overall="stands hip high on a six-foot man", cross_section="its shaft is as thick as one finger",
    detail="a polished silver ball knob the size of a plum caps it",
    material="black lacquered hardwood", sits="beside his right boot", held_by="john_watson"))
VIOLIN = refs_row(Prop(
    id="violin", name="the violin", aliases=["the fiddle"],
    overall="as long as a man's forearm from elbow to fingertip",
    cross_section="its lower bout is two spread hands across",
    detail="four strings run to a scrolled head", material="warm varnished maple"))


def test_a_prop_named_in_the_prose_is_found():
    said = "Insert on the buttoned seat: the violin lies with its bow across the strings."
    assert [r["entity_id"] for r in props_in(said, [STICK, VIOLIN])] == ["violin"]


def test_an_alias_counts():
    said = "His bare sunburnt hand closes on the black stick at the counter's rail."
    assert [r["entity_id"] for r in props_in(said, [STICK, VIOLIN])] == ["walking_stick"]


def test_a_prop_nobody_mentions_is_left_out():
    assert props_in("An empty room in grey light.", [STICK, VIOLIN]) == []


def test_the_match_is_case_insensitive_and_whole_word():
    assert props_in("The VIOLIN stands on the seat.", [VIOLIN])
    assert props_in("He crossed the violinist's room.", [VIOLIN]) == []


def test_each_prop_is_returned_once_however_often_it_is_named():
    said = "the violin on the seat, the violin's bow, the fiddle again"
    assert len(props_in(said, [VIOLIN])) == 1


def test_the_block_states_every_size_the_props_carry():
    said = props_block([STICK, VIOLIN])
    assert said.startswith("PROPS")
    for part in ("hip high on a six-foot man", "as thick as one finger",
                 "as long as a man's forearm", "two spread hands across"):
        assert part in said


def test_the_block_names_the_reference_picture_so_the_model_binds_them():
    said = props_block([STICK])
    assert "Watson's walking stick" in said


def test_no_props_means_no_block():
    assert props_block([]) == ""
