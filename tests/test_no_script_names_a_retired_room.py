"""Every reader must name a room that still exists.

The layout change (af91c0a) split one `frames/` folder into
`boards/{plates,cells,sheets,panels}`, moved `lines/` under `audio/` and
`shots_r2v/` under `takes/r2v/`.  `migrate_layout.py` moved the FILES and
repointed the records; it could not move the code, and five separate readers and
writers were left naming rooms that no longer exist:

  - `take_dq` gave `tv.measure` the boards root, so the take gate measured
    nothing at all and said every take was fine (ea0b8ec)
  - `foreign_names`' plate half resolved against `cells/` (ea0b8ec)
  - `drop_end_copies` looked in `boards/` and skipped every copy in silence,
    reporting `dropped_ends: []` (31a2cbe)
  - `seq_boards` wrote the sheet report to `boards/` while `qc` read it from
    `boards/sheets/` (3745f48)
  - `story.py`, the SERIES STATUS line, globs `home/"frames"` and `home/"lines"`
    and so reports the wrong stage -- on the very surface that is supposed to be
    the watchdog

Four of those five were silent, because a path that does not exist produces an
empty glob and an empty result reads as a clean one.

This test is the cheap standing guard: no script under scripts/episode/ or
studio/ may name a retired room.  `migrate_layout.py` is exempt -- translating
the old names is its whole job -- and so is a name used as a dict key or a
record field rather than a folder.
"""
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
RETIRED = ("frames", "shots_r2v", "shots_i2v")
EXEMPT = {"migrate_layout.py"}

FILES = sorted(p for p in list((ROOT / "scripts" / "episode").glob("*.py")) + list((ROOT / "studio").glob("*.py"))
               if p.name not in EXEMPT)


def joins(text: str) -> list[str]:
    """Every `... / "<name>"` path join in the file, by the name joined."""
    return re.findall(r'/\s*"([A-Za-z_0-9]+)"', text)


@pytest.mark.parametrize("path", FILES, ids=lambda p: p.name)
def test_no_path_join_names_a_retired_room(path):
    named = [n for n in joins(path.read_text(encoding="utf-8")) if n in RETIRED]
    assert not named, f"{path.name} joins a retired room: {sorted(set(named))}"


def test_the_guard_would_have_caught_the_ones_that_shipped():
    """Guard the guard: the shapes it is meant to see."""
    assert joins('home / "frames"') == ["frames"]
    assert joins('(home / "shots_r2v" / "prompts.json")') == ["shots_r2v"]


def test_a_record_field_called_shots_is_not_a_room():
    """`r.get("shots")` is a take's shot list and must not trip this."""
    assert joins('run = r.get("shots") or [index]') == []


def test_takes_under_addresses_an_engine_from_the_home(tmp_path):
    """The helper that exists so a reader holding only the episode home does not
    spell the room out by hand -- which is how `home / "shots_r2v"` outlived the
    folder it named."""
    from studio import episode_home
    assert episode_home.takes_under(tmp_path, "r2v") == tmp_path / "takes" / "r2v"


def test_takes_under_agrees_with_takes_dir(tmp_path):
    from studio import episode_home
    want = episode_home.takes_dir(tmp_path, 4, "r2v")
    assert episode_home.takes_under(episode_home.home(tmp_path, 4), "r2v") == want
