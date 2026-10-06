"""The generated sign-off clears studio/publish_lock.signoff_stops BY
CONSTRUCTION -- the sha8 in the header, the four SECTIONS each written -- and
every number it prints was measured in one of its inputs.  The lock itself is
unchanged; only the file that satisfies it stops being typed."""
from __future__ import annotations

from scripts.publish import signoff
from studio import publish_lock
from tests.publish_fixtures import book_with, episode_with


def test_the_rendered_signoff_clears_signoff_stops(tmp_path):
    home, sha8 = episode_with(book_with(tmp_path))
    path = signoff.write(home, sha8)
    assert publish_lock.signoff_stops(home, sha8) == []
    assert sha8 in path.read_text(encoding="utf-8")


def test_every_number_printed_was_measured_in_an_input(tmp_path):
    home, sha8 = episode_with(book_with(tmp_path))
    text = signoff.write(home, sha8).read_text(encoding="utf-8")
    for measured in ("120.5", "118.0", "-14.2", "-1.3", "4.7", "88.0", "0.31"):
        assert measured in text, f"{measured} came from an input file and must be printed"


def test_the_signed_line_names_the_generator_and_its_inputs(tmp_path):
    home, sha8 = episode_with(book_with(tmp_path))
    text = signoff.write(home, sha8).read_text(encoding="utf-8")
    assert f"Signed: judge:signoff@v1 from eye_{sha8}.json, qc_r2v.json, " \
           f"2 dq/content reports, learnings.jsonl" in text
