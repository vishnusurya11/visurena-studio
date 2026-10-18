"""The live card says WHY the step is where it is (page experts 2026-10-18, B3): the real cause
('plan_check refused: G-VARIETY ... measured 3 against 4') sat in small grey 'last words' and
that slot sometimes held a log banner instead.  `why` is the run's newest warning or refusal,
kept while later info lines scroll past."""
from __future__ import annotations

from pathlib import Path

from studio.command_center import legacy_progress as lp, models

TEMPLATES = Path(lp.__file__).resolve().parent / "templates"
REFUSAL = "plan_check refused: G-VARIETY plan: insert shots for 23 shots, measured 3 against 4"


def test_why_is_the_newest_warning_not_the_newest_line():
    rows = [{"level": "INFO", "msg": "step 02 started"}, {"level": "WARNING", "msg": REFUSAL},
            {"level": "INFO", "msg": "writing the plan, round 3"}]
    assert lp.why_of(rows) == REFUSAL


def test_a_refusal_over_several_lines_is_one_line():
    # live ep01 2026-10-18: the refusal's cause is on its second line; the first alone said 'plan_check refused:'
    rows = [{"level": "WARNING", "msg": "plan_check refused:\n  G-VARIETY plan: insert shots\n  for 23 shots"}]
    assert lp.why_of(rows) == "plan_check refused: G-VARIETY plan: insert shots for 23 shots"


def test_a_gate_report_keeps_only_what_refused():
    # live ep01 2026-10-18: the report listed eleven clean gates before the one that refused
    msg = ("plan_check refused:\nCONTRACT OK: Story of the Door | 24 shots\nG-LIGHT : clean\nG-PACE : clean\n"
           "G-VARIETY plan: insert shots for 23 shots, measured 3 against 4")
    assert lp.why_of([{"level": "WARNING", "msg": msg}]) == \
        "plan_check refused: G-VARIETY plan: insert shots for 23 shots, measured 3 against 4"


LIVE_REPORT = """plan_check refused:
CONTRACT OK: Story of the Door | 24 shots | 130s projected
G-LIGHT      : clean
G-SPEAKER    : clean (narrator 'narrator')
EXPECTS TEXT : [13]
MARKS        : clean | unmeasured 0
CAST BOUND   : all bound
ONE PER TAKE : every shot its own take
TAKE LENGTH  : every shot inside a take (at 2.45 words/s, budget 8.0 s)
G-TAKELINT   : 1
    G-TAKELINT shot 20: L14 LENGTH [shot 20]: 135 words; the gate is 150-360 a block [plan]
SHEET TEXT   :
    not applicable: this book draws storyboard grids, not seq_boards sheets
VERDICT      : REFUSED"""


def test_the_live_plan_report_names_the_one_fault():
    # Jekyll ep01's plan_check report, 2026-10-18 (copied from the run log)
    assert lp.why_of([{"level": "WARNING", "msg": LIVE_REPORT}]) == (
        "plan_check refused: G-TAKELINT shot 20: L14 LENGTH [shot 20]: 135 words; the gate is 150-360 a block [plan]")


def test_a_quiet_run_has_no_why():
    assert lp.why_of([{"level": "INFO", "msg": "step 02 started"}]) == "" and lp.why_of([]) == ""


def test_the_card_carries_and_shows_why():
    assert "why" in models.Progress.model_fields
    live = (TEMPLATES / "_unit_live.html").read_text(encoding="utf-8")
    assert 'data-k="why"' in live
