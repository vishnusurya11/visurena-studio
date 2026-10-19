"""A setup that stages a crowd must not switch the count check off for every
shot in it (retro 2026-10-19, P06).

ep01: `crowd_declared` returned True for any non-empty setup.crowd, so
`people_fault` tested only lookalikes >= 3 and the crowd that leaked into 14
extras-0 takes passed.  Now the crowd stands a count down only where the shot
declares extras > 0; a take is judged against its OWN panel's people.
"""
from __future__ import annotations

from types import SimpleNamespace

from studio import panel_content as pc, take_content as tc
from studio.panel_content import Seen

CROWD = SimpleNamespace(crowd="two distant figures strolling", described="a street at dusk")


def shot(extras=0, faces=1, declared=True, frame="Close on the man."):
    fields = {"frame", "faces"} | ({"extras"} if declared else set())
    return SimpleNamespace(frame=frame, at_rest="", size="medium", faces=["a"] * faces,
                           extras=extras, model_fields_set=fields)


def reads(*counts):
    return [Seen(people=n, hour="night") for n in counts]


def judged(counts, panel, extras=0, faces=1):
    return tc.take_faults(reads(*counts), planned=faces, crowd=pc.crowd_declared(shot(extras, faces), CROWD),
                          flat=False, night=False, physical="", frame="", extras=extras, panel_people=panel)


def test_a_setup_crowd_on_an_extras_zero_shot_is_not_a_declared_crowd():
    assert pc.crowd_declared(shot(extras=0), CROWD) is False


def test_extras_declared_over_a_crowd_setup_still_is():
    assert pc.crowd_declared(shot(extras=2), CROWD) is True


def test_a_plan_that_predates_extras_keeps_its_setup_crowd():
    assert pc.crowd_declared(shot(declared=False), CROWD) is True


def test_a_leaked_crowd_in_an_extras_zero_take_is_a_fault():
    got = judged([1, 3, 3], panel=1)
    assert any(f.startswith("crowd:") for f in got), got


def test_one_walk_in_is_an_unplanned_rise():
    got = judged([1, 1, 2], panel=1)
    assert any("rise" in f for f in got), got


def test_one_steady_extra_figure_is_inside_the_allowance():
    assert judged([2, 2, 2], panel=1) == []


def test_declared_extras_over_a_crowd_setup_pass_at_their_count():
    assert judged([2, 3, 4], panel=2, extras=2, faces=2) == []


def test_with_no_panel_row_the_declared_count_is_the_base():
    assert any(f.startswith("crowd:") for f in judged([1, 3, 3], panel=None))
    assert judged([2, 2, 2], panel=None) == []


def test_a_panel_that_held_more_people_widens_its_takes_base():
    assert judged([3, 3, 3], panel=3) == []
    assert any(f.startswith("crowd:") for f in judged([5, 5, 5], panel=3))


def test_the_panel_path_counts_the_extras_zero_shot_too():
    got = pc.judge_staged(Seen(people=3, hour="night"), shot(extras=0), CROWD, flat=False)
    assert any("figure(s)" in f for f in got), got


def test_the_panel_path_lets_a_declared_crowd_be():
    assert pc.judge_staged(Seen(people=3, hour="night"), shot(extras=2), CROWD, flat=False) == []


def test_the_runner_reads_the_shots_own_panel_row(tmp_path):
    from studio import episode_home
    from scripts.episode import take_content_check as tcc
    home = episode_home.home(tmp_path, 1) / "storyboard"
    home.mkdir(parents=True)
    (home / "panel_content.json").write_text('[{"shot": 2, "people": 3}, {"shot": 4, "people": 1}]', encoding="utf-8")
    assert tcc.panel_people_of(tmp_path, 1, 2) == 3
    assert tcc.panel_people_of(tmp_path, 1, 9) is None


def test_no_panel_file_means_no_row(tmp_path):
    from scripts.episode import take_content_check as tcc
    assert tcc.panel_people_of(tmp_path, 1, 2) is None


def _eval():
    import json
    from pathlib import Path
    path = Path(__file__).parent / "fixtures" / "dq_eval" / "kawajiri_ep01" / "manifest.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_ep01_replay_the_setup_crowd_stands_down_only_on_the_two_extras_shots():
    """P06 replay row: ep01's plan slice.  18 shots sit in a crowd-staging setup;
    the old rule called all 18 a declared crowd, the new one only shots 1 and 18."""
    plan = _eval()["plan"]
    shots = [s for s in plan["shots"] if plan["setups"][s["setup"]]["crowd"]]
    new = [s["index"] for s in shots if pc.crowd_declared(
        SimpleNamespace(frame="", at_rest="", extras=s["extras"], model_fields_set={"extras"}),
        SimpleNamespace(crowd=plan["setups"][s["setup"]]["crowd"]))]
    assert (len(shots), new) == (18, [1, 18])


def test_ep01_replay_the_28_clean_final_takes_raise_no_crowd_fault():
    """Precision on the clean population: the final takes' counts against their
    own panel rows and plan declarations (shoulder 0: no ep01 shot is over a shoulder)."""
    ev = _eval()
    shots = {s["index"]: s for s in ev["plan"]["shots"]}
    for t in ev["final_takes"]:
        s = shots[t["take"]]
        got = tc.crowd_fault(reads(t["people"], t["people"], t["people"]), s["faces"] + s["extras"],
                             ev["panel_people"].get(str(t["take"])))
        assert got is None, (t, got)


def test_ep01_replay_the_14_leaked_takes_are_all_refused_on_the_agents_eye_counts():
    """Recall of the RULE on the leak population, fed the agent's by-eye counts
    (the VL's own counts are the local replay's business): 14 of 14 leaks refused,
    the extras-1 take 27 passes."""
    ev = _eval()
    shots = {s["index"]: s for s in ev["plan"]["shots"]}
    hit = {}
    for t in (t for t in ev["takes"] if "eye_people" in t):
        s = shots[t["shot"]]
        hit[t["take"]] = tc.crowd_fault(reads(*t["eye_people"]), s["faces"] + s["extras"],
                                        ev["panel_people"].get(str(t["shot"]))) is not None
    leaks = {t["take"] for t in ev["takes"] if t["crowd_leak"]}
    assert {k for k, v in hit.items() if v} == leaks and len(leaks) == 14
