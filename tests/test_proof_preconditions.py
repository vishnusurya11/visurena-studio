"""The chapter precondition audit (DESIGN 2026-10-21_ep02_proof 4.3; package P2).

Read-only, $0: the book's source/book.json, the chapter text, the analysis rows that name who
speaks and who is present, the cast voices, the refs.json sheets and the places.json masters,
each opened BY NAME.  Every gap is printed as a predicted park or as a just-in-time ref step
with its cost from the book's own timing norms; F14 plants exactly these gaps.  The fixture
is a copy of the Jekyll book's named records, and `present_files.json` lists which of its
binary files existed on 2026-10-21 (the test makes each one an empty file)."""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

import pytest

from studio.rehearsal import preconditions as pre

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "proof" / "ch2_preconditions" / "book"
REPO = Path(__file__).resolve().parents[1]


@pytest.fixture
def book(tmp_path):
    dest = tmp_path / "library" / "jekyll"
    shutil.copytree(FIXTURE, dest)
    for rel in json.loads((dest / "present_files.json").read_text(encoding="utf-8"))["present"]:
        (dest / rel).parent.mkdir(parents=True, exist_ok=True)
        (dest / rel).write_bytes(b"")
    return dest


def kinds(gaps: list[dict], kind: str) -> set[str]:
    return {g["what"] for g in gaps if g["kind"] == kind}


def test_registry_aliases_resolve_the_names_the_chapter_uses(book):
    index = pre.alias_index(pre.read_json(book / "analysis" / "registry.json"))
    assert pre.resolve("Lanyon", index) == "reginald_lanyon"
    assert pre.resolve("Mr. Hyde", index) == "edward_hyde"
    assert pre.resolve("utterson", index) == "gabriel_john_utterson"
    assert pre.resolve("the solemn butler", index) == "poole"      # the registry's claim, kept as it is
    assert pre.resolve("a well-dressed, elderly servant", index) is None


def test_the_chapters_speakers_are_its_attributed_dialogue_plus_the_narrator(book):
    cast = pre.chapter_cast(book, 2)
    assert cast["speakers"] == {"narrator", "gabriel_john_utterson", "reginald_lanyon", "edward_hyde", "poole"}
    assert {"gabriel_john_utterson", "reginald_lanyon", "edward_hyde", "poole"} <= cast["present"]
    assert "henry_jekyll" not in cast["present"]
    assert cast["unresolved"] == {"a well-dressed, elderly servant"}


def test_the_chapters_places_are_its_scene_rows(book):
    assert pre.chapter_places(pre.read_json(book / "analysis" / "scenes.json"), 2) == [
        "utterson_house", "lanyon_dining_room", "black_mail_house_door", "jekyll_house", "london_streets"]


def test_a_speaker_with_no_cast_voice_is_a_predicted_park_at_the_record_step(book):
    (book / "cast" / "poole" / "voice" / "design.wav").unlink()
    gaps = pre.audit(book, 2)["gaps"]
    voice = next(g for g in gaps if g["kind"] == "voice")
    assert voice["what"] == "poole" and voice["outcome"] == "park" and voice["step"] == "04"
    assert "say_lines.py" in voice["basis"]


def test_ch2_finds_the_superseded_base_sheets_of_poole_and_lanyon(book):
    gaps = pre.audit(book, 2)["gaps"]
    assert kinds(gaps, "base_sheet") == {"poole", "reginald_lanyon"}
    sheet = next(g for g in gaps if g["kind"] == "base_sheet")
    assert sheet["outcome"] == "jit" and sheet["cost_s"] > 0 and "refs/pack.jsonl" in sheet["cost_basis"]


def test_ch2_finds_every_place_master_whose_picture_is_absent(book):
    gaps = pre.audit(book, 2)["gaps"]
    assert kinds(gaps, "place_picture") == {
        "utterson_house/business_room", "utterson_house/bedroom", "lanyon_dining_room/dining_room",
        "black_mail_house_door/court_entry_pavement", "jekyll_house/hall", "london_streets/night_street"}
    place = next(g for g in gaps if g["kind"] == "place_picture")
    assert place["outcome"] == "jit" and place["step"] == "03" and place["cost_s"] > 0


