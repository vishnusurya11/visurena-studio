"""G-LOOK and G-PLACE ride the battery as HARD rows on a continuity book and are
cured by code in plan_repair (never the writer); the brief of such a book lists
each place's drawn views, master and history and the looks a chapter allows."""
from __future__ import annotations

import json

from studio import look_timeline, plan_brief, plan_cures
from studio.continuity_spec import CharacterLooks
from tests import continuity_fixtures as fx
from tests.test_a_place_is_its_master import book

from scripts.episode import plan_check, plan_repair


def test_the_fault_rows_route_to_their_code_cures():
    assert plan_cures.cure_for("G-LOOK setup s: narrator's look 'x' is not allowed") == "continuity_looks"
    assert plan_cures.cure_for("G-PLACE setup rev: narrators_study/reverse would be a new room") == "continuity_places"


def test_a_legacy_book_is_not_judged(tmp_path):
    assert plan_check.continuity_book(tmp_path) is False
    assert plan_check.continuity_gates(tmp_path, None) == 0


def test_the_place_cure_rewrites_the_plan(tmp_path):
    b = book(tmp_path)
    (b / "refs" / "places.json").write_text(json.dumps({"places": {
        "narrators_home": {"name": "house", "members": ["narrators_home", "narrators_dining_room",
                                                         "narrators_study"]}}}), encoding="utf-8")
    doc = {"number": 2, "setups": {"rev": {"location": "narrators_study", "view": "reverse"}}}
    cured = plan_repair.continuity_cure(doc, "continuity_places", b, 2)
    assert cured["setups"]["rev"]["view"] == ""


def test_the_brief_carries_drawn_views_master_history_and_allowed_looks(tmp_path):
    b = book(tmp_path)
    look_timeline.write_looks(b, "narrator", CharacterLooks.model_validate(fx.CARD))
    (b / "analysis" / "locations" / "narrators_study.json").write_text(json.dumps({
        "id": "narrators_study", "name": "the study", "scenes": [{"chapter": 2}],
        "profile": {"design": {"views": [{"id": "wide_establishing"}, {"id": "undrawn_corner"}]}}}))
    row = next(p for p in plan_brief.places(b, 2) if p["id"] == "narrators_study")
    assert row["drawn_views"] == ["wide_establishing"] and row["master"] == "wide_establishing"
    assert [v["id"] for v in row["design"]["views"]] == ["wide_establishing"]
    assert row["history"] == ["ep01 narrators_study/wide_establishing"]
    got = plan_brief.with_looks(b, {"entity_id": "narrator"}, 26)
    assert got["default_look"] == "ragged" and [l["look"] for l in got["looks_allowed"]] == ["ragged", "borrowed"]
