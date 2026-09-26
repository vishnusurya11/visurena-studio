"""G-COVER and G-SHOUT (root cause 2026-09-26, B5 and B7).

ep12's plan stopped at paragraph 57 of 69: the chapter's TITLE event -- the
Heat-Ray destroying Weybridge and Shepperton, the scalding, the escape -- is not
in the episode, and no gate compared the plan with the chapter's end.  The same
plan filed "Get under the water!" as narration, so it was read as calm prose."""
from __future__ import annotations

from types import SimpleNamespace as NS

from studio import plan_gates as pg

PARAS = [f"paragraph {i} tells of the road and the pines and the hussars riding." for i in range(1, 10)]
PARAS.append("Then the heat-ray swept Weybridge and Shepperton and the river boiled.")
TITLE = "XII. WHAT I SAW OF THE DESTRUCTION OF WEYBRIDGE AND SHEPPERTON."


def plan(spans_per_shot, lines=()):
    shots = [NS(index=i, source=list(s)) for i, s in enumerate(spans_per_shot)]
    return NS(shots=shots, lines=list(lines))


def test_a_span_is_placed_on_its_paragraph():
    assert pg.span_paragraph("the heat-ray swept Weybridge and Shepperton", PARAS) == 10
    assert pg.span_paragraph("a sentence the chapter never wrote at all", PARAS) is None


def test_the_title_words_are_the_long_ones():
    assert pg.title_words(TITLE) == {"destruction", "weybridge", "shepperton"}
    assert pg.title_words("XIII. HOW I FELL IN WITH THE CURATE.") == {"curate"}


def test_the_last_title_paragraph():
    assert pg.title_last(PARAS, {"weybridge"}) == 10


def test_a_plan_that_stops_short_is_refused():
    short = plan([["paragraph 1 tells of the road"], ["paragraph 8 tells of the road"]])
    faults = pg.cover_faults(short, PARAS, TITLE)
    assert any("reaches paragraph 8 of 10" in f for f in faults)
    assert any("title" in f for f in faults)


def test_a_plan_that_reaches_the_end_is_clean():
    whole = plan([["paragraph 1 tells of the road"], ["the heat-ray swept Weybridge and Shepperton"]])
    assert pg.cover_faults(whole, PARAS, TITLE) == []


def test_a_shot_with_no_span_is_refused():
    faults = pg.cover_faults(plan([[], ["the heat-ray swept Weybridge and Shepperton"]]), PARAS, TITLE)
    assert faults == [pg.fault("G-COVER", "shot 0", "no chapter span places it in the chapter", 0, 1)]


def test_a_shout_filed_as_narration_is_refused():
    lines = [NS(index=16, kind="narration", text="Get under the water!"),
             NS(index=17, kind="narration", text="I ran into the river."),
             NS(index=20, kind="dialogue", text="Hit! They have hit it!")]
    assert pg.shout_faults(NS(lines=lines)) == [
        pg.fault("G-SHOUT", "line 16", "a shout filed as narration is read as calm prose; make it dialogue",
                 "narration", "dialogue")]


def test_the_chapter_paragraphs_come_from_the_source_copy(tmp_path):
    import json
    from studio import plan_brief
    room = tmp_path / "source" / "chapters"
    room.mkdir(parents=True)
    (room / "ch_13.json").write_text(json.dumps({"title": "XIII. THE CURATE.", "paragraphs": [
        {"n": 1, "text": "One."}, {"n": 2, "text": "Two."}]}), encoding="utf-8")
    assert plan_brief.chapter_paragraphs(tmp_path, 13) == ("XIII. THE CURATE.", ["One.", "Two."])
    assert plan_brief.chapter_paragraphs(tmp_path, 14) == ("", [])


def test_plan_check_runs_the_cover_gates(monkeypatch, capsys):
    from scripts.episode import plan_check
    paras = ["the road.", "the heat-ray swept Weybridge and Shepperton"]
    monkeypatch.setattr(plan_check.plan_brief, "chapter_paragraphs", lambda b, n: (TITLE, paras))
    short = plan([["the road."]], [NS(index=0, kind="narration", text="Run!")])
    assert plan_check.cover_gates(short, "book", 12) == 3
    assert "G-COVER" in capsys.readouterr().out
