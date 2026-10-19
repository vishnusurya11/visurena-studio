"""Ship review of the repair freeze (fix round, 2026-10-19), two majors.

1. THE FREEZE ENDED BEFORE THE REPAIR DID.  Step 09 completing clears the owner's receipt
   (work_orders.clear_taken) and the drive's end closes repair.json (drive.end_row).  Any later drive of
   ep01 -- the autopilot's retry after a QC refusal, a crash relaunch, a resume after the G-STANDING park --
   then had no window, read every delivered take stale by P03's words and queued all 28: the 11:18 incident
   again.  Now the repair that governs the takes is the open window, else the LATEST closed repair row
   (repair.jsonl): an episode an owner repaired at 09 or later keeps the bytes its records name until an
   owner redo of 01-08 says otherwise.  An episode no owner ever repaired keeps today's rule exactly.

2. THE TERMINAL SWAPPED A DELIVERED TAKE.  The retry stamp re-reads the eye, the ladder is spent, and the
   terminal's keep_best_draws restored attempts/T21_fail2.mp4 (hard 1, Se 3.34) over the delivered T21
   (hard 1, Se 3.55) -- without its graph or dq record, so T21 then matched no record, was neither frozen
   nor current, and the next entry of step 09 rendered it.  Now a frozen take keeps its bytes at the
   terminal; outside a repair the best draw is restored as before.

Replayed on ep01's real T00 graph pair, dq record, manifest and window (tests/fixtures/ep01_replay/
repair_rerun/); T21's two draws carry the measures read off ep01's records.  No GPU, no ComfyUI."""
from __future__ import annotations

import json
import shutil
from pathlib import Path
from types import SimpleNamespace

from studio import repair_clock, take_ladder, work_orders
from studio import take_currency as tc
from studio.judges.verdict import Fault, Verdict
from tests.test_a_repair_freezes_its_delivered_takes import NEW_WORDS, card, ep01, in_repair  # noqa: F401

FIX = Path(__file__).parent / "fixtures" / "ep01_replay" / "repair_rerun"


def after_the_drive(home) -> dict:
    """Step 09 completed (its receipt cleared) and the drive ended (its window closed into repair.jsonl)."""
    in_repair(home)
    work_orders.note_taken(home, "09", 38)
    work_orders.clear_taken(home, "09")
    return repair_clock.close(home, now=lambda: 1_792_440_000.0)


# ---- 1. the freeze outlives the drive -------------------------------------------------------

def test_after_the_repairs_drive_ends_t00_is_still_frozen(ep01):
    after_the_drive(ep01.home)
    assert repair_clock.read(ep01.home) is None and not work_orders.recorded(ep01.home, "09")
    assert tc.governing(ep01.home)["steps"] == ["09"]
    assert tc.frozen(ep01.take, ep01.home) == "delivered"


def test_a_relaunch_after_the_repair_renders_nothing(ep01, monkeypatch):
    from scripts.episode import step_09_shoot as s09
    from scripts.episode import takes_r2v
    after_the_drive(ep01.home)
    room = ep01.home / "takes" / "r2v"
    (room / "prompts.json").write_text(json.dumps([card()]), encoding="utf-8")
    monkeypatch.setattr(s09, "card_pictures", lambda c, book, number: [])
    monkeypatch.setattr(s09, "episode_canvas", lambda ctx: ep01.canvas)
    monkeypatch.setattr(takes_r2v, "card_pictures", lambda c, book, number: [])
    monkeypatch.setattr(takes_r2v, "W", ep01.canvas[0])
    monkeypatch.setattr(takes_r2v, "H", ep01.canvas[1])
    ctx = SimpleNamespace(home=ep01.home, book_dir=ep01.home.parents[1], number=1)
    assert s09.stale_takes(ctx) == []
    current = lambda: takes_r2v.current_to(card(), ep01.take, ep01.home.parents[1], 1)  # noqa: E731
    assert not takes_r2v.wants_render(card(), ep01.take, {0: {"index": 0, "shots": [0]}}, None, current)


def test_an_owner_redo_of_an_earlier_step_ends_the_freeze(ep01):
    after_the_drive(ep01.home)
    repair_clock.open_window(ep01.home, {"08": 41}, 1_792_450_000.0)
    assert tc.frozen(ep01.take, ep01.home) is None
    repair_clock.close(ep01.home)
    assert tc.governing(ep01.home)["steps"] == ["08"] and tc.frozen(ep01.take, ep01.home) is None


def test_an_episode_never_repaired_keeps_todays_rule(ep01):
    assert tc.governing(ep01.home) is None
    assert not tc.held(NEW_WORDS, ep01.take, ep01.home, canvas=ep01.canvas)


