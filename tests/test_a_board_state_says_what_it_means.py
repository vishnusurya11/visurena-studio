"""The owner did not know what `flagged` or `stale` meant (2026-10-11).  Every
state the board shows carries one plain line saying what it means -- the
hover title on its pill and the department's legend -- and a blocked row's
line names what it waits on."""
from __future__ import annotations

from studio.command_center import views


def test_every_legend_state_has_a_plain_meaning():
    for _, word in views.LEGEND:
        assert views.MEANINGS[word] and len(views.MEANINGS[word]) < 120


def test_a_blocked_row_says_what_it_waits_on():
    assert views.meaning("blocked", "refs/04") == "blocked: waits on refs/04"
    assert views.meaning("blocked") == "blocked: " + views.MEANINGS["blocked"]


def test_stale_and_flagged_say_what_happened():
    """Plain words since the board review (2026-10-12, A6): no lease, terminal or row."""
    assert "stopped reporting" in views.meaning("stale")
    assert "not looked at" in views.meaning("flagged")
    assert views.meaning("nonsense") == "nonsense"



def test_the_department_page_says_what_each_shown_state_means(tmp_path, monkeypatch):
    import html

    from fastapi.testclient import TestClient

    from command_center_fixtures import make_app
    page = html.unescape(TestClient(make_app(tmp_path, monkeypatch)).get("/d/episode").text)
    assert 'title="flagged: ' + views.MEANINGS["flagged"] + '"' in page        # the pill's hover title
    assert 'data-testid="state-legend"' in page and views.MEANINGS["stale"] in page
    assert "<b>1</b> flagged" in page                                          # counted apart from done
