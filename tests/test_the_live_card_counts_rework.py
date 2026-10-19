"""The live card's finish carries the measured relaunch rework and says how sure it is
(timeline debate 2026-10-18, D2; owner go).  $0: a tmp DB, no GPU."""
from __future__ import annotations

import time

from studio.command_center import models
from studio.command_center import progress_view as pv
from test_progress_card_api import _drive, _progress, board  # noqa: F401  (the fixture)


def test_the_range_says_rough_and_the_rework_it_carries():
    e = {"range": "6:15–7:15 pm", "finish": "6:45 pm", "steps_left": 7, "n_runs": 9, "basis": "measured",
         "firm": "rough", "rework": 0.11, "rework_n": 9}
    assert pv.range_words(e) == "range 6:15–7:15 pm · rough · rework +11 % (9 episodes) · 7 steps to run · 9 runs · measured"


def test_a_firm_finish_says_so_and_no_rework_says_nothing():
    e = {"range": "6:15–7:15 pm", "finish": "6:45 pm", "steps_left": 1, "firm": "firm", "rework": 0.0, "rework_n": 9}
    assert pv.range_words(e) == "range 6:15–7:15 pm · firm · 1 step to run"


def test_the_card_carries_firmness_and_the_rework_share(board):
    got = models.Progress.model_validate(_progress(board, _drive(time.time() - 3600)))
    assert got.eta.firm in ("firm", "rough") and got.eta.rework is not None
    assert got.eta.lo <= got.eta.finish_at <= got.eta.hi
