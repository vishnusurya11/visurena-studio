"""The episode has a sound layer (root cause 2026-09-26, D10).

`assemble.py` mixed every episode with an EMPTY cue list: twelve episodes of
voice and a violin, no gun, no shell, no river, no crowd.  The plan now names
its sounds -- a cue per event on its shot, an ambience per setup -- the mix lays
them, QC checks each one is actually heard, and a plan whose prose names a loud
event with no sound on that shot is refused before anything renders."""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace as NS

import pytest

from studio import episode_sound as es
from studio.episode_spec import Setup, Sound


def test_the_contract_takes_sounds_and_an_ambience():
    s = Sound(sound="six field guns firing together", at=0.5, seconds=3.0)
    assert s.gain_db == 0.0
    assert Setup(described="a meadow", ambience="larks, a slow river").ambience == "larks, a slow river"
    with pytest.raises(ValueError):
        Sound(sound="x", seconds=30.0)


def plan(shots, setups):
    return NS(number=13, where="Surrey, 1894", shots=shots, setups=setups)


def shot(index, setup="meadow", sounds=(), frame="", motion=""):
    return NS(index=index, setup=setup, sounds=list(sounds), frame=frame, motion=motion)


def test_the_plan_sounds_become_cues_on_their_shots():
    ep = plan([shot(0, sounds=[Sound(sound="a gun, distant", seconds=2.0)]), shot(1)],
              {"meadow": NS(ambience="larks")})
    (cue,) = es.cues_of(ep)
    assert cue.shot == 0 and cue.sound == "a gun, distant" and cue.seconds == 2.0


def test_the_layer_is_the_placed_cues_and_each_setups_ambience(tmp_path, monkeypatch):
    ep = plan([shot(0, sounds=[Sound(sound="a gun")]), shot(1, setup="river")],
              {"meadow": NS(ambience="larks"), "river": NS(ambience="")})
    placed = {"shots": [{"index": 0, "t_start": 0.0, "seconds": 5.0}, {"index": 1, "t_start": 5.0, "seconds": 4.0}]}
    monkeypatch.setattr(es.sfx_cues, "render_all", lambda cues, folder, seed, run=None, where="":
                        [(c, tmp_path / "gun.wav") for c in cues])
    beds = []
    monkeypatch.setattr(es.sfx_cues, "ambience", lambda sound, shots, folder, seed, run=None, where="":
                        beds.append((sound, [s["index"] for s in shots])) or [(0.0, tmp_path / "amb.wav")])
    layer = es.layer(tmp_path, ep, placed)
    assert layer == [(0.0, tmp_path / "gun.wav"), (0.0, tmp_path / "amb.wav")]
    assert beds == [("larks", [0])]


def test_a_cue_that_is_not_heard_is_a_fault(monkeypatch):
    ep = plan([shot(2, sounds=[Sound(sound="a shell burst", at=0.5)])], {})
    placed = {"shots": [{"index": 2, "t_start": 10.0, "seconds": 4.0}]}
    monkeypatch.setattr(es.sfx_cues, "event_db", lambda master, start, seconds: 2.0)
    rows = es.presence(Path("m.mp4"), ep, placed)
    assert rows == [{"shot": 2, "sound": "a shell burst", "at": 10.5, "db": 2.0, "ok": False}]


def test_a_loud_event_in_the_prose_needs_a_sound_on_its_shot():
    ep = plan([shot(4, frame="the battery fires; smoke rolls over the meadow"),
               shot(5, frame="he walks on", sounds=[])],
              {"meadow": NS(ambience="larks")})
    assert es.sound_faults(ep) == ["G-SOUND shot 4: the prose names 'fires' and the shot has no sound, "
                                   "measured 0 against 1"]


def test_a_setup_with_no_ambience_is_refused():
    ep = plan([shot(0)], {"meadow": NS(ambience="")})
    assert es.sound_faults(ep) == ["G-SOUND setup meadow: no ambience, measured 0 against 1"]


def test_qc_fails_a_master_where_a_planned_sound_is_not_heard():
    from tests.test_episode_qc_rollup import GOOD
    from scripts.episode import qc
    assert qc.verdict({**GOOD, "sound": [{"shot": 2, "ok": True}]})
    assert not qc.verdict({**GOOD, "sound": [{"shot": 2, "ok": True}, {"shot": 4, "ok": False}]})


def test_plan_check_runs_the_sound_gate(capsys):
    from scripts.episode import plan_check
    ep = plan([shot(0, frame="the guns fire")], {"meadow": NS(ambience="")})
    assert plan_check.sound_gates(ep) == 2
    assert "G-SOUND" in capsys.readouterr().out
