"""Owner go 2026-10-21 ~19:05 PDT: add yt-analytics.readonly at the NEXT weekly
re-consent, without breaking the token in use until then.

A refresh sends its scopes to Google, and google-auth's refresh_grant says "all
scopes must be authorized for the refresh token".  So the analytics scope cannot
simply join SCOPES: today's token was granted upload + force-ssl only, and a
refresh asking for a third scope is refused.  The consent asks for
CONSENT_SCOPES; a refresh asks for the scopes recorded beside the token when it
was stored (a token stored before that record existed holds SCOPES).
No test here reaches Google: flows are built offline and credentials never refresh."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

from studio import youtube

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("youtube_auth_scopes", ROOT / "scripts/publish/youtube_auth.py")
auth = importlib.util.module_from_spec(_spec)
sys.modules["youtube_auth_scopes"] = auth
_spec.loader.exec_module(auth)

UPLOAD = "https://www.googleapis.com/auth/youtube.upload"
FORCE = "https://www.googleapis.com/auth/youtube.force-ssl"
ANALYTICS = "https://www.googleapis.com/auth/yt-analytics.readonly"


def _env(tmp_path, *extra: str) -> Path:
    env = tmp_path / ".env"
    env.write_text("\n".join(["YOUTUBE_CLIENT_ID=id.apps.googleusercontent.com",
                              "YOUTUBE_CLIENT_SECRET=s3cret", "YOUTUBE_REFRESH_TOKEN=1//fake", *extra]) + "\n",
                   encoding="utf-8")
    return env


def test_the_consent_asks_for_analytics_beside_upload_and_force_ssl():
    assert youtube.ANALYTICS == ANALYTICS
    assert set(youtube.CONSENT_SCOPES) == {UPLOAD, FORCE, ANALYTICS}


def test_todays_token_without_a_scope_record_refreshes_with_the_two_it_was_granted(tmp_path):
    env = _env(tmp_path)
    assert youtube.token_scopes(env) == [UPLOAD, FORCE]
    assert youtube.credentials(env).scopes == [UPLOAD, FORCE]
    assert not youtube.can_read_analytics(env)


def test_a_token_stored_with_analytics_refreshes_with_it(tmp_path):
    env = _env(tmp_path, f"{youtube.GRANTED}={UPLOAD} {FORCE} {ANALYTICS}")
    assert youtube.credentials(env).scopes == [UPLOAD, FORCE, ANALYTICS]
    assert youtube.can_read_analytics(env)


def test_storing_a_token_records_the_scopes_it_was_granted(tmp_path):
    env = _env(tmp_path)
    auth.store_token(env, "1//new", now=1.0, scopes=[UPLOAD, FORCE, ANALYTICS])
    auth.store_token(env, "1//newer", now=2.0, scopes=[UPLOAD, FORCE])
    text = env.read_text(encoding="utf-8")
    assert text.count(f"{youtube.GRANTED}=") == 1 and youtube.token_scopes(env) == [UPLOAD, FORCE]


def test_the_granted_scopes_are_read_from_a_string_a_list_or_the_request():
    assert auth.granted(SimpleNamespace(granted_scopes=f"{UPLOAD} {ANALYTICS}", scopes=None)) == [UPLOAD, ANALYTICS]
    assert auth.granted(SimpleNamespace(granted_scopes=[FORCE], scopes=None)) == [FORCE]
    assert auth.granted(SimpleNamespace(granted_scopes=None, scopes=[UPLOAD])) == [UPLOAD]


def test_the_paste_consent_link_requests_the_analytics_scope(tmp_path):
    flow = auth.paste_flow(_env(tmp_path), None)
    url, _state = flow.authorization_url(prompt="consent", access_type="offline")
    assert "yt-analytics.readonly" in url and "youtube.force-ssl" in url


def test_keeping_a_consent_stores_its_token_and_granted_scopes(tmp_path):
    env = _env(tmp_path)
    auth.keep(env, SimpleNamespace(refresh_token="1//kept", granted_scopes=[UPLOAD, FORCE, ANALYTICS], scopes=None))
    assert youtube.read_env(env)["YOUTUBE_REFRESH_TOKEN"] == "1//kept" and youtube.can_read_analytics(env)
