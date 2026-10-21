"""Every gate added since 2026-10-14, replayed on delivered records (2026-10-21_ep02_proof DESIGN 4.6, P6).

scripts/proof/gates_under_test.yaml names each gate with its dotted callable, the reader that turns a
frozen delivered episode into the callable's inputs, and the date and commit it landed.  The replay
counts refusals over n readable units per gate, counts unreadable units apart, and lists refusals
confirmed as true faults, refusals an owner ruling already explains, and refusals no one has ruled on,
apart.  A refusal is false only when an owner ruled it so.  Fixtures are frozen with regress_delivered's
freeze into NEW tests/fixtures/delivered/<book>_<ep>/ folders (Jekyll's ep01 as jekyll_ep01; the older
ep01 fixture is the regress baseline's and is read, never written), every absolute path made relative."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.episode import regress_delivered as rd
from scripts.proof import gate_replay as gr

DESIGN_4_6 = {"G-STANDING", "G-META-CREDIT", "BRIEF-WITHHOLD-FACE", "ADVISORY-WORDING", "A28-TINY-FACE",
              "OUTSIDE-UNREAD", "FACE-LIST", "MASTER-EYE-KEY", "G-HOLE-SLACK", "G-CROWD-ORPHAN", "L28-STYLE-LIGHT",
              "LAUNCH-DRY-CHECK"}


def put(root: Path, rel: str, doc) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(doc if isinstance(doc, str) else json.dumps(doc), encoding="utf-8")
    return path


def test_the_spec_names_every_design_4_6_gate_since_2026_10_14_and_each_callable_resolves():
    spec = gr.load_spec()
    gates = {g["id"]: g for g in spec["gates"]}
    assert set(gates) == DESIGN_4_6
    for g in gates.values():
        assert g["since"] >= "2026-10-14" and g["commit"] and g["question"] in ("Q6", "Q8")
        if g.get("reader"):
            assert callable(gr.resolve(g["callable"])) and g["reader"] in gr.READERS
        else:
            assert g["why_not_replayed"]


def test_the_spec_names_27_wotw_14_scarlet_and_jekyll_ep01_each_frozen_in_its_own_folder():
    names = [name for name, _, _ in gr.episodes(gr.load_spec())]
    assert sum(n.startswith("wotw_") for n in names) == 27 and sum(n.startswith("scarlet_") for n in names) == 14
    assert "jekyll_ep01" in names and "ep01" not in names and len(names) == 42
    assert all((rd.FIXTURES / n).is_dir() for n in names)


def test_a_new_fixture_name_is_book_and_episode_and_never_an_existing_folder(tmp_path):
    assert gr.fixture_name("wotw", 5) == "wotw_ep05" and gr.fixture_name("jekyll", 1) == "jekyll_ep01"
    with pytest.raises(ValueError):
        gr.fixture_name("dracula", 1)
    (tmp_path / "wotw_ep05").mkdir()
    with pytest.raises(FileExistsError):
        gr.freeze(tmp_path / "src_book" / "episodes" / "ep05", tmp_path / "src_book", tmp_path / "wotw_ep05")


def test_freeze_copies_the_deciders_records_the_gate_inputs_and_the_books_standing_file(tmp_path):
    book = tmp_path / "book"
    home = book / "episodes" / "ep05"
    put(home, "plan.json", {"shots": []})
    put(home, "youtube.json", {"description": "x"})
    put(home, "takes/r2v/shots.json", [])
    put(home, "takes/r2v/T00.dq.json", {"take_sha8": "x"})
    (home / "takes" / "r2v" / "T00.mp4").write_bytes(b"take")
    put(book, "publish/standing.json", {"kind": "publish"})
    gr.freeze(home, book, tmp_path / "wotw_ep05")
    out = tmp_path / "wotw_ep05"
    assert (out / rd.STAT).is_file() and (out / "takes/r2v/T00.dq.json").is_file()
    assert (out / "plan.json").is_file() and (out / "youtube.json").is_file()
    assert (out / gr.BOOK_DIR / "publish/standing.json").is_file()
    assert not list(out.rglob("*.mp4"))


def standing_fixture(tmp_path: Path, doc) -> Path:
    fx = tmp_path / "wotw_ep05"
    if doc is not None:
        put(fx, f"{gr.BOOK_DIR}/publish/standing.json", doc)
    fx.mkdir(parents=True, exist_ok=True)
    return fx


def test_g_standing_refuses_an_unlisted_episode_and_passes_a_listed_one(tmp_path):
    ok = gr.resolve("studio.standing_approval:ok")
    base = {"kind": "publish", "decision": "2026-10-01-no-human-input-at-publish", "by": "owner"}
    assert gr.standing(standing_fixture(tmp_path / "a", base), ok)[0]["verdict"] == "refused"
    assert gr.standing(standing_fixture(tmp_path / "b", {**base, "episodes": [5]}), ok)[0]["verdict"] == "passed"
    assert gr.standing(standing_fixture(tmp_path / "c", None), ok)[0]["verdict"] == "unread"


def test_g_meta_credit_refuses_empty_quotes_and_a_missing_youtube_record_is_unread(tmp_path):
    faults = gr.resolve("scripts.publish.metadata:credit_faults")
    put(tmp_path / "a", "youtube.json", {"description": 'Chapter STORY OF THE DOOR of Part One, "", in the public domain.'})
    put(tmp_path / "b", "youtube.json", {"description": "Chapter I of Book One, \"Under Foot\", in the public domain."})
    (tmp_path / "c").mkdir()
    assert [gr.credit(tmp_path / k, faults)[0]["verdict"] for k in "abc"] == ["refused", "passed", "unread"]


def test_an_unread_outside_measure_on_a_kept_paste_is_a_refusal(tmp_path):
    refusal = gr.resolve("studio.face_refine:outside_refusal")
    put(tmp_path, "takes/r2v/refine.json", {"T05": {"people": [{"who": "a", "kept": True, "measures": {"outside": None}},
                                                               {"who": "b", "kept": True, "measures": {"outside": 0.0}},
                                                               {"who": "c", "kept": False, "measures": {}}]}})
    said = gr.outside(tmp_path, refusal)
    assert [(r["unit"], r["verdict"]) for r in said] == [("T05 a", "refused"), ("T05 b", "passed")]


def test_the_a28_column_flags_a_panel_face_under_100_px(tmp_path):
    record = gr.resolve("studio.panel_dq:tiny_face_record")
    put(tmp_path, "storyboard/panel_dq.json", [{"shot": 0, "face_h": 0.1}, {"shot": 1, "face_h": 0.2}, {"shot": 2}])
    assert [r["verdict"] for r in gr.tiny_face(tmp_path, record)] == ["refused", "passed"]


def test_g_hole_reads_the_measured_timeline_at_the_gates_slack(tmp_path):
    holes = gr.resolve("studio.speech_gap:holes")
    put(tmp_path, "placed.json", {"duration_s": 20.0, "shots": [{"index": 0, "t_start": 0, "t_end": 20}],
                                  "lines": [{"at": 0.0, "seconds": 2.0}, {"at": 7.6, "seconds": 12.4}]})
    said = gr.hole(tmp_path, holes)
    assert said[0]["verdict"] == "refused" and "5.60" in said[0]["why"]


def test_g_crowd_orphan_refuses_a_crowd_no_shot_draws(tmp_path):
    faults = gr.resolve("studio.plan_gates:orphan_crowd_faults")
    put(tmp_path, "plan.json", {"setups": {"inn": {"crowd": "a dozen drinkers"}, "road": {"crowd": ""}},
                                "shots": [{"index": 0, "setup": "inn", "size": "close"},
                                          {"index": 1, "setup": "road", "size": "wide"}]})
    said = gr.orphan_crowd(tmp_path, faults)
    assert [(r["unit"], r["verdict"]) for r in said] == [("setup inn", "refused"), ("setup road", "passed")]


def test_l28_refuses_a_sun_in_a_night_setups_style_line(tmp_path):
    lint = gr.resolve("studio.episode_ref_official:l28_style_light")
    prompt = "subject_definitions:\nx\n\ndetailed_description:\nInk, low sun from the west.\n[Shot 1] a door."
    put(tmp_path, "plan.json", {"setups": {"door": {"described": "the door at night"}, "day": {"described": "noon"}}})
    put(tmp_path, "takes/r2v/shots.json", [{"index": 0, "setup": "door", "prompt": prompt},
                                           {"index": 1, "setup": "day", "prompt": prompt}])
    assert [r["verdict"] for r in gr.style_light(tmp_path, lint)] == ["refused", "passed"]


def test_the_advisory_wording_counts_a_demoted_row_still_printing_hard(tmp_path):
    note = gr.resolve("studio.stillness:advisory_note")
    rows = [{"name": "frozen-whole", "ok": False, "hard": False, "note": "90% static, run 4s HARD: the whole frame stands still"},
            {"name": "frozen-whole", "ok": False, "hard": False, "note": "90% static (locked on the grammar, advisory)"}]
    put(tmp_path, "takes/r2v/T00.dq.json", {"gates": rows})
    assert [r["verdict"] for r in gr.wording(tmp_path, note)] == ["refused", "passed"]


def test_the_face_list_lists_a_soft_unpasted_face(tmp_path):
    listed = gr.resolve("studio.face_refine:face_list")
    put(tmp_path, "plan.json", {"shots": [{"index": 0, "size": "wide"}]})
    put(tmp_path, "takes/r2v/prompts.json", [{"index": 0, "shots": [0], "faces": ["a"]}])
    put(tmp_path, "takes/r2v/T00.dq.json", {"measures": {"warp": {"tracks": [{"min_px": 50.0}]}}})
    put(tmp_path, rd.STAT, {"files": {}, "kept": {"takes/r2v/T00.mp4": {"sha8": "aa"}}, "draws": {}, "eye": ""})
    assert [(r["unit"], r["verdict"]) for r in gr.face_list(tmp_path, listed)] == [("T00", "refused")]


def test_the_launch_dry_check_on_the_frozen_ep01_matches_its_committed_baseline():
    fixture = rd.FIXTURES / "ep01"
    said = gr.dry_check(fixture, gr.resolve("scripts.episode.regress_delivered:replay"))
    held = rd.read_baseline(fixture)["rows"]
    assert len(said) == len(held)
    assert sum(r["verdict"] == "refused" for r in said) == sum(not v["held"].startswith("keep") for v in held.values())


def test_the_tally_counts_unread_apart_and_a_refusal_is_false_only_by_an_owner_ruling():
    items = [{"unit": "a", "verdict": "refused"}, {"unit": "b", "verdict": "refused"}, {"unit": "c", "verdict": "passed"},
             {"unit": "d", "verdict": "unread"}]
    said = gr.tally(items, confirmed=[{"unit": "b", "source": "owner 2026-10-20"}])
    assert (said["n"], said["refused"], said["unread"], said["unruled"], said["ruled_false"]) == (3, 2, 1, 1, 0)
    assert said["confirmed"] == ["b"] and "false_refusals" not in said
    ruled = gr.tally(items, confirmed=[], ruled_false=[{"unit": "a", "source": "owner 2026-10-22"}])
    assert (ruled["ruled_false"], ruled["unruled"]) == (1, 1)


def test_refusals_an_owner_ruling_explains_are_expected_never_false_and_the_row_needs_none_unruled():
    items = [{"unit": "wotw_ep01 episode", "verdict": "refused"}, {"unit": "jekyll_ep01 episode", "verdict": "passed"}]
    rule = {"why": "the file lists no WotW episode", "source": "docs/DECISIONS.md 2026-10-20"}
    said = gr.tally(items, confirmed=[], expected=rule)
    assert (said["expected"], said["unruled"], said["ruled_false"]) == (1, 0, 0) and said["expected_by"] == rule
    gate = {"id": "G-STANDING", "question": "Q6", "callable": "studio.standing_approval:ok"}
    assert gr.gate_row(gate, said)["passed"] and not gr.gate_row(gate, gr.tally(items, confirmed=[]))["passed"]


def test_the_report_writes_one_design_5_row_per_replayed_gate(tmp_path):
    spec = {"gates": [{"id": "G-META-CREDIT", "callable": "scripts.publish.metadata:credit_faults", "reader": "credit",
                       "since": "2026-10-20", "commit": "967597b", "question": "Q6", "unit": "episode", "confirmed": []},
                      {"id": "MASTER-EYE-KEY", "callable": "studio.judges.master_eye:EyeCache", "since": "2026-10-21",
                       "commit": "b008100", "question": "Q6", "why_not_replayed": "a cache key"}]}
    put(tmp_path / "wotw_ep05", "youtube.json", {"description": '"" x'})
    doc = gr.report(spec, [("wotw_ep05", tmp_path / "wotw_ep05", 5)])
    (row,) = doc["proof_rows"]
    assert row["check"] == "gate_replay.G-META-CREDIT" and row["n_points"] == 1 and not row["passed"]
    assert doc["gates"]["MASTER-EYE-KEY"]["replayed"] is False


def test_the_dry_check_stand_in_carries_the_frozen_plan_and_a_crash_is_unread_never_a_pass(tmp_path):
    seen = {}

    def replay(home, doc):
        seen["plan"] = (Path(home) / "plan.json").is_file()
        raise FileNotFoundError("ladder.json")
    fixture = tmp_path / "wotw_ep05"
    put(fixture, rd.STAT, {"files": {}, "kept": {}, "draws": {}, "eye": ""})
    put(fixture, "takes/r2v/shots.json", [])
    put(fixture, "plan.json", {"shots": []})
    (row,) = gr.dry_check(fixture, replay)
    assert seen["plan"] and row["verdict"] == "unread" and "raised" in row["why"]


def test_a28_on_panels_that_measured_no_face_is_unread_never_zero_of_zero(tmp_path):
    record = gr.resolve("studio.panel_dq:tiny_face_record")
    put(tmp_path, "storyboard/panel_dq.json", [{"shot": 0, "faces": 2}, {"shot": 1}])
    assert [r["verdict"] for r in gr.tiny_face(tmp_path, record)] == ["unread"]


def test_the_face_list_without_the_plan_is_unread(tmp_path):
    listed = gr.resolve("studio.face_refine:face_list")
    put(tmp_path, "takes/r2v/shots.json", [{"index": 0, "shots": [0], "faces": ["a"]}])
    assert [r["verdict"] for r in gr.face_list(tmp_path, listed)] == ["unread"]


def test_an_advisory_gate_counts_flags_never_false_refusals():
    items = [{"unit": "a", "verdict": "refused"}, {"unit": "b", "verdict": "passed"}]
    said = gr.tally(items, confirmed=[], counts="flags")
    assert (said["n"], said["refused"], said["unruled"], said["flagged"]) == (2, 0, 0, 1)


def test_every_spec_gate_says_whether_it_refuses_flags_or_rewords():
    for g in gr.load_spec()["gates"]:
        if g.get("reader"):
            assert g.get("counts", "refusals") in gr.COUNTS
    kinds = {g["id"]: g.get("counts", "refusals") for g in gr.load_spec()["gates"] if g.get("reader")}
    assert kinds["A28-TINY-FACE"] == kinds["FACE-LIST"] == "flags" and kinds["ADVISORY-WORDING"] == "rewords"


def test_the_outside_wall_on_an_episode_with_no_refine_record_is_unread(tmp_path):
    assert [r["verdict"] for r in gr.outside(tmp_path, gr.resolve("studio.face_refine:outside_refusal"))] == ["unread"]


def test_a_gate_with_no_readable_unit_never_passes(tmp_path):
    spec = {"gates": [{"id": "OUTSIDE-UNREAD", "callable": "studio.face_refine:outside_refusal", "reader": "outside",
                       "since": "2026-10-20", "commit": "231071c", "question": "Q6", "confirmed": []}]}
    (tmp_path / "wotw_ep05").mkdir()
    (row,) = gr.report(spec, [("wotw_ep05", tmp_path / "wotw_ep05", 5)])["proof_rows"]
    assert row["n_points"] == 0 and not row["passed"]


def test_freeze_writes_every_absolute_path_relative_to_its_episode(tmp_path):
    book = tmp_path / "book"
    home = book / "episodes" / "ep05"
    strip = str(home / "takes" / "r2v" / "dq" / "T00_strip.png")
    put(home, "takes/r2v/shots.json", [])
    put(home, "takes/r2v/T00.dq.json", {"take_sha8": "x", "strip": strip, "gates": [{"file": "D:/elsewhere/a.png"}]})
    (home / "takes" / "r2v" / "T00.mp4").write_bytes(b"take")
    gr.freeze(home, book, tmp_path / "wotw_ep05")
    doc = json.loads((tmp_path / "wotw_ep05" / "takes/r2v/T00.dq.json").read_text(encoding="utf-8"))
    assert doc["strip"] == "takes/r2v/dq/T00_strip.png" and doc["gates"][0]["file"] == "a.png"


def test_no_frozen_fixture_holds_an_absolute_path():
    import re
    found = [p.relative_to(rd.FIXTURES).as_posix() for p in sorted(rd.FIXTURES.rglob("*.json"))
             if re.search(r'"[A-Za-z]:(\\|/)', p.read_text(encoding="utf-8"))]
    assert found == []


PINNED = {"G-STANDING": (28, 28, 14), "G-META-CREDIT": (42, 6, 0), "G-HOLE-SLACK": (42, 7, 0),
          "OUTSIDE-UNREAD": (11, 0, 41), "A28-TINY-FACE": (25, 8, 41), "G-CROWD-ORPHAN": (236, 21, 0),
          "L28-STYLE-LIGHT": (1044, 24, 0), "FACE-LIST": (1041, 4, 0), "ADVISORY-WORDING": (8, 8, 0)}
"""(n, hits, unread) each cheap gate replays to on the 42 frozen episodes, pinned from results/gates.json of
2026-10-21; a change to a gate or a fixture that moves one is seen here (the dry check runs in its own test)."""


@pytest.mark.parametrize("gate_id", sorted(PINNED))
def test_the_frozen_fixtures_replay_each_cheap_gate_to_its_pinned_counts(gate_id):
    spec = gr.load_spec()
    gate = next(g for g in spec["gates"] if g["id"] == gate_id)
    said = gr.run_gate(gate, gr.episodes(spec))
    hits = said["refused"] + said["flagged"] + said["reworded"]
    assert said["missing_fixtures"] == [] and (said["n"], hits, said["unread"]) == PINNED[gate_id]
