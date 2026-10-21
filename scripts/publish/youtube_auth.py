#!/usr/bin/env python
"""ONE-TIME: consent as the channel owner and store the refresh token.

    uv run python scripts/publish/youtube_auth.py

Opens a browser, asks you to sign in as the account that owns The Keeper's
Lantern, and requests two scopes: `youtube.upload` and `youtube.force-ssl`.
On success it writes YOUTUBE_REFRESH_TOKEN into `.env` (which is gitignored)
and then PROVES which channel the token actually belongs to, by calling
`channels.list(mine=True)` and printing the title beside the YOUTUBE_CHANNEL_ID
already in `.env`.

That last check is the point of the script.  Consenting while signed into the
wrong Google account is the easy mistake, and it fails silently: you get a
perfectly valid token that uploads to somebody else's channel.

The token is never printed.  Access tokens are derived from it at runtime and
are never stored at all.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio import settings, youtube

MINTED = "YOUTUBE_REFRESH_TOKEN_AT"
"""When the refresh token was stored (epoch seconds), written beside it in .env."""
TOKEN_WARN_DAYS = 5.0
"""A Testing consent's token dies at 7 days: at 5 the owner is sent the link (retro 2026-10-20 item 8)."""
DAY = 86_400.0


def store_token(env: Path, token: str, now: float | None = None) -> Path:
    """The token and the moment it was stored: the age the launch check reads."""
    youtube.save_refresh_token(env, token)
    return youtube.set_var(env, MINTED, str(time.time() if now is None else now))


def token_age_days(env: Path, now: float) -> float | None:
    """Days since the token was stored: its stamp, else .env's last write (the token
    is at least that old, so an old file is surely an old token).  None: no file."""
    stamp = youtube.read_env(env).get(MINTED)
    try:
        at = float(stamp) if stamp else Path(env).stat().st_mtime
    except (ValueError, OSError):
        return None
    return round((now - at) / DAY, 1)


def refresh_fails(env: Path) -> str | None:
    """None when Google trades the refresh token for an access token; else its error."""
    from google.auth.transport.requests import Request
    try:
        youtube.credentials(env).refresh(Request())
    except (Exception, SystemExit) as why:                     # noqa: BLE001 -- every failure is the same ask
        return f"{type(why).__name__}: {str(why)[:160]}"
    return None


def default_blob(root: Path = Path(".")) -> Path | None:
    """The downloaded OAuth client file in the repo root, when there is one."""
    return next(iter(sorted(Path(root).glob("client_secret*.json"))), None)


def token_note(env: Path, blob: Path | None, now: float, refresh=refresh_fails, link=None) -> str | None:
    """The owner's message when the token is TOKEN_WARN_DAYS old or a refresh fails,
    with the consent paste link; None when it is young and good."""
    age, failed = token_age_days(env, now), refresh(env)
    if failed is None and age is not None and age < TOKEN_WARN_DAYS:
        return None
    why = (f"refresh fails ({failed})" if failed else f"is {age} days old (a Testing consent dies at 7)"
           if age is not None else "has no recorded age")
    return (f"YouTube token {why}: open {(link or pending_link)(env, blob)} , approve, then send the localhost "
            f"address it fails on (uv run python scripts/publish/youtube_auth.py --paste=<address>)")


def consent(env: Path, blob: Path | None = None) -> str:
    """The browser round trip.  Returns the refresh token."""
    from google_auth_oauthlib.flow import InstalledAppFlow

    flow = InstalledAppFlow.from_client_config(youtube.client_config(env, blob), youtube.SCOPES)
    creds = flow.run_local_server(port=0, prompt="consent", access_type="offline")
    if not creds.refresh_token:
        raise SystemExit("Google returned no refresh token. Re-run: the consent screen must be "
                         "shown (prompt=consent) and access must be offline.")
    return creds.refresh_token


PASTE_REDIRECT = "http://localhost:8765/"
PENDING = settings.library_root(relative=True) / ".youtube_consent.json"
"""The PKCE verifier between the two halves of a pasted consent; library/ is gitignored.
In a rehearsal it lands in the sandbox library (2026-10-21_ep02_proof 1.2)."""


