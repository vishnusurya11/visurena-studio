"""A read-back describes A PICTURE. Replace the picture and it describes nothing.

MEASURED building episode 9. John Ferrier's bust was drawn with a black fur hat
baked into it, against the rule that a bust is bare-headed, and Lucy Ferrier's
with a bonnet. Both were redrawn bare-headed on the local GPU -- and
`cast_cards --check` went on reporting

    headgear: the text says none, the picture says other hat

for both, because `identity.traits` is a vision read-back of the picture that
was there BEFORE, stored on the row, and `--redraw` replaced the file and left
it. The gate was comparing the new words against the old photograph and had no
way to know.

Same shape as every other fault this week: a measurement kept past the world it
measured, whose staleness is invisible because a stale answer and a fresh one
look alike. The read-back is derived from the file, so it dies with the file.
"""
import sys

import pytest

from studio import cast_refs

sys.path.insert(0, "scripts/episode")


@pytest.fixture
def book(tmp_path):
    import json
    room = tmp_path / "refs" / "characters"
    room.mkdir(parents=True)
    (room / "char-someone.png").write_bytes(b"old picture")
    (tmp_path / "refs" / "refs.json").write_text(json.dumps({
        "book_id": "b", "palette": "p", "unbound": [],
        "refs": [{"ref_id": "char-someone", "kind": "character", "entity_id": "someone",
                  "name": "Someone", "physical": "A bare-headed person.",
                  "rel_path": "refs/characters/char-someone.png",
                  "identity": {"closest": "other", "differs": ["headgear"],
                               "traits": {"headgear": "other hat", "complexion": "fair"}}}],
    }), encoding="utf-8")
    return tmp_path


def test_a_redraw_clears_the_read_back_of_the_picture_it_replaced(book):
    import cast_bust

    cast_bust.draw(book, "someone", render=lambda *a, **k: a[-1], redraw=True)
    assert cast_refs.traits(cast_refs.row(book, "someone")) == {}


def test_a_draw_that_replaces_nothing_leaves_the_read_back_alone(book):
    """A bust already on disk is NOT redrawn without `--redraw`, and then the
    read-back still describes the picture that is there."""
    import cast_bust

    cast_bust.draw(book, "someone", render=lambda *a, **k: a[-1])
    assert cast_refs.traits(cast_refs.row(book, "someone"))["headgear"] == "other hat"


def test_the_superseded_copy_is_still_kept(book):
    import cast_bust

    cast_bust.draw(book, "someone", render=lambda *a, **k: a[-1], redraw=True)
    kept = list((book / "refs" / "characters" / ".superseded").glob("char-someone.*.png"))
    assert len(kept) == 1 and kept[0].read_bytes() == b"old picture"
