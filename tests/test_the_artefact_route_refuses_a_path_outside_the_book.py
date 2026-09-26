"""`/lib/{codex}/{path}` serves a book's artefacts and nothing else (report D
§3): the codex is 14 digits, the resolved path stays under that book's folder,
the suffix is on the allowlist, and every refusal is a 404 -- never a 403 that
confirms a file exists.  A served file is `Cache-Control: no-store`."""
from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

from command_center_fixtures import CODEX, OTHER, make_app
from studio.command_center import library_paths


@pytest.fixture()
def client(tmp_path, monkeypatch):
    return TestClient(make_app(tmp_path, monkeypatch))


def test_a_real_png_under_the_book_is_served_without_caching(client):
    response = client.get(f"/lib/{CODEX}/episodes/ep04/storyboard/shot_00.png")
    assert response.status_code == 200 and response.content == b"x" * 16
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["content-type"].startswith("image/png")


def test_a_video_answers_a_range(client):
    response = client.get(f"/lib/{CODEX}/episodes/ep04/cut/master_iter2.mp4", headers={"Range": "bytes=0-3"})
    assert response.status_code == 206 and response.content == b"xxxx"


@pytest.mark.parametrize("path", [
    f"/lib/{CODEX}/../{OTHER}_other-book/secret.png",
    f"/lib/{CODEX}/episodes/ep04/../../../{OTHER}_other-book/secret.png",
    f"/lib/{CODEX}/episodes/ep04/plan.py",
    f"/lib/{CODEX}/episodes/ep04/nothing.png",
    f"/lib/{CODEX}/episodes/ep04",
    f"/lib/{CODEX[:13]}/episodes/ep04/storyboard/shot_00.png",
    f"/lib/{CODEX}x/episodes/ep04/storyboard/shot_00.png",
    "/lib/20260901000009/episodes/ep04/storyboard/shot_00.png",
])
def test_everything_else_is_a_404(client, path):
    response = client.get(path)
    assert response.status_code == 404, path


def test_another_books_file_is_not_reachable_through_this_codex(client):
    assert client.get(f"/lib/{CODEX}/secret.png").status_code == 404
    assert client.get(f"/lib/{OTHER}/secret.png").status_code == 200


def test_a_symlink_out_of_the_book_is_a_404(client, tmp_path):
    book = tmp_path / "library" / f"{CODEX}_a-book"
    try:
        os.symlink(tmp_path / "library" / f"{OTHER}_other-book" / "secret.png", book / "link.png")
    except (OSError, NotImplementedError):
        pytest.skip("no symlinks on this account")
    assert client.get(f"/lib/{CODEX}/link.png").status_code == 404


def test_the_guard_is_one_function(tmp_path):
    library = tmp_path / "library"
    book = library / f"{CODEX}_a-book"
    (book / "a").mkdir(parents=True)
    (book / "a" / "f.json").write_text("{}", encoding="utf-8")
    assert library_paths.resolve_artefact(library, CODEX, "a/f.json") == book / "a" / "f.json"
    assert library_paths.resolve_artefact(library, CODEX, "a/../../x.json") is None
    assert library_paths.resolve_artefact(library, CODEX, "a/f.exe") is None
    assert library_paths.resolve_artefact(library, "not-a-codex", "a/f.json") is None
    assert library_paths.resolve_artefact(library, CODEX, "a") is None
