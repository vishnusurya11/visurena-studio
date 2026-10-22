"""A YouTube Data API stand-in for the publish lane's tests: videos, playlists and
playlist items held in dicts, every write kept in `writes`.  It answers the same
call shapes the real client does (`api.videos().list(...).execute()`), REPLACES a
part on update the way videos.update does, and 404s a playlist it does not hold.
Nothing reaches the network (house rule: no test spends anything)."""
from __future__ import annotations

import copy


class Call:
    def __init__(self, got):
        self.got = got

    def execute(self):
        if isinstance(self.got, Exception):
            raise self.got
        return self.got


class NotFound(Exception):
    """What the client raises for a 404; the code under test never catches it."""


def video(title: str, description: str, privacy: str = "public") -> dict:
    """One video as videos.list returns it: a writable snippet and a status."""
    return {"snippet": {"title": title, "description": description, "categoryId": "1",
                        "tags": ["a tag"], "defaultLanguage": "en", "channelTitle": "read-only"},
            "status": {"privacyStatus": privacy, "selfDeclaredMadeForKids": False}}


class FakeYouTube:
    def __init__(self, videos: dict | None = None, playlists: dict | None = None):
        self.store = {k: copy.deepcopy(v) for k, v in (videos or {}).items()}
        self.lists = {k: copy.deepcopy(v) for k, v in (playlists or {}).items()}
        self.writes: list[tuple[str, dict]] = []

    def videos(self):
        return _Videos(self)

    def playlists(self):
        return _Playlists(self)

    def playlistItems(self):  # noqa: N802 - the client's own name
        return _Items(self)


class _Videos:
    def __init__(self, yt):
        self.yt = yt

    def list(self, part, id, **_):  # noqa: A002 - the client's own name
        got = self.yt.store.get(id)
        return Call({"items": [dict(copy.deepcopy(got), id=id)] if got else []})

    def update(self, part, body):
        self.yt.writes.append((f"videos.update {part}", copy.deepcopy(body)))
        self.yt.store[body["id"]][part] = copy.deepcopy(body[part])
        return Call(copy.deepcopy(body))


class _Playlists:
    def __init__(self, yt):
        self.yt = yt

    def list(self, part, mine=True, maxResults=50, pageToken=None):  # noqa: N803
        items = [{"id": k, "snippet": {"title": v["title"], "description": v["description"]}}
                 for k, v in self.yt.lists.items()]
        return Call({"items": items})

    def insert(self, part, body):
        pid = f"PLmade{len(self.yt.lists) + 1}"
        self.yt.writes.append(("playlists.insert", copy.deepcopy(body)))
        self.yt.lists[pid] = {**body["snippet"], "privacy": body["status"]["privacyStatus"], "items": []}
        return Call({"id": pid})


class _Items:
    def __init__(self, yt):
        self.yt = yt

    def list(self, part, playlistId, maxResults=50, pageToken=None):  # noqa: N803
        held = self.yt.lists.get(playlistId)
        if held is None:
            return Call(NotFound(f"playlist {playlistId} not found"))
        return Call({"items": [{"contentDetails": {"videoId": v}} for v in held["items"]]})

    def insert(self, part, body):
        s = body["snippet"]
        self.yt.writes.append(("playlistItems.insert", copy.deepcopy(body)))
        self.yt.lists[s["playlistId"]]["items"].insert(s["position"], s["resourceId"]["videoId"])
        return Call({"id": "item"})
