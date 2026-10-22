"""A line said with feeling gets the drop its genuine lines need, and no more.

2026-10-21 review of the 16 kHz fix (fix/calibrate4.py -> reviewed.json): the felt drop
was kept at 0.20 when every other gap was re-set, and it disarmed two guards.

- The design floor.  A wrong voice from outside the cast (a line of B filed as A, with B's
  design not among the rivals) passed Jekyll's gate 13/296 times at 0.20, 3/296 with no
  drop.  Of 24 genuine felt lines only Enfield's urgent l19 (0.461, 3.9 s) needs a drop at
  all: one seed-noise interval (0.034) under it is 0.427, so the drop is 0.12 (10/296).
  The room score of an alternate render takes the same drop: l19's room is 0.514, and
  0.60 - 0.12 = 0.48 still clears it by one interval.
- The split-voice pair.  The allowance was taken once PER FELT LINE, so a pair of two felt
  lines was held to 0.53 - 0.40 = 0.13 and 18 of 21 Jekyll pairs of DIFFERENT speakers
  passed.  Taken once per pair at FEELING_PAIR_DROP 0.17 (the binding real pair, Enfield's
  calm l08 against his urgent l19 at 0.394, plus one interval), 2 of 21 pass and no genuine
  pair (0/22 one-felt, 0/7 two-felt) is refused.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

from scripts.episode import say_lines as say
from studio import episode_emotion as ee
from studio.speaker_spread import SAME_SPEAKER_FLOOR, spread

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("felt_speaker_check", ROOT / "scripts" / "episode" / "speaker_check.py")
check = importlib.util.module_from_spec(_spec)
sys.modules["felt_speaker_check"] = check
_spec.loader.exec_module(check)

SEED_NOISE = 0.034


def test_the_two_drops_are_the_documented_ones():
    assert ee.FEELING_FLOOR_DROP == 0.12 and ee.FEELING_PAIR_DROP == 0.17


def test_a_calm_line_takes_no_drop_and_a_felt_one_takes_the_line_drop():
    assert say.feeling_drop("calm") == 0.0 and say.feeling_drop("") == 0.0
    assert say.feeling_drop("urgent") == ee.FEELING_FLOOR_DROP


def test_enfields_urgent_line_still_clears_its_floor_by_one_seed_interval():
    assert 0.461 - say.line_floor(3.9, "urgent") >= SEED_NOISE - 0.005
    assert say.line_floor(3.0, "urgent") == round(say.similar_floor(3.0) - 0.12, 2)


def test_the_room_score_takes_the_same_drop():
    assert say.alternate_ok(0.514, 3.0, "urgent")
    assert not say.alternate_ok(0.47, 3.0, "urgent")


def test_a_pair_takes_the_allowance_once_however_many_lines_are_felt():
    said = {"l08": "calm", "l19": "urgent", "l20": "shouting"}
    assert check.allowance(("l08", "l19"), said) == ee.FEELING_PAIR_DROP
    assert check.allowance(("l19", "l20"), said) == ee.FEELING_PAIR_DROP
    assert check.allowance(("l08", "l08"), said) == 0.0


def test_enfields_real_pair_passes_and_two_felt_strangers_do_not():
    allow = SAME_SPEAKER_FLOOR - ee.FEELING_PAIR_DROP
    assert 0.394 - allow >= SEED_NOISE - 0.005
    assert not spread({("l19", "l20"): 0.30}, allow={("l19", "l20"): ee.FEELING_PAIR_DROP})["ok"]


VOICE = ROOT / "tests" / "fixtures" / "voice"


def _pair(a: str, b: str) -> float:
    return float(check.voice_ear.similarity(VOICE / f"{a}.wav", VOICE / f"{b}.wav", "cpu"))


@pytest.mark.local
def test_two_real_calm_speakers_filed_as_one_part_are_a_split():
    """Jekyll ep01's narrator l02 and Utterson l16 (both calm) under one name: 0.29 on 16 kHz."""
    sims = {("l02", "l16"): _pair("narrator_l02", "utterson_l16")}
    assert not spread(sims)["ok"]


@pytest.mark.local
def test_a_real_felt_line_and_a_strangers_calm_line_are_still_a_split():
    """Hyde's cold l10 against Enfield's calm l08 (0.31): the felt allowance does not hide it."""
    pair = ("l08", "l10")
    sims = {pair: _pair("enfield_l08", "hyde_l10")}
    allow = {pair: check.allowance(pair, {"l08": "calm", "l10": "cold"})}
    assert not spread(sims, allow=allow)["ok"]