def test_held_in_is_the_one_question_both_readers_ask(ep01):
    window = json.loads((FIX / "repair.json").read_text(encoding="utf-8"))
    assert tc.held_in(window, NEW_WORDS, ep01.take, ep01.home, canvas=ep01.canvas)
    assert not tc.held_in(None, NEW_WORDS, ep01.take, ep01.home, canvas=ep01.canvas)


# ---- is_current and its reason are one function ------------------------------------------------

def test_the_stale_reason_is_is_currents_own_answer(ep01):
    own = tc.prompt_of(json.loads((FIX / "T00.graph.json").read_text(encoding="utf-8")))
    cases = [(NEW_WORDS, ep01.canvas, "prompt"), (own, (576, 1024), "canvas"), (own, ep01.canvas, None),
             (own, None, None)]
    for built, canvas, why in cases:
        assert tc.stale_why(built, ep01.take, canvas=canvas) == why
        assert tc.is_current(built, ep01.take, canvas=canvas) is (why is None)


def test_an_absent_take_and_an_unknown_graph_have_their_reasons(ep01):
    tc.write_stub(tc.graph_of(ep01.take))
    assert tc.stale_why(NEW_WORDS, ep01.take) == "unknown provenance"
    ep01.take.unlink()
    assert tc.stale_why(NEW_WORDS, ep01.take) == "no take"


# ---- 2. the terminal keeps a frozen take ------------------------------------------------------

T21_DELIVERED, T21_FAIL2 = {"hard": 1, "Se": 3.55}, {"hard": 1, "Se": 3.34}
"""ep01's T21 and attempts/T21_fail2.mp4 as recorded_draw reads them (skeptic replay, 2026-10-19)."""


def t21_home(tmp_path) -> SimpleNamespace:
    """ep01's T21 as delivered (the manifest names its bytes), its second draw archived beside it."""
    home = tmp_path / "ep01"
    room = home / "takes" / "r2v"
    (room / "attempts").mkdir(parents=True)
    (room / "T21.mp4").write_bytes(b"delivered T21")
    (room / "attempts" / "T21_fail2.mp4").write_bytes(b"second draw")
    rows = [{"path": "episodes/ep01/takes/r2v/T21.mp4", "sha8": tc.sha8_of(room / "T21.mp4")}]
    (home / "manifest.json").write_text(json.dumps({"inputs": rows}), encoding="utf-8")
    said = []
    ctx = SimpleNamespace(home=home, book_dir=tmp_path, unit="ep01", log=lambda line, **k: said.append(line))
    return SimpleNamespace(home=home, room=room, ctx=ctx, said=said)


def draws(path: Path) -> dict:
    return T21_DELIVERED if path.read_bytes() == b"delivered T21" else T21_FAIL2


def t21_faulted() -> Verdict:
    return Verdict(judge="take_eye", version="1", passed=False, confidence=1.0, reads=1,
                   faults=[Fault(kind="warp", where="T21")])


def test_outside_a_repair_the_terminal_restores_the_lower_se_draw(tmp_path):
    ep = t21_home(tmp_path)
    take_ladder.keep_best_draws(ep.ctx, t21_faulted(), draws)
    assert (ep.room / "T21.mp4").read_bytes() == b"second draw"


def test_inside_the_repair_the_terminal_keeps_the_delivered_t21(tmp_path):
    ep = t21_home(tmp_path)
    shutil.copy(FIX / "repair.json", ep.home / repair_clock.WINDOW)
    take_ladder.keep_best_draws(ep.ctx, t21_faulted(), draws)
    assert (ep.room / "T21.mp4").read_bytes() == b"delivered T21"
    assert (ep.room / "attempts" / "T21_fail2.mp4").read_bytes() == b"second draw"
    assert ep.said and "T21" in ep.said[0] and "delivered" in ep.said[0]


def test_after_the_repair_the_terminal_still_keeps_it(tmp_path):
    ep = t21_home(tmp_path)
    shutil.copy(FIX / "repair.json", ep.home / repair_clock.WINDOW)
    repair_clock.close(ep.home)
    take_ladder.keep_best_draws(ep.ctx, t21_faulted(), draws)
    assert (ep.room / "T21.mp4").read_bytes() == b"delivered T21"


def test_the_best_pick_moves_nothing(tmp_path):
    ep = t21_home(tmp_path)
    best = take_ladder.pick_best(ep.room, 21, draws)
    assert best is not None and best.name == "T21_fail2.mp4"
    assert (ep.room / "T21.mp4").read_bytes() == b"delivered T21"
    assert take_ladder.pick_best(ep.room, 22, draws) is None
