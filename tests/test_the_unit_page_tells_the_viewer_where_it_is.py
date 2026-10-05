"""The unit page names its book, stage and unit on <body data-*> so a cold `#v=` link opens the
Viewer over it (SPEC_v3 History); its crumbs are the shell's (Home first, panel ruling 2.9); the
palette's refetch has its address (2.7).  TestClient over the tmp fixtures, $0."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from command_center_fixtures import CODEX, make_app


@pytest.fixture()
def client(tmp_path, monkeypatch):
    return TestClient(make_app(tmp_path, monkeypatch))


def test_the_unit_body_carries_its_codex_stage_and_unit(client):
    page = client.get(f"/d/episode/{CODEX}/ep04").text
    body = page[page.index("<body"):].split(">", 1)[0]
    assert f'data-codex="{CODEX}"' in body and 'data-stage="episode"' in body and 'data-unit="ep04"' in body


def test_a_list_page_body_names_no_unit(client):
    page = client.get("/").text
    body = page[page.index("<body"):].split(">", 1)[0]
    assert "data-unit=" not in body


def test_the_unit_crumbs_start_at_home(client):
    page = client.get(f"/d/episode/{CODEX}/ep04").text
    crumbs = page[page.index('class="crumbs"'):].split("</nav>", 1)[0]
    assert ">Home<" in crumbs and "ep04" in crumbs


def test_the_palette_index_is_served_as_json(client):
    response = client.get("/api/palette.json")
    assert response.status_code == 200 and isinstance(response.json(), list)
