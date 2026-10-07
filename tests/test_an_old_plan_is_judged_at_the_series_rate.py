"""ep19, 2026-10-07 15:40Z: the aside's draft (written 2026-10-06, before the
rate was persisted) carried no `words_per_second`; the cures split its nine
long shots at the measured 2.5 w/s (134 s), the contract then projected it at
the default 3.0 (117 s < 120) and the repair threw the cure away -- round after
round.  A doc from disk with no rate is judged at the series' measured rate,
in the battery and in every repair round; a doc that has one keeps it."""
from __future__ import annotations

from studio import plan_gates


def test_a_doc_without_a_rate_gets_the_series_rate(monkeypatch):
    monkeypatch.setattr(plan_gates, "series_rate", lambda book, number: 2.5)
    assert plan_gates.at_series_rate({"shots": []}, "book", 19)["words_per_second"] == 2.5


def test_a_doc_with_a_rate_keeps_it(monkeypatch):
    monkeypatch.setattr(plan_gates, "series_rate", lambda book, number: (_ for _ in ()).throw(AssertionError("asked")))
    assert plan_gates.at_series_rate({"words_per_second": 2.7}, "book", 19)["words_per_second"] == 2.7
