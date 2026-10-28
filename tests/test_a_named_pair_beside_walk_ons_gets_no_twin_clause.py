"""The grid never writes the twin clause the grid lint refuses.

Jekyll ep04 shot 17 staged its two named men (the lawyer and the inspector) beside eight walk-ons
(children and women at a gin palace).  `varied_group` skipped the clause only when the extras were fewer
than the count, so "the two men" got "The two men are two different individuals", and grid_lint's TWIN
rule refused the board: a generic noun ('men', 'women', 'people', 'figures') counted within the staged
faces is the bound pair, whatever the extras hold (2026-10-27).  A specific walk-on noun keeps it."""
from __future__ import annotations

from studio import grid_lint
from studio import storyboard_grid as sg


def test_a_named_pair_beside_many_extras_gets_no_clause():
    assert sg.varied_group("the two men small beside its step", named=2, extras=8) == ""


def test_walk_on_constables_still_get_the_clause():
    assert sg.varied_group("two constables stand by the door", named=2, extras=2).startswith("The two constables")


def test_what_the_builder_writes_the_lint_never_refuses():
    said = sg.varied_group("the two men small beside its step", named=2, extras=8)
    para = f"<image1> and <image2> stand by the cab. {said}"
    assert grid_lint.panel_faults(para, {"1", "2"}) == []
