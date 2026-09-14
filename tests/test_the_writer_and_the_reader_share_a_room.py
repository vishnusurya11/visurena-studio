"""The sheet report is written by one script and read by another, and they named
different rooms.

`seq_boards.draw_setup` wrote `boards / f"seq_{name}.dq.json"`.
`qc.sheets_rollup` reads `sq.sheets_in(boards).glob("seq_*.dq.json")`.

`migrate_layout.py` MOVED the existing reports into `boards/sheets/` and left
the writer pointing at the old place, so every episode drawn after the migration
puts its reports where QC does not look.

MEASURED 2026-09-14: episode 3's four reports are in `boards/sheets/` and
episode 4's four are in `boards/`.  `qc.sheets_rollup` would have returned an
empty list for episode 4 -- no setup, no strict-redraw count, no spend -- and an
empty rollup renders as a clean one.

A migration that moves files has to move the code that writes them, and the
guard against forgetting is a test that asks the writer and the reader for their
room and compares the two.
"""
from pathlib import Path

from studio import episode_seq_board as sq


def test_the_report_goes_where_qc_looks_for_it(tmp_path):
    import importlib.util
    import inspect
    import sys

    ROOT = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location("ep_qc", ROOT / "scripts" / "episode" / "qc.py")
    qc = importlib.util.module_from_spec(spec)
    sys.modules["ep_qc"] = qc
    spec.loader.exec_module(qc)

    from scripts.episode import seq_boards
    written = inspect.getsource(seq_boards.draw_setup)
    read = inspect.getsource(qc.sheets_rollup)
    assert "sheets_in(" in written, "the writer does not use the sheets room"
    assert "sheets_in(" in read
    assert 'boards / f"{stem}.dq.json"' not in written


def test_sheets_in_is_one_room_below_boards(tmp_path):
    assert sq.sheets_in(tmp_path) == tmp_path / "sheets"


def test_a_report_written_now_is_found_by_the_glob(tmp_path):
    """End to end on the filesystem, with no code inspection."""
    from studio import episode_home
    boards = tmp_path / "boards"
    sq.sheets_in(boards).mkdir(parents=True)
    episode_home.write_json(sq.sheets_in(boards) / "seq_cab.dq.json", {"setup": "cab", "passed": True})
    assert [p.name for p in sorted(sq.sheets_in(boards).glob("seq_*.dq.json"))] == ["seq_cab.dq.json"]


def test_nothing_is_left_in_the_boards_root(tmp_path):
    """The old location must stay empty, or a stale report outlives its sheet."""
    from studio import episode_home
    boards = tmp_path / "boards"
    sq.sheets_in(boards).mkdir(parents=True)
    episode_home.write_json(sq.sheets_in(boards) / "seq_cab.dq.json", {"setup": "cab"})
    assert not list(boards.glob("*.dq.json"))
