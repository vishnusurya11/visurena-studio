"""The owner's buttons (panel ruling PKG-6, 6.1 and 6.4-6.6), read off the
macros' own output: every /act/ form disables its submit button and drops a
second request while one is in flight, and swaps its receipt into the ONE
receipts region (never a `.receipt` inside a polled block); a button says what
will happen ("Move to front", "Retry from 09 shoot"); a hold offers reason
chips and states the one hold sentence; an acknowledge is deferred (Undo) yet
still a plain hx-post form, so it works without the orders script."""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from studio.command_center import actions
from studio.command_center.app import templates

BOARD = Path(actions.__file__).resolve().parent


def macro(call: str, writable: bool = True) -> str:
    """One macro call rendered the way a page imports them (`with context`)."""
    source = '{% import "_macros.html" as act with context %}' + "{{ " + call + " }}"
    return templates.env.from_string(source).render(writable=writable, read_only="read-only board",
                                                    HOLD_EFFECT=actions.HOLD_EFFECT)


def label(html: str) -> str:
    """The submit button's text."""
    found = re.search(r'<button class="btn"[^>]*type="submit"[^>]*>(.*?)</button>', html, re.S)
    return re.sub(r"<[^>]+>", "", found.group(1)).strip()


CALLS = [
    "act.order('bump', 'c', 'episode', 'ep07')",
    "act.order('requeue', 'c', 'episode', 'ep07')",
    "act.order('retry', 'c', 'episode', 'ep07', step='09 shoot')",
    "act.hold('unit', 'c', 'episode', 'ep07')",
    "act.hold('studio')",
    "act.lift(3)",
    "act.acknowledge('c', 'episode', 'ep03')"]


@pytest.mark.parametrize("call", CALLS)
def test_every_form_disables_its_button_and_drops_a_second_request(call):
    html = macro(call)
    assert 'hx-disabled-elt="find button[type=submit]"' in html and 'hx-sync="this:drop"' in html
    assert 'hx-target="#receipts"' in html and 'class="receipt"' not in html


@pytest.mark.parametrize("call", CALLS)
def test_no_form_writes_script(call):
    assert "hx-on" not in macro(call) and "<script" not in macro(call)


@pytest.mark.parametrize("call, verb", [
    ("act.order('bump', 'c', 'episode', 'ep07')", "Move to front"),
    ("act.order('bump', 'c', 'episode', 'ep07', '↑ bump')", "Move to front"),
    ("act.order('requeue', 'c', 'episode', 'ep07')", "Queue again"),
    ("act.order('retry', 'c', 'episode', 'ep07', step='09 shoot')", "Retry from 09 shoot"),
    ("act.order('retry', 'c', 'episode', 'ep07')", "Retry"),
    ("act.hold('unit', 'c', 'episode', 'ep07')", "Hold this episode"),
    ("act.hold('unit', 'c', 'refs', 'main')", "Hold this refs"),
    ("act.hold('book', 'c', label='hold book')", "Hold this book"),
    ("act.hold('studio')", "Hold the studio"),
    ("act.lift(3)", "Lift the hold"),
    ("act.acknowledge('c', 'episode', 'ep03')", "Acknowledge flags")])
def test_a_button_says_what_will_happen(call, verb):
    assert label(macro(call)) == verb


def test_a_hold_offers_reason_chips_and_states_the_hold_sentence():
    html = macro("act.hold('studio')")
    chips = re.findall(r'data-reason="([^"]+)"', html)
    assert chips == ["checking output", "GPU needed elsewhere", "wrong direction: stop"]
    assert 'name="reason" required' in html and actions.HOLD_EFFECT in html
    assert "data-reset" in html


def test_no_template_or_script_types_the_hold_sentence_itself():
    hits = [p.name for p in BOARD.rglob("*") if p.suffix in (".html", ".js")
            and "every run stops before its next GPU step" in p.read_text(encoding="utf-8")]
    assert hits == [] and "every run stops before its next GPU step" in actions.HOLD_EFFECT


def test_an_acknowledge_is_deferred_but_still_a_plain_form():
    html = macro("act.acknowledge('c', 'episode', 'ep03')")
    assert 'hx-post="/act/acknowledge"' in html and 'data-undo="5"' in html
    assert 'data-unit="ep03"' in html


def test_a_read_only_board_disables_every_button():
    html = macro("act.hold('studio')", writable=False)
    assert html.count("disabled") >= 4 and 'title="read-only board"' in html
