"""G-CAST (Jekyll ep03 retro, finding 1): the MASTER judge read Jekyll and Utterson
as one man ("two characters collapse") at the last gate, where no retake can fix
it.  The same measure now runs where the refs stage signs a sheet: every pair of
BASE sheets, facenet's largest face, the master's own wall (identity_gate.DRIFT).
A pair at or above it that holds a sheet being judged is a HARD fault on that
sheet and the sheet ladder climbs; a pair of two signed sheets is reported,
never refused.  Every embedder here is a stub; nothing loads facenet."""
from __future__ import annotations

import json

import numpy as np

from scripts.refs import step_04_verdict as step
from studio import cast_faces, identity_gate, sheet_ladder
from studio.judges import master_eye
from tests import look_fixtures as lf


def unit(*xs) -> np.ndarray:
    v = np.zeros(8)
    v[:len(xs)] = xs
    return v / np.linalg.norm(v)


SAME = unit(1.0, 0.2)
"""A face at cosine 0.98 to unit(1.0): over the wall."""
APART = unit(1.0, 1.4)
"""A face at cosine 0.58 to unit(1.0): under the wall."""


def counting(vectors: dict[str, np.ndarray], calls: list):
    def embed(picture):
        calls.append(lf.name_of(picture))
        return vectors.get(lf.name_of(picture))
    return embed


def test_the_wall_is_the_master_judges_collapse_wall():
    assert cast_faces.WALL == identity_gate.DRIFT
    a, b = unit(1.0), unit(1.0, 0.5)               # cosine 0.894
    master = master_eye.collapse_faults({"a": [a], "b": [b]})
    pairs = cast_faces.pair_scores({"a": a, "b": b})
    assert bool(master) == bool(cast_faces.collapses(pairs, {"a": "x/a.png", "b": "x/b.png"}, {"b"}))


def test_base_sheets_are_the_bound_characters_sheets_on_disk(tmp_path):
    book = lf.a_book(tmp_path)
    lf.character(book, "a")
    lf.character(book, "b")
    lf.add_row(book, "refs/characters/a/sheet_front.png")
    assert cast_faces.base_sheets(book, {"a", "b", "c"}) == {
        "a": "refs/characters/a/sheet.png", "b": "refs/characters/b/sheet.png"}


def test_every_pair_is_scored_once_highest_first():
    pairs = cast_faces.pair_scores({"a": unit(1.0), "b": SAME, "c": unit(0, 1.0)})
    assert [(p["a"], p["b"]) for p in pairs] == [("a", "b"), ("b", "c"), ("a", "c")]
    assert pairs[0]["cosine"] == round(float(unit(1.0) @ SAME), 3)


def test_a_pair_over_the_wall_holding_a_judged_sheet_is_a_hard_fault_on_it():
    sheets = {"a": "refs/characters/a/sheet.png", "b": "refs/characters/b/sheet.png"}
    pairs = cast_faces.pair_scores({"a": unit(1.0), "b": SAME})
    fault = cast_faces.collapses(pairs, sheets, {"b"})[0]
    assert fault.kind == cast_faces.KIND and fault.kind in sheet_ladder.HARD
    assert fault.where == "refs/characters/b/sheet.png"
    assert fault.evidence["other"] == "refs/characters/a/sheet.png"
    assert fault.evidence["wall"] == identity_gate.DRIFT and fault.evidence["cosine"] >= identity_gate.DRIFT
    assert "a" in fault.note and "b" in fault.note


def test_a_pair_of_two_signed_sheets_or_under_the_wall_refuses_nothing():
    sheets = {"a": "refs/characters/a/sheet.png", "b": "refs/characters/b/sheet.png"}
    assert cast_faces.collapses(cast_faces.pair_scores({"a": unit(1.0), "b": SAME}), sheets, set()) == []
    assert cast_faces.collapses(cast_faces.pair_scores({"a": unit(1.0), "b": APART}), sheets, {"a", "b"}) == []


def test_two_judged_sheets_fault_the_later_one():
    sheets = {"a": "refs/characters/a/sheet.png", "b": "refs/characters/b/sheet.png"}
    pairs = cast_faces.pair_scores({"a": unit(1.0), "b": SAME})
    assert [f.where for f in cast_faces.collapses(pairs, sheets, ["b", "a"])] == ["refs/characters/a/sheet.png"]


def test_each_sheet_is_embedded_once_until_its_bytes_change(tmp_path):
    book = lf.a_book(tmp_path)
    lf.character(book, "a")
    lf.character(book, "b")
    calls = []
    embed = counting({"a": unit(1.0), "b": APART}, calls)
    cast_faces.faults(book, {"a", "b"}, {"a"}, embed)
    cast_faces.faults(book, {"a", "b"}, {"a"}, embed)
    assert sorted(calls) == ["a", "b"]
    lf.draw(book, "refs/characters/a/sheet.png", colour=(1, 2, 3))
    cast_faces.faults(book, {"a", "b"}, {"a"}, embed)
    assert sorted(calls) == ["a", "a", "b"]


def test_every_pair_and_the_wall_are_written_for_the_report(tmp_path):
    book = lf.a_book(tmp_path)
    for who in ("a", "b", "c"):
        lf.character(book, who)
    cast_faces.faults(book, {"a", "b", "c"}, set(), counting({"a": unit(1.0), "b": SAME, "c": APART}, []))
    report = json.loads((book / cast_faces.REPORT).read_text(encoding="utf-8"))
    assert report["wall"] == identity_gate.DRIFT and len(report["pairs"]) == 3
    assert report["pairs"][0]["a"] == "a" and report["pairs"][0]["b"] == "b"


def test_a_sheet_without_a_face_is_never_paired(tmp_path):
    book = lf.a_book(tmp_path)
    lf.character(book, "a")
    lf.character(book, "b")
    assert cast_faces.faults(book, {"a", "b"}, {"a", "b"}, counting({"a": unit(1.0)}, [])) == []


def test_step_04_climbs_on_a_new_sheet_that_shares_a_face_and_signs_it_flagged(tmp_path):
    book = lf.a_book(tmp_path)
    lf.character(book, "a")
    lf.character(book, "b")
    drawn = []
    tools = lf.tools(embed=counting({"a": unit(1.0), "b": SAME}, []), reader=lf.reader_of({"a": "base", "b": "d4"}))
    ctx = lf.a_ctx(tmp_path, book, **tools, draw=lf.drawer(drawn, book))
    step.run(ctx)
    assert len(drawn) == len(sheet_ladder.LADDER.rungs)               # the stub face never moves
    signed = lf.verdict(book)
    kept = [f for f in signed["faults"] if f["kind"] == cast_faces.KIND]
    assert kept and kept[0]["where"] == "refs/characters/b/sheet.png"
    assert kept[0]["evidence"]["cosine"] >= identity_gate.DRIFT
