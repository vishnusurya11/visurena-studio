"""The $3 wall lives in THIS process: guard_spend fires inside the structured
call only under llm.spend_context, so step 13 must call metadata.ensure as a
direct import, never through ctx.run_script -- a subprocess has an empty
_SPEND and would bypass the ceiling.  The ctx fake's run_script raises, so a
completed run is proof the step never shelled out for anything."""
from __future__ import annotations

from scripts.episode import step_13_publish
from tests.test_step_13_publishes_and_polls import FakeApi, episode, fake_send


def test_metadata_is_called_in_process_never_via_run_script(tmp_path, monkeypatch):
    ctx, _book, _home, _sha8 = episode(tmp_path, monkeypatch)
    calls = []

    def spy(home, book, number, **kwargs):
        calls.append((home, book, number))
        return home / "youtube.json"

    monkeypatch.setattr(step_13_publish.metadata, "ensure", spy)
    step_13_publish.run(ctx, send=fake_send, build_api=FakeApi,
                        http=lambda url: (200, "https://www.youtube.com/shorts/vid1"),
                        sleep=lambda s: None)
    assert calls == [(ctx.home, ctx.book_dir, 3)]  # one direct call, this process
