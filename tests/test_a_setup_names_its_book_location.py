"""A setup may name the BOOK's own location picture, and a references-only take
stages that instead of the episode's plate.

OWNER, 2026-09-17: "use the same location references
library/<book>/refs/locations" and "no need to generate the storyboard or ref
images, define all that in prompts". The book carries thirteen canonical
locations drawn once for the whole series -- 221B with its fireplace, two
windows and armchairs; 3 Lauriston Gardens; the police-station chamber -- and
the per-episode plate is a fresh drawing of the same room, which is why episode
14's rooms drifted from take to take.
"""
import sys

import pytest

from studio.episode_spec import Setup

sys.path.insert(0, "scripts/episode")


def a_setup(**kw):
    return Setup(described="Interior, inside the sitting-room of 221B Baker Street, a coal fire.", **kw)


def test_a_setup_may_name_a_location_and_defaults_to_none():
    assert a_setup().location == ""
    assert a_setup(location="221b_baker_street").location == "221b_baker_street"


def test_the_location_picture_is_the_book_wide_one(tmp_path):
    import takes_r2v

    book = tmp_path / "book"
    (book / "refs" / "locations").mkdir(parents=True)
    (book / "refs" / "locations" / "loc-221b_baker_street.png").write_bytes(b"x")
    got = takes_r2v.location_picture(book, tmp_path / "boards", a_setup(location="221b_baker_street"), "lab")
    assert got.name == "loc-221b_baker_street.png"


def test_a_setup_with_no_location_falls_back_to_the_episode_plate(tmp_path):
    import takes_r2v

    book = tmp_path / "book"
    boards = tmp_path / "boards"
    (boards / "plates").mkdir(parents=True)
    (boards / "plates" / "plate_lab.png").write_bytes(b"x")
    got = takes_r2v.location_picture(book, boards, a_setup(), "lab")
    assert got.name == "plate_lab.png"


def test_a_named_location_that_is_not_on_disk_is_refused(tmp_path):
    import takes_r2v

    with pytest.raises(SystemExit, match="loc-nowhere.png"):
        takes_r2v.location_picture(tmp_path / "book", tmp_path / "boards", a_setup(location="nowhere"), "lab")
