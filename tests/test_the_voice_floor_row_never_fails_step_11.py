"""Wave 1 review finding 7: the voice floor row never fails step 11 (craft ruling T18, report only).

`qc.measure()` calls `voice_floor_rows` every time.  It read lines.json with no guard: a file that
was not JSON, a dict without a `lines` key (passed through, then iterated over its keys) or a row
with no `index` raised and failed QC on a row that never moves the verdict.  Wave 0 finding 5 fixed
the same class in `words_rows`.  Each now reads "voice floor: not measured (...)".  Built in
tmp_path; the good case reads tests/fixtures/craft (Jekyll ep01 lines.json).  No spend."""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.episode import qc
from studio import episode_home

BOOK = Path(__file__).parent / "fixtures" / "craft"


def book_with_lines(tmp_path: Path, text: str) -> Path:
    path = episode_home.lines_dir(tmp_path, 1) / "lines.json"
    path.parent.mkdir(parents=True)
    path.write_text(text, encoding="utf-8")
    return tmp_path


@pytest.mark.parametrize("text", [
    "{not json",
    '{"voice": "utterson"}',
    '[{"passed": true, "floor": 0.0, "similarity": 0.3}]',
    '"a string"',
])
def test_an_unreadable_lines_json_is_not_measured(tmp_path, text):
    i = SimpleNamespace(book=book_with_lines(tmp_path, text), number=1)
    block = qc.voice_floor_rows(i, {"inputs": {"ok": True}})["inputs"]["voice_floor"]
    assert block["line"].startswith("voice floor: not measured (") and block["dropped"] == {}


def test_a_readable_lines_json_still_names_its_dropped_floors():
    block = qc.voice_floor_rows(SimpleNamespace(book=BOOK, number=1), {})["inputs"]["voice_floor"]
    assert block["line"].startswith("voice floor: 3 of 22 lines shipped")


def test_no_lines_json_is_still_not_measured(tmp_path):
    block = qc.voice_floor_rows(SimpleNamespace(book=tmp_path, number=1), {})["inputs"]["voice_floor"]
    assert block["line"] == "voice floor: not measured (no lines.json)"
