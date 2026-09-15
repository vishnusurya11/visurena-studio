r"""`videos.update` with `part=snippet` REPLACES the snippet, it does not merge.

This is the documented behaviour and the reason a retitle is dangerous: send
`{"snippet": {"title": ...}}` and YouTube accepts it, returns 200, and the
video's description, tags and category are gone. On five public episodes that is
five descriptions written by hand and not recoverable from this repo -- the
`youtube.json` files hold them, but nothing checks they are in sync with what is
live, and `categoryId` is not in them at all.

So the new snippet is the LIVE one with one field changed, read back from
`videos.list` in the same run. Not from `youtube.json`, which is what the upload
*intended*; not from a constant. From the video as it actually stands.

`categoryId` is separately required on every `part=snippet` update -- omit it and
the call fails with `invalidCategoryId`, which at least fails loudly. Title and
description are the ones that fail silently by succeeding.
"""
import pytest

from scripts.publish.youtube_retitle import restitled

LIVE = {"title": '"What John Rance Had to Tell" — A Study in Scarlet Ep.4',
        "description": "Chapter four of A Study in Scarlet.\n\nAI-generated.",
        "tags": ["sherlock holmes", "audiobook"],
        "categoryId": "1",
        "channelTitle": "The Keeper's Lantern",
        "publishedAt": "2026-09-14T07:28:05Z"}


def test_the_title_is_the_new_one():
    got = restitled(LIVE, "Sherlock Holmes: A Study in Scarlet — Ep 04/14 — \"What John Rance Had to Tell\"")
    assert got["title"].startswith("Sherlock Holmes:")


def test_the_description_survives():
    got = restitled(LIVE, "new")
    assert got["description"] == LIVE["description"]


def test_the_tags_survive():
    got = restitled(LIVE, "new")
    assert got["tags"] == LIVE["tags"]


def test_the_category_survives():
    """Omitting it is an `invalidCategoryId` failure, not a silent loss."""
    got = restitled(LIVE, "new")
    assert got["categoryId"] == "1"


def test_read_only_fields_are_not_sent_back():
    """`channelTitle` and `publishedAt` are set by YouTube; echoing them is at
    best ignored and at worst an error."""
    got = restitled(LIVE, "new")
    assert "channelTitle" not in got and "publishedAt" not in got


def test_a_snippet_with_no_category_is_refused():
    """Better to stop than to send an update that strips it."""
    with pytest.raises(ValueError, match="categoryId"):
        restitled({"title": "t", "description": "d"}, "new")


def test_a_video_that_already_has_the_title_is_left_alone():
    same = dict(LIVE, title="Sherlock Holmes: A Study in Scarlet — Ep 04/14 — \"x\"")
    assert restitled(same, same["title"]) is None


def test_the_source_snippet_is_not_mutated():
    before = dict(LIVE)
    restitled(LIVE, "new")
    assert LIVE == before
