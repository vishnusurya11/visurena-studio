"""The panel verdict decides whether takes may be rendered, and it cannot
be passed by measuring nothing.

Audit items 4, 5, 6 and 36, measured 2026-09-22:
- `takes_r2v` never read panel_dq.json, so a failed panel went to the GPU;
- the panel runner skipped a missing panel and printed "0/0 panels pass";
- the night control was picked by any "dark" in the shot's prose, so 15 of
  ep09's 23 DAYLIGHT panels ("dark cedar", "dark brows") were judged against
  the night picture. The hour is the setup's, read from its own words.
"""
import json
import os
import time

from studio.panel_dq import at_night, panel_refusal


def test_night_is_read_from_the_setup_words():
    assert at_night("the sand-pits on Horsell Common at night in 1894")
    assert at_night("a lighted carriage, the gaslight falling on the seats")
    assert not at_night("a garden on a hot morning, a dark cedar at one corner")
    assert not at_night("hard midday sun; the brick reads dark red")


def write(path, rows):
    path.write_text(json.dumps(rows), encoding="utf-8")


def panels(tmp_path, n):
    out = []
    for i in range(n):
        p = tmp_path / f"shot_{i:02d}.png"
        p.write_bytes(b"png")
        out.append(p)
    return out


def test_a_clean_verdict_over_every_shot_lets_the_takes_run(tmp_path):
    shots = panels(tmp_path, 3)
    time.sleep(0.01)
    write(tmp_path / "panel_dq.json", [{"shot": i, "passed": True} for i in range(3)])
    assert panel_refusal(tmp_path / "panel_dq.json", shots, [0, 1, 2]) is None


def test_no_verdict_refuses(tmp_path):
    assert "no panel verdict" in panel_refusal(tmp_path / "panel_dq.json", panels(tmp_path, 2), [0, 1])


def test_a_failed_panel_refuses_and_names_it(tmp_path):
    shots = panels(tmp_path, 2)
    time.sleep(0.01)
    write(tmp_path / "panel_dq.json", [{"shot": 0, "passed": True}, {"shot": 1, "passed": False}])
    assert "1" in panel_refusal(tmp_path / "panel_dq.json", shots, [0, 1])


def test_a_verdict_that_skipped_a_shot_refuses(tmp_path):
    shots = panels(tmp_path, 3)
    time.sleep(0.01)
    write(tmp_path / "panel_dq.json", [{"shot": 0, "passed": True}, {"shot": 1, "passed": True}])
    assert "2" in panel_refusal(tmp_path / "panel_dq.json", shots, [0, 1, 2])


def test_an_empty_verdict_refuses(tmp_path):
    shots = panels(tmp_path, 1)
    time.sleep(0.01)
    write(tmp_path / "panel_dq.json", [])
    assert panel_refusal(tmp_path / "panel_dq.json", shots, [0]) is not None


def test_a_panel_redrawn_after_its_verdict_refuses(tmp_path):
    shots = panels(tmp_path, 1)
    write(tmp_path / "panel_dq.json", [{"shot": 0, "passed": True}])
    later = time.time() + 5
    os.utime(shots[0], (later, later))
    assert "newer" in panel_refusal(tmp_path / "panel_dq.json", shots, [0])
