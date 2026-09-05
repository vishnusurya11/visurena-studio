"""ComfyUI text outputs: a PreviewAny node reports `{"text": [...]}` in the
history record, not a file, so `outputs_of` never sees it."""
from __future__ import annotations

from studio import comfy

RECORD = {"outputs": {"3": {"text": ["a pale man in a bowler hat"]},
                      "4": {"images": [{"filename": "x.png", "type": "output"}]}},
          "status": {"completed": True, "status_str": "success"}}


def test_texts_of_collects_every_text_output_in_node_order():
    record = {"outputs": {"5": {"text": ["second"]}, "3": {"text": ["first", "also"]},
                          "4": {"images": [{"filename": "x.png"}]}}}
    assert comfy.texts_of(record) == ["first", "also", "second"]


def test_texts_of_ignores_non_strings_and_empty_records():
    assert comfy.texts_of({"outputs": {"3": {"text": [None, 4]}}}) == []
    assert comfy.texts_of({}) == []


def test_run_text_returns_the_joined_text_of_the_finished_job(monkeypatch):
    seen = {}
    monkeypatch.setattr(comfy, "load_workflow",
                        lambda name: ({"2": {"inputs": {"text": ""}}}, {"prompt": {"node": "2", "field": "text"}}))
    monkeypatch.setattr(comfy, "submit", lambda wf: seen.setdefault("workflow", wf) and "job-1")
    monkeypatch.setattr(comfy, "wait_record", lambda prompt_id, timeout: RECORD)
    assert comfy.run_text("image_qwen3vl_caption", {"prompt": "describe"}) == "a pale man in a bowler hat"
    assert seen["workflow"]["2"]["inputs"]["text"] == "describe"


def test_wait_record_returns_the_whole_record_on_completion(monkeypatch):
    monkeypatch.setattr(comfy, "history", lambda prompt_id: RECORD)
    assert comfy.wait_record("job-1", timeout=1.0) is RECORD
    assert comfy.wait("job-1", timeout=1.0) == comfy.outputs_of(RECORD)


def test_free_models_posts_the_unload_request(monkeypatch):
    sent = {}

    def fake_urlopen(request, timeout=None):
        sent.update(url=request.full_url, body=request.data)
        import io
        return io.BytesIO(b"")
    monkeypatch.setattr(comfy.urllib.request, "urlopen", fake_urlopen)
    comfy.free_models()
    assert sent["url"].endswith("/free")
    assert b'"unload_models": true' in sent["body"] and b'"free_memory": true' in sent["body"]


def test_interrupt_posts_to_the_interrupt_endpoint(monkeypatch):
    sent = {}

    def fake_urlopen(request, timeout=None):
        sent.update(url=request.full_url)
        import io
        return io.BytesIO(b"")
    monkeypatch.setattr(comfy.urllib.request, "urlopen", fake_urlopen)
    comfy.interrupt()
    assert sent["url"].endswith("/interrupt")


class FakeClock:
    def __init__(self):
        self.now = 1000.0

    def time(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds


def _clock(monkeypatch):
    clock = FakeClock()
    monkeypatch.setattr(comfy.time, "time", clock.time)
    monkeypatch.setattr(comfy.time, "sleep", clock.sleep)
    return clock


def test_the_timeout_clock_starts_when_the_job_leaves_the_queue(monkeypatch):
    """Run 6: a sheet queued behind an 11-minute take timed out before it had
    run a second.  Waiting in line is not running."""
    clock = _clock(monkeypatch)
    pending = {"left": 3}
    monkeypatch.setattr(comfy, "pending", lambda prompt_id: pending.__setitem__("left", pending["left"] - 1) or pending["left"] >= 0)
    done = {"at": None}

    def history(prompt_id):
        done["at"] = done["at"] or clock.now + 6
        return RECORD if clock.now >= done["at"] else {}
    monkeypatch.setattr(comfy, "history", history)
    assert comfy.wait_record("job-1", timeout=12.0, poll=5.0) is RECORD
    assert clock.now >= 1000.0 + 15 + 6  # 15 s in line did not count


def test_a_running_job_still_times_out(monkeypatch):
    _clock(monkeypatch)
    monkeypatch.setattr(comfy, "pending", lambda prompt_id: False)
    monkeypatch.setattr(comfy, "history", lambda prompt_id: {})
    import pytest
    with pytest.raises(TimeoutError):
        comfy.wait_record("job-1", timeout=10.0, poll=5.0)


def test_pending_reads_the_engines_queue(monkeypatch):
    queue = {"queue_running": [[0, "job-0", {}]], "queue_pending": [[1, "job-1", {}]]}
    monkeypatch.setattr(comfy, "_get", lambda path: queue)
    assert comfy.pending("job-1") is True
    assert comfy.pending("job-0") is False
