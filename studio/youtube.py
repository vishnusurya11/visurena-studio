"""The channel's OAuth client, and the one-time consent that mints its token.

A YOUTUBE_API_KEY CANNOT UPLOAD.  Google's own rule: "Operations that insert,
update, or delete resources always require user authorization", and
`videos.insert` lists only OAuth 2.0 scopes.  An API key reads public data --
it is what identified this channel -- and nothing else.  Uploading needs a
client id, a client secret and a REFRESH TOKEN minted by the channel's own
Google account.

Two facts that decide how this is set up, both verified against Google's docs
(2026-09-12):

  * A consent screen left in TESTING issues a refresh token that expires in
    SEVEN DAYS.  The project must be "In production"; unverified is fine for a
    single-user app, because `youtube.upload` is a sensitive scope, not a
    restricted one.
  * Scopes are fixed at consent.  `youtube.force-ssl` is asked for alongside
    `youtube.upload` NOW, because thumbnails, playlists and captions need it
    and adding a scope later means consenting again.
"""
from __future__ import annotations

import re
from pathlib import Path

SCOPES = ["https://www.googleapis.com/auth/youtube.upload",
          "https://www.googleapis.com/auth/youtube.force-ssl"]

ENV = Path(".env")
CLIENT_ID, CLIENT_SECRET = "YOUTUBE_CLIENT_ID", "YOUTUBE_CLIENT_SECRET"
REFRESH = "YOUTUBE_REFRESH_TOKEN"


def read_env(path: Path = ENV) -> dict[str, str]:
    """The .env as a mapping.  Values are never logged by anything here."""
    out: dict[str, str] = {}
    if not Path(path).exists():
        return out
    for line in Path(path).read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            out[key.strip()] = value.strip().strip('"').strip("'")
    return out


def client_config(path: Path = ENV, blob: Path | None = None) -> dict:
    """The installed-app client config `InstalledAppFlow` expects.

    A downloaded `client_secret_*.json` WINS over `.env` when one is given.
    Google shows a client secret in full only at creation, so a secret copied
    into a `.env` by hand goes stale the moment it is regenerated -- and the
    failure is `invalid_client` at the token exchange, AFTER the browser
    consent has already succeeded, which reads like a code bug and is not one.
    The downloaded file cannot be mistyped or go out of step with its id."""
    if blob is not None:
        import json

        data = json.loads(Path(blob).read_text(encoding="utf-8"))
        inner = data.get("installed") or data.get("web") or {}
        if not inner.get("client_id") or not inner.get("client_secret"):
            raise SystemExit(f"{blob} carries no client_id/client_secret; download the OAuth "
                             f"client JSON again from Google Cloud Console.")
        inner.setdefault("auth_uri", "https://accounts.google.com/o/oauth2/auth")
        inner.setdefault("token_uri", "https://oauth2.googleapis.com/token")
        inner.setdefault("redirect_uris", ["http://localhost"])
        return {"installed": inner}
    env = read_env(path)
    missing = [k for k in (CLIENT_ID, CLIENT_SECRET) if not env.get(k)]
    if missing:
        raise SystemExit(f"{', '.join(missing)} missing from {path}. An OAuth client is a "
                         f"'Desktop app' credential in Google Cloud; the API key cannot upload.")
    return {"installed": {"client_id": env[CLIENT_ID], "client_secret": env[CLIENT_SECRET],
                          "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                          "token_uri": "https://oauth2.googleapis.com/token",
                          "redirect_uris": ["http://localhost"]}}


def set_var(path: Path, name: str, value: str) -> Path:
    """Write ONE variable into .env, replacing any previous line for it.

    Appends or replaces one line and leaves every other byte alone: this file
    also holds the OpenAI and OpenRouter keys, and a .env clobbered by a token
    write costs all of them.  The replacement is a lambda because a refresh
    token starts `1//` and a secret carries `-` and `_`: a plain replacement
    string would let a backslash or a `\\1` be read as a group reference."""
    path = Path(path)
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    line = f"{name}={value}"
    if re.search(rf"^{re.escape(name)}=.*$", text, flags=re.M):
        text = re.sub(rf"^{re.escape(name)}=.*$", lambda m: line, text, flags=re.M)
    else:
        text = (text if text.endswith("\n") or not text else text + "\n") + line
    if not text.endswith("\n"):
        text += "\n"
    path.write_text(text, encoding="utf-8")
    return path


def save_refresh_token(path: Path, token: str) -> Path:
    """The durable half of the credential.  Access tokens derive from it."""
    return set_var(path, REFRESH, token)


def save_client(path: Path, config: dict) -> Path:
    """Sync the client id and secret OUT of a downloaded JSON and into .env.

    Without this the JSON is load-bearing forever: `credentials()` refreshes the
    access token using the id and secret in .env, so deleting the JSON while
    .env still names an OLDER client gives you a credential that works today and
    fails tomorrow -- with the same `invalid_client`, and just as confusingly,
    because the browser consent will have succeeded again."""
    inner = config["installed"]
    set_var(path, CLIENT_ID, inner["client_id"])
    return set_var(path, CLIENT_SECRET, inner["client_secret"])


def credentials(path: Path = ENV):
    """A ready-to-use Credentials object from the stored refresh token.

    Access tokens are derived at runtime and never stored; the refresh token is
    the only durable secret."""
    from google.oauth2.credentials import Credentials

    env = read_env(path)
    if not env.get(REFRESH):
        raise SystemExit(f"{REFRESH} missing from {path}: run "
                         f"`uv run python scripts/publish/youtube_auth.py` once to mint it.")
    return Credentials(None, refresh_token=env[REFRESH], token_uri="https://oauth2.googleapis.com/token",
                       client_id=env[CLIENT_ID], client_secret=env[CLIENT_SECRET], scopes=SCOPES)
