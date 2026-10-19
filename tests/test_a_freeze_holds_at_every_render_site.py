"""INCIDENT 2, 2026-10-19 12:29 PDT: the owner's repair rerun of Jekyll HEL ep01 (52e90bc: the delivered
takes frozen inside the repair window) was killed on "queueing 1 takes in one go: T01".  The dry check had
said "step 09 renders 0" and "retake ladder: 2/2 episode rounds -> spent", but step 09's CPU lane measured
the 28 frozen takes, take_overlap.early_cures routed T01's gait row ('feet slide', HARD) to the plan's verb,
and the EARLY round queued a retake of frozen T01 -- the freeze guarded only the terminal's best-draw swap.
ladder.json gained the round {"why": "batched_cures: gait", "faults": {"1": ["gait"]}, "early": true}
before any byte landed (T01 restored by hand, sha a4b22b62).

The rule now: under the repair that governs (take_currency.frozen), a frozen take is put in NO cure batch --
take_ladder.route skips it, so the early round, the batched rung and the climb's `curable` all see none --
its terminal is keep_best flagged (never a still), step 11's master retake refuses it, and take_dq
--attempts never ranks an archived draw over it.  Outside a repair the ladder is exactly as before.

And the stale round: a ladder.json round counts only when bytes landed for it (a take it names, or an
archived draw of one, written after it launched) or it was launched by this process (in flight); the
12:29 round landed nothing and no longer counts, blocks nothing and unblocks nothing.

Replayed on ep01's records (tests/fixtures/ep01_replay/repair_rerun/): T01.dq.json, the delivered
manifest.json, the killed run's repair.json, ladder.json and attempts.json as the 12:29 kill left them.
A stand-in file carries T01's sha a4b22b62.  No GPU, no ComfyUI, no network."""
from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from types import SimpleNamespace

import pytest

from studio import repair_clock, take_ladder, take_overlap
from studio import take_currency as tc
from studio.judges import take_eye
from studio.judges.verdict import Fault, Verdict

FIX = Path(__file__).parent / "fixtures" / "ep01_replay" / "repair_rerun"
T01_SHA8 = "a4b22b62"
"""T01.mp4 as delivered: manifest.json and T01.dq.json both name these bytes (sha-verified 2026-10-19)."""
T01_MTIME, T21_MTIME = 1_792_374_948, 1_792_379_701
"""ep01's T01.mp4 (restored by a move: its 2026-10-18 18:55 mtime) and T21.mp4 (the 20:14 round's render)."""
RETRY_STAMP = 1_792_437_058.0
"""ep01's clock_reset.json, 2026-10-19T12:10:58 PDT: the rounds the next launch reads begin here."""


@pytest.fixture
def ep01(tmp_path, monkeypatch):
    """ep01's home with T01 as delivered, its dq record (the gait row), the manifest and a bare plan."""
    home = tmp_path / "book" / "episodes" / "ep01"
    room = home / "takes" / "r2v"
    (room / "attempts").mkdir(parents=True)
    (room / "T01.mp4").write_bytes(b"restored T01")
    os.utime(room / "T01.mp4", (T01_MTIME, T01_MTIME))
    shutil.copy(FIX / "T01.dq.json", room / "T01.dq.json")
    shutil.copy(FIX / "manifest.json", home / "manifest.json")
    (home / "plan.json").write_text(json.dumps({"shots": [], "lines": []}), encoding="utf-8")
    monkeypatch.setattr(tc, "sha8_of", lambda p: T01_SHA8 if Path(p).read_bytes() == b"restored T01"
                        else "ffffffff")
    return SimpleNamespace(home=home, room=room)


def in_repair(home) -> None:
    shutil.copy(FIX / "repair.json", Path(home) / repair_clock.WINDOW)


def t01_verdict() -> Verdict:
    """The take eye's dq rows over T01, as step 09's CPU lane reads them."""
    faults = take_eye.dq_faults(1, json.loads((FIX / "T01.dq.json").read_text(encoding="utf-8")))
    return Verdict(judge=take_eye.NAME, version=take_eye.VERSION, passed=False, faults=faults,
                   confidence=1.0, reads=1)


