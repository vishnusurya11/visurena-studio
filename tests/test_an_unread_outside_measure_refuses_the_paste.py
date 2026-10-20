"""The outside-the-face wall cannot pass unread (retro 2026-10-20 item 3, package C).

`paste_refusals` refused `outside > OUTSIDE_MAX`, but only when the measure was read: a row whose
`outside` was None passed the wall without a number (docs/audit/2026-10-20_deadline_retro/RETRO.md
section 3, rank 3).  The ep01 iter2 warp reached a master through gates that never measured the pixels
outside the face, so an unread measure is now a refusal.  The regression fixture is ep01's iter3 paste
record (takes/r2v/refine.json, every row read `outside` 0.0): the new rule changes none of its decisions.
"""
from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

from scripts.episode import face_refine as cli
from studio import face_refine as fr

ITER3 = Path(__file__).parent / "fixtures" / "ep01_face_list" / "refine_iter3.json"


def measures(row: dict) -> fr.Measures:
    return fr.Measures(**{k: v for k, v in row["measures"].items() if k in fr.Measures.__dataclass_fields__})


def rows() -> list[dict]:
    doc = json.loads(ITER3.read_text(encoding="utf-8"))
    return [p for key, entry in doc.items() if key.startswith("T") for p in entry.get("people", [])]


def clean() -> fr.Measures:
    return fr.Measures(id_src=0.5, id_ref=0.6, seam=8.0, flick_src=4.0, flick_ref=3.9, faces_src=1, faces_ref=1,
                       change=11.0, outside=0.0, band_warp=0.5)


def test_an_unread_outside_measure_is_a_refusal():
    said = fr.paste_refusals(replace(clean(), outside=None))
    assert said and "outside" in said[0] and "unread" in said[0]


def test_an_unread_outside_measure_falls_back_to_the_take():
    kept, why = fr.decide(replace(clean(), outside=None))
    assert not kept and "unread" in why


def test_a_read_outside_measure_inside_the_wall_still_passes():
    assert fr.decide(clean()) == (True, "kept")


def test_every_iter3_row_read_its_outside_measure():
    assert rows() and all(p["measures"].get("outside") is not None for p in rows())


def test_the_iter3_decisions_are_unchanged_by_the_unread_rule():
    """Every ep01 iter3 row re-decided on its stored measures gives its stored decision."""
    for p in rows():
        assert fr.decide(measures(p)) == (p["kept"], p["why"]), p["crop"]


def test_an_iter3_kept_row_with_its_outside_measure_dropped_is_refused():
    kept = next(p for p in rows() if p["kept"])
    assert not fr.decide(replace(measures(kept), outside=None))[0]


def test_a_row_without_an_outside_measure_is_regated_before_a_cut():
    """The regate re-reads the paste's measures: a row that holds band_warp but no outside is stale."""
    row = {"measures": {**rows()[0]["measures"]}}
    row["measures"].pop("outside")
    assert cli.stale_row(row) and cli.regate_due({"people": [row]})


def test_a_row_the_regate_cannot_read_falls_back(tmp_path):
    """A regate that reads no take or crop window has no outside measure: the take keeps its face."""
    (tmp_path / "refine").mkdir()
    (tmp_path / "refine" / "T05_p0.json").write_text(json.dumps({"life": [0, 9], "windows": [[0, 0, 96]] * 10,
                                                                 "start": 0}), encoding="utf-8")
    row = {"who": "a", "crop": "refine/T05_p0.mp4", "track": "refine/T05_p0.json", "kept": True, "why": "kept",
           "measures": {"seam": 8.0}}
    out = cli.regate_row(tmp_path, [], row, read=lambda path: [], detect=None)
    assert out["kept"] is False and "unread" in out["why"]
