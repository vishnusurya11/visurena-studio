"""studio/progress.py's reader (progress tracker spec §1): `fold()` turns the
progress event lines into the state the card draws.  v1 feeds it events
derived from the files a run already writes; v2 feeds it progress.jsonl.  The
shape is the same either way."""
from __future__ import annotations

import json

from studio import progress


def _ep16_replay() -> list[dict]:
    """A synthetic progress stream replaying ep16's shoot: 26 takes, 3 kept."""
    rows = json.loads((__import__("pathlib").Path(__file__).parent / "fixtures" / "progress"
                       / "ep16_shots.json").read_text(encoding="utf-8"))
    items = [[f"T{r['index']:02d}", r["frames"]] for r in rows]
    evs = [{"t": 1.0, "ev": "step", "step": "08", "name": "panels", "state": "skip"},
           {"t": 2.0, "ev": "step", "step": "09", "name": "shoot", "state": "start"},
           {"t": 3.0, "ev": "plan", "step": "09", "items": items, "kept": ["T00", "T01", "T02"]}]
    t = 3.0
    for r in rows[3:11]:
        t += r["render_s"]
        evs.append({"t": t, "ev": "item", "item": f"T{r['index']:02d}", "weight": r["frames"],
                    "secs": r["render_s"], "state": "done"})
    return evs


def test_read_skips_a_torn_last_line(tmp_path):
    path = tmp_path / "progress.jsonl"
    path.write_text(json.dumps({"t": 1, "ev": "step", "step": "02", "state": "start"}) + "\n{\"t\": 2, \"ev",
                    encoding="utf-8")
    assert [e["step"] for e in progress.read_events(path)] == ["02"]


def test_read_of_a_missing_file_is_empty(tmp_path):
    assert progress.read_events(tmp_path / "nope.jsonl") == []


def test_fold_gives_the_running_step_and_its_counts():
    state = progress.fold(_ep16_replay())
    assert state["step"] == "09" and state["steps"]["09"]["state"] == "start"
    assert state["steps"]["08"]["state"] == "skip"
    done, total, wd, wt = progress.counts(state)
    assert (done, total) == (11, 26)
    assert wt == sum(w for _, w in state["plan"]) and 0 < wd < wt


def test_a_plan_sets_the_total_including_kept():
    state = progress.fold([{"t": 1, "ev": "plan", "items": [["T00", 10], ["T01", 20]], "kept": ["T00"]}])
    assert progress.counts(state) == (1, 2, 10, 30)


def test_a_second_plan_is_a_retake_round_and_a_second_landing_is_a_retake():
    evs = [{"t": 1, "ev": "plan", "items": [["T00", 10], ["T01", 10]], "kept": []},
           {"t": 2, "ev": "item", "item": "T00", "weight": 10, "secs": 5, "state": "done"},
           {"t": 3, "ev": "item", "item": "T01", "weight": 10, "secs": 5, "state": "done"},
           {"t": 4, "ev": "plan", "items": [["T00", 10], ["T01", 10]], "kept": ["T00"]},
           {"t": 5, "ev": "item", "item": "T01", "weight": 10, "secs": 6, "state": "done"}]
    state = progress.fold(evs)
    assert progress.counts(state)[:2] == (2, 2)
    assert state["done"]["T01"] == [5, 6] and progress.item_state(state, "T01") == "retake"
    assert progress.item_state(state, "T00") == "landed"


def test_a_failed_item_and_a_round_and_the_end_are_kept():
    evs = [{"t": 1, "ev": "plan", "items": [["T00", 10]], "kept": []},
           {"t": 2, "ev": "item", "item": "T00", "state": "fail"},
           {"t": 3, "ev": "round", "gate": "PLAN", "measured": 6.0, "action": "keep_best", "terminal": True},
           {"t": 4, "ev": "end", "outcome": "completed"}]
    state = progress.fold(evs)
    assert progress.item_state(state, "T00") == "failed"
    assert state["rounds"][0]["terminal"] is True and state["outcome"] == "completed"
    assert state["t0"] == 1 and state["last_t"] == 4


def test_fold_of_nothing_is_an_empty_state():
    state = progress.fold([])
    assert state["step"] is None and progress.counts(state) == (0, 0, 0, 0)
