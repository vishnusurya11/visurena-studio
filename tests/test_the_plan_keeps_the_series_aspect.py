"""G-ASPECT (2026-09-29): the plan's aspect is the series', never the writer's
guess.  ep14's writer draft carried 9:16 into a series of thirteen shipped 1:1
episodes; nothing checked it, and the episode rendered portrait at 2.88 s/frame
against 1.29-1.67 square -- ~7 extra hours -- with square panels letterboxed
into the portrait canvas."""
import json

from studio import canvas, plan_brief, plan_gates


def test_the_series_aspect_is_the_default_unless_series_json_says_otherwise(tmp_path):
    assert plan_gates.series_aspect(tmp_path) == canvas.DEFAULT
    (tmp_path / "series.json").write_text(json.dumps({"aspect": "9:16"}), encoding="utf-8")
    assert plan_gates.series_aspect(tmp_path) == "9:16"


def test_a_plan_off_the_series_aspect_is_refused_and_on_it_is_clean():
    class Ep:
        aspect = "9:16"
    faults = plan_gates.aspect_faults(Ep(), "1:1")
    assert len(faults) == 1 and faults[0].startswith("G-ASPECT") and "9:16" in faults[0]
    assert plan_gates.aspect_faults(Ep(), "9:16") == []


def test_the_writer_is_told_the_aspect():
    assert plan_brief.band()["aspect"] == canvas.DEFAULT
