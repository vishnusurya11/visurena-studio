"""G-STAGE (AREA 4, 2026-10-05): a plan that shows a machine or creature by a
bare word ("tripod", "a Martian wading") without the card name in the prose and
the pid in Setup.props stages a humanoid character sheet -- or nothing -- and
the drawer invents a naked humanoid.  The gate refuses at the plan, before
anything renders.  Pure functions, hand-built vocab, no disk, no API, $0."""
from __future__ import annotations

from types import SimpleNamespace

from studio import plan_gates as pg

VOCAB = {
    "machines": {"fighting_machine": {
        "name": "the Martian fighting-machine",
        "terms": ["giant", "martian", "tripod"],
        "physical": "A walking engine of glittering metal, higher than many houses."}},
    "creatures": {"martians": ["martian"]},
}


def shot(frame="", at_rest="", motion="", end="", setup="lane", index=3):
    return SimpleNamespace(index=index, frame=frame, at_rest=at_rest, motion=motion,
                           end=end, setup=setup, faces=[], cuts=[])


def setup_of(props=(), described="", crowd="", geometry=""):
    return SimpleNamespace(props=list(props), described=described, crowd=crowd,
                           geometry=geometry, cast=[])


def ep(shots, **setups):
    return SimpleNamespace(shots=shots, setups=setups)


def test_a_bare_machine_word_with_no_staged_sheet_is_a_fault():
    episode = ep([shot(frame="the tripod strides over the lane")], lane=setup_of())
    found = pg.stage_faults(episode, VOCAB)
    assert len(found) == 1
    assert "G-STAGE" in found[0] and "shot 3" in found[0]
    assert "fighting_machine" in found[0] and "stages no sheet" in found[0]


def test_a_staged_pid_shown_by_the_bare_word_wants_its_card_name():
    episode = ep([shot(frame="the tripod strides over the lane")],
                 lane=setup_of(props=["fighting_machine"]))
    found = pg.stage_faults(episode, VOCAB)
    assert len(found) == 1
    assert "bare word 'tripod'" in found[0] and "not its card name" in found[0]


def test_the_card_name_with_the_pid_staged_is_clean():
    episode = ep([shot(frame="the Martian fighting-machine strides over the lane")],
                 lane=setup_of(props=["fighting_machine"]))
    assert pg.stage_faults(episode, VOCAB) == []


def test_a_setup_text_machine_word_faults_on_the_setup():
    episode = ep([], lane=setup_of(described="A tripod towers beyond the hedge."))
    found = pg.stage_faults(episode, VOCAB)
    assert len(found) == 1 and "setup lane" in found[0]


def test_a_bare_creature_word_is_a_fault():
    episode = ep([shot(frame="a Martian wading up the Thames", index=14)],
                 lane=setup_of(props=["fighting_machine"]))
    found = pg.stage_faults(episode, VOCAB)
    assert any("bare creature word 'martian'" in f and "shot 14" in f for f in found)


def test_a_creature_word_inside_a_card_name_never_re_fires():
    episode = ep([shot(frame="the Martian fighting-machine wades the Thames")],
                 lane=setup_of(props=["fighting_machine"],
                               described="The Martian fighting-machine's pit smokes."))
    assert [f for f in pg.stage_faults(episode, VOCAB) if "creature" in f] == []


def test_a_bare_creature_word_in_setup_text_is_a_setup_keyed_fault():
    episode = ep([], lane=setup_of(described="A Martian stands beyond the hedge."))
    found = [f for f in pg.stage_faults(episode, VOCAB) if "creature" in f]
    assert len(found) == 1 and found[0].startswith("G-STAGE setup lane")
