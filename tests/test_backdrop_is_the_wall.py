"""The backdrop test measures the wall, not the man's shoulders.

`backdrop_std` reads the two side strips of a reference sheet and refuses the
picture when they vary -- the fault it is written for is a bust drawn against a
room instead of one flat wall, because a `<Subject>` is `fully_preserved` and
every wall behind it travels into every panel that shows the man.

BUT A BUST FRAMES HEAD AND SHOULDERS, so the shoulders reach the side edges near
the BOTTOM of the frame by construction, and a broad man's do it sooner.
Measured on `char-john_rance.png`, a deliberately heavy-shouldered constable
drawn against a plainly flat grey seamless:

    top third      left std  7.3   right std  7.8
    middle         left std  5.0   right std 12.7
    bottom third   left std 38.8   right std 39.1      <- his tunic
    whole strip    left std 32.7   right std 39.2      -> REFUSED at 20.0

The wall is flat. The gate was reading the man and calling him a second room.

It is not only this picture: `char-unnamed_retired_marine_sergeant.png` (35.3,
and his record says "broad, thick-set, heavy square shoulders") and
`char-stamford.png` (28.6) carry the same complaint, and the fault scales with
how wide a character is -- which is a property of the person, not of the plate.

So the strip is read down to the SHOULDER LINE only.  A room behind the head is
still a room and still refused; a pair of shoulders is no longer a wall.
"""
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from studio import cast_agree as ca

CHARS = Path(__file__).resolve().parents[1] / \
    "library/20260822113400_a-study-in-scarlet/refs/characters"


def sheet(tmp_path: Path, wall: int | None, shoulders: bool, noise: float = 2.0) -> Path:
    """A square bust: a flat (or varied) wall, with or without dark shoulders
    rising into the bottom corners."""
    rng = np.random.default_rng(0)
    size = 512
    art = rng.normal(wall if wall is not None else 128, noise, size=(size, size))
    if wall is None:                       # a second wall: a hard vertical edge
        art[:, : size // 3] = rng.normal(60, noise, size=(size, size // 3))
    if shoulders:
        art[int(size * 0.62):, :] = rng.normal(30, 6, size=(size - int(size * 0.62), size))
    out = tmp_path / "bust.png"
    Image.fromarray(art.clip(0, 255).astype(np.uint8), mode="L").save(out)
    return out


def test_a_flat_wall_behind_a_narrow_bust_passes(tmp_path):
    assert ca.plain_backdrop(sheet(tmp_path, 128, shoulders=False))


def test_a_flat_wall_behind_BROAD_SHOULDERS_still_passes(tmp_path):
    """The whole point: the shoulders are the subject, not a second room."""
    assert ca.plain_backdrop(sheet(tmp_path, 128, shoulders=True))


def test_a_second_wall_behind_the_head_is_still_refused(tmp_path):
    """The fault the gate exists for survives: a room behind the head is a room."""
    assert not ca.plain_backdrop(sheet(tmp_path, None, shoulders=False))


def test_a_second_wall_is_refused_even_with_shoulders_in_frame(tmp_path):
    assert not ca.plain_backdrop(sheet(tmp_path, None, shoulders=True))


def test_the_strip_is_read_above_the_shoulder_line(tmp_path):
    """A number, not a vibe: the measured std of a flat wall with shoulders in it
    must be near the wall's own noise, not near the shoulders' contrast."""
    assert ca.backdrop_std(sheet(tmp_path, 128, shoulders=True)) < 10.0


@pytest.mark.skipif(not (CHARS / "char-john_rance.png").exists(), reason="the book is not on disk")
def test_the_real_constable_is_not_a_second_room():
    """Rance, drawn against a flat grey seamless, read 35.7 against a 20.0 ceiling
    purely because he is broad."""
    assert ca.plain_backdrop(CHARS / "char-john_rance.png")