# ---- the router: the one decision every batch is built from -----------------------------------

def test_outside_a_repair_t01s_gait_routes_to_the_plans_verb(ep01):
    assert sorted(take_ladder.route(t01_verdict(), ep01.room)["gait_verb"]) == [1]


def test_inside_the_repair_frozen_t01_routes_to_no_cure(ep01):
    in_repair(ep01.home)
    assert tc.frozen(ep01.room / "T01.mp4", ep01.home) == "delivered"
    assert take_ladder.route(t01_verdict(), ep01.room) == {}


def test_after_the_repairs_drive_the_closed_row_still_keeps_t01_out(ep01):
    in_repair(ep01.home)
    repair_clock.close(ep01.home)
    assert take_ladder.route(t01_verdict(), ep01.room) == {}


def test_a_window_handed_in_decides_instead_of_the_disk(ep01):
    window = json.loads((FIX / "repair.json").read_text(encoding="utf-8"))
    assert take_ladder.route(t01_verdict(), ep01.room, window=window) == {}
    in_repair(ep01.home)
    assert sorted(take_ladder.route(t01_verdict(), ep01.room, window=None)["gait_verb"]) == [1]


# ---- the early round (the 12:29 site) ---------------------------------------------------------

def test_outside_a_repair_the_early_round_orders_t01s_gait_cure(ep01):
    cures = take_overlap.early_cures(ep01.room, [1])
    assert {i: cure for i, (cure, _) in cures.items()} == {1: "gait_verb"}


def test_inside_the_repair_the_early_round_orders_nothing(ep01):
    in_repair(ep01.home)
    assert take_overlap.early_cures(ep01.room, [1], RETRY_STAMP) == {}


# ---- the climb and its batched rung ------------------------------------------------------------

def test_the_climb_is_not_curable_on_frozen_takes_alone(ep01):
    assert take_ladder.still_curable(ep01.room, t01_verdict())
    in_repair(ep01.home)
    assert not take_ladder.still_curable(ep01.room, t01_verdict())


def rung_renders(ep01, monkeypatch) -> list:
    """The batched rung taken once on T01's verdict; the takes it would render (render_round recorded)."""
    rendered = []
    monkeypatch.setattr(take_ladder, "batch_of", lambda ctx, rung, renders, room, since: (renders, ""))
    monkeypatch.setattr(take_ladder, "write_edits", lambda *a: None)
    monkeypatch.setattr(take_ladder, "render_round",
                        lambda ctx, rung, kept, *a: rendered.append(sorted(kept)) or 1.0)
    ctx = SimpleNamespace(home=ep01.home)
    take_ladder.rungs(ctx, None, "--approved=render").take(take_ladder.BATCH, 0, t01_verdict())
    return rendered


def test_outside_a_repair_the_batched_rung_renders_t01(ep01, monkeypatch):
    assert rung_renders(ep01, monkeypatch) == [[1]]


def test_inside_the_repair_the_batched_rung_renders_nothing(ep01, monkeypatch):
    in_repair(ep01.home)
    assert rung_renders(ep01, monkeypatch) == []


# ---- the terminal still JUDGES and signs it ----------------------------------------------------

def hard_on_t01() -> Verdict:
    return Verdict(judge="take_eye", version="1", passed=False, confidence=1.0, reads=1,
                   faults=[Fault(kind="frozen-whole", where="T01")])


def narration_plan() -> SimpleNamespace:
    return SimpleNamespace(lines=[], turn=lambda: SimpleNamespace(index=9), button=lambda: SimpleNamespace(shot=9))


def still_ready(monkeypatch, ep01) -> list:
    """A passed panel, a free still slot and a short shot: outside a repair T01 would be held as a still."""
    held = []
    monkeypatch.setattr(take_ladder, "still_for", lambda home, i, fs: ep01.home / "storyboard" / "shot_01.png")
    monkeypatch.setattr(take_ladder, "placed_seconds", lambda home, i: 2.0)
    monkeypatch.setattr(take_ladder, "write_still", lambda home, i, panel, s, why: held.append(i))
    return held


