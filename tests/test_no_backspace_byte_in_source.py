"""No source file carries a backspace byte.

A `\\b` typed through a Bash heredoc reaches disk as the byte 0x08, and a regex
built from it silently matches nothing.  MEASURED 2026-09-17: three files held
it -- `studio/take_look.py` (the daylight words, caught by its own new test),
`studio/trailer_refs.py` (the Dr/Mr/Mrs/St lookbehinds, which never fired) and
`tests/test_bed_engine.py` (a no-singing assertion that could never fail).
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_no_python_source_holds_a_backspace_byte():
    bad = [str(p.relative_to(ROOT)) for folder in ("studio", "scripts", "tests")
           for p in (ROOT / folder).rglob("*.py")
           if "\x08" in p.read_text(encoding="utf-8", errors="ignore")]
    assert bad == []
