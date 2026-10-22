"""A15: each line projected at its own measured rate -- only if it wins out of sample (craft ruling, wave 1).

`plan_gates.measured_rate` gives one blended rate to every line (Jekyll ep01: 2.45 w/s), though the
narrator speaks 2.23, Enfield 2.96 and Utterson 3.06.  The ruling's fallback is per speaker (5 or more
voiced lines), per kind, blended, then STUDIO_RATE, and it SHIPS ONLY IF the $0 leave-one-episode-out
over every voiced lines.json beats the blended rate; a pause term ships only if it wins out of sample.
The replay (`scripts/episode/rate_replay.py`) is that measurement; it changes no projection itself.
Fixtures: tests/fixtures/craft (Jekyll ep01 lines.json) and synthetic books in tmp_path.  No spend."""
from __future__ import annotations

import json
from pathlib import Path

from scripts.episode import rate_replay as rr
from studio import plan_gates

BOOK = Path(__file__).parent / "fixtures" / "craft"
LINES = BOOK / "episodes" / "ep01" / "audio" / "lines" / "lines.json"


def rows() -> list[dict]:
    return rr.voiced(json.loads(LINES.read_text(encoding="utf-8")))


def test_the_fixture_speakers_have_their_own_rates():
    rates = rr.speaker_rates(rows())
    assert round(rates["narrator"], 2) == 2.23
    assert round(rates["richard_enfield"], 2) == 2.96
    assert round(rates["gabriel_john_utterson"], 2) == 3.06
    assert plan_gates.series_rate(BOOK, 1) == 2.45                       # today: one rate for all three


def test_line_12_projects_nearer_its_measured_seconds():
    line = rows()[12]
    blended = rr.words(line) / plan_gates.series_rate(BOOK, 1)          # what ep01 projected
    mine = rr.project(line, rows(), "speaker")
    assert round(blended, 2) == 5.71 and float(line["seconds"]) == 7.34
    assert blended < mine < 7.34


def test_the_fallback_order_is_speaker_kind_blended_studio():
    few = [{"speaker": "a", "kind": "tale", "text": "one two three", "seconds": 1.0}] * 2
    many_kind = few + [{"speaker": "b", "kind": "tale", "text": "one two", "seconds": 1.0}] * 5
    assert rr.rate_for({"speaker": "a", "kind": "tale"}, many_kind) == rr.rate(
        [r for r in many_kind if r["kind"] == "tale"])
    assert rr.rate_for({"speaker": "z", "kind": "inner"}, few) == rr.rate(few)
    assert rr.rate_for({"speaker": "z", "kind": "inner"}, []) == plan_gates.measured_rate([])


def book(tmp_path: Path, episodes: dict[int, list[dict]]) -> Path:
    for n, lines in episodes.items():
        home = tmp_path / "episodes" / f"ep{n:02d}" / "audio" / "lines"
        home.mkdir(parents=True)
        (home / "lines.json").write_text(json.dumps(lines), encoding="utf-8")
    return tmp_path


def two_voices(n: int) -> list[dict]:
    fast = [{"speaker": "fast", "kind": "dialogue", "text": "a b c d e f", "seconds": 1.5, "passed": True}] * 5
    slow = [{"speaker": "slow", "kind": "narration", "text": "a b c d e f", "seconds": 4.0, "passed": True}] * 5
    return fast + slow


def test_two_distinct_voices_ship_per_speaker(tmp_path):
    out = rr.loo([book(tmp_path, {1: two_voices(1), 2: two_voices(2), 3: two_voices(3)})])
    assert out["speaker"] < out["blended"] and rr.verdict(out).startswith("per-speaker wins")


def test_a_book_of_one_voice_ships_nothing(tmp_path):
    one = [{"speaker": s, "kind": "narration", "text": "a b c d", "seconds": 2.0, "passed": True}
           for s in ("x", "y") for _ in range(5)]
    out = rr.loo([book(tmp_path, {1: one, 2: one})])
    assert rr.verdict(out).startswith("per-speaker does not win") and "nothing ships" in rr.verdict(out)


def test_one_episode_is_no_out_of_sample_test(tmp_path):
    assert rr.loo([book(tmp_path, {1: two_voices(1)})])["lines"] == 0
