"""G-HOLD (advisory): a silent locked shot at medium, medium close or close, planned at
`stillness.MIN_SECONDS` or more, is named with its cure -- split the line across a reaction or an insert
(shot framework ruling 1 and F5, 2026-10-21).

Locked shots carrying only a gentle actor verb were alive 0 of 6 times on Kawajiri Wuli: ep01 T13 94-95 %
frozen, T26 86 %, the B1 controls of T10 78 % and T15 81 %.  A push un-froze them and overran 4 of 8, so the
cut is the cure, at plan time, for $0.  The stillness wall refuses only takes of 5 s or longer, so a hold
under 5 s is the anime-TV grammar itself.  Advisory: the voice sets the seconds.
Fixture: tests/fixtures/shot_framework/ (ep01 plan and placement)."""
from __future__ import annotations

import json
from types import SimpleNamespace

import shot_framework_fixtures as sf
from studio import episode_home, framing_grammar as fg, grammar_battery as gb, stillness

LOCKED = "The camera holds a locked-off frame across the whole shot; he turns his head; his hand lifts"


def ep01():
    episode = episode_home.load_plan(sf.BOOK, 1)
    placed = json.loads((sf.BOOK / "episodes" / "ep01" / "placed.json").read_text(encoding="utf-8"))
    return episode, gb.seconds(placed)


def named(rows):
    return {int(r.split(":")[0].split()[-1]) for r in rows if r.startswith("G-HOLD shot")}


def test_ep01_t10_and_t15_are_named():
    episode, secs = ep01()
    assert round(secs[10], 2) == 5.42 and round(secs[15], 2) == 6.54
    got = named(fg.hold_advisories(episode, secs))
    assert {10, 15} <= got
    assert all(secs[i] >= stillness.MIN_SECONDS for i in got)


def test_a_spoken_close_is_not_named():
    shot = SimpleNamespace(index=0, size="close", faces=["lead"], motion=LOCKED, still=False)
    talk = SimpleNamespace(index=0, shot=0, kind="dialogue")
    assert fg.hold_advisories(SimpleNamespace(shots=[shot], lines=[talk], omit=[]), {0: 6.0}) == []
    assert named(fg.hold_advisories(SimpleNamespace(shots=[shot], lines=[], omit=[]), {0: 6.0})) == {0}


def test_a_short_hold_a_wide_and_a_still_body_are_not_named():
    shots = [SimpleNamespace(index=0, size="medium", faces=["lead"], motion=LOCKED, still=False),
             SimpleNamespace(index=1, size="wide", faces=["lead"], motion=LOCKED, still=False),
             SimpleNamespace(index=2, size="close", faces=["lead"], motion=LOCKED, still=True)]
    ep = SimpleNamespace(shots=shots, lines=[], omit=[])
    assert fg.hold_advisories(ep, {0: 4.9, 1: 9.0, 2: 9.0}) == []


def test_the_battery_prints_the_hold_as_advice():
    episode, secs = ep01()
    assert named(gb.voice_advisories(episode, secs)) >= {10, 15}
    assert not any(f.startswith("G-HOLD") for f in gb.framing_faults(episode, secs))
