"""G-HOLE measures AT PLAN TIME exactly what step 05 measures after the voice
renders: `plan_gates.projected_place` IS `episode_timeline.place` fed projected
line seconds, so there is zero drift between the gate and the checker (ep18
shipped a plan projecting a 12.5 s hole that only timeline.py could refuse).
The fault row carries the load-bearing words 'hole in speech', which the cure
table already routes to the holds cure."""
from __future__ import annotations

from studio import episode_timeline as tl
from studio import plan_cures as pc
from studio import plan_gates as pg
from studio import speech_gap as sg
from studio.episode_spec import Episode, Line, Setup, Shot

RATE = 3.0
SETUPS = {"lab": Setup(described="a lab", cast=["a", "b"])}
NARR = ("Then we walked on together down the long corridor and neither of us "
        "spoke a word.")  # 17 words


def shot(i, section="friction", size="wide", faces=(), beat=0.0, coda=0.0):
    return Shot(index=i, section=section, setup="lab", size=size, faces=list(faces),
                frame="f", motion="m", beat_s=beat, coda_s=coda)


def episode_with_wordless_run() -> Episode:
    """Contract-valid, book-neutral; three wordless shots mid-plan project a
    hole of 9+ s between two narration lines."""
    shots = [shot(0, "hook", "medium_close", ["a"])]
    lines = [Line(index=0, kind="dialogue", speaker="a", shot=0,
                  text="You must not blame me if you do not get on with him at all.")]
    for k in range(22):
        section = "turn" if k == 14 else "friction"
        shots.append(shot(len(shots), section))
        lines.append(Line(index=len(lines), kind="narration", speaker="b",
                          text=NARR, shot=shots[-1].index))
        if k == 10:
            for _ in range(3):           # the wordless run: coda-only picture
                shots.append(shot(len(shots), coda=2.5))
    shots[-1] = shot(shots[-1].index, beat=1.5)
    shots.append(shot(len(shots), "button", "close", ["c"]))
    lines.append(Line(index=len(lines), kind="dialogue", speaker="c",
                      text="The question now is about blood.", shot=shots[-1].index))
    shots.append(shot(len(shots), "answer", coda=3.0))
    return Episode(number=1, title="t", protagonist="b", setups=SETUPS, shots=shots, lines=lines)


def test_the_gate_fires_on_the_projected_hole_at_the_margin_wall():
    ep = episode_with_wordless_run()
    rows = pg.hole_faults(ep, RATE)
    assert len(rows) == 1
    assert "G-HOLE" in rows[0] and "hole in speech" in rows[0]
    assert f"against {sg.MAX_GAP_S - sg.HOLE_MARGIN_S}" in rows[0]


def test_the_gate_is_step05s_own_measure():
    """Feeding the SAME per-line seconds to episode_timeline.place and to
    projected_place yields identical holes: the gate IS step 05's measure."""
    ep = episode_with_wordless_run()
    measured = {l.index: l.words() / RATE for l in ep.lines}
    wall = sg.MAX_GAP_S - sg.HOLE_MARGIN_S
    assert sg.over_wall(pg.projected_place(ep, RATE), wall) \
        == sg.over_wall(tl.place(ep, measured), wall)


def test_a_clean_plan_raises_no_hole_fault():
    ep = episode_with_wordless_run()
    for s in ep.shots:
        if not ep.lines_of(s.index) and s.section == "friction":
            s.coda_s = 0.5               # the run shrinks under the wall
    assert pg.hole_faults(ep, RATE) == []


def test_the_fault_row_routes_to_the_holds_cure():
    ep = episode_with_wordless_run()
    row = pg.hole_faults(ep, RATE)[0]
    assert pc.cure_for(row) == "holds"
    assert pc.cure_for("G-HOLE shots 3-5: projected hole in speech") == "holds"
