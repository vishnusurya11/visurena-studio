"""A12: G-REVEAL, shadow, with a hand-written Jekyll schedule (craft ruling 2026-10-21, wave 1).

The book withholds Hyde's face until ch2 list index 24 ("Mr. Hyde appeared to hesitate, and then, as"),
and ep01 lifted it three times: shot 0 widens "to show the small man's face", shot 9 "turns his pale face
up", shot 11 "lifts his chin" on a low angle with lamplight on his cheek.  A small pydantic `SeriesMap`
holds only `reveals`, in `series_map.json` (the book-root `series.json` already carries the owner's
aspect).  The gate faults a lift on a close or medium close of a scheduled entity before its episode
and paragraph; a book with no map is unreadable, never clean.  No agent, no stage.
Fixtures: tests/fixtures/craft (ep01 plan.json, ch_02.json, series_map.json).  No spend."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from pydantic import ValidationError

from scripts.episode import screenplay_replay as sr
from studio import screenplay_grammar as sg, series_map

CRAFT = Path(__file__).parent / "fixtures" / "craft"


def plan() -> dict:
    return json.loads((CRAFT / "episodes" / "ep01" / "plan.json").read_text(encoding="utf-8"))


def chapter(n: int) -> list[str]:
    doc = json.loads((CRAFT / "source" / "chapters" / f"ch_{n:02d}.json").read_text(encoding="utf-8"))
    return [p["text"] for p in doc["paragraphs"]]


def test_ep01_fires_on_exactly_shots_0_9_and_11():
    fires = sg.reveal_faults(plan(), chapter(1), series_map.load(CRAFT))
    assert [f.split(":")[0] for f in fires] == ["G-REVEAL shot 0", "G-REVEAL shot 9", "G-REVEAL shot 11"]
    assert "edward_hyde" in fires[0] and "episode 2" in fires[0]


def test_the_schedule_cites_its_paragraph_by_index_and_verbatim_words():
    reveal = series_map.load(CRAFT).reveals[0]
    assert (reveal.entity, reveal.episode, reveal.paragraph) == ("edward_hyde", 2, 24)
    assert " ".join(chapter(2)[24].split()[:8]) == reveal.words


def test_a_reveal_row_without_its_verbatim_words_is_invalid():
    with pytest.raises(ValidationError):
        series_map.SeriesMap(reveals=[{"entity": "edward_hyde", "episode": 2, "paragraph": 24, "words": ""}])


def test_in_the_reveal_episode_a_lift_after_the_paragraph_passes():
    doc = plan()
    doc["number"] = 2
    for shot in doc["shots"]:
        shot["source"] = [" ".join(chapter(2)[25].split()[:10])]       # every shot after index 24
    assert sg.reveal_faults(doc, chapter(2), series_map.load(CRAFT)) == []
    for shot in doc["shots"]:
        shot["source"] = [" ".join(chapter(2)[3].split()[:10])]        # every shot before it
    assert len(sg.reveal_faults(doc, chapter(2), series_map.load(CRAFT))) == 3


def test_a_book_with_no_map_is_unreadable_never_clean(tmp_path):
    assert series_map.load(tmp_path) is None
    home = tmp_path / "episodes" / "ep01"
    home.mkdir(parents=True)
    (home / "plan.json").write_text(json.dumps(plan()), encoding="utf-8")
    row = sr.replay(tmp_path, home / "plan.json")
    assert row["readable"]["reveal_early"] is False and row["fires"]["reveal_early"] is None
    shutil.copy(CRAFT / "series_map.json", tmp_path / "series_map.json")
    assert len(sr.replay(tmp_path, home / "plan.json")["fires"]["reveal_early"]) == 3


def test_the_map_is_not_series_json():
    assert series_map.FILE == "series_map.json"


def test_plan_check_prints_it_as_advice():
    import inspect
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "episode"))
    import plan_check
    assert "reveal_faults" in inspect.getsource(plan_check.shadow_rows)
