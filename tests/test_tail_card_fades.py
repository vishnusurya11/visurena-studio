"""The card may be faded up and down; every other frame must still be the card."""
import numpy as np

from studio.edit_gate import END_CHIP_FRAMES, tail_check


def _card(n=100):
    rng = np.random.default_rng(3)
    return rng.integers(40, 250, (n, 16, 16), dtype=np.uint8)


def _master(card, fade_in=11, fade_out=17, black=END_CHIP_FRAMES, picture=5):
    shown = card.astype(np.float32).copy()
    for i in range(fade_in):
        shown[i] *= i / fade_in
    for k in range(fade_out):
        shown[len(card) - 1 - k] *= k / fade_out
    body = np.concatenate([np.full((picture, 16, 16), 90, np.uint8),
                           shown.astype(np.uint8),
                           np.zeros((black, 16, 16), np.uint8)])
    return body


def test_a_faded_card_passes_and_its_middle_still_matches():
    card = _card()
    out = tail_check(_master(card), picture_frames=5, card=card)
    assert out["ok"], out
    assert out["card_frames_off"] == [] and out["card_fade_frames"]


def test_a_short_master_still_fails_even_with_fades():
    card = _card()
    master = _master(card)[:-3]
    assert not tail_check(master, picture_frames=5, card=card)["ok"]


def test_a_cropped_card_still_fails():
    card = _card()
    master = _master(card)
    master[5 + 50] = 0  # a middle frame that is not the card
    assert not tail_check(master, picture_frames=5, card=card)["ok"]


def test_a_fade_that_never_reaches_the_card_fails():
    card = _card()
    master = _master(card, fade_in=90, fade_out=0)
    assert not tail_check(master, picture_frames=5, card=card)["ok"]
