"""The plan brief is assembled from files on disk, one gather per file kind.

Each gather reads one place and returns what a writer can judge; the optional
inputs (chapter text, a screenplay, bound rows, places, the camera catalog,
the dq rules) are left out of the brief when absent, never raised on.
"""
from __future__ import annotations

import json

import pytest

from studio import episode_spec, plan_brief


def _json(path, doc):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    return path


@pytest.fixture()
def book(tmp_path):
    root = tmp_path / "20260901000001_book"
    _json(root / "analysis" / "extraction" / "ch_03.json", {
        "chapter": 3, "pov": "first", "scenes": [
            {"n": 1, "para_start": 1, "para_end": 4, "type": "scene", "location_text": "the yard",
             "int_ext": "EXT", "time_of_day": "DAY", "story_day": 2, "frame": None,
             "summary": "Two people meet in the yard.", "boundary_reason": "action",
             "time_evidence": [{"type": "date", "text": "June"}],
             "characters": [{"name_text": "the lead", "presence": "present", "role": "agent"}],
             "events": [{"type": "action", "summary": "They meet.", "quote": "..."}],
             "dialogue": [{"speaker_text": "the lead", "notable_quote": "Well?"}],
             "state_changes": []}]})
    return root


# ---- scenes -----------------------------------------------------------------------

def test_scenes_carry_the_judgeable_fields_and_drop_the_evidence(book):
    rows = plan_brief.scenes(book, 3)
    assert len(rows) == 1 and rows[0]["summary"] == "Two people meet in the yard."
    assert rows[0]["dialogue"][0]["notable_quote"] == "Well?"
    assert "time_evidence" not in rows[0] and "boundary_reason" not in rows[0]


def test_the_chapter_rows_are_required(book):
    with pytest.raises(FileNotFoundError):
        plan_brief.scenes(book, 4)


# ---- chapter text -----------------------------------------------------------------

def test_chapter_text_joins_the_source_paragraphs(book):
    _json(book / "source" / "chapters" / "ch_03.json",
          {"n": 3, "paragraphs": [{"n": 1, "text": "First."}, {"n": 2, "text": "Second."}]})
    assert plan_brief.chapter_text(book, 3) == "First.\n\nSecond."


def test_chapter_text_prefers_the_analysis_copy_and_its_text_field(book):
    _json(book / "source" / "chapters" / "ch_03.json", {"paragraphs": [{"text": "raw"}]})
    _json(book / "analysis" / "chapters" / "ch_03.json", {"text": "cleaned"})
    assert plan_brief.chapter_text(book, 3) == "cleaned"


def test_chapter_text_is_none_when_no_copy_exists(book):
    assert plan_brief.chapter_text(book, 3) is None


# ---- screenplay -------------------------------------------------------------------

def _screenplay(book, target="feature"):
    return _json(book / "screenplay" / target / "screenplay.json", {"scenes": [
        {"number": 1, "slug": {"text": "EXT. YARD - DAY"}, "cast": ["lead"],
         "elements": [{"kind": "action", "text": "A gate swings.", "character": None,
                       "source": {"chapter": 3, "scene": 1}},
                      {"kind": "dialogue", "text": "Well?", "character": "lead",
                       "source": {"chapter": 3, "scene": 1}},
                      {"kind": "action", "text": "Elsewhere.", "character": None,
                       "source": {"chapter": 4, "scene": 1}}]},
        {"number": 2, "slug": {"text": "INT. HALL - NIGHT"}, "cast": [],
         "elements": [{"kind": "action", "text": "Later.", "source": {"chapter": 9, "scene": 1}}]}]})


def test_screenplay_keeps_only_the_elements_sourced_from_this_chapter(book):
    _screenplay(book)
    got = plan_brief.screenplay(book, 3)
    assert len(got) == 1 and got[0]["target"] == "feature" and got[0]["slug"] == "EXT. YARD - DAY"
    assert [e["text"] for e in got[0]["elements"]] == ["A gate swings.", "Well?"]
    assert got[0]["elements"][1]["character"] == "lead"


def test_screenplay_reads_every_target_unless_told_which(book):
    _screenplay(book, "feature")
    _screenplay(book, "short")
    assert {s["target"] for s in plan_brief.screenplay(book, 3)} == {"feature", "short"}
    assert [s["target"] for s in plan_brief.screenplay(book, 3, ["short"])] == ["short"]


def test_no_screenplay_is_an_empty_list(book):
    assert plan_brief.screenplay(book, 3) == []


# ---- cast rows --------------------------------------------------------------------

def _refs(book, chapter=3):
    return _json(book / "refs" / "refs.json", {"chapter": chapter, "refs": [
        {"ref_id": "char-lead", "kind": "character", "entity_id": "lead", "name": "The Lead",
         "display": "Lead", "physical": "Tall man, grey eyes. Wearing: a brown coat.",
         "wardrobe": {"indoor": "a brown coat", "outdoor": "a brown coat"},
         "marks": ["a scar over the left brow"], "rel_path": "refs/characters/lead/sheet.png",
         "identity": {"traits": {"x": 1}}},
        {"ref_id": "loc-yard", "kind": "location", "entity_id": "yard", "name": "the yard"}]})


def test_cast_rows_are_the_bound_character_rows_trimmed(book):
    _refs(book)
    rows = plan_brief.cast_rows(book, 3)
    assert [r["entity_id"] for r in rows] == ["lead"]
    assert rows[0]["marks"] == ["a scar over the left brow"] and rows[0]["display"] == "Lead"
    assert "identity" not in rows[0] and "rel_path" not in rows[0]