def test_outside_a_repair_a_hard_narration_take_is_held_as_a_still(ep01, monkeypatch):
    held = still_ready(monkeypatch, ep01)
    settled = take_ladder.terminal(ep01.home, narration_plan(), hard_on_t01(), [0, 1, 2])
    assert held == [1] and settled.terminal == "still"


def test_inside_the_repair_a_frozen_take_is_kept_flagged_never_a_still(ep01, monkeypatch):
    in_repair(ep01.home)
    held = still_ready(monkeypatch, ep01)
    settled = take_ladder.terminal(ep01.home, narration_plan(), hard_on_t01(), [0, 1, 2])
    assert held == [] and settled.terminal == "keep_best"
    assert [f.evidence["settled"] for f in settled.faults] == ["keep_best"]


# ---- step 11's master retake and take_dq's --attempts ranking ------------------------------------

def master_retake(ep01, monkeypatch) -> list:
    from scripts.episode import step_09_shoot
    from studio import gate_policy, master_ladder
    calls = []
    monkeypatch.setattr(take_ladder, "retake", lambda *a, **k: calls.append(a[1]))
    monkeypatch.setattr(step_09_shoot, "approved", lambda p: "--ok")
    monkeypatch.setattr(gate_policy, "of", lambda stage, gate: None)
    ctx = SimpleNamespace(home=ep01.home, stage="episode", log=lambda *a, **k: None)
    master_ladder.retake_through_take_ladder(ctx, 1, SimpleNamespace(faults=[]))
    return calls


def test_outside_a_repair_step_11_retakes_the_shot(ep01, monkeypatch):
    assert master_retake(ep01, monkeypatch) == [[1]]


def test_inside_the_repair_step_11_never_retakes_a_frozen_take(ep01, monkeypatch, capsys):
    in_repair(ep01.home)
    assert master_retake(ep01, monkeypatch) == []
    assert "KEPT T01" in capsys.readouterr().out


def late_checks(ep01, monkeypatch) -> list[tuple]:
    """take_dq as a retake round asks it over T01 and a fresh T02 the round left unmeasured."""
    (ep01.room / "T02.mp4").write_bytes(b"a fresh T02")
    calls = []
    monkeypatch.setattr(take_ladder, "measured", lambda ctx, script, clock, suffix, *a: calls.append(a))
    take_ladder.measure_late(SimpleNamespace(home=ep01.home), [1, 2])
    return calls


def test_outside_a_repair_a_rounds_late_checks_rank_every_draw(ep01, monkeypatch):
    assert late_checks(ep01, monkeypatch) == [("1", "2", "--attempts")]


def test_inside_the_repair_take_dq_never_ranks_a_draw_over_a_frozen_take(ep01, monkeypatch):
    """take_dq --attempts keeps the best-scored draw as T<nn>.mp4: a frozen take is checked alone.  The guard
    lives in the callers: take_dq.py is measuring code, and an edit there re-measures all 28 takes."""
    in_repair(ep01.home)
    assert late_checks(ep01, monkeypatch) == [("2", "--attempts"), ("1",)]


def test_the_cpu_lane_never_hands_a_frozen_take_to_attempts(ep01):
    assert take_overlap.ranked(ep01.room, [1, 2], True, set()) == [1, 2]
    assert take_overlap.ranked(ep01.room, [1, 2], False, {2}) == [2]
    in_repair(ep01.home)
    assert take_overlap.ranked(ep01.room, [1, 2], True, set()) == [2]


# ---- the stale 12:29 round ----------------------------------------------------------------------

