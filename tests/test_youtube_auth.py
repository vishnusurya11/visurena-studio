"""Reading the OAuth client out of .env, and writing the refresh token back in.

The interactive half of consent cannot be tested (it opens a browser), so the
half that CAN go wrong is tested instead: reading the client, and writing one
new variable into a .env that already holds seven others without disturbing
them.  A .env clobbered by a token write costs the owner every other key in it.
"""
import pytest

from studio import youtube

ENV = """# comment line
OPENAI_API_KEY=sk-proj-aaa
YOUTUBE_API_KEY=AIzaSyXXXX
YOUTUBE_CLIENT_ID=874432-abc.apps.googleusercontent.com
YOUTUBE_CLIENT_SECRET=GOCSPX-secret
YOUTUBE_CHANNEL_ID=UCyjo8L-DEJaeGuufUqMpigw
"""


def a_env(tmp_path, text=ENV):
    p = tmp_path / ".env"
    p.write_text(text, encoding="utf-8")
    return p


def test_the_client_is_read_from_env(tmp_path):
    got = youtube.client_config(a_env(tmp_path))
    assert got["installed"]["client_id"] == "874432-abc.apps.googleusercontent.com"
    assert got["installed"]["client_secret"] == "GOCSPX-secret"


def test_a_missing_client_is_refused_with_the_variable_named(tmp_path):
    p = a_env(tmp_path, "OPENAI_API_KEY=sk-proj-aaa\n")
    with pytest.raises(SystemExit, match="YOUTUBE_CLIENT_ID"):
        youtube.client_config(p)


def test_the_token_is_appended_and_every_other_key_survives(tmp_path):
    p = a_env(tmp_path)
    youtube.save_refresh_token(p, "1//new-refresh-token")
    text = p.read_text(encoding="utf-8")
    for keep in ("OPENAI_API_KEY=sk-proj-aaa", "YOUTUBE_API_KEY=AIzaSyXXXX",
                 "YOUTUBE_CLIENT_SECRET=GOCSPX-secret", "# comment line"):
        assert keep in text
    assert "YOUTUBE_REFRESH_TOKEN=1//new-refresh-token" in text


def test_writing_twice_replaces_rather_than_duplicates(tmp_path):
    p = a_env(tmp_path)
    youtube.save_refresh_token(p, "1//first")
    youtube.save_refresh_token(p, "1//second")
    text = p.read_text(encoding="utf-8")
    assert text.count("YOUTUBE_REFRESH_TOKEN=") == 1
    assert "1//second" in text and "1//first" not in text


def test_the_file_keeps_its_trailing_newline(tmp_path):
    p = a_env(tmp_path, "A=1")
    youtube.save_refresh_token(p, "1//tok")
    assert p.read_text(encoding="utf-8").endswith("\n")


def test_the_scopes_cover_upload_and_the_extras_we_will_want():
    """Adding a scope later means re-consenting, so force-ssl is asked for now:
    it is what thumbnails, playlists and captions need."""
    assert "https://www.googleapis.com/auth/youtube.upload" in youtube.SCOPES
    assert "https://www.googleapis.com/auth/youtube.force-ssl" in youtube.SCOPES


def test_a_downloaded_client_secret_json_is_preferred_over_env(tmp_path):
    """Google shows a secret in full ONLY at creation, so a hand-copied one goes
    stale the moment it is regenerated -- which is exactly the invalid_client
    error this repo hit. The downloaded JSON cannot be mistyped."""
    import json

    env = a_env(tmp_path)
    blob = tmp_path / "client_secret_874432.json"
    blob.write_text(json.dumps({"installed": {
        "client_id": "874432-real.apps.googleusercontent.com",
        "client_secret": "GOCSPX-the-real-one",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token"}}), encoding="utf-8")
    got = youtube.client_config(env, blob)
    assert got["installed"]["client_secret"] == "GOCSPX-the-real-one"


def test_a_web_client_json_is_accepted_too(tmp_path):
    """Cloud Console emits {"web": ...} for a Web-application client; the flow
    needs the same three fields either way."""
    import json

    env = a_env(tmp_path)
    blob = tmp_path / "client_secret_web.json"
    blob.write_text(json.dumps({"web": {
        "client_id": "874432-web.apps.googleusercontent.com",
        "client_secret": "GOCSPX-web-one",
        "token_uri": "https://oauth2.googleapis.com/token"}}), encoding="utf-8")
    assert youtube.client_config(env, blob)["installed"]["client_id"].endswith("googleusercontent.com")


def test_env_is_still_used_when_no_json_is_given(tmp_path):
    assert youtube.client_config(a_env(tmp_path))["installed"]["client_secret"] == "GOCSPX-secret"


def test_the_client_is_synced_out_of_the_json_into_env(tmp_path):
    """Deleting the JSON must not break tomorrow's refresh: `credentials()` reads
    the id and secret from .env, so they have to be updated from the file that
    actually worked."""
    env = a_env(tmp_path)
    youtube.save_client(env, {"installed": {"client_id": "874432-new.apps.googleusercontent.com",
                                            "client_secret": "GOCSPX-new-one"}})
    got = youtube.read_env(env)
    assert got["YOUTUBE_CLIENT_ID"] == "874432-new.apps.googleusercontent.com"
    assert got["YOUTUBE_CLIENT_SECRET"] == "GOCSPX-new-one"
    assert got["OPENAI_API_KEY"] == "sk-proj-aaa"


def test_set_var_survives_a_value_holding_regex_characters(tmp_path):
    """A refresh token starts '1//' and secrets carry '-' and '_'; a naive
    re.sub replacement string would mangle a backslash or a group reference."""
    env = a_env(tmp_path)
    youtube.set_var(env, "YOUTUBE_REFRESH_TOKEN", r"1//0e\g1-_x")
    assert youtube.read_env(env)["YOUTUBE_REFRESH_TOKEN"] == r"1//0e\g1-_x"
