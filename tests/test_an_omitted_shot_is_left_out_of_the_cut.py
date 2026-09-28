"""A plan may omit a rendered shot from the cut without renumbering anything.

OWNER 2026-09-27 on ep13: the curate's flash-forward opening goes; the episode
starts on the chapter's first beat.  The shot's take, panel and verdicts stay
on disk and current; the timeline skips it and its lines, and everything
downstream (the cut, the sound, QC) follows the timeline.
"""
import json
from pathlib import Path

import pytest

from studio import episode_sound, episode_timeline, timeline_fresh
from studio.episode_spec import Episode

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "tests" / "fixtures" / "episodes" / "ep05_plan.json"


def plan(**extra) -> dict:
    return {**json.loads(PLAN.read_text(encoding="utf-8")), **extra}


def measured(doc: dict) -> dict[int, float]:
    return {l["index"]: 2.0 for l in doc["lines"]}


def test_an_omitted_shot_and_its_lines_are_not_placed():
    doc = plan(omit=[0])
    placed = episode_timeline.place(Episode.model_validate(doc), measured(doc))
    assert 0 not in [s["index"] for s in placed["shots"]]
    assert all(l["shot"] != 0 for l in placed["lines"])
    assert placed["shots"][0]["t_start"] == 0.0


def test_an_omit_that_names_no_shot_is_refused():
    with pytest.raises(ValueError):
        Episode.model_validate(plan(omit=[999]))


def test_omitting_a_shot_changes_the_fingerprint():
    a, b = Episode.model_validate(plan()), Episode.model_validate(plan(omit=[0]))
    assert timeline_fresh.fingerprint(a) != timeline_fresh.fingerprint(b)


def test_an_omitted_shot_lays_no_sound():
    doc = plan(omit=[0])
    doc["shots"][0]["sounds"] = [{"sound": "a gunshot", "at": 0.5, "seconds": 1.0}]
    assert all(c.shot != 0 for c in episode_sound.cues_of(Episode.model_validate(doc)))


def test_a_bed_span_on_an_omitted_shot_starts_at_the_next_shot_in_the_cut():
    from studio import episode_bed
    got = episode_bed.spans([{"from_shot": 0, "tone": "grave"}, {"from_shot": 3, "tone": "uneasy"}],
                            {1: 0.0, 2: 5.0, 3: 9.0}, 20.0)
    assert [(s.start, s.end, s.tone) for s in got] == [(0.0, 9.0, "grave"), (9.0, 20.0, "uneasy")]
