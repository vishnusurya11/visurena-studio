#!/usr/bin/env python
"""Where this machine stands for an unattended night: read-only, $0 (craft ruling A28).

    uv run --no-sync python scripts/ops/machine_check.py

Deadline retro 2026-10-20: a Windows Update reboot cost Jekyll ep01 a 4.7 h gap.  This prints Automatic
Restart Sign-On (ARSO: a reboot returns to the signed-in desktop, so the series task resumes), Windows
Update's active hours, any pause on updates, and the no-auto-reboot policy.  It opens each registry key
with KEY_READ and changes nothing: the owner applies the toggles (Settings > Accounts > Sign-in options,
Settings > Windows Update).  A value it cannot read is said "unread", never guessed.
"""
from __future__ import annotations

from datetime import datetime, timezone

SYSTEM = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System"
UX = r"SOFTWARE\Microsoft\WindowsUpdate\UX\Settings"
AU = r"SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU"
KEYS = {"DisableAutomaticRestartSignOn": SYSTEM, "ActiveHoursStart": UX, "ActiveHoursEnd": UX,
        "PauseUpdatesExpiryTime": UX, "NoAutoRebootWithLoggedOnUsers": AU}
"""Each value the check reads, under HKEY_LOCAL_MACHINE."""


def read_value(key: str, name: str):
    """One HKLM value, opened read-only; None when the key or the value is absent (or not Windows)."""
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key, 0, winreg.KEY_READ) as handle:
            return winreg.QueryValueEx(handle, name)[0]
    except (ImportError, OSError):
        return None


def arso_line(read) -> str:
    """ARSO is on unless the policy disables it (Windows' default is on for a signed-in owner)."""
    off = read(SYSTEM, "DisableAutomaticRestartSignOn")
    return ("ARSO: off by policy (a reboot stops at the sign-in screen)" if off == 1
            else "ARSO: on (no policy disables it; the Sign-in options toggle is the owner's to confirm)")


def active_hours_line(read) -> str:
    start, end = read(UX, "ActiveHoursStart"), read(UX, "ActiveHoursEnd")
    if start is None or end is None:
        return "active hours: unread"
    return f"active hours: {int(start):02d}:00-{int(end):02d}:00"


def pause_line(read, now: datetime) -> str:
    """Paused while the expiry Windows stores (ISO, UTC) is still ahead of `now`."""
    said = read(UX, "PauseUpdatesExpiryTime")
    try:
        until = datetime.fromisoformat(str(said).replace("Z", "+00:00")) if said else None
    except ValueError:
        return f"updates: pause unread ({said!r})"
    return f"updates: paused until {said}" if until and until > now else "updates: not paused"


def reboot_line(read) -> str:
    policy = read(AU, "NoAutoRebootWithLoggedOnUsers")
    return ("auto reboot: refused while signed in (policy)" if policy == 1
            else "auto reboot: allowed outside active hours (no policy)")


def report(read=read_value, now: datetime | None = None) -> list[str]:
    """The four lines, in the order the owner applies the toggles."""
    now = now or datetime.now(timezone.utc)
    return [arso_line(read), active_hours_line(read), pause_line(read, now), reboot_line(read)]


def main() -> int:
    print("\n".join(report()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
