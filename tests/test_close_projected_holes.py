"""The rewritten holds() closes a projected hole by the checker's own numbers:
step 3b's approximate coda+unvoiced-run model (which missed beat_s, the
2xHANDLE seam, and voiced-to-voiced holes) is replaced by
_close_projected_holes, which measures with the same placement G-HOLE and
step 05 read.  Floors hold: a wordless shot keeps coda_s >= 0.5 (the
contract's no-line-no-beat rule), the pre-button shot keeps beat_s >= 1.0,
the button shot keeps coda_s >= 0.6."""
from __future__ import annotations

from studio import plan_cures as pc
from studio import speech_gap as sg
from studio.episode_spec import Episode, Line, Setup, Shot

RATE = 2.5
WALL = sg.MAX_GAP_S - sg.HOLE_MARGIN_S
NARR = ("Then we walked on together down the long corridor and neither of us "
        "spoke a word.")  # 17 words


def shot(i, section="friction", size="wide", faces=(), setup="lab", beat=0.0, coda=0.0):
    return Shot(index=i, section=section, setup=setup, size=size, faces=list(faces),
                frame="f", motion="m", beat_s=beat, coda_s=coda)


def ep18_shaped_doc() -> dict:
    """Contract-valid, book-neutral: a voiced shot then THREE wordless shots
    at coda 3.5 project a 12+ s hole in speech (the ep18 shape)."""
    setups = {name: Setup(described="a room", cast=["a", "b"])
              for name in ("lab", "hall", "yard", "stair", "attic")}
    rooms = list(setups)
    shots = [shot(0, "hook", "medium_close", ["a"])]
    lines = [Line(index=0, kind="dialogue", speaker="a", shot=0,
                  text="You must not blame me if you do not get on with him at all.")]
    for k in range(22):
        section = "turn" if k == 14 else "friction"
        shots.append(shot(len(shots), section, setup=rooms[k // 5]))
        lines.append(Line(index=len(lines), kind="narration", speaker="b",
                          text=NARR, shot=shots[-1].index))
        if k == 10:
            for _ in range(3):
                shots.append(shot(len(shots), setup=rooms[k // 5], coda=3.5))
    shots[-1] = shot(shots[-1].index, setup=shots[-1].setup, beat=1.5)
    shots.append(shot(len(shots), "button", "close", ["c"], setup=rooms[4]))
    lines.append(Line(index=len(lines), kind="dialogue", speaker="c",
                      text="The question now is about blood.", shot=shots[-1].index))
    shots.append(shot(len(shots), "answer", setup=rooms[4], coda=3.0))
    return Episode(number=1, title="t", protagonist="b", setups=setups,
                   shots=shots, lines=lines).model_dump()


def wordless_of(doc: dict) -> list[dict]:
    voiced = {l["shot"] for l in doc["lines"]}
    return [s for s in doc["shots"] if s["index"] not in voiced]


def test_the_rewritten_holds_closes_a_twelve_second_projected_hole():
    doc = ep18_shaped_doc()
    holes = sg.over_wall(pc._projection(doc, RATE), WALL)
    assert holes and max(b - a for a, b, _ in holes) > 12.0      # the ep18 state
    cured = pc.holds(doc, rate=RATE)
    assert sg.over_wall(pc._projection(cured, RATE), WALL) == []


def test_the_cure_keeps_every_floor_and_the_contract():
    doc = ep18_shaped_doc()
    cured = pc.holds(doc, rate=RATE)
    button = cured["lines"][-1]["shot"]
    by = {s["index"]: s for s in cured["shots"]}
    for s in wordless_of(cured):
        assert float(s["coda_s"]) >= 0.5, f"wordless shot {s['index']} lost its coda"
    assert float(by[button - 1]["beat_s"]) >= 1.0
    Episode.model_validate(cured)


def test_the_ep16_shaped_voiced_coda_hole_still_closes():
    """Old 3b's own case: the VOICED shot's long coda plus a silent successor."""
    a = {"index": 0, "setup": "a", "beat_s": 1.5, "coda_s": 2.5}
    b = {"index": 1, "setup": "a", "beat_s": 1.0, "coda_s": 2.1}
    c = {"index": 2, "setup": "a", "beat_s": 0.1, "coda_s": 0.1}
    doc = {"shots": [a, b, c], "lines": [{"shot": 0, "text": "two words"},
                                         {"shot": 2, "text": "one line here"}]}
    cured = pc.holds(doc, rate=RATE)
    assert sg.over_wall(pc._projection(cured, RATE), WALL) == []


def test_the_floors_name_the_button_and_the_wordless_shots():
    doc = {"shots": [{"index": 0}, {"index": 1}, {"index": 2}],
           "lines": [{"shot": 0, "text": "a line"}, {"shot": 2, "text": "the button"}]}
    floors = pc._floors(doc)
    assert floors[(1, "coda_s")] == 0.5      # wordless
    assert floors[(1, "beat_s")] == 1.0      # pre-button
    assert floors[(2, "coda_s")] == 0.6      # button rest
    assert floors[(0, "coda_s")] == 0.0      # voiced


def test_shave_cuts_largest_first_and_never_below_a_floor():
    s0 = {"index": 0, "coda_s": 2.0, "beat_s": 0.5}
    s1 = {"index": 1, "coda_s": 0.5, "beat_s": 0.0}
    floors = {(0, "coda_s"): 0.0, (0, "beat_s"): 0.0, (1, "coda_s"): 0.5, (1, "beat_s"): 0.0}
    cut = pc._shave([(s0, "coda_s"), (s0, "beat_s"), (s1, "coda_s"), (s1, "beat_s")],
                    2.2, floors)
    assert cut == 2
    assert s0["coda_s"] == 0.0 and s0["beat_s"] == 0.3
    assert s1["coda_s"] == 0.5                                   # at its floor, untouched
