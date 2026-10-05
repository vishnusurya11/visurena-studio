"""The unit page answers four questions in its first screen and a half
(research F): where is it (the head, the step bar with durations and failure
reasons), why is it looping (the pass timeline, the loop detector, the fault
trend), what does it look like (panel tiles by shot number with fault badges,
a lightbox with the shot's plan text) and what can I do (the actions and this
unit's orders).  No text over 160 characters renders open; the raw rows sit in
one collapsed band; the page stays small when a learning's note is 40 KB."""
from __future__ import annotations

import html
import re
from html.parser import HTMLParser

import pytest
from fastapi.testclient import TestClient

from command_center_fixtures import BIG_NOTE, CODEX, FRAME_1, LOOP_RUN, make_looping_app
from studio.command_center import models


@pytest.fixture()
def client(tmp_path, monkeypatch):
    return TestClient(make_looping_app(tmp_path, monkeypatch))


@pytest.fixture()
def page(client):
    return client.get(f"/d/episode/{CODEX}/ep08").text


def test_the_head_says_where_it_is_and_that_the_lease_is_alive(page):
    assert "The Loop Chapter" in page and "Will it ever leave the panels?" in page
    assert "08 panels" in page and "lease ok" in page and f'title="{LOOP_RUN}"' in page


def test_the_pass_timeline_has_one_segment_per_run(page):
    timeline = re.search(r'<div[^>]*data-testid="passes"[^>]*>(.*?)</div>', page, re.S).group(1)
    assert timeline.count('data-testid="pass"') == 4
    assert "09 refused" in timeline and "08 running" in timeline


def test_a_loop_is_named_when_three_runs_end_on_the_same_step(page):
    assert "LOOPING" in page and "3 of the last 3 runs ended at 09 refused" in page


def test_the_fault_trend_reads_the_gates_measures(page):
    assert re.search(r"EYE_PANELS</b>\s*<span[^>]*>24 ▸ 20 ▸ 17</span>", page) and "↘ improving" in page


def test_faults_are_grouped_by_kind_with_shot_chips(page):
    gates = page[page.index('id="gates"'):page.index('id="pictures"')]
    assert re.search(r"framing\s*<b>×2</b>", gates) and 'href="#shot-01"' in gates
    assert "posture" in gates and "missing" in gates


def test_panel_tiles_carry_their_shot_number_and_a_badge(page):
    tile = re.search(r'<figure[^>]*id="shot-01".*?</figure>', page, re.S).group(0)
    assert ">01<" in tile and "medium_close" in tile and "framing ×2" in tile
    dq = re.search(r'<figure[^>]*id="shot-00".*?</figure>', page, re.S).group(0)
    assert "blur" in dq and "missing" in dq


def test_the_lightbox_holds_the_shots_plan_text_and_a_redo(page):
    assert '<dialog id="lightbox"' in page
    lb = html.unescape(re.search(r'<template id="lb-shot-01">(.*?)</template>', page, re.S).group(1))
    assert FRAME_1 in lb and "a 50mm lens" in lb and "redo this shot" in lb
    assert 'data-artefact="episodes/ep08/storyboard/shot_01.png"' in lb and 'data-step="08"' in lb


def test_takes_are_grey_slots_that_say_why(page):
    takes = page[page.index('id="takes"'):]
    assert takes.count('data-testid="slot"') == 3 and "the takes wait on the panels" in takes


def test_the_redo_defaults_to_the_holding_step(page):
    assert '<option value="08" selected>' in page
    assert "EYE_PANELS: framing ×2" in page


def test_the_raw_band_is_collapsed(page):
    raw = re.search(r'<details[^>]*id="raw"[^>]*>', page).group(0)
    assert " open" not in raw
    assert "PLAN: measured 61.0 vs None -&gt; improve" in page or "PLAN: measured 61.0 vs None -> improve" in page


class _OpenText(HTMLParser):
    """Text nodes outside any <details>, <template>, <dialog>, <script>, <style>."""
    FOLDS = {"details", "template", "dialog", "script", "style"}

    def __init__(self):
        super().__init__()
        self.depth, self.long = 0, []

    def handle_starttag(self, tag, attrs):
        self.depth += tag in self.FOLDS

    def handle_endtag(self, tag):
        self.depth -= tag in self.FOLDS

    def handle_data(self, data):
        if self.depth == 0 and len(data.strip()) > 160:
            self.long.append(data.strip()[:80])


def test_no_text_over_160_characters_renders_open(page):
    parser = _OpenText()
    parser.feed(page)
    assert parser.long == []


def test_the_page_stays_small_with_a_40kb_note(page):
    assert len(BIG_NOTE) > 40_000
    assert len(page.encode("utf-8")) < 400_000
    assert BIG_NOTE[:2000] not in page


def test_the_head_partial_polls_while_running(client):
    head = client.get(f"/partials/unit/episode/{CODEX}/ep08/head").text
    assert "<html" not in head and 'hx-trigger="every 3s' in head and "08 panels" in head
    done = client.get(f"/partials/unit/episode/{CODEX}/ep03/head").text
    assert "every 3s" not in done


def test_this_units_orders_are_listed(page):
    assert 'id="orders"' in page and "no orders for this unit" in page


def test_the_json_twin_carries_the_bands(client):
    body = client.get(f"/api/unit/episode/{CODEX}/ep08.json").json()
    unit = models.Unit.model_validate(body)
    assert unit.health["loop"]["looping"] is True and len(unit.health["passes"]) == 4
    assert [g["gate"] for g in unit.gates][:3] == ["PLAN", "LAYOUT", "EYE_PANELS"]
    assert unit.pictures["panels"][1]["faults"][0]["kind"] == "framing"
