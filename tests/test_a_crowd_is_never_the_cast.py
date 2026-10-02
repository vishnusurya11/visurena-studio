"""ep16 (2026-10-01): every shot said "many fugitives" while binding up to
three sheets, and neither builder forbade the crowd BEING the cast -- the grid
drawer filled crowds with cast copies (3 brothers, duplicate purple Misses)
and H3 minted clone parades even behind clean panels.  Both crowd clauses now
end by declaring every background figure a stranger to the named cast."""
from __future__ import annotations

from studio import episode_ref_official as ro
from studio.episode_seq_board import crowd_block
from studio.episode_spec import Setup


def setup_with(crowd: str) -> Setup:
    return Setup(described="x " * 95, geometry="y " * 65, location="l", view="v",
                 cast=[], crowd=crowd, ambience="wind", light="dusk light from the west")


def test_the_grid_crowd_block_declares_strangers():
    said = crowd_block(setup_with("many refugees press along the road"))
    assert "stranger" in said and "named" in said
    assert crowd_block(setup_with("a line of carts")) == ""     # no people, no block


def test_the_take_prompt_declares_strangers_once_when_life_exists():
    assert "stranger" in ro.strangers_line(True) and "distinct" in ro.strangers_line(True)
    assert ro.strangers_line(False) == ""
    # the life sentence itself stays one clean clause (L19 counts it)
    said = ro.life_sentence("many fugitives pass the gate", 0, 5, behind="<Subject 1>")
    assert "stranger" not in said and said.endswith(".")
