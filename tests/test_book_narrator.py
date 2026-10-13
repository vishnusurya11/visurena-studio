"""The book's narrator is decided once, before episode 1 (Jekyll ep01 review,
2026-10-13): a third-person book had none, G-SPEAKER refused `narrator` five
rounds running and listed the cast, and the writer took `henry_jekyll` -- the
wrong man, in the wrong person, chosen by nobody.  $0, no model."""
from __future__ import annotations

import json

import pytest

from studio import book_narrator as bn


def _plan(book, n: int, speakers: list[str], published: bool = True) -> None:
    home = book / "episodes" / f"ep{n:02d}"
    home.mkdir(parents=True)
    lines = [{"index": i, "kind": "narration", "speaker": s, "text": "x", "shot": 0} for i, s in enumerate(speakers)]
    (home / "plan.json").write_text(json.dumps({"lines": lines}), encoding="utf-8")
    if published:
        (home / "youtube.json").write_text("{}", encoding="utf-8")


def test_a_declared_narrator_is_read_from_the_book(tmp_path):
    bn.declare(tmp_path, bn.dedicated("a calm low storyteller", "third-person book"))
    got = bn.declared(tmp_path)
    assert got.speaker == bn.DEDICATED == "narrator" and got.person == "third" and not got.on_camera
    assert bn.narrator(tmp_path) == "narrator"


def test_a_book_with_nothing_declared_or_published_has_no_narrator(tmp_path):
    _plan(tmp_path, 1, ["henry_jekyll"], published=False)       # a signed-but-unshipped choice is no decision
    assert bn.declared(tmp_path) is None
    assert bn.narrator(tmp_path) == ""


def test_published_episodes_establish_the_narrator_they_share(tmp_path):
    _plan(tmp_path, 1, ["unnamed_first_person_narrator"])
    _plan(tmp_path, 2, ["unnamed_first_person_narrator", "curate"])   # WotW ep22: the curate tells a part
    assert bn.established(tmp_path) == "unnamed_first_person_narrator"
    assert bn.narrator(tmp_path) == "unnamed_first_person_narrator"


def test_the_declaration_outranks_what_was_published(tmp_path):
    _plan(tmp_path, 1, ["henry_jekyll"])
    bn.declare(tmp_path, bn.dedicated("calm", "why"))
    assert bn.narrator(tmp_path) == "narrator"


def test_an_unset_narrator_stops_and_never_lists_the_cast(tmp_path):
    with pytest.raises(SystemExit) as stop:
        bn.require(tmp_path)
    said = str(stop.value)
    assert "refs/narrator.json" in said and "before episode 1" in said
    assert "cast (" not in said


def test_require_returns_the_narrator_when_set(tmp_path):
    bn.declare(tmp_path, bn.dedicated("calm", "why"))
    assert bn.require(tmp_path) == "narrator"
