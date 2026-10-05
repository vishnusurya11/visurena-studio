"""A refusal sits in the shell (panel ruling 1.7): the 404 (and a 500) page is
rendered with the shell's context and the asked path, so the owner keeps the
sidebar and a way home; if the shell itself cannot be read, the page still
renders without it."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from command_center_fixtures import make_app
from studio.command_center import app as cc_app


@pytest.fixture()
def client(tmp_path, monkeypatch):
    return TestClient(make_app(tmp_path, monkeypatch), raise_server_exceptions=False)


def test_the_404_carries_the_sidebar_and_the_asked_path(client):
    response = client.get("/d/episode/x/ep99")
    assert response.status_code == 404
    assert 'data-testid="sidebar"' in response.text and "/d/episode/x/ep99" in response.text


def test_the_error_context_has_the_shell_and_the_path(client):
    seen = {}
    real = cc_app.templates.TemplateResponse

    def spy(request, name, context, **kw):
        seen.update(context)
        return real(request, name, context, **kw)
    cc_app.templates.TemplateResponse = spy
    try:
        client.get("/nope")
    finally:
        cc_app.templates.TemplateResponse = real
    assert seen["path"] == "/nope" and seen["shell"]["path"] == "/nope" and seen["status"] == 404


def test_a_broken_database_still_renders_the_error_page(client):
    def broken():
        raise RuntimeError("no db")
    client.app.state.conn_factory = broken
    response = client.get("/nope")
    assert response.status_code == 404 and "/nope" in response.text


def test_a_server_error_is_a_page_not_a_stack(client):
    @client.app.get("/boom")
    def boom():
        raise ValueError("kaboom")
    response = client.get("/boom")
    assert response.status_code == 500 and "Traceback" not in response.text and "/boom" in response.text
