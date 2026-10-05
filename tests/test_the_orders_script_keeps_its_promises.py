"""The orders script's pure core, run under node with no browser (panel
ruling PKG-6, 6.2 and 6.5).  `undoStep` is the acknowledge's deferred commit:
Undo inside the 5 s sends nothing; the deadline sends ONE post; leaving the
page sends ONE beacon; nothing sends twice.  `orderWords` is what a receipt
chip reads once its order moves: pending, taken by a run, applied, or unknown
(the read route is not there: the chip stays as it is).  Skipped where node is
not installed; it spends nothing."""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "studio" / "command_center" / "static" / "orders.js"
NODE = shutil.which("node")
pytestmark = pytest.mark.skipif(NODE is None, reason="node is not installed")


def run(expr: str):
    """Evaluate `expr` against the script's exports (`core`) and return its JSON."""
    code = f"const core = require({json.dumps(str(SCRIPT))}); process.stdout.write(JSON.stringify({expr}));"
    out = subprocess.run([NODE, "-e", code], capture_output=True, text=True, encoding="utf-8",
                         timeout=20, check=True)
    return json.loads(out.stdout)


def walk(events: list[dict]) -> list:
    """Feed events through undoStep from idle; the list of what each one sent."""
    expr = ("(function(){var s={phase:'idle'},sent=[];" + json.dumps(events) +
            ".forEach(function(e){var r=core.undoStep(s,e);s=r.s;sent.push(r.send);});return sent;})()")
    return run(expr)


PRESS = {"type": "press", "now": 0}


@pytest.mark.parametrize("events, sent", [
    ([PRESS, {"type": "undo", "now": 2000}, {"type": "tick", "now": 6000}, {"type": "hide", "now": 7000}],
     [None, None, None, None]),
    ([PRESS, {"type": "tick", "now": 4000}, {"type": "tick", "now": 5000}, {"type": "tick", "now": 6000}],
     [None, None, "post", None]),
    ([PRESS, {"type": "hide", "now": 1000}, {"type": "tick", "now": 6000}], [None, "beacon", None]),
    ([PRESS, {"type": "tick", "now": 5000}, {"type": "hide", "now": 5100}, {"type": "undo", "now": 5200}],
     [None, "post", None, None]),
    ([PRESS, PRESS, {"type": "tick", "now": 5000}], [None, None, "post"])])
def test_undo_sends_nothing_and_the_deadline_or_pagehide_sends_once(events, sent):
    assert walk(events) == sent


def test_the_undo_window_is_five_seconds():
    assert run("core.UNDO_MS") == 5000


@pytest.mark.parametrize("order, words", [
    ({"state": "pending"}, "○ pending"),
    ({"state": "taken", "run_at": "04:00"}, "● taken by the 04:00 run"),
    ({"state": "taken", "run_at": ""}, "● taken by a run"),
    ({"state": "applied"}, "● applied"),
    (None, None)])
def test_a_chip_reads_its_orders_state(order, words):
    assert run(f"core.orderWords({json.dumps(order)})") == words


@pytest.mark.parametrize("item, taken", [
    ({"id": "ord-41", "order": 41, "text": "bump on episode › ep06 taken by run 20260901000001__episode__20261005040056"},
     {"id": 41, "state": "taken", "run": "20260901000001__episode__20261005040056", "run_at": "04:00"}),
    ({"id": "ord-7", "order": 7, "text": "redo on episode › ep04 · step 02 taken by run r5"},
     {"id": 7, "state": "taken", "run": "r5", "run_at": ""}),
    ({"id": 1234, "ts": "x", "text": "ep17 · 08 panels completed"}, None)])
def test_a_pulse_event_for_a_taken_order_moves_its_chip(item, taken):
    assert run(f"core.takenFrom({json.dumps(item)})") == taken


def test_the_script_writes_markup_only_from_the_servers_receipts():
    text = SCRIPT.read_text(encoding="utf-8")
    sinks = [line.strip() for line in text.splitlines() if "innerHTML" in line or "insertAdjacentHTML" in line]
    assert all("receiptHTML" in line for line in sinks), sinks
