"""`plan_check` runs G-MOVES and G-SOURCE: hard on a new-form plan, advisory before it.

Every plan written before the camera catalog fails G-MOVES, and reading one is
not endorsing it (`Episode.long_shots`): a plan with no `source` span prints
the faults and counts none; a plan that writes a span anywhere is refused on them."""
import inspect
import sys
from types import SimpleNamespace

sys.path.insert(0, "scripts/episode")

from studio.episode_spec import Episode, Setup, Shot

SETUPS = {"lane": Setup(described="a lane", cast=["walker"])}


def plan(sourced: bool, extras: int):
    shots = [Shot(index=i, section="setup", setup="lane", size="medium", frame="Medium on the walker.",
                  motion="The camera pushes in on the walker; his hand lifts; his head turns", extras=extras,
                  source=["the walker came on"] if sourced and i == 0 else [])
             for i in range(4)]
    ep = SimpleNamespace(shots=shots, setups=SETUPS)
    ep.new_form = lambda: Episode.new_form(ep)
    return ep


def test_the_check_names_the_catalog_gates():
    import plan_check

    src = inspect.getsource(plan_check)
    for name in ("moves_faults", "source_faults", "chapter_text", "catalog_gates"):
        assert name in src, name


def test_an_older_plan_prints_and_counts_nothing(capsys):
    import plan_check

    assert plan_check.catalog_gates(plan(sourced=False, extras=3), chapter="the lane") == 0
    out = capsys.readouterr().out
    assert "advisory" in out and "G-MOVES" in out and "G-SOURCE" in out


def test_a_new_form_plan_is_refused(capsys):
    import plan_check

    hard = plan_check.catalog_gates(plan(sourced=True, extras=3), chapter="the walker came on down the lane")
    assert hard >= 3 + 1 + 3  # three unsourced counts, one distinct-moves wall, three pushes running
    assert "advisory" not in capsys.readouterr().out
