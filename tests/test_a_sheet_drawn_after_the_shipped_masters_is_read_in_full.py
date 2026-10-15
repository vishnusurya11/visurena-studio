"""A grandfathered bible is the sheets the shipped episodes USED.  A sheet drawn after
the newest master was used by no episode, so it is read in full -- the look-back, the
trait card and SHEET-ROW (Jekyll ep01 v2, 2026-10-15: the whole Hellsing cast was
redrawn after ep01 shipped, the first verdict read it light, and the girl's lace
bonnet and hollow eyes were never put to a reader)."""
from __future__ import annotations

import json
import os

from scripts.refs import step_04_verdict as step
from studio.judges import sheet_row
from tests import look_fixtures as lf


def a_shipped_book(tmp_path):
    book = lf.a_book(tmp_path)
    old = lf.character(book, "old")
    master = book / "episodes" / "ep01" / "cut" / "master_iter1.mp4"
    master.parent.mkdir(parents=True)
    master.write_bytes(b"mp4")
    os.utime(book / old["path"], (1_000_000, 1_000_000))
    os.utime(master, (2_000_000, 2_000_000))
    new = lf.character(book, "new")
    os.utime(book / new["path"], (3_000_000, 3_000_000))
    return book, old, new


def test_only_the_sheet_newer_than_every_master_is_fresh(tmp_path):
    book, old, new = a_shipped_book(tmp_path)
    assert step.fresh_paths(book, [old["path"], new["path"]]) == [new["path"]]


def test_a_book_with_no_master_has_every_sheet_fresh(tmp_path):
    book = lf.a_book(tmp_path)
    row = lf.character(book, "a")
    assert step.fresh_paths(book, [row["path"]]) == [row["path"]]


def test_the_first_verdict_reads_the_fresh_sheet_and_lights_the_old(tmp_path):
    book, old, new = a_shipped_book(tmp_path)
    asked = []
    ctx = lf.a_ctx(tmp_path, book, **lf.tools(reader=lf.reader_of(asked=asked)))
    assert step.grandfathered(ctx) is True
    step.run(ctx)
    read = {p.parent.name for p, q in asked if "absent" in q}
    assert read == {"new"}
