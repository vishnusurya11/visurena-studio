"""The take length was copied in four places (plan_cures TAKE_BUDGET_S 8.0 and its +0.3,
plan_gates PAIR_FLOOR_S 8.3, episode_takes.BUDGET): a cure that obeys 8.0 while the packer
reads another number loops.  One home: episode_takes.BUDGET; the rest derive from it."""
import subprocess
import sys

from studio import episode_takes as tk, plan_cures, plan_gates


def test_the_cures_budget_is_the_packers():
    assert plan_cures.TAKE_BUDGET_S == tk.BUDGET


def test_the_pair_floor_is_the_budget_plus_the_cures_margin():
    assert plan_gates.PAIR_FLOOR_S == tk.BUDGET + 0.3


def test_a_new_budget_reaches_every_copy():
    code = ("import studio.episode_takes as t; t.BUDGET = 9.0\n"
            "from studio import plan_cures, plan_gates\n"
            "print(plan_cures.TAKE_BUDGET_S, round(plan_gates.PAIR_FLOOR_S, 2))")
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True).stdout.split()
    assert out == ["9.0", "9.3"]


def test_the_pair_growth_reads_the_pair_floor_not_a_second_margin():
    import inspect
    assert "0.3" not in inspect.getsource(plan_cures._grow_pairs)
    assert "PAIR_FLOOR_S" in inspect.getsource(plan_cures._grow_pairs)


def test_the_dead_packer_is_gone_from_the_plan_check():
    sys.path.insert(0, "scripts/episode")
    import plan_check
    assert not hasattr(plan_check, "packed_shots")
