"""Every claude-sdk tier runs on the owner's login, never a billed key (owner
2026-10-07: "don't use API for money").  Group R bench R-B3 (2026-10-22): with a
dummy ANTHROPIC_API_KEY in the environment, both `claude -p` and the in-process
SDK failed "Invalid API key" -- the key wins over the login -- and
ClaudeAgentOptions.env MERGES onto os.environ, so an options allowlist cannot take
the key away.  So `.env` never loads an ANTHROPIC_* name into os.environ (the
OpenAI image paths load it for their own key), and a brain session refuses to
spawn while one is visible: named, never its value, and never retried."""
from __future__ import annotations

import os

import pytest
from pydantic import BaseModel

from studio import brain, llm

KEYS = ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN")


class Toy(BaseModel):
    answer: str


@pytest.fixture
def clean_env(monkeypatch):
    for name in (*KEYS, "OPENAI_API_KEY"):
        monkeypatch.delenv(name, raising=False)
    return monkeypatch


def test_dotenv_loads_the_other_keys_but_never_an_anthropic_one(tmp_path, clean_env):
    env = tmp_path / ".env"
    env.write_text("ANTHROPIC_API_KEY=dummy-a\nANTHROPIC_AUTH_TOKEN=dummy-b\nOPENAI_API_KEY=dummy-o\n",
                   encoding="utf-8")
    llm._load_dotenv(env)
    assert os.environ.get("OPENAI_API_KEY") == "dummy-o"
    assert not any(name in os.environ for name in KEYS)


@pytest.mark.parametrize("name", KEYS)
def test_a_visible_key_refuses_the_session_and_names_it(clean_env, name):
    clean_env.setenv(name, "dummy")
    with pytest.raises(brain.ApiKeyVisible, match=name) as refused:
        brain.refuse_api_key()
    assert "dummy" not in str(refused.value)


def test_no_key_lets_the_session_spawn(clean_env):
    brain.refuse_api_key()


def test_the_writer_session_is_refused_before_it_spawns(clean_env):
    import asyncio
    clean_env.setenv("ANTHROPIC_API_KEY", "dummy")
    with pytest.raises(brain.ApiKeyVisible):
        asyncio.run(brain.ask_structured("p", Toy, model="claude-sonnet-5", transport=object()))


def test_the_triage_turn_is_refused_before_it_spawns(clean_env, tmp_path):
    import asyncio
    clean_env.setenv("ANTHROPIC_AUTH_TOKEN", "dummy")
    with pytest.raises(brain.ApiKeyVisible):
        asyncio.run(brain.turn("why?", brain.triage_options(tmp_path), transport=object()))


class KeyRefused:
    calls = 0

    def __call__(self, prompt, structured_output_model=None):
        self.calls += 1
        raise brain.ApiKeyVisible("ANTHROPIC_API_KEY")


def test_structured_never_retries_a_visible_key(monkeypatch):
    sleeps, fake = [], KeyRefused()
    monkeypatch.setattr(llm.time, "sleep", sleeps.append)
    with pytest.raises(brain.ApiKeyVisible):
        llm.structured("workhorse", "p", Toy, _agent=fake)
    assert fake.calls == 1 and sleeps == []