def test_a_place_with_no_row_is_drawn_just_in_time_from_its_own_name(book):
    places = pre.read_json(book / "refs" / "places.json")
    assert pre.place_gaps(book, places, "a_new_room") == ["a_new_room/wide_establishing"]


def test_the_required_book_fields_are_the_ones_step_13_refuses_without(book):
    said = (REPO / "scripts" / "publish" / "youtube_retitle.py").read_text(encoding="utf-8")
    fields = re.search(r'for k in \(([^)]*)\) if not said\.get\(k\)', said).group(1)
    assert set(pre.REQUIRED_BOOK_FIELDS) >= {f.strip().strip('"') for f in fields.split(",")}


def test_a_book_json_missing_fields_is_one_named_park_per_field(book):
    path = book / "source" / "book.json"
    said = json.loads(path.read_text(encoding="utf-8"))
    for k in ("series", "display_title", "episodes"):
        said.pop(k)
    path.write_text(json.dumps(said), encoding="utf-8")
    gaps = pre.audit(book, 2)["gaps"]
    assert kinds(gaps, "book_field") == {"series", "display_title", "episodes"}
    assert all(g["outcome"] == "park" and g["step"] == "13" for g in gaps if g["kind"] == "book_field")


def test_a_chapter_with_no_text_is_a_park_before_the_plan(book):
    (book / "source" / "chapters" / "ch_02.json").unlink()
    gaps = pre.audit(book, 2)["gaps"]
    assert kinds(gaps, "chapter_text") == {"chapters/ch_02.json"}


def test_the_cost_norms_are_medians_of_the_books_own_records(book):
    norms = pre.norms(book)
    sheets = [json.loads(l)["seconds"] for l in (book / "refs" / "pack.jsonl").read_text().splitlines()]
    assert norms["base_sheet"]["seconds"] == pytest.approx(sorted(sheets)[len(sheets) // 2], abs=60)
    assert norms["place_picture"]["n"] >= 1 and norms["place_picture"]["seconds"] > 0
    assert norms["base_sheet"]["p90_s"] >= norms["base_sheet"]["seconds"]
    assert norms["voice"]["seconds"] is None


def test_the_audit_names_its_sources_and_props_as_real_run(book):
    out = pre.audit(book, 2)
    assert "source/book.json" in out["sources"] and "refs/places.json" in out["sources"]
    assert out["props"]["status"] == "REAL-RUN"
    assert all(not Path(s).is_absolute() for s in out["sources"])


def test_the_script_writes_the_audit_and_prints_its_path_first(book, tmp_path, capsys):
    from scripts.proof import preconditions as script
    out = tmp_path / "results" / "preconditions_ch2.json"
    assert script.main(["ch2", "--out", str(out), "--book", str(book)]) == 0
    said = capsys.readouterr().out.splitlines()
    assert said[0] == str(out.resolve())
    assert any("base_sheet poole" in line for line in said)
    assert json.loads(out.read_text(encoding="utf-8"))["chapter"] == 2


def test_the_chapter_argument_reads_ch2_or_2():
    from scripts.proof import preconditions as script
    assert script.chapter_of("ch2") == script.chapter_of("2") == 2


def test_a_paused_or_ended_series_is_an_owner_precondition_the_audit_lists(book):
    """AUDIT A8: the book's autopilot/series.json said paused, last 1 ('ep02 must not start'); an
    unattended ep02 needs the owner to change it, so the audit names it as a gap of its own."""
    (book / "autopilot").mkdir()
    (book / "autopilot" / "series.json").write_text(json.dumps(
        {"first": 1, "last": 1, "paused": True, "last_why": "ep02 must not start"}), encoding="utf-8")
    said = [g for g in pre.audit(book, 2)["gaps"] if g["kind"] == "series_state"]
    assert len(said) == 1 and said[0]["outcome"] == "owner"
    assert "paused" in said[0]["what"] and "last 1" in said[0]["what"]
    (book / "autopilot" / "series.json").write_text(json.dumps({"first": 1, "last": 9, "paused": False}),
                                                   encoding="utf-8")
    assert not [g for g in pre.audit(book, 2)["gaps"] if g["kind"] == "series_state"]
    assert "autopilot/series.json" in pre.audit(book, 2)["sources"]
