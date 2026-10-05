"""The Viewer's unit model (SPEC_v3, V03): sequences of shots, takes, grids,
masters and files computed from a tmp book -- every join one key, every missing
link said, never guessed."""
from __future__ import annotations

from pathlib import Path

import pytest

from studio.command_center import viewer_model as vm
from viewer_fixtures import CODEX, UNIT, make_book


@pytest.fixture
def home(tmp_path) -> Path:
    library, _ = make_book(tmp_path)
    return library / f"{CODEX}_a-book" / "episodes" / UNIT


@pytest.fixture
def U(home) -> dict:
    return vm.load(home, UNIT)


def test_unit_home_follows_the_unit_grammar():
    assert vm.unit_home("episode", "ep04") == "episodes/ep04"
    assert vm.unit_home("refs", "main") == "refs"


def test_kind_of_names_what_the_viewer_can_draw():
    assert [vm.kind_of(r) for r in ("a.PNG", "b.mp4", "c.wav", "d.jsonl", "e.txt", "f.log", "g.py")] == \
        ["image", "video", "audio", "doc", "text", "log", None]


def test_index_files_skips_pycache_and_unviewable_files(home):
    rels = [f["rel"] for f in vm.index_files(home)]
    assert "storyboard/shot_00.png" in rels and "drive_run01.log" in rels
    assert not any(r.endswith((".py", ".pyc")) for r in rels)


def test_index_files_marks_docs_under_the_cap_readable(home):
    F = {f["rel"]: f for f in vm.index_files(home)}
    assert F["plan.json"]["doc"] and not F["big.json"]["doc"] and not F["cut/master_r2v.mp4"]["doc"]


def test_index_files_stops_at_the_cap(home):
    assert len(vm.index_files(home, cap=3)) == 3


def test_read_doc_is_none_for_a_missing_or_broken_file(home, U):
    (home / "broken.json").write_text("{", encoding="utf-8")
    F = {f["rel"]: f for f in vm.index_files(home)}
    assert vm.read_doc(home, F, "broken.json") is None and vm.read_doc(home, F, "nope.json") is None


def test_eyes_sort_newest_first_and_carry_their_rel(U):
    assert U["eyes"]["panel"][0]["_rel"] == "storyboard/eye_aaaa1111.json"
    assert U["eyes"]["take"][0]["faults"][0]["where"] == "T02" and U["eyes"]["master"] == []


def test_joins_resolve_by_one_key(U):
    assert vm.card_of_shot(U, 1)["index"] == 0 and vm.card_of_shot(U, 9) is None
    assert vm.seg_of(U, 2)["start"] == 240
    assert vm.grid_of_shot(U, 2) == {"name": f"{UNIT}_grid_woods_3x1", "slot": 2,
                                     "rel": f"storyboard/grids/{UNIT}_grid_woods_3x1.png"}


def test_master_rel_is_the_newest_iteration_equal_to_master_r2v(U):
    assert vm.master_rel(U) == "cut/master_iter2.mp4"


def test_fails_of_lists_retired_attempts_newest_first(U):
    assert vm.fails_of(U, "T00") == [1] and vm.fails_of(U, "T02") == []


def test_shot_faults_split_plan_and_panel(U):
    assert [f["kind"] for f in vm.shot_faults(U, 0)["panel"]] == ["landmark"]
    assert [f["kind"] for f in vm.shot_faults(U, 1)["plan"]] == ["story"]


def test_shot_items_carry_four_stages(U):
    shots = vm.shot_items(U)
    assert [x["label"] for x in shots] == ["Shot 00", "Shot 01", "Shot 02"]
    assert [L["name"] for L in shots[0]["layers"]] == ["panel", "staged", "take", "master"]
    assert shots[0]["layers"][2]["rel"] == "takes/r2v/T00.mp4" and shots[0]["layers"][2]["poster_rel"] == "takes/work/content/T00_1.png"


def test_a_shot_in_the_master_carries_its_segment_in_seconds(U):
    seg = vm.shot_items(U)[2]["layers"][3]["seg"]
    assert seg == {"rel": "cut/master_iter2.mp4", "t0": 10.0, "t1": 15.0}


def test_a_held_still_is_said_on_the_shot(U):
    assert any(c["t"] == "held as a still" for c in vm.shot_items(U)[2]["chips"])


def test_a_missing_take_says_why(tmp_path):
    library, _ = make_book(tmp_path)
    U = vm.load(library / f"{CODEX}_a-book" / "episodes" / "ep05", "ep05")
    take = vm.shot_items(U)[0]["layers"][2]
    assert take["missing"] == "no take card" and vm.take_items(U) == []


def test_take_items_list_kept_then_failed_attempts(U):
    takes = vm.take_items(U)
    assert [t["label"] for t in takes] == ["T00", "T02"]
    assert [L["name"] for L in takes[0]["layers"]] == ["kept", "fail1"] and takes[0]["badge"] == "+1"


def test_take_items_flag_a_judged_fault(U):
    assert vm.take_items(U)[1]["flag"] and vm.take_items(U)[1]["chips"][0]["t"] == "⚑ lag"


def test_grid_items_carry_superseded_revisions(U):
    grid = vm.grid_items(U)[0]
    assert grid["shots"] == [0, 1, 2]
    assert [L["rel"] for L in grid["layers"]] == [f"storyboard/grids/{UNIT}_grid_woods_3x1.png",
                                                  f"storyboard/superseded/r1/{UNIT}_grid_woods_3x1.png"]


def test_master_items_fold_equal_iterations(U):
    masters = vm.master_items(U)
    assert [m["label"] for m in masters] == ["v2", "v1"]
    assert "master_r2v" in masters[0]["sub"] and masters[0]["judged"] and not masters[1]["judged"]


