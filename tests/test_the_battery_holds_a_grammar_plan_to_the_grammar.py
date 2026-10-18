"""The plan battery and the anime-TV grammar (2026-10-17).

- `plan_check.grammar_gate` counts the grammar's rows HARD on a plan that
  declares `grammar: anime_tv` and is not yet drawn, and prints them as advice
  on every older plan (the G-MOVES / `source` rule: reading a historical plan
  is not endorsing it).
- `--plan=<file>` runs the whole battery on a scratch plan beside plan.json
  (a re-plan is judged as an undrawn plan, never as the rendered one).
- G-MOVES under the grammar: a locked-off shot is the intended majority, so it
  leaves the share and the twice-running rule (05 section 2.6: the owner's
  complaint was ORBITS; a held frame is not an orbit).  At least 8 distinct
  moves still holds.
- G-VARIETY's six closes a person was fitted when closes were 20-30 % of the
  shots; the grammar asks 55 %, so a grammar plan's cap is 12.  $0."""
from __future__ import annotations

from types import SimpleNamespace

from studio import grammar_battery, plan_gates
from studio.episode_spec import Episode
from tests.test_episode_writer import canned_plan

LOCKED = "The camera holds a locked-off frame across the whole shot; he turns; his hand lifts"
MOVES = ["The camera pans across to the gate; he walks; the gate swings",
         "The camera tracks sideways to the right, past the wall; he walks; the dog runs",
         "The camera rises above the yard, looking down over the place; he runs; the cart rolls",
         "The camera pulls back from the cart, widening to show the place around it; he runs; the cart rolls",
         "The camera tilts up from the ground to the roof; the boy climbs; the slate slides",
         "The camera tracks beside the man; he walks; his coat swings",
         "The camera pushes in toward the lamp; his hand turns the wick; the flame rises"]


def _moves_ep(motions, grammar):
    shots = [SimpleNamespace(index=i, motion=m, camera="", still=False) for i, m in enumerate(motions)]
    return SimpleNamespace(shots=shots, lines=[], grammar=grammar)


def test_the_battery_reads_a_real_plan():
    ep = Episode.model_validate({**canned_plan(), "grammar": "anime_tv"})
    rows = grammar_battery.faults(ep, 2.45)
    assert any(r.startswith("G-ACT plan") for r in rows)        # the canned plan has no act-out
    assert any("G-SHOTS plan" in a for a in grammar_battery.advisories(ep, 2.45))


VOICE_ROWS = ("G-WIDE", "G-MEDIUM", "G-INSERT", "G-LOCKED")


def test_a_voice_measured_row_never_refuses_a_plan():
    """Jekyll Kawajiri ep01 (2026-10-18): the plan climb refused 69 lines for 30+ min
    over mediums at 7.04-7.96 s against 7.0, a wide at 4.58 against 4.0 and a locked
    share of 0.48 against 0.5.  Those seconds are the RECORDED VOICE's: no writer
    rewrite moves them, so they print as advice and never send the writer back
    (memory: the voice is the ruler; owner: cap every loop)."""
    ep = Episode.model_validate({**canned_plan(), "grammar": "anime_tv"})
    assert not [r for r in grammar_battery.faults(ep, 2.45) if r.startswith(VOICE_ROWS)]


def test_the_voice_measured_rows_still_print_as_advice():
    ep = Episode.model_validate({**canned_plan(), "grammar": "anime_tv"})
    assert any(a.startswith("G-LOCKED plan") for a in grammar_battery.advisories(ep, 2.45))


def test_the_gate_is_hard_on_a_grammar_plan_and_advice_on_a_legacy_one(tmp_path):
    from scripts.episode import plan_check
    grammar = Episode.model_validate({**canned_plan(), "grammar": "anime_tv"})
    legacy = Episode.model_validate(canned_plan())
    assert plan_check.grammar_gate(grammar, tmp_path, 3, 2.45) > 0
    assert plan_check.grammar_gate(legacy, tmp_path, 3, 2.45) == 0


def test_a_scratch_plan_is_judged_undrawn(tmp_path):
    from scripts.episode import plan_check
    (tmp_path / "episodes" / "ep03" / "takes").mkdir(parents=True)
    assert plan_check.rendered(tmp_path, 3)
    token = plan_check.PLAN_FILE.set("plan_v3.json")
    try:
        assert not plan_check.rendered(tmp_path, 3)
    finally:
        plan_check.PLAN_FILE.reset(token)


def test_locked_shots_running_leave_g_moves_on_a_grammar_plan():
    motions = MOVES[:4] + [LOCKED, LOCKED, LOCKED, LOCKED, LOCKED] + MOVES[4:]
    assert [f for f in plan_gates.moves_faults(_moves_ep(motions, "")) if "twice running" in f or "share" in f]
    assert plan_gates.moves_faults(_moves_ep(motions, "anime_tv")) == []


def test_a_grammar_plan_still_needs_eight_distinct_moves():
    motions = [LOCKED, MOVES[0], LOCKED, MOVES[1], LOCKED]
    assert any("distinct" in f for f in plan_gates.moves_faults(_moves_ep(motions, "anime_tv")))


def test_a_grammar_plan_may_close_on_a_lead_twelve_times():
    shots = [SimpleNamespace(index=i, size="close", faces=["lead"]) for i in range(12)]
    assert plan_gates.face_close_faults(SimpleNamespace(shots=shots, grammar="anime_tv")) == []
    assert plan_gates.face_close_faults(SimpleNamespace(shots=shots, grammar=""))
