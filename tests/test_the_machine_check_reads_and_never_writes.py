"""The machine availability check prints what decides an unattended night, and changes nothing (craft ruling A28).

Deadline retro 2026-10-20: a Windows Update reboot cost ep01 a 4.7 h gap.  The owner applies the toggles; this
check only says where they stand: Automatic Restart Sign-On (ARSO, so a reboot comes back to a signed-in desktop
and the series resumes), Windows Update's active hours, a pause on updates, and the no-auto-reboot policy.  It
reads the registry through `winreg` with KEY_READ only; the test hands it a fake reader and checks the source holds
no registry write."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from scripts.ops import machine_check as mc

NOW = datetime(2026, 10, 21, 22, 0, tzinfo=timezone.utc)


def reader(values: dict):
    return lambda key, name: values.get(name)


def test_arso_off_by_policy_is_said():
    lines = mc.report(reader({"DisableAutomaticRestartSignOn": 1}), NOW)
    assert any(l.startswith("ARSO: off") for l in lines)


def test_arso_with_no_policy_is_the_windows_default():
    assert any(l.startswith("ARSO: on") for l in mc.report(reader({}), NOW))


def test_active_hours_are_printed():
    lines = mc.report(reader({"ActiveHoursStart": 8, "ActiveHoursEnd": 2}), NOW)
    assert "active hours: 08:00-02:00" in lines


def test_a_pause_that_has_not_expired_is_said_with_its_end():
    lines = mc.report(reader({"PauseUpdatesExpiryTime": "2026-11-04T07:00:00Z"}), NOW)
    assert "updates: paused until 2026-11-04T07:00:00Z" in lines
    assert "updates: not paused" in mc.report(reader({"PauseUpdatesExpiryTime": "2026-10-01T07:00:00Z"}), NOW)


def test_an_unread_value_is_said_unread_never_guessed():
    lines = mc.report(reader({}), NOW)
    assert "active hours: unread" in lines and "updates: not paused" in lines


def test_the_check_holds_no_registry_write():
    source = Path(mc.__file__).read_text(encoding="utf-8")
    assert not any(w in source for w in ("SetValue", "CreateKey", "DeleteKey", "DeleteValue", "KEY_WRITE",
                                         "KEY_ALL_ACCESS", "subprocess"))
