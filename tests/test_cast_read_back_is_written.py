"""The episode pipeline demanded a read-back it could not produce.

`cast_refs.bound` (2026-09-16) refuses a character whose row has no
`identity.traits` -- the vision read of the bust that `cast_cards --check`
compares the caption against. But the only writer of that field was the TRAILER
pipeline (`scripts/trailer/step_02_refs.py`); `--check` read it and never wrote
it, and `cast_bust --redraw` clears it. So every redrawn or episode-authored
character was unbound with no command that could bind it.

`cast_cards --read <who>` runs `studio.describe.describe` on the bust and stores
the traits on the row. It is the read the gate asks for, made by the pipeline
that asks for it.
"""
import json
import sys

import pytest

sys.path.insert(0, "scripts/episode")


class FakeCard:
    def model_dump(self):
        return {"figure": "man", "headgear": "none", "hair_colour": "grey", "build": "stout"}


@pytest.fixture
def book(tmp_path):
    room = tmp_path / "refs" / "characters"
    room.mkdir(parents=True)
    (room / "char-someone.png").write_bytes(b"bust")
    (tmp_path / "refs" / "refs.json").write_text(json.dumps({
        "book_id": "b", "palette": "p", "unbound": [],
        "refs": [{"ref_id": "char-someone", "kind": "character", "entity_id": "someone",
                  "name": "Someone", "physical": "A stout man.", "pronouns": "he",
                  "rel_path": "refs/characters/char-someone.png"}]}), encoding="utf-8")
    return tmp_path


def test_read_stores_the_busts_traits_on_the_row(book, monkeypatch):
    import cast_cards
    from studio import cast_refs

    monkeypatch.setattr(cast_cards.describe, "describe", lambda image, **k: FakeCard())
    cast_cards.read_back(book, "someone")
    assert cast_refs.traits(cast_refs.row(book, "someone"))["build"] == "stout"


def test_read_is_what_bound_was_missing(book, monkeypatch):
    import cast_cards
    from studio import cast_refs

    monkeypatch.setattr(cast_cards.describe, "describe", lambda image, **k: FakeCard())
    before = cast_refs.bound(book, "someone", "indoor")
    assert any("read-back" in why for why in before)
    cast_cards.read_back(book, "someone")
    after = cast_refs.bound(book, "someone", "indoor")
    assert not any("read-back" in why for why in after)


def test_read_refuses_a_missing_bust(book, monkeypatch):
    import cast_cards

    (book / "refs" / "characters" / "char-someone.png").unlink()
    with pytest.raises(SystemExit, match="no bust"):
        cast_cards.read_back(book, "someone")
