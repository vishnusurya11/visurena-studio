"""director_signoff.md carries a Flagged takes section read off flagged_takes.json (contract K7):
every take that shipped flagged with its seconds, its rows and its severity.  It is a section of
the page, never a stop: publish_lock is unchanged (no-human-input at publish, 2026-10-01)."""
from __future__ import annotations

from scripts.publish import signoff
from studio import episode_home, publish_lock
from tests.publish_fixtures import book_with, episode_with

ROWS = [{"take": 8, "shot": [8], "seconds_in_master": 4.0, "slowed": False, "rows": ["clones"],
         "notes": ["clones: two faces read as one man (facenet 0.943)"], "severity": "high"},
        {"take": 21, "shot": [21], "seconds_in_master": 5.25, "slowed": True, "rows": ["warp"],
         "notes": ["warp: the face is redrawn"], "severity": "normal"}]


def written(tmp_path, rows=ROWS):
    home, sha8 = episode_with(book_with(tmp_path))
    if rows is not None:
        episode_home.write_json(home / "takes" / "work" / "flagged_takes.json", rows)
    return home, sha8, signoff.write(home, sha8).read_text(encoding="utf-8")


def test_every_flagged_take_is_in_its_section(tmp_path):
    _home, _sha8, text = written(tmp_path)
    section = publish_lock.sections(text)["Flagged takes"]
    assert "2 flagged takes ship, 9.25 s" in section
    assert "T08: 4.0 s, high, clones" in section and "facenet 0.943" in section
    assert "T21: 5.25 s (slowed), normal, warp" in section


def test_no_file_says_none_recorded(tmp_path):
    _home, _sha8, text = written(tmp_path, rows=None)
    assert "none recorded" in publish_lock.sections(text)["Flagged takes"]


def test_flagged_takes_add_no_publish_stop(tmp_path):
    home, sha8, _text = written(tmp_path)
    assert publish_lock.signoff_stops(home, sha8) == []
