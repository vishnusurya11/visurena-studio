"""The voice is learned from THIS book's own prior episodes at runtime -- the
code tree names no book, and another book's descriptions never leak into the
brief.  series_tags is the intersection of the priors' tag lists, kept in the
newest prior's own order."""
from __future__ import annotations

from scripts.publish import metadata
from tests.publish_fixtures import PLAN, book_with, episode_with, prior_with, publish_seeded


def test_the_brief_carries_only_this_books_priors(tmp_path):
    a = book_with(tmp_path / "a", name="20990101010101_book-a")
    b = book_with(tmp_path / "b", name="20990101010102_book-b")
    publish_seeded(a)
    prior_with(a, 1, description="Alpha episode one on Horsell common.", tags=("alpha", "serial"))
    prior_with(b, 1, description="BETAONLY episode one.", tags=("beta", "serial"))
    episode_with(a, 2)
    prompt = metadata.brief(a, 2, PLAN, metadata.priors(a, 2))
    assert "Alpha episode one" in prompt
    assert "BETAONLY" not in prompt


def test_the_current_episode_is_never_its_own_prior(tmp_path):
    a = book_with(tmp_path)
    prior_with(a, 1, description="one")
    prior_with(a, 2, description="SELFDESCRIPTION")
    assert all(d["episode"] != 2 for d in metadata.priors(a, 2))


def test_series_tags_is_the_intersection_in_the_newest_priors_order(tmp_path):
    a = book_with(tmp_path)
    prior_with(a, 1, tags=("alpha", "serial", "public domain"))
    prior_with(a, 2, tags=("serial", "alpha", "newthing"))
    assert metadata.series_tags(metadata.priors(a, 3)) == ["serial", "alpha"]
