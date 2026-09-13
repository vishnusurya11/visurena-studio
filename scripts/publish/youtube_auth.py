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

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio import youtube


def consent(env: Path, blob: Path | None = None) -> str:
    """The browser round trip.  Returns the refresh token."""
    from google_auth_oauthlib.flow import InstalledAppFlow

    flow = InstalledAppFlow.from_client_config(youtube.client_config(env, blob), youtube.SCOPES)
    creds = flow.run_local_server(port=0, prompt="consent", access_type="offline")
    if not creds.refresh_token:
        raise SystemExit("Google returned no refresh token. Re-run: the consent screen must be "
                         "shown (prompt=consent) and access must be offline.")
    return creds.refresh_token


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
    blob = next((Path(a) for a in args if a.endswith(".json")), None)
    if blob is None:
        blob = next(iter(sorted(Path(".").glob("client_secret*.json"))), None)
    if blob:
        print(f"using the OAuth client from {blob} (it cannot go stale like a copied secret)")
    print(f"scopes: {', '.join(youtube.SCOPES)}")
    print("a browser will open -- sign in as the owner of The Keeper's Lantern\n")
    youtube.save_refresh_token(env, consent(env, blob))
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
