"""No source file carries a control byte where an escape was meant.

A `\\b` typed inside a bash heredoc reaches disk as the BACKSPACE byte 0x08.
The pattern still compiles. It just matches nothing, silently, for ever.

THIS HAS NOW HAPPENED THREE TIMES on this project:

  `panel_check.py`'s CROWD regex, whose own docstring records it: "the first
  version had them and went to disk through a bash heredoc, which turned each
  one into a literal BACKSPACE byte (0x08). The pattern compiled, matched
  nothing, and every crowd shot was flagged -- silently, which is the whole
  danger."

  the storyboard crowd clause, same session, same cause.

  `content_check.py`'s walk-on regex, 2026-09-21, which made the content gate
  report a cast fault on every shot whose prose names a workman or a boy.

`feedback_patch_scripts_not_heredocs` records the rule and the rule was broken
anyway, so here is the check that does not depend on remembering it.
"""
from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MANGLED = {"\x07": "\\a", "\x08": "\\b", "\x0b": "\\v", "\x0c": "\\f"}
"""Control bytes a shell heredoc produces from the escapes a regex wants."""

WATCHED = ("studio", "scripts", "tests")


def sources() -> list[Path]:
    return [p for folder in WATCHED for p in (ROOT / folder).rglob("*.py")
            if "__pycache__" not in p.parts]


def test_the_scan_has_something_to_scan():
    assert len(sources()) > 50


@pytest.mark.parametrize("byte,meant", sorted(MANGLED.items()))
def test_no_source_carries_this_control_byte(byte, meant):
    found = []
    for path in sources():
        text = path.read_text(encoding="utf-8", errors="ignore")
        if byte in text:
            line = text[: text.index(byte)].count("\n") + 1
            found.append(f"{path.relative_to(ROOT).as_posix()}:{line}")
    assert not found, (
        f"{meant!r} reached disk as {byte!r} in {', '.join(found)} -- a heredoc ate "
        f"the backslash. Write the file with a Python script, or build the escape "
        f"with chr(92).")
