"""G-RISE: the episode's one bird's-eye is a rise from a wide or full, it carries no dialogue line, and the
voice holds it 3-5 s (shot framework A1, 2026-10-21).

Evidence (FRAMEWORK.md section 2): ep01 shot 18 shipped a crane_up from an eye-level wide (verdict 95); the
prompt bench's T18 rose 4 of 4 by eye and on the band meter, 0 clones, the walkers ending 22-35 px -- so a
rise never carries the face-acting (F2: the face reads on the next cut).  One per episode, on the text's own
vantage.  The count and the dialogue rows are the writer's to move (`framing_faults`); the seconds are the
voice's (`voice_advisories`).  An insert rise (A7) is not counted."""
from __future__ import annotations

from types import SimpleNamespace

from studio import framing_grammar as fg, grammar_battery as gb

RISE = "The camera rises above the two walkers, looking down over the street across the whole shot; they walk"
LOCKED = "The camera holds a locked-off frame across the whole shot; he turns his head; his hand lifts"


def _shot(i, size="wide", motion=RISE, faces=("lead",)):
    return SimpleNamespace(index=i, size=size, faces=list(faces), motion=motion, section="setup",
                           frame=f"{size} of the lead", camera="", at_rest="", end="", cuts=[],
                           beat_s=0.0, coda_s=0.0)


def _ep(shots, lines=()):
    return SimpleNamespace(shots=list(shots), lines=list(lines), omit=[])


def _line(i, shot, kind="dialogue"):
    return SimpleNamespace(index=i, shot=shot, kind=kind, speaker="lead", text="one two three")


def test_one_rise_from_a_wide_is_clean():
    assert fg.rise_faults(_ep([_shot(0), _shot(1, "close", LOCKED)])) == []


def test_two_rises_fault():
    got = fg.rise_faults(_ep([_shot(0), _shot(1, "close", LOCKED), _shot(2, "full")]))
    assert [f.split(":")[0] for f in got] == ["G-RISE shot 2"]


def test_an_insert_rise_is_not_the_birds_eye():
    assert fg.rise_faults(_ep([_shot(0), _shot(1, "insert", faces=())])) == []


def test_a_rise_with_dialogue_faults():
    got = fg.rise_faults(_ep([_shot(0)], [_line(0, 0)]))
    assert [f.split(":")[0] for f in got] == ["G-RISE shot 0"]
    assert fg.rise_faults(_ep([_shot(0)], [_line(0, 0, "narration")])) == []


def test_a_six_second_rise_is_advised():
    ep = _ep([_shot(0), _shot(1, "close", LOCKED)])
    assert [f.split(":")[0] for f in fg.rise_advisories(ep, {0: 6.0, 1: 2.0})] == ["G-RISE shot 0"]
    assert fg.rise_advisories(ep, {0: 4.0, 1: 9.0}) == []


def test_the_battery_reads_the_rise_where_the_writer_and_the_voice_own_it():
    ep = _ep([_shot(0), _shot(1, "full")], [_line(0, 0)])
    assert any(f.startswith("G-RISE") for f in gb.framing_faults(ep, {}))
    assert any(f.startswith("G-RISE") for f in gb.voice_advisories(ep, {0: 6.0, 1: 4.0}))


def test_the_brief_band_names_the_rise():
    band = fg.band()
    assert band["max_rises"] == 1 and band["rise_seconds"] == [3.0, 5.0]
