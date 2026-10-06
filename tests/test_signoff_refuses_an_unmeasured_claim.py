"""G-SIGNOFF-MEASURED: write() raises, listing every missing or stale input,
before a byte reaches disk -- an unmeasured claim is unrepresentable because
the module has no free-text parameter and refuses to render without its
sources (the typed sign-off satisfied by a six-frame glance is the family
fault, 2026-09-16)."""
from __future__ import annotations

import pytest

from scripts.episode import eye_review
from scripts.publish import signoff
from studio import episode_home
from tests.publish_fixtures import book_with, episode_with


def test_a_missing_eye_rubric_is_named(tmp_path):
    home, sha8 = episode_with(book_with(tmp_path))
    eye_review.rubric_path(home, sha8).unlink()
    with pytest.raises(SystemExit, match=f"eye_{sha8}.json"):
        signoff.write(home, sha8)


def test_a_qc_that_measured_other_bytes_is_refused(tmp_path):
    home, sha8 = episode_with(book_with(tmp_path))
    doc = episode_home.read_json(home / "qc_r2v.json")
    doc["sha8"] = "00000000"
    episode_home.write_json(home / "qc_r2v.json", doc)
    with pytest.raises(SystemExit, match="00000000"):
        signoff.write(home, sha8)


def test_an_unjudged_take_is_refused(tmp_path):
    home, sha8 = episode_with(book_with(tmp_path))
    (episode_home.takes_under(home, "r2v") / "T01.dq.json").unlink()
    with pytest.raises(SystemExit, match="T01"):
        signoff.write(home, sha8)


def test_a_refusal_writes_nothing(tmp_path):
    home, sha8 = episode_with(book_with(tmp_path))
    (home / "learnings.jsonl").unlink()
    with pytest.raises(SystemExit, match="learnings"):
        signoff.write(home, sha8)
    assert not (home / "review" / "director_signoff.md").exists()