def test_file_items_put_the_known_docs_first_then_the_logs(U):
    files = vm.file_items(U, [{"rel": "_logs/x.log", "name": "x.log", "run": "x", "size": 3}])
    ids = [f["id"] for f in files]
    assert ids[0] == "plan.json" and "drive_run01.log" in ids and ids[-1] == "_logs/x.log"
    assert files[-1]["layers"][0]["kind"] == "log"


def test_sequences_are_the_five_tabs(U):
    seqs = vm.sequences(U, [])
    assert [s["id"] for s in seqs] == ["shots", "takes", "grids", "masters", "files"]
    assert seqs[1]["extra"] == "+1"


def test_run_logs_list_the_unit_runs_that_exist(tmp_path):
    _, logs = make_book(tmp_path)
    found = vm.run_logs(logs, CODEX, "episode", [f"{CODEX}__episode__20260926010203", "gone", None])
    assert [x["name"] for x in found] == [f"{CODEX}__episode__20260926010203.log"]
    assert found[0]["rel"].startswith("_logs/")


def test_clock_formats_in_the_given_zone():
    from datetime import timezone
    assert vm.clock(0, timezone.utc) == "00:00" and vm.day_clock(0, timezone.utc) == "1 Jan 00:00"


def test_short_formats():
    assert (vm.nn(3), vm.tk(12), vm.mmss(36.541667)) == ("03", "T12", "0:36.54")


def test_plan_shot_and_ran_by_index_find_by_index(U):
    assert vm.plan_shot(U, 2)["faces"] == ["captain"] and vm.plan_shot(U, 9) is None
    assert vm.ran_by_index(U, 0)["measured_seconds"] == 10.0 and vm.ran_by_index(U, 2) == {}


def test_still_of_and_has(U):
    assert vm.still_of(U, 2)["why"] == "cut" and vm.still_of(U, 0) is None
    assert vm.has(U, "plan.json") and not vm.has(U, "nope.json")


def test_grid_name_keeps_the_tag():
    assert vm.grid_name("ep17", {"setup": "steamer_forward", "cols": 3, "rows": 1, "tag": "a"}) == \
        "ep17_grid_steamer_forward_3x1_a"


def test_a_take_without_a_card_or_a_file_is_said(U):
    assert vm.take_layer(U, None, 5, "p")["missing"] == "no take card"
    assert vm.take_layer(U, {"index": 7}, 7, "p")["missing"].startswith("not rendered yet")


def test_master_layer_without_a_segment_says_so(tmp_path):
    library, _ = make_book(tmp_path)
    U = vm.load(library / f"{CODEX}_a-book" / "episodes" / "ep05", "ep05")
    assert vm.master_layer(U, 0, "p")["missing"] == "no master yet (assemble)"


def test_panel_layers_say_what_is_not_drawn(U):
    assert vm.panel_layers(U, 9, {})[0]["missing"] == "not drawn yet (panels)"


def test_shot_chips_and_take_chips(U):
    assert vm.shot_chips({"panel": [], "plan": []}, None) == []
    chips, flag = vm.take_chips(U, "T00", None)
    assert chips == [{"t": "EYE_TAKES ✓", "cls": "ok"}] and not flag


def test_take_layers_and_take_item(U):
    assert [L["name"] for L in vm.take_layers(U, "T02", {}, None)] == ["kept"]
    assert vm.take_item(U, {"index": 0, "shots": [0, 1]})["dur"] == "10.0s"


def test_fail_count_counts_every_retired_attempt(U):
    assert vm.fail_count(U) == "+1"


def test_grid_rels_put_the_layout_first(U):
    assert vm.grid_rels(U) == [f"storyboard/grids/{UNIT}_grid_woods_3x1.png"]


def test_grid_revisions_and_grid_item(U):
    assert vm.grid_revisions(U, f"{UNIT}_grid_woods_3x1")[0]["name"] == "r1"
    assert vm.grid_item(U, f"storyboard/grids/{UNIT}_grid_woods_3x1.png")["label"] == "woods 3×1"


def test_master_groups_and_master_poster(U):
    assert [g["also"] for g in vm.master_groups(U)] == [["master_r2v"], []]
    assert vm.master_poster(U) is None


def test_master_item_says_no_verdict_for_an_old_iteration(U):
    old = vm.master_groups(U)[1]
    assert vm.master_item(U, old, None)["chips"] == [{"t": "no verdict kept", "cls": ""}]


def test_ordered_docs_follow_the_reading_order(U):
    rels = [f["rel"] for f in vm.ordered_docs(U)]
    assert rels.index("plan.json") < rels.index("takes/r2v/prompts.json") < rels.index("learnings.jsonl")


def test_file_row_and_eye_time(home):
    assert vm.file_row(home / "plan.json", "plan.json")["kind"] == "doc"
    assert vm.eye_time({"reviewed_at": "b"}) == "b" and vm.eye_time({}) == ""


def test_load_eyes_and_load(home, U):
    F = {f["rel"]: f for f in vm.index_files(home)}
    assert len(vm.load_eyes(home, F)["panel"]) == 1 and U["plan"]["shots"][0]["index"] == 0


def test_plan_shots_tolerate_a_broken_plan():
    assert vm.plan_shots({"plan": None}) == [] and vm._list({"cards": {}}, "cards") == []


def test_unit_model_answers_files_logs_and_seqs(home):
    body = vm.unit_model(home, CODEX, "episode", UNIT, f"episodes/{UNIT}", [])
    assert body["home"] == f"episodes/{UNIT}" and len(body["seqs"]) == 5 and body["files"]


def test_size_reads_like_a_person():
    assert (vm.size(10), vm.size(2048), vm.size(3 * 1048576)) == ("10 B", "2.0 KB", "3.0 MB")
