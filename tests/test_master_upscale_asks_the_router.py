"""The master upscale asks the compute router before it takes the card (Jekyll ep01: the av3 pass
claimed the GPU unasked).  A busy card is waited for, at most 5 minutes, then the master falls
back to lanczos, said.  Fake router and clock, $0."""
from __future__ import annotations

from contextlib import nullcontext

from studio import master_upscale as mu


class Router:
    def __init__(self, *answers):
        self.answers, self.asked = list(answers), []

    def __call__(self, job, need_gb, *a, **k):
        self.asked.append((job, need_gb))
        return self.answers.pop(0) if len(self.answers) > 1 else self.answers[0]


class Time:
    def __init__(self):
        self.now, self.slept = 0.0, []

    def sleep(self, s):
        self.slept.append(s)
        self.now += s

    def __call__(self):
        return self.now


def test_an_idle_card_is_taken_at_once():
    t, route = Time(), Router("cuda")
    assert mu.card_free("av3 master", 4.0, route=route, sleep=t.sleep, clock=t) is True
    assert t.slept == [] and route.asked == [("av3 master", 4.0)]


def test_a_busy_card_is_waited_for_until_it_frees():
    t, route = Time(), Router("cpu", "cpu", "cuda")
    assert mu.card_free("av3 master", 4.0, route=route, sleep=t.sleep, clock=t) is True
    assert len(t.slept) == 2


def test_a_card_busy_for_five_minutes_is_given_up_on():
    t, route = Time(), Router("cpu")
    assert mu.card_free("av3 master", 4.0, route=route, sleep=t.sleep, clock=t) is False
    assert mu.WAIT_S <= t.now <= mu.WAIT_S + mu.POLL_S


def test_the_wait_is_capped_at_five_minutes():
    assert mu.WAIT_S == 300.0


def test_a_busy_card_falls_back_to_lanczos_loudly(tmp_path, monkeypatch, capsys):
    ran = []
    monkeypatch.setattr(mu, "card_free", lambda *a, **k: False)
    monkeypatch.setattr(mu.subprocess, "run", lambda argv, **k: ran.append(argv))
    out = mu.master(tmp_path / "l.txt", tmp_path / "o.mp4", 768, 768, mu.CHOICES["av3"], 24)
    assert out == tmp_path / "o.mp4" and "scale=" in " ".join(ran[0])
    assert "CAP upscale: card busy" in capsys.readouterr().err


def test_a_free_card_runs_av3_as_asked(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(mu, "card_free", lambda *a, **k: True)
    monkeypatch.setattr(mu, "av3_master", lambda *a, **k: calls.append(a) or a[1])
    mu.master(tmp_path / "l.txt", tmp_path / "o.mp4", 768, 768, mu.CHOICES["av3"], 24)
    assert len(calls) == 1


def test_a_stand_in_model_never_asks_the_router(tmp_path, monkeypatch):
    monkeypatch.setattr(mu, "card_free", lambda *a, **k: (_ for _ in ()).throw(AssertionError("asked")))
    monkeypatch.setattr(mu, "av3_master", lambda *a, **k: a[1])
    mu.master(tmp_path / "l.txt", tmp_path / "o.mp4", 768, 768, mu.CHOICES["av3"], 24, upscaler=lambda f: f)
