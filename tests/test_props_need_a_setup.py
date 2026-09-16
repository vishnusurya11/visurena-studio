"""A prop is attached by a distinctive name, or by the setup that declares it.

MEASURED on episodes 8 and 9 (`docs/analysis/ep08_ep09_why_worse.md`, cause 8
and ep08 item 6): `props_in()` attached a prop by ANY alias, so "his hat" --
Jefferson Hope's, in a Utah parlour -- pulled Watson's brown bowler card off the
221B hat stand into two Utah sheets, and "the shawl" pulled the grey shawl from
the same hat stand onto three alkali-plain crag sheets, each with its size
contract and its "beside the sitting-room door".

An alias of pronoun-or-article + one common noun names a CATEGORY, and a
category belongs to more objects than the one that claimed it.  So it attaches
nothing unless the setup declares the prop; and a prop whose own description
keeps it in a place this setup lacks is refused with that place as the reason.
"""
import json
from pathlib import Path

from studio import episode_seq_board as sq, prop_refs
from studio.episode_spec import Episode, Setup

FIXTURES = Path(__file__).parent / "fixtures" / "episodes"

BOWLER = {"entity_id": "brown_bowler", "kind": "prop", "name": "Watson's brown bowler hat",
          "aliases": ["the bowler", "the brown bowler", "his hat"], "held_by": "john_watson",
          "physical": "Watson's brown bowler hat: Stiff dull brown felt; on the upper peg of the mahogany "
                      "hat stand beside the sitting-room door.",
          "sits": "on the upper peg of the mahogany hat stand beside the sitting-room door",
          "rel_path": "refs/props/prop-brown_bowler.png"}
SHAWL = {"entity_id": "grey_shawl", "kind": "prop", "name": "the folded grey wool shawl",
         "aliases": ["the shawl", "the grey shawl"], "held_by": "",
         "physical": "the folded grey wool shawl: Coarse knitted grey wool; over the lower peg of the "
                     "mahogany hat stand beside the sitting-room door.",
         "sits": "over the lower peg of the mahogany hat stand beside the sitting-room door",
         "rel_path": "refs/props/prop-grey_shawl.png"}
PRINT = {"entity_id": "fingerprint", "kind": "prop", "name": "the fingerprint on the window pane",
         "aliases": ["the mark on the glass", "the fingerprint"], "held_by": "",
         "physical": "the fingerprint on the window pane: skin grease on cold glass.",
         "sits": "on the inner face of the lower pane of the nearer sash window",
         "rel_path": "refs/props/prop-fingerprint.png"}
ROWS = [BOWLER, SHAWL, PRINT]

PARLOUR = Setup(described="The parlour of John Ferrier's log villa, a stone hearth and a pine table.",
                cast=["jefferson_hope"])
SITTING_ROOM = Setup(described="The sitting-room at 221B Baker Street, the hat stand beside the door.",
                     cast=["john_watson"])


def found(text, rows=ROWS, setup=None):
    return [r["entity_id"] for r in prop_refs.props_in(text, rows, setup)]


# ---- the alias ---------------------------------------------------------------------

def test_his_hat_is_a_category_and_attaches_nothing():
    assert found("Hope leaning in on his forearms with his hat off.", setup=PARLOUR) == []


def test_the_shawl_is_a_category_and_attaches_nothing():
    crag = Setup(described="The top of a crag on the alkali plain.", cast=["john_ferrier"], outdoors=True)
    assert found("the child wrapped in the shawl against his chest", setup=crag) == []


def test_a_distinctive_alias_still_attaches():
    assert found("the brown bowler on the peg", setup=SITTING_ROOM) == ["brown_bowler"]
    assert found("the mark on the glass catches the light") == ["fingerprint"]


def test_an_alias_that_is_the_objects_own_name_is_distinctive():
    """`the fingerprint` is article + noun, and the noun IS the object: there is
    one fingerprint in the book, so the category and the instance coincide."""
    assert found("the fingerprint stands on the glass") == ["fingerprint"]


def test_the_rule_names_the_shape_it_refuses():
    assert not prop_refs.distinctive("his hat", BOWLER)
    assert not prop_refs.distinctive("the shawl", SHAWL)
    assert not prop_refs.distinctive("the bowler", BOWLER)
    assert prop_refs.distinctive("the brown bowler", BOWLER)
    assert prop_refs.distinctive("walking stick", {"entity_id": "walking_stick"})
    assert prop_refs.distinctive("the fingerprint", PRINT)


# ---- the setup ---------------------------------------------------------------------

def test_a_setup_that_declares_the_prop_attaches_it_by_any_alias():
    declared = Setup(described="A Utah parlour.", cast=[], props=["brown_bowler"])
    assert found("Hope with his hat off", setup=declared) == ["brown_bowler"]


def test_a_prop_kept_in_another_place_is_refused_with_the_place_as_the_reason():
    refused = prop_refs.refusals("the grey shawl over the child", [SHAWL], PARLOUR)
    assert [r["entity_id"] for r, _why in refused] == ["grey_shawl"]
    assert "hat stand" in refused[0][1] and "sitting-room" in refused[0][1]


def test_the_same_prop_is_attached_where_its_place_is():
    assert found("the grey shawl on the peg", [SHAWL], SITTING_ROOM) == ["grey_shawl"]
    assert prop_refs.refusals("the grey shawl on the peg", [SHAWL], SITTING_ROOM) == []


def test_a_generic_alias_is_refused_with_the_alias_as_the_reason():
    refused = prop_refs.refusals("his hat off", [BOWLER], PARLOUR)
    assert len(refused) == 1 and "his hat" in refused[0][1]


def test_a_prop_the_text_never_names_is_neither_attached_nor_refused():
    assert found("An empty room.", setup=PARLOUR) == [] and prop_refs.refusals("An empty room.", ROWS, PARLOUR) == []


def test_without_a_setup_the_alias_rule_still_holds():
    """`seq_boards` passes no setup today; the alias rule needs none."""
    assert found("Hope with his hat off") == []


# ---- the fixtures ------------------------------------------------------------------

def prose(plan: str, name: str) -> str:
    episode = Episode.model_validate_json((FIXTURES / plan).read_text(encoding="utf-8"))
    return " ".join(str(v) for cell in sq.segments(episode.shots, name) for v in cell.values()), episode.setups[name]


def test_ep09_farm_parlour_and_the_drove_attach_no_bowler():
    for name in ("farm_parlour", "the_drove"):
        text, setup = prose("ep09_plan.json", name)
        assert "his hat" in text, name  # the alias that pulled it in
        assert found(text, setup=setup) == [], name


def test_ep08_crag_top_attaches_no_shawl():
    text, setup = prose("ep08_plan.json", "crag_top")
    assert "the shawl" in text
    assert found(text, setup=setup) == []


def test_ep09_as_drawn_had_the_fault():
    prompts = json.loads((FIXTURES / "ep09_sheet_prompts.json").read_text(encoding="utf-8"))
    for name in ("seq_farm_parlour_0.prompt.txt", "seq_the_drove_0.prompt.txt"):
        assert "prop-brown_bowler.png" in prompts[name]
