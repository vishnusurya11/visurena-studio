"""`/lib` revalidates by ETag (panel ruling 1.6): the tag is the file's mtime and
size, a matching `If-None-Match` is a 304 with no body, a Range request is
always served (206), and the board's fonts go out as `font/woff2`."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from command_center_fixtures import CODEX, make_app
from studio.command_center import library_paths

MASTER = f"/lib/{CODEX}/episodes/ep04/cut/master_iter2.mp4"


@pytest.fixture()
def client(tmp_path, monkeypatch):
    return TestClient(make_app(tmp_path, monkeypatch))


def test_an_artefact_carries_an_etag_and_a_match_is_304(client):
    first = client.get(MASTER)
    tag = first.headers["etag"]
    assert first.status_code == 200 and tag.startswith('"') and "-" in tag
    again = client.get(MASTER, headers={"If-None-Match": tag})
    assert again.status_code == 304 and again.content == b"" and again.headers["etag"] == tag


def test_a_stale_tag_gets_the_file(client):
    assert client.get(MASTER, headers={"If-None-Match": '"0-0"'}).status_code == 200


def test_a_range_request_is_served_even_with_a_matching_tag(client):
    tag = client.get(MASTER).headers["etag"]
    response = client.get(MASTER, headers={"If-None-Match": tag, "Range": "bytes=0-3"})
    assert response.status_code == 206 and response.content == b"xxxx"


def test_a_rewritten_file_is_a_new_tag(client):
    tag = client.get(MASTER).headers["etag"]
    target = next(client.app.state.library.glob(f"{CODEX}_*")) / "episodes/ep04/cut/master_iter2.mp4"
    target.write_bytes(b"y" * 32)
    assert client.get(MASTER).headers["etag"] != tag


def test_the_tag_and_its_match(tmp_path):
    f = tmp_path / "a.mp4"
    f.write_bytes(b"abc")
    tag = library_paths.etag(f)
    assert tag.endswith('-3"')
    assert library_paths.etag_matches(f'"x", W/{tag}', tag) and library_paths.etag_matches("*", tag)
    assert not library_paths.etag_matches(None, tag) and not library_paths.etag_matches('"x"', tag)


def test_fonts_are_served_as_woff2(client):
    response = client.get("/static/fonts/ibm-plex-sans-latin.woff2")
    assert response.status_code == 200 and response.headers["content-type"] == "font/woff2"
