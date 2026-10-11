"""Test temp files live on the NVMe, never the D: hard disk (2026-10-11): sessions that
inherited TEMP=D:\\temp ran pytest at 30-125 writes/s each into D:\\temp\\pytest-of-*
and held the disk at 0% idle."""
import tempfile
from pathlib import Path

import conftest


def test_the_fast_temp_is_localappdata_temp(monkeypatch, tmp_path):
    (tmp_path / "Temp").mkdir()
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    assert conftest.fast_tempdir() == str(tmp_path / "Temp")


def test_no_localappdata_leaves_temp_alone(monkeypatch):
    monkeypatch.delenv("LOCALAPPDATA", raising=False)
    assert conftest.fast_tempdir() is None


def test_this_run_writes_temp_under_the_fast_dir(tmp_path):
    fast = conftest.fast_tempdir()
    if fast:
        assert Path(tempfile.gettempdir()) == Path(fast)
        assert Path(fast) in tmp_path.parents