def code_from(url: str) -> str:
    """The one-time code in the failed localhost redirect the owner pasted."""
    from urllib.parse import parse_qs, urlparse
    code = parse_qs(urlparse(url.strip()).query).get("code", [""])[0]
    if not code:
        raise SystemExit(f"no code in that address (did the consent say allow?): {url[:120]}")
    return code


def paste_flow(env: Path, blob: Path | None, verifier: str | None = None):
    from google_auth_oauthlib.flow import InstalledAppFlow
    return InstalledAppFlow.from_client_config(youtube.client_config(env, blob), youtube.SCOPES,
                                               redirect_uri=PASTE_REDIRECT, code_verifier=verifier,
                                               autogenerate_code_verifier=verifier is None)


def paste_link(env: Path, blob: Path | None) -> str:
    """Half one, from any device: the link to open; the verifier kept for half two."""
    import json
    flow = paste_flow(env, blob)
    url, _state = flow.authorization_url(prompt="consent", access_type="offline")
    PENDING.write_text(json.dumps({"verifier": flow.code_verifier}), encoding="utf-8")
    return url


def pending_link(env: Path, blob: Path | None) -> str:
    """The link for the verifier already pending -- an owner mid-paste keeps a working
    link -- else a fresh one, its verifier kept for half two."""
    try:
        verifier = json.loads(PENDING.read_text(encoding="utf-8"))["verifier"]
    except (OSError, ValueError, KeyError, TypeError):
        return paste_link(env, blob)
    url, _state = paste_flow(env, blob, verifier).authorization_url(prompt="consent", access_type="offline")
    return url


def paste_token(env: Path, blob: Path | None, redirected: str) -> str:
    """Half two: the pasted address's code exchanged for the refresh token."""
    import json
    verifier = json.loads(PENDING.read_text(encoding="utf-8"))["verifier"]
    flow = paste_flow(env, blob, verifier)
    flow.fetch_token(code=code_from(redirected))
    PENDING.unlink(missing_ok=True)
    if not flow.credentials.refresh_token:
        raise SystemExit("Google returned no refresh token; open a fresh --paste-link and consent again.")
    return flow.credentials.refresh_token


def whose_channel(env: Path) -> dict:
    """Which channel this token can actually upload to."""
    from googleapiclient.discovery import build

    api = build("youtube", "v3", credentials=youtube.credentials(env), cache_discovery=False)
    got = api.channels().list(part="snippet,statistics", mine=True).execute()
    items = got.get("items") or []
    if not items:
        raise SystemExit("The token authorised no channel. Sign in as the channel owner, "
                         "not a Brand-Account viewer.")
    return items[0]


def main(argv: list[str]) -> None:
    args = [a for a in argv[1:] if not a.startswith("--")]
    env = youtube.ENV
    blob = next((Path(a) for a in args if a.endswith(".json")), None) or default_blob()
    if blob:
        print(f"using the OAuth client from {blob} (it cannot go stale like a copied secret)")
    print(f"scopes: {', '.join(youtube.SCOPES)}")
    if "--paste-link" in argv:
        print("open on ANY device, approve, then paste the localhost address it fails on:\n")
        print(paste_link(env, blob))
        return
    pasted = next((a.split("=", 1)[1] for a in argv if a.startswith("--paste=")), None)
    if pasted:
        store_token(env, paste_token(env, blob, pasted))
    else:
        print("a browser will open -- sign in as the owner of The Keeper's Lantern\n")
        store_token(env, consent(env, blob))
    print(f"refresh token stored in {env} (value not shown)\n")

    channel = whose_channel(env)
    wanted = youtube.read_env(env).get("YOUTUBE_CHANNEL_ID", "")
    got_id, snippet = channel["id"], channel["snippet"]
    print(f"the token uploads to: {snippet.get('title')}  ({snippet.get('customUrl')})")
    print(f"  channel id  {got_id}")
    print(f"  subscribers {channel.get('statistics', {}).get('subscriberCount')} "
          f"| videos {channel.get('statistics', {}).get('videoCount')}")
    if wanted and wanted != got_id:
        raise SystemExit(f"\nWRONG ACCOUNT: .env names {wanted} but the token authorises {got_id}. "
                         f"Delete YOUTUBE_REFRESH_TOKEN from .env and consent again as the right user.")
    print("\nmatches YOUTUBE_CHANNEL_ID. Uploads will go to this channel.")


if __name__ == "__main__":
    main(sys.argv)
