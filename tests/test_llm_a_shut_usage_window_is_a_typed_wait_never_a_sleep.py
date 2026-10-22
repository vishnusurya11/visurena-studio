"""A shut subscription window is a typed wait, never a transient error (group R
ruling A1, 2026-10-22).  brain.RateLimited was raised and caught nowhere by type:
llm.structured slept 3 s and 10 s inside a window shut for hours, asked twice
more, and the autopilot parked the episode brain_exhausted (bench R-B1 arm A:
3 calls and 13 s of sleep on every limit input, 60/60 runs).  Now RateLimited IS
an llm.LimitWait(resets_at, window): structured re-raises it after ONE call with
no sleep, its message says the window and the epoch it opens, and the drive
ledger's error word names it.  Limit TEXT on a failed result with no rejected
event (the shape nobody has captured yet, skeptic M2) is the same wait with an
unknown reset -- or the legacy `limit reached|<epoch>` epoch when the text has it."""
from __future__ import annotations

import anyio
import pytest
from pydantic import BaseModel

from studio import brain, episode_drive, llm
from tests.test_brain_a_verdict_is_read_from_the_result_never_from_prose import FakeTransport, result_row

RESETS = 1_793_030_400.0


class Toy(BaseModel):
    answer: str


class ShutWindow:
    def __init__(self, error: Exception):
        self.error, self.calls = error, 0

    def __call__(self, prompt, structured_output_model=None):
        self.calls += 1
        raise self.error


def test_structured_raises_the_wait_after_one_call_and_no_sleep(monkeypatch):
    sleeps, fake = [], ShutWindow(brain.RateLimited(RESETS, "seven_day"))
    monkeypatch.setattr(llm.time, "sleep", sleeps.append)
    with pytest.raises(llm.LimitWait) as caught:
        llm.structured("workhorse", "p", Toy, _agent=fake)
    assert fake.calls == 1 and sleeps == []
    assert caught.value.resets_at == RESETS and caught.value.window == "seven_day"


def test_the_message_names_the_window_and_the_epoch_it_opens():
    said = str(brain.RateLimited(RESETS, "five_hour"))
    assert "usage window five_hour shut until 1793030400" in said and "rate limited" in said
    assert "shut until unknown" in str(llm.LimitWait(None))


def test_the_drive_ledger_names_the_wait_as_the_runs_error():
    log = ("Traceback (most recent call last):\n  File \"episode.py\", line 9\n"
           f"studio.brain.RateLimited: {brain.RateLimited(RESETS, 'five_hour')}\n")
    assert episode_drive.error_class(log) == "studio.brain.RateLimited"


def _ask(replies: list[dict]):
    async def one():
        return await brain.ask_structured("p", Toy, model="claude-sonnet-5", transport=FakeTransport(replies))
    return anyio.run(one)


def test_a_rejected_event_carries_its_window_type(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    event = {"type": "rate_limit_event", "uuid": "u", "session_id": "s",
             "rate_limit_info": {"status": "rejected", "resetsAt": RESETS, "rateLimitType": "seven_day"}}
    with pytest.raises(brain.RateLimited) as caught:
        _ask([event, result_row({"answer": "x"})])
    assert caught.value.resets_at == RESETS and caught.value.window == "seven_day"


@pytest.mark.parametrize("said, resets", [
    ("You've hit your session limit - resets 3pm", None),
    ("Claude AI usage limit reached|1793030400", RESETS),
    ("You've hit your weekly limit", None),
])
def test_limit_text_on_a_failed_result_is_the_same_wait(monkeypatch, said, resets):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    failed = result_row(None, is_error=True, subtype="success", result=said)
    with pytest.raises(brain.RateLimited) as caught:
        _ask([failed])
    assert caught.value.resets_at == resets and caught.value.window == "said"


def test_a_failure_without_limit_words_stays_a_brain_failure(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(brain.BrainFailed) as caught:
        _ask([result_row(None, is_error=True, result="API Error: 529 overloaded")])
    assert not isinstance(caught.value, llm.LimitWait)


def test_an_answer_that_mentions_a_limit_is_still_an_answer(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    parsed, _ = _ask([result_row({"answer": "the usage limit reached the plan"})])
    assert parsed.answer.startswith("the usage limit")


def test_the_triage_turn_reads_limit_text_too():
    with pytest.raises(brain.RateLimited):
        brain.verdict_of(type("R", (), {"terminal_reason": None, "is_error": True, "subtype": "success",
                                        "errors": None, "result": "You've hit your limit",
                                        "structured_output": None})())
