"""Registering a new book: a codex row, a library folder, and the EPUB in place.

Doing this by hand for the first book was fine. Doing it ten times by hand is how the
folders drift apart, and step 01 already depends on the layout: `paths.book_dir` finds
the folder by id prefix, and step 03 reads `source/chapters/`.
"""

from __future__ import annotations

import pytest

from studio import db, intake


@pytest.fixture()
def conn(tmp_path):
    connection = db.get_connection(tmp_path / "t.db")
    db.init_db(connection)
    return connection


def test_slug_is_lowercase_hyphenated(conn):
    assert intake.slug("The Yellow Wallpaper") == "the-yellow-wallpaper"


def test_slug_strips_punctuation_and_collapses_spaces(conn):
    assert intake.slug("Frankenstein; Or, The Modern   Prometheus") == \
        "frankenstein-or-the-modern-prometheus"


def test_slug_is_capped_so_folder_names_stay_usable(conn):
    assert len(intake.slug("word " * 40)) <= intake.MAX_SLUG


def test_register_creates_the_codex_row(conn, tmp_path):
    codex_id = intake.register(conn, "Dracula", source_ref="pg345",
                               library_root=tmp_path / "library")
    assert db.get_codex(conn, codex_id)["name"] == "Dracula"


def test_register_creates_the_folder_named_id_underscore_slug(conn, tmp_path):
    root = tmp_path / "library"
    codex_id = intake.register(conn, "Dracula", source_ref="pg345", library_root=root)
    assert (root / f"{codex_id}_dracula").is_dir()


def test_the_folder_is_findable_by_the_path_helper(conn, tmp_path):
    """The whole point of the naming convention — paths.book_dir globs `<id>_*`."""
    from studio import paths
    root = tmp_path / "library"
    codex_id = intake.register(conn, "Dracula", source_ref="pg345", library_root=root)
    assert paths.book_dir(codex_id, library_root=root).name.endswith("_dracula")


def test_the_epub_is_copied_into_source(conn, tmp_path):
    epub = tmp_path / "pg345.epub"
    epub.write_bytes(b"not really an epub")
    root = tmp_path / "library"
    codex_id = intake.register(conn, "Dracula", source_ref="pg345",
                               epub=epub, library_root=root)
    from studio import paths
    assert (paths.book_dir(codex_id, library_root=root) / "source" / "pg345.epub").exists()


def test_registering_the_same_book_twice_is_refused(conn, tmp_path):
    """Two folders for one book would make paths.book_dir ambiguous, and it raises on
    anything but exactly one match."""
    root = tmp_path / "library"
    intake.register(conn, "Dracula", source_ref="pg345", library_root=root)
    with pytest.raises(ValueError):
        intake.register(conn, "Dracula", source_ref="pg345", library_root=root)


def test_a_second_distinct_book_gets_its_own_id(conn, tmp_path):
    root = tmp_path / "library"
    first = intake.register(conn, "Dracula", source_ref="pg345", library_root=root)
    second = intake.register(conn, "Frankenstein", source_ref="pg84", library_root=root)
    assert first != second
