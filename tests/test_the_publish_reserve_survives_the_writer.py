"""ep19 (2026-10-06): the writer spent $3.10 of the $3.00 wall in step 02, and
had the plan been signed, step 13's one metadata call would have met the same
wall and the episode could not publish.  `money.publish_reserve_usd` (0.10) is
the slice of the ceiling the writers (local, reasoning, canon) may not eat: a
writer call is refused at `cap - reserve`; the publish step (13) and the
workhorse tier may use the whole ceiling.  The ceiling itself is untouched.
$0: an in-memory database and a fake client."""
from __future__ import annotations

import sqlite3

import pytest

from studio import llm, spend


@pytest.fixture()
def conn():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    spend.init(c)
    return c


def charge(conn, usd, unit="ep19"):
    conn.execute("INSERT INTO usage (recorded_at, codex_id, stage, step_id, tier, model,"
                 " input_tokens, output_tokens, cost_usd, unit) VALUES"
                 " ('t','book','episode','02','local','gpt-5.6-luna',0,0,?,?)", (usd, unit))


@pytest.mark.parametrize("tier, step_id, cap", [
    ("local", "02", 2.90), ("reasoning", "02", 2.90), ("canon", "02", 2.90), (None, None, 2.90),
    ("reasoning", "13", 3.00), ("local", "13", 3.00), ("workhorse", "05", 3.00), ("workhorse", "02", 3.00)])
def test_the_effective_cap_holds_the_reserve_back_from_the_writers(tier, step_id, cap):
    assert llm.effective_cap(tier, step_id, 3.00, 0.10) == pytest.approx(cap)


def test_the_reserve_never_makes_a_negative_cap():
    assert llm.effective_cap("local", "02", 0.05, 0.10) == 0.0


def test_the_reserve_comes_from_models_yaml_and_the_ceiling_is_still_three_dollars():
    assert llm.publish_reserve_usd() == pytest.approx(0.10)
    assert llm.episode_ceiling_usd() == pytest.approx(3.00)


def test_a_writer_call_is_refused_at_the_reserve_and_the_publish_call_passes(conn):
    charge(conn, 2.92)                     # under $3.00, over $2.90: the reserve is what is left
    with llm.spend_context(conn, "book", "episode", "02", unit="ep19"):
        with pytest.raises(llm.OverBudget, match="reserved for the publish"):
            llm.guard_spend(model="gpt-5.6-luna", prompt="x" * 4_000, ceiling=3.00, tier="local")
    with llm.spend_context(conn, "book", "episode", "13", unit="ep19"):
        llm.guard_spend(model="gpt-5.6-luna", prompt="x" * 4_000, ceiling=3.00, tier="reasoning")


def test_the_reserve_follows_the_journaled_step(conn):
    """Step 13 runs under the runner's follow-the-journal context: the step id
    guard_spend reads is the one `spend_step` moved it to."""
    charge(conn, 2.92)
    with llm.spend_context(conn, "book", "episode", None, unit="ep19"):
        llm.spend_step("02")
        with pytest.raises(llm.OverBudget):
            llm.guard_spend(model="gpt-5.6-luna", prompt="x" * 4_000, ceiling=3.00, tier="reasoning")
        llm.spend_step("13")
        llm.guard_spend(model="gpt-5.6-luna", prompt="x" * 4_000, ceiling=3.00, tier="reasoning")


def test_the_native_caller_hands_its_tier_to_the_wall(monkeypatch):
    """The tier reaches guard_spend from the one caller every paid call passes
    (a fix that changes nothing is no fix: the wall must SEE the tier)."""
    monkeypatch.setattr(llm, "resolve_tier", lambda tier: {
        "model": "m", "provider": "lmstudio", "params": {},
        "provider_config": {"base_url": "http://localhost:1", "api_key_env": None}})
    seen = []

    def wall(model, prompt, ceiling=None, tier=None):
        seen.append((model, tier))
        raise llm.OverBudget("the wall")
    monkeypatch.setattr(llm, "guard_spend", wall)
    with pytest.raises(llm.OverBudget):
        llm._NativeStructuredCaller("local")("a prompt", None)
    assert seen == [("m", "local")]
