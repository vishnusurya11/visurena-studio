"""ep16 (2026-10-02): the take ladder's move substitution aimed at 'the first
clause of at_rest', split on commas -- but at_rest clauses are separated by
SEMICOLONS, so the whole paragraph became the aim ('The camera pushes in toward
Scattered sovereigns cover the lower left; the horse's bit stands at centre;
...').  The plan's motion lint refused it (M9) and the cure round crashed.
The aim is one short noun phrase: cut at the first clause mark, capped."""
from __future__ import annotations

from studio.take_ladder import aim_of, AIM_WORDS


def test_the_aim_is_one_clause_of_at_rest():
    at_rest = ("Scattered sovereigns cover the lower left; the horse's bit stands at centre; "
               "the brother's reaching arm enters from the right edge.")
    got = aim_of("The camera holds a locked-off frame", at_rest)
    assert ";" not in got and "," not in got
    assert len(got.split()) <= AIM_WORDS


def test_an_empty_at_rest_aims_at_the_figure():
    assert aim_of("The camera holds a locked-off frame", "") == "the figure"
