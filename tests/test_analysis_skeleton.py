"""Skeleton tests: registry-driven runner calls every step, in order, with the codex id."""

import analysis


def test_registry_loads_steps_in_file_order():
    steps = analysis.load_steps()
    assert [s.STEP_ID for s in steps] == sorted(s.STEP_ID for s in steps)
    assert len(steps) >= 6


def test_registry_ids_are_padded_and_match_modules():
    for entry, module in zip(analysis.load_registry()["steps"], analysis.load_steps()):
        assert entry["id"] == module.STEP_ID  # yaml and script agree
        for segment in entry["id"].split("_"):
            assert segment.isdigit() and len(segment) == 2  # fixed-width per EVENT_MODEL


def test_main_scans_codex_and_runs_steps_in_order(capsys, monkeypatch, tmp_path):
    from studio import db

    conn = db.get_connection(tmp_path / "t.db")
    db.init_db(conn)
    pending_id = db.insert_codex(conn, "Pending Book")
    for step in analysis.load_steps():
        monkeypatch.setattr(step, "run", lambda codex_id: None)  # never real work in tests
    monkeypatch.setattr(analysis, "RUN_UNTIL_STEP", "06")
    analysis.main(conn)
    out = capsys.readouterr().out
    positions = [out.index(f"step {s.STEP_ID}") for s in analysis.load_steps()]
    assert positions == sorted(positions)
    assert f"codex_id={pending_id}" in out


def test_main_skips_books_with_completed_analysis(capsys, monkeypatch, tmp_path):
    from studio import db

    conn = db.get_connection(tmp_path / "t.db")
    db.init_db(conn)
    done_id = db.insert_codex(conn, "Finished Book")
    db.add_event(conn, done_id, "analysis", analysis.FINAL_STEP_ID, "completed")
    analysis.main(conn)
    out = capsys.readouterr().out
    assert "0 book(s) pending" in out
    assert f"codex_id={done_id}" not in out


def test_run_until_step_stops_early(capsys, monkeypatch, tmp_path):
    from studio import db

    conn = db.get_connection(tmp_path / "t.db")
    db.init_db(conn)
    db.insert_codex(conn, "Book")
    for step in analysis.load_steps():
        monkeypatch.setattr(step, "run", lambda codex_id: None)
    monkeypatch.setattr(analysis, "RUN_UNTIL_STEP", "01")
    analysis.main(conn)
    out = capsys.readouterr().out
    assert "step 01" in out and "step 02" not in out
    assert "stopping after step 01" in out


# --- timeline time model (defects found 2026-08-23) ---


def test_scenes_in_one_chapter_get_distinct_times():
    from scripts.analysis import step_04_timeline as s04
    scenes = [{"chapter": 1, "scene": n, "track": "main", "time_of_day": "DAY",
               "story_day": 1, "time_evidence": [], "location_id": "x",
               "characters": []} for n in range(1, 5)]
    solved = s04.build_day_axis(scenes)
    times = [s["t"] for s in solved]
    assert len(set(times)) == len(times)          # no two scenes share an instant
    assert times == sorted(times)                 # telling order preserved


def test_absolute_dates_anchor_the_axis():
    from scripts.analysis import step_04_timeline as s04
    scenes = [
        {"chapter": 8, "scene": 1, "track": "flashback", "time_of_day": "DAY",
         "story_day": 1, "location_id": "x", "characters": [],
         "time_evidence": [{"type": "date", "text": "May 4th, 1847"}]},
        {"chapter": 12, "scene": 1, "track": "flashback", "time_of_day": "DAY",
         "story_day": 1, "location_id": "x", "characters": [],
         "time_evidence": [{"type": "date", "text": "August 4th, 1860"}]},
    ]
    solved = s04.build_day_axis(scenes)
    assert solved[0]["year"] == 1847
    assert solved[1]["year"] == 1860
    assert solved[1]["t"] > solved[0]["t"]


# --- time-of-day inference from surrounding scenes (owner request 2026-08-23) ---


def _scene(n, chapter=1, day=1, evidence=(), tod=None):
    return {"chapter": chapter, "scene": n, "track": "main", "day": day,
            "story_day": day, "location_id": "x", "characters": [],
            "time_of_day": tod or "UNKNOWN",
            "time_evidence": [{"type": "time_of_day", "text": t} for t in evidence]}


def test_gap_between_two_stated_times_is_interpolated():
    from scripts.analysis import step_04_timeline as s04
    scenes = [_scene(1, evidence=["in the morning"]), _scene(2), _scene(3),
              _scene(4, evidence=["that evening"])]
    s04.assign_time_of_day(scenes)
    hours = [s["hour"] for s in scenes]
    assert hours[0] == 9 and hours[-1] == 19
    assert hours[0] < hours[1] <= hours[2] < hours[-1]      # afternoon-ish, in order
    assert scenes[1]["clock_confidence"] == "inferred"


def test_scene_after_a_stated_time_advances_within_the_day():
    from scripts.analysis import step_04_timeline as s04
    scenes = [_scene(1, evidence=["at noon"]), _scene(2), _scene(3)]
    s04.assign_time_of_day(scenes)
    assert scenes[0]["hour"] == 12
    assert scenes[1]["hour"] > 12 and scenes[2]["hour"] > scenes[1]["hour"]


def test_scene_before_the_first_stated_time_is_inferred_earlier():
    from scripts.analysis import step_04_timeline as s04
    scenes = [_scene(1), _scene(2, evidence=["that evening"])]
    s04.assign_time_of_day(scenes)
    assert scenes[0]["hour"] is not None and scenes[0]["hour"] < 19


def test_inference_never_crosses_a_day_boundary():
    from scripts.analysis import step_04_timeline as s04
    scenes = [_scene(1, day=1, evidence=["at midnight"]), _scene(2, day=2)]
    s04.assign_time_of_day(scenes)
    assert scenes[1]["hour"] != 0            # a new day does not inherit midnight