def killed_run(ep01, t21: bool = True) -> None:
    """ladder.json, attempts.json and the episode clock as the 12:29 kill left them; T21 as the 20:14 round
    rendered it."""
    shutil.copy(FIX / "ladder_1229.json", ep01.room / take_ladder.LADDER_FILE)
    shutil.copy(FIX / "attempts_1229.json", ep01.home / "attempts.json")
    shutil.copy(FIX / "clock_1229.jsonl", ep01.home / "clock.jsonl")
    shutil.copy(FIX / "clock_1229.open.json", ep01.home / "clock.open.json")
    if t21:
        (ep01.room / "T21.mp4").write_bytes(b"T21 of the 20:14 round")
        os.utime(ep01.room / "T21.mp4", (T21_MTIME, T21_MTIME))


def test_the_1229_round_landed_nothing_and_does_not_count(ep01):
    killed_run(ep01)
    rounds = json.loads((ep01.room / take_ladder.LADDER_FILE).read_text(encoding="utf-8"))["rounds"]
    assert [take_ladder.landed(ep01.room, r) for r in rounds] == [True, False]
    assert take_ladder.rounds_of(ep01.room, RETRY_STAMP) == 0
    assert take_ladder.rounds_of(ep01.room) == 1                     # the 20:14 round rendered T21: it counts


def test_the_stale_round_blocks_no_cure(ep01):
    killed_run(ep01)
    assert take_ladder.progressed(ep01.room, 1, ["gait"])            # its signature was never cured
    assert take_overlap.early_open(ep01.room, RETRY_STAMP)
    assert take_overlap.early_taken(ep01.room, RETRY_STAMP) == set()


def test_the_stale_round_unblocks_nothing_inside_the_repair(ep01):
    killed_run(ep01)
    in_repair(ep01.home)
    assert take_overlap.early_cures(ep01.room, [1], RETRY_STAMP) == {}
    assert take_ladder.episode_spent(ep01.home)                       # attempts.json's 2/2 still holds


def test_a_round_in_flight_in_this_process_counts_once(ep01):
    killed_run(ep01, t21=False)
    take_overlap.join_early(ep01.room, "batched_cures: rotation", {"2": ["rotation"]}, RETRY_STAMP)
    take_overlap.join_early(ep01.room, "batched_cures: rotation", {"3": ["rotation"]}, RETRY_STAMP)
    rounds = json.loads((ep01.room / take_ladder.LADDER_FILE).read_text(encoding="utf-8"))["rounds"]
    assert len(rounds) == 3 and rounds[-1]["faults"] == {"2": ["rotation"], "3": ["rotation"]}
    assert rounds[1]["faults"] == {"1": ["gait"]}                    # the stale round is never folded into
    assert take_ladder.rounds_of(ep01.room, RETRY_STAMP) == 1


def test_a_round_that_names_no_take_counts_as_before(tmp_path):
    room = tmp_path / "takes" / "r2v"
    room.mkdir(parents=True)
    (room / take_ladder.LADDER_FILE).write_text(json.dumps({"rounds": [{"why": "x", "at": 5.0}]}), encoding="utf-8")
    assert take_ladder.rounds_of(room) == 1


# ---- the dry check calls the deciders, never a counter --------------------------------------------

def dry_text(home, window) -> str:
    from scripts.episode import repair_dry_check as dry
    return "\n".join(dry.ladder_lines(home, window))


def test_the_dry_check_prints_an_empty_batch_for_frozen_t01(ep01):
    killed_run(ep01)
    text = dry_text(ep01.home, json.loads((FIX / "repair.json").read_text(encoding="utf-8")))
    assert "early round (take_overlap.early_cures" in text and "take ladder (take_ladder.route" in text
    assert text.count("batch none") == 2, text
    assert "T01 (gait)" in text and "keep_best" in text
    assert "batched_cures: gait (T01): landed nothing" in text


def test_outside_a_repair_the_dry_check_names_t01_in_both_batches(ep01):
    text = dry_text(ep01.home, None)
    assert text.count("batch T01") == 2, text


def test_the_dry_check_asks_the_router_itself(ep01, monkeypatch):
    monkeypatch.setattr(take_ladder, "route", lambda *a, **k: {})
    assert dry_text(ep01.home, None).count("batch none") == 2
