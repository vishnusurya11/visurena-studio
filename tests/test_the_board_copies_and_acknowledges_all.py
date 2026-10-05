"""Two list controls PKG-4 draws need board.js behind them (lead, 2026-10-05): a [data-copy]
button copies its value and says so; [data-ack-all] submits every acknowledge form on the page,
each through its own 5 s Undo (orders.js), never one bulk POST.  Text checks, $0."""
from pathlib import Path

JS = (Path(__file__).parent.parent / "studio" / "command_center" / "static" / "board.js").read_text(encoding="utf-8")


def test_a_copy_button_copies_its_value_and_announces_it():
    assert "function copyValue(" in JS and "navigator.clipboard.writeText" in JS and "closest('[data-copy]')" in JS


def test_acknowledge_all_submits_each_acknowledge_form():
    assert "function ackAll(" in JS and "form.ack" in JS and "requestSubmit()" in JS
    assert "fetch('/act/acknowledge-all" not in JS
