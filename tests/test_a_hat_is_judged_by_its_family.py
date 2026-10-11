"""LOOK-STATE and G-LOOK-PANEL compare headwear by FAMILY (C2_verdict #4).

The reader names a battered brown felt hat `other_hat` 7 times in 8: LOOK-STATE
refused all three correct ragged_greyed draws on headwear (cycle-1 bench).
Brimmed = {felt_hat, other_hat}.  Every other marker is its own family; bowler
stays distinct until real bowler looks have been read (H7)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from studio import look_table as lt
from studio.continuity_spec import Markers
from studio.judges.look_state import marker_faults

EVIDENCE = Path(__file__).resolve().parents[1] / "docs" / "audit" / "2026-10-10_continuity_retro" / "bench_evidence" / "c1"
RAGGED = Markers(headwear="felt_hat", hair_colour="grey", facial_hair="beard", top="shirt", dirt="muddy")


def rejudged(record: dict) -> list[str]:
    """The cycle-1 verdict re-judged from its own evidence: the reader's words
    where it disagreed, the look's own marker where it did not."""
    seen = RAGGED.model_dump() | {f["kind"].removeprefix("look_"): f["evidence"]["seen"] for f in record["faults"]}
    return [f.kind for f in marker_faults(seen, RAGGED, "x") if f.severity == "high"]


def test_felt_and_other_hat_are_one_brimmed_family():
    assert lt.family("headwear", "felt_hat") == lt.family("headwear", "other_hat") == "brimmed"


@pytest.mark.parametrize("marker", ["bowler", "boater", "top_hat", "cap", "bonnet", "helmet", "hood", "none"])
def test_every_other_hat_is_its_own_family(marker):
    assert lt.family("headwear", marker) == marker


def test_the_cycle1_fresh_draws_pass_on_headwear_and_the_ghost_still_fails_on_its_beard():
    judged = json.loads((EVIDENCE / "looks_judge.json").read_text(encoding="utf-8"))
    assert [rejudged(judged[k]) for k in ("fresh_s0.png", "fresh_s1.png", "fresh_s2.png")] == [[], [], []]
    assert rejudged(judged["ghost_2x.png"]) == ["look_facial_hair"]


def test_the_shipped_ep25_boater_reads_still_refuse():
    shipped = json.loads((EVIDENCE / "regrid_ep25_report.json").read_text(encoding="utf-8"))["shipped_reads"]
    boaters = [r["headwear"] for r in shipped.values() if r["headwear"] == "boater"]
    assert boaters and all(lt.family("headwear", b) != lt.family("headwear", "felt_hat") for b in boaters)
    seen = RAGGED.model_dump() | {"headwear": "boater"}
    assert [f.kind for f in marker_faults(seen, RAGGED, "x")] == ["look_headwear"]
