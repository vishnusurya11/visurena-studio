"""R5 -- a wardrobe state that promises clothes must have a picture that shows them.

`cast_agree.check` walked `cast_refs.STATES` and measured the card for each state
`if card:` -- so a state with a written wardrobe line and NO card on disk was
skipped in silence.  That silence is where three parts of this book drifted apart
without one gate noticing:

  1. `Setup.state` calls the cab, Audley Court and the Lauriston gate `outdoor`
  2. `wardrobe["outdoor"]` promises Watson "wears the brown bowler hat squarely
     on his head"
  3. no `char-john_watson_outdoor.png` was ever drawn -- only its .prompt.txt

so `cast_sheet` falls through to the BUST, which is bare-headed by rule, and the
reference that actually reaches the drawer shows no hat.  The three disagree, and
the only reason nothing looks wrong in episode 4 is that the wardrobe line
reaches neither the sheet prompt nor the take prompt: the machinery is inert.
Connect any one of the three and the words contradict the picture (measured
2026-09-13 -- that is the bug that put Holmes in a `_bench` muffler through two
paid sheets of episode 3).

A promise nobody can keep should not be written down.  Either draw the card or
delete the line.
"""
import json
from pathlib import Path

from studio.cast_agree import promise_complaints


def book_with(tmp_path: Path, row: dict, files: tuple[str, ...] = ()) -> Path:
    (tmp_path / "refs" / "characters").mkdir(parents=True)
    (tmp_path / "refs" / "refs.json").write_text(json.dumps({"refs": [row]}), encoding="utf-8")
    for f in files:
        (tmp_path / "refs" / "characters" / f).write_bytes(b"")
    return tmp_path


ROW = {"ref_id": "char-x", "kind": "character", "entity_id": "x", "name": "X",
       "physical": "A man.", "rel_path": "refs/characters/char-x.png"}


def test_a_promise_with_no_picture_is_named(tmp_path):
    row = dict(ROW, wardrobe={"outdoor": "wears the brown bowler hat squarely on his head"})
    out = promise_complaints(book_with(tmp_path, row), "x")
    assert len(out) == 1 and "outdoor" in out[0] and "bowler" in out[0]


def test_it_says_which_picture_will_be_used_instead(tmp_path):
    """The complaint has to be actionable: the bust is what actually gets passed."""
    row = dict(ROW, wardrobe={"outdoor": "wears the brown bowler hat"})
    assert "bust" in promise_complaints(book_with(tmp_path, row), "x")[0]


def test_a_promise_with_its_picture_is_silent(tmp_path):
    row = dict(ROW, wardrobe={"outdoor": "wears the brown bowler hat"},
               cards={"outdoor": "refs/characters/char-x_outdoor.png"})
    book = book_with(tmp_path, row, ("char-x_outdoor.png",))
    assert promise_complaints(book, "x") == []


def test_a_card_found_by_its_conventional_name_counts(tmp_path):
    """`cast_refs.card` falls back to `char-<who>_<state>.png`; so does this."""
    row = dict(ROW, wardrobe={"indoor": "is bare-headed"})
    book = book_with(tmp_path, row, ("char-x_indoor.png",))
    assert promise_complaints(book, "x") == []


def test_a_row_named_card_that_is_not_on_disk_is_a_promise_too(tmp_path):
    row = dict(ROW, wardrobe={"indoor": "is bare-headed"},
               cards={"indoor": "refs/characters/char-x_indoor.png"})
    assert promise_complaints(book_with(tmp_path, row), "x")


def test_no_wardrobe_at_all_is_silent(tmp_path):
    assert promise_complaints(book_with(tmp_path, dict(ROW)), "x") == []


def test_an_empty_wardrobe_line_promises_nothing(tmp_path):
    row = dict(ROW, wardrobe={"outdoor": "   "})
    assert promise_complaints(book_with(tmp_path, row), "x") == []


def test_a_card_with_no_wardrobe_line_is_a_picture_nobody_describes(tmp_path):
    """The converse hole: a drawn card the prompt can never mention."""
    row = dict(ROW, wardrobe={"indoor": "is bare-headed"})
    book = book_with(tmp_path, row, ("char-x_indoor.png", "char-x_outdoor.png"))
    out = promise_complaints(book, "x")
    assert len(out) == 1 and "outdoor" in out[0] and "no wardrobe line" in out[0]


def test_both_states_can_complain_at_once(tmp_path):
    row = dict(ROW, wardrobe={"outdoor": "wears a hat"})
    book = book_with(tmp_path, row, ("char-x_indoor.png",))
    assert len(promise_complaints(book, "x")) == 2


def test_the_gate_runs_it(tmp_path):
    """R5 is part of `check`, not a function nobody calls."""
    import inspect

    from studio import cast_agree
    assert "promise_complaints" in inspect.getsource(cast_agree.check)
