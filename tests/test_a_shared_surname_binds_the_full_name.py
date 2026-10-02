"""ep16 (2026-10-01): both Elphinstone sisters surname to 'Elphinstone', so
called() bound EVERY mention to BOTH sheets -- eight takes staged a sheet the
plan never declared, and T22 tagged Mrs as the picture of Miss.  A titled
proper name whose surname another cast member shares now binds its FULL
display phrase only; a unique surname still binds bare.  And a character row
without gender refuses at adoption: ep16 prompted both women as 'this man'
('His mouth shapes every syllable' on a speaking woman).  $0: regex + a wall."""
from __future__ import annotations

import pytest

from studio import episode_ref_official as ro


@pytest.fixture(autouse=True)
def cast():
    saved = dict(ro.DISPLAY), set(ro.WOMEN)
    ro.DISPLAY.update({"miss_elphinstone": "Miss Elphinstone",
                       "mrs_elphinstone": "Mrs. Elphinstone",
                       "narrators_brother": "the brother"})
    ro.WOMEN.update({"miss_elphinstone", "mrs_elphinstone"})
    yield
    ro.DISPLAY.clear(); ro.DISPLAY.update(saved[0])
    ro.WOMEN.clear(); ro.WOMEN.update(saved[1])


def test_a_shared_surname_binds_only_its_full_display():
    text = "Mrs. Elphinstone clutches the bag while Miss Elphinstone takes the reins."
    assert ro.called("miss_elphinstone").findall(text) and ro.called("mrs_elphinstone").findall(text)
    got = ro.tagged(text, ["miss_elphinstone", "mrs_elphinstone"])
    assert "<Subject 1>" in got and "<Subject 2>" in got
    assert "Elphinstone" not in got          # neither mention left unbound or double-bound


def test_a_unique_surname_still_binds_bare():
    ro.DISPLAY["ogilvy"] = "Ogilvy"
    assert ro.called("ogilvy").search("Ogilvy runs to the pit.")


def test_a_definite_display_binds_its_phrase_case_blind():
    assert ro.called("narrators_brother").search("the brother reaches across the seat")


def test_adoption_refuses_a_character_row_without_gender():
    import importlib.util, sys
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location("tr", root / "scripts" / "episode" / "takes_r2v.py")
    tr = importlib.util.module_from_spec(spec); sys.modules["tr"] = tr
    spec.loader.exec_module(tr)
    rows = [{"kind": "character", "entity_id": "x", "display": "X", "gender": "male", "physical": ""}]
    tr.adopt_names(rows)                                     # complete row: fine
    with pytest.raises(SystemExit, match="gender"):
        tr.adopt_names([{"kind": "character", "entity_id": "y", "physical": ""}])
