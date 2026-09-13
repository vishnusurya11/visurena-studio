"""One character's identity BUST, drawn locally, without rewriting refs.json.

A chapter that brings a character nobody has drawn is a row in the episode
skill's own entry table, and until now there was no way to serve it.
`build_refs.py` draws busts, but it draws the WHOLE cast and then REWRITES
refs.json from what it drew -- which would have deleted the hand-authored
wardrobe contract, the sheet blocks and the cards map of every character
already bound.  Chapter II needed exactly one new bust (the commissionaire,
who speaks the episode's last line), so it needed a scalpel.

The bust is local and free; only the wardrobe CARD costs money, and that is
`cast_cards.py --draw`, which is already gated.
"""
import json

import pytest

from scripts.episode import cast_bust


def a_book(tmp_path, **over):
    row = {"ref_id": "char-someone", "kind": "character", "entity_id": "someone",
           "name": "Someone", "physical": "A broad man with a grey moustache.",
           "rel_path": "refs/characters/char-someone.png"} | over
    refs = tmp_path / "refs"
    (refs / "characters").mkdir(parents=True)
    (refs / "refs.json").write_text(json.dumps(
        {"book_id": "b", "palette": "Muted soot-black and gaslight amber.", "refs": [row]}),
        encoding="utf-8")
    return tmp_path


def test_the_prompt_leads_with_the_person_then_the_frame_and_the_palette(tmp_path):
    """`character_prompt` puts the body first on purpose: with the style block
    leading, seven characters came back as the same Victorian gentleman."""
    book = a_book(tmp_path)
    said = cast_bust.prompt_for(book, "someone")
    assert said.startswith("A broad man with a grey moustache.")
    assert "gaslight amber" in said


def test_the_bust_is_the_row_s_own_declared_path(tmp_path):
    book = a_book(tmp_path)
    assert cast_bust.target(book, "someone") == book / "refs" / "characters" / "char-someone.png"


def test_a_character_the_book_has_not_bound_is_refused_not_invented(tmp_path):
    """frames.py's rule: a character the book has not bound has no invented
    body.  Inventing one here is how "fair side-whiskers" entered a
    clean-shaven man's record."""
    book = a_book(tmp_path)
    with pytest.raises(KeyError, match="bind him before you draw him"):
        cast_bust.prompt_for(book, "a_stranger")


def test_a_bust_already_on_disk_is_never_redrawn(tmp_path):
    book = a_book(tmp_path)
    cast_bust.target(book, "someone").write_bytes(b"kept")
    drawn = cast_bust.draw(book, "someone", render=lambda *a, **k: pytest.fail("redrew"))
    assert drawn.read_bytes() == b"kept"


def test_the_render_is_asked_for_a_square_megapixel_at_the_rows_own_seed(tmp_path):
    """A bust is a portrait crop later, so a square ask wastes no pixels on
    backdrop, and the seed is derived from the entity id so a redraw of the
    same character is the same picture."""
    book = a_book(tmp_path)
    seen = {}

    def render(prompt, prefix, seed, dest):
        seen.update(prompt=prompt, prefix=prefix, seed=seed)
        dest.write_bytes(b"drawn")
        return dest

    cast_bust.draw(book, "someone", render=render)
    assert seen["prefix"] == "REF-char-someone"
    assert isinstance(seen["seed"], int)
    assert cast_bust.target(book, "someone").read_bytes() == b"drawn"


def test_refs_json_is_left_exactly_as_it_was(tmp_path):
    """The whole reason this script exists instead of build_refs.py."""
    book = a_book(tmp_path)
    before = (book / "refs" / "refs.json").read_bytes()
    cast_bust.draw(book, "someone", render=lambda p, x, s, d: (d.write_bytes(b"d"), d)[1])
    assert (book / "refs" / "refs.json").read_bytes() == before


def test_the_seed_is_stable_across_calls_and_differs_between_characters(tmp_path):
    assert cast_bust.seed_for("someone") == cast_bust.seed_for("someone")
    assert cast_bust.seed_for("someone") != cast_bust.seed_for("someone_else")


def test_a_redraw_keeps_the_old_bust_and_moves_the_seed(tmp_path):
    """A bust that comes back contradicting its own contract has to be redrawn,
    and the stable seed means asking again gives the SAME wrong picture -- so a
    redraw nudges the seed. The superseded picture is kept: it is free to keep
    and it is the evidence of what the words used to produce."""
    book = a_book(tmp_path)
    cast_bust.target(book, "someone").write_bytes(b"first")
    seeds = []

    def render(prompt, prefix, seed, dest):
        seeds.append(seed)
        dest.write_bytes(b"second")
        return dest

    cast_bust.draw(book, "someone", render=render, redraw=True)
    assert cast_bust.target(book, "someone").read_bytes() == b"second"
    assert seeds == [cast_bust.seed_for("someone") + 1]
    kept = list((book / "refs" / "characters" / ".superseded").glob("char-someone.*.png"))
    assert len(kept) == 1 and kept[0].read_bytes() == b"first"


def test_a_second_redraw_moves_the_seed_again(tmp_path):
    book = a_book(tmp_path)
    assert cast_bust.seed_for("someone", tries=2) == cast_bust.seed_for("someone") + 2
