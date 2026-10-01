"""ep16 (2026-10-01): the plan deferred as designed, and the DRIVE then died
printing the deferral summary -- UnicodeEncodeError, charmap, a replacement
character inside a quoted chapter span, because the Windows console is cp1252.
A pipeline must not die on a print.  The drive reconfigures its stdout and
stderr to UTF-8 with errors=replace at entry.  $0: a stream flag."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("drv", ROOT / "scripts" / "episode" / "drive.py")
drv = importlib.util.module_from_spec(spec)
sys.modules["drv"] = drv
spec.loader.exec_module(drv)


def test_utf8_console_makes_any_text_printable(capsys):
    drv.utf8_console()
    print("span 'my brother � went into him' — G-SOURCE")   # the ep16 killer line
    assert sys.stdout.encoding.lower().replace("-", "") == "utf8"
    assert sys.stdout.errors in ("replace", "backslashreplace")
