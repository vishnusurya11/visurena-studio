"""The publish lock (root cause 2026-09-26, A1 + A4 + C8).

ep12 was uploaded and made public with PLAN kept-best, EYE_PANELS kept-best at
attempt 0, EYE_TAKES kept-best and MASTER flagged -- every taste gate ended in a
terminal and nothing between the runner and the channel read that.  The lock
reads the unit's learnings, its voice check and the director's sign-off, and
lists every reason the master may not reach the platform.  Only an owner-written
waiver clears a terminal."""
from __future__ import annotations

import json

from studio import publish_lock as pl
from studio.learnings import Learning, record

SHA = "faf11c8f"
SIGNOFF = f"""# Director sign-off -- ep13 {SHA}

## Watched
Full size with sound, 0:00-2:41. 0:42 the gun thud lands on the cut; 1:55 the shout lifts.

## Take strips
All 24 strips read. T06 holds too long on the salute; retaken, now moves.

## Coverage
Last line covers paragraph 49 of 50; the curate's arrival (p12-20) and the title event are on screen.

## Flags
None open.
"""


def home_with(tmp_path, rows=(), speakers=None, signoff=SIGNOFF):
    home = tmp_path / "ep13"
    (home / "review").mkdir(parents=True)
    for row in rows:
        record(home / "learnings.jsonl", row)
    if speakers is not None:
        (home / "review" / "speaker_check.json").write_text(json.dumps(speakers), encoding="utf-8")
    if signoff is not None:
        (home / "review" / "director_signoff.md").write_text(signoff, encoding="utf-8")
    return home


def row(gate, action, terminal=False, note=""):
    return Learning(step="08", gate=gate, action=action, terminal=terminal, note=note)


def test_a_clean_unit_has_no_stops(tmp_path):
    home = home_with(tmp_path, [row("PLAN", "pass"), row("MASTER", "pass")], {"n": {"ok": True}})
    assert pl.stops(home, SHA) == []


def test_a_terminal_is_a_stop(tmp_path):
    home = home_with(tmp_path, [row("EYE_PANELS", "keep_best", True, "landmark at shot_00")])
    assert pl.open_terminals(home) == ["EYE_PANELS ended keep_best: landmark at shot_00"]
    assert len(pl.stops(home, SHA)) == 1


def test_the_last_row_per_gate_decides_and_budget_rows_do_not(tmp_path):
    rows = [row("MASTER", "flag", True, "faces"), row("MASTER", "pass"), row("budget", "defer")]
    assert pl.open_terminals(home_with(tmp_path, rows)) == []


def test_an_owner_waiver_clears_a_named_terminal(tmp_path):
    home = home_with(tmp_path, [row("MASTER", "flag", True, "faces at master")])
    (home / "review" / "waiver.json").write_text(json.dumps({"MASTER": "owner: face size accepted"}),
                                                 encoding="utf-8")
    assert pl.stops(home, SHA) == []


def test_an_empty_waiver_reason_clears_nothing(tmp_path):
    home = home_with(tmp_path, [row("MASTER", "flag", True)])
    (home / "review" / "waiver.json").write_text(json.dumps({"MASTER": " "}), encoding="utf-8")
    assert len(pl.stops(home, SHA)) == 1


def test_a_voice_that_is_not_one_voice_is_a_stop(tmp_path):
    home = home_with(tmp_path, speakers={"narrator": {"ok": False, "worst": 0.648}})
    assert pl.speaker_stops(home) == ["speaker_check: narrator is not one voice (worst pair 0.648)"]


def test_no_signoff_is_a_stop(tmp_path):
    home = home_with(tmp_path, signoff=None)
    assert pl.signoff_stops(home, SHA) == ["director_signoff.md is missing: watch, listen and sign before publishing"]


def test_a_signoff_for_another_cut_is_a_stop(tmp_path):
    home = home_with(tmp_path)
    assert pl.signoff_stops(home, "0badbeef") == ["director_signoff.md does not name this cut (0badbeef)"]


def test_an_empty_section_is_a_stop(tmp_path):
    home = home_with(tmp_path, signoff=SIGNOFF.replace("All 24 strips read. T06 holds too long on the salute; "
                                                         "retaken, now moves.", ""))
    assert pl.signoff_stops(home, SHA) == ["director_signoff.md section 'Take strips' is empty"]
