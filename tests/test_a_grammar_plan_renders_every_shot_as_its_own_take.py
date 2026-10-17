"""Every shot is its own take on a plan of the anime-TV grammar (2026-10-17).

The packer (`episode_takes.groups`) still joins consecutive same-setup shots
under 8 s into one take -- a legacy of the i2v boards; ONE PER TAKE has refused
every such pack since episode 4, and the holds cure grew beats until a pair
cleared 8.3 s.  The grammar cuts by size: an impact insert of 1-3 s beside a
reaction of 3 s is the point, and growing it to 8 s would undo it.  So a
grammar plan never packs (`budget_for` is 0 s): the take builder, its dry build
and ONE PER TAKE read the same budget, and a legacy plan keeps 8 s.  $0."""
from __future__ import annotations

import inspect
from types import SimpleNamespace

from studio import episode_takes as tk


def _rows(lengths):
    t, out = 0.0, []
    for i, sec in enumerate(lengths):
        out.append({"index": i, "t_start": t, "seconds": sec, "setup": "room", "cuts": []})
        t += sec
    return out


def test_a_grammar_plan_never_packs_two_shots():
    rows = _rows([2.0, 3.0, 2.5])
    assert tk.groups(rows, tk.budget_for(SimpleNamespace(grammar="anime_tv"))) == [[0], [1], [2]]


def test_a_legacy_plan_keeps_the_eight_second_packer():
    assert tk.budget_for(SimpleNamespace(grammar="")) == tk.BUDGET
    assert tk.groups(_rows([2.0, 3.0, 2.5]), tk.budget_for(SimpleNamespace())) == [[0, 1], [2]]


def test_the_builder_its_dry_build_and_the_battery_read_one_budget():
    from scripts.episode import plan_check, takes_r2v
    assert "budget_for(episode)" in inspect.getsource(takes_r2v.cards)
    assert "budget_for(episode)" in inspect.getsource(takes_r2v.dry_faults)
    assert "budget_for(ep)" in inspect.getsource(plan_check.main)
