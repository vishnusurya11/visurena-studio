"""The whole last mile against fakes: the upload row, the privacy flip row and
the shorts_poll row land in uploads.jsonl, the public Short URL is the LAST
line printed, done() turns true only after the public row + poll row, and a
re-run on the same sha8 uploads nothing (yp.uploaded idempotence).  Nothing
reaches the network: send, build_api and http are injected; the credentials
reader is stubbed; the metadata call is guarded so a paid call is impossible."""
from __future__ import annotations

import json

from scripts.episode import step_13_publish
from scripts.publish import metadata
from studio import episode_home, plan_verdict, youtube
from studio import youtube_publish as yp
from tests.publish_fixtures import FakeCtx, book_with, episode_with, standing


class _Call:
    def __init__(self, got):
        self.got = got

    def execute(self):
        return self.got


class FakeApi:
    """The two videos() calls youtube_privacy makes, over one privacy cell."""

    def __init__(self):
        self.privacy = "private"

    def videos(self):
        return self

    def list(self, **kwargs):
        return _Call({"items": [{"status": {"privacyStatus": self.privacy}}]})

    def update(self, **kwargs):
        self.privacy = kwargs["body"]["status"]["privacyStatus"]
        return _Call({"id": kwargs["body"]["id"], "status": {"privacyStatus": self.privacy}})


def fake_send(path, body, creds):
    return {"id": "vid1", "status": {"privacyStatus": "private"}}


def _metadata_file(book, home, number):
    """A youtube.json that passes metadata.recheck, so ensure() makes no call."""
    plan = episode_home.read_json(home / "plan.json")
    episode_home.write_json(home / "youtube.json", {
        "title": metadata.title_for(book, number, plan),
        "description": "A measured episode.\n\n" + metadata.disclosure("A. B. Author"),
        "tags": ["the test book"], "privacy": "private", "synthetic": True,
        "_synthetic_note": "Local models.",
        "_for": {"plan_sha8": plan_verdict.plan_sha8(home / "plan.json")}})


def episode(tmp_path, monkeypatch):
    library = tmp_path / "library"
    book = book_with(library)
    home, sha8 = episode_with(book, 3)
    standing(book)
    _metadata_file(book, home, 3)
    monkeypatch.setattr(episode_home, "LIBRARY", library)
    monkeypatch.setattr(yp, "file_facts", lambda master: (120.0, 1080, 1080))
    monkeypatch.setattr(youtube, "credentials", lambda path=None: object())
    monkeypatch.setattr(metadata.llm, "structured", lambda *a, **k: (_ for _ in ()).throw(
        AssertionError("a test reached a paid call")))
    return FakeCtx(book, home, 3), book, home, sha8


def test_the_run_uploads_flips_polls_and_ends_with_the_url(tmp_path, monkeypatch, capsys):
    ctx, book, home, sha8 = episode(tmp_path, monkeypatch)
    answers = iter([(200, "https://www.youtube.com/watch?v=vid1"),
                    (200, "https://www.youtube.com/shorts/vid1")])
    step_13_publish.run(ctx, send=fake_send, build_api=FakeApi,
                        http=lambda url: next(answers), sleep=lambda s: None)
    rows = [json.loads(line) for line in
            (book / "uploads.jsonl").read_text(encoding="utf-8").splitlines()]
    assert rows[0]["video_id"] == "vid1" and rows[0]["sha8"] == sha8
    assert [r.get("event") for r in rows].count("privacy") == 1
    poll = next(r for r in rows if r.get("event") == "shorts_poll")
    assert poll["status"] == 200 and "/shorts/" in poll["final_url"]
    printed = capsys.readouterr().out.strip().splitlines()
    assert printed[-1] == "https://www.youtube.com/shorts/vid1"
    assert step_13_publish.done(ctx) is True


def test_a_re_run_with_the_same_cut_uploads_nothing(tmp_path, monkeypatch, capsys):
    ctx, book, home, sha8 = episode(tmp_path, monkeypatch)
    step_13_publish.run(ctx, send=fake_send, build_api=FakeApi,
                        http=lambda url: (200, "https://www.youtube.com/shorts/vid1"),
                        sleep=lambda s: None)
    boom = lambda *a, **k: (_ for _ in ()).throw(AssertionError("sent twice"))  # noqa: E731
    step_13_publish.run(ctx, send=boom, build_api=boom, http=boom, sleep=lambda s: None)
    rows = [json.loads(line) for line in
            (book / "uploads.jsonl").read_text(encoding="utf-8").splitlines()]
    assert [r.get("event") for r in rows].count("privacy") == 1
    assert sum(1 for r in rows if "key" in r) == 1  # one upload row, ever
    assert capsys.readouterr().out.strip().splitlines()[-1] == "https://www.youtube.com/shorts/vid1"


def test_done_is_false_before_the_public_and_poll_rows(tmp_path, monkeypatch):
    ctx, _book, _home, _sha8 = episode(tmp_path, monkeypatch)
    assert step_13_publish.done(ctx) is False


def test_a_poll_that_never_sees_a_short_is_a_recorded_flag_not_a_stop(tmp_path, monkeypatch, capsys):
    ctx, book, home, sha8 = episode(tmp_path, monkeypatch)
    step_13_publish.run(ctx, send=fake_send, build_api=FakeApi,
                        http=lambda url: (200, "https://www.youtube.com/watch?v=vid1"),
                        sleep=lambda s: None)
    poll = next(json.loads(line) for line in
                (book / "uploads.jsonl").read_text(encoding="utf-8").splitlines()
                if json.loads(line).get("event") == "shorts_poll")
    assert "/watch" in poll["final_url"]
    learned = (home / "learnings.jsonl").read_text(encoding="utf-8")
    assert "G-SHORTS" in learned
    assert capsys.readouterr().out.strip().splitlines()[-1] == "https://www.youtube.com/shorts/vid1"
