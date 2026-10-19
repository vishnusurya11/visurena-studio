"""The take's anti-lettering sentence names the bait nouns the take's own text holds.

The constant used to say "cheque" in every take of every book (Jekyll Kawajiri ep01: 28 of 28), a word
the code tree must not know; the book's cheque appears only in the takes whose text holds one (T12).
P14 (`prompt_lint.p14_lettering`) is kept: any bait noun in the detail still needs 'unlettered'.
Fixture: tests/fixtures/ep01_replay/P03/shots.json (copy of ep01's takes/r2v/shots.json)."""
import json
import re
from pathlib import Path

from studio import episode_ref_official as ro
from studio import prompt_lint

TAKES = json.loads((Path(__file__).parent / "fixtures" / "ep01_replay" / "P03" / "shots.json").read_text("utf-8"))
OLD = "Every sign, plate, cheque and paper in the picture is plain and unlettered."


def test_the_code_tree_constant_names_no_book_noun():
    assert "cheque" not in ro.UNLETTERED
    assert ro.UNLETTERED == "Every sign, plate and paper in the picture is plain and unlettered."
    assert not ro.negations(ro.UNLETTERED)


def test_a_take_with_a_cheque_names_it():
    assert ro.unlettered_for("Enfield holds out the cheque.") == \
        "Every sign, plate, cheque and paper in the picture is plain and unlettered."


def test_a_take_with_two_bait_nouns_names_both_in_the_book_order():
    said = ro.unlettered_for("A letter and a ledger lie open.")
    assert said == "Every sign, plate, letter, ledger and paper in the picture is plain and unlettered."


def test_a_take_holding_none_says_the_base():
    assert ro.unlettered_for("The door stands shut.") == ro.UNLETTERED


def test_every_bait_noun_p14_knows_is_in_the_base_or_the_extras():
    stems = {n.rstrip("?")[:-1] if n.endswith("s?") else n.rstrip("?") for n in prompt_lint.BAIT.split("|")}
    assert stems <= {*ro.UNLETTERED_BASE, *ro.BAIT_EXTRA}


def test_replay_only_the_cheque_take_still_says_cheque():
    """R3: the sentence each recorded take would carry, from its own text (the recorded sentence cut out)."""
    said = {}
    for t in TAKES:
        rest = t["prompt"].replace(OLD, "")
        said[t["index"]] = "cheque" in ro.unlettered_for(rest)
    assert [k for k, v in said.items() if v] == [12]


def test_a_take_with_the_sentence_passes_p14():
    text = f"detailed_description: Enfield holds out the cheque. {ro.unlettered_for('the cheque')}"
    assert prompt_lint.p14_lettering("Enfield holds out the cheque.", text) == []
