"""An owner order that names a take lets it re-render under a repair (Jekyll ep06 retro F, 2026-10-29).

A repair of step 09 or later freezes every delivered take (take_currency.frozen_in, incident 2026-10-19), and
that is right for the takes nobody asked about.  Order 63 named T24 and T25 ("Retake T24 and T25 from their
redrawn panels") and the dry check accepted it, yet step 09 printed "KEPT T24: the owner's repair froze its
delivered bytes".  A take the window's own orders name is no longer frozen; every other take still is."""
from __future__ import annotations

import json
import sqlite3

from studio import repair_clock, take_currency as tc


def delivered_home(tmp_path, take_bytes=b"take24"):
    room = tmp_path / "takes" / "r2v"
    room.mkdir(parents=True)
    for i in (23, 24):
        (room / f"T{i}.mp4").write_bytes(take_bytes + bytes([i]))
    rows = [{"path": f"episodes/ep06/takes/r2v/T{i}.mp4", "sha8": tc.sha8_of(room / f"T{i}.mp4")} for i in (23, 24)]
    (tmp_path / "manifest.json").write_text(json.dumps({"inputs": rows}))
    return tmp_path, room


def test_a_named_take_is_not_frozen_and_the_rest_still_are(tmp_path, monkeypatch):
    home, room = delivered_home(tmp_path)
    monkeypatch.setattr(repair_clock, "delivered", lambda home: True)
    window = {"steps": ["09"], "orders": {"09": 63}, "named": [24]}
    assert tc.frozen_in(window, room / "T24.mp4", home) is None
    assert tc.frozen_in(window, room / "T23.mp4", home) == "delivered"


def test_a_window_without_names_freezes_as_before(tmp_path, monkeypatch):
    home, room = delivered_home(tmp_path)
    monkeypatch.setattr(repair_clock, "delivered", lambda home: True)
    assert tc.frozen_in({"steps": ["09"], "orders": {"09": 63}}, room / "T24.mp4", home) == "delivered"


def test_the_window_records_the_takes_its_orders_name():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE orders (id INTEGER PRIMARY KEY, note TEXT)")
    conn.execute("INSERT INTO orders VALUES (63, 'Retake T24 and T25 from their redrawn panels')")
    conn.execute("INSERT INTO orders VALUES (62, 'Re-judge the panels; shot 25')")
    assert repair_clock.named_takes(conn, {"09": 63, "08": 62}) == [24, 25]


def test_opening_a_window_keeps_the_names(tmp_path):
    window = repair_clock.open_window(tmp_path, {"09": 63}, started=1.0, named=[25, 24])
    assert window["named"] == [24, 25]
    assert repair_clock.read(tmp_path)["named"] == [24, 25]