def test_cast_rows_are_redressed_for_this_chapter_when_the_stamp_differs(book):
    _refs(book, chapter=7)
    _json(book / "analysis" / "characters" / "lead.json", {
        "name": "The Lead", "profile": {"physical": "Tall man, grey eyes.",
                                        "wardrobe": {"travel": "a green cloak"},
                                        "wardrobe_by_chapter": {"1": "travel"}}})
    rows = plan_brief.cast_rows(book, 3)
    assert rows[0]["physical"] == "Tall man, grey eyes. Wearing: a green cloak"
    assert rows[0]["display"] == "Lead"


def test_cast_rows_keep_the_stamped_row_when_no_dossier_can_redress_it(book):
    _refs(book, chapter=7)
    assert plan_brief.cast_rows(book, 3)[0]["physical"].endswith("a brown coat.")


def test_no_refs_is_an_empty_cast(book):
    assert plan_brief.cast_rows(book, 3) == []


# ---- places -----------------------------------------------------------------------

def _location(book, lid, chapters, design=None):
    return _json(book / "analysis" / "locations" / f"{lid}.json", {
        "id": lid, "name": f"the {lid}", "scenes": [{"chapter": c, "scene": 1} for c in chapters],
        "profile": {"visual": f"{lid} as seen", "design": design or {"layout": "one gate"}}})


def test_places_are_the_locations_this_chapter_visits(book):
    _location(book, "yard", [3])
    _location(book, "hall", [9])
    _json(book / "analysis" / "locations" / "dossier.json", {"note": "a summary file, no id"})
    got = plan_brief.places(book, 3)
    assert [p["id"] for p in got] == ["yard"]
    assert got[0]["name"] == "the yard" and got[0]["visual"] == "yard as seen"
    assert got[0]["design"] == {"layout": "one gate"}


def test_places_fall_back_to_every_location_when_none_names_the_chapter(book):
    _location(book, "yard", [])
    _location(book, "hall", [])
    assert [p["id"] for p in plan_brief.places(book, 3)] == ["hall", "yard"]


def test_no_locations_folder_is_an_empty_list(book):
    assert plan_brief.places(book, 3) == []


# ---- the catalog, the rules, the band ---------------------------------------------

def test_camera_catalog_is_the_file_text_or_none(tmp_path):
    path = tmp_path / "camera_catalog.md"
    assert plan_brief.camera_catalog(path) is None
    path.write_text("# moves\n- push in", encoding="utf-8")
    assert plan_brief.camera_catalog(path) == "# moves\n- push in"


def test_dq_rules_are_the_book_file_or_none(book):
    assert plan_brief.dq_rules(book) is None
    _json(book / "analysis" / "dq_rules.json", {"banned_subjects": ["doll"]})
    assert plan_brief.dq_rules(book) == {"banned_subjects": ["doll"]}


def test_the_band_is_read_from_the_contract():
    band = plan_brief.band()
    assert band["min_seconds"] == episode_spec.MIN_SECONDS
    assert band["max_seconds"] == episode_spec.MAX_SECONDS
    assert band["words_per_second"] == episode_spec.WORDS_PER_SECOND
    assert band["max_words_per_line"] == episode_spec.MAX_WORDS
    assert band["max_voices"] == episode_spec.MAX_SPEAKING
    assert band["max_setups"] == episode_spec.MAX_SETUPS


# ---- build and render -------------------------------------------------------------

def test_build_omits_what_is_absent_and_carries_what_is_there(book, monkeypatch):
    monkeypatch.setattr(plan_brief, "CAMERA_CATALOG", book / "nowhere.md")
    brief = plan_brief.build(book, 3)
    assert brief["number"] == 3 and brief["scenes"] and brief["band"]
    for absent in ("chapter_text", "screenplay", "cast", "places", "camera_catalog", "dq_rules"):
        assert absent not in brief


def test_build_carries_every_optional_input_when_present(book, monkeypatch):
    catalog = book / "catalog.md"
    catalog.write_text("moves", encoding="utf-8")
    monkeypatch.setattr(plan_brief, "CAMERA_CATALOG", catalog)
    _json(book / "source" / "chapters" / "ch_03.json", {"paragraphs": [{"text": "Prose."}]})
    _screenplay(book)
    _refs(book)
    _location(book, "yard", [3])
    _json(book / "analysis" / "dq_rules.json", {"banned_subjects": ["doll"]})
    brief = plan_brief.build(book, 3, targets=["feature"])
    assert brief["chapter_text"] == "Prose." and brief["camera_catalog"] == "moves"
    assert brief["screenplay"][0]["target"] == "feature"
    assert brief["cast"][0]["entity_id"] == "lead" and brief["places"][0]["id"] == "yard"
    assert brief["dq_rules"] == {"banned_subjects": ["doll"]}


def test_render_has_a_section_per_present_input_in_a_fixed_order():
    text = plan_brief.render({
        "number": 3, "band": {"min_seconds": 120.0}, "scenes": [{"n": 1, "summary": "Meet."}],
        "chapter_text": "Prose.", "screenplay": [{"target": "feature"}],
        "cast": [{"entity_id": "lead"}], "places": [{"id": "yard"}],
        "camera_catalog": "moves", "dq_rules": {"banned_subjects": ["doll"]}})
    order = [text.index(h) for h in plan_brief.SECTIONS.values()]
    assert order == sorted(order)
    assert "Meet." in text and "Prose." in text and "moves" in text and '"doll"' in text


def test_render_leaves_out_the_sections_of_absent_inputs():
    text = plan_brief.render({"number": 3, "band": {"min_seconds": 120.0}, "scenes": []})
    assert plan_brief.SECTIONS["scenes"] in text
    assert plan_brief.SECTIONS["chapter_text"] not in text
    assert plan_brief.SECTIONS["camera_catalog"] not in text
